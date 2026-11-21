
(function(){
"use strict";
var $ = function(id){return document.getElementById(id);};
if(typeof THREE==='undefined'){
  $('err').style.display='flex';
  $('err').textContent='三维引擎 three.js 加载失败：请确认同目录 three.min.js 存在，或联网以走 CDN 兜底。';
  return;
}

/* ============ 常数（照抄 Robert Vella 源码） ============ */
var GOLDEN_ANGLE = 2.399963;         // rad = 137.5077°
var INNER_TO_OUTER_CONE_RATIO = 0.4325;
var RADIUS_TO_LENGTH_RATIO = 0.9534;
var UP_VECTOR = new THREE.Vector3(0,-1,0);
var PHI = (1+Math.sqrt(5))/2;
/* 埃及金字塔比：底面对角线/2（外接圆半径）与高之比 = √2/√φ ≈ 1.111786。
   胡夫金字塔实测 (230.37·√2/2)/146.6 = 1.11116，误差仅 0.056%。
   对应锥半顶角 arctan(√2/√φ) = 48.03°，全顶角 96.06°。 */
var PYRAMID_RL = Math.SQRT2/Math.sqrt(PHI);
var FIB = [1,1,2,3,5,8,13,21,34,55,89];

var PRESETS = {
  romanesco:   {levels:3, angle:137.508, cones:11, r2l:0.95, i2o:0.43, pal:0, form:'fractal'},
  cauliflower: {levels:3, angle:137.508, cones:14, r2l:1.18, i2o:0.60, pal:2, form:'fractal'},
  broccoli:    {levels:3, angle:137.508, cones:7,  r2l:0.68, i2o:0.38, pal:1, form:'fractal'},
  // 直立花盘：锥轴垂直、底面平放平台、锥数少（黄金角平铺的莲蓬/生命之花）
  upright:     {levels:3, angle:137.508, cones:7, r2l:1.111786, i2o:0.46, pal:4, form:'upright', upTilt:1.0, upBuds:55},
  xmas:        {levels:5, angle:137.508, cones:7, r2l:1.111786, i2o:0.46, pal:4, form:'upright', upTilt:0.0, upBuds:6},
  // 正60面体（截角二十面体 / 足球烯 C60）：每面贴砖式直立花盘
  bucky:       {levels:3, angle:137.508, cones:7, r2l:1.111786, i2o:0.46, pal:4, form:'poly', upTilt:1.0, upBuds:16}
};
var PALETTES = [
  {name:'罗马绿',   hue:[0.22,0.34], sat:[0.46,0.64], light:[0.28,0.55]},
  {name:'翡翠青',   hue:[0.40,0.50], sat:[0.48,0.66], light:[0.24,0.54]},
  {name:'花椰菜奶白',hue:[0.13,0.17], sat:[0.10,0.22], light:[0.62,0.90]},
  {name:'紫罗兰',   hue:[0.72,0.84], sat:[0.38,0.60], light:[0.32,0.62]},
  {name:'原图橄榄绿', hue:[0.16,0.30], sat:[0.42,0.68], light:[0.30,0.52]}
];

function clamp(v,a,b){return Math.max(a,Math.min(b,v));}
function lerp(a,b,t){return a+(b-a)*t;}
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;var t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
function angleBetween(a,b){return Math.acos(clamp(a.dot(b),-1,1));}

/* ===== 分级配色 colormap（科学配色锚点，线性插值） ===== */
var CMAP={
  turbo:[[0.19,0.07,0.23],[0.30,0.40,0.79],[0.16,0.77,0.85],[0.20,0.94,0.51],[0.66,0.99,0.24],[0.96,0.75,0.13],[0.97,0.33,0.09],[0.72,0.03,0.10],[0.48,0.01,0.01]],
  viridis:[[0.27,0.00,0.33],[0.28,0.14,0.46],[0.25,0.26,0.53],[0.21,0.37,0.55],[0.16,0.47,0.56],[0.13,0.57,0.55],[0.14,0.66,0.52],[0.27,0.75,0.44],[0.48,0.82,0.32],[0.74,0.89,0.15],[0.99,0.91,0.14]],
  plasma:[[0.05,0.03,0.53],[0.29,0.01,0.63],[0.47,0.06,0.61],[0.62,0.15,0.51],[0.74,0.27,0.41],[0.84,0.40,0.31],[0.91,0.54,0.21],[0.97,0.70,0.13],[0.99,0.86,0.11],[0.94,0.98,0.13]]
};
function cmapRGB(name,t){
  t=clamp(t,0,1);
  if(name==='hsv')return new THREE.Color().setHSL((0.62+0.72*t)%1,0.78,lerp(0.34,0.62,t));
  var A=CMAP[name]||CMAP.turbo;
  var x=t*(A.length-1),i=Math.floor(x),f=x-i;
  if(i>=A.length-1){i=A.length-2;f=1;}
  return new THREE.Color().setRGB(
    lerp(A[i][0],A[i+1][0],f),lerp(A[i][1],A[i+1][1],f),lerp(A[i][2],A[i+1][2],f));
}

/* 照抄 HelperMethods.pde : intersectionBetweenTwoLines */
function intersectionBetweenTwoLines(l1s,l1e,l2s,l2e){
  var a=new THREE.Vector3().subVectors(l1e,l1s);
  var b=new THREE.Vector3().subVectors(l2e,l2s);
  var c=new THREE.Vector3().subVectors(l2s,l1s);
  var ab=new THREE.Vector3().crossVectors(a,b);
  var cb=new THREE.Vector3().crossVectors(c,b);
  var q=cb.dot(ab)/Math.pow(ab.length(),2);
  if(!isFinite(q))q=0;
  return new THREE.Vector3().add(l1s,a.multiplyScalar(q));
}

/* ============ 状态 ============ */
var S={levels:3,angleDeg:137.508,cones:11,r2l:0.95,i2o:0.43,pal:0,form:'upright',
       /* 直立花盘（蜂窝·垂直平放·Broccoli多级）参数 */
       upN:7, upSpread:1.0, upTilt:1.0, upBuds:55,   // 蜂窝单元数 / 间距系数(>2留缝) / 子锥倾角(0=垂直) / 每级芽数
       spiralMode:'golden', spiralDeg:45, upBudsEff:24,  // 底层分布算法 / 对称角度 / 预算自适应后生效芽数
       autoFill:false, fillK:1.00, fillCount:0,        // 自动填满三角空隙 / 补株相对尺寸(≤1) / 实际补株数
       hexBase:true, hexThick:5, hexOverlap:0.00,     // 红色六边形砖底盘(默认开) / 厚度mm / 与株底重叠高度(默认0)
       cmap:'fib', fibArms:13, fibTwist:2.6,           // 默认斐波那契螺旋臂配色 / 臂数(8/13/21) / 对数螺旋缠绕紧度
                                                      // 其它可选: viridis/level/hsv/turbo/plasma/height
       spin:false,spiral:false,wire:false,speed:1,prog:1,playing:false,seed:12345,
       leaves:[],visible:0,altitude:6,
       /* 第0级蜂窝面板 */
       honey:false, boardL:250, boardW:180, boardT:5, brocSize:28,   // mm
       /* 正60面体（截角二十面体）表面贴砖 */
       polyEdge:2.40, polyFaces:null, polyTileMesh:null, polyEdgeLines:null, polyFlowers:0, polyEdges:true,
       stlSeg:5, cells:[], renderList:[], plateMesh:null};

/* ============ three 场景 ============ */
var stage=$('stage'),cv=$('cv');
var renderer,scene,camera,root,leafMesh,spiralLine,ctrl;
var cam={theta:0.55,phi:0.92,radius:14,target:new THREE.Vector3(0,0,0)};
var _camFramed=false;   // 相机是否已首次取景：保证调任何参数都不重置视角

function initScene(){
  renderer=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:true});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
  renderer.setClearColor(0xffffff,0);
  scene=new THREE.Scene();
  camera=new THREE.PerspectiveCamera(42,1,0.1,1000);
  root=new THREE.Group();
  scene.add(root);
  scene.add(new THREE.AmbientLight(0xffffff,0.52));
  var d1=new THREE.DirectionalLight(0xffffff,0.62); d1.position.set(6,12,8); scene.add(d1);
  var d2=new THREE.DirectionalLight(0xc8ecd6,0.26); d2.position.set(-8,4,-6); scene.add(d2);
  ctrl=makeOrbit(camera,cam,cv);
  resize();
  window.addEventListener('resize',resize);
}
function resize(){
  var w=stage.clientWidth,h=stage.clientHeight;
  renderer.setSize(w,h,false);
  camera.aspect=w/h;camera.updateProjectionMatrix();
}
function makeOrbit(cam3,st,dom){
  var drag=false,lx=0,ly=0,btn=0;
  dom.addEventListener('contextmenu',function(e){e.preventDefault();});
  dom.addEventListener('mousedown',function(e){drag=true;lx=e.clientX;ly=e.clientY;btn=e.button;});
  window.addEventListener('mouseup',function(){drag=false;});
  window.addEventListener('mousemove',function(e){
    if(!drag)return;
    var dx=e.clientX-lx,dy=e.clientY-ly;lx=e.clientX;ly=e.clientY;
    if(btn===2){
      var s=st.radius*0.0016;
      var right=new THREE.Vector3().setFromMatrixColumn(cam3.matrix,0);
      var up=new THREE.Vector3().setFromMatrixColumn(cam3.matrix,1);
      st.target.addScaledVector(right,-dx*s).addScaledVector(up,dy*s);
    }else{
      st.theta-=dx*0.006;
      st.phi=clamp(st.phi-dy*0.006,0.08,Math.PI-0.08);
    }
  });
  dom.addEventListener('wheel',function(e){e.preventDefault();st.radius=clamp(st.radius*(1+Math.sign(e.deltaY)*0.09),3,80);},{passive:false});
  return {update:function(){
    var sp=Math.sin(st.phi);
    cam3.position.set(st.target.x+st.radius*sp*Math.sin(st.theta),
                      st.target.y+st.radius*Math.cos(st.phi),
                      st.target.z+st.radius*sp*Math.cos(st.theta));
    cam3.lookAt(st.target);
  }};
}

/* ============ 核心递归（照抄 RomanescoBroccoliGenerator.pde） ============ */
function fibPair(alphaDeg){
  // 用 360·F_k/F_{k+2} 逼近发散角，返回相邻 Fibonacci 螺旋列 (F_k,F_{k+1})
  var F=[1,1,2,3,5,8,13,21,34,55];
  var best=null,be=1e9;
  for(var k=0;k+2<F.length;k++){
    var ideal=360*F[k]/F[k+2];
    var e=Math.abs(ideal-alphaDeg);
    if(e<be){be=e;best=[F[k],F[k+1]];}
  }
  return best||[8,13];
}

/* ===== 正60面体 = 截角二十面体（Truncated Icosahedron / C60 足球烯） =====
   20 个正六边形 + 12 个正五边形，共 32 面 / 60 顶点 / 90 棱。
   由标准正二十面体每条棱三等分、截去 12 个顶点严格构造：
   原三角面 → 正六边形；原顶点周围 5 条棱的截点 → 正五边形。 */
function buildTruncatedIcosahedron(edge){
  var ico=new THREE.IcosahedronGeometry(1,0);
  var pa=ico.getAttribute('position'),verts=[],vidx={};
  for(var i=0;i<pa.count;i++){
    var v=new THREE.Vector3().fromBufferAttribute(pa,i);
    var key=v.x.toFixed(4)+'|'+v.y.toFixed(4)+'|'+v.z.toFixed(4);
    if(vidx[key]===undefined){vidx[key]=verts.length;verts.push(v);}
  }
  var tris=[];
  for(var i2=0;i2<pa.count;i2+=3){
    var ids=[];
    for(var j=0;j<3;j++){
      var q=new THREE.Vector3().fromBufferAttribute(pa,i2+j);
      ids.push(vidx[q.x.toFixed(4)+'|'+q.y.toFixed(4)+'|'+q.z.toFixed(4)]);
    }
    if(ids[0]!==ids[1]&&ids[1]!==ids[2]&&ids[2]!==ids[0])tris.push(ids);
  }
  ico.dispose();
  var nbr={};
  tris.forEach(function(t){
    [[t[0],t[1]],[t[1],t[2]],[t[2],t[0]]].forEach(function(e){
      if(!nbr[e[0]])nbr[e[0]]=[];
      if(nbr[e[0]].indexOf(e[1])<0)nbr[e[0]].push(e[1]);
    });
  });
  function cut(a,b,f){return verts[a].clone().lerp(verts[b],f);}
  function cornerOrder(i){
    var v=verts[i];
    var ref=Math.abs(v.y)>0.88?new THREE.Vector3(1,0,0):new THREE.Vector3(0,1,0);
    var e1=ref.clone().sub(v.clone().multiplyScalar(ref.dot(v))).normalize();
    var e2=new THREE.Vector3().crossVectors(v,e1).normalize(); // e1×e2=v → 从球外看逆时针
    return (nbr[i]||[]).map(function(j){
      var p=cut(i,j,1/3).sub(v);
      return {p:p.clone().add(v),a:Math.atan2(p.dot(e2),p.dot(e1))};
    }).sort(function(a,b){return a.a-b.a;}).map(function(o){return o.p;});
  }
  var raw=[];
  tris.forEach(function(t){
    var a=t[0],b=t[1],c=t[2];
    raw.push({type:'hex',pts:[cut(a,b,1/3),cut(a,b,2/3),cut(b,c,1/3),cut(b,c,2/3),cut(c,a,1/3),cut(c,a,2/3)]});
  });
  verts.forEach(function(_,i){var pts=cornerOrder(i);if(pts.length===5)raw.push({type:'pent',pts:pts});});
  // 统一缩放到指定棱长（截角后棱长 = 原二十面体棱长/3）
  var e0=raw[0].pts[0].distanceTo(raw[0].pts[1]);
  var sc=edge/e0;
  var faces=raw.map(function(f){
    var pts=f.pts.map(function(p){return p.multiplyScalar(sc);});
    var C=new THREE.Vector3();pts.forEach(function(p){C.add(p);});C.multiplyScalar(1/pts.length);
    var n=new THREE.Vector3().crossVectors(pts[1].clone().sub(pts[0]),pts[2].clone().sub(pts[0])).normalize();
    if(n.dot(C)<0){n.negate();pts.reverse();}
    var u=pts[0].clone().sub(C).normalize();
    var w=new THREE.Vector3().crossVectors(u,n);   // 局部 X=u, Y=n(外法线), Z=w，右手系
    var d0=pts[0].clone().sub(C);
    return {type:f.type,pts:pts,center:C,normal:n,u:u,w:w,
            offset:Math.atan2(d0.dot(w),d0.dot(u))};
  });
  return faces;
}

/* 每个面一块多边形底砖：顶面与多面体面严格共边，向内挤出厚度 → 32 块严丝合缝 */
function buildPolyTileGeometry(faces,thick){
  var arr=[];
  function tri(a,b,c){arr.push(a.x,a.y,a.z,b.x,b.y,b.z,c.x,c.y,c.z);}
  faces.forEach(function(f){
    var top=f.pts,bot=f.pts.map(function(p){return p.clone().addScaledVector(f.normal,-thick);});
    var cT=f.center,cB=f.center.clone().addScaledVector(f.normal,-thick);
    for(var i=0;i<top.length;i++){
      var j=(i+1)%top.length;
      tri(cT,top[i],top[j]);
      tri(cB,bot[j],bot[i]);
      tri(top[i],bot[i],bot[j]);
      tri(top[i],bot[j],top[j]);
    }
  });
  var g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(arr,3));
  g.computeVertexNormals();
  return g;
}

/* 90 条棱线：沿球面法向外抬，浮在花盘之上，青灰色细线勾勒足球拓扑 */
function buildPolyEdgeLines(faces,lift){
  var arr=[];
  function lifted(p){var r=p.length();return p.clone().multiplyScalar((r+lift)/r);}
  faces.forEach(function(f){
    for(var i=0;i<f.pts.length;i++){
      var a=lifted(f.pts[i]),b=lifted(f.pts[(i+1)%f.pts.length]);
      arr.push(a.x,a.y,a.z,b.x,b.y,b.z);
    }
  });
  var g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(arr,3));
  return g;
}

/* 正60面体的每面贴砖布局：5边形=5株中空；6边形=6株+偏小中心株 */
function buildPolyPlacements(faces,H0,r2l,edge){
  var unitR=H0*r2l*0.44;                 // 单株花盘底面半径（场景单位，与平面蜂窝一致）
  var rHex=0.275*edge;                   // 六边形面外环花盘半径：略收 → 面砖边缘可见，5/6 分组清晰
  var rPent=0.250*edge;                  // 五边形面外环花盘半径：略收 → 五边形轮廓清晰
  var sHex=rHex/unitR,sPent=rPent/unitR,sMid=sHex*0.62;
  var out=[];
  faces.forEach(function(f,fi){
    var M0=new THREE.Matrix4().makeBasis(f.u,f.normal,f.w);
    var isHex=f.type==='hex';
    var cnt=isHex?6:5;
    var ring=isHex?2*rHex:(rPent/Math.sin(Math.PI/5));
    var sc=isHex?sHex:sPent;
    for(var k=0;k<cnt;k++){
      var a=f.offset+2*Math.PI*k/cnt;
      var pos=f.center.clone().addScaledVector(f.u,ring*Math.cos(a))
                            .addScaledVector(f.w,ring*Math.sin(a))
                            .addScaledVector(f.normal,0.02);
      var m=M0.clone();m.scale(new THREE.Vector3(sc,sc,sc));m.setPosition(pos);
      out.push({mat:m,gid:fi*7+k});
    }
    if(isHex){                            // 6 中实：中心一株明显偏小
      var mc=M0.clone();mc.scale(new THREE.Vector3(sMid,sMid,sMid));
      mc.setPosition(f.center.clone().addScaledVector(f.normal,0.02));
      out.push({mat:mc,gid:fi*7+6});
    }
  });
  return out;
}

function buildFractal(keepCam){
  while(root.children.length){
    var o=root.children[0];root.remove(o);
    if(o.geometry)o.geometry.dispose();
    if(o.material){if(o.material.length)o.material.forEach(function(m){m.dispose();});else o.material.dispose();}
  }
  S.leaves=[];
  if(S.polyTileMesh){S.polyTileMesh.geometry.dispose();S.polyTileMesh.material.dispose();S.polyTileMesh=null;}
  if(S.polyEdgeLines){S.polyEdgeLines.geometry.dispose();S.polyEdgeLines.material.dispose();S.polyEdgeLines=null;}

  var alpha=S.angleDeg*Math.PI/180;
  var rnd=mulberry32(S.seed);
  var pal=PALETTES[S.pal];
  var H0=S.altitude;
  var MAX=120000;  // 实例上限保护；缝隙靠几何布局解决，不靠堆锥数
  var rootObj=new THREE.Object3D();
  var nodeCount=0,leafData=[];

  // 单位锥：底 y=0、尖 y=1、底半径 1（尖朝 +Y）
  var geo=new THREE.ConeGeometry(1,1,10,1,false);
  geo.translate(0,0.5,0);

  var vY=new THREE.Vector3(0,1,0);

  /* ===== 忠实近似 Broccoli Equation：锥面对数螺旋密铺 + 芽朝外放射 + IFS 递归 ===== */
  function buildUpright(parent,placements){
    var need=Math.max(1,Math.round(S.upN||7));
    var lv=Math.max(1,Math.round(S.levels));
    var buds=Math.max(8,Math.round(S.upBuds||24));     // 每层芽数≈对数螺旋采样点(源头200π的近似)
    var alpha=S.angleDeg*Math.PI/180;                  // 黄金角(螺旋相位)
    var unitR=H0*S.r2l*0.44;
    var d=2*unitR*(S.upSpread||1.8);
    var scale=unitR/(H0*S.r2l);

    var pts;
    S.fillCount=0;
    if(placements){                               // 正60面体：每个面的花盘由预计算的空间矩阵摆放
      pts=placements;
      S.polyFlowers=pts.length;
    }else{
    // 六边形蜂窝坐标
    pts=[{x:0,z:0}];
    for(var k=1;pts.length<need;k++){
      var rad=k*d,corner=[];
      for(var c=0;c<6;c++){var ca=Math.PI/3*c;corner.push({x:rad*Math.cos(ca),z:rad*Math.sin(ca)});}
      for(var e=0;e<6;e++){
        var p0=corner[e],p1=corner[(e+1)%6];
        for(var j=0;j<k;j++){var f=j/k;pts.push({x:p0.x+(p1.x-p0.x)*f,z:p0.z+(p1.z-p0.z)*f});if(pts.length>=need)break;}
        if(pts.length>=need)break;
      }
    }
    pts=pts.slice(0,need);

    /* ===== 自动填满 = 补齐到下一个完整六边形环（轴向坐标格点法）=====
       六边形中心数序列 1,7,19,37…（半径 k 环含 3k²+3k+1 格点）。
       主株 upN=7(中心+6环绕,k=1) 开启后补齐到 k=2 的 19 个格点 → 补 12 株，
       正好是一整圈第二环、外轮廓仍是标准正六边形（不是三角重心/外缘顶点那种近似）。
       轴向坐标 (q,r) → 笛卡尔: x=d·(q+r/2), z=d·(√3/2·r);  环号=max(|q|,|r|,|q+r|)。*/
    if(S.autoFill&&pts.length>=3){
      var SQ3=Math.sqrt(3);
      var qkOf=function(p){return Math.round(p.x/d*100)+'_'+Math.round(p.z/d*100);};
      var exist={};pts.forEach(function(p){exist[qkOf(p)]=1;});  // 已有主株(浮点坐标)的 key
      // 由笛卡尔坐标反解轴向坐标(四舍五入到最近格点)
      var axialOf=function(p){
        var qf=p.x/d - p.z/(d*SQ3), rf=(2/Math.sqrt(3))*p.z/d;
        return {q:Math.round(qf),r:Math.round(rf)};
      };
      var xyOf=function(q,r){return {x:d*(q+r/2),z:d*(SQ3/2*r)};};
      var ringOf=function(q,r){return Math.max(Math.abs(q),Math.abs(r),Math.abs(q+r));};
      // 主株最大环号 k
      var kmax=1;pts.forEach(function(p){var a=axialOf(p);var kr=ringOf(a.q,a.r);if(kr>kmax)kmax=kr;});
      var kfill=kmax+1;                              // 补齐到下一环
      var fills=[];
      for(var q=-kfill;q<=kfill;q++)for(var r=-kfill;r<=kfill;r++){
        if(ringOf(q,r)!==kfill)continue;              // 只取新增的这一环
        var pos=xyOf(q,r);
        if(exist[qkOf(pos)])continue;                 // 已存在则跳过
        fills.push({x:pos.x,z:pos.z});
      }
      // 补株用缩小比例：整体 scale 乘 fillK
      fills.forEach(function(f){pts.push({x:f.x,z:f.z,fill:true});});
      S.fillCount=fills.length;
    }
    }

    /* ===== 单株底盘 = 1中心 + 6环绕 的六边形蜂窝（生命之花） =====
       7 个底盘锥两两相切：中心 (0,0)，环绕半径 = 2·bR，整体外径 = 3·bR = R0 */
    var R0=H0*S.r2l;                       // 单株原底面半径(局部)
    var bR=R0/3;                           // 底盘单元底半径 → 3·bR = R0 恰好铺满
    var ringR=2*bR;                        // 环绕单元中心半径(相邻相切)
    var bH=H0*0.50;                        // 底盘锥高
    var baseCells=[{x:0,z:0}];
    for(var h=0;h<6;h++){
      var ha=Math.PI/3*h;
      baseCells.push({x:ringR*Math.cos(ha),z:ringR*Math.sin(ha)});
    }

    /* ===== 预算规划：自适应每级芽数，保证每棵子树完整生成（杜绝底盘外露 bug） =====
       原来 levels=5 理论锥数 ≈ 70万 >> MAX，递归中途硬截断 → 父锥已渲染、子锥没长 → 露出大圆锥面。
       这里反解在预算内可完整生成的最大芽数：每底盘锥数 = 1+b+...+b^(lv-1) */
    var BUDGET=80000;                                   // 完整子树预算：层数修正后按 lv 计代价，留余量避免截断
    var perBase=Math.max(2,Math.floor(BUDGET/(pts.length*baseCells.length)));
    var layers=lv;                                      // 实际渲染层数：1=仅底盘锥；2=加一代；3=加两代
    function treeCost(b,L){var s=0,t=1;for(var k=0;k<L;k++){s+=t;t*=b;}return s;}
    var budsEff=buds;
    while(budsEff>2&&treeCost(budsEff,layers)>perBase)budsEff--;
    if(treeCost(budsEff,layers)>perBase)budsEff=2;
    S.upBudsEff=budsEff;                                // 供 HUD 显示真实生效芽数

    // IFS 递归的芽：圆锥本体 + 锥面螺旋上的子芽
    // cx,cz = 所属花球(底盘锥)的中心(rootObj 局部坐标)，供斐波那契螺旋臂着色用
    function broccoli(host,H,R,level,cx,cz,seq,gid){
      if(nodeCount>MAX)return;
      // 本级圆锥本体：level 0 主锥是被覆盖的塔底，不渲染（避免露出大底面）
      if(level>0){
        var self=new THREE.Object3D();host.add(self);nodeCount++;
        leafData.push({obj:self,h:H,r:R,t:(level)/Math.max(1,lv-1),level:level+1,cx:cx,cz:cz,seq:seq||0,gid:gid});
      }
      if(level>=lv)return;                              // 层级定义：lv=1 只有底盘锥；lv=2 多一代；lv=3 多两代
      // 沿锥面铺芽：底层分布角度算法可切换；t 由底(0)到顶(1)，芽随高度指数缩小
      var perRing=0,totalRings=1,symRad=0;
      if(S.spiralMode!=='golden'){
        perRing=Math.max(2,Math.round(360/S.spiralDeg)); // 每环芽数（整除→旋转对称）
        totalRings=Math.max(1,Math.ceil(budsEff/perRing));
        symRad=S.spiralDeg*Math.PI/180;
      }
      for(var i=0;i<budsEff&&nodeCount<MAX;i++){
        var u=i/(budsEff-1);                            // 0..1
        var theta,t;
        if(S.spiralMode==='golden'){
          theta=i*alpha;                                // 黄金角：均匀螺旋（自然、非镜像对称）
          t=0.08+0.86*u;                                // 高度连续
        }else{
          var ri=Math.floor(i/perRing),pj=i%perRing;    // 第 ri 环、环内第 pj 个
          // 环内保持对称角量化；环间相位由“发散角”驱动 → 调发散角即时改变图形
          theta=pj*symRad + ri*alpha + (ri%2?symRad*0.5:0);
          t=0.08+0.86*(totalRings<=1?0.5:ri/(totalRings-1)); // 同环等高 → 旋转对称
        }
        // 对数螺旋半径衰减：r ∝ a^θ，用 b 控制收拢
        var taper=Math.pow(0.5,u*1.0);                  // a=1/2 递推
        var rho=R*(1-t)*0.92;                           // 该高度锥半径
        var px=Math.cos(theta)*rho, pz=Math.sin(theta)*rho, py=H*t;
        // 子芽尺寸：底大顶小 (S2)
        var bH=H*0.5*taper, bR=bH*S.r2l*0.9;
        // R：芽沿母锥母线方向朝外上放射（spread=锥半顶角），贴合锥面不撑爆
        var beta=Math.atan(R/H);
        var spread=beta*(0.9+0.2*(1-t));                // 沿母线方向，底略外张
        var axis=new THREE.Vector3(Math.cos(theta)*Math.sin(spread),Math.cos(spread),Math.sin(theta)*Math.sin(spread)).normalize();
        var bud=new THREE.Object3D();
        bud.position.set(px,py,pz);
        if(S.upTilt>0) bud.quaternion.setFromUnitVectors(vY,axis); // upTilt=0 → 全竖直(圣诞树)
        host.add(bud);   // 容器节点不计入预算：只统计真正渲染的锥体，否则高 levels 会中途截断漏株
        broccoli(bud,bH,bR,level+1,cx,cz,i,gid);   // i=叶序序号：theta=i·黄金角，i mod F 即 parastichy 臂号
      }
    }
    S.uprightCenters=[]; S.uprightUnitR=unitR; S.uprightD=d;   // 供平面六边形砖底盘使用
    for(var pi=0;pi<pts.length;pi++){
      var p=pts[pi],gid=(p.gid!=null)?p.gid:null,cX=0,cZ=0;
      var rootPl=new THREE.Object3D();
      if(p.mat){                            // 正60面体：整株按面法线"竖"在该面上
        rootPl.matrixAutoUpdate=false;
        rootPl.matrix.copy(p.mat);
        cX=p.mat.elements[12];cZ=p.mat.elements[14];
      }else{                                // 平面蜂窝：底面平放平台
        S.uprightCenters.push({x:p.x,z:p.z,k:p.fill?S.fillK:1});
        var sc=scale*(p.fill?S.fillK:1);
        rootPl.position.set(p.x,0,p.z);
        rootPl.scale.setScalar(sc);
        cX=p.x;cZ=p.z;
      }
      parent.add(rootPl);
      // 7 个底盘锥：中心 1 + 环绕 6，底面两两相切 → 从底下看就是标准六边形蜂窝(生命之花)
      for(var bi=0;bi<baseCells.length&&nodeCount<MAX;bi++){
        var bp=new THREE.Object3D();
        bp.position.set(baseCells[bi].x,0,baseCells[bi].z);
        rootPl.add(bp);nodeCount++;
        // 该花球中心在 rootObj 局部坐标 = 株位置 + 底盘锥局部位置×株缩放
        var sc2=(p.mat)?0:scale*(p.fill?S.fillK:1);   // 多面体模式用 gid 分组，cx/cz 只作平面模式后备
        broccoli(bp,bH,bR,1,cX+baseCells[bi].x*sc2,cZ+baseCells[bi].z*sc2,bi,gid);
      }
    }
  }

  function grow(parent,H,R,level,maxLevel){
    if(nodeCount>MAX)return;
    var n=S.cones;
    var beta=Math.atan(R/H);
    var sinB=Math.sin(beta),cosB=Math.cos(beta);
    // 每一级先放一个中央主锥（构成实心塔芯），它本身继续递归
    var core=new THREE.Object3D();
    core.position.set(0,0,0);
    parent.add(core); nodeCount++;
    var coreH=H,coreR=R;
    // 中央芯只作递归骨架、不渲染，塔身由末端叶锥簇构成（避免大底面外露）
    if(level+1<maxLevel) grow(core,coreH,coreR,level+1,maxLevel);
    if(level>=maxLevel)return;
    for(var i=0;i<n;i++){
      if(nodeCount>MAX)break;
      var t=0.12+0.80*(i+0.5)/n;
      var theta=i*alpha;
      var radial=new THREE.Vector3(Math.cos(theta),0,Math.sin(theta));
      var surfR=R*(1-t)*0.72;
      var pos=new THREE.Vector3(radial.x*surfR,H*t,radial.z*surfR);
      // 子锥轴：主要朝上、略微外倾（tilt 系数），使整体收拢成塔
      var tilt=sinB*0.55;
      var axis=new THREE.Vector3(radial.x*tilt,cosB,radial.z*tilt).normalize();
      var q=new THREE.Quaternion().setFromUnitVectors(vY,axis);
      var child=new THREE.Object3D();
      child.position.copy(pos);
      child.quaternion.copy(q);
      parent.add(child);
      nodeCount++;
      var childH=H*S.i2o*(1-0.45*t);
      var childR=childH*S.r2l;
      if(level+1>=maxLevel){
        leafData.push({obj:child,h:childH,r:childR,t:t,level:level+1});
      }else{
        grow(child,childH,childR,level+1,maxLevel);
      }
    }
  }
  if(S.form==='poly'){
    // 32 面朝外贴砖：多边形底砖 + 每面 5/6+1 株直立花盘
    var faces=buildTruncatedIcosahedron(S.polyEdge||2.4);
    S.polyFaces=faces;
    var tileGeo=buildPolyTileGeometry(faces,(S.hexThick||5)*MM*0.32);
    var tileMat=new THREE.MeshStandardMaterial({color:0xc4c9cf,roughness:0.82,metalness:0.02,side:THREE.DoubleSide});
    S.polyTileMesh=new THREE.Mesh(tileGeo,tileMat);
    root.add(S.polyTileMesh);
    if(S.polyEdges){
      var eg=buildPolyEdgeLines(faces,H0*0.24);
      S.polyEdgeLines=new THREE.LineSegments(eg,new THREE.LineBasicMaterial({color:0x66727e,transparent:true,opacity:0.55}));
      root.add(S.polyEdgeLines);
    }
    buildUpright(rootObj,buildPolyPlacements(faces,H0,S.r2l,S.polyEdge||2.4));
  }else if(S.form==='upright') buildUpright(rootObj);
  else grow(rootObj,H0,H0*S.r2l,0,S.levels);
  rootObj.updateMatrixWorld(true);   // 整棵树构建完再统一刷新世界矩阵
  if(!leafData.length)return;
  // 此时才能安全读取每个叶锥的最终世界矩阵
  leafData.forEach(function(d){ d.m=d.obj.matrixWorld.clone(); delete d.obj; });

  var maxH=0;for(var mi=0;mi<leafData.length;mi++){if(leafData[mi].h>maxH)maxH=leafData[mi].h;}  // 避免大数组 apply 爆栈
  var maxLevel=S.levels;
  // 世界高度范围：级级套叠时可见的都是末级，只有“世界高度”能产生肉眼可见的分层渐变
  var yMin=1e9,yMax=-1e9;
  leafData.forEach(function(d){
    var wy=d.m?d.m.elements[13]:0;
    if(wy<yMin)yMin=wy;if(wy>yMax)yMax=wy;
  });
  if(yMax-yMin<1e-6)yMax=yMin+1;

  /* ===== 斐波那契螺旋臂：每株按黄金角叶序分 N 臂，相邻臂严格异色（黄/绿/紫）=====
     参考《Broccoli Equation》配图：黄金角叶序的 parastichy 螺旋臂被染成不同颜色，
     此处用 黄/绿/紫 三色周期序列严格交替，同时每级小锥保留层级明度差。
     做法：锥的世界位置 (x,z) → 减去所属植株中心 → 极角 theta + 半径 rho；
     对数螺旋相位 phi = theta/(2π) + k·ln(rho/rhoMax)·(臂数/2π)，
     取 floor 得臂号 arm；arm 经黄金比低差异散列映射到三色组。*/
  var fibArms=Math.max(2,Math.round(S.fibArms||13));
  var fibK=(S.fibTwist!=null)?S.fibTwist:2.6;   // 0 是合法值(不缠绕)，不能用 || 否则回退
  var PHI_G=(1+Math.sqrt(5))/2;
  // 每个花球各自的局部最大半径（按花球中心分组），归一化 ln(rho) 用。
  // 必须用局部尺度：若用全场尺度，花球内 rho 极小 → ln 剧烈震荡 → 臂碎成噪点。
  var rhoMap={};
  leafData.forEach(function(d){
    if(!d.m)return;
    var wx=d.m.elements[12],wz=d.m.elements[14];
    var ocx=(d.cx!=null)?d.cx:0, ocz=(d.cz!=null)?d.cz:0;
    var key=(d.gid!=null)?('g'+d.gid):(Math.round(ocx*50)+'_'+Math.round(ocz*50));
    var rho=Math.hypot(wx-ocx,wz-ocz);
    if(!rhoMap[key]||rho>rhoMap[key])rhoMap[key]=rho;
  });

  leafData.forEach(function(d){
    var f=clamp(d.h/maxH,0,1);
    var lt=clamp((d.level-1)/Math.max(1,maxLevel-1),0,1);   // 层级归一 0..1
    var wy=d.m?d.m.elements[13]:0;
    var hN=clamp((wy-yMin)/(yMax-yMin),0,1);                 // 世界高度归一 0..1
    if(S.cmap==='fib'){
      // 两种效果叠加：① 相邻螺旋臂异色(黄/绿/紫) ② 按层级颜色从深到浅
      // ① Parastichy：子芽 theta=seq·黄金角，arm=seq mod 臂数 即一条可见螺旋臂；
      //    三色严格循环(arm%3) → 相邻臂必异色，不会并成大片。
      var seq=(d.seq!=null)?d.seq:0;
      // 缠绕度：改变芽在黄金角螺旋上的步进密度 → 臂数/缠绕松紧即时变化。
      // seq 均匀分布(0..每级芽数)，floor 后必然覆盖多个臂号，滑杆一定生效；同 seq 恒同臂(同色)。
      var arm=((Math.floor(seq*(1+fibK*0.05))%fibArms)+fibArms)%fibArms;  // 0..臂数-1
      var FIBSEQ=[0.13,0.31,0.74];                            // 黄(金) / 绿(深橄榄) / 紫(蓝紫)
      var ci=((arm%3)+3)%3;
      var hue=FIBSEQ[ci];
      var sat=(ci===0)?0.80:((ci===1)?0.70:0.60);             // 中高饱和：浓郁但不荧光
      // ② 层级深浅：底层深→顶层浅。明度 0.26~0.50，保证浓郁不过曝
      var depthN=clamp((d.level-2)/Math.max(1,maxLevel-2),0,1);
      var lig=clamp(lerp(0.26,0.50,depthN)+(hN-0.5)*0.03,0.20,0.56);
      d.color=new THREE.Color().setHSL(hue,sat,lig);
    }else if(S.cmap==='hsvarm'){
      // HSV 连续色环做基色(按世界高度转一圈)，明度按螺旋臂号交替深浅 → 臂与臂用明暗隔开
      var seqH=(d.seq!=null)?d.seq:0;
      var armH=((Math.floor(seqH*(1+fibK*0.05))%fibArms)+fibArms)%fibArms;
      var armShade=((armH%2)+2)%2;                         // 相邻臂深浅交替
      var baseHue=(0.60+0.85*hN+0.04*lt)%1;                // HSV 色环随高度渐变
      var ligH=armShade?lerp(0.30,0.40,hN):lerp(0.52,0.64,hN); // 深臂/浅臂
      d.color=new THREE.Color().setHSL(baseHue,0.78,ligH);
    }else if(S.cmap==='height'){
      var h=lerp(pal.hue[0],pal.hue[1],1-f)+(rnd()-0.5)*0.010;
      var sat=lerp(pal.sat[0],pal.sat[1],1-f);
      var li=lerp(pal.light[0],pal.light[1],1-f);
      d.color=new THREE.Color().setHSL(clamp(h,0,1),sat,li);
    }else if(S.cmap==='level'){
      // 层级 + 高度混合：层级给主色相跳变，世界高度给可见的连续渐变（避免只看得到末级单色）
      var ltLevel=clamp((d.level-2)/Math.max(1,maxLevel-2),0,1);
      var hue=(0.34+0.60*ltLevel+0.10*hN)%1;            // 级间跳色相 + 高度微移
      var li2=lerp(0.30,0.60,hN);                        // 按世界高度渐变明度 → 侧视清晰分层
      d.color=new THREE.Color().setHSL(hue,0.70,clamp(li2,0.26,0.62));
    }else{
      // cmap 按世界高度取色 → 底→顶连续梯度，肉眼可见
      d.color=cmapRGB(S.cmap,0.15+0.85*hN);
    }
    d.birth=clamp(0.06+0.62*(d.level/maxLevel)*0.55+0.62*d.t*0.45+(rnd()-0.5)*0.03,0,0.9);
  });
  // 按出生时间排序，长的有序
  leafData.sort(function(a,b){return a.birth-b.birth;});
  S.leaves=leafData;
  // 调试：统计每株实际生成的锥数，确保没有任何一株被预算/截断漏掉
  window.__plantStats=null;
  if((S.form==='upright'||S.form==='poly')&&leafData.length){
    var grp={};
    leafData.forEach(function(d){
      var key;
      if(d.gid!=null)key='g'+d.gid;
      else{
        var best=0,bd=1e9;
        (S.uprightCenters||[]).forEach(function(c,i){
          var dd=(d.cx-c.x)*(d.cx-c.x)+(d.cz-c.z)*(d.cz-c.z);
          if(dd<bd){bd=dd;best=i;}
        });
        key='p'+best;
      }
      grp[key]=(grp[key]||0)+1;
    });
    var ks=Object.keys(grp),mn=1e9,mx=0;
    ks.forEach(function(k){if(grp[k]<mn)mn=grp[k];if(grp[k]>mx)mx=grp[k];});
    window.__plantStats={plants:ks.length,min:mn,max:mx,empty:ks.filter(function(k){return grp[k]===0;}).length};
  }
  // InstancedMesh 统一由 buildRenderList() 创建（单株/蜂窝共用一套渲染列表）

  if(S.spiral){
    var pts=[],n=320;
    for(var k=0;k<n;k++){
      var th=k/n*Math.PI*2*3.4;
      var f=Math.pow(PHI,-th/(2*Math.PI));
      pts.push(new THREE.Vector3(H0*S.r2l*f*Math.cos(th),H0*(1-f),H0*S.r2l*f*Math.sin(th)));
    }
    var g2=new THREE.BufferGeometry().setFromPoints(pts);
    spiralLine=new THREE.Line(g2,new THREE.LineBasicMaterial({color:0xc98a00,transparent:true,opacity:0.65}));
    root.add(spiralLine);
  }

  /* ---------- 第0级蜂窝面板：六边形密堆积（1 中心 + 6 环绕） ---------- */
  var MM=0.1; // 1mm = 0.1 场景单位
  function buildHoneycombCells(){
    S.cells=[];
    if(!S.honey)return;
    var L=S.boardL*MM, W=S.boardW*MM;
    var d=S.brocSize*MM;               // 单元圆直径
    var R=d/2;                          // 圆半径
    var stepX=2*R;                      // 六角密堆积水平间距
    var stepZ=Math.sqrt(3)*R;           // 垂直间距
    var margin=R*0.35;
    var cols=Math.max(1,Math.floor((L-2*margin)/stepX)+1);
    var rows=Math.max(1,Math.floor((W-2*margin)/stepZ)+1);
    var originX=-(cols-1)*stepX/2;
    var originZ=-(rows-1)*stepZ/2;
    for(var r=0;r<rows;r++){
      for(var c=0;c<cols;c++){
        var x=originX+c*stepX+(r%2?R:0);
        var z=originZ+r*stepZ;
        if(Math.abs(x)+R>L/2+0.01||Math.abs(z)+R>W/2+0.01)continue;
        S.cells.push({x:x,z:z});
      }
    }
  }

  /* ---------- 红色六边形砖底盘：按主株格点密铺，向上抬升与株底部分重叠 ---------- */
  function buildHexBase(){
    if(S.hexBaseMesh){root.remove(S.hexBaseMesh);S.hexBaseMesh.geometry.dispose();S.hexBaseMesh.material.dispose();S.hexBaseMesh=null;}
    if(S.form!=='upright'||!S.hexBase||!S.uprightCenters||!S.uprightCenters.length)return;
    var d=S.uprightD||1;                       // 主株中心距(场景单位)
    var unitR=S.uprightUnitR||d/2;             // 单株底面半径
    // 底盘 = 一整块大正六棱柱，6 条直边包络所有花球 → 外轮廓必为标准六边形。
    // 关键(返工根因)：格点六边形环的 6 个角点在方位角 0/60/120...（atan2(z,x)），
    // 而 THREE.CylinderGeometry 的 6 顶点默认在方位角 30/90/150...，
    // 必须 rotateY(+30°) 让顶点对准花球角点；否则底盘边中点(内切半径=外接×0.866)
    // 正对花球角点方向 → 花球从边上露出，观感即“错位60°+花底座没全在盘上+V形缺口”。
    // 半径：对 3 组对边法线(30/90/150°)取 max(花球中心投影+花球半径)=内切半径 a，
    // 外接半径 Rbig=a/cos30°，保证所有花球被包络、同时红边最小。
    // 用所有锥的实际水平位置(含分形外扩)求包络：花球真实半径 >> unitR(仅圆锥底半径)，
    // 若按 unitR 算底盘会偏小，外环花球露在盘外成“六角星”。
    var cos30=Math.cos(Math.PI/6);
    var normals=[Math.PI/6,Math.PI/2,Math.PI/6+2*Math.PI/3];
    var apothem=0;
    // 先把每个锥的世界 xz + 该锥底半径存成点集
    var ptsXZ=[];
    (S.leaves||[]).forEach(function(l){
      if(!l.m)return;
      ptsXZ.push({x:l.m.elements[12],z:l.m.elements[14],r:(l.r||0)*0.5});
    });
    for(var ni=0;ni<normals.length;ni++){
      var nx=Math.cos(normals[ni]),nz=Math.sin(normals[ni]);
      var projMax=0;
      for(var i=0;i<ptsXZ.length;i++){
        var p=ptsXZ[i];
        var proj=p.x*nx+p.z*nz+p.r;            // 锥中心投影 + 锥底半径
        if(proj>projMax)projMax=proj;
      }
      if(projMax>apothem)apothem=projMax;
    }
    var Rbig=apothem/cos30;                    // 外接半径：6 条边恰好包络所有锥的外缘
    var thick=S.hexThick*MM;                   // 厚度 mm→场景
    var topY=S.hexOverlap;                     // 砖顶面高度(>0 即插进株底，形成重叠)
    var geo=new THREE.CylinderGeometry(Rbig,Rbig,thick,6,1,false);  // 单个大正六棱柱
    geo.rotateY(Math.PI/6);                    // 顶点对准 0/60/120...（花球格点角点方向）
    geo.translate(0, topY-thick/2, 0);
    var mat=new THREE.MeshStandardMaterial({color:0xd5d8dc,roughness:0.82,metalness:0.02,side:THREE.DoubleSide});
    var mesh=new THREE.Mesh(geo,mat);
    root.add(mesh);S.hexBaseMesh=mesh;
  }

  /* ---------- 构建"最终渲染实例列表"：单株 or 蜂窝复制 ---------- */
  function buildRenderList(keepCam){
    S.renderList=[];
    // 底板 mesh
    if(S.plateMesh){root.remove(S.plateMesh);S.plateMesh.geometry.dispose();S.plateMesh.material.dispose();S.plateMesh=null;}
    var boxMin=new THREE.Vector3(),boxMax=new THREE.Vector3();
    if(S.honey){
      buildHoneycombCells();
      var scale=(S.brocSize*MM)/S.altitude;   // 单株高6场景单位 -> brocSize
      var lift=S.boardT*MM;                   // 板厚：锥底抬到板面
      var mPlate=new THREE.Mesh(
        new THREE.BoxGeometry(S.boardL*MM,S.boardT*MM,S.boardW*MM),
        new THREE.MeshStandardMaterial({color:0xdfe7dd,roughness:0.9,wireframe:S.wire}));
      mPlate.position.set(0,-S.boardT*MM/2,0);
      root.add(mPlate);S.plateMesh=mPlate;
      var CAP=80000;
      S.cells.forEach(function(cell,ci){
        if(S.renderList.length>=CAP)return;
        var T=new THREE.Matrix4().makeTranslation(cell.x,lift,cell.z);
        var Sc=new THREE.Matrix4().makeScale(scale,scale,scale);
        var base=T.multiply(Sc);
        S.leaves.forEach(function(l){
          if(S.renderList.length>=CAP)return;
          var mm=base.clone().multiply(l.m);
          S.renderList.push({m:mm,h:l.h*scale,r:l.r*scale,color:l.color,birth:l.birth,cell:ci});
        });
      });
      boxMin.set(-S.boardL*MM/2,0,-S.boardW*MM/2);
      boxMax.set(S.boardL*MM/2,lift+S.brocSize*MM,S.boardW*MM/2);
    }else{
      S.leaves.forEach(function(l){S.renderList.push({m:l.m.clone(),h:l.h,r:l.r,color:l.color,birth:l.birth,cell:0});});
      S.leaves.forEach(function(l){var p=new THREE.Vector3().setFromMatrixPosition(l.m);boxMax.max(p);boxMin.min(p);});
      boxMax.y+=S.altitude;
    }
    S._boxMin=boxMin;S._boxMax=boxMax;
    // 重建 InstancedMesh
    if(leafMesh){root.remove(leafMesh);leafMesh.geometry.dispose();leafMesh.material.dispose();leafMesh=null;}
    var geo=new THREE.ConeGeometry(1,1,10,1,false);
    geo.translate(0,0.5,0);
    var mat=new THREE.MeshStandardMaterial({roughness:0.82,metalness:0.02,side:THREE.DoubleSide,wireframe:S.wire});
    leafMesh=new THREE.InstancedMesh(geo,mat,Math.max(1,S.renderList.length));
    leafMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    root.add(leafMesh);
    // 相机：仅首次构建取景一次；之后调任何参数/切预设都保持用户当前视角不动
    if(!_camFramed){
      var size=new THREE.Vector3().subVectors(boxMax,boxMin);
      var c=boxMin.clone().addScaledVector(size,0.5);
      cam.target.copy(c);
      cam.radius=clamp(Math.max(size.x,size.y,size.z)*1.55,6,120);
      cam.phi=S.honey?0.62:0.92;   // 蜂窝模式偏俯视，看"生命之花"
      _camFramed=true;
    }
    buildHexBase();
  }

  /* ---------- 公共：提取所有三角面（单位 mm） ---------- */
  function collectTriangles(seg){
    if(!S.renderList.length)return [];
    var tris=[];
    var expGeo=new THREE.ConeGeometry(1,1,seg||5,1,false);
    expGeo.translate(0,0.5,0);
    var pos=expGeo.getAttribute('position'),idx=expGeo.index;
    var triCount=idx?idx.count/3:pos.count/3;
    var v=new THREE.Vector3(),k=1/MM;
    function push(mat,p1,p2,p3){
      v.fromBufferAttribute(pos,p1).applyMatrix4(mat);var a=v.clone();
      v.fromBufferAttribute(pos,p2).applyMatrix4(mat);var b=v.clone();
      v.fromBufferAttribute(pos,p3).applyMatrix4(mat);var cc=v.clone();
      tris.push([a.x*k,a.y*k,a.z*k,b.x*k,b.y*k,b.z*k,cc.x*k,cc.y*k,cc.z*k]);
    }
    S.renderList.forEach(function(l){
      var g=clamp(S.prog,0,1),s=(g<=l.birth)?0.0001:1;
      var M=l.m.clone().multiply(new THREE.Matrix4().makeScale(l.r*s,l.h*s,l.r*s));
      for(var t=0;t<triCount;t++){
        if(idx)push(M,idx.getX(t*3),idx.getX(t*3+1),idx.getX(t*3+2));
        else push(M,t*3,t*3+1,t*3+2);
      }
    });
    if(S.honey&&S.plateMesh){
      var pm=S.plateMesh;pm.updateMatrixWorld(true);
      var pg=pm.geometry,pp=pg.getAttribute('position'),pi=pg.index;
      var pt=pi?pi.count/3:pp.count/3;
      for(var t2=0;t2<pt;t2++){
        var a2=new THREE.Vector3().fromBufferAttribute(pp,pi?pi.getX(t2*3):t2*3).applyMatrix4(pm.matrixWorld);
        var b2=new THREE.Vector3().fromBufferAttribute(pp,pi?pi.getX(t2*3+1):t2*3+1).applyMatrix4(pm.matrixWorld);
        var c2=new THREE.Vector3().fromBufferAttribute(pp,pi?pi.getX(t2*3+2):t2*3+2).applyMatrix4(pm.matrixWorld);
        tris.push([a2.x*k,a2.y*k,a2.z*k,b2.x*k,b2.y*k,b2.z*k,c2.x*k,c2.y*k,c2.z*k]);
      }
    }
    // 红色六边形砖底盘（每个实例一块正六棱柱）
    if(S.hexBaseMesh){
      var hm=S.hexBaseMesh,hg=hm.geometry,hp=hg.getAttribute('position'),hi=hg.index;
      var ht=hi?hi.count/3:hp.count/3, im4=new THREE.Matrix4();
      for(var ii=0;ii<hm.count;ii++){
        hm.getMatrixAt(ii,im4);
        for(var t3=0;t3<ht;t3++){
          var ha=new THREE.Vector3().fromBufferAttribute(hp,hi?hi.getX(t3*3):t3*3).applyMatrix4(im4);
          var hb2=new THREE.Vector3().fromBufferAttribute(hp,hi?hi.getX(t3*3+1):t3*3+1).applyMatrix4(im4);
          var hc=new THREE.Vector3().fromBufferAttribute(hp,hi?hi.getX(t3*3+2):t3*3+2).applyMatrix4(im4);
          tris.push([ha.x*k,ha.y*k,ha.z*k,hb2.x*k,hb2.y*k,hb2.z*k,hc.x*k,hc.y*k,hc.z*k]);
        }
      }
    }
    // 正60面体：32 块面砖（多边形棱柱）一并导出
    if(S.polyTileMesh){
      var pm3=S.polyTileMesh,pg3=pm3.geometry,pa3=pg3.getAttribute('position');
      pm3.updateMatrixWorld(true);
      for(var t5=0;t5<pa3.count;t5+=3){
        var p1=new THREE.Vector3().fromBufferAttribute(pa3,t5).applyMatrix4(pm3.matrixWorld);
        var p2=new THREE.Vector3().fromBufferAttribute(pa3,t5+1).applyMatrix4(pm3.matrixWorld);
        var p3=new THREE.Vector3().fromBufferAttribute(pa3,t5+2).applyMatrix4(pm3.matrixWorld);
        tris.push([p1.x*k,p1.y*k,p1.z*k,p2.x*k,p2.y*k,p2.z*k,p3.x*k,p3.y*k,p3.z*k]);
      }
    }
    expGeo.dispose();
    return tris;
  }
  function baseName(){
    var tag=S.form==='poly'?('bucky32faces_'+(S.polyFaces?S.polyFaces.length:32)+'tiles')
                          :(S.honey?('honey_'+S.cells.length+'cells'):'single');
    return 'romanesco_'+tag+'_'+S.levels+'L';
  }
  function download(blob,name){
    var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;
    a.click();setTimeout(function(){URL.revokeObjectURL(a.href);},3000);
  }

  /* ---------- STL（二进制） ---------- */
  function exportSTL(){
    var tris=collectTriangles(S.stlSeg||5);
    if(!tris.length){alert('没有可导出的几何');return 0;}
    var buf=new ArrayBuffer(84+tris.length*50),dv=new DataView(buf);
    var enc=function(off,str){for(var i=0;i<str.length&&i<79;i++)dv.setUint8(off+i,str.charCodeAt(i));};
    enc(0,'Romanesco fractal '+S.levels+'L '+S.cells.length+'cells unit=mm');
    dv.setUint32(80,tris.length,true);
    var o=84;
    tris.forEach(function(t){
      var ux=t[3]-t[0],uy=t[4]-t[1],uz=t[5]-t[2];
      var vx=t[6]-t[0],vy=t[7]-t[1],vz=t[8]-t[2];
      var nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
      var nl=Math.sqrt(nx*nx+ny*ny+nz*nz)||1;
      dv.setFloat32(o,nx/nl,true);dv.setFloat32(o+4,ny/nl,true);dv.setFloat32(o+8,nz/nl,true);o+=12;
      for(var i=0;i<9;i++){dv.setFloat32(o,t[i],true);o+=4;}
      dv.setUint16(o,0,true);o+=2;
    });
    download(new Blob([buf],{type:'model/stl'}),baseName()+'.stl');
    return tris.length;
  }

  /* ---------- OBJ（文本，共享顶点以减小体积） ---------- */
  function exportOBJ(){
    var tris=collectTriangles(S.stlSeg||5);
    if(!tris.length){alert('没有可导出的几何');return 0;}
    var verts=[],index={},faces=[];
    function vid(x,y,z){
      var key=x.toFixed(4)+','+y.toFixed(4)+','+z.toFixed(4);
      if(index[key]!==undefined)return index[key];
      var id=verts.length+1;verts.push([x,y,z]);index[key]=id;return id;
    }
    tris.forEach(function(t){
      var a=vid(t[0],t[1],t[2]),b=vid(t[3],t[4],t[5]),c=vid(t[6],t[7],t[8]);
      faces.push([a,b,c]);
    });
    var lines=['# Romanesco fractal — unit mm','# '+S.levels+'L, '+S.cells.length+' cells','o romanesco'];
    verts.forEach(function(v){lines.push('v '+v[0].toFixed(4)+' '+v[1].toFixed(4)+' '+v[2].toFixed(4));});
    faces.forEach(function(f){lines.push('f '+f[0]+' '+f[1]+' '+f[2]);});
    download(new Blob([lines.join('\n')],{type:'text/plain'}),baseName()+'.obj');
    return tris.length;
  }

  /* ---------- PLY（二进制小端） ---------- */
  function exportPLY(){
    var tris=collectTriangles(S.stlSeg||5);
    if(!tris.length){alert('没有可导出的几何');return 0;}
    var nv=tris.length*3;
    var head='ply\nformat binary_little_endian 1.0\ncomment Romanesco fractal unit=mm\n'
      +'element vertex '+nv+'\nproperty float x\nproperty float y\nproperty float z\n'
      +'element face '+tris.length+'\nproperty list uchar int vertex_indices\nend_header\n';
    var hb=new TextEncoder().encode(head);
    var buf=new ArrayBuffer(hb.length+nv*12+tris.length*16),dv=new DataView(buf);
    hb.forEach(function(b,i){dv.setUint8(i,b);});
    var off=hb.length;
    tris.forEach(function(t){
      for(var i=0;i<9;i++){dv.setFloat32(off,t[i],true);off+=4;}
    });
    tris.forEach(function(_,i){dv.setUint8(off,3);off++;var base=i*3;
      dv.setInt32(off,base,true);off+=4;dv.setInt32(off,base+1,true);off+=4;dv.setInt32(off,base+2,true);off+=4;});
    download(new Blob([buf],{type:'application/octet-stream'}),baseName()+'.ply');
    return tris.length;
  }

  /* ---------- STEP（AP203 · 三角面片 BREP，单位 mm） ---------- */
  /* 说明：STEP 面数过多时文件会很大，接口给 3 万面上限保护。 */
  function exportSTEP(){
    var tris=collectTriangles(S.stlSeg||5);
    if(!tris.length){alert('没有可导出的几何');return 0;}
    var CAP=30000;
    if(tris.length>CAP){
      if(!confirm('当前 '+tris.length+' 面，STEP 导出会很大且慢。\n建议改用 STL/OBJ/PLY。\n仍要继续吗？'))return -1;
    }
    var L=[];
    L.push('ISO-10303-21;');
    L.push('HEADER;');
    L.push("FILE_DESCRIPTION(('Romanesco fractal, unit mm'),'2;1');");
    L.push("FILE_NAME('romanesco.step','2026-01-01',(''),(''),'WorkBuddy','','');");
    L.push("FILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));");
    L.push('ENDSEC;');
    L.push('DATA;');
    L.push("#1=APPLICATION_CONTEXT('configuration controlled 3d designs of mechanical parts and assemblies');");
    L.push("#2=PRODUCT('romanesco','Romanesco fractal', '',(#3));");
    L.push("#3=PRODUCT_CONTEXT('',#1,'mechanical');");
    L.push("#4=PRODUCT_DEFINITION_FORMATION('','',#2);");
    L.push("#5=PRODUCT_DEFINITION('','',#4,#6);");
    L.push("#6=PRODUCT_DEFINITION_CONTEXT('part definition',#1,'design');");
    var id=100;
    function nid(){return '#'+(id++);}
    var faceIds=[];
    // 世界坐标系（先定义，避免编号冲突）
    var orgP=nid(),dirZ=nid(),dirX=nid(),axisW=nid();
    L.push(orgP+"=CARTESIAN_POINT('',(0.,0.,0.));");
    L.push(dirZ+"=DIRECTION('',(0.,0.,1.));");
    L.push(dirX+"=DIRECTION('',(1.,0.,0.));");
    L.push(axisW+'=AXIS2_PLACEMENT_3D(\'\','+orgP+','+dirZ+','+dirX+');');
    L.push(nid()+'=SHAPE_REPRESENTATION(\'romanesco\',(),'+axisW+');');
    // 每个三角面：3 点 -> 3 向量 -> 3 顶点 -> 3 边 -> 边环 -> 面边界 -> 平面 -> 面
    tris.forEach(function(t){
      var pids=[],vids=[],edges=[];
      for(var i=0;i<3;i++){
        var pid=nid();pids.push(pid);
        L.push(pid+"=CARTESIAN_POINT('',("+t[i*3].toFixed(4)+','+t[i*3+1].toFixed(4)+','+t[i*3+2].toFixed(4)+'));');
      }
      var dirid=nid();L.push(dirid+"=DIRECTION('',(0.,0.,1.));");
      var axid=nid(),refdir=nid();
      L.push(refdir+"=DIRECTION('',(1.,0.,0.));");
      L.push(axid+'=AXIS2_PLACEMENT_3D(\'\','+pids[0]+','+dirid+','+refdir+');');
      var plid=nid();L.push(plid+'=PLANE(\'\','+axid+');');
      for(var i2=0;i2<3;i2++){
        var vid2=nid();vids.push(vid2);
        L.push(vid2+'=VERTEX_POINT(\'\','+pids[i2]+');');
      }
      for(var j=0;j<3;j++){
        var vecid=nid(),lineid=nid(),eid=nid();edges.push(eid);
        L.push(vecid+'=VECTOR(\'\','+pids[(j+1)%3]+','+pids[j]+',1.);');
        L.push(lineid+'=LINE(\'\','+pids[j]+','+vecid+');');
        L.push(eid+'=EDGE_CURVE(\'\','+vids[j]+','+vids[(j+1)%3]+','+lineid+',.T.);');
      }
      var loop=nid();L.push(loop+'=EDGE_LOOP(\'\',('+edges.join(',')+'));');
      var bound=nid();L.push(bound+'=FACE_OUTER_BOUND(\'\','+loop+',.T.);');
      var fid=nid();L.push(fid+'=ADVANCED_FACE(\'\',('+bound+'),'+plid+',.T.);');
      faceIds.push(fid);
    });
    var shell=nid();L.push(shell+'=CLOSED_SHELL(\'\',('+faceIds.join(',')+'));');
    var solid=nid();L.push(solid+'=MANIFOLD_SOLID_BREP(\'romanesco\','+shell+');');
    L.push(nid()+'=ADVANCED_BREP_SHAPE_REPRESENTATION(\'\',('+solid+','+axisW+'));');
    L.push('ENDSEC;');L.push('END-ISO-10303-21;');
    download(new Blob([L.join('\n')],{type:'application/step'}),baseName()+'.step');
    return tris.length;
  }

  window.__exporters={stl:exportSTL,obj:exportOBJ,ply:exportPLY,step:exportSTEP,stp:exportSTEP};
  window.__cam={theta:function(){return cam.theta;},phi:function(){return cam.phi;},radius:function(){return cam.radius;}};  // 只读调试接口
  window.__poly=(S.form==='poly'&&faces)?{
    faces:faces.length,
    pent:faces.filter(function(f){return f.type==='pent';}).length,
    hex:faces.filter(function(f){return f.type==='hex';}).length,
    flowers:S.polyFlowers,
    tileTris:S.polyTileMesh?S.polyTileMesh.geometry.getAttribute('position').count/3:0,
    cones:S.renderList.length
  }:null;


  buildHoneycombCells();
  buildRenderList(keepCam);
  updateInstances(S.prog);
  updateHUD();
}

/* 生长动画：easeOutBack 弹出 */
function easeOutBack(x){var c1=1.70158,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2);}
var _m=new THREE.Matrix4(),_s=new THREE.Matrix4();
function updateInstances(prog){
  if(!leafMesh||!S.renderList.length)return;
  var L=S.renderList,vis=0,span=0.30;
  for(var i=0;i<L.length;i++){
    var l=L[i];
    var g=clamp((prog-l.birth)/span,0,1);
    var s=g<=0?0.0001:easeOutBack(g);
    if(g>0.05)vis++;
    _s.makeScale(l.r*s,l.h*s,l.r*s);
    _m.copy(l.m).multiply(_s);
    leafMesh.setMatrixAt(i,_m);
    leafMesh.setColorAt(i,l.color);
  }
  leafMesh.instanceMatrix.needsUpdate=true;
  if(leafMesh.instanceColor)leafMesh.instanceColor.needsUpdate=true;
  leafMesh.count=L.length;
  S.visible=vis;
}
function updateHUD(){
  var n=S.renderList.length,v=S.visible,a=S.angleDeg;
  var fp=fibPair(a),f1=fp[0],f2=fp[1];
  var extra='';
  var polyInfo=(S.form==='poly')?('<br><b>⚽ 正60面体</b> 32 面贴砖 ｜ 12 五边形(5株中空) + 20 六边形(6+1中实) ｜ 花盘 <b>'+S.polyFlowers+'</b>'):'';
  var algo=(S.form==='upright'||S.form==='poly')?('<br>分布算法 <b>'+spiralModeName(S.spiralMode)+'</b>'+(S.spiralMode==='custom'?' '+Math.round(S.spiralDeg)+'°':'')+
    ' ｜ 生效芽数 <b>'+(S.upBudsEff||S.upBuds)+'</b>'+(S.upBudsEff&&S.upBudsEff<S.upBuds?'（预算收敛）':'')+
    (S.autoFill?'<br>自动填满 <b>开</b> ｜ 补株 <b>'+S.fillCount+'</b> 个（'+S.fillK.toFixed(2)+'×）':'')+
    (S.hexBase?'<br>六边形砖底盘 <b>开</b> ｜ '+S.hexThick+'mm ｜ 重叠 '+S.hexOverlap.toFixed(2):'')):'';
  $('hudBody').innerHTML='锥体总数 <b>'+n+'</b> ｜ 已长出 <b>'+v+'</b><br>'+
    '自相似层数 <b>'+S.levels+'</b> ｜ 发散角 <b>'+a.toFixed(3)+'°</b><br>'+
    '可见螺旋列 <b>'+f1+' / '+f2+'</b>（相邻 Fibonacci）'+extra+polyInfo+algo;
  $('legend').innerHTML='φ = 1.6180339887<br>α = 360°/φ² = 137.507°<br>IFS: C′ = T · R(α) · S · C';
  $('fibNote').innerHTML='螺旋列（顺/逆）≈ <b>'+f1+' / '+f2+'</b>（相邻 Fibonacci）。发散角越接近 137.507°，螺旋列越稳定；偏离则出现径向缝隙。';
}

/* ============ 动画循环 ============ */
var last=performance.now();
function loop(now){
  var dt=Math.min((now-last)/1000,0.05);last=now;
  if(S.playing){
    S.prog+=dt*0.22*S.speed;
    if(S.prog>=1.2){S.prog=1.2;S.playing=false;$('btnPlay').textContent='▶ 生长';}
    $('prog').value=Math.round(clamp(S.prog,0,1)*1000);
    $('vProg').textContent=Math.round(clamp(S.prog,0,1)*100)+'%';
    updateInstances(clamp(S.prog,0,1));updateHUD();
  }
  if(S.spin){cam.theta+=dt*0.16;}
  ctrl.update();
  renderer.render(scene,camera);
  requestAnimationFrame(loop);
}

/* ============ UI ============ */
function setRanges(p){
  $('levels').value=p.levels;$('vLevels').textContent=p.levels;
  $('angle').value=p.angle;$('vAngle').textContent=p.angle.toFixed(3)+'°';
  $('cones').value=p.cones;$('vCones').textContent=p.cones;
  $('r2l').value=Math.round(p.r2l*100);
  $('vR2L').textContent=Math.abs(p.r2l-PYRAMID_RL)<0.0001?'1.1118 🔺':p.r2l.toFixed(2);
  $('i2o').value=Math.round(p.i2o*100);$('vI2O').textContent=p.i2o.toFixed(2);
  $('palette').value=p.pal;$('vPalette').textContent=PALETTES[p.pal].name;
  S.levels=p.levels;S.angleDeg=p.angle;S.cones=p.cones;S.r2l=p.r2l;S.i2o=p.i2o;S.pal=p.pal;
  S.form=p.form||'fractal';
  if(S.form==='upright'||S.form==='poly'){
    S.upN=p.cones; if($('upN')){$('upN').value=p.cones;$('vUpN').textContent=p.cones;}
    S.upBuds=p.upBuds!=null?p.upBuds:55;
    S.upTilt=p.upTilt!=null?p.upTilt:1.0;
    S.upSpread=1.0;
    if($('upBuds')){$('upBuds').value=S.upBuds;$('vUpBuds').textContent=S.upBuds;}
    if($('upTilt')){$('upTilt').value=Math.round(S.upTilt*100);$('vUpTilt').textContent=S.upTilt.toFixed(2);}
    if($('upSpread')){$('upSpread').value=10;$('vUpSpread').textContent='1.00×';}
  }
  // 直立花盘 / 正60面体专用参数区显隐
  if($('upSec'))$('upSec').style.display=(S.form==='upright'||S.form==='poly')?'block':'none';
  if($('polyNote'))$('polyNote').style.display=(S.form==='poly')?'block':'none';
  if($('polyEdgesRow'))$('polyEdgesRow').style.display=(S.form==='poly')?'flex':'none';
  syncAlgoUI();
}
function spiralModeName(m){
  return {golden:'黄金角螺旋',silver:'白银比 61.7°',hex60:'六重 60°',oct45:'八重 45°',
          dec36:'十重 36°',quad90:'四重 90°',custom:'自定义角度'}[m]||m;
}
function applySpiralMode(m){
  S.spiralMode=m;
  var DEG={golden:137.508,silver:61.72,hex60:60,oct45:45,dec36:36,quad90:90};
  if(m!=='custom'&&DEG[m]!=null)S.spiralDeg=DEG[m];
  syncAlgoUI();
}
function syncAlgoUI(){
  if($('spiralMode')){$('spiralMode').value=S.spiralMode;$('vSpiralMode').textContent=spiralModeName(S.spiralMode);}
  if($('spiralDeg')){$('spiralDeg').value=Math.round(S.spiralDeg);$('vSpiralDeg').textContent=Math.round(S.spiralDeg)+'°';}
  if($('spiralDegRow'))$('spiralDegRow').style.display=(S.spiralMode==='custom')?'block':'none';
  if($('cmap')){$('cmap').value=S.cmap;$('vCmap').textContent={fib:'斐波那契螺旋臂',hsvarm:'HSV·臂深浅',level:'按层级',hsv:'HSV 色环',turbo:'Turbo',viridis:'Viridis',plasma:'Plasma',height:'按高度'}[S.cmap]||S.cmap;}
  if($('fibOpts'))$('fibOpts').style.display=(S.cmap==='fib'||S.cmap==='hsvarm')?'block':'none';
  if($('fibArms')){$('fibArms').value=String(S.fibArms);$('vFibArms').textContent=S.fibArms;}
  if($('fibTwist')){$('fibTwist').value=Math.round(S.fibTwist*10);$('vFibTwist').textContent=S.fibTwist.toFixed(1);}
  if($('vUpBuds'))$('vUpBuds').textContent=S.upBuds;
  if($('polyEdges'))$('polyEdges').checked=!!S.polyEdges;
  if($('autoFill')){$('autoFill').checked=!!S.autoFill;$('autoFill').disabled=(S.form==='poly');}
  if($('fillK')){$('fillK').value=Math.round(S.fillK*100);$('vFillK').textContent=S.fillK.toFixed(2)+'×';}
  if($('fillKRow'))$('fillKRow').style.display=(S.autoFill&&S.form!=='poly')?'block':'none';
  if($('hexBase')){$('hexBase').checked=!!S.hexBase;$('hexBase').disabled=(S.form==='poly');}
  if($('hexBaseOpts'))$('hexBaseOpts').style.display=S.hexBase?'block':'none';
  if($('hexThick')){$('hexThick').value=Math.round(S.hexThick);$('vHexThick').textContent=S.hexThick+' mm';}
  if($('hexOverlap')){$('hexOverlap').value=Math.round(S.hexOverlap*100);$('vHexOverlap').textContent=S.hexOverlap.toFixed(2);}
}
function initUI(){
  $('preset').addEventListener('change',function(){
    var prev=S.form,p=PRESETS[this.value];setRanges(p);S.prog=0;S.playing=false;
    if(S.form==='poly'){S.autoFill=false;S.hexBase=false;syncAlgoUI();} // 面砖取代平面底盘/补株
    else if(prev==='poly'){S.hexBase=true;S.autoFill=false;syncAlgoUI();} // 从多面体返回恢复平面默认底盘
    $('btnPlay').textContent='▶ 生长';$('prog').value=0;$('vProg').textContent='0%';
    buildFractal(true);
  });
  function rb(id,key,fmt,after){
    $(id).addEventListener('input',function(){
      var v=parseFloat(this.value);S[key]=v;$(fmt.id).textContent=fmt.fn(v);
      if(after)after(v);buildFractal(true);
    });
  }
  rb('levels','levels',{id:'vLevels',fn:function(v){return v;}});
  rb('angle','angleDeg',{id:'vAngle',fn:function(v){return v.toFixed(3)+'°';}});
  rb('cones','cones',{id:'vCones',fn:function(v){return v;}});
  $('r2l').addEventListener('input',function(){S.r2l=parseInt(this.value,10)/100;$('vR2L').textContent=S.r2l.toFixed(2);buildFractal(true);});
  $('btnPyramid').addEventListener('click',function(){
    S.r2l=PYRAMID_RL;
    $('r2l').value=Math.round(S.r2l*100);
    $('vR2L').textContent='1.1118 🔺';
    buildFractal(true);
  });
  $('i2o').addEventListener('input',function(){S.i2o=parseInt(this.value,10)/100;$('vI2O').textContent=S.i2o.toFixed(2);buildFractal(true);});
  $('upN').addEventListener('input',function(){S.upN=parseInt(this.value,10);$('vUpN').textContent=S.upN;buildFractal(true);});
  $('btnGrowRing').addEventListener('click',function(){
    // 中心六边形数 3k²+3k+1：1,7,19,37,61,91,127
    var seq=[];for(var k=0;k<=6;k++)seq.push(3*k*k+3*k+1);
    var cur=S.upN,next=seq[seq.length-1];
    for(var i=0;i<seq.length;i++){if(seq[i]>cur){next=seq[i];break;}}
    if(next===seq[seq.length-1]&&cur>=seq[seq.length-1])next=seq[0];  // 到顶回 1
    S.upN=next;$('upN').value=next;$('vUpN').textContent=next;
    buildFractal(true);
  });
  $('upSpread').addEventListener('input',function(){S.upSpread=parseInt(this.value,10)/10;$('vUpSpread').textContent=S.upSpread.toFixed(2)+'×';buildFractal(true);});
  $('polyEdges').addEventListener('change',function(){S.polyEdges=this.checked;buildFractal(true);});
  $('autoFill').addEventListener('change',function(){S.autoFill=this.checked;if($('fillKRow'))$('fillKRow').style.display=S.autoFill?'block':'none';buildFractal(true);});
  $('fillK').addEventListener('input',function(){S.fillK=parseInt(this.value,10)/100;$('vFillK').textContent=S.fillK.toFixed(2)+'×';buildFractal(true);});
  $('hexBase').addEventListener('change',function(){S.hexBase=this.checked;if($('hexBaseOpts'))$('hexBaseOpts').style.display=S.hexBase?'block':'none';buildFractal(true);});
  $('hexThick').addEventListener('input',function(){S.hexThick=parseInt(this.value,10);$('vHexThick').textContent=S.hexThick+' mm';buildFractal(true);});
  $('hexOverlap').addEventListener('input',function(){S.hexOverlap=parseInt(this.value,10)/100;$('vHexOverlap').textContent=S.hexOverlap.toFixed(2);buildFractal(true);});
  $('upBuds').addEventListener('input',function(){S.upBuds=parseInt(this.value,10);$('vUpBuds').textContent=S.upBuds;buildFractal(true);});
  $('upTilt').addEventListener('input',function(){S.upTilt=parseInt(this.value,10)/100;$('vUpTilt').textContent=S.upTilt.toFixed(2);buildFractal(true);});
  $('spiralMode').addEventListener('change',function(){applySpiralMode(this.value);buildFractal(true);});
  $('spiralDeg').addEventListener('input',function(){S.spiralDeg=parseInt(this.value,10);$('vSpiralDeg').textContent=S.spiralDeg+'°';buildFractal(true);});
  $('cmap').addEventListener('change',function(){S.cmap=this.value;syncAlgoUI();buildFractal(true);});
  $('fibArms').addEventListener('change',function(){S.fibArms=parseInt(this.value,10);$('vFibArms').textContent=S.fibArms;buildFractal(true);});
  $('fibTwist').addEventListener('input',function(){S.fibTwist=parseInt(this.value,10)/10;$('vFibTwist').textContent=S.fibTwist.toFixed(1);buildFractal(true);});
  $('speed').addEventListener('input',function(){S.speed=parseInt(this.value,10)/100;$('vSpeed').textContent=S.speed.toFixed(1)+'×';});
  $('palette').addEventListener('change',function(){S.pal=parseInt(this.value,10);$('vPalette').textContent=PALETTES[S.pal].name;buildFractal(true);});
  $('spin').addEventListener('change',function(){S.spin=this.checked;});
  $('showSpiral').addEventListener('change',function(){S.spiral=this.checked;buildFractal(true);});
  $('wireframe').addEventListener('change',function(){S.wire=this.checked;buildFractal(true);});
  $('prog').addEventListener('input',function(){
    S.prog=parseInt(this.value,10)/1000;S.playing=false;$('btnPlay').textContent='▶ 生长';
    $('vProg').textContent=Math.round(S.prog*100)+'%';updateInstances(S.prog);updateHUD();
  });
  $('btnPlay').addEventListener('click',function(){
    if(S.prog>=1)S.prog=0;S.playing=!S.playing;this.textContent=S.playing?'⏸ 暂停':'▶ 生长';
  });
  $('btnReset').addEventListener('click',function(){
    S.prog=0;S.playing=false;$('btnPlay').textContent='▶ 生长';$('prog').value=0;$('vProg').textContent='0%';
    updateInstances(0);updateHUD();   // 只重置生长进度，不动视角
  });
  $('btnStep').addEventListener('click',function(){
    var u=1/(S.levels+1);S.prog=clamp(Math.floor(S.prog/u+1e-4)*u+u*0.7,0,1);
    $('prog').value=Math.round(S.prog*1000);$('vProg').textContent=Math.round(S.prog*100)+'%';
    updateInstances(S.prog);updateHUD();
  });
  $('btnSeed').addEventListener('click',function(){S.seed=(Math.random()*1e9)|0;buildFractal(true);});

  /* ---- STL 导出 ---- */
  $('stlSeg').addEventListener('change',function(){S.stlSeg=parseInt(this.value,10);$('vStlSeg').textContent=this.value;});
  $('expFmt').addEventListener('change',function(){$('vFmt').textContent=this.options[this.selectedIndex].text.split(' ')[0];});
  $('btnTop').addEventListener('click',function(){cam.phi=0.12;cam.theta=0;cam.target.set(0,0,0);});
  $('btnSTL').addEventListener('click',function(){
    var t0=performance.now();
    var fmt=$('expFmt').value;
    try{
      var n=window.__exporters[fmt]();
      if(n<0){$('stlInfo').innerHTML='⚠ 已取消 STEP 导出（面数过多）';return;}
      $('stlInfo').innerHTML='✅ 已导出 <b>'+fmt.toUpperCase()+'</b> · <b>'+n+'</b> 三角面（mm，'+Math.round(performance.now()-t0)+'ms）';
    }catch(e){$('stlInfo').innerHTML='❌ 导出失败：'+e.message;}
  });

  /* ---- 右浮窗：收起 / 拖动 / 宽度可调；HUD 收起；让位跟随 --dw（SOUL F13/N199） ---- */
  var dock=$('dock'),head=$('dockHead'),rs=$('dockResize');
  $('dockToggle').addEventListener('click',function(){
    dock.classList.toggle('collapsed');
    this.textContent=dock.classList.contains('collapsed')?'+':'–';
  });
  $('hudToggle').addEventListener('click',function(){
    var h=$('hud');h.classList.toggle('collapsed');
    this.textContent=h.classList.contains('collapsed')?'▸':'▾';
  });
  // 拖动浮窗（仅头部，且不在按钮上）
  var dg=false,dx0=0,dy0=0,sx0=0,sy0=0;
  head.addEventListener('mousedown',function(e){
    if(e.target.tagName==='BUTTON')return;
    dg=true;dx0=e.clientX;dy0=e.clientY;
    sx0=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--dock-x'))||0;
    sy0=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--dock-y'))||0;
  });
  window.addEventListener('mousemove',function(e){
    if(!dg)return;
    var nx=sx0+(e.clientX-dx0),ny=sy0+(e.clientY-dy0);
    document.documentElement.style.setProperty('--dock-x',nx+'px');
    document.documentElement.style.setProperty('--dock-y',ny+'px');
  });
  window.addEventListener('mouseup',function(){dg=false;});
  // 宽度调节
  var rg=false,rx0=0,w0=0;
  rs.addEventListener('mousedown',function(e){
    rg=true;rx0=e.clientX;
    w0=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--dw'))||340;
    e.stopPropagation();
  });
  window.addEventListener('mousemove',function(e){
    if(!rg)return;
    var w=clamp(w0-(e.clientX-rx0),230,Math.min(620,window.innerWidth*0.7));
    document.documentElement.style.setProperty('--dw',w+'px');
    resize();
  });
  window.addEventListener('mouseup',function(){rg=false;});
}

/* ============ 启动 ============ */
initScene();
setRanges(PRESETS.upright);   // 默认直立花盘（蜂窝满铺），S.prog=1 打开即长满
initUI();
buildFractal();
requestAnimationFrame(loop);
})();
