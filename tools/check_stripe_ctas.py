#!/usr/bin/env python3
"""Gate for købsrejsen: kun tilladte Stripe-links, én CTA pr. tilbud, ingen falske priser.

Opgaverne er:

1. `tools/stripe_catalog.json` er den eneste maskinlæsbare allowlist, og den
   skal være identisk med `docs/stripe-kontrakt.md` og med produkterne i
   `site/_worker.js`.
2. Hvert `buy.stripe.com`/`donate.stripe.com`-link i source og i shippede
   klienter skal stå i allowlisten.
3. Inventoret af synlige Pro-tilbud (`offers`) skal være fuldt: ingen side med
   en købsknap må stå udenfor, ingen inventeret side må mangle, og hver side
   skal have præcis én synlig CTA med det rette link og kun dokumenterede priser.
4. Ingen side må love et køb der ikke findes ("coming soon", "når butikken
   åbner", "paid checkout is not wired up").
5. Et download-produkt må kun sælges, når dets filer faktisk kan leveres.
   `tools/paid_content.json` er den eneste kilde til det (`kv_verified`), og
   et produkt uden `kv_verified: true` må ikke have sit betalingslink nogen
   sted i `site/`. Modsat retning tæller også som fejl: et leverbart produkt
   uden købsside ville blive solgt helt uden.

    python3 tools/check_stripe_ctas.py           # gate
    python3 tools/check_stripe_ctas.py --report  # inventaret, uden at fejle
    python3 tools/check_stripe_ctas.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "tools/stripe_catalog.json"
CONTRACT = ROOT / "docs/stripe-kontrakt.md"
PAID_CONTENT = ROOT / "tools/paid_content.json"
WORKER = ROOT / "site/_worker.js"

KNOWN_DOMAINS = ("cleancopy.tools", "deskuptime.com", "bugbottle.dev", "mahope.tools")

# Kundeportalen har sti-segmenter (billing.stripe.com/p/login/…), betalingslinks ikke.
LINK_PATTERN = re.compile(r"https://(?:buy|donate|billing)\.stripe\.com/[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*")
PRICE_TOKEN = re.compile(r"\$\s?\d[\d.]*")
PRODUCT_KEY = re.compile(r"^[a-z0-9-]+$")

# Filer der scanst for links: hele site-kilden plus de shippede licensklienter.
SCAN_ROOTS = (
    "site",
    "page-profile",
    "obsidian-plugin",
    "extension-clean-copy",
    "extension-clean-copy-firefox",
    "extension-clean-copy-vscode",
)
SCAN_FILES = ("main.js", "core.js")
SKIP_DIRS = {"__pycache__", ".wrangler"}

HIDDEN_TAGS = {"head", "script", "style", "template", "noscript"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
             "meta", "param", "source", "track", "wbr"}

FORBIDDEN_CLAIMS = (
    "pro is coming",
    "coming soon",
    "available soon",
    "available when store launches",
    "when store launches",
    "kommer når butikken åbner",
    "kommer når butikken åbner.",
    "paid checkout is not wired up",
    "ikke er koblet en betalt checkout",
    "there are no recurring charges",
)

REQUIRED_PRODUCT_KEYS = (
    "clean-copy-pro",
    "deskuptime-pro",
    "transmute-desktop",
    "eucomply-pro",
    "page-profile-pro",
    "eucomply-dpa",
    "eucomply-nis2-clauses",
    "eucomply-nda-clauses",
    "eucomply-eaa-statement",
    "eucomply-report-kit",
    "eucomply-template-bundle",
    "eu-compliance-ebook-bundle",
    "support-mahope-oss",
)

REQUIRED_KINDS = {
    "clean-copy-pro": "license",
    "deskuptime-pro": "license",
    "transmute-desktop": "license",
    "eucomply-pro": "license",
    "page-profile-pro": "license",
    "eucomply-dpa": "download",
    "eucomply-nis2-clauses": "download",
    "eucomply-nda-clauses": "download",
    "eucomply-eaa-statement": "download",
    "eucomply-report-kit": "download",
    "eucomply-template-bundle": "download",
    "eu-compliance-ebook-bundle": "download",
    "support-mahope-oss": "donation",
}


class Page(HTMLParser):
    """Synlig tekst, synlige links og alle links — også dem i JSON-LD."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden: dict[str, int] = {}
        self.visible_parts: list[str] = []
        self.all_links: list[str] = []
        self.in_json_ld = False
        self.current_href: str | None = None
        self.current_anchor_parts: list[str] = []

    def _is_hidden(self) -> bool:
        return any(self.hidden.values())

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}
        href = attributes.get("href", "")
        if href:
            self.all_links.append(href)
            self.current_href = href
            self.current_anchor_parts = []
        style = attributes.get("style", "")
        hidden = (
            tag in HIDDEN_TAGS
            or "hidden" in attributes
            or attributes.get("aria-hidden", "").casefold() == "true"
            or re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", style, re.I) is not None
        )
        if tag == "script" and attributes.get("type", "").casefold() == "application/ld+json":
            self.in_json_ld = True
        if hidden and tag not in VOID_TAGS:
            self.hidden[tag] = self.hidden.get(tag, 0) + 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_json_ld:
            self.in_json_ld = False
        if tag in self.hidden and self.hidden[tag] > 0:
            self.hidden[tag] -= 1
        if tag == "a":
            self.current_href = None
            self.current_anchor_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_json_ld or self._is_hidden():
            return
        self.visible_parts.append(data)
        if self.current_href is not None:
            self.current_anchor_parts.append(data)

    @property
    def text(self) -> str:
        return normalize(" ".join(self.visible_parts))


class AnchorCollector(HTMLParser):
    """Ankre med synlig tekst, i dokumentrækkefølge."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden: dict[str, int] = {}
        self.anchors: list[tuple[str, str]] = []
        self.open: list[tuple[str, list[str]]] = []
        self.in_json_ld = False

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}
        if tag == "script" and attributes.get("type", "").casefold() == "application/ld+json":
            self.in_json_ld = True
        style = attributes.get("style", "")
        hidden = (
            tag in HIDDEN_TAGS
            or "hidden" in attributes
            or attributes.get("aria-hidden", "").casefold() == "true"
            or re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", style, re.I) is not None
        )
        if hidden and tag not in VOID_TAGS:
            self.hidden[tag] = self.hidden.get(tag, 0) + 1
        if tag == "a" and not self._hidden():
            self.open.append((attributes.get("href", ""), []))

    def _hidden(self) -> bool:
        return self.in_json_ld or any(self.hidden.values())

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_json_ld:
            self.in_json_ld = False
        if tag == "a" and self.open:
            href, parts = self.open.pop()
            text = normalize(" ".join(parts))
            if text:
                self.anchors.append((href, text))
        if tag in self.hidden and self.hidden[tag] > 0:
            self.hidden[tag] -= 1

    def handle_data(self, data: str) -> None:
        if self._hidden():
            return
        for _, parts in self.open:
            parts.append(data)


def normalize(text: str) -> str:
    return " ".join(text.split())


# ── Hvad en Pro-side skal vise om den gratis udgave ──────────────────────
#
# Missionens punkt 4: "hver Pro-side klart viser, hvad gratis og betalt
# giver". Indtil nu var det kun en hensigtserklæring i katalogens `why`, og
# ingen port læste den — så /clean-copy-tool, siden hvor Clean Copy Pro
# faktisk købes og aktiveres, ikke nævnte den gratis udgave overhovedet.
# Ordet "free" stod kun i "More free tools"-linket nederst på siden.
#
# Både en sætning og en tabel tæller, fordi de sunde sider bruger begge
# former: DeskUptime og Page Profile har en "Free and Pro"-tabel, mens
# /clean-copy og /activate har en sætning. En port der krævede den ene
# form ville gøre de andre sider røde uden grund.
FREE_TIER_PHRASES = re.compile(
    r"\bfree (?:version|tier|tool|cli|web|edition|plan)\b"
    r"|\bstays free\b"
    r"|\bnot a trial\b"
    r"|\bis free\b"
    r"|\bgratis (?:version|udgave|værktøj|web|plan|cli)\b"
    r"|\ber gratis\b"
    r"|\bgratis og\b"
    r"|\bgratis cli\b"
    r"|\bingen prøveversion\b"
)
FREE_LABEL = re.compile(r"\bfree\b|\bgratis\b", re.I)
PAID_LABEL = re.compile(r"\bpro\b|\bpaid\b|\bpremium\b|\$|\busd\b|\bkr\.?|\beur\b|\bdkk\b", re.I)

# `PRICE_TOKEN` kræver et `$`, og det er ikke nok. `/clean-copy-tool` skriver
# sin Pro-pris som "19 USD per year" — hele den families vigtigste købsside
# står altså med en pris, en `$`-baseret regel ikke kan se. Derfor tæller
# valutaord og symboler begge, ellers er porten grøn på præcis den
# forsvundne købsmulighed den er skrevet til at fange.
CURRENCY_AMOUNT = re.compile(
    r"[$€£]\s?\d[\d.]*"
    r"|\b\d[\d.,]*\s?(?:usd|eur|dkk|kr\.?)\b",
    re.I,
)


class VisibleBlocks(HTMLParser):
    """Synlig tekst plus overskrifterne i de tabeller der er synlige.

    En lukket `<details>` er ikke synlig uden et klik, så dens indhold tæller
    ikke. Det er den tunge del: en gratis- forklaring gemt i en lukket FAQ
    er netop den måde denne fejlform kommer tilbage på.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden: dict[str, int] = {}
        self.parts: list[str] = []
        self.in_json_ld = False
        self.table_headers: list[list[str]] = []
        self.comparisons: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._in_header = False

    def _is_hidden(self) -> bool:
        return any(self.hidden.values())

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}
        style = attributes.get("style", "")
        hidden = (
            tag in HIDDEN_TAGS
            or "hidden" in attributes
            or attributes.get("aria-hidden", "").casefold() == "true"
            or re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", style, re.I) is not None
            # En <details> uden `open` er lukket. `hidden` i attributerne
            # dækker ikke dette, og det er den vigtigste skjulested.
            or (tag == "details" and "open" not in attributes)
        )
        if tag == "script" and attributes.get("type", "").casefold() == "application/ld+json":
            self.in_json_ld = True
        if hidden and tag not in VOID_TAGS:
            self.hidden[tag] = self.hidden.get(tag, 0) + 1
        if self._is_hidden():
            return
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
            if tag == "th":
                self._in_header = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_json_ld:
            self.in_json_ld = False
        if tag in ("td", "th"):
            if self._cell is not None and self._row is not None:
                self._row.append(normalize(" ".join(self._cell)))
            self._cell = None
            if tag == "th":
                self._in_header = False
        elif tag == "tr" and self._row is not None and self._table is not None:
            self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            if self._table:
                self.table_headers.append(self._table[0])
                self.comparisons.append(self._table)
            self._table = None
        if tag in self.hidden and self.hidden[tag] > 0:
            self.hidden[tag] -= 1

    def handle_data(self, data: str) -> None:
        if self.in_json_ld or self._is_hidden():
            return
        self.parts.append(data)
        if self._cell is not None:
            self._cell.append(data)

    @property
    def text(self) -> str:
        return normalize(" ".join(self.parts))


def free_pro_tables(text: str) -> list[tuple[list[list[str]], int]]:
    """Synlige gratis/Pro-sammenligningstabeller, med Pro-kolonnens index.

    Kun synlige: en lukket `<details>`, `<head>`, JSON-LD eller en `style`
    med `display:none` tæller ikke, fordi det er præcis de steder en
    sammenligning bliver usynlig uden at forsvinde fra koden.

    Pro-kolonnen er den første overskrift der ligner en betalt udgave, men
    ikke ligner den gratis. `Feature` og `Free` kan ikke være den, og
    `Pro (not released)` kan godt være det — en kolonne der siger "Pro,
    ikke udgivet endnu" er stadig den kolonne, der lover noget.
    """
    blocks = VisibleBlocks()
    blocks.feed(text)
    blocks.close()
    tables: list[tuple[list[list[str]], int]] = []
    for rows in blocks.comparisons:
        header = rows[0]
        if not any(FREE_LABEL.search(cell) for cell in header):
            continue
        paid_column = next(
            (index for index, cell in enumerate(header)
             if PAID_LABEL.search(cell) and not FREE_LABEL.search(cell)),
            None,
        )
        if paid_column is not None:
            tables.append((rows, paid_column))
    return tables


def check_comparisons(catalog: dict, pages: list[tuple[str, str]]) -> list[str]:
    """En gratis/Pro-tabel skal vise forskellen, og den skal kun prise noget
    der kan købes.

    To regler, begge på *alle* sider og ikke kun på dem, der sælger et
    katalogprodukt — det var præcis det hul, der lod en helt ukendt
    "EAA Scanner Pro — $19/år" stå på en publiceret side i ugevisninger:

    1. **Tomme celler.** En sammenligningstabel med tomme celler er
       værre end ingen tabel: den lader som om den viser forskellen, og
       en køber kan ikke se den. Oprindelsen var ikke sløshed, men en
       oprydning (`2c9909d`) der fjernede `✓`-ikoner: de tre celler der
       kun indeholdt et `✓`, blev tomme, da symbolet forsvandt.
    2. **En pris uden en købsknap.** En Pro-kolonne der viser en pris, er
       et løfte om at pengene kan bruges. Hvis siden ingen steder har et
       betalingslink fra katalogen, er prisen ubetalingsbar — og den er
       dobbelt sådan, fordi produktet ikke findes i katalogen overhovedet.
       Samme fejl som en død knap, bare uden knappen.
    """
    links = catalog_links(catalog)
    problems: list[str] = []
    for relative, text in pages:
        has_payment_link = any(href in links for href, _ in parse_page(text)[1])
        for rows, paid_column in free_pro_tables(text):
            for index, row in enumerate(rows[1:], start=2):
                if len(row) < paid_column + 1:
                    continue
                blanks = [position for position, cell in enumerate(row[1:], start=2)
                          if not cell.strip()]
                if blanks:
                    problems.append(
                        f"{relative}: gratis/Pro-tabellen har tomme celler i række {index} "
                        f"({row[0][:40]!r}, kolonne {blanks[0]}) — den viser ikke, hvad niveauet giver"
                    )
                price = row[paid_column]
                if CURRENCY_AMOUNT.search(price) and not has_payment_link:
                    problems.append(
                        f"{relative}: Pro-kolonnen viser prisen {normalize(price)[:40]!r} i "
                        f"række {index} ({row[0][:40]!r}), men siden har ingen købsknap — "
                        f"prisen kan ikke betales, og produktet findes ikke i katalogen"
                    )
    return problems


def check_free_tier(catalog: dict, pages: list[tuple[str, str]]) -> list[str]:
    """En side der sælger en licens, skal vise hvad den gratis udgave giver.

    Kun produkter med `kind: license`. En donation og et download-produkt har
    per definition ingen gratis udgave at vise, så de skal ikke fejle på en
    regel de ikke kan opfylde.

    Sætningen skal stå i læsbar tekst: hverken i `<head>`, i JSON-LD, i en
    attribut eller i en lukket `<details>`. En løsning på at skjule den
    gratis-fordelen i en collapsed FAQ er derfor umulig.
    """
    products = catalog["products"]
    offers = catalog.get("offers")
    if not isinstance(offers, list):
        return []
    by_path = dict(pages)
    problems: list[str] = []
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        product = products.get(offer.get("product"))
        if not isinstance(product, dict) or product.get("kind") != "license":
            continue
        relative = offer.get("path")
        text = by_path.get(relative)
        if text is None:
            continue  # check_offers melder en manglende fil.
        blocks = VisibleBlocks()
        blocks.feed(text)
        blocks.close()
        visible = blocks.text
        comparisons = [rows for rows, _ in free_pro_tables(text)]
        if FREE_TIER_PHRASES.search(visible) or comparisons:
            continue
        problems.append(
            f"{relative}: sælger {offer.get('product')} men siger aldrig, hvad den gratis "
            f"udgave giver — hverken i læsbar tekst eller i en synlig gratis/Pro-tabel"
        )
    return problems


def parse_page(text: str) -> tuple[str, list[tuple[str, str]]]:
    visible = Page()
    visible.feed(text)
    visible.close()
    anchors = AnchorCollector()
    anchors.feed(text)
    anchors.close()
    return visible.text, anchors.anchors


def load_catalog(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def catalog_links(catalog: dict) -> set[str]:
    links = {product["payment_link"] for product in catalog["products"].values()}
    portal = catalog.get("billing_portal")
    if isinstance(portal, str):
        links.add(portal)
    return links


def scan_files() -> list[Path]:
    files: list[Path] = []
    for name in SCAN_ROOTS:
        base = ROOT / name
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or SKIP_DIRS & set(path.parts):
                continue
            files.append(path)
    files.extend(ROOT / name for name in SCAN_FILES if (ROOT / name).is_file())
    return files


def check_catalog(catalog: dict) -> list[str]:
    problems: list[str] = []
    products = catalog.get("products")
    if not isinstance(products, dict) or not products:
        return ["tools/stripe_catalog.json: products skal være et ikke-tomt objekt"]
    links: dict[str, str] = {}
    for key, product in products.items():
        if not PRODUCT_KEY.match(key):
            problems.append(f"catalog: ugyldig product_key {key!r}")
        if not isinstance(product, dict):
            problems.append(f"catalog: {key} er ikke et objekt")
            continue
        for field in ("name", "kind", "price", "price_note", "payment_link"):
            if not isinstance(product.get(field), str) or not product[field]:
                problems.append(f"catalog: {key} mangler {field}")
        if not isinstance(product.get("payment_link"), str):
            continue
        if not product["payment_link"].startswith(("https://buy.stripe.com/", "https://donate.stripe.com/")):
            problems.append(f"catalog: {key} har et link uden for Stripe Payment Links")
        previous = links.setdefault(product["payment_link"], key)
        if previous != key:
            problems.append(f"catalog: link {product['payment_link']} bruges af både {previous} og {key}")
    for key in REQUIRED_PRODUCT_KEYS:
        if key not in products:
            problems.append(f"catalog: kontraktproduktet {key} mangler")
        elif products[key].get("kind") != REQUIRED_KINDS[key]:
            problems.append(f"catalog: {key} har kind {products[key].get('kind')!r}, forventet {REQUIRED_KINDS[key]!r}")
    return problems


def check_contract_doc(catalog: dict) -> list[str]:
    path = ROOT / catalog.get("contract", "docs/stripe-kontrakt.md")
    if not path.is_file():
        return [f"{catalog.get('contract')}: kontraktdokumentet mangler"]
    text = path.read_text(encoding="utf-8")
    problems: list[str] = []
    for key, product in catalog["products"].items():
        if f"`{key}`" not in text:
            problems.append(f"{path.name}: product_key {key} står ikke i tabellen")
        if product["payment_link"] not in text:
            problems.append(f"{path.name}: betalingslink for {key} står ikke i tabellen")
    for extra in LINK_PATTERN.findall(text):
        if extra not in catalog_links(catalog):
            problems.append(f"{path.name}: link {extra} er ikke i allowlisten")
    return problems


def check_worker(catalog: dict) -> list[str]:
    text = WORKER.read_text(encoding="utf-8")
    products = catalog["products"]
    problems: list[str] = []
    block = re.search(r"const STRIPE_PRODUCTS = \{(.*?)\n\};", text, re.S)
    if block is None:
        return ["site/_worker.js: STRIPE_PRODUCTS blev ikke fundet"]
    worker_keys = set(re.findall(r"^\s*'([a-z0-9-]+)':\s*\{", block.group(1), re.M))
    entries = dict(re.findall(r"^\s*'([a-z0-9-]+)':\s*\{([^\n]*)$", block.group(1), re.M))
    for key in sorted(worker_keys - set(products)):
        problems.append(f"site/_worker.js: produktet {key} mangler i allowlisten")
    for key, product in sorted(products.items()):
        if key not in worker_keys:
            problems.append(f"site/_worker.js: allowlisten har {key}, som workeren ikke kender")
            continue
        if key in REQUIRED_PRODUCT_KEYS and product["name"] not in text.split("const STRIPE_PRODUCTS")[1]:
            problems.append(f"site/_worker.js: navnet på {key} afviger fra allowlisten ({product['name']!r})")
    # Kun de årlige produkter må markeres som abonnement, ellers får et engangskøb
    # et kundeportalslink den aldrig kan bruge — eller et abonnement mangler det.
    worker_subscriptions = {key for key, entry in entries.items() if re.search(r"\bsubscription:\s*true\b", entry)}
    catalog_subscriptions = {key for key, product in products.items() if product.get("subscription") is True}
    for key in sorted(worker_subscriptions - catalog_subscriptions):
        problems.append(f"site/_worker.js: {key} er markeret som abonnement, men allowlisten siger engangskøb")
    for key in sorted(catalog_subscriptions - worker_subscriptions):
        problems.append(f"site/_worker.js: {key} er et årligt abonnement i allowlisten, men er ikke markeret som abonnement")
    if catalog_subscriptions and catalog.get("billing_portal") not in text:
        problems.append("site/_worker.js: kundeportalen mangler i workeren, så abonnenter ikke kan opsige selv")
    links_block = re.search(r"const STRIPE_LINKS = \{(.*?)\n  \};", text, re.S)
    if links_block is None:
        problems.append("site/_worker.js: STRIPE_LINKS blev ikke fundet")
        return problems
    for short, link in re.findall(r"(\w+):\s*'(https://buy\.stripe\.com/[A-Za-z0-9]+)'", links_block.group(1)):
        owner = next((key for key, product in products.items() if product["payment_link"] == link), None)
        if owner is None:
            problems.append(f"site/_worker.js: STRIPE_LINKS.{short} er ikke i allowlisten ({link})")
        if link not in text:
            problems.append(f"site/_worker.js: STRIPE_LINKS.{short} mangler i allowlisten")
    return problems


def check_links(catalog: dict) -> list[str]:
    allowed = catalog_links(catalog)
    problems: list[str] = []
    for path in scan_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for link in sorted(set(LINK_PATTERN.findall(text))):
            if link not in allowed:
                problems.append(f"{path.relative_to(ROOT)}: {link} er ikke i allowlisten")
    return problems


def price_tokens(text: str) -> set[str]:
    return {normalize(token) for token in PRICE_TOKEN.findall(text)}


ROUTE_PATTERN = re.compile(r"^/(?:[a-z0-9._~-]+/)*[a-z0-9._~-]*$")


def route_file(domain: str, route: str) -> Path | None:
    """Den byggede fil for en public route, hvis buildet ligger i dist/."""
    if (ROOT / "dist" / domain).is_dir():
        base = ROOT / "dist" / domain / route.strip("/")
        for candidate in (base.with_suffix(".html"), base / "index.html", base):
            if candidate.is_file():
                return candidate
    return None


def check_routes(offers: list[dict], core_pages: object) -> list[str]:
    """Hver købsside skal have sit domæne og sin public route, og de fire
    centrale produktsider skal findes med den CTA de erklærer."""
    problems: list[str] = []
    listed = {(offer.get("path"), offer.get("product")) for offer in offers if isinstance(offer, dict)}
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        domain, route = offer.get("domain"), offer.get("route")
        label = f"{offer.get('path')} ({offer.get('product')})"
        if domain not in KNOWN_DOMAINS:
            problems.append(f"{label}: ukendt domæne {domain!r}")
        if not isinstance(route, str) or not ROUTE_PATTERN.match(route):
            problems.append(f"{label}: ugyldig route {route!r}")
            continue
        if domain in KNOWN_DOMAINS and route_file(domain, route) is None:
            problems.append(f"{label}: {domain}{route} findes ikke i dist/")

    if not isinstance(core_pages, list) or len(core_pages) != 4:
        problems.append("catalog: core_pages skal være præcis fire centrale produktsider")
        return problems
    for page in core_pages:
        if not isinstance(page, dict):
            problems.append("catalog: en central produktside er ikke et objekt")
            continue
        label = f"core_page {page.get('product')!r}"
        if (page.get("path"), page.get("product")) not in listed:
            problems.append(f"{label}: {page.get('path')} sælger ikke {page.get('product')} i inventoriet")
        if not str(page.get("why", "")).strip():
            problems.append(f"{label}: mangler begrundelse")
    return problems


def check_offers(catalog: dict) -> tuple[list[str], list[dict]]:
    products = catalog["products"]
    offers = catalog.get("offers")
    if not isinstance(offers, list):
        return ["tools/stripe_catalog.json: offers skal være en liste"], []
    problems: list[str] = []
    seen: dict[tuple[str, str], int] = {}
    inventory: list[dict] = []

    for offer in offers:
        if not isinstance(offer, dict):
            problems.append("catalog: et offer er ikke et objekt")
            continue
        path = ROOT / offer.get("path", "")
        product = offer.get("product")
        if not path.is_file():
            problems.append(f"catalog: tilbuddet på {offer.get('path')!r} findes ikke")
            continue
        if product not in products:
            problems.append(f"catalog: {offer['path']} bruger ukendt product_key {product!r}")
            continue
        if (offer["path"], product) in seen:
            problems.append(f"catalog: {offer['path']} står to gange for {product}")
        seen[(offer["path"], product)] = seen.get((offer["path"], product), 0) + 1

        visible, anchors = parse_page(path.read_text(encoding="utf-8"))
        link = products[product]["payment_link"]
        ctas = [(href, text) for href, text in anchors if href == link]
        tokens = sorted(price_tokens(visible))
        inventory.append({
            "path": offer["path"],
            "domain": offer.get("domain"),
            "route": offer.get("route"),
            "product": product,
            "price": products[product]["price"],
            "prices_on_page": tokens,
            "cta": [text for _, text in ctas],
            "link": link,
        })
        if len(ctas) != 1:
            problems.append(f"{offer['path']}: {len(ctas)} synlige CTA'er for {product}, forventet præcis 1")
        allowed_tokens = set(offer.get("prices") or [])
        unknown = sorted(set(tokens) - allowed_tokens)
        if unknown:
            problems.append(f"{offer['path']}: udokumenterede priser {unknown} (tilladt: {sorted(allowed_tokens)})")
        for required in offer.get("requires_text", []):
            if normalize(required).casefold() not in visible.casefold():
                problems.append(f"{offer['path']}: mangler påkrævet tekst {required!r}")
        for forbidden in offer.get("forbids_text", []):
            if normalize(forbidden).casefold() in visible.casefold():
                problems.append(f"{offer['path']}: forbudt tekst {forbidden!r}")

    listed = {(offer.get("path"), offer.get("product")) for offer in offers if isinstance(offer, dict)}
    for path in scan_files():
        if path.suffix != ".html":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        relative = str(path.relative_to(ROOT))
        if relative.startswith("dist/"):
            continue
        _, anchors = parse_page(text)
        visible_links = {href for href, _ in anchors}
        for link in sorted(visible_links & set(LINK_PATTERN.findall(text))):
            if link == catalog.get("billing_portal"):
                # Kundeportalen er ikke en købsknap; den har sin egen sidekontrol.
                continue
            owner = next((key for key, product in products.items() if product["payment_link"] == link), None)
            if owner is None:
                problems.append(f"{relative}: synligt link {link} er ikke i allowlisten")
            elif (relative, owner) not in listed:
                problems.append(f"{relative}: synlig købsknap for {owner} mangler i inventoryet")
    return problems, inventory


def check_billing_portal(catalog: dict) -> list[str]:
    """Kundeportalen skal findes præcis de steder, en abonnent kan opsige fra.

    `/thanks` bygger linket ud fra leveringssvaret, så den skal referere
    `billing_portal`; `/support` og `/terms/` linker til den direkte.
    """
    problems: list[str] = []
    portal = catalog.get("billing_portal")
    if not isinstance(portal, str) or not portal.startswith("https://billing.stripe.com/p/login/"):
        return [f"tools/stripe_catalog.json: billing_portal skal være en billing.stripe.com-punktal, fik {portal!r}"]
    pages = catalog.get("portal_pages")
    if not isinstance(pages, list) or not pages:
        return ["tools/stripe_catalog.json: portal_pages skal være en ikke-tom liste"]
    for page in pages:
        path = ROOT / page
        if not path.is_file():
            problems.append(f"tools/stripe_catalog.json: portalsiden {page!r} findes ikke")
            continue
        text = path.read_text(encoding="utf-8")
        if portal not in text and "billing_portal" not in text:
            problems.append(f"{page}: mangler kundeportalen, så abonnenter kan ikke opsige selv")
    for path in scan_files():
        relative = str(path.relative_to(ROOT))
        # Kun sider: workerens brug af portalen er styret af check_worker.
        if path.suffix != ".html" or relative in pages or relative.startswith("dist/"):
            continue
        if portal in path.read_text(encoding="utf-8", errors="ignore"):
            problems.append(f"{relative}: bruger kundeportalen uden at være deklareret portalside")
    return problems


def check_forbidden_claims() -> list[str]:
    problems: list[str] = []
    for path in scan_files():
        if path.suffix != ".html":
            continue
        relative = str(path.relative_to(ROOT))
        if relative.startswith("dist/"):
            continue
        visible, _ = parse_page(path.read_text(encoding="utf-8"))
        lowered = visible.casefold()
        for claim in FORBIDDEN_CLAIMS:
            if claim in lowered:
                problems.append(f"{relative}: forbudt købs-påstand {claim!r}")
    return problems


def source_pages() -> list[tuple[str, str]]:
    """Alle sider i `site/`, som parret (relativ sti, tekst).

    Kun kilden, ikke `dist/`: bygget er gaten's første step og kopierer
    siderne uændret, så en kilde der er ren giver et rent dist.
    """
    pages: list[tuple[str, str]] = []
    for path in scan_files():
        if path.suffix != ".html":
            continue
        relative = str(path.relative_to(ROOT))
        if relative.startswith("dist/"):
            continue
        try:
            pages.append((relative, path.read_text(encoding="utf-8")))
        except (UnicodeDecodeError, OSError):
            continue
    return pages


def check_deliverable(catalog: dict, pages: list[tuple[str, str]], paid: dict | None = None) -> list[str]:
    """Et download-produkt må kun sælges, når filen kan leveres.

    Betalte filer ligger i Cloudflare KV, og `/api/download` svarer 503 når
    nøglen `paidfile:<fil>` mangker. `tools/paid_content.json` er den eneste
    kilde til om den findes. Så længe den ikke gør det, tager et køb penge
    ind og leverer intet — og fordi produkterne sælges gennem statiske Stripe
    Payment Links kan checkout ikke blokeres. Så må siden ikke tilbyde købet.

    Begge retninger er fejl. Uden den modsatte regel ville et produkt, der
    bliver leveringsklart, kunne forblive uden købsside og så aldrig sælges
    igen.
    """
    problems: list[str] = []
    relative_inventory = str(PAID_CONTENT.relative_to(ROOT))
    if paid is None:
        if not PAID_CONTENT.is_file():
            return [f"{relative_inventory}: betalt-indholds-inventaret mangler"]
        paid = json.loads(PAID_CONTENT.read_text(encoding="utf-8"))
    entries = paid.get("products")
    if not isinstance(entries, list):
        return [f"{relative_inventory}: products skal være en liste"]
    inventory = {entry.get("product_key"): entry for entry in entries if isinstance(entry, dict)}
    sold = {offer.get("product") for offer in catalog.get("offers") or [] if isinstance(offer, dict)}

    for key, product in sorted(catalog["products"].items()):
        if product.get("kind") != "download":
            continue
        entry = inventory.get(key)
        if entry is None:
            problems.append(f"catalog: {key} er et download-produkt uden post i {relative_inventory}")
            continue
        if entry.get("kv_verified") is True:
            if key not in sold:
                problems.append(f"catalog: {key} kan leveres, men ingen købsside sælger det")
            continue
        files = ", ".join(entry.get("delivery_files") or []) or "ingen filer"
        for label, text in pages:
            if product["payment_link"] in text:
                problems.append(
                    f"{label}: sælger {key}, men filerne er ikke i KV ({files}) — "
                    f"køberen betaler for et køb der svarer 503 i /api/download. "
                    f"Sæt kv_verified på true i {relative_inventory} når de er uploadet."
                )
    return problems


def run(catalog: dict) -> tuple[list[str], list[dict]]:
    problems = check_catalog(catalog)
    problems += check_contract_doc(catalog)
    problems += check_worker(catalog)
    problems += check_links(catalog)
    offer_problems, inventory = check_offers(catalog)
    problems += offer_problems
    problems += check_routes(catalog.get("offers") or [], catalog.get("core_pages"))
    problems += check_billing_portal(catalog)
    problems += check_forbidden_claims()
    problems += check_deliverable(catalog, source_pages())
    problems += check_free_tier(catalog, source_pages())
    problems += check_comparisons(catalog, source_pages())
    return problems, inventory


def discover_offers(catalog: dict) -> list[dict]:
    """Alle sider med en synlig købsknap, uanset inventaret."""
    products = catalog["products"]
    by_link = {product["payment_link"]: key for key, product in products.items()}
    found: list[dict] = []
    for path in scan_files():
        if path.suffix != ".html" or str(path.relative_to(ROOT)).startswith("dist/"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        visible, anchors = parse_page(text)
        ctas = [(href, label) for href, label in anchors if href in by_link]
        if not ctas:
            continue
        found.append({
            "path": str(path.relative_to(ROOT)),
            "prices_on_page": sorted(price_tokens(visible)),
            "ctas": [{"product": by_link[href], "text": label} for href, label in ctas],
        })
    return found


def self_test() -> int:
    """Beviser at gaten faktisk fanger de fem driftformer."""
    good = load_catalog(CATALOG)
    rogue_link = {**good, "products": {
        **good["products"],
        "clean-copy-pro": {**good["products"]["clean-copy-pro"],
                           "payment_link": "https://buy.stripe.com/ukjendtLink0"},
    }}
    missing_product = {**good, "products": {
        key: value for key, value in good["products"].items() if key != "deskuptime-pro"}}
    shared_link = {**good, "products": {
        **good["products"],
        "eucomply-nda-clauses": {**good["products"]["eucomply-nda-clauses"],
                                 "payment_link": good["products"]["eucomply-eaa-statement"]["payment_link"]},
    }}
    unsatisfiable_offer = {**good, "offers": [{
        "path": "site/books/compliance-bundle.html",
        "product": "eu-compliance-ebook-bundle",
        "prices": ["$29"],
        "requires_text": ["et krav der ikke kan stå på siden"],
    }]}
    uninventoried = {**good, "offers": []}
    # Muterer scenariet en side, der ikke lenger sælger noget, bliver det en
    # stum kontrol: den fejl, den skal fange, kan så ikke opstå. Derfor
    # verificeres her, at mutationen rent faktisk rammer en købsside.
    wrong_domain = {**good, "offers": [
        {**offer, "domain": "example.com"} if offer["path"] == "site/clean-copy.html" else offer
        for offer in good["offers"]]}
    if wrong_domain["offers"] == good["offers"]:
        print("SELFTEST FEJLER: domænescenariet muterer ingen købsside — det er en stum kontrol")
        return 1
    missing_core = {**good, "core_pages": good["core_pages"][:3]}
    rogue_portal = {**good, "billing_portal": "https://billing.stripe.com/p/login/ukjendtPortal0"}
    no_subscriptions = {**good, "products": {
        key: {field: value for field, value in product.items() if field != "subscription"}
        for key, product in good["products"].items()}}

    # 5: et download-produkt uden filer i KV må ikke sælges. Kilden scanneres
    # normalt, så scenarierne sender syntetiske sider ind i stedet for at
    # røre de rigtige filer — ellers ville selftesten selv skrive den fejl,
    # den skal fange.
    report_kit = good["products"]["eucomply-report-kit"]["payment_link"]
    synthetic_sale = [("site/eksempel.html", f'<a href="{report_kit}">Buy</a>')]
    undeliverable = check_deliverable(good, synthetic_sale)
    # Samme side med et produkt, der faktisk kan leveres: må ikke fejle.
    deliverable_page = [("site/eksempel.html", '<a href="https://buy.stripe.com/6oU4gy76PgvgdBIdAXbMQ00">Buy</a>')]
    should_pass = check_deliverable(good, deliverable_page)
    verified = json.loads(PAID_CONTENT.read_text(encoding="utf-8"))
    for entry in verified["products"]:
        if entry["product_key"] == "eucomply-report-kit":
            entry["kv_verified"] = True
    delisted = {**good, "offers": [
        offer for offer in good["offers"] if offer["product"] != "eucomply-report-kit"]}
    forgot_the_page = check_deliverable(delisted, [], verified)

    # 6: en Pro-side skal vise hvad den gratis udgave giver. Scenarierne er
    # syntetiske, så selftesten ikke skriver den fejl ind i de rigtige sider.
    clean_copy_link = good["products"]["clean-copy-pro"]["payment_link"]
    donate_link = good["products"]["support-mahope-oss"]["payment_link"]
    buys_only = f'<html><body><h1>Tool</h1><p>Convert text.</p><a href="{clean_copy_link}">Buy</a></body></html>'
    says_free = (f'<html><body><p>The free version is the complete tool, not a trial.</p>'
                 f'<a href="{clean_copy_link}">Buy</a></body></html>')
    says_free_but_buried = (f'<html><body><details><summary>FAQ</summary>'
                            f'<p>The free version is the complete tool, not a trial.</p></details>'
                            f'<a href="{clean_copy_link}">Buy</a></body></html>')
    empty_table = (f'<html><body><table><tr><th>Feature</th><th>Free</th><th>Pro</th></tr>'
                   f'<tr><td>Batch mode</td><td>—</td><td></td></tr>'
                   f'<tr><td>Price</td><td>free</td><td>$19/year</td></tr></table>'
                   f'<a href="{clean_copy_link}">Buy</a></body></html>')
    donation = f'<html><body><p>Thanks for using the free tools.</p><a href="{donate_link}">Donate</a></body></html>'
    only_offer = [{**offer, "path": "site/eksempel.html"} for offer in good["offers"]
                  if offer["product"] == "clean-copy-pro"]
    free_tier_only = {**good, "offers": only_offer}
    no_free_tier = check_free_tier(free_tier_only, [("site/eksempel.html", buys_only)])
    buried_free_tier = check_free_tier(free_tier_only, [("site/eksempel.html", says_free_but_buried)])
    # Tomme celler hører nu til `check_comparisons`, som læser alle sider og
    # ikke kun katalogens købssider. Scenariet beholder sin købsknap, så det
    # isolerer den ene regel: her skal kun den tomme celle fanges.
    hollow_table = check_comparisons(good, [("site/eksempel.html", empty_table)])
    # Negativ kontrol: siden siger gratis-udgaven, og en donation skal ikke
    # fejle på en regel om gratis-udgaven — den har ikke en.
    should_also_pass = check_free_tier(free_tier_only, [("site/eksempel.html", says_free)])
    donation_only = {**good, "offers": [
        offer for offer in good["offers"] if offer["product"] == "support-mahope-oss"]}
    donation_no_free = check_free_tier(donation_only, [("site/support.html", donation)])
    # Uden denne kontrol er de tre scenarier ovenfor stumme: en syntese der
    # ikke rammer købssiden, ville stå som fanget uden at prøve noget, præcis
    # som fejlen i opgave 30.
    if not only_offer or only_offer == good["offers"]:
        print("SELFTEST FEJLER: gratis-udgave-scenarierne muterer ingen købsside — de er stumme")
        return 1
    if FREE_TIER_PHRASES.search("The free version is the complete tool, not a trial.") is None:
        print("SELFTEST FEJLER: frasen i det positive scenarie matcher ikke portens egen mønster")
        return 1

    # 7: en sammenligningstabel på en side der ikke sælger. Opgave 32 blev
    # meldt "kræver Mads", fordi porten kun læste katalogens købssider — så
    # en helt ukendt "EAA Scanner Pro — $19/år" kunne stå på en publiceret
    # side. Scenarierne er syntetiske, så selftesten ikke skriver fejlen ind i
    # de rigtige sider.
    def table(price: str, free_cell: str = "yes", pro_cell: str = "yes", link: str = "") -> str:
        return (f'<html><body><table><tr><th>Feature</th><th>Free</th>'
                f'<th>Pro (not released)</th></tr>'
                f'<tr><td>Batch scanning</td><td>{free_cell}</td><td>{pro_cell}</td></tr>'
                f'<tr><td>Price</td><td>Free (MIT)</td><td>{price}</td></tr></table>'
                f'{link}</body></html>')

    unbuyable_symbol = check_comparisons(good, [("site/eksempel.html", table("$19/year"))])
    unbuyable_words = check_comparisons(good, [("site/eksempel.html", table("19 USD per year"))])
    hollow_unsold = check_comparisons(
        good, [("site/eksempel.html", table("Not for sale yet", pro_cell=""))])
    # Negativ kontroller: det samme med en købsknap, og det samme uden pris.
    buyable = check_comparisons(
        good, [("site/eksempel.html", table("$19/year", link=f'<a href="{clean_copy_link}">Buy</a>'))])
    priceless = check_comparisons(good, [("site/eksempel.html", table("Not for sale yet"))])
    # Uden denne kontrol er `unbuyable_words` en stum scene: `$`-mønsteret
    # ville have fundet nul priser i "19 USD per year", så scenariet kunne
    # stå som fanget uden at have prøvet det valutaordene er der for.
    if PRICE_TOKEN.search("19 USD per year") is not None:
        print("SELFTEST FEJLER: valutaord-scenariet kan ikke skelnes fra PRICE_TOKEN — "
              "reglen om valutaord er uden betydning")
        return 1
    if CURRENCY_AMOUNT.search("19 USD per year") is None:
        print("SELFTEST FEJLER: CURRENCY_AMOUNT finder ikke sit eget positive eksempel")
        return 1

    scenarios: list[tuple[str, list[str] | Any]] = [
        ("et link uden for allowlisten", check_links(rogue_link)),
        ("et kontraktprodukt mangler i allowlisten", check_catalog(missing_product)),
        ("ét link delt mellem to produkter", check_catalog(shared_link)),
        ("en opfundet påstand på en virkelig købsside", check_offers(unsatisfiable_offer)[0]),
        ("en dokumenteret købsside uden inventar", check_offers(uninventoried)[0]),
        ("en købsside med forkert domæne", check_routes(wrong_domain["offers"], good["core_pages"])),
        ("for få centrale produktsider", check_routes(good["offers"], missing_core["core_pages"])),
        ("en kundeportal-URL der ikke er allowlistet", check_links(rogue_portal)),
        ("en kundeportal der ikke findes på portalsiderne", check_billing_portal(rogue_portal)),
        ("en abonnement-markering der ikke er i allowlisten", check_worker(no_subscriptions)),
        ("et download-produkt der ikke kan leveres, men sælges", undeliverable),
        ("et leverbart download-produkt uden købsside", forgot_the_page),
        ("en Pro-side der aldrig siger hvad gratis-udgaven giver", no_free_tier),
        ("en gratis-udgave forklaret i en lukket FAQ", buried_free_tier),
        ("en gratis/Pro-tabel med tomme celler", hollow_table),
        ("en Pro-pris uden nogen købsknap", unbuyable_symbol),
        ("en Pro-pris i valutaord uden købsknap", unbuyable_words),
        ("en tom celle i en tabel på en side der ikke sælger", hollow_unsold),
    ]
    missed = [label for label, problems in scenarios if not problems]
    for label in missed:
        print(f"SELFTEST FEJLER: {label} blev ikke fanget")
    for label, problems in (("en Pro-side der siger hvad gratis-udgaven giver", should_also_pass),
                            ("en donationsside uden gratis-udgave", donation_no_free),
                            ("en gratis/Pro-tabel med købsknap", buyable),
                            ("en gratis/Pro-tabel uden pris", priceless)):
        if problems:
            print(f"SELFTEST FEJLER (falsk alarm): {label}: {problems[0]}")
            missed.append(label)
    if should_pass:
        # En kontrol der aldrig må fejle. Uden den kunne den nye regel være
        # stram nok til at gøre hver købsside rød, uden at nogen ser det.
        print(f"SELFTEST FEJLER: et leverbart produkt blev meldt som ikke-leverbart: {should_pass[0]}")
        missed.append("et leverbart produkt på en syntetisk købsside")
    print(f"selftest: {len(scenarios) - len(missed)}/{len(scenarios)} fejlformer fanget")
    return 1 if missed else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true", help="printér inventaret uden at kræve grøn gate")
    parser.add_argument("--self-test", action="store_true", help="bevis at gaten fanger drift")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    catalog = load_catalog(CATALOG)
    if args.report:
        print(json.dumps({"discovered": discover_offers(catalog)}, ensure_ascii=False, indent=2))
        return 0
    problems, inventory = run(catalog)
    print(f"{len(catalog['products'])} produkter, {len(inventory)} dokumenterede købssider")
    print(f"problems: {len(problems)}")
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
