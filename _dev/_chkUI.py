import time,urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
opts=Options()
for a in ["--headless=new","--no-sandbox","--enable-webgl","--use-gl=swiftshader","--enable-unsafe-swiftshader"]:opts.add_argument(a)
drv=webdriver.Chrome(options=opts);drv.set_script_timeout(60)
drv.get("http://127.0.0.1:8899/"+urllib.parse.quote('罗马花椰菜_分形生长参数台.html'));time.sleep(2)
print("before display:",drv.execute_script("return document.getElementById('upSec').style.display"))
drv.execute_script("var s=document.getElementById('preset');s.value='upright';s.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(1)
print("after display:",drv.execute_script("return document.getElementById('upSec').style.display"))
print("upN val:",drv.execute_script("return document.getElementById('upN').value"))
drv.quit()
