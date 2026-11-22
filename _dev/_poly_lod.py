# -*- coding: utf-8 -*-
"""B1 验证：正60面体「每面花盘密度 LOD」rich / one 两档。
   指标：花盘株数、底盘锥数、生效芽数、总锥数、已长出=总数（零截断）、导出非空。
   同时各出一张正面图 + 一张特写，肉眼核对"花盘是否变清晰、有没有露灰。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9441; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_lod_9441')
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
  for k in range(1,13):
    call('Input.dispatchMouseEvent',{'type':'mouseMoved','x':x1+(x2-x1)*k/12,'y':y1+(y2-y1)*k/12,'button':'left','buttons':1})
  call('Input.dispatchMouseEvent',{'type':'mouseReleased','x':x2,'y':y2,'button':'left','buttons':0,'clickCount':1})
def wheel(x,y,dy):call('Input.dispatchMouseEvent',{'type':'mouseWheel','x':x,'y':y,'deltaX':0,'deltaY':dy})
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
js("var e=document.getElementById('preset');e.value='bucky';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(4)

def setdens(v):
  js("var e=document.getElementById('polyDens');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));"%v)
  time.sleep(5.5)

for v in ['rich','one']:
  setdens(v)
  hud=js("document.getElementById('hudBody').innerText")
  poly=js("JSON.stringify(window.__poly())")
  axis=js("JSON.stringify(window.__axis())")
  tile=js("JSON.stringify(window.__tile())")
  err=js("document.getElementById('err').style.display")
  d=json.loads(poly or '{}'); a=json.loads(axis or '{}'); ti=json.loads(tile or '{}')
  print('--- polyDens=%s ---'%v,flush=True)
  print('  flowers=%s cones=%s budsEff=%s tileScMax=%s'%(d.get('flowers'),d.get('cones'),
        js("String(S.upBudsEff)"), round(ti.get('scMax') or 0,4)),flush=True)
  print('  axis: count=%s minY=%.3f neg=%s'%(a.get('count'),a.get('minY') or 0,a.get('neg')),flush=True)
  print('  hud:',hud.replace('\n',' | ')[:180],flush=True)
  print('  err=',err,flush=True)
  # 导出非空
  exp=js("""(function(){try{
      var t0=performance.now();var n=window.__exporters.stl();
      return JSON.stringify({n:n,ms:Math.round(performance.now()-t0)});
    }catch(e){return 'ERR:'+e.message;}})()""")
  print('  stl:',exp,flush=True)
  shot('../预览_LOD_%s_正面.png'%v,{'x':330,'y':100,'width':490,'height':490,'scale':1.3})
  wheel(560,340,-260);time.sleep(1.2)
  shot('../预览_LOD_%s_特写.png'%v,{'x':330,'y':100,'width':490,'height':490,'scale':1.3})
  wheel(560,340,260);time.sleep(0.8)
print('DONE',flush=True)
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
