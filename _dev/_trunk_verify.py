# -*- coding: utf-8 -*-
"""验证第0级连片主体：trunkBase/trunkAll 开关 + 三形态截图 + 零错误 + 视角保持。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9487
PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_trunk_9487')
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([CHROME,'--headless=new','--no-sandbox','--enable-webgl','--use-gl=swiftshader',
 '--enable-unsafe-swiftshader','--window-size=1602,1002','--hide-scrollbars',
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
def toggle(i,v):js("(function(){var e=document.getElementById('%s');e.checked=%s;e.dispatchEvent(new Event('change',{bubbles:true}));})()"%(i,'true' if v else 'false'))
def shot(p,clip=None):
 prm={'format':'png'}
 if clip:prm['clip']=clip
 d=call('Page.captureScreenshot',prm)['result']['data']
 open(p,'wb').write(base64.b64decode(d));print('SHOT',p,os.path.getsize(p))
def ax():return json.loads(js("JSON.stringify(window.__axis())"))
def cam():return js("JSON.stringify([window.__cam.theta(),window.__cam.phi(),window.__cam.radius()])")
CLIP={'x':150,'y':80,'width':900,'height':700,'scale':1}
call('Page.enable');call('Runtime.enable');call('Log.enable')
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(120):
 if js("document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"):break
 time.sleep(0.5)
time.sleep(1.5)

print('=== 1. 三形态第0级主体开关 ===')
for p in ['romanesco','cauliflower','broccoli']:
 setv('preset',p,'change');time.sleep(1.4)
 setv('prog',1000);time.sleep(1.0)
 toggle('trunkBase',True);time.sleep(1.0);on=ax()
 toggle('trunkBase',False);time.sleep(1.0);off=ax()
 toggle('trunkBase',True);time.sleep(1.0)
 print('%s ON count=%d trunkCones=%d | OFF count=%d trunkCones=%d'%(
   p,on['count'],on['trunkCones'],off['count'],off['trunkCones']))
 assert on['trunkCones']==1, p+' 根级主体应恰好1个'
 assert off['trunkCones']==0, p+' 关闭后无主体锥'
 assert on['count']==off['count']+1, p+' 主体锥应贡献1个锥'
 shot('_dev/trunk_%s_on.png'%p,CLIP)

print('=== 2. trunkAll 每级中轴 ===')
setv('preset','romanesco','change');time.sleep(1.2);setv('prog',1000);time.sleep(0.8)
toggle('trunkAll',False);time.sleep(1.0);one=ax()
toggle('trunkAll',True);time.sleep(1.0);allv=ax()
print('trunkAll OFF trunkCones=%d | ON trunkCones=%d'%(one['trunkCones'],allv['trunkCones']))
assert allv['trunkCones']>one['trunkCones'], 'trunkAll 应渲染更多中轴锥'
toggle('trunkAll',False);time.sleep(0.8)
shot('_dev/trunk_romanesco_all.png',CLIP)

print('=== 3. 视角保持 ===')
c0=cam();toggle('trunkBase',False);time.sleep(1.0);c1=cam()
print('CAM',c0,c1,'SAME',c0==c1)
assert c0==c1,'视角应保持'

print('ERRORS',ERR)
assert not ERR,'有JS错误'
print('ALL_PASS')
sp=subprocess;sp.Popen(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=sp.DEVNULL,stderr=sp.DEVNULL)
