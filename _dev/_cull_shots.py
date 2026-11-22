# -*- coding: utf-8 -*-
"""拍"删除底面暴露锥"开/关对比图（prog=100%），验证老师红圈问题是否消除。"""
import time, os, json, base64, subprocess, urllib.request, urllib.parse
import websocket
PORT=9486
PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_cullshot_9486')
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
_mid=[0]
def call(m,p=None):
 _mid[0]+=1;i=_mid[0];ws.send(json.dumps({'id':i,'method':m,'params':p or {}}))
 while True:
  msg=json.loads(ws.recv())
  if msg.get('id')==i:return msg
def js(e):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('result',{}).get('value')
def setv(i,v,ev='input'):js("(function(){var e=document.getElementById('%s');e.value=%s;e.dispatchEvent(new Event('%s',{bubbles:true}));})()"%(i,json.dumps(str(v)),ev))
def toggle(i,v):js("(function(){var e=document.getElementById('%s');e.checked=%s;e.dispatchEvent(new Event('change',{bubbles:true}));})()"%(i,'true' if v else 'false'))
def shot(p,clip=None):
 prm={'format':'png'}
 if clip:prm['clip']=clip
 d=call('Page.captureScreenshot',prm)['result']['data']
 open(p,'wb').write(base64.b64decode(d));print('SHOT',p,os.path.getsize(p))
call('Page.enable');call('Runtime.enable')
url='http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
call('Page.navigate',{'url':url})
for _ in range(120):
 if js("document.getElementById('hudBody')&&document.getElementById('hudBody').innerText.indexOf('锥体总数')>=0"):break
 time.sleep(0.5)
time.sleep(1.5)

# 老师参数：芽数3 白银比 发散45 倾角1
setv('preset','upright','change');time.sleep(1.2)
setv('spiralMode','silver','change');time.sleep(0.6)
setv('angle',45);time.sleep(0.6)
setv('upTilt',100);time.sleep(0.6)
setv('upBuds',3);time.sleep(1.0)
setv('prog',1000);time.sleep(1.2)
toggle('cullBottom',False);time.sleep(1.2);shot('_dev/cullcmp_buds3_off.png',{'x':300,'y':150,'width':700,'height':550,'scale':1})
toggle('cullBottom',True);time.sleep(1.2);shot('_dev/cullcmp_buds3_on.png',{'x':300,'y':150,'width':700,'height':550,'scale':1})

# 芽数21
setv('upBuds',21);time.sleep(1.2);setv('prog',1000);time.sleep(1.0)
toggle('cullBottom',False);time.sleep(1.2);shot('_dev/cullcmp_buds21_off.png',{'x':300,'y':150,'width':700,'height':550,'scale':1})
toggle('cullBottom',True);time.sleep(1.2);shot('_dev/cullcmp_buds21_on.png',{'x':300,'y':150,'width':700,'height':550,'scale':1})
sp=subprocess;sp.Popen(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=sp.DEVNULL,stderr=sp.DEVNULL)
