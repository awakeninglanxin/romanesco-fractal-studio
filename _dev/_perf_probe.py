# -*- coding: utf-8 -*-
"""性能探针：各预设的锥数 / 帧率 / 导出耗时 / 导出体积。
   只读，不改任何参数。用于判断优化优先级。"""
import time, os, json, subprocess, urllib.request, urllib.parse
import websocket

BASE = 'http://127.0.0.1:8899/'
FILE = urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
URL = BASE + FILE
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
if not os.path.exists(CHROME):
    CHROME = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'

proc = subprocess.Popen([CHROME, '--headless=new', '--remote-debugging-port=9333',
                         '--disable-gpu', '--window-size=1280,900',
                         '--user-data-dir=' + os.path.join(os.getcwd(), '_cdp_pf'),
                         'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9333/json').read())
ws_url = [t for t in tabs if t['type'] == 'page'][0]['webSocketDebuggerUrl']
ws = websocket.create_connection(ws_url, timeout=180)
_id = [0]

def cmd(method, params=None):
    _id[0] += 1
    ws.send(json.dumps({'id': _id[0], 'method': method, 'params': params or {}}))
    while True:
        m = json.loads(ws.recv())
        if m.get('id') == _id[0]:
            return m

def js(expr):
    r = cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
    return r.get('result', {}).get('result', {}).get('value')

cmd('Page.enable')
cmd('Page.navigate', {'url': URL})
time.sleep(3)

print('=== 各预设：锥数 / FPS / 导出耗时与体积 ===')
for v in ['romanesco', 'cauliflower', 'broccoli', 'upright', 'bucky', 'pent']:
    js("var e=document.getElementById('preset');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));" % v)
    time.sleep(3.0)
    info = js("""(function(){
      var a=window.__axis?window.__axis():{};
      // 清空帧计数，用 rAF 实测 60 帧
      return JSON.stringify({count:a.count, shown:document.getElementById('hud').innerHTML.match(/已长出[^0-9]*([0-9,]+)/)?document.getElementById('hud').innerHTML.match(/已长出[^0-9]*([0-9,]+)/)[1]:null});
    })()""")
    fps = js("""new Promise(function(res){
      var n=0,t0=performance.now();
      function tick(){n++;if(n<60)requestAnimationFrame(tick);else res(Math.round(60000/(performance.now()-t0)));}
      requestAnimationFrame(tick);
    })""")
    exp = js("""(function(){
      var t0=performance.now();
      var out={};
      ['stl','obj','ply'].forEach(function(k){
        var t1=performance.now();
        try{ window.__exporters[k](); }catch(e){ out[k+'Err']=String(e).slice(0,60); }
        out[k]=Math.round(performance.now()-t1);
      });
      out.total=Math.round(performance.now()-t0);
      out.bytes=(window.__blobs||[]).length;
      return JSON.stringify(out);
    })()""")
    err = js("document.getElementById('err').style.display")
    print('%-12s %-46s fps=%-4s export=%s err=%s' % (v, str(info)[:46], fps, exp, err))

print('\n=== 单帧三角面数（渲染压力）===')
print(js("""(function(){
  var n=0,inst=0;
  scene.traverse(function(o){
    if(o.isInstancedMesh){inst+=o.count;n+=o.count*(o.geometry.index?o.geometry.index.count/3:o.geometry.attributes.position.count/3);}
    else if(o.isMesh&&o.geometry){n+=(o.geometry.index?o.geometry.index.count/3:o.geometry.attributes.position.count/3);}
  });
  return 'instances='+inst+' triangles='+Math.round(n);
})()"""))

ws.close(); proc.terminate()
