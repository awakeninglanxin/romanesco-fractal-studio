# -*- coding: utf-8 -*-
"""补株模式下 STL/OBJ/PLY 导出非空回归。"""
import time, os, json, subprocess, urllib.request, urllib.parse
import websocket
PORT=9473
PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_holeexp_9473')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl',
 '--use-gl=swiftshader','--enable-unsafe-swiftshader','--window-size=1402,902',
 '--remote-debugging-port=%d'%PORT,'--user-data-dir='+PROFILE,'about:blank'],
 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(100):
    try:
        tabs=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list'%PORT,timeout=1))
        pages=[t for t in tabs if t['type']=='page']
        if pages:break
    except Exception:pass
    time.sleep(0.4)
ws=websocket.create_connection(pages[0]['webSocketDebuggerUrl'],timeout=240,suppress_origin=True)
m=[0];ERR=[]
def call(method,params=None):
    m[0]+=1;i=m[0]
    ws.send(json.dumps({'id':i,'method':method,'params':params or {}}))
    while True:
        r=json.loads(ws.recv())
        if r.get('method')=='Runtime.exceptionThrown':ERR.append(r['params']['exceptionDetails'].get('text'))
        if r.get('id')==i:return r
def js(e):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('result',{}).get('value')
def setv(id_,v,ev='input'):
    js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()"%(id_,json.dumps(str(v)),ev))
def click(id_):js("document.getElementById('%s').click()"%id_)
call('Page.enable');call('Runtime.enable')
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(100):
    if js("document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"):break
    time.sleep(0.5)
time.sleep(1)
setv('upN',7);click('autoFill');time.sleep(2.5)
print('FILL',js("JSON.stringify({n:window.__fill().fillCount,cmap:window.__fill().cmap})"))
# hook: 覆盖 URL.createObjectURL 捕获最后一个 Blob 的 size
js("window.__blobSizes=[];var _cu=URL.createObjectURL;URL.createObjectURL=function(b){window.__blobSizes.push(b.size);return _cu.apply(this,arguments);};")
for fmt in ['stl','obj','ply']:
    js("window.__exporters.%s()"%fmt)
    sz=js("window.__blobSizes[window.__blobSizes.length-1]")
    print('EXPORT',fmt,sz,'OK' if sz and sz>0 else 'FAIL')
print('ERRS',len(ERR),ERR[:5])
try:proc.terminate()
except Exception:pass
print('DONE')
