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

Porten dømmer derfor tre ting:

1. **Ingen kopi.** Regelens linjer må kun findes i `net.js`. En kopi uden for er
   et fund, uanset at den er rigtig — den er den næste at drifte fra.
2. **`net.js` er hel.** Den skal stadig rumme reglen og begge funktioner, ellers
   er porten grøn ved at slette kernen i stedet for at bruge den.
3. **Ingen klient uden omkring kernen.** En fil i `site/` der *kaldet* en af
   vores egne worker-ruter skal gå gennem `NET.ask`/`NET.postJSON`, med en
   navngiven undtagelsesliste for de der endnu ikke er flyttet.

   Dom 1 og 2 dømmer *kopier af reglen*. De dømmer ikke det dejligheden her
   handlede om: `book-lead.js` var grøn hos dom 1 med et blindt `res.json()`
   skrevet i egen hånd, fordi porten ledte efter en kopi af reglen og filen
   ikke havde en. Reglen *manglede* uden at porten kunne se det. Dom 3 ser
   kaldet i stedet for teksten omkring det.

   Dommen måles på **kald**, ikke på nævn: `fetch('/api/…')` og
   `NET.postJSON('/api/…')` i `<script>`-kode. Ruterne læses fra `_worker.js`es
   egen dispatch, så porten ikke kan holde en liste ved siden af den, der
   rister — samme fejl som de fem håndskrevne tal i kvotetabellen. To ruter er
   undtaget af selve dommen, hver med sin grund: `/api/track` er en beacon der
   skal aldrig kaste, og `/api/stripe-webhook` er Stripe *til* os, ikke en
   klient der kan kalde den.

   `<pre>` er fjernet før kaldene søges. Det er ikke en håndrækning: to
   artikler om API'et (`/blog/html-to-markdown-api` + den danske) viser et
   `fetch('/api/clean-copy')` som **eksempel** i en `<pre>`, og en port der
   dømmer dem ville være en port folk slår fra.

Den dømmer *kun* koden, ikke prose. En artikel der viser et `curl`-kald i et
`<pre>` (`/blog/compare-two-web-pages-seo`) nævner `/api/profile` uden at være en
klient, så «nævner ruten» kan ikke være dommen — kun den brugbare kode.

    python3 tools/check_net_copies.py            # dom alle klienter
    python3 tools/check_net_copies.py --self-test # 15 kontroller
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

# === Dom 3: klienter der kalder vores egne ruter uden omkring kernen ===

# Ruterne læses fra `_worker.js`es egen dispatch, så de kan ikke komme i
# drift fra portens side. 22 ruter, målt 4/10.
DISPATCH_RE = re.compile(r"path === '(/api/[a-z/-]+)'")
# Kun `<script>`-kode. `<pre>` er fjernet først, så et **eksempel** i en artikel
# ikke dømmes som et kald — målt 4/10: de to artikler om `/api/clean-copy`
# skriver et `fetch('/api/clean-copy')` i en `<pre>`.
PRE_RE = re.compile(r"<pre\b.*?</pre>", re.S | re.I)
SCRIPT_RE = re.compile(r"<script\b[^>]*>(.*?)</script>", re.S | re.I)
# Et rute-navn i en kommentar eller et `<pre>` er ikke et kald. Kald *gennem
# kernen* er heller ikke et fund — de skal bare gå samme sted som de andre.
# Derfor er de to holdt adskilt: `rå_kald` er det dommen dømmer, `NET_BRUG_RE`
# er det den sammenligner med.
RA_KALD_RE = re.compile(r"(?:window\.)?fetch\s*\(\s*['\"`](/api/[a-z/-]+)")
NET_BRUG_RE = re.compile(r"NET\.(?:ask|postJSON|getJSON)\s*\(")

# Ruter dom 3 slet ikke dømmer, hver med sin grund.
IKKE_ET_KLIENTKALD = {
    "/api/track": "en beacon fra `track.js` — den skal aldrig kaste, fordi en "
                  "kastet fejl i en kliklytter ville tage hele siden med",
    "/api/stripe-webhook": "kaldes af Stripe til os, ikke af en klient",
}

# Navngiven undtagelsesliste: fil → de ruter den må kalde uden kernen, med en
# grund. Den er **per rute**, ikke per fil, så en undtagelsesfil der vokser en
# ny kalds rute stadig bliver rød. Grunden er derfor ikke en undskyldning men
# en regning: hver linje er en fil der endnu ikke er flyttet, og porten skriver
# dem ud i sin egen grønne udskrift, så listen ikke kan vokse i stilhed.
#
# Målt 4/10: 15 filer. Listen er derfor *ikke* længere end den skal være — den er
# bare ikke tom, og det er fordi dommen så den i ansigtet i stedet for at lade
# den ligge.
_WAITLIST = "en tilmelding i en NIS2-vurdering — ikke flyttet endnu, og det er " \
            "seks filer der skal laves på én gang"
UNDTAGELSER: dict[str, tuple[frozenset[str], str]] = {
    "nis2-check.html": (frozenset({"/api/waitlist"}), _WAITLIST),
    "nis2-check-da.html": (frozenset({"/api/waitlist"}), _WAITLIST),
    "nis2-gap-assessment.html": (frozenset({"/api/waitlist"}), _WAITLIST),
    "nis2-gap-assessment-da.html": (frozenset({"/api/waitlist"}), _WAITLIST),
    "nis2-incident-generator.html": (frozenset({"/api/waitlist"}), _WAITLIST),
    "nis2-incident-generator-da.html": (frozenset({"/api/waitlist"}), _WAITLIST),
    "compliance-ai.html": (frozenset({"/api/compliance-ai"}),
                           "ruten kaldes to gange; den her (linje 486) er et "
                           "ældre kald ved siden af NET.ask"),
    "da/compliance-ai.html": (frozenset({"/api/compliance-ai"}),
                              "ruten kaldes to gange; den her (linje 487) er et "
                              "ældre kald ved siden af NET.ask"),
    "compliance-report.html": (frozenset({"/api/license/validate", "/api/report"}),
                               "licensetjek og rapport håndterer 429/5xx i egen "
                               "wrapper, fordi siden viser kundens egen nøgle"),
    "clean-copy-api.html": (frozenset({"/api/clean-copy"}),
                            "dokumentationssiden med et levende kald i egen hånd"),
    "paid-templates.html": (frozenset({"/api/paid-files"}),
                            "read-only GET på fillisten"),
    "da/paid-templates.html": (frozenset({"/api/paid-files"}),
                               "read-only GET på fillisten"),
    "stats.html": (frozenset({"/api/stats"}),
                   "kræver brugerens eget token i en header, så kaldet kan ikke "
                   "gå gennem den delte hjælper"),
    "thanks.html": (frozenset({"/api/stripe/fulfillment"}),
                    "poller købsbekræftelsen på 202 og skal genkalde den med "
                    "eget interval — en 429 her betyder «vent endnu», ikke «stop»"),
    "bugbottle-demo.js": (frozenset({"/api/bugbottle-demo"}),
                          "demoens tre opkald uden fejlvisning"),
}


def arbejdende_ruter() -> set[str]:
    """Vores egne API-ruter, læst i `_worker.js`es dispatch."""
    tekst = (SITE / "_worker.js").read_text(encoding="utf-8")
    return set(DISPATCH_RE.findall(tekst))


def scriptkode(tekst: str, er_html: bool) -> str:
    """Koden der *kører* i siden: script-blokke, `<pre>` fjernet."""
    uden_pre = PRE_RE.sub("", tekst)
    if not er_html:
        return uden_pre
    return "\n".join(SCRIPT_RE.findall(uden_pre))


def dom_kaldere(tekst: str, sti: str, ruter: set[str], er_html: bool) -> list[str]:
    """Fund i én fil for dom 3. `er_html` afgør om script-blokke skal findes."""
    kode = scriptkode(tekst, er_html)
    kaldte = {m.group(1) for m in RA_KALD_RE.finditer(kode)
              if m.group(1) in ruter and m.group(1) not in IKKE_ET_KLIENTKALD}
    if not kaldte:
        return []
    tilladte, grund = UNDTAGELSER.get(sti, (frozenset(), ""))
    ubrugte = sorted(kaldte - tilladte)
    if not ubrugte:
        return []
    # Filen bruger kernen et andet sted, så det her er ikke en klient der
    # reglen aldrig nåede — den skal bare gå gennem kernen som alle andre.
    if NET_BRUG_RE.search(kode):
        return [f"{sti}: kalder {', '.join(ubrugte)} med egen fetch() "
                f"selv om filen bruger NET andetsteds — brug NET.ask() også her"]
    fund = [f"{sti}: kalder {', '.join(ubrugte)} uden NET.ask() — en 429 fra "
            f"serveren bliver genkaldt og koster den besøgendes kvote"]
    if grund:
        fund[0] += f" (filen står i undtagelseslisten: {grund})"
    return fund


def dom_kaldere_alle() -> list[str]:
    ruter = arbejdende_ruter()
    fund: list[str] = []
    for fil in sorted(SITE.rglob("*.html")) + sorted(SITE.rglob("*.js")):
        sti = str(fil.relative_to(SITE))
        if sti in (KERNE, "_worker.js"):
            continue
        fund.extend(dom_kaldere(fil.read_text(encoding="utf-8", errors="replace"),
                                sti, ruter, fil.suffix == ".html"))
    return fund


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
    fund.extend(dom_kaldere_alle())
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

# Dom 3: `(navn, kilde, sti, forventede fund)`. De er skrevet som hele HTML- eller
# JS-kilder, fordi dommen læser script-blokke og `<pre>` — en kilde uden `<pre>`
# ville være en test af noget andet end det, porten dømmer.
SELFTEST_KALD = [
    ("rå fetch på en af vores ruter er et fund",
     "<script>fetch('/api/compliance-scan', {method:'POST'});</script>",
     "selv.html", 1),
    ("samme kald gennem kernen er ikke et fund",
     "<script>NET.ask('/api/compliance-scan', {urls:[]});</script>",
     "selv.html", 0),
    ("et eksempel i <pre> er ikke et kald",
     "<pre><code>await fetch('/api/clean-copy', {body})</code></pre>"
     "<script>var x = 1;</script>",
     "selv.html", 0),
    ("et kald i almindelig tekst er ikke et kald",
     "<p>Kalder du <code>/api/compliance-scan</code> får du svaret her.</p>"
     "<script>var x = 1;</script>",
     "selv.html", 0),
    ("en beacon er ikke et klientkald",
     "<script>fetch('/api/track', {method:'POST', keepalive:true});</script>",
     "selv.html", 0),
    ("Strikes webhook er ikke et klientkald",
     "<script>fetch('/api/stripe-webhook', {method:'POST'});</script>",
     "selv.html", 0),
    ("en undtagelsesfil må kalde den rute den er navngivet for",
     "<script>fetch('/api/waitlist', {method:'POST'});</script>",
     "nis2-check.html", 0),
    ("en undtagelsesfil må ikke få en ny rute gratis",
     "<script>fetch('/api/waitlist');fetch('/api/compliance-scan');</script>",
     "nis2-check.html", 1),
    ("kernen andetsteds i filen er ikke en brugsletning",
     "<script>NET.ask('/api/waitlist', {email:e});"
     "fetch('/api/compliance-ai');</script>",
     "selv.html", 1),
    ("et rute-navn der ikke er i dispatchen er ikke vores",
     "<script>fetch('/api/ukendte-rute');</script>", "selv.html", 0),
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

    # Dom 3. Ruterne er `_worker.js`es egne, så seltesten ikke kan blive grøn
    # ved at opfinde en rute der ikke findes.
    ruter = arbejdende_ruter()
    for navn, kilde, sti, forventet in SELFTEST_KALD:
        fund = dom_kaldere(kilde, sti, ruter, "<script>" in kilde)
        ok = len(fund) == forventet
        fejl += 0 if ok else 1
        print(f"{'ok   ' if ok else 'FEJL '} {navn} "
              f"({len(fund)} fund, forventede {forventet})")

    total = len(SELFTEST) + len(SELFTEST_KALD)
    print(f"selvtest: {total - fejl}/{total} kontroller")
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
    # Listen skrives ud, så en ny undtagelse er en synlig linje i gaten og ikke
    # en stille vækst i portens egen kode.
    print(f"net-kopier: GRØN — reglen findes kun i {KERNE}")
    if UNDTAGELSER:
        ruter = arbejdende_ruter()
        print(f"  {len(UNDTAGELSER)} filer kalder en rute uden kernen, hver med "
              f"sin grund ({len(ruter)} ruter dømt):")
        for sti, (tilladte, grund) in sorted(UNDTAGELSER.items()):
            ubrugte = sorted(tilladte - ruter)
            note = f" — {len(ubrugte)} af dem findes ikke i dispatchen" if ubrugte else ""
            print(f"  - {sti}: {', '.join(sorted(tilladte))} — {grund}{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
