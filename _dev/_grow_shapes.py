# -*- coding: utf-8 -*-
"""拍摄三种 grow 形态（prog=1000）对比轮廓差异 + 保存截图。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket

PORT = 9482
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_shapes_9482')
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
            if pages: return pages[0]
        except Exception: pass
        time.sleep(0.4)
    raise RuntimeError('no devtools')

tab = wait_devtools()
ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=240, suppress_origin=True)
_mid=[0]; ERRORS=[]
def call(method, params=None):
    _mid[0]+=1; i=_mid[0]
    ws.send(json.dumps({'id':i,'method':method,'params':params or {}}))
    while True:
        msg=json.loads(ws.recv())
        if msg.get('method')=='Runtime.exceptionThrown': ERRORS.append(msg['params']['exceptionDetails'].get('text','exception'))
        if msg.get('id')==i: return msg
def js(expr):
    r=call('Runtime.evaluate',{'expression':expr,'returnByValue':True,'awaitPromise':True})
    return r.get('result',{}).get('result',{}).get('value')
def setv(id_,v,ev='input'):
    js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()"%(id_,json.dumps(str(v)),ev))
def shot(path):
    d=call('Page.captureScreenshot',{'format':'png','clip':{'x':0,'y':0,'width':1240,'height':1000,'scale':1}})['result']['data']
    open(path,'wb').write(base64.b64decode(d)); print('SHOT',path,os.path.getsize(path))

call('Page.enable'); call('Runtime.enable'); call('Log.enable'); call('Network.enable')
call('Network.setCacheDisabled',{'cacheDisabled':True})
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(120):
    if js("document.getElementById('hudBody') && document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"): break
    time.sleep(0.5)
time.sleep(1.5)

for p in ['romanesco','cauliflower','broccoli']:
    setv('preset',p,'change'); time.sleep(1.6)
    setv('prog',1000); time.sleep(1.4)     # 关键：prog=100% 才渲染出模型
    hud=(js("document.getElementById('hudBody').innerText") or '').replace('\n',' | ')
    print('SHAPE',p,hud[:120])
    shot('预览_形态_%s.png'%p)
print('ERRORS',ERRORS)
sp=subprocess
sp.Popen(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=sp.DEVNULL,stderr=sp.DEVNULL)
