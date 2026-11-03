"""Build a seamless ASCII knot -> vitorcomc -> knot loop. Python stdlib only.

Run from any directory: python3 scripts/build-ascii.py
The SVGs animate without JavaScript or external resources. Optional static preview
SVGs are written only when a previews/ directory already exists.
"""
from pathlib import Path
from html import escape
import math

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 864, 200
DURATION = 16
SPIN_FRAMES, SPIN_SECONDS = 72, 9
MORPH_START, NAME_START, NAME_END, MORPH_END = 5.5, 7.5, 10.5, 12.5
CAPTURE = 44
COLS, ROWS, CELL = 76, 30, 7.5
RAMP = ' .,:;irsXA253hMHGS#9B@'
FONT = 'Courier New, Courier, monospace'
THEMES = [('dark', '#0d1117', '#e6edf3', '#35404c'),
          ('light', '#ffffff', '#171717', '#c3cad1')]


def add(a, b): return tuple(x + y for x, y in zip(a, b))
def mul(a, k): return tuple(x * k for x in a)
def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def unit(a): return mul(a, 1 / math.sqrt(sum(x*x for x in a)))


SURFACE = []
for n in range(640):
    t = math.tau * n / 640
    p = (math.sin(t)+2*math.sin(2*t), math.cos(t)-2*math.cos(2*t), -math.sin(3*t))
    tangent = unit((math.cos(t)+4*math.cos(2*t), -math.sin(t)+4*math.sin(2*t), -3*math.cos(3*t)))
    normal = unit(cross(tangent, (0, 0, 1)))
    binormal = unit(cross(tangent, normal))
    for m in range(24):
        a = math.tau * m / 24
        face = add(mul(normal, math.cos(a)), mul(binormal, math.sin(a)))
        SURFACE.append((add(p, mul(face, .36)), face))


def rotate(p, angle):
    x, y, z = p
    tilt = .72
    y, z = y*math.cos(tilt)-z*math.sin(tilt), y*math.sin(tilt)+z*math.cos(tilt)
    return x*math.cos(angle)+z*math.sin(angle), y, -x*math.sin(angle)+z*math.cos(angle)


# The original profile camera and scale keep every orientation within the banner.
EXTENT = max(abs(rotate(p, math.tau*i/40+.25)[1] /
                 (7.5+rotate(p, math.tau*i/40+.25)[2]))
             for i in range(40) for p, _ in SURFACE)
SCALE = 85 / EXTENT


def knot(index):
    chars = [[' '] * COLS for _ in range(ROWS)]
    depth = [[-999.] * COLS for _ in range(ROWS)]
    light = unit((-.45, -.6, -1))
    angle = math.tau * index / SPIN_FRAMES + .25
    for pos, norm in SURFACE:
        x, y, z = rotate(pos, angle)
        q = 1 / (7.5 + z)
        col = round(COLS/2 + x*q*SCALE/(CELL*.6))
        row = round(ROWS/2 + y*q*SCALE/CELL)
        if 0 <= col < COLS and 0 <= row < ROWS and q > depth[row][col]:
            face = rotate(norm, angle)
            brightness = .16 + .84 * max(0, sum(a*b for a, b in zip(face, light)))
            chars[row][col] = RAMP[min(len(RAMP)-1, int(brightness*(len(RAMP)-1)))]
            depth[row][col] = q
    return [''.join(row).rstrip() for row in chars]


def interference(index):
    # Exactly the same field, palette, aspect ratio and 16 s cycle as the profile.
    phase = math.tau * index / 40
    result = []
    for row in range(20):
        line = []
        for col in range(144):
            x, y = (col-71.5)*6, (row-9.5)*10
            r1 = math.hypot(x+145, y*1.8)
            r2 = math.hypot(x-145, y*1.8)
            wave = (math.sin(r1*.065-phase) + math.sin(r2*.068+phase)) / 2
            line.append(' .:+='[min(4, max(0, round((wave+1)*2)))])
        result.append(''.join(line).rstrip())
    return result


# Small lower-case letterforms; each lit pixel is made of real ASCII characters.
LETTERS = {
    'v': ['00000', '00000', '10001', '10001', '10001', '01010', '00100'],
    'i': ['00100', '00000', '01100', '00100', '00100', '00100', '01110'],
    't': ['01000', '01000', '11110', '01000', '01000', '01001', '00110'],
    'o': ['00000', '00000', '01110', '10001', '10001', '10001', '01110'],
    'r': ['00000', '00000', '10110', '11001', '10000', '10000', '10000'],
    'c': ['00000', '00000', '01111', '10000', '10000', '10000', '01111'],
    'm': ['00000', '00000', '11010', '10101', '10101', '10101', '10101'],
}


def name_points():
    points = []
    for letter_index, letter in enumerate('vitorcomc'):
        for row, bits in enumerate(LETTERS[letter]):
            for col, bit in enumerate(bits):
                if bit == '1':
                    for dy in range(2):
                        for dx in range(2):
                            points.append(((letter_index*12 + col*2 + dx)*CELL*.6,
                                           (row*2+dy)*CELL))
    center_x = (min(x for x, _ in points)+max(x for x, _ in points))/2
    center_y = (min(y for _, y in points)+max(y for _, y in points))/2
    return sorted([(x-center_x+WIDTH/2-CELL*.3, y-center_y+HEIGHT/2+CELL*.3)
                   for x, y in points])


KNOTS = [knot(i) for i in range(SPIN_FRAMES)]
FIELDS = [interference(i) for i in range(40)]
NAME = name_points()
SOURCE = sorted([(WIDTH/2-COLS*CELL*.3+col*CELL*.6,
                  HEIGHT/2-ROWS*CELL/2+row*CELL, ch)
                 for row, line in enumerate(KNOTS[CAPTURE])
                 for col, ch in enumerate(line) if ch != ' '])
assert len(NAME) >= len(SOURCE)

# Sorting and quantile matching make the narrow knot expand into the word rather
# than sending random particles across the entire banner. Duplicate source points
# coincide exactly at each handoff, so the silhouette never flashes or disappears.
PARTICLES = []
for i, (tx, ty) in enumerate(NAME):
    sx, sy, ch = SOURCE[i*len(SOURCE)//len(NAME)]
    dx, dy = tx-sx, ty-sy
    bend = 22*math.sin(i*2.3999632297)
    cx, cy = dx/2 + 8*math.cos(i*.71), dy/2+bend
    PARTICLES.append((sx, sy, tx, ty, cx, cy, ch))


def number(value):
    return f'{value:.6f}'.rstrip('0').rstrip('.')


def text_rows(rows, x, y, step):
    return ''.join(f'<tspan x="{number(x)}" y="{number(y+n*step)}">{escape(row)}</tspan>'
                   for n, row in enumerate(rows) if row.strip())


def ascii_rows(rows, x, y, step):
    return f'<text xml:space="preserve" font-size="{number(step)}">{text_rows(rows,x,y,step)}</text>'


def window(start, end):
    times, values = [0], [1 if start == 0 else 0]
    if start:
        times.append(start/DURATION)
        values.append(1)
    if end < DURATION:
        times.append(end/DURATION)
        values.append(0)
    times.append(1)
    values.append(values[0])
    return (f'<animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" '
            f'calcMode="discrete" keyTimes="{";".join(number(t) for t in times)}" '
            f'values="{";".join(map(str,values))}"/>')


def morph():
    times = ';'.join(number(t/DURATION) for t in (0, MORPH_START, NAME_START, NAME_END, MORPH_END, DURATION))
    timing = (f'dur="{DURATION}s" repeatCount="indefinite" calcMode="spline" '
              f'keyPoints="0;0;1;1;0;0" keyTimes="{times}" '
              'keySplines="0 0 1 1;.42 0 .58 1;0 0 1 1;.42 0 .58 1;0 0 1 1"')
    result = []
    for sx, sy, tx, ty, cx, cy, ch in PARTICLES:
        path = f'M0 0Q{number(cx)} {number(cy)} {number(tx-sx)} {number(ty-sy)}'
        result.append(f'<text x="{number(sx)}" y="{number(sy)}">{escape(ch)}'
                      f'<animateMotion path="{path}" {timing}/></text>')
    return f'<g opacity="0" font-size="{CELL}">{window(MORPH_START,MORPH_END)}{"".join(result)}</g>'


def prefix(paper, static=False):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" role="img" aria-labelledby="title desc">
<title id="title">vitorcomc — holograma ASCII</title>
<desc id="desc">Um nó tridimensional gira, seus caracteres se reorganizam no nome vitorcomc e retornam ao nó, em um ciclo contínuo sobre ondas ASCII.</desc>
<defs><radialGradient id="halo"><stop offset="0" stop-color="black"/><stop offset=".45" stop-color="black"/><stop offset="1" stop-color="white"/></radialGradient><mask id="depth"><rect width="864" height="200" fill="white"/><ellipse cx="432" cy="100" rx="155" ry="112" fill="url(#halo)">{'' if static else f'<animate attributeName="rx" values="155;155;310;310;155;155" keyTimes="0;.34375;.46875;.65625;.78125;1" dur="{DURATION}s" repeatCount="indefinite" calcMode="spline" keySplines="0 0 1 1;.42 0 .58 1;0 0 1 1;.42 0 .58 1;0 0 1 1"/>'}</ellipse></mask></defs>
<rect width="{WIDTH}" height="{HEIGHT}" fill="{paper}"/>
'''


def static_scene(time, ink, field):
    time %= DURATION
    progress = 0
    if MORPH_START <= time < NAME_START:
        progress = (time-MORPH_START)/(NAME_START-MORPH_START)
    elif NAME_START <= time < NAME_END:
        progress = 1
    elif NAME_END <= time < MORPH_END:
        progress = 1-(time-NAME_END)/(MORPH_END-NAME_END)
    # For static previews, use the same cubic timing as SVG's .42 0 .58 1.
    lo, hi = 0., 1.
    for _ in range(24):
        t = (lo+hi)/2
        v = 3*(1-t)**2*t*.42 + 3*(1-t)*t*t*.58 + t**3
        if v < progress: lo = t
        else: hi = t
    t = (lo+hi)/2
    p = 3*(1-t)*t*t+t**3
    background = ascii_rows(interference(time/DURATION*40),0,8,10)
    result = f'<g font-family="{FONT}"><g fill="{field}" mask="url(#depth)">{background}</g><g fill="{ink}">'
    if time < MORPH_START or time >= MORPH_END:
        active = time if time < MORPH_START else MORPH_START+time-MORPH_END
        frame = min(SPIN_FRAMES-1, int(active/SPIN_SECONDS*SPIN_FRAMES))
        result += ascii_rows(KNOTS[frame],WIDTH/2-COLS*CELL*.3,HEIGHT/2-ROWS*CELL/2,CELL)
    else:
        for sx, sy, tx, ty, cx, cy, ch in PARTICLES:
            # Quadratic trajectories. SMIL paces these by arc length; the still
            # previews approximate position along each curve for easy review.
            x = sx+2*(1-p)*p*cx+p*p*(tx-sx)
            y = sy+2*(1-p)*p*cy+p*p*(ty-sy)
            result += f'<text font-size="{CELL}" x="{number(x)}" y="{number(y)}">{escape(ch)}</text>'
    return result+'</g></g>'


def build():
    (ROOT/'assets').mkdir(exist_ok=True)
    for theme, paper, ink, field in THEMES:
        result = prefix(paper)
        result += '<defs><mask id="still-depth"><rect width="864" height="200" fill="white"/><ellipse cx="432" cy="100" rx="310" ry="112" fill="url(#halo)"/></mask></defs>'
        result += '<style>.still{display:none}@media(prefers-reduced-motion:reduce){.animated{display:none}.still{display:inline}}</style>'
        result += f'<g font-family="{FONT}">'
        result += f'<g class="animated"><g fill="{field}" mask="url(#depth)">'
        for i, rows in enumerate(FIELDS):
            result += f'<g opacity="{int(i==0)}">{window(i*.4,(i+1)*.4)}{ascii_rows(rows,0,8,10)}</g>'
        result += f'</g><g fill="{ink}">'
        for i, rows in enumerate(KNOTS):
            start = i*SPIN_SECONDS/SPIN_FRAMES
            if i >= CAPTURE: start += MORPH_END-MORPH_START
            result += (f'<g opacity="{int(i==0)}">{window(start,start+SPIN_SECONDS/SPIN_FRAMES)}'
                       f'{ascii_rows(rows,WIDTH/2-COLS*CELL*.3,HEIGHT/2-ROWS*CELL/2,CELL)}</g>')
        result += morph()+'</g></g>'
        # Reduced motion: a legible, static name; no CSS or SMIL motion is visible.
        result += f'<g class="still"><g fill="{field}" opacity=".6" mask="url(#still-depth)">{ascii_rows(FIELDS[0],0,8,10)}</g><g fill="{ink}" font-size="{CELL}">'
        for _, _, tx, ty, _, _, ch in PARTICLES:
            result += f'<text x="{number(tx)}" y="{number(ty)}">{escape(ch)}</text>'
        result += '</g></g></g></svg>\n'
        path = ROOT/'assets'/f'ascii-morph-{theme}.svg'
        path.write_text(result)
        print(f'{path.name}: {len(result.encode()):,} bytes; {len(PARTICLES)} particles; {DURATION} s')
        preview = ROOT/'previews'
        if preview.exists():
            for time in (0, 5.5, 6.5, 8.5, 11.5, 12.5, 15.875, 16):
                (preview/f'{theme}-{time:06.3f}.svg').write_text(prefix(paper,static=True)+static_scene(time,ink,field)+'</svg>\n')


if __name__ == '__main__':
    build()
