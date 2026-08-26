#!/usr/bin/env python3
"""Cross-linking for /da/blog: indsæt "Relaterede guides"-boks i bunden af alle DA-indlæg.

Spejler tools/crosslink_blog.py (EN-udgaven). Vælger de 3 mest relaterede andre
DA-indlæg via token-overlap på titel + description. Idempotent: eksisterende boks
opdateres, ikke duplikeret.

Verificering efter kørsel:
  - alle 95 DA-blogfiler har boksen
  - alle links i boksene peger på eksisterende filer
  - /da/-forsiden linker stadig til alle DA-indlæg

Usage: python3 tools/crosslink_blog_da.py [--deploy]
"""
import glob
import html as htmllib
import os
import re
import subprocess
import sys

SITE = 'site'
BLOG = f'{SITE}/da/blog'
HUB = f'{SITE}/da.html'
MARKER = '<!-- crosslink-related-da -->'


def clean(s):
    s = re.sub(r'<br\s*/?>', ' ', s)
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def page_meta(path):
    h = open(path).read()
    t = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.DOTALL)
    d = re.search(r'name="description" content="(.*?)"', h)
    title = clean(htmllib.unescape(t.group(1))) if t else ''
    desc = clean(htmllib.unescape(d.group(1))) if d else ''
    return title, desc


STOP = set('''af at der deres det din dit du en ene er et for fra få ham han
har havde have henne hensin hier hvordan hvor hvad når og også op eller
side sider sites website websites hjemmeside hjemmesider guide guides gratis
online tool tools tjek checker bedste kan skal vil uden nye brug using use
2026'''.split())


def tokens(s):
    return {w for w in re.findall(r"[a-zæøå]{3,}", s.lower()) if w not in STOP}


def similarity(a, b):
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def pick_related(slug, metas):
    title, desc = metas[slug]
    scored = []
    for other in metas:
        if other == slug:
            continue
        ot, od = metas[other]
        score = similarity(title, ot) * 2 + similarity(desc, od)
        scored.append((score, other))
    scored.sort(reverse=True)
    return [s for _, s in scored[:3]]


def build_box(related):
    items = []
    for r in related[:3]:
        title, desc = page_meta(f'{BLOG}/{r}.html')
        short = desc.split('. ')[0].rstrip('.') if desc else title
        if len(short) > 110:
            short = short[:107].rstrip() + '…'
        items.append(
            f'<li><a href="/da/blog/{r}"><strong>{htmllib.escape(title)}</strong></a>'
            f'<br><span style="color:#555;font-size:14px;">{htmllib.escape(short)}.</span></li>'
        )
    return (
        f'{MARKER}\n'
        f'<div class="related-guides" style="border:1px solid #e5e7eb;border-radius:10px;'
        f'padding:20px 24px;margin:32px 0;">\n'
        f'  <h2 style="margin-top:0;">Relaterede guides</h2>\n'
        f'  <ul style="list-style:none;padding:0;margin:0;">\n'
        f'    ' + '\n    '.join(items) + '\n  </ul>\n'
        f'</div>'
    )


def main():
    deploy = '--deploy' in sys.argv
    files = sorted(os.path.basename(f)[:-5]
                   for f in glob.glob(f'{BLOG}/*.html')
                   if os.path.basename(f) != 'index.html')
    metas = {s: page_meta(f'{BLOG}/{s}.html') for s in files}

    changed = []
    for slug in files:
        path = f'{BLOG}/{slug}.html'
        c = open(path).read()
        box = build_box(pick_related(slug, metas))
        if MARKER in c:
            pre = c.index(MARKER)
            end = c.find('</div>', c.find('</ul>', pre))
            assert end != -1, f'{slug}: kunne ikke finde slut på gammel boks'
            end += len('</div>')
            new = c[:pre] + box + c[end:]
        else:
            anchor = c.rfind('<footer')
            if anchor == -1:
                anchor = c.rfind('<script>')
                assert anchor != -1, f'{slug}: intet indsættelsespunkt fundet'
            new = c[:anchor] + box + '\n\n' + c[anchor:]
        if new != c:
            open(path, 'w').write(new)
            changed.append(slug)

    # Verificering: hver fil har boksen, ingen døde links
    disk = set(files)
    for slug in files:
        c = open(f'{BLOG}/{slug}.html').read()
        assert MARKER in c, f'{slug}: mangler related-boks'
        boxpart = c.split(MARKER, 1)[1]
        for href in re.findall(r'href="(/da/blog/[^"]+)"', boxpart.split('</ul>')[0]):
            target = ('site' + href)
            assert os.path.exists(target + '.html'), f'{slug}: dødt link {href}'
    print(f'verify OK: {len(files)} DA-filer har Relaterede-boksen, ingen døde links')

    # Regressionstjek: /da/-forsiden linker stadig til alle indlæg
    hub = open(HUB).read()
    missing = disk - set(re.findall(r'href="/da/blog/([^"#?]+)"', hub))
    assert not missing, f'/da/-forsiden mangler nu: {missing}'

    if deploy:
        subprocess.run(['./deploy.sh'], check=True)
    print(f'done — ændret: {len(changed)} filer')


if __name__ == '__main__':
    main()
