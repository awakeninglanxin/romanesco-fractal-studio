# -*- coding: utf-8 -*-
"""正60面体灰底覆盖率量化：解码 PNG(无PIL)，统计"灰面砖像素"占比，扫描贴片比例系数。"""
import time, os, json, base64, zlib, struct, subprocess, urllib.request, urllib.parse
import websocket
PORT=9424; PROFILE=os.path.join(os.environ.get('TEMP','/tmp'),'wb_tune_9424')
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
t=targets();ws=websocket.create_connection(t['webSocketDebuggerUrl'],timeout=180,suppress_origin=True)
mid=[0]
def call(m,p=None):
  mid[0]+=1;n=mid[0];ws.send(json.dumps({'id':n,'method':m,'params':p or {}}))
  while True:
    r=json.loads(ws.recv())
    if r.get('id')==n:return r
def js(e,awaitp=False):return call('Runtime.evaluate',{'expression':e,'returnByValue':True,'awaitPromise':awaitp}).get('result',{}).get('result',{}).get('value')

def png_pixels(data):
  assert data[:8]==b'\x89PNG\r\n\x1a\n'
  pos=8;w=h=bd=ct=None;idat=b''
  while pos<len(data):
    ln=struct.unpack('>I',data[pos:pos+4])[0];typ=data[pos+4:pos+8];chunk=data[pos+8:pos+8+ln]
    if typ==b'IHDR':
      w,h,bd,ct=struct.unpack('>IIBB',chunk[:10])
    elif typ==b'IDAT':idat+=chunk
    elif typ==b'IEND':break
    pos+=12+ln
  raw=zlib.decompress(idat)
  ch=4 if ct==6 else 3
  stride=w*ch;out=bytearray();prev=bytearray(stride);p=0
  for y in range(h):
    f=raw[p];p+=1;line=bytearray(raw[p:p+stride]);p+=stride
    if f==1:
      for i in range(ch,stride):line[i]=(line[i]+line[i-ch])&255
    elif f==2:
      for i in range(stride):line[i]=(line[i]+prev[i])&255
    elif f==3:
      for i in range(stride):
        a=line[i-ch] if i>=ch else 0
        line[i]=(line[i]+((a+prev[i])>>1))&255
    elif f==4:
      for i in range(stride):
        a=line[i-ch] if i>=ch else 0
        b=prev[i];c=prev[i-ch] if i>=ch else 0
        pa=abs(b-c);pb=abs(a-c);pc=abs(a+b-2*c)
        pr=a if (pa<=pb and pa<=pc) else (b if pb<=pc else c)
        line[i]=(line[i]+pr)&255
    out+=line;prev=line
  return w,h,ch,bytes(out)

def grey_ratio(png):
  w,h,ch,px=png_pixels(png)
  grey=0;plant=0
  for y in range(0,h,2):
    base=y*w*ch
    for x in range(0,w,2):
      i=base+x*ch
      r,g,b=px[i],px[i+1],px[i+2]
      mx=max(r,g,b);mn=min(r,g,b);lum=(r+g+b)//3
      if lum<235 and lum>90 and (mx-mn)<=20: grey+=1
      elif (mx-mn)>45 and mx>60: plant+=1
  tot=grey+plant
  return (100.0*grey/tot if tot else -1), grey, plant

call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setCacheDisabled',{'cacheDisabled':True})
call('Page.navigate',{'url':'http://127.0.0.1:8899/'+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'})
for _ in range(80):
  if js("typeof THREE!=='undefined' && document.getElementById('hudBody') && document.getElementById('hudBody').innerText.length>0"):break
  time.sleep(0.5)
time.sleep(2)
js("var e=document.getElementById('preset');e.value='bucky';e.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(3)
CLIP={'x':120,'y':60,'width':640,'height':640,'scale':1.0}
def grab(p):
  d=call('Page.captureScreenshot',{'format':'png','clip':CLIP})['result']['data']
  raw=base64.b64decode(d)
  if p: open(p,'wb').write(raw)
  return raw
print('%-34s %-8s %-8s %s'%('params','grey%','grey','plant'))
for tag,par in [
  ('A 0.50/0.62/0.34',{'hexR':0.50,'hexRing':0.62,'hexMid':0.20,'pentR':0.34}),
  ('B 0.55/0.62/0.38',{'hexR':0.55,'hexRing':0.62,'hexMid':0.22,'pentR':0.38}),
  ('C 0.62/0.64/0.44',{'hexR':0.62,'hexRing':0.64,'hexMid':0.26,'pentR':0.44}),
  ('D 0.70/0.66/0.50',{'hexR':0.70,'hexRing':0.66,'hexMid':0.30,'pentR':0.50}),
]:
  js("JSON.stringify(window.__tileSet(%s))"%json.dumps(par));time.sleep(2.4)
  raw=grab('../预览_灰底扫描_%s.png'%tag.split()[0])
  gr,g,p= grey_ratio(raw)
  print('%-34s %-8.2f %-8d %d'%(tag,gr,g,p),flush=True)
print('ERR:',js("document.getElementById('err').style.display"),flush=True)
js("window.__tileSet(null)");time.sleep(2.0)
grab('../预览_灰底扫描_默认.png')
ws.close();proc.terminate()
try:proc.wait(timeout=5)
except Exception:proc.kill()
print('DONE',flush=True)
