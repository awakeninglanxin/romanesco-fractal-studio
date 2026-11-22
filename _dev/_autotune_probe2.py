# -*- coding: utf-8 -*-
"""评分器标定 2：改用"径向边界"判越界（顶点方向合法外伸），并扫补株半径。"""
import math
def reg_poly(n,R,off):
    return [(R*math.cos(off+2*math.pi*k/n), R*math.sin(off+2*math.pi*k/n)) for k in range(n)]
def inside(pts,x,z):
    s=0
    for i in range(len(pts)):
        a=pts[i]; b=pts[(i+1)%len(pts)]
        cr=(b[0]-a[0])*(z-a[1])-(b[1]-a[1])*(x-a[0])
        if cr>1e-10:
            if s<0: return False
            s=1
        elif cr<-1e-10:
            if s>0: return False
            s=-1
    return True
def samples(pts,nv):
    xs=[p[0] for p in pts]; zs=[p[1] for p in pts]
    x0,x1,z0,z1=min(xs),max(xs),min(zs),max(zs); out=[]
    for a in range(nv+1):
        for b in range(nv+1):
            x=x0+(x1-x0)*a/nv; z=z0+(z1-z0)*b/nv
            if inside(pts,x,z): out.append((x,z))
    return out
def hit(q,ringK,x,z):
    dx=x-q['x']; dz=z-q['z']; b=q['b']
    if q.get('single'): return dx*dx+dz*dz<=b*b
    if dx*dx+dz*dz<=b*b: return True
    ring=ringK*b
    for s in range(6):
        a=q.get('spin',0)+s*math.pi/3
        ex=dx-ring*math.cos(a); ez=dz-ring*math.sin(a)
        if ex*ex+ez*ez<=b*b: return True
    return False
def cover(sm,fl,ringK):
    n=0
    for (x,z) in sm:
        for q in fl:
            if hit(q,ringK,x,z): n+=1; break
    return n/len(sm)
def hex_flowers(e,r,ring,rMid):
    fl=[{'x':ring*math.cos(2*math.pi*k/6),'z':ring*math.sin(2*math.pi*k/6),'b':r/3} for k in range(6)]
    fl.append({'x':0,'z':0,'b':rMid/3}); return fl
def pent_flowers(e,r,rcF,gap):
    S36=math.sin(math.pi/5); ring=r/S36; rc=r*rcF
    fl=[{'x':ring*math.cos(math.pi/2+2*math.pi*k/5),'z':ring*math.sin(math.pi/2+2*math.pi*k/5),'b':r/3} for k in range(5)]
    fl.append({'x':0,'z':0,'b':rc/3})
    if gap:
        inPent=0.688*e; gapD=max(0.05*e,inPent-rc); rEdge=gapD*0.62; pos=(rc+inPent)*0.5
        for k in range(5):
            a=math.pi/2+math.pi/5+2*math.pi*k/5
            fl.append({'x':pos*math.cos(a),'z':pos*math.sin(a),'b':rEdge,'single':True})
    return fl

def boundary_r(pts):
    """给定多边形，返回函数 r_b(phi)=该方向上的边界半径（凸多边形射线求交）。"""
    n=len(pts)
    def f(phi):
        dx,dz=math.cos(phi),math.sin(phi)
        best=1e9
        for i in range(n):
            ax,az=pts[i]; bx,bz=pts[(i+1)%n]
            ex,ez=bx-ax,bz-az
            den=dx*ez-dz*ex
            if abs(den)<1e-12: continue
            t=((ax)*ez-az*ex)/den          # 射线参数
            u=(dx*(az)-dz*(ax))/den        # 线段参数 0..1
            if t>0 and -1e-9<=u<=1+1e-9: best=min(best,t)
        return best
    return f

def radial_out(fl,ringK,pts):
    rb=boundary_r(pts); m=-1e9
    for q in fl:
        ext=q['b'] if q.get('single') else q['b']*(ringK+1)
        phi=math.atan2(q['z'],q['x'])
        m=max(m,ext-rb(phi))
    return m

e=1.0
H=reg_poly(6,e,0); P=reg_poly(5,e/(2*math.sin(math.pi/5)),math.pi/2)
smH=samples(H,44); smP=samples(P,44)

print('== 六边形面（径向越界 ≤0.005e）：覆盖率 / 盘半径')
rows=[]
for r in (0.56,0.60,0.64,0.68,0.72,0.76):
    for ring in (0.54,0.58,0.62,0.66):
        for mid in (0.20,0.24,0.28,0.32):
            for rk in (2.0,1.85,1.7):
                fl=hex_flowers(e,r*e,ring*e,mid*e)
                c=cover(smH,fl,rk); o=radial_out(fl,rk,H)
                rows.append((c,o,r,ring,mid,rk))
ok=[x for x in rows if x[1]<=0.005]
print(' 可行',len(ok),'/',len(rows))
for x in sorted(ok,key=lambda t:(-t[0],t[2]))[:10]:
    print('  cov %.4f out %+.3f r%.2f ring%.2f mid%.2f rk%.2f'%x)

print('\n== 五边形面（径向越界 ≤0.005e）')
rows=[]
for r in (0.44,0.48,0.52,0.56,0.60,0.64):
    for rcF in (0.85,0.95,1.05,1.15):
        for gap in (0,1):
            fl=pent_flowers(e,r*e,rcF,gap)
            c=cover(smP,fl,2.0); o=radial_out(fl,2.0,P)
            rows.append((c,o,r,rcF,gap))
ok=[x for x in rows if x[1]<=0.005]
print(' 可行',len(ok),'/',len(rows))
for x in sorted(ok,key=lambda t:(-t[0],t[2]))[:10]:
    print('  cov %.4f out %+.3f r%.2f rc%.2f gap%d'%x)

print('\n== 正五边形相切（径向越界 ≤0.005e，补缝半径倍数扫描）')
def tangent2(e,rtF,rcF,gapRad):
    rt=rtF*e; ring=rt/math.sin(math.pi/5); rc=rt*rcF
    fl=[{'x':ring*math.cos(math.pi/2+2*math.pi*k/5),'z':ring*math.sin(math.pi/2+2*math.pi*k/5),'b':rt/3} for k in range(5)]
    fl.append({'x':0,'z':0,'b':rc/3})
    if gapRad>0:
        inPent=0.688*e; gapD=max(0.05*e,inPent-rc); rEdge=gapD*gapRad; pos=(rc+inPent)*0.5
        for k in range(5):
            a=math.pi/2+math.pi/5+2*math.pi*k/5
            fl.append({'x':pos*math.cos(a),'z':pos*math.sin(a),'b':rEdge,'single':True})
    return fl
rows=[]
for rtF in (0.285,0.30,0.315,0.325):
    for rcF in (0.70,0.85,1.00,1.15,1.30):
        for gr in (0,0.62,0.75,0.90,1.05):
            fl=tangent2(e,rtF,rcF,gr)
            c=cover(smP,fl,2.0); o=radial_out(fl,2.0,P)
            rows.append((c,o,rtF,rcF,gr))
ok=[x for x in rows if x[1]<=0.005]
print(' 可行',len(ok),'/',len(rows))
for x in sorted(ok,key=lambda t:(-t[0],-t[2]))[:10]:
    print('  cov %.4f out %+.3f rt%.3f rc%.2f gapR%.2f'%x)

print('\n== 直立花盘：交错相位 + 重心补株（目标 ≥99.5%）')
SQ3=math.sqrt(3)
def up(i_sp,i_rk,alt,i_fk):
    b=1/3; d=2*i_sp; hf=math.pi/6 if alt else 0
    tri=[(0,0),(d,0),(d/2,d*SQ3/2)]
    sm=samples(tri,44)
    fl=[{'x':0,'z':0,'b':b},{'x':d,'z':0,'b':b,'spin':hf},{'x':d/2,'z':d*SQ3/2,'b':b,'spin':hf}]
    if i_fk: fl.append({'x':d/2,'z':d*SQ3/6,'b':b*i_fk})
    return cover(sm,fl,i_rk)
for sp in (1.00,0.96,0.92,0.88):
    for rk in (2.0,1.85,1.70):
        for fk in (0,0.6,0.75,0.9,1.05,1.2):
            c=up(sp,rk,1,fk)
            if c>=0.995:
                print('  sp %.2f rk %.2f fill %.2f → %.2f%%'%(sp,rk,fk,c*100)); break
