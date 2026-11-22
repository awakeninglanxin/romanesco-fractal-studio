# -*- coding: utf-8 -*-
"""轻量导出验证：默认金字塔+自动填满状态下4格式非空。"""
import time, os, json, subprocess, urllib.request, urllib.parse
import websocket
PORT=9368; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_expq_9368')
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
t=targets();ws=websocket.create_connection(t['webSocketDebuggerUrl'],timeout=180,suppress_origin=True)
mid=[0]
def call(m,p=None):
  mid[0]+=1;n=mid[0];ws.send(json.dumps({'id':n,'method':m,'params':p or {}}))
  while True:
    r=json.loads(ws.recv())
    if r.get('id')==n:return r
def js(e):return call('Runtime.evaluate',{'expression':e,'returnByValue':True}).get('result',{}).get('result',{}).get('value')
call('Page.enable');call('Runtime.enable')
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
js("window.__blobs=[];var _o=URL.createObjectURL;URL.createObjectURL=function(b){window.__blobs.push(b.size);return _o.apply(this,arguments);};")
# 直接调导出函数（绕过UI，避免STEP生成时UI阻塞）
for f in ['stl','obj','ply','step']:
  call('Runtime.evaluate',{'expression':"window.__exporters.%s()"%f,'awaitPromise':False})
  time.sleep(2)
  print(f,'blobs:',js("JSON.stringify(window.__blobs)"))
print('ERR:',js("document.getElementById('err').style.display"))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
