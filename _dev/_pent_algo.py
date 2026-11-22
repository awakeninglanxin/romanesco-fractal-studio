# -*- coding: utf-8 -*-
"""正五边形三种底层算法验证：tangent / ifs / ifs3d
   指标：花盘数、锥数、已长出=总数、导出非空、JS 错误；各出一张俯视/斜视截图。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9447; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_pentalgo_9447')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
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
def js(e,awaitp=False):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':awaitp}).get('result',{}).get('result',{}).get('value')
def shot(p,clip=None):
  par={'format':'png'}
  if clip:par['clip']=clip
  d=call('Page.captureScreenshot',par)['result']['data']
  open(p,'wb').write(base64.b64decode(d));print('SHOT',p,flush=True)
def drag(x1,y1,x2,y2):
  call('Input.dispatchMouseEvent',{'type':'mousePressed','x':x1,'y':y1,'button':'left','buttons':1,'clickCount':1})
  for k in range(1,10):
    call('Input.dispatchMouseEvent',{'type':'mouseMoved','x':x1+(x2-x1)*k/10,'y':y1+(y2-y1)*k/10,'button':'left','buttons':1})
  call('Input.dispatchMouseEvent',{'type':'mouseReleased','x':x2,'y':y2,'button':'left','buttons':0,'clickCount':1})
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
js("var e=document.getElementById('preset');e.value='pent';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(4)

def probe(tag):
  d=json.loads(js("JSON.stringify(window.__poly())") or '{}')
  hud=js("document.getElementById('hudBody').innerText").replace('\n',' | ')
  err=js("document.getElementById('err').style.display")
  exp=js("""(function(){try{var t0=performance.now();var n=window.__exporters.stl();
     return JSON.stringify({n:n,ms:Math.round(performance.now()-t0)});}catch(e){return 'ERR:'+e.message;}})()""")
  print('=== %s ==='%tag)
  print('  flowers=%s cones=%s ifs=%s'%(d.get('flowers'),d.get('cones'),json.dumps(d.get('ifs'),ensure_ascii=False)))
  print('  hud:',hud[:200])
  print('  stl:',exp,' err=',err)
  return d

case=js
# 1) tangent
probe('tangent')
shot('../预览_五边形_tangent.png',{'x':300,'y':90,'width':520,'height':520,'scale':1.25})
# 2) ifs depth 2 center on
js("var e=document.getElementById('pentAlgo');e.value='ifs';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(6)
probe('ifs d=2 center')
shot('../预览_五边形_ifs_d2.png',{'x':300,'y':90,'width':520,'height':520,'scale':1.25})
# 3) ifs depth 1
js("var e=document.getElementById('ifsDepth');e.value=1;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(5)
probe('ifs d=1')
shot('../预览_五边形_ifs_d1.png',{'x':300,'y':90,'width':520,'height':520,'scale':1.25})
js("var e=document.getElementById('ifsDepth');e.value=2;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(5)
# 4) ifs3d
js("var e=document.getElementById('pentAlgo');e.value='ifs3d';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(7)
probe('ifs3d N=60')
shot('../预览_五边形_ifs3d_俯视.png',{'x':300,'y':90,'width':520,'height':520,'scale':1.25})
drag(560,330,560,240)
time.sleep(1.5)
shot('../预览_五边形_ifs3d_斜视.png',{'x':300,'y':90,'width':520,'height':520,'scale':1.25})
print('DONE',flush=True)
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
