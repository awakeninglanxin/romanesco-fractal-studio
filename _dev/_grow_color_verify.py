# -*- coding: utf-8 -*-
"""任务1验证：三种基础分形(grow)螺旋臂配色 seq 生效 + cmap/臂数/缠绕度即时响应。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket

PORT = 9481
PROFILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'wb_growcolor_9481')
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
def shot(path):
    d=call('Page.captureScreenshot',{'format':'png','clip':{'x':0,'y':0,'width':1240,'height':1000,'scale':1}})['result']['data']
    open(path,'wb').write(base64.b64decode(d)); print('SHOT',path,os.path.getsize(path))
def growStat():
    return json.loads(js("JSON.stringify(window.__grow?window.__grow():null)"))

call('Page.enable'); call('Runtime.enable'); call('Log.enable'); call('Network.enable')
call('Network.setCacheDisabled',{'cacheDisabled':True})
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(120):
    if js("document.getElementById('hudBody') && document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"): break
    time.sleep(0.5)
time.sleep(1.5)

print('=== 1. 三种 grow 形态 seq/臂号/颜色分布（修复前 seqDistinct=1）===')
for p in ['romanesco','cauliflower','broccoli']:
    setv('preset',p,'change'); time.sleep(1.8)
    st=growStat()
    print('GROW',p,'leaves=%d withSeq=%d seqDistinct=%d armDistinct=%d colorDistinct=%d cmap=%s'%(
        st['leaves'],st['withSeq'],st['seqDistinct'],st['armDistinct'],st['colorDistinct'],st['cmap']))
    assert st['withSeq']>0, p+' 叶锥仍缺 seq'
    assert st['seqDistinct']>=3 and st['armDistinct']>=3, p+' 螺旋臂号应多样'
    assert st['colorDistinct']>=3, p+' 颜色应多样（不再单一）'

print('=== 2. 臂数 fibArms 变化 → 颜色分布变化 ===')
setv('preset','romanesco','change'); time.sleep(1.6)
setv('cmap','fib','change'); time.sleep(1.4)
setv('fibArms','8','change'); time.sleep(1.2); a8=growStat()
setv('fibArms','21','change'); time.sleep(1.2); a21=growStat()
print('ARMS 8 -> colorDistinct=%d arms=%d ; 21 -> colorDistinct=%d arms=%d'%(
    a8['colorDistinct'],a8['armDistinct'],a21['colorDistinct'],a21['armDistinct']))
assert a8['sampleColors']!=a21['sampleColors'] or a8['armDistinct']!=a21['armDistinct'], '臂数变化应改变配色'

print('=== 3. 缠绕度 fibTwist 变化 → 颜色分布变化 ===')
setv('fibArms','13','change'); time.sleep(1.0)
setv('fibTwist','0'); time.sleep(1.2); t0=growStat()
setv('fibTwist','60'); time.sleep(1.2); t60=growStat()
print('TWIST 0 -> arms=%d colors=%s ; 60 -> arms=%d colors=%s'%(
    t0['armDistinct'],t0['sampleColors'][:3],t60['armDistinct'],t60['sampleColors'][:3]))
assert t0['sampleColors']!=t60['sampleColors'], '缠绕度变化应改变配色'

print('=== 4. hsvarm / fib 切换都有色 ===')
for cm in ['hsvarm','fib']:
    setv('cmap',cm,'change'); time.sleep(1.2)
    st=growStat()
    print('CMAP',cm,'colorDistinct=%d'%st['colorDistinct'])
    assert st['colorDistinct']>=3, cm+' 配色退化'
    shot('_dev/grow_%s.png'%cm)

print('ERRORS',ERRORS)
assert not ERRORS, '存在 JS 错误'
print('ALL_PASS')
import subprocess as sp
sp.Popen(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=sp.DEVNULL,stderr=sp.DEVNULL)
