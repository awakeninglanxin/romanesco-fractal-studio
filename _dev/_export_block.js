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
    var id=10;
    function nid(){return '#'+(id++);}
    var faceIds=[];
    L.push(nid()+'=SHAPE_REPRESENTATION(\'romanesco\',(),'+'#8);');
    L.push('#8=AXIS2_PLACEMENT_3D(\'\',#9,#10,#11);');
    L.push('#9=CARTESIAN_POINT(\'\',(0.,0.,0.));');
    L.push('#10=DIRECTION(\'\',(0.,0.,1.));');
    L.push('#11=DIRECTION(\'\',(1.,0.,0.));');
    // 每个三角面：3 点 -> 3 向量 -> 3 顶点 -> 3 边 -> 边环 -> 面边界 -> 平面 -> 面
    tris.forEach(function(t){
      var pids=[],vids=[],edges=[];
      for(var i=0;i<3;i++){
        var pid=nid();pids.push(pid);
        L.push(pid+"=CARTESIAN_POINT('',("+t[i*3].toFixed(4)+','+t[i*3+1].toFixed(4)+','+t[i*3+2].toFixed(4)+'));');
      }
      var dirid=nid();L.push(dirid+"=DIRECTION('',(0.,0.,1.));");
      var plid=nid();L.push(plid+'=PLANE(\'\','+nid()+'=AXIS2_PLACEMENT_3D(\'\','+pids[0]+','+dirid+','+nid()+'=DIRECTION(\'\',(1.,0.,0.))));');
      for(var i2=0;i2<3;i2++){
        var vid2=nid();vids.push(vid2);
        L.push(vid2+'=VERTEX_POINT(\'\','+pids[i2]+');');
      }
      for(var j=0;j<3;j++){
        var eid=nid();edges.push(eid);
        L.push(eid+'=EDGE_CURVE(\'\','+vids[j]+','+vids[(j+1)%3]+','+nid()+'=LINE(\'\','+pids[j]+','+nid()+'=VECTOR(\'\','+pids[(j+1)%3]+','+pids[j]+',1.)) ,.T.);');
      }
      var loop=nid();L.push(loop+'=EDGE_LOOP(\'\',('+edges.join(',')+'));');
      var bound=nid();L.push(bound+'=FACE_OUTER_BOUND(\'\','+loop+',.T.);');
      var fid=nid();L.push(fid+'=ADVANCED_FACE(\'\',('+bound+'),'+plid+',.T.);');
      faceIds.push(fid);
    });
    var shell=nid();L.push(shell+'=CLOSED_SHELL(\'\',('+faceIds.join(',')+'));');
    var solid=nid();L.push(solid+'=MANIFOLD_SOLID_BREP(\'romanesco\','+shell+');');
    L.push(nid()+'=ADVANCED_BREP_SHAPE_REPRESENTATION(\'\',('+solid+','+'#8));');
    L.push('ENDSEC;');L.push('END-ISO-10303-21;');
    download(new Blob([L.join('\n')],{type:'application/step'}),baseName()+'.step');
    return tris.length;
  }

  window.__exporters={stl:exportSTL,obj:exportOBJ,ply:exportPLY,step:exportSTEP,stp:exportSTEP};
