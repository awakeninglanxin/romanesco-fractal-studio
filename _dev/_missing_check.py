# -*- coding: utf-8 -*-
"""复现用户截图参数：levels=5 / α=133.365° / cmap=turbo，核查是否缺株。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT = 9466
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_missing_9466')
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
m = [0]
def call(method, params=None):
    m[0] += 1; i = m[0]
    ws.send(json.dumps({'id': i, 'method': method, 'params': params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get('id') == i: return r
def js(e):
    return call('Runtime.evaluate', {'expression': e, 'returnByValue': True, 'awaitPromise': True}).get('result', {}).get('result', {}).get('value')
def setv(id_, v, ev='input'):
    js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()" % (id_, json.dumps(str(v)), ev))
call('Page.enable'); call('Runtime.enable')
call('Page.navigate', {'url': 'http://127.0.0.1:8899/' + urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(100):
    if js("document.getElementById('hudBody') && document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"): break
    time.sleep(0.5)
time.sleep(1)
setv('levels', 5); time.sleep(2)
setv('angle', 133.365); time.sleep(2)
setv('r2l', 111); time.sleep(2)
setv('i2o', 46); time.sleep(2)
setv('cmap', 'turbo', 'change'); time.sleep(2)
setv('prog', 1000); time.sleep(1)
print('HUD', (js("document.getElementById('hudBody').innerText") or '').replace('\n', ' | '))
print('PLANTS', js("JSON.stringify(window.__plantStats)"))
d = call('Page.captureScreenshot', {'format': 'png'})['result']['data']
open('_dev/levels5_userparams.png', 'wb').write(base64.b64decode(d))
print('SHOT _dev/levels5_userparams.png', os.path.getsize('_dev/levels5_userparams.png'))
try: proc.terminate()
except Exception: pass
print('DONE')
