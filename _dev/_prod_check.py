# -*- coding: utf-8 -*-
"""生产页面（无 ?debug=1）功能验证 + 截图"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket

BASE = 'http://127.0.0.1:8899/'
URL = BASE + urllib.parse.quote('罗马花椰菜_分形生长参数台.html')   # 不带 debug
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
if not os.path.exists(CHROME):
    CHROME = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
OUT = r'D:\AAA我的文件\西兰花3d建模网页展示'

proc = subprocess.Popen([CHROME, '--headless=new', '--remote-debugging-port=9337',
                         '--disable-gpu', '--window-size=1440,900',
                         '--user-data-dir=' + os.path.join(os.getcwd(), '_cdp_pd'),
                         'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9337/json').read())
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

def shot(name):
    r = cmd('Page.captureScreenshot', {'format': 'png'})
    d = r.get('result', {}).get('data')
    if d:
        p = os.path.join(OUT, name)
        open(p, 'wb').write(base64.b64decode(d))
        print('  saved', name, os.path.getsize(p) // 1024, 'KB')

cmd('Page.enable'); cmd('Page.navigate', {'url': URL}); time.sleep(4)

print('=== 生产页面（无 debug 参数）===')
print('  __axis 暴露?', js("typeof window.__axis"))          # 应为 undefined
print('  err 显示?', js("document.getElementById('err').style.display"))

# 导出按钮能用（依赖内部 EXPORTERS，不依赖 window.__exporters）
js("document.getElementById('expFmt').value='stl';")
js("document.getElementById('stlSeg').value='3';document.getElementById('stlSeg').dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(0.3)
js("document.getElementById('btnSTL').click();")
time.sleep(6)
print('  导出结果:', js("document.getElementById('stlInfo').innerText"))

# 切预设（生产页也要正常）
for v in ['bucky', 'romanesco', 'upright']:
    js("var e=document.getElementById('preset');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));" % v)
    time.sleep(6)
    print('  切到 %-10s  HUD已长出=%s  err=%s' % (
        v, js("(document.getElementById('hudBody').innerText.match(/已长出[^\\n]*/)||[''])[0]"),
        js("document.getElementById('err').style.display")))

print('\n=== 截图 ===')
js("var e=document.getElementById('preset');e.value='upright';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(6)
shot('预览_优化后_直立花盘.png')

# 手动显示导出遮罩，确认样式（浅色系）
js("document.getElementById('busyT').textContent='正在导出 OBJ…';"
   "document.getElementById('busyS').textContent='共 138,960 个锥 · 请稍候';"
   "document.getElementById('busy').classList.add('on');")
time.sleep(0.4)
shot('预览_优化后_导出遮罩.png')
js("document.getElementById('busy').classList.remove('on');")

js("var e=document.getElementById('preset');e.value='bucky';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(10)
shot('预览_优化后_正60面体.png')

ws.close(); proc.terminate()
