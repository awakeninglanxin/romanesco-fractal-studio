# -*- coding: utf-8 -*-
"""验证：切换任意形态预设后，生长进度默认 100%。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9387; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_prog_9387')
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
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
opts=js("JSON.stringify(Array.from(document.getElementById('preset').options).map(o=>({v:o.value,t:o.textContent})))")
opts=json.loads(opts)
print('打开默认:',js("document.getElementById('preset').value"),'prog=',js("document.getElementById('prog').value"),'label=',js("document.getElementById('vProg').textContent"))
allok=True
for o in opts:
  v=o['v']
  js("var e=document.getElementById('preset');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));"%v)
  time.sleep(1.6)
  pv=js("document.getElementById('prog').value"); lab=js("document.getElementById('vProg').textContent")
  err=js("document.getElementById('err').style.display")
  ok=(str(pv)=='1000' and str(lab)=='100%' and err!='block')
  allok=allok and ok
  print(('%-4s'%('OK' if ok else 'FAIL')),'%-14s'%v, o['t'][:16],'prog=',pv,'label=',lab,'err=',err)
print('ERR_FINAL:',js("document.getElementById('err').style.display"))
print('RESULT:', 'ALL_PASS' if allok else 'HAS_FAIL')
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
