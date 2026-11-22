# -*- coding: utf-8 -*-
"""低视角截图，确认蓝锥底面与灰盘顶面贴合无缝隙(复现老师截图角度)。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9393; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_low_9393')
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
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
# 低视角：phi 调大(接近水平/略俯)，用 __cam 读当前值再设
js("var e=document.getElementById('preset');e.value='broccoli';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(1.8)
# 画布上拖拽来压低视角（从中心向下拖 = phi 增大看底部）
def drag(x1,y1,x2,y2):
  call('Input.dispatchMouseEvent',{'type':'mousePressed','x':x1,'y':y1,'button':'left','buttons':1,'clickCount':1})
  steps=12
  for k in range(1,steps+1):
    xx=x1+(x2-x1)*k/steps; yy=y1+(y2-y1)*k/steps
    call('Input.dispatchMouseEvent',{'type':'mouseMoved','x':xx,'y':yy,'button':'left','buttons':1})
  call('Input.dispatchMouseEvent',{'type':'mouseReleased','x':x2,'y':y2,'button':'left','buttons':0,'clickCount':1})
# 画布中心约 (450,360)，向下拖 = 视角抬高从上看；向上拖=压低从下看
drag(450,360,450,520)   # 先试一个方向
time.sleep(0.5)
dat=call('Page.captureScreenshot',{'format':'png'})['result']['data']
open('../预览_落地盘贴合_低视角A.png','wb').write(base64.b64decode(dat))
drag(450,520,450,200)   # 反向大幅，看底部
time.sleep(0.5)
dat=call('Page.captureScreenshot',{'format':'png'})['result']['data']
open('../预览_落地盘贴合_低视角B.png','wb').write(base64.b64decode(dat))
print('BASE:',js("JSON.stringify(window.__base())"))
print('ERR:',js("document.getElementById('err').style.display"))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
