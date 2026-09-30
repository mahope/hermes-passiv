#!/usr/bin/env python3
"""Cross-linking: de 3 mest relaterede indlæg til hvert /blog-indlæg.

For hvert EN-blogindlæg vælges de 3 mest relaterede andre indlæg (token-
overlap på titel + description, plus badge-kategori som tiebreaker).

Hvor de lander, afhænger af hvad siden allerede har (30/9):

* 43 af 44 artikler har et `<section class="products">` med `<h2>Tools and
  guides</h2>` og et kortgitter. **Der flettes ind i det gitter** — et nyt kort
  pr. relateret indlæg, og hvis destinationskortet allerede findes, bærer det
  i stedet beskrivelsen. Det er her fejlen lå: 36 af de 132 relaterede links
  pegede på en destination, siden allerede viste i sit eget gitter, så
  `/blog/text-on-image-contrast-check` — den mest besøgte artikel på
  mahope.tools — nåede læseren med `/blog/wcag-contrast-checker` to gange under
  to overskrifter og to navne. `tools/check_tool_sections.py` dømmer det.
* 1 artikel (`macos-menu-bar-website-monitor`) har samme `<h2>` over en `<p>`
  med inline-links. Der flettes ind i den `<p>`.
* Resten af bloggen har intet værktøjsafsnit, og får den gamle boks.

Idempotent: en genkørsel tilføjer intet nyt, fordi de flettede kort *er* kortene
nu, og destinationerne findes så allerede. `pick_related` kan vælge et nyt
sæt, når der kommer artikler til; nye destinationer flettes ind, og det
fordærvede gitter beholder sit kort — det er ikke længere et krydslink, det er
et kort på lige fod med de øvrige.

Danskere-indlæg (/da/blog) spejles ikke her — de har deres egen hub.

Verificering: alle links i boks og gitter peger på eksisterende filer; alle 96
EN-blogfiler har relaterede links efter kørsel.

Usage: python3 tools/crosslink_blog.py [--deploy]
"""
import glob
import html as htmllib
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crosslink_merge as M  # noqa: E402  (deler logikken med DA-udgaven)

SITE = 'site'
MARKER = M.MARKER_EN
TOOLS_H2 = M.TOOLS_H2_EN



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


def kort_tekst(related):
    """(href, titel, kort beskrivelse) for de valgte indlæg, i rækkefølge."""
    return M.relaterede_kort(
        {r: page_meta(f'{SITE}/blog/{r}.html') for r in related[:3]}, related)


def build_box(slug, related):
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
        original = open(path).read()
        c = original
        items = kort_tekst(pick_related(slug, metas))
        h2 = c.find(TOOLS_H2)
        if h2 != -1 and M.GITTER_RE.search(c, h2):
            # Form 1: kortgitter. Destinationerne bliver kort, og den gamle boks
            # forsvinder, så siden ender med ét afsnit og ingen dobbelt link.
            new = M.flet_i_gitter(c, items)
            new = M.fjern_boks(new, MARKER)
        elif h2 != -1:
            # Form 2: `<h2>` over en `<p>` med inline-links.
            new = M.fjern_boks(M.flet_i_inline(c, items), MARKER)
        elif MARKER in c:
            # Ingen værktøjsafsnit: den gamle boks, opdateret idempotent.
            box = build_box(slug, pick_related(slug, metas))
            pre = c.index(MARKER)
            end = c.find('</div>', c.find('</ul>', pre))
            assert end != -1, f'{slug}: kunne ikke finde slut på gammel boks'
            new = c[:pre] + box + c[end + len('</div>'):]
        else:
            anchor = c.rfind('<footer')
            if anchor == -1:
                anchor = c.rfind('<script>')
                assert anchor != -1, f'{slug}: intet indsættelsespunkt fundet'
            new = c[:anchor] + build_box(slug, pick_related(slug, metas)) + '\n\n' + c[anchor:]
        # Mod `original`, ikke mod `c`: når et greb på `c` (fjernet kasse,
        # flettet kort) ikke ændrer den nye tekst, ville `new == c` vælge
        # *ikke* at skrive — og så forblev det, grebet fjernede, på disken.
        if new != original:
            open(path, 'w').write(new)
            changed.append(slug)

    # Verificering: hver fil har relaterede links, og de peger på filer der findes
    disk = set(files)
    for slug in files:
        c = open(f'{SITE}/blog/{slug}.html').read()
        relaterede = {h for h in M.LINK_RE.findall(c) if re.fullmatch(r'/blog/[a-z0-9-]+', h)}
        assert relaterede, f'{slug}: mangler relaterede links'
        for href in set(relaterede):
            assert os.path.exists('site' + href + '.html'), f'{slug}: dødt link {href}'
    print(f'verify OK: {len(files)} filer har relaterede links, ingen døde links')

    # Sørg for at forsiden stadig linker til alle (regressionstjek fra fix_en_hub)
    #
    # Målt 30/9: `fix_en_hub.py` har siden gjort forsiden til en produktside, så
    # den linker ikke længere til hvert indlæg — 83 af 93 mangler. Det er et
    # korrekt valg, ikke en regression, men tjekket stod som `assert` og fik
    # **hver** kørsel til at dø med en 400-ords undtagelse efter at alle 93
    # filer var skrevet. Et tjek der altid fejler, er ikke et tjek: det gjorde
    # exit-koden ubrugelig, så ingen kunne se om denne kørsel ellers var grøn.
    # Det er derfor en advarsel med et tal, ikke en undtagelse.
    hub = open(f'{SITE}/index.html').read()
    missing = disk - set(re.findall(r'href="/blog/([^"#?]+)"', hub))
    if missing:
        print(f'ADVARSEL: forsiden linker ikke direkte til {len(missing)} af '
              f'{len(disk)} indlæg (indlæggene ligger på /blog, ikke på forsiden)')

    if deploy:
        raise SystemExit("Manuel deploy er deaktiveret; commit til main og lad GitHub Actions udgive.")
    print(f'done — ændret: {len(changed)} filer')


if __name__ == '__main__':
    main()
