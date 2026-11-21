import time,re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
opts=Options()
for a in ["--headless=new","--no-sandbox","--enable-webgl","--use-gl=swiftshader","--enable-unsafe-swiftshader","--window-size=1200,800"]:opts.add_argument(a)
drv=webdriver.Chrome(options=opts);drv.set_script_timeout(180)
drv.get("http://127.0.0.1:8899/罗马花椰菜_分形生长参数台.html");time.sleep(2)
drv.execute_script("var l=document.getElementById("levels");l.value=2;l.dispatchEvent(new Event("input",{bubbles:true}));")
time.sleep(1)
txt=drv.execute_script("""
return new Promise(function(resolve){
  var orig=URL.createObjectURL,cap=null;
  URL.createObjectURL=function(b){cap=b;return orig.call(URL,b);};
  var sel=document.getElementById('expFmt');sel.value='step';sel.dispatchEvent(new Event('change',{bubbles:true}));
  document.getElementById('btnSTL').click();URL.createObjectURL=orig;
  var fr=new FileReader();fr.onload=function(){resolve(fr.result);};fr.readAsText(cap);
});
""")
drv.quit()
ids=re.findall(r'(?m)^#(\d+)=',txt)
dup=[x for x in set(ids) if ids.count(x)>1]
print("entities:",len(ids),"unique:",len(set(ids)),"duplicates:",dup[:10])
# 嵌套定义检测：一行里出现两个 #号= 
nested=[l for l in txt.split('\n') if re.search(r'#\d+=',l) and len(re.findall(r'#\d+=',l))>1]
print("nested-def lines:",len(nested),nested[:2])
print("paren balanced:",txt.count('(')==txt.count(')'))
print("semicolon每条:",all((not l.strip()) or l.strip().endswith(';') for l in txt.split('\n')))
