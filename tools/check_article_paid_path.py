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
   ned som `frontpage_routes()` med sin grund, så den ikke kan falde tilbage
   til en regex der rammer dem igen. Mængden er *afledt* af build-manifestet,
   fordi den håndlavede udgave måtte lappes, da `/da/` stod med skråstreg her og
   uden i inventaret.

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

**Dom 5 (klik uden knap, målt 30/9).** Dom 4 forlod porten med ét blinde
problem tilbage, fordi dens definition er *manglende* købsvej. Men `paid_links()`
tæller to ting som én (klik til en købsside, og `buy.stripe.com` i egen tekst),
mens `knap_links()` kun tæller den sidste. En artikel kan derfor være
**dækket og alligevel uden købsknap** — læseren skal finde et link, åbne en
andre side og dér finde knappen. Det er den dyreste af de to fejl og den var
usynlig, fordi porten kun rapporterede den anden halvdel.

Målt i rækken på de 190 artikler: **148** har en indirekte vej og nul knap.
Uden flere krav er det 148 røde linjer, altså ingenting — så klassen kræver
**trafik** og **publicering**, som begge er målt, ikke valgt:

| Krav | Hvorfor | Målt 30/9 |
|---|---|---|
| `paid` ikke-tom | Ellers er det bare en blind artikel, som dom 1 allerede dømmer | 148 |
| `knapper == 0` | Klassen *er* forskellen mellem klik og knap | 148 |
| `visits` | 146 af de 148 har **0** målte besøg; en knap på en side uden læsere er ikke konvertering | 2 |
| `publiceret` | De 2 med trafik ligger begge på `bugbottle.dev` og gav **404** på alle live-domæner — dom 4s egen måling | **0** |

Klassen er derfor **0** i dag, og det er ikke en grøn cirkel: `--self-test`
bygger formen syntetisk og dømmer evnen, ikke data (samme regel som kontrol 7b).
Tilstanden før sidste iteration var målt til **1** — `blog/html-to-markdown-vscode`
med 8 besøgende på cleancopy.tools — og den fik sin knap i samme iteration. Det
er ratcheten: en ny række i klassen skal have en linje med begrundelse i
`tools/article_click_no_button.json`, en linje der ikke længere er i klassen
skal fjernes, og listen må kun krympe.

**Dom 7 (forsiden pr. domæne, målt 30/9).** Dom 6 undtager forsiderne med
vilje, og det er den rigtige regel — men den lagde **fire forskellige sider**
uden for portens dom. `/` er `site/clean-copy.html` på cleancopy.tools,
`site/deskuptime/index.html` på deskuptime.com, `site/index.html` på
mahope.tools og `bugbottle-landing/index.html` på bugbottle.dev, og ét
trafiktal summerer dem: **461 af 505** målte besøg, altså 91 %. `page_rows()`
skrev derfor `knapper: None` på de to ruter, og en forside kunne miste sin
købsknap uden at nogen port sagde det.

Dom 7 måler derfor hver forside på **den fil domænet faktisk serverer**, og
kilden er `build_sites.SITES` + `select_files()` — buildens egen mapping, så
et nyt domæne, et nyt `index_from` eller et nyt `remap` giver automatisk en ny
række. Målt 30/9 på de tre udgivne domæner: cleancopy.tools 2 knapper på begge
sprog, deskuptime.com 1, mahope.tools 1 — **0** i klassen. `bugbottle.dev`
måles til **0** men dømmes ikke, fordi det ikke står i deploy-matricen; det er
❓-et om domænet, synligt i hver kørsel i stedet for gemt i en note.

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
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from check_stripe_ctas import Page  # noqa: E402  (delt læser, se punkt 4 nedenfor)
from check_weekly_history import (  # noqa: E402  (delt selvklik-regel, se nedenfor)
    published_routes,
    unpublished_rows,
)

SITE = ROOT / "site"
CATALOG = ROOT / "tools" / "stripe_catalog.json"
BLIND = ROOT / "tools" / "article_paid_path_blind.json"
REPORTS = ROOT / "reports" / "weekly"
INVENTORY = ROOT / "tools" / "route_inventory.json"
WORKFLOW = ROOT / ".github" / "workflows" / "deploy-sites.yml"
PUBLISHED = ROOT / "tools" / "article_paid_path_published.json"
CLICK_NO_BUTTON = ROOT / "tools" / "article_click_no_button.json"
PAGE_NO_BUTTON = ROOT / "tools" / "article_page_paid_path.json"
FRONTPAGE_NO_BUTTON = ROOT / "tools" / "frontpage_no_button.json"

# Punkt 1 og 2 ovenfor. Målt: 69 artikler linker til `/` og 32 til `/da/` fra
# hele dokumentet, og begge er købssider i katalogens `offers`, fordi
# Clean Copy Pro sælges på forsiden. Uden denne udeladelse er der 0 blinde
# artikler, og porten ville være grøn på det den er skrevet for at finde.
#
# Målt 30/9: mængden var **håndlavet**, og den måtte lappes to gange fordi den
# skrev `/da/` med skråstreg mens inventaret skriver `/da` uden. Derfor er den
# nu *afledt* af build-manifestet: `frontpage_routes()` spørger `SITES` +
# `select_files()` — den samme kode der lægger filerne i `dist/<domæne>/` —
# så den kan ikke komme bag de ruter der faktisk er forsider. Se dom 7.
FRONTPAGE_DESTS = ("index.html", "da/index.html")

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


def frontpage_sources() -> dict[str, dict[str, Path | None]]:
    """Domæne → {rute: kildefil} for forsiden — **bygget**, ikke gættet.

    Målt 30/9, og det er hele dom 7: `/` er fire forskellige filer, fordi
    hvert domæne bygges af sit eget manifest. `site/clean-copy.html`
    (cleancopy.tools, 2 købsknapper), `site/deskuptime/index.html`
    (deskuptime.com, 1), `site/index.html` (mahope.tools, 1) og
    `bugbottle-landing/index.html` (bugbottle.dev, 0). Den gamle
    `CHROME_ROUTES` vidste at `/` var en forside, men ikke hvilken fil den var
    på hvilket domæne — så `page_rows()` skrev `knapper: None` for **461 af
    505** målte besøg, altså 91 % af den trafik porten kender, fordi ét tal
    summerer fire sider.

    Kilden er `build_sites.SITES` + `select_files()`: den samme funktion der
    afgør hvad der lander i `dist/<domæne>/index.html`. Derfor kan svaret ikke
    blive *nyt* på en måde porten ikke ser — en ny `index_from`, et nyt `remap`
    eller et nyt domæne i manifestet giver automatisk en ny række.

    `index_from` er den del der lå gemt: cleancopy.tools har ingen fil med
    `dest == "index.html"`, fordi forsiden er `clean-copy.html` der *kopieres*
    til `index.html`. Uden at læse `index_from` ville porten have fundet fire
    domæner hvoraf det ene ikke har en forsidefil — altså "kan ikke måle" for
    det domæne der sælger *to* produkter. Målt 30/9: `bugbottle.dev` er det
    domæne der *kun* findes via `extra` (kilden ligger uden for `site/`), og
    `index_only` er grunden til at cleancopy.tools' kilde ikke også får sin egen
    rute.
    """
    try:
        import build_sites
    except Exception as exc:  # pragma: no cover - kun hvis importen brydes
        raise RuntimeError(f"kan ikke læse build-manifestet: {exc}") from exc
    sites = {d: build_sites.Site(d, c) for d, c in build_sites.SITES.items()}
    build_sites.select_files(sites)
    out: dict[str, dict[str, Path | None]] = {}
    for domain, site in sites.items():
        index_from = site.cfg.get("index_from") or {}
        per: dict[str, Path | None] = {}
        for dest in FRONTPAGE_DESTS:
            target = index_from.get(dest) or dest
            per[_route_of_dest(dest)] = next(
                (src for _key, (src, d) in site.files.items() if d == target), None
            )
        out[domain] = per
    return out


def _route_of_dest(dest: str) -> str:
    """`da/index.html` → `/da/`. Samme form som ruterne i inventaret."""
    if dest == "index.html":
        return "/"
    return "/" + dest[: -len("index.html")]


@lru_cache(maxsize=1)
def _frontpage_sources_cached() -> tuple[dict[str, dict[str, Path | None]], str]:
    try:
        return frontpage_sources(), ""
    except Exception as exc:
        return {}, str(exc)


def frontpage_manifest_error() -> str:
    """Tom streng hvis manifestet kunne læses, ellers hvorfor det ikke kunne."""
    return _frontpage_sources_cached()[1]


def frontpage_sources_or_empty() -> dict[str, dict[str, Path | None]]:
    return _frontpage_sources_cached()[0]


@lru_cache(maxsize=1)
def frontpage_routes() -> frozenset[str]:
    """Ruterne der er en forside i *mindst ét* domæne, afledt af manifestet.

    Samme to ruter som den håndlavede `CHROME_ROUTES` gav, målt 30/9 — men
    de kan ikke længere komme bag de to former af `/da`. En forside der
    *kun* findes som `extra` (bugbottle.dev) tælles med, fordi porten skal se
    den som forside også der; den er ikke publiceret, så dom 7 dømmer den ikke,
    men den måles og skrives i udskriften, så ❓-et om domænet er synligt.
    """
    routes: set[str] = set()
    for per in frontpage_sources_or_empty().values():
        routes.update(per)
    return frozenset(routes)


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
    chrome = frontpage_routes()
    found = []
    for href in page.all_links:
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        if RE_BUY.match(href):
            found.append(href)
            continue
        route = _route_of_href(href)
        if route in offer_routes and route not in chrome and route not in mirrors:
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


def traffic_source(reports: Path = REPORTS,
                   today: date | None = None) -> tuple[dict[str, int], dict]:
    """Besøg pr. rute **og hvor tallene kommer fra**.

    Uge 37 og 38 har `top_paths` med tal, 39 og 40 har ikke. Vi tager den
    nyeste der har tal, så porten bruger det bedste vi har uden at kræve at
    en ny rapport er skrevet.

    **Målt 30/9: det var her den porten holdt op at sige sandheden.** Den gamle
    `traffic()` gav kun tal, så ranglisten skrev `8` for
    `/blog/html-to-markdown-vscode` som om det var en måling i dag — men `8` kom
    fra uge 38, genereret 24/9, **seks dage gammelt**, mens to nyere rapporter
    står med `traffic.available: false` fordi `/api/stats` svarer 401
    (`STATS_TOKEN` mangler på workeren, ❓ Til Mads). Ti iterationer har skrevet
    "målte besøg" i planen uden at nogen kunne se at tallene var en uge gamle.

    Derfor returnerer den nu målingen **sammen med** `file`, `week`,
    `generated_at`, `age_days` og `newer_without` — antallet af rapporter der er
    nyere end kilden og ikke har trafik. Uden `newer_without` er alderen ikke
    nok: en gammel rapport kan være gammel fordi trafikken døde, ikke fordi
    ingen har skrevet en ny.

    **Målt 30/9: en rapport, der tæller vores egen trafik, bruges slet ikke.**
    `reports/weekly/*.json` får sine sidevisninger fra `track.js`, som posterer
    `location.pathname` — så ethvert kald *vi* selv laver med JavaScript
    (`tools/shots.py --live`, `tools/layout_check.py --live`) lander i samme
    tæller som et kundebesøg, på en rute der er ægte. Den kan derfor ikke findes
    med en navneliste, og det er ikke nok at skrive advarslen i `meta`: en
    forfalsket besøgstæller i en rangliste er præcis det fundet handler om. En
    rapport med en rute vi ikke udgiver springes derfor **over**, og dens navn
    står i `meta["skipped"]`, så læseren ser at der var noget at kassere.
    Rækkefølgen er bevidst: arkivporten `check_weekly_history.py` dømmer
    rapporten rød, og den her nægter at citere den.
    """
    if not reports.is_dir():
        return {}, {"file": None, "week": None, "generated_at": None,
                    "age_days": None, "newer_without": 0, "reports": 0,
                    "skipped": []}
    today = today or date.today()
    published = published_routes() or set()
    best: dict[str, int] = {}
    parsed: list[tuple[Path, dict, list | None]] = []
    for path in sorted(reports.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        parsed.append((path, data, (data.get("traffic") or {}).get("top_paths")))
    skipped: list[str] = []
    with_traffic: list[tuple[Path, dict, list]] = []
    for path, data, top in parsed:
        if not (isinstance(top, list) and top):
            continue
        bad = unpublished_rows(top, published)
        if bad:
            skipped.append(f"{path.name} ({len(bad)} rute(r) vi ikke udgiver)")
            continue
        with_traffic.append((path, data, top))
    for _path, _data, top in with_traffic:
        for row in top:
            route, visits = row.get("path"), row.get("visits")
            if isinstance(route, str) and isinstance(visits, int):
                # Sorteret stigende, så den nyeste rapport med tal overskriver
                # en ældre måling af samme rute — samme rækkefølge som den gamle
                # løkke. Ruter der kun findes i en ældre rapport bliver stående,
                # fordi de ikke er målt væk, kun ikke målt i dag.
                best[route] = visits
    if not with_traffic:
        return {}, {"file": None, "week": None, "generated_at": None,
                    "age_days": None, "newer_without": 0,
                    "reports": len(parsed), "skipped": skipped}
    chosen_path, chosen_data, _top = with_traffic[-1]
    # Kun rapporter *efter* kilden tælles. Målt 30/9 i selftesten: en løkke der
    # talte ved hvert skridt gav `newer_without: 2` for to rapporter der lå
    # *før* kilden, altså et tal der pegede på det forkerte og ville have
    # forklaret alderen med det modsatte.
    newer_without = sum(1 for p, _d, t in parsed
                        if p > chosen_path and not (isinstance(t, list) and t))
    generated = str(chosen_data.get("generated_at") or "")[:10]
    age = None
    if len(generated) == 10:
        try:
            age = (today - date.fromisoformat(generated)).days
        except ValueError:
            age = None
    return best, {"file": chosen_path.name, "week": chosen_data.get("iso_week"),
                  "generated_at": generated or None, "age_days": age,
                  "newer_without": newer_without, "reports": len(parsed),
                  "skipped": skipped}


def traffic(reports: Path = REPORTS) -> dict[str, int]:
    """Kun tallene — brug `traffic_source()` når tallene skal vises for en

    læser, så alderen kommer med. `rows()` bruger denne, fordi en række ikke
    skal bære kilden i hver celle; `_print_ranking` og dom 5 bruger den anden.
    """
    return traffic_source(reports)[0]


def traffic_note(meta: dict) -> str:
    """Menneskelæselig kilde på de målte besøg, til rapporten og til dom 5.

    Uden `age_days` er teksten bevidst vag: *"trafik fra 2026-38 uden dato"* er
    sand, og den siger at vi ikke ved hvor gammel den er. Det er en måling i
    sig selv — `generated_at` mangler i en rapport, så porten må ikke gætte.
    """
    if not meta or not meta.get("file"):
        read = (meta or {}).get("reports") or 0
        kasset = ""
        if meta and meta.get("skipped"):
            kasset = (f" · {len(meta['skipped'])} rapport(er) kasseret fordi de "
                      f"tæller vores egen trafik")
        return (f"trafik: ingen af {read} rapporter(r) har målte besøg — "
                f"besøgskolonnen er ikke et tal, det er en fraværende måling"
                f"{kasset}")
    alder = (f"{meta['age_days']} dage gammel" if meta.get("age_days") is not None
             else "uden dato")
    nyere = meta.get("newer_without") or 0
    kasset = ""
    if meta.get("skipped"):
        # Uden denne er fraværet af en rapport usynligt, og læseren ville
        # tro at porten bare valgte den nyeste med tal.
        kasset = (f" · kasseret fordi de tæller vores egen trafik: "
                  f"{', '.join(meta['skipped'])}")
    return (f"trafik: {meta.get('week') or meta['file']} genereret "
            f"{meta.get('generated_at') or '(ingen dato)'} ({alder}) · "
            f"{nyere} nyere rapport(er) uden trafik · {meta.get('reports')} "
            f"rapport(er) læst{kasset}")


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


def route_domain_map(inventory: dict) -> dict[str, set[str]]:
    """Rute → **alle** domæner der serverer den, fra `route_inventory.json`.

    Ruterne renses for bagvendt skråstreg, fordi inventaret er skrevet med
    både former: målt på cleancopy.tools står `'/'` og `'/activate/'`, mens
    bugbottle.dev har `'/blog/bug-reports-in-ci-pipeline'` uden skråstreg. Uden
    rensningen ville en artikel kunne miste sit domæne på en tegnform, og
    porten ville så *ikke* flåse den — den fejl der ligner grønt.

    **Målt 30/9: to ruter er delte af alle fire domæner.** `/` og `/da/`
    står i hvert af inventaret fire domæner — og de to bærer **461 af de 505**
    målte besøg, altså 91 % af al trafik porten kender. Den gamle
    `route_domains()` var en dict-forståelse, så den gemte fire domæner bag
    *det sidste i rækkefølgen* (`mahope.tools`) uden at sige det. I dag er
    valget heldigtvis rigtigt, fordi `mahope.tools` står sidst i inventaret og
    er udgivet — men det er ikke en egenskab ved porten, det er en egenskab ved
    rækkefølgen i en JSON-fil. Den dag Mads flytter `bugbottle.dev` ned i
    inventaret, ville `/` og `/da/` blive `publiceret=False`, og dom 4s flås
    ville kræve en begrundelse for forsiden af hele mahope.tools.

    Derfor er domænet her et **sæt**, og det er `publiceret` der afgør
    publicering: mindst ét af domænerne skal være udgivet. Se `rows()`.
    """
    out: dict[str, set[str]] = {}
    for domain, routes in inventory.items():
        for route in routes:
            out.setdefault(route.rstrip("/") or "/", set()).add(domain)
    return out


def domain_label(domains) -> str:
    """Domænesæt → tekst til udskriften. `a+b` betyder at ruten er delt."""
    return "+".join(sorted(domains)) if domains else ""


def unpublished_routes(root: Path = SITE, inventory: dict | None = None,
                       workflow: Path = WORKFLOW) -> dict[str, str]:
    """Artikler hvis domæne ikke står i deploy-matricen. Rute → domæneliste.

    Målt 30/9 før denne funktion: `blog/bug-reports-in-ci-pipeline.html`,
    `da/blog/bugrapporter-i-ci-pipeline.html`,
    `da/blog/tilfoej-fejlrapport-formular-hjemmeside.html` — de tre artikler
    på `bugbottle.dev` i korpus, alle med 404 på de live domæner.

    En rute er **udpubliceret** først når *intet* af dens domæner er udgivet,
    fordi en delt rute findes på hvert af dem. Se `route_domain_map()`.
    """
    inventory = inventory if inventory is not None else json.loads(
        INVENTORY.read_text(encoding="utf-8")
    )
    live = deployed_domains(workflow)
    dom = route_domain_map(inventory)
    out: dict[str, str] = {}
    for path in article_files(root):
        route = route_of(root, path)
        domains = dom.get(route)
        if domains and not (domains & live):
            out[route] = domain_label(domains)
    return out


def rows(root: Path = SITE, catalog: dict | None = None) -> list[dict]:
    catalog = catalog if catalog is not None else json.loads(CATALOG.read_text(encoding="utf-8"))
    offers = offer_routes(catalog)
    inbound = inbound_counts(root)
    visits = _visits_by_route(traffic())
    dom = route_domain_map(json.loads(INVENTORY.read_text(encoding="utf-8")))
    live = deployed_domains()
    out = []
    for path in article_files(root):
        route = route_of(root, path)
        paid = paid_links(root, path, offers)
        domains = dom.get(route)
        out.append({
            "file": path.relative_to(root).as_posix(),
            "route": route,
            "visits": visits.get(route),
            "links": len(inbound.get(route, ())),
            "paid": paid,
            "knapper": len(knap_links(root, path)),
            "domains": sorted(domains) if domains else [],
            "domain": domain_label(domains),
            "delt": bool(domains) and len(domains) > 1,
            # `None` = vi ved ikke hvor den ligger. Det er *ikke* det samme som
            # udgivet, og porten skelner: en rute uden domæne skal findes i
            # inventaret, ellers er læsningen af filen forældet.
            #
            # `publiceret` er **mindst ét** udgivet domæne, ikke domænet der
            # kom sidst i inventaret. Se `route_domain_map()` for målingen:
            # `/` og `/da/` er delte af alle fire, så en rute der findes på et
            # udgivet og et udpubliceret domæne *er* publiceret. `delt` og
            # `publiceret_alle` siger det samme uden at skjule det.
            "publiceret": bool(domains and domains & live),
            "publiceret_alle": bool(domains) and domains <= live,
        })
    out.sort(key=lambda r: (-(r["visits"] or 0), -r["links"], r["route"]))
    return out


def _visits_by_route(visits: dict[str, int]) -> dict[str, int]:
    """Trafiknøgler i én form, så et opslag ikke kan ramme en skråstreg forbi.

    **Målt 30/9, fundet af selftestens egen kontrol:** rapportens `top_paths`
    skriver `/da/` **med** bagvendt skråstreg, mens `route_inventory.json`
    skriver `/da` **uden**. Et dict-opslag på den normaliserede nøgle gav derfor
    `None` for den danske forside — 31 besøg, den næststørste enkelt-rute i
    hele korpus — og ruten forsvandt fra målingen af ikke-artikler. Den så ud
    som en forside der ikke findes, hvilket er præcis det `CHROME_ROUTES`
    undtagelsen skjuler.

    Begge former lægges ind, så det er ligegyldigt hvilken form kilden bruger.
    Den med flest besøg vinder, så en rapport der skriver ruten to gange ikke
    kan få tallet til at falde.
    """
    out: dict[str, int] = {}
    for path, count in visits.items():
        key = path.rstrip("/") or "/"
        out[key] = max(out.get(key, 0), count)
        # Begge former skal kunne slås op. Uden den anden linje forsvandt
        # `/da/`-besøgene igen, fordi inventaret skriver ruten uden skråstreg.
        out[path] = max(out.get(path, 0), count)
    return out


def _chrome(route: str) -> bool:
    """Er ruten en forside?

    Mængden er **afledt** af build-manifestet (`frontpage_routes()`), så den
    kan ikke falde tilbage til en håndlavet liste der skriver ruten i en anden
    form end inventaret gør. Den gamle `CHROME_ROUTES` skrev `/da/` med
    skråstreg mens `route_inventory.json` skriver `/da` uden, så et råt
    `route in CHROME_ROUTES` klassificerede den danske forside som en helt
    almindelig side — og dom 6 dømmede den. Målt 30/9: det gav
    `NY SIDE-UDEN-KNAP: /da … 31 målte besøg` på en rute porten netop har
    undtaget med vilje. Normaliseringen er der stadig, fordi inventaret og
    trafikken stadig skriver begge former.
    """
    return (route.rstrip("/") or "/") in {r.rstrip("/") or "/" for r in frontpage_routes()}


def page_rows(root: Path = SITE, catalog: dict | None = None,
              inventory: dict | None = None) -> list[dict]:
    """Målingen af det porten *ikke* så: ruter der ikke er artikler.

    Portens øvrige funktioner læser `site/blog/**` og `site/da/blog/**`.
    Målt 30/9 er de **tre mest besøgte ruter i hele korpus ikke artikler**:
    `/` **430**, `/da/` **31** og `/clean-copy-tool` **6** mod `/blog/…-vscode`
    **8** som bedste artikel — altså **475 af 505** målte besøg lå uden for
    portens ramme. Ni iterationer skrev "målte besøg" i planen om de 8, og
    ingen af dem nævnte at 461 lå på to sider porten med vilje ser bort fra
    (`CHROME_ROUTES`, fordi de er domænernes forside).

    Derfor er de to slags **målt og udskrevet, ikke skjult**:
    `chrome` er forsiderne, `page` er alt andet. En rute i inventaret uden
    artikel-fil er ikke en fejl — den er et værktøj, en landingsside, en
    `/scan`-side eller en 404, og den har brug for en købsknap lige så meget
    som en artikel gør det. Ruter der står i inventaret men ikke findes som
    fil i `site/` får `file: None` og tælles med, fordi de serveres alligevel.

    Kun ruter med **målt** trafik er med. Det er samme krav som dom 5, og af
    samme grund: porten skal ramme læsere, ikke bare sider.
    """
    catalog = catalog if catalog is not None else json.loads(CATALOG.read_text(encoding="utf-8"))
    inventory = inventory if inventory is not None else json.loads(
        INVENTORY.read_text(encoding="utf-8")
    )
    dom = route_domain_map(inventory)
    live = deployed_domains()
    articles = {route_of(root, p) for p in article_files(root)}
    inbound = inbound_counts(root)
    visits = _visits_by_route(traffic())
    out = []
    for route, domains in dom.items():
        if route in articles:
            continue
        visits_here = visits.get(route)
        if not visits_here:
            continue
        delt = len(domains) > 1
        # En delt rute er **flere forskellige sider**. Målt 30/9: `/` er
        # `site/clean-copy.html` på cleancopy.tools, `site/deskuptime/index.html`
        # på deskuptime.com, `site/index.html` på mahope.tools og
        # `site/bugbottle.html` på bugbottle.dev — fire sider med fire forskellige
        # købsknapper, som ét trafiktal summerer. `_page_file()` ville finde *én*
        # af dem og porten ville skrive dens knaptal som om det gjaldt ruten.
        # Derfor måles filen og knapperne **kun** når ruten har ét domæne; ellers
        # er de `None`, og det siges i udskriften.
        path = None if delt else _page_file(root, route)
        out.append({
            "route": route,
            "file": path.relative_to(root).as_posix() if path else None,
            "visits": visits_here,
            "links": len(inbound.get(route, ())),
            "knapper": len(knap_links(root, path)) if path else None,
            "chrome": _chrome(route),
            "domains": sorted(domains),
            "domain": domain_label(domains),
            "delt": delt,
            "publiceret": bool(domains & live),
            "publiceret_alle": domains <= live,
        })
    out.sort(key=lambda r: (-r["visits"], r["route"]))
    return out


def _page_file(root: Path, route: str) -> Path | None:
    """Filen bag en rute. `index.html` er mappens rute — samme som `route_of`."""
    for cand in (root / f"{route.lstrip('/')}.html",
                 root / route.lstrip("/") / "index.html"):
        if cand.is_file():
            return cand
    return None


def page_no_button(table: list[dict] | None = None) -> list[dict]:
    """Dom 6: en ikke-artikel med læsere på en udgivet rute uden købsknap.

    Samme fire krav som dom 5, minus `paid`: en ikke-artikel har ingen
    artikels `indirekte vej`-liste at læse, så kravet er at der ikke står *nogen*
    synlig købsknap. Forsiderne er undtaget med vilje — de er domænernes
    hovedsider og har en helt anden rolle end en værktøjside, så at dømme dem
    ville være at tælle den samme købsknap to gange.

    Målt 30/9 på de 296 ruter i inventaret: **3** har målte besøg, **2** er
    chrome, og den tredje — `/clean-copy-tool` — har **2** købsknapper
    (abonnement + lifetime). Klassen er altså **0**, målt på `main`.
    """
    table = table if table is not None else page_rows()
    return [r for r in table if not r["chrome"] and r["publiceret"]
            and not r["knapper"]]


def page_no_button_problems(table: list[dict] | None = None,
                            doc: dict | None = None,
                            meta: dict | None = None) -> list[str]:
    """Dom 6, begrundelses-flås over `page_no_button()`.

    Samme fire domme som dom 5, af samme grund: en port der konstant er rød
    bliver slåt fra. Forsiderne er undtaget, og beskeden siger hvor mange besøg
    de bærer, fordi ellers er det uforståeligt at porten springer over dem.
    """
    table = table if table is not None else page_rows()
    doc = doc if doc is not None else (
        json.loads(PAGE_NO_BUTTON.read_text(encoding="utf-8"))
        if PAGE_NO_BUTTON.is_file() else {"acknowledged": []}
    )
    entries = doc.get("acknowledged", [])
    known = {e["route"]: e for e in entries if isinstance(e.get("route"), str)}
    measured = {r["route"]: r for r in page_no_button(table)}
    problems: list[str] = []
    chrome = sum(r["visits"] for r in table if r["chrome"])

    for route in sorted(set(measured) - set(known)):
        row = measured[route]
        problems.append(
            f"NY SIDE-UDEN-KNAP: {route} har {row['visits']} målte besøg "
            f"({traffic_note(meta if meta is not None else traffic_source()[1])}), "
            f"ligger på {row['domain']} og er ikke en artikel, men har ingen "
            f"købsknap. Sæt en knap på siden, eller tilføj en linje med en "
            f"grund i tools/article_page_paid_path.json."
        )
    for route, entry in sorted(known.items()):
        if not str(entry.get("reason") or "").strip():
            problems.append(
                f"NY SIDE-UDEN-KNAP: {route} står i "
                f"tools/article_page_paid_path.json, men `reason` er tom. En "
                f"undtagelse uden grund er en måde at slå reglen fra."
            )
        elif route not in measured:
            row = next((r for r in table if r["route"] == route), None)
            if row is None:
                why = "ruten har ikke længere målte besøg i rapporten"
            elif row["chrome"]:
                why = "den er en forside (chrome) og hører ikke i denne klasse"
            elif row["knapper"]:
                why = f"den har nu {row['knapper']} købsknap(per)"
            else:
                why = f"ruten er ikke publiceret ({row['domain']})"
            problems.append(
                f"DØD LINJE i listen: {route} er ikke længere i den målte "
                f"klasse — {why}. Fjern den fra "
                f"tools/article_page_paid_path.json — listen må kun krympe."
            )
    if len(known) != len(entries):
        problems.append("side-uden-knap-listen har dubletter; den er en mængde.")
    if problems and chrome:
        problems.append(
            f"note: dom 6 ser {chrome} besøg på forsiderne og dømmer dem ikke. "
            f"Forsider er domænernes hovedsider og tælles i "
            f"`check_stripe_ctas.py` i stedet."
        )
    return problems


def frontpage_rows(workflow: Path = WORKFLOW) -> list[dict]:
    """Dom 7s måling: **hvert domænes egen forside**, med sit eget knaptal.

    Dom 6 undtager forsiderne, fordi de er domænernes hovedsider. Det var den
    rigtige regel, men den lod **fire forskellige sider** ligge uden for
    portens dom: målt 30/9 ligger `/` (430) + `/da/` (31) = **461 af 505**
    målte besøg, altså 91 %, på to ruter porten med vilje så bort fra, og
    `page_rows()` satte `knapper: None` på dem fordi ét trafiktal summerer
    fire sider. En forside kunne miste sin købsknap, og ingen port ville sige
    det.

    Derfor måles den **pr. domæne**, på den fil domænet faktisk serverer — fra
    build-manifestet, ikke fra en håndlavet liste (`frontpage_sources()`).
    Besøgstallet kan *ikke* deles pr. domæne, fordi det er summen af alle fire,
    så hver række bærer tallet med `delt: True` og udskriften siger det.

    Kun domæner i deploy-matricen dømmes. `bugbottle.dev` måles og skrives med
    sine **0** knapper — det er ❓-et om hvem der ejer domænet, synligt i
    hver kørsel — men det er ikke i matricen, så det dømmes ikke. Den dag det
    kommer i matricen, går dom 7 rød med en besked om hvilken fil der skal have
    en knap, og det er den rigtige rettelse: en forside uden købsvej er et hul.
    """
    per_domain = frontpage_sources_or_empty()
    live = deployed_domains(workflow)
    visits = _visits_by_route(traffic())
    dom = route_domain_map(json.loads(INVENTORY.read_text(encoding="utf-8")))
    out: list[dict] = []
    for domain in sorted(per_domain):
        for route, src in per_domain[domain].items():
            knapper = knap_links(SITE, src) if src else None
            out.append({
                "domain": domain,
                "route": route,
                "file": _rel(src) if src else None,
                "knapper": len(knapper) if src else None,
                "knap_urls": knapper or None,
                "publiceret": domain in live,
                "delt": len(dom.get(route.rstrip("/") or "/", ())) > 1,
                "visits": visits.get(route),
                "i_inventar": (route.rstrip("/") or "/") in dom,
            })
    out.sort(key=lambda r: (r["domain"], r["route"]))
    return out


def _rel(path: Path) -> str:
    """Sti til læseren. Kilder uden for `site/` står som `../bugbottle-landing/…`."""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return "../" + path.as_posix().lstrip("/")


def frontpage_no_button(table: list[dict] | None = None,
                        workflow: Path = WORKFLOW) -> list[dict]:
    """Dom 7: en publiceret forside uden købsknap. Se `frontpage_rows()`.

    Målt 30/30 på de tre udgivne domæner: cleancopy.tools **2** knapper på begge
    sprog (abonnement + lifetime), deskuptime.com **1**, mahope.tools **1** —
    efter sidste iteration lagde en købsknap på mahope.tools' egen forside.
    Klassen er altså **0** i dag, og det er målt på filerne, ikke på en liste.

    En forside hvis fil *ikke* kan findes (`knapper is None`) er ikke i klassen:
    ukendt er ikke nul, og den bliver rød i `frontpage_problems()` med en
    anden besked. Ellers ville en fil der forsvinder se ud som en forside
    uden købsknap — eller værre: som en forside der aldrig har eksisteret.
    """
    table = table if table is not None else frontpage_rows(workflow)
    return [r for r in table if r["publiceret"] and r["knapper"] == 0]


def frontpage_problems(table: list[dict] | None = None,
                       doc: dict | None = None,
                       workflow: Path = WORKFLOW) -> list[str]:
    """Dom 7, begrundelses-flås over `frontpage_no_button()`.

    Samme tre domme som dom 5 og 6, af samme grund: en port der konstant er
    rød bliver slåt fra. Men der kommer to mere, fordi dom 7 måler noget de
    to andre ikke gør:

    1. En målt forside uden knap uden linje i `tools/frontpage_no_button.json`
       → rød, med domænet, filen og ruten i beskeden.
    2. En linje uden begrundelse → rød. Samme regel som `ctas_note`.
    3. En linje der ikke længere er i klassen → rød, med *hvorfor* den faldt
       ud (fik knap, er ikke publiceret, filen er væk).
    4. Dubletter → rød. Nøglen er `domæne + rute`, fordi `/` findes fire gange.
    5. **En publiceret forside hvis fil ikke kan findes** → rød. Det er det
       dom 6 *ikke* kunne se: `page_rows()` skrev `knapper: None` og gik videre.
    6. **Et publiceret domæne uden forside-række** → rød. Samme grund: et
       domæne der ikke måles må ikke se ud som et domæne uden købsknap.
    """
    if table is None:
        table = frontpage_rows(workflow) if not frontpage_manifest_error() else []
    doc = doc if doc is not None else (
        json.loads(FRONTPAGE_NO_BUTTON.read_text(encoding="utf-8"))
        if FRONTPAGE_NO_BUTTON.is_file() else {"acknowledged": []}
    )
    entries = doc.get("acknowledged", [])
    key = lambda r: f"{r['domain']}{r['route']}"  # noqa: E731
    known = {e["key"]: e for e in entries
             if isinstance(e, dict) and isinstance(e.get("key"), str)}
    measured = {key(r): r for r in frontpage_no_button(table)}
    problems: list[str] = []

    if frontpage_manifest_error():
        problems.append(
            f"KAN IKKE MÅLE FORSIDEN: {frontpage_manifest_error()}. Uden "
            f"målingen er dom 7 død, og det er værre end rødt: porten ville "
            f"springe domænernes forsider over i det stille."
        )
    for k in sorted(set(measured) - set(known)):
        row = measured[k]
        problems.append(
            f"NY FORSIDE-UDEN-KNAP: {row['domain']}{row['route']} er en "
            f"publiceret forside ({row['file']}) med 0 købsknapper. Sæt en "
            f"knap på siden, eller tilføj en linje med en grund i "
            f"tools/frontpage_no_button.json."
        )
    for k, entry in sorted(known.items()):
        if not str(entry.get("reason") or "").strip():
            problems.append(
                f"NY FORSIDE-UDEN-KNAP: {k} står i "
                f"tools/frontpage_no_button.json, men `reason` er tom. En "
                f"undtagelse uden grund er en måde at slå reglen fra."
            )
        elif k not in measured:
            row = next((r for r in table if key(r) == k), None)
            if row is None:
                why = "domænet eller ruten er ikke længere i build-manifestet"
            elif row["knapper"]:
                why = f"den har nu {row['knapper']} købsknap(per)"
            else:
                why = f"domænet er ikke publiceret ({row['domain']})"
            problems.append(
                f"DØD LINJE i listen: {k} er ikke længere i den målte klasse — "
                f"{why}. Fjern den fra tools/frontpage_no_button.json — "
                f"listen må kun krympe."
            )
    if len(known) != len(entries):
        problems.append("forside-uden-knap-listen har dubletter; den er en mængde.")

    # Dom 7s to ekstra domme: det porten ellers ikke ser.
    for row in table:
        if not row["publiceret"]:
            continue
        if row["knapper"] is None:
            problems.append(
                f"KAN IKKE MÅLE FORSIDEN: {row['domain']}{row['route']} er en "
                f"publiceret forside, men porten fandt ingen kildefil for den. "
                f"Det er ikke det samme som 0 knapper — målingen skal rettes, "
                f"ellers er domænets forside usynlig."
            )
        elif not row["i_inventar"]:
            problems.append(
                f"FORSIDE UDEN RUTE I INVENTARET: {row['domain']}{row['route']} "
                f"({row['file']}) står ikke i tools/route_inventory.json, så "
                f"besøgstallet kan ikke slås op. Opdatér inventaret."
            )
    covered = {(r["domain"], r["route"]) for r in table}
    for domain in sorted(deployed_domains(workflow)):
        for route in sorted(frontpage_routes()):
            if (domain, route) not in covered:
                problems.append(
                    f"FORSLIDE UDEN MÅLING: {domain}{route} er en publiceret "
                    f"forside, men dom 7 har ingen række for den. Uden rækken "
                    f"er domænets forside uden for portens syn."
                )
    return problems


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
    # Dom 5, klik uden knap. Samme grund: målingen er nu 0, så porten skal være
    # grøn på en *begrundet* måling, ikke på en tør.
    problems.extend(click_no_button_problems(rows(root, catalog)))
    # Dom 6, ikke-artikler. Målingen er også 0, men af en anden grund: de tre
    # ruter uden for artiklerne med målt trafik er to forsider og én
    # værktøjside med to købsknapper. Se `page_rows()`.
    problems.extend(page_no_button_problems())
    # Dom 7, forsiden pr. domæne. Dom 6 undtager forsiderne med vilje, og det
    # er derfor den her måler dem — ellers ligger 461 af 505 målte besøg
    # uden for portens dom. Se `frontpage_rows()`.
    problems.extend(frontpage_problems())
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


def click_no_button(table: list[dict]) -> list[dict]:
    """Klik uden knap — dom 5. Se docstringens måling.

    Kræver fire ting, og hver af dem er målt i stedet for valgt:

    - `paid` ikke-tom: ellers er det en blind artikel, som dom 1 allerede dømmer.
    - `knapper == 0`: det *er* klassen. 148 af 190 har klik uden knap, så
      dette krav alene er ikke en port — det er dækning.
    - `visits`: 146 af de 148 har 0 målte besøg.
    - `publiceret`: de 2 med trafik ligger på `bugbottle.dev` og gav 404 på
      alle live-domæner, målt med `curl` 30/9.

    Uden de to sidste er porten 148 røde linjer, altså ingenting. Med dem er
    den **0** i dag — og det er målt ved at køre `rows()` mod de to tidligere
    commits, ikke ved at læse en liste.
    """
    return [r for r in table if r["paid"] and not r["knapper"]
            and r["visits"] and r["publiceret"]]


def click_no_button_problems(table: list[dict] | None = None,
                             doc: dict | None = None,
                             meta: dict | None = None) -> list[str]:
    """Dom 5: en artikel med læsere, en betalt vej og ingen købsknap skal have
    en begrundelse, og grunden skal forsvinde når den får en knap.

    Samme tre domme som `published_problems`, af samme grund: en port der
    konstant er rød bliver slået fra. Derfor er dette en *begrundelses*-flås
    over en målt klasse, ikke en tærskel.

    1. En målt række uden linje i `tools/article_click_no_button.json` → rød.
       Skal have en købsknap, eller en linje med en grund.
    2. En linje uden begrundelse → rød. Samme regel som `ctas_note`.
    3. En linje der ikke længere er i den målte klasse → rød, og beskeden siger
       *hvorfor* den faldt ud (knap, tabt trafik, tabt publicering, slettet
       fil), fordi ellers får næste iteration fire forskellige forklaringer på
       den samme linje. Listen må kun krympe, præcis som blindlisten.
    4. Dubletter → rød. Listen er en mængde.
    """
    table = table if table is not None else rows()
    doc = doc if doc is not None else (
        json.loads(CLICK_NO_BUTTON.read_text(encoding="utf-8"))
        if CLICK_NO_BUTTON.is_file() else {"acknowledged": []}
    )
    entries = doc.get("acknowledged", [])
    known = {e["file"]: e for e in entries if isinstance(e.get("file"), str)}
    measured = {r["file"]: r for r in click_no_button(table)}
    problems: list[str] = []

    for file in sorted(set(measured) - set(known)):
        row = measured[file]
        # Kilden skriver i selve røde linje. Det er her porten beder en person
        # om at skrive en begrundelse, så beskeden skal kunne vejes: "8 målte
        # besøg" fra en seks dage gammel rapport er et andet krav end "8 målte
        # besøg" fra i går (målt 30/9 — se `traffic_source`).
        problems.append(
            f"NY KLIK-UDEN-KNAP: {file} har {row['visits']} målte besøg "
            f"({traffic_note(meta if meta is not None else traffic_source()[1])}), "
            f"{len(row['paid'])} indirekte vej(er), men ingen købsknap. Sæt en "
            f"knap på siden, eller tilføj en linje med en grund i "
            f"tools/article_click_no_button.json."
        )
    for file, entry in sorted(known.items()):
        if not str(entry.get("reason") or "").strip():
            problems.append(
                f"NY KLIK-UDEN-KNAP: {file} står i "
                f"tools/article_click_no_button.json, men `reason` er tom. En "
                f"undtagelse uden grund er en måde at slå reglen fra."
            )
        elif file not in measured:
            row = next((r for r in table if r["file"] == file), None)
            if row is None:
                why = "filen findes ikke længere på disk"
            elif not row["paid"]:
                why = "den har ikke længere nogen betalt vej"
            elif row["knapper"]:
                why = f"den har nu {row['knapper']} købsknap(per)"
            elif not row["visits"]:
                why = "besøgstallet er ikke længere målt i rapporten"
            else:
                why = f"ruten er ikke publiceret ({row['domain']})"
            problems.append(
                f"DØD LINJE i listen: {file} er ikke længere i den målte "
                f"klasse — {why}. Fjern den fra "
                f"tools/article_click_no_button.json — listen må kun krympe."
            )
    if len(known) != len(entries):
        problems.append("klik-uden-knap-listen har dubletter; den er en mængde.")
    return problems


def _print_ranking(table: list[dict], limit: int, meta: dict | None = None) -> None:
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
    # Kilden står *over* kolonnen, ikke nederst. Målt 30/9: de målte tal kom fra
    # en rapport seks dage gammel, og de otte foregående iterationer skrev dem i
    # planen som "målte besøg" uden at alderen kunne ses. En kolonne uden kilde
    # er et tal læseren ikke kan veje.
    print(traffic_note(meta if meta is not None else traffic_source()[1]))
    blind = [r for r in table if not r["paid"]]
    for row in blind[:limit]:
        trafik = str(row["visits"]) if row["visits"] is not None else "-"
        print(f"{trafik:>6} {row['links']:>5}  {row['file']:<52} {row['route']}")
    # Dom 5, klik uden knap. De 148 med klik uden knap måles og *tælles* her,
    # men porten dømmer dem ikke: se `click_no_button()` for hvorfor (trafik og
    # publicering). Udskriften skal kunne vise at klassen er 0, ellers er det
    # umuligt at se om porten ser den.
    loose = [r for r in table if r["paid"] and not r["knapper"]]
    klasse = click_no_button(table)
    print(f"klik uden knap: {len(loose)} artikler har en indirekte vej men ingen "
          f"købsknap · {sum(1 for r in loose if r['visits'])} med målt trafik · "
          f"{len(klasse)} på en publiceret rute (dømmes)")
    for row in sorted(klasse, key=lambda r: (-(r["visits"] or 0), r["route"]))[:limit]:
        print(f"{row['visits']:>6} {row['links']:>5}  {row['file']:<52} "
              f"{row['route']} — {len(row['paid'])} vej(er)")
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

    # Dom 6, det porten ellers ikke ser. Målt 30/9 ligger **461 af 505** målte
    # besøg på to forsider, og porten så dem ikke — de er `CHROME_ROUTES`, så
    # de var undtaget med vilje. Uden denne blokke er det umuligt at se at 91 %
    # af trafikken er uden for portens synsfelt, og de ni iterationer der skrev
    # "målte besøg" om en artikel med 8 besøg havde ingen grund til at vælge den.
    sider = page_rows()
    chrome = [r for r in sider if r["chrome"]]
    andre = [r for r in sider if not r["chrome"]]
    delt = [r for r in sider if r["delt"]]
    klasse6 = page_no_button(sider)
    print(f"uden for artiklerne: {len(sider)} ruter har målte besøg · "
          f"{sum(r['visits'] for r in chrome)} på {len(chrome)} forside(r) "
          f"(dømmes ikke) · {sum(r['visits'] for r in andre)} på {len(andre)} "
          f"andre ruter · {len(delt)} delt af flere domæner · "
          f"{len(klasse6)} uden købsknap (dømmes)")
    for row in (chrome + andre)[:limit]:
        if row["knapper"] is None:
            state = (f"fordelt på {len(row['domains'])} domæner — porten ved "
                     f"ikke hvilken side besøgene landede på")
        else:
            state = "forside" if row["chrome"] else f"{row['knapper']} knap(per)"
        fil = row["file"] or f"(hver af {len(row['domains'])} domæner sin side)"
        print(f"{row['visits']:>6} {row['links']:>5}  {fil:<52} "
              f"{row['domain']} — {state}")

    # Dom 7, forsiden pr. domæne. Det er den måling dom 6s undtagelse skjuler:
    # 461 besøg på to ruter der er *fire* forskellige sider, så porten skrev
    # `knapper: None` og gik videre. Her måles hver side på sin egen fil, fra
    # build-manifestet. Besøgstallet står på alle fire rækker, fordi det er
    # summen — det står derfor med "delt" og må ikke læses som fire målinger.
    forsider = frontpage_rows()
    klasse7 = frontpage_no_button(forsider)
    ruter = sorted({r["route"] for r in forsider})
    delte = sorted({r["route"] for r in forsider if r["delt"]})
    besog = sum(max((r["visits"] or 0) for r in forsider if r["route"] == rt)
                for rt in ruter)
    print(f"\nforside pr. domæne (dom 7): {len(forsider)} forsider på "
          f"{len({r['domain'] for r in forsider})} domæner · {besog} målte "
          f"besøg på {len(ruter)} forside-rute(r), hvoraf {len(delte)} er "
          f"delt af alle domæner · "
          f"{sum(1 for r in forsider if not r['publiceret'])} rækker på et "
          f"domæne der ikke udgives (måles, dømmes ikke) · {len(klasse7)} "
          f"uden købsknap (dømmes)")
    for row in forsider[:limit]:
        trafik = str(row["visits"]) if row["visits"] is not None else "-"
        dele = " · trafikken er delt med de andre domæner" if row["delt"] else ""
        stat = "udgives ikke" if not row["publiceret"] else "udgives"
        knap = row["knapper"] if row["knapper"] is not None else "kan ikke måles"
        print(f"{trafik:>6} {'':>5}  {(row['file'] or '(ingen fil)'):<52} "
              f"{row['domain']}{row['route']} — {knap} knap(per), {stat}{dele}")


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
    check("forsiden er ikke en købsvej",
          {"/", "/da/"} <= frontpage_routes(),
          f"{sorted(frontpage_routes())}")

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
    no_blog_dom = route_domain_map({d: [r for r in rs if r.rstrip("/") != "/blog"]
                                    for d, rs in inv.items()})
    hub_route = route_of(SITE, SITE / "blog" / "index.html")
    check("inventar uden /blog får hub-ruten til at miste domænet",
          hub_route == "/blog" and hub_route in route_domain_map(inv)
          and hub_route not in no_blog_dom,
          f"route={hub_route} i inventaret={hub_route in route_domain_map(inv)} "
          f"i mutant={hub_route in no_blog_dom}")
    check("`ukendt domæne`-rækken kan blive fyldt igen",
          hub_route not in no_blog_dom,
          f"ville stå som ukendt domæne: {not (hub_route in no_blog_dom)}")

    # 12. Dom 5, klik uden knap. Fire kontroller + fire mutationer. Formen
    #     findes **ikke** i `site/` i dag — målt 30/9 er den 0 på de 190
    #     artikler, fordi de eneste med trafik ligger på `bugbottle.dev`. Derfor
    #     bygges den syntetisk, samme grund som kontrol 5b og 7b: selftester
    #     skal dømme *evnen*, ikke data (NEXT_TASK fra vscode-artikel-knap).
    lo = [r for r in table if r["paid"] and not r["knapper"]]
    check("klassen 'klik uden knap' findes og måles (148 af 190)",
          len(lo) > 100,
          f"{len(lo)} af {len(table)}")
    check("flåsen er grøn på det målte tilstand",
          not click_no_button_problems(table),
          f"{len(click_no_button_problems(table))} problem(er)")

    # 12a. Den syntetiske række: målt trafik + publiceret rute + indirekte vej
    #      + nul knap. Den skal dømmes. Uden denne kontrol er porten grøn fordi
    #      klassen er tom, hvilket er præcis den fejl 7b beskriver.
    synth = dict(table[0])
    synth.update({
        "file": "blog/syntetisk-klik-uden-knap.html",
        "route": "/blog/syntetisk-klik-uden-knap",
        "visits": 42,
        "links": 1,
        "paid": ["/clean-copy-tool"],
        "knapper": 0,
        "domain": "mahope.tools",
        "publiceret": True,
    })
    check("en række med trafik, publiceret rute og nul knap er i klassen",
          [r["file"] for r in click_no_button([synth])] == [synth["file"]],
          f"{len(click_no_button([synth]))} række(r)")
    check("den syntetiske række gør flåsen rød uden begrundelse",
          any("NY KLIK-UDEN-KNAP" in p
              for p in click_no_button_problems([synth])),
          f"{len(click_no_button_problems([synth]))} problem(er)")

    # 12b. Hvert af de fire krav skal kunne fjerne rækken. Målt på fire
    #      mutationer af *den samme* syntetiske række — ellers kunne porten være
    #      grøn fordi den kun læser ét af dem.
    for name, mut in (
        ("trafik", {"visits": None}),
        ("publicering", {"publiceret": False}),
        ("knap", {"knapper": 1}),
        ("betalt vej", {"paid": []}),
    ):
        mutated = dict(synth, **mut)
        check(f"kravet '{name}' fjerner rækken fra klassen",
              click_no_button([mutated]) == [])

    # 12c. En begrundelse uden grund → rød (punkt 2).
    hit = click_no_button_problems([synth], {"acknowledged": [
        {"file": synth["file"], "reason": "   "}]})
    check("begrundelse uden grund giver rødt",
          any("NY KLIK-UDEN-KNAP" in p and "reason" in p for p in hit),
          f"{len(hit)} problem(er)")

    # 12d. En linje der ikke længere er i klassen → rød, og beskeden skal sige
    #      HVORFOR. Uden årsagen får næste iteration fire forklaringer på den
    #      samme linje, hvilket er målt som den almindelige måde døde linjer
    #      forsvinder på i de to andre lister. Rækken måles på disk denne gang
    #      fordi de fire årsager skal kunne skelnes: `blog/html-to-markdown-vscode`
    #      har 8 målte besøg, en publiceret rute og 1 købsknap, altså præcis en
    #      linje der har været i klassen og er faldet ud af den med *knappen*.
    with_knap = next((r for r in table if r["visits"] and r["publiceret"]
                      and r["knapper"] and r["paid"]), None)
    check("der findes en række på disk der er faldet ud af klassen med en knap",
          with_knap is not None,
          f"{with_knap['file'] if with_knap else '?'}")
    if with_knap:
        hit = click_no_button_problems(table, {"acknowledged": [
            {"file": with_knap["file"], "reason": "testbegrundelse"}]})
        dead = [p for p in hit if "DØD LINJE" in p]
        check("død linje giver rødt og siger at årsagen er knappen",
              len(dead) == 1 and "købsknap" in dead[0],
              dead[0] if dead else f"{len(hit)} problem(er)")
    #      Og de tre andre årsager skal kunne *siges*: en fil der ikke findes,
    #      en der mistede trafik, og en der ikke er publiceret. Alle tre bygges
    #      syntetisk, for ingen af dem findes i korpus i dag.
    for name, mut, expect in (
        ("filen er slettet", None, "ikke længere på disk"),
        ("trafikken forsvandt", {"visits": None}, "besøgstallet"),
        ("ruten er ikke publiceret", {"publiceret": False}, "publiceret"),
    ):
        if mut is None:
            # Filen findes hverken på disk eller i korpus, så korpus-tabellen
            # er tom: det er den eneste af de fire årsager, der ikke kan bygges
            # som en række.
            probe: list[dict] = []
            probe_file = "blog/syntetisk-slettet.html"
        else:
            probe = [dict(synth, **mut)]
            probe_file = probe[0]["file"]
        hit = click_no_button_problems(probe, {"acknowledged": [
            {"file": probe_file, "reason": "testbegrundelse"}]})
        dead = [p for p in hit if "DØD LINJE" in p]
        check(f"død linje siger at årsagen er: {name}",
              len(dead) == 1 and expect in dead[0],
              dead[0] if dead else f"{len(hit)} problem(er)")

    # 12e. Dubletter → rød (punkt 4). Listen er en mængde.
    hit = click_no_button_problems([synth], {"acknowledged": [
        {"file": synth["file"], "reason": "a"},
        {"file": synth["file"], "reason": "b"}]})
    check("dubletter i listen giver rødt",
          any("dubletter" in p for p in hit), f"{len(hit)} problem(er)")

    # 12f. Filen på disk skal findes og have de nøgler porten læser. Uden denne
    #      kontrol kan porten være grøn fordi filen ikke findes, hvilket er det
    #      samme som kontrol 9 gjorde for blindlisten.
    doc = json.loads(CLICK_NO_BUTTON.read_text(encoding="utf-8"))
    check("klassen-filen findes med note, source og acknowledged",
          set(("note", "source", "acknowledged")) <= set(doc),
          f"{sorted(doc)}")
    check("klassen-filen er grøn som den ligger på disk",
          not click_no_button_problems(table, doc),
          f"{len(click_no_button_problems(table, doc))} problem(er)")

    # 13. Kilden på de målte besøg. Målt 30/9: de tal porten rangerer på kom fra
    #     uge 38 (genereret 24/9) mens uge 39 og 40 stod med `available: false`,
    #     fordi `/api/stats` svarer 401. Ti iterationer skrev "målte besøg" uden
    #     alder. Formen *er* målt i dag, så syntetiske rapporter bruges kun til
    #     at dømme evnen — de fire årsager, en kilde kan have, skal kunne skelnes.
    import tempfile

    # Målt 30/9: fixtures med ruten `/blog/x` holdt op at være gyldige, da
    # regel 5 (se `traffic_source`) gør en rapport med en rute vi ikke udgiver
    # ubrugelig. Det er samme fejltype som opgave 10: selftestens egen
    # udgangstilfælde lå i en vokabel porten ikke accepterer. Ruten vælges derfor
    # fra *målingen* — en publiceret rute — så den holder hvis inventaret flytter.
    _pub = sorted(published_routes() or ())
    _rute = next((r for r in _pub if r.startswith("/blog/")), None)
    check("selftestens fixtures bruger en publiceret rute, ikke en opdigtet",
          _rute is not None, f"{len(_pub)} publicerede ruter")
    _rute = _rute or "/"

    with tempfile.TemporaryDirectory() as tmp:
        rep = Path(tmp)

        def write_report(name: str, week: str, generated: str | None,
                         rows_: list[dict] | None) -> None:
            body = {"iso_week": week, "traffic": {}}
            if generated:
                body["generated_at"] = generated
            body["traffic"]["top_paths"] = rows_ if rows_ else []
            if rows_ is None:
                body["traffic"]["available"] = False
            (rep / name).write_text(json.dumps(body), encoding="utf-8")

        # (a) Én rapport med tal, genereret i går: alderen skal kunne regnes,
        #     og ingen nyere uden trafik skal tælles med.
        write_report("2026-40.json", "2026-40", "2026-09-29",
                     [{"path": _rute, "visits": 11}])
        got, meta = traffic_source(rep, today=date(2026, 9, 30))
        check("kilden regner alderen ud fra generated_at",
              meta["week"] == "2026-40" and meta["age_days"] == 1
              and meta["newer_without"] == 0, json.dumps(meta, ensure_ascii=False))
        check("besøgene læses fra den rapport der er valgt",
              got == {_rute: 11}, json.dumps(got, ensure_ascii=False))

        # (b) Målt form: to nyere rapporter uden trafik. Uden denne kontrol kunne
        #     `newer_without` være konstant 0, og alderen alene ville være sand
        #     uden at sige *hvorfor* tallene er gamle.
        write_report("2026-41.json", "2026-41", "2026-09-30", None)
        write_report("2026-42.json", "2026-42", "2026-09-30", [])
        got, meta = traffic_source(rep, today=date(2026, 9, 30))
        check("en nyere rapport uden trafik tælles, og kilden bliver den ældre",
              meta["week"] == "2026-40" and meta["newer_without"] == 2
              and meta["age_days"] == 1, json.dumps(meta, ensure_ascii=False))

        # (c) Den *nyeste med tal* vinder. Uden denne kontrol kunne læseren tage
        #     den første rapport den ser, og alle målinger på de tre ville se
        #     ens ud uanset hvor gamle de var.
        write_report("2026-43.json", "2026-43", "2026-09-30",
                     [{"path": _rute, "visits": 99}])
        got, meta = traffic_source(rep, today=date(2026, 9, 30))
        check("den nyeste rapport med tal vinder over ældre",
              got.get(_rute) == 99 and meta["week"] == "2026-43"
              and meta["newer_without"] == 0, json.dumps(meta, ensure_ascii=False))

        # (d) Uden nogen rapport med tal må porten ikke finde på et tal. Den skal
        #     sige at kolonnen er en fraværende måling — ikke vise `0`, som er
        #     den samme påstand som "ingen besøgte siden".
        for path in rep.glob("*.json"):
            path.unlink()
        write_report("2026-40.json", "2026-40", "2026-09-29", None)
        got, meta = traffic_source(rep, today=date(2026, 9, 30))
        check("ingen rapport med tal giver ingen besøg og ingen kilde",
              got == {} and meta["file"] is None,
              json.dumps(meta, ensure_ascii=False))
        check("teksten siger fraværende måling, ikke et tal",
              "fraværende måling" in traffic_note(meta), traffic_note(meta))

        # (e) En rapport uden `generated_at` må ikke få en opdigtet alder.
        (rep / "2026-40.json").write_text(json.dumps({
            "iso_week": "2026-40",
            "traffic": {"top_paths": [{"path": _rute, "visits": 5}]},
        }), encoding="utf-8")
        got, meta = traffic_source(rep, today=date(2026, 9, 30))
        check("manglende dato giver alder None og siger 'uden dato'",
              meta["age_days"] is None and "uden dato" in traffic_note(meta),
              traffic_note(meta))

    # (f) Dogfooding: den målte tilstand i dag skal kunne vise alderen, ellers
    #     er hele rettelsen noget der kun virker på syntetiske rapporter.
    _, real_meta = traffic_source()
    check("rigtige rapporter giver en kilde med alder",
          isinstance(real_meta.get("file"), str)
          and real_meta.get("age_days") is not None,
          traffic_note(real_meta))

    # (g) Den røde linje i dom 5 skal skrive kilden med, så den beder om en
    #     begrundelse på et tal læseren kan veje.
    with_src = click_no_button_problems([synth], {"acknowledged": []},
                                        {"file": "2026-38.json", "week": "2026-38",
                                         "generated_at": "2026-09-24",
                                         "age_days": 6, "newer_without": 2,
                                         "reports": 4})
    check("den røde linje i dom 5 nævner kildens alder",
          any("2026-38" in p and "6 dage gammel" in p for p in with_src),
          with_src[0] if with_src else "ingen linje")

    # 13a. En rapport, der tæller vores egen trafik, må **ikke** blive kilden
    #      for en rangliste. Målt 30/9: `track.js` posterer `location.pathname`,
    #      så hvert `--live`-screenshot fra disse iterationer er et syntetisk
    #      besøg på en *ægte* rute — det kan ingen rute-port se. Her måles den
    #      anden halvdel: ruter vi slet ikke udgiver (selftest-fixtures) må
    #      gøre hele rapporten ubrugelig, og fraværet skal kunne ses.
    with tempfile.TemporaryDirectory() as tmp:
        rep2 = Path(tmp)

        def w2(name: str, week: str, rows_: list[dict]) -> None:
            (rep2 / name).write_text(json.dumps({
                "iso_week": week, "generated_at": "2026-09-29",
                "traffic": {"top_paths": rows_},
            }), encoding="utf-8")

        # (a) Ren kilde: tallene bruges, og intet kasseres.
        w2("2026-50.json", "2026-50",
           [{"path": "/blog/html-to-markdown-vscode", "visits": 8}])
        got, meta = traffic_source(rep2, today=date(2026, 9, 30))
        check("en ren rapport bruges som kilde",
              got.get("/blog/html-to-markdown-vscode") == 8
              and meta["skipped"] == [] and meta["week"] == "2026-50",
              json.dumps(meta, ensure_ascii=False))

        # (b) Den syntetiske rute gør hele rapporten ubrugelig — ikke kun
        #     rækken. Ellers kunne næste iteration blot slette den ene linje
        #     og citere resten, som om den altid havde været ren.
        w2("2026-51.json", "2026-51",
           [{"path": "/blog/html-to-markdown-vscode", "visits": 8},
            {"path": "/blog/syntetisk-klik-uden-knap", "visits": 42}])
        got, meta = traffic_source(rep2, today=date(2026, 9, 30))
        check("en rapport med en rute vi ikke udgiver kasseres helt",
              meta["file"] == "2026-50.json"
              and got.get("/blog/syntetisk-klik-uden-knap") is None
              and any("2026-51" in s for s in meta["skipped"]),
              f"file={meta['file']} skipped={meta['skipped']}")
        check("kasseringen står i teksten, så fraværet ikke er usynligt",
              "2026-51" in traffic_note(meta) and "egen trafik" in traffic_note(meta),
              traffic_note(meta))

        # (c) Er *alle* rapporter kontaminerede, skal læseren se en fraværende
        #     måling — ikke `0`, som er den samme påstand som "ingen har
        #     besøgt siden uge 38".
        for path in rep2.glob("*.json"):
            path.unlink()
        w2("2026-52.json", "2026-52",
           [{"path": "/oxloop-selftest", "visits": 7}])
        got, meta = traffic_source(rep2, today=date(2026, 9, 30))
        check("kun kontaminerede rapporter giver ingen besøg og ingen kilde",
              got == {} and meta["file"] is None and len(meta["skipped"]) == 1,
              json.dumps(meta, ensure_ascii=False))

        # (d) Mutation: gør `unpublished_rows` blind, så kontrollerne ovenfor
        #     taber deres byrde. Uden denne kunne hele rettelsen være grøn fordi
        #     den aldrig læser rækken. Modulet patch'es i *dette* navnerum —
        #     scriptet kører som `__main__`, så et `import
        #     check_article_paid_path` ville lappe en anden kopi, og mutationen
        #     ville se grøn ud uden at have rørt noget.
        saved = globals()["unpublished_rows"]
        try:
            globals()["unpublished_rows"] = lambda top, published: []
            w2("2026-53.json", "2026-53", [{"path": "/oxloop-selftest", "visits": 7}])
            got, meta = traffic_source(rep2, today=date(2026, 9, 30))
            check("en blind læser tager den syntetiske rapport med (mutation fanges)",
                  meta["file"] == "2026-53.json" and meta["skipped"] == [],
                  f"file={meta['file']} skipped={meta['skipped']}")
        finally:
            globals()["unpublished_rows"] = saved

    # 14. Delte ruter. Målt 30/9 på `main`: `/` og `/da/` står i inventaret
    #     under *alle fire* domæner, og de bærer 461 af 505 målte besøg. Den
    #     gamle `route_domains()` var en dict-forståelse, så den gemte fire
    #     domæner bag det sidste i rækkefølgen. Her dømmes læserens evne med et
    #     syntetisk inventar, fordi fejlen *kun* kan ses når der findes en delt
    #     rute — og fordi den i dag er usynlig netop fordi rækkefølgen er
    #     heldig. (15) dømmer mutationen af den gamle læsning.
    live_now = deployed_domains()
    delt_inv = {"mahope.tools": ["/"], "cleancopy.tools": ["/"],
                "bugbottle.dev": ["/"], "deskuptime.com": ["/"]}
    delt_map = route_domain_map(delt_inv)
    check("en delt rute bærer alle sine domæner, ikke det sidste",
          delt_map.get("/") == {"mahope.tools", "cleancopy.tools",
                                "bugbottle.dev", "deskuptime.com"},
          f"{sorted(delt_map.get('/', ()))}")
    check("delt-udskriften siger at ruten er delt",
          domain_label(delt_map["/"]).count("+") == 3,
          domain_label(delt_map["/"]))
    check("en delt rute er publiceret når ét af domænerne er udgivet",
          bool(delt_map["/"] & live_now), f"udgivet={sorted(live_now)}")
    check("en delt rute er publiceret på alle domæner kun hvis de alle er",
          not (delt_map["/"] <= live_now), f"{sorted(delt_map['/'])}")

    # 14a. Samme spørgsmål stillet til `unpublished_routes()`: en delt rute må
    #      *aldrig* ende i listen, fordi den findes på mindst ét live domæne.
    kun_dark = route_domain_map({"mahope.tools": ["/x"], "bugbottle.dev": ["/x"]})
    check("en delt rute med ét live domæne regnes som publiceret",
          bool(kun_dark["/x"] & live_now), f"live={sorted(kun_dark['/x'] & live_now)}")
    kun_mørk = route_domain_map({"bugbottle.dev": ["/y"]})
    check("en rute på kun udpublicerede domæner er udpubliceret",
          not (kun_mørk["/y"] & live_now), f"live={sorted(kun_mørk['/y'] & live_now)}")

    # 15. Mutationen af den gamle læsning, i samme diff som kontrollerne der
    #     dømmer den. Uden denne linje er kontrol 14 grøn fordi `route_domains`
    #     ikke findes mere, og det er præcis den fejl denne portfamilie har
    #     dømt ni gange: en kontrol der ikke kan fejle er en grøn cirkel.
    #     Beviset er at svaret *afhænger af rækkefølgen*: samme inventar,
    #     to rækkefølger, to forskellige domæne for forsiden.
    gammel_a = {r.rstrip("/") or "/": d for d, rs in delt_inv.items() for r in rs}
    delt_inv_by = {d: delt_inv[d] for d in ["bugbottle.dev", "cleancopy.tools",
                                            "deskuptime.com", "mahope.tools"]}
    gammel_b = {r.rstrip("/") or "/": d for d, rs in delt_inv_by.items() for r in rs}
    check("mutationen: den gamle dict-læsning gør forsiden til ét domæne",
          isinstance(gammel_a["/"], str) and gammel_a["/"] != gammel_b["/"],
          f"rækkefølge A={gammel_a['/']} · rækkefølge B={gammel_b['/']}")

    # 16. Dom 6, ikke-artikler. Formen *er* målt i dag — `page_rows()` giver tre
    #     ruter, to forsider og `/clean-copy-tool` med to købsknapper — så
    #     klassen er 0 af en målt grund og ikke fordi porten ingenting ser.
    sider = page_rows()
    chrome_rows = [r for r in sider if r["chrome"]]
    andre = [r for r in sider if not r["chrome"]]
    check("ikke-artiklerne måles: fire ruter med trafik, hvoraf to forsider",
          len(sider) == 4 and len(chrome_rows) == 2
          and {r["route"] for r in andre} == {"/bugbottle-demo", "/clean-copy-tool"},
          f"{len(sider)} ruter · {len(chrome_rows)} forside(r) · "
          f"{sorted(r['route'] for r in andre)}")
    check("forsiderne bærer størsteparten af den målte trafik",
          sum(r["visits"] for r in chrome_rows) == 461,
          f"{sum(r['visits'] for r in chrome_rows)} besøg")
    check("flåsen er grøn på det målte tilstand (klassen er 0)",
          not page_no_button_problems(sider),
          f"{len(page_no_button_problems(sider))} problem(er)")
    check("klassen er 0 af to målte grunde: knap, eller domænet er ikke udgivet",
          {r["route"]: (r["knapper"], r["publiceret"]) for r in andre}
          == {"/clean-copy-tool": (2, True), "/bugbottle-demo": (0, False)},
          f"{[(r['route'], r['knapper'], r['publiceret']) for r in andre]}")

    # 16a. Forsiderne er undtaget med vilje, og de skal stadig være
    #      genkendelige efter at ruterne er skrevet uden skråstreg. Uden denne
    #      kontrol dømte dom 6 den danske forside — målt 30/9 som
    #      `NY SIDE-UDEN-KNAP: /da … 31 målte besøg`.
    check("forsidegenkendelsen overlever skråstregformen",
          _chrome("/da/") and _chrome("/") and not _chrome("/blog/x"),
          f"/da/={_chrome('/da/')} /={_chrome('/')} /blog/x={_chrome('/blog/x')}")

    # 16f. Dom 7, forsiden pr. domæne. De otte rækker er målt på filerne, så
    #      porten ser her *hver* forside og ikke fire sider bag ét tal — og det
    #      er hele hullet dom 6 lod åbent: 461 af 505 målte besøg.
    forsider = frontpage_rows()
    målt = {f"{r['domain']}{r['route']}": r["knapper"] for r in forsider}
    check("dom 7 måler alle fire domæners forsider, begge sprog",
          len(forsider) == 8 and sorted({r["domain"] for r in forsider})
          == ["bugbottle.dev", "cleancopy.tools", "deskuptime.com",
              "mahope.tools"],
          f"{len(forsider)} rækker · {sorted(målt)}")
    # Målt 30/9 på filerne, ikke på en liste. De tre *udgivne* domæner har
    # 2/2, 1/1 og 1/1; bugbottle.dev står med 0 og er ikke i matricen.
    check("dom 7: de publicerede forsider har knapper, målt på filerne",
          målt.get("cleancopy.tools/") == 2
          and målt.get("cleancopy.tools/da/") == 2
          and målt.get("deskuptime.com/") == 1
          and målt.get("deskuptime.com/da/") == 1
          and målt.get("mahope.tools/") == 1
          and målt.get("mahope.tools/da/") == 1,
          f"{målt}")
    check("dom 7: filerne er fire forskellige, målt fra build-manifestet",
          len({r["file"] for r in forsider if r["route"] == "/"}) == 4
          and {r["file"] for r in forsider if r["domain"] == "cleancopy.tools"}
          == {"site/clean-copy.html", "site/da/clean-copy.html"},
          f"{sorted({r['file'] for r in forsider if r['route'] == '/'})}")
    check("dom 7: klassen er 0 på de publicerede forsider",
          not frontpage_problems(forsider, {"acknowledged": []}),
          f"{frontpage_problems(forsider, {'acknowledged': []})[:1]}")
    check("dom 7: bugbottle.dev måles men ikke dømt, fordi det ikke udgives",
          all(not r["publiceret"] for r in forsider
              if r["domain"] == "bugbottle.dev")
          and not [r for r in frontpage_no_button(forsider)
                   if r["domain"] == "bugbottle.dev"]
          and målt.get("bugbottle.dev/") == 0,
          f"bugbottle.dev={målt.get('bugbottle.dev/')} "
          f"publiceret={[r['publiceret'] for r in forsider if r['domain'] == 'bugbottle.dev']}")
    # Mutationen: en publiceret forside mister sin knap. Det er præcis det
    # dom 6 ikke kunne se, fordi den skrev `knapper: None` for delte ruter.
    minus = [dict(r, knapper=0) if r["domain"] == "mahope.tools" and r["route"] == "/" else r
             for r in forsider]
    linjer7 = frontpage_problems(minus, {"acknowledged": []})
    check("mutationen: en forside uden knap gør dom 7 rød med domæne og fil",
          [r["domain"] + r["route"] for r in frontpage_no_button(minus)]
          == ["mahope.tools/"]
          and any("mahope.tools/" in p and "site/index.html" in p
                  and "frontpage_no_button.json" in p for p in linjer7),
          linjer7[0] if linjer7 else "ingen linje")
    # `knapper is None` må *ikke* være det samme som 0. Uden denne kontrol er
    # ukendt → grøn, og det er den falske grønde der gjorde dom 6 unyttig på
    # de to ruter der bærer 91 % af trafikken.
    ukendt = [dict(r, knapper=None, file=None)
              if r["domain"] == "deskuptime.com" and r["route"] == "/da/" else r
              for r in forsider]
    check("dom 7: en forside porten ikke kan finde er rød, ikke grøn",
          not frontpage_no_button([r for r in ukendt if r["route"] == "/da/"
                                   and r["domain"] == "deskuptime.com"])
          and any("KAN IKKE MÅLE FORSIDEN" in p for p in
                  frontpage_problems(ukendt, {"acknowledged": []})),
          f"{[p for p in frontpage_problems(ukendt, {'acknowledged': []})][:1]}")
    # Et publiceret domæne uden række må heller ikke se ud som et domæne uden
    # købsknap — det er det andet "kan ikke se" i dom 6.
    check("dom 7: en manglende række for et publiceret domæne er rød",
          any("FORSLIDE UDEN MÅLING" in p for p in frontpage_problems(
              [r for r in forsider if r["domain"] != "deskuptime.com"],
              {"acknowledged": []})),
          f"{[p for p in frontpage_problems([r for r in forsider if r['domain'] != 'deskuptime.com'], {'acknowledged': []})][:1]}")
    check("dom 7: tom begrundelse giver rødt",
          any("`reason` er tom" in p for p in frontpage_problems(
              [], {"acknowledged": [{"key": "mahope.tools/", "reason": " "}]})),
          "tom grund")
    check("dom 7: en linje uden for klassen giver rødt med årsagen i beskeden",
          any("DØD LINJE" in p and "har nu 1 købsknap" in p
              for p in frontpage_problems(
                  forsider, {"acknowledged": [{"key": "mahope.tools/",
                                               "reason": "test"}]})),
          f"{[p for p in frontpage_problems(forsider, {'acknowledged': [{'key': 'mahope.tools/', 'reason': 'test'}]})][:1]}")
    check("dom 7: dubletter giver rødt (nøglen er domæne + rute)",
          any("dubletter" in p for p in frontpage_problems(
              [], {"acknowledged": [{"key": "mahope.tools/", "reason": "a"},
                                    {"key": "mahope.tools/", "reason": "b"}]})),
          "dublet")
    # Sidste kontrol: dom 6 og dom 7 dækker de forskellige ting, så en forside
    # kan ikke slippe ud mellem dem. Dom 6 springer `chrome` over; dom 7 kræver
    # en række pr. publiceret domæne pr. forside-rute.
    check("dom 6 og dom 7 dækker forsiderne mellem sig",
          {(r["route"].rstrip("/") or "/") for r in forsider if r["publiceret"]}
          == {(r["route"].rstrip("/") or "/")
              for r in page_rows() if r["chrome"]},
          f"dom 7={sorted({r['route'] for r in forsider if r['publiceret']})} "
          f"dom 6={sorted({r['route'] for r in page_rows() if r['chrome']})}")

    # 16b. En delt rute må ikke få *én* sides knaptal. Målt 30/9: `/` er fire
    #      forskellige filer — `site/clean-copy.html` (2 købsknapper),
    #      `site/deskuptime/index.html`, `site/index.html` (0 købsknapper) og
    #      `site/bugbottle.html` — og ét trafiktal summerer dem. Uden `None`
    #      skrev porten mahope.tools' forside som *siden* bag de 430 besøg.
    check("en delt rute måler ingen knapper, fordi den er flere sider",
          all(r["knapper"] is None and r["file"] is None
              for r in sider if r["delt"]),
          f"{[(r['route'], r['knapper']) for r in sider if r['delt']]}")

    # 16c. Den syntetiske række: en ikke-artikel med læsere på en udgivet rute
    #      uden købsknap skal dømmes, og den røde linje skal skrive kilden —
    #      samme to krav som dom 5.
    synth6 = [dict(andre[0], route="/scan", file="scan.html", chrome=False,
                   knapper=0, visits=17, domains=["mahope.tools"],
                   domain="mahope.tools", publiceret=True)]
    check("en ikke-artikel med læsere og ingen knap er i klassen",
          [r["route"] for r in page_no_button(synth6)] == ["/scan"],
          f"{[r['route'] for r in page_no_button(synth6)]}")
    check("sætter læseren en knap på, forsvinder rækken af klassen",
          not page_no_button([dict(synth6[0], knapper=1)]),
          f"klasse={len(page_no_button([dict(synth6[0], knapper=1)]))}")
    linjer6 = page_no_button_problems(synth6, {"acknowledged": []}, real_meta)
    check("den røde linje i dom 6 nævner ruten, besøgene og kildens alder",
          any("/scan" in p and "17 målte besøg" in p and "dage gammel" in p
              for p in linjer6),
          linjer6[0] if linjer6 else "ingen linje")
    check("dom 6: tom begrundelse giver rødt",
          any("`reason` er tom" in p for p in page_no_button_problems(
              [], {"acknowledged": [{"route": "/x", "reason": "  "}]})),
          "tom grund")
    check("dom 6: en linje uden for klassen giver rødt med årsagen i beskeden",
          any("DØD LINJE" in p and "ikke længere målte besøg" in p
              for p in page_no_button_problems(
                  sider, {"acknowledged": [{"route": "/blog/ukendt",
                                           "reason": "test"}]})),
          "død linje")
    check("dom 6: dubletter giver rødt",
          any("dubletter" in p for p in page_no_button_problems(
              [], {"acknowledged": [{"route": "/x", "reason": "a"},
                                    {"route": "/x", "reason": "b"}]})),
          "dublet")

    # 16d. En rute i inventaret uden fil i `site/` må ikke få porten til at
    #      fejle, og den skal *siges* — ellers forsvinder den fra målingen
    #      uden at nogen ved det. Rækken bruges også til at dømme at
    #      `page_rows()` tåler en manglende fil, fordi `knap_links()` ellers
    #      ville læse `None`.
    fil_løs = [dict(andre[0], file=None, route="/findes-ikke", knapper=0,
                    publiceret=True, chrome=False)]
    check("en rute uden fil i site/ måles stadig og siges det",
          any("/findes-ikke" in p for p in page_no_button_problems(
              fil_løs, {"acknowledged": []})),
          f"{len(page_no_button_problems(fil_løs, {'acknowledged': []}))} linje(r)")

    # 16e. PORTFEJL, fundet af kontrol 16 i samme diff som den dømmer den:
    #      trafiknøglen og inventarnøglen var skrevet i to former. `top_paths`
    #      skriver `/da/` med skråstreg, `route_inventory.json` skriver `/da`
    #      uden, så et dict-opslag på den normaliserede nøgle gav `None` — og
    #      `/da/` forsvandt fra målingen af ikke-artikler. Det er præcis det
    #      `CHROME_ROUTES`-undtagelsen skjuler: ruten er en forside, så en
    #      forsvunden forside ser ud som en forside der ikke er der.
    check("besøg læses på den normaliserede rute, uanset skråstreg i kilden",
          _visits_by_route({"/da/": 31}).get("/da") == 31
          and _visits_by_route({"/da": 31}).get("/da") == 31,
          f"med skråstreg={_visits_by_route({'/da/': 31})} "
          f"uden={_visits_by_route({'/da': 31})}")

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
        _print_ranking(rows(SITE, catalog), args.limit, traffic_source()[1])

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
