import sys, os, json, hashlib, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

URL="http://127.0.0.1:8899/罗马花椰菜_分形生长参数台.html"
opts=Options()
opts.add_argument("--headless=new")
opts.add_argument("--disable-gpu-sandbox")
opts.add_argument("--no-sandbox")
opts.add_argument("--enable-webgl")
opts.add_argument("--use-gl=swiftshader")
opts.add_argument("--enable-unsafe-swiftshader")
opts.add_argument("--window-size=1500,950")
opts.add_argument("--hide-scrollbars")
drv=webdriver.Chrome(options=opts)
drv.set_page_load_timeout(40)
drv.get(URL)
time.sleep(3)
# 画布几何 + 视口
info=drv.execute_script("""
var cv=document.getElementById('cv');var r=cv.getBoundingClientRect();
var dock=document.getElementById('dock').getBoundingClientRect();
return {cv:{top:r.top,bottom:r.bottom,left:r.left,right:r.right,w:r.width,h:r.height},
        dock:{top:dock.top,left:dock.left,right:dock.right,w:dock.width},
        ih:innerHeight,iw:innerWidth,
        leaves:document.getElementById('hudBody').innerText};
""")
print("INFO",json.dumps(info,ensure_ascii=False))
drv.save_screenshot("shot_full.png")
# 元素截图
try:
    drv.find_element(By.ID,"cv").screenshot("shot_canvas.png")
except Exception as e:
    print("canvas elem shot err",e)
# 点播放后再截一张，验证字节不同
drv.find_element(By.ID,"btnPlay").click()
time.sleep(2.5)
drv.save_screenshot("shot_full2.png")
try:
    drv.find_element(By.ID,"cv").screenshot("shot_canvas2.png")
except Exception as e: print(e)
for f in ["shot_full.png","shot_full2.png","shot_canvas.png","shot_canvas2.png"]:
    if os.path.exists(f):
        print(f,os.path.getsize(f),hashlib.md5(open(f,'rb').read()).hexdigest())
drv.quit()
