# -*- coding: utf-8 -*-
"""最终导出回归：三种 grow 形态(cull+trunk 开启) STL/OBJ/PLY 非空 + 零错误。"""
import time, os, json, subprocess, urllib.request, urllib.parse
import websocket
PORT=9489
PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_fexp_9489')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
 '--enable-unsafe-swiftshader','--window-size=1280,900','--hide-scrollbars',
 '--remote-debugging-port=%d'%PORT,'--user-data-dir='+PROFILE,'about:blank'],
 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def wait():
 for _ in range(100):
  try:
   tabs=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list'%PORT,timeout=1))
   p=[t for t in tabs if t['type']=='page']
   if p:return p[0]
  except:pass
  time.sleep(0.4)
 raise RuntimeError('no devtools')
tab=wait();ws=websocket.create_connection(tab['webSocketDebuggerUrl'],timeout=300,suppress_origin=True)
_mid=[0];ERR=[]
def call(m,p=None):
 _mid[0]+=1;i=_mid[0];ws.send(json.dumps({'id':i,'method':m,'params':p or {}}))
 while True:
  msg=json.loads(ws.recv())
  if msg.get('method')=='Runtime.exceptionThrown':ERR.append(msg['params']['exceptionDetails'].get('text','ex'))
  if msg.get('method')=='Log.entryAdded':
   e=msg['params']['entry']
   if e.get('level')=='error':ERR.append(e.get('text','logerr'))
  if msg.get('id')==i:return msg
def js(e):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('result',{}).get('value')
def setv(i,v,ev='input'):js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()"%(i,json.dumps(str(v)),ev))
call('Page.enable');call('Runtime.enable');call('Log.enable')
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(120):
 if js("document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"):break
 time.sleep(0.5)
time.sleep(1.5)
# hook download 捕获 Blob 大小
js("""(function(){window.__blobSizes={};var _c=URL.createObjectURL;URL.createObjectURL=function(b){try{window.__blobSizes[(b.type||'bin')]=b.size;}catch(e){}return _c.apply(this,arguments);};})()""")
print('=== 三形态导出(cull+trunk 默认开) ===')
for p in ['romanesco','cauliflower','broccoli']:
 setv('preset',p,'change');time.sleep(1.4)
 for fmt in ['stl','obj','ply']:
  js("window.__blobSizes={};window.__exporters.%s();"%fmt);time.sleep(0.5)
  sizes=js("JSON.stringify(window.__blobSizes)") or '{}'
  sz=json.loads(sizes);total=sum(sz.values()) if sz else 0
  print('%s %s total=%d sizes=%s'%(p,fmt,total,sz))
  assert total>0, p+' '+fmt+' 导出为空'
print('ERRORS',ERR)
assert not ERR,'有JS错误'
print('ALL_PASS')
sp=subprocess;sp.Popen(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=sp.DEVNULL,stderr=sp.DEVNULL)
