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
              inventory: dict | None = None, visits: dict | None = None) -> list[dict]:
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
    """
    catalog = catalog if catalog is not None else json.loads(
        CATALOG.read_text(encoding="utf-8")
    )
    inventory = inventory if inventory is not None else json.loads(
        INVENTORY.read_text(encoding="utf-8")
    )
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
        })
    # Trafik først, så en side med målte læsere altid ligger over en side
    # uden. `visits` er `None` når ingen rapport har tal, og `or 0` gør den
    # til 0 — så en fraværende måling kan ikke slå en rigtig.
    rows.sort(key=lambda r: (-(r["visits"] or 0), -r["links"], r["route"]))
    return rows


def judged(row: dict) -> bool:
    """Måles porten den her række overhovedet?

    To former er **målt men ikke dømt**, og begge ville give en rød port i dag
    af en fejl der ikke er en fejl:

    - **Ruten har ingen fil i `site/`.** Målt 30/9: `/bulk-url-checker`,
      `/security-headers-checker` og `/tools` står i inventaret og serveres
      som 404. De har ingen købsknap at miste, så at kræve en vej på dem ville
      kræve at oprette en side, porten ikke kan måle værdien af.
    - **Domænet udgives ikke.** Målt 30/9: `/bugbottle-demo` ligger på
      `bugbottle.dev`, som ikke står i deploy-matricen. Det er et ❓ (en
      beslutning Mads skal tage), ikke en mangel, og dom 4/7 i artikelporten
      har samme regel.

    Begge skrives i udskriften, så de kan *ses* at porten springer dem over i
    stedet for at have glemt dem.
    """
    return bool(row["file"]) and row["publiceret"]


def blind_now(rows: list[dict] | None = None) -> list[str]:
    """De dømte værktøjssider uden betalt vej — den ærlige arbejdskø."""
    table = rows if rows is not None else tool_rows()
    return sorted(r["route"] for r in table if judged(r) and not r["paid"])


def judge(rows: list[dict] | None = None, doc: dict | None = None) -> list[str]:
    """Portens to domme. Begge skal være grønne."""
    table = rows if rows is not None else tool_rows()
    doc = doc if doc is not None else json.loads(BLIND.read_text(encoding="utf-8"))
    known = list(doc.get("blind") or [])
    measured = blind_now(table)
    by_route = {r["route"]: r for r in table}
    problems: list[str] = []

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
        elif row["file"] is None:
            why = "ruten har ingen kildefil i site/"
        elif not row["publiceret"]:
            why = f"domænet {row['domain']} udgives ikke"
        else:
            why = f"den har nu {row['knapper']} købsknap(per), så den er dækket"
        problems.append(
            f"DØD LINJE i listen: {route} er ikke længere i den målte klasse "
            f"— {why}. Fjern den fra tools/tool_paid_path_blind.json — listen "
            f"må kun krympe."
        )
    if len(known) != len(set(known)):
        problems.append("listen har dubletter; den er en mængde, ikke en liste.")
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
    chrome = {(r.rstrip("/") or "/") for r in A.frontpage_routes()}
    check("ser engelske værktøjssider",
          len([r for r in routes if not r.startswith("/da")]) > 40,
          f"EN={sum(1 for r in routes if not r.startswith('/da'))}")
    check("ser danske værktøjssider",
          len([r for r in routes if r.startswith("/da")]) > 2,
          f"DA={sum(1 for r in routes if r.startswith('/da'))}")
    check("artikler er ikke i værktøjsklassen", not (routes & artikler),
          f"{len(routes & artikler)} overlap")
    check("forsider er ikke i værktøjsklassen", not (normaliseret & chrome),
          f"{sorted(normaliseret & chrome)}")
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
    #    og en med vej skal ikke. Begge former findes i `site/` i dag, så de
    #    læses fra disk — men dømmes på en tabel med præcis den ene side, så
    #    portens egen klasse (43 linjer) ikke forurenser testen.
    with_vej = next(r for r in table if r["file"] == "contrast-checker.html")
    without_vej = next(r for r in table if r["file"] == "json-formatter.html")
    rød = judge([with_vej, without_vej], {"blind": []})
    check("en side uden vej gør porten rød med filnavn",
          any("json-formatter.html" in p and "NY BLIND VÆRKTØJSSIDE" in p
              for p in rød), f"{len(rød)} problem(er)")
    check("en side med vej er ikke i den røde besked",
          not any("contrast-checker.html" in p for p in rød),
          f"{[p[:70] for p in rød]}")
    check("kun en side med vej giver grønt",
          not judge([with_vej], {"blind": []}), "")
    check("beskeden siger hvor mange indgående links siden har",
          any("15 indgående links" in p for p in rød),
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
    # `judged()` er den undtagelse, og den skal kunne fejle på hver af sine to
    # halvdele. Uden denne kontrol kunne `judged()` blive `lambda r: True` og
    # de to kontroller ovenfor stadig være grønne, fordi de dømmer en port der
    # slet ikke bruger den.
    check("judged() afviser en rute uden fil", not judged(dict(without_vej, file=None)),
          "")
    check("judged() afviser et domæne uden i matricen",
          not judged(dict(without_vej, publiceret=False)), "")
    check("judged() accepterer en rigtig værktøjsside", judged(without_vej), "")
    # De fire undtagne ruter findes rigtigt i korpus, så klasserne er ikke tomme
    # af en fejl i `judged()`.
    undtagne = {r["route"]: (r["file"], r["publiceret"])
                for r in table if not judged(r)}
    check("de undtagne ruter er de fire målte, ikke tilfældige",
          set(undtagne) == {"/bulk-url-checker", "/security-headers-checker",
                            "/tools", "/bugbottle-demo"},
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
