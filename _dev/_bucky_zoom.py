# -*- coding: utf-8 -*-
"""正60面体近景：确认每面 5/6+1 花盘布局。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT = 9464
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_buckyzoom_9464')
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc = subprocess.Popen([CHROME, '--headless=new', '--no-sandbox', '--enable-webgl',
    '--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--window-size=1800,1200',
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
m = [0]
def call(method, params=None):
    m[0] += 1; i = m[0]
    ws.send(json.dumps({'id': i, 'method': method, 'params': params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get('id') == i: return r
def js(e):
    return call('Runtime.evaluate', {'expression': e, 'returnByValue': True, 'awaitPromise': True}).get('result', {}).get('result', {}).get('value')
def shot(p, clip=None):
    prm = {'format': 'png'}
    if clip: prm['clip'] = clip
    d = call('Page.captureScreenshot', prm)['result']['data']
    open(p, 'wb').write(base64.b64decode(d)); print('SHOT', p, os.path.getsize(p))
call('Page.enable'); call('Runtime.enable')
call('Page.navigate', {'url': 'http://127.0.0.1:8899/' + urllib.parse.quote('罗马花椰菜_分形生长参数台.html')})
for _ in range(100):
    if js("document.getElementById('hudBody') && document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"): break
    time.sleep(0.5)
time.sleep(1)
js("(function(){var e=document.getElementById('preset');e.value='bucky';e.dispatchEvent(new Event('change',{bubbles:true}));})()")
time.sleep(3)
js("(function(){var e=document.getElementById('prog');e.value=1000;e.dispatchEvent(new Event('input',{bubbles:true}));})()")
time.sleep(1)
# 近景：滚轮放大（画布中心约 600,600）
for _ in range(6):
    call('Input.dispatchMouseEvent', {'type': 'mouseWheel', 'x': 600, 'y': 600, 'deltaX': 0, 'deltaY': -120})
time.sleep(1.5)
shot('_dev/bucky_zoom1.png', {'x': 0, 'y': 0, 'width': 1200, 'height': 1200, 'scale': 1})
# 正对一个面：小幅旋转
call('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': 600, 'y': 600, 'button': 'left', 'clickCount': 1})
call('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': 700, 'y': 540, 'button': 'left'})
call('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': 700, 'y': 540, 'button': 'left'})
time.sleep(1.2)
shot('_dev/bucky_zoom2.png', {'x': 0, 'y': 0, 'width': 1200, 'height': 1200, 'scale': 1})
print('CAM', js("JSON.stringify([window.__cam.theta(),window.__cam.phi(),window.__cam.radius()])"))
try: proc.terminate()
except Exception: pass
print('DONE')
