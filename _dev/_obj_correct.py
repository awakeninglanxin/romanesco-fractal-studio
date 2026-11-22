# -*- coding: utf-8 -*-
"""OBJ 导出正确性 + 耗时校验（整型哈希表版）"""
import time, os, json, subprocess, urllib.request, urllib.parse
import websocket

BASE = 'http://127.0.0.1:8899/'
Q = urllib.parse.quote('罗马花椰菜_分形生长参数台.html')
URL = BASE + Q + '?debug=1'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
if not os.path.exists(CHROME):
    CHROME = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'

proc = subprocess.Popen([CHROME, '--headless=new', '--remote-debugging-port=9336',
                         '--disable-gpu', '--window-size=1440,900',
                         '--user-data-dir=' + os.path.join(os.getcwd(), '_cdp_oj'),
                         'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9336/json').read())
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

cmd('Page.enable'); cmd('Page.navigate', {'url': URL}); time.sleep(4)

# 捕获导出 blob
js("""(function(){
  window.__cap=[];
  var o=URL.createObjectURL;
  URL.createObjectURL=function(b){window.__cap.push(b);return o.call(URL,b);};
})()""")

for preset, lv in [('bucky', 3), ('upright', 3), ('pent', 3)]:
    js("var e=document.getElementById('preset');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));" % preset)
    time.sleep(2.5)
    js("var el=document.getElementById('levels');el.value=%d;el.dispatchEvent(new Event('input',{bubbles:true}));" % lv)
    time.sleep(0.3)
    js("var el=document.getElementById('levels');el.dispatchEvent(new Event('change',{bubbles:true}));")
    time.sleep(10)
    n = js("window.__axis().count")
    r = js("""(function(){
      window.__cap.length=0;
      var t0=performance.now();
      var tris=window.__exporters.obj();
      var ms=Math.round(performance.now()-t0);
      return JSON.stringify({tris:tris,ms:ms,nblob:window.__cap.length});
    })()""")
    info = json.loads(r) if r else {}
    print('\n[%s] cones=%s  obj=%s' % (preset, n, info))
    # 校验文件内容
    chk = js("""(async function(){
      var b=window.__cap[window.__cap.length-1];
      if(!b)return JSON.stringify({err:'no blob'});
      var txt=await b.text();
      var lines=txt.split('\\n');
      var nv=0,nf=0,maxIdx=0,badIdx=0,negIdx=0;
      for(var i=0;i<lines.length;i++){
        var L=lines[i];
        if(L.charCodeAt(0)===118&&L.charCodeAt(1)===32){nv++;}
        else if(L.charCodeAt(0)===102&&L.charCodeAt(1)===32){
          nf++;
          var p=L.split(' ');
          for(var k=1;k<4;k++){
            var a=parseInt(p[k],10);
            if(!isFinite(a)){badIdx++;continue;}
            if(a<1)negIdx++;
            if(a>maxIdx)maxIdx=a;
          }
        }
      }
      return JSON.stringify({bytes:b.size,nv:nv,nf:nf,maxIdx:maxIdx,
        idxOutOfRange:(maxIdx>nv),badIdx:badIdx,negIdx:negIdx,
        head:lines[0],head2:lines[1],head3:lines[2]});
    })()""")
    print('   file:', chk)

print('\nERR:', js("document.getElementById('err').style.display"))
ws.close(); proc.terminate()
