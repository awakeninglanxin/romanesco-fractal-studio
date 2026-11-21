import time, os, urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

URL = "http://127.0.0.1:8899/" + urllib.parse.quote('罗马花椰菜_分形生长参数台.html')
opts = Options()
for a in ["--headless=new", "--no-sandbox", "--enable-webgl", "--use-gl=swiftshader",
          "--enable-unsafe-swiftshader", "--window-size=1500,950", "--hide-scrollbars"]:
    opts.add_argument(a)
drv = webdriver.Chrome(options=opts)
drv.set_script_timeout(120)
drv.get(URL)
time.sleep(2)

# 切到直立花盘预设
drv.execute_script("""
var s=document.getElementById('preset');s.value='upright';
s.dispatchEvent(new Event('change',{bubbles:true}));
""")
time.sleep(1.5)
print("HUD:", drv.execute_script("return document.getElementById('hudBody').innerText").replace('\n', ' | '))
# 拉满生长
drv.execute_script("var p=document.getElementById('prog');p.value=1000;p.dispatchEvent(new Event('input',{bubbles:true}));")
time.sleep(1)
drv.save_screenshot("_dev/upright_side.png")
# 俯视
drv.execute_script("document.getElementById('btnTop').click()")
time.sleep(1)
drv.save_screenshot("_dev/upright_top.png")
for f in ["_dev/upright_side.png", "_dev/upright_top.png"]:
    print(f, os.path.getsize(f))
drv.quit()
