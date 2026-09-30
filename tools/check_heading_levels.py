#!/usr/bin/env python3
"""Dom spring i overskriftsniveau: `<h1>` → `<h3>` uden et `<h2>` imellem.

Målt 30/9: 12 af 224 sider i `site/` sprang et niveau. `paid-templates` (EN+DA)
satte 14 produkternavne i `<h3>` som det første indhold efter `<h1>` og havde
ikke ét `<h2>` før længere nede; `clean-copy-cli-ref` havde *intet* `<h2>` på
hele siden. `compliance-report` og `stats` stod i planen som mistænkte, men er
grønne — de har begge et `<h2>` før deres første `<h3>`, så et grep uden
dokumentrækkefølge kan ikke skelne.

Det læseren mærker er overskriftslisten: en skærmlæsere kan springe frem med
 niveau-tasten eller hente listen, og den siger "1, 3, 3, 3, 2" — to niveauer
findes ikke i dokumentet. WCAG 1.3.1 (Information and Relationships) er derfor
brudt, og det er en fejl: siderne er bygget af os, så niveauet kan bare vælges
rigtigt.

Reglen er *kun* spring, ikke dybde. `h1 → h3 → h3 → h2` er et spring.
`h1 → h2 → h4` er også et spring. `h1 → h2 → h3 → h2` er ikke, fordi niveauet
aldrig springer; en ny `<h2>` efter en `<h3>` er et nyt afsnit, ikke en dybere
niveaufejl. Og springet måles i **dokumentrækkefølge**: et `<h3>` der står
før sideens første `<h2>` er springet, uanset hvor mange `<h2>` der kommer senere.

Kode er ikke indhold. En `<h3>` i en kommentar, i `<script>` (vores egen JS
bygger overskrifter som strenge) eller i JSON-LD tæller ikke — ellers får
porten en rød uden en fejl, og det er den fejl den skal finde.

    python3 tools/check_heading_levels.py            # dom alle sider
    python3 tools/check_heading_levels.py --list     # hvilke filer, kun talt
    python3 tools/check_heading_levels.py --self-test # 12 kontroller
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# Hele overskriftselementet, så åbnings- og lukketag flyttes sammen. Uden
# `\1`-lukketagen bliver `<h3>x</h2>` efter en rettelse, og det er en fejl i
# det stille.
H_RE = re.compile(r"<h([1-6])(?![0-9])((?:\s[^>]*)?)>(.*?)</h\1\s*>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")
# Skjuler det der ikke er indhold, i stedet for at splitte på det: en kommentar
# har ingen gruppe indeni, en `<script>` har to, så indeks-paritet i en
# split-liste afhænger af hvilken slags der blev fundet først. Samme grund som
# i `check_duplicate_headings.py`.
SPLIT_RE = re.compile(
    r"(<!--.*?-->|<(script|style|noscript|template|svg)\b.*?</\2\s*>)", re.S | re.I)


def disposition(html: str) -> list[int]:
    """Overskriftsniveauer i dokumentrækkefølge, tomme overskrifter udeladt."""
    række = []
    for m in H_RE.finditer(SPLIT_RE.sub("", html)):
        if TAG_RE.sub("", m.group(3)).strip():
            række.append(int(m.group(1)))
    return række


def spring(række: list[int]) -> list[tuple[int, int]]:
    """Niveauspring i rækkefølgen som `(fra, til)`."""
    return [(a, b) for a, b in zip(række, række[1:]) if b - a > 1]


def dom(root: Path = SITE) -> list[str]:
    fund: list[str] = []
    for fil in sorted(root.rglob("*.html")):
        række = disposition(fil.read_text(encoding="utf-8", errors="replace"))
        for fra, til in spring(række):
            fund.append(
                f"SPRING i {fil.relative_to(root)}: <h{fra}> → <h{til}> "
                f"uden et h{fra + 1} imellem (rækkefølge {' '.join(map(str, række[:10]))})"
            )
    return fund


def self_test() -> int:
    fejl: list[str] = []

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        if not sand:
            fejl.append(f"{navn}{': ' + detalje if detalje else ''}")

    # 1. Det fundne spring, som en port der intet så ikke ville se.
    tjek("h1→h3 er rød",
         spring(disposition("<h1>A</h1><h3>B</h3>")) == [(1, 3)])
    # 2. Ét niveau ned ad gangen er grøn.
    tjek("h1→h2→h3 er grøn",
         spring(disposition("<h1>A</h1><h2>B</h2><h3>C</h3>")) == [])
    # 3. Springet måles i rækkefølge, ikke i *sæt*. `h1 3 3 2` er et spring,
    #    selv om sættet {1,2,3} er fuldt — det er præcis den fejl, grep på
    #    "findes der et h2 på siden" misser.
    tjek("rækkefølge ikke sæt",
         spring(disposition("<h1>A</h1><h3>B</h3><h3>C</h3><h2>D</h2>")) == [(1, 3)])
    # 4. Et nyt afsnit efter et h3 er ikke et spring.
    tjek("h3 efterfulgt af h2 er grøn",
         spring(disposition("<h1>A</h1><h2>B</h2><h3>C</h3><h2>D</h2>")) == [])
    # 5. Spring i dybden tæller lige så vel: 2 → 4 springer 3.
    tjek("h2→h4 er rød",
         spring(disposition("<h1>A</h1><h2>B</h2><h4>C</h4>")) == [(2, 4)])
    # 6. `h4` under `h3` under `h2` under `h1` er grøn — dybde er ikke fejl.
    tjek("dybde uden spring er grøn",
         spring(disposition("<h1>A</h1><h2>B</h2><h3>C</h3><h4>D</h4>")) == [])
    # 7. Kode er ikke indhold. Vores egen JS bygger overskrifter som strenge, så
    #    uden denne regel får porten rød på sider der er korrekte.
    tjek("script og kommentar tæller ikke",
         spring(disposition(
             '<script>el.innerHTML += "<h3>Total visits</h3>";</script>'
             '<!-- <h3>Udkast</h3> -->'
             '<style>.x::after{content:"<h3>"}</style>'
             '<h1>A</h1><h2>B</h2>')) == [])
    # 8. Tomme overskrifter kan ikke dømmes. `blog/macos-menu-bar-website-monitor`
    #    har `<h3>` i en JSON-LD-blok og tomme rester i faner.
    tjek("tom overskrift springer ikke",
         spring(disposition("<h1>A</h1><h3>  </h3><h2>B</h2>")) == [])
    # 9. Tags og entities i overskriften er indhold, så de gør den dømt.
    tjek("tags i overskriften er indhold",
         spring(disposition("<h1>A</h1><h3><em>B</em> &amp; C</h3>")) == [(1, 3)])
    # 10. Mutation: målingen skal være grøn på `site/` — ellers er den ude i
    #     gaten og blokerer deploys for en fejl, der ikke findes.
    med_fejl = dom(SITE)
    tjek("målingen er grøn på site/", not med_fejl, "; ".join(med_fejl[:3]))
    # 11. Mutation: læg den fundne fejlform ind i en syntetisk side, og porten
    #     skal dømme den — ellers er kontrol 10 grøn fordi porten intet ser.
    #     Den syntetiske side er en kopi af `clean-copy-cli-ref.html` før
    #     rettelsen: h1 og en bunke h3, intet h2.
    with tempfile.TemporaryDirectory() as tmp:
        rod = Path(tmp)
        (rod / "spring.html").write_text(
            "<h1>Ref</h1><h3>Basic usage</h3><h3>Flags</h3>", encoding="utf-8")
        fund = dom(rod)
        tjek("syntetisk spring er rød", len(fund) == 1, str(fund))
        tjek("springet er navngivet",
             any("<h1> → <h3>" in f for f in fund), str(fund))
        # 12. Mutation: samme side efter rettelsen skal være grøn igen, så
        #     porten kan ikke være grøn fordi den afviser alt.
        (rod / "spring.html").write_text(
            '<h1>Ref</h1><h2 class="sub">Basic usage</h2>'
            '<h2 class="sub">Flags</h2>', encoding="utf-8")
        tjek("rettet side er grøn", dom(rod) == [], str(dom(rod)))
        # 13. Mutation: to spring på én side skal give to domme, ikke ét. En
        #     port der kun rapporterer det første spring lader det næste stå.
        (rod / "spring.html").write_text(
            "<h1>A</h1><h3>B</h3><h3>C</h3><h2>D</h2><h4>E</h4><h3>F</h3>",
            encoding="utf-8")
        fund = dom(rod)
        tjek("to spring giver to domme", len(fund) == 2, str(fund))

    for linje in fejl:
        print(f"  FEJL  {linje}")
    print(f"check-heading-levels-selftest: {'OK' if not fejl else 'RØD'}"
          f" ({13 - len(fejl)}/13 kontroller)")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true",
                        help="vis hvilke sider der dømmes, kun talt")
    parser.add_argument("--self-test", action="store_true",
                        help="kør portens egen kontrol af sig selv")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    fund = dom()
    for linje in fund:
        print(linje)
    sider = len({l.split(" i ", 1)[1].split(":", 1)[0] for l in fund})
    antal = len(list(SITE.rglob("*.html")))
    if args.list:
        dømt = {l.split(" i ", 1)[1].split(":", 1)[0] for l in fund}
        print(f"\nheading-levels: {len(dømt)} af {antal} sider dømt")
        return 1 if fund else 0
    if fund:
        print(f"\nheading-levels: RØD — {len(fund)} spring på {sider} sider")
        return 1
    print(f"heading-levels: GRØN — ingen spring i dispositionen på nogen af "
          f"{antal} sider i site/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
