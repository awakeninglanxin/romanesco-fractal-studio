# -*- coding: utf-8 -*-
"""最终验证：默认不旋转 / 金字塔R/L默认 / 自动填满 / 4格式导出。只终止自己启动的chrome。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket

PORT = 9365
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_final_9365')
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc = subprocess.Popen([
    CHROME, '--headless=new', '--no-sandbox', '--enable-webgl',
    '--use-gl=swiftshader', '--enable-unsafe-swiftshader',
    '--window-size=1510,962', '--hide-scrollbars',
    '--remote-debugging-port=%d' % PORT, '--user-data-dir=' + PROFILE, 'about:blank'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def wait_targets():
    for _ in range(80):
        try:
            ts = json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list' % PORT, timeout=1))
            pages = [t for t in ts if t['type'] == 'page']
            if pages: return pages[0]
        except Exception: pass
        time.sleep(0.5)
    raise RuntimeError('devtools not ready')

t0 = wait_targets()
ws = websocket.create_connection(t0['webSocketDebuggerUrl'], timeout=90, suppress_origin=True)
_mid=[0]
def call(m, p=None):
    _mid[0]+=1; mid=_mid[0]
    ws.send(json.dumps({'id':mid,'method':m,'params':p or {}}))
    while True:
        r=json.loads(ws.recv())
        if r.get('id')==mid: return r
def js(e):
    return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('result',{}).get('value')
def shot(p):
    d=call('Page.captureScreenshot',{'format':'png'})['result']['data']
    open(p,'wb').write(base64.b64decode(d)); print('SHOT',p,os.path.getsize(p))

call('Page.enable');call('Runtime.enable');call('Network.enable')
call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')})
for _ in range(80):
    if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"): break
    time.sleep(0.5)
time.sleep(2)

# 1) 默认不旋转
print('SPIN_CHECKED:', js("document.getElementById('spin').checked"))
print('PYRAMID_BTN:', js("!!document.getElementById('btnPyramid')"))

# 2) 默认 upright 预设 → 金字塔 R/L
def setv(id,val,ev):
    js("var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));"%(id,json.dumps(str(val)),ev))
setv('preset','upright','change')
time.sleep(1)
print('R2L_LABEL:', js("document.getElementById('vR2L').textContent"))
print('R2L_VALUE:', js("document.getElementById('r2l').value"))
print('AUTOFILL_CHECKED:', js("document.getElementById('autoFill').checked"))

# 3) 开自动填满 + 进度拉满 + 俯视 出预览
setv('upN',19,'input');setv('upSpread',10,'input');setv('spiralMode','dec36','change')
setv('cmap','viridis','change')
js("var a=document.getElementById('autoFill');if(!a.checked)a.click();")
setv('fillK',68,'input')
setv('prog',1000,'input')
time.sleep(2)
js("document.getElementById('btnTop').click()")
time.sleep(1)
shot('预览_自动填满_金字塔比_俯视.png')
print('HUD:', js("document.getElementById('hudBody').innerText").replace('\n',' | '))
print('ERR:', js("document.getElementById('err').style.display"))

# 4) 4格式导出
js("window.__blobs=[];var _o=URL.createObjectURL;URL.createObjectURL=function(b){window.__blobs.push(b.size);return _o.apply(this,arguments);};")
for f in ['stl','obj','ply','step']:
    setv('expFmt',f,'change'); js("document.getElementById('btnSTL').click()"); time.sleep(1.5)
print('BLOBS:', js("JSON.stringify(window.__blobs)"))
print('ERR_FINAL:', js("document.getElementById('err').style.display"))

ws.close();proc.terminate()
try: proc.wait(timeout=5)
except Exception: proc.kill()
print('DONE')
