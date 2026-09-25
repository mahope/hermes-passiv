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
    wrong_domain = {**good, "offers": [
        {**offer, "domain": "example.com"} if offer["path"] == "site/scan.html" else offer
        for offer in good["offers"]]}
    missing_core = {**good, "core_pages": good["core_pages"][:3]}
    rogue_portal = {**good, "billing_portal": "https://billing.stripe.com/p/login/ukjendtPortal0"}
    no_subscriptions = {**good, "products": {
        key: {field: value for field, value in product.items() if field != "subscription"}
        for key, product in good["products"].items()}}

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
    ]
    missed = [label for label, problems in scenarios if not problems]
    for label in missed:
        print(f"SELFTEST FEJLER: {label} blev ikke fanget")
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
