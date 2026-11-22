# -*- coding: utf-8 -*-
"""验证：调任何参数/切预设都不改变相机视角（仅首次取景）。"""
import time, os, json, subprocess, urllib.request, urllib.parse
import websocket
PORT=9391; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_cam_9391')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1200,800','--remote-debugging-port=%d'%PORT,
  '--user-data-dir='+PROFILE,'about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def targets():
  for _ in range(80):
    try:
      ts=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list'%PORT,timeout=1))
      p=[t for t in ts if t['type']=='page']
      if p:return p[0]
    except Exception:pass
    time.sleep(0.5)
  raise RuntimeError('no devtools')
t=targets();ws=websocket.create_connection(t['webSocketDebuggerUrl'],timeout=120,suppress_origin=True)
mid=[0]
def call(m,p=None):
  mid[0]+=1;n=mid[0];ws.send(json.dumps({'id':n,'method':m,'params':p or {}}))
  while True:
    r=json.loads(ws.recv())
    if r.get('id')==n:return r
def js(e):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('result',{}).get('value')
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && window.__cam && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
def camstate():return js("JSON.stringify({t:window.__cam.theta(),p:window.__cam.phi(),r:window.__cam.radius()})")
def setv(id,val,ev):js("var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));"%(id,json.dumps(str(val)),ev))
# 手动旋转+缩放到自定义视角
rect=json.loads(js("JSON.stringify(document.getElementById('cv').getBoundingClientRect())"))
cx=rect['left']+rect['width']*0.4;cy=rect['top']+rect['height']*0.5
call('Input.dispatchMouseEvent',{'type':'mousePressed','x':cx,'y':cy,'button':'left','buttons':1,'clickCount':1})
call('Input.dispatchMouseEvent',{'type':'mouseMoved','x':cx+180,'y':cy-90,'button':'left','buttons':1})
call('Input.dispatchMouseEvent',{'type':'mouseReleased','x':cx+180,'y':cy-90,'button':'left','buttons':0,'clickCount':1})
call('Input.dispatchMouseEvent',{'type':'mouseWheel','x':cx,'y':cy,'deltaX':0,'deltaY':240})
time.sleep(1)
base=camstate();print('BASE_CAM:',base)
# 依次调各种参数
tests=[
  ('angle',126.348,'input'),
  ('levels',4,'input'),
  ('upN',19,'input'),
  ('upSpread',15,'input'),
  ('hexThick',12,'input'),
  ('spiralMode','dec36','change'),
  ('cmap','turbo','change'),
  ('preset','xmas','change'),
  ('preset','upright','change'),
]
for id,val,ev in tests:
  setv(id,val,ev);time.sleep(0.5)
  now=camstate()
  print('%-12s -> %s  SAME=%s'%(id,now,now==base))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
