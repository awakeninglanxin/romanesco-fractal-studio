# -*- coding: utf-8 -*-
"""验证自动补株新算法：内部三角孔(occ=3) + 边缘缺口(occ=2) 都补，坐标由格点三角形重心给出。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse, math
import websocket
PORT=9411; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_filledge_9411')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1400,900','--hide-scrollbars',
  '--remote-debugging-port=%d'%PORT,'--user-data-dir='+PROFILE,'about:blank'],
  stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def targets():
  for _ in range(80):
    try:
      ts=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list'%PORT,timeout=1))
      p=[t for t in ts if t['type']=='page']
      if p:return p[0]
    except Exception:pass
    time.sleep(0.5)
  raise RuntimeError('no devtools')
t=targets();ws=websocket.create_connection(t['webSocketDebuggerUrl'],timeout=180,suppress_origin=True)
mid=[0]
def call(m,p=None):
  mid[0]+=1;n=mid[0];ws.send(json.dumps({'id':n,'method':m,'params':p or {}}))
  while True:
    r=json.loads(ws.recv())
    if r.get('id')==n:return r
def js(e,awaitp=False):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':awaitp}).get('result',{}).get('result',{}).get('value')
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)

# 1) 切到直立花盘 + 开自动填满
js("var e=document.getElementById('preset');e.value='upright';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(1.5)
if js("document.getElementById('autoFill').checked")!=True:
  js("var c=document.getElementById('autoFill');c.checked=true;c.dispatchEvent(new Event('change',{bubbles:true}));")
  time.sleep(1.5)

# 2) 几何自检：补株重心到多少株主株的距离≈d/√3
CHECK="""(function(){
  var F=window.__fill(),d=F.d,rr=d/Math.sqrt(3),main=F.main,out=[];
  F.holes.forEach(function(h){
    var cnt=0,mind=1e9;
    main.forEach(function(m){var dd=Math.hypot(m.x-h.x,m.z-h.z);
      if(dd<rr*1.02){cnt++;} if(dd<mind)mind=dd;});
    out.push({x:+h.x.toFixed(4),z:+h.z.toFixed(4),edge:!!h.edge,nearest:cnt,mind:+mind.toFixed(4)});
  });
  return JSON.stringify({d:d,rr:+rr.toFixed(4),n:F.holes.length,
    edgeHoles:out.filter(function(o){return o.edge}),
    bad:out.filter(function(o){return o.edge?o.nearest!==2:o.nearest!==3})});
})()"""

print('%-6s %-6s %-8s %-8s %-8s %s'%('upN','total','inner','edge','expect','note'))
allok=True
for upN,expI,expE in [(1,0,0),(7,6,6),(19,24,12),(37,54,18)]:
  js("var s=document.getElementById('upN');s.value=%d;s.dispatchEvent(new Event('input',{bubbles:true}));"%upN)
  time.sleep(2.2)
  F=json.loads(js("JSON.stringify(window.__fill())"))
  nI,nE=F['fillInner'],F['fillEdge']
  c=json.loads(js(CHECK))
  err=js("document.getElementById('err').style.display")
  ok=(nI==expI and nE==expE and len(c['bad'])==0 and err!='block')
  allok=allok and ok
  print('%-6d %-6d %-8d %-8d %-8s %s'%(upN,F['fillCount'],nI,nE,'%d+%d'%(expI,expE),
        'OK' if ok else 'FAIL  bad=%s err=%s'%(c['bad'][:3],err)))
  if upN==7:
    print('   upN=7 补株坐标(前12):')
    for o in c['edgeHoles']:print('     edge  x=%8.4f z=%8.4f 距离d/√3的邻居数=%d mind=%.4f'%(o['x'],o['z'],o['nearest'],o['mind']))
    tot=json.loads(js(CHECK))
    for o in [x for x in json.loads(js(CHECK))['edgeHoles']]:
      pass
  if upN in (7,19):
    dat=call('Page.captureScreenshot',{'format':'png'})['result']['data']
    pth='../预览_补株_内部+边缘缺口_upN%d.png'%upN; open(pth,'wb').write(base64.b64decode(dat)); print('   SHOT',pth)
  if upN==7:
    # 内部孔也打印一遍
    inn=json.loads(js(CHECK))
    print('   全部补株: total=%d (inner=%d, edge=%d)'%(inn['n'],inn['n']-len(inn['edgeHoles']),len(inn['edgeHoles'])))
    print('   非标准位置数(nearest 不等于 2/3)=',len(inn['bad']))
print('HUD:',js("document.getElementById('hudBody').innerText").replace('\n',' | '))
print('RESULT:','ALL_PASS' if allok else 'HAS_FAIL')
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
