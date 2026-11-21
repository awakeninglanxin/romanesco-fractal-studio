# -*- coding: utf-8 -*-
"""验证缠绕度滑杆真正改变图形 + 臂数默认13 + 整体导出。"""
import time,os,json,base64,subprocess,urllib.request,urllib.parse
import websocket
PORT=9443;PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_twist_9443')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
 '--enable-unsafe-swiftshader','--window-size=1564,1002','--hide-scrollbars',
 '--remote-debugging-port=%d'%PORT,'--user-data-dir='+PROFILE,'about:blank'],
 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def wait():
    for _ in range(80):
        try:
            ts=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list'%PORT,timeout=1))
            ps=[t for t in ts if t['type']=='page']
            if ps:return ps[0]
        except Exception:pass
        time.sleep(0.5)
    raise RuntimeError('no devtools')
t0=wait();ws=websocket.create_connection(t0['webSocketDebuggerUrl'],timeout=120,suppress_origin=True)
_m=[0]
def call(m,p=None):
    _m[0]+=1;i=_m[0];ws.send(json.dumps({'id':i,'method':m,'params':p or {}}))
    while True:
        r=json.loads(ws.recv())
        if r.get('id')==i:return r
def js(e):
    r=call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True})
    return r.get('result',{}).get('result',{}).get('value')
def setv(id,v,ev='input'):
    js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()"%(id,v,ev))
def shot_raw():
    return call('Page.captureScreenshot',{'format':'png'})['result']['data']
def shot(p):
    d=shot_raw();open(p,'wb').write(base64.b64decode(d));print('SHOT',p,os.path.getsize(p))
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')
call('Page.navigate',{'url':url})
for _ in range(90):
    if js("document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"):break
    time.sleep(0.5)
time.sleep(1.5)
print('DEFAULTS',js("JSON.stringify({arms:document.getElementById('fibArms').value,twist:document.getElementById('fibTwist').value,cmap:document.getElementById('cmap').value})"))
js("(function(){document.getElementById('btnTop')&&document.getElementById('btnTop').click();})()");time.sleep(1)
# 缠绕度 0 / 2.6 / 6 截图对比
imgs={}
for tw in [0,26,60]:
    setv('fibTwist',tw);time.sleep(1.2)
    imgs[tw]=shot_raw()
    shot('_dev/twist_%d.png'%tw)
print('TWIST_0_eq_26',imgs[0]==imgs[26])
print('TWIST_26_eq_60',imgs[26]==imgs[60])
# 臂数10? 用13(默认) 21
setv('fibTwist',26);time.sleep(1)
setv('fibArms',21,'change');time.sleep(1.2);shot('_dev/twist_arms21.png')
print('ERR',js("(window.__errs||[]).length"))
try:proc.terminate()
except Exception:pass
print('DONE')
