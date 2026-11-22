# -*- coding: utf-8 -*-
"""综合验证：补株12 / 缠绕度生效 / hsvarm模式 / 视觉。"""
import time,os,json,base64,subprocess,urllib.request,urllib.parse
import websocket
PORT=9455;PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_multi_9455')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
 '--enable-unsafe-swiftshader','--window-size=1562,1000','--hide-scrollbars',
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
    vv=json.dumps(str(v))
    js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()"%(id,vv,ev))
def shot(p):
    d=call('Page.captureScreenshot',{'format':'png'})['result']['data']
    open(p,'wb').write(base64.b64decode(d));print('SHOT',p,os.path.getsize(p))
def raw():return call('Page.captureScreenshot',{'format':'png'})['result']['data']
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(90):
    if js("document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"):break
    time.sleep(0.5)
time.sleep(1.5)
# upN=7 + 自动填满
setv('upN',7);time.sleep(1)
js("(function(){var e=document.getElementById('autoFill');if(!e.checked){e.checked=true;e.dispatchEvent(new Event('change',{bubbles:true}));}})()");time.sleep(1.5)
print('HUD_FILL',js("document.getElementById('hudBody').innerText"))
print('AUTOFILL_STATE',js("document.getElementById('autoFill').checked"))
print('FILLCOUNT',js("S.fillCount"))
js("(function(){document.getElementById('btnTop')&&document.getElementById('btnTop').click();})()");time.sleep(1)
shot('_dev/multi_up7_fill.png')
# 缠绕度 0 vs 6（在 fib 模式）
setv('cmap','fib','change');time.sleep(1)
setv('fibTwist',0);time.sleep(1.2);a=raw()
setv('fibTwist',60);time.sleep(1.2);b=raw()
print('TWIST_DIFF',a!=b,len(a),len(b))
shot('_dev/multi_twist60.png')
# hsvarm 模式
setv('fibTwist',26);time.sleep(0.5)
setv('cmap','hsvarm','change');time.sleep(1.5)
print('HUD_HSVARM',js("document.getElementById('vCmap').textContent"))
shot('_dev/multi_hsvarm.png')
print('ERR',js("(window.__errs||[]).length"))
try:proc.terminate()
except Exception:pass
print('DONE')
