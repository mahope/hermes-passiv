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
   egen dispatch — **begge** former, fordi den har to: `path === '/api/…'` og
   `path.startsWith('/api/download/')` — så porten ikke kan holde en liste ved
   siden af den, der rister. Samme fejl som de fem håndskrevne tal i
   kvotetabellen, og som fundet 4/10: kun den lig form blev læst, så den 23. rute
   var usynlig for porten.

   Et kald der **ikke** findes i dispatchen er også et fund. En relativ
   `/api/…` i vores egen side er enten vores rute eller en 404 — der er ingen
   tredjepart på vores domæne — så det er en død vej, ikke en fremmed rute.
   Undtagelseslisten dømmes også: en rute i den der ikke længere findes i
   dispatchen er et fund, fordi den ellers lukker et kald porten burde dømme.

   To ruter er undtaget af selve dommen, hver med sin grund: `/api/track` er en
   beacon der skal aldrig kaste, og `/api/stripe-webhook` er Stripe *til* os,
   ikke en klient der kan kalde den.

   `<pre>` er fjernet før kaldene søges. Det er ikke en håndrækning: to
   artikler om API'et (`/blog/html-to-markdown-api` + den danske) viser et
   `fetch('/api/clean-copy')` som **eksempel** i en `<pre>`, og en port der
   dømmer dem ville være en port folk slår fra.

Den dømmer *kun* koden, ikke prose. En artikel der viser et `curl`-kald i et
`<pre>` (`/blog/compare-two-web-pages-seo`) nævner `/api/profile` uden at være en
klient, så «nævner ruten» kan ikke være dommen — kun den brugbare kode.

    python3 tools/check_net_copies.py            # dom alle klienter
    python3 tools/check_net_copies.py --self-test # 30 kontroller
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
# drift fra portens side. 23 ruter, målt 5/10.
#
# Dispatchen har to former, og kun den første blev læst: 22 ruter med
# `path === '/api/…'` og **én** med `path.startsWith('/api/download/')`
# (`site/_worker.js:286`). Den 23. er `GET /api/download/<token>/<fil>` — en rigtig,
# klient-rækbar rute der leverer betalte filer — og intet `path ===`-mønster kan
# se den. Fund 4/10: en `fetch('/api/download/tok/x.pdf')` i en vilkårlig side var
# **GRØN**, fordi porten kun kendte de 22. Samme fejlklasse som
# `stripe_catalog.json` og som de otte ratchet-ankre: en afledt liste der er
# præcis så komplet som sit mønster.
#
# Præfiks-mønsteret kræver et navn efter `/api/`, så catch-allen
# `path.startsWith('/api/')` (der svarer 404) ikke kan blive en rute.
ROUTE_LIG_RE = re.compile(r"path === '(/api/[a-z/-]+)'")
ROUTE_PRAEFIX_RE = re.compile(r"path\.startsWith\('(/api/[a-z][a-z/-]*/)'\)")
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
# ny kalds rute stadig bliver rød. Grundene er derfor ikke en undskyldning men
# en regning: hver linje er et kald kernen endnu ikke kan tage, og porten
# skriver dem ud i sin egen grønne udskrift, så listen ikke kan vokse i stilhed.
#
# Målt 4/10: 15 filer, heraf de **seks `nis2-*`** på `/api/waitlist` og de to
# `compliance-ai`. 4/10 er de otte flyttet: `nis2-*` kalder nu `NET.ask` med to
# forsøg, og `compliance-ai` spørger om nøglens tilstedeværelse med
# `NET.getJSON`. Kun det der *ikke* kan gå gennem kernen står her — filer der
# kræver et token i en header, poller på 202, eller viser kundens egen nøgle.
UNDTAGELSER: dict[str, tuple[frozenset[str], str]] = {
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
    "track.js": (frozenset({"/api/client-error"}),
                 "en fejlrapport må ikke vise brugeren en fejlmeddelelse, og den "
                 "må ikke genkaldes ved 429 — den skal bare forsvinde. Den "
                 "går gennem `sendBeacon` i 99 % af kaldene, fordi det er det "
                 "eneste der kan sendes fra en side der lige er gået i styker, "
                 "og kernen ville desuden vise serverens egen sætning midt i "
                 "et værktøj. Dæmpningen ligger i stedet i klienten (højst tre "
                 "pr. side, samme fejltekst én gang) og i ruten, der svarer 429 "
                 "uden at skrive til Sentry."),
}

# Kald der ikke findes i dispatchen er **ikke** vores ruter, så de kan heller
# ikke gå gennem kernen. Målt 5/10 er der præcis ét af dem i `site/`, og det er
# et dynamisk bygget præfiks: `clean-copy-tool.html` skriver
# `'/api/license/' + endpoint`, fordi den kalder fem licensendepunkter med samme
# krop. Det er den eneste grund den står her — alt andet er en 404 for læseren,
# og en 404 der ser ud som et kald er præcis den fejl porten skal finde.
UKENDTE_UNDTAGELSER: dict[str, str] = {
    "clean-copy-tool.html": (
        "dynamisk rute: `'/api/license/' + endpoint` kaler de fem "
        "licensendepunkter med samme krop, så porten kan ikke læse dem fra "
        "kilden. Licensemodulets egen `decide()` holder den 7-dages cache og "
        "viser serverens egen sætning, så kaldet skal ikke gå gennem kernen"
    ),
}


def arbejdende_ruter() -> set[str]:
    """Vores egne API-ruter, læst i `_worker.js`es dispatch — begge former."""
    tekst = (SITE / "_worker.js").read_text(encoding="utf-8")
    return set(ROUTE_LIG_RE.findall(tekst)) | set(ROUTE_PRAEFIX_RE.findall(tekst))


def route_daekker(kald: str, ruter: set[str]) -> bool:
    """Kalder et kald en af vores ruter? Præfiks-ruter dækker deres underruter."""
    return any(kald == rute or kald.startswith(rute) for rute in ruter)


def scriptkode(tekst: str, er_html: bool) -> str:
    """Koden der *kører* i siden: script-blokke, `<pre>` fjernet."""
    uden_pre = PRE_RE.sub("", tekst)
    if not er_html:
        return uden_pre
    return "\n".join(SCRIPT_RE.findall(uden_pre))


def dom_kaldere(tekst: str, sti: str, ruter: set[str], er_html: bool) -> list[str]:
    """Fund i én fil for dom 3. `er_html` afgør om script-blokke skal findes."""
    kode = scriptkode(tekst, er_html)
    fund: list[str] = []
    kaldte: set[str] = set()
    ukendte_grund = UKENDTE_UNDTAGELSER.get(sti)
    for m in RA_KALD_RE.finditer(kode):
        kald = m.group(1)
        if kald in IKKE_ET_KLIENTKALD:
            continue
        if not route_daekker(kald, ruter):
            # En relativ `/api/…` i vores egen side er enten vores rute eller en
            # 404 — der er ingen tredjepart på vores domæne. Så et kald der ikke
            # findes i dispatchen er en død vej, ikke en undtagelse.
            if ukendte_grund is None:
                fund.append(f"{sti}: kalder {kald} som ikke findes i "
                            f"{SITE.name}/_worker.js — kaldet svarer 404 for "
                            f"læseren (kræver en grund i UKENDTE_UNDTAGELSER)")
            continue
        if kald not in kaldte:
            kaldte.add(kald)
    if not kaldte:
        return fund
    tilladte, grund = UNDTAGELSER.get(sti, (frozenset(), ""))
    ubrugte = sorted(kaldte - tilladte)
    if not ubrugte:
        return fund
    # Filen bruger kernen et andet sted, så det her er ikke en klient der
    # reglen aldrig nåede — den skal bare gå gennem kernen som alle andre.
    if NET_BRUG_RE.search(kode):
        fund.append(f"{sti}: kalder {', '.join(ubrugte)} med egen fetch() "
                    f"selv om filen bruger NET andetsteds — brug NET.ask() også her")
    else:
        fund.append(f"{sti}: kalder {', '.join(ubrugte)} uden NET.ask() — en 429 "
                    f"fra serveren bliver genkaldt og koster den besøgendes kvote")
        if grund:
            fund[-1] += f" (filen står i undtagelseslisten: {grund})"
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


def dom_undtagelser(undtagelser: dict[str, tuple[frozenset[str], str]],
                    ruter: set[str]) -> list[str]:
    """Undtagelser der døjer: en rute der ikke længere findes i dispatchen.

    Undtagelseslisten er håndskrevet, så den kan komme i drift fra portens side
    — i hver sin retning. Ruten forsvinder (en handler bliver omdøbt), så læseren
    bliver rød uden at have kaldet noget; eller ruten hedder noget andet, så den
    døj undtagelse lukker et kald porten burde have dømt. Før var det kun en note
    i grøn-udskriften, og fund-kravet om at listen er synlig gjorde den *mere*
    troværdig uden at gøre den rød. Derfor er det et fund nu.
    """
    return [
        f"{sti}: undtagelsen {rute} findes ikke i _worker.js — reglen døjer, "
        f"eller ruten hedder noget andet"
        for sti, (tilladte, _) in sorted(undtagelser.items())
        for rute in sorted(tilladte - ruter)
    ]


def dom_alle() -> list[str]:
    fund: list[str] = []
    for fil in sorted(SITE.rglob("*.html")) + sorted(SITE.rglob("*.js")):
        if fil.name == KERNE:
            continue
        fund.extend(dom_fil(fil, str(fil.relative_to(SITE))))
    fund.extend(dom_kaldere_alle())
    fund.extend(dom_undtagelser(UNDTAGELSER, arbejdende_ruter()))
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
# De to undtagelses-cases bruger `paid-templates.html`, fordi den stadig
    # står i listen. De kørte før på `nis2-check.html`, som holdt sit kald uden
    # kernen indtil 4/10 — en fil der *ikke* er undtagelse mere ville gøre dem
    # grønne af den forkerte grund.
    ("en undtagelsesfil må kalde den rute den er navngivet for",
     "<script>fetch('/api/paid-files');</script>",
     "paid-templates.html", 0),
    ("en undtagelsesfil må ikke få en ny rute gratis",
     "<script>fetch('/api/paid-files');fetch('/api/compliance-scan');</script>",
     "paid-templates.html", 1),
    # Den anden halvdel af den samme flytning: en fil der har været undtagelse
    # og nu går gennem kernen, må blive rød hvis sit gamle rå kald kommer tilbage.
    ("en flyttet fil må ikke få sit gamle rå kald tilbage",
     "<script>fetch('/api/waitlist', {method:'POST'});</script>",
     "nis2-check.html", 1),
    ("kernen andetstedes i filen er ikke en brugsletning",
     "<script>NET.ask('/api/waitlist', {email:e});"
     "fetch('/api/compliance-ai');</script>",
     "selv.html", 1),
    ("et rute-navn der ikke findes i dispatchen er en død vej",
     "<script>fetch('/api/ukendte-rute');</script>", "selv.html", 1),
    # Fundet 4/10, målt ved mutation: en `fetch('/api/download/tok/x.pdf')` i en
    # vilkårlig side var GRØN, fordi portens rute-mønster kun kendte `path ===`
    # og `/api/download/` dispatches med `startsWith`. Den her kontrol er den
    # mutation som gør det umuligt at gentage.
    ("en præfiks-dispatchet rute dømmes også",
     "<script>fetch('/api/download/tok/x.pdf');</script>", "selv.html", 1),
    # Undtagelsen for det dynamiske licenspræfiks er navngiven, så den er ikke
    # bare grøn af den forkerte grund: i en anden fil er det samme kald et fund.
    ("et dynamisk rute-præfiks må stå med sin grund",
     "<script>fetch('/api/license/' + e);</script>", "clean-copy-tool.html", 0),
    ("et dynamisk rute-præfiks i en anden fil er et fund",
     "<script>fetch('/api/license/' + e);</script>", "selv.html", 1),
]

# Dom 3b: selve undtagelseslisten må ikke døje. Den er håndskrevet, så den kan
# komme i drift fra portens side, og det var en note før det blev et fund.
SELFTEST_UNDTAGELSER = [
    ("en undtagelse med en rute der ikke findes er et fund",
     {"selv.html": (frozenset({"/api/compliance-scan", "/api/flyt-et-sted-hen"}),
                    "grund")}, 1),
    ("en undtagelse hvis ruter alle findes er grøn",
     {"selv.html": (frozenset({"/api/compliance-scan"}), "grund")}, 0),
]

# Ruterne læses fra kilden, så selvtesten skal kunne bevise at BEGGE
# dispatch-former er læst — ellers ville den grønne præfiks-kontrol ovenfor være
# grøn af den forkerte grund, præcis som fundet 4/10 var.
SELFTEST_ROUTE = [
    ("en lig rute dækkes", "/api/compliance-scan", True),
    ("en præfiks-rute dækker sin underrute", "/api/download/tok/x.pdf", True),
    ("en præfiks-rute dækker sig selv", "/api/download/", True),
    ("et kald der ikke findes dækkes ikke", "/api/ukendte-rute", False),
    ("catch-allen '/api/' er ikke en rute", "/api/", False),
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

    for navn, undtagelser, forventet in SELFTEST_UNDTAGELSER:
        fund = dom_undtagelser(undtagelser, ruter)
        ok = len(fund) == forventet
        fejl += 0 if ok else 1
        print(f"{'ok   ' if ok else 'FEJL '} {navn} "
              f"({len(fund)} fund, forventede {forventet})")

    for navn, kald, forventet in SELFTEST_ROUTE:
        fund = 1 if route_daekker(kald, ruter) else 0
        ok = fund == forventet
        fejl += 0 if ok else 1
        print(f"{'ok   ' if ok else 'FEJL '} {navn} ({fund}, forventede {forventet})")

    total = (len(SELFTEST) + len(SELFTEST_KALD) + len(SELFTEST_UNDTAGELSER)
             + len(SELFTEST_ROUTE))
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
              f"sin grund ({len(ruter)} ruter dømt, begge dispatch-former):")
        for sti, (tilladte, grund) in sorted(UNDTAGELSER.items()):
            print(f"  - {sti}: {', '.join(sorted(tilladte))} — {grund}")
    if UKENDTE_UNDTAGELSER:
        print(f"  {len(UKENDTE_UNDTAGELSER)} filer kalder en rute der ikke findes "
              f"i dispatchen, hver med sin grund:")
        for sti, grund in sorted(UKENDTE_UNDTAGELSER.items()):
            print(f"  - {sti}: {grund}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
