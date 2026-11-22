# -*- coding: utf-8 -*-
"""验证"删除底面暴露锥"：开启后剩余锥世界轴 y 全 >= 阈值，开关/阈值即时生效，导出非空，视角保持。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9485
PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_cull_9485')
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
def js(e):
 return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('result',{}).get('value')
def setv(i,v,ev='input'):js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()"%(i,json.dumps(str(v)),ev))
def toggle(i,v):js("(function(){var e=document.getElementById('%s');e.checked=%s;e.dispatchEvent(new Event('change',{bubbles:true}));})()"%(i,'true' if v else 'false'))
def shot(p):
 d=call('Page.captureScreenshot',{'format':'png','clip':{'x':0,'y':0,'width':1240,'height':1000,'scale':1}})['result']['data']
 open(p,'wb').write(base64.b64decode(d));print('SHOT',p,os.path.getsize(p))
def ax():return json.loads(js("JSON.stringify(window.__axis())"))
def cam():return js("JSON.stringify([window.__cam.theta(),window.__cam.phi(),window.__cam.radius()])")
call('Page.enable');call('Runtime.enable');call('Log.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(120):
 if js("document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"):break
 time.sleep(0.5)
time.sleep(1.5)

print('=== 1. 老师参数(芽数3/21,白银比,发散45,倾角1) 开关对比 ===')
setv('preset','upright','change');time.sleep(1.5)
setv('spiralMode','silver','change');time.sleep(0.8)
setv('angle',45);time.sleep(0.8)
setv('upTilt',100);time.sleep(0.8)
for buds in [3,21]:
 setv('upBuds',buds);time.sleep(1.2)
 toggle('cullBottom',False);time.sleep(1.2);off=ax()
 toggle('cullBottom',True);time.sleep(1.2);on=ax()
 print('buds=%d OFF count=%d minY=%.3f neg=%d low=%d | ON count=%d minY=%.3f neg=%d low=%d culled=%d'%(
  buds,off['count'],off['minY'],off['neg'],off['low'],on['count'],on['minY'],on['neg'],on['low'],on['culled']))
 assert on['minY']>=on['cullFloor']-0.01, 'buds=%d 开启后仍有底面暴露锥(minY<阈值)'%buds
 assert on['culled']>0, 'buds=%d 应有锥被删'%buds
 assert on['neg']==0 and on['low']==0, 'buds=%d 不应再有轴翻转/近水平锥'%buds
 shot('_dev/cull_buds%d_on.png'%buds)

print('=== 2. 三种 grow 形态开启后无底面暴露锥 ===')
setv('preset','romanesco','change');time.sleep(1.0)  # 恢复常规参数
for p in ['romanesco','cauliflower','broccoli']:
 setv('preset',p,'change');time.sleep(1.5)
 on=ax()
 print('%s count=%d minY=%.3f neg=%d low=%d culled=%d'%(p,on['count'],on['minY'],on['neg'],on['low'],on['culled']))
 assert on['neg']==0 and on['low']==0, p+' 仍有底面暴露锥'
 shot('_dev/cull_%s_on.png'%p)

print('=== 3. 阈值即时生效 ===')
setv('preset','upright','change');time.sleep(1.2)
setv('cullFloor',10);time.sleep(1.2);t10=ax()
setv('cullFloor',60);time.sleep(1.2);t60=ax()
print('floor=0.10 culled=%d count=%d | floor=0.60 culled=%d count=%d'%(t10['culled'],t10['count'],t60['culled'],t60['count']))
assert t60['culled']>=t10['culled'], '阈值越高删越多'

print('=== 4. 视角保持 ===')
c0=cam();setv('cullFloor',35);time.sleep(1.0);toggle('cullBottom',False);time.sleep(1.0);c1=cam()
print('CAM',c0,c1,'SAME',c0==c1)
assert c0==c1,'视角应保持'

print('ERRORS',ERR)
assert not ERR,'有JS错误'
print('ALL_PASS')
sp=subprocess;sp.Popen(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=sp.DEVNULL,stderr=sp.DEVNULL)
