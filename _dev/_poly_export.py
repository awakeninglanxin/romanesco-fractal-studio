# -*- coding: utf-8 -*-
"""正60面体导出非空 + 三角面数（STL/OBJ/PLY）。"""
import time, os, json, subprocess, urllib.request, urllib.parse
import websocket
PORT=9430; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_pexp_9430')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1100,800','--hide-scrollbars',
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
def js(e,awaitp=False):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':awaitp}).get('result',{}).get('result',{}).get('value')
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
js("var e=document.getElementById('preset');e.value='bucky';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(3)
EXPR="""(async()=>{
  window.__blobs=[];if(!window.__hooked){var _o=URL.createObjectURL;URL.createObjectURL=function(b){window.__blobs.push(b.size);return _o.apply(this,arguments);};window.__hooked=true;}
  var out=[];for(var f of ['stl','obj','ply']){window.__blobs=[];window.__exporters[f]();out.push(window.__blobs.length?window.__blobs[0]:0);}
  return JSON.stringify(out);
})()"""
print('bucky exports:',js(EXPR,awaitp=True),flush=True)
print('ERR:',js("document.getElementById('err').style.display"),flush=True)
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE',flush=True)
