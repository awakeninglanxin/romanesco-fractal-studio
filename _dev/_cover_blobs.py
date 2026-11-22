# -*- coding: utf-8 -*-
"""缺口「连通块」分析：真正决定"看着有没有缝"的不是覆盖率百分比，
   而是最大连续空白块的尺寸。用 (i,j) 重心格栅做 4 邻域洪泛。"""
import math, random
import _cover_solve2 as m

L1,L2,Cx,Cy,Rp,Hp=m.frame(); AREA=0.5*L1*Cy

def lattice_pts(N,rk,jitter=0.14,spin=30.0,seed=1,rot_choice=None):
    d=math.sqrt(2*AREA/(math.sqrt(3)*N)); r0=rk*d
    rnd=random.Random(seed); best=None; brot=0.0
    for rot in (0.0, math.pi/6):
        pl=[]; n=int((L1+2*Cy)/d)+2
        ax,az=math.cos(rot),math.sin(rot); bx,bz=math.cos(rot+math.pi/3),math.sin(rot+math.pi/3)
        for i in range(-n,n+1):
            for j in range(-n,n+1):
                x=i*d*ax+j*d*bx; y=i*d*az+j*d*bz
                if m.inside((x,y),L1,Cx,Cy,-0.02): pl.append((x,y))
        if best is None or len(pl)>len(best): best=pl; brot=rot
    pts=[]
    for (x,y) in best:
        nx=x+(rnd.random()-0.5)*2*jitter*d; ny=y+(rnd.random()-0.5)*2*jitter*d
        if not m.inside((nx,ny),L1,Cx,Cy,0.0): nx,ny=x,y
        pts.append([nx,ny,r0,(brot+math.radians(spin))])
    return pts,d,r0

def covered(pts,x,y):
    for (px,py,r,sp) in pts:
        br=r/3.0; dx=x-px; dy=y-py
        if dx*dx+dy*dy<=br*br: return True
        for k in range(6):
            a=sp+k*math.pi/3
            ex=dx-2*br*math.cos(a); ey=dy-2*br*math.sin(a)
            if ex*ex+ey*ey<=br*br: return True
    return False

def analyze(pts,nv=110):
    # 第 i 行有 i+1 个点（wC=j/nv, wB=i/nv）
    grid=[]; idx=[]
    for i in range(nv+1):
        row=[]
        for j in range(nv+1-i):
            wB=i/nv; wC=j/nv
            row.append(covered(pts,wB*L1+wC*Cx,wC*Cy))
        grid.append(row)
    # 洪泛：邻居 (i+1,j) (i+1,j+1) (i,j-1) (i,j+1)
    seen=[[False]*(nv+1-i) for i in range(nv+1)]
    comps=[]
    for i in range(nv+1):
        for j in range(nv+1-i):
            if grid[i][j] or seen[i][j]: continue
            st=[(i,j)]; seen[i][j]=True; cells=[]
            while st:
                a,b=st.pop(); cells.append((a,b))
                for na,nb in ((a+1,b),(a-1,b),(a,b-1),(a,b+1),(a+1,b-1),(a-1,b+1)):
                    if 0<=na<=nv and 0<=nb<=nv-na and not grid[na][nb] and not seen[na][nb]:
                        seen[na][nb]=True; st.append((na,nb))
            comps.append(cells)
    comps.sort(key=len,reverse=True)
    tot=sum(len(c) for c in comps)
    allc=(nv+1)*(nv+2)//2
    # 每个块的"直径"（以面高 Cy 归一）
    info=[]
    for c in comps[:6]:
        pts2=[(b/nv*L1+a/nv*Cx, a/nv*Cy) for a,b in c]
        xs=[p[0] for p in pts2]; ys=[p[1] for p in pts2]
        dia=math.hypot(max(xs)-min(xs),max(ys)-min(ys))
        info.append((len(c), dia/Cy*100))
    return 1-tot/allc, info, allc

if __name__=="__main__":
    print("N  rk  覆盖%  最大块(采样数/直径%面高)  次大  第三")
    for N in (32,40,48):
        for rk in (0.66,0.70,0.74,0.78):
            pts,d,r0=lattice_pts(N,rk)
            cov,info,allc=analyze(pts)
            s='  '.join('%d/%.1f%%'%(a,b) for a,b in info[:3])
            print("%2d %.2f %6.2f%%  %s"%(N,rk,cov*100,s))
