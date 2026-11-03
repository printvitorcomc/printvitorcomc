"""Build the profile's ASCII knot and moving interference field. No dependencies."""
from pathlib import Path
from html import escape
import math

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 864, 200
COUNT, DURATION = 40, 16
COLS, ROWS, CELL = 76, 30, 7.5
RAMP = ' .,:;irsXA253hMHGS#9B@'

def add(a, b): return tuple(x + y for x, y in zip(a, b))
def mul(a, k): return tuple(x * k for x in a)
def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def unit(a): return mul(a, 1 / math.sqrt(sum(x*x for x in a)))

surface = []
for n in range(640):
    t = math.tau * n / 640
    p = (math.sin(t)+2*math.sin(2*t), math.cos(t)-2*math.cos(2*t), -math.sin(3*t))
    tangent = unit((math.cos(t)+4*math.cos(2*t), -math.sin(t)+4*math.sin(2*t), -3*math.cos(3*t)))
    normal = unit(cross(tangent, (0, 0, 1)))
    binormal = unit(cross(tangent, normal))
    for m in range(24):
        a = math.tau * m / 24
        face = add(mul(normal, math.cos(a)), mul(binormal, math.sin(a)))
        surface.append((add(p, mul(face, .36)), face))

def rotate(p, angle):
    x, y, z = p
    tilt = .72
    y, z = y*math.cos(tilt)-z*math.sin(tilt), y*math.sin(tilt)+z*math.cos(tilt)
    return x*math.cos(angle)+z*math.sin(angle), y, -x*math.sin(angle)+z*math.cos(angle)

# Fit every orientation inside the shorter banner, using a fixed camera.
extent = 0
for i in range(COUNT):
    angle = math.tau * i / COUNT + .25
    for pos, _ in surface:
        x, y, z = rotate(pos, angle)
        extent = max(extent, abs(y / (7.5 + z)))
SCALE = 85 / extent

def knot(index):
    chars = [[' '] * COLS for _ in range(ROWS)]
    depth = [[-999.] * COLS for _ in range(ROWS)]
    light = unit((-.45, -.6, -1))
    angle = math.tau * index / COUNT + .25
    for pos, norm in surface:
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
    phase = math.tau * index / COUNT
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

def text_rows(rows, x, y, step):
    return ''.join(f'<tspan x="{x:g}" y="{y+n*step:.2f}">{escape(row)}</tspan>'
                   for n, row in enumerate(rows) if row.strip())

knots = [knot(i) for i in range(COUNT)]
fields = [interference(i) for i in range(COUNT)]

def scene(index, ink, field):
    background = text_rows(fields[index], 0, 8, 10)
    foreground = text_rows(knots[index], WIDTH/2-COLS*CELL*.3, HEIGHT/2-ROWS*CELL/2, CELL)
    return (f'<text xml:space="preserve" font-family="Courier New, Courier, monospace" '
            f'font-size="10" fill="{field}" mask="url(#depth)">{background}</text>'
            f'<text xml:space="preserve" font-family="Courier New, Courier, monospace" '
            f'font-size="{CELL}" fill="{ink}">{foreground}</text>')

for theme, paper, ink, field in [
    ('dark', '#0d1117', '#e6edf3', '#35404c'),
    ('light', '#ffffff', '#171717', '#c3cad1'),
]:
    prefix = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" role="img" aria-labelledby="title desc">
<title id="title">Nó ASCII em um campo de interferência</title>
<desc id="desc">Uma forma tridimensional central gira sobre ondas de caracteres que se movem em sentidos opostos, criando uma ilusão de profundidade.</desc>
<defs><radialGradient id="halo"><stop offset="0" stop-color="black"/><stop offset=".45" stop-color="black"/><stop offset="1" stop-color="white"/></radialGradient><mask id="depth"><rect width="864" height="200" fill="white"/><ellipse cx="432" cy="100" rx="155" ry="112" fill="url(#halo)"/></mask></defs>
<rect width="{WIDTH}" height="{HEIGHT}" fill="{paper}"/>
'''
    style = f'''<style>.frame{{opacity:0;animation:frame {DURATION}s step-end infinite}}.f0{{opacity:1}}@keyframes frame{{0%{{opacity:1}}{100/COUNT:g}%,100%{{opacity:0}}}}@media(prefers-reduced-motion:reduce){{.frame{{animation:none;opacity:0}}.f0{{opacity:1}}}}</style>'''
    groups = [f'<g class="frame f{i}" style="animation-delay:{i*DURATION/COUNT:.2f}s">{scene(i, ink, field)}</g>' for i in range(COUNT)]
    (ROOT/'assets'/f'ascii-depth-{theme}.svg').write_text(prefix + style + ''.join(groups) + '</svg>\n')
    preview_dir = ROOT/'previews'
    if preview_dir.exists():
        for i in range(COUNT):
            (preview_dir/f'{theme}-{i:02}.svg').write_text(prefix + scene(i, ink, field) + '</svg>\n')
