    // 单株罗马花椰菜：参数照抄默认 grow（老师认可的塔形），整体平移到蜂窝点、主锥零倾角。
    // S.upTilt=1 -> 标准锥面外扩花椰菜；S.upTilt=0 -> 全垂直创意(圣诞树)。
    function emit(host,px,py,pz,H,R,level,dirX,dirY,dirZ){
      if(nodeCount>MAX)return;
      var obj=new THREE.Object3D();
      obj.position.set(px,py,pz);
      if(dirY<0.9999){
        obj.quaternion.setFromUnitVectors(vY,new THREE.Vector3(dirX,dirY,dirZ).normalize());
      }
      host.add(obj);nodeCount++;
      var isLeaf=(level>=lv);
      if(isLeaf) leafData.push({obj:obj,h:H,r:R,t:(level-1)/Math.max(1,lv-1),level:level});
      if(isLeaf)return;
      var beta=Math.atan(R/H),sinB=Math.sin(beta),cosB=Math.cos(beta);
      for(var i=0;i<buds&&nodeCount<MAX;i++){
        var t=0.12+0.80*(i+0.5)/buds;        // 高度范围照抄 grow
        var th=i*alpha+(level-1)*0.31;        // 黄金角螺旋
        var sr=R*(1-t)*0.72;                  // 贴面半径照抄 grow
        var lx=Math.cos(th)*sr,lz=Math.sin(th)*sr,ly=H*t;
        // 标准花椰菜：子锥轴沿母线外扩 tilt=sinB*0.55；圣诞树：全垂直
        var k=S.upTilt;
        var ax=Math.cos(th)*sinB*0.55*k, ay=cosB+(1-k)*sinB*0.45, az=Math.sin(th)*sinB*0.55*k;
        var cH=H*S.i2o*(1-0.45*t);            // 子锥缩放照抄 grow
        var cR=cH*S.r2l;
        emit(obj,lx,ly,lz,cH,cR,level+1,ax,ay,az);
      }
    }
