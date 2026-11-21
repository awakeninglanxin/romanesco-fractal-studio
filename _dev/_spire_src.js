  /* ===== 忠实近似 Broccoli Equation：锥面对数螺旋密铺 + 芽朝外放射 + IFS 递归 ===== */
  function buildUpright(parent){
    var need=Math.max(1,Math.round(S.upN||7));
    var lv=Math.max(1,Math.round(S.levels));
    var buds=Math.max(8,Math.round(S.upBuds||60));     // 每层芽数≈对数螺旋采样点(源头200π的近似)
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
      // 本级圆锥本体（渲染），底面 y=0 尖朝 +Y
      var self=new THREE.Object3D();host.add(self);nodeCount++;
      leafData.push({obj:self,h:H,r:R,t:(level)/Math.max(1,lv-1),level:level+1});
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
        // R：芽朝外放射——轴沿径向水平分量大、竖直分量小（松塔鳞片状）
        var spread=Math.PI*0.36*(1-t*0.45);             // 靠底更水平、靠顶更竖
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
