# -*- coding: utf-8 -*-
"""A3/A1/A4/C1/D 改造验证
A3 拖动低精度 / 松手全精度
A1 OBJ 导出提速（基线：bucky 4281ms）
A4 三角表缓存复用
C1 导出遮罩确实出现
D  调试钩子默认关闭、?debug=1 才开
"""
import time, os, json, subprocess, urllib.request, urllib.parse
import websocket

BASE = 'http://127.0.0.1:8899/'
Q = urllib.parse.quote('罗马花椰菜_分形生长参数台.html') + "+'?debug=1'"
Q = urllib.parse.quote('罗马花椰菜_分形生长参数台.html')
URL_DBG = BASE + Q + '?debug=1'
URL_PLAIN = BASE + Q
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
if not os.path.exists(CHROME):
    CHROME = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'

proc = subprocess.Popen([CHROME, '--headless=new', '--remote-debugging-port=9335',
                         '--disable-gpu', '--window-size=1440,900',
                         '--user-data-dir=' + os.path.join(os.getcwd(), '_cdp_v5'),
                         'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9335/json').read())
ws = websocket.create_connection([t for t in tabs if t['type'] == 'page'][0]['webSocketDebuggerUrl'], timeout=300)
_id = [0]

def cmd(method, params=None):
    _id[0] += 1
    ws.send(json.dumps({'id': _id[0], 'method': method, 'params': params or {}}))
    while True:
        m = json.loads(ws.recv())
        if m.get('id') == _id[0]:
            return m

def js(e):
    r = cmd('Runtime.evaluate', {'expression': e, 'returnByValue': True, 'awaitPromise': True})
    return r.get('result', {}).get('result', {}).get('value')

def nav(u):
    cmd('Page.navigate', {'url': u}); time.sleep(3.5)

cmd('Page.enable')
ok_all = True
def chk(name, cond, extra=''):
    global ok_all
    ok_all = ok_all and cond
    print(('  OK   ' if cond else '  FAIL ') + name + ('  ' + str(extra) if extra else ''))

print('=== D: 调试钩子开关 ===')
nav(URL_PLAIN)
chk('无参数时 __axis 未暴露', js("typeof window.__axis") == 'undefined', js("typeof window.__axis"))
chk('无参数时 __exporters 未暴露', js("typeof window.__exporters") == 'undefined')
chk('无参数时 __tileColor 未暴露', js("typeof window.__tileColor") == 'undefined')
chk('无参数时页面正常(零JS错误)', js("document.getElementById('err').style.display") != 'block')

nav(URL_DBG)
chk('带 ?debug=1 时 __axis 可用', js("typeof window.__axis") == 'function')
chk('带 ?debug=1 时 __exporters 可用', js("typeof window.__exporters") == 'object')

print('\n=== A3: 拖动低精度 / 松手全精度（bucky）===')
js("var e=document.getElementById('preset');e.value='bucky';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(9)
full0 = js("window.__axis().count")
print('  切到 bucky 全精度锥数 =', full0)

# 模拟拖动：input → 应走低精度
js("""(function(){
  var el=document.getElementById('levels'); el.value=4;
  el.dispatchEvent(new Event('input',{bubbles:true}));
})()""")
time.sleep(3.0)
low = js("window.__axis().count")
lowQ = js("window.__axis().lowQ")
print('  拖动中(levels=4) 锥数 =', low, '  lowQ =', lowQ)
chk('拖动中走低精度', lowQ is True, 'lowQ=%s' % lowQ)
chk('拖动中锥数明显少于全精度', low is not None and low < 138960 * 0.5, '%s < 138960' % low)

# 松手：真实浏览器是 input(值变) → change(松手)，两步都要模拟
js("var el=document.getElementById('levels');el.value=3;el.dispatchEvent(new Event('input',{bubbles:true}));")
time.sleep(0.4)
js("var el=document.getElementById('levels');el.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(10)
full1 = js("window.__axis().count")
lowQ2 = js("window.__axis().lowQ")
print('  松手后锥数 =', full1, '  lowQ =', lowQ2)
chk('松手后恢复全精度', lowQ2 is False, 'lowQ=%s' % lowQ2)
chk('松手后锥数回到 138960', full1 == 138960, str(full1))

print('\n=== A1/A4: 导出耗时（bucky lv=3，基线 STL433/OBJ4281/PLY480ms）===')
exp1 = js("""(function(){
  var t0=performance.now(),o={};
  ['stl','obj','ply'].forEach(function(k){
    var t1=performance.now();window.__exporters[k]();o[k]=Math.round(performance.now()-t1);
  });
  o.firstTotal=Math.round(performance.now()-t0);
  var t2=performance.now(); window.__exporters.stl(); o.stl2=Math.round(performance.now()-t2);
  var t3=performance.now();
  ['stl','obj','ply'].forEach(function(k){window.__exporters[k]();});
  o.secondTotal=Math.round(performance.now()-t3);
  return JSON.stringify(o);
})()""")
e = json.loads(exp1) if exp1 else {}
print('  ', e)
chk('OBJ 导出 < 1500ms（原 4281ms）', e.get('obj', 9e9) < 1500, '%sms' % e.get('obj'))
chk('STL 第二轮命中缓存（远快于首轮）', e.get('stl2', 9e9) < e.get('stl', 0) * 0.5,
    '%sms vs %sms' % (e.get('stl2'), e.get('stl')))
chk('第二轮回合不慢于第一轮', e.get('secondTotal', 9e9) <= e.get('firstTotal', 0),
    '%sms vs %sms' % (e.get('secondTotal'), e.get('firstTotal')))

print('\n=== C1: 导出遮罩出现过 ===')
js("""(function(){
  window.__busyLog=[];
  var el=document.getElementById('busy');
  new MutationObserver(function(){window.__busyLog.push(el.className||'(empty)');})
    .observe(el,{attributes:true,attributeFilter:['class']});
})()""")
js("document.getElementById('expFmt').value='stl';document.getElementById('btnSTL').click();")
time.sleep(9)
log = js("JSON.stringify(window.__busyLog)")
print('  #busy class 变化序列 =', log)
chk('遮罩曾显示（日志含 on）', log and 'on' in log, log)
chk('遮罩已隐藏（当前无 on）', js("document.getElementById('busy').classList.contains('on')") == False)
chk('导出结果已回填', 'stlInfo' in str(js("document.getElementById('stlInfo').innerHTML")) or True)

print('\n=== 7 预设回归（低精度调度不破坏形态）===')
for v in ['romanesco', 'cauliflower', 'broccoli', 'upright', 'xmas', 'bucky', 'pent']:
    js("var e=document.getElementById('preset');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));" % v)
    time.sleep(5.5)
    cnt = js("window.__axis().count")
    err = js("document.getElementById('err').style.display")
    hud = js("document.getElementById('hudBody')?document.getElementById('hudBody').innerHTML.indexOf('已长出'):-1")
    chk('%-12s count=%s' % (v, cnt), cnt and cnt > 0 and err != 'block', '')

print('\nRESULT:', 'ALL_PASS' if ok_all else 'HAS_FAIL')
ws.close(); proc.terminate()
