#!/usr/bin/env python3
"""Dom at scannerens eget felt ligger i folden — og at et klik fører til noget.

**Hullet.** Målt 5/10 på kilden og i `site/`: `/scan` er mål for **559**
interne links på **228** sider (optalt med `html.parser` over hele `site/`, så
tælleren ignorerer de 4 fund i `dist/`-kopierne), og den er toppen af den
dyreste betalte linje — EUComply Pro, **$79/år pr. website**. `/api/results`
læser **0** resultater i **28** dage, og `/api/conversion` **0**
`pro-card-clicks`. Folden var imidlertid ikke en tom marketing-banner: den var
`FREE TOOL` + `<h1>` + tagline og så et tomt `required`-felt i det første
afsnit af `<main>` — altså præcis det de **otte** værktøjssider fik deres egen
handling over folden for (opgave 6). Samme mønster som
`/text-on-image-checker`, hvor dommen flyttede fra 1739 px til 601 px.

Der er **to** ting, fordi den første alene gør klikket dødt:

1. `<form id="scanForm">` ligger **inde i `<header class="hero">`**, før
   `</header>`. Ikke et link til feltet — feltet.
2. Knappen bruger husets `btn-primary`. Den egne regel `.scanbox button`
   (0,1,1) lå oven i `.btn-primary` (0,1,0) og lagde sin egen `#0b6e8f` på den,
   så scannerens ene primære handling så anderledes ud end de otte andre sider
   den er bygget sammen med. Porten dømmer derfor også at siden **ikke**
   definerer `background` for `.scanbox button`.

Og en tredje ting, fordi flytningen flytter resultatet væk fra knappen:
`#result` ligger under folden (et resultat er langt og må ikke fylde heroen), så
et klik i folden ville intet gøre synligt. Derfor skal alle **tre** skrivninger
til `#result` kalde `revealResult(out)`, som kun ruller når `#result` ikke
allerede kan ses — ellers ville et læst resultat hoppe op ved hvert skærmbillede.

**Porten dømmer kilden, ikke en browser** (samme begrænselse som
`check_verdict_first.py`): den dømmer de ting der *ville* flytte feltet ud af
folden eller slå klikket dødt. Polaritet målt på de rigtige filer —
`--self-test` flytter formularen tilbage til `<main>`, giver knappen
`class="btn"`, lægger `.scanbox button { background: … }` tilbage, fjerner
`revealResult` og efterlader `#result` i heroen — alle fem skal blive **RØD**.
Den skal også have været **RØD** på den gamle kode, og det er den mutation der
ligger i samme diff.

    python3 tools/check_scan_fold.py
    python3 tools/check_scan_fold.py --self-test
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIDER = (ROOT / "site" / "scan.html", ROOT / "site" / "scan-da.html")

RE_HTML_KOMMENTAR = re.compile(r"<!--.*?-->", re.S)
RE_SCANBOX_BTN_BG = re.compile(r"\.scanbox\s+button[^{]*\{[^}]*\bbackground\b", re.S)


def ryd(tekst: str) -> str:
    return re.sub(r"\s+", " ", tekst).strip()


def hero(html: str) -> tuple[str, str]:
    """(heroens markup, resten af siden efter `</header>`)."""
    start = re.search(r'<header\b[^>]*class="[^"]*\bhero\b[^"]*"[^>]*>', html)
    if not start:
        return "", ""
    slut = html.find("</header>", start.end())
    if slut == -1:
        return html[start.end():], ""
    return html[start.end():slut], html[slut + len("</header>"):]


def dom(tekst: str) -> list[str]:
    """Fund for én sides kildemarkup. Tom liste = grøn."""
    html = RE_HTML_KOMMENTAR.sub("", tekst)
    heroen, resten = hero(html)
    grunde: list[str] = []

    if not heroen:
        return ["`<header class=\"hero\">` findes ikke, så «i folden» er udefineret"]

    # 1. Formularen i heroen — præcis én, og den skal være der.
    formularer = re.findall(r'<form\b[^>]*\bid="scanForm"[^>]*>', html)
    if not formularer:
        grunde.append("`id=\"scanForm\"` findes ikke i markup'en")
        return grunde
    if len(formularer) > 1:
        grunde.append(f"der er {len(formularer)} `id=\"scanForm\"` — scanneren skal kun have ét felt")
    if heroen.find('id="scanForm"') == -1:
        grunde.append("`<form id=\"scanForm\">` ligger **ikke** i `<header class=\"hero\">`, "
                      "altså under folden — det er præcis det hullet var")

    # 2. Husets knap, ikke sidens egen farve.
    knap = re.search(r'<button\b[^>]*type="submit"[^>]*>', heroen)
    if not knap:
        grunde.append("`heroen` har ingen `<button type=\"submit\">`")
    else:
        klasser = knap.group(0)
        if "btn-primary" not in klasser:
            grunde.append("knappen i heroen bruger ikke `btn-primary`, så scannerens ene "
                          "primære handling ikke ser ud som de andre værktøjssiders")
    if RE_SCANBOX_BTN_BG.search(html):
        grunde.append("siden definerer `background` for `.scanbox button` — den har højere "
                      "specificitet end `.btn-primary` og lægger sin egen farve oven i husets")

    # 3. `#result` skal være under heroen, og alle tre skrivninger skal rulle den frem.
    if len(re.findall(r'id="result"', html)) != 1:
        grunde.append(f"der er {len(re.findall(chr(34) + 'result' + chr(34), html))} `id=\"result\"`")
    if resten.find('id="result"') == -1:
        grunde.append("`#result` ligger i heroen — et resultat er langt og skal ikke fylde folden")
    kald = len(re.findall(r"revealResult\(out\)\s*;", html))
    if kald < 3:
        grunde.append(f"`revealResult(out)` kaldes {kald} gang — de tre skrivninger til "
                      "`#result` (scanning i gang, fejl og resultat) skal alle rulle den frem, "
                      "så et klik i folden ikke ser ud til at gøre noget")

    return grunde


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true",
                    help="kør mutationerne på de rigtige filer; alle skal give RØD")
    args = ap.parse_args()

    def kør(over: dict[Path, str]) -> dict[str, list[str]]:
        return {p.name: dom(over.get(p, p.read_text(encoding="utf-8"))) for p in SIDER}

    fund: list[str] = []
    for navn, grunde in kør({}).items():
        for g in grunde:
            fund.append(f"{navn}: {g}")

    if fund:
        print(f"check_scan_fold: RØD — {len(fund)} fund")
        for f in fund:
            print(f"  - {f}")
        return 1
    print("check_scan_fold: GRØN — formularen ligger i folden i begge sprog, knappen bruger "
          "`btn-primary`, og alle tre skrivninger til `#result` ruller den frem")

    if not args.self_test:
        return 0

    def til_main(tekst: str) -> str:
        """1. Flyt formularen tilbage til `<main>`."""
        m = re.search(r"\n[ \t]*<form id=\"scanForm\".*?</form>", tekst, re.S)
        if not m:
            return tekst
        formular = m.group(0).strip()
        rest = tekst[:m.start()] + tekst[m.end():]
        anker = '<main class="container">'
        return rest.replace(anker, anker + "\n" + formular, 1)

    def egen_knap(tekst: str) -> str:
        """2. Giv knappen sin egen klasse igen."""
        return tekst.replace('<button type="submit" class="btn-primary">',
                             '<button type="submit" class="btn">', 1)

    def egen_farve(tekst: str) -> str:
        """3. Læg `.scanbox button { background: … }` tilbage."""
        return tekst.replace("  @media (max-width: 460px)",
                             "  .scanbox button { background: #0b6e8f; color: #fff; }\n"
                             "  @media (max-width: 460px)", 1)

    def uden_reveal(tekst: str) -> str:
        """4. Fjern alle `revealResult(out);`-kald (men ikke definitionen)."""
        return tekst.replace("\n  revealResult(out);", "").replace("\n    revealResult(out);", "")

    def resultat_i_heroen(tekst: str) -> str:
        """5. Flyt `#result` op i heroen — den skal så dømmes på sin *plads*."""
        start = re.search(r'<header\b[^>]*class="[^"]*\bhero\b[^"]*"[^>]*>', tekst)
        m = re.search(r'[ \t]*<div id="result"[^>]*></div>\n', tekst)
        if not start or not m or m.start() < start.end():
            return tekst
        ryd_resultat = m.group(0).strip()
        uden = tekst[:m.start()] + tekst[m.end():]
        hero_slut = uden.find("</header>", start.end())
        return uden[:hero_slut] + ryd_resultat + "\n  " + uden[hero_slut:]

    mutationer = [
        ("formularen flyttet tilbage til <main>", til_main),
        ("knappen uden btn-primary", egen_knap),
        (".scanbox button får sin egen background igen", egen_farve),
        ("revealResult-kaldene fjernet", uden_reveal),
        ("#result flyttet op i heroen", resultat_i_heroen),
    ]

    fejl = 0
    for beskrivelse, mut in mutationer:
        over = {}
        rørte = 0
        for p in SIDER:
            ny = mut(p.read_text(encoding="utf-8"))
            if ny != p.read_text(encoding="utf-8"):
                over[p] = ny
                rørte += 1
        if rørte == 0:
            print(f"  SELFTEST: FEJL — mutationen «{beskrivelse}» ændrede ingen fil")
            fejl += 1
            continue
        resultat = kør(over)
        røde = [f"{navn}: {g}" for navn, grude in resultat.items() for g in grude]
        if røde:
            print(f"  SELFTEST OK — {beskrivelse} → RØD ({røde[0][:110]})")
        else:
            print(f"  SELFTEST: FEJL — «{beskrivelse}» gav stadig GRØN")
            fejl += 1

    # Polaritet: en helt ny fil skal give grunde, ikke crash'e.
    with tempfile.TemporaryDirectory() as tmp:
        tom = Path(tmp) / "scan.html"
        tom.write_text("<!doctype html><html><body><p>tom</p></body></html>", encoding="utf-8")
        if dom(tom.read_text(encoding="utf-8")):
            print("  SELFTEST OK — en side uden hero giver en grund")
        else:
            print("  SELFTEST: FEJL — en side uden hero gav ingen grund")
            fejl += 1

    if fejl:
        print(f"check_scan_fold --self-test: {fejl} fejl")
        return 1
    print(f"check_scan_fold --self-test: alle {len(mutationer)} mutationer er RØD")
    return 0


if __name__ == "__main__":
    sys.exit(main())