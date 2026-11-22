import time, urllib.parse, json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
URL="http://127.0.0.1:8899/"+urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
opts=Options()
for a in ["--headless=new","--no-sandbox","--enable-webgl","--use-gl=swiftshader","--enable-unsafe-swiftshader","--window-size=1500,950"]:opts.add_argument(a)
drv=webdriver.Chrome(options=opts);drv.set_script_timeout(120)
drv.get(URL);time.sleep(2)
for val in ['romanesco','cauliflower','broccoli','upright','xmas']:
    drv.execute_script("var s=document.getElementById('preset');s.value='%s';s.dispatchEvent(new Event('change',{bubbles:true}));"%val)
    time.sleep(1.2)
    hud=drv.execute_script("return document.getElementById('hudBody').innerText").split('\n')[0]
    print(f"{val:12} -> {hud}")
# 画布视口检查
info=drv.execute_script("var r=document.getElementById('cv').getBoundingClientRect();return JSON.stringify({top:r.top,bottom:r.bottom,ih:innerHeight});")
print("canvas:",info)
errs=[x['message'][:80] for x in drv.get_log('browser') if x['level']=='SEVERE' and 'favicon' not in x['message']]
print("JS errors:",errs[:3])
drv.quit()
