import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
opts=Options()
for a in ["--headless=new","--no-sandbox","--enable-webgl","--use-gl=swiftshader","--enable-unsafe-swiftshader","--window-size=1200,800"]:opts.add_argument(a)
drv=webdriver.Chrome(options=opts);drv.set_script_timeout(120)
drv.get("http://127.0.0.1:8899/罗马花椰菜_分形生长参数台.html");time.sleep(2)
# 直接调用内部逻辑拿数字：通过 HUD 和重新读取（不触发重算）
print("before:",drv.execute_script("return document.getElementById('hudBody').innerText").replace('\n',' '))
t=time.time()
drv.execute_script("var h=document.getElementById('honey');h.checked=true;h.dispatchEvent(new Event('change',{bubbles:true}));")
print("elapsed change:",round(time.time()-t,2),"s")
print("after:",drv.execute_script("return document.getElementById('hudBody').innerText").replace('\n',' '))
drv.quit()
