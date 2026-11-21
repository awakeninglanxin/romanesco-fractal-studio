import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
opts=Options()
for a in ["--headless=new","--no-sandbox","--enable-webgl","--use-gl=swiftshader","--enable-unsafe-swiftshader","--window-size=1200,800"]:opts.add_argument(a)
drv=webdriver.Chrome(options=opts);drv.set_script_timeout(180)
drv.get("http://127.0.0.1:8899/罗马花椰菜_分形生长参数台.html");time.sleep(2)
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
# 检查 STEP 语法
lines=txt.split('\n')
print("lines:",len(lines),"size:",len(txt))
print("starts:",lines[0],"| ends:",lines[-1].strip())
print("has ENDSEC/END-ISO:", 'ENDSEC;' in txt, 'END-ISO-10303-21;' in txt)
print("entities:", {k:txt.count('='+k+'(') for k in ['MANIFOLD_SOLID_BREP','ADVANCED_FACE','CLOSED_SHELL','ADVANCED_BREP_SHAPE_REPRESENTATION','CARTESIAN_POINT']})
# 括号平衡
print("paren balanced:", txt.count('(')==txt.count(')'), txt.count('('), txt.count(')'))
# 检查每个 entity 是否以 ; 结尾
bad=[l for l in lines if l.strip() and '=' in l and not l.strip().endswith(';') and not l.startswith(('FILE','#1=','#2=','#3=','#4=','#5=','#6='))][:5]
print("sample non-semicolon lines:",bad[:3])
