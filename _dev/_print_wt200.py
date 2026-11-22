# -*- coding: utf-8 -*-
"""3D 打印水密体重铸验证：
   ① 普通导出的拓扑（非流形边应 >0，证明"视觉实体"确实不水密）
   ② SDF+SurfaceNets 重铸后的拓扑（非流形边=0、边界边=0 → 闭合流形）
   ③ 体积/体素/耗时/文件字节数
   ④ 截图参数台状态"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9451; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_wt_9451')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
  '--enable-unsafe-swiftshader','--window-size=1200,900','--hide-scrollbars',
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
t=targets();ws=websocket.create_connection(t['webSocketDebuggerUrl'],timeout=900,suppress_origin=True)
mid=[0]
def call(m,p=None):
  mid[0]+=1;n=mid[0];ws.send(json.dumps({'id':n,'method':m,'params':p or {}}))
  while True:
    r=json.loads(ws.recv())
    if r.get('id')==n:return r
def js(e,awaitp=False):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':awaitp}).get('result',{}).get('result',{}).get('value')
def shot(p,clip=None):
  par={'format':'png'}
  if clip:par['clip']=clip
  d=call('Page.captureScreenshot',par)['result']['data']
  open(p,'wb').write(base64.b64decode(d));print('SHOT',p,flush=True)
call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
js("""
(function(){
  if(window.__blobHook)return;window.__blobHook=1;window.__lastBlob=0;
  var _cu=URL.createObjectURL;
  URL.createObjectURL=function(b){try{window.__lastBlob=b.size;}catch(e){}return _cu.call(URL,b);};
})()""")

def run(form,res,base,tag):
  js("var e=document.getElementById('preset');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}));"%form)
  time.sleep(5.0)
  nt=js("JSON.stringify(window.__normalTopo())")
  print('[%s] normal-topo: %s'%(tag,nt),flush=True)
  r=js("""(function(){try{var t0=performance.now();
      var n=window.__printRun(%d,%s);
      return JSON.stringify({n:n,ms:Math.round(performance.now()-t0),
        st:window.__print(),blob:window.__lastBlob});
    }catch(e){return 'ERR:'+e.message;}})()"""%(res,'true' if base else 'false'))
  print('[%s] watertight: %s'%(tag,r),flush=True)
  d=json.loads(nt or '{}')
  try: ok=json.loads(r)
  except Exception: ok={}
  st=ok.get('st') or {}
  goodnum = (st.get('nonManifold')==0 and st.get('boundary')==0 and (st.get('tris') or 0)>0)
  print('   => 普通导出非流形边=%s / 重铸后非流形边=%s 边界边=%s 三角面=%s 体素=%.2fmm 体积=%.0fcm3 %s'%(
      d.get('nonManifold'),st.get('nonManifold'),st.get('boundary'),st.get('tris'),
      (st.get('vox') or 0),(st.get('volume') or 0)/1000,
      'OK' if goodnum else 'FAIL'),flush=True)
  return ok

run("romanesco",200,True,"romanesco-200")
run("upright",200,True,"upright-200")
run('upright',96,False,'upright-96-nobase')
run('cauliflower',144,True,'cauliflower-144(裁剪)')
print('ERR:',js("document.getElementById('err').style.display"),flush=True)
shot('../预览_水密体重铸_面板.png')
print('DONE',flush=True)
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
