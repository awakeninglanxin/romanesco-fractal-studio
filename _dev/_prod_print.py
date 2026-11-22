# -*- coding: utf-8 -*-
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9463; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_pp_9463')
CHROME=r"C:/Program Files/Google/Chrome/Application/chrome.exe"
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
t=targets();ws=websocket.create_connection(t['webSocketDebuggerUrl'],timeout=600,suppress_origin=True)
mid=[0]
def call(m,p=None):
  mid[0]+=1;n=mid[0];ws.send(json.dumps({'id':n,'method':m,'params':p or {}}))
  while True:
    r=json.loads(ws.recv())
    if r.get('id')==n:return r
def js(e):return call('Runtime.evaluate',{'expression':e,'returnByValue':True}).get('result',{}).get('result',{}).get('value')
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
# 生产页：不带 ?debug=1
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
print('debug hooks (should be undefined):',js("typeof window.__printRun"),js("typeof window.__exporters"),flush=True)
# 1) 点真实按钮
js("document.getElementById('btnPrint').click()")
time.sleep(9)
print('printInfo:',js("document.getElementById('printInfo').innerText"),flush=True)
print('busy hidden:',js("document.getElementById('busy').className"),flush=True)
# 2) 正60面体 LOD 下拉真实交互
js("var e=document.getElementById('preset');e.value='bucky';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(7)
print('polyDensRow display:',js("document.getElementById('polyDensRow').style.display"),flush=True)
js("var e=document.getElementById('polyDens');e.value='one';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(8)
print('LOD=one hud:',js("document.getElementById('hudBody').innerText").replace('\n',' | ')[:160],flush=True)
# 3) 五边形算法下拉真实交互（切到 ifs3d 并截图）
js("var e=document.getElementById('preset');e.value='pent';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(6)
print('pentAlgoRow display:',js("document.getElementById('pentAlgoRow').style.display"),
      'pentSolidRow:',js("document.getElementById('pentSolidRow').style.display"),flush=True)
js("var e=document.getElementById('pentAlgo');e.value='ifs3d';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(8)
print('ifsNRow:',js("document.getElementById('ifsNRow').style.display"),
      'pentSolidRow:',js("document.getElementById('pentSolidRow').style.display"),flush=True)
print('pent hud:',js("document.getElementById('hudBody').innerText").replace('\n',' | ')[:170],flush=True)
print('ERR:',js("document.getElementById('err').style.display"),flush=True)
d=call('Page.captureScreenshot',{'format':'png'})['result']['data']
open('../预览_五边形_IFS花盘山_成品.png','wb').write(base64.b64decode(d));print('SHOT ok',flush=True)
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
