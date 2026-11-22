# -*- coding: utf-8 -*-
"""验证自动填满：复现老师参数（upN=19 间距1.00 十重36°），对比开/关三角孔洞。只终止自己启动的 chrome。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket

PORT = 9361
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_autofill_9361')
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc = subprocess.Popen([
    CHROME, '--headless=new', '--no-sandbox', '--enable-webgl',
    '--use-gl=swiftshader', '--enable-unsafe-swiftshader',
    '--window-size=1510,962', '--hide-scrollbars',
    '--remote-debugging-port=%d' % PORT, '--user-data-dir=' + PROFILE,
    'about:blank'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def wait_targets():
    for _ in range(80):
        try:
            ts = json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list' % PORT, timeout=1))
            pages = [t for t in ts if t['type'] == 'page']
            if pages:
                return pages[0]
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError('devtools not ready')

t0 = wait_targets()
ws = websocket.create_connection(t0['webSocketDebuggerUrl'], timeout=90, suppress_origin=True)
_mid = [0]
def call(method, params=None):
    _mid[0] += 1
    m = _mid[0]
    ws.send(json.dumps({'id': m, 'method': method, 'params': params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get('id') == m:
            return r
def js(expr):
    r = call('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
    return r.get('result', {}).get('result', {}).get('value')
def shot(path):
    r = call('Page.captureScreenshot', {'format': 'png'})
    with open(path, 'wb') as f:
        f.write(base64.b64decode(r['result']['data']))
    print('SHOT', path, os.path.getsize(path))

call('Page.enable'); call('Runtime.enable'); call('Network.enable')
call('Network.setCacheDisabled', {'cacheDisabled': True})
url = 'http://127.0.0.1:8899/' + urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate', {'url': url})
for _ in range(80):
    if js("typeof THREE!=='undefined' && !!document.getElementById('cv') && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):
        break
    time.sleep(0.5)
time.sleep(2)
js("var c=document.getElementById('spin');if(c.checked)c.click();")

def setv(id, val, ev):
    js("var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));" % (id, json.dumps(str(val)), ev))
def click(id):
    js("document.getElementById('%s').click();" % id)

def setup(upn, spread, buds, levels, algo, cm='viridis'):
    click('btnReset')
    setv('preset', 'upright', 'change')
    time.sleep(0.4)
    setv('upN', upn, 'input')
    setv('upSpread', spread, 'input')
    setv('upBuds', buds, 'input')
    setv('levels', levels, 'input')
    setv('spiralMode', algo, 'change')
    setv('cmap', cm, 'change')
    setv('prog', 1000, 'input')
    time.sleep(2.5)

# 关闭自动填满（默认）
setup(19, 10, 30, 3, 'dec36')
js("document.getElementById('btnTop').click();")
time.sleep(1)
shot('_dev/af_off.png')
print('HUD_OFF:', js("document.getElementById('hudBody').innerText").replace('\n',' | '))
print('ERR_OFF:', js("document.getElementById('err').style.display"))

# 开启自动填满
click('autoFill')
time.sleep(2.5)
js("document.getElementById('btnTop').click();")
time.sleep(1)
shot('_dev/af_on.png')
print('HUD_ON:', js("document.getElementById('hudBody').innerText").replace('\n',' | '))
print('ERR_ON:', js("document.getElementById('err').style.display"))

# 调补株大小到 0.85
setv('fillK', 85, 'input')
time.sleep(2)
js("document.getElementById('btnTop').click();")
time.sleep(1)
shot('_dev/af_on_085.png')
print('HUD_085:', js("document.getElementById('hudBody').innerText").replace('\n',' | '))

# 导出验证（hook blob）
js("""window.__blobs=[];var _o=URL.createObjectURL;URL.createObjectURL=function(b){window.__blobs.push(b.size);return _o.apply(this,arguments);};""")
for f in ['stl','obj','ply','step']:
    setv('expFmt', f, 'change')
    click('btnSTL')
    time.sleep(1.5)
print('BLOBS:', js("JSON.stringify(window.__blobs)"))
print('ERR_FINAL:', js("document.getElementById('err').style.display"))

ws.close()
proc.terminate()
try:
    proc.wait(timeout=5)
except Exception:
    proc.kill()
print('DONE')
