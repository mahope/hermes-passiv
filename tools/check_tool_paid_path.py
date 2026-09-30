#!/usr/bin/env python3
"""Rangér **værktøjssider** efter manglende betalt vej, og gør listens tilgængelig.

Baggrund (opgave 3, 30. september 2026): fire iterationer i træk rettede én
betalt vej ad gangen på en værktøjsside, og alle fire fandt den *ved at læse
trafikken i hovedet på den enkelte iteration*:

    6a01d8a  /text-on-image-checker      (bloggen der sender folk videre til den)
    66172a0  otte gratis tjek            (compliance-ai, cookie-check, …)
    ff32199  lagringsløfter på tretten sider

`check_article_paid_path.py` dømmer artiklerne, og dens dom 6 dømmer
ikke-artikler **kun når de har målte besøg** (`page_no_button()` kræver
`visits`). Det er den rigtige regel for *dom 6*, fordi dom 6 handler om
købsknapper på sider med læsere. Men som følge heraf ligger hele værktøjssiden
uden for portens dom: målt i dag er **43** publicerede værktøjssider uden
betalt vej, og ingen af dem har besøg i nogen rapport, fordi `/api/stats`
svarer 401 siden uge 37 (❓ `STATS_TOKEN`). Dom 6 kan derfor aldrig have set
dem — ikke fordi de er forsøgt, men fordi dens tærskel er besøg.

Målt 30/9 på de **104** ruter i `tools/route_inventory.json` der hverken er
artikler eller forsider: 3 har ingen fil i `site/` (`/bulk-url-checker`,
`/security-headers-checker`, `/tools` — de serveres som 404), 1 ligger på
`bugbottle.dev` som ikke udgives (❓), 0 er delte af flere domæner, og af de
**100** der dømmes har **42** ingen betalt vej. Øverst på listen står
`/books/compliance-bundle` med 199 indgående links og `/da/compliance-ai` med
97 — to sider der hver især har læsere og ingen vej.

**Reglerne er skrevet som målinger, ikke som navnelister**, fordi de syv
forudgående fejl i denne familie alle var en hjemlavet læsning der så *én*
halvdel af verdenen:

1. **Delte læsere, ingen hjemlavet.** `paid_links()`, `knap_links()`,
   `inbound_counts()`, `traffic_source()`, `route_domain_map()` og
   `content_region()` importeres fra `check_article_paid_path` — de er samme
   filers læsere, og to læsere giver to sandheder der kan glide fra hinanden.
   Sådan opstod tre af fejlene i denne familie. Derfor importeres også de to
   interne hjælpere, `_page_file` og `_visits_by_route`, med nyt navn i stedet
   for at skrive dem om: en omdøbning her ville være en *ny* læsning.

2. **Ruten er den på webserveren.** Samme `route_of()`/`_page_file()` som
   artikelporten, så `index.html` er mappens rute og `/da/` skrives uden
   skråstreg. Målt 30/9: en rå læsning af filnavnet klassificerede den danske
   forside som en almindelig side, og dom 6 dømmede den med 31 målte besøg.

3. **Forsider er chrome, ikke værktøj.** Undtagelsen er artikelportens
   `frontpage_routes()`, som er *afledt* af build-manifestet — ikke en
   håndlavet liste, der kan falde tilbage til `/da/` med skråstreg.

4. **Artikler er ikke værktøjssider.** En artikel uden vej er
   `check_article_paid_path.py`s blind-liste, ikke denne ports. Ellers ville
   de to ringer overlappe, og hver især se en del af fejlen.

**Porten dømmer tre ting, og alle tre kan blive røde:**

- En værktøjsside **uden** betalt vej som ikke står i
  `tools/tool_paid_path_blind.json` er en ny blind værktøjsside.
- En linje i listen der **har** fået en betalt vej er en død linje. Listen er
  en *ratchet*: den må kun krympe.
- En betalt vej der **stod på siden ved målingen og ikke gør mere** er en
  tilbagefaldet side — se `path_problems()` og
  `tools/tool_paid_path_ratchet.json`. Dette er den tredje dom, og den er den
  der fanger mutationen målingen 30/9 ikke kunne: en revert der ramte
  `All books →` i stedet for pro-note-linket efterlod siden med *én* betalt
  vej, så de to domme ovenfor var begge grønne, selv om siden havde byttet om
  destinationerne.

Ruter på et domæne der ikke står i deploy-matricen måles og skrives i
udskriften, men dømmes ikke — samme regel som dom 4 og dom 7 i artikelporten,
fordi ❓-et om `bugbottle.dev` er en beslutning og ikke en fejl. Ruter uden
fil i `site/` måles på ruten og siges det; de er 404, så de har ingen købsknap
at miste. Begge former samles i `judged()`.

**Syntetiske rapporter kan aldrig læses som en kundes besøg.** Selvtesten i
`check_article_paid_path.py` skriver sine rapporter i et midlertidigt
bibliotek, men det er kun en aftale mellem to filer. Her er det en *regel*:
`traffic_rows()` springer over enhver rapport med `"synthetic": true` i
topniveauet og **navngiver** den. Uden den kunne en syntetisk rapport med
opdigtede tal blive den højest rangerede "måling" i portens egen udskrift —
altså præcis det tal, der næste iteration citerer som besøg. Selftestens
kontrol 9 dømmer det, og kontrol 9b er mutationen der viser at porten
*uden* reglen gør præcis det.

    python3 tools/check_tool_paid_path.py             # rangliste + dommene
    python3 tools/check_tool_paid_path.py --quiet     # kun dommene
    python3 tools/check_tool_paid_path.py --limit 60
    python3 tools/check_tool_paid_path.py --write --force
    python3 tools/check_tool_paid_path.py --self-test

`--write` skriver **begge** filer fra samme måling, så de aldrig kan beskrive
to forskellige øjeblikke: `tool_paid_path_blind.json` (siderne uden vej) og
`tool_paid_path_ratchet.json` (destinationerne hver side lå på). Uden
`--force` nægtes skrivningen, hvis en målt vej skal forsvinde — ellers kunne
ratcheten frigives ved at køre `--write`, og så er den ikke en ratchet.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

# Regel 1: delte læsere. Importen sker efter `sys.path.insert`, fordi
# `check_article_paid_path` selv indsætter `tools/` og roden.
import check_article_paid_path as A  # noqa: E402

# De to interne hjælpere importeres med nyt navn i stedet for at skrives om.
# Begrundelsen står i regel 1: en ny læsning af samme fil er en ny sandhed.
page_file = A._page_file            # filen bag en rute, `index.html` = mappens rute
visits_by_route = A._visits_by_route  # trafiknøgle uden skråstreg i begge ender

SITE = A.SITE
CATALOG = A.CATALOG
INVENTORY = A.INVENTORY
REPORTS = A.REPORTS
BLIND = ROOT / "tools" / "tool_paid_path_blind.json"
# Ratcheten over de betalte veje hver side havde, da den blev målt. Se
# `path_problems()`.
RATCHET = ROOT / "tools" / "tool_paid_path_ratchet.json"
BUILD = ROOT / "build_sites.py"

# Navnet på den erklæring, en side kan bære om at den intet sælger. Den er
# kort, så den ikke kan forveksles med en rigtig bruger-meta, og den starter
# med `x-`, fordi den ikke er en standardegenskab ved HTML.
DECL_NAME = "x-no-paid-path"


class RatchetFejl(RuntimeError):
    """Ratchetfilen kan ikke læses som en måling — aldrig som "ingen linjer"."""


# --------------------------------------------------------------------------
# To klasser der er målt, ikke navngivet
# --------------------------------------------------------------------------
def chrome_url_routes(build: Path = BUILD) -> tuple[dict[str, str], str]:
    """(`rute` →grund) for de ruter bygget selv erklærer som chrome-URL.

    **Opgave 12, 30/9: porten beder `/privacy` og `/terms` om en købsknap.**
    Begge stod på blindlisten med 0 indgående sider, fordi porten rangerer dem
    som værktøjssider. En købsknap på en privatlivspolitik ville være skadelig,
    så de skal *ikke* have en — men de må heller ikke blive stående i listen,
    fordi så "løser" en senere iteration dem med en note der løber.

    Derfor skelner porten nu mellem en værktøjsside og en side der er **chrome**,
    og chrome-grunden læses i byggens egen chrome-konfiguration: `ctx`-blokken
    i `apply_shell` tildeler `privacy_url` og `terms_url` (og `support_url`), og
    de er præcis de ruter builden hænger i **hver** sides footer. Målt 30/9 på
    `build_sites.py:979-981` giver det fire ruter: `/privacy`, `/terms`,
    `/support` og `/da/support`.

    **Hvorfor ikke en navneliste.** De forudgående fejl i denne familie var
    hjemlavede læsninger der så én halvdel af verdenen (regel 1 i docstringen).
    En liste med `/privacy` i porten ville være nøjagtig den fejl igen: den ville
    være sand, indtil builden flytter footeren, og så ville den tie stille. Her
    kan svaret ikke blive nyt på en måde porten ikke ser — en ny `*_url` i
    `ctx` giver automatisk en ny rute, og en flyttet footer fjerner den igen.

    Kun `*_url`-nøgler tages, og kun de rod-relative strenge i deres værdi:
    `/search/` (`search_url=search_url`, et variabelnavn) og `/issues`
    (`report_url`, en GitHub-sti) er dermed ikke med. Den anden halvdel af
    hver værdi er den absolutte `https://mahope.tools/…`-gren, som ikke er en
    rute i dette domæne.

    Returnerer fejlteksten i anden tuple, fordi en byggefil der ikke kan læses
    er **ikke** det samme som "der er ingen chrome-ruter": det første er en
    fejl porten skal råbe om, det andet er et svar.
    """
    try:
        src = build.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, f"kan ikke læse {build.name}: {exc}"
    linjer = src.splitlines()
    start = next((n for n, linje in enumerate(linjer) if "ctx = dict(" in linje), None)
    if start is None:
        return {}, (f"{build.name} har ingen `ctx = dict(`-blok længere; "
                    "porten kan ikke læse hvilke ruter bygget hænger i "
                    "footeren, så den kan heller ikke vide hvad der er chrome")
    # Blokken slutter på den første linje der er helt `)` eller `),` — samme
    # form som `ctx`-linjen starter på, altså `dict(...)` på flere linjer.
    dybde = 0
    slut = None
    for n in range(start, len(linjer)):
        for tegn in linjer[n]:
            if tegn == "(":
                dybde += 1
            elif tegn == ")":
                dybde -= 1
                if dybde == 0:
                    slut = n
                    break
        if slut is not None:
            break
    if slut is None:
        return {}, f"{build.name}:952 `ctx = dict(`-blokken er ikke lukket"
    blok = "\n".join(linjer[start:slut + 1])
    out: dict[str, str] = {}
    for fund in re.finditer(r"(\w+_url)\s*=\s*([^,\n]+)", blok):
        nøgle = fund.group(1)
        # `=` medtages, så den første streng i værdien har et tegn foran sig
        # ligesom alle de andre.
        værdi = "=" + fund.group(2)
        # En streng er en **rute** kun hvis den står for sig selv. Målt 30/9
        # gav den naive læsning to fejl: `report_url=cfg["github"] + "/issues"`
        # lagde `/issues` i listen som en rute (den er en GitHub-sti, ikke en
        # side), og `search_url=search_url` er et navn. Tegnet lige foran
        # strengen afgør det: `=`, `(` eller `else`/`if` = den er valgt for
        # sig selv, `+` = den er limmet på noget andet. Den absolutte
        # `https://mahope.tools/…`-gren i samme betingelse er heller ikke en
        # rute i dette domæne, så `://` sorteres væk.
        for streng in re.finditer(r'"([^"]+)"', værdi):
            tekst = streng.group(1)
            if not tekst.startswith("/") or "://" in tekst:
                continue
            forrige = værdi[:streng.start()].rstrip()
            if not forrige.endswith(("=", "(", "else", "if")):
                continue
            rute = tekst.rstrip("/") or "/"
            linje = start + blok[:fund.start()].count("\n") + 1
            out[rute] = f"{nøgle}='{tekst}' ({build.name}:{linje})"
    return out, ""


def no_paid_declaration(path: Path) -> str | None:
    """Sidens *egen* erklæring om at den intet sælger, eller `None`.

    Målt 30/9: to sider stod på blindlisten uden at have noget at sælge —
    `/site-icons`, der i sin egen FAQ siger at Pro-licensen ikke findes "not
    today, and the page will not pretend otherwise", og
    `/cookie-consent-banner-demo`, en live-demo af et gratis banner. En note
    på dem ville løbe; at efterlade dem i listen er det samme problem, for så
    "løser" nogen dem med en note der løber.

    Erklæringen ligger i siden, ikke i porten, og **grunden er påkrævet**:
    en tom `content` giver ikke en undtagelse, men en rød port. Det er den
    modsatte fejlretning af en navneliste — porten kan ikke tie en side stille,
    og hver kørsel skriver grunden i udskriften, så den kan læses.

    `None` betyder "ingen erklæring". Tom streng betyder "erklæring uden grund",
    og den er rød. Skelningen er hele pointen med denne funktion.
    """
    try:
        src = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for m in re.finditer(r"<meta\b[^>]*>", src, re.I):
        tag = m.group(0)
        navn = re.search(r'name\s*=\s*"([^"]*)"', tag, re.I)
        if not navn or navn.group(1).strip().lower() != DECL_NAME:
            continue
        indhold = re.search(r'content\s*=\s*"([^"]*)"', tag, re.I)
        return (indhold.group(1).strip() if indhold else "")
    return None


# --------------------------------------------------------------------------
# Trafik med syntetiske rapporter lukket ude
# --------------------------------------------------------------------------
def traffic_rows(reports: Path = REPORTS) -> tuple[dict, dict, list[str]]:
    """(`besøg pr. rute`, `kilde`, navnene på de rapporter der blev sprunget over).

    `check_article_paid_path.traffic_source()` læser alle `*.json` i mappen.
    Det er korrekt for ugearkivet, men porten skal kunne bevise at en rapport
    den selv har skrevet aldrig kan blive et målt besøg. Derfor læses filerne
    her først, og enhver med `"synthetic": true` i topniveauet springes over
    og navngives i returværdien.

    De ægte rapporter spejles ind i et midlertidigt bibliotek, så den delte
    læser (*regel 1*) stadig er den der læser — og dens kildeangivelse
    (`file`, `week`, alder) er uændret, fordi filnavnene bevares.
    """
    if not reports.is_dir():
        return {}, {"file": None, "week": None, "generated_at": None,
                    "age_days": None, "newer_without": 0, "reports": 0}, []
    skipped: list[str] = []
    real: dict[str, dict] = {}
    for path in sorted(reports.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("synthetic") is True:
            skipped.append(path.name)
            continue
        real[path.name] = data
    if not real:
        return {}, {"file": None, "week": None, "generated_at": None,
                    "age_days": None, "newer_without": 0,
                    "reports": len(skipped)}, skipped
    with tempfile.TemporaryDirectory() as tmp:
        mirror = Path(tmp)
        for name, data in real.items():
            (mirror / name).write_text(json.dumps(data), encoding="utf-8")
        visits, meta = A.traffic_source(mirror)
    # `traffic_source` tæller de filer den ser. Uden denne linje ville
    # spejlingen få en rapport med tal til at se ud som om den lå i en mappe
    # uden andet indhold, og alderen ville forklares med det modsatte.
    meta["reports"] = len(skipped) + int(meta.get("reports") or 0)
    return visits, meta, skipped


# --------------------------------------------------------------------------
# Målingen
# --------------------------------------------------------------------------
def tool_routes(root: Path = SITE, inventory: dict | None = None) -> list[str]:
    """Ruterne der er værktøjssider: hverken artikler eller forsider.

    Målt 30/9: 104 ruter i inventaret er hverken artikler eller chrome. De er
    *værktøj, landingsside, bogsamling, demo eller 404* — de otte tilfælde er
    ikke til at skelne fra filnavnet, så de måles alle og beskrives i
    udskriften i stedet for at blive undtaget i en navneliste.
    """
    inventory = inventory if inventory is not None else json.loads(
        INVENTORY.read_text(encoding="utf-8")
    )
    articles = {A.route_of(root, p) for p in A.article_files(root)}
    chrome = {(r.rstrip("/") or "/") for r in A.frontpage_routes()}
    out = [route for route in A.route_domain_map(inventory)
           if route not in articles and (route.rstrip("/") or "/") not in chrome]
    return sorted(out)


def tool_rows(root: Path = SITE, catalog: dict | None = None,
              inventory: dict | None = None, visits: dict | None = None,
              chrome: dict[str, str] | None = None) -> list[dict]:
    """Hver værktøjsside med sin betalt vej, sine links og sin publicering.

    `visits` kommer fra `traffic_rows()` — **ikke** fra artikelportens
    `traffic()`. Ellers kunne ranglisten og dommene se to forskellige tal for
    det samme korpus, og det ville være præcis den slags fejl porten er lavet
    for at finde.

    Ruter der er delte af flere domæner får `file: None` og `knapper: None`:
    ét trafiktal summerer flere forskellige sider, og at skrive den ene sides
    knaptal som om det gjaldt ruten er den fejl dom 6/7 i artikelporten blev
    bygget for at undgå. Målt 30/9 er der 0 af dem her, så klassen er tom i
    dag — men porten skal kunne sige det, ikke finde ud af det ved at fejle.

    `chrome_url` og `erklaret` er de to grunde en side kan være målt uden at
    være dømt (opgave 12). De måles her, på siden og i byggen, så `judged()`
    ikke skal læse filer selv — ellers ville de to klasser have hver deres
    sandhed, hvilket er regel 1 i docstringen.
    """
    catalog = catalog if catalog is not None else json.loads(
        CATALOG.read_text(encoding="utf-8")
    )
    inventory = inventory if inventory is not None else json.loads(
        INVENTORY.read_text(encoding="utf-8")
    )
    chrome = chrome_url_routes()[0] if chrome is None else chrome
    offers = A.offer_routes(catalog)
    dom = A.route_domain_map(inventory)
    live = A.deployed_domains()
    inbound = A.inbound_counts(root)
    raw = traffic_rows()[0] if visits is None else visits
    seen = visits_by_route(raw)
    rows = []
    for route in tool_routes(root, inventory):
        domains = dom.get(route, set())
        delt = len(domains) > 1
        path = None if delt else page_file(root, route)
        rows.append({
            "route": route,
            "file": path.relative_to(root).as_posix() if path else None,
            "visits": seen.get(route),
            "links": len(inbound.get(route, ())),
            "paid": A.paid_links(root, path, offers) if path else [],
            # Samme måling som `paid`, men **parvis**: hvilket anker der
            # peger hvor. Ratcheten dømmer på denne og ikke på `paid`, fordi
            # et sæt destinationer ikke kan se to links der bytter plads.
            # Den bæres på rækken — ligesom `paid` — så `measured_anchors()`
            # ikke skal læse filen igen, og så selftestens syntetiske rækker
            # kan dømmes mod par de selv siger (regel 1).
            "ankere": (dict(A.paid_anchors(root, path, offers)) if path else {}),
            "knapper": len(A.knap_links(root, path)) if path else None,
            "domains": sorted(domains),
            "domain": A.domain_label(domains),
            "delt": delt,
            "publiceret": bool(domains & live),
            "chrome_url": chrome.get(route),
            "erklaret": no_paid_declaration(path) if path else None,
        })
    # Trafik først, så en side med målte læsere altid ligger over en side
    # uden. `visits` er `None` når ingen rapport har tal, og `or 0` gør den
    # til 0 — så en fraværende måling kan ikke slå en rigtig.
    rows.sort(key=lambda r: (-(r["visits"] or 0), -r["links"], r["route"]))
    return rows


def undtagelsesgrund(row: dict) -> str:
    """Hvorfor måles rækken men ikke dømmes — tom streng når den dømmes.

    Fire former, alle målt (opgave 12, 30/9):

    - **Ruten har ingen fil i `site/`.** `/bulk-url-checker`,
      `/security-headers-checker` og `/tools` står i inventaret og serveres
      som 404. De har ingen købsknap at miste, så at kræve en vej på dem ville
      kræve at oprette en side, porten ikke kan måle værdien af.
    - **Domænet udgives ikke.** `/bugbottle-demo` ligger på `bugbottle.dev`,
      som ikke står i deploy-matricen. Det er et ❓ (en beslutning Mads skal
      tage), ikke en mangel, og dom 4/7 i artikelporten har samme regel.
    - **Bygget hænger den i hver sides chrome.** `/privacy` og `/terms` er
      `privacy_url`/`terms_url` i `apply_shell`s `ctx`, altså sider builden
      lægger i alle 262 footere. De er vilkårssider, og en købsknap på en
      privatlivspolitik ville være skadelig. Grund: nøglen og linjen i byggen.
    - **Siden siger selv at den intet sælger.** `/site-icons` og
      `/cookie-consent-banner-demo` — målt, med sidens egen ord som grund.

    Skelningen er grunden *ikke* navngivet i porten: chrome-grunden læses i
    byggen, og den erklærede grund står i siden. Derfor skal hver undtagelse
    kunne skrives ud med sin begrundelse — en undtagelse uden grund ville være
    den fejl igen, bare et andet sted.
    """
    if not row["file"]:
        return "ruten har ingen kildefil i site/ (den serveres som 404)"
    if not row["publiceret"]:
        return f"domænet {row['domain']} udgives ikke"
    if row.get("chrome_url"):
        return f"bygget hænger den i chrome: {row['chrome_url']}"
    grund = erklaring_grund(row)
    if grund:
        return f"siden erklærer at den intet sælger: “{grund}”"
    return ""


def erklaring_grund(row: dict) -> str:
    """Sidens egen grund, renset for mellemrum — `""` når den mangler.

    Mellemrum er ikke en grund. Uden denne rensning ville `content="  "` give
    en undtagelse, og det ville være den stille afstempling porten her skal
    fjerne. Derfor går både dommeren og `undtagelsesgrund()` gennem denne.
    """
    return (row.get("erklaret") or "").strip()


def judged(row: dict) -> bool:
    """Måles porten den her række overhovedet?

    Alt, hvad `undtagelsesgrund()` kan begrunde, er **målt men ikke dømt**,
    og skrives i udskriften — så porten springer dem over i stedet for at have
    glemt dem. Se målingerne dér.
    """
    return not undtagelsesgrund(row)


def blind_now(rows: list[dict] | None = None) -> list[str]:
    """De dømte værktøjssider uden betalt vej — den ærlige arbejdskø."""
    table = rows if rows is not None else tool_rows()
    return sorted(r["route"] for r in table if judged(r) and not r["paid"])


def measured_paths(rows: list[dict] | None = None) -> dict[str, list[str]]:
    """(`rute` → de betalte veje siden har **i dag**) for de dømte sider.

    Kun *dømte* sider med en vej: en blind side har ingen vej at passe på, og
    en målt-men-ikke-dømt side (chrome, erklæring, 404) skal ikke låse porten,
    fordi en side flytter klasse.

    Destinationerne er de **rå** href'er `A.paid_links()` målte, uden
    normalisering ud over mængden: `paid_links()` returnerer allerede
    rutestrenge for katalogruter og fuld URL for Stripe-links, så de to former
    kan ikke sammenlignes uden en ny læsning af filen — og regel 1 i
    docstringen forbyder netop den.

    **Denne funktion dømmer ikke længere alene.** Den ser et *sæt* per rute,
    så to destinationer der bytter plads er usynlige. `measured_anchors()`
    ser parvis og det er den, `path_problems()` dømmer; denne er beholdt for
    selftestens syntetiske rækker og for blindlistens `len()`-tællinger, der
    skal blive ved med at tælle veje og ikke anker.
    """
    table = rows if rows is not None else tool_rows()
    return {r["route"]: sorted(set(r["paid"])) for r in table
            if judged(r) and r["paid"]}


def measured_anchors(rows: list[dict] | None = None) -> dict[str, dict[str, str]]:
    """(`rute` → {anker: destination}) for de dømte sider.

    Det er herfra `path_problems()` dømmer, fordi et sæt ikke kan se en
    ombytning. Fundet 30/9: på `/clean-copy-tool` peger `pro-buy`
    ("Buy Clean Copy Pro — $19/year") på `…/6oU4gy…` (19 USD pr. år) og
    `pro-buy-lifetime` ("$39 once") på `…/aFadR81…` (39 USD engang). Byt de
    to href'er om, så læseren ser det rigtige navn og det rigtige pris-tal,
    klikker på det rigtige navn og bliver trukket for den anden vare — og
    ratcheten på destinationer var grøn, fordi *sættet* var uændret. Det er
    samme fejl som den docstringen ovenfor siger, porten blev skrevet for at
    fange: «en revert der ramte `All books →` i stedet for pro-note-linket».

    Samme filtre som `A.paid_links()` og derfor samme destinationsform —
    `_paid_target()` ligger i `check_article_paid_path.py` og bruges af begge
    læsere, så de kan ikke glide fra hinanden (regel 1).

    Parene læses fra rækken (`tool_rows()` måler dem), ikke fra filen her.
    Ellers ville selftestens syntetiske rækker blive dømt mod de 94 rigtige
    linjers filer i stedet for mod det de selv siger — og så ville porten
    kunne være `lambda *_: []` og alle kontrollerne grønne af den forkerte
    grund.
    """
    table = rows if rows is not None else tool_rows()
    out: dict[str, dict[str, str]] = {}
    for r in table:
        anker = r.get("ankere") or {}
        if judged(r) and r["paid"] and anker:
            out[r["route"]] = dict(anker)
    return out


def read_ratchet(path: Path = RATCHET) -> dict[str, list[str]]:
    """Ratchetfilens `paths`, med fejl der ikke kan læses som svar.

    En fil der ikke kan læses, eller en værdi der ikke er et `{anker:
    destination}`-objekt, er **ikke** det samme som "ingen linjer": det
    første er en fejl porten skal råbe om, for ellers ville en slettet fil
    gøre porten grøn (regel 5 i reglerne ovenfor: en port der ikke kan
    måle, må ikke sige "ok"). Derfor hænger `path_problems()` på en
    `RatchetFejl`.

    **Formatet er `{rute: {anker: destination}}`, ikke `{rute: [destination]}`.**
    En liste kan ikke se en ombytning, fordi den kun ved *hvilke*
    destinationer siden har — ikke hvilket anker der peger hvor. Den gamle
    form læses ikke og konverteres ikke: en konvertering ville opfinde
    paringer porten ikke har belæg for, altså rydde en ratchet ud med data
    den ikke har. Den gamle form er derfor en fejl med en besked, der siger
    hvad der skal ske.
    """
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RatchetFejl(f"kan ikke læse {path.name}: {exc}") from exc
    paths = doc.get("paths")
    if not isinstance(paths, dict):
        raise RatchetFejl(
            f"{path.name} har ingen `paths`-objekt (fandt "
            f"{type(paths).__name__}); porten kan ikke vide hvilke veje der "
            f"blev målt, så den må ikke sige at de stadig er der")
    out: dict[str, dict[str, str]] = {}
    for rute, veje in paths.items():
        if not isinstance(rute, str):
            raise RatchetFejl(f"{path.name}: ruten {rute!r} er ikke en streng")
        if isinstance(veje, list):
            raise RatchetFejl(
                f"{path.name}: linjen {rute!r} er en liste af destinationer. "
                f"Ratchetfilen måler nu *hvilket anker* der peger hvor, så en "
                f"liste kan ikke se to links der bytter plads. Kør "
                f"`--write --force` for at måle parene — det skriverkun den "
                f"destination der stod, nu med sit anker ved siden af."
            )
        if not isinstance(veje, dict) or not all(
                isinstance(k, str) and isinstance(v, str) for k, v in veje.items()):
            raise RatchetFejl(
                f"{path.name}: linjen {rute!r} skal være et objekt der "
                f"parrer hvert anker med sin destination, fandt {veje!r}")
        out[rute] = dict(veje)
    return out


def path_problems(rows: list[dict], ratchet: dict[str, dict[str, str]]) -> list[str]:
    """Røde domme for betalte veje der er **forsvundet** — eller **ombyttet**.

    Baggrund (opgave 8, 30. september 2026): porten dømte *om* en side havde
    en betalt vej, ikke *hvilken*. Beviset stod i målingen: en revert der ramte
    `All books →` i stedet for pro-note-linket efterlod alle tre porte grønne,
    selv om siden havde byttet om de to destinationer. Og fordi blindlisten
    måles på "har den en vej", er en side der står på listen og mister sin vej
    igen præcis den tilstand porten forventer af den.

    **Ratcheten måler par, ikke sæt** (rettelse 30/9 efter review-fund).
    `{rute: {anker: destination}}` ser *hvilket* anker der peger *hvor*, så
    dommen kan skelne de to fejl der ligner hinanden: en destination der
    forsvinder, og to destinationer der **bytter plads**. Den anden var usynlig
    i den gamle form, fordi sættet var uændret — og den er den dyreste, fordi
    læseren ser det rigtige navn og det rigtige pris-tal, klikker på det
    rigtige navn og bliver trukket for den anden vare. Målt på mutationen:
    byttet om de to Stripe-href'er på `/clean-copy-tool` var den gamle port
    grøn; den nye er rød med de to anker ved navn.

    Derfor bærer hver linje parene den målte ved skrivningen, og porten dømmer
    fire ting der alle kan være røde:

    - **Mistet vej.** En destination der stod på linjen og ikke står i
      målingen mere. Det dækker både "linket blev slettet" og "linket blev
      byttet ud med et andet", fordi det er den *konkrete* destination der
      forsvinder, ikke et tal.
    - **Ombyttet par.** Et anker der stod på linjen peger i dag på en anden
      destination end den det blev målt med. Destinationen kan være den
      samme, som den var — det er *ankeret* der flyttede, og det er præcis
      det tilfælde den gamle form ikke kunne se. Fejlmeddelelsen siger begge
      destinationer, så en læser kan se hvilken vare der nu ligger under
      hvilket navn.
    - **Død linje.** En rute der ikke længere er en dømt værktøjsside. Så
      står der intet mere at passe på, og linjen ville leve for evigt.
    - **Tom linje.** En linje uden et eneste par er den samme fejl som en
      slettet fil: den kan kun ske ved at skrive den, så den er rød.

    Tilføjelser er **ikke** røde. En ny betalt vej er fremskridt, og den må
    kunne skrives uden `--force`; kun en forsvunden vej kræver at nogen
    bevidst frigiver ratcheten.

    Dømningen læser `measured_anchors()` og ikke `measured_paths()`. Den
    sidste bruges kun til at sige *hvilke* destinationer siden har i dag, så
    fejlmeddelelsen kan nævne dem — ikke til at afgøre om noget er rødt.
    """
    problems: list[str] = []
    measured = measured_anchors(rows)
    veje = measured_paths(rows)
    for rute in sorted(ratchet):
        registreret = dict(ratchet[rute] or {})
        if rute not in measured:
            problems.append(
                f"DØD VEJ-LINJE i {RATCHET.name}: {rute} er ikke længere en "
                f"dømt værktøjsside med en betalt vej, så linjen passer på "
                f"intet. Kør --write --force, hvis det er meningen."
            )
            continue
        if not registreret:
            problems.append(
                f"TOM VEJ-LINJE i {RATCHET.name}: {rute} står med nul "
                f"destinationer, så den låser intet. Mål den igen med "
                f"--write, eller fjern linjen."
            )
            continue
        i_dag = measured[rute]
        bygget = sorted(set(registreret.values()) - set(i_dag.values()))
        if bygget:
            problems.append(
                f"MISTET BETALT VEJ: {rute} havde {len(registreret)} "
                f"destination(er) målt, og {', '.join(bygget)} er ikke blandt "
                f"dem længere — nu har den {len(i_dag)}: "
                f"{', '.join(sorted(set(i_dag.values()))) or '(ingen)'}. En side "
                f"der mister den betalte vej den lå på er en tilbagefaldet "
                f"side, også når der stadig står en anden vej på den."
            )
        flyttet = sorted(
            (anker, gammel, i_dag[anker])
            for anker, gammel in registreret.items()
            if anker in i_dag and i_dag[anker] != gammel
        )
        for anker, gammel, ny in flyttet:
            problems.append(
                f"OMBYTTET BETALT VEJ: {rute} — ankeret {anker!r} blev målt "
                f"til {gammel} og peger nu på {ny}. Begge destinationer kan "
                f"godt være på siden ({', '.join(sorted(set(i_dag.values())))})"
                f"{'; de er bare byttet om' if gammel in set(i_dag.values()) else ''}"
                f", så tallene på siden er uændrede og kun ratcheten kan se "
                f"det. En læser ser navnet og prisen på det anker han klikker "
                f"på og bliver trukket for den anden vare. Ret href'en, eller "
                f"kør --write hvis ombytningen er villet."
            )
        mistet_anker = sorted(set(registreret) - set(i_dag))
        if mistet_anker:
            problems.append(
                f"MISTET ANKER: {rute} havde {len(mistet_anker)} anker(er) "
                f"målt der ikke findes på siden længere: "
                f"{', '.join(mistet_anker[:6])}. Ankeret *er* købsvejen — "
                f"uden det står navnet på en knap, der intet peger på."
            )
    return problems


def judge(rows: list[dict] | None = None, doc: dict | None = None,
          ratchet: dict[str, list[str]] | None = None) -> list[str]:
    """Portens domme på en målt tabel. Alle skal være grønne.

    `ratchet` gives målingen, så **filen læses ikke her**: `dom()` er den ene
    sted der læser den fra disk, og selftestens syntetiske rækker skal dømmes
    mod det de selv siger — ikke mod de 94 rigtige linjer.
    """
    table = rows if rows is not None else tool_rows()
    doc = doc if doc is not None else json.loads(BLIND.read_text(encoding="utf-8"))
    known = list(doc.get("blind") or [])
    measured = blind_now(table)
    by_route = {r["route"]: r for r in table}
    problems: list[str] = list(path_problems(table, ratchet or {}))

    # 0. Kan porten overhovedet læse, hvad bygten hænger i chrome? Uden
    #    `ctx`-blokken er `/privacy` og `/terms` hverken dømte eller undtagne,
    #    og de ville stå som ny blinde uden at sige hvorfor. Det er en fejl i
    #    porten, ikke en mangel på sider, så den melder sig selv.
    fejl = chrome_url_routes()[1]
    if fejl:
        problems.append(
            f"CHROME KUNNE IKKE LÆSES: {fejl}. Uden den må porten hverken dømme "
            f"eller undtage en side, bygget selv hænger i hver sides footer."
        )

    for route in sorted(set(measured) - set(known)):
        row = by_route[route]
        links = row["links"]
        problems.append(
            f"NY BLIND VÆRKTØJSSIDE: {route} ({row['file'] or 'ingen fil'}) "
            f"ligger på {row['domain']} og har {links} indgående link"
            f"{'' if links == 1 else 's'} i site/, men ingen betalt vej: ingen "
            f"buy.stripe.com i egen tekst og intet link til en side i "
            f"stripe_catalog.json. Sæt en vej på siden, eller tilføj en linje "
            f"i tools/tool_paid_path_blind.json."
        )
    for route in sorted(set(known) - set(measured)):
        row = by_route.get(route)
        if row is None:
            why = ("ruten er ikke længere en værktøjsside (artikel, forside "
                   "eller ikke i inventaret)")
        elif row["paid"]:
            why = f"den har nu {len(row['paid'])} betalt(e) vej(er)"
        else:
            why = undtagelsesgrund(row) or (
                f"den har nu {row['knapper']} købsknap(per), så den er dækket")
        problems.append(
            f"DØD LINJE i listen: {route} er ikke længere i den målte klasse "
            f"— {why}. Fjern den fra tools/tool_paid_path_blind.json — listen "
            f"må kun krympe."
        )
    if len(known) != len(set(known)):
        problems.append("listen har dubletter; den er en mængde, ikke en liste.")

    # 1. En erklæring skal kunne holdes. En side der siger "jeg sælger intet"
    #    og samtidig har en købsknap, modsiger sig selv, og en erklæring uden
    #    grund er præcis den stille undtagelse porten her skal fjerne — så
    #    begge er røde. Uden dem kunne en enkelt tom meta-tag slå porten fra.
    for row in table:
        erklæring = erklaring_grund(row)
        if row.get("erklaret") is None:
            continue
        rute = row["route"]
        if not erklæring:
            problems.append(
                f"ERKLÆRING UDEN GRUND: {rute} ({row['file']}) bærer "
                f'name="{DECL_NAME}" med tom content. En tom grund er ikke en '
                f"grund — skriv hvorfor siden intet sælger, eller fjern "
                f"erklæringen, så porten dømmer siden som enhver anden."
            )
        elif row["paid"]:
            problems.append(
                f"MODSIGELSE: {rute} erklærer at den intet sælger ("
                f"“{erklæring}”), men har {len(row['paid'])} betalt(e) vej(er) "
                f"i egen tekst. En af de to er en løgn — enten fjernes "
                f"erklæringen, eller siden har noget at sælge."
            )
    return problems


def _read_legacy_ratchet(path: Path) -> dict[str, dict[str, str]] | None:
    """Læs den gamle listeform som `{rute: {}}` — kun til migrering.

    Destinationerne **tabes bevidst**: listeformen ved ikke hvilket anker der
    hørte til hvilken destination, så porten opfinder ingen paringer for dem.
    Den eneste brug er at tjekke at de stadig findes på siderne, så en
    migrering kan frigive ratcheten ved et uheld. `None` når filen heller
    ikke er læselig som JSON.
    """
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    paths = doc.get("paths") if isinstance(doc, dict) else None
    if not isinstance(paths, dict):
        return None
    if not all(isinstance(k, str) and isinstance(v, list)
               and all(isinstance(x, str) for x in v) for k, v in paths.items()):
        return None
    # Nøglen er destinationen: den gamle fil skal kunne svare "findes den
    # stadig?", ikke "hvilket anker hørte til den?".
    return {rute: {f"legacy:{v}": v for v in sorted(set(veje))}
            for rute, veje in paths.items()}


def _write_ratchet(målt: dict[str, dict[str, str]], force: bool,
                   sti: Path = RATCHET) -> tuple[str, str]:
    """Skriv ratchetfilen fra målingen. `(retning, fejl)` — en af dem er tom.

    Samme tommelfingerregel som blindlisten: `--write` må ikke kunne frigive
    ratcheten ved at man lige kører den. Derfor kræver en forsvunden vej
    `force`, og fejlen **navngiver** de destinationer der stod på linjen — så
    beskeden er et spørgsmål ("må de virkelig være væk?") og ikke en
    afvisning, man læser forbi.

    **Migrering fra listeformen.** En fil der skriver hver rute som en *liste*
    af destinationer læses ikke af `read_ratchet()` — den siger det, og det er
    med vilje, fordi en liste ikke kan se en ombytning. Den gamle form må dog
    migreres, og det er **kun** under `--force`, og **kun** når den nye måling
    stadig indeholder hver destination den gamle fil havde. Det er derfor en
    skærpelse og ikke en frigivelse: parene *tilføjes*, og intet tabes. Den
    gamle fil giver ingen anker-identitet, så porten opfinder ingen paringer
    for den — den måler dem fra siderne, som er den eneste kilde der har
    belæg for dem.
    """
    gammel_format_migrering = False
    try:
        gammel = read_ratchet(sti)
    except RatchetFejl as exc:
        # En ratchetfil der ikke findes endnu er ikke en fejl: første
        # skrivning skaber den.
        if not sti.exists():
            gammel = {}
        else:
            gammel = _read_legacy_ratchet(sti)
            if gammel is None:
                return "", f"kan ikke skrive {sti.name}: {exc}"
            gammel_format_migrering = True
    tabt: list[str] = []
    if gammel_format_migrering:
        # Kun destinations-sættet kan sammenlignes med den gamle form; den
        # har ingen anker, så anker-loopen nedenfor ville tælle hver enkelt
        # destination som "anker væk". Derfor springes den over her.
        for rute, veje in gammel.items():
            nu = målt.get(rute, {})
            for vej in sorted(set(veje.values()) - set(nu.values())):
                tabt.append(f"{rute} mistede destinationen {vej}")
        if tabt and not force:
            return "", (
                "--write ville fjerne destinationer fra ratcheten:\n  "
                + "\n  ".join(tabt)
                + "\nDen gamle listeform kan ikke se ombytninger, så den må "
                  "kun migreres når intet er tabt. Ret siden, eller kør med "
                  "--force hvis det er væk med vilje."
            )
    else:
        for rute, veje in gammel.items():
            nu = målt.get(rute, {})
            for anker, vej in sorted(veje.items()):
                if anker not in nu:
                    tabt.append(f"{rute}: ankeret {anker!r} ({vej}) er væk")
                elif nu[anker] != vej:
                    tabt.append(
                        f"{rute}: ankeret {anker!r} peger nu på {nu[anker]} "
                        f"i stedet for {vej}")
            for gammel_vej in sorted(set(veje.values()) - set(nu.values())):
                if gammel_vej not in nu.values():
                    tabt.append(f"{rute} mistede destinationen {gammel_vej}")
    if tabt and not force:
        return "", ("--write ville fjerne målte veje fra ratcheten:\n  "
                    + "\n  ".join(tabt)
                    + "\nEn forsvunden vej skal frigives bevidst. Ret siden, "
                      "eller kør med --force hvis den er væk med vilje.")
    doc = {
        "note": (
            "Hvert betalt anker på hver dømt værktøjsside, målt af "
            "check_tool_paid_path.py. Ratchet: et par der står her og ikke "
            "længere findes på siden er rød, fordi en side der mister den "
            "vej den lå på er en tilbagefaldet side — også når der stadig "
            "står en anden vej på den. Den dømmer OGSÅ et anker der peger på "
            "en anden destination end den blev målt med, altså en ombytning: "
            "en liste destinationer kan ikke se den, fordi sættet er "
            "uændret. `blind` i tool_paid_path_blind.json er det modsatte: "
            "sider der MÅLSLIGE ikke har nogen. Begge skrives med "
            "`--write --force`."
        ),
        "source": (
            "python3 tools/check_tool_paid_path.py --write  · Parrene er de "
            "rå href'er A.paid_anchors() målte i sidens egen tekst, nøglet på "
            "ankerets `id` (ellers dets synlige tekst)"
        ),
        "measured": date.today().isoformat(),
        "paths": {rute: dict(sorted(veje.items())) for rute, veje in sorted(målt.items())},
    }
    sti.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    tilfojet = sorted(set(målt) - set(gammel))
    nyt = sum(len(set(målt[r]) - set(gammel.get(r, {}))) for r in målt)
    if gammel_format_migrering:
        # "221 nye destinationer" ville være en løgn her: destinationerne er
        # de samme som før, de har blot fået et anker ved siden af. Den
        # ærlige besked siger hvad der skete, så en der læser loggen ikke
        # tror ratcheten er blevet slettet og genopbygget.
        antal = sum(len(v) for v in målt.values())
        retning = (f"migreret fra listeform til par ({antal} anker fordelt på "
                   f"{len(målt)} linje(r); intet destinationstab)")
    elif tabt:
        retning = f"{len(tabt)} destination(er) frigivet (krævede --force)"
    elif tilfojet or nyt:
        retning = (f"{len(tilfojet)} nye linje(r), {nyt} nye destination(er)"
                   if tilfojet else f"{nyt} nye destination(er)")
    else:
        retning = "uændret"
    return retning, ""


def dom(table: list[dict] | None = None, doc: dict | None = None,
        ratchet_sti: Path = RATCHET) -> list[str]:
    """`judge()` med ratchetfilen læst fra disk — det `main()` og selvtesten
    begge bruger, så der kun er ét sted der læser filen.

    En ratchetfil der ikke kan læses er **rød**, ikke grøn: en slettet eller
    ødelagt fil må ikke kunne slå porten fra. Det er regel 5 ovenfor — en port
    der ikke kan måle, må ikke sige "ok".
    """
    if table is None:
        table = tool_rows()
    try:
        ratchet = read_ratchet(ratchet_sti)
    except RatchetFejl as exc:
        return [f"RATCHET KUNNE IKKE LÆSES: {exc}"]
    return judge(table, doc, ratchet)


# --------------------------------------------------------------------------
# Udskrift
# --------------------------------------------------------------------------

def _print_ranking(rows: list[dict], limit: int, meta: dict,
                   skipped: list[str]) -> None:
    ko = [r for r in rows if judged(r)]
    blind = [r for r in ko if not r["paid"]]
    print(f"værktøjssider: {len(rows)} ruter · {len(ko)} dømte (med fil på et "
          f"udgivet domæne) · med betalt vej: {len(ko) - len(blind)} · "
          f"blinde: {len(blind)} · målt men ikke dømt: {len(rows) - len(ko)}")
    # Kilden står *over* kolonnen, ikke nederst: målt 30/9 ligger tallene i
    # uge 38, og fire iterationer skrev dem i planen som "målte besøg" uden
    # alder. En kolonne uden kilde er et tal læseren ikke kan veje.
    print(A.traffic_note(meta))
    if skipped:
        print(f"springer over {len(skipped)} syntetisk(e) rapport(er), der ikke "
              f"er kunders besøg: {', '.join(skipped)}")
    print(f"{'trafik':>6} {'links':>5}  {'fil':<50} rute")
    for row in blind[:limit]:
        trafik = str(row["visits"]) if row["visits"] is not None else "-"
        print(f"{trafik:>6} {row['links']:>5}  {(row['file'] or '(ingen fil)'):<50} "
              f"{row['route']}")

    mangle = [r for r in rows if r["file"] is None]
    dark = [r for r in rows if r["file"] and not r["publiceret"]]
    chrome = [r for r in rows if r.get("chrome_url") and r["file"]
              and r["publiceret"]]
    erklæret = [r for r in rows if r.get("erklaret") and r["file"]
                and r["publiceret"]]
    if mangle:
        print(f"\nuden kildefil: {len(mangle)} rute(r) — de serveres som 404, så "
              f"de har ingen købsknap at miste, og de dømmes ikke:")
        for row in mangle[:limit]:
            print(f"{'':>6} {row['links']:>5}  {'(findes ikke i site/)':<50} "
                  f"{row['route']} — {row['domain']}")
    if dark:
        print(f"\nikke udgivet: {len(dark)} rute(r) på et domæne uden i "
              f"deploy-matricen — måles, dømmes ikke (❓ om bugbottle.dev):")
        for row in dark[:limit]:
            trafik = str(row["visits"]) if row["visits"] is not None else "-"
            print(f"{trafik:>6} {row['links']:>5}  {(row['file'] or ''):<50} "
                  f"{row['route']} — {row['domain']}")
    # De to nye klasser skrives med deres grund, fordi en undtagelse uden grund
    # er det porten her skal fjerne. Antallet på sidens linje tæller *kun de
    # undtagne ruter der står på blindlisten* — hvis en chrome-side nogensinde
    # mister sin vej, skal den kunne ses i denne udskrift.
    if chrome:
        print(f"\nchrome ifølge bygget: {len(chrome)} rute(r) — byggen hænger "
              f"dem i hver sides footer, så de er vilkårssider, ikke "
              f"værktøjssider. En købsknap på dem ville være skadelig:")
        for row in chrome[:limit]:
            print(f"{'':>6} {row['links']:>5}  {row['file']:<50} "
                  f"{row['route']} — {row['chrome_url']}")
    if erklæret:
        print(f"\nintet at sælge ifølge siden: {len(erklæret)} rute(r) — siden "
              f"bærer sin egen grund, så porten dømmer dem ikke:")
        for row in erklæret[:limit]:
            print(f"{'':>6} {row['links']:>5}  {row['file']:<50} "
                  f"{row['route']} — {row['erklaret']}")


# --------------------------------------------------------------------------
# Selftest
# --------------------------------------------------------------------------
def _self_test() -> int:
    """Kontroller der kan fejle. Uden dem er `--self-test` grøn af den simple
    grund at porten ingenting kan se.

    Formerne der ikke findes i `site/` bygges syntetisk — samme regel som
    artikelportens kontrol 5b: en kontrol der måler en tom klasse er grøn for
    den forkerte grund.
    """
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    offers = A.offer_routes(catalog)
    table = tool_rows(SITE, catalog)

    # 1. Porten læser filerne, ikke en kopi af dem. Uden denne kontrol kunne
    #    en mutation af `site/` være grøn. Eksemplet vælges blandt de sider
    #    der *har* en vej, og formen bygges syntetisk når ingen har: da
    #    kontrol 5 i 30/9 skrev `contrast-checker.html` som sit eksempel, faldt
    #    den af en opgave der *lykkedes* — siden fik sin vej, porten var urørt.
    dømt_med_vej = [r for r in table if judged(r) and r["file"] and r["paid"]]
    læst = (len(A.paid_links(SITE, SITE / dømt_med_vej[0]["file"], offers))
            if dømt_med_vej else 0)
    check("læser en værktøjside med betalt vej i egen tekst",
          læst == len(dømt_med_vej[0]["paid"]) if dømt_med_vej else False,
          f"{læst} vej(er) i {dømt_med_vej[0]['file'] if dømt_med_vej else '—'}")
    with tempfile.TemporaryDirectory() as tmp:
        kunst = Path(tmp) / "syntetisk.html"
        kunst.write_text(
            '<html><body><header><a href="/blog/x">x</a></header><div>'
            '<a href="https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03">køb</a>'
            "</div><footer>x</footer></body></html>", encoding="utf-8")
        tom = Path(tmp) / "tom.html"
        tom.write_text(
            '<html><body><header><a href="/blog/x">x</a></header>'
            "<div>intet at købe</div><footer>x</footer></body></html>",
            encoding="utf-8")
        check("læseren dømmer filen den får, ikke en kopi",
              len(A.paid_links(SITE, kunst, offers)) == 1
              and A.paid_links(SITE, tom, offers) == [],
              f"{len(A.paid_links(SITE, kunst, offers))} / "
              f"{len(A.paid_links(SITE, tom, offers))}")

    # 2. Den såkaldte forbigående fejl: et købslink i *footer* tæller ikke.
    footer_only = (
        '<html><body><header><a href="/blog/x">x</a></header><div>værktøj</div>'
        '<footer><a href="https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03">køb'
        "</a></footer></body></html>"
    )
    body_only = (
        '<html><body><header><a href="/blog/x">x</a></header><div>'
        '<a href="https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03">køb</a>'
        "</div><footer>x</footer></body></html>"
    )
    check("købslink i footer tæller ikke (chrome)",
          A.content_region(footer_only).count("buy.stripe.com") == 0)
    check("købslink i brødteksten tæller",
          A.content_region(body_only).count("buy.stripe.com") == 1)

    # 3. Klassen er værktøjssider, ikke artikler og ikke forsider. Alle tre er
    #    målt på disk, så regel 3 og 4 i docstringen kunne have ladet 190
    #    artikler ligge i portens dom uden at nogen så det.
    artikler = {A.route_of(SITE, p) for p in A.article_files(SITE)}
    routes = set(tool_routes())
    normaliseret = {(r.rstrip("/") or "/") for r in routes}
    forsider = {(r.rstrip("/") or "/") for r in A.frontpage_routes()}
    check("ser engelske værktøjssider",
          len([r for r in routes if not r.startswith("/da")]) > 40,
          f"EN={sum(1 for r in routes if not r.startswith('/da'))}")
    check("ser danske værktøjssider",
          len([r for r in routes if r.startswith("/da")]) > 2,
          f"DA={sum(1 for r in routes if r.startswith('/da'))}")
    check("artikler er ikke i værktøjsklassen", not (routes & artikler),
          f"{len(routes & artikler)} overlap")
    check("forsider er ikke i værktøjsklassen", not (normaliseret & forsider),
          f"{sorted(normaliseret & forsider)}")
    check("korpuset er større end artiklerne alene", len(routes) > 50, f"{len(routes)}")

    # 4. Ruten er den på webserveren, ikke filnavnet. `index.html` er mappens
    #    rute; en rå læsning ville klassificeret `/books` som `/books/index`.
    check("index.html er mappens rute",
          A.route_of(SITE, SITE / "books" / "index.html") == "/books",
          A.route_of(SITE, SITE / "books" / "index.html"))
    check("en rute findes med og uden skråstreg",
          page_file(SITE, "/books") == SITE / "books" / "index.html"
          and page_file(SITE, "/books/") == SITE / "books" / "index.html")

    # 5. Dommeren: en målt værktøjsside uden vej skal kunne gøre porten rød,
    #    og en med vej skal ikke. Begge former læses fra `site/` i dag, men
    #    **hvilken** side der er blind, vælger tabellen selv. Det var derfor de
    #    gjorde grøn i 30/9: `json-formatter.html` stod hårdkodet som eksempel på
    #    en side uden vej, og da den fik sin, faldt to kontroller — af en opgave
    #    der *lykkedes*. Samme familie som `RE_CLAIM`s hårdkodede former.
    #
    #   Og når *ingen* side er blind længere — hvilket er målet med opgave 4,
    #    og blev sandt 30/9 da listen nåede nul — bygges formen syntetisk. En
    #    kontrol der kræver en rigtig blind side er ellers grøn af den forkerte
    #    grund, at porten ingenting har at dømme: præcis den fejl denne kontrol
    #    blev skrevet for at fange.
    kandidater = [r for r in table if judged(r)]
    with_vej = next((r for r in kandidater if r["paid"]), None)
    rigtig_blind = next((r for r in kandidater if not r["paid"]), None)
    without_vej = rigtig_blind or dict(
        with_vej or {}, route="/syntetisk-blind", file="syntetisk.html",
        links=3, paid=[], knapper=0, chrome_url=None, erklaret=None)
    rød = judge([r for r in (with_vej, without_vej) if r], {"blind": []})
    check("en side uden vej gør porten rød med filnavn",
          any(without_vej["file"] in p and "NY BLIND VÆRKTØJSSIDE" in p
              for p in rød),
          f"{len(rød)} problem(er)"
          + ("" if rigtig_blind else " (syntetisk: ingen rigtig blind side)"))
    check("en side med vej er ikke i den røde besked",
          bool(with_vej) and not any(with_vej["file"] in p for p in rød),
          f"{[p[:70] for p in rød]}")
    check("kun en side med vej giver grønt",
          bool(with_vej) and not judge([with_vej], {"blind": []}), "")
    check("beskeden siger hvor mange indgående links siden har",
          any(f"{without_vej['links']} indgående link" in p for p in rød),
          f"{[p for p in rød if 'indgående' in p][:1]}")

    # 5b. Død linje: en linje i listen uden en reel mangel er rød, fordi
    #     listen er en ratchet. Uden denne kontrol kunne listen vokse i det
    #     skjulte, og fire iterationers "1 side fik en vej" ville have været
    #     det samme som "listen blev længere".
    død = judge([with_vej], {"blind": [with_vej["route"]]})
    check("en død linje i listen er rød med årsagen",
          any("DØD LINJE" in p and "betalt(e) vej" in p for p in død), f"{død}")
    check("dubletter i listen er røde",
          any("dubletter" in p for p in judge([], {"blind": ["/x", "/x"]})), "")

    # 5c. Ruter på et domæne uden i deploy-matricen, og ruter uden fil i
    #     `site/`, måles men dømmes ikke. `bugbottle.dev` er det eneste, og det
    #     er et ❓ — en beslutning, ikke en fejl. Formerne bygges syntetisk,
    #     fordi porten ellers ville være grøn af den forkerte grund at
    #     klasserne er tomme. Begge er målt på de rigtige ruter her, så
    #     kontrollen dømmer på portens egen undtagelse og ikke på en kopi.
    check("en side på et domæne uden i matricen er målt men ikke dømt",
          not judge([dict(without_vej, domains=["bugbottle.dev"],
                          domain="bugbottle.dev", publiceret=False)],
                    {"blind": []}), "")
    check("en rute uden fil i site/ er heller ikke dømt",
          not judge([dict(without_vej, file=None, domains=["mahope.tools"],
                          domain="mahope.tools", publiceret=True)],
                    {"blind": []}), "")
    # `judged()` er den undtagelse, og den skal kunne fejle på hver af sine
    # halvdele. Uden denne kontrol kunne `judged()` blive `lambda r: True` og
    # kontrollerne ovenfor stadig være grønne, fordi de dømmer en port der
    # slet ikke bruger den.
    check("judged() afviser en rute uden fil", not judged(dict(without_vej, file=None)),
          "")
    check("judged() afviser et domæne uden i matricen",
          not judged(dict(without_vej, publiceret=False)), "")
    check("judged() accepterer en rigtig værktøjsside", judged(without_vej), "")

    # 5d. Opgave 12: en juridisk side skal **ikke** have en købsknap, og porten
    #     skal kunne se forskel på den og en værktøjsside — uden en navneliste.
    #     Chromen læses i byggens egen `ctx`, så kontrolen måler *byggen*.
    bygget, bygg_fejl = chrome_url_routes()
    check("byggets chrome-ruter læses uden fejl", not bygg_fejl, bygg_fejl)
    check("bygget hænger /privacy og /terms i hver sides footer",
          {"/privacy", "/terms"} <= set(bygget),
          f"{sorted(bygget)}")
    check("grunden navngiver nøglen og linjen i byggen",
          all("build_sites.py:" in grund for grund in bygget.values()),
          f"{sorted(bygget.values())[:1]}")
    # MUTATION: samme syntetiske bygge uden `ctx`-blokken skal finde *intet*,
    # så reglen kan fejle. Uden denne linje kunne `chrome_url_routes()` være
    # `lambda _: {"/privacy": "ja"}` og alle tre kontroller ovenfor være grønne
    # af den forkerte grund.
    with tempfile.TemporaryDirectory() as tmp:
        rå = Path(tmp) / "build_sites.py"
        rå.write_text("SITES = {}\n", encoding="utf-8")
        tom, tom_fejl = chrome_url_routes(rå)
        check("mutation: en bygge uden `ctx = dict(` finder ingen chrome-ruter",
              not tom and "ctx = dict(" in tom_fejl, f"{tom} / {tom_fejl}")
    # Samme byg, med en rute der er *ikke* rod-relativ, skal den heller ikke
    # tage med — ellers ville `report_url=github+"/issues"` blive en rute.
    with tempfile.TemporaryDirectory() as tmp:
        rå = Path(tmp) / "build_sites.py"
        rå.write_text(
            'def apply_shell():\n'
            '    ctx = dict(t,\n'
            '               privacy_url="/privacy/",\n'
            '               report_url=cfg["github"] + "/issues",\n'
            '               search_url=search_url)\n',
            encoding="utf-8")
        kun, _ = chrome_url_routes(rå)
        check("mutation: kun rod-relative `*_url` er chrome",
              set(kun) == {"/privacy"}, f"{sorted(kun)}")
    # En rigtig chrome-side skal være målt men ikke dømt. Samme måling uden
    # chrome-grunden skal dømme den — så reglen kan fejle, uanset at den rute
    # der ligger i korpus, har en købsknap og derfor aldrig ville blive blind.
    chrome_række = next((r for r in table if r.get("chrome_url")), None)
    check("en chrome-side i korpus er målt men ikke dømt",
          bool(chrome_række) and not judged(chrome_række)
          and not judge([chrome_række], {"blind": []}),
          f"{chrome_række['route'] if chrome_række else 'ingen'}")
    som_chrome = dict(without_vej, chrome_url="privacy_url='/x/' (build_sites.py:1)")
    check("mutation: samme blinde side uden chrome-grunden er dømt",
          judged(without_vej) and not judged(som_chrome)
          and not judge([som_chrome], {"blind": []})
          and any("NY BLIND" in p for p in judge([without_vej], {"blind": []})),
          "")
    check("død linje med chrome-grund siger hvorfor",
          any("DØD LINJE" in p and "chrome" in p
              for p in judge([som_chrome], {"blind": [som_chrome["route"]]})), "")

    # 5e. En side kan sige at den intet sælger, men kun med en grund, og
    #     modsigelsen (erklæring + købsknap) er rød. Ellers kunne ét tomt
    #     meta-tag slå porten fra — det modsatte af opgave 12.
    erklæret_række = next((r for r in table if r.get("erklaret")), None)
    check("en side der erklærer intet at sælge er målt men ikke dømt",
          bool(erklæret_række) and not judged(erklæret_række)
          and not judge([erklæret_række], {"blind": []}),
          f"{erklæret_række['route'] if erklæret_række else 'ingen'}")
    check("mutation: samme side uden erklæringen er dømt",
          judged(dict(erklæret_række, erklaret=None)), "")
    check("erklæring uden grund er rød, ikke en undtagelse",
          any("ERKLÆRING UDEN GRUND" in p for p in
              judge([dict(without_vej, erklaret="   ")], {"blind": []}))
          and judged(dict(without_vej, erklaret="   ")), "")
    check("erklæring på en side med købsknap er en modsigelse",
          any("MODSIGELSE" in p for p in
              judge([dict(without_vej, erklaret="intet", paid=["x"])],
                    {"blind": []})), "")
    # Formerne bygges syntetisk: 30/9-punden var `json-formatter.html` som
    # eksempel på en side *uden* erklæring, og da den fik sin, faldt
    # kontrollen af en opgave der lykkedes. Porten skal kunne skelne mellem
    # de tre former uanset hvilke sider der ligger i `site/`.
    with tempfile.TemporaryDirectory() as tmp:
        med = Path(tmp) / "med-erklaring.html"
        med.write_text(
            f'<html><head><meta name="{DECL_NAME}" content="siden sælger intet">'
            "</head><body>x</body></html>", encoding="utf-8")
        uden = Path(tmp) / "uden-erklaring.html"
        uden.write_text(
            '<html><head><title>x</title></head><body>x</body></html>',
            encoding="utf-8")
        grundløs = Path(tmp) / "erklaring-uden-grund.html"
        grundløs.write_text(
            f'<html><head><meta name="{DECL_NAME}" content="   ">'
            "</head><body>x</body></html>", encoding="utf-8")
        check("erklæringen læses kun fra sidens egen meta",
              no_paid_declaration(med) == "siden sælger intet"
              and no_paid_declaration(uden) is None
              and no_paid_declaration(grundløs) == "",
              f"{no_paid_declaration(med)!r} / {no_paid_declaration(uden)!r} / "
              f"{no_paid_declaration(grundløs)!r}")

    # De undtagne ruter findes rigtigt i korpus, så klasserne er ikke tomme
    # af en fejl i `judged()`. Sættet er de målte — ikke tilfældige — fordi det
    # er præcis de fire der er hverken fil-lose, udgivne, chrome eller
    # erklærede. En ny måling skal opdatere sættet her, ikke slå kontrolen fra.
    undtagne = {r["route"]: undtagelsesgrund(r)[:38] for r in table
                if not judged(r)}
    check("de undtagne ruter er dem, porten kan begrunde",
          set(undtagne) == {"/bulk-url-checker", "/security-headers-checker",
                            "/tools", "/bugbottle-demo", "/privacy", "/terms",
                            "/support", "/da/support", "/site-icons",
                            "/cookie-consent-banner-demo"},
          f"{sorted(undtagne)}")

    # 6. Kilden på besøgene. Målt 30/9 ligger tallene i uge 38, og fire
    #    iterationer skrev dem uden alder; porten skal kunne regne alderen og
    #    sige hvor mange nyere rapporter der står uden trafik.
    _visits, meta, _skipped = traffic_rows()
    check("porten læser trafik med sin alder og kilde",
          meta.get("week") is not None and meta.get("age_days") is not None,
          json.dumps(meta, ensure_ascii=False))
    check("kilden siges i teksten, ikke kun i et tal",
          "trafik:" in A.traffic_note(meta), A.traffic_note(meta))
    check("besøgene læses på den normaliserede rute",
          visits_by_route({"/da/": 31}).get("/da") == 31
          and visits_by_route({"/da": 31}).get("/da") == 31,
          f"med skråstreg={visits_by_route({'/da/': 31})} "
          f"uden={visits_by_route({'/da': 31})}")

    with tempfile.TemporaryDirectory() as tmp:
        rep = Path(tmp)

        # 7. En rapport uden tal må ikke finde på et tal. Uden kontrollen
        #    kunne porten skrive `0` og få det læst som "ingen har besøgt
        #    siden" — det er fraværende måling, ikke et tal.
        (rep / "2026-40.json").write_text(json.dumps(
            {"iso_week": "2026-40", "traffic": {"available": False,
                                               "top_paths": []}}),
            encoding="utf-8")
        got, meta2, _ = traffic_rows(rep)
        check("ingen rapport med tal giver ingen besøg og ingen kilde",
              got == {} and meta2.get("file") is None,
              json.dumps(meta2, ensure_ascii=False))
        check("teksten siger fraværende måling, ikke et tal",
              "fraværende måling" in A.traffic_note(meta2), A.traffic_note(meta2))

        # 8. Nyeste rapport med tal vinder, og alderen regnes fra `generated_at`.
        (rep / "2026-40.json").write_text(json.dumps(
            {"iso_week": "2026-40", "generated_at": "2026-09-29",
             "traffic": {"top_paths": [{"path": "/json-formatter",
                                        "visits": 11}]}}),
            encoding="utf-8")
        (rep / "2026-41.json").write_text(json.dumps(
            {"iso_week": "2026-41", "generated_at": "2026-09-30",
             "traffic": {"available": False, "top_paths": []}}),
            encoding="utf-8")
        got2, meta3, _ = traffic_rows(rep)
        check("rækker trafik fra rapporten der har den",
              got2.get("/json-formatter") == 11, json.dumps(got2, ensure_ascii=False))
        # Alderen måles mod **dagens dato**, ikke mod en håndlavet dag. Datoen
        # er derfor dagens, så kontrollen er sand uanset hvilken dag porten
        # kører — en test der krævede `age_days == 1` ville være rød i morgen
        # og grøn i dag, altså en grøn cirkel der ligner en måling.
        i_dag = date.today()
        (rep / "2026-40.json").write_text(json.dumps(
            {"iso_week": "2026-40", "generated_at": i_dag.isoformat(),
             "traffic": {"top_paths": [{"path": "/json-formatter",
                                        "visits": 11}]}}),
            encoding="utf-8")
        _g4, meta3b, _ = traffic_rows(rep)
        check("alderen regnes fra dagens dato, og den nyere rapport uden "
              "trafik tælles med",
              meta3b.get("age_days") == 0 and meta3b.get("newer_without") == 1,
              json.dumps(meta3b, ensure_ascii=False))

        # 9. SYNtetiske rapporter. Formen findes ikke i `reports/weekly/`
        #    lige nu, så den bygges syntetisk — ellers ville kontrollen være
        #    grøn af den simple grund at porten ingenting kunne se.
        #
        #    Den syntetiske rapport er **nyere** end alt andet og har et stort
        #    tal: må den bruges som målt trafik, skriver portens egen udskrift
        #    et opdigtet besøg som om det var en kundes, og netop det tal
        #    bliver citeret i de næste iterationers planer.
        (rep / "2099-01.json").write_text(json.dumps(
            {"iso_week": "2099-01", "generated_at": "2099-01-01",
             "synthetic": True,
             "traffic": {"top_paths": [{"path": "/json-formatter",
                                        "visits": 999999}]}}),
            encoding="utf-8")
        got3, meta4, skipped3 = traffic_rows(rep)
        check("en syntetisk rapport bruges ikke som trafik",
              got3.get("/json-formatter") == 11, json.dumps(got3, ensure_ascii=False))
        check("den syntetiske rapport navngives, ikke bare springes over",
              skipped3 == ["2099-01.json"], f"{skipped3}")
        check("kilden er den ægte rapport, ikke den syntetiske",
              meta4.get("week") == "2026-40", json.dumps(meta4, ensure_ascii=False))
        # `traffic_source` tæller de filer *den* ser, altså de ægte i
        # spejlingen. Uden denne linje ville porten sige "1 rapport læst" om
        # en mappe med tre, og alderen ville forklares med det modsatte.
        check("tællingen af rapporter tæller også de sprunget over",
              meta4.get("reports") == 3, json.dumps(meta4, ensure_ascii=False))

        # 9b. MUTATION: den delte læser fra artikelporten læser *alle*
        #     `*.json`, så uden portens egen regel overtager den syntetiske
        #     rapport målingen. Beviset på at kontrol 9 kan fejle.
        naiv, _naiv_meta = A.traffic_source(rep)
        check("mutation: uden reglen overtager den syntetiske rapport målingen",
              naiv.get("/json-formatter") == 999999,
              json.dumps(naiv, ensure_ascii=False))

    # 10. Listen på disk er i synk med målingen, og den er ikke hele korpus.
    #     Uden den første kontrol er portens grønne svar værdiløst; uden den
    #     anden er den en konstant rød port, og en sådan bliver slået fra.
    ratchet: dict[str, dict[str, str]] = {}
    ratchet_fejl = ""
    try:
        ratchet = read_ratchet()
    except RatchetFejl as exc:
        ratchet_fejl = str(exc)
    check("ratchetfilen kan læses som en måling", not ratchet_fejl,
          ratchet_fejl)
    # Ratchetfilen på disk skal have de destinationer porten måler i dag. Det
    # måles på **destination-sættet**, ikke på parene og ikke på lister med
    # gentagelser: filen er skrevet af en tidligere kørsel, så et anker-id kan
    # være ændret siden da, og det er ikke det, synk-kontrollen skal fange.
    # Mængder sammenlignes som sæt, fordi to anker på samme side kan pege på
    # samme destination — parformen har dem begge, listformen tæller dem to.
    check("ratcheten måler de veje porten målte i dag",
          {x: set(v.values()) for x, v in ratchet.items()}
          == {x: set(v) for x, v in measured_paths(table).items()},
          f"{len(ratchet)} linjer mod {len(measured_paths(table))} målte")
    real_problems = dom(table)
    check("listen er i synk med målingen", not real_problems,
          f"{len(real_problems)} problem(er)")
    check("listen er ikke hele korpus (den ville være meningsløs)",
          len(blind_now(table)) < len(table) - 5,
          f"blind={len(blind_now(table))} korpus={len(table)}")
    check("mindst én værktøjsside har en betalt vej (ellers dømmer intet)",
          any(r["paid"] for r in table),
          f"{sum(1 for r in table if r['paid'])}/{len(table)}")
    check("listen er en ratchet, så den er skrevet med `--write`",
          set(("note", "source", "measured", "blind"))
          <= set(json.loads(BLIND.read_text(encoding="utf-8"))), "")
    check("ratchetfilen er skrevet med `--write` (note, source, measured, paths)",
          set(("note", "source", "measured", "paths"))
          <= set(json.loads(RATCHET.read_text(encoding="utf-8"))), "")

    # 11. Ratcheten over de betalte veje (opgave 8). Herfra dømmer porten
    #     *hvilken* vej en side har, ikke om den har en — og det er hele
    #     forskellen. Alle kontrollerne bygger syntetiske rækker ud fra den
    #     **målte** række, så de er ikke afhængige af hvilken side der lige
    #     har en vej (samme regel som kontrol 5).
    #
    #     Rækken vælges fra tabellen, og dens destinationer bruges som det,
    #     der skal *mister* en: så er fejlretningen beviselig. Uden mutationerne
    #     nederst kunne `path_problems()` være `lambda *_: []` og alle de andre
    #     kontroller være grønne af den forkerte grund.
    målt_række = next((r for r in table if judged(r) and len(r["paid"]) > 1),
                      None) or next((r for r in table if judged(r) and r["paid"]),
                                    None)
    if målt_række is None:
        check("målingen har en side med en betalt vej at dømme", False,
              "ingen dømt side har en vej")
    else:
        rute = målt_række["route"]
        veje = sorted(set(målt_række["paid"]))
        # Ratchetformen er par: hvert anker med sin destination. Nøglerne
        # vælges blandt sidens **egne** anker, så kontrollen ikke afhænger af
        # et håndskrevet anker-id (opgave 10: en selvtest må ikke fejle fordi
        # den side den målte, har fået et nyt id).
        # Ratchetformen er par: hvert anker med sin destination. Parene er
        # sidens **egne** — `tool_rows()` målte dem med `A.paid_anchors()` —
        # så kontrollen ikke afhænger af et håndskrevet anker-id (opgave 10: en
        # selvtest må ikke fejle fordi den side den målte, har fået et nyt id).
        hel = {rute: dict(målt_række.get("ankere") or {})}
        ankerliste = sorted(hel[rute])
        check("målingen har mindst to anker at bytte om",
              len(ankerliste) >= 2 and len(set(hel[rute].values())) >= 2,
              f"{rute} har {len(ankerliste)} anker")
        base = [målt_række]
        check("ratcheten som ligger på disk gør målingen grøn",
              not path_problems(base, hel), f"{path_problems(base, hel)}")
        # Den konkrete fejl fra målingen: siden beholder *én* vej og mister
        # den anden. Alle gamle porte var grønne, fordi de talte veje.
        # Mutationen skal fjerne **ankeret** og ikke kun tallet: ratcheten
        # dømmer par, så en række hvis `ankere` stadig har begge destinationer
        # har ikke mistet noget, uanset hvad `paid` siger.
        mistet_række = [dict(
            målt_række, paid=veje[:1],
            anker={a: v for a, v in hel[rute].items()
                   if v in set(veje[:1])})]
        mistet_række[0]["ankere"] = mistet_række[0]["anker"]
        check("en side der mister ét målt anker er rød",
              any("MISTET BETALT VEJ" in p
                  for p in path_problems(mistet_række, hel)),
              f"{path_problems(mistet_række, hel)[:1]}")
        # **OMBYTNING** — den fejl ratcheten på destinationer ikke kunne se.
        # Mutationen bygger ombytningen af sidens *egne* par: den beholder
        # præcis de samme destinationer, kun ankerne bytter plads, så
        # destinations-sættet er uændret. Det er derfor en gammel ratchet var
        # grøn på præcis denne side, og det er den dyreste af de to fejl:
        # læseren ser navnet og prisen på knappen han klikker på og bliver
        # trukket for den anden vare. Kræver mindst to anker — ellers er der
        # intet at bytte, og kontrollen ville være grøn af den forkerte grund.
        if len(ankerliste) >= 2 and len(veje) >= 2:
            ombyttet = dict(hel[rute])
            nøgler = sorted(ombyttet)[:2]
            ombyttet[nøgler[0]], ombyttet[nøgler[1]] = (
                ombyttet[nøgler[1]], ombyttet[nøgler[0]])
            # Nøglen på rækken er `ankere` — samme som `tool_rows()` skriver.
            # Den skal have de ombyttede par, ellers dømmer porten uændrede
            # anker og mutationen grønnes af den forkerte grund at den aldrig
            # blev sat ind.
            række_byttet = [dict(
                målt_række,
                paid=sorted(set(ombyttet.values())),  # destinationsmængden er uændret
                anker=ombyttet)]
            række_byttet[0]["ankere"] = ombyttet
            domme = path_problems(række_byttet, hel)
            check("MUTATION: to anker der bytter destination er rød, selv om "
                  "sættet af destinationer er uændret",
                  any("OMBYTTET BETALT VEJ" in p for p in domme)
                  and not any("MISTET BETALT VEJ" in p for p in domme),
                  f"{domme[:1]}")
            # Mutationen skal være en *forskydning*, ikke en tilfældighed:
            # hvis dommen kun rammer fordi destinationssættet røgede, ville
            # kontrol 2 ovenfor have fanget den. Derfor kræves OMBYTTET og
            # forbudt MISTET — og destinationssættet skal være identisk.
            check("mutation: dommen er ombytningen og ikke en mistet vej",
                  sorted(set(ombyttet.values())) == sorted(set(veje))
                  and any("OMBYTTET BETALT VEJ" in p for p in domme)
                  and not any("MISTET BETALT VEJ" in p for p in domme),
                  f"{sorted(set(ombyttet.values()))} vs {sorted(set(veje))}")
        else:
            check("målingen har to anker at bytte om", False,
                  f"{rute} har {len(ankerliste)} anker og {len(veje)} veje")
        # Flere veje er **ikke** røde: det er fremskridt, og `--write` skriver
        # dem uden `--force`. Ellers kunne man ikke lappe en side.
        check("en side der får en ekstra vej ikke er rød",
              not path_problems([dict(målt_række, paid=veje + ["/support"])],
                                hel), "")
        # Død og tom linje: en rute der ikke længere er en dømt værktøjsside,
        # og en linje der låser intet. Uden dem kunne ratcheten tømmes ved at
        # skrive den, hvilket er præcis hvad den skal forhindre.
        check("en linje på en rute der ikke findes mere er rød",
              any("DØD VEJ-LINJE" in p
                  for p in path_problems(base, {"/findes-ikke": ["/x"]})), "")
        check("en linje uden destinationer er rød",
              any("TOM VEJ-LINJE" in p
                  for p in path_problems(base, {rute: []})), "")
        # Ratcheten skal ikke dømme det den ikke kan se: chrome-sider,
        # erklærede sider og 404-ruter er målt men ikke dømt, så de hører
        # ikke i filen. En linje på sådan en rute er en død linje, ikke en
        # måling — ellers kunne byggens eget chrome låse porten fast.
        check("ratcheten dømmer kun dømte sider",
              not measured_paths([dict(målt_række, file=None, publiceret=True,
                                       domains=["mahope.tools"],
                                       domain="mahope.tools")]), "")
        # De to læsere skal være enige om **hvilke** links der er betalte.
        # `paid` er listen (med gentagelser) og `ankere` er parene; de bruges
        # i to forskellige domme, så en divergens ville give to sandheder om
        # samme side. Målt på hele korpus, ikke på én række — en fejl der
        # kun opstår på sider med to anker til samme destination ville ellers
        # blive grøn her. Mængderne sammenlignes som sæt, fordi parformen
        # mister en gentagelse som listen tæller to gange.
        afvigende = sorted(
            r["route"] for r in table
            if set((r.get("ankere") or {}).values()) != set(r["paid"]))
        check("mutation: de to læsere er enige om sidens betalte links",
              not afvigende,
              f"{len(afvigende)} række(r) afviger, fx {afvigende[:3]}")
        # Og den skal kunne fejle: en række hvor `ankere` er fjernet skal
        # afvige. Uden denne linje kunne kontrollen ovenfor være
        # `not True` og grøn af den forkerte grund.
        check("mutation: en række uden anker afviger fra sin egen liste",
              set((målt_række.get("ankere") or {}).values()) == set(målt_række["paid"])
              and (set({}.values()) != set(målt_række["paid"])), "")
        # MUTATION: samme måling uden dommen. Uden denne linje kunne
        # `path_problems()` ignorere sit input og være grøn af den forkerte
        # grund, at porten ingenting kan se.
        check("mutation: en målt forsvunden vej uden ratchet er grøn",
              not path_problems([dict(målt_række, paid=[])], {}), "")

    # 11b. `--write` må ikke selv kunne frigive ratcheten. Uden `--force` skal
    #     en forsvunden vej nægtes, og fejlen skal **navngive** den — ellers er
    #     den en afvisning man læser forbi.
    with tempfile.TemporaryDirectory() as tmp:
        sti = Path(tmp) / "ratchet.json"
        sti.write_text(json.dumps({"paths": {"/a": {"knap-1": "/x", "knap-2": "/y"}}},
                                  ensure_ascii=False), encoding="utf-8")
        retning, fejl = _write_ratchet({"/a": {"knap-1": "/x"}}, False, sti)
        check("en forsvunden vej kræver --force",
              not retning and "/y" in fejl, f"{retning!r} / {fejl!r}")
        # Én skrivning, ét resultat: `_write_ratchet` skriver, så to kald i
        # samme kontrol ville måle den anden fil og grønne af den forkerte
        # grund. Mutationen er at `--force` faktisk frigiver den samme linje.
        # Tallet er 2 og ikke 1, fordi frigivelsen tæller *begge* former den
        # tabte: ankeret der forsvandt, og destinationen der så også er væk.
        tvungen, tvungen_fejl = _write_ratchet({"/a": {"knap-1": "/x"}}, True, sti)
        check("mutation: samme skrivning med --force frigiver linjen",
              tvungen.startswith("2 ") and not tvungen_fejl,
              f"{tvungen!r} / {tvungen_fejl!r}")
        check("ratchetfilen efter --write har de fire nøgler",
              set(("note", "source", "measured", "paths"))
              <= set(json.loads(sti.read_text(encoding="utf-8"))), "")
        # MIGRATION fra listeformen. Den skal ske uden `--force` når intet er
        # tabt — den gamle form kan ikke se ombytninger, så hun må ikke bruges
        # til at frigive noget, men hun må heller ikke låse en korrekt
        # skærpelse ude. Og hun skal nægtes, når noget *er* tabt.
        gammel_sti = Path(tmp) / "gammel.json"
        gammel_sti.write_text(json.dumps({"paths": {"/a": ["/x", "/y"]}},
                                         ensure_ascii=False), encoding="utf-8")
        ret, mig_fejl = _write_ratchet({"/a": {"kn1": "/x", "kn2": "/y"}}, False,
                                       gammel_sti)
        check("listenform migrerer uden --force når intet destination er tabt",
              bool(ret) and "migreret" in ret and not mig_fejl,
              f"{ret!r} / {mig_fejl!r}")
        check("mutation: listenform med en tabt destination kræver --force",
              (lambda r, f: (not r) and "/y" in f)(
                  *_write_ratchet({"/a": {"kn1": "/x"}}, False, gammel_sti)),
              f"{_write_ratchet({'/a': {'kn1': '/x'}}, False, gammel_sti)}")
        # `read_ratchet()` skal **nægte** listeformen. Ellers kunne næste
        # iteration skrive den tilbage ved en fejl, og porten ville grønne på
        # en måling der ikke kan se en ombytning. Filen må være frisk: de to
        # migrationskontroller ovenfor skrev den om i par-form.
        frisk = Path(tmp) / "frisk-gammel.json"
        frisk.write_text(json.dumps({"paths": {"/a": ["/x", "/y"]}},
                                    ensure_ascii=False), encoding="utf-8")
        nægtet = False
        try:
            read_ratchet(frisk)
        except RatchetFejl:
            nægtet = True
        check("listeformen nægtes som ratchet (den kan ikke se ombytninger)",
              nægtet, "read_ratchet() læste listeformen som en måling")
        # En manglende ratchetfil kan oprettes ved første skrivning
        check("en manglende ratchetfil kan oprettes ved første skrivning",
              _write_ratchet({"/a": {"kn1": "/x"}}, True, Path(tmp) / "ny.json")[0],
              "")
        sti.write_text("{ikke json", encoding="utf-8")
        check("en ødelagt ratchetfil er en fejl, ikke 'ingen linjer'",
              "kan ikke læse" in _write_ratchet({"/a": {"/x"}}, True, sti)[1],
              f"{_write_ratchet({'/a': ['/x']}, True, sti)}")
        check("mutation: en slettet fil giver aldrig grønt i judge()",
              any("RATCHET KUNNE IKKE LÆSES" in p
                  for p in dom(table, ratchet_sti=Path(tmp) / "slet.json")),
              "")

    failed = 0
    for name, ok, detail in checks:
        if ok:
            print(f"  ok   {name}" + (f" ({detail})" if detail else ""))
        else:
            failed += 1
            print(f"  FEJL {name}" + (f" ({detail})" if detail else ""), file=sys.stderr)
    print(f"tool-paid-path-selftest: {len(checks) - failed}/{len(checks)} kontroller bestået")
    return 1 if failed else 0


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quiet", action="store_true", help="kun dommene")
    parser.add_argument("--limit", type=int, default=30, help="hvor mange rækker")
    parser.add_argument("--write", action="store_true",
                        help="skriv blind-listen fra målingen (kræver --force)")
    parser.add_argument("--force", action="store_true",
                        help="bekræft --write: listen må kun krympe")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    visits, meta, skipped = traffic_rows()
    table = tool_rows(visits=visits)

    if args.write:
        measured = blind_now(table)
        current = json.loads(BLIND.read_text(encoding="utf-8"))
        existing = list(current.get("blind") or [])
        added = sorted(set(measured) - set(existing))
        if added and not args.force:
            print("tool-paid-path: --write ville tilføje linjer:\n  "
                  + "\n  ".join(added)
                  + "\nListen må kun krympe. Ret siden, eller kør med --force "
                    "og skriv en grund i filen.", file=sys.stderr)
            return 1
        # Skriv kun `blind`. De øvrige nøgler er filens egen dokumentation
        # (`note` siger hvad listen *er*, `source` hvordan den måles,
        # `measured` hvornår) — samme fejl som artikelporten gjorde første
        # gang, da `--write` skrev `{"blind": …}` og slettede dem alle tre.
        out = dict(current)
        out["blind"] = measured
        out["measured"] = date.today().isoformat()
        BLIND.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")
        # Ratcheten over de betalte veje skrives i samme kørsel, så de to
        # filer aldrig kan beskrive forskellige øjeblikke. En forsvunden vej
        # kræver `--force` — ellers ville porten kunne frigives ved at køre
        # `--write`, og så er den ikke en ratchet længere. En *ny* vej er
        # derimod fremskridt og skrives uden samme bevis.
        sti, fejl = _write_ratchet(measured_anchors(table), args.force)
        if fejl:
            print(f"tool-paid-path: {fejl}", file=sys.stderr)
            return 1
        if sti:
            print(f"tool-paid-path: ratchet {sti} — {RATCHET.name} skrevet")
        left = sorted(set(existing) - set(measured))
        # Antallet skriver *retningen*, ikke etage minus. Den gamle formel
        # `len(existing) - len(measured)` sagde "42 færre" da den såede listen
        # fra 0 til 42 — altså at den blev mindre, mens den blev større. Det er
        # præcis den påstand porten skal kunne bruges til, så den må ikke
        # regnes frem.
        if left:
            retning = f"{len(left)} færre"
        elif added:
            retning = f"{len(added)} flere (krævede --force)"
        else:
            retning = "uændret"
        print(f"tool-paid-path: skrev {len(measured)} linjer ({retning})")
        for route in left:
            print(f"  forlod listen: {route}")
        return 0

    if not args.quiet:
        _print_ranking(table, args.limit, meta, skipped)

    problems = dom(table)
    for problem in problems:
        print(f"tool-paid-path: {problem}", file=sys.stderr)
    if problems:
        print(f"tool-paid-path: RØD — {len(problems)} problem(er).", file=sys.stderr)
        return 1
    print("tool-paid-path: GRØN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
