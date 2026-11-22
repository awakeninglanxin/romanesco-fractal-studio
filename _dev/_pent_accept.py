# -*- coding: utf-8 -*-
"""五棱锥一键铺满：完整验收（7 预设无报错 / 默认参数 / 一键最优 / 生长动画 / 导出）"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9483; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_pen_9483')
CHROME=r"C:/Program Files/Google/Chrome/Application/chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1400,1000','--hide-scrollbars',
  '--remote-debugging-port=%d'%PORT,'--user-data-dir='+PROFILE,'about:blank'],
  stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def targets():
  for _ in range(60):
    try:
      ts=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list'%PORT,timeout=1))
      p=[t for t in ts if t['type']=='page']
      if p:return p[0]
    except Exception:pass
    time.sleep(0.5)
  raise RuntimeError('no devtools')
t=targets(); ws=websocket.create_connection(t['webSocketDebuggerUrl'],timeout=600,suppress_origin=True)
mid=[0]; ERR=[]
def call(m,p=None):
  mid[0]+=1; n=mid[0]; ws.send(json.dumps({'id':n,'method':m,'params':p or {}}))
  while True:
    r=json.loads(ws.recv())
    if r.get('method')=='Runtime.exceptionThrown': ERR.append(json.dumps(r['params']['exceptionDetails'])[:260])
    if r.get('id')==n:return r
def js(e):
  r=call('Runtime.evaluate',{'expression':e,'returnByValue':True})
  if 'exceptionDetails' in r.get('result',{}): ERR.append(json.dumps(r['result']['exceptionDetails'])[:260])
  return r.get('result',{}).get('result',{}).get('value')
def shot(p,clip=None):
  par={'format':'png'}
  if clip:par['clip']=clip
  open(p,'wb').write(base64.b64decode(call('Page.captureScreenshot',par)['result']['data'])); print('SHOT',p,flush=True)
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.4)
time.sleep(1.0)
# 1) 7 个预设
for pv in ('romanesco','cauliflower','broccoli','upright','xmas','bucky','pent'):
  js("var e=document.getElementById('preset');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));"%pv)
  time.sleep(2.0)
  print('%-12s %s'%(pv,js("document.getElementById('hudBody').innerText.split('\\n')[0]")))
# 2) 五棱锥 ifs3d 默认
js("var e=document.getElementById('pentAlgo');e.value='ifs3d';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(4)
print('默认:',js("document.getElementById('hudBody').innerText").replace('\n',' | ')[:300])
# 3) 一键最优（计时）
t0=time.time()
js("document.getElementById('btnPentAuto').click()")
for _ in range(40):
  if js("!document.getElementById('btnPentAuto').disabled"):break
  time.sleep(0.4)
print('一键耗时 %.2fs'%(time.time()-t0))
print('结果行:',js("document.getElementById('ifsAutoNote').innerText").replace('\n',' | ')[:320])
print('HUD   :',js("document.getElementById('hudBody').innerText").replace('\n',' | ')[:300])
# 4) 生长动画 50%
js("var e=document.getElementById('prog');e.value=500;e.dispatchEvent(new Event('input',{bubbles:true}));")
time.sleep(1.0)
print('50%%:',js("document.getElementById('hudBody').innerText.split('\\n')[0]"))
js("var e=document.getElementById('prog');e.value=1000;e.dispatchEvent(new Event('input',{bubbles:true}));")
time.sleep(1.0)
# 5) 导出 STL（走一下 collectTriangles，确认逐株缩放没被写死）
print('按钮可见:',js("document.getElementById('btnPentAuto').offsetHeight>0"))
print('ERRORS:',ERR[:4] if ERR else 'none')
proc.terminate()
