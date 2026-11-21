# -*- coding: utf-8 -*-
"""验证网页打开即默认：直立花盘满铺 + 红底盘5mm/0.00 + 进度100% + 不旋转。不改任何参数直接截图。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9385; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_def_9385')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1518,970','--hide-scrollbars',
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
t=targets();ws=websocket.create_connection(t['webSocketDebuggerUrl'],timeout=180,suppress_origin=True)
mid=[0]
def call(m,p=None):
  mid[0]+=1;n=mid[0];ws.send(json.dumps({'id':n,'method':m,'params':p or {}}))
  while True:
    r=json.loads(ws.recv())
    if r.get('id')==n:return r
def js(e):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('result',{}).get('value')
def shot(p):
  d=call('Page.captureScreenshot',{'format':'png'})['result']['data']
  open(p,'wb').write(base64.b64decode(d));print('SHOT',p,os.path.getsize(p))
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(3)
print('PRESET:',js("document.getElementById('preset').value"))
print('PROG:',js("document.getElementById('prog').value"),js("document.getElementById('vProg').textContent"))
print('SPIN:',js("document.getElementById('spin').checked"))
print('HEXBASE:',js("document.getElementById('hexBase').checked"))
print('HEXTHICK:',js("document.getElementById('vHexThick').textContent"))
print('HEXOVERLAP:',js("document.getElementById('vHexOverlap').textContent"))
print('R2L:',js("document.getElementById('vR2L').textContent"))
print('SPREAD:',js("document.getElementById('vUpSpread').textContent"))
print('FILLK:',js("document.getElementById('vFillK').textContent"))
print('HUD:',js("document.getElementById('hudBody').innerText").replace('\n',' | '))
print('ERR:',js("document.getElementById('err').style.display"))
shot('预览_默认打开状态.png')
# 导出4格式确认仍在（删面板后）
js("window.__blobs=[];var _o=URL.createObjectURL;URL.createObjectURL=function(b){window.__blobs.push(b.size);return _o.apply(this,arguments);};")
for f in ['stl','obj','ply']:
  setv="var e=document.getElementById('expFmt');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));document.getElementById('btnSTL').click();"%f
  js(setv);time.sleep(1.5)
print('BLOBS3:',js("JSON.stringify(window.__blobs)"))
print('ERR_FINAL:',js("document.getElementById('err').style.display"))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
