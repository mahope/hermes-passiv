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
# periode, funktioner, maskiner — læses fra katalogen, så en ny pris ikke kan
# kræve en kodeændring.
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
        "lifetime": "{amount} once — lifetime, first {limit} purchases",
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
        "lifetime": "{amount} én gang — livstid, første {limit} køb",
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
    pris = f"${produkt['price_usd']}{mellemrum}{ord}"
    scope = produkt.get("scope")
    if isinstance(scope, dict) and scope.get(lang):
        pris += f" {scope[lang]}"
    return pris


def celler(nøgle: str, produkt: dict, lang: str, perioder: dict) -> tuple[str, str, str, str, str]:
    """`(gratis-funktioner, pro-funktioner, gratis-pris, pro-pris, noter)`.

    Kolonnerne er gratis og Pro, fordi det er den form `check_stripe_ctas.py`
    målte på otte købssider, og fordi den læses uden at læse en tekst.
    Funktionerne er katalogens, så en kunde ikke kan betale for noget der
    ikke står her.

    Noterne (livstidspris og antal maskiner) ligger i **én** linje under
    tabellen. Målt 2/10 i browseren: inde i den smalle prismødre blev cellen
    260-330 px høj på telefon, fordi hver note skulle brydes i 120 px.
    """
    t = TEKST[lang]

    def punkter(nøgle_fil: str) -> str:
        ud = []
        for feature in produkt.get(nøgle_fil) or []:
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
                                         limit=livstid.get("limit", 100)))
    maskiner = produkt.get("max_devices")
    # `max_devices: 1` betyder for EUComply «ét website pr. licens», ikke én
    # maskine — det står i `scope`. Så under to siger tal ikke noget, og
    # porten lader være.
    if isinstance(maskiner, int) and maskiner > 1:
        ord_ = (produkt.get("devices_word") or {}).get(lang)
        if not ord_:
            ord_ = "devices" if lang == "en" else "enheder"
        noter.append(t["devices"].format(n=maskiner, word=ord_))

    return (f"<ul>{punkter('free_features')}</ul>",
            f"<ul>{punkter('pro_features')}</ul>",
            f'<span class="pro-price">{t["free_price"]}</span>'
            f'<span class="pro-note">{h(t["free_note"])}</span>',
            f'<span class="pro-price">{h(beløb(nøgle, produkt, lang, perioder))}</span>',
            noter)


def blok(nøgle: str, produkt: dict, lang: str, perioder: dict,
         anker_id: str = "") -> str:
    """Den færdige blok. Determinisme er kravet: porten sammenligner bytes."""
    t = TEKST[lang]
    id_attr = f' id="{h(anker_id)}"' if anker_id else ""
    gratis, pro, gratis_pris, pro_pris, noter = celler(
        nøgle, produkt, lang, perioder)
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
                         side.get("anchor") or "").strip()
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
                  side.get("anchor") or "")
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
