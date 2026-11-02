from pathlib import Path
from html import escape
import math

ROOT = Path(__file__).resolve().parents[1]
W, H, COUNT = 64, 30, 40
RAMP = ' .,:;irsXA253hMHGS#9B@'

def add(a,b): return tuple(x+y for x,y in zip(a,b))
def mul(a,k): return tuple(x*k for x in a)
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(a): return mul(a,1/math.sqrt(sum(x*x for x in a)))

surface=[]
for n in range(640):
    t=math.tau*n/640
    p=(math.sin(t)+2*math.sin(2*t),math.cos(t)-2*math.cos(2*t),-math.sin(3*t))
    tangent=unit((math.cos(t)+4*math.cos(2*t),-math.sin(t)+4*math.sin(2*t),-3*math.cos(3*t)))
    normal=unit(cross(tangent,(0,0,1)))
    binormal=unit(cross(tangent,normal))
    for m in range(24):
        a=math.tau*m/24
        face=add(mul(normal,math.cos(a)),mul(binormal,math.sin(a)))
        surface.append((add(p,mul(face,.36)),face))

def rotate(p,angle):
    x,y,z=p
    tilt=.72
    y,z=y*math.cos(tilt)-z*math.sin(tilt),y*math.sin(tilt)+z*math.cos(tilt)
    x,z=x*math.cos(angle)+z*math.sin(angle),-x*math.sin(angle)+z*math.cos(angle)
    return x,y,z

def frame(index):
    chars=[[' ']*W for _ in range(H)]
    depth=[[-999.]*W for _ in range(H)]
    light=unit((-.45,-.6,-1))
    angle=math.tau*index/COUNT+.25
    for pos,norm in surface:
        x,y,z=rotate(pos,angle)
        q=1/(7.5+z)
        col=round(W/2+x*q*62)
        row=round(H/2+y*q*37.2)
        if 0<=col<W and 0<=row<H and q>depth[row][col]:
            nx,ny,nz=rotate(norm,angle)
            luminosity=.16+.84*max(0,nx*light[0]+ny*light[1]+nz*light[2])
            chars[row][col]=RAMP[min(len(RAMP)-1,int(luminosity*(len(RAMP)-1)))]
            depth[row][col]=q
    return [''.join(row).rstrip() for row in chars]

frames=[frame(i) for i in range(COUNT)]
(ROOT/'ascii-frame.txt').write_text('\n'.join(frames[0])+'\n')

for theme,bg,fg,muted,line in [('dark','#0d1117','#e6edf3','#7d8590','#30363d'),('light','#ffffff','#171717','#656563','#deded9')]:
    chunks=[]
    for i,rows in enumerate(frames):
        lines=''.join(f'<tspan x="456" y="{30+n*9.2:.1f}">{escape(row)}</tspan>' for n,row in enumerate(rows) if row.strip())
        chunks.append(f'<g class="frame f{i}" style="animation-delay:{i*.3:.1f}s"><text xml:space="preserve" font-family="Courier New, Courier, monospace" font-size="9.2" fill="{fg}">{lines}</text></g>')
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 864 320" width="864" height="320" role="img" aria-labelledby="title desc">
<title id="title">vitorcomc — ASCII</title><desc id="desc">Um nó tridimensional feito de caracteres gira lentamente. Representa a conexão entre sistemas.</desc>
<rect width="864" height="320" fill="{bg}"/>
<path d="M32 36H52M32 36V56M832 264V284H812" fill="none" stroke="{line}"/>
<text x="32" y="167" font-family="Courier New, Courier, monospace" font-size="51" font-weight="700" letter-spacing="-2" fill="{fg}">vitorcomc<tspan fill="{muted}">_</tspan></text>
<style>.frame{{opacity:0;animation:frame 12s step-end infinite}}.f0{{opacity:1}}@keyframes frame{{0%{{opacity:1}}2.5%,100%{{opacity:0}}}}@media(prefers-reduced-motion:reduce){{.frame{{animation:none;opacity:0}}.f0{{opacity:1}}}}</style>
{''.join(chunks)}
</svg>
'''
    (ROOT/'assets'/f'ascii-{theme}.svg').write_text(svg)
