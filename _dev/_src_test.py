import time, os, urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

URL = "http://127.0.0.1:8899/" + urllib.parse.quote('罗马花椰菜_分形生长参数台.html')
opts = Options()
for a in ["--headless=new", "--no-sandbox", "--enable-webgl", "--use-gl=swiftshader",
          "--enable-unsafe-swiftshader", "--window-size=1500,950", "--hide-scrollbars"]:
    opts.add_argument(a)
drv = webdriver.Chrome(options=opts); drv.set_script_timeout(180)
drv.get(URL); time.sleep(2)
# 直立花盘 → 单株 upN=1, buds=24, levels=3
drv.execute_script("""
var s=document.getElementById('preset');s.value='upright';s.dispatchEvent(new Event('change',{bubbles:true}));
var u=document.getElementById('upN');u.value=7;u.dispatchEvent(new Event('input',{bubbles:true}));
var b=document.getElementById('upBuds');b.value=24;b.dispatchEvent(new Event('input',{bubbles:true}));
""")
time.sleep(6)
print("HUD:", drv.execute_script("return document.getElementById('hudBody').innerText").replace('\n',' | '))
drv.execute_script("var p=document.getElementById('prog');p.value=1000;p.dispatchEvent(new Event('input',{bubbles:true}));")
time.sleep(2)
drv.save_screenshot("_dev/src_honey.png")
print("shot", os.path.getsize("_dev/src_honey.png"))
drv.quit()
