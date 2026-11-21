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
      S.cells.forEach(function(cell,ci){
        var T=new THREE.Matrix4().makeTranslation(cell.x,lift,cell.z);
        var Sc=new THREE.Matrix4().makeScale(scale,scale,scale);
        var base=T.multiply(Sc);
        S.leaves.forEach(function(l){
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

  /* ---------- STL 导出（二进制）：锥体实例 + 底板，单位 mm ---------- */
  function exportSTL(){
    if(!S.renderList.length){alert('没有可导出的几何');return;}
    var tris=[]; // 每项 [ax,ay,az,bx,by,bz,cx,cy,cz] 场景单位
    var pos=leafMesh.geometry.getAttribute('position');
    var idx=leafMesh.geometry.index;
    var triCount=idx?idx.count/3:pos.count/3;
    var v=new THREE.Vector3();
    function addTri(mat,p1,p2,p3){
      v.fromBufferAttribute(pos,p1).applyMatrix4(mat);var a=v.clone();
      v.fromBufferAttribute(pos,p2).applyMatrix4(mat);var b=v.clone();
      v.fromBufferAttribute(pos,p3).applyMatrix4(mat);var cc=v.clone();
      // 场景单位 -> mm
      var k=1/MM;
      tris.push([a.x*k,a.y*k,a.z*k,b.x*k,b.y*k,b.z*k,cc.x*k,cc.y*k,cc.z*k]);
    }
    S.renderList.forEach(function(l){
      var g=clamp(S.prog,0,1);
      var s=(g<=l.birth)?0.0001:1;
      var M=l.m.clone().multiply(new THREE.Matrix4().makeScale(l.r*s,l.h*s,l.r*s));
      for(var t=0;t<triCount;t++){
        if(idx)addTri(M,idx.getX(t*3),idx.getX(t*3+1),idx.getX(t*3+2));
        else addTri(M,t*3,t*3+1,t*3+2);
      }
    });
    // 底板（6 面 = 12 三角）
    if(S.honey&&S.plateMesh){
      var pm=S.plateMesh;pm.updateMatrixWorld(true);
      var pg=pm.geometry,pp=pg.getAttribute('position'),pi=pg.index;
      var pt=pi?pi.count/3:pp.count/3;
      for(var t2=0;t2<pt;t2++){
        var a2=new THREE.Vector3().fromBufferAttribute(pp,pi?pi.getX(t2*3):t2*3).applyMatrix4(pm.matrixWorld);
        var b2=new THREE.Vector3().fromBufferAttribute(pp,pi?pi.getX(t2*3+1):t2*3+1).applyMatrix4(pm.matrixWorld);
        var c2=new THREE.Vector3().fromBufferAttribute(pp,pi?pi.getX(t2*3+2):t2*3+2).applyMatrix4(pm.matrixWorld);
        var kk=1/MM;
        tris.push([a2.x*kk,a2.y*kk,a2.z*kk,b2.x*kk,b2.y*kk,b2.z*kk,c2.x*kk,c2.y*kk,c2.z*kk]);
      }
    }
    // 写二进制 STL
    var buf=new ArrayBuffer(84+tris.length*50);
    var dv=new DataView(buf);
    var enc=function(off,str){for(var i=0;i<str.length&&i<79;i++)dv.setUint8(off+i,str.charCodeAt(i));};
    enc(0,'Romanesco fractal '+S.levels'L '+S.cells.length+'cells unit=mm');
    dv.setUint32(80,tris.length,true);
    var o=84;
    tris.forEach(function(t){
      // 法向 = 叉积归一
      var ux=t[3]-t[0],uy=t[4]-t[1],uz=t[5]-t[2];
      var vx=t[6]-t[0],vy=t[7]-t[1],vz=t[8]-t[2];
      var nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
      var nl=Math.sqrt(nx*nx+ny*ny+nz*nz)||1;
      dv.setFloat32(o,nx/nl,true);dv.setFloat32(o+4,ny/nl,true);dv.setFloat32(o+8,nz/nl,true);o+=12;
      for(var i=0;i<9;i++){dv.setFloat32(o,t[i],true);o+=4;}
      dv.setUint16(o,0,true);o+=2;
    });
    var blob=new Blob([buf],{type:'model/stl'});
    var a=document.createElement('a');a.href=URL.createObjectURL(blob);
    a.download='romanesco_'+(S.honey?('honey_'+S.cells.length+'cells'):'single')+'_'+S.levels+'L.stl';
    a.click();setTimeout(function(){URL.revokeObjectURL(a.href);},2000);
    return tris.length;
  }

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
