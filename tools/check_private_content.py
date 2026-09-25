#!/usr/bin/env python3
"""Gate for betalt indhold: intet betalt må ligge i det offentlige repo eller i dist.

Opgave 5 i `IMPLEMENTATION_PLAN.md`. Betalte filer leveres fra Cloudflare KV som
`paidfile:<fil>` gennem `GET /api/download/<token>/<fil>`. Kilderne ligger i det
private `mahope/paid-products` og må aldrig offentliggøres.

Gaten fejler ved:

1. `tools/paid_content.json` er ikke fuldstændig eller ikke konsistent med
   `site/_worker.js` (`STRIPE_PRODUCTS`) og `tools/stripe_catalog.json`.
2. Et betalt leveringsfilnavn ligger i den git-tracked tree eller under `dist/`.
3. En offentlig side linker direkte til et betalt leveringsfil.
4. En fil, der blev fjernet i `3eb1dac` ("Fjern betalt indhold fra products/"),
   er dukket op igen i den git-tracked tree.
5. `/api/download` ikke læser sit indhold fra KV.
6. Historikken står som fuldt remedieret. Det må den ikke: betalt indhold findes
   stadig i gamle commits, og det kræver Mads' go at fjerne.

    python3 tools/check_private_content.py            # gate
    python3 tools/check_private_content.py --report   # inventar, uden at fejle
    python3 tools/check_private_content.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools/paid_content.json"
WORKER = ROOT / "site/_worker.js"
CATALOG = ROOT / "tools/stripe_catalog.json"
DIST = ROOT / "dist"
SITE = ROOT / "site"
SKIP_DIRS = {"__pycache__", ".wrangler", ".git", "node_modules"}

BLOCKED_REMEDIATION = "BLOCKED: kræver Mads-godkendelse"
PRODUCT_KEY = re.compile(r"^[a-z0-9-]+$")
FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
ATTR = re.compile(r"""\b(?:href|src|content)\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
# Products-blokken i _worker.js: nøgle + inline objekt på én linje.
WORKER_ENTRY = re.compile(r"'([a-z0-9-]+)'\s*:\s*\{([^{}]*)\}")
KV_READ = re.compile(r"paidfile:\$\{file\}")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_tracked() -> set[str]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        capture_output=True, text=True, check=True)
    return {line for line in out.stdout.splitlines() if line}


def worker_downloads(worker_text: str) -> dict[str, dict]:
    """Alle `kind: 'download'`-produkter i STRIPE_PRODUCTS med navn og filer."""
    products: dict[str, dict] = {}
    for key, body in WORKER_ENTRY.findall(worker_text):
        if "kind: 'download'" not in body:
            continue
        name = re.search(r"name:\s*'([^']+)'", body)
        files = re.search(r"files:\s*\[([^\]]*)\]", body)
        products[key] = {
            "name": name.group(1) if name else None,
            "files": re.findall(r"'([^']+)'", files.group(1)) if files else [],
        }
    return products


def delivery_files(manifest: dict) -> set[str]:
    return {name for product in manifest.get("products", [])
            for name in product.get("delivery_files", [])}


def retired_files(manifest: dict) -> set[str]:
    return {name for name in manifest.get("retired_public_files", {}).get("files", [])}


def check_manifest(manifest: dict, worker: dict[str, dict], catalog: dict) -> list[str]:
    """Struktur, fuldstændighed og trevejs-konsistens."""
    problems: list[str] = []
    if manifest.get("schema") != "hermes-paid-content-1":
        problems.append(f"manifest: ukendt schema {manifest.get('schema')!r}")
    products = manifest.get("products")
    if not isinstance(products, list) or not products:
        return problems + ["manifest: `products` skal være en ikke-tom liste"]

    seen_keys: set[str] = set()
    for product in products:
        key = product.get("product_key", "<mangler>")
        if not PRODUCT_KEY.match(key):
            problems.append(f"manifest: ugyldigt product_key {key!r}")
        if key in seen_keys:
            problems.append(f"manifest: {key} står to gange")
        seen_keys.add(key)
        if not product.get("name"):
            problems.append(f"manifest: {key} mangler name")
        if not product.get("price"):
            problems.append(f"manifest: {key} mangler en dokumenteret pris")
        files = product.get("delivery_files")
        if not isinstance(files, list) or not files:
            problems.append(f"manifest: {key} har ingen delivery_files")
            continue
        if len(set(files)) != len(files):
            problems.append(f"manifest: {key} har en dublet i delivery_files")
        for name in files:
            if not FILENAME.match(name) or "/" in name:
                problems.append(f"manifest: {key} har et ugyldigt filnavn {name!r}")
        sha = product.get("sha256")
        if sha is not None and not SHA256.match(sha):
            problems.append(f"manifest: {key} har et ugyldigt sha256 {sha!r}")
        if not isinstance(product.get("build_command"), (str, type(None))):
            problems.append(f"manifest: {key} har et ikke-strengt build_command")
        if not isinstance(product.get("kv_verified"), bool):
            problems.append(f"manifest: {key} mangler kv_verified")

    # Workeren er source of truth for hvad en køber faktisk får.
    for key, entry in worker.items():
        listed = next((p for p in products if p.get("product_key") == key), None)
        if listed is None:
            problems.append(f"worker: downloadproduktet {key} mangler i paid_content.json")
            continue
        if listed.get("delivery_files") != entry["files"]:
            problems.append(
                f"drift: {key} leverer {entry['files']} i workeren, "
                f"men {listed.get('delivery_files')} i inventaret")
        if listed.get("name") != entry["name"]:
            problems.append(f"drift: {key} hedder {entry['name']!r} i workeren, "
                            f"{listed.get('name')!r} i inventaret")
    for product in products:
        key = product.get("product_key")
        if key not in worker:
            problems.append(f"inventar: {key} findes ikke som downloadprodukt i workeren")
        elif key not in catalog.get("products", {}):
            problems.append(f"katalog: {key} mangler i stripe_catalog.json")
        elif catalog["products"][key].get("kind") != "download":
            problems.append(f"katalog: {key} er ikke kind=download")
        elif catalog["products"][key].get("price") != product.get("price"):
            problems.append(f"drift: {key} står til {product.get('price')} i inventaret, "
                            f"{catalog['products'][key].get('price')} i katalogen")
    return problems


def check_provenance(manifest: dict) -> list[str]:
    """Historikken må ikke stå som remedieret, og kilden skal være privat."""
    problems: list[str] = []
    history = manifest.get("history", {})
    if history.get("remediation") != BLOCKED_REMEDIATION:
        problems.append(
            f"provenance: history.remediation skal være {BLOCKED_REMEDIATION!r}, "
            f"er {history.get('remediation')!r}")
    if not history.get("public_commits_with_paid_content"):
        problems.append("provenance: history skal fastholde, at betalt indhold findes i gamle commits")
    if not history.get("cleanup_commit"):
        problems.append("provenance: history mangler cleanup_commit")
    source = manifest.get("private_source", {})
    if source.get("visibility") != "privat":
        problems.append("provenance: private_source skal være deklareret som privat")
    if not source.get("repo"):
        problems.append("provenance: private_source mangler sit private repo")
    return problems


def check_tracked(manifest: dict, tracked: set[str]) -> list[str]:
    """Ingen betalte leveringsfiler i den git-tracked tree."""
    problems = [f"offentligt repo: betalt fil {name} er git-tracked"
                for name in sorted(delivery_files(manifest)) if name in tracked]
    problems += [f"offentligt repo: fjernet fil {path} er git-tracked igen"
                 for path in sorted(retired_files(manifest)) if path in tracked]
    # products/ er den mappe, hvorfra betalt indhold tidligere blev committet.
    problems += [f"offentligt repo: products/ har igen filen {path}"
                 for path in sorted(tracked) if path.startswith("products/")
                 and path not in {"products/bundle-cover.png"}]
    return problems


def check_dist(manifest: dict, found: dict[str, list[str]]) -> list[str]:
    """Ingen betalte leveringsfiler i offentligt buildoutput."""
    return [f"offentligt buildoutput: {name} findes i dist/{', '.join(paths)}"
            for name, paths in sorted(found.items()) if paths]


def check_public_links(manifest: dict, links: list[tuple[str, str]]) -> list[str]:
    """Ingen offentlig side må pege direkte på et betalt leveringsfil."""
    paid = delivery_files(manifest)
    retired = {Path(name).name for name in retired_files(manifest)}
    problems: list[str] = []
    for path, href in links:
        target = href.split("?")[0].split("#")[0].rsplit("/", 1)[-1]
        if target in paid:
            problems.append(f"offentlig side: {path} linker direkte på den betalte fil {target}")
        elif target in retired:
            problems.append(f"offentlig side: {path} linker på den fjernede fil {target}")
    return problems


def check_worker_delivery(worker_text: str) -> list[str]:
    """`/api/download` skal hente sit indhold i KV, ikke i en statisk fil."""
    problems: list[str] = []
    handler = re.search(r"async function handlePaidDownload\(.*?\n\}", worker_text, re.DOTALL)
    if handler is None:
        return ["worker: handlePaidDownload blev ikke fundet"]
    body = handler.group(0)
    if not KV_READ.search(body):
        problems.append("worker: handlePaidDownload læser ikke fra KV (`paidfile:${file}`)")
    if "env.ASSETS" in body:
        problems.append("worker: handlePaidDownload må ikke hente fra statiske assets")
    if not re.search(r"env\.VISITS\.get\(`dl:\$\{m\[1\]\}`\)", body):
        problems.append("worker: handlePaidDownload skal validere sit download-token")
    return problems


def scan_dist() -> dict[str, list[str]]:
    """Grundnavne på alle filer under dist/, som er et betalt leveringsfil."""
    names = delivery_files(load_json(MANIFEST))
    found: dict[str, list[str]] = {}
    for path in DIST.rglob("*"):
        if not path.is_file():
            continue
        for part in path.parts:
            if part in SKIP_DIRS:
                break
        else:
            if path.name in names or path.name in retired_files(load_json(MANIFEST)):
                found.setdefault(path.name, []).append(str(path.relative_to(ROOT)))
    return found


def scan_public_links() -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    for path in sorted(SITE.rglob("*.html")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        for href in ATTR.findall(path.read_text(encoding="utf-8", errors="replace")):
            links.append((str(path.relative_to(ROOT)), href))
    return links


def collect(manifest: dict) -> dict:
    return {
        "worker": load_json_safe(WORKER),
        "catalog": load_json(CATALOG),
        "tracked": git_tracked(),
        "dist": scan_dist(),
        "links": scan_public_links(),
    }


def load_json_safe(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run(manifest: dict, data: dict) -> list[str]:
    worker_downloads_map = worker_downloads(data["worker"])
    problems = check_manifest(manifest, worker_downloads_map, data["catalog"])
    problems += check_provenance(manifest)
    problems += check_tracked(manifest, data["tracked"])
    problems += check_dist(manifest, data["dist"])
    problems += check_public_links(manifest, data["links"])
    problems += check_worker_delivery(data["worker"])
    return problems


def report(manifest: dict) -> None:
    source = manifest.get("private_source", {})
    print(f"Betalt indhold — {len(manifest.get('products', []))} produkter")
    print(f"Kilder: {source.get('repo')} ({source.get('visibility')}), "
          f"levering: KV {manifest['public_delivery']['kv_prefix']}<fil>")
    for product in manifest.get("products", []):
        print(f"\n  {product['product_key']} — {product['name']} ({product['price']})")
        for name in product["delivery_files"]:
            key = f"{manifest['public_delivery']['kv_prefix']}{name}"
            state = "verificeret" if product.get("kv_verified") else "uverificeret i KV"
            print(f"    {key:44} {name:38} {state}")
        print(f"    build: {product.get('build_command') or 'ikke dokumenteret (privat kilde)'}")
        print(f"    sha256: {product.get('sha256') or 'ikke fastsat'}")
    history = manifest.get("history", {})
    print(f"\nHistorik: fjernet i {history.get('cleanup_commit')}, "
          f"remediering {history.get('remediation')}")


def self_test() -> int:
    """Beviser at gaten fanger hver fejlform, den siger at fange."""
    good = load_json(MANIFEST)
    worker_text = load_json_safe(WORKER)
    worker_map = worker_downloads(worker_text)
    catalog = load_json(CATALOG)
    paid = sorted(delivery_files(good))
    retired = sorted(retired_files(good))

    scenarios: list[tuple[str, list[str]]] = [
        ("et betalt leveringsfil i den git-tracked tree",
         check_tracked(good, {"README.md", paid[0]})),
        ("en fil fjernet i 3eb1dac der er dukket op igen",
         check_tracked(good, {"README.md", retired[0]})),
        ("et nyt betalt arkiv under products/",
         check_tracked(good, {"README.md", "products/ny-skabelon.pdf"})),
        ("et betalt leveringsfil i dist",
         check_dist(good, {paid[1]: ["mahope.tools/" + paid[1]]})),
        ("en offentlig side der linker på det betalte fil",
         check_public_links(good, [("site/thanks.html", "/downloads/" + paid[2])])),
        ("en downloadprodukt i workeren uden inventar",
         check_manifest(good, {**worker_map, "eucomply-helt-nyt": {
             "name": "Nyt", "files": ["nyt.pdf"]}}, catalog)),
        ("en fil-liste der er ændret i workeren",
         check_manifest(good, {**worker_map, "eucomply-dpa": {
             **worker_map["eucomply-dpa"], "files": ["dpa-template.pdf"]}}, catalog)),
        ("en pris der ikke matcher katalogen",
         check_manifest({**good, "products": [
             {**p, "price": "$1"} if p["product_key"] == "eucomply-dpa" else p
             for p in good["products"]]}, worker_map, catalog)),
        ("historiek der står som fuldt remedieret",
         check_provenance({**good, "history": {**good["history"],
                                               "remediation": "done"}})),
        ("en downloadroute der ikke læser fra KV",
         check_worker_delivery(worker_text.replace(
             "paidfile:${file}", "assets/${file}"))),
    ]
    missed = [label for label, problems in scenarios if not problems]
    for label in missed:
        print(f"SELFTEST FEJLER: {label} blev ikke fanget")
    print(f"selftest: {len(scenarios) - len(missed)}/{len(scenarios)} fejlformer fanget")
    return 1 if missed else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true",
                        help="printér inventaret uden at kræve grøn gate")
    parser.add_argument("--self-test", action="store_true",
                        help="bevis at gaten fanger drift")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    manifest = load_json(MANIFEST)
    if args.report:
        report(manifest)
        return 0

    problems = run(manifest, collect(manifest))
    for problem in problems:
        print(f"PROBLEM: {problem}")
    print(f"check_private_content: {len(problems)} problemer")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
