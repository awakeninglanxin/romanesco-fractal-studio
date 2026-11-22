# -*- coding: utf-8 -*-
"""验证扩大一圈按钮序列 + 底盘六边形 + 补株默认1.00 + 相机保持。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9401; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_ring_9401')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1530,982','--hide-scrollbars',
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
  d=call('Page.captureScreenshot',{'format':'png'})['result']['data'];open(p,'wb').write(base64.b64decode(d));print('SHOT',p,os.path.getsize(p))
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && window.__cam && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
def setv(id,val,ev):js("var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));"%(id,json.dumps(str(val)),ev))
def click(id):js("document.getElementById('%s').click();"%id)
def camstate():return js("JSON.stringify({t:window.__cam.theta(),p:window.__cam.phi(),r:window.__cam.radius()})")
print('FILLK:',js("document.getElementById('vFillK').textContent"))
# 按钮序列（先设 upN=1）
setv('upN',1,'input');time.sleep(0.5)
seq=[]
for i in range(8):
  seq.append(js("document.getElementById('upN').value"))
  click('btnGrowRing');time.sleep(0.7)
print('RING_SEQ:',seq)
print('ERR:',js("document.getElementById('err').style.display"))
# 相机保持验证
base=camstate();click('btnGrowRing');time.sleep(0.6)
print('CAM_SAME_AFTER_RING:',camstate()==base,base,camstate())
# 底盘六边形预览：设回19，俯视
setv('upN',19,'input');time.sleep(1)
js("document.getElementById('btnTop').click()");time.sleep(1)
shot('预览_标准六边形底盘.png')
print('HUD:',js("document.getElementById('hudBody').innerText").replace('\n',' | '))
# 大upN压力测试 127
setv('upN',127,'input');time.sleep(3)
print('HUD127:',js("document.getElementById('hudBody').innerText").replace('\n',' | '))
print('ERR127:',js("document.getElementById('err').style.display"))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
