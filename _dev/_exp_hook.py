# -*- coding: utf-8 -*-
"""hook URL.createObjectURL 捕获导出 Blob 的 size/type，验证 4 格式非空。"""
import time, json, subprocess, urllib.request, urllib.parse
import websocket
PORT=9335; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_exp_9335') if False else None
import os
PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_exp_9335')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
 '--enable-unsafe-swiftshader','--remote-debugging-port=%d'%PORT,'--user-data-dir='+PROFILE,'about:blank'],
 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
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
def js(e):
    return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('result',{}).get('value')
call('Page.enable');call('Runtime.enable')
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')})
for _ in range(80):
    if js("typeof THREE!=='undefined'&&!!document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.length>0"):break
    time.sleep(0.5)
time.sleep(2)
js("var s=document.getElementById('preset');s.value='upright';s.dispatchEvent(new Event('change',{bubbles:true}));var u=document.getElementById('upN');u.value=1;u.dispatchEvent(new Event('input',{bubbles:true}));var p=document.getElementById('prog');p.value=1000;p.dispatchEvent(new Event('input',{bubbles:true}));")
time.sleep(2)
# hook createObjectURL，捕获每次导出的 blob
js("""window.__blobs=[];var _ou=URL.createObjectURL.bind(URL);
URL.createObjectURL=function(b){window.__blobs.push({size:b.size,type:b.type});return _ou(b);};
var _ac=HTMLAnchorElement.prototype.click;HTMLAnchorElement.prototype.click=function(){};
""")
for fmt in ['stl','obj','ply','step']:
    js("window.__exporters['%s']();"%fmt)
print('BLOBS',js("JSON.stringify(window.__blobs)"))
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE')
