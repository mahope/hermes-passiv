#!/usr/bin/env python3
"""Dom sider der lister deres værktøjer to gange, og links der optræder to gange.

Målt 30/9: 44 af 190 EN-blogfiler havde **to** afsnit med samme job —

    <section class="products"><h2>Tools and guides</h2><div class="problem-cards">…
    <div class="related-guides"><h2>Related Guides</h2><ul>…

— med hver sin liste. `check_duplicate_headings` er korrekt grøn på dem, for
overskrifterne er forskellige, og ingen anden port dømmer struktur: de dømmer
links, priser og løfter. Og de to lister var ikke ens — de overlappede i 36 af
132 relaterede links. Konkret på `/blog/text-on-image-contrast-check`, den mest
besøgte artikel på mahope.tools (8 af 15 besøgende): læseren fik
`/blog/wcag-contrast-checker` to gange, først som «WCAG contrast checker: how
to check color contrast» i kortgitteret og 20 linjer længere nede som «WCAG
Contrast Checker Check Color Contrast for Free» i en liste. To navne, én
destination, to steder at læseren må regne med at blive sendt hen.

Porten dømmer to ting, for de er to forskellige fejl:

1. **To afsnit med samme job.** `Tools and guides` og `Related Guides` er samme
   løfte for en læser — «her er hvor du kan gå hen» — så begge på én side er
   en fejl, uanset at de lister forskellige ting. Samme regel på dansk.
2. **Én destination to gange i værktøjsafsnittet.** Det er den del af fejlen
   der ikke er en overskrift, så en port der kun læser `<h2>` ser den ikke.

Begge dele læses fra `site/`, og `crosslink_blog.py` er den generator der
skrev den anden boks, så porten og generatoren dømmer hver sin halvdel af
samme fejlform.

    python3 tools/check_tool_sections.py            # dom alle sider
    python3 tools/check_tool_sections.py --self-test # 11 kontroller
    python3 tools/check_tool_sections.py --list     # kun de dømte løfter
"""
from __future__ import annotations

import argparse
import html as htmllib
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# Overskrifterne der lover værktøjer eller guides. Casen er ligegyldig: en
# læser kan ikke se forskel på «Tools and guides» og «Tools And Guides».
# `verktøj`/`værktøj` er ikke en fejl i sig selv — kun en side med **to** af dem.
VAERKTOJ = {"tools and guides", "værktøjer og guides",
            "related guides", "relaterede guides"}
H2_RE = re.compile(r"<h2\b[^>]*>(.*?)</h2>", re.S | re.I)
HREF_RE = re.compile(r'href="([^"]+)"')
# Et afsnit løber fra sin overskrift til næste `<h2>` **eller** til siden
# slutter. Uden den anden halvdel tæller `<footer>`-linkene med: på
# `/blog/text-on-image-contrast-check` gav det «/free-tools står 2 gange under
# tools and guides», fordi kortgitteret linker til All free tools og footeren
# også gør det. Det er ikke en dublet — det er to steder på en side, som
# footeren er lavet til. Begge slutteringer er nødvendige, for den ene uden den
# anden giver en rød uden en fejl.
AFSLUT_RE = re.compile(r"<h2\b|</main\b|</article\b|</body\b|<footer\b", re.I)
SPLIT_RE = re.compile(
    r"(<!--.*?-->|<(script|style|noscript|template|svg)\b.*?</\2\s*>)", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")


def normaliser(overskrift: str) -> str:
    """Hvad en læser ser i indholdsfortegnelsen, i én linje."""
    tekst = htmllib.unescape(TAG_RE.sub("", overskrift))
    return re.sub(r"\s+", " ", tekst).strip().casefold()


def afsnit(html: str) -> list[tuple[str, str]]:
    """`(overskrift, blokkens html)` for hvert værktøjs-/guideafsnit."""
    indhold = SPLIT_RE.sub("", html)
    fund: list[tuple[str, str]] = []
    for m in H2_RE.finditer(indhold):
        tekst = normaliser(m.group(1))
        if tekst not in VAERKTOJ:
            continue
        næste = AFSLUT_RE.search(indhold, m.end())
        fund.append((tekst, indhold[m.start():næste.start() if næste else len(indhold)]))
    return fund


def dubletter_i_afsnit(blok: str) -> dict[str, int]:
    """Destinationer der optræder mere end én gang i ét afsnit, med antal."""
    tæller: dict[str, int] = {}
    for href in HREF_RE.findall(blok):
        tæller[href] = tæller.get(href, 0) + 1
    return {h: n for h, n in tæller.items() if n > 1}


def dom_fil(fil: Path) -> list[str]:
    fund: list[str] = []
    afsnittene = afsnit(fil.read_text(encoding="utf-8", errors="replace"))
    # 1. To afsnit med samme job på én side.
    for i in range(len(afsnittene)):
        for j in range(i + 1, len(afsnittene)):
            fund.append(
                f'TO VÆRKTØJSAFSNIT i {fil}: "{afsnittene[i][0]}" og '
                f'"{afsnittene[j][0]}" er samme løfte for en læser — kun ét afsnit pr. side'
            )
    # 2. Én destination to gange i det samme afsnit.
    for overskrift, blok in afsnittene:
        for href, antal in sorted(dubletter_i_afsnit(blok).items()):
            fund.append(
                f'DUBLET LINK i {fil}: {href} står {antal} gange under "{overskrift}"'
            )
    return fund


def dom(rod: Path = SITE) -> list[str]:
    fund: list[str] = []
    for fil in sorted(rod.rglob("*.html")):
        fund.extend(dom_fil(fil))
    return fund


def self_test() -> int:
    fejl: list[str] = []

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        if not sand:
            fejl.append(f"{navn}{': ' + detalje if detalje else ''}")

    gitter = ('<h2>Tools and guides</h2><div class="problem-cards">'
              '<div class="card"><a href="/a">A</a></div></div>')
    kasse = ('<h2>Related Guides</h2><ul><li><a href="/b"><strong>B</strong></a></li></ul>')

    # 1. Casing er ikke forskel — det er samme afsnit for en læser.
    tjek("casing er ikke forskel",
         len(afsnit("<h2>TOOLS AND GUIDES</h2><h2>Priser</h2>")) == 1)
    # 2. Tags og entities i overskriften er det samme afsnit — de former der
    #    faktisk optræder i `site/`. (Ikke «Tools & guides»: den overskrift
    #    findes ikke, og porten skal dømme de fire den kender.)
    tjek("tags og entities er ikke forskel",
         len(afsnit("<h2>Tools <em>and</em> guides</h2>")) == 1
         and len(afsnit("<h2>Tools&nbsp;and guides</h2>")) == 1)
    # 3. Dansk og engelsk er samme familie, så de to er en fejl sammen.
    tjek("dansk og engelsk er én familie",
         len(dom_fil(_fil("<h2>Værktøjer og guides</h2><h2>Relaterede guides</h2>"))) == 1)
    # 4. Den fundne fejlform: gitter **og** kasse på én side.
    tjek("gitter plus kasse er rød", len(dom_fil(_fil(gitter + kasse))) == 1)
    # 5. Én destination to gange i ét afsnit er rød, selv uden to overskrifter —
    #    det er den halvdel `check_duplicate_headings` ikke kan se.
    tjek("samme destination to gange i ét afsnit er rød",
         len(dom_fil(_fil('<h2>Tools and guides</h2>'
                         '<a href="/x">X</a><a href="/x">X igen</a>'))) == 1)
    # 6. To forskellige destinationer i ét afsnit er grønne.
    tjek("forskellige destinationer er grønne",
         dom_fil(_fil('<h2>Tools and guides</h2><a href="/x">X</a><a href="/y">Y</a>')) == [])
    # 7. Ét afsnit alene er grønt — det er det, 49 af filerne har.
    tjek("ét afsnit alene er grønt", dom_fil(_fil(kasse)) == [])
    tjek("ét gitter alene er grønt", dom_fil(_fil(gitter)) == [])
    # 8. Kode er ikke indhold: en overskrift i kommentar eller JSON-LD må ikke
    #    gøre porten rød, ellers får den en rød uden en fejl.
    tjek("kommentar og JSON-LD tæller ikke",
         dom_fil(_fil('<!-- <h2>Related Guides</h2> --><h2>Tools and guides</h2>'
                      '<script>{"a":"<h2>Related Guides</h2>"}</script>')) == [])
    # 9. Et afsnit slutter ved næste `<h2>`, så et link i et **andet** afsnit er
    #    ikke en dublet af et link i dette.
    tjek("link i næste afsnit er ikke en dublet",
         dom_fil(_fil('<h2>Tools and guides</h2><a href="/x">X</a>'
                      '<h2>Om os</h2><a href="/x">X</a>')) == [])
    # 10. Mutation: målingen på site/ skal være grøn, ellers er den ikke brugbar.
    med_fejl = dom()
    tjek("målingen er grøn på site/", not med_fejl, "; ".join(med_fejl[:3]))
    # 11. Mutation: læg den fundne fejlform ind i en syntetisk fil, og porten
    #     skal dømme den — elvis er kontrol 10 grøn fordi porten intet ser.
    with tempfile.TemporaryDirectory() as tmp:
        rod = Path(tmp)
        (rod / "syntetisk.html").write_text(gitter + kasse, encoding="utf-8")
        tjek("syntetisk fejl er rød", len(dom(rod)) == 1, str(dom(rod)))
        (rod / "syntetisk.html").write_text(gitter, encoding="utf-8")
        tjek("rettet fil er grøn", dom(rod) == [], str(dom(rod)))

    for linje in fejl:
        print(f"  FEJL  {linje}")
    print(f"check-tool-sections-selftest: {'OK' if not fejl else 'RØD'}"
          f" ({11 - len(fejl)}/11 kontroller)")
    return 1 if fejl else 0


def _fil(html: str) -> Path:
    """En fil med `html` i sig, så `dom_fil` kan læse den fra en sti."""
    tmp = Path(tempfile.mkdtemp()) / "side.html"
    tmp.write_text(html, encoding="utf-8")
    return tmp


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="kør portens egen kontrol af sig selv")
    parser.add_argument("--list", action="store_true",
                        help="vis hver domt værktøjsfremgang")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    fund = dom()
    for linje in fund:
        print(linje)
    sider = len({l.split(" i ", 1)[1].split(":", 1)[0] for l in fund})
    if fund:
        print(f"\ntool-sections: RØD — {len(fund)} fund på {sider} sider")
        return 1
    if args.list:
        # Uden fund er `--list` tom. Det siger eksplicit hvor mange afsnit der
        # blev læst, så «ingen fund» ikke kan forveksles med «porten læste intet».
        antal = sum(len(afsnit(f.read_text(encoding="utf-8", errors="replace")))
                    for f in SITE.rglob("*.html"))
        print(f"tool-sections: GRØN — {antal} værktøjsafsnit læst i site/, "
              f"ingen side lister sine værktøjer to gange")
    else:
        print("tool-sections: GRØN — ingen side i site/ lister sine værktøjer to gange")
    return 0


if __name__ == "__main__":
    sys.exit(main())
