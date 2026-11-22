# -*- coding: utf-8 -*-
"""老师建议：先看蜂窝单元数=1 的中心单株（7花球），验证不同螺旋臂异色。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9436;PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_para_9436')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1558,998','--hide-scrollbars',
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
def setv(id,v,ev='input'):
    js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()"%(id,v if isinstance(v,str) else "'%s'"%v,ev))
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(90):
    if js("document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"):break
    time.sleep(0.5)
time.sleep(1.5)
# 关底盘（看清配色），upN=1，芽数55
setv('hexBase',False,'change');time.sleep(0.8)
setv('upN',1);time.sleep(1.2)
print('HUD1',js("document.getElementById('hudBody').innerText.split('\\n')[0]"))
js("(function(){document.getElementById('btnTop')&&document.getElementById('btnTop').click();})()");time.sleep(1.2)
# 滚轮放大单株（画布中心约 x=465,y=400）
for _ in range(12):
    call('Input.dispatchMouseEvent',{'type':'mouseWheel','x':465,'y':400,'deltaX':0,'deltaY':-120})
time.sleep(1)
shot('_dev/para5_up1_top.png')
# 旋到侧视：用鼠标拖拽
call('Input.dispatchMouseEvent',{'type':'mousePressed','x':500,'y':400,'button':'left','buttons':1,'clickCount':1})
call('Input.dispatchMouseEvent',{'type':'mouseMoved','x':500,'y':560,'button':'left','buttons':1})
call('Input.dispatchMouseEvent',{'type':'mouseReleased','x':500,'y':560,'button':'left','buttons':0})
time.sleep(1.2);shot('_dev/para5_up1_side.png')
# 8臂 对比
setv('fibArms',8,'change');time.sleep(1.2)
shot('_dev/para5_up1_8arm.png')
# 21臂
setv('fibArms',21,'change');time.sleep(1.2)
shot('_dev/para5_up1_21arm.png')
print('ERR',js("(window.__errs||[]).length"))
try:proc.terminate()
except Exception:pass
print('DONE')
