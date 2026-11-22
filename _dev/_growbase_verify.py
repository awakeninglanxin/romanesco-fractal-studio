# -*- coding: utf-8 -*-
"""任务3验证：三种分形塔落地底盘 + 修复底盘导出 bug + 形状/开关即时响应。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket

PORT = 9483
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_growbase_9483')
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
ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=300, suppress_origin=True)
_mid=[0]; ERRORS=[]
def call(method, params=None):
    _mid[0]+=1; i=_mid[0]
    ws.send(json.dumps({'id':i,'method':method,'params':params or {}}))
    while True:
        msg=json.loads(ws.recv())
        if msg.get('method')=='Runtime.exceptionThrown': ERRORS.append(msg['params']['exceptionDetails'].get('text','exception'))
        if msg.get('method')=='Log.entryAdded':
            e=msg['params']['entry']
            if e.get('level')=='error': ERRORS.append(e.get('text','log error'))
        if msg.get('id')==i: return msg
def js(expr):
    r=call('Runtime.evaluate',{'expression':expr,'returnByValue':True,'awaitPromise':True})
    return r.get('result',{}).get('result',{}).get('value')
def setv(id_,v,ev='input'):
    js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()"%(id_,json.dumps(str(v)),ev))
def toggle(id_,val):
    js("(function(){var e=document.getElementById('%s');e.checked=%s;e.dispatchEvent(new Event('change',{bubbles:true}));})()"%(id_,'true' if val else 'false'))
def shot(path):
    d=call('Page.captureScreenshot',{'format':'png','clip':{'x':0,'y':0,'width':1240,'height':1000,'scale':1}})['result']['data']
    open(path,'wb').write(base64.b64decode(d)); print('SHOT',path,os.path.getsize(path))
def gs(): return json.loads(js("JSON.stringify(window.__grow?window.__grow():null)"))
def cam(): return js("JSON.stringify([window.__cam.theta(),window.__cam.phi(),window.__cam.radius()])")

call('Page.enable'); call('Runtime.enable'); call('Log.enable'); call('Network.enable')
call('Network.setCacheDisabled',{'cacheDisabled':True})
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(120):
    if js("document.getElementById('hudBody') && document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"): break
    time.sleep(0.5)
time.sleep(1.5)

print('=== 1. 三种分形塔落地底盘存在 + 导出含底盘 ===')
for p in ['romanesco','cauliflower','broccoli']:
    setv('preset',p,'change'); time.sleep(1.6)
    setv('prog',1000); time.sleep(1.2)
    st=gs()
    print('GROW',p,'growBase=%s shape=%s baseTris=%d exportTris=%d'%(
        st['growBase'],st['growBaseShape'],st['growBaseTris'],st['exportTris']))
    assert st['growBase'] and st['growBaseTris']>0, p+' 落地底盘未生成'
    assert st['exportTris']>0, p+' 导出为空'
    shot('_dev/growbase_%s.png'%p)

print('=== 2. 底盘开关：关→底盘消失、导出减少；开→恢复 ===')
setv('preset','romanesco','change'); time.sleep(1.5); setv('prog',1000); time.sleep(1.0)
on=gs(); toggle('growBase',False); time.sleep(1.2); off=gs(); toggle('growBase',True); time.sleep(1.2); on2=gs()
print('TOGGLE on baseTris=%d exp=%d | off baseTris=%d exp=%d | on2 baseTris=%d exp=%d'%(
    on['growBaseTris'],on['exportTris'],off['growBaseTris'],off['exportTris'],on2['growBaseTris'],on2['exportTris']))
assert off['growBaseTris']==0 and off['exportTris']<on['exportTris'], '关底盘应使导出减少'
assert on2['growBaseTris']==on['growBaseTris'] and on2['exportTris']==on['exportTris'], '重开应恢复'

print('=== 3. 形状切换 round(48边→更多三角) vs hex(6边) ===')
setv('growBaseShape','hex','change'); time.sleep(1.2); hexst=gs()
setv('growBaseShape','round','change'); time.sleep(1.2); rndst=gs()
print('SHAPE hex baseTris=%d exp=%d | round baseTris=%d exp=%d'%(
    hexst['growBaseTris'],hexst['exportTris'],rndst['growBaseTris'],rndst['exportTris']))
assert rndst['growBaseTris']!=hexst['growBaseTris'] and rndst['growBaseShape']=='round', '形状切换应改变底盘三角数'
shot('_dev/growbase_hex.png') if False else None

print('=== 4. 视角保持 ===')
c0=cam(); setv('growBaseShape','hex','change'); time.sleep(1.0); toggle('growBase',False); time.sleep(1.0); c1=cam()
print('CAM',c0,c1,'SAME',c0==c1)
assert c0==c1, '调底盘参数视角应保持'

print('ERRORS',ERRORS)
assert not ERRORS, '存在 JS 错误'
print('ALL_PASS')
sp=subprocess
sp.Popen(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=sp.DEVNULL,stderr=sp.DEVNULL)
