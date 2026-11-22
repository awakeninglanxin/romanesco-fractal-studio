# -*- coding: utf-8 -*-
"""品红判据：把五棱锥山体染成品红，数画布里的"露底像素"占比。
   对比 petal=2.0（原相切花盘）/ 1.70（新）/ fill 0..2，验证几何结论。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse, sys
import websocket
sys.path.insert(0,'.')
from _pngstat import magenta_stats

PORT=9475; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_pen_9475')
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
    if r.get('method')=='Runtime.exceptionThrown': ERR.append(json.dumps(r['params']['exceptionDetails'])[:200])
    if r.get('id')==n:return r
def js(e):
  r=call('Runtime.evaluate',{'expression':e,'returnByValue':True})
  if 'exceptionDetails' in r.get('result',{}): ERR.append(json.dumps(r['result']['exceptionDetails'])[:200])
  return r.get('result',{}).get('result',{}).get('value')
def shot(p,clip=None):
  par={'format':'png'}
  if clip:par['clip']=clip
  open(p,'wb').write(base64.b64decode(call('Page.captureScreenshot',par)['result']['data']))
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
js("window.__camSet(0.55,0.80,17)")
time.sleep(1.0)
box=js("(function(){var r=document.getElementById('cv').getBoundingClientRect();return {x:Math.round(r.x+60),y:Math.round(r.y+30),width:Math.round(r.width-120),height:Math.round(r.height-60)};})()")
print('clip',box)
js("window.__pyrColor(0xff00ff)")
time.sleep(0.6)

def measure(tag, opts):
    if opts: print(' set',js("JSON.stringify(window.__pentSet(%s))"%json.dumps(opts)))
    time.sleep(1.6)
    js("window.__pyrColor(0xff00ff)")   # 重建会换新材质 → 每次都要重新染
    time.sleep(0.9)
    p='../_dev/_mag_%s.png'%tag
    shot(p,dict(box,scale=1.0))
    st=magenta_stats(p,(0,0,box['width'],box['height']))
    d=js("JSON.stringify(window.__poly().ifs)")
    print('%-22s 品红像素 %6d / %6d = %5.2f%%   ifs=%s'%(tag,st['magenta'],st['total'],st['mag_pct'],d),flush=True)

import sys as _s
CFG={'A':('A_petal2.0',{'ifsPetal':2.0,'ifsDr':1.44,'ifsFill':2}),
     'B':('B_petal1.85',{'ifsPetal':1.85,'ifsDr':1.44,'ifsFill':2}),
     'C':('C_petal1.70',{'ifsPetal':1.70,'ifsDr':1.44,'ifsFill':2}),
     'D':('D_fill0',{'ifsPetal':1.70,'ifsDr':1.44,'ifsFill':0}),
     'E':('E_N40',{'ifsPetal':1.70,'ifsDr':1.44,'ifsFill':2,'ifsN':40}),
     'F':('F_N160',{'ifsPetal':1.70,'ifsDr':1.44,'ifsFill':2,'ifsN':160})}
for k in (_s.argv[1] if len(_s.argv)>1 else 'ABCDEF'):
    measure(CFG[k][0],CFG[k][1])
print('ERR',ERR[:4] if ERR else 'none')
proc.terminate()
