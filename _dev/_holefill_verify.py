# -*- coding: utf-8 -*-
"""验证：默认配色=hsvarm；补株=三角孔补小株(数量/位置/主株不变)；截图俯视。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT = 9471
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_holefill_9471')
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
def click(id_):
    js("document.getElementById('%s').click()" % id_)
def shot(p):
    d = call('Page.captureScreenshot', {'format': 'png'})['result']['data']
    open(p, 'wb').write(base64.b64decode(d)); print('SHOT', p, os.path.getsize(p))
call('Page.enable'); call('Runtime.enable')
call('Page.navigate', {'url': 'http://127.0.0.1:8899/' + urllib.parse.quote('罗马花椰菜_分形生长参数台.html')})
for _ in range(100):
    if js("document.getElementById('hudBody') && document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"): break
    time.sleep(0.5)
time.sleep(1.5)

# 1) 默认配色
print('DEFAULT_CMAP', js("JSON.stringify({sel:document.getElementById('cmap').value,label:document.getElementById('vCmap').textContent})"))
print('DEFAULT_FILL', js("JSON.stringify(window.__fill())")[:400])

# 2) upN=7 开补株
setv('upN', 7); click('autoFill'); time.sleep(2.5)
f7 = js("JSON.stringify(window.__fill())")
print('UPN7_FILL', f7[:900])

# 3) upN=19 开补株
setv('upN', 19); time.sleep(3)
f19 = js("JSON.stringify(window.__fill())")
d19 = json.loads(f19)
print('UPN19_FILL', 'main=%d holes=%d fillCount=%d d=%.3f cmap=%s' % (
    len(d19['main']), len(d19['holes']), d19['fillCount'], d19['d'] or 0, d19['cmap']))
# 验证补株重心：到最近3主株距离应≈d/√3
if d19['main'] and d19['holes']:
    import math
    d = d19['d']; expect = d/math.sqrt(3)
    errs=[]
    for h in d19['holes'][:6]:
        ds=sorted(math.hypot(h['x']-p['x'],h['z']-p['z']) for p in d19['main'])[:3]
        errs.append(round((sum(ds)/3-expect)/expect,3))
    print('HOLE_CENTROID_RELERR(first6)', errs, 'expect d/sqrt3=%.3f'%expect)

# 4) 俯视截图（相机设顶视）upN=19 补株开
setv('upN',19); time.sleep(1)
js("(function(){var c=document.getElementById('cv');})()")
shot('_dev/holefill_u19_topdown.png')

# 5) upN=7 补株开 俯视
setv('upN',7); time.sleep(2.5)
shot('_dev/holefill_u7_topdown.png')

print('ERRS', len(ERRS), ERRS[:5])
try: proc.terminate()
except Exception: pass
print('DONE')
