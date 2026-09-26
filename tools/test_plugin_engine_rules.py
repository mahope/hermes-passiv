#!/usr/bin/env python3
"""Kør pluginens egen PHP-motor og kræv, at den fyrer alle 22 regler.

Baggrunden er opgave 85. Det publicerede zip var en ældre build af
`scanner/wp-plugin/`, og siden talte 16 regler — rigtigt for den fil kunden
hentede, men seks bag den kode vi vedligeholder. Intet i porten kunne se det:
`check_rule_claims.py` læste **den publicerede zip**, så den målte motoren
korrekt og fandt 16, og 16 var altså ikke en fejl. Den var en *fuldstændig*
måling af det forkerte produkt.

Derfor må denne test ikke læse kode. Den indlæser motoren fra det publicerede
arkiv, kalder `scan_html()` på `tools/fixtures/eaa_engine_all_rules.html` og
kræver, at alle 22 regler fyrer. Tre ting skal holde samtidig:

1. **Arkivet er i sync med kilden.** Ellers måler vi en motor, der ikke er den
   vi udgiver, og portens 22 siger om kildens motor.
2. **Alle 22 fyrer.** Ikke "mindst 22" og ikke "22 forskellige id'er i
   koden" — 22 *fund* i et *dokument*. En regel, der er kodet men aldrig kan
   fyre, er en regel kunden ikke har.
3. **Den dynamiske mængde er den statiske.** De id'er der fyrer, skal være
   præcis de id'er `check_rule_claims.py` tæller. Uden dette krydscheck kan de
   to blive enige om et forkert tal, og en port der kun er en port.

Uden `php` springes kørslen over — med en synlig besked, ikke med en stille
grøn linje. Resten af testen (1 og 3) kræver ikke PHP og kører alligevel, for
så en maskine uden PHP stadig fanger et ude af sync arkiv.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from check_rule_claims import (  # noqa: E402
    PLUGIN_ENGINE_IN_ZIP,
    py_engine_ids,
)

ZIP_PATH = REPO / "site" / "eaa-compliance-scanner.zip"
SOURCE_DIR = REPO / "scanner" / "wp-plugin" / "eaa-compliance-scanner"
PROBE = REPO / "tools" / "plugin_engine_probe.php"
FIXTURE = REPO / "tools" / "fixtures" / "eaa_engine_all_rules.html"

EXPECTED = 22


def fail(msg: str) -> None:
    print(f"FEJL: {msg}")
    raise SystemExit(1)


def check_zip_in_sync() -> list[str]:
    """(1) Det publicerede arkiv skal være den kode vi vedligeholder."""
    r = subprocess.run([sys.executable, "tools/build_plugin_zip.py", "--check"],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        fail(r.stdout.strip() or r.stderr.strip())

    with zipfile.ZipFile(ZIP_PATH) as zf:
        names = sorted(n for n in zf.namelist() if not n.endswith("/"))
    return names


def check_claims_say(expected: int) -> None:
    """Pluginens egne dokumenter skal nævne det samme tal som porten.

    `engine.php:7`, `README.txt:3` og pluginens WordPress-header sagde hver
    deres egen ting (21, 15, 15), og alle tre lå i det arkiv kunden hentede.
    De er ikke kosmetik: headeren er den tekst WordPress viser i
    plugin-katalogen, og `(15 rules)` stod i den skærm kunden så.
    """
    engine = (SOURCE_DIR / "engine.php").read_text(encoding="utf-8")
    readme = (SOURCE_DIR / "README.txt").read_text(encoding="utf-8")
    main = (SOURCE_DIR / "eaa-compliance-scanner.php").read_text(encoding="utf-8")

    # Ét tal i hver kilde, kunne være et hvilket som helst andet sted i filen.
    docblock = re.search(r"Act: (\d+) rules", engine)
    if not docblock:
        fail("engine.php's docblock nævner ikke længere et regeltal — "
             "fjern den, eller skriv hvorfor motoren ikke har et fast antal")
    if int(docblock.group(1)) != expected:
        fail(f"engine.php's docblock siger {docblock.group(1)} regler, "
             f"motoren kører {expected}")

    for name, src, pattern in (
        ("README.txt", readme, r"WCAG 2\.1 AA subset, (\d+) rules"),
        ("eaa-compliance-scanner.php", main, r"WCAG 2\.1 AA subset, (\d+) rules"),
        ("eaa-compliance-scanner.php (skærmen)", main,
         r"\((\d+) rules\)\. Runs entirely"),
    ):
        m = re.search(pattern, src)
        if not m:
            fail(f"{name} nævner ikke længere et regeltal")
        if int(m.group(1)) != expected:
            fail(f"{name} siger {m.group(1)} regler, motoren kører {expected}")

    ver = re.search(r"const EAA_SCANNER_VERSION = '([^']+)'", main)
    header = re.search(r"\* Version:\s*(\S+)", main)
    if not ver or not header:
        fail("plugin-headeren mangler Version eller EAA_SCANNER_VERSION")
    if ver.group(1) != header.group(1):
        fail(f"WordPress-headeren siger version {header.group(1)}, men "
             f"konstanten er {ver.group(1)} — de to er dem kunden ser")


def run_engine() -> list[str] | None:
    """(2) Kør motoren fra det publicerede arkiv. `None` hvis PHP mangler."""
    php = shutil.which("php")
    if php is None:
        print(" SPRUNGET OVER: `php` findes ikke i PATH, så motoren blev ikke "
              "kørt. Resten af testen kørte. Gaten måler fortsat de 22 fra "
              "koden, men ingen her bekræfter dem ved en kørsel.")
        return None

    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(ZIP_PATH) as zf:
            zf.extract(PLUGIN_ENGINE_IN_ZIP, tmp)
        engine = Path(tmp) / PLUGIN_ENGINE_IN_ZIP
        r = subprocess.run([php, str(PROBE), str(engine), str(FIXTURE)],
                           cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"motoren kunne ikke køre: {r.stderr.strip() or r.stdout.strip()}")
    try:
        return json.loads(r.stdout.strip())["rule_ids"]
    except (ValueError, KeyError) as exc:
        fail(f"motorens svar var ikke JSON med rule_ids ({exc}): {r.stdout!r}")


def main() -> int:
    if not ZIP_PATH.is_file():
        fail(f"{ZIP_PATH} mangler")

    names = check_zip_in_sync()
    print(f"  arkiv i sync med kilden: {', '.join(n.split('/')[-1] for n in names)}")

    claimed = py_engine_ids(SOURCE_DIR / "engine.php")
    if len(claimed) != EXPECTED:
        fail(f"kilden har {len(claimed)} regel-id'er, porten forventer {EXPECTED}")
    check_claims_say(EXPECTED)

    fired = run_engine()
    if fired is None:
        print(f"test_plugin_engine_rules: OK (delvis — ingen PHP)")
        return 0

    if len(fired) != EXPECTED:
        missing = sorted(set(claimed) - set(fired))
        fail(f"motoren fyrer {len(fired)} regler, porten hævter {EXPECTED}. "
             + (f"Mangler i kørslen: {', '.join(missing)}." if missing
                else "Der fyrer regler porten ikke kender."))

    # (3) Den dynamiske mængde skal være præcis den statiske. Uden dette kan de
    # to være enige om et forkert tal, og porten er da ingen prøve.
    if set(fired) != set(claimed):
        only_run = sorted(set(fired) - set(claimed))
        only_code = sorted(set(claimed) - set(fired))
        fail("motoren og den statiske tælling er uenige: "
             + (f"kun i kørslen {', '.join(only_run)}; " if only_run else "")
             + (f"kun i koden {', '.join(only_code)}" if only_code else ""))

    print(f"test_plugin_engine_rules OK: {len(fired)}/{EXPECTED} regler fyrer "
          f"på den publicerede motor, og de er præcis de {EXPECTED} porten tæller")
    return 0


if __name__ == "__main__":
    sys.exit(main())
