# -*- coding: utf-8 -*-
"""从底部仰视验证：红砖是否漏掉补株位置。用相机phi接近PI。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9393; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_bot_9393')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1518,970','--hide-scrollbars',
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
def js(e):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('result',{}).get('value')
def shot(p):
  d=call('Page.captureScreenshot',{'format':'png'})['result']['data']
  open(p,'wb').write(base64.b64decode(d));print('SHOT',p,os.path.getsize(p))
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
def setv(id,val,ev):js("var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));"%(id,json.dumps(str(val)),ev))
def click(id):js("document.getElementById('%s').click();"%id)
# 复现老师参数：upN=11 spread=1.5 autoFill=0.96 redbase=6mm overlap=0.30
setv('preset','upright','change');time.sleep(0.4)
setv('upN',11,'input');setv('upSpread',15,'input');setv('spiralMode','dec36','change')
js("var a=document.getElementById('autoFill');if(!a.checked)a.click();")
setv('fillK',100,'input')
js("var h=document.getElementById('hexBase');if(!h.checked)h.click();")
setv('hexThick',5,'input');setv('hexOverlap',0,'input');setv('prog',1000,'input');time.sleep(2.5)
print('HUD:',js("document.getElementById('hudBody').innerText").replace('\n',' | '))
# 仰视：鼠标从画面中心向下拖 → phi 增大到接近 PI（相机到下方）
rect=json.loads(js("JSON.stringify(document.getElementById('cv').getBoundingClientRect())"))
cx=rect['left']+rect['width']*0.35;cy=rect['top']+rect['height']*0.5
call('Input.dispatchMouseEvent',{'type':'mousePressed','x':cx,'y':cy,'button':'left','buttons':1,'clickCount':1})
for i in range(1,9):
  call('Input.dispatchMouseEvent',{'type':'mouseMoved','x':cx,'y':cy+i*45,'button':'left','buttons':1})
  time.sleep(0.05)
call('Input.dispatchMouseEvent',{'type':'mouseReleased','x':cx,'y':cy+360,'button':'left','buttons':0,'clickCount':1})
time.sleep(1.5)
shot('_dev/edge_gap_now.png')
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
