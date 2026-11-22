# -*- coding: utf-8 -*-
"""遍历 7 预设：确认底面暴露新策略(倒挂删/近水平扶正)不破坏任何形态、零 JS 错误。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9401; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_cullall_9401')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1400,900','--hide-scrollbars',
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
opts=json.loads(js("JSON.stringify(Array.from(document.getElementById('preset').options).map(o=>o.value))"))
print('presets:',opts)
EXPR="""(async()=>{
  window.__blobs=[];if(!window.__hooked){var _o=URL.createObjectURL;URL.createObjectURL=function(b){window.__blobs.push(b.size);return _o.apply(this,arguments);};window.__hooked=true;}
  var out=[];for(var f of ['stl','obj','ply']){window.__blobs=[];window.__exporters[f]();out.push(window.__blobs.length?window.__blobs[0]:0);}
  return JSON.stringify(out);
})()"""
allok=True
for v in opts:
  js("var e=document.getElementById('preset');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));"%v)
  time.sleep(1.8)
  ax=js("JSON.stringify(window.__axis())")
  a=json.loads(ax)
  err=js("document.getElementById('err').style.display")
  exps=None
  if v in ('romanesco','cauliflower','broccoli'):
    exps=json.loads(js(EXPR,awaitp=True))
  ok=(err!='block') and (exps is None or all(x>0 for x in exps))
  allok=allok and ok
  print(('%-4s'%('OK' if ok else 'FAIL')),'%-12s'%v,'count=%s'%a.get('count'),'culled=%s'%a.get('culled'),
        'fixed=%s'%a.get('cullFixed'),'minY=%.3f'%a.get('minY'),'neg=%s'%a.get('neg'),
        ('exports=%s'%exps) if exps else '', 'err=%s'%err)
  if v in ('bucky','pent'):
    dat=call('Page.captureScreenshot',{'format':'png'})['result']['data']
    pth='../预览_扶正修复_'+v+'.png'; open(pth,'wb').write(base64.b64decode(dat)); print(' SHOT',pth)
print('RESULT:', 'ALL_PASS' if allok else 'HAS_FAIL')
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
