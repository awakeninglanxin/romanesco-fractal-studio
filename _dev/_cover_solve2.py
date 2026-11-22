# -*- coding: utf-8 -*-
"""覆盖求解器 v2：用「7 个相切底盘锥的真实并集」来验收覆盖率，
   而不是用等效圆近似 —— 避免"算法说铺满了、眼睛看到缝"的循环论证。"""
import math, random

def frame(e=5.0, hp_k=0.62):
    Rp = e/(2*math.sin(math.pi/5)); Hp = hp_k*Rp
    L1 = e; L2 = math.hypot(Rp, Hp); Cx = L1/2
    Cy = math.sqrt(max(0.0, L2*L2 - Cx*Cx))
    return L1, L2, Cx, Cy, Rp, Hp

def bary(p,L1,Cx,Cy):
    wC=p[1]/Cy; wB=(p[0]-wC*Cx)/L1; return 1-wB-wC,wB,wC

def inside(p,L1,Cx,Cy,eps=0.0):
    a,b,c=bary(p,L1,Cx,Cy); return a>=eps and b>=eps and c>=eps

def solve(e=5.0,N=40,fill=2,jitter=0.14,rk=0.70,ref_eff=0.90,seed=1,plug=True):
    L1,L2,Cx,Cy,Rp,Hp=frame(e); area=0.5*L1*Cy
    d=math.sqrt(2*area/(math.sqrt(3)*N)); r0=rk*d
    rnd=random.Random(seed)
    best=None
    for rot in (0.0, math.pi/6):
        pl=[]
        n=int((L1+2*Cy)/d)+2
        ax,az=math.cos(rot),math.sin(rot); bx,bz=math.cos(rot+math.pi/3),math.sin(rot+math.pi/3)
        for i in range(-n,n+1):
            for j in range(-n,n+1):
                x=i*d*ax+j*d*bx; y=i*d*az+j*d*bz
                if inside((x,y),L1,Cx,Cy,-0.02): pl.append((x,y))
        if best is None or len(pl)>len(best): best=pl
    pts=[]
    for (x,y) in best:
        nx=x+(rnd.random()-0.5)*2*jitter*d; ny=y+(rnd.random()-0.5)*2*jitter*d
        if not inside((nx,ny),L1,Cx,Cy,0.0): nx,ny=x,y     # 抖出界 -> 回到格点
        pts.append({"x":nx,"y":ny,"r":r0})
    base=len(pts)

    def clear_field(pts, extra=()):
        cell=r0*1.05; g={}
        allp=list(pts)+list(extra)
        for idx,p in enumerate(allp):
            k=(int(math.floor(p["x"]/cell)),int(math.floor(p["y"]/cell)))
            g.setdefault(k,[]).append(idx)
        out=[]
        for s in SAMP:
            ix,iy=int(math.floor(s[0]/cell)),int(math.floor(s[1]/cell)); cd=1e9
            for dx in(-1,0,1):
                for dy in(-1,0,1):
                    for idx in g.get((ix+dx,iy+dy),()):
                        p=allp[idx]
                        dd=math.hypot(p["x"]-s[0],p["y"]-s[1])-ref_eff*p["r"]
                        if dd<cd: cd=dd
            out.append(cd)
        return out

    # 验收采样：比求解采样更密
    nv=max(40,min(160,int(round(L1/(0.12*r0)))))
    SAMP=[]
    for i in range(nv+1):
        for j in range(nv+1-i):
            wB=i/nv; wC=j/nv
            SAMP.append((wB*L1+wC*Cx,wC*Cy))
    added=0
    if plug:
        for rd in range(fill+1):
            guard=0
            while guard<N*2:
                guard+=1
                cl=clear_field(pts); bi=max(range(len(cl)),key=lambda k:cl[k]); worst=cl[bi]
                if worst<=0.02*r0: break
                s=SAMP[bi]; rn=min(r0*0.80,max(r0*0.40,worst*1.45))
                pts.append({"x":s[0],"y":s[1],"r":rn}); added+=1
                if added>N*1.5: break
            if added>N*1.5 or worst<=0.02*r0: break

    # 真实并集验收（7 个半径 r/3 的圆盘：中心 + 环半径 2r/3）
    RING=[(math.cos(k*math.pi/3),math.sin(k*math.pi/3)) for k in range(6)]
    def true_cover(pt):
        for p in pts:
            r=p["r"]; br=r/3.0
            dx=pt[0]-p["x"]; dy=pt[1]-p["y"]
            if dx*dx+dy*dy <= br*br: return True
            for (cx6,cz6) in RING:
                ex=dx-2*br*cx6; ey=dy-2*br*cz6
                if ex*ex+ey*ey<=br*br: return True
        return False
    cov=sum(1 for s in SAMP if true_cover(s))/len(SAMP)
    cov0=None
    return dict(N=N,per_face=len(pts),base=base,added=added,r0=r0,d=d,cover=cov,
                area=area,samples=len(SAMP),pts=pts)

if __name__=="__main__":
    print("N  基准 补缝 总株 r0     d      真实覆盖率")
    for rk in (0.66,0.70,0.74):
        print("--- rk=%.2f ---"%rk)
        for N in (20,24,28,32,40,48,64):
            r=solve(N=N,rk=rk)
            print("%2d %4d %4d %4d %.4f %.4f %7.3f%%"%(r['N'],r['base'],r['added'],r['per_face'],r['r0'],r['d'],r['cover']*100))
