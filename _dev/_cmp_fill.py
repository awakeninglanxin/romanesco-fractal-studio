# -*- coding: utf-8 -*-
"""对照：fill=0（纯格点）vs fill=2（含补缝），看"浅色带"是否由补缝小花盘造成"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse, sys
import websocket
PORT=9481; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_pen_9481')
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
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(1.2)
js("var e=document.getElementById('preset');e.value='pent';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(0.8)
js("var e=document.getElementById('pentAlgo');e.value='ifs3d';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(5)
js("window.__camSet(0.45,0.62,16)"); time.sleep(0.8)
box=js("(function(){var r=document.getElementById('cv').getBoundingClientRect();return {x:Math.round(r.x+110),y:Math.round(r.y+40),width:Math.round(r.width-220),height:Math.round(r.height-80)};})()")
for tag,opts in (('N40',{'ifsFill':2,'ifsN':40}),('N80',{'ifsFill':2,'ifsN':80}),('N160',{'ifsFill':2,'ifsN':160})):
    js("window.__pentSet(%s)"%json.dumps(opts)); time.sleep(1.8); js("window.__camSet(0.45,0.62,16)"); time.sleep(0.8)
    shot('../_dev/_cmp_%s.png'%tag,dict(box,scale=1.0))
    print(tag, js("JSON.stringify(window.__poly().ifs)"))
print('ERR',ERR[:3] if ERR else 'none')
proc.terminate()
