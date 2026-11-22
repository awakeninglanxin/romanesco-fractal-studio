# -*- coding: utf-8 -*-
"""单株八重对称侧视，prog=100%，分级配色，看层级分色。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9340; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_side4_9340')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
 '--enable-unsafe-swiftshader','--window-size=1512,964','--remote-debugging-port=%d'%PORT,
 '--user-data-dir='+PROFILE,'about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def target():
    for _ in range(80):
        try:
            ts=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list'%PORT,timeout=1))
            for t in ts:
                if t['type']=='page':return t
        except Exception:pass
        time.sleep(0.5)
    raise RuntimeError('no devtools')
ws=websocket.create_connection(target()['webSocketDebuggerUrl'],timeout=120,suppress_origin=True)
_m=[0]
def call(m,p=None):
    _m[0]+=1;i=_m[0];ws.send(json.dumps({'id':i,'method':m,'params':p or {}}))
    while True:
        r=json.loads(ws.recv())
        if r.get('id')==i:return r
def js(e):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('result',{}).get('value')
def shot(p):
    d=call('Page.captureScreenshot',{'format':'png'})['result']['data']
    open(p,'wb').write(base64.b64decode(d));print('SHOT',p,os.path.getsize(p))
call('Page.enable');call('Runtime.enable')
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
    if js("typeof THREE!=='undefined'&&!!document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.length>0"):break
    time.sleep(0.5)
time.sleep(2)
# 高度4层以看到分层；六重对称；分级配色；单株；prog满；斜视
js("""(function(){
var c=document.getElementById('spin');if(c.checked)c.click();
var s=document.getElementById('preset');s.value='upright';s.dispatchEvent(new Event('change',{bubbles:true}));
})()""");time.sleep(2)
def setv(id,val,ev='input'):
    js("var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));"%(id,json.dumps(str(val)),ev));time.sleep(1)
setv('levels',4);setv('upN',1);setv('spiralMode','hex60','change');setv('cmap','viridis','change')
setv('prog',1000)   # 最后设进度，避免被 buildFractal 重置
time.sleep(1)
print('HUD:',js("document.getElementById('hudBody').innerText").replace('\n',' | '))
shot('_dev/side_viridis2.png')
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
