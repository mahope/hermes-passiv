#!/usr/bin/env python3
"""Dom at en donation kun bedes om, hvor læseren lige har fået sit svar.

Baggrund (missionen, 30. september): «Link til donation der, hvor en glad
bruger naturligt ville sige tak, fx efter et vellykket resultat. Det må aldrig
blive påtrængende.» Målt før denne port blev skrevet: `site/` har **161**
HTML-sider, og **4** af dem linkede til donation — `/scan`, `/scan-da` og de
to `/support`. Katalogen, `FUNDING.yml` og kontrakten har alle haft linket
længe; ingen port målte om det nåede nogen.

De fire var de rigtige steder. `/scan` beder om den i sit *resultat*, i samme
13px-grå linje som de øvrige noter under en scanning, og slet ikke som en
knap. Det er modellen her.

**Hvad porten dømmer.** Pr. kildefil i `tools/donation.json`:

1. **Donationslinket er katalogets.** URL'en læses fra
   `tools/stripe_catalog.json` → `products.support-mahope-oss.payment_link`,
   ikke skrevet her, så en ny donationspris slår automatisk igennem.
2. **Det er aldrig en knap.** `class="btn…"` på ankeret er rødt. Det er den
   direkte maskinlæsbare del af «aldrig påtrængende»: en knap deler
   opmærksomhed med værktøjets egen primære handling, en 13px-sætning gør
   ikke. Samme regel som `check_first_action.py` bruger på folden, modsat
   vej: her skal den *sekundære* linje blive ved med at være sekundær.
3. **Det ligger i `<script>`, ikke i det statiske `<body>`.** En donation i
   markup'en viser sig på sidevisningen, før læseren har bedt om noget, og
   det er præcis det «efter et vellykket resultat» udelukker. I et script
   opstår den kun når værktøjet renderer sit svar. Det er den stærkeste
   sandhed porten kan hæfte ved en statisk fil, og den er målt: de to
   rettede sider sætter den i samme `res.innerHTML` som selve resultatet.
4. **Der er præcis én.** To donationer på én side er to chances for at den
   føles påtrængende, og den anden er næsten altid et kopieringsfejl.

**Hvad porten dømmer på donationssiderne selv.** `/support` og `/da/support`
er ikke i `donation.json` — dommene ovenfor handler om en linje der opstår
*efter et resultat*, og der er intet resultat på donationssiden. De dømmes i
stedet for den anden ting: de skal sige katalogens `price_min`, så ingen side
lover et beløb Stripe afviser under.

**Hvad porten kun tæller.** Sider der renderer et målt resultat og endnu
ikke har linjen. De dømmes ikke, fordi de er en samlet beslutning om hvor
mange sider der skal have den (se `❓` i `IMPLEMENTATION_PLAN.md`), og en
port der lovede at dømme dem, ville være løgnen over det den kan se. Målt
30/9: **37** værktøjssider. Blogartikler er ikke i opgøret — en læser der
er færdig med en artikel er ikke et *resultat*, og de tælles derfor heller
ikke, så tallet ikke overdriver det der faktisk mangler.

    python3 tools/check_donation_paths.py
    python3 tools/check_donation_paths.py --self-test
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
RATCHET = ROOT / "tools" / "donation.json"
KATALOG = ROOT / "tools" / "stripe_catalog.json"

# Ét `<script>…</script>`-interval pr. side. Uden dette kan porten ikke se
# forskel på "donationen står i markup'en" og "donationen opstår når
# værktøjet svarer" — og det er den forskel hele opgaven handler om.
SCRIPT_RE = re.compile(r"<script\b[^>]*>(.*?)</script>", re.S | re.I)
A_RE = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.S | re.I)
HREF_RE = re.compile(r'href="([^"]*)"')
CLASS_RE = re.compile(r'class="([^"]*)"')

# Et målt resultat: en beholder hvis navn siger, at her kommer et svar. Samme
# signal som `check_storage_claims.py` bruger til at finde sider der *kalder*
# en gemmende rute, så de to porte ser det samme sæt maskiner.
RESULT_RE = re.compile(
    r'id="[a-z0-9_-]*(?:result|results|output|findings|score|summary)[a-z0-9_-]*"'
    r'|class="[^"]*\b(?:result|results|output|findings|score)\b[^"]*"', re.I)

# Sider hvor «tak for pengene» er det forkerte sted. `/thanks` er lige efter
# et køb, `/support` *er* donationssiden, og de betalte produkt-siders købsknap
# må ikke få en donation som konkurrent lige under sig.
ALDRIG = ("site/thanks.html", "site/support.html", "site/da/support.html")

# De to donationssider selv. De er **ikke** i `donation.json`, fordi dommen
# ovenfor handler om en linje der opstår *efter et resultat* — på `/support`
# er der intet resultat. De dømmes i stedet for den anden ting, de skal være
# ærlige om: hvor meget man mindst kan give.
DONATIONS_SIDER = ("site/support.html", "site/da/support.html")


def donation_produkt(rod: Path = ROOT) -> dict:
    """Donationsvaren i katalogen. Læst, ikke skrevet."""
    produkter = json.loads((rod / "tools" / "stripe_catalog.json").read_text(
        encoding="utf-8"))["products"]
    return produkter["support-mahope-oss"]


def donation_url(rod: Path = ROOT) -> str:
    """Katalogets donations-URL. Læst, ikke skrevet, så prisen kan ændre sig."""
    return donation_produkt(rod)["payment_link"]


def min_mangler(rod: Path = ROOT) -> list[str]:
    """`/support` skal sige katalogens minimum — ellers lover den for meget.

    Baggrund (målt 2/10 af review): katalogen siger «fra 10 kr.» for præcis den
    vare, og `/pricing` lovede håndskrevet «Any amount», fordi den ene pris der
    ikke læses fra katalogen lå i prosa i generatoren. `/support` — den side
    donationen faktisk sker på — sagde «You choose the amount» / «Du vælger
    beløbet». Sådan skrev en læser, der ville give 5 kr., sig selv ind i en
    Stripe-fejl uden at nogen side havde fortalt, at der var en grænse.

    Dommen læser **katalogens** `price_min` for sidens sprog, så ændrer
    minimumsbeløbet sig, bliver begge sider røde i stedet for at lyve stille.
    Sproget afgøres af ruten, fordi `donation.json` ikke dømmer disse to sider
    og der derfor ikke er andet sted at finde det.
    """
    produkt = donation_produkt(rod)
    minimum = produkt.get("price_min")
    fund: list[str] = []
    if not isinstance(minimum, dict) or not minimum:
        return ["katalog: support-mahope-oss mangler `price_min` — minimumsbeløbet "
                "for en donation skal kunne læses ét sted, så ingen side kan love "
                "«hvad som helst»"]
    for kilde in DONATIONS_SIDER:
        fil = rod / kilde
        if not fil.exists():
            fund.append(f"{kilde}: filen findes ikke")
            continue
        lang = "da" if "/da/" in kilde else "en"
        tekst = minimum.get(lang)
        if not isinstance(tekst, str) or not tekst.strip():
            fund.append(f"katalog: `price_min.{lang}` mangler, så {kilde} ikke "
                        f"kan sige hvad læseren mindst kan give")
            continue
        html = fil.read_text(encoding="utf-8", errors="replace")
        # Uden `re.I` ville den danske minimumstreng «fra 10 kr.» være umulig at
        # skrive ind i en dansk sætning uden also at ændre katalogen.
        if not re.search(re.escape(tekst), html, re.I):
            fund.append(f"{kilde}: siger ikke katalogens minimum «{tekst}» — "
                        f"ellers lover siden et beløb Stripe afviser under")
    return fund


def i_script(html: str, pos: int) -> bool:
    """Står positionen `pos` inde i et `<script>`-element?"""
    for match in SCRIPT_RE.finditer(html):
        if match.start() <= pos < match.end():
            return True
    return False


def donation_ankre(html: str, url: str) -> list[re.Match[str]]:
    fund: list[re.Match[str]] = []
    for match in A_RE.finditer(html):
        href = HREF_RE.search(match.group(1))
        if href and href.group(1) == url:
            fund.append(match)
    return fund


def fejl_for(html: str, url: str) -> list[str]:
    fund: list[str] = []
    fund.extend(mal_url(html, url))
    ankre = donation_ankre(html, url)
    if len(ankre) == 0:
        fund.append("ingen donation på siden")
        return fund
    if len(ankre) > 1:
        fund.append(f"{len(ankre)} donationer på siden — én efter resultatet er nok, "
                    "to er påtrængende")
    for match in ankre:
        klasser = CLASS_RE.search(match.group(1))
        navne = (klasser.group(1) if klasser else "").split()
        knap = [k for k in navne if k.startswith("btn")]
        if knap:
            fund.append(f"donationen er en knap ({' '.join(knap)}) — den skal være en "
                        "lille linje, ellers konkurrerer den med værktøjets egen knap")
        if not i_script(html, match.start()):
            fund.append("donationen står i sidens markup, så den vises før læseren "
                        "har bedt om et resultat; den skal sættes ind når værktøjet "
                        "renderer sit svar")
    return fund


def mal_url(html: str, url: str) -> list[str]:
    """Skriveren skal pege på katalogets URL, ikke på en gammel donation."""
    fund: list[str] = []
    for href in re.findall(r"https://donate\.stripe\.com/[A-Za-z0-9]+", html):
        if href != url:
            fund.append(f"donationslinket er {href}, men katalogen siger {url}")
    return fund


def ratchet(rod: Path = ROOT) -> list[str]:
    data = json.loads((rod / "tools" / "donation.json").read_text(encoding="utf-8"))
    return [k for k in data if not k.startswith("_")]


def dom(rod: Path = ROOT) -> tuple[list[str], dict[str, list[str]]]:
    url = donation_url(rod)
    fund: list[str] = []
    detaljer: dict[str, list[str]] = {}
    for kilde in ratchet(rod):
        fil = rod / kilde
        if not fil.exists():
            fund.append(f"{kilde}: filen findes ikke")
            detaljer[kilde] = ["filen findes ikke"]
            continue
        problemer = fejl_for(fil.read_text(encoding="utf-8", errors="replace"), url)
        detaljer[kilde] = problemer
        fund.extend(f"{kilde}: {p}" for p in problemer)
    fund.extend(min_mangler(rod))
    return fund, detaljer


def uden_laeg(rod: Path = ROOT) -> list[str]:
    """Værktøjssider der renderer et målt resultat og ikke har linjen endnu."""
    url = donation_url(rod)
    mangler: list[str] = []
    for fil in sorted((rod / "site").rglob("*.html")):
        kilde = str(fil.relative_to(rod))
        if kilde in ALDRIG or "/blog/" in kilde or kilde.startswith("site/_"):
            continue
        html = fil.read_text(encoding="utf-8", errors="replace")
        if url in html or not RESULT_RE.search(html):
            continue
        mangler.append(kilde)
    return mangler


def self_test() -> int:
    fejl: list[str] = []

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        if not sand:
            fejl.append(f"{navn}{': ' + detalje if detalje else ''}")

    url = donation_url()
    script = (
        "<script>\n"
        "res.innerHTML = '<span>4.54:1</span>' +\n"
        "  '<br><span>a small <a href=\"" + url + "\" rel=\"nofollow noopener\">"
        "donation</a> keeps it running.</span>';\n"
        "</script>")
    statisk = (f'<p style="font-size:13px">a small <a href="{url}">donation</a> '
               "keeps it running.</p>")

    tjek("rettet side er grøn", not fejl_for(script, url), str(fejl_for(script, url)))
    tjek("donation i markup'en er rød", bool(fejl_for(statisk, url)),
         str(fejl_for(statisk, url)))
    som_knap = script.replace('<a href="', '<a class="btn-primary" href="')
    fund = fejl_for(som_knap, url)
    tjek("donation som knap er rød", any("knap" in f for f in fund), str(fund))
    gammel_url = script.replace(url, "https://donate.stripe.com/7sYeVcbn50wieFM8gDbMQ0Q")
    fund = fejl_for(gammel_url, url)
    tjek("et donationslink der ikke er katalogets er rødt",
         any("katalogen siger" in f for f in fund), str(fund))
    tjek("en side uden donation er rød", bool(fejl_for("<p>intet</p>", url)))
    tjek("to donationer er røde", any("2 donationer" in f
                                     for f in fejl_for(script + script, url)))

    tjek("katalog-URL'en er den i kontrakten",
         url == "https://donate.stripe.com/7sYeVcbn50wieFM8gDbMQ0c", url)

    # Ratchetfilen skal dømme præcis de sider, der er rettet, og de skal have
    # en donation — ellers er kontrollerne grønne fordi porten intet ser.
    dømt = ratchet()
    tjek("ratchetfilen dømmer de rettede sider", len(dømt) >= 11, str(dømt))
    tjek("de to kontrasværktøjer er stadig i ratchetfilen",
         "site/text-on-image-checker.html" in dømt
         and "site/text-on-image-checker-da.html" in dømt, str(dømt))
    # Ratchetfilen må ikke navngive en side der ikke har linjen: så ville
    # `uden_laeg` springe den over, og porten ville aldrig se den igen.
    fund, _ = dom()
    tjek("målingen på site/ er grøn", not fund, "; ".join(fund[:3]))
    mangler = uden_laeg()
    tjek("de rettede sider tælles ikke som manglende",
         not (set(dømt) & set(mangler)),
         str(sorted(set(dømt) & set(mangler))[:4]))
    # Når alle rettelige sider er rettet, er de tre der bliver ved et *navngivet*
    # resultat af opgaven, ikke et tal der falder. Tællingen skal derfor dømme
    # *hvem* der står tilbage, ellers ville porten grønne over en side den
    # burde have dømt.
    tjek("kun de tre navngive undtagelser mangler linjen",
         set(mangler) == {"site/clean-copy-tool.html", "site/compliance-report.html",
                          "site/site-icons.html"},
         f"{len(mangler)} sider: {', '.join(mangler)}")
    tjek("tak-siden tælles ikke med (købet er lige sket)",
         "site/thanks.html" not in mangler)

    # Mutation: en klon hvor linjen er en knap skal være rød, også når
    # porten kører fra en anden rod.
    with tempfile.TemporaryDirectory() as tmp:
        rod = Path(tmp)
        (rod / "site").mkdir()
        (rod / "tools").mkdir()
        (rod / "site" / "vaerktoj.html").write_text(som_knap, encoding="utf-8")
        (rod / "tools" / "donation.json").write_text(
            json.dumps({"site/vaerktoj.html": True}), encoding="utf-8")
        skriv_katalog(rod)
        fund, _ = dom(rod)
        tjek("mutation: linjen som knap er rød", any("knap" in f for f in fund),
             "; ".join(fund))
    with tempfile.TemporaryDirectory() as tmp:
        rod = Path(tmp)
        (rod / "site").mkdir()
        (rod / "tools").mkdir()
        (rod / "site" / "vaerktoj.html").write_text(statisk, encoding="utf-8")
        (rod / "tools" / "donation.json").write_text(
            json.dumps({"site/vaerktoj.html": True}), encoding="utf-8")
        skriv_katalog(rod)
        fund, _ = dom(rod)
        tjek("mutation: linjen i markup'en er rød",
             any("markup" in f for f in fund), "; ".join(fund))

    # Minimumsbeløbet på donationssiderne. Tre kontroller i træk, fordi dommen
    # skal kunne både se en side der lyver og **bevise** at den dømmer mod
    # katalogen og ikke mod en fast sætning: ændres minimumsbeløbet i
    # katalogen, skal den lyvende side blive grøn, fordi den så siger det
    # rigtige. Uden den polaritet ville mutationen bare have gjort porten rød
    # for alt.
    tjek("de rigtige donationssider er grønne", not min_mangler(),
         "; ".join(min_mangler()[:2]))

    def donations_rod(tmp: str, dansk: str) -> Path:
        rod = Path(tmp)
        (rod / "site" / "da").mkdir(parents=True)
        (rod / "tools").mkdir()
        (rod / "site" / "support.html").write_text(
            "<p class='hint'>" + dansk + "</p>", encoding="utf-8")
        (rod / "site" / "da" / "support.html").write_text(
            "<p class='hint'>Valgfrit beløb fra 10 kr.</p>", encoding="utf-8")
        (rod / "tools" / "donation.json").write_text("{}", encoding="utf-8")
        skriv_katalog(rod)
        return rod

    with tempfile.TemporaryDirectory() as tmp:
        fund = min_mangler(donations_rod(tmp, "You choose the amount."))
        tjek("mutation: donationsside uden minimum er rød",
             any("minimum" in f for f in fund), "; ".join(fund))
    with tempfile.TemporaryDirectory() as tmp:
        rod = donations_rod(tmp, "Any amount from 10 kr.")
        tjek("polaritet: donationssiden med minimum er grøn",
             not min_mangler(rod), "; ".join(min_mangler(rod)))
        # Og når **katalogen** hæver minimum, skal den samme side blive rød.
        katalog = json.loads((rod / "tools" / "stripe_catalog.json").read_text(
            encoding="utf-8"))
        katalog["products"]["support-mahope-oss"]["price_min"]["en"] = "From 25 kr."
        (rod / "tools" / "stripe_catalog.json").write_text(
            json.dumps(katalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        fund = min_mangler(rod)
        tjek("mutation: hævet minimum gør den gamle side rød",
             any("25 kr." in f for f in fund), "; ".join(fund))
    with tempfile.TemporaryDirectory() as tmp:
        rod = donations_rod(tmp, "Any amount from 10 kr.")
        katalog = json.loads((rod / "tools" / "stripe_catalog.json").read_text(
            encoding="utf-8"))
        del katalog["products"]["support-mahope-oss"]["price_min"]
        (rod / "tools" / "stripe_catalog.json").write_text(
            json.dumps(katalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        fund = min_mangler(rod)
        tjek("mutation: katalog uden price_min er rød",
             any("mangler `price_min`" in f for f in fund), "; ".join(fund))

    for linje in fejl:
        print("  rød:", linje)
    return len(fejl)


def skriv_katalog(rod: Path) -> None:
    (rod / "tools" / "stripe_catalog.json").write_text(
        KATALOG.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        antal = self_test()
        print(f"donation-paths-selftest: {antal} fejl" if antal
              else "donation-paths-selftest: alle kontroller bestået")
        return 1 if antal else 0
    fund, detaljer = dom()
    mangler = uden_laeg()
    for kilde, problemer in detaljer.items():
        for p in problemer:
            print(f"  rød: {kilde}: {p}")
    if mangler:
        print(f"  talt: {len(mangler)} værktøjssider mangler linjen (dømmes ikke): "
              f"{', '.join(mangler)}")
    if fund:
        print(f"donation-paths: RØD — {len(fund)} fejl")
        return 1
    print(f"donation-paths: GRØN — {len(ratchet())} sider dømt, "
          f"{len(mangler)} talt uden dom")
    return 0


if __name__ == "__main__":
    sys.exit(main())
