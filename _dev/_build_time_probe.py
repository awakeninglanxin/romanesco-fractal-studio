# -*- coding: utf-8 -*-
"""测几何重建耗时：levels 1..5（poly）+ 切预设，判断调参流畅度。"""
import time, os, json, subprocess, urllib.request, urllib.parse
import websocket

BASE = 'http://127.0.0.1:8899/'
URL = BASE + urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
if not os.path.exists(CHROME):
    CHROME = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'

proc = subprocess.Popen([CHROME, '--headless=new', '--remote-debugging-port=9334',
                         '--disable-gpu', '--window-size=1280,900',
                         '--user-data-dir=' + os.path.join(os.getcwd(), '_cdp_bd'),
                         'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9334/json').read())
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

cmd('Page.enable'); cmd('Page.navigate', {'url': URL}); time.sleep(3)

print('=== poly 形态：levels 1..5 重建耗时 (ms) ===')
js("var e=document.getElementById('preset');e.value='bucky';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(8)
for lv in [1, 2, 3, 4, 5]:
    ms = js("""(function(){
      var el=document.getElementById('levels'); el.value=%d;
      var t0=performance.now();
      el.dispatchEvent(new Event('input',{bubbles:true}));
      el.dispatchEvent(new Event('change',{bubbles:true}));
      return Math.round(performance.now()-t0);
    })()""" % lv)
    time.sleep(4)
    a = js("JSON.stringify(window.__axis?window.__axis():{})")
    try:
        d = json.loads(a)
    except Exception:
        d = {}
    print('  levels=%d  rebuild=%sms  cones=%s  budsEff=%s' % (lv, ms, d.get('count'), d.get('budsEff')))

print('\n=== 切预设耗时 (ms) ===')
for v in ['romanesco', 'cauliflower', 'broccoli', 'upright', 'xmas', 'bucky', 'pent']:
    ms = js("""(function(){
      var e=document.getElementById('preset'); e.value='%s';
      var t0=performance.now();
      e.dispatchEvent(new Event('change',{bubbles:true}));
      return Math.round(performance.now()-t0);
    })()""" % v)
    print('  %-12s %sms' % (v, ms))
    time.sleep(2.5)

print('\n=== 内存/资源 ===')
print(js("""(function(){
  var g=renderer.info;
  return JSON.stringify({geometries:g.memory.geometries,textures:g.memory.textures,
    drawCalls:g.render.calls,triangles:g.render.triangles,
    heapMB: performance.memory?Math.round(performance.memory.usedJSHeapSize/1048576):null});
})()"""))
print('ERR:', js("document.getElementById('err').style.display"))
ws.close(); proc.terminate()
