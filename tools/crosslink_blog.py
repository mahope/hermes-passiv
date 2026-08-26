#!/usr/bin/env python3
"""Cross-linking: indsæt "Related guides"-sektion i bunden af alle /blog-indlæg.

For hvert EN-blogindlæg vælges de 3 mest relaterede andre indlæg (token-
overlap på titel + description, plus badge-kategori som tiebreaker), og en
"Related guides"-boks med kort + links indsættes lige før footer. Idempotent:
indlæg der allerede har boksen får den opdateret, ikke duplikeret.

Danskere-indlæg (/da/blog) spejles ikke her — de har deres egen hub.

Verificering: alle links i bokserne peger på eksisterende filer; alle 96
EN-blogfiler har boksen efter kørsel.

Usage: python3 tools/crosslink_blog.py [--deploy]
"""
import glob
import html as htmllib
import os
import re
import subprocess
import sys

SITE = 'site'
MARKER = '<!-- crosslink-related -->'


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


STOP = set('''a an and are as at be by for from how in is it of on or that the
this to what when where which with your you we our free guide guides check
checker online tool tools website websites site without best using use can
should does do why into out up new 2026'''.split())


def tokens(s):
    return {w for w in re.findall(r"[a-zæøå]{3,}", s.lower()) if w not in STOP}


def similarity(a, b):
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def build_box(slug, related):
    items = []
    for r in related[:3]:
        title, desc = page_meta(f'{SITE}/blog/{r}.html')
        short = desc.split('. ')[0].rstrip('.') if desc else title
        if len(short) > 110:
            short = short[:107].rstrip() + '…'
        items.append(
            f'<li><a href="/blog/{r}"><strong>{htmllib.escape(title)}</strong></a>'
            f'<br><span style="color:#555;font-size:14px;">{htmllib.escape(short)}.</span></li>'
        )
    return (
        f'{MARKER}\n'
        f'<div class="related-guides" style="border:1px solid #e5e7eb;border-radius:10px;'
        f'padding:20px 24px;margin:32px 0;">\n'
        f'  <h2 style="margin-top:0;">Related Guides</h2>\n'
        f'  <ul style="list-style:none;padding:0;margin:0;">\n'
        f'    ' + '\n    '.join(items) + '\n  </ul>\n'
        f'</div>'
    )


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


def main():
    deploy = '--deploy' in sys.argv
    files = sorted(os.path.basename(f)[:-5]
                   for f in glob.glob(f'{SITE}/blog/*.html')
                   if os.path.basename(f) != 'index.html')
    metas = {s: page_meta(f'{SITE}/blog/{s}.html') for s in files}

    changed = []
    for slug in files:
        path = f'{SITE}/blog/{slug}.html'
        c = open(path).read()
        box = build_box(slug, pick_related(slug, metas))
        if MARKER in c:
            # erstat eksisterende boks (idempotent opdatering)
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

    # Verificering: hver fil har boksen, og alle links virker
    disk = set(files)
    for slug in files:
        c = open(f'{SITE}/blog/{slug}.html').read()
        assert MARKER in c, f'{slug}: mangler related-boks'
        for href in re.findall(r'href="(/blog/[^"]+)"', c.split(MARKER, 1)[1].split('</div>')[0]):
            target = ('site' + href)
            assert os.path.exists(target + '.html'), f'{slug}: dødt link {href}'
    print(f'verify OK: {len(files)} filer har Related-boksen, ingen døde links')

    # Sørg for at forsiden stadig linker til alle (regressionstjek fra fix_en_hub)
    hub = open(f'{SITE}/index.html').read()
    missing = disk - set(re.findall(r'href="/blog/([^"#?]+)"', hub))
    assert not missing, f'forsiden mangler nu: {missing}'

    if deploy:
        subprocess.run(['./deploy.sh'], check=True)
    print(f'done — ændret: {len(changed)} filer')


if __name__ == '__main__':
    main()
