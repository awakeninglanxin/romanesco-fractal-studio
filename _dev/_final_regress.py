# -*- coding: utf-8 -*-
"""删除第0级面板后的最终回归：预设切换/导出/默认参数/红色底盘。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9378; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_reg_9378')
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
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
def setv(id,val,ev):js("var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));"%(id,json.dumps(str(val)),ev))
def click(id):js("document.getElementById('%s').click();"%id)

print('HONEY_EXISTS:',js("!!document.getElementById('honey')"))
print('EXPORT_EXISTS:',js("!!document.getElementById('btnSTL')"))
print('SPIN:',js("document.getElementById('spin').checked"))
print('SPREAD:',js("document.getElementById('vUpSpread').textContent"))
print('FILLK:',js("document.getElementById('vFillK').textContent"))
# 5预设切换
for p in ['romanesco','cauliflower','broccoli','upright','xmas']:
  setv('preset',p,'change');time.sleep(0.8)
  print('PRESET',p,'ERR:',js("document.getElementById('err').style.display"),'cones:',js("document.getElementById('hudBody').innerText.split('\\n')[0]"))
# 导出4格式（UI按钮路径，删除区块后重点验证）
js("window.__blobs=[];var _o=URL.createObjectURL;URL.createObjectURL=function(b){window.__blobs.push(b.size);return _o.apply(this,arguments);};")
setv('preset','upright','change');time.sleep(0.5)
for f in ['stl','obj','ply','step']:
  setv('expFmt',f,'change');click('btnSTL');time.sleep(1.8)
print('BLOBS:',js("JSON.stringify(window.__blobs)"))
print('STLINFO:',js("document.getElementById('stlInfo').innerText"))
print('ERR_FINAL:',js("document.getElementById('err').style.display"))
# 最终预览：upright 19株 十重 自动填满0.96 红底盘 俯视
setv('upN',19,'input');setv('spiralMode','dec36','change');setv('cmap','viridis','change')
js("var a=document.getElementById('autoFill');if(!a.checked)a.click();")
setv('fillK',96,'input')
js("var h=document.getElementById('hexBase');if(!h.checked)h.click();")
setv('hexThick',10,'input');setv('hexOverlap',35,'input');setv('prog',1000,'input');time.sleep(2.5)
click('btnTop');time.sleep(1)
shot('预览_最终_红底盘满铺蜂窝.png')
print('HUD_FINAL:',js("document.getElementById('hudBody').innerText").replace('\n',' | '))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
