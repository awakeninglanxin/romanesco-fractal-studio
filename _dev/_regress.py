# -*- coding: utf-8 -*-
"""回归：5 预设切换零报错 + 4 种导出 Blob 校验。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket

PORT = 9334
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_cdp_reg_9334')
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc = subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl',
    '--use-gl=swiftshader','--enable-unsafe-swiftshader','--window-size=1400,900',
    '--remote-debugging-port=%d'%PORT,'--user-data-dir='+PROFILE,'about:blank'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def target():
    for _ in range(80):
        try:
            ts=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list'%PORT,timeout=1))
            for t in ts:
                if t['type']=='page': return t
        except Exception: pass
        time.sleep(0.5)
    raise RuntimeError('no devtools')
ws=websocket.create_connection(target()['webSocketDebuggerUrl'],timeout=90,suppress_origin=True)
_m=[0]
def call(m,p=None):
    _m[0]+=1;i=_m[0];ws.send(json.dumps({'id':i,'method':m,'params':p or {}}))
    while True:
        r=json.loads(ws.recv())
        if r.get('id')==i:return r
def js(e):
    return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('result',{}).get('value')
call('Page.enable');call('Runtime.enable')
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(80):
    if js("typeof THREE!=='undefined'&&!!document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.length>0"):break
    time.sleep(0.5)
time.sleep(2)
# 捕获 window error
js("window.__errs=[];window.addEventListener('error',function(e){window.__errs.push(e.message);});")

for preset in ['romanesco','cauliflower','broccoli','upright','xmas']:
    js("var s=document.getElementById('preset');s.value='%s';s.dispatchEvent(new Event('change',{bubbles:true}));"%preset)
    time.sleep(2)
    hud=js("document.getElementById('hudBody').innerText").replace('\n',' | ')
    print('PRESET',preset,'->',hud[:90])

# 切回 upright 做导出（蜂窝场景用户最关心）
js("var s=document.getElementById('preset');s.value='upright';s.dispatchEvent(new Event('change',{bubbles:true}));var u=document.getElementById('upN');u.value=1;u.dispatchEvent(new Event('input',{bubbles:true}));var p=document.getElementById('prog');p.value=1000;p.dispatchEvent(new Event('input',{bubbles:true}));")
time.sleep(2)
for fmt in ['stl','obj','ply','step']:
    res=js("(function(){try{var b=window.__exporters['%s']();return JSON.stringify({ok:true,size:b.size,type:b.type,head:Array.from(new Uint8Array(b.slice(0,80))).map(function(x){return String.fromCharCode(x)}).join('')});}catch(e){return JSON.stringify({ok:false,err:e.message});}})()"%fmt)
    print('EXPORT',fmt,res)

print('WINERR',js("JSON.stringify(window.__errs)"))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
