# -*- coding: utf-8 -*-
"""同一俯视机位，autoFill 关/开 各截一张上边缘特写（CDP clip 放大），直观看边缘 6 个缺口是否补上。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9413; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_fillab_9413')
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
def shot(p,clip=None):
  par={'format':'png'}
  if clip:par['clip']=clip
  d=call('Page.captureScreenshot',par)['result']['data']
  open(p,'wb').write(base64.b64decode(d));print('SHOT',p)
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
js("var e=document.getElementById('preset');e.value='upright';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(1.5)
js("document.getElementById('btnTop').click()");time.sleep(0.9)
CLIP={'x':330,'y':50,'width':470,'height':190,'scale':2.4}
# 关
js("var c=document.getElementById('autoFill');c.checked=false;c.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(2.0)
shot('../预览_补株对照_关_upN7.png',CLIP)
print('OFF fill=',js("window.__fill().fillCount"))
# 开
js("var c=document.getElementById('autoFill');c.checked=true;c.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(2.5)
shot('../预览_补株对照_开_upN7.png',CLIP)
F=json.loads(js("JSON.stringify(window.__fill())"))
print('ON fill=',F['fillCount'],'inner=',F['fillInner'],'edge=',F['fillEdge'])
print('ERR:',js("document.getElementById('err').style.display"))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
