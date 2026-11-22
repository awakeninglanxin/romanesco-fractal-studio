# -*- coding: utf-8 -*-
"""品红判据：把底砖染成自发光品红，数画布上"露底像素"占比。
   对照 默认参数 vs 一键最优，各三个视角。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse, sys
import websocket
sys.path.insert(0,os.path.dirname(__file__))
from _pngstat import read_png

PORT=9498; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_magp_9498')
CHROME=r"C:/Program Files/Google/Chrome/Application/chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1200,900','--hide-scrollbars','--allow-file-access-from-files',
  '--remote-debugging-port=%d'%PORT,'--user-data-dir='+PROFILE,'about:blank'],
  stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def tgt():
  for _ in range(60):
    try:
      ts=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list'%PORT,timeout=1))
      p=[t for t in ts if t['type']=='page']
      if p:return p[0]
    except Exception:pass
    time.sleep(0.4)
t=tgt(); ws=websocket.create_connection(t['webSocketDebuggerUrl'],timeout=600,suppress_origin=True)
mid=[0]; ERR=[]
def call(m,p=None):
  mid[0]+=1;n=mid[0];ws.send(json.dumps({'id':n,'method':m,'params':p or {}}))
  while True:
    r=json.loads(ws.recv())
    if r.get('method')=='Runtime.exceptionThrown': ERR.append(json.dumps(r['params']['exceptionDetails'])[:200])
    if r.get('id')==n:return r
def js(e):
  r=call('Runtime.evaluate',{'expression':e,'returnByValue':True})
  if 'exceptionDetails' in r.get('result',{}): ERR.append(json.dumps(r['result']['exceptionDetails'])[:200])
  return r.get('result',{}).get('result',{}).get('value')
def shot(p):
  open(p,'wb').write(base64.b64decode(call('Page.captureScreenshot',{'format':'png'})['result']['data'])); return p

def mag_pct(path):
  w,h,ch,px=read_png(path); mag=0; tot=0
  for y in range(0,h,2):
    for x in range(0,w,2):
      i=(y*w+x)*ch
      r,g,b=px[i],px[i+1],px[i+2]
      # 画布背景是深色渐变，山体/砖是品红(255,0,255)
      if r>200 and b>200 and g<60:
        mag+=1
      if r+g+b>60: tot+=1
  return 100.0*mag/max(1,tot)

call('Page.enable');call('Runtime.enable')
base=os.path.abspath('..').replace('\\','/')
call('Page.navigate',{'url':'file:///'+base+'/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.4)
time.sleep(1.2)
OUT=os.path.join(base,'_dev')
VIEWS=[(0.62,0.86,13),(2.1,1.05,13)]
def setp(pv,algo=None):
  js("var e=document.getElementById('preset');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));"%pv)
  time.sleep(2.0)
  if algo:
    js("var e=document.getElementById('pentAlgo');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));"%algo)
    time.sleep(2.0)
def measure(tag):
  tot=[]
  for vi,(th,ph,r) in enumerate(VIEWS):
    js("window.__camSet&&window.__camSet(%f,%f,%f)"%(th,ph,r)); time.sleep(0.6)
    js("window.__baseColor&&window.__baseColor(0xff00ff)"); time.sleep(0.25)
    p=shot(os.path.join(OUT,'_mag_%s_%d.png'%(tag,vi)))
    v=mag_pct(p); tot.append(v)
  print('  %-18s 露底%%: %s'%(tag,' '.join('%.3f'%v for v in tot)),flush=True)
  return tot

for pv in ('bucky',):
  setp(pv, 'tangent' if pv=='pent' else None)
  print('==',pv)
  measure(pv+'_default')
  js("document.getElementById('btnAuto').click()")
  time.sleep(4.0)
  for _ in range(12):
    if js("!document.getElementById('btnAuto').disabled"):break
    time.sleep(0.6)
  print('  note:',(js("document.getElementById('autoNote').innerText") or '').split('\n')[0][:90])
  measure(pv+'_auto')
print('ERR',len(ERR))
proc.terminate()
