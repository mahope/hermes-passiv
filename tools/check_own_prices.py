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

Tre domme:

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
    """`{payment_link: {product, variant, price, name}}` for hvert købslink."""
    out: dict[str, dict] = {}
    for key, product in catalog["products"].items():
        link = product.get("payment_link")
        if isinstance(link, str):
            out[link] = {"product": key, "variant": "abonnement"
                         if product.get("subscription") else "engang",
                         "price": product.get("price_usd"),
                         "name": product.get("name", key)}
        life = product.get("lifetime") or {}
        if isinstance(life.get("payment_link"), str):
            out[life["payment_link"]] = {
                "product": key, "variant": "lifetime",
                "price": life.get("price_usd"),
                "name": f"{product.get('name', key)} Lifetime"}
    return out


def check_buttons(site: Path, prices: dict[str, dict]) -> list[dict]:
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
            if not found:
                # Beløbet må stå i et pristag i samme `.pt-foot`. Den nærmeste
                # *forudgående* `.pt-foot` — ikke alle i dokumentet: en regex der
                # læser hele sideforsiden tog alle syv priser på /paid-templates,
                # så hver knapp blev dømt mod de andre produkter.
                opens = list(PT_FOOT.finditer(text, 0, match.start()))
                foot = text[opens[-1].end():match.start()] if opens else ""
                found = [a for tag in PRICE_TAG.findall(foot)
                         for a in amounts(plain(tag))]
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
     '<p class="pt-price">$59</p>', '<p class="pt-price">$149</p>'),
    ("ekstra belob ved siden af det rigtige",
     "site/clean-copy.html",
     "Buy Clean Copy Pro — $19/year",
     "Buy Clean Copy Pro — $19/year ($39 lifetime)"),
    ("pris fjernet fra knappen",
     "site/deskuptime/index.html",
     "Buy DeskUptime Pro — 19 USD", "Buy DeskUptime Pro"),
    # Bemærk: porten dømmer *beløbet*, ikke periode-ordet. «19 USD/year» om et
    # engangskøb er en reel påstand uden dom, men den kræver en ordliste for to
    # sprog (år/year/annuel, engang/once/one-time, lifetime), og de 84 knapper
    # skal måles før den skrives — ellers bliver den en gammel `$144/year`
    # med en ny regexp. Det er en opgave, ikke en mutation her.
    ("belob der passer til et andet produkt i samme fod",
     "site/paid-templates.html",
     '<p class="pt-price">$29</p>', '<p class="pt-price">$39</p>'),
    ("lifetime-pris paa abonnementslinket",
     "site/clean-copy.html",
     "Buy Clean Copy Pro — $19/year", "Buy Clean Copy Pro — $39/year"),
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

    baseline = check_buttons(SITE, prices)
    ok(not baseline, f"knapperne er grønne ({len(baseline)} fund)")
    link_findings = check_links(catalog, prices)
    ok(not link_findings, f"linkene er grønne ({len(link_findings)} fund)")

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
            found = check_buttons(work, prices)
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
    findings = check_buttons(SITE, prices) + check_links(catalog, prices)
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
