"""Theme-only browser checks. Does not load, play, or test audio."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json,os,subprocess,tempfile,threading
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class QuietHandler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
with tempfile.TemporaryDirectory() as folder:
 dist=Path(folder)/'dist'
 subprocess.run(['node','--input-type=module','-e',"import {build} from 'vite'; await build({publicDir:false,build:{outDir:process.argv[1],emptyOutDir:true}});",str(dist)],cwd=ROOT,check=True)
 (dist/'audio').mkdir()
 track=dict(number=1,name='001.mp3',url='audio/files/'+'a'*64+'.mp3')
 (dist/'audio/manifest.json').write_text(json.dumps(dict(version=1,tracks=[track])))
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(dist)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as p:
   exe=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium')
   browser=p.chromium.launch(headless=True,args=['--no-sandbox'],**({'executable_path':exe} if Path(exe).exists() else {}))
   for width in [1440,320,390]:
    context=browser.new_context(viewport={'width':width,'height':900},color_scheme='dark',is_mobile=width<600,has_touch=width<600)
    page=context.new_page();errors=[];media=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:media.append(r.url) if r.resource_type=='media' else None)
    page.add_init_script("window.__playCalls=0;HTMLMediaElement.prototype.play=function(){window.__playCalls++;throw Error('Audio playback is excluded from theme tests')};if(!localStorage.getItem('listening-room-v1'))localStorage.setItem('listening-room-v1',JSON.stringify({tracks:[{number:1,id:'bundled-1',count:7}],groups:[],speed:1,repeat:false}))")
    page.goto(f'http://127.0.0.1:{server.server_port}/');page.locator('h1').wait_for()
    assert page.locator('html').get_attribute('data-theme')=='dark'
    before=page.evaluate("localStorage.getItem('listening-room-v1')")
    colors={}
    for theme in ['light','dark']:
     page.locator('#theme-select').select_option(theme)
     assert page.locator('html').get_attribute('data-theme')==theme
     colors[theme]=page.evaluate("getComputedStyle(document.documentElement).backgroundColor")
     for view in ['home','tracks','groups','records']:
      page.locator(f'nav [data-view="{view}"]').click()
      assert page.locator('#theme-select').input_value()==theme
      assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(width,view,theme)
     assert page.evaluate("localStorage.getItem('listening-room-v1')")==before
     page.reload();page.locator('h1').wait_for()
     assert page.locator('html').get_attribute('data-theme')==theme
     assert page.locator('#theme-select').input_value()==theme
     if width in [1440,390]:page.screenshot(path=f'/tmp/listening-theme-{width}-{theme}.png',full_page=True)
    assert colors['light']!=colors['dark']
    # Saved selection must win even when the OS preference changes.
    page.locator('#theme-select').select_option('light');page.emulate_media(color_scheme='dark');page.reload();page.locator('h1').wait_for();assert page.locator('html').get_attribute('data-theme')=='light'
    assert page.evaluate('__playCalls')==0;assert not media,media;assert not errors,errors
    print(f'PASS {width}px: system default, light/dark on all 4 screens, persistence, no overflow, unchanged progress, no audio requests/playback')
    context.close()
   browser.close()
 finally:server.shutdown();server.server_close()
