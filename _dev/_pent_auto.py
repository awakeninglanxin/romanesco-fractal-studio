# -*- coding: utf-8 -*-
"""五棱锥花盘山：一键最优铺满 —— 数值验收 + 截图"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse, sys
import websocket

PORT=9471; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_pen_9471')
CHROME=r"C:/Program Files/Google/Chrome/Application/chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1400,1000','--hide-scrollbars',
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
    if r.get('method')=='Runtime.exceptionThrown':
      ERR.append(json.dumps(r['params']['exceptionDetails'])[:400])
    if r.get('method')=='Runtime.consoleAPICalled' and r['params'].get('type')=='error':
      ERR.append(str(r['params']['args'])[:300])
    if r.get('id')==n:return r
def js(e):
  r=call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True})
  if 'exceptionDetails' in r.get('result',{}):
    ERR.append(json.dumps(r['result']['exceptionDetails'])[:400])
  return r.get('result',{}).get('result',{}).get('value')
def shot(p,clip=None):
  par={'format':'png'}
  if clip:par['clip']=clip
  d=call('Page.captureScreenshot',par)['result']['data']
  open(p,'wb').write(base64.b64decode(d)); print('SHOT',p,flush=True)

call('Page.enable');call('Runtime.enable');call('Network.enable')
call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(90):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(1.5)
js("var e=document.getElementById('preset');e.value='pent';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(1.2)
js("var e=document.getElementById('pentAlgo');e.value='ifs3d';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(6)
print('--- 旧参数（默认 N=80）---')
print(json.dumps(js("window.__pent().ifs"),ensure_ascii=False))
print('HUD:',js("document.getElementById('hudBody').innerText").replace('\n',' | ')[:400])

# 相机：俯视 + 斜视
js("window.__camSet&&window.__camSet(0.02,0.02,15)")
time.sleep(1)
shot('../预览_铺满_俯视.png')
js("window.__camSet&&window.__camSet(0.7,0.62,15)")
time.sleep(1)
shot('../预览_铺满_斜视.png')

# 一键最优
t0=time.time()
js("document.getElementById('btnPentAuto').click()")
time.sleep(8)
print('--- 一键最优后 ---')
print(json.dumps(js("window.__pent().ifs"),ensure_ascii=False))
print('NOTE:',js("document.getElementById('ifsAutoNote').innerText").replace('\n',' | '))
print('HUD:',js("document.getElementById('hudBody').innerText").replace('\n',' | ')[:400])
print('耗时 %.1fs'%(time.time()-t0))
js("window.__camSet&&window.__camSet(0.02,0.02,15)"); time.sleep(1)
shot('../预览_最优_俯视.png')
js("window.__camSet&&window.__camSet(0.7,0.62,15)"); time.sleep(1)
shot('../预览_最优_斜视.png')
# 画布特写（按 getBoundingClientRect 裁剪）
box=js("(function(){var r=document.getElementById('cv').getBoundingClientRect();return {x:r.x+80,y:r.y+40,width:r.width-160,height:r.height-80};})()")
shot('../预览_最优_特写.png',dict(box,scale=1.8))
print('ERRORS:',ERR[:5] if ERR else 'none')
proc.terminate()
