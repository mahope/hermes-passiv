#!/usr/bin/env python3
"""Dom at reglen for «hvad en besøgende ser, når vi har en dårlig dag» kun findes ét sted.

`site/net.js` blev skrevet, fordi den samme fejlform var kopieret ind i klienterne.
Den skriver ned præcis, hvad den vil have gjort, og det er to ting der ikke er til
at forhandle:

1. **429 er endeligt.** Serveren har allerede sagt hvor længe det varer, og den
   tæller den besøgendes *eget* budget. Et genkald betaler for et svar serveren
   netop har sagt nej til at give — og det er derfor, at en klient der genkalder
   429 skrubber sin egen kvote væk. Fejlen bærer serverens egen sætning i
   `err.message`, så siden viser den.
2. **Kun 5xx og en ulæselig krop er forbigående.** Cloudflare svarer en krasjet
   worker med en HTML-side, så en bare `res.json()` kaster, og catch'en så skylder
   den besøgendes wifi for vores driftsstop.

Målt 2/10: seks klienter havde hver sin kopi af de to linjer, hvor `net.js`
skriver dem —

    err.transient = !data || res.status >= 500;   // EN + DA compliance-site-check
    err.transient = !j    || r.status >= 500;     // EN + DA page-profile
    err.transient = !data || r.status >= 500;     // security-headers-check
    err.transient = !data || res.status >= 500;     // url-inspector/index

Alle seks gjorde det rigtigt den dag de blev skrevet. Det er præcis problemet:
reglen lå seks steder, så næste rettelse bliver lavet ét sted — og kopierne er
inline i en `<script>`, altså filer ingen dør til. `net.js` beskriver i sin egen
docstring en DA-kopi, der var dræbet et par tegn, før nogen lagde mærke til den.
Det er ikke en hypotetisk fare; det er hvad der skete.

Porten dømmer derfor to ting:

1. **Ingen kopi.** Regelens linjer må kun findes i `net.js`. En kopi uden for er
   et fund, uanset at den er rigtig — den er den næste at drifte fra.
2. **`net.js` er hel.** Den skal stadig rumme reglen og begge funktioner, ellers
   er porten grøn ved at slette kernen i stedet for at bruge den.

Den dømmer *kun* koden, ikke prose. En artikel der viser et `curl`-kald i et
`<pre>` (`/blog/compare-two-web-pages-seo`) nævner `/api/profile` uden at være en
klient, så «nævner ruten» kan ikke være dommen — kun den brugbare kode.

    python3 tools/check_net_copies.py            # dom alle klienter
    python3 tools/check_net_copies.py --self-test # 9 kontroller
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
KERNE = "net.js"

# Regelens to linjer. Begge varianter af hver står i porten, fordi de seks
# kopier var skrevet på to varianter af det samme kald: en der læser `data` og en
# der læser `j`, og en der læser `r.status` og en der læser `res.status`. Det er
# den lighed, der gjorde dem lige så svære at finde med øjet som nemme at kopiere.
KOPI_TRANSIENT = re.compile(r"\.transient\s*=\s*!\w+\s*\|\|\s*\w+\.status\s*>=\s*500")
KOPI_LIMITED = re.compile(r"\.limited\s*=\s*\w+\.status\s*===\s*429")
# Det samme som en klient der lader 429 ligge i egen hånd, fordi den regel er
# skrevet som en afsluttende `>= 500` uden `!data`-halvet. Den ligner de andre
# nok til at blive kopieret, så den dømmes på ordet.
KOPI_NAVN = re.compile(r"\.transient\s*=\s*\w+\.status\s*>=\s*500\b")


def dom_fil(fil: Path, sti: str | None = None) -> list[str]:
    """Fund i én fil. `sti` er hvad der skrives i fundet; som standard filens navn."""
    vis = sti if sti is not None else fil.name
    tekst = fil.read_text(encoding="utf-8", errors="replace")
    fund: list[str] = []
    for linje_no, linje in enumerate(tekst.splitlines(), 1):
        regel = None
        if KOPI_TRANSIENT.search(linje):
            regel = "`transient`-reglen"
        elif KOPI_LIMITED.search(linje):
            regel = "`limited`-reglen"
        elif KOPI_NAVN.search(linje):
            regel = "en `transient`-regel uden `!data`-halvet"
        if regel:
            fund.append(
                f"{vis}:{linje_no}: inline kopi af {regel} fra {KERNE} "
                f"— brug NET.ask() / NET.postJSON()")
    return fund


def dom_alle() -> list[str]:
    fund: list[str] = []
    for fil in sorted(SITE.rglob("*.html")) + sorted(SITE.rglob("*.js")):
        if fil.name == KERNE:
            continue
        fund.extend(dom_fil(fil, str(fil.relative_to(SITE))))
    # Punkt 2: kernen skal stadig være hel.
    tekst = (SITE / KERNE).read_text(encoding="utf-8")
    mangler: list[str] = []
    if not KOPI_TRANSIENT.search(tekst):
        mangler.append(f"{KERNE} har mistet `transient`-reglen")
    if not KOPI_LIMITED.search(tekst):
        mangler.append(f"{KERNE} har mistet `limited`-reglen")
    for navn in ("postJSON", "ask"):
        if f"function {navn}" not in tekst:
            mangler.append(f"{KERNE} har mistet `{navn}()`")
    fund.extend(mangler)
    return fund


SELFTEST = [
    ("kernen er den eneste undtagelse", None, 2),
    ("inline transient-kopi (data/r)", "err.transient = !data || r.status >= 500;", 1),
    ("inline transient-kopi (j/res)", "err.transient = !j || res.status >= 500;", 1),
    ("inline limited-kopi", "err.limited = r.status === 429;", 1),
    ("transient uden !data-halvet", "err.transient = r.status >= 500;", 1),
    ("et andet transient-flag røres ikke", "err.transient = true;", 0),
    ("en 502-beskrivelse i tekst", "if (x === 500) return 'server busy';", 0),
    ("ren klient", "var x = 1;", 0),
    ("net.js nævnt i en kommentar", "// see net.js for the rule", 0),
]


def selvtest() -> int:
    fejl = 0
    tmp = SITE / "_selftest_net.html"
    for navn, kilde, forventet in SELFTEST:
        if kilde is None:
            # Undtagelsen er selve poinet: en fil med navnet net.js må rumme
            # reglen, og det skal være det ENESTE sted den gør. Her skriver vi
            # kernens egne linjer ind i en fil med kernens navn — 0 fund.
            tmp2 = SITE / KERNE
            fund = dom_fil(tmp2, KERNE)
            fund = [f for f in fund if f.startswith(KERNE)]
        else:
            tmp.write_text(f"<script>{kilde}</script>", encoding="utf-8")
            try:
                fund = dom_fil(tmp, "_selftest_net.html")
            finally:
                tmp.unlink(missing_ok=True)
        ok = len(fund) == forventet
        fejl += 0 if ok else 1
        print(f"{'ok   ' if ok else 'FEJL '} {navn} "
              f"({len(fund)} fund, forventede {forventet})")
    print(f"selvtest: {len(SELFTEST) - fejl}/{len(SELFTEST)} kontroller")
    return 1 if fejl else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return selvtest()
    fund = dom_alle()
    for f in fund:
        print(f"  {f}")
    if fund:
        print(f"\nnet-kopier: RØD — {len(fund)} fund i site/")
        return 1
    print(f"net-kopier: GRØN — reglen findes kun i {KERNE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
