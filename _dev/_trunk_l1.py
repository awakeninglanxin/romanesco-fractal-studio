# -*- coding: utf-8 -*-
"""复现老师图1：西兰花 levels=1，trunkBase 开/关对比。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9488
PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_trunkl1_9488')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
 '--enable-unsafe-swiftshader','--window-size=1602,1002','--hide-scrollbars',
 '--remote-debugging-port=%d'%PORT,'--user-data-dir='+PROFILE,'about:blank'],
 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def wait():
 for _ in range(100):
  try:
   tabs=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list'%PORT,timeout=1))
   p=[t for t in tabs if t['type']=='page']
   if p:return p[0]
  except:pass
  time.sleep(0.4)
 raise RuntimeError('no devtools')
tab=wait();ws=websocket.create_connection(tab['webSocketDebuggerUrl'],timeout=300,suppress_origin=True)
def call(m,p=None):
 ws.send(json.dumps({'id':1,'method':m,'params':p or {}}))
 while True:
  msg=json.loads(ws.recv())
  if msg.get('id')==1:return msg
def js(e):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('result',{}).get('value')
def setv(i,v,ev='input'):js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()"%(i,json.dumps(str(v)),ev))
def toggle(i,v):js("(function(){var e=document.getElementById('%s');e.checked=%s;e.dispatchEvent(new Event('change',{bubbles:true}));})()"%(i,'true' if v else 'false'))
def shot(p):
 d=call('Page.captureScreenshot',{'format':'png','clip':{'x':150,'y':150,'width':700,'height':550,'scale':1}})['result']['data']
 open(p,'wb').write(base64.b64decode(d));print('SHOT',p,os.path.getsize(p))
call('Page.enable');call('Runtime.enable')
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(120):
 if js("document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"):break
 time.sleep(0.5)
time.sleep(1.5)
setv('preset','broccoli','change');time.sleep(1.2)
setv('levels',1);time.sleep(1.2)
setv('prog',1000);time.sleep(1.0)
toggle('trunkBase',False);time.sleep(1.0);shot('_dev/trunk_l1_off.png')
toggle('trunkBase',True);time.sleep(1.0);shot('_dev/trunk_l1_on.png')
sp=subprocess;sp.Popen(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=sp.DEVNULL,stderr=sp.DEVNULL)
