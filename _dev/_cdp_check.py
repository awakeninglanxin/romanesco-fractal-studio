# -*- coding: utf-8 -*-
"""用 CDP 驱动 headless Chrome：底部视角验证单株底盘六边形蜂窝。只终止自己启动的 chrome 进程。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket

PORT = 9333
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_cdp_hexbase_9333')
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

proc = subprocess.Popen([
    CHROME, '--headless=new', '--no-sandbox', '--enable-webgl',
    '--use-gl=swiftshader', '--enable-unsafe-swiftshader',
    '--window-size=1500,950', '--hide-scrollbars',
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
    data = r['result']['data']
    with open(path, 'wb') as f:
        f.write(base64.b64decode(data))
    print('SHOT', path, os.path.getsize(path))

call('Page.enable'); call('Runtime.enable')
url = 'http://127.0.0.1:8899/' + urllib.parse.quote('罗马花椰菜_分形生长参数台.html')
call('Page.navigate', {'url': url})
for _ in range(80):
    if js("typeof THREE!=='undefined' && !!document.getElementById('cv') && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):
        break
    time.sleep(0.5)
time.sleep(2)

js("var c=document.getElementById('spin');if(c.checked)c.click();")

def setup(preset, upn, buds, levels):
    js("""(function(){
      var s=document.getElementById('preset');s.value='%s';s.dispatchEvent(new Event('change',{bubbles:true}));
      var u=document.getElementById('upN');u.value=%d;u.dispatchEvent(new Event('input',{bubbles:true}));
      var b=document.getElementById('upBuds');b.value=%d;b.dispatchEvent(new Event('input',{bubbles:true}));
      var lv=document.getElementById('levels');lv.value=%d;lv.dispatchEvent(new Event('input',{bubbles:true}));
      var p=document.getElementById('prog');p.value=1000;p.dispatchEvent(new Event('input',{bubbles:true}));
    })()""" % (preset, upn, buds, levels))
    time.sleep(3)

def bottom():
    rect = json.loads(js("JSON.stringify(document.getElementById('cv').getBoundingClientRect())"))
    cx = rect['left'] + rect['width']/2; cy = rect['top'] + rect['height']/2
    call('Input.dispatchMouseEvent', {'type':'mousePressed','x':cx,'y':cy+250,'button':'left','buttons':1,'clickCount':1})
    call('Input.dispatchMouseEvent', {'type':'mouseMoved','x':cx,'y':cy+250-360,'button':'left','buttons':1})
    call('Input.dispatchMouseEvent', {'type':'mouseReleased','x':cx,'y':cy-110,'button':'left','buttons':0,'clickCount':1})
    time.sleep(1)

def top():
    js("document.getElementById('btnTop').click()")
    time.sleep(1)

setup('upright', 1, 24, 3)
bottom(); shot('_dev/hex_single_bottom.png')
top();    shot('_dev/hex_single_top.png')

setup('upright', 7, 24, 3)
bottom(); shot('_dev/hex_7_bottom.png')
top();    shot('_dev/hex_7_top.png')

print('HUD:', js("document.getElementById('hudBody').innerText").replace('\n', ' | '))
print('ERR:', js("document.getElementById('err').style.display"))
print('LEAVES:', js("(function(){try{return document.getElementById('hudBody').innerText}catch(e){return e.message}})()")[:200])

ws.close()
proc.terminate()
try:
    proc.wait(timeout=5)
except Exception:
    proc.kill()
print('DONE')
