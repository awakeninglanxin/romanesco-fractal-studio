# -*- coding: utf-8 -*-
"""验证：斐波那契螺旋配色 + 六边形底盘朝向包络。俯视/侧视截图 + 状态读取。只终止自己起的chrome。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket

PORT = 9428
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_fibhex_9428')
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc = subprocess.Popen([
    CHROME, '--headless=new', '--no-sandbox', '--enable-webgl',
    '--use-gl=swiftshader', '--enable-unsafe-swiftshader',
    '--window-size=1542,982', '--hide-scrollbars',
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
ws = websocket.create_connection(t0['webSocketDebuggerUrl'], timeout=120, suppress_origin=True)
_mid=[0]
def call(method, params=None):
    _mid[0]+=1; m=_mid[0]
    ws.send(json.dumps({'id':m,'method':method,'params':params or {}}))
    while True:
        r=json.loads(ws.recv())
        if r.get('id')==m: return r
def js(expr):
    r=call('Runtime.evaluate',{'expression':expr,'returnByValue':True,'awaitPromise':True})
    res=r.get('result',{}).get('result',{})
    if 'exceptionDetails' in r.get('result',{}):
        print('JSERR',r['result']['exceptionDetails'].get('text'))
    return res.get('value')
def shot(path):
    data=call('Page.captureScreenshot',{'format':'png'})['result']['data']
    open(path,'wb').write(base64.b64decode(data)); print('SHOT',path,os.path.getsize(path))

call('Page.enable');call('Runtime.enable');call('Page.navigate',{'url':'about:blank'})
call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(90):
    if js("typeof THREE!=='undefined' && typeof S!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):
        break
    time.sleep(0.5)
time.sleep(2)

print('DEFAULT', js("JSON.stringify({form:S.form,cmap:S.cmap,fibArms:S.fibArms,fibTwist:S.fibTwist,upN:S.upN,hexBase:S.hexBase,prog:S.prog})"))
print('HUD', js("document.getElementById('hudBody').innerText"))

# 默认俯视（fib 配色 + 底盘）
call('Runtime.evaluate',{'expression':"document.getElementById('btnTop')&&document.getElementById('btnTop').click()"});time.sleep(1.5)
shot('_dev/FINAL_fib_top.png')

# 侧视：用相机接口设低仰角（若存在）
print('CAMAPI', js("typeof window.__setCam"))
js("if(typeof window.__setCam==='function'){window.__setCam(0.6,0.18);}") ; time.sleep(1.2)
shot('_dev/FINAL_fib_side.png')

# 单株特写：upN=7，fib配色，臂数13；关闭底盘看纯配色
js("""(function(){
  var e=document.getElementById('upN');e.value=7;e.dispatchEvent(new Event('input',{bubbles:true}));
})()""");time.sleep(1.2)
call('Runtime.evaluate',{'expression':"document.getElementById('btnTop')&&document.getElementById('btnTop').click()"});time.sleep(1.2)
shot('_dev/FINAL_fib_default.png')

# 臂数对比 8 / 21
for arms,name in [(8,'8'),(21,'21')]:
    js("(function(){var e=document.getElementById('fibArms');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));})()"%arms)
    time.sleep(1.2)
    shot('_dev/fibhex_arms%s.png'%name)

print('ERRCOUNT', js("(window.__errs||[]).length"))
try: proc.terminate()
except Exception: pass
print('DONE')
