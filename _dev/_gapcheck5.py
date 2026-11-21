import time, os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import urllib.parse

URL = "http://127.0.0.1:8899/" + urllib.parse.quote('罗马花椰菜_分形生长参数台.html')
opts = Options()
for a in ["--headless=new", "--no-sandbox", "--enable-webgl", "--use-gl=swiftshader",
          "--enable-unsafe-swiftshader", "--window-size=1500,950", "--hide-scrollbars"]:
    opts.add_argument(a)
drv = webdriver.Chrome(options=opts)
drv.set_script_timeout(300)
drv.set_page_load_timeout(90)
drv.get(URL)
time.sleep(2.5)

# 设成老师截图的参数：5层 11芽
drv.execute_script("""
var l=document.getElementById('levels'); l.value=5; l.dispatchEvent(new Event('input',{bubbles:true}));
var c=document.getElementById('cones'); c.value=11; c.dispatchEvent(new Event('input',{bubbles:true}));
""")
t1 = time.time()
time.sleep(6)
print("build:", round(time.time() - t1, 2), "s")
print("HUD:", drv.execute_script("return document.getElementById('hudBody').innerText").replace('\n', ' | '))
drv.execute_script("var p=document.getElementById('prog');p.value=1000;p.dispatchEvent(new Event('input',{bubbles:true}));")
time.sleep(5)
print("HUD2:", drv.execute_script("return document.getElementById('hudBody').innerText").replace('\n', ' | '))
drv.save_screenshot("_dev/gap5_full.png")
try:
    drv.find_element(By.ID, "cv").screenshot("_dev/gap5_canvas.png")
except Exception as e:
    print("shot err", e)
for f in ["_dev/gap5_full.png", "_dev/gap5_canvas.png"]:
    if os.path.exists(f):
        print(f, os.path.getsize(f))
drv.quit()
