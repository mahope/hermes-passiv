#!/usr/bin/env python3
"""Tegner den fælles gratis-mod-Pro-tabel på hver produktside.

Baggrund (målt 2/10): de fire produktsider viste gratis og Pro på fire forskellige
måder. `site/page-profile.html` havde et ni-rækkers ja/—-gitter med **håndskreven**
pris ($0 forever / $19/year / $39 once), `site/deskuptime/index.html` havde et
andet gitter med «19 USD once», `site/clean-copy.html` havde to afsnit i prosa, og
`site/compliance-report.html` én linje. Ingen port dømte priserne i de gitre —
`check_own_prices.py` læser kun beløb i **købsknapper** — så en pris i Stripe kunne
 glide fra teksten uden at nogen så det. Samme fejlform som opgave 40 (konkurrenternes
priser), bare for vores egne.

Derfor ligger tabellen i denne fil, og den tegnes af `tools/stripe_catalog.json`:
beløb, periode, funktioner og antal maskiner. Siderne har kun en markør
`<!-- pro-table -->`, og alt mellem `<!-- pro-table:start -->` og
`<!-- pro-table:end -->` er generatorens — en håndredigering i markørland kan
ikke overleve næste kørsel, fordi `tools/check_pro_table.py` dømmer hver blok mod
det samme output.

    python3 tools/pro_table.py             # vis de otte sider og deres blokke
    python3 tools/pro_table.py --apply     # tegn igen (idempotent)
    python3 tools/pro_table.py --check     # dom, exit 1 ved afvigelse

Rækkerne er to pr. plan — «hvad du får» og «pris» — fordi det er den samme
sammenligning `/scan` laver på dansk og engelsk, og fordi en læser skal kunne se
forskellen uden at læse en afsnitst tekst.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "tools" / "stripe_catalog.json"
SITE = ROOT / "site"

START = "<!-- pro-table:start -->"
END = "<!-- pro-table:end -->"
# Hele det område generatoren ejer: enten den løse markør i kilden, eller den
# blok den har skrevet. Én mønstre gjør `--apply` idempotent uden at den skal
# vide hvilken af de to former filen lige nu har.
EJER_RE = re.compile(
    r"[ \t]*(?:<!--\s*pro-table:start\s*-->.*?<!--\s*pro-table:end\s*-->"
    r"|<!--\s*pro-table\s*-->)", re.S)

# Tekst der ikke findes i katalogen. Kun det, der er **det samme** på tværs af
# produkter: gratisprisen er 0 for alle fire, og «ingen nøgle» er sandt for alle
# fire, fordi de frie værktøjer ikke kan tage imod en nøgle. Alt andet — beløb,
# periode, funktioner, maskiner, omfang — læses fra katalogen, så en ny pris
# ikke kan kræve en kodeændring.
TEKST = {
    "en": {
        "col_plan": "Plan",
        "col_free": "Free",
        "col_pro": "{product}",
        "col_gets": "What you get",
        "col_price": "Price",
        "free_price": "$0",
        "free_note": "no licence key needed",
        "caption": "Free and {product}, side by side",
        "lifetime": "{amount} once{scope} — lifetime, first {limit} purchases",
        "devices": "One licence covers {n} {word}.",
        # Den ordvariant vi vil vise for hver periode. Ordlisten i katalogen
        # rummer både engelsk og dansk i samme række (`yearly` er «/year»,
        # «pr. år», «/år» …), så porten skal vælge — og hunde hvert ord i
        # `billing_periods.words`, ellers ville den opfinde en skrivemåde
        # `check_own_prices.py` ikke kender.
        "period": {"yearly": "/year", "one_time": "once", "lifetime": "lifetime"},
    },
    "da": {
        "col_plan": "Plan",
        "col_free": "Gratis",
        "col_pro": "{product}",
        "col_gets": "Hvad du får",
        "col_price": "Pris",
        "free_price": "$0",
        "free_note": "ingen licensnøgle nødvendig",
        "caption": "Gratis og {product}, side mod side",
        "lifetime": "{amount} én gang{scope} — livstid, første {limit} køb",
        "devices": "Én licens dækker {n} {word}.",
        "period": {"yearly": "/år", "one_time": "én gang", "lifetime": "livstid"},
    },
}


def h(value: str) -> str:
    """Escape til en attribut- og tekst-celle. Katalogen er skrevet af os, men
    et produktnavn med `&` må ikke kunne lukke taggen."""
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def load() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def sider(catalog: dict) -> list[dict]:
    """Sidernes liste fra katalogen, med hver sides produkt og sprog."""
    produkter = catalog["products"]
    ud: list[dict] = []
    for post in catalog.get("pro_table_pages") or []:
        if not isinstance(post, dict):
            continue
        nøgle = post.get("product")
        if nøgle not in produkter:
            raise SystemExit(f"pro_table: ukendt produkt {nøgle!r} i katalogen")
        sprog = post.get("lang")
        if sprog not in TEKST:
            raise SystemExit(f"pro_table: ukendt sprog {sprog!r} for {nøgle}")
        ud.append({**post, "product_obj": produkter[nøgle], "lang": sprog})
    return ud


def scope_tekst(produkt: dict, lang: str) -> str:
    """Katalogens omfang med et foranstående mellemrum — eller tomt.

    `eucomply-pro` sælger pr. website, så **begge** priser skal sige det. Fund fra
    review 2/10: livstidsnoten skrev «$149 once — lifetime» lige under en
    priscelle der sagde «$79/year per website», altså «149 engang for alle
    websites» — en licens der kun gælder for ét. Derfor læses omfanget ét sted,
    og det bruges af både `beløb()` og livstidsnoten.
    """
    scope = produkt.get("scope")
    if isinstance(scope, dict) and scope.get(lang):
        return " " + str(scope[lang])
    return ""


def beløb(nøgle: str, produkt: dict, lang: str, perioder: dict) -> str:
    """Prisen som læseren ser den: beløb, periode og dets omfang.

    Katalogens `price` er dansk («$19/år»), så det kan ikke bruges på en
    engelsk side. Beløbet kommer fra `price_usd`, perioden fra
    `billing_periods.words` — samme ordliste `check_own_prices.py` dom 4
    bygger sin periode-detektor af, så de to kan ikke blive uenige. Ordet skal
    stå i den liste; ellers er det en skrivemåde ingen port kender, og
    `check_own_prices.py` ville dømme knappen bag den rød uden at vide hvorfor.
    """
    tilladt = (perioder.get("products") or {}).get(nøgle) or []
    ordliste = perioder.get("words") or {}
    # Katalogen må kun erklære en periode den faktisk sælger; ellers tager vi
    # den første tilladte, så porten aldrig printer en tom periode.
    periode = tilladt[0] if tilladt else "yearly"
    ord = TEKST[lang]["period"].get(periode)
    tilladte_ord = ordliste.get(periode) or []
    if not ord or ord not in tilladte_ord:
        raise SystemExit(
            f"pro-table: «{ord}» er ikke i katalogens {periode}-periodeord "
            f"for {nøgle} — find en skrivemåde der er, eller tilføj ordet til "
            f"billing_periods.words.{periode}")
    # «/year» og «/år» hænger direkte på beløbet; «once» og «én gang» skal
    # have et mellemrum. Mellemrum er derfor ikke noget katalogen afgør, men
    # portens sprogtabel ved det — ellers stod der «$19once».
    mellemrum = "" if ord.startswith(("/", "$")) else " "
    return f"${produkt['price_usd']}{mellemrum}{ord}{scope_tekst(produkt, lang)}"


def celler(nøgle: str, produkt: dict, lang: str, perioder: dict,
           side_free: list | None = None,
           side_pro: list | None = None) -> tuple[str, str, str, str, list, str]:
    """`(gratis-funktioner, pro-funktioner, gratis-pris, pro-pris, noter, ærlig grænse)`.

    Kolonnerne er gratis og Pro, fordi det er den form `check_stripe_ctas.py`
    målte på otte købssider, og fordi den læses uden at læse en tekst.
    Funktionerne er katalogens, så en kunde ikke kan betale for noget der
    ikke står her.

    `side_free` er sidens **egne** frie funktioner, og den bruges kun af en
    side der ikke er produktets egen (dom 6 i `check_pro_table.py`). Grunden
    er målt 2/10: `page-profile-pro`s liste er skrevet til `page_profile.py`
    — historik, terminalrapport, score og karakter — mens browseren på
    `/url-inspector` ingen af delene har. Uden dette argument ville den have
    tegnet CLI-funktioner ind på en side der ikke kører CLI'en.

    `side_pro` er sidens **egne** Pro-funktioner, og den bruges af samme slags
    sider. Målt 2/10 på `/text-on-image-checker`: kortet lovede «alle de andre
    billeder», og det er **crawl af hele sitet** — en tredje ting, der hverken er
    i `pdf-download` eller i `server-checks`. Uden denne liste ville den have tegnet
    to af tre løfter ind og tabt det tredje, og tabellen ville have sagt mindre
    end det håndskrevne kort den erstatter.

    tabellen. Målt 2/10 i browseren: inde i den smalle prismødre blev cellen
    260-330 px høj på telefon, fordi hver note skulle brydes i 120 px.
    """
    t = TEKST[lang]

    def punkter(nøgle_fil: str, kilder: list | None = None) -> str:
        ud = []
        for feature in (kilder if kilder is not None
                        else (produkt.get(nøgle_fil) or [])):
            labels = (feature.get("labels") or {})
            # Katalogens `labels` er en ordliste over *alternative*
            # skrivemåder af den samme funktion — `check_stripe_ctas.py`
            # matcher dem casefolds, så kun den første bruges her. Alle ville
            # gjort «Unlimited sites, unlimited, 30 second, 30 s» til fire
            # funktioner på en dansk side.
            varianter = labels.get(lang) or []
            if not varianter:
                continue
            tekst = str(varianter[0])
            s = tekst[:1].upper() + tekst[1:] if tekst else tekst
            ud.append(f"<li>{h(s)}</li>")
        return "".join(ud)

    noter: list[str] = []
    livstid = produkt.get("lifetime")
    if isinstance(livstid, dict) and livstid.get("price_usd"):
        noter.append(t["lifetime"].format(amount=f"${livstid['price_usd']}",
                                         limit=livstid.get("limit", 100),
                                         scope=scope_tekst(produkt, lang)))
    maskiner = produkt.get("max_devices")
    # `max_devices: 1` betyder for EUComply «ét website pr. licens», ikke én
    # maskine — det står i `scope`. Så under to siger tal ikke noget, og
    # porten lader være.
    if isinstance(maskiner, int) and maskiner > 1:
        ord_ = (produkt.get("devices_word") or {}).get(lang)
        if not ord_:
            ord_ = "devices" if lang == "en" else "enheder"
        noter.append(t["devices"].format(n=maskiner, word=ord_))
    # `pro_limit` er en **anden slags** oplysning end en prisnote, så den får
    # sin egen linje. Målt 6/10: lagt i samme note læste den
    # «Én licens dækker 3 maskiner. · Alarmer er …» — et punktum midt i en
    # punktumliste. Den linje er ærlig information, ikke en pris, og den skal
    # kunne læses for sig selv.
    grænse = produkt.get("pro_limit")
    ærlig = str(grænse[lang]) if isinstance(grænse, dict) and grænse.get(lang) else ""

    return (f"<ul>{punkter('free_features', side_free)}</ul>",
            f"<ul>{punkter('pro_features', side_pro)}</ul>",
            f'<span class="pro-price">{t["free_price"]}</span>'
            f'<span class="pro-note">{h(t["free_note"])}</span>',
            f'<span class="pro-price">{h(beløb(nøgle, produkt, lang, perioder))}</span>',
            noter, ærlig)


def kompakt_blok(blok_tekst: str, rel: str) -> str:
    """Én linje, så blokken også kan stå **inde i en JavaScript-streng**.

    Målt 2/10: elleve af de tretten pro-kort ligger i et inline script, som en
    streng med `+`-sammensætning (`var PRO_CARD = '<div class="pro-card">' …`).
    Den normale blok har linjeskift, og en rå linjeskift i en enkelt- eller
    dobbeltanførselst streng er en **syntaxfejl** — så den ville have slået
    værktøjssiden ihjel ved den første indlæsning, ikke ved porten.

    Derfor er der to former, og katalogen vælger med `layout: "inline"`.formen
    må ikke indholde noget der kan lukke strengen eller blokere HTML-parsingen:

      - intet linjeskift (det er hele pointen),
      - ingen `'`, fordi den er strengens afslutning,
      - ingen `\\`, fordi en backslash ville ændre betydningen af det der står
        efter den,
      - intet `</script`, fordi blokken ligger inde i et inline `<script>`.

    Ét `raise` i stedet for en stille fejl: en katalogtekst med et apostrof
    eller et linjeskift ville ellers give en værktøjsside der ikke indlæser, og
    ingen port læser en syntaksfejl i en streng den bare sammenligner bytes i.
    """
    tekst = " ".join(blok_tekst.split())
    for forbudt, hvad in (("'", "apostrof"), ("\\", "backslash"),
                          ("</script", "</script")):
        if forbudt in tekst:
            raise SystemExit(
                f"pro-table: {rel} er layout=inline, og blokken indeholder en "
                f"{hvad} ({forbudt!r}) — den ville lukke JavaScript-strengen. "
                f"Skriv teksten uden den, eller giv siden layout=block.")
    return tekst


def blok(nøgle: str, produkt: dict, lang: str, perioder: dict,
         anker_id: str = "", side_free: list | None = None,
         side_pro: list | None = None, layout: str = "block") -> str:
    """Den færdige blok. Determinisme er kravet: porten sammenligner bytes."""
    t = TEKST[lang]
    id_attr = f' id="{h(anker_id)}"' if anker_id else ""
    gratis, pro, gratis_pris, pro_pris, noter, ærlig = celler(
        nøgle, produkt, lang, perioder, side_free, side_pro)
    linjer = [
        START,
        '<div class="table-wrap">',
        # Ankeret er valgt i katalogen: 20 links i dist/deskuptime.com peger
        # på `/#compare`, fordi den håndskrevne tabel havde id="compare", og de
        # fleste af de sider ligger i ../auditedwp som vi ikke må ændre.
        f'<table class="compare pro-table"{id_attr}>',
        f'  <caption class="sr-only">{h(t["caption"].format(product=h(produkt["name"])))}</caption>',
        "  <thead>",
        f'    <tr><th scope="col"><span class="sr-only">{h(t["col_plan"])}</span></th>'
        f'<th scope="col">{h(t["col_free"])}</th>'
        f'<th scope="col">{h(t["col_pro"].format(product=h(produkt["name"])))}</th></tr>',
        "  </thead>",
        "  <tbody>",
        f'    <tr><th scope="row">{h(t["col_gets"])}</th><td>{gratis}</td><td>{pro}</td></tr>',
        f'    <tr><th scope="row">{h(t["col_price"])}</th><td>{gratis_pris}</td><td>{pro_pris}</td></tr>',
        "  </tbody>",
        "</table>",
        "</div>",
    ]
    if noter:
        linjer.append(f'<p class="pro-note">{" · ".join(h(n) for n in noter)}</p>')
    if ærlig:
        # Samme klasse som prisnoten, så den ser ud som den del af kortet den
        # er — og så den arver styling på de sider der ikke linker
        # `/style.css` (`/cookie-check` og `/url-inspector` gør ikke det).
        # Den ekstra klasse er portens krog: dom 4c i `check_pro_table.py`
        # finder præcis denne linje, så en grænse der forsvinder fra
        # noten stadig dømmes.
        linjer.append(f'<p class="pro-note pro-limit">{h(ærlig)}</p>')
    linjer.append(END)
    return "\n".join(linjer)


def dom(catalog: dict) -> list[str]:
    fund: list[str] = []
    perioder = catalog.get("billing_periods", {})
    for side in sider(catalog):
        fil = ROOT / side["path"]
        rel = side["path"]
        if not fil.exists():
            fund.append(f"{rel}: filen findes ikke")
            continue
        html = fil.read_text(encoding="utf-8")
        områder = EJER_RE.findall(html)
        if len(områder) != 1:
            fund.append(f"{rel}: {len(områder)} pro-table-områder — "
                        f"en side skal have præcis ét")
            continue
        nøgle = side["product"]
        forventet = blok(nøgle, side["product_obj"], side["lang"], perioder,
                         side.get("anchor") or "",
                         side.get("free_features"), side.get("pro_features"),
                         side.get("layout") or "block").strip()
        if (side.get("layout") or "block") == "inline":
            forventet = kompakt_blok(forventet, rel)
        if områder[0].strip() != forventet:
            fund.append(f"{rel}: blokken er ikke tegnet af katalogen "
                        f"(kør `python3 tools/pro_table.py --apply`)")
    return fund


def anvend(catalog: dict) -> int:
    perioder = catalog.get("billing_periods", {})
    ændret = 0
    for side in sider(catalog):
        fil = ROOT / side["path"]
        rel = side["path"]
        if not fil.exists():
            print(f"  springer over: {rel} findes ikke")
            continue
        html = fil.read_text(encoding="utf-8")
        antal = len(EJER_RE.findall(html))
        if antal == 0:
            print(f"  springer over: {rel} har ingen <!-- pro-table -->")
            continue
        if antal > 1:
            raise SystemExit(f"pro-table: {rel} har {antal} pro-table-områder")
        ny = blok(side["product"], side["product_obj"], side["lang"], perioder,
                  side.get("anchor") or "", side.get("free_features"),
                  side.get("pro_features"), side.get("layout") or "block")
        if (side.get("layout") or "block") == "inline":
            ny = kompakt_blok(ny, rel)
        ny_html = EJER_RE.sub(lambda _m: ny, html, count=1)
        if ny_html != html:
            fil.write_text(ny_html, encoding="utf-8")
            ændret += 1
            print(f"  tegnet: {rel}")
    return ændret


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="tegn tabellen igen på alle otte sider")
    parser.add_argument("--check", action="store_true",
                        help="dom hver blok mod katalogen (samme som check_pro_table.py)")
    args = parser.parse_args(argv)
    catalog = load()
    if args.apply:
        antal = anvend(catalog)
        print(f"pro-table: {antal} sider tegnet igen")
        return 0
    fund = dom(catalog)
    for linje in fund:
        print(linje)
    if fund:
        print(f"\npro-table: RØD — {len(fund)} fund")
        return 1
    print(f"pro-table: GRØN — {len(sider(catalog))} sider med den samme "
          f"to-rækkers-tabel fra katalogen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
