# -*- coding: utf-8 -*-
"""诊断：调发散角为何无反应。测 golden / dec36 两种模式下改 angle 的几何变化。"""
import time, os, json, subprocess, urllib.request, urllib.parse
import websocket, base64, hashlib
PORT=9389; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_ang_9389')
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
call('Page.enable');call('Runtime.enable');call('Page.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
def setv(id,val,ev):js("var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));"%(id,json.dumps(str(val)),ev))
# 几何指纹：取所有实例矩阵前若干个元素的和
FP="(function(){var s=0;try{var im=document.querySelector('canvas');return document.getElementById('hudBody').innerText;}catch(e){return e.message}})()"
def leafhash():
  return js("(function(){var im=window.__leaves;return document.getElementById('hudBody').innerText;})()")

for mode in ['golden','dec36']:
  setv('spiralMode',mode,'change');time.sleep(1)
  print('=== MODE',mode,'===')
  print(' spiralMode UI:',js("document.getElementById('spiralMode').value"))
  setv('angle',137.508,'input');time.sleep(0.8)
  a=js("document.getElementById('hudBody').innerText"); imgA=call('Page.captureScreenshot',{'format':'png'})['result']['data']
  setv('angle',111.885,'input');time.sleep(0.8)
  b=js("document.getElementById('hudBody').innerText"); imgB=call('Page.captureScreenshot',{'format':'png'})['result']['data']
  print(' angle label:',js("document.getElementById('vAngle').textContent"))
  print(' PIXEL_SAME?', imgA==imgB, 'lenA',len(imgA),'lenB',len(imgB))
  print(' A:',a.replace('\n',' | '))
  print(' B:',b.replace('\n',' | '))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
