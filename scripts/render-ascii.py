"""Render the existing ASCII loop to static SVG frames, then encode with sharp.

Requires Python 3, Node.js, sharp, and Courier New/Courier fonts. Run:
  python3 scripts/render-ascii.py
  node scripts/encode-ascii.cjs

The stdlib generator remains the source of truth. This samples its original
timing, particle interpolation, glyph textures, and moving background mask.
"""
from pathlib import Path
from html import escape
import importlib.util
import math
import json

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ascii_source', ROOT/'scripts/build-ascii.py')
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)
OUT = ROOT/'.ascii-frames'
FPS = 32
COUNT = round(source.DURATION*FPS)

def ease(progress):
    lo, hi = 0., 1.
    for _ in range(24):
        t = (lo+hi)/2
        x = 3*(1-t)**2*t*.42 + 3*(1-t)*t*t*.58 + t**3
        if x < progress: lo = t
        else: hi = t
    t = (lo+hi)/2
    return 3*(1-t)*t*t+t**3

def morph_progress(time):
    if source.MORPH_START <= time < source.NAME_START:
        return ease((time-source.MORPH_START)/(source.NAME_START-source.MORPH_START))
    if source.NAME_START <= time < source.NAME_END: return 1
    if source.NAME_END <= time < source.MORPH_END:
        return 1-ease((time-source.NAME_END)/(source.MORPH_END-source.NAME_END))
    return 0

def name_offset(time, letter):
    # The original SVG interpolates the 28 motion samples linearly.
    p = (time-source.NAME_START)/(source.NAME_END-source.NAME_START)
    sample = p*(source.NAME_FRAMES-1)
    i = min(source.NAME_FRAMES-2, int(sample))
    blend = sample-i
    a = source.name_motion(i/(source.NAME_FRAMES-1),letter)
    b = source.name_motion((i+1)/(source.NAME_FRAMES-1),letter)
    return tuple(x+(y-x)*blend for x,y in zip(a,b))

def foreground(time):
    if time < source.MORPH_START or time >= source.MORPH_END:
        active = time if time < source.MORPH_START else source.MORPH_START+time-source.MORPH_END
        index = min(source.SPIN_FRAMES-1,int(active/source.SPIN_SECONDS*source.SPIN_FRAMES+1e-9))
        return source.ascii_rows(source.KNOTS[index],source.WIDTH/2-source.COLS*source.CELL*.3,
                                 source.HEIGHT/2-source.ROWS*source.CELL/2,source.CELL)
    positions, glyphs = [], []
    for i,(sx,sy,tx,ty,_,_,ch) in enumerate(source.PARTICLES):
        if source.NAME_START <= time < source.NAME_END:
            dx,dy = name_offset(time,source.letter_of(tx))
            x,y = tx+dx,ty+dy
            if source.NAME_START+.125 <= time < source.NAME_END-.125:
                texture = int((time % .5)/.125+1e-9) % 4
                ch = source.name_char(i,texture+1)
        else:
            p = morph_progress(time)
            x,y = sx+p*(tx-sx),sy+p*(ty-sy)
        positions.append((x,y))
        glyphs.append(ch)
    # Individual positioned glyphs avoid renderer differences for SVG x/y lists.
    return ''.join(f'<text font-size="{source.CELL}" x="{x:.4f}" y="{y:.4f}">{escape(ch)}</text>'
                   for (x,y),ch in zip(positions,glyphs))

def still(ink,field):
    glyphs = ''.join(f'<text font-size="{source.CELL}" x="{p[2]:.4f}" y="{p[3]:.4f}">{escape(p[-1])}</text>'
                     for p in source.PARTICLES)
    return document(310,ink,field,source.FIELDS[0],glyphs,.6)

def document(rx,ink,field,rows,form,opacity=1):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="864" height="200" viewBox="0 0 864 200">
<defs><radialGradient id="halo"><stop offset="0" stop-color="black"/><stop offset=".45" stop-color="black"/><stop offset="1" stop-color="white"/></radialGradient><mask id="depth"><rect width="864" height="200" fill="white"/><ellipse cx="432" cy="100" rx="{rx:.4f}" ry="112" fill="url(#halo)"/></mask></defs>
<g font-family="{source.FONT}"><g fill="{field}" mask="url(#depth)" opacity="{opacity}">{source.ascii_rows(rows,0,8,10)}</g><g fill="{ink}">{form}</g></g></svg>'''

def main():
    for theme,ink,field in [('dark','#e6edf3','#35404c'),('light','#171717','#c3cad1')]:
        folder = OUT/theme
        folder.mkdir(parents=True,exist_ok=True)
        for i in range(COUNT):
            time = i/FPS
            rows = source.FIELDS[min(39,int(time/source.DURATION*40+1e-9))]
            svg = document(155+155*morph_progress(time),ink,field,rows,foreground(time))
            (folder/f'{i:04}.svg').write_text(svg)
        (folder/'still.svg').write_text(still(ink,field))
    (OUT/'timing.json').write_text(json.dumps({
        'width':864,'height':200,'fps':FPS,'count':COUNT,
        'delay':[round((i+1)*1000/FPS)-round(i*1000/FPS) for i in range(COUNT)]
    }))
    print(f'Rendered {COUNT} frames per theme; {source.DURATION} seconds at {FPS} FPS.')

if __name__ == '__main__': main()
