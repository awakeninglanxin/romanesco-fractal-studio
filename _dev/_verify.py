import os,time,hashlib,struct
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
opts=Options()
for a in ["--headless=new","--no-sandbox","--enable-webgl","--use-gl=swiftshader","--enable-unsafe-swiftshader","--window-size=1500,950","--hide-scrollbars"]:opts.add_argument(a)
prefs={"download.default_directory":os.getcwd(),"download.prompt_for_download":False}
opts.add_experimental_option("prefs",prefs)
drv=webdriver.Chrome(options=opts);drv.set_page_load_timeout(60)
drv.get("http://127.0.0.1:8899/罗马花椰菜_分形生长参数台.html");time.sleep(2.5)

# 1) 单株满生长
drv.execute_script("var p=document.getElementById('prog');p.value=1000;p.dispatchEvent(new Event('input',{bubbles:true}));")
time.sleep(1)
print("SINGLE HUD:",drv.execute_script("return document.getElementById('hudBody').innerText").replace('\n',' | '))

# 2) 开启蜂窝模式
drv.execute_script("var h=document.getElementById('honey');h.checked=true;h.dispatchEvent(new Event('change',{bubbles:true}));")
time.sleep(2.5)
drv.execute_script("var p=document.getElementById('prog');p.value=1000;p.dispatchEvent(new Event('input',{bubbles:true}));")
time.sleep(1)
print("HONEY HUD:",drv.execute_script("return document.getElementById('hudBody').innerText").replace('\n',' | '))
drv.save_screenshot("verify_honey.png")
# 俯视
drv.execute_script("document.getElementById('btnTop').click()")
time.sleep(1)
drv.save_screenshot("verify_honey_top.png")

# 3) 导出 STL
for f in [x for x in os.listdir('.') if x.endswith('.stl')]: os.remove(f)
drv.execute_script("document.getElementById('btnSTL').click()")
time.sleep(3)
stls=[x for x in os.listdir('.') if x.endswith('.stl')]
print("STL files:",stls)
if stls:
    p=stls[0];data=open(p,'rb').read()
    n=struct.unpack('<I',data[80:84])[0]
    expect=84+n*50
    print("STL size:",len(data),"triangles:",n,"expected:",expect,"VALID:",len(data)==expect)
    print("STL header:",data[:40].decode('latin1',errors='ignore'))
drv.quit()
