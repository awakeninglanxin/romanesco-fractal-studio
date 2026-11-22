# -*- coding: utf-8 -*-
"""俯视对比：补株关 vs 开；验证视角不随参数变化。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT = 9472
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_holecmp_9472')
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc = subprocess.Popen([CHROME, '--headless=new', '--no-sandbox', '--enable-webgl',
    '--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--window-size=1602,1002',
    '--hide-scrollbars', '--remote-debugging-port=%d' % PORT, '--user-data-dir=' + PROFILE, 'about:blank'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(100):
    try:
        tabs = json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list' % PORT, timeout=1))
        pages = [t for t in tabs if t['type'] == 'page']
        if pages: break
    except Exception: pass
    time.sleep(0.4)
ws = websocket.create_connection(pages[0]['webSocketDebuggerUrl'], timeout=240, suppress_origin=True)
m=[0]; ERR=[]
def call(method, params=None):
    m[0]+=1;i=m[0]
    ws.send(json.dumps({'id':i,'method':method,'params':params or {}}))
    while True:
        r=json.loads(ws.recv())
        if r.get('method')=='Runtime.exceptionThrown':ERR.append(r['params']['exceptionDetails'].get('text'))
        if r.get('id')==i:return r
def js(e):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('result',{}).get('value')
def setv(id_,v,ev='input'):
    js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()"%(id_,json.dumps(str(v)),ev))
def click(id_):js("document.getElementById('%s').click()"%id_)
def shot(p):
    d=call('Page.captureScreenshot',{'format':'png'})['result']['data']
    open(p,'wb').write(base64.b64decode(d));print('SHOT',p,os.path.getsize(p))
call('Page.enable');call('Runtime.enable')
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(100):
    if js("document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"):break
    time.sleep(0.5)
time.sleep(1.2)

# 设 upN=19，关补株，俯视
setv('upN',19);time.sleep(2)
click('btnTop');time.sleep(1.2)
cam0=js("JSON.stringify({theta:window.__cam.theta(),phi:window.__cam.phi(),radius:window.__cam.radius()})")
print('CAM_OFF',cam0)
shot('_dev/holecmp_off.png')

# 开补株（视角应不变）
click('autoFill');time.sleep(2.8)
cam1=js("JSON.stringify({theta:window.__cam.theta(),phi:window.__cam.phi(),radius:window.__cam.radius()})")
print('CAM_ON',cam1,'SAME' if cam0==cam1 else 'CHANGED!')
shot('_dev/holecmp_on.png')

# 调 fillK 大小，视角仍不变
setv('fillK',55);time.sleep(2.5)
cam2=js("JSON.stringify({theta:window.__cam.theta(),phi:window.__cam.phi(),radius:window.__cam.radius()})")
print('CAM_FILLK55',cam2,'SAME' if cam0==cam2 else 'CHANGED!')
shot('_dev/holecmp_fillk55.png')

print('ERRS',len(ERR),ERR[:5])
try:proc.terminate()
except Exception:pass
print('DONE')
