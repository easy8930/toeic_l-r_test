"""Run against npm run dev. Requires Python Playwright and system Chromium."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import wave,io,zipfile,json,os

def wav(seconds=1):
 b=io.BytesIO()
 with wave.open(b,'wb') as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(b'\0\0'*int(8000*seconds))
 return b.getvalue()
archive=io.BytesIO()
with zipfile.ZipFile(archive,'w') as z:
 for n in [132,133,136]:z.writestr(f'audio03/7018001_{n}.wav',wav(1.2))
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1100});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(os.environ.get('APP_URL','http://localhost:5173'))
 page.locator('h1').wait_for();assert 'まだ音声がありません' in page.inner_text('body')
 page.screenshot(path='/tmp/listening-room-empty.png',full_page=True)
 page.locator('#file-input').set_input_files({'name':'7018001_audio03.zip','mimeType':'application/zip','buffer':archive.getvalue()})
 page.wait_for_function("document.querySelector('#import-status').textContent.includes('3トラックを保存しました（')")
 page.locator('nav [data-view="tracks"]').click();assert page.locator('.track-row').count()==3
 page.locator('[data-track]').first.click();page.wait_for_function("document.querySelector('#play').getAttribute('aria-label') === '一時停止'")
 page.locator('#play').click();page.wait_for_timeout(200)
 assert page.locator('.listen-count b').first.inner_text()=='0'
 page.locator('#play').click()
 page.wait_for_function("JSON.parse(localStorage.getItem('listening-room-v1')).tracks.every(t=>t.count===1)",timeout=15000)
 page.wait_for_function("document.querySelector('#play').getAttribute('aria-label') === '再生'")
 assert page.locator('.listen-count b').all_inner_texts()==['1','1','1']
 page.reload();page.locator('h1').wait_for();page.locator('nav [data-view="tracks"]').click();assert page.locator('.listen-count b').all_inner_texts()==['1','1','1']
 page.locator('#search').fill('133');assert page.locator('.track-row').count()==1;page.locator('#search').fill('')
 page.locator('nav [data-view="groups"]').click();page.locator('#range-start').fill('136');page.locator('#range-end').fill('136');page.locator('#range-form button').click()
 page.wait_for_function("JSON.parse(localStorage.getItem('listening-room-v1')).tracks.find(t=>t.number===136).count===2",timeout=10000)
 page.wait_for_timeout(500);s=page.evaluate("JSON.parse(localStorage.getItem('listening-room-v1'))");assert [t['count'] for t in s['tracks']]==[1,1,2]
 page.locator('#group-name').fill('Part 2 自習');page.locator('#group-start').fill('132');page.locator('#group-end').fill('136');page.locator('#group-form button').click();assert page.locator('.group-card').count()==8
 page.locator('nav [data-view="home"]').click();page.screenshot(path='/tmp/listening-room-desktop.png',full_page=True)
 page.locator('#drive').click();assert page.locator('#driver').is_visible();page.locator('#close-driver').click()
 # Export must preserve counts and group boundaries.
 page.locator('nav [data-view="import"]').click()
 with page.expect_download() as info:page.locator('[data-action="export"]').click()
 backup=json.loads(Path(info.value.path()).read_text());assert [t['count'] for t in backup['tracks']]==[1,1,2];assert backup['groups'][0]['start']==132
 # Same-number re-import replaces the audio but preserves counts.
 page.locator('#file-input').set_input_files({'name':'132.wav','mimeType':'audio/wav','buffer':wav(1.2)})
 page.wait_for_function("document.querySelector('#import-status').textContent.includes('1トラックを保存しました（')")
 assert page.evaluate("JSON.parse(localStorage.getItem('listening-room-v1')).tracks.find(t=>t.number===132).count")==1
 # Repeat a one-track range, then pause to prevent an endless loop.
 page.locator('nav [data-view="groups"]').click();page.locator('#range-start').fill('133');page.locator('#range-end').fill('133');page.locator('#repeat').click();page.locator('#range-form button').click()
 page.wait_for_function("JSON.parse(localStorage.getItem('listening-room-v1')).tracks.find(t=>t.number===133).count>=3",timeout=10000)
 page.locator('#play').click();page.locator('#repeat').click()
 page.set_viewport_size({'width':390,'height':844});page.locator('nav [data-view="home"]').click();assert page.evaluate('document.documentElement.scrollWidth <= innerWidth');page.screenshot(path='/tmp/listening-room-mobile.png',full_page=True)
 for v in ['tracks','groups','import']:
  page.locator(f'nav [data-view="{v}"]').click();assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),v
 assert not errors,errors
 print('PASS: ZIP import; real WAV playback; pause/resume; completion counts; automatic advance; inclusive range stop; repeat; reload persistence; search; custom groups; backup export; replacement preserves counts; mobile layouts; no page errors')
 browser.close()
