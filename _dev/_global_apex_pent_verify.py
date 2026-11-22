# -*- coding: utf-8 -*-
"""全局删顶尖锥(grow) + 正五边形相切不重叠 + 发散角45°按钮 验证。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse, math, re
import websocket

PORT = 9475
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_global_9475')
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
        if msg.get('method')=='Log.entryAdded':
            e=msg['params']['entry']
            if e.get('level')=='error': ERRORS.append(e.get('text','log error'))
        if msg.get('id')==i: return msg
def js(expr):
    r=call('Runtime.evaluate',{'expression':expr,'returnByValue':True,'awaitPromise':True})
    return r.get('result',{}).get('result',{}).get('value')
def setv(id_,v,ev='input'):
    js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()"%(id_,json.dumps(str(v)),ev))
def click(id_): js("document.getElementById('%s').click()"%id_)
def toggle(id_,val):
    js("(function(){var e=document.getElementById('%s');e.checked=%s;e.dispatchEvent(new Event('change',{bubbles:true}));})()"%(id_,'true' if val else 'false'))
def cones():
    t=js("document.getElementById('hudBody').innerText") or ''
    m=re.search(r'锥体总数\s*(\d+)',t)
    return int(m.group(1)) if m else -1
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

print('=== 1. 全局删顶尖锥：grow 三形态 trimApex 开/关 ===')
for p in ['romanesco','cauliflower','broccoli']:
    setv('preset',p,'change'); time.sleep(1.8)
    toggle('trimApex',True); time.sleep(1.2); on=cones()
    toggle('trimApex',False); time.sleep(1.2); off=cones()
    toggle('trimApex',True); time.sleep(1.2); on2=cones()
    print('GROW',p,'on=%d off=%d on2=%d diff=%d'%(on,off,on2,off-on))
    assert off>on and on2==on, p+' 全局删锥应生效且可逆'

print('=== 2. 正五边形：单一预设 + 补中心圆锥开关，第一级相切不重叠 ===')
setv('preset','pent','change'); time.sleep(2.0)
for solid,expect,tag in [(False,5,'5hollow'),(True,6,'6solid')]:
    toggle('pentSolid',solid); time.sleep(1.2)
    setv('prog',1000); time.sleep(1.2)
    pp=json.loads(js("JSON.stringify(window.__poly?window.__poly():null)"))
    disks=pp.get('disks',[])
    print('PENT solid=%s flowers=%d disks=%d'%(solid,pp['flowers'],len(disks)))
    assert pp['pentSolid']==solid and pp['flowers']==expect and len(disks)==expect, '正五边形花盘数不符'
    # 两两不重叠：中心距 >= R1+R2（真实半径，留微小容差）
    minclear=1e9
    for i in range(len(disks)):
        for j in range(i+1,len(disks)):
            a,b=disks[i],disks[j]
            dist=math.sqrt((a['x']-b['x'])**2+(a['y']-b['y'])**2+(a['z']-b['z'])**2)
            clear=dist-(a['R']+b['R'])
            minclear=min(minclear,clear)
    print('  min clearance = %.4f (应 >= -0.01)'%minclear)
    assert minclear>=-0.02, '正五边形花盘重叠了'
    # 中心株应偏小
    if solid:
        center=[d for d in disks if abs(d['x'])<1e-6 and abs(d['z'])<1e-6]
        outer=[d for d in disks if d not in center]
        print('  centerR=%.4f outerR=%.4f ratio=%.2f'%(center[0]['R'],outer[0]['R'],center[0]['R']/outer[0]['R']))
        assert center[0]['R']<outer[0]['R']*0.8, '中心圆锥应明显偏小'
    shot('预览_%s_相切平放.png'%tag)

print('=== 3. 发散角一键 45° ===')
setv('preset','upright','change'); time.sleep(1.5)
click('btnAngle45'); time.sleep(1.5)
ang=js("JSON.stringify({v:document.getElementById('vAngle').textContent,slider:document.getElementById('angle').value})")
print('ANGLE45',ang)
d=json.loads(ang)
assert d['v']=='45.000°' and d['slider']=='45', '45°按钮应生效'

print('=== 4. 视角保持 ===')
c0=js("JSON.stringify([window.__cam.theta(),window.__cam.phi(),window.__cam.radius()])")
click('btnAngle45'); time.sleep(1.0)
c1=js("JSON.stringify([window.__cam.theta(),window.__cam.phi(),window.__cam.radius()])")
print('CAM',c0,c1,'SAME',c0==c1)
assert c0==c1

print('ERRORS',len(ERRORS),json.dumps(ERRORS[:8],ensure_ascii=False))
assert len(ERRORS)==0
try: proc.terminate()
except Exception: pass
print('ALL_PASS')
