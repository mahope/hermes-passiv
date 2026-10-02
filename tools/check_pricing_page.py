#!/usr/bin/env python3
"""Dom at `/pricing` viser katalogens priser — og at siden ikke sælger.

Baggrund (målt 2/10): `tools/pricing_page.py` bygger siden fra
`tools/stripe_catalog.json`, så en pris kan ikke glide **inden i** den fil. Men
det siger intet om tre ting, der alle er målbare og alle er gået galt i denne
familie før:

1. **Siderne kan holdes opdateret af en generator og alligevel have en gammel
   pris.** `check_buyable.py` fandt 7 af 13 produkter uden købsside, og ingen
   port sagde noget, fordi porten kun dømmer et produkt *når en side sælger
   det*. Her skal siden være rød hvis den afviger fra generatorens output —
   altså hvis nogen har skrevet en pris i hånden oveni den.

2. **Et produkt uden købsside får en knap der ingen vegne hen går.** Derfor er
   `pricing_link` påkrævet i katalogen, og dom 2 dømmer at hver række har en
   rute der svarer til en side der faktisk findes i bygget site.

3. **Siden kunne blive en købsside.** Den skal **ikke** tage imod betaling:
   målt 2/10 da den gjorde det, `check_stripe_ctas.py` læser en sides
   gratis/Pro-flade som én produkts påstande, så tolv produkter på én side gav
   hver sin fejl («den gratis side af siden nævner ikke 'history'», fordi den
   side der sælger EUComply Pro også nævner Page Profiles gratis-funktioner).
   Dom 3 dømmer derfor at der står **nogen** `buy.stripe.com` på siden.

Dom 4 er den egentlige nytte: et katalogprodukt der er **på vej frem** — det
har en `pricing_page`-rute, en pris og en købsside — men ikke står på
prislisten, er en vare læseren ikke kan finde. Den er rød, fordi det er præcis
den mangel siden er lavet for at lukke.

Dom 5 er svaret på det dom 1–4 ikke kan se: en generator der **selv** skriver
en pris. Dom 1 dømmer at siden er generatorens output, så en håndskrevet pris
oveni den er rød — men målt 2/10 af review skrev `tools/pricing_page.py` selv
donationens pris i hånden («Any amount»), mens katalogen for præcis den vare
siger «fra 10 kr.». Siden var grøn hele vejen, og den lovede noget Stripe
afviser under. Dom 5 dømmer derfor **beløbene i den byggede celle mod den
vares egen katalogpost**, så håndskriven prosa ikke kan overleve: et `$`-beløb
skal være `price_usd` eller `lifetime.price_usd` for den vare, og en donation
skal vise katalogens `price_min` for sit sprog, ord til ord.

    python3 tools/check_pricing_page.py             # dom
    python3 tools/check_pricing_page.py --self-test # 9 mutationer
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import pricing_page  # noqa: E402

CATALOG = ROOT / "tools" / "stripe_catalog.json"
DIST = ROOT / "dist" / "mahope.tools"
ROUTE_TIL_FIL = {"/pricing": "pricing.html", "/da/pricing": "da/pricing.html"}

BELØB_RE = re.compile(r"\$\s?(\d+)")


def dom5_pris(produkt: dict, celle: str, lang: str) -> list[str]:
    """Dom 5: intet beløb i priscellen må være skrevet uden for katalogen.

    Håndværket er at **læse den byggede celle**, ikke at spørge generatoren
    hvad den ville lave — ellers dømmer porten generatoren mod sig selv, og
    det var præcis der fejlen lå. Derfor fanges kun beløb med `$` foran, som er
    den skriveform hele familien bruger; `kr.`-beløb fanges af dom 5b, der
    kræver katalogens egen minimum for en donation.
    """
    fund: list[str] = []
    nøgle = produkt["_nøgle"]
    tilladt: set[str] = set()
    if isinstance(produkt.get("price_usd"), (int, float)):
        tilladt.add(str(produkt["price_usd"]))
    livstid = produkt.get("lifetime")
    if isinstance(livstid, dict) and isinstance(livstid.get("price_usd"), (int, float)):
        tilladt.add(str(livstid["price_usd"]))
    minimum = (produkt.get("price_min") or {}).get(lang)
    if isinstance(minimum, str):
        tilladt |= set(BELØB_RE.findall(minimum.replace("kr.", "$")))

    for beløb in BELØB_RE.findall(celle):
        if beløb not in tilladt:
            fund.append(f"{nøgle}: beløbet ${beløb} i priscollen står ikke i "
                        f"katalogens post ({'/'.join(sorted(tilladt)) or 'ingen beløb'})")

    # Dom 5b: en donation skal vise katalogens minimum. Uden `price_min` er det
    # ikke «ubehageligt at læse et tomt felt» — det er at siden så ikke ved,
    # hvad Stripe afviser under, fordi ingen har skrevet det ned.
    if produkt.get("kind") == "donation":
        if not isinstance(minimum, str) or not minimum.strip():
            fund.append(f"{nøgle}: katalogen skal oplyse `price_min.{lang}` — "
                        f"minimumsbeløbet for en donation må ikke stå i prosa i "
                        f"generatoren")
        elif minimum not in celle:
            fund.append(f"{nøgle}: donationsprisen er «{celle}», men katalogens "
                        f"`price_min.{lang}` siger «{minimum}»")
    return fund


def dom(cat: dict, dist: Path, site: Path | None = None) -> list[str]:
    """Alle fund. Tom liste = grøn.

    `site` er roden for kilderne. Selftesten lægger dem i en midlertidig
    kopi, så porten skal kunne læse mutationerne og ikke repoet — derfor er
    roden et argument frem for et konstant."""
    fund: list[str] = []
    rod = site or ROOT
    for sti, lang in pricing_page.sider(cat):
        kilde_fil = (rod / "site" / str(sti).split("site/", 1)[-1]) if site else sti
        rel = f"site/{str(sti).split('site/', 1)[-1]}"
        kilde = kilde_fil.read_text(encoding="utf-8")

        # Dom 1: siden er generatorens output, ubeskåret. Skrevet i hånden
        # oveni den er den fejl, `--check` ikke kan se fordi den kun læser den
        # første blok — så dommen her sammenligner hele filens blok.
        m = pricing_page.EJER_RE.search(kilde)
        if not m:
            fund.append(f"{rel}: ingen `pricing`-blok")
            continue
        if m.group(0) != pricing_page.byg_blok(cat, lang):
            fund.append(f"{rel}: blokken er skrevet i hånden oveni generatorens "
                        f"output — kør `python3 tools/pricing_page.py --apply`")

        # Dom 3: ingen betaling på siden. Se docstring.
        for link in sorted(set(re.findall(r"(?:buy|donate)\.stripe\.com/\w+", kilde))):
            fund.append(f"{rel}: sælger direkte ({link}). /pricing skal linke til "
                        f"produktets købsside, ikke tage imod betaling")

        # Dom 2: hver række skal pege på en side der findes. Ruten læses fra
        # rækken, så en død rute er et fund og ikke en stille 404.
        for nøgle, rute in re.findall(
                r'data-product="([^"]+)">\s*<th[^>]*>.*?</th>\s*<td>.*?</td>\s*'
                r'<td[^>]*>.*?</td>\s*<td>.*?</td>\s*<td>\s*'
                r'<a class="pc-buy" href="([^"]*)"', kilde, re.S):
            if not rute:
                fund.append(f"{rel}: rækken {nøgle} har ingen købsside")
                continue
            if rute.startswith(("http://", "https://")):
                continue
            fil = (dist / (rute.strip("/") + "/index.html")) if rute.endswith("/") \
                else (dist / (rute.strip("/") + ".html"))
            if not fil.exists() and not (dist / rute.strip("/") / "index.html").exists():
                fund.append(f"{rel}: rækken {nøgle} linker til {rute}, som ikke "
                            f"findes i det byggede site")

        # Dom 5: hvert beløb i hver priscelle skal stå i **den vares** egen
        # katalogpost. Læser den byggede fil, så en generator der selv skriver
        # en pris er rød her — se domstringen.
        for nøgle, celle in re.findall(
                r'data-product="([^"]+)">\s*<th[^>]*>.*?</th>\s*<td>(.*?)</td>',
                kilde, re.S):
            if nøgle not in cat["products"]:
                continue  # den syntetiske `free`-række: $0 er ikke en katalogvare
            fund.extend(f"{rel}: " + f for f in dom5_pris(
                {**cat["products"][nøgle], "_nøgle": nøgle}, celle, lang))

    # Dom 4: et produkt der er på vej frem, men ikke står på listen.
    på_liste = {nøgle for nøgle, _ in pricing_page.produkter(cat, "en")}
    for nøgle, produkt in sorted(cat["products"].items()):
        if nøgle in på_liste:
            continue
        if produkt.get("pricing_page") is False:
            continue  # bevidst udenfor, med en begrundelse i katalogen
        # Ikke på listen og ikke bevidst undtaget: så mangler den en
        # købsside, en pris — eller en undtagelse. Alle tre skal siges.
        fund.append(f"katalog: {nøgle} står ikke på /pricing og har ikke "
                    f"`pricing_page: false`. Sæt `pricing_page: false` med en "
                    f"begrundelse hvis den ikke skal sælges her — ellers er den "
                    f"en vare læseren ikke kan finde")
    return fund


def self_test() -> int:
    """Elleve kontroller, hvoraf ni er mutationer, der hver skal give sit fund.

    Mutationerne lægger sig på de **filer** porten læser — en midlertidig kopi
    af hele `site/` og `dist/` — ikke på et katalogobjekt. Det er pointen med
    dom 1: porten skal kunne se en håndskrevet pris på siden, og det kan den
    kun, hvis den læser den samme fil en mutation har ændret. Dom 5's mutationer
    følger samme regel for den modsatte grund: de skal ramme den **byggede**
    celle, ellers dømmer porten generatoren mod sig selv.
    """
    fejl: list[str] = []
    talt = [0]

    def tjek(navn: str, betingelse: bool, detalje: str = "") -> None:
        talt[0] += 1
        if not betingelse:
            fejl.append(f"{navn}{(' — ' + detalje) if detalje else ''}")

    cat = pricing_page.katalog()

    # (0) negativ kontrol: repoet skal være grøn, ellers dommer mutationerne
    #     ingenting.
    rød = dom(cat, DIST)
    tjek("repoet er grøn", not rød, "; ".join(rød[:2]))

    def med_filer(ændringer: list[tuple[str, str]], kat: dict | None = None) -> list[str]:
        """Kør `dom` mod en midlertidig kopi hvor filerne er ændret.

        En katalogmutation **gen tegner** siderne før dommen, fordi dom 1
        ellers ville være rød af sig selv og dække den dom, mutationen egentlig
        skal teste. Sådan rammer hver mutation præcis sin egen dom — samme
        princip som dom 3b i `check_pro_table.py`."""
        with tempfile.TemporaryDirectory() as tmp:
            rod = Path(tmp)
            (rod / "site").mkdir()
            (rod / "dist").mkdir()
            for original in (ROOT / "site").rglob("*.html"):
                mål = rod / "site" / original.relative_to(ROOT / "site")
                mål.parent.mkdir(parents=True, exist_ok=True)
                mål.write_text(original.read_text(encoding="utf-8"), encoding="utf-8")
            for original in DIST.rglob("*"):
                if original.is_file():
                    mål = rod / "dist" / original.relative_to(DIST)
                    mål.parent.mkdir(parents=True, exist_ok=True)
                    mål.write_bytes(original.read_bytes())

            # Gen tegn med den muterede katalog, så dom 1 er grøn med vilje.
            kat = kat or json.loads(json.dumps(cat))
            # Ruterne skal pege på **kopien**, ikke på repoet — både for
            # `_apply` (der skriver) og for `dom` (der læser). Sættes derfor
            # først, ellers bliver dom 1 rød af en mutation der intet har med
            # den at gøre.
            kat["pricing_pages"] = [
                {"path": f"site/{post['path'].split('site/', 1)[-1]}",
                 "lang": post["lang"]} for post in cat["pricing_pages"]]
            pricing_page._apply(kat, rod)
            for sti, erstatning in ændringer:
                fil = rod / sti
                fil.write_text(fil.read_text(encoding="utf-8").replace(*erstatning),
                               encoding="utf-8")
            return dom(kat, rod / "dist", rod)

    # Dom 1: en pris skrevet i hånden oveni generatorens output.
    fund = med_filer([("site/pricing.html",
                       ("$19/year", "$17/year"))])
    tjek("håndskrevet pris er rød",
         any("hånden" in f for f in fund), "; ".join(fund[:1]))

    # Dom 3: et Stripe-link på siden.
    fund = med_filer([("site/pricing.html",
                       ('href="/paid-templates"',
                        'href="https://buy.stripe.com/bJe7sK8aT4My7dk7czbMQ05"'))])
    tjek("direkte betaling er rød",
         any("sælger direkte" in f for f in fund), "; ".join(fund[:1]))

    # Dom 2: en død købsside i katalogens `pricing_link`.
    kat_død = json.loads(json.dumps(cat))
    kat_død["products"]["clean-copy-pro"]["pricing_link"] = "/findes-ikke"
    fund = med_filer([], kat_død)
    tjek("død købsside er rød",
         any("ikke findes i det byggede site" in f for f in fund),
         "; ".join(fund[:1]))

    # Dom 2/4: en købsside der tømmes. En vare uden `pricing_link` kommer ikke
    # på siden (så et link på den ville pege på ingenting), og dom 4 gør da
    # **mangelen** rød i stedet for at den forsvinder stille. Derfor er dom 2
    # og dom 4 samme fejl set fra hver sin side: den ene dømmer rækken, den
    # anden dømmer at varen ikke kan findes.
    kat_tom = json.loads(json.dumps(cat))
    kat_tom["products"]["page-profile-pro"]["pricing_link"] = ""
    fund = med_filer([], kat_tom)
    tjek("tømt købsside er rød",
         any("page-profile-pro" in f and "står ikke på /pricing" in f
             for f in fund), "; ".join(fund[:1]))

    # Dom 4: et produkt **uden** `pricing_link`. Et produkt med en købsside
    # står på listen af sig selv, så mutationen skal være den vare der hverken
    # har en rute eller en begrundet undtagelse. Uden dom 4 ville den bare
    # forsvinde fra siden, og ingen port ville sige noget — samme blinde
    # dødszone som `check_buyable.py` blev skrevet for at lukke.
    kat_ny = json.loads(json.dumps(cat))
    kat_ny["products"]["et-helt-nyt-produkt"] = {
        "name": "Et helt nyt produkt", "kind": "license", "price_usd": 9,
        "payment_link": "https://buy.stripe.com/000000000000000000",
    }
    fund = med_filer([], kat_ny)
    tjek("produkt uden købsside er rødt",
         any("står ikke på /pricing" in f for f in fund), "; ".join(fund[:1]))

    # Og den undtagelse, der gør dom 4 grøn igen: varen sælges et andet sted
    # (transmute.run), så den skal være væk fra denne side med en begrundelse.
    kat_ok = json.loads(json.dumps(kat_ny))
    kat_ok["products"]["et-helt-nyt-produkt"]["pricing_page"] = False
    fund = med_filer([], kat_ok)
    tjek("begrundet undtagelse er grøn",
         not any("et-helt-nyt-produkt" in f for f in fund), "; ".join(fund[:1]))

    # Dom 5: et beløb der ikke står i katalogens post. Dette er den mutation
    # review 2/10 selv lavede i hånden og opdagede, at porten ikke så: katalogens
    # pris sat til «fra 500 kr.», siderne genbygget, porten grøn, siden uændret.
    # Nu rammer den dommen, fordi dommen læser den byggede celle.
    fund = med_filer([("site/pricing.html", ("$19/year", "$419/year"))])
    tjek("beløb uden for katalogen er rødt",
         any("står ikke i katalogens post" in f for f in fund), "; ".join(fund[:1]))

    # Dom 5b: «Any amount» i stedet for katalogens minimum. Det var den
    # håndskrevne sætning der lå i generatoren indtil 2/10.
    fund = med_filer([("site/pricing.html",
                       ("From 10 kr.", "Any amount"))])
    tjek("håndskrevet donationspris er rød",
         any("price_min" in f for f in fund), "; ".join(fund[:1]))

    # Polaritet for dom 5b: når **katalogen** siger «Any amount», skal den
    # samme streng være grøn. Uden den kontrol ville dommen bare have været en
    # streng der altid er rød, og de to mutationer ovenfor intet bevare.
    kat_any = json.loads(json.dumps(cat))
    kat_any["products"]["support-mahope-oss"]["price_min"]["en"] = "Any amount"
    fund = med_filer([], kat_any)
    tjek("katalogens egen donationspris er grøn",
         not any("support-mahope-oss" in f for f in fund), "; ".join(fund[:1]))

    # Og polaritet for dom 5b modsat: katalogen uden `price_min` er rød, for så
    # står minimumsbeløbet ingen steder — hverken i katalogen eller på siden.
    kat_uden = json.loads(json.dumps(cat))
    del kat_uden["products"]["support-mahope-oss"]["price_min"]
    fund = med_filer([], kat_uden)
    tjek("donation uden price_min er rød",
         any("skal oplyse `price_min" in f for f in fund), "; ".join(fund[:1]))

    for linje in fejl:
        print(f"  FEJL  {linje}")
    print(f"check-pricing-page-selftest: {'OK' if not fejl else 'RØD'} "
          f"({talt[0] - len(fejl)}/{talt[0]} kontroller)")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="kør mutationerne")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    fund = dom(pricing_page.katalog(), DIST)
    for f in fund:
        print(f"  {f}")
    if not DIST.exists():
        print("check-pricing-page: RØD — dist/mahope.tools mangler; kør "
              "`python3 build_sites.py` først")
        return 1
    print(f"check-pricing-page: {'GRØN' if not fund else 'RØD'} "
          f"({len(pricing_page.produkter(pricing_page.katalog(), 'en'))} produkter, "
          f"{len(pricing_page.sider(pricing_page.katalog()))} sider)")
    return 1 if fund else 0


if __name__ == "__main__":
    sys.exit(main())