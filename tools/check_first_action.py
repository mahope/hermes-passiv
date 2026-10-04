#!/usr/bin/env python3
"""Dom den første handling over folden på de sider, der har trafik.

Målt 30/9: `/blog/text-on-image-contrast-check` var Mahope.tools' mest besøgte
side i 28 dage (8 af 15 besøgende) med 100 % bounce. Årsagen lå i folden: heroens
`btn-primary` var «See how it works» — et anker ned i artiklen — mens selve
værktøjet var `btn-secondary`. Lige under `</header>` stod to mere `btn-primary`
(Den scanner-CTA og AI-CTA'en, indsat af `tools/add_top_cta_495.py` og
`tools/add_ai_cta.py`), så læseren mødte tre ens knapper hvoraf ingen gav det
han kom for. Samme måling over hele `site/`: **182 af de 224 sider med en hero
har 2–3 `btn-primary` over folden**, og på mange af dem er heroens egen primære
et anker (`#content`, `#how`, `#checklist`) frem for det værktøj, siden handler om.

Samme fejlform som den betalte port fangede, på den gratis side: en side *har*
en købsvej, men vejen til den er den, læseren skal finde. Ratchetet her er derfor
per *rute med forventet destination* og ikke per rute, så en ombytning af to
`href` bliver rød — ellers ville porten være grøn fordi siden stadig har en
primær handling, bare den forkert.

**Hvad porten dømmer, og hvad den kun tæller.** Den dømmer de sider, der står i
`tools/first_action.json`: præcis én `btn-primary` i foldregionen, den skal være
regionens første link, og den skal pege på den ratchetede rute. De øvrige 182
sider **tælles** og skrives ud i hver kørsel, men dømmes ikke — de er en samlet
beslutning (se ❓ i `IMPLEMENTATION_PLAN.md`), ikke 182 små rettelser. En port der
lovede at dømme dem, ville være løgnen over det den faktisk kan se.

    python3 tools/check_first_action.py            # dom de ratchetede sider
    python3 tools/check_first_action.py --list     # hvad er dømt, og hvorfor
    python3 tools/check_first_action.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
RATCHET = ROOT / "tools" / "first_action.json"

HERO_RE = re.compile(
    r'<div class="hero">(.*?)\n</div>|<header class="hero">(.*?)</header>', re.S)
BANNER_RE = re.compile(r'<div class="blog-tool-cta(?: ai-cta)?">.*?</div>', re.S)
A_RE = re.compile(r"<a\b([^>]*)>")
HREF_RE = re.compile(r'href="([^"]*)"')
CLASS_RE = re.compile(r'class="([^"]*)"')


def fold_region(html: str) -> str:
    """Alt hvad en læser ser på første skærm: heroen og de CTA-bannere der
    ligger mellem `</header>` og det første `<section>`.

    Bannerne tæller med, fordi de *er* over folden — de er bare ikke i heroen.
    En port der kun læste `<header>` ville have sagt grøn på præcis den side,
    der har tre knapper oven på folden.
    """
    match = HERO_RE.search(html)
    if match is None:
        return ""
    region = match.group(1) or match.group(2) or ""
    rest = html[match.end():]
    stop = rest.find("<section")
    for banner in BANNER_RE.findall(rest if stop == -1 else rest[:stop]):
        region += banner
    return region


def handlinger(region: str) -> list[tuple[str, str]]:
    """`(href, classes)` for hvert link i foldregionen, i dokumentrækkefølge."""
    fund: list[tuple[str, str]] = []
    for attributer in A_RE.findall(region):
        href = HREF_RE.search(attributer)
        if href is None:
            continue
        klasser = CLASS_RE.search(attributer)
        fund.append((href.group(1), klasser.group(1) if klasser else ""))
    return fund


def fejl_for(html: str, forventet: str) -> list[str]:
    """Alt der gør siden's første skærm uforståelig, som lister."""
    region = fold_region(html)
    if not region:
        return ["foldregionen findes ikke (ingen `<div class=\"hero\">` eller "
                "`<header class=\"hero\">`)"]
    links = handlinger(region)
    primære = [href for href, klasser in links if "btn-primary" in klasser.split()]
    fund: list[str] = []
    if len(primære) == 0:
        fund.append("ingen btn-primary i foldregionen")
    elif len(primære) > 1:
        fund.append(f"{len(primære)} btn-primary i foldregionen "
                    f"({', '.join(primære)}) — læseren skal selv vælge")
    if links and "btn-primary" in links[0][1].split() and len(primære) == 1:
        if links[0][0] != forventet:
            fund.append(f"første link er {links[0][0]}, ikke {forventet}")
    elif primære and forventet not in primære:
        fund.append(f"den primære handling er {primære[0]}, ikke {forventet}")
    # Målet skal også findes. Ratchetets formkontrol siger at handlingen er den
    # samme som sidste gang; den siger intet om at `#ankeret` stadig findes, og
    # et anker uden mål er en knap der flytter læseren ingen steder. Kun
    # `#`-destinationer — en rute (`/free-tools`) kan ikke dømmes her, fordi den
    # er en fil i `dist/`, ikke i kilden.
    if forventet.startswith("#") and f'id="{forventet[1:]}"' not in html:
        fund.append(f"handlingen peger på {forventet}, men siden har ingen "
                    f'`id="{forventet[1:]}"` — ankeret er dødt')
    return fund


def ratchet() -> dict[str, str]:
    data = json.loads(RATCHET.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def dom() -> tuple[list[str], dict[str, list[str]]]:
    fund: list[str] = []
    detaljer: dict[str, list[str]] = {}
    for kilde, forventet in ratchet().items():
        fil = ROOT / kilde
        if not fil.exists():
            fund.append(f"{kilde}: filen findes ikke, så folden kan ikke dømmes")
            detaljer[kilde] = ["filen findes ikke"]
            continue
        problemer = fejl_for(fil.read_text(encoding="utf-8", errors="replace"), forventet)
        detaljer[kilde] = problemer
        fund.extend(f"{kilde}: {p}" for p in problemer)
    return fund, detaljer


def maalt_uden_domslutning() -> tuple[int, int, int]:
    """`(sider med hero, sider med >1 primær over folden, sider med 0 primære)`."""
    med_hero = flere = nul = 0
    for fil in sorted(SITE.rglob("*.html")):
        html = fil.read_text(encoding="utf-8", errors="replace")
        if not fold_region(html):
            continue
        med_hero += 1
        primære = [h for h, k in handlinger(fold_region(html))
                   if "btn-primary" in k.split()]
        if len(primære) > 1:
            flere += 1
        elif not primære:
            nul += 1
    return med_hero, flere, nul


def self_test() -> int:
    fejl: list[str] = []
    antal = 0

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        nonlocal antal
        antal += 1
        if not sand:
            fejl.append(f"{navn}{': ' + detalje if detalje else ''}")

    hero = ('<header class="hero"><div class="hero-cta">'
            '<a href="{a}" class="btn-primary">Værktøjet</a>'
            '<a href="#how" class="btn-secondary">Se hvordan</a>'
            "</div></header>")
    # 1. Rettet form: værktøjet er den primære og det første link.
    tjek("rettet fold er grøn", not fejl_for(hero.format(a="/tool"), "/tool"))
    # 2. Den fundne fejlform: primæren er et anker, værktøjet er sekundær.
    ombyttet = hero.format(a="/tool").replace(
        '<a href="/tool" class="btn-primary">Værktøjet</a>'
        '<a href="#how" class="btn-secondary">Se hvordan</a>',
        '<a href="#how" class="btn-primary">Se hvordan</a>'
        '<a href="/tool" class="btn-secondary">Værktøjet</a>')
    tjek("anker som primær er rød", bool(fejl_for(ombyttet, "/tool")))
    # 3. To banner-knapper over folden er to valg, ikke én handling.
    med_banner = (hero.format(a="/tool") +
                  '<div class="blog-tool-cta"><span class="btc-label">Tjek en side:</span>'
                  ' <a href="/scan" class="btn-primary">Scanner</a></div>'
                  '<section><h2>Brødtekst</h2></section>')
    fund = fejl_for(med_banner, "/tool")
    tjek("banner over folden tæller med", any("2 btn-primary" in f for f in fund), str(fund))
    # 4. Samme banner *nede* i artiklen er ikke over folden og må ikke gøre rød.
    nede = (hero.format(a="/tool") + "<section><h2>Brødtekst</h2></section>"
            '<div class="blog-tool-cta"><span class="btc-label">Tjek en side:</span>'
            ' <a href="/scan" class="btn-primary">Scanner</a></div>')
    tjek("banner under artiklen er grøn", not fejl_for(nede, "/tool"))
    # 5. En ombytning af destinationerne skal være rød, også når der stadig
    #    er én primær handling — det er den fejl ratchet-per-rute ikke så.
    permutation = hero.format(a="/scan")
    tjek("forkert destination er rød",
         any("/scan" in f and "/tool" in f for f in fejl_for(permutation, "/tool")))
    # 5b. Handlingen skal pege på et `id`, der findes. Ratchetets formkontrol
    #     kan ikke se det: `#tool-heading` kan forsvinde fra siden ved en
    #     omdøbning, og så er knappen stadig grøn hos porten og død for
    #     læseren. Kun `#`-destinationer dømmes — en rute `/free-tools` er en
    #     fil i `dist/`, ikke i kilden.
    med_anker = hero.format(a="#tool-heading")
    fund = fejl_for(med_anker, "#tool-heading")
    tjek("dødt anker er rødt", any("ankeret er dødt" in f for f in fund), str(fund))
    med_mål = med_anker.replace("</header>",
                                '<h2 id="tool-heading">Værktøjet</h2></header>')
    tjek("levende anker er grønt", not fejl_for(med_mål, "#tool-heading"),
         str(fejl_for(med_mål, "#tool-heading")))
    # 6. En side uden hero kan ikke dømmes, og porten skal sige det.
    tjek("manglende hero er rød", bool(fejl_for("<p>ingen hero</p>", "/tool")))
    # 7. Ratchetfilen skal dømme hver kildefil, der står i den, og ingen anden.
    dømt = ratchet()
    tjek("ratchetets nøgler er kildefiler",
         all(k.startswith("site/") and (ROOT / k).exists() for k in dømt),
         str(sorted(dømt)))
    # 8. Målingen på den virkelige `site/` skal være grøn, ellers er 1-7 grønne
    #    fordi porten intet ser.
    fund, _ = dom()
    tjek("målingen på site/ er grøn", not fund, "; ".join(fund[:3]))
    # 9. Mutation mod de RIGTIGTE filer: bannerne flyttes op under `</header>`
    #    igen og demoteres, altså præcis den fejlform de otte artikler havde.
    #    Porten skal blive rød på den og grøn igen på den uændrede — ellers
    #    dømmer den ikke de sider, den påstår at dømme.
    with tempfile.TemporaryDirectory() as tmp:
        rod = Path(tmp)
        (rod / "tools").mkdir()
        (rod / "site").mkdir()
        for kilde in dømt:
            (rod / kilde).parent.mkdir(parents=True, exist_ok=True)
            (rod / kilde).write_text((ROOT / kilde).read_text(encoding="utf-8"), encoding="utf-8")
        (rod / "tools" / "first_action.json").write_text(
            json.dumps(dømt, ensure_ascii=False), encoding="utf-8")
        tjek("de rigtige filer er grønne i et rent udtræk", dom_med_rod(rod)[0] == [])

        muteret = 0
        for kilde in dømt:
            fil = rod / kilde
            src = fil.read_text(encoding="utf-8")
            banners = re.findall(r'<div class="blog-tool-cta(?: ai-cta)?">.*?</div>', src, re.S)
            if not banners:
                continue
            hoved, rest = src.split("</header>", 1)
            oppe = "".join(b.replace("btn-secondary", "btn-primary") for b in banners)
            fil.write_text(hoved + "</header>\n" + oppe + rest, encoding="utf-8")
            muteret += 1
        fejl_mut, _ = dom_med_rod(rod)
        tjek(f"bannerne oppe igen er rødt på alle {muteret} sider",
             muteret > 0 and len(fejl_mut) == muteret,
             f"{muteret} muteret, {len(fejl_mut)} fund: {'; '.join(fejl_mut[:2])}")
    # 10. Mutation: en syntetisk `site/` med den fundne fejlform skal være rød,
    #     også når porten kører fra en anden rod.
    with tempfile.TemporaryDirectory() as tmp:
        rod = Path(tmp)
        (rod / "site").mkdir()
        (rod / "tools").mkdir()
        (rod / "site" / "test.html").write_text(ombyttet, encoding="utf-8")
        (rod / "tools" / "first_action.json").write_text(
            json.dumps({"site/test.html": "/tool"}), encoding="utf-8")
        fejl_her, _ = dom_med_rod(rod)
        tjek("syntetisk side er rød", bool(fejl_her), str(fejl_her))
        (rod / "site" / "test.html").write_text(hero.format(a="/tool"), encoding="utf-8")
        tjek("rettet syntetisk side er grøn", dom_med_rod(rod)[0] == [])

    for linje in fejl:
        print(f"  FEJL  {linje}")
    print(f"check-first-action-selftest: {'OK' if not fejl else 'RØD'}"
          f" ({antal - len(fejl)}/{antal} kontroller)")
    return 1 if fejl else 0


def dom_med_rod(rod: Path) -> tuple[list[str], dict[str, list[str]]]:
    """Som `dom()`, men mod en midlertidig rod — bruges af selftesten."""
    data = json.loads((rod / "tools" / "first_action.json").read_text(encoding="utf-8"))
    fund: list[str] = []
    for kilde, forventet in ((k, v) for k, v in data.items() if not k.startswith("_")):
        fil = rod / kilde
        if not fil.exists():
            fund.append(f"{kilde}: filen findes ikke")
            continue
        fund.extend(f"{kilde}: {p}" for p in
                    fejl_for(fil.read_text(encoding="utf-8"), forventet))
    return fund, {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true",
                        help="vis hvad der er dømt, og hvorfor det er rødt")
    parser.add_argument("--self-test", action="store_true",
                        help="kør portens egen kontrol af sig selv")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    fund, detaljer = dom()
    med_hero, flere, nul = maalt_uden_domslutning()
    if args.list:
        for kilde, forventet in sorted(ratchet().items()):
            problemer = detaljer.get(kilde, ["filen findes ikke"])
            tilstand = "GRØN" if not problemer else "RØD"
            print(f"  {tilstand}  {kilde} → {forventet}")
            for p in problemer:
                print(f"          {p}")
        return 1 if fund else 0
    for linje in fund:
        print(linje)
    dømt = len(ratchet())
    print(f"\nfirst-action: {dømt} sider dømt, {len(fund)} problemer")
    print(f"  kun talt, ikke dømt: {flere} af {med_hero} sider med en hero har "
          f"mere end én btn-primary over folden ({nul} har nul)")
    if fund:
        print("\nfirst-action: RØD")
        return 1
    print("first-action: GRØN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
