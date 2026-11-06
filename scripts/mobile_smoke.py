"""Test a LAN HTTP origin with mobile touch emulation. APP_URL must be non-localhost."""
import os,io,wave,zipfile
from playwright.sync_api import sync_playwright
b=io.BytesIO()
with wave.open(b,'wb') as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(b'\0\0'*4000)
z=io.BytesIO()
with zipfile.ZipFile(z,'w') as f:f.writestr('132.wav',b.getvalue())
url=os.environ['APP_URL']
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
 
 if os.environ.get('ROUTE_LOCAL'):
  from urllib.parse import urlsplit
  def local_route(route):
   target='http://127.0.0.1:5173'+urlsplit(route.request.url).path
   query=urlsplit(route.request.url).query
   if query:target+='?'+query
   response=route.fetch(url=target)
   route.fulfill(response=response)
  context.route(url+'/**',local_route)
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(url);page.locator('h1').wait_for();assert not page.evaluate('isSecureContext');assert page.evaluate('typeof crypto.randomUUID')=='undefined'
 for width in [320,390,430]:
  page.set_viewport_size({'width':width,'height':844})
  for view in ['home','tracks','groups','import']:
   page.locator(f'nav [data-view="{view}"]').tap();assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(width,view)
   for button in page.locator('nav button').all():
    box=button.bounding_box();assert box['width']>=44 and box['height']>=44;assert box['x']>=0 and box['x']+box['width']<=width
 page.locator('#file-input').set_input_files({'name':'audio.zip','mimeType':'application/zip','buffer':z.getvalue()})
 page.wait_for_function("document.querySelector('#import-status').textContent.includes('1トラックを保存しました（')")
 page.locator('nav [data-view="tracks"]').tap();page.locator('[data-track]').first.tap()
 page.wait_for_function("JSON.parse(localStorage.getItem('listening-room-v1')).tracks[0].count===1")
 page.reload();page.locator('nav [data-view="tracks"]').tap();assert page.locator('.listen-count b').inner_text()=='1'
 page.locator('nav [data-view="groups"]').tap();page.locator('#group-name').fill('スマホのまとめ');page.locator('#group-start').fill('132');page.locator('#group-end').fill('132');page.locator('#group-form button').tap();assert page.locator('.group-card').count()==8
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path='/tmp/listening-room-mobile-touch.png',full_page=True)
 assert not errors,errors
 print('PASS: LAN HTTP without randomUUID; touch navigation at 320/390/430px; ZIP import; actual playback count; reload persistence; group creation')
 context.close();browser.close()
