import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
opts=Options()
for a in ["--headless=new","--no-sandbox","--enable-webgl","--use-gl=swiftshader","--enable-unsafe-swiftshader","--window-size=1200,800"]:opts.add_argument(a)
drv=webdriver.Chrome(options=opts);drv.set_script_timeout(180)
drv.get("http://127.0.0.1:8899/罗马花椰菜_分形生长参数台.html");time.sleep(2)
drv.execute_script("var h=document.getElementById('honey');h.checked=true;h.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(2)
res=drv.execute_script("""
return new Promise(function(resolve){
  var orig=URL.createObjectURL; var captured=null;
  URL.createObjectURL=function(blob){captured=blob;return orig.call(URL,blob);};
  document.getElementById('btnSTL').click();
  URL.createObjectURL=orig;
  if(!captured){resolve('NO_BLOB');return;}
  var fr=new FileReader();
  fr.onload=function(){
    var dv=new DataView(fr.result);var n=dv.getUint32(80,true);
    resolve(JSON.stringify({size:fr.result.byteLength,triangles:n,expected:84+n*50,valid:fr.result.byteLength===84+n*50}));
  };
  fr.readAsArrayBuffer(captured);
});
""")
print("HONEY STL:",res)
print("info:",drv.execute_script("return document.getElementById('stlInfo').innerText"))
drv.quit()
