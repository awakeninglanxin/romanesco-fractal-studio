# -*- coding: utf-8 -*-
"""纯标准库 PNG 解码 + 像素统计：把山体染成品红，数"露底像素"占比。
   为什么不用肉眼：品红像素数是可复现的客观量，能直接对比"改前/改后"。
   用法: python _pngstat.py a.png [b.png ...]"""
import zlib, sys

def read_png(path):
    data=open(path,'rb').read()
    assert data[:8]==b'\x89PNG\r\n\x1a\n', 'not png'
    pos=8; idat=b''; w=h=ct=bd=None
    while pos<len(data):
        ln=int.from_bytes(data[pos:pos+4],'big'); typ=data[pos+4:pos+8]
        chunk=data[pos+8:pos+8+ln]; pos+=12+ln
        if typ==b'IHDR':
            w=int.from_bytes(chunk[0:4],'big'); h=int.from_bytes(chunk[4:8],'big')
            bd=chunk[8]; ct=chunk[9]
        elif typ==b'IDAT': idat+=chunk
        elif typ==b'IEND': break
    raw=zlib.decompress(idat)
    ch={0:1,2:3,4:2,6:4}[ct]
    assert bd==8, 'only 8bit'
    stride=w*ch; out=bytearray(h*stride); prev=bytearray(stride); p=0
    for y in range(h):
        f=raw[p]; p+=1
        line=bytearray(raw[p:p+stride]); p+=stride
        if f==1:
            for i in range(ch,stride): line[i]=(line[i]+line[i-ch])&255
        elif f==2:
            for i in range(stride): line[i]=(line[i]+prev[i])&255
        elif f==3:
            for i in range(stride):
                a=line[i-ch] if i>=ch else 0
                line[i]=(line[i]+((a+prev[i])>>1))&255
        elif f==4:
            for i in range(stride):
                a=line[i-ch] if i>=ch else 0
                b=prev[i]; c=prev[i-ch] if i>=ch else 0
                pp=a+b-c; pa=abs(pp-a); pb=abs(pp-b); pc=abs(pp-c)
                pr=a if (pa<=pb and pa<=pc) else (b if pb<=pc else c)
                line[i]=(line[i]+pr)&255
        out[y*stride:(y+1)*stride]=line; prev=line
    return w,h,ch,out

def magenta_stats(path, box=None):
    w,h,ch,px=read_png(path)
    x0,y0,x1,y1 = box or (0,0,w,h)
    tot=0; mag=0; near=0
    for y in range(y0,y1):
        base=y*w*ch
        for x in range(x0,x1):
            i=base+x*ch
            r=px[i]; g=px[i+1]; b=px[i+2]
            tot+=1
            if r>225 and b>225 and g<70: mag+=1
            elif r>170 and b>170 and g<120 and abs(r-b)<40: near+=1
    return dict(w=w,h=h,total=tot,magenta=mag,mag_pct=100.0*mag/max(1,tot),loose=near)

if __name__=='__main__':
    for p in sys.argv[1:]:
        print(p, magenta_stats(p))
