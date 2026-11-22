# -*- coding: utf-8 -*-
"""看补株12后全貌：滚轮缩小 + 俯视。"""
import time,os,json,base64,subprocess,urllib.request,urllib.parse
import websocket
PORT=9459;PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_fillov_9459')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
 '--enable-unsafe-swiftshader','--window-size=1606,1006','--hide-scrollbars',
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
def shot(p):
    d=call('Page.captureScreenshot',{'format':'png'})['result']['data']
    open(p,'wb').write(base64.b64decode(d));print('SHOT',p,os.path.getsize(p))
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(90):
    if js("document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"):break
    time.sleep(0.5)
time.sleep(1.5)
# 开补株，upN=7（默认已是7）
js("(function(){var e=document.getElementById('autoFill');if(!e.checked){e.checked=true;e.dispatchEvent(new Event('change',{bubbles:true}));}})()");time.sleep(1.5)
js("(function(){document.getElementById('btnTop')&&document.getElementById('btnTop').click();})()");time.sleep(1)
# 缩小（正 deltaY）
for _ in range(7):
    call('Input.dispatchMouseEvent',{'type':'mouseWheel','x':480,'y':420,'deltaX':0,'deltaY':120})
time.sleep(1)
shot('_dev/fill_overview4.png')
print('HUD',[l for l in js("document.getElementById('hudBody').innerText").split('\n') if '补株' in l])
try:proc.terminate()
except Exception:pass
print('DONE')
