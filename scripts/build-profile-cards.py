"""Build the linked, theme-aware SVG cards and contact buttons for the profile.

Requires fonttools: python3 -m pip install fonttools
Typography: GitHub Mona Sans Regular/Bold, SIL Open Font License 1.1.
Source: https://github.com/github/mona-sans
Pass --font-dir with MonaSans-Regular.ttf and MonaSans-Bold.ttf.
Only used glyphs are included; integer coordinates avoid excessive SVG precision.
Card and secondary-button surfaces are transparent to follow GitHub's background.
Project copy and links live in assets/profile/projects.json.
"""
from pathlib import Path
from html import escape
import argparse
import json
import re
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT/'assets'/'profile'
THEME = '''<style>
.paper{fill:none}.line{stroke:#e6eaef}.ink{fill:#1f2328}.copy{fill:#57606a}.accent{stroke:#0969da}
.primary{fill:#1f2328;stroke:#1f2328}.primary-ink{fill:#ffffff}.primary-icon{stroke:#ffffff}
.secondary{fill:none;stroke:#8c959f}.secondary-icon{stroke:#1f2328}
@media(prefers-color-scheme:dark){.line{stroke:#252d36}.ink{fill:#e6edf3}.copy{fill:#afb8c1}.accent{stroke:#79c0ff}.primary{fill:#e6edf3;stroke:#e6edf3}.primary-ink{fill:#0d1117}.primary-icon{stroke:#0d1117}.secondary{stroke:#b1bac4}.secondary-icon{stroke:#e6edf3}}
</style>'''


def n(value):
    return f'{value:.6f}'.rstrip('0').rstrip('.')


class Typeface:
    def __init__(self, folder):
        self.fonts = {key: TTFont(folder/f'MonaSans-{weight}.ttf')
                      for key,weight in (('r','Regular'),('b','Bold'))}

    def width(self, text, size, weight='r'):
        font = self.fonts[weight]
        cmap = font.getBestCmap()
        return sum(font['hmtx'][cmap[ord(c)]][0] for c in text)*size/font['head'].unitsPerEm

    def paths(self, uses):
        result = []
        for weight, text in uses.items():
            font = self.fonts[weight]
            glyphs = font.getGlyphSet()
            cmap = font.getBestCmap()
            for char in sorted(set(text)):
                if char.isspace():
                    continue
                pen = SVGPathPen(glyphs, ntos=lambda value: str(round(value)))
                glyphs[cmap[ord(char)]].draw(pen)
                result.append(f'<path id="{weight}{ord(char):x}" d="{pen.getCommands()}"/>')
        return '<defs>'+''.join(result)+'</defs>'

    def text(self, text, x, y, size, weight='r', style='ink'):
        font = self.fonts[weight]
        cmap = font.getBestCmap()
        scale = size/font['head'].unitsPerEm
        result = [f'<g class="{style}" transform="translate({n(x)} {n(y)}) scale({n(scale)} -{n(scale)})">']
        cursor = 0
        for char in text:
            if not char.isspace():
                result.append(f'<use href="#{weight}{ord(char):x}" x="{cursor}"/>')
            cursor += font['hmtx'][cmap[ord(char)]][0]
        return ''.join(result)+'</g>'


def svg(width, height, title, description, defs, body):
    # Each image carries only the palette entries it actually uses.
    classes = set(' '.join(re.findall(r'class="([^"]+)"', body)).split())
    light, dark = THEME.removeprefix('<style>\n').removesuffix('\n</style>').split('@media(prefers-color-scheme:dark){')
    def palette(source):
        return ''.join(f'.{name}{{{values}}}' for name, values in
                       re.findall(r'\.([\w-]+)\{([^}]+)\}', source) if name in classes)
    theme = '<style>'+palette(light)+'@media(prefers-color-scheme:dark){'+palette(dark)+'}</style>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">'
            f'<title id="title">{escape(title)}</title><desc id="description">{escape(description)}</desc>'
            '<metadata>Mona Sans, GitHub, SIL OFL 1.1. Used glyphs only.</metadata>'
            +theme+defs+body+'</svg>\n')


def wrap(copy, font, size, limit):
    rows = ['']
    for word in copy.split():
        candidate = (rows[-1]+' '+word).strip()
        if font.width(candidate,size)>limit and rows[-1]: rows.append(word)
        else: rows[-1] = candidate
    return rows


def card(project, font, mobile=False):
    # Transparent right/bottom gutters provide spacing without GitHub-only CSS.
    width = 320 if mobile else 426
    height = 144 if mobile else 80
    box_height = 132 if mobile else 70
    title_size, copy_size = (19.5,18) if mobile else (17,12)
    title_y, copy_y = (32,62) if mobile else (26,48)
    copy_limit = 284 if mobile else 392
    rows = wrap(project['description'],font,copy_size,copy_limit) if mobile else [project['description']]
    assert len(rows)<=3
    assert font.width(project['name'],title_size,'b')<=(274 if mobile else 365)
    assert all(font.width(row,copy_size)<=copy_limit for row in rows)
    body = f'<rect class="paper line" x=".5" y=".5" width="{width-7}" height="{box_height-1}" stroke-width="1"/>'
    body += font.text(project['name'],14,title_y,title_size,'b')
    for i,row in enumerate(rows): body += font.text(row,14,copy_y+i*(25 if mobile else 20),copy_size,style='copy')
    arrow_x = 287 if mobile else 391
    body += f'<path class="accent" d="M{arrow_x} 22l10-10m-10 0h10v10" fill="none" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
    defs = font.paths({'b':project['name'],'r':project['description']})
    return svg(width,height,project['name'],project['description'],defs,body)


def icon(name, x, y, primary=False):
    style = 'primary-icon' if primary else 'secondary-icon'
    stroke = f'class="{style}" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'
    if name=='portfolio':
        drawing = f'<g {stroke}><circle cx="11" cy="11" r="10"/><ellipse cx="11" cy="11" rx="4.8" ry="10"/><path d="M1 11h20"/></g>'
    elif name=='email':
        drawing = f'<g {stroke}><rect x="0" y="3" width="22" height="16" rx="1"/><path d="m1 4 10 8L21 4"/></g>'
    else:
        # Small LinkedIn mark kept independent of the label's typeface.
        drawing = '<path class="ink" d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.35V9h3.414v1.561h.049c.476-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 1 1 0-4.124 2.062 2.062 0 0 1 0 4.124zM7.119 20.452H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0z"/>'
    return f'<g transform="translate({x} {y})">{drawing}</g>'


def button(name,label,font,primary=False):
    body = f'<rect class="{"primary" if primary else "secondary"}" x=".6" y=".6" width="274.8" height="46.8" rx="5" stroke-width="1.2"/>'
    width = font.width(label,19,'b')
    total = 24+12+width+12+12
    left = (276-total)/2
    body += icon(name,left,12,primary)
    body += font.text(label,left+36,30.5,19,'b','primary-ink' if primary else 'ink')
    ax = left+36+width+12
    arrow_style = 'primary-icon' if primary else 'secondary-icon'
    body += f'<path class="{arrow_style}" d="M{n(ax)} 30l10-10m-10 0h10v10" fill="none" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>'
    return svg(282,58,label,f'Abrir {label}',font.paths({'b':label}),body)


def image_link(project):
    slug = project['slug']
    alt = escape(f"{project['name']} — {project['description']}",quote=True)
    return (f'<a href="{escape(project["url"],quote=True)}"><picture>'
            f'<source media="(max-width: 767px)" srcset="assets/profile/{slug}-mobile.svg">'
            f'<img src="assets/profile/{slug}.svg" alt="{alt}" width="414">'
            '</picture></a>')


def section(projects):
    result = ['<!-- profile-projects:start -->',
              '<h3><img src="assets/profile/projects-heading.svg" alt="Projetos" width="200" height="42"></h3>',
              '<p>']
    for row in range(0,len(projects),2):
        result.append(' '.join(image_link(p) for p in projects[row:row+2]))
        if row+2<len(projects): result.append('<br>')
    result.append('</p>')
    result.append('<p>')
    for name,label,link in [('portfolio','Portfólio','https://vitorcomc.com.br/'),
                            ('linkedin','LinkedIn','https://www.linkedin.com/in/vitorcomc/'),
                            ('email','E-mail','mailto:victoralexandrepk@gmail.com')]:
        result.append(f'<a href="{link}"><img src="assets/profile/contact-{name}.svg" alt="{label}" width="274"></a>')
    result.extend(['</p>','<!-- profile-projects:end -->'])
    return '\n'.join(result)+'\n'


def build(font_dir):
    font = Typeface(font_dir)
    projects = json.loads((ASSETS/'projects.json').read_text())
    assert len(projects)==14 and len({p['url'] for p in projects})==14
    for p in projects:
        for mobile in (False,True):
            suffix = '-mobile' if mobile else ''
            (ASSETS/f'{p["slug"]}{suffix}.svg').write_text(card(p,font,mobile))
    for key,label,primary in [('portfolio','Portfólio',True),('linkedin','LinkedIn',False),('email','E-mail',False)]:
        (ASSETS/f'contact-{key}.svg').write_text(button(key,label,font,primary))
    (ASSETS/'projects-heading.svg').write_text(svg(200,42,'Projetos','Projetos',font.paths({'b':'Projetos'}),font.text('Projetos',0,29,30,'b')))
    output = section(projects)
    (ROOT/'projects-section.html').write_text(output)
    readme = ROOT/'README.md'
    if readme.exists():
        current = readme.read_text()
        if '<!-- profile-projects:start -->' in current:
            current = re.sub(r'<!-- profile-projects:start -->.*?<!-- profile-projects:end -->\n?',output,current,flags=re.S)
        else:
            current = current.split('### Projetos')[0]+output
        readme.write_text(current)
    print(f'Built {len(projects)} linked project cards in desktop/mobile variants, 3 buttons and the section heading.')


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font-dir',type=Path,required=True)
    build(parser.parse_args().font_dir)
