# -*- coding: utf-8 -*-
"""验证：默认间距1.00 / 补株0.96 / 红色六边形砖底盘（俯视+侧视）+ 导出含底盘。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9372; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_hexbase_9372')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1512,964','--hide-scrollbars',
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
call('Page.enable');call('Runtime.enable');call('Network.enable')
call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
def setv(id,val,ev):
  js("var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));"%(id,json.dumps(str(val)),ev))
def click(id):js("document.getElementById('%s').click();"%id)

# 默认状态检查
print('SPIN:',js("document.getElementById('spin').checked"))
print('SPREAD:',js("document.getElementById('upSpread').value"),js("document.getElementById('vUpSpread').textContent"))
print('FILLK:',js("document.getElementById('fillK').value"),js("document.getElementById('vFillK').textContent"))
# 场景：upright 19株 dec36 + 自动填满0.96 + 红色底盘
setv('preset','upright','change');time.sleep(0.5)
setv('upN',19,'input');setv('spiralMode','dec36','change');setv('cmap','viridis','change')
js("var a=document.getElementById('autoFill');if(!a.checked)a.click();")
setv('fillK',96,'input')
js("var h=document.getElementById('hexBase');if(!h.checked)h.click();")
setv('hexThick',10,'input');setv('hexOverlap',35,'input')
setv('prog',1000,'input');time.sleep(2.5)
print('HUD:',js("document.getElementById('hudBody').innerText").replace('\n',' | '))
print('ERR:',js("document.getElementById('err').style.display"))
click('btnTop');time.sleep(1);shot('预览_红色六边形底盘_俯视.png')
# 侧视（用相机拖拽把 phi 拉到接近水平）
js("document.getElementById('btnReset').click();")  # 只重置进度不改视角? reset会重置生长——改用直接设相机
time.sleep(0.3)
setv('prog',1000,'input');time.sleep(1)
# 通过 mock 鼠标下拖降低仰角
rect=json.loads(js("JSON.stringify(document.getElementById('cv').getBoundingClientRect())"))
cx=rect['left']+rect['width']/2;cy=rect['top']+rect['height']/2
call('Input.dispatchMouseEvent',{'type':'mousePressed','x':cx,'y':cy,'button':'left','buttons':1,'clickCount':1})
call('Input.dispatchMouseEvent',{'type':'mouseMoved','x':cx,'y':cy+150,'button':'left','buttons':1})
call('Input.dispatchMouseEvent',{'type':'mouseReleased','x':cx,'y':cy+150,'button':'left','buttons':0,'clickCount':1})
time.sleep(1);shot('预览_红色六边形底盘_侧视.png')

# 导出验证：底盘是否进入三角面（对比开/关底盘的 STL blob 大小）
js("window.__blobs=[];var _o=URL.createObjectURL;URL.createObjectURL=function(b){window.__blobs.push(b.size);return _o.apply(this,arguments);};")
call('Runtime.evaluate',{'expression':"window.__exporters.stl()"});time.sleep(2)
with_base=js("JSON.stringify(window.__blobs)")
print('STL_WITH_BASE:',with_base)
js("var h=document.getElementById('hexBase');if(h.checked)h.click();")  # 关底盘
time.sleep(1.5)
call('Runtime.evaluate',{'expression':"window.__exporters.stl()"});time.sleep(2)
print('STL_NO_BASE:',js("JSON.stringify(window.__blobs)"))
print('ERR_FINAL:',js("document.getElementById('err').style.display"))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
