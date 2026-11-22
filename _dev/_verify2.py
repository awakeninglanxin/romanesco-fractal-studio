# -*- coding: utf-8 -*-
"""综合验证：levels=5 无裸露锥 + 多算法/多cmap切换 + 导出 + 截图。只终止自己起的 chrome。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9336; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_v2d_9336')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
 '--enable-unsafe-swiftshader','--window-size=1518,970','--remote-debugging-port=%d'%PORT,
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
def js(e):
    return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('result',{}).get('value')
def shot(p):
    d=call('Page.captureScreenshot',{'format':'png'})['result']['data']
    open(p,'wb').write(base64.b64decode(d));print('SHOT',p,os.path.getsize(p))
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
    if js("typeof THREE!=='undefined'&&!!document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.length>0"):break
    time.sleep(0.5)
time.sleep(2)
js("window.__errs=[];window.addEventListener('error',function(e){window.__errs.push(e.message);});var c=document.getElementById('spin');if(c.checked)c.click();")

def preset(name):
    js("var s=document.getElementById('preset');s.value='%s';s.dispatchEvent(new Event('change',{bubbles:true}));"%name);time.sleep(2)
def setv(id,val,ev='input'):
    js("var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));"%(id,json.dumps(str(val)),ev));time.sleep(1.5)
def hud():return js("document.getElementById('hudBody').innerText").replace('\n',' | ')

# --- levels=5 bug 复现场景：upright, levels=5, upN=7, buds=24 ---
preset('upright')
setv('levels',5);setv('upN',7);setv('upBuds',24)
setv('prog',1000)
print('L5 HUD:',hud())
shot('_dev/v2_L5_golden.png')

# 切到六重60°对称 + 分级配色
setv('spiralMode','hex60','change')
print('HEX60 HUD:',hud())
shot('_dev/v2_L5_hex60.png')

# 八重45°
setv('spiralMode','oct45','change')
print('OCT45 HUD:',hud())
shot('_dev/v2_L5_oct45.png')

# 白银比
setv('spiralMode','silver','change')
print('SILVER HUD:',hud())
shot('_dev/v2_L5_silver.png')

# cmap 系列 (hex60 下)
for cm in ['level','hsv','turbo','viridis','plasma','height']:
    setv('cmap',cm,'change')
    print('CMAP',cm,'->',hud()[:70])
    shot('_dev/v2_cmap_%s.png'%cm)

# 导出验证（upright, upN=1 减负）
preset('upright');setv('upN',1);setv('prog',1000)
js("""window.__blobs=[];var _ou=URL.createObjectURL.bind(URL);
URL.createObjectURL=function(b){window.__blobs.push({size:b.size,type:b.type});return _ou(b);};
var _ac=HTMLAnchorElement.prototype.click;HTMLAnchorElement.prototype.click=function(){};""")
for fmt in ['stl','obj','ply','step']:
    js("window.__exporters['%s']();"%fmt)
print('BLOBS',js("JSON.stringify(window.__blobs)"))
print('WINERR',js("JSON.stringify(window.__errs)"))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
