"""scanner_core.py — omdirigering til den motor der bygger.

Denne fil var en 520 linjer lang kopi af scanneren med **16 regler**, mens
`pip install eaa-scanner`, npm-CLI'en og desktop-appen kører de **22** i
`scanner/packaging/eaa_scanner/core.py`. De to filer var ens i API og
forskellige i indhold, så de kunne ikke vedligeholdes sammen.

Det var ikke død kode. `site/downloads/eaa-scanner-README.md` — den README
kunden henter — siger:

    git clone <this repo> && cd scanner
    python scan.py https://example.com

Den vej gik gennem `scan.py` → denne fil → 16 regler, så en kunde der fulgte
README'en fik seks færre regler end `pip install` på den *samme* side. Målt på
`tools/fixtures/eaa_engine_all_rules.html`: 16 her, 22 i hjulet.

Derfor er der nu ingen motor her. Denne fil indlæser den der bygger, så
kildevejen og installationsvejen er den samme kode og det samme tal. Den
publicerede API er uændret, så `scan.py` og `scan_pro.py` virker som før.

Hvis du læser en regel og vil vide hvor den bor, er svaret
`scanner/packaging/eaa_scanner/core.py` — det er den fil hjulet bygges af.
"""

import os
import sys

_PACKAGING = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "packaging")
if _PACKAGING not in sys.path:
    sys.path.insert(0, _PACKAGING)

from eaa_scanner.core import (  # noqa: E402,F401
    Finding,
    contrast_ratio,
    crawl_site,
    extract_links,
    scan_html,
    scan_url,
)

__all__ = [
    "Finding",
    "contrast_ratio",
    "crawl_site",
    "extract_links",
    "scan_html",
    "scan_url",
]
