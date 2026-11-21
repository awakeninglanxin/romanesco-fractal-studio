# -*- coding: utf-8 -*-
"""正60面体贴砖 + 历史需求综合验证（CDP 驱动 Chrome）。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket

PORT = 9463
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_bucky_9463')
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc = subprocess.Popen([CHROME, '--headless=new', '--no-sandbox', '--enable-webgl',
    '--use-gl=swiftshader', '--enable-unsafe-swiftshader',
    '--window-size=1602,1002', '--hide-scrollbars',
    '--remote-debugging-port=%d' % PORT, '--user-data-dir=' + PROFILE, 'about:blank'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def wait_devtools():
    for _ in range(100):
        try:
            tabs = json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list' % PORT, timeout=1))
            pages = [t for t in tabs if t['type'] == 'page']
            if pages:
                return pages[0]
        except Exception:
            pass
        time.sleep(0.4)
    raise RuntimeError('no devtools')

tab = wait_devtools()
ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=240, suppress_origin=True)
_mid = [0]
ERRORS = []

def call(method, params=None):
    _mid[0] += 1
    i = _mid[0]
    ws.send(json.dumps({'id': i, 'method': method, 'params': params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get('method') == 'Runtime.exceptionThrown':
            ERRORS.append(msg['params']['exceptionDetails'].get('text', 'exception'))
        if msg.get('method') == 'Log.entryAdded':
            e = msg['params']['entry']
            if e.get('level') == 'error':
                ERRORS.append(e.get('text', 'log error'))
        if msg.get('id') == i:
            return msg

def js(expr):
    r = call('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
    return r.get('result', {}).get('result', {}).get('value')

def setv(id_, v, ev='input'):
    js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()" % (id_, json.dumps(str(v)), ev))

def shot(path, canvas_only=False):
    if canvas_only:
        d = call('Page.captureScreenshot', {'format': 'png', 'clip': {'x': 0, 'y': 0, 'width': 1240, 'height': 1000, 'scale': 1}})['result']['data']
    else:
        d = call('Page.captureScreenshot', {'format': 'png'})['result']['data']
    open(path, 'wb').write(base64.b64decode(d))
    print('SHOT', path, os.path.getsize(path))

call('Page.enable'); call('Runtime.enable'); call('Log.enable'); call('Network.enable')
call('Network.setCacheDisabled', {'cacheDisabled': True})
url = 'http://127.0.0.1:8899/' + urllib.parse.quote('罗马花椰菜_分形生长参数台.html')
call('Page.navigate', {'url': url})
for _ in range(120):
    if js("document.getElementById('hudBody') && document.getElementById('hudBody').innerText.indexOf('锥体总数') >= 0"):
        break
    time.sleep(0.5)
time.sleep(1.5)

print('=== 默认状态 ===')
print(js("JSON.stringify({preset:document.getElementById('preset').value,cmap:document.getElementById('cmap').value,arms:document.getElementById('fibArms').value,twist:document.getElementById('vFibTwist').textContent,upN:document.getElementById('upN').value,fillK:document.getElementById('vFillK').textContent,hex:document.getElementById('hexBase').checked,spin:document.getElementById('spin').checked,prog:document.getElementById('vProg').textContent})"))

print('=== 切换到正60面体 ===')
setv('preset', 'bucky', 'change')
for _ in range(120):
    if js("!!window.__poly"):
        break
    time.sleep(0.5)
time.sleep(2)
print('POLY', js("JSON.stringify(window.__poly)"))
print('HUD', (js("document.getElementById('hudBody').innerText") or '').replace('\n', ' | '))
print('UI', js("JSON.stringify({note:getComputedStyle(document.getElementById('polyNote')).display,fillDisabled:document.getElementById('autoFill').disabled,hexDisabled:document.getElementById('hexBase').checked})"))
setv('prog', 1000); time.sleep(1.5)   # 截图前让花盘完全长出
print('GROWN', js("document.getElementById('hudBody').innerText.split('\\n')[0]"))
shot('预览_正60面体_32面贴砖.png')
shot('_dev/bucky_canvas.png', True)

print('=== 视角保持（调缠绕度） ===')
c0 = js("JSON.stringify(window.__cam ? [window.__cam.theta(),window.__cam.phi(),window.__cam.radius()] : null)")
setv('fibTwist', 0); time.sleep(1.2)
c1 = js("JSON.stringify(window.__cam ? [window.__cam.theta(),window.__cam.phi(),window.__cam.radius()] : null)")
setv('fibTwist', 60); time.sleep(1.2)
print('CAM', c0, c1, 'SAME', c0 == c1)
setv('fibTwist', 26); time.sleep(0.8)

print('=== 导出（多面体模式） ===')
call('Runtime.evaluate', {'expression': "window.__blobSizes=[];var _o=URL.createObjectURL;URL.createObjectURL=function(b){window.__blobSizes.push(b.size);return _o(b);};"})
for f in ['stl', 'obj', 'ply']:
    setv('expFmt', f, 'change'); time.sleep(0.2)
    js("document.getElementById('btnSTL').click()")
    time.sleep(1.2)
print('BLOBS', js("JSON.stringify(window.__blobSizes)"))

print('=== 六个预设全部切换 ===')
for p in ['romanesco', 'cauliflower', 'broccoli', 'upright', 'xmas', 'bucky', 'upright']:
    setv('preset', p, 'change'); time.sleep(1.2)
    print('PRESET', p, (js("document.getElementById('hudBody').innerText.split('\\n')[0]") or ''))
print('BACK_TO_UPRIGHT_HEX', js("document.getElementById('hexBase').checked"))
print('ERRORS', len(ERRORS), json.dumps(ERRORS[:8], ensure_ascii=False))
try: proc.terminate()
except Exception: pass
print('DONE')
