#!/usr/bin/env python3
"""Dom at `/blog/` faktisk er «every guide on this site».

Målt 2/10: siden siger i sin egen `<meta name="description">` «Every guide on
this site», men `site/` rummede 93 engelske og 96 danske guides, og siden linkede
**86** og **83**. To typer lå uden for enhver liste på siden: de var skrevet
efter den sidste gang generatoren kørte, og intet dømte det. Så læser de 20 artikler
— blandt dem `get-notified-when-website-goes-down`,
`macos-menu-bar-website-monitor`, `website-metadata-checker` og hele rækken af
danske modstående — kun via sitemap.

**Hvorfor det er mere end en manglende linje.** Bloggen er 189 artikler på
tværs af fire domæner, og den er den eneste interne vej til dem: søgemaskiner
rankerede artikler efter de links der peger på dem, og en læser der lander på
`/blog/` leder efter «find alle sider». Så snart generatoren kører igen uden at
nogen kigger, kommer samme fejl tilbage helt stille — ingen undtagelse, ingen
konsolefejl, kun en side der lyver om sig eget indhold.

**De tre krav porten dømmer.**

1. *Dækning*: hver guidefil i `site/blog/` og `site/da/blog/` skal have præcis ét
   link fra `site/blog/index.html`. Ikke kun de nye — heller ikke de gamle, for
   det er en håndredderet forældet `href` der lå i den gamle kode.
2. *Tallet i heroen*: «{n} English guides … plus {nda} Danish guides» skal være
   de rigtige tal. Ellers retter en ny guide ikke antallet, og siden får en ny
   løgnest.
3. *Generatoren ejer filen*: den committede side skal være **byte-identisk** med
   `python3 tools/make_blog_index.py --out <tmp>`. Det er det eneste krav der
   fanger en redigering i hånden — også en *god* en, som bogs-CTA'en og det
   afsluttende track-script var. Derfor skrev `9f07a09`-runden dem ind i
   generatoren i stedet for at lappe siden; porten er grunden til at det holder.

Kør selvtesten, før du stoler på porten: den muterer de rigtige filer og
fordriver dem igen.

    python3 tools/check_blog_index.py
    python3 tools/check_blog_index.py --list
    python3 tools/check_blog_index.py --self-test
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "site" / "blog" / "index.html"
GENERATOR = ROOT / "tools" / "make_blog_index.py"

HREF_RE = re.compile(r'href="(/(?:da/)?blog/([^"/]+))"')
HERO_RE = re.compile(r"(\d+) English guides on .*? plus (\d+) Danish guides", re.S)


def guide_slugs(folder: Path) -> list[str]:
    return sorted(p.stem for p in folder.glob("*.html") if p.stem != "index")


def fejl_mod(html: str, en: list[str], da: list[str]) -> list[str]:
    fund: list[str] = []
    links: dict[str, list[str]] = {}
    for href, slug in HREF_RE.findall(html):
        links.setdefault(slug, []).append(href)

    for sprog, slugs in (("EN", en), ("DA", da)):
        for slug in slugs:
            fund_hrefs = links.get(slug)
            if not fund_hrefs:
                fund.append(
                    f"  {sprog}-guide `{slug}` har intet link fra /blog/ — "
                    f"kør `python3 tools/make_blog_index.py`")
            elif len(fund_hrefs) > 1:
                fund.append(
                    f"  {sprog}-guide `{slug}` linkes {len(fund_hrefs)} gange "
                    f"({', '.join(sorted(set(fund_hrefs)))})")
        # En dansk slug må ikke hænge på en /blog/-sti og omvendt.
        for slug, hrefs in links.items():
            for href in hrefs:
                dansk_href = href.startswith("/da/")
                er_dansk_fil = (ROOT / "site" / "da" / "blog" / f"{slug}.html").exists()
                if dansk_href != er_dansk_fil:
                    fund.append(
                        f"  linket `{href}` peger på den {'engelske' if dansk_href else 'danske'} "
                        f"fil `{slug}.html`")

    hero = HERO_RE.search(html)
    if not hero:
        fund.append("  heroen har ingen «N English guides … plus N Danish guides»-sætning "
                    "at tælle imod")
    else:
        n_en, n_da = int(hero.group(1)), int(hero.group(2))
        if (n_en, n_da) != (len(en), len(da)):
            fund.append(f"  heroen siger {n_en} engelske og {n_da} danske guides, "
                        f"men `site/` har {len(en)} og {len(da)}")
    return fund


def genereret(tmp: Path) -> str | None:
    out = tmp / "blog-index.html"
    res = subprocess.run([sys.executable, str(GENERATOR), "--out", str(out)],
                         cwd=ROOT, capture_output=True, text=True)
    if res.returncode != 0 or not out.exists():
        return None
    return out.read_text(encoding="utf-8")


def dom(index: Path = INDEX) -> tuple[list[str], dict[str, str]]:
    en = guide_slugs(ROOT / "site" / "blog")
    da = guide_slugs(ROOT / "site" / "da" / "blog")
    tekst = index.read_text(encoding="utf-8")
    fund = fejl_mod(tekst, en, da)
    detaljer = {}
    with tempfile.TemporaryDirectory() as tmp:
        ny = genereret(Path(tmp))
        if ny is None:
            fund.append("  `tools/make_blog_index.py --out` kørte ikke, så "
                        "generatorens ejerskab kan ikke dømmes")
        elif ny != tekst:
            detaljer["generator"] = (
                "  site/blog/index.html er ikke lig den genererede side — "
                "kør `python3 tools/make_blog_index.py` (eller skriv ændringen "
                "ind i generatoren, så den overlever næste kørsel)")
    return fund, detaljer


def self_test() -> int:
    fejl: list[str] = []
    antal = 0

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        nonlocal antal
        antal += 1
        if not sand:
            fejl.append(f"{navn}{': ' + detalje if detalje else ''}")

    rigtig = INDEX.read_text(encoding="utf-8")
    en = guide_slugs(ROOT / "site" / "blog")
    da = guide_slugs(ROOT / "site" / "da" / "blog")
    fund = fejl_mod(rigtig, en, da)
    # 1. Den committede side er grøn, ellers er 2-6 grønne for intet.
    tjek("committede /blog/ er grøn", not fund, "; ".join(fund[:3]))

    # 2. Den fejlform porten findes for: en ny guide uden link.
    ny_guide = da[0]
    uden = rigtig.replace(f'href="/da/blog/{ny_guide}"', 'href="/da/blog/ukendt-guide"')
    tjek("DA-guide uden link er rød",
         any(ny_guide in f for f in fejl_mod(uden, en, da)))

    # 3. Samme for en engelsk.
    ny_en = en[0]
    uden_en = rigtig.replace(f'href="/blog/{ny_en}"', 'href="/blog/ukendt-guide"')
    tjek("EN-guide uden link er rød",
         any(ny_en in f for f in fejl_mod(uden_en, en, da)))

    # 4. Tallet i heroen skal dømmes for sig selv: samme links, ét tal for lavt.
    forkert_tal = rigtig.replace(f"{len(en)} English guides", f"{len(en) - 1} English guides")
    tjek("forkert antal i heroen er rød",
         any("heroen siger" in f for f in fejl_mod(forkert_tal, en, da)))

    # 5. En dansk guide linket med den engelske sti er rød — det er den
    #    ombytning, kun dækning på slugs ville overse.
    ombyttet = rigtig.replace(f'href="/da/blog/{ny_guide}"', f'href="/blog/{ny_guide}"')
    tjek("DA-guide på /blog/-sti er rød",
         bool(fejl_mod(ombyttet, en, da)))

    # 6. Samme guide linket to gange er rød: det er en dublet, ikke dækning.
    dobbelt = rigtig.replace(f'href="/blog/{ny_en}"',
                             f'href="/blog/{ny_en}"><!--x--><a href="/blog/{ny_en}"')
    tjek("dobbeltlink er rød",
         any("linkes 2 gange" in f for f in fejl_mod(dobbelt, en, da)))

    # 7. Generatoren skal eje filen: en håndredigering af den rigtige side skal
    #    give rødt, uanset at links og tal stadig er i orden.
    with tempfile.TemporaryDirectory() as tmp:
        rod = Path(tmp)
        (rod / "site" / "blog").mkdir(parents=True)
        (rod / "site" / "da" / "blog").mkdir(parents=True)
        (rod / "tools").mkdir()
        hånd = rigtig.replace('<div class="badge">BLOG</div>',
                              '<div class="badge">BLOG (håndskrevet)</div>')
        (rod / "site" / "blog" / "index.html").write_text(hånd, encoding="utf-8")
        (rod / "tools" / "make_blog_index.py").write_text(
            GENERATOR.read_text(encoding="utf-8"), encoding="utf-8")
        fund2, detalje = dom(rod / "site" / "blog" / "index.html")
        tjek("håndskrevet side er rød mod generatoren",
             "generator" in detalje, str(detalje))
        fund3, detalje3 = dom()
        tjek("uændret side er grøn mod generatoren",
             not fund3 and not detalje3, "; ".join(fund3[:3]))

    # 8. Målingen på de rigtige filer skal være grøn — ellers dømmer resten
    #    ingenting, fordi `en`/`da` er tomme.
    tjek(f"{len(en)} EN + {len(da)} DA guides målte", len(en) > 80 and len(da) > 80,
         f"en={len(en)} da={len(da)}")

    for linje in fejl:
        print(f"  FAIL {linje}")
    print(f"blog-index-selftest: {antal - len(fejl)}/{antal}")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true",
                        help="vis dækningstal for begge sprog")
    parser.add_argument("--self-test", action="store_true",
                        help="kør portens egen kontrol af sig selv")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    fund, detaljer = dom()
    en = guide_slugs(ROOT / "site" / "blog")
    da = guide_slugs(ROOT / "site" / "da" / "blog")
    html = INDEX.read_text(encoding="utf-8")
    links = {slug for _href, slug in HREF_RE.findall(html)}
    if args.list:
        for sprog, slugs in (("EN", en), ("DA", da)):
            mangler = [s for s in slugs if s not in links]
            print(f"  {sprog}: {len(slugs) - len(mangler)}/{len(slugs)} linket fra /blog/")
            for s in mangler:
                print(f"        mangler: {s}")
        return 1 if fund else 0
    for linje in fund:
        print(linje)
    for linje in detaljer.values():
        print(linje)
    print(f"\nblog-index: {len(en)} EN + {len(da)} DA guides, "
          f"{len(fund) + len(detaljer)} problemer")
    if fund or detaljer:
        print("blog-index: RØD")
        return 1
    print("blog-index: GRØN")
    return 0


if __name__ == "__main__":
    sys.exit(main())