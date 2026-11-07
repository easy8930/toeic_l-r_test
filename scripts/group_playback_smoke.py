"""Production-browser regression for partial libraries and actual group playback.
Uses an isolated build and generated WAV fixtures; never edits textbook audio.
"""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import io,json,os,subprocess,tempfile,threading,wave
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
class QuietHandler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

with tempfile.TemporaryDirectory() as folder:
 dist=Path(folder)/'dist'
 subprocess.run(['node','--input-type=module','-e',"import {build} from 'vite'; await build({publicDir:false, build:{outDir:process.argv[1],emptyOutDir:true}});",str(dist)],cwd=ROOT,check=True)
 audio=dist/'audio/files';audio.mkdir(parents=True,exist_ok=True)
 data=io.BytesIO()
 with wave.open(data,'wb') as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(b'\0\0'*8000)
 # Valid production URL shape and actual decodable sound.
 for n in [1,2,101,132,133]:
  (audio/(f'{n:064x}'+'.wav')).write_bytes(data.getvalue())
 def library(numbers):
  tracks=[dict(id=f'bundled-{n}',number=n,name=f'{n:03}.wav',url=f'audio/files/{n:064x}.wav') for n in numbers]
  (dist/'audio/manifest.json').write_text(json.dumps(dict(version=1,tracks=tracks)))
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(dist)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as p:
   executable=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium')
   options={'executable_path':executable} if Path(executable).exists() else {}
   browser=p.chromium.launch(headless=True,args=['--no-sandbox'],**options)
   for width in [1440,390]:
    for numbers,group in [([1,2,101],'all-audio'),([132,133],'part2')]:
     library(numbers)
     for screen in ['home','groups']:
      context=browser.new_context(viewport={'width':width,'height':844},has_touch=width<600,is_mobile=width<600)
      page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
      page.add_init_script("window.__played=[];const original=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){if(!window.__played.includes(this))window.__played.push(this);return original.call(this)}")
      page.goto(f'http://127.0.0.1:{server.server_port}/');page.locator('h1').wait_for()
      if screen=='groups':page.locator('nav [data-view="groups"]').click()
      button=page.locator(f'[data-group="{group}"]');assert button.is_enabled()
      if numbers[0]==1:
       unavailable=page.locator('[data-group="part2"]')
       if unavailable.count():assert unavailable.is_disabled();assert 'まだ登録されていません' in unavailable.locator('xpath=ancestor::article').inner_text()
      button.click()
      # Do not settle for an enabled button or a play() call: media must decode and advance.
      page.wait_for_function('window.__played.some(a=>!a.paused && a.readyState>=2 && a.currentTime>0.05)',timeout=10000)
      first=numbers[0];second=numbers[1]
      page.wait_for_function(f"JSON.parse(localStorage.getItem('listening-room-v1')).tracks.find(t=>t.number==={first}).count===1",timeout=10000)
      page.wait_for_function(f"window.__played.some(a=>a.currentSrc.includes('{second:064x}') && !a.paused && a.currentTime>0.05)",timeout=10000)
      page.wait_for_function("JSON.parse(localStorage.getItem('listening-room-v1')).tracks.every(t=>t.count===1)",timeout=10000)
      assert page.locator('#play').get_attribute('aria-label')=='再生'
      page.reload();page.locator('h1').wait_for();saved=page.evaluate("JSON.parse(localStorage.getItem('listening-room-v1'))");assert all(t['count']==1 for t in saved['tracks'])
      assert not errors,errors
      print(f'PASS: {width}px {screen} {group}: decoded playback, time advances, next track plays, queue stops, counts persist')
      context.close()
   browser.close()
 finally:server.shutdown();server.server_close()
