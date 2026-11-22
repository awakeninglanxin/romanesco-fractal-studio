# -*- coding: utf-8 -*-
"""默认展示参数(upBuds=25/hex60) + 正五边形花盘预设(5株中空/6株中实) 验证。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket

PORT = 9471
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_pent_9471')
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
_mid = [0]
ERRORS = []

def call(method, params=None):
    _mid[0] += 1; i = _mid[0]
    ws.send(json.dumps({'id': i, 'method': method, 'params': params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get('method') == 'Runtime.exceptionThrown':
            ERRORS.append(msg['params']['exceptionDetails'].get('text', 'exception'))
        if msg.get('method') == 'Log.entryAdded':
            e = msg['params']['entry']
            if e.get('level') == 'error': ERRORS.append(e.get('text', 'log error'))
        if msg.get('id') == i: return msg

def js(expr):
    r = call('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
    return r.get('result', {}).get('result', {}).get('value')

def setv(id_, v, ev='input'):
    js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()" % (id_, json.dumps(str(v)), ev))

def shot(path, clip=None):
    p = {'format':'png'}
    if clip: p['clip'] = clip
    d = call('Page.captureScreenshot', p)['result']['data']
    open(path,'wb').write(base64.b64decode(d))
    print('SHOT', path, os.path.getsize(path))

call('Page.enable'); call('Runtime.enable'); call('Log.enable'); call('Network.enable')
call('Network.setCacheDisabled', {'cacheDisabled': True})
url = 'http://127.0.0.1:8899/' + urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate', {'url': url})
for _ in range(120):
    if js("document.getElementById('hudBody') && document.getElementById('hudBody').innerText.indexOf('锥体总数') >= 0"): break
    time.sleep(0.5)
time.sleep(1.5)

print('=== 1. 默认展示参数 ===')
dflt = js("JSON.stringify({preset:document.getElementById('preset').value,upBuds:document.getElementById('upBuds').value,vUpBuds:document.getElementById('vUpBuds').textContent,spiralMode:document.getElementById('spiralMode').value,vSpiralMode:document.getElementById('vSpiralMode').textContent,cmap:document.getElementById('cmap').value})")
print('DEFAULT', dflt)
d = json.loads(dflt)
assert d['upBuds']=='25' and d['vUpBuds']=='25', '默认芽数应为25'
assert d['spiralMode']=='hex60', '默认应为六重60°'
assert js("document.getElementById('trimApex').checked")==True, '删除顶尖锥默认应开'

import re
def conecount():
    t = js("document.getElementById('hudBody').innerText") or ''
    m = re.search(r'锥体总数\s*(\d+)', t)
    return int(m.group(1)) if m else -1

print('=== 1b. 删除顶尖绿锥（trimApex 开/关）===')
setv('prog',1000); time.sleep(1.2)
n_on = conecount()
# 关闭删除顶尖锥
js("(function(){var e=document.getElementById('trimApex');e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}));})()")
time.sleep(2.0)
n_off = conecount()
shot('预览_删顶尖锥_关闭_对照.png', {'x':0,'y':0,'width':1240,'height':1000,'scale':1})
# 重新开启
js("(function(){var e=document.getElementById('trimApex');e.checked=true;e.dispatchEvent(new Event('change',{bubbles:true}));})()")
time.sleep(2.0)
n_on2 = conecount()
shot('预览_删顶尖锥_开启_默认.png', {'x':0,'y':0,'width':1240,'height':1000,'scale':1})
print('CONES on=%d off=%d on2=%d diff=%d' % (n_on,n_off,n_on2,n_off-n_on))
assert n_off>n_on and n_on2==n_on, '删除顶尖锥应使锥数减少且可逆'
setv('prog',0)

print('=== 2. 正五边形 · 单一预设 + 补中心开关（5株中空）===')
setv('preset','pent','change'); time.sleep(2.0)
js("(function(){var e=document.getElementById('pentSolid');e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}));})()")
time.sleep(1.5)
setv('prog',1000); time.sleep(1.5)
p5 = js("JSON.stringify(window.__poly?window.__poly():null)")
print('PENT 5hollow', p5)
q5 = json.loads(p5)
assert q5['form']=='pent' and q5['pentSolid']==False and q5['flowers']==5, '应为5株中空'
print('HUD5', (js("document.getElementById('hudBody').innerText") or '').replace('\n',' | '))
shot('预览_正五边形_5株中空.png', {'x':0,'y':0,'width':1240,'height':1000,'scale':1})

print('=== 3. 正五边形 · 补中心（6株中实）===')
js("(function(){var e=document.getElementById('pentSolid');e.checked=true;e.dispatchEvent(new Event('change',{bubbles:true}));})()")
time.sleep(1.5)
setv('prog',1000); time.sleep(1.5)
p6 = js("JSON.stringify(window.__poly?window.__poly():null)")
print('PENT 6solid', p6)
q6 = json.loads(p6)
assert q6['form']=='pent' and q6['pentSolid']==True and q6['flowers']==6, '应为6株中实'
print('HUD6', (js("document.getElementById('hudBody').innerText") or '').replace('\n',' | '))
shot('预览_正五边形_6株中实.png', {'x':0,'y':0,'width':1240,'height':1000,'scale':1})

print('=== 4. 视角保持（调芽数）===')
c0 = js("JSON.stringify([window.__cam.theta(),window.__cam.phi(),window.__cam.radius()])")
setv('upBuds',40); time.sleep(1.2)
setv('upBuds',25); time.sleep(1.2)
c1 = js("JSON.stringify([window.__cam.theta(),window.__cam.phi(),window.__cam.radius()])")
print('CAM', c0, c1, 'SAME', c0==c1)
assert c0==c1, '视角应保持'

print('=== 4b. 发散角一键按钮（45° / 黄金角）===')
js("document.getElementById('btnAngle45').click()"); time.sleep(0.6)
a45 = js("JSON.stringify([window.__S?window.__S.angleDeg:document.getElementById('angle').value,document.getElementById('vAngle').textContent])")
print('ANGLE45', a45)
assert '45' in a45, '45°按钮应设角度为45'
js("document.getElementById('btnAngleGolden').click()"); time.sleep(0.6)
ag = js("JSON.stringify([document.getElementById('angle').value,document.getElementById('vAngle').textContent])")
print('ANGLE_GOLDEN', ag)
qg = json.loads(ag)
assert abs(float(qg[0])-137.508)<0.01 and '137.508' in qg[1], '黄金角按钮应设137.508°'
c2 = js("JSON.stringify([window.__cam.theta(),window.__cam.phi(),window.__cam.radius()])")
assert c0==c2, '按钮调角视角应保持'

print('=== 5. 导出（pent 模式）===')
call('Runtime.evaluate', {'expression': "window.__blobSizes=[];var _o=URL.createObjectURL;URL.createObjectURL=function(b){window.__blobSizes.push(b.size);return _o(b);};"})
for f in ['stl','obj','ply']:
    setv('expFmt', f, 'change'); time.sleep(0.2)
    js("document.getElementById('btnSTL').click()"); time.sleep(1.2)
blobs = js("JSON.stringify(window.__blobSizes)")
print('BLOBS', blobs)
assert all(s and s>0 for s in json.loads(blobs)), '导出应非空'

print('=== 6. 全部预设切换 ===')
for p in ['romanesco','cauliflower','broccoli','upright','xmas','bucky','pent','upright']:
    setv('preset',p,'change'); time.sleep(1.0)
    print('PRESET', p, (js("document.getElementById('hudBody').innerText.split('\\n')[0]") or ''))
print('BACK_HEX', js("document.getElementById('hexBase').checked"), 'BACK_MODE', js("document.getElementById('spiralMode').value"))

print('ERRORS', len(ERRORS), json.dumps(ERRORS[:8], ensure_ascii=False))
assert len(ERRORS)==0, '零JS错误'
try: proc.terminate()
except Exception: pass
print('ALL_PASS')
