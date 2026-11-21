    // Broccoli 递归：主锥垂直平放(骨架不渲染)，末级小锥簇组成花椰菜。
    // 子锥沿母锥母线黄金角螺旋外扩(自然罗马花椰菜)；S.upTilt=0 时全垂直(圣诞树)。
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
        var t=0.28+0.60*(i+0.5)/buds;        // 沿锥面高度取样
        var th=i*alpha+(level-1)*0.37;        // 黄金角螺旋
        var sr=R*(1-t)*0.80;
        var lx=Math.cos(th)*sr,lz=Math.sin(th)*sr,ly=H*t;
        var ax=Math.cos(th)*sinB*S.upTilt, ay=cosB+(1-S.upTilt), az=Math.sin(th)*sinB*S.upTilt;
        var cH=H*S.i2o*(1-0.35*t);            // 子锥缩放（内/外比，不再额外放大）
        var cR=cH*S.r2l;
        emit(obj,lx,ly,lz,cH,cR,level+1,ax,ay,az);
      }
    }
