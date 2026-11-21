  /* ===== 直立花盘：六边形蜂窝(生命之花,留缝) + 每单元一株标准罗马花椰菜(照抄grow) ===== */
  function buildUpright(parent){
    var need=Math.max(1,Math.round(S.upN||7));
    var alpha=S.angleDeg*Math.PI/180;
    var buds=Math.max(2,Math.round(S.upBuds||5));
    var lv=Math.max(1,Math.round(S.levels));
    var unitR=H0*S.r2l*0.44;                 // 单株底面半径（装进蜂窝单元）
    var d=2*unitR*(S.upSpread||1.8);         // 蜂窝间距，>2R 留缝
    var scale=unitR/(H0*S.r2l);              // 单株整体缩放

    // 六边形同心环蜂窝坐标：中心1 + 第k环6k
    var pts=[{x:0,z:0}];
    for(var k=1;pts.length<need;k++){
      var rad=k*d,corner=[];
      for(var c=0;c<6;c++){var ca=Math.PI/3*c;corner.push({x:rad*Math.cos(ca),z:rad*Math.sin(ca)});}
      for(var e=0;e<6;e++){
        var p0=corner[e],p1=corner[(e+1)%6];
        for(var j=0;j<k;j++){
          var f=j/k;pts.push({x:p0.x+(p1.x-p0.x)*f,z:p0.z+(p1.z-p0.z)*f});
          if(pts.length>=need)break;
        }
        if(pts.length>=need)break;
      }
    }
    pts=pts.slice(0,need);

    // 完全照抄 grow 的塔形递归：中央 core 递归成塔芯 + 子锥黄金角螺旋；末级锥渲染
    function spire(host,H,R,level,rotY){
      if(nodeCount>MAX)return;
      var k=S.upTilt;
      var beta=Math.atan(R/H),sinB=Math.sin(beta),cosB=Math.cos(beta);
      // 塔芯：同轴递归（不渲染），保证正塔形下宽上尖
      if(level+1<lv){
        var core=new THREE.Object3D();core.position.set(0,0,0);host.add(core);nodeCount++;
        spire(core,H,R,level+1,rotY);
      }
      if(level>=lv)return;
      for(var i=0;i<buds&&nodeCount<MAX;i++){
        var t=0.12+0.80*(i+0.5)/buds;
        var theta=i*alpha+rotY;
        var surfR=R*(1-t)*0.72;
        var px=Math.cos(theta)*surfR,pz=Math.sin(theta)*surfR,py=H*t;
        var tilt=sinB*0.55*k;
        var axis=new THREE.Vector3(Math.cos(theta)*tilt, cosB+(1-k)*(1-cosB), Math.sin(theta)*tilt).normalize();
        var ch=new THREE.Object3D();
        ch.position.set(px,py,pz);
        ch.quaternion.setFromUnitVectors(vY,axis);
        host.add(ch);nodeCount++;
        var cH=H*S.i2o*(1-0.45*t),cR=cH*S.r2l;
        if(level+1>=lv){
          leafData.push({obj:ch,h:cH,r:cR,t:t,level:level+1});
        }else{
          spire(ch,cH,cR,level+1,theta);
        }
      }
    }
    for(var pi=0;pi<pts.length;pi++){
      // 株根：平移到蜂窝点 + 整体缩放；所有子锥相对它构建，matrixWorld 自动带变换
      var rootPl=new THREE.Object3D();
      rootPl.position.set(pts[pi].x,0,pts[pi].z);
      rootPl.scale.setScalar(scale);
      parent.add(rootPl);
      spire(rootPl,H0,H0*S.r2l,0,0);
    }
  }
