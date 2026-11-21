import time,urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
URL="http://127.0.0.1:8899/"+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')
opts=Options()
for a in ["--headless=new","--no-sandbox","--enable-webgl","--use-gl=swiftshader","--enable-unsafe-swiftshader"]:opts.add_argument(a)
drv=webdriver.Chrome(options=opts);drv.set_script_timeout(120)
drv.get(URL);time.sleep(2)
drv.execute_script("var s=document.getElementById('preset');s.value='upright';s.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(3)
for fmt in ['stl','obj','ply']:
    r=drv.execute_script("""
return new Promise(function(res){
 var o=URL.createObjectURL,c=null;URL.createObjectURL=function(b){c=b;return o.call(URL,b);};
 var s=document.getElementById('expFmt');s.value='%s';s.dispatchEvent(new Event('change',{bubbles:true}));
 document.getElementById('btnSTL').click();URL.createObjectURL=o;
 if(!c){res('NO_BLOB');return;}
 var fr=new FileReader();fr.onload=function(){res('size='+fr.result.byteLength);};fr.readAsArrayBuffer(c);
});""" % fmt)
    print(fmt,r)
drv.quit()
