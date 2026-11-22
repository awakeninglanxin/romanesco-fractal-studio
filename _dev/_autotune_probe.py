# -*- coding: utf-8 -*-
"""一键最优评分器的离线标定：把网页里的 flowerHit/coverFrac 原样复刻，扫参数地形。"""
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
    x0,x1,z0,z1=min(xs),max(xs),min(zs),max(zs)
    out=[]
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

def maxout(fl,ringK,pts):
    m=-1e9
    for q in fl:
        md=1e9
        for i in range(len(pts)):
            a=pts[i]; b=pts[(i+1)%len(pts)]
            ex=b[0]-a[0]; ez=b[1]-a[1]; L=math.hypot(ex,ez) or 1
            d=(ex*(q['z']-a[1])-ez*(q['x']-a[0]))/L
            md=min(md,d)
        ext=q['b'] if q.get('single') else q['b']*(ringK+1)
        m=max(m,ext-md)
    return m

def hex_flowers(e,r,ring,rMid):
    fl=[{'x':ring*math.cos(2*math.pi*k/6),'z':ring*math.sin(2*math.pi*k/6),'b':r/3} for k in range(6)]
    fl.append({'x':0,'z':0,'b':rMid/3})
    return fl

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

def tangent_flowers(e,rtF,rcF,gap):
    rt=rtF*e; ring=rt/math.sin(math.pi/5); rc=rt*rcF
    fl=[{'x':ring*math.cos(math.pi/2+2*math.pi*k/5),'z':ring*math.sin(math.pi/2+2*math.pi*k/5),'b':rt/3} for k in range(5)]
    fl.append({'x':0,'z':0,'b':rc/3})
    if gap:
        inPent=0.688*e; gapD=max(0.05*e,inPent-rc); rEdge=gapD*0.62; pos=(rc+inPent)*0.5
        for k in range(5):
            a=math.pi/2+math.pi/5+2*math.pi*k/5
            fl.append({'x':pos*math.cos(a),'z':pos*math.sin(a),'b':rEdge,'single':True})
    return fl

e=1.0
H=reg_poly(6,e,0); P=reg_poly(5,e/(2*math.sin(math.pi/5)),math.pi/2)
smH=samples(H,44); smP=samples(P,44)
print('== 正60面体 · 六边形面（目标：覆盖 100%、越界 ≤0.02e）')
rows=[]
for r in (0.62,0.66,0.70,0.74,0.78):
    for ring in (0.56,0.60,0.64,0.68):
        for mid in (0.22,0.26,0.30,0.34):
            for rk in (2.0,1.85,1.7):
                fl=hex_flowers(e,r*e,ring*e,mid*e)
                c=cover(smH,fl,rk); o=maxout(fl,rk,H)
                rows.append((c,o,r,ring,mid,rk))
ok=[x for x in rows if x[1]<=0.02]
print(' 可行组合',len(ok),'/',len(rows))
for x in sorted(ok,key=lambda t:(-t[0],t[1]))[:6]: print('  cov %.4f out %+.3f r%.2f ring%.2f mid%.2f rk%.2f'%x)
print(' 无约束时覆盖率前 6:')
for x in sorted(rows,key=lambda t:-t[0])[:6]: print('  cov %.4f out %+.3f r%.2f ring%.2f mid%.2f rk%.2f'%x)

print('\n== 正60面体 · 五边形面（越界 ≤0.02e）')
rows=[]
for r in (0.44,0.48,0.52,0.56,0.60):
    for rcF in (0.85,0.95,1.05,1.15):
        for gap in (0,1):
            fl=pent_flowers(e,r*e,rcF,gap)
            c=cover(smP,fl,2.0); o=maxout(fl,2.0,P)
            rows.append((c,o,r,rcF,gap))
ok=[x for x in rows if x[1]<=0.02]
print(' 可行',len(ok),'/',len(rows))
for x in sorted(ok,key=lambda t:(-t[0],t[1]))[:8]: print('  cov %.4f out %+.3f r%.2f rc%.2f gap%d'%x)

print('\n== 正五边形 · 相切平铺')
rows=[]
for rtF in (0.285,0.30,0.315,0.33):
    for rcF in (0.70,0.85,1.00,1.15):
        for gap in (0,1):
            fl=tangent_flowers(e,rtF,rcF,gap)
            c=cover(smP,fl,2.0); o=maxout(fl,2.0,P)
            rows.append((c,o,rtF,rcF,gap))
for x in sorted(rows,key=lambda t:(-t[0],t[1]))[:10]: print('  cov %.4f out %+.3f rt%.3f rc%.2f gap%d'%x)

print('\n== 直立花盘：蜂窝基本胞（b=1/3, 株距 2·spread）')
SQ3=math.sqrt(3)
def up_cover(spread,ringK,alt,fillK=None):
    b=1/3; d=2*spread; hf=math.pi/6 if alt else 0
    tri=[(0,0),(d,0),(d/2,d*SQ3/2)]
    sm=samples(tri,44)
    fl=[{'x':0,'z':0,'b':b},{'x':d,'z':0,'b':b,'spin':hf},{'x':d/2,'z':d*SQ3/2,'b':b,'spin':hf}]
    if fillK: fl.append({'x':d/2,'z':d*SQ3/6,'b':b*fillK})
    return cover(sm,fl,ringK)
for sp in (1.00,0.95,0.90,0.88,0.85,0.82):
    line='sp %.2f |'%sp
    for rk in (2.0,1.85,1.70):
        line+=' rk%.2f %6.2f%%'%(rk,100*up_cover(sp,rk,0))
    print(line)
print(' 交错30°：')
for sp in (1.00,0.95,0.90,0.88,0.85):
    line='sp %.2f |'%sp
    for rk in (2.0,1.85,1.70):
        line+=' rk%.2f %6.2f%%'%(rk,100*up_cover(sp,rk,1))
    print(line)
print(' 交错30° + 重心补株：')
for sp in (1.00,0.95):
    for fk in (0.5,0.65,0.8,0.95):
        print('  sp %.2f fill %.2f → %6.2f%%'%(sp,fk,100*up_cover(sp,1.85,1,fk)))
