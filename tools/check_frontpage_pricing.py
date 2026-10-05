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
4. *Henvisningen modsiger ikke listerne over den* — sætningen der sender
   læseren videre til prislisten må kun navngive varer der ikke allerede står i
   listerne ovenfor. Findet 6/10 (review-fund, LAV): sætningen lød «The other
   products — Clean Copy Pro, DeskUptime Pro, … — are not listed above», men
   Clean Copy og DeskUptime står i «With their own sites» lige overfor med
   deres pris i teksten. Det er punkt 11 flyttet fra et tal til en påstand, og
   læseren kan ikke finde ud af hvad der menes, fordi de to lister overhovedet
   er dem hun lige har læst.

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
# Henvisningssætningen er den `<p>` der indeholder linket til prislisten. Den er
# fundet ved sit indhold, ikke ved en klasse eller et id, fordi den på de to
# forsider er skrevet forskelligt (EN: «Not listed above: …», DA: «Ikke listet
# ovenfor: …»), og fordi den flytter sig, hvis en ny vare føjes til listerne.
P_RE = re.compile(r'<p\b[^>]*>.*?</p>', re.S)
# Tallet i en prosalinje er bevidst **ikke** en dom. Det ville tvinge «11» ned i
# en sætning, der er skrevet for at læses, og et tal i prosa er i sig selv en
# påstand der kan blive forældet. I stedet dømmer krav 3 det samme som det
# gælder om: at katalogens produkter faktisk kan findes. Samme grundlag for
# portens egen *melding*: den siger ikke længere «2 i listen, 11 via den».
# Det tal blev håndholdt, og fundet 6/10 viste at ingen vidste hvilke to varer
# det egentlig dækkede — den talte solgte varelinjer, mens afsnittet navngiver
# fire katalogprodukter. En besked skal ikke have et tal hun ikke kan regne
# sig frem til.


def katalog_antal() -> int:
    produkter = json.loads(CATALOG.read_text(encoding="utf-8"))["products"]
    return len(produkter)


def katalognavne() -> list[str]:
    """Katalognavne uden «Pro»-suffixen, som en henvisning på en forside skriver.

    Sætningen på forsiden skriver «Clean Copy Pro», fordi det er produktets
    navn i katalogen. Men det er **værktøjet** (Clean Copy) der står i listerne
    ovenfor, og det er det en læser kan se. Derfor dømmes der på navnet uden
    suffixen — ellers ville den fejl, fundet fandt, være usynlig for porten.

    Korte navne springes over: et navn på under seks tegn kan være et almindeligt
    ord i en prosasætning og give en rød port på en sand side.
    """
    produkter = json.loads(CATALOG.read_text(encoding="utf-8"))["products"]
    navne = set()
    for produkt in produkter.values():
        navn = str(produkt.get("name", "")).removesuffix(" Pro").strip()
        if len(navn) >= 6:
            navne.add(navn)
    return sorted(navne)


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
            f"katalogprodukter der ikke står i listerne er så ubefærdelige fra "
            f"forsiden. Tilføj `{exp_pricing}`.")
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

    # Krav 4: henvisningen må ikke modsige listerne over den. Den `<p>` der
    # indeholder linket er fundet på sit indhold; alt andet i afsnittet er
    # «ovenfor». Et katalognavn der står i begge steder er en påstand der
    # modsiger sig selv — fundet 6/10 gjorde netop det med Clean Copy Pro.
    henvisning = ""
    for afsnit_p in P_RE.findall(krop):
        if PRICING_RE.search(afsnit_p):
            henvisning = afsnit_p
            break
    if henvisning:
        ovenfor = krop.replace(henvisning, "")
        laevet = ovenfor.lower()
        for navn in katalognavne():
            if navn.lower() in henvisning.lower() and navn.lower() in laevet:
                fund.append(
                    f"  {sprog}: henvisningen siger at «{navn}» ikke står "
                    f"ovenfor, men den står i listerne over den. Skriv navnet "
                    f"væk, eller skriv «resten af katalogen» uden "
                    f"opremsning.")
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

    # Mutation 5: krav 4 skal kunne fejle *alene*. Mutation 1–3 rører `href` og
    # mutation 4 fjerner hele afsnittet, så ingen af dem kan nå krav 4. Den
    # genindsætter derfor præcis den sætning fundet 6/10 fandt — Clean Copy Pro
    # og DeskUptime Pro nævnt som værende «ikke listet ovenfor» — og lader
    # `href` være korrekt. Uden denne mutation ville krav 4 være en regel uden
    # en dom der kan fejle, præcis den fejlform docstringen advarer om.
    ny_saetning_en = ("<p style=\"margin-bottom:0\">Not listed above: "
                      "Transmute Desktop, the compliance templates and the "
                      "report kits.")
    gammel_saetning_en = ("<p style=\"margin-bottom:0\">The other products "
                          "— Clean Copy Pro, DeskUptime Pro, Transmute "
                          "Desktop, the compliance templates and the report "
                          "kits — are not listed above.")
    ny_saetning_da = ("<p style=\"margin-bottom:0\">Ikke listet ovenfor: "
                      "Transmute Desktop, compliance-skabelonerne og "
                      "rapportpakkerne.")
    gammel_saetning_da = ("<p style=\"margin-bottom:0\">De øvrige produkter "
                          "— Clean Copy Pro, DeskUptime Pro, Transmute "
                          "Desktop, compliance-skabelonerne og "
                          "rapportpakkerne — står ikke ovenfor.")
    # Mutationen læser den rigtige fil, kun på den del af sætningen der står
    # *før* knappen — så den holder hvis klassen eller teksten på knappen ændrer
    # sig, hvilket skete i mutation 1 (se kommentaren der).
    for sti, ny, gammel, sprog in (
        (EN_INDEX, ny_saetning_en, gammel_saetning_en, "EN"),
        (DA_INDEX, ny_saetning_da, gammel_saetning_da, "DA"),
    ):
        original = sti.read_text(encoding="utf-8")
        if ny not in original:
            fejl.append(f"{sprog}: mutation 5 kan ikke genindsætte den gamle "
                        f"sætning — den nuværende tekst er ikke den porten "
                        f"blev skrevet imod")
            continue
        try:
            sti.write_text(original.replace(ny, gammel, 1), encoding="utf-8")
            fund = dom()
            tjek(f"{sprog} med en modsigende henvisning er rød",
                 any("men den står i listerne over den" in f for f in fund),
                 "; ".join(fund))
        finally:
            sti.write_text(original, encoding="utf-8")

    # Mutation 6: de rigtige filer skal være grønne — ellers lå porten i gaten
    # og rødmede deploys for en fejl der ikke findes.
    fund = dom()
    tjek("de rigtige filer er grønne", not fund, "; ".join(fund[:3]))

    antal_kontroller = 7
    for linje in fejl:
        print(f"  FEJL  {linje}")
    print(f"check-frontpage-pricing-selftest: {'OK' if not fejl else 'RØD'} "
          f"({antal_kontroller - len(fejl)}/{antal_kontroller} kontroller)")
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
          f"så alle {antal} katalogprodukter er at finde fra forsiden")
    return 0


if __name__ == "__main__":
    sys.exit(main())