# -*- coding: utf-8 -*-
"""最终综合验证 + 出预览图。"""
import time,os,json,base64,subprocess,urllib.request,urllib.parse
import websocket
PORT=9462;PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_finalall_9462')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
 '--enable-unsafe-swiftshader','--window-size=1602,1002','--hide-scrollbars',
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
t0=wait();ws=websocket.create_connection(t0['webSocketDebuggerUrl'],timeout=180,suppress_origin=True)
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
    js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()"%(id,json.dumps(str(v)),ev))
def shot(p):
    d=call('Page.captureScreenshot',{'format':'png'})['result']['data']
    open(p,'wb').write(base64.b64decode(d));print('SHOT',p,os.path.getsize(p))
def raw():return call('Page.captureScreenshot',{'format':'png'})['result']['data']
def zoom(n,dy):
    for _ in range(n):call('Input.dispatchMouseEvent',{'type':'mouseWheel','x':480,'y':420,'deltaX':0,'deltaY':dy})
    time.sleep(0.8)
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(90):
    if js("document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"):break
    time.sleep(0.5)
time.sleep(1.5)
print('DEFAULTS',js("JSON.stringify({form:S.form,cmap:S.cmap,arms:S.fibArms,twist:S.fibTwist,upN:S.upN,buds:S.upBuds,hex:S.hexBase,spin:S.spin,prog:S.prog})"))
# 1. 默认俯视（fib, upN=7, 无补株）
js("(function(){document.getElementById('btnTop')&&document.getElementById('btnTop').click();})()");time.sleep(1)
zoom(7,120)
shot('_dev/FINAL1_fib_default.png')
# 2. 补株12
js("(function(){var e=document.getElementById('autoFill');if(!e.checked){e.checked=true;e.dispatchEvent(new Event('change',{bubbles:true}));}})()");time.sleep(1.5)
print('FILL_HUD',[l for l in js("document.getElementById('hudBody').innerText").split('\n') if '补株' in l])
shot('_dev/FINAL2_fib_fill19.png')
# 3. hsvarm
setv('cmap','hsvarm','change');time.sleep(1.5)
print('CMAP_LABEL',js("document.getElementById('vCmap').textContent"))
shot('_dev/FINAL3_hsvarm.png')
# 4. 缠绕度生效（hsvarm下）
setv('fibTwist',0);time.sleep(1);a=raw()
setv('fibTwist',60);time.sleep(1);b=raw()
print('TWIST_DIFF',a!=b)
setv('fibTwist',26);time.sleep(0.5)
# 5. 5预设切换
setv('cmap','fib','change');time.sleep(0.5)
errs=[]
for p in ['romanesco','cauliflower','broccoli','upright','xmas']:
    setv('preset',p,'change');time.sleep(0.9)
    hud=js("document.getElementById('hudBody').innerText.split('\\n')[0]")
    print('PRESET',p,hud)
# 6. 导出4格式
setv('preset','upright','change');time.sleep(1)
call('Runtime.evaluate',{'expression':"window.__blobSizes=[];var _o=URL.createObjectURL;URL.createObjectURL=function(b){window.__blobSizes.push(b.size);return _o(b);};"})
for f in ['stl','obj','ply']:
    setv('expFmt',f,'change');time.sleep(0.3)
    call('Runtime.evaluate',{'expression':"document.getElementById('btnSTL').click()"});time.sleep(0.8)
print('BLOBS',js("JSON.stringify(window.__blobSizes)"))
print('ERR',js("(window.__errs||[]).length"))
try:proc.terminate()
except Exception:pass
print('DONE')
