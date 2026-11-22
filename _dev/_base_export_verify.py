# -*- coding: utf-8 -*-
"""验证落地盘贴合改动后，三种 grow 形态导出非空 + 零 JS 错误。
用页面内异步 IIFE 同步导出三格式后一次性回传 blob 大小数组，避免 CDP 调用排队误报。"""
import time, os, json, subprocess, urllib.request, urllib.parse
import websocket
PORT=9396; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_baseexp_9396')
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
def js(e,awaitp=False):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':awaitp}).get('result',{}).get('result',{}).get('value')
call('Page.enable');call('Runtime.enable')
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
EXPR="""(async()=>{
  window.__blobs=[];if(!window.__hooked){var _o=URL.createObjectURL;URL.createObjectURL=function(b){window.__blobs.push(b.size);return _o.apply(this,arguments);};window.__hooked=true;}
  var out=[];
  for(var f of ['stl','obj','ply']){window.__blobs=[];window.__exporters[f]();out.push(window.__blobs.slice());}
  return JSON.stringify(out);
})()"""
for preset in ['romanesco','cauliflower','broccoli']:
  js("var e=document.getElementById('preset');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));"%preset)
  time.sleep(1.6)
  raw=js(EXPR,awaitp=True)
  groups=json.loads(raw)
  flat=[g[0] if g else 0 for g in groups]
  ok=len(flat)==3 and all(x>0 for x in flat)
  print(('OK' if ok else 'FAIL'),preset,'blob_sizes=',flat,'base=',js("JSON.stringify(window.__base())"))
print('ERR:',js("document.getElementById('err').style.display"))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
