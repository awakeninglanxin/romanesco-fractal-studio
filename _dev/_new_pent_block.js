/* ===== 正五边形 · IFS 五棱锥「花盘山」（混沌游戏 + 坡面法线布株）=====
   把文献里三件事揉进同一个几何体，而不是各画各的：
   ① 山（mountain）：五边形底 + 中心一个尖顶 → 正五棱锥，锥面就是"山坡"（高程场）；
   ② 五棱锥 IFS（pentaflake）：以 6 个吸引子（5 个底角 + 1 个尖顶）跑混沌游戏
      p ← s·p + (1−s)·V_k ，s = 1/(1+φ) ≈ 0.381966。点云自带五重自相似团簇，
      是"山体内部的分形尘埃"，正好当花盘的分布密度函数；
   ③ 树（tree）：每株花盘不再竖直摆放，而是**沿坡面法线**生长 —— 像山坡上长树，
      法线 n ∝ (cosθ·H, R, sinθ·H)（用圆锥面的光滑法线，避免棱面处跳变）。
   把点沿半径投影到"该高度处的坡面"上，于是点云被摊成一层贴合锥面的壳。
   ⚠️ 不做"中点位移"高度噪声：花盘底面必须落在坡面上，随机抬降会让底面悬空。

   ===== 2026-11-22 · 面内「无缝铺满」求解器（老师：一键调到最优、无缝铺满山包）=====
   旧版布点用 4 映射混沌游戏取点，为什么必然留灰块（根因，不是参数没调好）：
     · 混沌游戏的吸引子是"极限上"铺满三角形，有限个点一定成团、团间一定留洞
       （Poisson 撒点的孔洞概率 e^(−λπr²)，且空洞尺寸无上界）——加大 N 只把洞变小，不会消失；
     · 更根本的是单个花盘本身就有孔：花盘 = 1 中心锥 + 6 花瓣锥（底半径 b，环半径 2b 相切），
       7 个圆盘两两相切时，相邻花瓣在 30° 方向留 6 个凹口，最近处只到 0.42·rf
       —— 也就是"一个花盘自己就漏 6%"，任何摆法都补不上。
   两条修正（都是几何结论，不是玄学调参）：
     ① 花瓣环半径收到 petal·b（petal=1.70）：相邻圆盘重叠 ~15%，
        圆心三角形外接圆 1.70b/√3 = 0.98b < b → 并集自身无孔（实测 petal≤1.80 即可）；
     ② 三角格点间距 d = dr·rf（dr=1.44）：花盘轮廓是"带齿六边形"，
        相切平铺 d=√3·rf 时齿槽仍留 4~9%；dr=1.44 时真实并集覆盖率 100%。
   求解四步（pentCoverSolve）：
     ① 三角格点撒种（沿底边 / 转 30° 两种取向，取落在面内更多的）；
     ② 抖动 ≤0.12d（去掉"高尔夫球"式机械感，保留有机感）；
     ③ 覆盖率栅格（重心坐标采样）+ 距离场：逐点判"7 圆盘真实并集"是否盖住；
     ④ 自相似补缝：在最大空洞处补一株 0.42~0.90 倍的小花盘（romanesco 的尺度层级），
        迭代到栅格全覆盖 —— 大花盘之间嵌小花盘，正是罗马花椰菜的真实结构。
   ⚠️ 只解 1 个坡面，其余 4 个面用同一份 (u,v) 布局 → 严格五重对称（五角星）。 */
function pentCoverSolve(L1,Cx,Cy,opt){
  opt=opt||{};
  var petal=(opt.petal==null?1.70:opt.petal);    // 花瓣环半径（× 底盘锥半径 b），2.0=相切
  var dr=(opt.dr==null?1.44:opt.dr);             // 三角格点间距 / 花盘外接半径 rf
  var jitter=(opt.jitter==null?0.12:opt.jitter); // 抖动幅度（× d）
  var fillN=Math.max(0,Math.min(4,(opt.fill==null?2:opt.fill)));
  var spin=(opt.spin||0)*Math.PI/180;            // 花盘自转角（相对格点）
  var N=Math.max(4,Math.round(opt.n||30));
  var rnd=mulberry32(((opt.seed|0)||12345)+7727);
  var area=0.5*L1*Cy;
  var d=Math.sqrt(2*area/(Math.sqrt(3)*N));      // 面积/N 反解三角格点间距
  var rf=d/dr;                                   // 花盘外接半径（世界单位）
  var bb=rf/(petal+1);                           // 单个底盘锥底半径（世界单位）
  var P=[];
  function insideT(x,y){
    var wC=y/Cy; if(wC<-1e-9)return false;
    var wB=(x-wC*Cx)/L1;
    return (wB>=-1e-9)&&(1-wB-wC>=-1e-9);
  }
  /* ① 三角格点：两种取向择优 */
  var best=null,brot=0;
  [0,Math.PI/6].forEach(function(rot){
    var ax=Math.cos(rot),ay=Math.sin(rot),bx=Math.cos(rot+Math.PI/3),by=Math.sin(rot+Math.PI/3);
    var n=Math.ceil((L1+Cy)/d)+2,out=[];
    for(var i=-n;i<=n;i++){for(var j=-n;j<=n;j++){
      var x=i*d*ax+j*d*bx,y=i*d*ay+j*d*by;
      if(insideT(x,y))out.push([x,y]);
    }}
    if(!best||out.length>best.length){best=out;brot=rot;}
  });
  /* ② 抖动（抖出界就退回格点，保证花盘中心一定落在坡面上） */
  best.forEach(function(p){
    var x=p[0]+(rnd()*2-1)*jitter*d, y=p[1]+(rnd()*2-1)*jitter*d;
    if(!insideT(x,y)){x=p[0];y=p[1];}
    P.push({x:x,y:y,r:rf,s:brot+spin});
  });
  var baseN=P.length;
  if(baseN<3)return {pts:P,cover:0,base:baseN,added:0,rf:rf,d:d,nv:0,petal:petal,dr:dr,total:0};
  /* ③ 覆盖率栅格：重心坐标均匀采样（含边界），逐点测 7 圆盘真实并集 */
  var nv=Math.max(24,Math.min(110,Math.round(L1/(0.16*rf))));
  var rows=nv+1,total=rows*(rows+1)/2;
  var cxA=new Float32Array(total),cyA=new Float32Array(total);
  var t0=0;
  for(var si=0;si<rows;si++){for(var sj=0;sj<rows-si;sj++){
    var wB=si/nv,wC=sj/nv;
    cxA[t0]=wB*L1+wC*Cx; cyA[t0]=wC*Cy; t0++;
  }}
  var cellR=rf*1.06, hash={};
  function hkey(ix,iy){return ix*100003+iy;}
  function addHash(p){
    var ix=Math.floor(p.x/cellR),iy=Math.floor(p.y/cellR),k=hkey(ix,iy);
    (hash[k]||(hash[k]=[])).push(p);
  }
  function isCov(x,y){
    var ix=Math.floor(x/cellR),iy=Math.floor(y/cellR);
    for(var dx=-1;dx<=1;dx++){for(var dy=-1;dy<=1;dy++){
      var arr=hash[hkey(ix+dx,iy+dy)]; if(!arr)continue;
      for(var t=0;t<arr.length;t++){
        var q=arr[t],ex=x-q.x,ey=y-q.y;
        if(ex*ex+ey*ey>q.r*q.r)continue;          // 外接圆预筛
        var b2=q.r/(petal+1),b2s=b2*b2;
        if(ex*ex+ey*ey<=b2s)return true;          // 中心锥
        var ring=petal*b2;
        for(var s=0;s<6;s++){                     // 6 个花瓣锥
          var a=q.s+s*Math.PI/3;
          var gx=ex-ring*Math.cos(a),gy=ey-ring*Math.sin(a);
          if(gx*gx+gy*gy<=b2s)return true;
        }
      }
    }}
    return false;
  }
  P.forEach(addHash);
  function raster(){
    var c=0;
    for(var t=0;t<total;t++){if(isCov(cxA[t],cyA[t]))c++;}
    return c;
  }
  var covN=raster(), added=0;
  /* ④ 自相似补缝：BFS 距离场 → 最大空洞中心 → 补一株缩小的花盘 */
  var gstep=L1/nv, D=new Int32Array(rows*rows), Q=new Int32Array(rows*rows*2);
  function holeMax(){
    D.fill(-1);
    var qh=0,qt=0,bestD=0,bestId=-1;
    for(var i=0;i<rows;i++){for(var j=0;j<rows-i;j++){
      if(!isCov(cxA[i*rows-i*(i-1)/2+j],cyA[i*rows-i*(i-1)/2+j]))continue;
      D[i*rows+j]=0; Q[qt++]=i*rows+j;
    }}
    while(qh<qt){
      var id=Q[qh++],ci=(id/rows)|0,cj=id%rows,dv=D[id];
      for(var k=0;k<6;k++){
        var a=ci+[1,-1,0,0,1,-1][k], b=cj+[0,0,1,-1,-1,1][k];
        if(a<0||b<0||a+b>nv)continue;
        var nid=a*rows+b;
        if(D[nid]!==-1)continue;
        D[nid]=dv+1; Q[qt++]=nid;
        if(dv+1>bestD){bestD=dv+1;bestId=nid;}
      }
    }
    return [bestD,bestId];
  }
  for(var round=0;round<fillN;round++){
    if(covN>=total)break;
    var guard=0,cap=Math.ceil(N*0.9);
    while(guard++<cap){
      var hm=holeMax();
      if(hm[1]<0||hm[0]*gstep<0.09*rf)break;      // 只剩级缝，收工
      var ci=(hm[1]/rows)|0, cj=hm[1]%rows;
      var idx=ci*rows-ci*(ci-1)/2+cj;
      var rNew=Math.min(rf*0.92,Math.max(rf*0.40,hm[0]*gstep*1.55));
      var np={x:cxA[idx],y:cyA[idx],r:rNew,s:brot+spin,gen:round+2};
      P.push(np); addHash(np); added++;
      covN=raster();
      if(covN>=total)break;
    }
    if(added>N*1.6)break;
  }
  return {pts:P,cover:covN/total,base:baseN,added:added,rf:rf,d:d,nv:nv,
          petal:petal,dr:dr,total:total};
}

/* ===== 正五边形 · 五棱锥布株（五重对称 + 面内无缝铺满） ===== */
function buildPentagonPyramidPlacements(face,H0,r2l,edge,N){
  var R0=H0*r2l;
  var Rp=edge/(2*Math.sin(Math.PI/5));          // 五边形外接半径
  var Hp=Rp*0.62;                               // 山高（坡角约 32°）
  var petal=(S.ifsPetal==null?1.70:S.ifsPetal);
  var dr=(S.ifsDr==null?1.44:S.ifsDr);
  var fill=(S.ifsFill==null?2:S.ifsFill);
  var spinDeg=(S.ifsSpin==null?30:S.ifsSpin);
  var nPer=Math.max(4,Math.round((N||80)/5));
  /* 面基准三角形（等长可直接用长度算 2D 坐标）：A=底顶点，B=下一底顶点，C=尖顶 */
  var L1=edge, L2=Math.hypot(Rp,Hp), Cx=L1/2;
  var Cy=Math.sqrt(Math.max(1e-9,L2*L2-Cx*Cx));
  /* 缓存：拖动滑块会反复重建，同一组参数不重复求解（求解约 10~30ms） */
  var key=[L1.toFixed(4),L2.toFixed(4),nPer,petal,dr,fill,spinDeg,S.seed].join('|');
  if(!S._pentCover||S._pentCover.key!==key){
    S._pentCover={key:key,sol:pentCoverSolve(L1,Cx,Cy,{n:nPer,petal:petal,dr:dr,
                    fill:fill,spin:spinDeg,seed:S.seed})};
  }
  var sol=S._pentCover.sol, pts=sol.pts;
  /* 单株花盘在本地坐标的外接半径 = (petal+1)·bR，bR=R0/3 → 世界半径 rf 需缩放 sc */
  var sc=sol.rf/((petal+1)*R0/3);
  /* 五棱锥的 5 个底顶点 / 尖顶（face 局部坐标 → 世界） */
  function toW(x,y,z){
    return new THREE.Vector3().copy(face.center)
      .addScaledVector(face.u,x).addScaledVector(face.normal,y).addScaledVector(face.w,z);
  }
  var base=[],k;
  for(k=0;k<5;k++){
    var a=face.offset+2*Math.PI*k/5;
    base.push(toW(Math.cos(a)*Rp,0,Math.sin(a)*Rp));
  }
  var apex=toW(0,Hp,0);
  var out=[],gid=0,vY=new THREE.Vector3(0,1,0);
  var spinR=spinDeg*Math.PI/180, cs=Math.cos(spinR), sn=Math.sin(spinR);
  for(var f=0;f<5;f++){
    var Af=base[f], Bf=base[(f+1)%5];
    var e1=Bf.clone().sub(Af), e1L=e1.length()||1; e1.multiplyScalar(1/e1L);
    var tv=apex.clone().sub(Af), pr=tv.dot(e1);
    var e2=tv.clone().addScaledVector(e1,-pr);
    var e2L=e2.length()||1; e2.multiplyScalar(1/e2L);
    var nrm=new THREE.Vector3().crossVectors(e1,e2).normalize();   // 坡面法线
    var cen=Af.clone().add(Bf).add(apex).multiplyScalar(1/3);
    if(nrm.dot(cen.clone().addScaledVector(vY,-Hp*0.25))<0)nrm.multiplyScalar(-1);  // 朝外
    /* 花盘局部坐标：X=坡面底边方向（与 2D 求解的 u 轴一致）、Y=坡面法线、Z=X×Y */
    var zAx=new THREE.Vector3().crossVectors(e1,nrm).normalize();
    var xAx=e1.clone().multiplyScalar(cs).addScaledVector(zAx,sn);   // 绕法线自转 spinR
    var zAx2=zAx.clone().multiplyScalar(cs).addScaledVector(e1,-sn);
    var M0=new THREE.Matrix4().makeBasis(xAx,nrm,zAx2);
    for(var t=0;t<pts.length;t++){
      var p=pts[t];
      var pos=Af.clone().addScaledVector(e1,p.x).addScaledVector(e2,p.y)
                 .addScaledVector(nrm,0.02);
      var m=M0.clone();
      m.scale(new THREE.Vector3(sc,sc,sc));
      m.setPosition(pos);
      out.push({mat:m,gid:gid++});
    }
  }
  S.ifsInfo={mode:'ifs3d',perFace:pts.length,flowers:out.length,cover:sol.cover,
             base:sol.base,added:sol.added,rf:sol.rf,r:d,petal:petal,dr:dr,spin:spinDeg,
             nv:sol.nv,total:sol.total};
  return out;
}
