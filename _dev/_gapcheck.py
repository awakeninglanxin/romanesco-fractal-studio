import time, os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

URL = "http://127.0.0.1:8899/" + __import__('urllib.parse', fromlist=['quote']).quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
opts = Options()
for a in ["--headless=new", "--no-sandbox", "--enable-webgl", "--use-gl=swiftshader",
          "--enable-unsafe-swiftshader", "--window-size=1500,950", "--hide-scrollbars"]:
    opts.add_argument(a)
drv = webdriver.Chrome(options=opts)
drv.set_script_timeout(240)
drv.set_page_load_timeout(90)
t0 = time.time()
drv.get(URL)
time.sleep(3)
print("load:", round(time.time() - t0, 2), "s")
print("HUD:", drv.execute_script("return document.getElementById('hudBody').innerText").replace('\n', ' | '))
t1 = time.time()
drv.execute_script("var p=document.getElementById('prog');p.value=1000;p.dispatchEvent(new Event('input',{bubbles:true}));")
time.sleep(4)
print("grow:", round(time.time() - t1, 2), "s")
print("HUD2:", drv.execute_script("return document.getElementById('hudBody').innerText").replace('\n', ' | '))
drv.save_screenshot("_dev/gap_after_full.png")
try:
    drv.find_element(By.ID, "cv").screenshot("_dev/gap_after_canvas.png")
except Exception as e:
    print("shot err", e)
for f in ["_dev/gap_after_full.png", "_dev/gap_after_canvas.png"]:
    if os.path.exists(f):
        print(f, os.path.getsize(f))
drv.quit()
