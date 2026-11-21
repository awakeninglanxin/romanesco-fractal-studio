import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
opts=Options()
for a in ["--headless=new","--no-sandbox","--enable-webgl","--use-gl=swiftshader","--enable-unsafe-swiftshader","--window-size=1200,800"]:opts.add_argument(a)
drv=webdriver.Chrome(options=opts);drv.set_script_timeout(120)
drv.get("http://127.0.0.1:8899/罗马花椰菜_分形生长参数台.html");time.sleep(2)

def test(fmt):
    return drv.execute_script("""
return new Promise(function(resolve){
  var orig=URL.createObjectURL,cap=null;
  URL.createObjectURL=function(b){cap=b;return orig.call(URL,b);};
  var sel=document.getElementById('expFmt');sel.value='%s';sel.dispatchEvent(new Event('change',{bubbles:true}));
  document.getElementById('btnSTL').click();
  URL.createObjectURL=orig;
  if(!cap){resolve(JSON.stringify({err:'NO_BLOB',info:document.getElementById('stlInfo').innerText}));return;}
  var name=cap&&cap.name||'';
  var fr=new FileReader();
  fr.onload=function(){
    var head='';var arr=new Uint8Array(fr.result.slice(0,120));
    for(var i=0;i<120;i++)head+=String.fromCharCode(arr[i]);
    resolve(JSON.stringify({size:fr.result.byteLength,head:head.replace(/[^\\x20-\\x7e\\n]/g,'.').slice(0,100),info:document.getElementById('stlInfo').innerText}));
  };
  fr.readAsArrayBuffer(cap);
});
""" % fmt)

for f in ['stl','obj','ply','step']:
    print(f.upper(),':',test(f))
drv.quit()
