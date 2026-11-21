
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
var FIB = [1,1,2,3,5,8,13,21,34,55,89];

var PRESETS = {
  romanesco:   {levels:3, angle:137.508, cones:11, r2l:0.95, i2o:0.43, pal:0, form:'fractal'},
  cauliflower: {levels:3, angle:137.508, cones:14, r2l:1.18, i2o:0.60, pal:2, form:'fractal'},
  broccoli:    {levels:3, angle:137.508, cones:7,  r2l:0.68, i2o:0.38, pal:1, form:'fractal'},
  // 直立花盘：锥轴垂直、底面平放平台、锥数少（黄金角平铺的莲蓬/生命之花）
  upright:     {levels:3, angle:137.508, cones:7, r2l:0.95, i2o:0.46, pal:4, form:'upright', upTilt:1.0, upBuds:24},
  xmas:        {levels:5, angle:137.508, cones:7, r2l:0.95, i2o:0.46, pal:4, form:'upright', upTilt:0.0, upBuds:6}
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
var S={levels:3,angleDeg:137.508,cones:11,r2l:0.95,i2o:0.43,pal:0,form:'fractal',
       /* 直立花盘（蜂窝·垂直平放·Broccoli多级）参数 */
       upN:7, upSpread:1.8, upTilt:1.0, upBuds:24,   // 蜂窝单元数 / 间距系数(>2留缝) / 子锥倾角(0=垂直) / 每级芽数
       spin:true,spiral:false,wire:false,speed:1,prog:0,playing:false,seed:12345,
       leaves:[],visible:0,altitude:6,
       /* 第0级蜂窝面板 */
       honey:false, boardL:250, boardW:180, boardT:5, brocSize:28,   // mm
       stlSeg:5, cells:[], renderList:[], plateMesh:null};

/* ============ three 场景 ============ */
var stage=$('stage'),cv=$('cv');
var renderer,scene,camera,root,leafMesh,spiralLine,ctrl;
var cam={theta:0.55,phi:0.92,radius:14,target:new THREE.Vector3(0,0,0)};

function initScene(){
  renderer=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:true});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
  renderer.setClearColor(0xffffff,0);
  scene=new THREE.Scene();
  camera=new THREE.PerspectiveCamera(42,1,0.1,1000);
  root=new THREE.Group();
  scene.add(root);
  scene.add(new THREE.AmbientLight(0xffffff,0.80));
  var d1=new THREE.DirectionalLight(0xffffff,0.78); d1.position.set(6,12,8); scene.add(d1);
  var d2=new THREE.DirectionalLight(0xc8ecd6,0.38); d2.position.set(-8,4,-6); scene.add(d2);
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

function buildFractal(){
  while(root.children.length){
    var o=root.children[0];root.remove(o);
    if(o.geometry)o.geometry.dispose();
    if(o.material){if(o.material.length)o.material.forEach(function(m){m.dispose();});else o.material.dispose();}
  }
  S.leaves=[];

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
  function buildUpright(parent){
    var need=Math.max(1,Math.round(S.upN||7));
    var lv=Math.max(1,Math.round(S.levels));
    var buds=Math.max(8,Math.round(S.upBuds||24));     // 每层芽数≈对数螺旋采样点(源头200π的近似)
    var alpha=S.angleDeg*Math.PI/180;                  // 黄金角(螺旋相位)
    var unitR=H0*S.r2l*0.44;
    var d=2*unitR*(S.upSpread||1.8);
    var scale=unitR/(H0*S.r2l);

    // 六边形蜂窝坐标
    var pts=[{x:0,z:0}];
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

    // IFS 递归的芽：圆锥本体 + 锥面螺旋上的子芽
    function broccoli(host,H,R,level){
      if(nodeCount>MAX)return;
      // 本级圆锥本体：level 0 主锥是被覆盖的塔底，不渲染（避免露出大底面）
      if(level>0){
        var self=new THREE.Object3D();host.add(self);nodeCount++;
        leafData.push({obj:self,h:H,r:R,t:(level)/Math.max(1,lv-1),level:level+1});
      }
      if(level>=lv-1)return;                            // 末级只画本体
      // 沿锥面对数螺旋铺芽：θ=i·黄金角；t 由底(0)到顶(1)，芽随高度指数缩小
      for(var i=0;i<buds&&nodeCount<MAX;i++){
        var u=i/(buds-1);                               // 0..1
        var theta=i*alpha;                              // 黄金角相位→均匀螺旋
        var t=0.08+0.86*u;                              // 锥面高度位置
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
        host.add(bud);nodeCount++;
        broccoli(bud,bH,bR,level+1);
      }
    }
    for(var pi=0;pi<pts.length;pi++){
      var rootPl=new THREE.Object3D();
      rootPl.position.set(pts[pi].x,0,pts[pi].z);
      rootPl.scale.setScalar(scale);
      parent.add(rootPl);
      broccoli(rootPl,H0,H0*S.r2l,0);
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
  if(S.form==='upright') buildUpright(rootObj);
  else grow(rootObj,H0,H0*S.r2l,0,S.levels);
  rootObj.updateMatrixWorld(true);   // 整棵树构建完再统一刷新世界矩阵
  if(!leafData.length)return;
  // 此时才能安全读取每个叶锥的最终世界矩阵
  leafData.forEach(function(d){ d.m=d.obj.matrixWorld.clone(); delete d.obj; });

  var maxH=0;for(var mi=0;mi<leafData.length;mi++){if(leafData[mi].h>maxH)maxH=leafData[mi].h;}  // 避免大数组 apply 爆栈
  var maxLevel=S.levels;
  leafData.forEach(function(d){
    var f=clamp(d.h/maxH,0,1);
    var h=lerp(pal.hue[0],pal.hue[1],1-f)+(rnd()-0.5)*0.010;
    var sat=lerp(pal.sat[0],pal.sat[1],1-f);
    var li=lerp(pal.light[0],pal.light[1],1-f);
    d.color=new THREE.Color().setHSL(clamp(h,0,1),sat,li);
    d.birth=clamp(0.06+0.62*(d.level/maxLevel)*0.55+0.62*d.t*0.45+(rnd()-0.5)*0.03,0,0.9);
  });
  // 按出生时间排序，长的有序
  leafData.sort(function(a,b){return a.birth-b.birth;});
  S.leaves=leafData;
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

  /* ---------- 构建"最终渲染实例列表"：单株 or 蜂窝复制 ---------- */
  function buildRenderList(){
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
    // 相机
    var size=new THREE.Vector3().subVectors(boxMax,boxMin);
    var c=boxMin.clone().addScaledVector(size,0.5);
    cam.target.copy(c);
    cam.radius=clamp(Math.max(size.x,size.y,size.z)*1.55,6,120);
    cam.phi=S.honey?0.62:0.92;   // 蜂窝模式偏俯视，看"生命之花"
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
    expGeo.dispose();
    return tris;
  }
  function baseName(){
    return 'romanesco_'+(S.honey?('honey_'+S.cells.length+'cells'):'single')+'_'+S.levels+'L';
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


  buildHoneycombCells();
  buildRenderList();
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
  var extra=S.honey?('<br>蜂窝单元 <b>'+S.cells.length+'</b> 个 ｜ 板 '+S.boardL+'×'+S.boardW+'×'+S.boardT+'mm'):'';
  $('hudBody').innerHTML='锥体总数 <b>'+n+'</b> ｜ 已长出 <b>'+v+'</b><br>'+
    '自相似层数 <b>'+S.levels+'</b> ｜ 发散角 <b>'+a.toFixed(3)+'°</b><br>'+
    '可见螺旋列 <b>'+f1+' / '+f2+'</b>（相邻 Fibonacci）'+extra;
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
  $('r2l').value=Math.round(p.r2l*100);$('vR2L').textContent=p.r2l.toFixed(2);
  $('i2o').value=Math.round(p.i2o*100);$('vI2O').textContent=p.i2o.toFixed(2);
  $('palette').value=p.pal;$('vPalette').textContent=PALETTES[p.pal].name;
  S.levels=p.levels;S.angleDeg=p.angle;S.cones=p.cones;S.r2l=p.r2l;S.i2o=p.i2o;S.pal=p.pal;
  S.form=p.form||'fractal';
  if(S.form==='upright'){
    S.upN=p.cones; if($('upN')){$('upN').value=p.cones;$('vUpN').textContent=p.cones;}
    S.upBuds=p.upBuds!=null?p.upBuds:24;
    S.upTilt=p.upTilt!=null?p.upTilt:1.0;
    S.upSpread=1.8;
    if($('upBuds')){$('upBuds').value=S.upBuds;$('vUpBuds').textContent=S.upBuds;}
    if($('upTilt')){$('upTilt').value=Math.round(S.upTilt*100);$('vUpTilt').textContent=S.upTilt.toFixed(2);}
    if($('upSpread')){$('upSpread').value=18;$('vUpSpread').textContent='1.80×';}
  }
  // 直立花盘专用参数区显隐
  if($('upSec'))$('upSec').style.display=(S.form==='upright')?'block':'none';
}
function initUI(){
  $('preset').addEventListener('change',function(){
    var p=PRESETS[this.value];setRanges(p);S.prog=0;S.playing=false;
    $('btnPlay').textContent='▶ 生长';$('prog').value=0;$('vProg').textContent='0%';
    buildFractal();
  });
  function rb(id,key,fmt,after){
    $(id).addEventListener('input',function(){
      var v=parseFloat(this.value);S[key]=v;$(fmt.id).textContent=fmt.fn(v);
      if(after)after(v);buildFractal();
    });
  }
  rb('levels','levels',{id:'vLevels',fn:function(v){return v;}});
  rb('angle','angleDeg',{id:'vAngle',fn:function(v){return v.toFixed(3)+'°';}});
  rb('cones','cones',{id:'vCones',fn:function(v){return v;}});
  $('r2l').addEventListener('input',function(){S.r2l=parseInt(this.value,10)/100;$('vR2L').textContent=S.r2l.toFixed(2);buildFractal();});
  $('i2o').addEventListener('input',function(){S.i2o=parseInt(this.value,10)/100;$('vI2O').textContent=S.i2o.toFixed(2);buildFractal();});
  $('upN').addEventListener('input',function(){S.upN=parseInt(this.value,10);$('vUpN').textContent=S.upN;buildFractal();});
  $('upSpread').addEventListener('input',function(){S.upSpread=parseInt(this.value,10)/10;$('vUpSpread').textContent=S.upSpread.toFixed(2)+'×';buildFractal();});
  $('upBuds').addEventListener('input',function(){S.upBuds=parseInt(this.value,10);$('vUpBuds').textContent=S.upBuds;buildFractal();});
  $('upTilt').addEventListener('input',function(){S.upTilt=parseInt(this.value,10)/100;$('vUpTilt').textContent=S.upTilt.toFixed(2);buildFractal();});
  $('speed').addEventListener('input',function(){S.speed=parseInt(this.value,10)/100;$('vSpeed').textContent=S.speed.toFixed(1)+'×';});
  $('palette').addEventListener('change',function(){S.pal=parseInt(this.value,10);$('vPalette').textContent=PALETTES[S.pal].name;buildFractal();});
  $('spin').addEventListener('change',function(){S.spin=this.checked;});
  $('showSpiral').addEventListener('change',function(){S.spiral=this.checked;buildFractal();});
  $('wireframe').addEventListener('change',function(){S.wire=this.checked;buildFractal();});
  $('prog').addEventListener('input',function(){
    S.prog=parseInt(this.value,10)/1000;S.playing=false;$('btnPlay').textContent='▶ 生长';
    $('vProg').textContent=Math.round(S.prog*100)+'%';updateInstances(S.prog);updateHUD();
  });
  $('btnPlay').addEventListener('click',function(){
    if(S.prog>=1)S.prog=0;S.playing=!S.playing;this.textContent=S.playing?'⏸ 暂停':'▶ 生长';
  });
  $('btnReset').addEventListener('click',function(){
    S.prog=0;S.playing=false;$('btnPlay').textContent='▶ 生长';$('prog').value=0;$('vProg').textContent='0%';
    cam.theta=0.55;cam.phi=0.92;cam.target.set(0,0,0);updateInstances(0);updateHUD();
  });
  $('btnStep').addEventListener('click',function(){
    var u=1/(S.levels+1);S.prog=clamp(Math.floor(S.prog/u+1e-4)*u+u*0.7,0,1);
    $('prog').value=Math.round(S.prog*1000);$('vProg').textContent=Math.round(S.prog*100)+'%';
    updateInstances(S.prog);updateHUD();
  });
  $('btnSeed').addEventListener('click',function(){S.seed=(Math.random()*1e9)|0;buildFractal();});

  /* ---- 第0级蜂窝面板 + STL 导出 ---- */
  $('honey').addEventListener('change',function(){
    S.honey=this.checked;
    if(S.honey){ // 老师要求：蜂窝下每个西兰花默认 4 级分形；芽数降到可控预算
      S.levels=4;$('levels').value=4;$('vLevels').textContent='4';
      S.cones=5;$('cones').value=5;$('vCones').textContent='5';
    }else{ // 退回单株恢复默认值
      S.cones=11;$('cones').value=11;$('vCones').textContent='11';
      S.levels=3;$('levels').value=3;$('vLevels').textContent='3';
    }
    buildFractal();
  });
  $('hLevel').addEventListener('input',function(){
    var v=parseInt(this.value,10);$('vHLevel').textContent=v;
    S.levels=v;$('levels').value=v;$('vLevels').textContent=v;buildFractal();
  });
  $('broc').addEventListener('input',function(){S.brocSize=parseInt(this.value,10);$('vBroc').textContent=S.brocSize+' mm';buildFractal();});
  $('bL').addEventListener('input',function(){S.boardL=parseInt(this.value,10);$('vBL').textContent=S.boardL+' mm';buildFractal();});
  $('bW').addEventListener('input',function(){S.boardW=parseInt(this.value,10);$('vBW').textContent=S.boardW+' mm';buildFractal();});
  $('bT').addEventListener('input',function(){S.boardT=parseFloat(this.value);$('vBT').textContent=S.boardT+' mm';buildFractal();});
  $('stlSeg').addEventListener('change',function(){S.stlSeg=parseInt(this.value,10);$('vStlSeg').textContent=this.value;});
  $('expFmt').addEventListener('change',function(){$('vFmt').textContent=this.options[this.selectedIndex].text.split(' ')[0];});
  $('btnTop').addEventListener('click',function(){cam.phi=0.12;cam.theta=0;cam.target.set(0,0,0);});
  $('btnSTL').addEventListener('click',function(){
    var t0=performance.now();
    var fmt=$('expFmt').value;
    try{
      var n=window.__exporters[fmt]();
      if(n<0){$('stlInfo').innerHTML='⚠ 已取消 STEP 导出（面数过多）';return;}
      $('stlInfo').innerHTML='✅ 已导出 <b>'+fmt.toUpperCase()+'</b> · <b>'+n+'</b> 三角面（'+(S.honey?S.cells.length+' 单元 · ':'')+'mm，'+Math.round(performance.now()-t0)+'ms）';
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
setRanges(PRESETS.romanesco);
initUI();
buildFractal();
requestAnimationFrame(loop);
})();
