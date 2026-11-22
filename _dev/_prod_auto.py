# -*- coding: utf-8 -*-
"""生产模式（无 ?debug=1）冒烟：切换预设 → 点一键最优 → 读结果行，确认无报错"""
import time, os, json, subprocess, urllib.request, urllib.parse, base64
import websocket
PORT=9509; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_prod_9509')
CHROME=r"C:/Program Files/Google/Chrome/Application/chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
 '--enable-unsafe-swiftshader','--window-size=1200,900','--allow-file-access-from-files',
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
t=tgt(); ws=websocket.create_connection(t['webSocketDebuggerUrl'],timeout=300,suppress_origin=True)
mid=[0]; ERR=[]
def call(m,p=None):
  mid[0]+=1;n=mid[0];ws.send(json.dumps({'id':n,'method':m,'params':p or {}}))
  while True:
    r=json.loads(ws.recv())
    if r.get('method')=='Runtime.exceptionThrown': ERR.append(json.dumps(r['params']['exceptionDetails'])[:240])
    if r.get('id')==n:return r
def js(e):
  r=call('Runtime.evaluate',{'expression':e,'returnByValue':True})
  if 'exceptionDetails' in r.get('result',{}): ERR.append(json.dumps(r['result']['exceptionDetails'])[:240])
  return r.get('result',{}).get('result',{}).get('value')
call('Page.enable');call('Runtime.enable')
base=os.path.abspath('..').replace('\\','/')
call('Page.navigate',{'url':'file:///'+base+'/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.4)
time.sleep(1.0)
print('DEBUG hook (应为 undefined):',js("typeof window.__autoTune"))
for pv in ('upright','bucky','pent','romanesco'):
  js("var e=document.getElementById('preset');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));"%pv)
  time.sleep(2.2 if pv in ('bucky','pent') else 1.6)
  js("document.getElementById('btnAuto').click()")
  time.sleep(2.5)
  for _ in range(12):
    if js("!document.getElementById('btnAuto').disabled"):break
    time.sleep(0.6)
  note=(js("document.getElementById('autoNote').innerText") or '').replace('\n',' | ')
  print('%-10s %s'%(pv,note[:150]))
print('JS ERRORS:',len(ERR))
for e in ERR[:5]:print('  ',e)
proc.terminate()
