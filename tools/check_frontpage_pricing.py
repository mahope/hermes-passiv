#!/usr/bin/env python3
"""Dom at forsiden kan finde alle 13 produkter — ikke kun de 2 den nævner.

Målt 5/10 på Plausible (28 dage): `mahope.tools/` havde **6** besøgende og
**100 %** bounce, og `deskuptime.com/` **7** med **100 %**. Kilderne var Direct
og None, altså ingen søgemaskine endnu. Så tallerne er for små til at dømme en
forside med — de kan kun pege på, hvor det først var værd at kigge.

Kigget fandt en strukturel mangel, ikke en tekstmangel: `#products` på forsiden
lister **2** produkter (`page-profile` og EU Compliance Report), og **0**
af sidens links pegede på `/pricing` — den eneste side der viser alle **13**
katalogprodukter med pris. `/free-tools` linkede til den to steder; forsiden
gjorde ingen steder. Så en læser der landede på forsiden og ville vide, hvad
Clean Copy Pro eller NIS2-skabelonsættet kostede, skulle ramme `/free-tools`
eller gætte en URL. Det er den egenskab kontrakten kalder *konvertering*, og den
er usynlig i en diff: intet var brudt, intet var forkert, en vej manglede.

**De tre krav porten dømmer.**

1. *Forsiden linker til hele listen* — i begge sprog, og hver sprogversion peger
   på sin egen. Uden `/pricing` (EN) og `/da/pricing` (DA) i salgsafsnittet er
   de 11 øvrige produkter ubefærdelige fra forsiden igen.
2. *Listen findes* — den rute forsiden peger på skal være en fil i `site/`, så
   linket ikke kan være en 404 der ligner en købsvej.
3. *Salgsafsnittet findes overhovedet* — på den danske forside har afsnittet
   intet `id` (målt 5/10), så porten leder efter det på sin `<h2>`. Uden denne
   dom ville en forside hvor afsnittet er omdøbt være grøn, fordi resten af
   kravene så ingen sider at dømme.

**Hvorfor ikke bare læse `$`-beløb.** `check_own_prices.py` dømmer beløb, og
`check_pricing_page.py` dømmer at `/pricing` viser katalogens priser. Ingen af
dem dømmer *vejen dertil* — det er præcis den mangel der lå her, og de to
porter var grønne hele vejen.

Kør selvtesten, før du stoler på porten. Den skriver de rigtige filer, kalder
porten på dem og fordriver dem igen.

    python3 tools/check_frontpage_pricing.py
    python3 tools/check_frontpage_pricing.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "tools" / "stripe_catalog.json"
EN_INDEX = ROOT / "site" / "index.html"
DA_INDEX = ROOT / "site" / "da" / "index.html"

# Kun `#products`-afsnittet. Navigation og footer er ikke dømt her: det er den
# købsvej i kroppen der skal findes, og en evt. footer-link er en gave, ikke
# kravet. En evt. footer der engang fjerner et link skal ikke rødme porten for
# en hensigt den ikke kan se.
# Kun det afsnit der sælger. På engelsk hedder det `id="products"`; den danske
# forside har **intet** id på samme afsnit (målt 5/10 — kun `id="check"` og
# `id="faq"` findes der), så porten finder den på den `<h2>` der indleder den,
# uanset om et id er sat. Det er derfor der er to mønstre: ellers ville den
# danske forside være «fundet, men uden id»-rød for en mangel der ikke findes.
SECTION_EN_RE = re.compile(r'<section id="products">.*?</section>', re.S)
SECTION_DA_RE = re.compile(
    r'<section[^>]*>\s*<div class="container wide">\s*<h2>Større værktøjer</h2>'
    r'.*?</section>', re.S)
PRICING_RE = re.compile(r'href="(/(?:da/)?pricing/?)"')
# Tallet i en prosalinje er bevidst **ikke** en dom. Det ville tvinge «11» ned i
# en sætning, der er skrevet for at læses, og et tal i prosa er i sig selv en
# påstand der kan blive forældet. I stedet dømmer krav 3 det samme som det
# gælder om: at katalogens produkter faktisk kan findes.

# Hvad `#products` lister i dag, målt 5/10. Hvis en ny vare føjes til listen,
# skal denne tal stå her — ellers dømmer krav 3 en forældet påstand i stedet
# for en reel mangel. Det er derfor porten skriver tallet i sin egen fejltekst.
NAVNTE_I_LISTEN = 2


def katalog_antal() -> int:
    produkter = json.loads(CATALOG.read_text(encoding="utf-8"))["products"]
    return len(produkter)


def fejl_forside(html: str, *, section_re: re.Pattern, exp_pricing: str,
                 sprog: str) -> list[str]:
    fund: list[str] = []
    afsnit = section_re.search(html)
    if afsnit is None:
        return [f"  {sprog}: salgsafsnittet ikke fundet — porten dømmer det "
                f"afsnit, og uden det ved den ikke hvad forsiden tilbyder"]
    krop = afsnit.group(0)

    # Krav 1: vejen til hele listen, i sit eget sprog.
    priser = PRICING_RE.findall(krop)
    if not priser:
        fund.append(
            f"  {sprog}: salgsafsnittet har 0 link til prislisten — de "
            f"{katalog_antal() - NAVNTE_I_LISTEN} produkter der ikke står i "
            f"listen er så ubefærdelige fra forsiden. Tilføj `{exp_pricing}`.")
    elif priser[0] != exp_pricing:
        fund.append(
            f"  {sprog}: salgsafsnittet peger på `{priser[0]}`, ikke "
            f"`{exp_pricing}` — den danske forside skal ikke sende en dansk "
            f"læser til den engelske liste.")

    # Krav 2: linket skal pege på en side der findes i kilden. `pricing.html` er
    # en flad fil, ikke en mappe med index — målt 5/10 — så begge former prøves.
    if priser:
        rute = priser[0].strip("/")
        flad = ROOT / "site" / f"{rute}.html"
        mappe = ROOT / "site" / rute / "index.html"
        if not flad.exists() and not mappe.exists():
            fund.append(
                f"  {sprog}: `{priser[0]}` findes ikke i `site/` — hverken "
                f"{flad.relative_to(ROOT)} eller {mappe.relative_to(ROOT)} "
                f"findes. Linket er en 404 der ligner en købsvej.")
    return fund


def dom() -> list[str]:
    fund: list[str] = []
    for sti, mønster, exp, sprog in (
        (EN_INDEX, SECTION_EN_RE, "/pricing", "EN"),
        (DA_INDEX, SECTION_DA_RE, "/da/pricing", "DA"),
    ):
        fund += fejl_forside(sti.read_text(encoding="utf-8"),
                             section_re=mønster, exp_pricing=exp, sprog=sprog)
    return fund


def self_test() -> int:
    fejl: list[str] = []

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        if not sand:
            fejl.append(f"{navn}{': ' + detalje if detalje else ''}")

    # Mutation 1: salgsafsnittet på den engelske forside peger ikke længere på
    # prislisten — mutationen der bragte fejlen til verden. Porten skal være rød.
    en0 = EN_INDEX.read_text(encoding="utf-8")
    da0 = DA_INDEX.read_text(encoding="utf-8")
    try:
        # Kun `href`-attributtet, aldrig hele `<a …>`-taggen: en mutation der
        # rammer markup, holder kun til den markup den blev skrevet imod, så
        # den bliver rød (fejlslag) så snart klassen ændrer sig. Det skete
        # her — `btn btn-small` kom på, og mutationen greb ikke længere.
        EN_INDEX.write_text(en0.replace('<a class="btn btn-small" href="/pricing">',
                                        '<a class="btn btn-small" href="/prisliste">'),
                            encoding="utf-8")
        fund = dom()
        tjek("EN uden linket er rød",
             any("ubefærdelige" in f for f in fund), "; ".join(fund))
    finally:
        EN_INDEX.write_text(en0, encoding="utf-8")

    # Mutation 2: dansk forside peger på den engelske liste. Det er ikke en død
    # link — den virker — så en ren `check_links`-dom ville være grøn, og det er
    # præcis derfor porten skriver denne regel selv.
    try:
        DA_INDEX.write_text(da0.replace('<a class="btn btn-small" href="/da/pricing">',
                                         '<a class="btn btn-small" href="/pricing">'),
                            encoding="utf-8")
        fund = dom()
        tjek("DA på den engelske liste er rød",
             any("engelske liste" in f for f in fund), "; ".join(fund))
    finally:
        DA_INDEX.write_text(da0, encoding="utf-8")

    # Mutation 3: krav 2 skal kunne fejle *alene*. Med et ændret href fanger
    # krav 1 det først, så krav 2 var uopnåeligt — en regel uden en dom der kan
    # fejle, præcis den fejlform denne ports docstring advarer om. Derfor flyttes
    # den rigtige fil aside i stedet: href'en er da uændret korrekt, så kun
    # krav 2 kan være årsagen.
    prisfil = ROOT / "site" / "pricing.html"
    gemt = ROOT / "site" / "pricing.html.bak"
    try:
        prisfil.rename(gemt)
        fund = dom()
        tjek("en prisliste der ikke findes er rød",
             any("404 der ligner en købsvej" in f for f in fund), "; ".join(fund))
    finally:
        if gemt.exists():
            gemt.rename(prisfil)

    # Mutation 4: afsnittet skal findes. Hvis `<h2>Større værktøjer</h2>`
    # omdøbes, skal porten sige det — ellers dømmer krav 1 og 2 ingen sider,
    # fordi `section_re` ikke matcher, og alt er grønt uden en købsvej.
    try:
        DA_INDEX.write_text(da0.replace("<h2>Større værktøjer</h2>",
                                         "<h2>Alt</h2>"), encoding="utf-8")
        fund = dom()
        tjek("et omdøbt salgsafsnit er rødt",
             any("salgsafsnittet ikke fundet" in f for f in fund), "; ".join(fund))
    finally:
        DA_INDEX.write_text(da0, encoding="utf-8")

    # Mutation 5: de rigtige filer skal være grønne — ellers lå porten i gaten
    # og rødmede deploys for en fejl der ikke findes.
    fund = dom()
    tjek("de rigtige filer er grønne", not fund, "; ".join(fund[:3]))

    for linje in fejl:
        print(f"  FEJL  {linje}")
    print(f"check-frontpage-pricing-selftest: {'OK' if not fejl else 'RØD'} "
          f"({5 - len(fejl)}/5 kontroller)")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true",
                        help="kør portens egen kontrol af sig selv")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    fund = dom()
    for linje in fund:
        print(linje)
    if fund:
        print(f"\nfrontpage-pricing: RØD — {len(fund)} fund")
        return 1
    antal = katalog_antal()
    print(f"frontpage-pricing: GRØN — begge forsider linker til prislisten, "
          f"så alle {antal} katalogprodukter er at finde fra forsiden "
          f"({NAVNTE_I_LISTEN} i listen, {antal - NAVNTE_I_LISTEN} via den)")
    return 0


if __name__ == "__main__":
    sys.exit(main())