import os,time,hashlib
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
opts=Options()
for a in ["--headless=new","--no-sandbox","--enable-webgl","--use-gl=swiftshader","--enable-unsafe-swiftshader","--window-size=1500,950","--hide-scrollbars"]:opts.add_argument(a)
drv=webdriver.Chrome(options=opts);drv.set_page_load_timeout(40)
drv.get("http://127.0.0.1:8899/罗马花椰菜_分形生长参数台.html");time.sleep(2.5)
# 把进度拉满
drv.execute_script("var p=document.getElementById('prog');p.value=1000;p.dispatchEvent(new Event('input',{bubbles:true}));")
time.sleep(1.5)
drv.save_screenshot("shot_fullgrown.png")
print("hud:",drv.find_element(By.ID,"hudBody").text if False else drv.execute_script("return document.getElementById('hudBody').innerText"))
try: drv.find_element(By.ID,"cv").screenshot("shot_canvas_grown.png")
except Exception as e: print(e)
for f in ["shot_fullgrown.png","shot_canvas_grown.png"]:
    print(f,os.path.getsize(f),hashlib.md5(open(f,'rb').read()).hexdigest())
drv.quit()
