/* ============================================================
   ===== 通用「铺满」评分内核 + 四类形态的一键最优求解 =====
   ------------------------------------------------------------
   四个预设的"漏"不是同一个几何量，所以分开解：
     A 直立花盘/圣诞树 → 蜂窝格点之间（基本胞是等边三角形）的缝合缝
     B 正60面体      → 每个五/六边形面内的露砖（面局部 2D）
     C 正五边形      → 单块五边形上的相切缝 / IFS 自相似空腔
     D 三种分形塔    → 母锥侧面有没有裸（锥面展开成矩形算覆盖率）

   单株花盘的**真实**几何（必须按这个建模，否则求解结果落地会不符）：
     底盘 = 1 中心锥 + 6 花瓣锥，锥底半径 b（= R0/3），花瓣环半径 = ringK·b；
     故占地半径 = (ringK+1)·b。ringK=2 → 7 盘两两相切，30° 方向自带 6 个凹口
     （单个花盘自身就漏 ~6%）；ringK≈1.70 → 相邻盘重叠、并集近似整圆，
     但占地半径同时缩到 0.9 倍 —— 所以 ringK 与株距必须一起解，不能只调一个。
   判定一律用**真实并集**：逐采样点测"到 7 个圆心距离 ≤ b"，不做圆近似。 */

/* 凸多边形内外判定（任意绕向，按叉积符号自洽） */
function polyInside(pts,x,z){
  var s=0;
  for(var i=0;i<pts.length;i++){
    var a=pts[i],b=pts[(i+1)%pts.length];
    var cr=(b.x-a.x)*(z-a.z)-(b.z-a.z)*(x-a.x);
    if(cr>1e-10){if(s<0)return false;s=1;}
    else if(cr<-1e-10){if(s>0)return false;s=-1;}
  }
  return true;
}
/* 多边形内均匀采样点（一次生成、多组参数复用 → 搜索才够快） */
function polySamples(pts,nv){
  var x0=1e9,x1=-1e9,z0=1e9,z1=-1e9;
  for(var i=0;i<pts.length;i++){
    var p=pts[i];
    if(p.x<x0)x0=p.x; if(p.x>x1)x1=p.x;
    if(p.z<z0)z0=p.z; if(p.z>z1)z1=p.z;
  }
  var xs=[],zs=[];
  for(var a=0;a<=nv;a++){
    for(var b=0;b<=nv;b++){
      var x=x0+(x1-x0)*a/nv,z=z0+(z1-z0)*b/nv;
      if(polyInside(pts,x,z)){xs.push(x);zs.push(z);}
    }
  }
  return {xs:xs,zs:zs,n:xs.length};
}
/* 单株命中：q={x,z,b,spin,single}  b=底盘锥底半径；single=只有中心锥（补缝小株） */
function flowerHit(q,ringK,x,z){
  var dx=x-q.x,dz=z-q.z,b=q.b;
  if(q.single)return dx*dx+dz*dz<=b*b;
  var b2=b*b;
  if(dx*dx+dz*dz<=b2)return true;                 // 中心盘
  var ring=ringK*b,sp=q.spin||0;
  for(var s=0;s<6;s++){
    var a=sp+s*Math.PI/3;
    var ex=dx-ring*Math.cos(a),ez=dz-ring*Math.sin(a);
    if(ex*ex+ez*ez<=b2)return true;               // 6 个花瓣盘
  }
  return false;
}
function coverFrac(sm,fl,ringK){
  var hit=0;
  for(var i=0;i<sm.n;i++){
    var x=sm.xs[i],z=sm.zs[i];
    for(var k=0;k<fl.length;k++){
      if(flowerHit(fl[k],ringK,x,z)){hit++;break;}
    }
  }
  return sm.n?hit/sm.n:0;
}
/* 正 n 边形在方向 φ 上的边界半径（顶点方向 = R，边中点方向 = 内切圆半径）。
   为什么不用"到最近边距离"判越界：顶点方向的花盘本来就要越过边线才够得着顶点，
   那是设计意图而非越界；真正该管的是"花盘有没有伸出该方向上的多边形边界"。 */
function regRadial(n,R,off,phi){
  var d=((phi-off)%(2*Math.PI/n))-Math.PI/n;
  return R*Math.cos(Math.PI/n)/Math.cos(d);
}
function radOutOf(fl,ringK,n,R,off){
  var m=-1e9;
  for(var i=0;i<fl.length;i++){
    var q=fl[i],ext=q.single?q.b:q.b*(ringK+1);
    var o=ext-regRadial(n,R,off,Math.atan2(q.z,q.x));
    if(o>m)m=o;
  }
  return m;
}
function regPoly(n,R,off){
  var out=[];
  for(var k=0;k<n;k++){
    var a=off+2*Math.PI*k/n;
    out.push({x:R*Math.cos(a),z:R*Math.sin(a)});
  }
  return out;
}
/* 正六边形面：6 株环绕 + 中心 1 株（环半径与盘半径相互独立，与构建同式） */
function hexFaceFlowers(e,r,ring,rMid){
  var fl=[];
  for(var k=0;k<6;k++){
    var a=2*Math.PI*k/6;
    fl.push({x:ring*Math.cos(a),z:ring*Math.sin(a),b:r/3,spin:0});
  }
  fl.push({x:0,z:0,b:rMid/3,spin:0});
  return fl;
}
/* 五边形面 = 5 顶点株 + 中心株 + 5 条边中点株。
   实测（面内栅格）：只做 5+中心 覆盖 82%；补 5 条"相切透镜缝"到 89%；
   把补缝换成"边中点一整株"直接到 98%，株数同为 11 —— 空缺本在边中点那一带，
   缝只是它的残余，补整株比补缝更对位。 */
function pentFaceFlowers(e,r,ringF,rcF,midR,midRing){
  var ring=r*ringF,rc=r*rcF,fl=[];
  for(var k=0;k<5;k++){
    var a=Math.PI/2+2*Math.PI*k/5;
    fl.push({x:ring*Math.cos(a),z:ring*Math.sin(a),b:r/3,spin:0});
  }
  fl.push({x:0,z:0,b:rc/3,spin:0});
  if(midR>0){
    for(var k2=0;k2<5;k2++){
      var a2=Math.PI/2+Math.PI/5+2*Math.PI*k2/5;
      fl.push({x:midRing*Math.cos(a2),z:midRing*Math.sin(a2),b:midR/3,spin:0});
    }
  }
  return fl;
}

/* ---------------- A. 直立花盘 / 圣诞树：蜂窝基本胞缝合 ----------------
   基本胞 = 相邻三株中心围出的等边三角形（边长 = 株距 d、三株各一个花盘）。
   三株相切时重心到顶点 = 2/√3 = 1.155 > 1（占地半径）→ 必留孔；
   两条解法：① 株距收到 √3 以下；② 基本胞重心补一株（autoFill 的语义）。
   邻株相位交错 30°：我的 30° 凹口正对邻居的花瓣，缝自己咬合 —— 比硬缩株距自然。
   评分 = 覆盖率达标（≥99.5%）后取"畸变最小"（株距别缩、花形别压扁、补株别太大）。 */
function upAutoTune(){
  var SQ3=Math.sqrt(3),target=0.995,b=1/3;   // 归一化：ringK=2 时占地半径 = 1
  var ringKs=[2.00,1.85,1.70],sps=[1.00,0.96,0.92],alts=[0,1],fks=[0,0.75,0.90,1.05];
  var best=null,fallback=null;
  for(var si=0;si<sps.length;si++)for(var ki=0;ki<ringKs.length;ki++)
  for(var ai=0;ai<alts.length;ai++)for(var fi=0;fi<fks.length;fi++){
    var sp=sps[si],rk=ringKs[ki],al=alts[ai],fk=fks[fi];
    var d=2*sp,hf=al?Math.PI/6:0;
    var tri=[{x:0,z:0},{x:d,z:0},{x:d/2,z:d*SQ3/2}];
    var sm=polySamples(tri,48);
    var fl=[{x:0,z:0,b:b,spin:0},
            {x:d,z:0,b:b,spin:hf},
            {x:d/2,z:d*SQ3/2,b:b,spin:hf}];
    if(fk>0)fl.push({x:d/2,z:d*SQ3/6,b:b*fk,spin:0});   // 基本胞重心补株
    var cov=coverFrac(sm,fl,rk);
    var rec={ringK:rk,spread:sp,alt:al,cover:cov,fillK:fk,d:d,
             dist:(1-sp)*1.2+(2-rk)*0.6+(fk?0.35:0)+Math.max(0,fk-1)*0.6};
    if(fallback===null||cov>fallback.cover)fallback=rec;
    if(cov>=target&&(best===null||rec.dist<best.dist))best=rec;
  }
  if(!best)best=fallback;
  S.upPetal=best.ringK;S.upSpread=best.spread;S.upAlt=best.alt;
  S.autoFill=best.fillK>0;if(best.fillK>0)S.fillK=best.fillK;
  var pct=(best.cover*100).toFixed(2);
  return '<b style="color:'+(best.cover>=0.995?'#1b8a3a':'#b3541e')+'">✨ 最优解已应用：覆盖 '+pct+'%</b><br>'+
    '花瓣环 <b>'+best.ringK.toFixed(2)+'b</b>（占地 ×'+((best.ringK+1)/3).toFixed(2)+'）｜ 株距 <b>'+best.spread.toFixed(2)+'×</b> ｜ '+
    '邻株相位 '+(best.alt?'<b>交错 30°</b>':'同相 0°')+' ｜ '+
    (best.fillK?'重心补株 <b>'+best.fillK.toFixed(2)+'×</b>（已勾上自动填满）':'<b>无需补株</b>')+'<br>'+
    '<span style="color:#5a6672">判据：蜂窝基本胞（三株围出的等边三角形）内逐点验 7 盘真实并集。'+
    '三株相切时重心距顶点 1.155 &gt; 1（占地半径），必漏 —— 这是为什么要么缩株距、要么补一株。</span>';
}

/* ---------------- B. 正60面体：每面贴砖的露砖率 ----------------
   五/六边形面各自是正多边形，花盘半径/环半径按面棱长 e 定标。
   旧值（六 盘 0.72e / 环 0.66e / 中心 0.34e；五 5+中心+5 条透镜缝）是手调的：
   面内栅格实测六边形 97%、五边形只有 89%（五边形的空缺在边中点，不在缝里）。
   这里按真实并集 + 径向边界（不越出棱线）重新解，结果写进 S.tileP 原样落地。 */
function polyAutoTune(){
  var e=S.polyEdge||2.4;
  var R6=e,R5=e/(2*Math.sin(Math.PI/5));
  var hexPoly=regPoly(6,R6,0),pentPoly=regPoly(5,R5,Math.PI/2);
  var smH=polySamples(hexPoly,46),smP=polySamples(pentPoly,46);
  if(S.polyDens==='one'){
    var fl0=[{x:0,z:0,b:e/3,spin:0}];
    var cH=coverFrac(smH,fl0,2.0),cP=coverFrac(smP,[{x:0,z:0,b:0.98*e/3,spin:0}],2.0);
    return '✨ <b>单朵·精雕</b>：每面 1 株，覆盖率受"一株花盘的六边形轮廓"限制 —— '+
      '六边形面 <b>'+(cH*100).toFixed(1)+'%</b>、五边形面 <b>'+(cP*100).toFixed(1)+'%</b>。<br>'+
      '<span style="color:#b3541e">要零露砖请切「贴砖·密集」再点一次（单朵模式的露角是算法本征，不是参数问题）。</span>';
  }
  /* 六边形面：花瓣环保持 2.0（相切花神图案），只调盘半径/环半径/中心株 */
  var bestH=null;
  for(var r=0.70;r<=0.8401;r+=0.02)for(var ring=0.64;ring<=0.7401;ring+=0.02)
  for(var mid=0.18;mid<=0.3001;mid+=0.04){
    var fl=hexFaceFlowers(e,r*e,ring*e,mid*e);
    var out=radOutOf(fl,2.0,6,R6,0);
    if(out>0.01)continue;                       // 伸出棱线 → 会和邻面花盘打架
    var cov=coverFrac(smH,fl,2.0);
    var sco=cov-r*0.02;                        // 达标后取更小的盘（少重叠、花更清）
    if(bestH===null||sco>bestH.sco)bestH={sco:sco,cov:cov,out:out,r:r,ring:ring,mid:mid};
  }
  if(!bestH){   // 兜底：退回当前手调值
    bestH={cov:coverFrac(smH,hexFaceFlowers(e,0.72*e,0.66*e,0.34*e),2.0),out:0,r:0.72,ring:0.66,mid:0.34};
  }
  /* 五边形面：5 顶点株 + 中心 + 5 边中点株 */
  var bestP=null;
  for(var pr=0.34;pr<=0.4601;pr+=0.03)for(var rf=1.45;rf<=1.7001;rf+=0.125)
  for(var rcF=0.90;rcF<=1.1001;rcF+=0.10)for(var mr=0.38;mr<=0.4801;mr+=0.05)
  for(var mrg=0.36;mrg<=0.4601;mrg+=0.05){
    var fl2=pentFaceFlowers(e,pr*e,rf,rcF,mr*e,mrg*e);
    var out2=radOutOf(fl2,2.0,5,R5,Math.PI/2);
    if(out2>0.01)continue;
    var cov2=coverFrac(smP,fl2,2.0);
    var sco2=cov2-pr*0.02;
    if(bestP===null||sco2>bestP.sco)bestP={sco:sco2,cov:cov2,out:out2,r:pr,ringF:rf,rcF:rcF,midR:mr,midRing:mrg};
  }
  if(!bestP){
    bestP={cov:coverFrac(smP,pentFaceFlowers(e,0.52*e,1.7009,0.95,0,0),2.0),out:0,r:0.52,ringF:1.7009,rcF:0.95,midR:0,midRing:0};
  }
  S.tileP={hexR:bestH.r,hexRing:bestH.ring,hexMid:bestH.mid,
           pentR:bestP.r,pentRingF:bestP.ringF,pentRc:bestP.rcF,
           pentMidR:bestP.midR,pentMidRing:bestP.midRing,pentGap:0};
  S.polyPentFill=false;S.polyPetal=2.0;
  var pct=Math.min(bestH.cov,bestP.cov)*100;
  return '<b style="color:'+(pct>=99?'#1b8a3a':'#b3541e')+'">✨ 最优贴砖已应用：最差面覆盖 '+pct.toFixed(2)+'%</b><br>'+
    '六边形面：盘 <b>'+bestH.r.toFixed(2)+'e</b> ｜ 环 <b>'+bestH.ring.toFixed(2)+'e</b> ｜ 中心 <b>'+bestH.mid.toFixed(2)+'e</b>（覆盖 '+(bestH.cov*100).toFixed(2)+'%，径向越界 '+bestH.out.toFixed(3)+'e）<br>'+
    '五边形面：11 株 = 5 顶点 + 中心 + 5 边中点 ｜ 盘 <b>'+bestP.r.toFixed(2)+'e</b> ｜ 环 <b>'+bestP.ringF.toFixed(2)+'r</b> ｜ 中边株 <b>'+bestP.midR.toFixed(2)+'e@'+bestP.midRing.toFixed(2)+'e</b>（覆盖 '+(bestP.cov*100).toFixed(2)+'%）<br>'+
    '<span style="color:#5a6672">判据：面局部坐标系里对 12 个五边形 + 20 个六边形逐点验 7 盘真实并集；'+
    '越界用"径向边界"判（顶点方向的外伸是设计意图，不算越界）。</span>';
}

/* ---------------- C. 正五边形（相切平铺 / Sierpinski IFS） ----------------
   相切模式：5 株沿顶点方向相切。rt 上限 = Rp/2.70 = 0.315e（再大就戳出顶点）；
   中心株要与五株"相切不留环形缝"需 rc ≥ rt·(1/sin36−1) = 0.70rt；
   五条相切缝（沿 36°+72k）再放 5 株单锥小株，半径取缝长 × gapR。
   IFS 模式：副本以 r=(3−√5)/2 收缩，Sierpinski 的五份副本之间**本征留空**，
   只能靠"每株花盘略大于副本内切圆"去压缝，覆盖率天然上不到 100%。 */
function pentFlatAutoTune(){
  var e=S.pentEdge||5.0;
  var Rp=e/(2*Math.sin(Math.PI/5));
  var pentPoly=regPoly(5,Rp,Math.PI/2);
  var sm=polySamples(pentPoly,56);
  var i,fl,cov,best=null;
  if(S.pentAlgo==='ifs'){
    var PHIv=(1+Math.sqrt(5))/2,rS=1/(1+PHIv),COS36=Math.cos(Math.PI/5);
    var depth=S.ifsDepth||2,wc=S.ifsCenter!==false;
    var nodes=[{x:0,z:0,R:Rp,rot:Math.PI/2}];
    for(var dd=0;dd<depth;dd++){
      var next=[];
      nodes.forEach(function(p){
        for(var k=0;k<5;k++){
          var a=p.rot+2*Math.PI*k/5;
          next.push({x:p.x+(1-rS)*p.R*Math.cos(a),z:p.z+(1-rS)*p.R*Math.sin(a),R:p.R*rS,rot:p.rot});
        }
        if(wc)next.push({x:p.x,z:p.z,R:p.R*rS,rot:p.rot+Math.PI/5});
      });
      nodes=next;
    }
    var scales=[0.96,1.02,1.08,1.14,1.20];
    for(i=0;i<scales.length;i++){
      fl=nodes.map(function(p){return {x:p.x,z:p.z,b:p.R*COS36*scales[i]/3,spin:0};});
      cov=coverFrac(sm,fl,2.0);
      if(best===null||cov>best.cov+1e-9)best={cov:cov,scale:scales[i],n:nodes.length};
    }
    S.pentIFSScale=best.scale;
    return '<b style="color:'+(best.cov>=0.995?'#1b8a3a':'#b3541e')+'">✨ IFS 最优：覆盖率 '+(best.cov*100).toFixed(2)+'%</b><br>'+
      '每株花盘占地 = 副本内切圆 × <b>'+best.scale.toFixed(2)+'</b> ｜ 共 <b>'+best.n+'</b> 株（depth '+depth+(wc?' · 含中心映射':'')+'）<br>'+
      '<span style="color:#b3541e">Sierpinski 五边形的五份副本之间本征留空 —— 覆盖率上不去是分形定义决定的；'+
      '要 100% 无缝请切「相切平铺」或「五棱锥花盘山」。</span>';
  }
  /* 相切平铺：rt × 中心株 × 相切缝补株半径 */
  var rtFs=[0.285,0.300,0.315,0.325],rcFs=[0.70,0.85,1.00],gapRs=[0,0.75,0.90,1.05];
  for(var a2=0;a2<rtFs.length;a2++)for(var b3=0;b3<rcFs.length;b3++)for(var g=0;g<gapRs.length;g++){
    var rt=rtFs[a2]*e,ring=rt/Math.sin(Math.PI/5),rc=rt*rcFs[b3];
    fl=[];
    for(i=0;i<5;i++){
      var ang=Math.PI/2+2*Math.PI*i/5;
      fl.push({x:ring*Math.cos(ang),z:ring*Math.sin(ang),b:rt/3,spin:0});
    }
    if(S.pentSolid!==false)fl.push({x:0,z:0,b:rc/3,spin:0});
    if(gapRs[g]>0){
      var inPent=0.688*e,gapD=Math.max(0.05*e,inPent-rc),rEdge=gapD*gapRs[g],pos=(rc+inPent)*0.5;
      for(i=0;i<5;i++){
        var a3=Math.PI/2+Math.PI/5+2*Math.PI*i/5;
        fl.push({x:pos*Math.cos(a3),z:pos*Math.sin(a3),b:rEdge,single:true});
      }
    }
    var out=radOutOf(fl,2.0,5,Rp,Math.PI/2);
    if(out>0.01)continue;
    cov=coverFrac(sm,fl,2.0);
    var sco=cov+rt*0.15-gapRs[g]*0.01;       // 覆盖率优先，其次"贴得越满越好"，补株越小越好
    if(best===null||sco>best.sco)best={sco:sco,cov:cov,out:out,rtF:rtFs[a2],rcF:rcFs[b3],gapR:gapRs[g]};
  }
  if(!best)best={cov:0,out:0,rtF:0.285,rcF:0.70,gapR:0.62};
  S.pentRF=best.rtF;S.pentRcF=best.rcF;S.pentGapFill=best.gapR>0;S.pentGapR=best.gapR;
  return '<b style="color:'+(best.cov>=0.995?'#1b8a3a':'#b3541e')+'">✨ 最优相切已应用：覆盖 '+(best.cov*100).toFixed(2)+'%</b><br>'+
    '花盘半径 <b>'+best.rtF.toFixed(3)+'e</b> ｜ 中心株 <b>'+best.rcF.toFixed(2)+'r</b> ｜ 相切缝补株 <b>'+(best.gapR>0?('5 株 × '+best.gapR.toFixed(2)+' 缝长'):'关')+'</b> ｜ 径向越界 '+best.out.toFixed(3)+'e<br>'+
    '<span style="color:#5a6672">rt 上限 = Rp/2.70 = 0.315e（再大就戳出顶点）；中心株 ≥0.70r 才与五株相切不留环形缝。</span>';
}

/* ---------------- D. 三种分形塔：母锥侧面的裸露率 ----------------
   把母锥侧面按 (θ, t) 展开：横向弧长 = θ·R(1−t)，纵向 = t·母线长。
   子芽在 t=0.12+0.80(i+0.5)/n、θ=i·α 处，占地半径 = 子锥底半径 childR。
   逐点算到最近子芽的测地距离，> childR 就是裸锥面 —— 直接对应
   "levels 太大 → 预算被压穿 → 母锥大片裸露"那个可见问题。
   预算 nodeCount = 1+n+…+n^L ≤ 0.82·MAX（MAX=120000），超了就会中途截断。 */
function coneCover(n,i2o,r2l){
  var H=1,R=r2l,alpha=S.angleDeg*Math.PI/180;
  var slant=Math.hypot(H,R);
  var seeds=[];
  for(var i=0;i<n;i++){
    var t=0.12+0.80*(i+0.5)/n,th=i*alpha;
    var childH=H*i2o*(1-0.45*t),childR=childH*r2l;
    seeds.push({t:t,th:th,r:childR});
  }
  var hit=0,tot=0;
  for(var ti=0;ti<=26;ti++){
    var t=0.02+0.96*ti/26;
    for(var ai=0;ai<44;ai++){
      var th=2*Math.PI*ai/44;
      tot++;
      for(var k=0;k<seeds.length;k++){
        var s=seeds[k];
        var dth=Math.abs(th-s.th)%(2*Math.PI);
        if(dth>Math.PI)dth=2*Math.PI-dth;
        var dx=dth*R*(1-(t+s.t)*0.5);
        var dy=(t-s.t)*slant;
        if(dx*dx+dy*dy<=s.r*s.r){hit++;break;}
      }
    }
  }
  return hit/tot;
}
function fractalAutoTune(){
  var MAXN=120000*0.82;
  function cost(n,L){var s=0,t=1;for(var k=0;k<=L;k++){s+=t;t*=n;}return s;}
  var lv0=Math.max(1,Math.round(S.levels));
  var cur=coneCover(Math.round(S.cones),S.i2o,S.r2l);
  /* 不许把预设的"松/紧"风格洗掉：芽数最多到 1.6 倍，子锥比只在原值 ±0.08 内微调。
     「西兰花—松散花蕾」被调成密堆就不是那个预设了，这比覆盖率更重要。 */
  var n0=Math.max(5,Math.round(S.cones)),i0=S.i2o;
  var nMax=Math.min(31,Math.max(n0,Math.round(n0*1.6))),nMin=Math.max(5,n0-2);
  var i2os=[i0-0.04,i0,i0+0.04,i0+0.08].filter(function(v){return v>=0.3&&v<=0.7;});
  if(!i2os.length)i2os=[i0];
  var best=null;
  for(var L=Math.min(5,lv0+1);L>=2;L--){
    for(var n=nMin;n<=nMax;n++){
      var c=cost(n,L);
      if(c>MAXN)break;
      for(var q=0;q<i2os.length;q++){
        var cov=coneCover(n,i2os[q],S.r2l);
        var score=cov-1e-4*c/MAXN-0.004*Math.abs(L-lv0);
        if(best===null||score>best.score)best={score:score,cov:cov,n:n,L:L,i2o:i2os[q],cost:c};
      }
    }
  }
  var sameL=(best&&best.L===lv0&&best.n===n0&&Math.abs(best.i2o-S.i2o)<1e-9);
  if(!best||best.cov<=cur+0.01||sameL){
    return '✨ 当前参数已是预算内最优：母锥裸露 <b>'+((1-cur)*100).toFixed(1)+'%</b>（'+
      n0+' 芽 × '+lv0+' 层 ｜ 子锥比 '+S.i2o.toFixed(2)+'）。<br>'+
      '<span style="color:#5a6672">残余裸露集中在 t&lt;0.12 的锥脚与 t&gt;0.92 的锥尖 —— 那两处本来就不长芽，属于几何本征。</span>';
  }
  S.levels=best.L;S.cones=best.n;S.i2o=best.i2o;
  if($('levels')){$('levels').value=best.L;$('vLevels').textContent=best.L;}
  if($('cones')){$('cones').value=best.n;$('vCones').textContent=best.n;}
  if($('i2o')){$('i2o').value=Math.round(best.i2o*100);$('vI2O').textContent=best.i2o.toFixed(2);}
  return '<b style="color:'+(best.cov>=0.97?'#1b8a3a':'#b3541e')+'">✨ 最优密度已应用：母锥覆盖 '+(best.cov*100).toFixed(2)+'%</b><br>'+
    '每级 <b>'+best.n+'</b> 芽 × <b>'+best.L+'</b> 层 ｜ 子锥比 <b>'+best.i2o.toFixed(2)+'</b> ｜ '+
    '预算占用 '+(best.cost/MAXN*100).toFixed(0)+'%（不截断，每株都完整生成）<br>'+
    '<span style="color:#5a6672">判据：母锥侧面展开（横向弧长 × 纵向母线长），逐点算到最近子芽的测地距离；'+
    '距离大于子锥底半径的地方，就是肉眼看得见的裸锥面。</span>';
}

/* 统一入口：按当前形态分派 */
function autoTuneAll(){
  var f=S.form,msg;
  if(f==='upright')msg=upAutoTune();
  else if(f==='poly')msg=polyAutoTune();
  else if(f==='pent')msg=(S.pentAlgo==='ifs3d')?pentAutoTune():pentFlatAutoTune();
  else msg=fractalAutoTune();
  S.autoMsg=msg;
  return msg;
}
