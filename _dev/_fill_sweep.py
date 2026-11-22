# -*- coding: utf-8 -*-
"""扫多个 upN（含非整环的 25/31）验证补株坐标判定恒为 2(边缘)/3(内部) 且零 JS 错误。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9414; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_fillsweep_9414')
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
js("var e=document.getElementById('preset');e.value='upright';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(1.5)
js("var c=document.getElementById('autoFill');c.checked=true;c.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(1.5)
CHECK="""(function(){var F=window.__fill(),d=F.d,rr=d/Math.sqrt(3),bad=0,dup=0,seen={},over=0;
 F.holes.forEach(function(h){var cnt=0;F.main.forEach(function(m){if(Math.hypot(m.x-h.x,m.z-h.z)<rr*1.02)cnt++;});
   if(h.edge?cnt!==2:cnt!==3)bad++;
   var k=(h.x.toFixed(3))+'_'+(h.z.toFixed(3));if(seen[k])dup++;seen[k]=1;
   if(Math.hypot(h.x,h.z)>1e9)over++;});
 return JSON.stringify({n:F.holes.length,i:F.fillInner,e:F.fillEdge,bad:bad,dup:dup});})()"""
print('%-6s %-7s %-6s %-6s %-5s %-4s %s'%('upN','total','inner','edge','bad','dup','err'))
allok=True
for upN in [1,2,3,4,7,10,12,19,25,31,37]:
  js("var s=document.getElementById('upN');s.value=%d;s.dispatchEvent(new Event('input',{bubbles:true}));"%upN)
  time.sleep(1.9)
  c=json.loads(js(CHECK));err=js("document.getElementById('err').style.display")
  ok=(c['bad']==0 and c['dup']==0 and err!='block');allok=allok and ok
  print('%-6d %-7d %-6d %-6d %-5d %-4d %s'%(upN,c['n'],c['i'],c['e'],c['bad'],c['dup'],'' if ok else 'FAIL err=%s'%err))
print('RESULT:','ALL_PASS' if allok else 'HAS_FAIL')
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
