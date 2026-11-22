# -*- coding: utf-8 -*-
"""低斜视角看外缘：确认补在边缘缺口的小株落在淡灰底盘上、不悬空、不外露锥底。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9415; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_filllow_9415')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1400,900','--hide-scrollbars',
  '--remote-debugging-port=%d'%PORT,'--user-data-dir='+PROFILE,'about:blank'],
  stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def targets():
  for _ in range(80):
    try:
      ts=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list'%PORT,timeout=1))
      p=[t for t in ts if t['type']=='page']
      if p:return p[0]
    except Exception:pass
    time.sleep(0.5)
  raise RuntimeError('no devtools')
t=targets();ws=websocket.create_connection(t['webSocketDebuggerUrl'],timeout=180,suppress_origin=True)
mid=[0]
def call(m,p=None):
  mid[0]+=1;n=mid[0];ws.send(json.dumps({'id':n,'method':m,'params':p or {}}))
  while True:
    r=json.loads(ws.recv())
    if r.get('id')==n:return r
def js(e,awaitp=False):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':awaitp}).get('result',{}).get('result',{}).get('value')
def shot(p,clip=None):
  par={'format':'png'}
  if clip:par['clip']=clip
  d=call('Page.captureScreenshot',par)['result']['data']
  open(p,'wb').write(base64.b64decode(d));print('SHOT',p)
def drag(x1,y1,x2,y2):
  call('Input.dispatchMouseEvent',{'type':'mousePressed','x':x1,'y':y1,'button':'left','buttons':1,'clickCount':1})
  for k in range(1,13):
    call('Input.dispatchMouseEvent',{'type':'mouseMoved','x':x1+(x2-x1)*k/12,'y':y1+(y2-y1)*k/12,'button':'left','buttons':1})
  call('Input.dispatchMouseEvent',{'type':'mouseReleased','x':x2,'y':y2,'button':'left','buttons':0,'clickCount':1})
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
js("var e=document.getElementById('preset');e.value='upright';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(1.5)
js("var c=document.getElementById('autoFill');c.checked=true;c.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(2)
js("document.getElementById('btnTop').click()");time.sleep(0.8)
shot('../预览_补株_低斜视角_全景_upN7.png')
drag(500,260,500,360)   # 往下拖 → 抬高 phi 变成低斜视
time.sleep(1.0)
shot('../预览_补株_低斜视角_边缘特写_upN7.png',{'x':300,'y':250,'width':520,'height':260,'scale':2.2})
print('CAM:',js("JSON.stringify({t:window.__cam.theta(),p:window.__cam.phi(),r:window.__cam.radius()})"))
print('FILL:',js("JSON.stringify({n:window.__fill().fillCount,i:window.__fill().fillInner,e:window.__fill().fillEdge})"))
print('ERR:',js("document.getElementById('err').style.display"))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
