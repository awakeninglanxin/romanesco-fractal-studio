# -*- coding: utf-8 -*-
"""五棱锥花盘山：高清截图 + 山体隐藏对照（分辨灰带成因）"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9473; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_pen_9473')
CHROME=r"C:/Program Files/Google/Chrome/Application/chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1500,1080','--hide-scrollbars',
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
t=targets(); ws=websocket.create_connection(t['webSocketDebuggerUrl'],timeout=900,suppress_origin=True)
mid=[0]; ERR=[]
def call(m,p=None):
  mid[0]+=1; n=mid[0]; ws.send(json.dumps({'id':n,'method':m,'params':p or {}}))
  while True:
    r=json.loads(ws.recv())
    if r.get('method')=='Runtime.exceptionThrown': ERR.append(json.dumps(r['params']['exceptionDetails'])[:300])
    if r.get('id')==n:return r
def js(e):
  r=call('Runtime.evaluate',{'expression':e,'returnByValue':True})
  if 'exceptionDetails' in r.get('result',{}): ERR.append(json.dumps(r['result']['exceptionDetails'])[:300])
  return r.get('result',{}).get('result',{}).get('value')
def shot(p,clip=None):
  par={'format':'png'}
  if clip:par['clip']=clip
  open(p,'wb').write(base64.b64decode(call('Page.captureScreenshot',par)['result']['data'])); print('SHOT',p,flush=True)
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(90):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(1.5)
js("var e=document.getElementById('preset');e.value='pent';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(1.0)
js("var e=document.getElementById('pentAlgo');e.value='ifs3d';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(6)
js("document.getElementById('btnPentAuto').click()")
time.sleep(6)
print('AUTO:',js("document.getElementById('ifsAutoNote').innerText").replace(chr(10),' | ')[:240])
js("window.__camSet&&window.__camSet(0.55,0.85,15)")
time.sleep(1.5)
box=js("(function(){var r=document.getElementById('cv').getBoundingClientRect();return {x:r.x+150,y:r.y+60,width:r.width-300,height:r.height-140};})()")
shot('../预览_铺满_高清.png',dict(box,scale=1.6))
js("window.__pyr&&window.__pyr(0)")
time.sleep(1.2)
shot('../预览_铺满_无山体.png',dict(box,scale=1.6))
js("window.__pyr&&window.__pyr(1)")
js("window.__camSet&&window.__camSet(0.02,0.02,15)")
time.sleep(1.2)
shot('../预览_铺满_顶视高清.png',dict(box,scale=1.6))
print('ERR',ERR[:4] if ERR else 'none')
proc.terminate()
