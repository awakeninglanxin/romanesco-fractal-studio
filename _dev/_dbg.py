import time, urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

URL = "http://127.0.0.1:8899/" + urllib.parse.quote('罗马花椰菜_分形生长参数台.html')+'?debug=1'
opts = Options()
for a in ["--headless=new", "--no-sandbox", "--enable-webgl", "--use-gl=swiftshader",
          "--enable-unsafe-swiftshader", "--window-size=1500,950"]:
    opts.add_argument(a)
drv = webdriver.Chrome(options=opts)
drv.set_script_timeout(300)
logs = []
drv.get(URL)
time.sleep(2)
# 用 preset 而不是滑块
print("presets:", drv.execute_script("var s=document.getElementById('preset');var o=[];for(var i=0;i<s.options.length;i++)o.push(s.options[i].value+':'+s.options[i].text);return o.join(' | ')"))
# 单独设 levels
r = drv.execute_script("""
try {
  var l=document.getElementById('levels');l.value=5;l.dispatchEvent(new Event('input',{bubbles:true}));
  return 'OK vLevels='+document.getElementById('vLevels').textContent+' cones='+document.getElementById('vCones').textContent;
} catch(e){ return 'ERR '+e.message+' '+e.stack; }
""")
print("set level:", r)
time.sleep(8)
print("HUD:", drv.execute_script("return document.getElementById('hudBody').innerText").replace('\n', ' | '))
print("console logs:", drv.get_log('browser')[:6])
drv.quit()
