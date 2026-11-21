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

# 关闭自动旋转，避免截图时画面乱转
drv.execute_script("var c=document.getElementById('spin');if(c.checked)c.click();")

def setup(preset, upn, buds, levels):
    drv.execute_script("""
      var s=document.getElementById('preset');s.value='%s';s.dispatchEvent(new Event('change',{bubbles:true}));
      var u=document.getElementById('upN');u.value=%d;u.dispatchEvent(new Event('input',{bubbles:true}));
      var b=document.getElementById('upBuds');b.value=%d;b.dispatchEvent(new Event('input',{bubbles:true}));
      var lv=document.getElementById('levels');lv.value=%d;lv.dispatchEvent(new Event('input',{bubbles:true}));
      var p=document.getElementById('prog');p.value=1000;p.dispatchEvent(new Event('input',{bubbles:true}));
    """ % (preset, upn, buds, levels))
    time.sleep(3)

def bottom_view():
    # makeOrbit: mousemove -> st.phi = clamp(st.phi - dy*0.006, ...)
    # 向上拖 dy<0 使 phi 增大到接近 π → 相机到模型下方
    drv.execute_script("""
      var cv=document.getElementById('cv');var r=cv.getBoundingClientRect();
      var x=r.left+r.width/2, y=r.top+r.height/2;
      cv.dispatchEvent(new MouseEvent('mousedown',{clientX:x,clientY:y+250,button:0,bubbles:true}));
      window.dispatchEvent(new MouseEvent('mousemove',{clientX:x,clientY:y+250-360,button:0,bubbles:true}));
      window.dispatchEvent(new MouseEvent('mouseup',{button:0,bubbles:true}));
    """)
    time.sleep(1)

def top_view():
    drv.execute_script("document.getElementById('btnTop').click()")
    time.sleep(1)

# 单株：底盘六边形蜂窝是否清晰
setup('upright', 1, 24, 3)
bottom_view(); drv.save_screenshot("_dev/hex_single_bottom.png")
print("single_bottom", os.path.getsize("_dev/hex_single_bottom.png"))
top_view(); drv.save_screenshot("_dev/hex_single_top.png")
print("single_top", os.path.getsize("_dev/hex_single_top.png"))

# 整盘 7 株：底部 + 俯视
setup('upright', 7, 24, 3)
bottom_view(); drv.save_screenshot("_dev/hex_7_bottom.png")
print("7_bottom", os.path.getsize("_dev/hex_7_bottom.png"))
top_view(); drv.save_screenshot("_dev/hex_7_top.png")
print("7_top", os.path.getsize("_dev/hex_7_top.png"))

# HUD / 错误检查
print("HUD:", drv.execute_script("return document.getElementById('hudBody').innerText").replace('\n',' | '))
print("ERR:", drv.execute_script("return document.getElementById('err').style.display"))
drv.quit()
