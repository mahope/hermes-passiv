#!/usr/bin/env python3
"""Dømmer hver købsknap i `site/` mod `tools/stripe_catalog.json`.

Baggrund (1/10): `check_stripe_ctas.py` dømmer *hvilke* produkter en side sælger
og at der er en købsknap. `check_competitor_prices.py` dømmer **konkurrenternes**
beløb mod `tools/competitor_prices.json`. **Ingen port dømte vores egne priser.**
Målt 1/10 på alle 84 købsknapper gav det 0 fund — fordi porten ikke fandtes.

Det er samme fejlform som opgave 33 (konkurrentpriser): et beløb i teksten er en
påstand uden dom. Den faldt lige så stille for *vores egen* omsætning. En gammel
`$19/år` for et produkt Stripe nu sælger engang, eller en knap der siger `$149`
om et `$59`-produkt, er præcis lige så stille som `$144/year` var på
UptimeRobot-siden.

Fire domme:

1. **Prisen skal stå.** En købsknap skal have sit beløb i knappens egen tekst,
   eller i en `pt-price` i samme `.pt-foot` — målt 1/10 har 70 af 84 knapper
   beløbet i teksten, og de 14 øvrige er pristags i `.pt-foot` på
   `/paid-templates` (EN + DA). Uden beløb kan læseren ikke regne ud, hvad
   noget koster, før klikket.
2. **Beløbet skal være katalogets.** Ethvert beløb i knappens tekst skal være
   `price_usd` for den variant, linket peger på. Det fanger både en gammel
   pris og *et ekstra* beløb ved siden af det rigtige — `$19/$39` i én knap er
   to påstande, og kun den ene kan være den, linket sælger.
3. **Linket skal pege på det produkt det er sat på.** Katalogens `payment_link`
   læses *pr. række* i kontrakttabellen og pr. nøgle i `_worker.js`, så to
   produkter der har byttet link er et fund. `check_stripe_ctas` spørger kun om
   linket *findes et sted i* kontrakten — et byttet link er derfor stadig
   grønt der.
4. **Perioden skal være katalogens, og den skal stå.** Dom 1 dømmer beløbet,
   så «Buy DeskUptime Pro — 19 USD» om et produkt Stripe sælger **engang** var
   grønt, selv om teksten slet ikke siger det — og `$19` er det samme tal som
   Clean Copy Pro *tilbage* i dag, så læseren kan ikke gætte sig til forskellen.
   Omvendt er «$39 once» på et engangskøb en påstand uden dom. Katalogens
   `billing_periods` siger hvilke ord der må bruges (`yearly`, `one_time`,
   `lifetime`) for hvert produkt, og porten bygger sin detektor af den ordliste,
   så et nyt ord i katalogen genkendes uden at porten ændres. Et produkt uden
   `periods` i katalogen kan ikke dømmes, og det er selv et fund.

Selvtesten bygger hver mutation ind i en kopi af `site/`, så porten skal kunne
fejle. Brug: `python3 tools/check_own_prices.py [--json] [--self-test]`
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "tools" / "stripe_catalog.json"
CONTRACT = ROOT / "docs" / "stripe-kontrakt.md"
WORKER = ROOT / "site" / "_worker.js"
SITE = ROOT / "site"

BUY_LINK = re.compile(r"^https://buy\.stripe\.com/[A-Za-z0-9]+$")
ANCHOR = re.compile(
    r'<a\b[^>]*href="(https://(?:buy|donate)\.stripe\.com/[^"]+)"[^>]*>(.*?)</a>',
    re.I | re.S)
TAG = re.compile(r"<[^>]+>")

# Beløb i begge retninger. Danske sider skriver «79 $ pr. år» og engelske «$79»,
# og nogle skriver «19 USD». `&nbsp;` er et mellemrum for en browser, så det er
# et mellemrum her også — målt 1/10, ellers fandt porten 38 af 84 knapper
# «uden pris», som alle svarede til «79&nbsp;$».
ENTITIES = (("&nbsp;", " "), ("&#160;", " "), ("&thinsp;", " "), ("&#8201;", " "),
            ("&ensp;", " "), ("&emsp;", " "))
CURRENCY = r"US\$|\$|&euro;|€|USD|EUR|DKK"
AMOUNT = re.compile(
    rf"(?:{CURRENCY})\s?(\d[\d.,]*)"          # $79
    rf"|(\d[\d.,]*)\s?(?:{CURRENCY})"          # 79 $ / 19 USD
    rf"|(\d[\d.,]*)\s?kr\.?", re.I)

PRICE_TAG = re.compile(
    r'<p[^>]*class="[^"]*\bpt-price\b[^"]*"[^>]*>(.*?)</p>', re.I | re.S)
PT_FOOT = re.compile(r'<div[^>]*class="[^"]*\bpt-foot\b[^"]*"[^>]*>')


def plain(text: str) -> str:
    """Tags væk, entities løst, mellemrum normaliseret."""
    for old, new in ENTITIES:
        text = text.replace(old, new)
    text = unescape(TAG.sub(" ", text))
    return re.sub(r"\s+", " ", text).strip()


def amounts(text: str) -> list[tuple[float, str]]:
    """Alle beløb i `text` som `(tal, currency)`. «79 $» og «$79» er samme."""
    found: list[tuple[float, str]] = []
    for m in AMOUNT.finditer(text):
        raw = next(g for g in m.groups() if g)
        digits = re.sub(r"[.,]", "", raw)
        try:
            value = float(digits)
        except ValueError:
            continue
        cur = next(c for c in re.findall(CURRENCY, m.group(0), re.I) if c)
        found.append((value, cur))
    return found


def catalog_prices(catalog: dict) -> dict[str, dict]:
    """`{payment_link: {product, variant, price, name, periods}}` pr. købslink."""
    periods = catalog.get("billing_periods", {}).get("products", {})
    lifetimes = catalog.get("billing_periods", {}).get("lifetime", {})
    out: dict[str, dict] = {}
    for key, product in catalog["products"].items():
        link = product.get("payment_link")
        if isinstance(link, str):
            out[link] = {"product": key, "variant": "abonnement"
                         if product.get("subscription") else "engang",
                         "price": product.get("price_usd"),
                         "periods": periods.get(key),
                         "name": product.get("name", key)}
        life = product.get("lifetime") or {}
        if isinstance(life.get("payment_link"), str):
            out[life["payment_link"]] = {
                "product": key, "variant": "lifetime",
                "price": life.get("price_usd"),
                "periods": lifetimes.get(key),
                "name": f"{product.get('name', key)} Lifetime"}
    return out


def period_detector(catalog: dict) -> tuple[re.Pattern, dict[str, str]] | None:
    """Byg en detektor af `billing_periods.words` — ét sted for perioderne.

    Ordlisten er *målt* (se `_note` i katalogen), så porten skal ikke have sin
    egen: et ord der står i katalogen, men som porten ikke genkender, ville give
    en stille grøn. Derfor bygges regexp'en her af katalogens egne strenge, og
    selvtesten dømmer at hvert af dem kan findes igen.

    Venstre- og højregrænse: et ord skal stå som sit eget token. `$19/år` er
    derfor gyldigt (ordet begynder med `/`) mens `engangskøb` ikke er det — det er
    et substantiv, ikke en prisperiode, og en knap der skriver det skal have den
    rigtige periode skrevet ud.
    """
    words = catalog.get("billing_periods", {}).get("words") or {}
    if not words:
        return None
    tokens: list[tuple[str, str]] = []
    for klass, entries in words.items():
        for word in entries:
            tokens.append((word, klass))
    if not tokens:
        return None
    # Længste først: skrives «pr. år» og «år» senere ind i katalogen, skal
    # den længste skrivning vinde, ellers ville klassen høre til det korte ord.
    tokens.sort(key=lambda pair: len(pair[0]), reverse=True)
    parts, owner = [], {}
    for word, klass in tokens:
        # Ordet må ikke optræde som en del af et længere ord. `/(?=\w)` ville
        # slå «/år» ihjel, fordi `$` er et ordtegn — så en ord der selv starter
        # med `/` får ingen venstregrænse.
        left = "" if word.startswith("/") else r"(?<!\w)"
        parts.append(f"{left}{re.escape(word)}(?!\w)")
        owner[word] = klass
    return re.compile("|".join(parts), re.I), owner


def period_words(text: str, detector) -> list[tuple[str, str]]:
    """`(ord, klasse)` for hver periode skrevet i `text`."""
    if detector is None:
        return []
    match, owner = detector
    return [(m.group(0).lower(), owner.get(m.group(0).lower(), "?"))
            for m in match.finditer(text)]


def check_buttons(site: Path, prices: dict[str, dict],
                  detector=None) -> list[dict]:
    findings: list[dict] = []
    base = ROOT if site is SITE else site
    for page in sorted(site.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        rel = page.relative_to(base).as_posix()
        for match in ANCHOR.finditer(text):
            href = match.group(1)
            if not BUY_LINK.match(href):
                continue  # donationer er ikke vores priser at dømme
            label = plain(match.group(2))
            found = amounts(label)
            where = f"{rel}: «{label}»"
            offer = prices.get(href)
            if offer is None:
                findings.append({
                    "kind": "ukendt betalingslink", "where": where,
                    "detail": f"{href} står ikke i stripe_catalog.json."})
                continue
            expected = offer["price"]
            price_text = label
            if not found:
                # Beløbet må stå i et pristag i samme `.pt-foot`. Den nærmeste
                # *forudgående* `.pt-foot` — ikke alle i dokumentet: en regex der
                # læser hele sideforsiden tog alle syv priser på /paid-templates,
                # så hver knap blev dømt mod de andre produkter.
                opens = list(PT_FOOT.finditer(text, 0, match.start()))
                foot = text[opens[-1].end():match.start()] if opens else ""
                tags = PRICE_TAG.findall(foot)
                found = [a for tag in tags for a in amounts(plain(tag))]
                price_text = label + " " + plain(" ".join(tags))
                if not found:
                    findings.append({
                        "kind": "købsknap uden pris", "where": where,
                        "detail": (f"Knappen sælger {offer['name']} "
                                   f"({expected} USD) men nævner intet beløb — "
                                   "hverken i knappens tekst eller i en pt-price "
                                   "i samme .pt-foot.")})
                    continue
            for value, cur in found:
                if expected is None or value != float(expected):
                    findings.append({
                        "kind": "forkert pris", "where": where,
                        "detail": (f"Knappen sælger {offer['name']} via linket "
                                   f"til {offer['variant']}, og kataloget siger "
                                   f"{expected} USD — men knappen siger "
                                   f"{value:g} {cur}.")})

            # Dom 4: perioden. Den søges i knappens tekst *og* i det pristag,
            # beløbet kom fra, fordi en periode må stå begge steder — men den
            # skal stå et af stederne.
            allowed = offer.get("periods")
            said = period_words(price_text, detector)
            if allowed is None:
                findings.append({
                    "kind": "produkt uden periode i katalogen", "where": where,
                    "detail": (f"{offer['product']} har ingen `periods` i "
                               "stripe_catalog.json, så perioden ved prisen kan "
                               "ikke dømmes mod sandheden.")})
                continue
            for word, klass in said:
                if klass not in allowed:
                    findings.append({
                        "kind": "periode modsiger katalogen", "where": where,
                        "detail": (f"Knappen sælger {offer['name']} via linket "
                                   f"til {offer['variant']}, som er "
                                   f"{'/'.join(allowed)} — men den skriver «{word}» "
                                   f"ved prisen.")})
            if not said:
                findings.append({
                    "kind": "købsknap uden periode", "where": where,
                    "detail": (f"Knappen sælger {offer['name']} for {expected} USD "
                               f"({offer['variant']}, {'/'.join(allowed)}) men siger "
                               "det ikke — hverken i knappens tekst eller i det "
                               "pristag beløbet står i. Katalogen har både et "
                               "19-USD-årsabonnement (Clean Copy Pro) og et "
                               "19-USD-engangskøb (DeskUptime Pro), så beløbet "
                               "alene siger ikke hvad man får.")})
    return findings


def check_links(catalog: dict, prices: dict[str, dict]) -> list[dict]:
    """Dom 3: katalogens link skal være det, nøglen peger på, andre steder."""
    findings: list[dict] = []

    # Kontrakten: læs linket *pr. række*, ikke «findes et sted i dokumentet».
    path = ROOT / catalog.get("contract", "docs/stripe-kontrakt.md")
    if not path.is_file():
        findings.append({"kind": "kontrakten mangler", "where": path.name,
                         "detail": "Fandt ikke kontraktdokumentet."})
    else:
        # {product_key: [links på de rækker der nævner nøglen]}
        row_links: dict[str, list[str]] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            key = re.search(r"`([a-z0-9-]+)`", line)
            link = re.search(r"https://buy\.stripe\.com/[A-Za-z0-9]+", line)
            if key and link:
                row_links.setdefault(key.group(1), []).append(link.group(0))

        for key, product in sorted(catalog["products"].items()):
            want = {l for l, o in prices.items() if o["product"] == key}
            rows = row_links.get(key)
            if rows is None:
                continue  # nøglen står ikke i tabellen; det dømmer check_stripe_ctas
            if set(rows) != want:
                findings.append({
                    "kind": "betalingslink peger på et andet produkt",
                    "where": f"{path.name}: `{key}`",
                    "detail": (f"Katalogen siger {key} sælger via "
                               f"{', '.join(sorted(want))}, men rækken/rækkerne "
                               f"for `{key}` i kontrakten peger på "
                               f"{', '.join(sorted(set(rows)))}.")})

    # Workerens `link:` pr. nøgle skal være katalogens — den afgør hvad
    # kvitteringen og mailen sender køberen videre til.
    if WORKER.is_file():
        block = re.search(r"const STRIPE_PRODUCTS = \{(.*?)\n\};",
                          WORKER.read_text(encoding="utf-8"), re.S)
        if block:
            entries = dict(re.findall(
                r"^\s*'([a-z0-9-]+)':\s*\{([^\n]*)$", block.group(1), re.M))
            for key, entry in sorted(entries.items()):
                worker_link = re.search(r"link:\s*'([^']+)'", entry)
                if not worker_link:
                    continue
                want = catalog["products"].get(key, {}).get("payment_link")
                if want and worker_link.group(1) != want:
                    findings.append({
                        "kind": "workerens link afviger fra kataloget",
                        "where": f"site/_worker.js: {key}",
                        "detail": (f"Katalogen siger {want}, workeren sender "
                                   f"køberen til {worker_link.group(1)}.")})
    return findings


MUTATIONER = [
    # (navn, fil, gammel tekst, ny tekst)
    ("gammel aarspris paa et engangskob",
     "site/clean-copy.html",
     "Buy Clean Copy Pro — $19/year", "Buy Clean Copy Pro — $14/year"),
    ("pris der passer til et andet produkt",
     "site/paid-templates.html",
     '<p class="pt-price">$59 once</p>', '<p class="pt-price">$149 once</p>'),
    ("ekstra belob ved siden af det rigtige",
     "site/clean-copy.html",
     "Buy Clean Copy Pro — $19/year",
     "Buy Clean Copy Pro — $19/year ($39 lifetime)"),
    ("pris fjernet fra knappen",
     "site/deskuptime/index.html",
     "Buy DeskUptime Pro — 19 USD once", "Buy DeskUptime Pro"),
    # Bemærk: porten dømmer *beløbet* og perioden. Mutations der kun ændrer
    # beløbet fanger dom 1; perioden har sine egne, se dom 4 i docstringen.
    ("belob der passer til et andet produkt i samme fod",
     "site/paid-templates.html",
     '<p class="pt-price">$29 once</p>', '<p class="pt-price">$39 once</p>'),
    ("lifetime-pris paa abonnementslinket",
     "site/clean-copy.html",
     "Buy Clean Copy Pro — $19/year", "Buy Clean Copy Pro — $39/year"),
    # Dom 4. `/year` på et engangskøb er præcis den fejl, dommen er skrevet til:
    # samme form som `$144/year` om UptimeRobot i opgave 33.
    ("aarstal paa et engangskob",
     "site/deskuptime/index.html",
     "Buy DeskUptime Pro — 19 USD once",
     "Buy DeskUptime Pro — 19 USD/year"),
    ("engangskob skrevet som et aarsabonnement",
     "site/clean-copy.html",
     "Buy Clean Copy Pro — $19/year", "Buy Clean Copy Pro — $19 once"),
    ("perioden fjernet fra knappen",
     "site/blog/desktop-website-monitor-cli.html",
     "Buy DeskUptime Pro for $19 once", "Buy DeskUptime Pro for $19"),
    ("engang skrevet som et substantiv uden periode",
     "site/deskuptime/index.html",
     "Buy DeskUptime Pro — 19 USD once", "Buy DeskUptime Pro — 19 USD engangskøb"),
    ("perioden fjernet fra et pristag",
     "site/paid-templates.html",
     '<p class="pt-price">$59 once</p>', '<p class="pt-price">$59</p>'),
]


def self_test() -> int:
    import copy
    import shutil
    import tempfile

    checks = failures = 0

    def ok(cond: bool, label: str) -> None:
        nonlocal checks, failures
        checks += 1
        if not cond:
            failures += 1
            print(f"  FEJL  {label}")
        else:
            print(f"  ok    {label}")

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    prices = catalog_prices(catalog)
    detector = period_detector(catalog)

    baseline = check_buttons(SITE, prices, detector)
    ok(not baseline, f"knapperne er grønne ({len(baseline)} fund)")
    link_findings = check_links(catalog, prices)
    ok(not link_findings, f"linkene er grønne ({len(link_findings)} fund)")

    # Dom 4s egen forudsætning: detektoren skal kunne finde hvert ord katalogen
    # tillader. Ellers ville et nyt ord i `billing_periods.words` give en stille
    # grøn — præcis den fejlform dommen er skrevet imod.
    words = catalog["billing_periods"]["words"]
    for klass, entries in sorted(words.items()):
        for word in entries:
            found = period_words(f"Køb noget — 19 USD {word}", detector)
            ok(found == [(word, klass)],
               f"ordet {word!r} i klassen {klass} genkendes ({found})")

    for name, rel, old, new in MUTATIONER:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "site"
            shutil.copytree(SITE, work)
            target = work / Path(rel).relative_to("site")
            body = target.read_text(encoding="utf-8")
            if old not in body:
                ok(False, f"mutation {name!r}: mønsteret findes ikke mere")
                continue
            target.write_text(body.replace(old, new, 1), encoding="utf-8")
            found = check_buttons(work, prices, detector)
        ok(bool(found), f"mutation {name!r} fanges ({len(found)} fund)")

    # To produkter der bytter link: katalogen skal dømme det, fordi kontrakten
    # og workeren ikke gør. Det er den dom, opgaven bad om.
    for left, right in (("eucomply-dpa", "eucomply-nda-clauses"),
                        ("clean-copy-pro", "deskuptime-pro")):
        broken = copy.deepcopy(catalog)
        a = broken["products"][left]["payment_link"]
        b = broken["products"][right]["payment_link"]
        broken["products"][left]["payment_link"] = b
        broken["products"][right]["payment_link"] = a
        found = check_links(broken, catalog_prices(broken))
        ok(bool(found), f"byttet link {left}/{right} fanges ({len(found)} fund)")

    # Kildens egen grundlag: hvert købslink skal have en pris at dømme mod.
    links = [l for l in prices if BUY_LINK.match(l)]
    ok(len(links) == 15, f"15 købslinks i katalogen (har {len(links)})")
    ok(all(prices[l]["price"] for l in links),
       "hvert købslink har en price_usd")
    ok(sum(1 for o in prices.values() if o["variant"] == "lifetime") == 3,
       "tre lifetime-varianter")

    # Dom 4 mod katalogen selv: et produkt uden `periods` kan ikke dømmes, og
    # en forkert `periods` dømmer den røde side grøn. Begge skal være fund.
    blind = copy.deepcopy(catalog)
    del blind["billing_periods"]["products"]["clean-copy-pro"]
    found = check_buttons(SITE, catalog_prices(blind), period_detector(blind))
    ok([f for f in found if f["kind"] == "produkt uden periode i katalogen"],
       "produkt uden `periods` er et fund")

    swapped = copy.deepcopy(catalog)
    swapped["billing_periods"]["products"]["clean-copy-pro"] = ["one_time"]
    found = check_buttons(SITE, catalog_prices(swapped),
                          period_detector(swapped))
    mismatched = [f for f in found if f["kind"] == "periode modsiger katalogen"]
    ok(mismatched, f"forkert `periods` i katalogen dømmer siderne røde "
                   f"({len(mismatched)} fund)")

    print(f"selvtest: {checks - failures}/{checks} kontroller")
    return 0 if failures == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    prices = catalog_prices(catalog)
    findings = (check_buttons(SITE, prices, period_detector(catalog))
                + check_links(catalog, prices))
    if args.json:
        print(json.dumps({"findings": findings}, ensure_ascii=False, indent=2))
    else:
        for f in findings:
            print(f"{f['where']} [{f['kind']}]: {f['detail']}")
        pages = len(list(SITE.rglob("*.html")))
        print(f"{pages} sider, {len(prices)} betalingslinks, {len(findings)} fund")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
