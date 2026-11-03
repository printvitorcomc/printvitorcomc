"""Build native GitHub project cards and contact links. Python stdlib only.

Run: python3 scripts/build-profile-cards.py
Copy and destinations live in assets/profile/projects.json. Native HTML keeps
the GitHub font, color theme, zoom, selection and mobile wrapping in one system.
GitHub strips custom CSS, so supported table alignment and clear attributes
provide two columns when space permits, then one column on narrow screens.
"""
from pathlib import Path
from html import escape
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def section(projects):
    rows = ['<!-- profile-projects:start -->','### Projetos','']
    for index,p in enumerate(projects):
        rows.extend(['<table align="left">',
                     '  <tr><td width="414" height="88">',
                     f'    <a href="{escape(p["url"],quote=True)}"><strong>{escape(p["name"])} ↗</strong></a><br>',
                     f'    {escape(p["description"])}',
                     '  </td></tr>','</table>'])
        if index%2==1: rows.append('<br clear="all">')
    rows.append('')
    for url,label in [('https://vitorcomc.com.br/','Portfólio'),
                      ('https://www.linkedin.com/in/vitorcomc/','LinkedIn'),
                      ('mailto:victoralexandrepk@gmail.com','E-mail')]:
        rows.extend(['<table align="left">',
                     f'  <tr><td width="274" height="48" align="center"><a href="{url}"><strong>{label} ↗</strong></a></td></tr>',
                     '</table>'])
    rows.extend(['<br clear="all">','<!-- profile-projects:end -->',''])
    return '\n'.join(rows)


def build():
    projects = json.loads((ROOT/'assets/profile/projects.json').read_text())
    assert len(projects)==14 and len({p['url'] for p in projects})==14
    readme = ROOT/'README.md'
    text = readme.read_text()
    text = text.replace('<h1><samp>Victor Alexandre</samp></h1>','# Victor Alexandre')
    text = text.replace('<p><samp>','').replace('</samp></p>','')
    output = section(projects)
    if '<!-- profile-projects:start -->' in text:
        text = re.sub(r'<!-- profile-projects:start -->.*?<!-- profile-projects:end -->\n?',output,text,flags=re.S)
    else:
        text = text.split('### Projetos')[0]+output
    readme.write_text(text)
    print('Built 14 native cards and 3 native contact links; zero project images or external fonts.')


if __name__=='__main__':
    build()
