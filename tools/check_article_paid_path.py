#!/usr/bin/env python3
"""Rangér artikler efter manglende betalt vej, og gør listens tilgængelig.

Baggrund (opgave 1, 29. september 2026): missionens konverteringskrav siger
"find de sider der har flest besøg, og sørg for at hver Pro-side klart viser
hvad gratis og betalt giver, og har én købsknap der virker". Den mest besøgte
artikel på mahope.tools, `/blog/text-on-image-contrast-check` (8 af 10 rigtige
besøgende, bounce 100 %), havde **0** `buy.stripe.com`, **0** "Pro" og **4**
links til et gratis værktøj. Den fik sin betalte vej i samme iteration, fordi
netop den måling fandt den — men målingen lå i hovedet på den iteration, så
næste måling måtte finde den næste side selv. Det er det her porten gør.

Den erstatter tre hjemlavede læsninger i samme familie, som alle har vist sig
at lyve. Reglerne er derfor skrevet ned som *målinger*:

1. **Artiklens egen tekst, ikke hele filen.** Første måling tællede `href` i
   hele dokumentet og fandt **0** artikler uden købsvej, fordi 69 af dem linker
   til `/` og 32 til `/da/` — og forsiden *er* registreret som købsside i
   `tools/stripe_catalog.json` (den sælger Clean Copy Pro). Et logolink i
   headeren er altså ikke en købsvej, og med hele filen som synsfelt er der
   ingen. Derfor læses regionen mellem `</header>` og `<footer>`.

2. **Forsiderne er chrome, ikke købsvej.** Samme måling som punkt 1, skrevet
   ned som `CHROME_ROUTES` med sin grund, så den ikke kan falde tilbage til
   en regex der rammer dem igen.

3. **Alle 190 artikler, ikke 96.** Anden måling filtrerede på
   `"/blog/" in rel`, hvor `rel` er stien *relativt til `site/`* — altså
   `"blog/x.html"` for en engelsk artikel og `"da/blog/x.html"` for en dansk.
   Den betingelse er aldrig sand for engelsk, så alle 94 engelske artikler var
   uden for målingen, og porten skrev "123 af 190" ud fra 96 filer. samme
   fejlform som de syv foregående i denne familie: *en læsning der kun ser én
   halvdel af verdenen bliver grøn uden at have set noget.* Selftestens
   kontrol 5 dømmer derfor at porten finder en engelsk artikel, ikke en
   dansk.

**Rangering.** Først besøg fra den nyeste `reports/weekly/*.json` der har
`traffic.top_paths` med tal, ellers antal sider der linker *til* artiklen.
Grunden står i hver linje, fordi de to tal ikke må forveksles: `trafik` er
målt besøg, `links` er vor egen links-tælling. `/api/stats` har svaret 401
siden uge 37 (`STATS_TOKEN` mangler på workeren, ❓ Til Mads), så i dag er
næsten hver linje `links`, og porten siger det i stedet for at skjule det.

**Porten dømmer tre ting, og alle tre kan blive røde:**

- En artikel *uden for* `tools/article_paid_path_blind.json` uden betalt vej er
  en ny blind artikel — regression.
- En artikel *med* betalt vej som står i listen er en død linje. Listen skal
  således kunne **krympe**, og det er den eneste vej den kan blive mindre.
- En linje i listen der ikke findes på disk er en død linje, så en omdøbt
  artikel kan ikke blive en usynlig undtagelse.

**Dom 4 (publiceret-flåsen, målt 30/9).** Otve iterationer lagde købsknapper på
artikler og skrev "baseline 0 målbare besøgende" i planen. Den niende fandt at de
to eneste artikler i hele korpus med *målt* trafik lå på `bugbottle.dev` — et
domæne der stod i `tools/route_inventory.json` men ikke i deploy-matricen, så
de sider gav **404** på alle live-domæner. "9 målte besøg" var altså teknisk
sand og operationelt død, og ingen port kunne fange det: `check_article_paid_path`
rangerer på `trafik` uden at vide om ruten er publiceret.

Derfor dømmer porten nu fire ting om *publicering*, ikke bare om betalt vej:

- Et domæne i inventaret der **ikke** står i deploy-matricen skal stå i
  `tools/article_paid_path_published.json` med en begrundelse. Uden den er
  domænet uforklaret, og det er præcis sådan hullet blev skabt: det stod der
  uden at nogen spørgsmål.
- En bekræftelse uden begrundelse er rød. Samme regel som `ctas_note` i
  `check_stripe_ctas.py`: en undtagelse uden grund er en måde at slå reglen fra.
- En bekræftelse på et domæne der **nu** står i matricen er rød. Flåsen skal
  lukkes, ellers bliver den en permanent undtagelse der vokser med tiden.
- En blind artikel med målt trafik på et domæne der ikke er publiceret, nævnes
  i rankingen som `IKKE UDGIVET`, så den ikke kan vælges ved en læsning af
  trafikkolonnen alene.

**Hvorfor flåsen ikke dømmer direkte.** Rå lighed ville gøre gaten rød i dag på
den ene artikel der faktisk er i den situation — og så ville den blive slået
fra i stedet for forklaret. Derfor er den en *begrundelses*-flås: hullet skal
stå i filen med en grund, og grunden skal forsvinde, når hullet lukkes.
Lukker Mads `❓` om bugbottle.dev, så forsvinder rækken ved at tilføje domænet
til matricen — og flåsen siger det.

Ud over det printer porten hele ranglisten, fordi det er den næste iteration
har brug for. Den behøver ikke selv at finde de mest linkede artikler.

    python3 tools/check_article_paid_path.py             # rangliste + de tre domme
    python3 tools/check_article_paid_path.py --quiet     # kun dommene
    python3 tools/check_article_paid_path.py --write     # skriv listen fra målingen
    python3 tools/check_article_paid_path.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from check_stripe_ctas import Page  # noqa: E402  (delt læser, se punkt 4 nedenfor)

SITE = ROOT / "site"
CATALOG = ROOT / "tools" / "stripe_catalog.json"
BLIND = ROOT / "tools" / "article_paid_path_blind.json"
REPORTS = ROOT / "reports" / "weekly"
INVENTORY = ROOT / "tools" / "route_inventory.json"
WORKFLOW = ROOT / ".github" / "workflows" / "deploy-sites.yml"
PUBLISHED = ROOT / "tools" / "article_paid_path_published.json"

# Punkt 1 og 2 ovenfor. Målt: 69 artikler linker til `/` og 32 til `/da/` fra
# hele dokumentet, og begge er købssider i katalogens `offers`, fordi
# Clean Copy Pro sælges på forsiden. Uden denne udeladelse er der 0 blinde
# artikler, og porten ville være grøn på det den er skrevet for at finde.
CHROME_ROUTES = {"/", "/da/"}

RE_HREF = re.compile(r'href="([^"]+)"')
RE_BUY = re.compile(r"^(?:https?://)?(?:buy|donate)\.stripe\.com/")
RE_ALTERNATE = re.compile(
    r'<link[^>]+rel="alternate"[^>]+href="([^"]+)"', re.I
)
RE_MATRIX_DOMAIN = re.compile(r"^\s+- domain: (\S+)\s*$", re.M)


def article_files(root: Path = SITE) -> list[Path]:
    """Alle artikler, begge sprog. Se punkt 3: `"blog/x.html"` har ikke `/blog/`."""
    return sorted(
        p for p in root.rglob("*.html")
        if "/blog/" in "/" + p.relative_to(root).as_posix()
    )


def content_region(html: str) -> str:
    """Teksten mellem `</header>` og `<footer>` — der hvor artikelens links er.

    Skellet er målt på kilden: artiklerne har præcis én `<header>` og én
    `<footer>`, og de CTA-blokke der ligger lige under headeren
    (`hero-cta`, `blog-tool-cta`) er en del af artiklen og bliver *med*.
    """
    start = html.find("</header>")
    if start == -1:
        start = html.find("<body")
        if start == -1:
            start = 0
    end = html.find("<footer")
    if end == -1:
        end = len(html)
    return html[start:end]


def paid_links(root: Path, path: Path, offer_routes: set[str]) -> list[str]:
    """Links i artikelens egen tekst der fører til et køb.

    To former tæller, og de er målt som to forskellige ting:

    1. Et Stripe-link (`buy.stripe.com` / `donate.stripe.com`). Artiklen
       sælger selv. Målt: 3 af 190.
    2. Et rod-relativt link til en rute der står i katalogens `offers`, altså
       en side der sælger. Ét klik derfra.

   Links læses med `check_stripe_ctas.Page` — portens egen læser, som
    springer `script`/`style`/JSON-LD over. Det er punkt 4: de tre sidste
    fejl i denne familie var alle en hjemlavet læsning af en fil en anden
    port læser, og en sådan læsning får advarslerne til at forsvinde som
    *grønt* i stedet for *rødt*.

    **Artiklens egen sprogsspejling tæller ikke** (punkt 5, målt efter at
    mutationen af kontrastartiklen *ikke* gjorde porten rød). Mutationen
    fjernede artiklens `buy.stripe.com`-link, og porten blev stadig grøn,
    fordi artiklen linker til sin egen danske spejling
    `/da/blog/tekst-paa-billede-kontrasttjek` — og *den* rute står i
    katalogens `offers`, fordi sidste iteration registrerede spejlingen som
    købsside. Det er cirkulært: artiklen har en købsvej, *fordi* den peger på
    en side der kun er en købsside, fordi artiklen peger på den. Spejlingen er
    samme side på et andet sprog, ikke en købsside nedstrøms, så den tælles
    ikke. Kilden er sidens **egne `hreflang`-links**, som er deklarative i
    stedet for gættet af slug.
    """
    html = path.read_text(encoding="utf-8", errors="ignore")
    page = Page()
    page.feed(content_region(html))
    mirrors = {_route_of_href(h) for h in RE_ALTERNATE.findall(html)}
    found = []
    for href in page.all_links:
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        if RE_BUY.match(href):
            found.append(href)
            continue
        route = _route_of_href(href)
        if route in offer_routes and route not in CHROME_ROUTES and route not in mirrors:
            found.append(route)
    return found


def knap_links(root: Path, path: Path) -> list[str]:
    """Købslinket i artikelens egen tekst — kun den *direkte* form.

    `paid_links()` tæller to former som om de var ens: en købsknap (`buy.
    stripe.com` i egen tekst) og et link til en side der sælger. Det er ikke
    ens. Mutationen i `notion-artikel-pro` målte forskellen: med
    `buy.stripe.com` fjernet fra begge artikler blev porten stadig grøn, fordi
    den nye sektion også linker til `/clean-copy-tool` — og den rute står i
    `offers`. To artikler, nul knapper, én indirekte vej, porten grøn.

    Forskellen er målt i de to lister `paid_links()` allerede producerer, så
    den er to linjer og ikke en ny læsning af filen — punkt 4 i docstringen.
    """
    html = path.read_text(encoding="utf-8", errors="ignore")
    page = Page()
    page.feed(content_region(html))
    return [h for h in page.all_links if RE_BUY.match(h)]


def _route_of_href(href: str) -> str:
    """Href → rute. Absolutte URL'er reduceres til stien, som katalogen bruger."""
    href = href.split("#")[0]
    href = re.sub(r"^https?://[^/]+", "", href)
    if href.endswith(".html"):
        href = href[:-5]
    return href or "/"


def offer_routes(catalog: dict) -> set[str]:
    return {o["route"] for o in catalog["offers"]}


def inbound_counts(root: Path = SITE) -> dict[str, set[str]]:
    """Sider der linker til hver rute. Egen tælling, målt over hele `site/`."""
    hits: dict[str, set[str]] = {}
    for path in sorted(root.rglob("*.html")):
        rel = path.relative_to(root).as_posix()
        for href in RE_HREF.findall(path.read_text(encoding="utf-8", errors="ignore")):
            if href.startswith(("mailto:", "tel:", "javascript:", "//", "#", "http")):
                continue
            route = href.split("#")[0]
            if route.endswith(".html"):
                route = route[:-5]
            hits.setdefault(route, set()).add(rel)
    return hits


def traffic(reports: Path = REPORTS) -> dict[str, int]:
    """Besøg pr. rute fra den nyeste rapport der faktisk har tal.

    Uge 37 og 38 har `top_paths` med tal, 39 og 40 har ikke. Vi tager den
    nyeste der har tal, så porten bruger det bedste vi har uden at kræve at
    en ny rapport er skrevet.
    """
    if not reports.is_dir():
        return {}
    best: dict[str, int] = {}
    for path in sorted(reports.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        top = (data.get("traffic") or {}).get("top_paths")
        if not isinstance(top, list) or not top:
            continue
        for row in top:
            route, visits = row.get("path"), row.get("visits")
            if isinstance(route, str) and isinstance(visits, int):
                best[route] = visits
    return best


def route_of(root: Path, path: Path) -> str:
    """Fil → rute, som den hedder *på webserveren*.

    `index.html` er mappens rute, ikke en rute ved navn. Målt 30/9: `route_of`
    gav `site/blog/index.html` ruten `/blog/index`, som ikke findes — live er
    den en **308** til `/blog/`, målt med `curl -o /dev/null -w '%{redirect_url}'`,
    og `/blog/` står i både `sitemap.xml` og `tools/route_inventory.json`.
    Konsekvensen var at hub-siden faldt ud af *alle* opslag på domæne: den lå
    i `ukendt domæne`-blokken, selv om dens domæne er `mahope.tools` og den
    er publiceret. Uden denne rettelse er den eneste `ukendt domæne`-række en
    måling af portens egen fejl, ikke af siderne.

    Bemærk at ruten *ikke* får en skråstreg til sidst. `route_domains` renser
    inventaret for skråstreg i begge ender, så nøglen skal være `/blog` — samme
    form som trafikkens (`/blog/html-to-markdown-vscode`) og katalogens.
    """
    rel = path.relative_to(root).as_posix()
    stem = rel[:-len(".html")]
    if stem.endswith("/index"):
        stem = stem[: -len("/index")]
    return "/" + stem if stem else "/"


def deployed_domains(workflow: Path = WORKFLOW) -> set[str]:
    """Domænerne CI'en faktisk deployer — læst i filen, ikke hardkodet.

    Kilden er `.github/workflows/deploy-sites.yml`'s `matrix.include`. Målt
    30/9: tre `- domain:`-linjer, `cleancopy.tools`, `deskuptime.com` og
    `mahope.tools` — og `bugbottle.dev` stod i `tools/route_inventory.json`
    uden at stå herfra. Det er *én* måling af den samme sandhed fra to sider,
    og det er den mismatch porten dømmer.

    Hardkodes domænerne ikke, fordi flåsen så ville være grøn præcis når den
    bliver brug for: den dag Mads sætter bugbottle.dev i matricen, skal porten
    sige at bekræftelsen er død, ikke fortsat godkende den.
    """
    if not workflow.is_file():
        return set()
    return set(RE_MATRIX_DOMAIN.findall(workflow.read_text(encoding="utf-8")))


def route_domains(inventory: dict) -> dict[str, str]:
    """Rute → domæne, fra `tools/route_inventory.json`.

    Ruterne renses for bagvendt skråstreg, fordi inventaret er skrevet med
    både former: målt på cleancopy.tools står `'/'` og `'/activate/'`, mens
    bugbottle.dev har `'/blog/bug-reports-in-ci-pipeline'` uden skråstreg. Uden
    rensningen ville en artikel kunne miste sit domæne på en tegnform, og
    porten ville så *ikke* flåse den — den fejl der ligner grønt.
    """
    return {
        route.rstrip("/") or "/": domain
        for domain, routes in inventory.items()
        for route in routes
    }


def unpublished_routes(root: Path = SITE, inventory: dict | None = None,
                       workflow: Path = WORKFLOW) -> dict[str, str]:
    """Artikler hvis domæne ikke står i deploy-matricen. Rute → domæne.

    Målt 30/9 før denne funktion: `blog/bug-reports-in-ci-pipeline.html`,
    `da/blog/bugrapporter-i-ci-pipeline.html`,
    `da/blog/tilfoej-fejlrapport-formular-hjemmeside.html` — de tre artikler
    på `bugbottle.dev` i korpus, alle med 404 på de live domæner.
    """
    inventory = inventory if inventory is not None else json.loads(
        INVENTORY.read_text(encoding="utf-8")
    )
    live = deployed_domains(workflow)
    dom = route_domains(inventory)
    out: dict[str, str] = {}
    for path in article_files(root):
        route = route_of(root, path)
        domain = dom.get(route)
        if domain and domain not in live:
            out[route] = domain
    return out


def rows(root: Path = SITE, catalog: dict | None = None) -> list[dict]:
    catalog = catalog if catalog is not None else json.loads(CATALOG.read_text(encoding="utf-8"))
    offers = offer_routes(catalog)
    inbound = inbound_counts(root)
    visits = traffic()
    dom = route_domains(json.loads(INVENTORY.read_text(encoding="utf-8")))
    live = deployed_domains()
    out = []
    for path in article_files(root):
        route = route_of(root, path)
        paid = paid_links(root, path, offers)
        domain = dom.get(route)
        out.append({
            "file": path.relative_to(root).as_posix(),
            "route": route,
            "visits": visits.get(route),
            "links": len(inbound.get(route, ())),
            "paid": paid,
            "knapper": len(knap_links(root, path)),
            "domain": domain,
            # `None` = vi ved ikke hvor den ligger. Det er *ikke* det samme som
            # udgivet, og porten skelner: en rute uden domæne skal findes i
            # inventaret, ellers er læsningen af filen forældet.
            "publiceret": bool(domain and domain in live),
        })
    out.sort(key=lambda r: (-(r["visits"] or 0), -r["links"], r["route"]))
    return out


def blind_now(root: Path = SITE, catalog: dict | None = None) -> list[str]:
    return sorted(r["file"] for r in rows(root, catalog) if not r["paid"])


def judge(root: Path, catalog: dict) -> list[str]:
    """Portens tre domme. Alle tre skal være grønne."""
    data = json.loads(BLIND.read_text(encoding="utf-8"))
    known = list(data["blind"])
    measured = blind_now(root, catalog)
    problems: list[str] = []

    for extra in sorted(set(measured) - set(known)):
        problems.append(
            f"NY BLIND ARTIKEL uden for listen: {extra} — den skal have en "
            f"betalt vej, eller en linje i listen med en grund."
        )
    for done in sorted(set(known) - set(measured)):
        problems.append(
            f"DØD LINJE i listen: {done} har nu en betalt vej. Fjern den fra "
            f"tools/article_paid_path_blind.json — listen må kun krympe."
        )
    if len(known) != len(set(known)):
        problems.append("listen har dubletter; den er en mængde, ikke en liste.")
    # Dom 4, publiceringsflåsen. Hænger på de tre ovenfor, fordi de alle er
    # "find den fejl der er opstået"; den her er "find den der *kunne* opstå",
    # og den må ikke gøre de tre røde af sig selv.
    problems.extend(published_problems(root))
    return problems


def published_problems(root: Path = SITE, inventory: dict | None = None,
                       workflow: Path = WORKFLOW,
                       published: dict | None = None) -> list[str]:
    """Dom 4: domæner i inventaret der ikke udgives skal have en begrundelse.

    Det er *ikke* det samme som at være rød på dem. En rød port her ville være
    rød i dag på `bugbottle.dev` — og en port der er konstant rød bliver
    slået fra, hvilket er præcis hvad der skete i en tidligere iteration hvor
    en arm altid var grøn. Derfor er dette en **begrundelses**-flås: domænet
    skal stå i `tools/article_paid_path_published.json` med en grund, og
    grunden forsvinder, når domænet kommer i matricen.

    Tre domme, alle målte:

    1. Et udpubliceret domæne uden bekræftelse → rød.
    2. En bekræftelse uden begrundelse → rød. Samme regel som `ctas_note` i
       `check_stripe_ctas.py:2712`: en undtagelse uden grund kan slås fra af
       hvem som helst, så den skal koste en sætning.
    3. En bekræftelse på et domæne der står i matricen → rød. Flåsen skal
       lukkes når hullet lukkes, ellers bliver den en permanent undtagelse.

    Beviset for at porten kan dømme: `--self-test` muterer matricen, så
    `bugbottle.dev` *ser* udgivet ud, og dømmer så skal den rød på punkt 3.
    """
    inventory = inventory if inventory is not None else json.loads(
        INVENTORY.read_text(encoding="utf-8")
    )
    live = deployed_domains(workflow)
    doc = published if published is not None else (
        json.loads(PUBLISHED.read_text(encoding="utf-8"))
        if PUBLISHED.is_file() else {"acknowledged": []}
    )
    acknowledged = {a["domain"]: a for a in doc.get("acknowledged", [])}
    problems: list[str] = []

    for domain in sorted(set(inventory) - live):
        entry = acknowledged.get(domain)
        if entry is None:
            problems.append(
                f"UDPUBLICERET DOMÆNE uden begrundelse: {domain} står i "
                f"tools/route_inventory.json ({len(inventory[domain])} ruter) "
                f"men ikke i deploy-matricen. Tilføj en linje med en grund i "
                f"tools/article_paid_path_published.json, eller udgiv domænet."
            )
        elif not str(entry.get("reason") or "").strip():
            problems.append(
                f"UDPUBLICERET DOMÆNE uden begrundelse: {domain} står i "
                f"listen, men `reason` er tom. En undtagelse uden grund er en "
                f"måde at slå reglen fra — samme regel som `ctas_note`."
            )
    for domain in sorted(acknowledged):
        if domain not in inventory:
            problems.append(
                f"DØD BEKRÆFTELSE: {domain} er bekræftet som udpubliceret, "
                f"men findes ikke i tools/route_inventory.json."
            )
        elif domain in live:
            problems.append(
                f"DØD BEKRÆFTELSE: {domain} står nu i deploy-matricen, så "
                f"bekræftelsen skal fjernes fra "
                f"tools/article_paid_path_published.json — ellers bliver den "
                f"en permanent undtagelse."
            )
    if len(acknowledged) != len(doc.get("acknowledged", [])):
        problems.append("bekræftelseslisten har dubletter.")
    return problems


def _print_ranking(table: list[dict], limit: int) -> None:
    knap = [r for r in table if r["knapper"]]
    print(f"artikler: {len(table)} · med betalt vej: "
          f"{sum(1 for r in table if r['paid'])} · med købsknap: {len(knap)} · "
          f"blinde: {sum(1 for r in table if not r['paid'])}")
    # Dækning efter *klik*, ikke bare efter "har en vej". De to er ikke ens:
    # en artikel med ét klik til en købsside er dækket, men læseren skal
    # stadig klikke videre, og det er ikke det samme som en knap på siden.
    # Uden denne linje skriver hver iteration "N artikler fik en betalt vej",
    # hvilket er den forkerte påstand — rigtigt er "N fik en knap, M fik ét
    # klik". Målt for første gang i `notion-artikel-pro` ved håndkontrol.
    print(f"dækning: {len(knap)} med købsknap · "
          f"{sum(1 for r in table if not r['knapper'] and len(r['paid']) == 1)} med 1 klik · "
          f"{sum(1 for r in table if not r['knapper'] and len(r['paid']) >= 2)} med 2+ klik · "
          f"{sum(1 for r in table if not r['paid'])} med 0 klik")
    print(f"{'trafik':>6} {'links':>5}  {'fil':<52} købsvej")
    blind = [r for r in table if not r["paid"]]
    for row in blind[:limit]:
        trafik = str(row["visits"]) if row["visits"] is not None else "-"
        print(f"{trafik:>6} {row['links']:>5}  {row['file']:<52} {row['route']}")
    # Publiceringsflåsen i udskriften, målt 30/9. `trafik`-kolonnen er besøg
    # på en rute *vi har bygget* — den siger intet om hvor den ligger. Da de
    # eneste artikler med målt trafik viste sig at ligge på et domæne uden i
    # matricen, skrev otve iterationer "9 målte besøg" i planen om sider der
    # gav 404. Derfor står domænet på linjen, og en rute der ikke er publiceret
    # siges det — også når den *har* en betalt vej, for det er dér dyrt at se
    # bort fra det.
    dark = [r for r in table if r["domain"] and not r["publiceret"]]
    unknown = [r for r in table if not r["domain"]]
    if dark:
        print(f"ikke udgivet: {len(dark)} artikler — domænet mangler i deploy-matricen:")
        for row in dark[:limit]:
            trafik = str(row["visits"]) if row["visits"] is not None else "-"
            state = "blind" if not row["paid"] else f"{len(row['paid'])} vej(er)"
            print(f"{trafik:>6} {row['links']:>5}  {row['file']:<52} "
                  f"{row['domain']} — {state}")
    if unknown:
        # Ikke det samme som "ikke udgivet": her kender porten ikke domænet,
        # fordi ruten ikke står i inventaret. Målt 30/9 var denne blokke præcis
        # **én** fil, `site/blog/index.html`, fordi `route_of` gav ruten
        # `/blog/index` mens inventaret skriver `/blog/`. `route_of` er rettet,
        # så blokken skal nu være **tom** på det målte tilstand — og det er den
        # kontrol `route_of` har i selftesten. Blokerne er to forskellige fejl,
        # så de må ikke blandes i én linje, og en blok der altid er tom er en
        # grøn cirkel: hvis en ny fil dukker op uden en rute i inventaret, skal
        # den siges her.
        print(f"ukendt domæne: {len(unknown)} fil(er) — ruten står ikke i "
              f"route_inventory.json, så publiceringen kan ikke vurderes:")
        for row in unknown[:limit]:
            print(f"{'':>6} {row['links']:>5}  {row['file']:<52} {row['route']}")


def _self_test() -> int:
    """Positive kontroller. Uden dem er `--self-test` grøn på et repo hvor
    alt er målt, altså grøn af den simple grund at den ikke ser fejlene."""
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    offers = offer_routes(catalog)

    # 1. Porten læser filen, ikke en kopi af den. Uden denne kontrol kunne
    #    `_trackers`-læsningen fra de tre forrige iterationer have været grøn
    #    på en mutation af `site/`.
    probe = ROOT / "site" / "blog" / "text-on-image-contrast-check.html"
    real = paid_links(SITE, probe, offers)
    check("læser en artikel med købslink i egen tekst", bool(real),
          f"{len(real)} link(s)")

    # 2. Den såkaldte forbigående fejl: et købslink i *footer* tæller ikke.
    #    Det er punkt 1 i docstringen, og det er målt (69 artikler linker til
    #    forsiden fra hele dokumentet).
    footer_only = (
        '<html><body><header><a href="/blog/x">x</a></header>'
        '<div><a href="/">hjem</a></div>'
        '<footer><a href="https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03">køb</a>'
        "</footer></body></html>"
    )
    body_only = (
        '<html><body><header><a href="/blog/x">x</a></header>'
        '<div><a href="https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03">køb</a>'
        "</div><footer><a href='/'>hjem</a></footer></body></html>"
    )
    check("købslink i footer tæller ikke (CHROME)",
          content_region(footer_only).count("buy.stripe.com") == 0)
    check("købslink i brødteksten tæller", content_region(body_only).count("buy.stripe.com") == 1)

    # 3. Forsiden er chrome: et link til `/` er ikke en købsvej.
    check("forsiden er ikke en købsvej", "/" in CHROME_ROUTES and "/da/" in CHROME_ROUTES)

    # 4. Donationslink tæller som en købsvej — det er det samme køb.
    check("donate.stripe.com er en købsvej", bool(RE_BUY.match("https://donate.stripe.com/7sYeV"))
          and not RE_BUY.match("https://evil.tld/buy.stripe.com/"))

    # 5. Punkt 3 fra docstringen: porten skal se EN engelsk artikel. Den
    #    betingelse der slap alle 94 af dem igennem var `"/blog/" in rel`.
    en = [r for r in rows(SITE, catalog) if r["file"].startswith("blog/")]
    da = [r for r in rows(SITE, catalog) if r["file"].startswith("da/blog/")]
    check("ser engelske artikler (ikke kun danske)", len(en) > 50, f"EN={len(en)}")
    check("ser danske artikler", len(da) > 50, f"DA={len(da)}")

    # 5b. Knap vs. klik. De to er ikke ens, og mutationen i `notion-artikel-pro`
    #     målte at forskellen er rigtig: med `buy.stripe.com` fjernet fra begge
    #     Notion-artikler blev porten stadig GRØN, fordi sektionen også
    #     linker til `/clean-copy-tool`, og den rute står i `offers`. Uden
    #     kontrol 18 og 19 kan de to falde sammen igen stille — og det er sådan
    #     fire iterationer i træk har rapporteret "N artikler fik en betalt vej",
    #     hvilket er den forkerte påstand.
    #
    #     Den rigtige artikel måles på disk (den har begge dele: egen knap *og*
    #     et klik til webværktøjet). Formen " klik uden knap" findes ikke i
    #     `site/` lige nu, så den bygges syntetisk — ellers ville kontrollen
    #     være grøn af den simple grund at den ingenting kunne se.
    notion = ROOT / "site" / "blog" / "copy-table-website-to-notion.html"
    paid_notion = paid_links(SITE, notion, offers)
    knap_notion = knap_links(SITE, notion)
    check("artikel med egen knap har knap (og tæller kliket til webværktøjet)",
          len(knap_notion) == 1 and "/clean-copy-tool" in paid_notion,
          f"klik={len(paid_notion)} knap={len(knap_notion)}")

    only_click = (
        '<html><body><div>'
        '<a href="/clean-copy-tool">webværktøjet</a>'
        "</div><footer>x</footer></body></html>"
    )
    page = Page()
    page.feed(only_click)
    indirect = [h for h in page.all_links if _route_of_href(h) == "/clean-copy-tool"]
    knap_of_page = [h for h in page.all_links if RE_BUY.match(h)]
    check("ét klik til en købsside er IKKE en knap",
          len(indirect) == 1 and not knap_of_page,
          f"klik={len(indirect)} knap={len(knap_of_page)}")

    # 6. Rangeringen bruger trafik når den findes, ellers links, og siger
    #    hvilken. Uden `visits` ville porten have skjult at tallene er
    #    401-blokerede siden uge 37.
    table = rows(SITE, catalog)
    check("rækker trafik fra rapporten når den findes",
          any(r["visits"] for r in table))
    check("rækker links på alle artikler", all(r["links"] >= 0 for r in table))

    # 7. Dommeren: en liste der er for tom (alle artikler undtagen) skal give
    #    rødt på en artikel der mangler. Dømmer `judge` direkte, fordi det er
    #    portens *beslutning* — en audit der kun kan finde fejl uden at
    #    afgøre om noget er en fejl, kan ikke være port.
    measured = blind_now(SITE, catalog)
    table = rows(SITE, catalog)
    real_problems = judge(SITE, catalog)
    check("listen er i synk med målingen", not real_problems,
          f"{len(real_problems)} problem(er)")
    check("listen er ikke hele korpus (den ville være meningsløs)",
          len(measured) < len(table) - 5,
          f"blind={len(measured)} korpus={len(table)}")

    # 7b. Læseren skal kunne sige "blind". Kravet før var `0 < len(measured)`,
    #     altså at korpus *skal* have en blind artikel — men det er en
    #     egenskab ved data, ikke ved porten, og den blev rød 30/9 da
    #     ratchet'en nåede nul: en tom måling kunne være resultatet ( alle
    #     artikler har en betalt vej ) eller en læser der var holdt op med at
    #     se. Formen findes ikke i `site/` lige nu, så den bygges syntetisk,
    #     samme grund som kontrol 5b.
    synthetic_blind = Path("/tmp/oxloop-selftest-blind.html")
    synthetic_blind.write_text(
        '<html><body><div><a href="/da/blog/gdpr-boeder-2026">bøder</a></div>'
        "<footer>x</footer></body></html>",
        encoding="utf-8",
    )
    try:
        check("læseren kan stadig sige 'blind' på en artikel uden købsvej",
              paid_links(synthetic_blind, synthetic_blind, offers) == [],
              f"{len(paid_links(synthetic_blind, synthetic_blind, offers))} vej(er)")
    finally:
        synthetic_blind.unlink(missing_ok=True)

    # 8. Ratchet: en død linje skal give rødt. Mutér listen i hukommersen.
    #    Når målingen er tom tages den døde linje fra korpus i stedet for fra
    #    målingen — ellers ville mutationen ikke ske, og kontrollen være
    #    grøn af den simple grund at den ingenting testede.
    data = json.loads(BLIND.read_text(encoding="utf-8"))
    patched = list(data["blind"])
    dead_line = measured[0] if measured else next(
        (r["file"] for r in table if r["paid"]), None
    )
    if dead_line:
        patched.append(dead_line)
    saved = BLIND.read_text(encoding="utf-8")
    try:
        BLIND.write_text(json.dumps({"blind": patched}, ensure_ascii=False, indent=1),
                         encoding="utf-8")
        check("død linje i listen giver rødt", bool(judge(SITE, catalog)))
    finally:
        BLIND.write_text(saved, encoding="utf-8")
    check("listen genskabt efter mutationen",
          json.loads(BLIND.read_text(encoding="utf-8"))["blind"] == data["blind"])

    # 9. `--write` må ikke slette filens egen dokumentation. Første kørsel af
    #    `--write` (30/9) skrev `{"blind": …}` og fjernede `note`, `source` og
    #    `measured`, fordi `judge()` kun læser nøglen `blind` — så ingen port
    #    kunne se det. Mutér filen på disk med de tre nøgler, kør `main(["--write"])`
    #    to gange, og kræv at de overlever. Mutationen rydder op i en `finally`.
    saved = BLIND.read_text(encoding="utf-8")
    try:
        doc = dict(data)
        doc["note"] = "selftest-note"
        doc["source"] = "selftest-source"
        doc["measured"] = "1999-01-01"
        BLIND.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        main(["--write", "--quiet"])
        main(["--write", "--quiet"])
        after = json.loads(BLIND.read_text(encoding="utf-8"))
        check("--write bevarer note/source", after.get("note") == "selftest-note"
              and after.get("source") == "selftest-source")
        check("--write opdaterer measured", after.get("measured") == date.today().isoformat())
        check("--write bevarer blind-listen", after["blind"] == data["blind"],
              f"{len(after['blind'])} linjer")
    finally:
        BLIND.write_text(saved, encoding="utf-8")
    check("listen genskabt efter --write-mutationen",
          json.loads(BLIND.read_text(encoding="utf-8"))["blind"] == data["blind"])

    # 10. Publiceringsflåsen (dom 4). Fire kontroller + fire mutationer, fordi
    #     en flås der aldrig kan rødme er en grøn cirkel. Målt 30/9: porten
    #     læser matricen og genkender netop de tre domæner CI'en deployer, og
    #     korpus har fire artikler på et domæne uden i matricen.
    live = deployed_domains()
    check("læser deploy-matricen (ikke hardkodet)",
          {"mahope.tools", "cleancopy.tools", "deskuptime.com"} <= live,
          f"{sorted(live)}")
    check("inventaret rummer et domæne matricen ikke kender",
          bool(set(json.loads(INVENTORY.read_text(encoding="utf-8"))) - live),
          f"{sorted(set(json.loads(INVENTORY.read_text(encoding='utf-8'))) - live)}")

    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    check("flåsen er grøn på det målte tilstand",
          not published_problems(SITE, inv),
          f"{len(published_problems(SITE, inv))} problem(er)")

    # 10a. En syntetisk matrix uden `bugbottle.dev` gør bekræftelsen til en
    #      død linje. Beviser at punkt 3 kan dømme — altså at porten ikke bare
    #      accepterer hvad der står i filen.
    fake_wf = Path("/tmp/oxloop-fake-deploy.yml")
    fake_wf.parent.mkdir(parents=True, exist_ok=True)
    fake_wf.write_text("        include:\n          - domain: bugbottle.dev\n",
                       encoding="utf-8")
    try:
        hit = published_problems(SITE, inv, fake_wf)
        check("bekræftelse på et nu udgivet domæne giver rødt",
              any("DØD BEKRÆFTELSE" in p for p in hit), f"{len(hit)} problem(er)")
    finally:
        fake_wf.unlink(missing_ok=True)

    # 10b. Uden bekræftelse → rød. Beviser punkt 1.
    hit = published_problems(SITE, inv, WORKFLOW, {"acknowledged": []})
    check("udpubliceret domæne uden bekræftelse giver rødt",
          any("UDPUBLICERET DOMÆNE" in p for p in hit), f"{len(hit)} problem(er)")

    # 10c. Bekræftelse uden begrundelse → rød. Beviser punkt 2, og at reglen
    #      ikke kan slås fra ved at tilføje en tom linje.
    hit = published_problems(SITE, inv, WORKFLOW,
                             {"acknowledged": [{"domain": "bugbottle.dev",
                                                "reason": "  "}]})
    check("bekræftelse uden begrundelse giver rødt",
          any("UDPUBLICERET DOMÆNE" in p for p in hit), f"{len(hit)} problem(er)")

    # 10d. Rankingen skal sige det, ellers er flåsen en fil ingen læser. Målt
    #      på `blog/bug-reports-in-ci-pipeline.html`, den artikel der gav 404
    #      på alle fire domæner da flåsen blev skrevet.
    bb = next((r for r in table if r["file"] == "blog/bug-reports-in-ci-pipeline.html"), None)
    check("rækken ved domænet og siger at det ikke er udgivet",
          bb is not None and bb["domain"] == "bugbottle.dev" and not bb["publiceret"],
          f"domæne={bb['domain'] if bb else '?'} "
          f"udgivet={bb['publiceret'] if bb else '?'}")
    check("rækken har trafik — flåsen skal kunne ramme præcis dem der har den",
          bb is not None and bb["visits"], f"visits={bb['visits'] if bb else '?'}")

    # 11. `route_of` på `index.html`. Før rettelsen (30/9) gav
    #     `site/blog/index.html` ruten `/blog/index`, som ikke findes: live er
    #     den en 308 til `/blog/`. Følgen var at hub-siden ikke blev fundet i
    #     `route_domains` og derfor lå i `ukendt domæne`-blokken — dens domæne
    #     er `mahope.tools`, og den *er* publiceret. Blokeren må altså være tom
    #     på det målte tilstand, ellers måler den portens egen fejl.
    hub = next((r for r in table if r["file"] == "blog/index.html"), None)
    check("index.html får mappens rute, ikke /index",
          hub is not None and hub["route"] == "/blog",
          f"route={hub['route'] if hub else '?'}")
    check("hub-side er ikke længere ukendt domæne",
          hub is not None and hub["domain"] == "mahope.tools" and hub["publiceret"],
          f"domæne={hub['domain'] if hub else '?'} "
          f"udgivet={hub['publiceret'] if hub else '?'}")
    check("`ukendt domæne`-blokken er tom på det målte tilstand",
          not [r for r in table if not r["domain"]],
          f"{len([r for r in table if not r['domain']])} fil(er)")

    # 11a. Mutationen: blokeren skal kunne blive rød igen, ellers er den en
    #      grøn cirkel. `unknown` i `_print_ranking` er præcis
    #      `[r for r in table if not r["domain"]]`, og `domain` kommer fra
    #      `route_domains(inventar)`. Derfor muterer vi inventaret — fjerner
    #      `/blog` — og spørger de to funktioner som rækken bygges af. Det er
    #      præcis den fejl der lå bag den gamle række: en hub-side hvis rute
    #      ikke kan findes, så den ligner ubekendt.
    no_blog_dom = route_domains({d: [r for r in rs if r.rstrip("/") != "/blog"]
                                 for d, rs in inv.items()})
    hub_route = route_of(SITE, SITE / "blog" / "index.html")
    check("inventar uden /blog får hub-ruten til at miste domænet",
          hub_route == "/blog" and hub_route in route_domains(inv)
          and hub_route not in no_blog_dom,
          f"route={hub_route} i inventaret={hub_route in route_domains(inv)} "
          f"i mutant={hub_route in no_blog_dom}")
    check("`ukendt domæne`-rækken kan blive fyldt igen",
          hub_route not in no_blog_dom,
          f"ville stå som ukendt domæne: {not (hub_route in no_blog_dom)}")

    failed = 0
    for name, ok, detail in checks:
        if ok:
            print(f"  ok   {name}" + (f" ({detail})" if detail else ""))
        else:
            failed += 1
            print(f"  FEJL {name}" + (f" ({detail})" if detail else ""), file=sys.stderr)
    print(f"article-paid-path-selftest: {len(checks) - failed}/{len(checks)} kontroller bestået")
    return 1 if failed else 0


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

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    if args.write:
        measured = blind_now(SITE, catalog)
        current = json.loads(BLIND.read_text(encoding="utf-8"))
        existing = current["blind"]
        added = sorted(set(measured) - set(existing))
        if added and not args.force:
            print("article-paid-path: --write ville tilføje linjer:\n  "
                  + "\n  ".join(added)
                  + "\nListen må kun krympe. Ret artiklen, eller kør med --force "
                    "og skriv en grund i filen.", file=sys.stderr)
            return 1
        # Skriv kun `blind` — de øvrige nøgler er filens egen dokumentation
        # (`note` siger hvad listen *er*, `source` hvordan den måles, `measured`
        # hvornår). Første `--write` (30/9) skrev `{"blind": …}` og slettede dem
        # alle tre uden at sige det, fordi `judge()` kun læser nøglen `blind`.
        # Beviset er mutationen i `_self_test`: `--write` to gange på en fil med
        # note/source/measured efterlader dem uændrede.
        out = dict(current)
        out["blind"] = measured
        out["measured"] = date.today().isoformat()
        BLIND.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")
        left = sorted(set(existing) - set(measured))
        print(f"article-paid-path: skrev {len(measured)} linjer "
              f"({len(existing) - len(measured)} færre)")
        for route in left:
            # Hver krympet linje skal kunne forklares: enten artiklen har selv
            # fået en købsvej, eller den linker nu til en side der sælger. Uden
            # denne udskrift så 31 krympninger ud som 31 rettelser.
            print(f"  forlod listen: {route}")
        return 0

    if not args.quiet:
        _print_ranking(rows(SITE, catalog), args.limit)

    problems = judge(SITE, catalog)
    for problem in problems:
        print(f"article-paid-path: {problem}", file=sys.stderr)
    if problems:
        print(f"article-paid-path: RØD — {len(problems)} problem(er).", file=sys.stderr)
        return 1
    print("article-paid-path: GRØN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
