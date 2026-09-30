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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crosslink_merge as M  # noqa: E402  (deler logikken med EN-udgaven)

SITE = 'site'
BLOG = f'{SITE}/da/blog'
HUB = f'{SITE}/da/index.html'
MARKER = M.MARKER_DA
TOOLS_H2 = M.TOOLS_H2_DA


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


def kort_tekst(related):
    """(href, titel, kort beskrivelse) for de valgte indlæg, i rækkefølge."""
    return M.relaterede_kort(
        {r: page_meta(f'{BLOG}/{r}.html') for r in related[:3]}, related, '/da/blog/')


def build_box(related):
    items = [
        f'<li><a href="{href}"><strong>{htmllib.escape(title)}</strong></a>'
        + (f'<br><span style="color:#555;font-size:14px;">{htmllib.escape(short)}</span>'
           if short else '') + '</li>'
        for href, title, short in kort_tekst(related)
    ]
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
        original = open(path).read()
        c = original
        # En DA-side må aldrig have den **engelske** kasse. Målt 30/9:
        # `da/blog/bugrapporter-i-ci-pipeline` havde begge, fordi siden er en
        # dansk oversættelse af en EN-side, der fik den med i kopien. Den
        # peger på `/blog/…` — engelske artikler på en dansk læsers side.
        c = M.fjern_boks(c, M.MARKER_EN)
        items = kort_tekst(pick_related(slug, metas))
        h2 = c.find(TOOLS_H2)
        if h2 != -1 and M.GITTER_RE.search(c, h2):
            # Samme greb som EN: de relaterede artikler bliver kort i det
            # afsnit siden allerede har, og kassen forsvinder. 18 DA-sider
            # havde ellers to afsnit med samme job side om side.
            new = M.fjern_boks(M.flet_i_gitter(c, items), MARKER)
        elif h2 != -1:
            new = M.fjern_boks(M.flet_i_inline(c, items), MARKER)
        elif MARKER in c:
            pre = c.index(MARKER)
            end = c.find('</div>', c.find('</ul>', pre))
            assert end != -1, f'{slug}: kunne ikke finde slut på gammel boks'
            new = c[:pre] + build_box(pick_related(slug, metas)) + c[end + len('</div>'):]
        else:
            anchor = c.rfind('<footer')
            if anchor == -1:
                anchor = c.rfind('<script>')
                assert anchor != -1, f'{slug}: intet indsættelsespunkt fundet'
            new = c[:anchor] + build_box(pick_related(slug, metas)) + '\n\n' + c[anchor:]
        # Mod `original`, ikke mod `c`: når et greb på `c` (fjernet kasse,
        # flettet kort) ikke ændrer den nye tekst, ville `new == c` vælge
        # *ikke* at skrive — og så forblev det, grebet fjernede, på disken.
        if new != original:
            open(path, 'w').write(new)
            changed.append(slug)

    # Verificering: hver fil har boksen, ingen døde links
    disk = set(files)
    for slug in files:
        c = open(f'{BLOG}/{slug}.html').read()
        relaterede = {h for h in M.LINK_RE.findall(c) if re.fullmatch(r'/da/blog/[a-z0-9-]+', h)}
        assert relaterede, f'{slug}: mangler relaterede links'
        for href in relaterede:
            assert os.path.exists('site' + href + '.html'), f'{slug}: dødt link {href}'
        assert M.MARKER_EN not in c, f'{slug}: dansk side med den engelske kasse'
    print(f'verify OK: {len(files)} DA-filer har relaterede links, ingen døde links')

    # Regressionstjek: /da/-forsiden linker stadig til alle indlæg
    # Samme som i EN-udgaven (30/9): `/da.html` er en produktside og linker
    # ikke til hvert indlæg, så `assert` ville få hver kørsel til at dø efter at
    # alle filer var skrevet — et tjek der altid fejler, er ikke et tjek.
    # `HUB` lå på `site/da.html`, som ikke findes længere — forsiden er
    # `site/da/index.html` siden DA-huben blev en produktside. Uden den
    # rettelse døde scriptet med FileNotFoundError, ikke med en besked om
    # hvad der manglede.
    hub = open(HUB).read()
    missing = disk - set(re.findall(r'href="/da/blog/([^"#?]+)"', hub))
    if missing:
        print(f'ADVARSEL: /da/ forsiden linker ikke direkte til {len(missing)} af '
              f'{len(disk)} indlæg (indlæggene ligger på /da/blog)')

    if deploy:
        raise SystemExit("Manuel deploy er deaktiveret; commit til main og lad GitHub Actions udgive.")
    print(f'done — ændret: {len(changed)} filer')


if __name__ == '__main__':
    main()
