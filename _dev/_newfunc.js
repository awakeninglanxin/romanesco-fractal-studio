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
  var MAX=60000;
  var rootObj=new THREE.Object3D();
  var nodeCount=0,leafData=[];

  // 单位锥：底 y=0、尖 y=1、底半径 1（尖朝 +Y）
  var geo=new THREE.ConeGeometry(1,1,10,1,false);
  geo.translate(0,0.5,0);

  var vY=new THREE.Vector3(0,1,0);
  function grow(parent,H,R,level,maxLevel){
    if(level>=maxLevel||nodeCount>MAX)return;
    var n=S.cones;
    var beta=Math.atan(R/H); // 母线倾角
    var sinB=Math.sin(beta),cosB=Math.cos(beta);
    for(var i=0;i<n;i++){
      if(nodeCount>MAX)break;
      var t=0.10+0.84*(i+0.5)/n;          // 高度参数（避开尖端/底面）
      var theta=i*alpha;
      var radial=new THREE.Vector3(Math.cos(theta),0,Math.sin(theta));
      var surfR=R*(1-t)*0.80;              // 贴面半径
      var pos=new THREE.Vector3(radial.x*surfR,H*t,radial.z*surfR);
      // 子锥轴：沿母锥母线向外上方
      var axis=new THREE.Vector3(radial.x*sinB,cosB,radial.z*sinB).normalize();
      var q=new THREE.Quaternion().setFromUnitVectors(vY,axis);

      var child=new THREE.Object3D();
      child.position.copy(pos);
      child.quaternion.copy(q);
      parent.add(child);
      nodeCount++;

      var childH=H*S.i2o*(1-0.55*t);
      var childR=childH*S.r2l;
      if(level+1>=maxLevel){
        child.updateMatrixWorld(true);
        leafData.push({m:child.matrixWorld.clone(),h:childH,r:childR,t:t,level:level+1});
      }else{
        grow(child,childH,childR,level+1,maxLevel);
      }
    }
  }
  grow(rootObj,H0,H0*S.r2l,0,S.levels);
  rootObj.updateMatrixWorld(true);
  if(!leafData.length)return;

  var maxH=Math.max.apply(null,leafData.map(function(d){return d.h;}));
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

  var mat=new THREE.MeshStandardMaterial({roughness:0.82,metalness:0.02,side:THREE.DoubleSide,wireframe:S.wire});
  leafMesh=new THREE.InstancedMesh(geo,mat,S.leaves.length);
  leafMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  root.add(leafMesh);

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

  var maxR=0;
  S.leaves.forEach(function(l){var p=new THREE.Vector3().setFromMatrixPosition(l.m);var d=p.length()+l.h;if(d>maxR)maxR=d;});
  cam.radius=clamp(maxR*2.0,6,70);
  cam.target.set(0,H0*0.45,0);
  updateInstances(S.prog);
  updateHUD();
}
