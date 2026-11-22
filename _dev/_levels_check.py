# -*- coding: utf-8 -*-
"""levels 1..5 层级差异 + levels=5 是否有缺株（CDP）。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT = 9465
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_levels_9465')
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
m = [0]; ERRS = []
def call(method, params=None):
    m[0] += 1; i = m[0]
    ws.send(json.dumps({'id': i, 'method': method, 'params': params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get('method') == 'Runtime.exceptionThrown': ERRS.append(r['params']['exceptionDetails'].get('text'))
        if r.get('id') == i: return r
def js(e):
    return call('Runtime.evaluate', {'expression': e, 'returnByValue': True, 'awaitPromise': True}).get('result', {}).get('result', {}).get('value')
def setv(id_, v, ev='input'):
    js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()" % (id_, json.dumps(str(v)), ev))
def shot(p):
    d = call('Page.captureScreenshot', {'format': 'png'})['result']['data']
    open(p, 'wb').write(base64.b64decode(d)); print('SHOT', p, os.path.getsize(p))
call('Page.enable'); call('Runtime.enable')
call('Page.navigate', {'url': 'http://127.0.0.1:8899/' + urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(100):
    if js("document.getElementById('hudBody') && document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"): break
    time.sleep(0.5)
time.sleep(1)
for L in [1, 2, 3, 4, 5]:
    setv('levels', L); time.sleep(2.5)
    setv('prog', 1000); time.sleep(0.8)
    hud = js("document.getElementById('hudBody').innerText")
    line = hud.split('\n')[0] + ' | ' + [x for x in hud.split('\n') if '生效芽数' in x][0]
    print('LEVEL', L, line)
    if L in [1, 2, 5]:
        shot('_dev/levels_%d.png' % L)
print('ERRS', len(ERRS), ERRS[:5])
try: proc.terminate()
except Exception: pass
print('DONE')
