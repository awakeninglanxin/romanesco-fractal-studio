# -*- coding: utf-8 -*-
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9459; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_ui_9459')
CHROME=r"C:/Program Files/Google/Chrome/Application/chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1400,1000','--hide-scrollbars',
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
t=targets();ws=websocket.create_connection(t['webSocketDebuggerUrl'],timeout=600,suppress_origin=True)
mid=[0]
def call(m,p=None):
  mid[0]+=1;n=mid[0];ws.send(json.dumps({'id':n,'method':m,'params':p or {}}))
  while True:
    r=json.loads(ws.recv())
    if r.get('id')==n:return r
def js(e):return call('Runtime.evaluate',{'expression':e,'returnByValue':True}).get('result',{}).get('result',{}).get('value')
def shot(p,clip=None):
  par={'format':'png'}
  if clip:par['clip']=clip
  d=call('Page.captureScreenshot',par)['result']['data']
  open(p,'wb').write(base64.b64decode(d));print('SHOT',p,flush=True)
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
js("var e=document.getElementById('preset');e.value='pent';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(4)
js("var e=document.getElementById('pentAlgo');e.value='ifs';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(5)
js("document.getElementById('pentAlgoRow').scrollIntoView({block:'center'})")
time.sleep(1.2)
shot('../预览_UI_五边形IFS选项.png',{'x':860,'y':120,'width':400,'height':520,'scale':1.6})
js("var e=document.getElementById('pentAlgo');e.value='ifs3d';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(7)
shot('../预览_UI_五边形IFS花盘山.png',{'x':860,'y':120,'width':400,'height':560,'scale':1.6})
js("document.getElementById('btnPrint').scrollIntoView({block:'center'})")
time.sleep(1.0)
shot('../预览_UI_水密导出区.png',{'x':860,'y':120,'width':400,'height':520,'scale':1.6})
print('DIAG:',js("JSON.stringify({algo:S.pentAlgo,rows:[document.getElementById('ifsDepthRow').style.display,document.getElementById('ifsNRow').style.display,document.getElementById('pentSolidRow').style.display]})"),flush=True)
print('ERR:',js("document.getElementById('err').style.display"),flush=True)
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
