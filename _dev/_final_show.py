# -*- coding: utf-8 -*-
"""最终成品图：upright 配色 + bucky lv=3 近距特写（看每株从里到外的渐变）"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9439; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_fs_9439')
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

call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)

# 直立花盘：看每株"从里到外"的同心环
js("var e=document.getElementById('preset');e.value='upright';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(5)
shot('../预览_成品_直立花盘_生长渐变.png',{'x':300,'y':90,'width':560,'height':560,'scale':1.25})

# 正60面体 lv=3：近距特写
js("var e=document.getElementById('preset');e.value='bucky';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(6)
wheel(600,420,-820); time.sleep(1.4)
shot('../预览_成品_正60面体_近距.png',{'x':320,'y':80,'width':540,'height':540,'scale':1.4})
print('ERR:',js("document.getElementById('err').style.display"),flush=True)
print('DONE',flush=True)
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
