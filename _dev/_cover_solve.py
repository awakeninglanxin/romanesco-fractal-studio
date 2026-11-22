# -*- coding: utf-8 -*-
"""二维"三角面无缝覆盖"求解器原型
目的：给网页里 ifs3d（五棱锥花盘山）找一组数学上保证铺满的参数，
      而不是靠肉眼看截图手调。

几何基准（面局部坐标，单位=场景单位）：
  底面边长 e=5.0，外接半径 Rp=e/(2 sin36°)，山高 Hp=0.62 Rp
  坡面三角形：A(0,0) B(L1,0) C(Cx,Cy)
花盘真实占地 = 7 个相切底盘锥 -> 外接圆半径 r，等效圆半径 r_eff=0.90r
覆盖判据（三角格点间距 d）：d/√3 ≤ r_eff   （相切是 d=√3 r，覆盖要再缩）
"""
import math, random

def frame(e=5.0, hp_k=0.62):
    Rp = e/(2*math.sin(math.pi/5))
    Hp = hp_k*Rp
    L1 = e                       # 底边
    L2 = math.hypot(Rp, Hp)      # 母线（斜边）
    Cx = L1/2
    Cy = math.sqrt(max(0.0, L2*L2 - Cx*Cx))
    return L1, L2, Cx, Cy, Rp, Hp

def bary(p, L1, Cx, Cy):
    wC = p[1]/Cy
    wB = (p[0]-wC*Cx)/L1
    wA = 1-wB-wC
    return wA, wB, wC

def inside(p, L1, Cx, Cy, eps=-0.01):
    a,b,c = bary(p,L1,Cx,Cy)
    return a>=eps and b>=eps and c>=eps

def lattice(d, rot, L1, Cx, Cy):
    ax,az = math.cos(rot), math.sin(rot)
    bx,bz = math.cos(rot+math.pi/3), math.sin(rot+math.pi/3)
    pts=[]
    # 覆盖范围
    n = int((L1+2*Cy)/d)+2
    for i in range(-n, n+1):
        for j in range(-n, n+1):
            x = i*d*ax + j*d*bx
            y = i*d*az + j*d*bz
            pts.append((x,y))
    return pts

def solve(e=5.0, N=40, fill=2, jitter=0.14, target=0.995, rk=0.70, ref_eff=0.90, seed=1):
    L1,L2,Cx,Cy,Rp,Hp = frame(e)
    area = 0.5*L1*Cy
    d = math.sqrt(2*area/(math.sqrt(3)*N))
    r0 = rk*d
    rnd = random.Random(seed)

    # ① 两种取向取面内点更多的那个
    best=None
    for rot in (0.0, math.pi/6):
        pl=[p for p in lattice(d,rot,L1,Cx,Cy) if inside(p,L1,Cx,Cy, -0.02)]
        if best is None or len(pl)>len(best): best=pl
    pts=[{"x":p[0]+(rnd.random()-0.5)*2*jitter*d,
          "y":p[1]+(rnd.random()-0.5)*2*jitter*d,"r":r0,"gen":1} for p in best]
    # 夹回三角形内（抖动越界 -> 拉回）
    for p in pts:
        if not inside((p["x"],p["y"]),L1,Cx,Cy,0.0):
            p["x"]=min(max(p["x"],0.0),L1); p["y"]=min(max(p["y"],0.0),Cy)

    # ② 覆盖率栅格（重心坐标均匀采样，含边界）
    ns = max(14, min(80, int(round(L1/(0.30*r0)))))
    S=[]
    for i in range(ns+1):
        for j in range(ns+1-i):
            wB=i/ns; wC=j/ns; wA=1-wB-wC
            S.append((wB*L1+wC*Cx, wC*Cy, wA,wB,wC))
    def clearance_field(pts):
        # 用网格桶加速
        cell=r0*1.05
        g={}
        for idx,p in enumerate(pts):
            k=(int(math.floor(p["x"]/cell)),int(math.floor(p["y"]/cell)))
            g.setdefault(k,[]).append(idx)
        out=[]
        for s in S:
            ix,iy=int(math.floor(s[0]/cell)),int(math.floor(s[1]/cell))
            cd=1e9
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    for idx in g.get((ix+dx,iy+dy),()):
                        p=pts[idx]
                        dd=math.hypot(p["x"]-s[0],p["y"]-s[1])-ref_eff*p["r"]
                        if dd<cd: cd=dd
            out.append(cd)
        return out

    added=0
    for rd in range(fill+1):
        cl=clearance_field(pts)
        worst=max(cl)
        if worst<=0.04*r0: break
        # 只在真正的大洞补，逐点插（补完重算，避免越补越乱）
        guard=0
        while guard < N*2:
            guard+=1
            cl=clearance_field(pts)
            bi=max(range(len(cl)), key=lambda k: cl[k])
            worst=cl[bi]
            if worst<=0.03*r0: break
            s=S[bi]
            rn=min(r0*0.78, max(r0*0.42, worst*1.45))
            pts.append({"x":s[0],"y":s[1],"r":rn,"gen":rd+2})
            added+=1
            if added> N*1.4: break
        if added> N*1.4: break

    cl=clearance_field(pts)
    cover=sum(1 for c in cl if c<=0)/len(cl)
    return dict(N=N, per_face=len(pts), base=len(best), added=added, r0=r0, d=d,
                cover=cover, area=area, ns=ns, samples=len(S))

if __name__=="__main__":
    L1,L2,Cx,Cy,Rp,Hp=frame()
    area=0.5*L1*Cy
    print("面: L1=%.3f L2=%.3f C=(%.3f,%.3f) Rp=%.3f Hp=%.3f area=%.3f"%(L1,L2,Cx,Cy,Rp,Hp,area))
    print("N  点数 补缝 r0     d     覆盖%")
    for N in (12,16,20,24,28,32,36,40,48,56,64,80):
        r=solve(N=N)
        print("%2d %4d %4d %.4f %.4f %6.2f%%"%(r['N'],r['per_face'],r['added'],r['r0'],r['d'],r['cover']*100))
