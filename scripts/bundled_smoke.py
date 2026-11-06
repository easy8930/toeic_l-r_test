"""Use generated WAV fixtures; refuses to overwrite any existing bundled material."""
from pathlib import Path
import tempfile,subprocess,wave,io,zipfile,shutil,os
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];output=root/'public/audio'
assert not output.exists(),'Move existing public/audio aside before running fixture test'
with tempfile.TemporaryDirectory() as tmp:
 b=io.BytesIO()
 with wave.open(b,'wb') as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(b'\0\0'*5600)
 path=Path(tmp)/'fixture.zip'
 with zipfile.ZipFile(path,'w') as z:
  for n in [132,133]:z.writestr(f'folder/{n}.wav',b.getvalue())
 try:
  subprocess.run(['node','scripts/bundle-audio.mjs',str(path)],cwd=root,check=True)
  # Rerunning preparation is safe and retains stable content URLs.
  before=(output/'manifest.json').read_bytes()
  subprocess.run(['node','scripts/bundle-audio.mjs',str(path)],cwd=root,check=True)
  assert (output/'manifest.json').read_bytes()==before
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
   for width in [1440,390]:
    context=browser.new_context(viewport={'width':width,'height':844},has_touch=width==390,is_mobile=width==390)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(os.environ.get('APP_URL','http://localhost:5173'));page.locator('h1').wait_for()
    page.locator('nav [data-view="tracks"]').click();assert page.locator('.track-row').count()==2
    assert page.locator('.listen-count b').all_inner_texts()==['0','0']
    page.locator('[data-track]').first.click()
    page.wait_for_function("JSON.parse(localStorage.getItem('listening-room-v1')).tracks.every(t=>t.count===1)")
    page.reload();page.locator('nav [data-view="tracks"]').click();assert page.locator('.listen-count b').all_inner_texts()==['1','1']
    assert not errors,errors
    context.close()
   browser.close()
  print('PASS: repeatable bundling; fresh desktop and mobile see and play audio without import; continuous playback; per-browser counts persist')
 finally:
  if output.exists():shutil.rmtree(output)
