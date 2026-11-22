# -*- coding: utf-8 -*-
"""验证：poly 预算放宽后芽数/锥数，及"从里到外 HSV"新配色"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9435; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_rg_9435')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1200,900','--hide-scrollbars',
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
t=targets();ws=websocket.create_connection(t['webSocketDebuggerUrl'],timeout=300,suppress_origin=True)
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
  open(p,'wb').write(base64.b64decode(d));print('SHOT',p,flush=True)
def wheel(x,y,dy):call('Input.dispatchMouseEvent',{'type':'mouseWheel','x':x,'y':y,'deltaX':0,'deltaY':dy})
def drag(x1,y1,x2,y2):
  call('Input.dispatchMouseEvent',{'type':'mousePressed','x':x1,'y':y1,'button':'left','buttons':1,'clickCount':1})
  for k in range(1,11):
    call('Input.dispatchMouseEvent',{'type':'mouseMoved','x':x1+(x2-x1)*k/10,'y':y1+(y2-y1)*k/10,'button':'left','buttons':1})
  call('Input.dispatchMouseEvent',{'type':'mouseReleased','x':x2,'y':y2,'button':'left','buttons':0,'clickCount':1})

call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
js("var e=document.getElementById('preset');e.value='bucky';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(4)

for lv in [2,3]:
  js("var e=document.getElementById('levels');e.value='%d';e.dispatchEvent(new Event('input',{bubbles:true}));"%lv)
  time.sleep(6.0)
  hud=js("document.getElementById('hudBody').innerText.replace(/\\n/g,' | ')")
  print('--- levels=%d ---'%lv,flush=True)
  print('HUD:',hud,flush=True)
  shot('../预览_新配色_levels%d_全景.png'%lv,{'x':320,'y':90,'width':540,'height':540,'scale':1.25})
  wheel(600,420,-760); time.sleep(1.3)
  shot('../预览_新配色_levels%d_特写.png'%lv,{'x':330,'y':100,'width':520,'height':520,'scale':1.35})
  wheel(600,420,760); time.sleep(0.8)

# 直立花盘配色回归（非 poly，确认没被配色改动破坏）
js("var e=document.getElementById('preset');e.value='upright';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(5)
print('upright HUD:',js("document.getElementById('hudBody').innerText.replace(/\\n/g,' | ')"),flush=True)
shot('../预览_新配色_upright.png',{'x':320,'y':90,'width':540,'height':540,'scale':1.25})
print('ERR:',js("document.getElementById('err').style.display"),flush=True)
print('ERRTXT:',js("document.getElementById('err').innerText"),flush=True)
print('DONE',flush=True)
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
