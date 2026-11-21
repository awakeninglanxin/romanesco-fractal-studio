# -*- coding: utf-8 -*-
"""出最终预览：六重对称整盘俯视、八重单株俯视/侧视、levels5修复对照。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9337; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_fs5_9337')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
 '--enable-unsafe-swiftshader','--window-size=1516,968','--remote-debugging-port=%d'%PORT,
 '--user-data-dir='+PROFILE,'about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def target():
    for _ in range(80):
        try:
            ts=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list'%PORT,timeout=1))
            for t in ts:
                if t['type']=='page':return t
        except Exception:pass
        time.sleep(0.5)
    raise RuntimeError('no devtools')
ws=websocket.create_connection(target()['webSocketDebuggerUrl'],timeout=120,suppress_origin=True)
_m=[0]
def call(m,p=None):
    _m[0]+=1;i=_m[0];ws.send(json.dumps({'id':i,'method':m,'params':p or {}}))
    while True:
        r=json.loads(ws.recv())
        if r.get('id')==i:return r
def js(e):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('result',{}).get('value')
def shot(p):
    d=call('Page.captureScreenshot',{'format':'png'})['result']['data']
    open(p,'wb').write(base64.b64decode(d));print('SHOT',p,os.path.getsize(p))
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')})
for _ in range(80):
    if js("typeof THREE!=='undefined'&&!!document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.length>0"):break
    time.sleep(0.5)
time.sleep(2)
js("var c=document.getElementById('spin');if(c.checked)c.click();")
def setv(id,val,ev='input'):
    js("var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));"%(id,json.dumps(str(val)),ev));time.sleep(1)
def top():js("document.getElementById('btnTop').click()");time.sleep(1)

# 六重对称整盘俯视（levels=3 好看的密度）
js("var s=document.getElementById('preset');s.value='upright';s.dispatchEvent(new Event('change',{bubbles:true}));");time.sleep(2)
setv('levels',3);setv('upN',7);setv('spiralMode','hex60','change');setv('cmap','level','change');setv('prog',1000)
top();shot('_dev/FINAL_board_viridis.png')

# 八重单株俯视
setv('upN',1);setv('spiralMode','oct45','change');top();shot('_dev/FINAL_single_top.png')
# 单株侧视（复位到默认斜视）
js("document.getElementById('btnReset').click()");time.sleep(1);shot('_dev/final_oct45_single_side3.png')

# turbo cmap 整盘
setv('upN',7);setv('cmap','turbo','change');top();shot('_dev/FINAL_turbo.png')

print('HUD:',js("document.getElementById('hudBody').innerText").replace('\n',' | '))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
