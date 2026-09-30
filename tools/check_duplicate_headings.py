#!/usr/bin/env python3
"""Dom dublet `<h2>` med samme normaliserede tekst på én side.

Målt 30/9: 63 af 190 blogfiler havde to `<h2>` med samme tekst. På 62 af dem
var det `<section class="products">`-blokken ("Related guides" / "Relaterede
guides") og den genererede crosslink-boks ("Related Guides"), på `site/
url-to-markdown.html` var det to FAQ-sektioner. Indholdet var forskelligt —
median overlap mellem de to sektioners links var 0 af 3 — så ingen port så
fejlen: de dømmer links, priser og løfter, ikke struktur.

Det læseren mærker er indholdsfortegnelsen, som `build_sites.py` bygger af
`<h2>`: to afsnit med samme navn to gange, og en læser der leder efter det
ene afsnit ved at tælle ned. Siden er bygget af os, så det er en fejl, ikke et
designvalg.

Normaliseringen skal fange præcis den fejlform: `Related guides` og `Related
Guides` er samme afsnit for en læser, så casing og Entities (`&amp;`) tæller
ikke. Tags og indrykning inde i overskriften tæller heller ikke.

    python3 tools/check_duplicate_headings.py            # dom alle sider
    python3 tools/check_duplicate_headings.py --self-test # 12 kontroller
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

# Kun `<h2>`. `<h1>` er titlen (én pr. side) og `<h3>` ligger under sit afsnit,
# så en gentaget `<h3>` er ikke det samme symptom — det er et kort under en
# overskrift, og det er ikke i indholdsfortegnelsen.
H2_RE = re.compile(r"<h2\b[^>]*>(.*?)</h2>", re.S | re.I)
# Script, style og kommentarer er ikke indhold. En `<h2>` i en kommentar eller i
# en JSON-LD-blok tæller ikke, og tæller den, får porten en rød uden en fejl.
SPLIT_RE = re.compile(
    r"(<!--.*?-->|<(script|style|noscript|template|svg)\b.*?</\2\s*>)", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")


def normaliser(overskrift: str) -> str:
    """Hvad en læser ser i indholdsfortegnelsen, i én linje."""
    tekst = htmllib.unescape(TAG_RE.sub("", overskrift))
    return re.sub(r"\s+", " ", tekst).strip().casefold()


def dubletter(html: str) -> dict[str, int]:
    """`<h2>`-tekster der optræder mere end én gang, med antal."""
    tæller: dict[str, int] = {}
    # Skjuler det der ikke er indhold, i stedet for at splitte på det: en
    # kommentar har ingen gruppe indeni, en `<script>` har to, så indeks-paritet
    # i en split-liste afhænger af hvilken slags der blev fundet først.
    indhold = SPLIT_RE.sub("", html)
    for overskrift in H2_RE.findall(indhold):
        tekst = normaliser(overskrift)
        if tekst:
            tæller[tekst] = tæller.get(tekst, 0) + 1
    return {t: n for t, n in tæller.items() if n > 1}


def dom(root: Path = SITE) -> list[str]:
    fund: list[str] = []
    for fil in sorted(root.rglob("*.html")):
        dub = dubletter(fil.read_text(encoding="utf-8", errors="replace"))
        for tekst, antal in sorted(dub.items()):
            fund.append(
                f"DUBLET <h2> i {fil.relative_to(root)}: "
                f'"{tekst}" står {antal} gange'
            )
    return fund


def self_test() -> int:
    fejl: list[str] = []

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        if not sand:
            fejl.append(f"{navn}{': ' + detalje if detalje else ''}")

    # 1. Casing er samme afsnit for en læser — det er hele den fundne fejl.
    tjek("casing er ikke forskel",
         dubletter("<h2>Related guides</h2><h2>Related Guides</h2>") == {"related guides": 2})
    # 2. Entities og tags i overskriften er det samme afsnit.
    tjek("entities og tags er ikke forskel",
         dubletter("<h2>Tools &amp; guides</h2><h2>Tools &amp; guides</h2>") == {"tools & guides": 2}
         and dubletter('<h2><em>Priser</em></h2><h2>Priser</h2>') == {"priser": 2})
    # 3. To forskellige afsnit er ikke en fejl.
    tjek("forskellige afsnit er grønne",
         dubletter("<h2>Priser</h2><h2>Om os</h2>") == {})
    # 4. Indrykning og linjeskift i tagget er ikke forskel.
    tjek("linjeskift i tagget er ikke forskel",
         dubletter('<h2\n  class="x">Om os</h2><h2>Om os</h2>') == {"om os": 2})
    # 5. Kode er ikke indhold: en `<h2>` i en kommentar eller i JSON-LD må
    #    ikke gøre porten rød, ellers får den en rød uden en fejl.
    tjek("kommentar og JSON-LD tæller ikke",
         dubletter('<!-- <h2>Om os</h2> --><h2>Om os</h2>'
                   '<script>{"a":"<h2>Om os</h2>"}</script>') == {})
    # 6. Tom `<h2>` kan ikke dømmes og må ikke slå en dublet.
    tjek("tom overskrift tæller ikke",
         dubletter("<h2>  </h2><h2>Om os</h2>") == {})
    # 7. Mutation: den virkelige fejlform fra `site/` skal være rød.
    med_fejl = dom(SITE)
    tjek("målingen er grøn på site/", not med_fejl, "; ".join(med_fejl[:3]))
    # 8. Mutation: læg den fundne fejlform ind i en syntetisk side, og porten
    #    skal dømme den — elvis er check 7 grøn fordi porten intet ser.
    with tempfile.TemporaryDirectory() as tmp:
        rod = Path(tmp)
        (rod / "syntetisk.html").write_text(
            "<h2>Related guides</h2><h2>Related Guides</h2>", encoding="utf-8")
        (rod / "ren.html").write_text("<h2>Om os</h2><h2>Priser</h2>", encoding="utf-8")
        tjek("syntetisk dublet er rød", len(dom(rod)) == 1, str(dom(rod)))
        # 9. Mutation: samme side efter rettelsen skal være grøn igen, så
        #    porten kan ikke være grøn fordi den afviser alt.
        (rod / "syntetisk.html").write_text(
            "<h2>Tools and guides</h2><h2>Related Guides</h2>", encoding="utf-8")
        tjek("rettet side er grøn", dom(rod) == [], str(dom(rod)))
    # 10. Mutation: en side der *mister* sin anden `<h2>` må ikke blive rød,
    #     fordi normaliseringen af enlig tekst ikke dømmer sig selv.
    with tempfile.TemporaryDirectory() as tmp:
        rod = Path(tmp)
        (rod / "a.html").write_text("<h2>Om os</h2><h2>Om os</h2>", encoding="utf-8")
        tjek("dublet på en fil er rød", len(dom(rod)) == 1)
        (rod / "a.html").write_text("<h2>Om os</h2>", encoding="utf-8")
        tjek("enlig overskrift er grøn", dom(rod) == [])

    for linje in fejl:
        print(f"  FEJL  {linje}")
    print(f"check-duplicate-headings-selftest: {'OK' if not fejl else 'RØD'}"
          f" ({10 - len(fejl)}/10 kontroller)")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="kør portens egen kontrol af sig selv")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    fund = dom()
    for linje in fund:
        print(linje)
    sider = len({l.split(" i ", 1)[1].split(":", 1)[0] for l in fund})
    if fund:
        print(f"\nduplicate-headings: RØD — {len(fund)} dubletter på {sider} sider")
        return 1
    print("duplicate-headings: GRØN — ingen dublet <h2> på nogen side i site/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
