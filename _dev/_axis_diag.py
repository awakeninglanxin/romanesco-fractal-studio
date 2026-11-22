# -*- coding: utf-8 -*-
"""诊断：各形态/参数下叶锥世界轴向 y 分布，判断底面暴露成因。"""
import time, os, json, subprocess, urllib.request, urllib.parse
import websocket
PORT=9484
PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_axis_9484')
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
tab=wait();ws=websocket.create_connection(tab['webSocketDebuggerUrl'],timeout=240,suppress_origin=True)
_mid=[0];ERR=[]
def call(m,p=None):
 _mid[0]+=1;i=_mid[0];ws.send(json.dumps({'id':i,'method':m,'params':p or {}}))
 while True:
  msg=json.loads(ws.recv())
  if msg.get('method')=='Runtime.exceptionThrown':ERR.append(msg['params']['exceptionDetails'].get('text','ex'))
  if msg.get('id')==i:return msg
def js(e):
 return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('result',{}).get('value')
def setv(i,v,ev='input'):js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()"%(i,json.dumps(str(v)),ev))
call('Page.enable');call('Runtime.enable');call('Log.enable')
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(120):
 if js("document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"):break
 time.sleep(0.5)
time.sleep(1.5)

print('=== 老师截图参数：upright + 芽数3/21 + 白银比61.7 + 发散45 + 子锥倾角1 ===')
setv('preset','upright','change');time.sleep(1.5)
setv('spiralMode','silver','change');time.sleep(1.0)
setv('angle',45);time.sleep(1.0)
setv('upTilt',100);time.sleep(1.0)   # 子锥倾角1.00
for buds in [3,6,10,15,21,30]:
 setv('upBuds',buds);time.sleep(1.2)
 a=json.loads(js("JSON.stringify(window.__axis())"))
 print('buds=%2d count=%5d minY=%+.3f neg(尖朝下)=%4d low(y<.35)=%4d hist[neg,low,mid,high,vhigh]=%s'%(
   buds,a['count'],a['minY'],a['neg'],a['low'],a['hist']))

print('=== 其它形态默认 ===')
for p in ['romanesco','cauliflower','broccoli','xmas']:
 setv('preset',p,'change');time.sleep(1.5)
 a=json.loads(js("JSON.stringify(window.__axis())"))
 print('%s count=%5d minY=%+.3f neg=%4d low=%4d hist=%s'%(p,a['count'],a['minY'],a['neg'],a['low'],a['hist']))
print('ERR',ERR)
sp.Popen(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=sp.DEVNULL,stderr=sp.DEVNULL)
