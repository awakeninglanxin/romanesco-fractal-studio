# -*- coding: utf-8 -*-
"""俯视放大：确认 upN=7 时外轮廓 6 条边的缺口已被补小株填上（对照老师红箭头处）。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9412; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_fillclose_9412')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1400,900','--hide-scrollbars',
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
def js(e,awaitp=False):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':awaitp}).get('result',{}).get('result',{}).get('value')
def shot(p):
  d=call('Page.captureScreenshot',{'format':'png'})['result']['data']
  open(p,'wb').write(base64.b64decode(d));print('SHOT',p)
def wheel(x,y,dy):call('Input.dispatchMouseEvent',{'type':'mouseWheel','x':x,'y':y,'deltaX':0,'deltaY':dy})
def drag(x1,y1,x2,y2):
  call('Input.dispatchMouseEvent',{'type':'mousePressed','x':x1,'y':y1,'button':'left','buttons':1,'clickCount':1})
  for k in range(1,15):
    call('Input.dispatchMouseEvent',{'type':'mouseMoved','x':x1+(x2-x1)*k/14,'y':y1+(y2-y1)*k/14,'button':'left','buttons':1})
  call('Input.dispatchMouseEvent',{'type':'mouseReleased','x':x2,'y':y2,'button':'left','buttons':0,'clickCount':1})
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
js("var e=document.getElementById('preset');e.value='upright';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(1.5)
js("var c=document.getElementById('autoFill');c.checked=true;c.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(2)
js("document.getElementById('btnTop').click()")   # 俯视
time.sleep(0.8)
shot('../预览_补株_俯视全图_upN7.png')
# 放大到能看清边缘缺口
for _ in range(5): wheel(500,420,-240)
time.sleep(0.8)
shot('../预览_补株_俯视放大_upN7.png')
# 稍微压低一点，看边缘是否有空洞/悬空
drag(500,300,500,230)
time.sleep(0.8)
shot('../预览_补株_斜俯视放大_upN7.png')
print('FILL:',js("JSON.stringify({n:window.__fill().fillCount,i:window.__fill().fillInner,e:window.__fill().fillEdge})"))
print('ERR:',js("document.getElementById('err').style.display"))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
