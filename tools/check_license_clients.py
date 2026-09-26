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
import shutil
import sys
import tempfile
from functools import lru_cache
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
    "tools/check_clean_copy_distribution.py",
    "tools/build_clean_copy_archives.py",
    # Opgave 26: porten over rod-README'en nævner licens-API'en i en kommentar om
    # hvorfor den *ikke* står i sin egen liste over ikke-sider. Samme fejlform som
    # opgave 20 (check_license_clients fangede sin egen docstring): en gate der
    # leder efter en sti i al tekst, træffer alt der vil forklare stien.
    "tools/check_repo_readme.py",
    # Opgave 28: samme fejlform igen. `check_retired_downloads.py` nævner
    # licens-API'en i portens egen docstring og i en begrundelse om hvorfor 1.5.3
    # blev trukket tilbage, og `retired_downloads.json` har samme begrundelse som
    # data. Ingen af dem kalder den — de beskriver hvorfor en *kunde* gør det.
    "tools/check_retired_downloads.py",
    "tools/retired_downloads.json",
}

# Marker omkring det indlejrede kanoniske modul.
MARK_A = "/* >>> clean-copy-license: tools/clean_copy_license.js — do not edit by hand */"
MARK_B = "/* <<< clean-copy-license */"

SKIP_DIRS = {"dist", "node_modules", ".git", ".wrangler", "site-icons/dist",
             # CI checkouter det eksterne build-repo ved siden af workspace
             # (se `AUDITEDWP_DIR` i deploy-sites.yml), så det ligger inde i
             # `ROOT` kun i CI — aldrig lokalt. Uden den her regel fejlede
             # gaten i kørsel 36185964282 med fem fund i `mahope/auditedwp`,
             # som er et andet repo med sin egen licenskontrakt, som vi ikke
             # må ændre. Fundene er noteret i planen i stedet for at drukne i
             # en rød port på hvert push.
             "auditedwp-src", "deskuptime-src"}
SKIP_SUFFIX = {".md", ".zip", ".tar.gz", ".png", ".jpg", ".ico", ".woff", ".woff2"}


@lru_cache(maxsize=None)
def is_external_checkout(top: str) -> bool:
    """Er denne mappe på øverste niveau en indlejret checkout af et andet repo?

    Regelprincip, ikke en navneliste: en mappe der indeholder en `.git` et sted
    under sig er ikke vores kode, uanset hvor dybt den ligger og hvad CI har
    kaldt den. Eftersom CI checkouter `auditedwp-src` *ved siden af* workspace
    (`AUDITEDWP_DIR`), ligger det kun inde i `ROOT` i CI — aldrig lokalt, så
    uden denne regel så gaten ren på min maskine og rød i kørsel 36185964282.
    """
    base = ROOT / top
    if not base.is_dir():
        return False
    return any(path.is_dir() for path in base.rglob(".git"))


def is_skipped(path: Path) -> bool:
    # `find_callers` giver en relativ sti, kalderne til `check_exceptions` en
    # absolut. `relative_to` ville kaste på den relative, så begge normaliseres.
    rel = path if not path.is_absolute() else path.relative_to(ROOT)
    if any(part in SKIP_DIRS for part in rel.parts):
        return True
    if rel.parts and is_external_checkout(rel.parts[0]):
        return True
    name = rel.name
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


def check_seat_release(callers: dict[str, str]) -> list[str]:
    """En klient der kan aktivere skal også kunne afgive sin plads.

    Kontrakten tæller én plads pr. maskine og har et `deactivate`-endpoint
    netop til det. Uden et kald til det kan en kunde, der flytter til en ny
    maskine, ikke komme under grænsen igen — og den eneste udveje er at
    skrive til et menneske, hvilket missionen forbyder.
    """
    problems: list[str] = []
    for rel, text in sorted(callers.items()):
        if rel in EXCEPTIONS or rel in NOT_CLIENTS:
            continue
        body = strip_comments(text)
        if "proLicense" not in body:
            continue
        if "/activate" not in body:
            continue
        if "/deactivate" in body:
            continue
        problems.append(
            f"{rel}: kan aktivere en licens, men kalder aldrig /deactivate — "
            "pladsen på licensserveren kan så aldrig frigives af brugeren selv"
        )
    return problems


def run() -> list[str]:
    canon = CANON.read_text(encoding="utf-8")
    if "clean-copy-pro" not in canon or "7 * 24 * 60 * 60 * 1000" not in canon:
        return ["tools/clean_copy_license.js: den kanoniske regel mangler product eller syvdagesregel"]
    return (check_callers(find_callers()) + check_exceptions()
            + check_copies(canon) + check_cache_rule()
            + check_seat_release(find_callers()))


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
        ("en klient der kan aktivere men ikke afgive pladsen",
         check_seat_release({**callers, "site/ny-klient.html":
                             "const A = API_BASE + '/activate'; chrome.storage.local.set({proLicense: k});"})),
    ]

    failures = 0
    for name, problems in scenarios:
        if problems:
            print(f"OK   {name}: {problems[0]}")
        else:
            print(f"FELO {name}: gaten siger OK, men den skulle have fanget noget")
            failures += 1

    # Negativ kontrol: en klient der *kan* afgive pladsen, og en der slet ikke
    # kan aktivere, må begge være grønne. Uden dem kunne reglen smadre enhver
    # klient, og det ville lukke porten for de fejl den er skrevet til at finde.
    for name, probe in [
        ("en klient der både aktiverer og afgiver plads",
         "const A = API_BASE + '/activate', D = API_BASE + '/deactivate'; "
         "chrome.storage.local.set({proLicense: k});"),
        ("en klient der kun tjekker, uden at gemme nøglen",
         "const V = API_BASE + '/validate'; fetch(V);"),
    ]:
        got = check_seat_release({"site/probe.html": probe})
        if got:
            print(f"FELO {name} blev fejlet: {got[0]}")
            failures += 1
        else:
            print(f"OK   {name}: ikke fejlet")

    # Den indlejret-checkout-regel kræver en rigtig mappe at kigge på, så den
    # probes på filsystemet i stedet for i en dict. Uden denne test kunne
    # reglen slettes uden at nogen opdagede det, og gaten ville blive rød i
    # hvert CI-run igen — se kørsel 36185964282.
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        name = Path(tmp).name
        probe = ROOT / name / "probe"
        probe.mkdir(parents=True)
        (probe / "lic.js").write_text("fetch('https://api.lemonsqueezy.com/v1/licenses/validate')",
                                      encoding="utf-8")
        try:
            # Uden `.git` må mappen kun springes over, hvis den hedder det, CI
            # bruger. Ellers ville reglen springe enhver midlertidig mappe over.
            if name in SKIP_DIRS:
                print("FELO testen ligger i en mappe, der er på skip-listen — "
                      "den beviser intet om navne-listen")
                failures += 1
            elif is_skipped(probe / "lic.js"):
                print("FELO en almindelig mappe blev springet over som om den "
                      "var et eksternt repo")
                failures += 1
            else:
                print("OK   en almindelig mappe læses: kun et eksternt repo "
                      "springes over")
            (probe / ".git").mkdir()
            is_external_checkout.cache_clear()
            if is_skipped(probe / "lic.js"):
                print("OK   en indlejret checkout springes over: den har sin egen .git")
            else:
                print("FELO en mappe med sin egen .git blev læst som vores kode — "
                      "gaten fejler i CI på et repo vi ikke ejer")
                failures += 1
        finally:
            shutil.rmtree(ROOT / name, ignore_errors=True)

    # Den navngivne regel: CI's checkout hedder `auditedwp-src`, og den skal
    # springes over også hvis den er eksporteret uden `.git`.
    if "auditedwp-src" not in SKIP_DIRS:
        print("FELO `auditedwp-src` mangler i skip-listen — se kørsel 36185964282")
        failures += 1
    else:
        print("OK   CI's `auditedwp-src` står på skip-listen")

    # Den sunde tilstand skal være ren.
    clean = (check_callers(callers) + check_exceptions()
             + check_copies(canon) + check_cache_rule()
             + check_seat_release(callers))
    if clean:
        print("FELO den nuværende kode giver problemer: " + "; ".join(clean[:3]))
        failures += 1
    else:
        print("OK   den nuværende kode holder kontrakten")
    total = len(scenarios) + 5
    print(f"{total - failures}/{total} self-tests bestået")
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
