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
drv.set_script_timeout(300)
drv.get(URL)
time.sleep(2)
# 罗马花椰菜 + 5层 + 11芽
drv.execute_script("""
var s=document.getElementById('preset');s.value='romanesco';s.dispatchEvent(new Event('change',{bubbles:true}));
var l=document.getElementById('levels');l.value=5;l.dispatchEvent(new Event('input',{bubbles:true}));
""")
t=time.time()
time.sleep(10)
print("build wait:",round(time.time()-t,1),"s")
print("HUD:", drv.execute_script("return document.getElementById('hudBody').innerText").replace('\n',' | '))
errs=[x for x in drv.get_log('browser') if x['level']=='SEVERE' and 'favicon' not in x['message']]
print("errors:",errs[:3])
drv.execute_script("var p=document.getElementById('prog');p.value=1000;p.dispatchEvent(new Event('input',{bubbles:true}));")
time.sleep(4)
drv.save_screenshot("_dev/fill5.png")
print("shot:",os.path.getsize("_dev/fill5.png"))
drv.quit()
