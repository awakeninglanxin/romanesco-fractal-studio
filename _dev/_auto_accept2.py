# -*- coding: utf-8 -*-
"""一键最优（四类形态）：7 预设 × 点按钮 → 读结果行 / 覆盖率 / JS 错误 / 截图"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse, sys
import websocket
PORT=9505; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_auto_9505')
CHROME=r"C:/Program Files/Google/Chrome/Application/chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1400,1000','--hide-scrollbars',
  '--allow-file-access-from-files',
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
    if r.get('method')=='Runtime.exceptionThrown': ERR.append(json.dumps(r['params']['exceptionDetails'])[:300])
    if r.get('id')==n:return r
def js(e):
  r=call('Runtime.evaluate',{'expression':e,'returnByValue':True})
  if 'exceptionDetails' in r.get('result',{}): ERR.append(json.dumps(r['result']['exceptionDetails'])[:300])
  return r.get('result',{}).get('result',{}).get('value')
def shot(p):
  open(p,'wb').write(base64.b64decode(call('Page.captureScreenshot',{'format':'png'})['result']['data'])); print('SHOT',p,flush=True)
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
base=os.path.abspath('..')
url='file:///'+base.replace('\\','/')+'/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.4)
time.sleep(1.2)
print('LOADED\nDEBUG hooks:',js("typeof window.__autoTune"))
print('URL:',js("location.href")[:90],'| search:',js("location.search"))

def preset(pv,algo=None,wait=1.6):
  js("var e=document.getElementById('preset');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));"%pv)
  time.sleep(wait)
  if algo:
    js("var e=document.getElementById('pentAlgo');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));"%algo)
    time.sleep(wait)

def run_auto(tag,shot_path=None):
  t0=time.time()
  js("document.getElementById('btnAuto').click()")
  time.sleep(2.2)
  for _ in range(10):
    if js("!document.getElementById('btnAuto').disabled"):break
    time.sleep(0.5)
  dt=time.time()-t0
  note=js("document.getElementById('autoNote').innerText") or ''
  note=' | '.join([n for n in note.split('\n') if n.strip()])
  hud=js("document.getElementById('hudBody').innerText") or ''
  print('%-22s %5.2fs  %s'%(tag,dt,note[:300]))
  print('%-22s        HUD: %s'%('',hud.split('\n')[0][:120]))
  if shot_path: shot(shot_path)
  return note

js("window.__camSet&&window.__camSet(0.02,0.03,16)")
for pv in ('romanesco','cauliflower','broccoli','upright','xmas','bucky','pent'):
  preset(pv, wait=2.2 if pv in ('bucky','pent') else 1.6)
  run_auto(pv, os.path.join(os.path.dirname(__file__),'..','预览_一键_%s.png'%pv))
# 五边形三种底层算法
for algo in ('tangent','ifs'):
  preset('pent',algo,2.0)
  run_auto('pent·'+algo, os.path.join(os.path.dirname(__file__),'..','预览_一键_pent_%s.png'%algo))
preset('pent','ifs3d',2.2)
run_auto('pent·ifs3d', os.path.join(os.path.dirname(__file__),'..','预览_一键_pent_ifs3d.png'))
print('JS ERRORS:',len(ERR))
for e in ERR[:6]: print('  ',e)
proc.terminate()
