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
vares egen katalogpost**, så håndskreven prosa ikke kan overleve: et `$`-beløb
skal være `price_usd` eller `lifetime.price_usd` for den vare, og en donation
skal vise katalogens `price_min` for sit sprog, ord til ord.

Dom 6 er det spørgsmål dom 1–5 ikke stiller: **kan læseren overhovedet finde
siden?** Målt 4/10 var den ubegribelig vanskelig at finde. `grep -rl
'href="/pricing"'` over `site/` gav **én** fil — forsidens egen hub, der
linker til den to gange — og ingen af de 270 byggede sider havde den i
footeren, fordi footeren bygges af `nav` + `footer_extra` i `build_sites.py`.
Så den lå i `sitemap.xml`, altså målbar for Google og usynlig for alle andre:
en gratis-række og hver vares pris, en gratis-mod-betalt-tabel pr. vare, og ingen
vej fra en værktøjsside hen til den. Det er samme fejlklasse som dom 4, set fra
den anden side — dom 4 dømmer varen der mangler på listen, dom 6 dømmer listen
der mangler i sidernes krom. Dom 6 læser de **byggede** footere, fordi footeren
ikke findes i `site/`: den bliver skrevet af `apply_shell` undervejs.

Dom 7 er svaret på den anden fejl i samme slags: dom 2 dømmer at *filen*
findes, men målt 6/10 var alle købsruter bleven **ankere**, altså den eneste
måde at få læseren fra prislisten **hen til den vares egen knap** uden at sælge
direkte på siden (dom 3). Et `id` der bliver omdøbt på destinationssiden
efterlader ellers en række, der ser troværdig ud og sender læseren *oven for*
den knap han lige har bedt om.

Dom 8 dømmer det dom 2 og dom 7 ikke kan se: **sproget**. Målt 6/10 havde
`/da/pricing` to rækker med `https://cleancopy.tools/#price` og én med
`https://deskuptime.com/#pro` — altså engelske købssider midt i den betaling en
dansk læser var ved at vælge, og begge domme var grønne, fordi ruterne pegede på
en side der fandtes, på et anker der fandtes. Dom 8 læser derfor den **byggede**
destinationssides egen `<html lang>`, altså ikke en navnekonvention i ruten.

    python3 tools/check_pricing_page.py             # dom
    python3 tools/check_pricing_page.py --self-test # mutationer
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import pricing_page  # noqa: E402

CATALOG = ROOT / "tools" / "stripe_catalog.json"
DIST_ROOT = ROOT / "dist"
DIST = DIST_ROOT / "mahope.tools"
ROUTE_TIL_FIL = {"/pricing": "pricing.html", "/da/pricing": "da/pricing.html"}

# Dom 7 læser de **krydsdomæne**-købssider i det samme byggede site, så et
# `#anker` på en anden family er målbart på lige fod med et lokalt. Nøglen er
# værtsnavnet i katalogens `pricing_link` — en bygget mappe pr. domæne. Uden
# denne tabel ville dom 7 være tavs på præcis de to rækker hvor læseren skal
# krydse et domæneskift, altså hvor jagten efter knappen er længst.
# `dom()` tager `dist`-roden for at kunne læse søskendedomænerne i selftesten.
DOMÆNE_DIST = {
    "cleancopy.tools": "cleancopy.tools",
    "deskuptime.com": "deskuptime.com",
}

BELØB_RE = re.compile(r"\$\s?(\d+)")

# Dom 6 læser footeren i det **byggede** site. Den skrives af `apply_shell` i
# `build_sites.py` undervejs, så den findes ikke i `site/` — og en dom der læste
# kilden ville være grøn uanset hvad skellet gjorde. Målt 4/10: 270 af 270
# byggede sider har den, så kravet gælder alle og der er ingen undtagelse.
RE_FOOTER = re.compile(r'<footer class="site-footer">(.*?)</footer>', re.S)


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


def find_fil(rute: str, dist: Path) -> Path | None:
    """Den **byggede** fil en købsrute lander i, eller `None`.

    `rute` er `pricing_link` uden et eventuelt `#anker`. En rute med skråstreg
    på sidst (`/x/`) peger på en mappe med `index.html`; ellers er den filen
    selv. Samme to former som dom 2 bruger — de skal dele den, ellers dømmer
    dom 2 en fil eksistere mens dom 7 siger den gør."""
    ruten = rute.strip("/")
    for kandidat in (dist / ruten / "index.html", dist / f"{ruten}.html"):
        if kandidat.exists():
            return kandidat
    return None


def dom7_anker(rel: str, nøgle: str, rute: str, dist_rod: Path,
               pris_fil: Path) -> list[str]:
    """Dom 7: et `#anker` på en købsrute skal findes i den side den peger på.

    Baggrund (målt 6/10): dom 2 dømmer at *filen* findes, og det var nok så
    længe købsruterne var hele sider. De er nu ankre, fordi det er den eneste
    måde at få læseren fra prislisten **hen til den vares egen knap** uden at
    sælge direkte på siden (dom 3): 6 af 7 dokumentrækker pegede på
    `/paid-templates`, der sælger syv varer, så læseren landede i et gitter
    og skulle selv finde den rigtige knap.

    Uden denne dom er ankerne ubevogtede: et `id` der bliver omdøbt eller
    slettet på destinationssiden efterlader en `/pricing`-række, der ser
    troværdig ud og sender læseren *oven for* den knap, han lige har bedt om.
    Det er præcis «Alt virker»-bruddet, dom 2 ikke kan se."""
    del_anker, _, anker = rute.partition("#")
    if not anker:
        return []  # et link uden anker skal dømmes af dom 2, ikke her

    if not del_anker:
        # `href="#x"` er et anker på **prislisten selv**. Uden denne arm ville
        # den falde til `mahope.tools/index.html` og dømme et id der slet ikke
        # har med siden at gøre.
        if re.search(rf'\bid=["\']{re.escape(anker)}["\']',
                     pris_fil.read_text(encoding="utf-8", errors="ignore")):
            return []
        return [f"{rel}: {nøgle} sender læseren til #{anker}, men "
                f"prislisten selv har ingen `id=\"{anker}\"`"]

    dele = urlsplit(del_anker)
    if dele.netloc:
        vært = dele.netloc.lower()
        if vært not in DOMÆNE_DIST:
            # Bevidst **ikke** tavs: et nyt krydsdomæne uden en bygget mappe
            # ville få dom 7 til at tie på præcis de rækker, hvor den er mest
            # nødvendig. Skriv domænet i `DOMÆNE_DIST`, så kan den dømmes.
            return [f"{rel}: {nøgle} peger på {vært}, som ikke står i "
                    f"`DOMÆNE_DIST` — dom 7 kan ikke dømme et anker i en side "
                    f"den ikke kan finde"]
        rod = dist_rod / DOMÆNE_DIST[vært]
        rute = dele.path or "/"
    else:
        rod = dist_rod / "mahope.tools"
        rute = del_anker

    fil = find_fil(rute, rod)
    if fil is None:
        # Dom 2 dømmer den døde fil i mahope.tools. Her skal sæsonders dømmes:
        # et anker på en side vi ikke kan finde i det byggede site er ikke
        # kontrolleret, og det er værre end et fund — det ligner et dødt anker
        # uden at nogen siger det.
        return [f"{rel}: {nøgle} har ankeret #{anker} på {rute}, men den side "
                f"findes ikke i det byggede site ({rod.relative_to(ROOT) if rod.is_relative_to(ROOT) else rod})"]

    tekst = fil.read_text(encoding="utf-8", errors="ignore")
    if not re.search(rf'\bid=["\']{re.escape(anker)}["\']', tekst):
        rel_fil = fil.relative_to(dist_rod).as_posix() if fil.is_relative_to(dist_rod) else fil.name
        return [f"{rel}: {nøgle} sender læseren til #{anker}, men den side "
                f"({rel_fil}) har ingen `id=\"{anker}\"`. Rækken ligner at "
                f"finde knappen og lander oven for den"]
    return []


def dom8_sprog(rel: str, nøgle: str, rute: str, lang: str, dist_rod: Path,
               pris_fil: Path) -> list[str]:
    """Dom 8: en række skal sende læseren til en side på **samme sprog**.

    Baggrund (målt 6/10): dom 2 dømmer at filen findes og dom 7 at ankeret
    findes — og begge var grønne, fordi de tre rækker der peger på et andet
    domæne gjorde præcis det de bad om. `/da/pricing` sendte to rækker til
    `https://cleancopy.tools/#price` og én til `https://deskuptime.com/#pro`,
    altså **engelske** købssider midt i den betaling en dansk læser var ved at
    vælge. Sproget i ruten er ikke noget porten kan gætte: `/da/…` er en
    navnekonvention, ikke en egenskab ved siden.

    Derfor læses **den byggede sides egen `<html lang>`** — samme detektion dom 6
    bruger til at finde ud af hvilken prisliste en footer skal pege på, og den
    er målt på alle byggede sider. Kildeformen `/da/ruten` er stadig nyttig, men
    den er **inputtet**, ikke dommen: mutationerne nedenfor sætter den danske
    rute til den engelske side, og kun dom 8 kan se forskellen.

    Skriver den resolutionstesten fra dom 7 igen frem for at genbruge den: dom 7
    *finder* filen og *dommer ankeret*, og dens fund skal blive ved at hedde det
    de siger. En fælles hjælper ville skrive dens fund to steder, og de to domme
    ville så fejle hinanden i stedet for hver for sig."""
    del_anker, _, _ = rute.partition("#")
    if not del_anker:
        # `href="#x"` er et anker på prislisten selv — den ligger i sit eget sprog.
        return []

    dele = urlsplit(del_anker)
    if dele.netloc:
        rod = dist_rod / DOMÆNE_DIST.get(dele.netloc.lower(), dele.netloc.lower())
        rute = dele.path or "/"
    else:
        rod = dist_rod / "mahope.tools"
        rute = del_anker

    fil = find_fil(rute, rod)
    if fil is None:
        # Dom 2 (lokale ruter) og dom 7 (ankere) dømmer den manglende side. Her
        # ville en ekstra fund bare sige det samme to gange med et andet ord.
        return []

    tekst = fil.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'<html[^>]*\blang="([a-zA-Z-]+)"', tekst[:600])
    rel_fil = fil.relative_to(dist_rod).as_posix() if fil.is_relative_to(dist_rod) \
        else fil.name
    if not m:
        return [f"{rel}: {nøgle} peger på {rel_fil}, og dom 8 kan ikke læse "
                f"sidens sprog — der står ingen `lang` i de første 600 tegn, "
                f"så dommen kan hverken sige at rækken er rigtig eller forkert"]
    if m.group(1).lower() != lang:
        return [f"{rel}: {nøgle} er en række på den {'danske' if lang == 'da' else 'engelske'} "
                f"prisliste, men den peger på {rel_fil}, der er "
                f"`lang=\"{m.group(1)}\"`. Læseren lander midt i betalingen på "
                f"den anden sprogs købsside. Sæt `pricing_link` på den rute der "
                f"ligger i {lang}, eller lad feltet være en streng for de varer "
                f"hvor `/da/` foran ruten er nok"]
    return []


def dom(cat: dict, dist: Path, site: Path | None = None) -> list[str]:
    """Alle fund. Tom liste = grøn.

    `site` er roden for kilderne. Selftesten lægger dem i en midlertidig
    kopi, så porten skal kunne læse mutationerne og ikke repoet — derfor er
    roden et argument frem for et konstant."""
    fund: list[str] = []
    rod = site or ROOT
    # Dom 7 læser søskendedomænerne i det samme `dist/`, så roden er `dist`
    # selv. `dist` er her mahope.tools' **egne** mappe — både fra `main` og fra
    # selftesten, der lægger hele `dist/` ind i `rod/dist/<domæne>/`.
    dist_rod = dist if dist.name != "mahope.tools" else dist.parent
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
        # rækken, så en død rute er et fund og ikke en stille 404. Ankeret
        # skæres fra før filnavnet regnes — ellers ville `/x#y` læses som en
        # fil der hedder `x#y`, og dom 2 ville være rød af den forkerte grund.
        for nøgle, rute in re.findall(
                r'data-product="([^"]+)">\s*<th[^>]*>.*?</th>\s*<td>.*?</td>\s*'
                r'<td[^>]*>.*?</td>\s*<td>.*?</td>\s*<td>\s*'
                r'<a class="pc-buy" href="([^"]*)"', kilde, re.S):
            if not rute:
                fund.append(f"{rel}: rækken {nøgle} har ingen købsside")
                continue
            if rute.startswith(("http://", "https://")):
                continue
            if find_fil(rute.partition("#")[0], dist) is None:
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

        # Dom 7: rækken skal lande på det sted hvor betalingen sker. Se
        # `dom7_anker` — dom 2 dømmer filen, den her dømmer ankeret.
        #
        # Rækkerne læses **én ad gangen** frem for med ét mønster hen over hele
        # filen. Det lyder som en detalje, men et `data-lifetime`-`data-`-mønster
        # med `.*?` på tværs af cellerne kan løbe ind i den næste `<tr>` og
        # tage *dens* navn med, hvis en række en dag mangler en celle — så et
        # fund ville pege på den forkerte vare.
        pris_fil = dist / ROUTE_TIL_FIL.get(f"/{'da/' if lang == 'da' else ''}pricing",
                                            "pricing.html")
        for række in re.finditer(r"<tr\b[^>]*>(.*?)</tr>", kilde, re.S):
            krop = række.group(1)
            nøgle_m = re.search(r'data-(?:product|lifetime)="([^"]+)"', række.group(0))
            rute_m = re.search(r'<a class="pc-buy" href="([^"]*)"', krop)
            if not (nøgle_m and rute_m):
                continue
            fund.extend(dom7_anker(rel, nøgle_m.group(1), rute_m.group(1),
                                   dist_rod, pris_fil))
            fund.extend(dom8_sprog(rel, nøgle_m.group(1), rute_m.group(1),
                                   lang, dist_rod, pris_fil))

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

    # Dom 6: hver bygget side har prislisten i sin footer, på sit eget sprog.
    # Dømmer *antallet* og *sproget* — en dansk side der linker til `/pricing`
    # sender læseren ud af sit sprog, og to links i samme footer er to valg der
    # ligner hinanden. Se docstringen for hvorfor denne dom overhovedet er nødvendig.
    #
    # Sproget læses af sidens egen `<html lang>`, ikke af ruten, fordi de danske
    # værktøjs-sider ligger som `/palette-generator-da` i **roden** og ikke under
    # `/da/` (målt 4/10: 14 af dist's 270 sider er `-da` i roden). En rutebaseret
    # `startswith("da/")` ville dømme dem som engelske og kræve den engelske
    # prisliste på en dansk side. Samme detektion som `apply_shell` bruger.
    # Målt 4/10: alle 270 sider har `lang` i de første 600 tegn (112 `da`,
    # 158 `en`), så afsnittet kan ikke give en falsk *dansk*.
    #
    # Varernes antal **udledes** af katalogen, ikke skrevet i teksten: en hånd-
    # skreven optælling i en fejlmeddelelse er en påstand, der bliver forkert
    # stille næste gang katalogen vokser (målt 4/10: katalogen har 13 produkter,
    # 12 af dem står på listen, så «alle 13 varer» ville være løgn).
    antal_varer = len(på_liste)
    for fil in sorted(dist.rglob("*.html")):
        rel_fil = fil.relative_to(dist).as_posix()
        tekst = fil.read_text(encoding="utf-8", errors="ignore")
        dansk = bool(re.search(r'<html[^>]*\blang="da"', tekst[:600], re.I))
        forvent = "/da/pricing" if dansk else "/pricing"
        anden = "/pricing" if dansk else "/da/pricing"
        m = RE_FOOTER.search(tekst)
        if not m:
            fund.append(f"dist/{rel_fil}: ingen site-footer. Skellet i "
                        f"build_sites.py skriver den på alle 270 sider, så en "
                        f"manglende footer er en bygget fejl — og den er også "
                        f"sidens eneste vej til /pricing")
            continue
        hrefs = re.findall(r'href="([^"]+)"', m.group(1))
        antal = hrefs.count(forvent)
        # Hvor mange der peger på den *anden* sprogs prisliste. Uden denne tæller
        # kunne porten ikke skelne «linket mangler» fra «linket peger på den
        # engelske udgave på en dansk side» — og det er den fejl, mutationen
        # `href="/da/pricing"` → `href="/pricing"` laver.
        anden_antal = hrefs.count(anden)
        hvis_anden = (f" — den peger i stedet på {anden}, som er den anden "
                      f"sprogs udgave" if anden_antal else "")
        if antal != 1:
            fund.append(f"dist/{rel_fil}: footeren har {antal} linke til "
                        f"{forvent}, og den skal have præcis 1{hvis_anden}. "
                        f"/pricing er den eneste side i familien der samler "
                        f"alle {antal_varer} varers priser, så uden den kan en "
                        f"læser på ingen anden side finde ud af hvad Pro koster")
        elif anden_antal:
            fund.append(f"dist/{rel_fil}: footeren har både {forvent} og "
                        f"{anden}{anden_antal} gange. To prislister i én footer "
                        f"er to valg der ligner hinanden")
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
            # Dom 7 læser også de **krydsdomæne**-købssider, så hele `dist/`
            # kopieres — ikke kun mahope.tools. Ellers ville dom 7 være rød
            # på de to rækker der peger på cleancopy.tools og deskuptime.com
            # i hver eneste selftestkørsel, og mutationerne ville dømme en
            # port der aldrig har været grøn.
            for original in DIST_ROOT.rglob("*"):
                if original.is_file():
                    mål = rod / "dist" / original.relative_to(DIST_ROOT)
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
            # Hele `dist/` kopieres ind i `rod/dist/…`, så mahope.tools'
            # egen mappe ligger i `rod/dist/mahope.tools` — og det er den
            # `dom` skal kende som sin egen rod. Dom 7 finder søskende-
            # domænerne i `rod/dist/<navn>`.
            return dom(kat, rod / "dist" / "mahope.tools", rod)

    # Dom 1: en pris skrevet i hånden oveni generatorens output.
    fund = med_filer([("site/pricing.html",
                       ("$19/year", "$17/year"))])
    tjek("håndskrevet pris er rød",
         any("hånden" in f for f in fund), "; ".join(fund[:1]))

    # Dom 3: et Stripe-link på siden.
    fund = med_filer([("site/pricing.html",
                       ('href="/paid-templates#eucomply-dpa"',
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

    # Dom 7: et anker der ikke findes i den side det peger på. Det er den
    # mutation dom 7 er skrevet for: uden den er dommen en påstand, fordi
    # intet i repoetVille ændre et `id` på destinationssiden.
    fund = med_filer([("dist/mahope.tools/paid-templates.html",
                       ('id="eucomply-dpa"', 'id="eucomply-dpa-v2"'))])
    tjek("dødt anker er rødt",
         any("har ingen `id=" in f and "eucomply-dpa" in f for f in fund),
         "; ".join(fund[:1]))

    # Samme dom, krydsdomænet: `cleancopy.tools/#price` dømmes i **sit eget**
    # byggede site, ikke i mahope.tools'. Uden den mutation er det uafprøvet,
    # om dommen overhovedet læser det andet domæne.
    fund = med_filer([("dist/cleancopy.tools/index.html",
                       ('id="price"', 'id="priser"'))])
    tjek("dødt anker i et krydsdomæne er rødt",
         any("har ingen `id=" in f and "clean-copy-pro" in f for f in fund),
         "; ".join(fund[:1]))

    # Og polariteten modsat: et korrekt anker skal være grønt, ellers er
    # dommen bare en streng der altid er rød.
    fund = med_filer([])
    tjek("korrekt anker er grønt",
         not any("har ingen `id=" in f for f in fund), "; ".join(fund[:1]))

    # Dom 6: en bygget side hvor footeren ikke har prislisten. Det var hele
    # målingen der gjorde dommen nødvendig: 1 fil i `site/`, 0 af 270 i `dist/`.
    # Mutationen skal ramme en **bygget** fil, for dom 6 læser den footer
    # `apply_shell` skrev undervejs — en kildefil har aldrig footeren, så en
    # mutation dér ville være grøn af den forkerte grund.
    fund = med_filer([("dist/mahope.tools/index.html", ('href="/pricing"', 'href="/priser"'))])
    tjek("manglende prisliste i footeren er rød",
         any("skal have præcis 1" in f and "dist/index.html" in f for f in fund),
         "; ".join(fund[:1]))

    # Og den anden halvdel af dommen: den danske side skal pege på den danske
    # prisliste. `/pricing` er engelsk, så linket ville sende læseren ud af sit
    # sprog — og porten skal kunne se det, ellers er sprogdelen dekoration.
    fund = med_filer([("dist/mahope.tools/da/index.html", ('href="/da/pricing"', 'href="/pricing"'))])
    tjek("dansk side med engelsk prisliste er rød",
         any("dist/da/index.html" in f and "den anden sprogs udgave" in f
             for f in fund),
         "; ".join(fund[:1]))

    # Dom 8: den danske række skal pege på en dansk købsside. Det var hele
    # fejlen dom 2 og dom 7 ikke så: de tre rækker der krydser et domæne
    # gjorde præcis det portene bad om — de pegede på en side der fandtes, og
    # på et anker der fandtes. Mutationen sætter `da`-ruten til den **engelske**
    # side, altså præcis den fejl der lå i `main` 6/10.
    #
    # Den sker som en **katalog**-mutation og ikke som en fil-ændring, fordi dom
    # 1 ellers ville være rød af sig selv og dække dommen — samme grund som
    # dom 2's mutationer. Sådan rammer den præcis sin egen dom.
    kat_eng = json.loads(json.dumps(cat))
    kat_eng["products"]["clean-copy-pro"]["pricing_link"]["da"] = \
        kat_eng["products"]["clean-copy-pro"]["pricing_link"]["en"]
    fund = med_filer([], kat_eng)
    tjek("dansk række på engelsk købsside er rød",
         any("clean-copy-pro" in f and "anden sprogs købsside" in f
             for f in fund), "; ".join(fund[:1]))

    # Samme dom, en rute der **ikke** krydser et domæne. Den skal være absolut,
    # fordi `købs_rute` selv sætter `/da` foran en relativ rute — en relativ
    # mutation kan altså ikke slå dommen ihjel, og det er netop sådan en
    # håndskrivet `https://mahope.tools/…` i katalogen ser ud. Den rigtige fejl
    # på de otte mahope.tools-rækker var aldrig mulig, fordi `/da/ruten` er
    # afledt af den engelske rute; det er kun et **andet domæne** der kan glemme
    # det, og det er derfor dom 8 har brug for krydsdomænetabellen.
    kat_lok = json.loads(json.dumps(cat))
    kat_lok["products"]["eucomply-pro"]["pricing_link"] = \
        "https://mahope.tools/compliance-report#buy"
    fund = med_filer([], kat_lok)
    tjek("dansk række på lokal engelsk rute er rød",
         any("eucomply-pro" in f and "anden sprogs købsside" in f for f in fund),
         "; ".join(fund[:1]))

    # Og en mutation der fjerner **ankeret** på den danske købsside: dom 8 skal
    # ikke tie på den, fordi ankeret mangler — dom 7 ejer den fejl. Ellers ville
    # dom 8 og dom 7 begge rødme, og rettelsen ville se ud som at man kan vælge
    # mellem dem.
    fund = med_filer([("dist/cleancopy.tools/da/index.html",
                       ('id="priser"', 'id="priser-v2"'))])
    tjek("dom 8 tier om et manglende anker",
         not any("cleancopy" in f and "lang=" in f for f in fund),
         "; ".join(fund[:1]))

    # Polaritet: med katalogens egne `da`-ruter er dom 8 grøn. Uden denne test
    # kunne dommen være en streng der altid er rød, og de tre mutationer ovenfor
    # intet bevare.
    fund = med_filer([])
    tjek("korrekt sprog i købsruten er grønt",
         not any("lang=" in f for f in fund), "; ".join(fund[:1]))

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