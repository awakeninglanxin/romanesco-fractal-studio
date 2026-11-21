import time,os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
opts=Options()
for a in ["--headless=new","--no-sandbox","--enable-webgl","--use-gl=swiftshader","--enable-unsafe-swiftshader","--window-size=1200,800"]:opts.add_argument(a)
drv=webdriver.Chrome(options=opts);drv.set_script_timeout(120)
drv.get("http://127.0.0.1:8899/罗马花椰菜_分形生长参数台.html");time.sleep(2)
drv.execute_script("document.getElementById('btnSTL').click()")
time.sleep(2)
print("stlInfo:",drv.execute_script("return document.getElementById('stlInfo').innerText"))
drv.quit()
