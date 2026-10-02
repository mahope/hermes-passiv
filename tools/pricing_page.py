#!/usr/bin/env python3
"""Byg `/pricing` — den ene side der viser hvad alt koster.

Baggrund (målt 2/10): katalogen har 13 produkter, og de ligger spredt på otte
sider. `site/paid-templates.html` sælger de syv skabeloncekøb, `site/clean-copy.html`
sælger Clean Copy Pro, `site/deskuptime/index.html` sælger DeskUptime Pro,
`site/page-profile.html` sælger Page Profile Pro, og `site/compliance-report.html`
sælger EUComply Pro. **Ingen side viser dem samlet.** Målt på de 102 ruter i
`tools/route_inventory.json` er der ingen, hvis `<title>` eller `<h1>` nævner
to produkter på én gang, så en læser der skal finde ud af, om de vil betale for
compliance eller for Clean Copy, skal først gætte hvilken af de otte sider der
har det rigtige svar.

Det er tre filtre forude i købsrejsen på den ene slags spørgsmål, der ikke
handler om et enkelt værktøj: *hvad koster det, og hvad får jeg for det?*

Derfor ligger siden i denne fil og ikke i hånden. Samme begrundelse som
`tools/pro_table.py`: beløb, periode, omfang og betalingslink læses **kun** fra
`tools/stripe_catalog.json`, så en pris i Stripe kan glide uden at nogen kan se
det på siden. Kilden har blot en markør `<!-- pricing:start -->` … `<!--
pricing:end -->`, og alt mellem markørerne er generatorens — en håndredigering
kan ikke overleve næste kørsel, fordi `tools/check_pricing_page.py` dømmer
blokken mod præcis det output.

**Siden sælger ikke — den linker.** Der er allerede én købsside pr. produkt:
`/compliance-report`, `/page-profile`, `/paid-templates`, `cleancopy.tools/`,
`deskuptime.com/` og `/support`. Målt 2/10 da jeg prøvede at sælge direkte:
`check_stripe_ctas.py` læser en sides gratis/Pro-flade som **én** produkts
påstande, så tolv produkter på én side gav hver sin fejl — «den gratis side af
siden nævner ikke 'history'», fordi den side der sælger EUComply Pro også
nævner Page Profiles gratis-funktioner. Det er ikke en fejl i porten, det er
en fejl i designet: en side der sælger tolv ting er ikke en produktside.

Derfor linker hver række til produktets egen købsside, læst fra katalogens
`pricing_link`. Prisen står her, købet sker der. Det er samme regel som resten
af repoet: `check_pro_card.py` og `check_pro_table.py` er begge bygget på «én
købsvej pr. produkt», og planen 2/10 afviste livstidsprisen som prislink af
præcis den grund.

    python3 tools/pricing_page.py             # vis produkterne og deres ruter
    python3 tools/pricing_page.py --apply     # byg siden (idempotent)
    python3 tools/pricing_page.py --check     # dom, exit 1 ved afvigelse
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

START = "<!-- pricing:start -->"
END = "<!-- pricing:end -->"
EJER_RE = re.compile(
    r"[ \t]*(?:<!--\s*pricing:start\s*-->.*?<!--\s*pricing:end\s*-->"
    r"|<!--\s*pricing-grid\s*-->)", re.S)

# Produkterne sorteres efter den rolle de spiller i købsrejsen, ikke efter
# navn: et abonnement man betaler for hvert år skal stå over et engangskøb af
# en PDF, fordi det er abonnementet der afgør om nogen overhovedet kommer
# tilbage. Række `kind` er derfor sluttet til katalogens `kind` — den er den
# maskinlæsbare sandhed om hvad et produkt er, og den findes i katalogen.
import pro_table
from pro_table import beløb, scope_tekst

RÆKKE = {"license": 0, "download": 1, "template": 1, "donation": 2}

# `title`, `description` og `h1` er **ikke** genereret — de står i sidens egen
# `<head>`/`<h1>`, fordi de er håndskrevne og kun skal findes ét sted. De ligger
# her for at kunne læses samlet med resten, og de skal holdes i overensstemmelse
# med siden; resten af `TEKST` bruges af `byg_blok()`.
TEKST = {
    "en": {
        "title": "Pricing — every Mahope tool and template, in one list",
        "description": ("Every paid Mahope product with its real price: Clean Copy Pro, "
                        "DeskUptime Pro, EUComply Pro and Page Profile Pro, plus the paid "
                        "compliance templates. Free tools stay free."),
        "th_product": "Product",
        "th_price": "Price",
        "th_free": "What you get free",
        "th_gets": "What the paid version adds",
        "th_buy": "Where to buy",
        "buy_label": "Buy",
        "donate_label": "Donate",
        "buy_missing": "No page yet",
        "free_th": "Free",
        "free_td": ("Every tool on this site, with no account and no limit on how many "
                    "pages you run through it."),
        "free_gets": "Nothing — this row is what you get without paying.",
        "free_nobuy": "Nothing to buy",
        "no_free_tier": "No free version — this is the paid product.",
        "lifetime_label": "Lifetime",
        "devices": "{n} machines",
        "one_device": "1 machine",
        "lifetime_note": ("Lifetime is a one-time price for the same product, with no renewal "
                          "and no expiry. Founding price, first {limit} purchases."),
        "lifetime_td": "Pay once. No renewal, no expiry.",
        "license_note": "A licence key, sent to your email after payment.",
        "download_note": "Delivered as files right after payment.",
        "donation_note": ("Optional, and it changes nothing about the tools. Every tool here "
                          "stays free whether you give or not."),
        "donation_price": "Any amount",
    },
    "da": {
        "title": "Priser — alle Mahope-værktøjer og -skabeloner samlet",
        "description": ("Alle betalte Mahope-produkter med den rigtige pris: Clean Copy Pro, "
                        "DeskUptime Pro, EUComply Pro og Page Profile Pro, plus de betalte "
                        "compliance-skabeloner. Gratisværktøjerne bliver gratis."),
        "h1": "Hvad alt koster",
        "th_product": "Produkt",
        "th_price": "Pris",
        "th_free": "Hvad du får gratis",
        "th_gets": "Hvad den betalte version tilføjer",
        "th_buy": "Hvor du køber",
        "buy_label": "Køb",
        "donate_label": "Donér",
        "buy_missing": "Ingen side endnu",
        "free_th": "Gratis",
        "free_td": ("Alle værktøjer på denne side, uden konto og uden grænse for hvor mange "
                    "sider du kører dem på."),
        "free_gets": "Intet — denne række er det du får uden at betale.",
        "free_nobuy": "Intet at købe",
        "no_free_tier": "Ingen gratis udgave — dette er det betalte produkt.",
        "lifetime_label": "Livstid",
        "devices": "{n} maskiner",
        "one_device": "1 maskine",
        "lifetime_note": ("Livstid er en engangspris for samme produkt, uden fornyelse og uden "
                          "udløb. Stiftelsespris, første {limit} køb."),
        "lifetime_td": "Betal én gang. Ingen fornyelse, intet udløb.",
        "license_note": "En licensnøgle på din mail efter betaling.",
        "download_note": "Leveres som filer lige efter betaling.",
        "donation_note": ("Valgfrit, og det ændrer intet ved værktøjerne. Alle værktøjer her er "
                          "gratis, uanset om du giver."),
        "donation_price": "Valgfrit beløb",
    },
}

# Hver produkttype får én kort beskrivelse af hvad man **får ved at betale**.
# Skrevet her, ikke i katalogen, fordi det er redaktionel tekst: katalogen er
# maskinlæsbar og bruges af otte andre porte, og den skal ikke få et felt der
# kun én side læser. `check_pricing_page.py` dømmer at nøgleordet for hver
# produkttype står i kortet, så en ny `kind` i katalogen bliver rød her indtil
# den har fået en ærlig beskrivelse — ikke en tom celle.
GETS = {
    "clean-copy-pro": {
        "en": ("Batch conversion, your own cleaning rules, and JSON output — for the "
               "pages you have to redo every week."),
        "da": ("Batch-konvertering, dine egne rense regler og JSON-output — til de sider "
               "du skal lave om hver uge."),
    },
    "deskuptime-pro": {
        "en": ("Monitoring that runs on a schedule instead of on your laptop: webhooks, "
               "unlimited sites, and a client report."),
        "da": ("Overvågning der kører på en tidsplan i stedet for på din bærbar: webhooks, "
               "ubegrænsede sites og en kunderapport."),
    },
    "eucomply-pro": {
        "en": ("A scan becomes a report you can send a client: EAA, GDPR cookie consent "
               "and NIS2 findings in one PDF."),
        "da": ("Et scan bliver en rapport du kan sende en kunde: EAA, GDPR-cookieconsent "
               "og NIS2-fund i én PDF."),
    },
    "page-profile-pro": {
        "en": ("Unlimited redirect-chain and Open Graph checks, with the results you can "
               "paste into a report."),
        "da": ("Ubegrænsede redirect-kæde- og Open Graph-tjek, med resultater du kan "
               "sætte ind i en rapport."),
    },
    "donation": {
        "en": "Keeps the free tools free. No feature is held back.",
        "da": "Holder gratisværktøjerne gratis. Ingen funktion er holdt tilbage.",
    },
    "template": {
        "en": "The document, written and ready to send.",
        "da": "Dokumentet, skrevet og klar til at sende.",
    },
}


def katalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def sorter(key: str, produkt: dict) -> tuple:
    """Sortér efter rolle, så et abonnement står over et engangskøb."""
    return (RÆKKE.get(produkt.get("kind", ""), 9), key)


def produkter(cat: dict, lang: str) -> list[tuple[str, dict]]:
    """(nøgle, produkt) for de produkter prislisten skal vise.

    `transmute-desktop` er bevidst **uden**, fordi katalogen siger
    `pricing_page: false` på det: det sælges på transmute.run, som er et
    separat site i et andet repo. En pris her uden købsknap ville være en pris
    læseren ikke kan købe — præcis den fejl `check_stripe_ctas.py` findes for
    at fange. At det er et **felt** og ikke en note i prosa er pointen: en
    håndredigeret undtagelse i denne fil ville være næste sted en ny port
    skulle lede efter.
    """
    # Kun produkter med en købsside. En vare uden `pricing_link` kan ikke have
    # et link på siden — den ville pege på ingenting — så den hører hjemme
    # i `check_pricing_page.py`s dom 4, der gør netop den mangel rød i stedet
    # for at den forsvinder stille.
    ud = [(k, v) for k, v in cat["products"].items()
          if v.get("pricing_page") is not False and v.get("pricing_link")]
    return sorted(ud, key=lambda par: sorter(*par))


def enheder(produkt: dict, lang: str) -> str:
    """Antal maskiner — kun når et produkt har en `scope` (pr. website), fordi
    ellers er maskinantallet ikke det en læser skal vælge på: EUComply Pro
    sælger pr. website, og «1 machine» oveni læses som en ekstra begrænsning
    oven på en pris der i forvejen er afgrænset til ét website."""
    n = produkt.get("max_devices")
    scope = produkt.get("scope")
    if not isinstance(n, int) or n < 1 or (isinstance(scope, dict) and scope.get(lang)):
        return ""
    t = TEKST[lang]
    return t["one_device"] if n == 1 else t["devices"].format(n=n)


def prislinje(nøgle: str, produkt: dict, lang: str, cat: dict) -> str:
    """Pris, periode, omfang og enheder.

    Katalogens `price` er dansk («$19/år»), så den kan ikke bruges på en
    engelsk side. Derfor læses beløb og periode gennem `pro_table.beløb()` —
    samme læser som produktsidernes egen tabel, bygget på samme
    `billing_periods.words` som `check_own_prices.py` dømmer. To læsere af det
    samme beløb er præcis den fejlform de otte forgangne revisioner i denne
    familie fandt.
    """
    t = TEKST[lang]
    if produkt.get("kind") == "donation":
        return t["donation_price"]
    dele = [beløb(nøgle, produkt, lang, cat.get("billing_periods") or {})]
    enhed = enheder(produkt, lang)
    if enhed:
        dele.append(enhed)
    livstid = produkt.get("lifetime")
    if isinstance(livstid, dict) and livstid.get("price_usd"):
        dele.append(f"{t['lifetime_label']}: ${livstid['price_usd']}"
                    f"{scope_tekst(produkt, lang)}")
    return " · ".join(d for d in dele if d)


def gets_tekst(nøgle: str, produkt: dict, lang: str) -> str:
    """Kortteksten i kolonnen «hvad den betalte version tilføjer»."""
    kind = produkt.get("kind", "")
    if nøgle in GETS:
        return GETS[nøgle][lang]
    if kind == "donation":
        return GETS["donation"][lang]
    return GETS["template"][lang]


def gratis_tekst(nøgle: str, produkt: dict, lang: str) -> str:
    """Hvad den **gratis** udgave allerede kan — katalogens `free_features`.

    Samme krav som på produktsiderne: `check_stripe_ctas.py` dom 6b dømmer, at
    en side der sælger et produkt også skal vise hvad kunden får gratis, fordi
    «dette er gratis» ellers er en påstand uden flade. Her læses teksten af
    katalogens egne `labels`, så den ikke kan glide fra det sted hvor den er
    dokumenteret.

    Kun **første** label pr. funktion. En funktion har ofte to skrivemåder
    («history tracking» / «historik»), og porten dømmer på den første — så
    alle skriver bare den første.
    """
    dele = []
    for feature in produkt.get("free_features") or []:
        labels = feature.get("labels") if isinstance(feature, dict) else None
        if isinstance(labels, dict):
            for tekst in labels.get(lang) or []:
                if tekst:
                    dele.append(str(tekst))
                    break
    if dele:
        return ", ".join(dele)
    # Et download eller en donation har ingen gratis udgave. Det skal stå,
    # ikke stå tomt: en tom celle i en pris-tabel er ulæselig, og
    # `check_stripe_ctas.py` dommerer tomme celler i en gratis/Pro-tabel
    # fordi de læses som «den her giver ingenting».
    return TEKST[lang]["no_free_tier"]


def note_tekst(nøgle: str, produkt: dict, lang: str) -> str:
    """Den lille linje under knappen.

    Hvilken note der er rigtig afhænger af **hvilken vare** det er, ikke af
    om den har en livstidsudgave: en livstidslicens skal forklare at den er
    engangs og ubegrænset, en PDF skal siges at den kommer med det samme, og
    en donation skal siges at den ikke låser noget op. Først at vælge efter
    «har den lifetime?» gav DeskUptime Pro «Delivered as files right after
    payment» — den er en licens til et program, ikke et download.
    """
    t = TEKST[lang]
    livstid = produkt.get("lifetime")
    if produkt.get("kind") == "donation":
        return t["donation_note"]
    if isinstance(livstid, dict) and livstid.get("limit"):
        return t["lifetime_note"].format(limit=livstid["limit"])
    if produkt.get("kind") == "license":
        return t["license_note"]
    return t["download_note"]


def købs_rute(produkt: dict, lang: str) -> str:
    """Ruten til produktets købsside i det sprog, siden er skrevet på.

    Katalogen kender kun den engelske rute, og det er nok: målt 2/10 i
    dist-sitemap findes den danske som præcis samme rute med `/da/` foran.
    Derfor skrives den danske rute her **én** gang frem for seks gange i
    katalogen — seks næsten ens felter er seks steder at glemme en."""
    rute = produkt.get("pricing_link") or ""
    if lang != "da" or rute.startswith(("http://", "https://", "/da/")):
        return rute
    return f"/da{rute}"


def købs_knap(nøgle: str, produkt: dict, lang: str) -> str:
    """Linket til produktets egen købsside — aldrig et Stripe-link.

    `pricing_link` er eksplicit i katalogen pr. produkt, så en ny vare uden en
    købsside er **rød** i `check_pricing_page.py` frem for at få en knap der
    ingen vegne hen går."""
    # Katalogens `pricing_link` er den engelske rute. Kun de få produkter der
    # har en dansk udgave får `pricing_link_da`; resten har samme rute på begge
    # sprog, målt 2/10 i dist-sitemap. Uden den skelnen skrev den danske side
    # et engelsk link, og check_hreflang_pairs.py gjorde den rød.
    rute = købs_rute(produkt, lang)
    t = TEKST[lang]
    if not rute:
        return t["buy_missing"]
    return f"{t['buy_label']} {produkt['name']}" if produkt.get("kind") != "donation" \
        else t["donate_label"]


def byg_blok(cat: dict, lang: str) -> str:
    """Hele det genererede område. Hver værdi læses fra katalogen."""
    t = TEKST[lang]
    rækker = []
    for nøgle, produkt in produkter(cat, lang):
        rækker.append(
            f'      <tr data-product="{nøgle}">\n'
            f'        <th scope="row">{produkt["name"]}</th>\n'
            f'        <td>{prislinje(nøgle, produkt, lang, cat)}</td>\n'
            f'        <td class="pc-free"><span class="pc-lbl">{t["th_free"]}</span>'
            f'{gratis_tekst(nøgle, produkt, lang)}</td>\n'
            f'        <td><span class="pc-lbl">{t["th_gets"]}</span>'
            f'{gets_tekst(nøgle, produkt, lang)}</td>\n'
            f'        <td><a class="pc-buy" href="{købs_rute(produkt, lang)}">'
            f'{købs_knap(nøgle, produkt, lang)}</a>'
            f'<span class="pc-note">{note_tekst(nøgle, produkt, lang)}</span></td>\n'
            f'      </tr>')

    livstid_rækker = []
    for nøgle, produkt in produkter(cat, lang):
        livstid = produkt.get("lifetime")
        if not (isinstance(livstid, dict) and livstid.get("price_usd")):
            continue
        livstid_rækker.append(
            f'      <tr data-lifetime="{nøgle}">\n'
            f'        <th scope="row">{produkt["name"]} — {t["lifetime_label"]}</th>\n'
            f'        <td>${livstid["price_usd"]}{scope_tekst(produkt, lang)}</td>\n'
            f'        <td class="pc-free"><span class="pc-lbl">{t["th_free"]}</span>'
            f'{gratis_tekst(nøgle, produkt, lang)}</td>\n'
            f'        <td>{t["lifetime_td"]}</td>\n'
            f'        <td><a class="pc-buy" href="{købs_rute(produkt, lang)}">'
            f'{("Buy" if lang == "en" else "Køb")} {produkt["name"]} — '
            f'${livstid["price_usd"]}</a></td>\n'
            f'      </tr>')

    dele = [
        f"    <table class=\"pc-table\">\n"
        f"      <caption class=\"sr-only\">{t['th_product']}, {t['th_price']}, "
        f"{t['th_free']}, {t['th_gets']}</caption>\n"
        f"      <thead><tr>"
        f"<th scope=\"col\">{t['th_product']}</th>"
        f"<th scope=\"col\">{t['th_price']}</th>"
        f"<th scope=\"col\">{t['th_free']}</th>"
        f"<th scope=\"col\">{t['th_gets']}</th>"
        f"<th scope=\"col\">{t['th_buy']}</th>"
        f"</tr></thead>\n"
        f"      <tbody>\n"
        f'      <tr data-product="free">\n'
        f"        <th scope=\"row\">{t['free_th']}</th>\n"
        f"        <td>$0</td>\n"
        f"        <td class=\"pc-free\">{t['free_td']}</td>\n"
        f"        <td>{t['free_gets']}</td>\n"
        f"        <td class=\"pc-nobuy\">{t['free_nobuy']}</td>\n"
        f"      </tr>\n" + "\n".join(rækker) + "\n      </tbody>\n    </table>",
    ]
    if livstid_rækker:
        dele.append(
            f"    <h2 id=\"lifetime\">{t['lifetime_label']}</h2>\n"
            f"    <table class=\"pc-table\">\n"
            f"      <caption class=\"sr-only\">{t['th_product']}, {t['th_price']}, "
            f"{t['lifetime_td']}</caption>\n"
            f"      <thead><tr>"
            f"<th scope=\"col\">{t['th_product']}</th>"
            f"<th scope=\"col\">{t['th_price']}</th>"
            f"<th scope=\"col\">{t['th_free']}</th>"
            f"<th scope=\"col\">{t['th_gets']}</th>"
            f"<th scope=\"col\">{t['th_buy']}</th>"
            f"</tr></thead>\n"
            f"      <tbody>\n" + "\n".join(livstid_rækker) + "\n      </tbody>\n    </table>")
    # Markørerne **inde i** blokken, ikke omkring den. `_sæt_indhold` erstatter
    # hele `EJER_RE`-træffet, så hvis markørerne lå uden for ville den første
    # `--apply` slette dem og den næste ville indsætte en ekstra tabel oveni.
    # Samme som `tools/pro_table.py`: den skrev også sine egne markører.
    return f"{START}\n" + "\n".join(dele) + f"\n{END}"


def sider(cat: dict) -> list[tuple[Path, str]]:
    """(fil, sprog) for de to sider generatoren ejer."""
    sider_ = cat.get("pricing_pages")
    if not sider_:
        return [(SITE / "pricing.html", "en"), (SITE / "da" / "pricing.html", "da")]
    return [(ROOT / post["path"], post["lang"]) for post in sider_]


def _sæt_indhold(kilde: str, blok: str) -> str:
    """Erstat markørområdet. Uden markøren indsættes blokken lige før
    `</main>`, så en ny side ikke behøver en tom pladsholder i kilden."""
    if EJER_RE.search(kilde):
        return EJER_RE.sub(lambda _: blok, kilde, count=1)
    return kilde.replace("</main>", f"{blok}\n</main>", 1)


def _apply(cat: dict, rod: Path) -> list[str]:
    """Byg begge sider i `rod` (som i selftesten)."""
    ændret = []
    for post in cat.get("pricing_pages") or [
            {"path": "site/pricing.html", "lang": "en"},
            {"path": "site/da/pricing.html", "lang": "da"}]:
        sti = rod / post["path"]
        lang = post["lang"]
        kilde = sti.read_text(encoding="utf-8")
        ny = _sæt_indhold(kilde, byg_blok(cat, lang))
        if ny != kilde:
            sti.write_text(ny, encoding="utf-8")
            ændret.append(post["path"])
    return ændret


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="byg siden")
    parser.add_argument("--check", action="store_true", help="dom, exit 1 ved afvigelse")
    args = parser.parse_args(argv)
    cat = katalog()

    if args.check:
        fejl = []
        for sti, lang in sider(cat):
            kilde = sti.read_text(encoding="utf-8")
            m = EJER_RE.search(kilde)
            if not m:
                fejl.append(f"{sti.relative_to(ROOT)}: ingen `pricing`-blok")
                continue
            # **Én** blok. `EJER_RE` rammer kun den første, så enfil med to
            # blokke ville være grøn her — målt 2/10, da en `--apply` der ikke
            # fandt markøren indsatte en ekstra tabel oveni den gamle. Tælles
            # derfor eksplicit, siden dobbeltprisen er den fejl en læser
            # mærker først.
            for mærke in (START, END):
                antal = kilde.count(mærke)
                if antal != 1:
                    fejl.append(f"{sti.relative_to(ROOT)}: {antal} {mærke} "
                                f"(skal være 1) — siden har mere end én "
                                f"generatorblok")
            if m.group(0) != byg_blok(cat, lang):
                fejl.append(f"{sti.relative_to(ROOT)}: blokken afviger fra generatoren")
        for f in fejl:
            print(f"  {f}")
        print(f"pricing_page --check: {'GRØN' if not fejl else 'RØD'} "
              f"({len(sider(cat))} sider)")
        return 1 if fejl else 0

    if args.apply:
        for f in _apply(cat, ROOT):
            print(f"  skrev {f}")
        return 0

    for nøgle, produkt in produkter(cat, "en"):
        print(f"{produkt['name']:36s} {produkt.get('price') or '-':22s} "
              f"{produkt['kind']:10s} {produkt['payment_link']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())