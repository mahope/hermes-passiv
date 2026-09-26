#!/usr/bin/env python3
"""Kør kildevejen i README'en og kræv, at den er den motor der bygger.

Baggrunden er opgave 87. `scanner/scanner_core.py` var en 520 linjer lang kopi
af scanneren med **16 regler**, mens `pip install eaa-scanner`, npm-CLI'en og
desktop-appen kører de **22** i `scanner/packaging/eaa_scanner/core.py`. De to
filer var ens i API og forskellige i indhold, så de kunne ikke vedligeholdes
sammen — og ingen port så det, fordi ingen målte den fil.

Det var heller ikke død kode. `site/downloads/eaa-scanner-README.md` — den
README kunden henter — dokumenterer kildevejen:

    git clone <this repo> && cd scanner
    python scan.py https://example.com

Den vej gik gennem `scan.py` → `scanner_core.py` → 16 regler, så en kunde der
fulgte README'en fik seks færre regler end `pip install` på den *samme* side.
Målt på `tools/fixtures/eaa_engine_all_rules.html`: 16 i kildevejen, 22 i
hjulet. Det er den alvorlige retning: en kunde der *køber* en regel, en
rapport eller en audit uden at vide at scanningen kørte seks regler færre.

Derfor skal denne test tre ting holde samtidig:

1. **`scanner_core.py` er en omdirigering.** Den må ikke definere sin egen
   motor igen. Det er den fejlform der gjorde de 16 mulige, så hvis filen
   vokser tilbage til en kopi, skal det rødme med det samme.
2. **Kildevejen kører den motor der bygger.** Testen indlæser `scanner_core`
   og kalder `scan_html()` — det er præcis det `scan.py` gør — og kræver at
   svaret er det samme som hjulets.
3. **Den dynamiske mængde er den statiske.** De id'er der fyrer, skal være
   præcis dem `check_rule_claims.py` tæller i koden. Ellers kan de to blive
   enige om et forkert tal, og porten er da ingen prøve.

Testen læser altså ikke kode for at tælle regler — den **kører** vejen. Det er
sammeprincip som `test_plugin_engine_rules.py`, og af samme grund: en fuldstændig
måling af det forkerte produkt er grøn, fordi den er fuldstændig.

Uden `python3` springer intet over. Uden README-linjen springer kun arm 2
over, med en synlig besked — så en fremtidig udgave der fjerner kildevejen
ikke får en grøn linje der ligner en bestået prøve.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from check_rule_claims import py_engine_ids  # noqa: E402

SHIM = REPO / "scanner" / "scanner_core.py"
CANONICAL = REPO / "scanner" / "packaging" / "eaa_scanner" / "core.py"
README = REPO / "site" / "downloads" / "eaa-scanner-README.md"
FIXTURE = REPO / "tools" / "fixtures" / "eaa_engine_all_rules.html"

EXPECTED = 22

# Tegn der optræder i en egen motor og ikke i en omdirigering. De er valgt for
# at være umulige at skrive ved en fejltagelse: en omdirigering nævner
# `eaa_scanner.core`, og den streng har intet med den motor at gøre.
ENGINE_MARKERS = ("class _Collector", "HTMLParser", "def crawl_site",
                  "def scan_html", "findings.append")


def fail(msg: str) -> None:
    print(f"FEJL: {msg}")
    raise SystemExit(1)


def check_shim_is_redirect() -> None:
    """(1) Filen må ikke være en motor igen."""
    if not SHIM.is_file():
        fail(f"{SHIM} mangler")

    text = SHIM.read_text(encoding="utf-8")
    found = [m for m in ENGINE_MARKERS if m in text]
    if found:
        fail(f"{SHIM.relative_to(REPO)} definerer igen sin egen motor "
             f"({', '.join(found)}). Den skal være en omdirigering til "
             f"{CANONICAL.relative_to(REPO)} — ellers kommer de 16 regler "
             f"tilbage, og kildevejen i README'en kører dem igen.")

    if "eaa_scanner" not in text:
        fail(f"{SHIM.relative_to(REPO)} indlæser ikke den motor der bygger "
             f"(`eaa_scanner.core`). Uden det peger intet på "
             f"{CANONICAL.relative_to(REPO)}.")


def run_via(code: str, what: str) -> list[str]:
    r = subprocess.run([sys.executable, "-c", code], cwd=REPO,
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"{what} kunne ikke køre: {r.stderr.strip() or r.stdout.strip()}")
    return [x for x in r.stdout.strip().split(",") if x]


def check_source_path() -> None:
    """(2)+(3) Kildevejen skal køre præcis den motor hjulet bygger."""
    claimed = py_engine_ids(CANONICAL)
    if len(claimed) != EXPECTED:
        fail(f"{CANONICAL.relative_to(REPO)} har {len(claimed)} regel-id'er, "
             f"porten forventer {EXPECTED}")

    # Den vej `scan.py` går: `sys.path` med `scanner/`, så `scanner_core`
    # indlæses som et topniveau-modul — nøjagtig som når kunden kører
    # `python scan.py` i `scanner/`.
    via_shim = run_via(
        "import sys; sys.path.insert(0, 'scanner');"
        "from scanner_core import scan_html;"
        f"r = scan_html(open({str(FIXTURE)!r}).read());"
        "assert r.get('ok') is not False, r.get('error');"
        "print(','.join(f['rule_id'] for f in r['findings']))",
        "kildevejen (scanner_core)")

    via_wheel = run_via(
        "import sys; sys.path.insert(0, 'scanner/packaging');"
        "from eaa_scanner.core import scan_html;"
        f"r = scan_html(open({str(FIXTURE)!r}).read());"
        "assert r.get('ok') is not False, r.get('error');"
        "print(','.join(f['rule_id'] for f in r['findings']))",
        "hjulets motor")

    if set(via_shim) != set(via_wheel):
        only_shim = sorted(set(via_shim) - set(via_wheel))
        only_wheel = sorted(set(via_wheel) - set(via_shim))
        fail("kildevejen og hjulet er uenige om samme dokument: "
             + (f"kun i kildevejen {', '.join(only_shim)}; " if only_shim else "")
             + (f"kun i hjulet {', '.join(only_wheel)}" if only_wheel else "")
             + ". Begge veje skal køre samme motor.")

    if set(via_shim) != set(claimed):
        only_run = sorted(set(via_shim) - set(claimed))
        only_code = sorted(set(claimed) - set(via_shim))
        fail("kørslen og den statiske tælling er uenige: "
             + (f"kun i kørslen {', '.join(only_run)}; " if only_run else "")
             + (f"kun i koden {', '.join(only_code)}" if only_code else ""))

    print(f"  kildevejen og hjulet er enige: {len(via_shim)}/{EXPECTED} regler "
          f"på samme dokument")


def check_readme_documents_it() -> None:
    """Hvis README'en anviser kildevejen, skal den være den der køres her."""
    if not README.is_file():
        fail(f"{README} mangler")

    text = README.read_text(encoding="utf-8")
    if "python scan.py" not in text:
        print(" SPRUNGET OVER: README'en anviser ikke længere `python scan.py`, "
              "så der er ingen kildevej at dømme. Omdirigeringen er stadig "
              "testet ovenfor.")
        return

    if "cd scanner" not in text:
        fail("README'en siger `python scan.py` uden at bede om `cd scanner`. "
             "Kommandoen virker kun fra `scanner/`, så enten skal linjen have "
             "`cd scanner` med, eller den skal pege på rodniveauet.")

    print(f"  README'en anviser kildevejen, og den er den der blev kørt")


def main() -> int:
    check_shim_is_redirect()
    check_source_path()
    check_readme_documents_it()
    print(f"test_scanner_core_redirect OK: kildevejen kører de {EXPECTED} "
          f"regler, der bygger — ikke de 16 der lå i filen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
