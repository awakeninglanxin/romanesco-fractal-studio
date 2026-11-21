  /* ===== 直立花盘：六边形蜂窝(生命之花,允许缝隙) + 每锥用 Broccoli 锥面螺旋递归建多级 ===== */
  function buildUpright(parent){
    var need=Math.max(1,Math.round(S.upN||37));
    var H0=S.altitude;
    var alpha=S.angleDeg*Math.PI/180;
    var baseR=H0*S.r2l*0.40;              // 单元主锥底半径
    var d=2*baseR*(S.upSpread||1.3);      // 蜂窝中心间距，>2R 即留缝隙（老师允许）
    var lv=Math.max(1,Math.round(S.levels));
    var buds=Math.max(2,Math.round(S.upBuds||5));

    // 六边形同心环蜂窝坐标：中心1 + 第k环6k 个
    var pts=[{x:0,z:0}];
    for(var k=1;pts.length<need;k++){
      var rad=k*d,corner=[];
      for(var c=0;c<6;c++){var ca=Math.PI/3*c;corner.push({x:rad*Math.cos(ca),z:rad*Math.sin(ca)});}
      for(var e=0;e<6;e++){
        var p0=corner[e],p1=corner[(e+1)%6];
        for(var j=0;j<k;j++){
          var f=j/k;
          pts.push({x:p0.x+(p1.x-p0.x)*f,z:p0.z+(p1.z-p0.z)*f});
          if(pts.length>=need)break;
        }
        if(pts.length>=need)break;
      }
    }
    pts=pts.slice(0,need);

    // Broccoli 递归：在当前锥的锥面上按黄金角螺旋摆子锥，子锥再递归。
    // 主锥零倾角垂直平放；子锥倾角由 S.upTilt 控制（0=全部垂直）。
    function emit(host,px,py,pz,H,R,level,tiltX,tiltZ){
      if(nodeCount>MAX)return;
      var obj=new THREE.Object3D();
      obj.position.set(px,py,pz);
      if(tiltX||tiltZ){
        obj.quaternion.setFromUnitVectors(vY,new THREE.Vector3(tiltX,1,tiltZ).normalize());
      }
      host.add(obj);nodeCount++;
      leafData.push({obj:obj,h:H,r:R,t:(level-1)/Math.max(1,lv-1),level:level});
      if(level>=lv)return;
      var beta=Math.atan(R/H),sinB=Math.sin(beta);
      for(var i=0;i<buds&&nodeCount<MAX;i++){
        var t=0.20+0.64*(i+0.5)/buds;         // 沿母锥母线的高度参数
        var th=i*alpha+(level-1)*0.37;        // 黄金角螺旋 + 逐级相位错开
        var sr=R*(1-t)*0.78;                   // 贴锥面半径
        var lx=Math.cos(th)*sr,lz=Math.sin(th)*sr,ly=H*t;
        var tx=Math.cos(th)*sinB*S.upTilt,tz=Math.sin(th)*sinB*S.upTilt;
        var cH=H*(1-0.55*t)*S.i2o*1.7;        // 子锥高（缩放递推）
        var cR=cH*S.r2l;
        emit(obj,lx,ly,lz,cH,cR,level+1,tx,tz);
      }
    }
    for(var pi=0;pi<pts.length;pi++){
      emit(parent,pts[pi].x,0,pts[pi].z,H0,baseR,1,0,0);  // 每个蜂窝点：垂直主锥、底面贴平台
    }
  }
