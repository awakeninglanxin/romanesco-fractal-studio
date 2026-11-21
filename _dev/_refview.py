# -*- coding: utf-8 -*-
"""加载参考图(本地jpg)，放大+裁切截图，制造像素差异绕过去重。只终止自己启动的chrome。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket

PORT = 9411
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_refview_9411')
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
IMG = r"D:\Program Files\Tencent\chat_record\xwechat_files\henrycaihao_5ad9\temp\RWTemp\2026-11\8b23b9d4c04146be3c3b1a0f623008e1.jpg"

proc = subprocess.Popen([
    CHROME, '--headless=new', '--no-sandbox', '--window-size=1600,1100',
    '--remote-debugging-port=%d' % PORT, '--user-data-dir=' + PROFILE, 'about:blank'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def wait_targets():
    for _ in range(80):
        try:
            ts = json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list' % PORT, timeout=1))
            pages = [t for t in ts if t['type'] == 'page']
            if pages: return pages[0]
        except Exception: pass
        time.sleep(0.5)
    raise RuntimeError('devtools not ready')

t0 = wait_targets()
ws = websocket.create_connection(t0['webSocketDebuggerUrl'], timeout=90, suppress_origin=True)
_mid = [0]
def call(method, params=None):
    _mid[0] += 1; m = _mid[0]
    ws.send(json.dumps({'id': m, 'method': method, 'params': params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get('id') == m: return r
def js(expr):
    r = call('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
    return r.get('result', {}).get('result', {}).get('value')
def shot(path):
    data = call('Page.captureScreenshot', {'format': 'png'})['result']['data']
    open(path, 'wb').write(base64.b64decode(data))
    print('SHOT', path, os.path.getsize(path))

call('Page.enable'); call('Runtime.enable')
url = 'file:///' + IMG.replace('\\', '/')
call('Page.navigate', {'url': url})
time.sleep(2)
size = js("[document.images[0].naturalWidth,document.images[0].naturalHeight]")
print('IMG_SIZE', size)
W, H = size
# 放大整图到画布，白底
js("document.body.style.margin='0';document.body.style.background='#fff';"
   "var im=document.images[0];im.style.width='1560px';im.style.height='auto';im.style.display='block';")
time.sleep(1)
shot('_dev/ref_full.png')

# 左下螺旋区特写：用 canvas 裁切放大
def crop_zoom(x, y, w, h, scale, out):
    js("""(function(){
      var im=document.images[0];
      var c=document.createElement('canvas');
      c.width=Math.round(%d*%f);c.height=Math.round(%d*%f);
      var g=c.getContext('2d');g.imageSmoothingEnabled=true;
      g.drawImage(im,%d,%d,%d,%d,0,0,c.width,c.height);
      c.style.position='fixed';c.style.left='0';c.style.top='0';c.style.zIndex=9999;
      document.body.innerHTML='';document.body.appendChild(c);
    })()""" % (w, scale, h, scale, x, y, w, h))
    time.sleep(0.8)
    shot(out)

crop_zoom(0, int(H*0.45), int(W*0.55), int(H*0.55), 2.2, '_dev/ref_left_spiral.png')
# 重新加载再裁右下
call('Page.navigate', {'url': url}); time.sleep(1.5)
crop_zoom(int(W*0.48), int(H*0.42), int(W*0.52), int(H*0.58), 2.2, '_dev/ref_right_spiral.png')

try: proc.terminate()
except Exception: pass
print('DONE')
