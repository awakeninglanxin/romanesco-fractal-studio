# -*- coding: utf-8 -*-
"""按最终要写进网页的算法，扫 (petal, dr, spin) 参数表：
   底盘花瓣环半径 = petal×b（b=单锥底半径），花盘外接半径 rf=(petal+1)b，
   三角格点间距 d = dr·rf，抖动 0.12d，用 7 圆盘真实并集判覆盖。
   输出：面内覆盖率（含边界）+ 需要补缝的级数。"""
import math, random

def frame(e=5.0):
    Rp=e/(2*math.sin(math.pi/5)); Hp=0.62*Rp
    L1=e; L2=math.hypot(Rp,Hp); Cx=L1/2
    Cy=math.sqrt(max(0.0,L2*L2-Cx*Cx))
    return L1,Cx,Cy,Rp,Hp

L1,Cx,Cy,Rp,Hp=frame(); AREA=0.5*L1*Cy

def solve(N=40,petal=1.65,dr=1.42,jit=0.12,spin=30,seed=7,fill=2):
    d=math.sqrt(2*AREA/(math.sqrt(3)*N)); rf=d/dr; bb=rf/(petal+1)
    rnd=random.Random(seed)
    def ins(x,y):
        wC=y/Cy
        if wC<-1e-9: return False
        wB=(x-wC*Cx)/L1
        return wB>=-1e-9 and 1-wB-wC>=-1e-9
    best=None;brot=0
    for rot in (0.0,math.pi/6):
        ax,ay=math.cos(rot),math.sin(rot); bx,by=math.cos(rot+math.pi/3),math.sin(rot+math.pi/3)
        n=int((L1+Cy)/d)+2; out=[]
        for i in range(-n,n+1):
            for j in range(-n,n+1):
                x=i*d*ax+j*d*bx; y=i*d*ay+j*d*by
                if ins(x,y): out.append((x,y))
        if best is None or len(out)>len(best): best,brot=out,rot
    P=[]
    for (x,y) in best:
        nx=x+(rnd.random()*2-1)*jit*d; ny=y+(rnd.random()*2-1)*jit*d
        if not ins(nx,ny): nx,ny=x,y
        P.append((nx,ny,rf,brot+math.radians(spin)))
    baseN=len(P)
    nv=max(24,min(96,int(round(L1/(0.16*rf)))))
    S=[]
    for i in range(nv+1):
        for j in range(nv+1-i):
            wB=i/nv; wC=j/nv
            S.append((wB*L1+wC*Cx,wC*Cy,i,j))
    def covered(x,y):
        for (px,py,r,s) in P:
            dx=x-px;dy=y-py
            if dx*dx+dy*dy>r*r: continue
            b2=r/(petal+1); b2s=b2*b2
            if dx*dx+dy*dy<=b2s: return True
            ring=petal*b2
            for k in range(6):
                a=s+k*math.pi/3
                gx=dx-ring*math.cos(a); gy=dy-ring*math.sin(a)
                if gx*gx+gy*gy<=b2s: return True
        return False
    def raster():
        c=0
        for (x,y,i,j) in S:
            if covered(x,y): c+=1
        return c
    covN=raster(); tot=len(S)
    # 补缝：BFS 距离场找最大空洞
    added=0
    for rnd_i in range(fill):
        if covN>=tot: break
        for _ in range(int(N*0.8)):
            # 距离场
            INF=-1; D={}
            q=[]
            for (x,y,i,j) in S:
                if covered(x,y): D[(i,j)]=0; q.append((i,j))
            head=0; best=(0,None)
            while head<len(q):
                i,j=q[head]; head+=1; dv=D[(i,j)]
                for (a,b) in ((i+1,j),(i-1,j),(i,j+1),(i,j-1),(i+1,j-1),(i-1,j+1)):
                    if a<0 or b<0 or a+b>nv: continue
                    if (a,b) in D: continue
                    D[(a,b)]=dv+1; q.append((a,b))
                    if dv+1>best[0]: best=(dv+1,(a,b))
            h=L1/nv
            if best[0]*h < 0.10*rf or best[1] is None: break
            i,j=best[1]
            px=i/nv*L1+j/nv*Cx; py=j/nv*Cy
            rn=min(rf*0.90,max(rf*0.42,best[0]*h*1.55))
            P.append((px,py,rn,brot+math.radians(spin)))
            added+=1
            covN=raster()
        if added>N*1.6: break
    return covN/tot, baseN, added, rf, d, nv

if __name__=="__main__":
    print("petal  dr   覆盖%   基准 补缝 总株  rf")
    for petal in (2.00,1.85,1.70,1.60,1.50,1.40):
        for dr in (1.62,1.52,1.44,1.36):
            cov,base,add,rf,d,nv=solve(petal=petal,dr=dr)
            print("%.2f  %.2f %7.2f%%  %3d %4d %4d  %.3f"%(petal,dr,cov*100,base,add,base+add,rf))
