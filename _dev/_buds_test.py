# -*- coding: utf-8 -*-
"""测试不同每级芽数下的锥数/性能，并截图。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket

PORT = 9426
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_buds_9426')
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc = subprocess.Popen([
    CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
    '--enable-unsafe-swiftshader','--window-size=1538,978','--hide-scrollbars',
    '--remote-debugging-port=%d'%PORT,'--user-data-dir='+PROFILE,'about:blank'
],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def wait():
    for _ in range(80):
        try:
            ts=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list'%PORT,timeout=1))
            ps=[t for t in ts if t['type']=='page']
            if ps:return ps[0]
        except Exception:pass
        time.sleep(0.5)
    raise RuntimeError('no devtools')
t0=wait();ws=websocket.create_connection(t0['webSocketDebuggerUrl'],timeout=120,suppress_origin=True)
_m=[0]
def call(m,p=None):
    _m[0]+=1;i=_m[0];ws.send(json.dumps({'id':i,'method':m,'params':p or {}}))
    while True:
        r=json.loads(ws.recv())
        if r.get('id')==i:return r
def js(e):
    r=call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True})
    return r.get('result',{}).get('result',{}).get('value')
def shot(p):
    d=call('Page.captureScreenshot',{'format':'png'})['result']['data']
    open(p,'wb').write(base64.b64decode(d));print('SHOT',p,os.path.getsize(p))
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(90):
    if js("document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"):break
    time.sleep(0.5)
time.sleep(1.5)
# 单株 upN=7，测各芽数
js("(function(){var e=document.getElementById('upN');e.value=7;e.dispatchEvent(new Event('input',{bubbles:true}));})()")
time.sleep(1)
js("(function(){document.getElementById('btnTop')&&document.getElementById('btnTop').click();})()")
time.sleep(1)
for buds in [24,40,55,80]:
    js("(function(){var e=document.getElementById('upBuds');e.value=%d;e.dispatchEvent(new Event('input',{bubbles:true}));})()"%buds)
    time.sleep(1.8)
    hud=js("document.getElementById('hudBody').innerText")
    line=hud.split('\n')[0]
    print('BUDS',buds,line)
    shot('_dev/budstop_%d.png'%buds)
try:proc.terminate()
except Exception:pass
print('DONE')
