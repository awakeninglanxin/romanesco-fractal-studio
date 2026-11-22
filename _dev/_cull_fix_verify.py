# -*- coding: utf-8 -*-
"""验证：近水平锥改扶正后，直立花盘底面暴露处理 —— 删锥量下降、扶正数>0、低视角无大片蓝底裸露。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9397; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_cullfix_9397')
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
  open(p,'wb').write(base64.b64decode(d));print('SHOT',p)
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2.5)
print('PRESET:',js("document.getElementById('preset').value"))
print('AXIS_ON :',js("JSON.stringify(window.__axis())"))
shot('../预览_扶正修复_默认视角.png')
# 关掉 cullBottom 作为锥数基准
js("var c=document.getElementById('cullBottom');c.checked=false;c.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(1.5)
print('AXIS_OFF:',js("JSON.stringify(window.__axis())"))
# 重新开启
js("var c=document.getElementById('cullBottom');c.checked=true;c.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(1.5)
print('AXIS_ON2:',js("JSON.stringify(window.__axis())"))
# 压低视角：向上拖拽（phi 减小→更侧视/仰视），多次
def drag(x1,y1,x2,y2):
  call('Input.dispatchMouseEvent',{'type':'mousePressed','x':x1,'y':y1,'button':'left','buttons':1,'clickCount':1})
  for k in range(1,15):
    xx=x1+(x2-x1)*k/14; yy=y1+(y2-y1)*k/14
    call('Input.dispatchMouseEvent',{'type':'mouseMoved','x':xx,'y':yy,'button':'left','buttons':1})
  call('Input.dispatchMouseEvent',{'type':'mouseReleased','x':x2,'y':y2,'button':'left','buttons':0,'clickCount':1})
drag(460,300,460,140)
time.sleep(0.6)
shot('../预览_扶正修复_低视角.png')
print('ERR:',js("document.getElementById('err').style.display"))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
