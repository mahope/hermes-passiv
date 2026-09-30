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

**Porten dømmer to ting, og begge kan blive røde:**

- En værktøjsside **uden** betalt vej som ikke står i
  `tools/tool_paid_path_blind.json` er en ny blind værktøjsside.
- En linje i listen der **har** fået en betalt vej er en død linje. Listen er
  en *ratchet*: den må kun krympe.

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
BUILD = ROOT / "build_sites.py"

# Navnet på den erklæring, en side kan bære om at den intet sælger. Den er
# kort, så den ikke kan forveksles med en rigtig bruger-meta, og den starter
# med `x-`, fordi den ikke er en standardegenskab ved HTML.
DECL_NAME = "x-no-paid-path"


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


def judge(rows: list[dict] | None = None, doc: dict | None = None) -> list[str]:
    """Portens domme. Alle skal være grønne."""
    table = rows if rows is not None else tool_rows()
    doc = doc if doc is not None else json.loads(BLIND.read_text(encoding="utf-8"))
    known = list(doc.get("blind") or [])
    measured = blind_now(table)
    by_route = {r["route"]: r for r in table}
    problems: list[str] = []

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
    #    en mutation af `site/` være grøn.
    probe = ROOT / "site" / "contrast-checker.html"
    check("læser en værktøjside med betalt vej i egen tekst",
          bool(A.paid_links(SITE, probe, offers)),
          f"{len(A.paid_links(SITE, probe, offers))} vej(er)")

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
    check("erklæringen læses kun fra dens egen meta",
          no_paid_declaration(SITE / "json-formatter.html") is None
          and bool(no_paid_declaration(SITE / "site-icons.html")), "")

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
    real_problems = judge(table)
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

    problems = judge(table)
    for problem in problems:
        print(f"tool-paid-path: {problem}", file=sys.stderr)
    if problems:
        print(f"tool-paid-path: RØD — {len(problems)} problem(er).", file=sys.stderr)
        return 1
    print("tool-paid-path: GRØN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
