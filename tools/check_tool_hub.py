#!/usr/bin/env python3
"""Dom at en nav-rute kaldet «Værktøjer» faktisk fører til værktøjerne.

Fejlformen er målt 6/10 på `ceo/tools-side-med-de-tre-tjek`, som lå ucommittet
indtil denne port fandt den. `deskuptime.com` har to værktøjsruter der faktisk
serveres — `/bulk-url-checker/` og `/security-headers-checker/` — og vores egen
navigation har et menupunkt der hedder «Tools» / «Værktøjer». Men «Tools»
pegede på `../auditedwp`s **egne forside**, som gav nul af de to værktøjer,
satte sin egen `<title>`, `og:title` og canonical ved siden af `/` (to sider om
samme produkt), og kaldte den betalte desktop-app «Download for macOS &
Windows (free)».

Det værste var ikke det visuelle. Det var at **hele gaten var grøn**: 177 steps,
0 fund, mens den rute vores egen nav kalder «Tools» linkede nul værktøjer. Målt
6/10 ved at slette begge `href` fra den nye side og køre hele
`tools/quality_gate.py` — resultatet var `quality_gate: GRØN — 177 steps`. De
porte der findes dømmer priser, købsknapper, løfter og links, men ingen af dem
spørger om en indeksside overhovedet peger på det den er indeks over. Så den
kunne miste hele sit indhold uden at nogen bemærkede det.

**Dommen er derfor strukturel, ikke en navneliste.** To ting læses fra
**byggets eget filudvalg** (`build_sites.SITES` + `select_files()`), altså den
samme sandhed som `check_front_door.py` bruger til at finde forsider:

1. **Find hub-ruten fra nav-konfigurationen.** `nav[lang]` i `build_sites.SITES`
   har en post hvis *tekst* siger værktøj (`tools`, `værktøj`, `verktøj`,
   `werkzeug`, …). Den er fundet ved tekst, ikke ved at hårdkode `/tools/`, så et
   nyt domæne eller en ny nav-post der hedder «Værktøjer» dømmes automatisk.
2. **Find de ruter hub'en skal pege på.** Alle ruter i samme domæne der
   publiceres og som er **et værktøj**: de ligger under `/tools/`, eller de er
   nævnt i domænets `route_inventory` og deres fil hedder `*-checker*`. Ruter
   som er forsiden, chrome (`/privacy`, `/terms`, `/search/`, `/sitemap.xml`) eller
   artikler er ikke værktøj og skal ikke kræves.

En hub-side der mangler **ét** af dem er rød, med navnet på den manglende rute,
fordi det er præcis den information læseren (og google) ikke får. Samme regel
på dansk: en dansk hub der kun linker de engelske værktøj er rød, fordi den så
sender en dansk læser ud i engelsk midt i en opgave.

    python3 tools/check_tool_hub.py            # dom alle domæners hub-ruter
    python3 tools/check_tool_hub.py --list     # kun de dømte fund
    python3 tools/check_tool_hub.py --self-test # 10 kontroller
"""
from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

# Chrome: ruter bygget lægger i hver side, som hverken er værktøj eller en
# destination læseren kan have villet linke fra en værktøjsindeks.
CHROME_SUFFIXES = (
    "/privacy/", "/terms/", "/search/", "/404.html", "/sitemap.xml",
    "/llms.txt", "/robots.txt", "/.well-known/", "/favicon", "/apple-touch-icon",
)

# Ordet i nav-teksten der gør en post til en værktøjsindeks. Fundet på den
# **publicerede** tekst, så «Tools», «Værktøjer», «Verktøy» og «Werkzeuge» alle
# finder deres post, og «Pro» gør ikke.
#
# Ordgrænserne er `(?<!\w)`/`(?!\w)` og ikke `\b`, og det er ikke en
# brugervenlig detalje: pythons `\b` regner på `\w`, som i `re` med `str` er
# ASCII — så «Værktøjer» **ikke** matcher `værktø+[jey]` (målt: `\bværkt` er
# falsk på «Værktøjer»). En port hvis egen navnefindning fejler på det ene
# sprog den udgiver på, ville have ladt den danske halvdel af hvert domæne
# springe over. Med `(?!\w)` er «Tools» stadig fundet i «Toolshed».
HUB_WORDS = re.compile(
    r"(?i)(?<!\w)(tools?|værktø+\w*|verktøy\w*|werkzeug\w*|herramientas|outils|"
    r"strumenti|nástroje)(?!\w)")

# Ruter der er ** prosa**, ikke værktøj. En indeksside over værktøjer skal
# ikke pege på artikler — det ville være 60+ fund på mahope.tools alene, fordi
# `/blog/meta-tag-checker` har «checker» i navnet. Ruterne er de tre
# indholdssektioner bygget selv bruger på samme måde, og de er ikke en navneliste
# men de tre kataloger `check_article_paid_path.py` og `gen_sitemap.py` skiller
# på: artikler (`/blog/`), bøger (`/books/`) og CMS-guider (`/guides/`).
# `/guides/` er ikke artikler, men de er den tredje type: en side der forklarer
# en platform, ikke et værktøj der tager en URL. Målt 6/10: de 69 fund var præcis
# denne forveksling plus den danske halvdel (se `_lang`).
PROSE_PREFIXES = ("/blog/", "/books/", "/guides/", "/da/blog/", "/da/books/",
                  "/da/guides/")

# Et værktøj er en rute hvis **sidste segment** siger det. Ren tekst, fordi de
# to ruter på deskuptime.com hedder `bulk-url-checker` og
# `security-headers-checker` — de ligger ikke under `/tools/`, så en regel der
# kun læser prefixed ville se nul af dem.
TOOL_WORDS = re.compile(
    r"(?i)(checker|tjek|check|url-scan|scanner|konverter|converter|generator|"
    r"simulator|encoder|decoder|formatter|analyzer|analys|bulk|profil|profile)")


def _build():
    """`build_sites`-modulet, eller `None` i et checkout hvor det ikke kan.

    Uden den kan porten ikke se filudvalget, og så ** tier den stille** — en
    port der grønner uden at dømme noget er værre end ingen port.
    """
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        return importlib.import_module("build_sites")
    except Exception:
        return None


def hub_routes() -> dict[str, str]:
    """`domæne` → den nav-rute der hedder «Værktøjer».

    Læses fra `build_sites.SITES[...]["nav"]`, altså den samme konfiguration
    `apply_shell` skriver menuens `href` ud fra. Derfor kan den ikke glide fra
    den rigtige side: en nav-post der ændrer tekst eller adresse ændrer dommen
    samme sted.
    """
    build = _build()
    out: dict[str, str] = {}
    if build is None:
        return out
    for domain, cfg in build.SITES.items():
        for lang in ("en", "da"):
            for label, href in cfg.get("nav", {}).get(lang, []) or []:
                if not isinstance(label, str) or not HUB_WORDS.search(label):
                    continue
                if not isinstance(href, str) or not href.startswith("/"):
                    continue
                out[domain] = href if href.endswith("/") else href + "/"
                break
            if domain in out:
                break
    return out


def published_files(build) -> dict[str, dict[str, Path]]:
    """`domæne` → `{rute: kildefil}` for alt hvad bygget faktisk publicerer."""
    try:
        sites = {d: build.Site(d, c) for d, c in build.SITES.items()}
        build.select_files(sites)
    except Exception:
        return {}
    out: dict[str, dict[str, Path]] = {}
    for domain, site in sites.items():
        routes: dict[str, Path] = {}
        for _key, (src, dest) in site.files.items():
            if not str(src).endswith(".html"):
                continue
            try:
                url = build.canonical_url(dest)
            except Exception:
                continue
            if not isinstance(url, str) or not url.startswith("/"):
                continue
            route = url if url.endswith("/") else url + "/"
            routes[route] = Path(src)
        out[domain] = routes
    return out


def _lang(page: Path) -> str:
    """Sidens **publicerede** sprog, fra `<html lang>`. `""` hvis den mangler.

    Samme kilde som dom 8 i `check_pricing_page.py` bruger, og af samme grund:
    rutens navn er ikke et sprogssignal — `/da/free-tools` hedder «da» i navnet,
    men det er `<html lang="da">` der afgør om siden er dansk. Læses fra filen,
    fordi det er den der læseren og google ser.
    """
    try:
        head = page.read_text(encoding="utf-8")[:2000]
    except OSError:
        return ""
    m = re.search(r'<html\b[^>]*\blang="([a-zA-Z-]+)"', head, re.I)
    return m.group(1).lower() if m else ""


def route_lang(route: str) -> str:
    """Sproget i en rute, afledt af de to huskonventioner for dansk.

    mahope.tools bruger **to** former for dansk: `/da/…`-præfiks og `-da`-endelse
    (`/dpa-generator-da`). Kun præfikset var nok til at dømme EN-siden for de
    `-da`-værktøjer — 30 falske fund, målt. Så begge former tæller, og de er
    fundet i de byggede sider (`href="/dpa-generator-da"` står på `/free-tools`),
    ikke i en håndlavet liste.

    Samme fejlform som dom 8 i `check_pricing_page.py`, og den dømmer det samme:
    **den publicerede** form, fordi rutens navn alene ikke kan sige om en side er
    dansk. Derfor læses `lang` fra `<html lang>` når vi har siden, og denne
    funktion bruges kun til at sortere *ruter imellem hinanden*.
    """
    if route.startswith("/da/"):
        return "da"
    last = route.strip("/").rsplit("/", 1)[-1].replace(".html", "")
    return "da" if last.endswith("-da") else "en"


def tool_routes(routes: dict[str, Path], lang: str = "en") -> set[str]:
    """De af `routes` der er **værktøj i `lang`** — det hub'en skal pege på.

    Sproget er ikke en undtagelsesflås: en hub er målt for **sit eget** sprog,
    fordi det er den konvention hele sitet bruger. Den engelske `/free-tools`
    linker `/nis2-incident-generator`, den danske `/da/free-tools` linker
    `/nis2-incident-generator-da` — hver sin halvdel, ingen fejl. En port der
    slog dem sammen ville finde 30 «manglende» værktøjer på to sider der begge
    er rigtige, og dømme en hub for at have en anden sprogside som sit ansvar.
    """
    out: set[str] = set()
    for route in routes:
        if route == "/":
            continue
        if any(route.endswith(sfx) or sfx in route for sfx in CHROME_SUFFIXES):
            continue
        if route.startswith(PROSE_PREFIXES):
            continue
        if route_lang(route) != lang:
            continue
        # Sidste segment **uden** den afsluttende skråstreg. Ruterne er
        # normaliseret til at slutte med `/` (samme som bygget skriver dem), så
        # `route.rsplit("/", 1)[-1]` er `""` for dem alle — målt: det gjorde
        # navnereglen dødv, og de tre ruter den skulle fange
        # (`/bulk-url-checker/`, `/security-headers-checker/`) blev set som
        # værktøj *kun* fordi de lå under `/tools/`, hvilket de ikke gør.
        # Tre selftesttilfælde faldt på præcis det.
        name = route.strip("/").rsplit("/", 1)[-1].replace(".html", "")
        if route.startswith("/tools/"):
            out.add(route)
        elif TOOL_WORDS.search(name):
            out.add(route)
    return out


def linked_hrefs(page: Path) -> set[str]:
    """De ruter siden faktisk **linker**, normaliseret som bygget skriver dem."""
    try:
        text = page.read_text(encoding="utf-8")
    except OSError:
        return set()
    out: set[str] = set()
    for m in re.finditer(r'<a\b[^>]*href="([^"]+)"', text, re.I):
        href = m.group(1).split("#")[0].split("?")[0]
        if not href or href.startswith(("http://", "https://", "mailto:", "//")):
            continue
        out.add(href if href.endswith("/") else href + "/")
    return out


def find(domain: str, hub: str, routes: dict[str, Path],
         lang: str | None = None) -> list[str]:
    """Værktøj i domænet som hub-ruten **ikke** linker. Tom liste = grøn.

    `lang=None` betyder «læs den fra siden selv» — så selftestens fixtures uden
    `<html lang>` dømmes neutralt, mens det rigtige repo altid læser den rigtige
    værdi. Det er ikke en hale: `judge()` går aldrig gennem den.
    """
    page = routes.get(hub)
    if page is None:
        return [f"{domain}{hub}: hub-ruten har ingen kildefil — den dømmes ikke"]
    have = linked_hrefs(page)
    sprog = _lang(page) if lang is None else lang
    sprog = sprog[:2] or "en"
    missing = sorted(r for r in tool_routes(routes, sprog)
                     if r != hub and r not in have)
    return [f"{domain}{hub} linker ikke {r}" for r in missing]


def judge() -> list[str]:
    build = _build()
    if build is None:
        return []
    problems: list[str] = []
    for domain, hub in sorted(hub_routes().items()):
        routes = published_files(build).get(domain, {})
        problems += find(domain, hub, routes)
    return problems


# (navn, ruter i domænet, hub, de links hub'en har, forventede fund)
#
# Felterne er: navn, ruter, hub, links, **hub'ens sprog**, forventede fund.
# Sproget står i hvert tilfælde og ikke som et fast `lang="en"` i sløjfen —
# ellers dømte en `/da/`-hub efter engelske regler, hvilket gav tre fejl i
# selve selftesten. Den skal skrive sit eget input, også det.
#
# Hvert tilfælde skriver de links **eksplicit** i stedet for at lade dem blive
# udledt af forventningen. Det var den første skrivning, der gjorde selftesten
# grøn mod en port der ikke virkede: den byggede siden som «alle værktøjer minus
# dem i forventningen», så `linker ikke X` blev sandt ved at konstruere den
# fejl den skulle finde. En selftest der definerer sit eget svar kan ikke
# fange en fejl i dommen — kun en der skriver inputtet.
SELFTEST = [
    ("hub der linker begge værktøjer er grøn",
     ["/tools/", "/bulk-url-checker/", "/security-headers-checker/"],
     "/tools/", ["/bulk-url-checker/", "/security-headers-checker/"], "en", []),
    ("hub der mister ét værktøj er rød",
     ["/tools/", "/bulk-url-checker/", "/security-headers-checker/"],
     "/tools/", ["/security-headers-checker/"], "en",
     ["d/tools/ linker ikke /bulk-url-checker/"]),
    ("hub der mister begge er rød med begge navne",
     ["/tools/", "/bulk-url-checker/", "/security-headers-checker/"],
     "/tools/", [], "en",
     ["d/tools/ linker ikke /bulk-url-checker/",
      "d/tools/ linker ikke /security-headers-checker/"]),
    ("chrome og artikler er ikke værktøj",
     ["/tools/", "/privacy/", "/terms/", "/search/", "/blog/website-down-checker-free/"],
     "/tools/", ["/privacy/", "/terms/", "/search/",
                 "/blog/website-down-checker-free/"], "en", []),
    ("hub'en skal ikke kræve sig selv",
     ["/tools/", "/bulk-url-checker/"], "/tools/", ["/bulk-url-checker/"], "en", []),
    ("forsiden er ikke et værktøj",
     ["/tools/", "/", "/bulk-url-checker/"], "/tools/",
     ["/bulk-url-checker/"], "en", []),
    # Et værktøj under /tools/ tælles uden ordet «checker» i navnet — så
    # dækkende kun på navnet ville se nul af deskuptimes to ruter.
    ("et værktøj under /tools/ tælles",
     ["/tools/", "/tools/headline-analyzer/"], "/tools/", [], "en",
     ["d/tools/ linker ikke /tools/headline-analyzer/"]),
    # Og omvendt: et værktøj uden for /tools/ tælles på sit navn.
    ("'bulk' i navnet er nok uden /tools/-præfiks",
     ["/tools/", "/bulk-anything/"], "/tools/", [], "en",
     ["d/tools/ linker ikke /bulk-anything/"]),
    # Regression på den anden huskonvention: en dansk rute hedder også
    # `/da/…`. Den er et værktøj, men det er **dansk** — så en EN-hub skal
    # dømmes på sit eget sprog, ikke på den danske halvdel.
    ("dansk tjek-navn er et værktøj i DA, ikke i EN",
     ["/tools/", "/da/meta-tjekker/"], "/tools/", [], "en", []),
    # `href` uden skråstreg er det samme link: bygget skriver dem begge veje,
    # så en streng sammenligning ville kræve en skråstreg læseren aldrig ser.
    ("et link uden skråstreg tælles som linket",
     ["/tools/", "/bulk-url-checker/"], "/tools/", ["/bulk-url-checker"],
     "en", []),
    # Samme destinations med et anker er stadig samme link.
    ("et link med #anker tælles som linket",
     ["/tools/", "/bulk-url-checker/"], "/tools/",
     ["/bulk-url-checker/#top"], "en", []),
    # Prose-sektioner er ikke værktøj, selv om de har «checker» i navnet.
    # Uden denne undtagelse gav porten 69 fund, hvoraf de 30 i
    # `/free-tools` var artikler og danske tvillinger.
    ("blog- og bog-ruter er ikke værktøj",
     ["/tools/", "/blog/meta-tag-checker/", "/books/eaa-checklist/",
      "/guides/webflow-accessibility-check/", "/bulk-url-checker/"],
     "/tools/", ["/bulk-url-checker/"], "en", []),
    # Sproget er husets egen konvention, målt begge veje: en EN-hub skal
    # dømmes på EN-værktøj og **ikke** på danske. Første skrivning kendte kun
    # `/da/`-præfikset og gav 30 falske fund, fordi mahope.tools bruger
    # `-da`-endelsen — så porten dømte en rigtig side for at mangle en anden
    # sprogside som sit ansvar.
    ("en EN-hub dømmes ikke på -da-værktøjer",
     ["/tools/", "/dpa-generator/", "/dpa-generator-da"], "/tools/",
     ["/dpa-generator/"], "en", []),
    ("en EN-hub dømmes heller ikke på /da/-værktøjer",
     ["/tools/", "/dpa-generator/", "/da/meta-tjekker"], "/tools/",
     ["/dpa-generator/"], "en", []),
    ("men den skal på sit eget",
     ["/tools/", "/dpa-generator/", "/dpa-generator-da"], "/tools/", [], "en",
     ["d/tools/ linker ikke /dpa-generator/"]),
    # Sådan ser en DA-hub ud: den dømmer på de danske ruter og **ikke** på de
    # engelske. Det er samme konvention som på de rigtige sider, hvor
    # `/free-tools` linker `/nis2-incident-generator` og `/da/free-tools`
    # linker `/nis2-incident-generator-da`.
    ("en DA-hub dømmer på /da/-ruter, ikke på EN",
     ["/da/tools/", "/da/meta-tjekker/", "/bulk-url-checker/"], "/da/tools/",
     ["/bulk-url-checker/"], "da",
     ["d/da/tools/ linker ikke /da/meta-tjekker/"]),
]


def self_test() -> int:
    import tempfile

    fejl = 0
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)

        # Én fil pr. rute. Den første skrivning brugte **samme** sti for alle
        # ruter, så sidste skrivning overskrev de andre og hub'enlinkede sine
        # egne værktøjer *på vegne af alle ruter* — tre tilfælde fejlede af den
        # grund, ikke fordi dommen var forkert. Fixtures der deler en fil, kan
        # ikke måle noget: de måler den fil.
        def side(links: list[str], name: str = "hub") -> Path:
            p = d / f"{name}.html"
            anchors = "".join(f'<a href="{u}">x</a>' for u in links)
            p.write_text(f"<html><body>{anchors}</body></html>", encoding="utf-8")
            return p

        for navn, ruter, hub, links, sprog, forventet in SELFTEST:
            filer = {r: side([], r.rsplit("/", 1)[-1] or "root") for r in ruter}
            filer[hub] = side(links, "hub")
            got = find("d", hub, filer, lang=sprog)
            if got != forventet:
                print(f"  FEJL {navn}:\n        forventede {forventet}\n        fik      {got}")
                fejl += 1
            else:
                print(f"  ok   {navn}")

        # En hub-side der ikke findes skal **dømmes**, ikke tie.
        got = find("d", "/tools/", {"/bulk-url-checker/": side([], "bulk")})
        if not got or "ingen kildefil" not in got[0]:
            print(f"  FEJL hub uden kildefil tier i stedet for at blive dømt: {got}")
            fejl += 1
        else:
            print("  ok   hub uden kildefil dømmes")

        # Porten skal være grøn på det rigtige repo lige nu.
        rigtige = judge()
        if rigtige:
            print(f"  FEJL det rigtige repo har {len(rigtige)} fund: {rigtige[:3]}")
            fejl += 1
        else:
            print("  ok   det rigtige repo er grønt")

    # HUB_WORDS skal finde de nav-tekster der faktisk bruges på de to sprog, og
    # ignorere de andre poster i samme menu.
    fundet = [lab for lab in ("Tools", "Værktøjer", "Verktøy", "Werkzeuge",
                              "Verktøyene", "Outils", "Strumenti")
              if not HUB_WORDS.search(lab)]
    hvis_fundet = [lab for lab in ("Pro", "Docs", "Compare", "Sammenlign",
                                   "Support", "Priser", "Toolshed", "Prolimit")
                   if HUB_WORDS.search(lab)]
    for lab in fundet:
        print(f"  FEJL HUB_WORDS finder ikke «{lab}»")
        fejl += 1
    for lab in hvis_fundet:
        print(f"  FEJL HUB_WORDS tager «{lab}» for en værktøjsindeks")
        fejl += 1
    if not fundet and not hvis_fundet:
        print("  ok   HUB_WORDS matcher de rigtige og afviser de forkerte nav-tekster")

    # hub_routes skal finde deskuptime.com i det rigtige manifest, og ikke
    # tage «Pro»-posten i samme menu.
    huber = hub_routes()
    if huber.get("deskuptime.com") != "/tools/":
        print(f"  FEJL hub_routes fandt ikke deskuptime.com: {huber}")
        fejl += 1
    else:
        print("  ok   hub_routes finder /tools/ i build-manifestet")

    n = len(SELFTEST) + 4
    print(f"\nselftest: {n - fejl}/{n} kontroller")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--list", action="store_true", help="kun fundene")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    problems = judge()
    if args.list:
        for p in problems:
            print(p)
        return 1 if problems else 0
    huber = hub_routes()
    if not huber:
        print("check_tool_hub: kunne ikke læse build-manifestet — porten tier "
              "stille (den dømmer intet)")
        return 0
    print(f"check_tool_hub: {len(huber)} hub-rute(r) fundet i nav-konfigurationen")
    for domain, hub in sorted(huber.items()):
        print(f"  {domain}{hub}")
    if problems:
        print(f"\nRØD — {len(problems)} fund:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nGRØN: hver hub-rute linker de værktøjer domænet udgiver")
    return 0


if __name__ == "__main__":
    sys.exit(main())
