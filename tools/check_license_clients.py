#!/usr/bin/env python3
"""Hold alle Clean Copy-licensklienter på den aftalte kontrakt.

Del 1 af opgave 7 fandt, at de shippede klienter ikke sendte `product`, ramte
et dødt endepunkt og slettede Pro ved en licensserverfejl. Den adfærd er nu
testet i `tools/test_license_clients.js`, som indlæser de filer der faktisk
ships. Det her er den del tests ikke kan se: en *ny* klient, der kalder
`/api/license` uden at overholde kontrakten.

Kør: python3 tools/check_license_clients.py            (fra repo-roden)
     python3 tools/check_license_clients.py --self-test
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "tools/clean_copy_license.js"

# Kilder der SKAL findes, hvis de kalder /api/license. Hver linje er
# (sti, forventet product_key). Tom streng = ingen product forventet (kun
# tilladt hvor der står en begrundelse).
CLIENTS: dict[str, str] = {
    "obsidian-plugin/main.js": "clean-copy-pro",
    "extension-clean-copy/options.js": "clean-copy-pro",
    "extension-clean-copy-firefox/options.js": "clean-copy-pro",
    "extension-clean-copy/license.js": "clean-copy-pro",
    "extension-clean-copy-firefox/license.js": "clean-copy-pro",
    "tools/clean_copy_license.js": "clean-copy-pro",
    "site/clean-copy-tool.html": "clean-copy-pro",
    "site/compliance-report.html": "eucomply-pro",
    "page-profile/page_profile.py": "page-profile-pro",
    "site/downloads/page-profile/page_profile.py": "page-profile-pro",
    "site-icons/site_icons.py": "",
    "site/downloads/site-icons/site_icons.py": "",
}

# Filer der bevidst ikke følger kontrakten endnu, med begrundelse. Uden en
# linje her er en afvigelse en fejl, så listen kan ikke vokse ved et uheld.
EXCEPTIONS: dict[str, str] = {
    "site/_worker.js": "serveren selv: modtager kalden og udsteder nøgler",
    "desktop/main.js": (
        "EAA-scannerens desktop-klient. Vært peger på den døde "
        "hermes-passiv.pages.dev, og der er ingen EAA-produkt i Stripe-kontrakten, "
        "så den kræver en beslutning (❓ Til Mads 5) — ikke en blind rettelse"
    ),
}

# Filer der overhovedet ikke er klienter: tests, kontrakttabellen og gaten
# selv. De nævner API'en, men ingen køber indlæser dem.
NOT_CLIENTS = {
    "tests/stripe-worker.test.mjs",
    "page-profile/test_page_profile.py",
    "tools/test_license_clients.js",
    "tools/test_license_flow.js",
    "tools/stripe_catalog.json",
    "tools/check_license_clients.py",
}

# Marker omkring det indlejrede kanoniske modul.
MARK_A = "/* >>> clean-copy-license: tools/clean_copy_license.js — do not edit by hand */"
MARK_B = "/* <<< clean-copy-license */"

SKIP_DIRS = {"dist", "node_modules", ".git", ".wrangler", "site-icons/dist"}
SKIP_SUFFIX = {".md", ".zip", ".tar.gz", ".png", ".jpg", ".ico", ".woff", ".woff2"}


def is_skipped(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    name = path.name
    return any(name.endswith(sfx) for sfx in SKIP_SUFFIX)


def find_callers() -> dict[str, str]:
    """Alle kildefiler der nævner /api/license, undtagen dem der ikke er klienter.

    Filer i CLIENTS og EXCEPTIONS tages med uanset, så en klient der skifter
    fra en hardkodet base til et modul stadig bliver holdt i øje.
    """
    found: dict[str, str] = {}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or is_skipped(path.relative_to(ROOT)):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, ValueError):
            continue
        rel = str(path.relative_to(ROOT))
        if "/api/license" in text or "api.lemonsqueezy" in text or rel in CLIENTS or rel in EXCEPTIONS:
            found[rel] = text
    for rel in NOT_CLIENTS:
        found.pop(rel, None)
    return found


def strip_comments(text: str) -> str:
    """Fjern //- og /* */-kommentarer, så en nævnt URL ikke tæller som et kald."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"^\s*(?://|#).*$", " ", text, flags=re.M)


def check_callers(callers: dict[str, str]) -> list[str]:
    problems: list[str] = []
    for rel, text in sorted(callers.items()):
        if rel in EXCEPTIONS:
            continue
        body = strip_comments(text)
        if "api.lemonsqueezy" in body:
            problems.append(f"{rel}: kalder den lukkede Lemon Squeezy-API")
        # Kildefilerne har stadig OLD_ORIGIN i deres OG-tags; build_sites.py
        # skriver dem om til det rette domæne. Flagget gælder derfor kun den
        # døde vært i et licenskald.
        for line in body.splitlines():
            if "hermes-passiv.pages.dev" in line and "api/license" in line:
                problems.append(f"{rel}: licenskaldet bruger den døde vært hermes-passiv.pages.dev")
        if "/api/license" not in body:
            continue
        expected = CLIENTS.get(rel)
        if expected is None:
            problems.append(
                f"{rel}: kalder /api/license men er ikke opført i CLIENTS — "
                "tilføj den med sit product_key, så kontrakten håndhæves"
            )
            continue
        if expected and expected not in body:
            problems.append(f"{rel}: sender ikke product '{expected}'")
    for rel in CLIENTS:
        if rel in EXCEPTIONS:
            problems.append(f"{rel}: er både CLIENT og EXCEPTION")
        elif rel not in callers:
            problems.append(f"{rel}: forventet licensklient findes ikke længere")
    return problems


def check_exceptions(existing: set[str] | None = None) -> list[str]:
    """En undtagelse skal have en begrundelse, en fil og stadig være nødvendig."""
    problems: list[str] = []
    for rel in EXCEPTIONS:
        if existing is None:
            present = (ROOT / rel).exists()
        else:
            present = rel in existing
        if not present:
            problems.append(f"{rel}: undtagelsen findes ikke længere — fjern den")
    return problems


def inline_module(text: str) -> str | None:
    """Det indlejrede modul mellem markørerne, eller None hvis de mangler."""
    a, b = text.find(MARK_A), text.find(MARK_B)
    if a < 0 or b < a:
        return None
    return text[a + len(MARK_A):b].strip()


def check_inline(text: str, rel: str, canon: str) -> list[str]:
    module = inline_module(text)
    if module is None:
        return [f"{rel}: det indlejrede licensmodul mangler sine markører"]
    if module != canon.strip():
        return [f"{rel}: indlejret modul afviger fra tools/clean_copy_license.js"]
    return []


def check_copies(canon: str) -> list[str]:
    """Det indlejrede modul skal være byte-identisk med den kanoniske kilde."""
    problems: list[str] = []
    for rel in ("extension-clean-copy/license.js", "extension-clean-copy-firefox/license.js"):
        path = ROOT / rel
        if not path.exists():
            problems.append(f"{rel}: mangler")
        elif path.read_text(encoding="utf-8") != canon:
            problems.append(f"{rel}: afviger fra tools/clean_copy_license.js")

    problems += check_inline((ROOT / "site/clean-copy-tool.html").read_text(encoding="utf-8"),
                             "site/clean-copy-tool.html", canon)
    problems += check_inline((ROOT / "obsidian-plugin/main.js").read_text(encoding="utf-8"),
                             "obsidian-plugin/main.js", canon)

    firefox = ROOT / "extension-clean-copy-firefox/options.js"
    chrome = ROOT / "extension-clean-copy/options.js"
    if firefox.exists() and chrome.exists():
        if firefox.read_text(encoding="utf-8") != chrome.read_text(encoding="utf-8"):
            problems.append("extension-clean-copy-firefox/options.js: afviger fra Chrome-kopien")
    return problems


def check_cache_rule() -> list[str]:
    """Klienter der kan låse en betalende kunde ude skal have syvdagesreglen."""
    problems: list[str] = []
    for rel in ("obsidian-plugin/main.js", "extension-clean-copy/options.js",
                "site/clean-copy-tool.html"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        if "CleanCopyLicense" not in text:
            problems.append(f"{rel}: bruger ikke det kanoniske licensmodul")
    return problems


def run() -> list[str]:
    canon = CANON.read_text(encoding="utf-8")
    if "clean-copy-pro" not in canon or "7 * 24 * 60 * 60 * 1000" not in canon:
        return ["tools/clean_copy_license.js: den kanoniske regel mangler product eller syvdagesregel"]
    return (check_callers(find_callers()) + check_exceptions()
            + check_copies(canon) + check_cache_rule())


def self_test() -> int:
    """Bevis at gaten fanger hver fejlform, den siger at fange."""
    canon = CANON.read_text(encoding="utf-8")
    callers = find_callers()
    page = (ROOT / "site/clean-copy-tool.html").read_text(encoding="utf-8")
    scenarios: list[tuple[str, list[str]]] = [
        ("et kald uden product",
         check_callers({**callers, "site/ny-klient.html": "fetch('/api/license/validate', {body:'{}'})"})),
        ("et kald på den døde vært",
         check_callers({**callers, "site/ny-klient.html": "fetch('https://hermes-passiv.pages.dev/api/license/validate')"})),
        ("et kald på den lukkede Lemon Squeezy-API",
         check_callers({**callers, "site/ny-klient.html": "fetch('https://api.lemonsqueezy.com/v1/licenses/validate')"})),
        ("en ny klient der ikke er opført",
         check_callers({**callers, "site/ukendt.html": "fetch('/api/license/activate')"})),
        ("en forventet klient der er væk",
         check_callers({k: v for k, v in callers.items() if k != "obsidian-plugin/main.js"})),
        ("en undtagelse der ikke længere findes", check_exceptions(set())),
        ("et indlejret modul der afviger",
         check_inline(page.replace("CACHE_MAX_MS = 7", "CACHE_MAX_MS = 30"),
                      "site/clean-copy-tool.html", canon)),
        ("et indlejret modul der mangler i siden",
         check_inline(page.replace(MARK_A, "/* slettet */").replace(MARK_B, ""),
                      "site/clean-copy-tool.html", canon)),
    ]

    failures = 0
    for name, problems in scenarios:
        if problems:
            print(f"OK   {name}: {problems[0]}")
        else:
            print(f"FELO {name}: gaten siger OK, men den skulle have fanget noget")
            failures += 1

    # Den sunde tilstand skal være ren.
    clean = (check_callers(callers) + check_exceptions()
             + check_copies(canon) + check_cache_rule())
    if clean:
        print("FELO den nuværende kode giver problemer: " + "; ".join(clean[:3]))
        failures += 1
    else:
        print("OK   den nuværende kode holder kontrakten")
    print(f"{len(scenarios) + 1 - failures}/{len(scenarios) + 1} self-tests bestået")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="bevis at gaten fanger de fejl, den siger at fange")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    problems = run()
    print(f"{len(find_callers())} licensklient-kilder læst")
    print("problems:", len(problems))
    for problem in problems:
        print(f"  {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
