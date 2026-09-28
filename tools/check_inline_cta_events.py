#!/usr/bin/env python3
"""Gate for at den indlejrede CTA-tracker sender et begivenhedsnavn workeren
accepterer, opgave fra planens NEXT_TASK 1 i `IMPLEMENTATION_PLAN.md`.

Baggrunden er en måling, ikke en formodning. `site/scan.html` og
`site/scan-da.html` byggede deres begivenhedsnavn ud fra den **valgfrie
`(da\/)?`-gruppe** — altså sprogpræfikset, ikke værktøjet:

    h.match(/^\/(da\/)?(scan|clean-copy-tool|…)(\.html)?(#[^#]*)?$/)||[])[2]
                                                           ^-- gruppeindekset

Så `/compliance-report` sendte `cta-undefined` og `/da/compliance-report#pris`
sendte `cta-da/`. Begge er gyldig JavaScript, ingen fejl i loggen — kun et
begivenhedsnavn, der hverken kan læses eller tælles, fordi `handleTrack` i
`site/_worker.js` kræver `/^[a-z0-9-]+$/` og afviser resten med **400**:

    const event = String(body.event || 'pageview').slice(0, 64);
    if (!/^[a-z0-9-]+$/.test(event)) {
      return privateJsonResp({ ok: false, error: 'Invalid event.' }, 400);
    }

To filer, ikke hele familien: 207 sider har en `cta-`-tracker, og 205 af dem
tager navnet fra gruppen med værktøjsnavnet. Netop derfor skal dette være en
port — en håndmåling ville blive ved med at være grøn de 205 andre gange.

Porten fejler ved to ting, pr. match:

1. **Et navn der ikke består `^[a-z0-9-]+$`** — herunder `cta-undefined`, fordi
   gruppeindekset peger på en gruppe der ikke deltog i matchet, og `cta-da/`,
   fordi den fik sprogpræfikset. Det er præcis de to betingelser `handleTrack`
   håndhæver, så en grøn port er ensbetydende med at begivenhederne kan tælles.
2. **Et tomt navn** — et match hvor den valgte gruppe er `null`.

Den læser `site/`, ikke `dist/`. Det er et valg og ikke en forglemme: de to
fejl var i den indlejrede `<script>` i kilden, og det er den *samme* streng der
kopieres til `dist/`. Til gengæld læser porten **sidens egne `href`**, så den
finder præcis de links der rent faktisk ville sende det ødelagte navn — en
tracker der ikke matcher noget på siden er ikke en fejl, den er blot måleless.

Uden for hard-fail har porten én advarsel, fordi et klik der ikke kan måles er
en salgsmulighed der ikke kan tælles: **en værktøjssti der står i en sides egen
href, men ikke i den sides egen whitelist.** `paid-templates` stod således i
1 af 207 lister. Advarslerne tælles pr. sti og gør porten rød kun hvis de
findes — de er en kø, ikke en fejl i en udgivet side.

**Den blinde plet, porten stadig har, og hvorfor selftesten lukker den.** En sti
*ingen* måler er uden for portens synsfelt, fordi `tool_paths` bygges af de
whitelister porten kan læse. Det var præcis den plet, der gemte
`/compliance-ai` (192 links) og hele `/deskuptime`-linkene. Den kan ikke
lukkes herfra, fordi de links der sås i `site/` er rodrelative, mens bygget
skriver dem til absolutte URL'er — en kildemåling kan ikke se det. Selftesten
lukker den *andre* halvdel: den læser den rigtige `site/track.js` og kræver, at
den matcher de former bygget faktisk producerer. Uden den kontrol kunne næste
iteration fjerne værts-præfikset igen, og porten ville være grøn.

    python3 tools/check_inline_cta_events.py
    python3 tools/check_inline_cta_events.py --self-test
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Samme regel som `handleTrack` i site/_worker.js, og kun der: ændres den
# workeren, skal den her ændres med.
RE_EVENT_NAME = re.compile(r"^[a-z0-9-]+$")

RE_SCRIPT = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S | re.I)
RE_TRACKER = re.compile(r"event:'cta-'")
RE_HREF_SEGMENT = re.compile(r"getAttribute\('href'\)\|\|'';(.*?);if\(!\w+\)return", re.S)
# Selve regexet, og det gruppeindeks der læses bagefter: `m[1]` i den gamle form
# og `[2]` på `(h.match(…)||[])` i den nye.
#
# Et regex-literal slutter på det **uescapede** skråstreg. Det er ikke en
# detalje: kilderne skriver `^\/(scan|…)`, så en `.*?/` ville stoppe ved `\/` og
# give `/^\` som mønster. Den kompilerer ikke, `pattern` bliver None, ingen
# href nogensinde simuleres, og porten er grøn uden at have set noget. Den
# første version af denne port gjorde præcis det — selftesten fangede det.
RE_LITERAL = r"/(?:[^/\\]|\\.)*/"
RE_MATCH = re.compile(rf"match\(({RE_LITERAL})", re.S)
RE_GROUP_INDEX = re.compile(r"\[(\d+)\]")
# En betinget gren der sender et fast navn: `…test(h)?'donate':…`
RE_LITERAL_BRANCH = re.compile(rf"({RE_LITERAL})\.test\(h\)\?'([a-z0-9-]+)'", re.S)
RE_HREF = re.compile(r"""<a\b[^>]*?\bhref=["']([^"']+)["']""", re.I)
# Den fælles tracker. Sådan indlæser en side den.
RE_TRACK_JS = re.compile(r"""<script\b[^>]*\bsrc=["']/track\.js["']""", re.I)
# En `href` der peger på en af familiens egne stier. Samme form som den inline
# tracker matcher på, så de to veje dømmer det samme.
RE_FAMILY_PATH = re.compile(
    r"/(?:da/)?([a-z0-9-]+)(?:\.html)?/?(?:#[^#]*)?\Z")


def _shared_tracker(root: Path) -> str:
    """Indholdet af `site/track.js`, eller en tom streng når den ikke findes."""
    path = root / "site" / "track.js"
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


# Den fælles trackers hvidliste: `var CTA_PATHS = /^\/…(scan|…)…/;`
#
# Den skal have sin egen læser. `_trackers` forventer den **indlejrede** form,
# der læser gruppen lige efter `h.match(…)`; `track.js` læser den i et separat
# regex-literal og bruger m[1] senere i en anden sætning. At genbruge
# `_trackers` ville give 0 trackere — altså "denne fil måler intet" — og
# porten ville advare om de præcis 70 sider rettelsen fik til at sende. En
# fejl i en port, der ligner de 207 andre sider grønne, er dyrere end ingen
# port, så formen læses eksplicit og med sin egen selftest.
# Den **plain** kapturerende gruppe i en hvidliste: alternativet af stier.
# `(?:da\/)` og `(\.html)?` er struktur og skal forbigås — se `_tool_names`.
RE_TOOL_GROUP = re.compile(r"\(([a-z0-9|_.\-]+)\)")


def _tool_names(pattern: "re.Pattern[str]") -> set[str]:
    """Værktøjsnavnene i en trackers hvidliste.

    Læser den første gruppe **uden** `?` — altså gruppen der rummer
    alternativet af stier — i stedet for at klippe kilden på det første `)`.
    Klipningen så `(?:da\/)?` som et navn, og da `(?:da\/)?` blev skrevet
    foran gruppen i 201 filer den 28/9, gav den `^/(?:da\/` i `tool_paths` og
    **porten blev grøn uden at se noget**: en sti ingen måler skal ikke
    advares om, så en rodet `tool_paths` slår alle advarsler fra. Det er den
    dyreste fejl en port som denne kan have, og derfor har `_tool_names` sin
    egen kontrol i selftesten.
    """
    names: set[str] = set()
    for group in RE_TOOL_GROUP.findall(pattern.pattern):
        names.update(
            name for name in group.split("|")
            if re.fullmatch(r"[a-z0-9-]+", name))
    return names


RE_SHARED_CTA = re.compile(r"CTA_PATHS\s*=\s*(/[^\n;]+)")
RE_SHARED_HOME = re.compile(r"CTA_HOME\s*=\s*(/[^\n;]+)")
RE_SHARED_SEND = re.compile(r"event:\s*'cta-'\s*\+|\['cta-'\s*\+")


def _shared_has_cta_tracker(text: str) -> Tracker | None:
    """Trackeren i `track.js`, eller None hvis filen ikke sender cta-begivenheder.

    Dømmer på *begge* dele: en hvidliste der findes, men ingen der sender den,
    måler lige så lidt som ingen hvidliste.
    """
    if not text or not RE_SHARED_SEND.search(text):
        return None
    literal = RE_SHARED_CTA.search(text)
    if not literal:
        return None
    return Tracker(_js_regex(literal.group(1)), 1, [])


def _family_links(text: str, tool_paths: set[str]) -> list[str]:
    """De værktøjsstier siden faktisk linker til, i dokumentets rækkefølge."""
    found: list[str] = []
    for href in dict.fromkeys(RE_HREF.findall(text)):
        if href.startswith(("http://", "https://", "#", "mailto:", "tel:", "javascript:", "//")):
            continue
        seg = RE_FAMILY_PATH.match(href)
        if seg and seg.group(1) in tool_paths:
            found.append(href)
    return found


def _js_regex(source: str) -> re.Pattern[str] | None:
    """Python-kompilér et JavaScript-regex-literal. `\/` betyder `/` i begge."""
    try:
        return re.compile(source.strip("/").replace(r"\/", "/"))
    except re.error:
        return None


class Tracker:
    """Én sides CTA-tracker: regex, gruppeindeks og eventuelle faste navne."""

    def __init__(self, pattern: re.Pattern[str] | None, group: int,
                 literals: list[tuple[re.Pattern[str], str]]):
        self.pattern = pattern
        self.group = group
        self.literals = literals

    def event_for(self, href: str) -> str | None:
        """Det begivenhedsnavn et klik på `href` sender, eller None (intet sendes).

        Samme rækkefølge som siden: en fast gren vinder over regexet, fordi den
        står først i den ternære kæde i `site/scan.html`.
        """
        for cond, name in self.literals:
            if cond.search(href):
                return f"cta-{name}"
        if self.pattern is None:
            return None
        m = self.pattern.search(href)
        if not m:
            return None
        value = m.group(self.group) if self.group <= (m.re.groups or 0) else None
        return f"cta-{value}" if value is not None else "cta-undefined"


def _trackers(text: str) -> list[Tracker]:
    """Alle CTA-trackere i ét HTML-dokument."""
    found: list[Tracker] = []
    for script in RE_SCRIPT.findall(text):
        if not RE_TRACKER.search(script):
            continue
        segment = RE_HREF_SEGMENT.search(script)
        if not segment:
            continue
        body = segment.group(1)
        regex_match = RE_MATCH.search(body)
        if not regex_match:
            continue
        # Gruppeindekset står i det der *følger* regexet i scriptet, så søg i
        # hele scriptet og tag den første indekserede adgang.
        after = script[regex_match.end():]
        index = RE_GROUP_INDEX.search(after)
        literals = []
        for cond, name in RE_LITERAL_BRANCH.findall(body):
            compiled = _js_regex(cond)
            if compiled is not None:
                literals.append((compiled, name))
        found.append(Tracker(_js_regex(regex_match.group(1)),
                             int(index.group(1)) if index else 1, literals))
    return found


def check(root: Path = ROOT) -> tuple[list[str], list[str]]:
    """(fejl, advarsler) for alle sider i `site/`. Tomme lister når intet er der."""
    problems: list[str] = []
    warnings: list[str] = []
    site = root / "site"
    if not site.is_dir():
        return problems, warnings

    # Først alle trackere, så vi ved hvilke værktøjsstier der overhovedet er
    # målbare i familien. En sti ingen måler, skal heller ikke advares om.
    # `track.js` tælles med: den har sin egen delegerede CTA-lytter, så dens
    # hvidliste er lige så reel som den inline forms.
    pages: list[tuple[Path, list[Tracker]]] = []
    untracked: list[tuple[str, list[str]]] = []
    tool_paths: set[str] = set()
    for path in sorted(site.rglob("*.html")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        trackers = _trackers(text)
        if not trackers:
            continue
        pages.append((path, trackers))
        for t in trackers:
            if t.pattern is not None:
                tool_paths.update(_tool_names(t.pattern))
                tool_paths.discard("")

    shared = _shared_tracker(root)
    shared_tracker = _shared_has_cta_tracker(shared)
    if shared_tracker is not None and shared_tracker.pattern is not None:
        tool_paths.update(_tool_names(shared_tracker.pattern))

    # En side *uden* egen tracker kan stadig måles, hvis den indlæser den
    # fælles `track.js`. Det er præcis rettelsen i denne iteration, så porten
    # skal kende den vej — ellers ville den advare om de 70 sider, rettelsen
    # netop fik til at sende. Den skal derfor *kun* advare om sider der hverken
    # har egen tracker eller indlæser en `track.js` der sender.
    for path in sorted(site.rglob("*.html")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if _trackers(text):
            continue
        if shared_tracker is not None and RE_TRACK_JS.search(text) is not None:
            continue
        targets = _family_links(text, tool_paths)
        if targets:
            untracked.append((path.relative_to(site).as_posix(), targets))

    unmapped: dict[str, set[str]] = {}
    for path, trackers in pages:
        rel = path.relative_to(site).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        hrefs = [h for h in dict.fromkeys(RE_HREF.findall(text)) if h]
        for tracker in trackers:
            for href in hrefs:
                event = tracker.event_for(href)
                if event is None:
                    # Intet sendes. Advarsel kun hvis linket er en værktøjssti
                    # som *andre* sider måler — så er klikket målbart i teorien.
                    seg = re.fullmatch(r"/(?:da/)?([a-z0-9-]+)(?:\.html)?(?:#[^#]*)?", href)
                    if seg and seg.group(1) in tool_paths:
                        unmapped.setdefault(seg.group(1), set()).add(rel)
                    continue
                if "undefined" in event:
                    problems.append(
                        f"{rel}: linket {href!r} sender {event!r} — gruppeindekset "
                        f"peger på en gruppe der ikke deltog i matchet, så navnet "
                        f"kan hverken læses eller tælles")
                elif not RE_EVENT_NAME.match(event):
                    problems.append(
                        f"{rel}: linket {href!r} sender {event!r}, som handleTrack "
                        f"afviser med 400 (kræver ^[a-z0-9-]+$)")

    for target, sources in sorted(unmapped.items()):
        shown = ", ".join(sorted(sources)[:3])
        more = f" (+{len(sources) - 3} flere)" if len(sources) > 3 else ""
        warnings.append(
            f"link til /{target} på {len(sources)} sider sendes ingen cta-begivenhed, "
            f"fordi stien ikke står i de sideres egen whitelist: {shown}{more} — "
            f"klikket kan ikke måles")

    if untracked:
        shown = ", ".join(f"{rel} ({len(t)} links)" for rel, t in sorted(untracked)[:4])
        more = f" (+{len(untracked) - 4} flere)" if len(untracked) > 4 else ""
        warnings.append(
            f"{len(untracked)} sider linker til en værktøjssti uden nogen vej til at "
            f"sende: hverken egen CTA-tracker eller en /track.js der har en: "
            f"{shown}{more} — klikket kan ikke måles")
    return problems, warnings


def _fixture(root: Path, pages: dict[str, str]) -> None:
    """Skriver en minimal site/ med de givne trackers."""
    for rel, tracker in pages.items():
        f = root / "site" / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(
            f'<!doctype html><html lang="en"><head><title>T</title></head>'
            f'<body><a href="/scan">Scan</a><a href="/page-profile">PP</a>'
            f'<a href="/da/scan">DA</a>'
            f'<script>{tracker}</script></body></html>',
            encoding="utf-8")


def _bare(root: Path, rel: str, track_js: bool) -> None:
    """En side der linker til værktøjsstier, men har *ingen* egen tracker.

    `_fixture` skriver altid en tracker ind. Det er præcis den fejl min første
    version af scenarie 6 lavede: siden havde en egen tracker, så advarslen
    udelukkende skyldtes den manglende `track.js` — og scenariet bevisede så
    intet om det, det siger at det beviser.
    """
    f = root / "site" / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    tag = '<script defer src="/track.js"></script>' if track_js else ""
    f.write_text(
        f'<!doctype html><html lang="en"><head><title>T</title>{tag}</head>'
        f'<body><a href="/scan">Scan</a><a href="/page-profile">PP</a>'
        f'<a href="/da/scan">DA</a></body></html>',
        encoding="utf-8")


def _tracker(regex: str, index: int, hrefs: str = "") -> str:
    return (
        "(function(){try{if(navigator.doNotTrack==='1')return;var p='/';" \
        "document.addEventListener('click',function(ev){var a=ev.target.closest"
        "('a[href]');if(!a)return;var h=a.getAttribute('href')||'';" +
        (f"var k={hrefs}?'':(h.match({regex})||[])[{index}];" if hrefs
         else f"var m=h.match({regex});if(!m)return;var k=m[{index}];") +
        "if(!k)return;navigator.sendBeacon('/api/track',new Blob([JSON.stringify("
        "{path:p,event:'cta-'+k})],{type:'application/json'}));},true);}catch(e){}})();")


# Den korrekte form, som den ser ud i de 201 filer rettelsen den 28/9 skrev:
# `(?:da\/)?` foran gruppen, så `/da/scan` og `/scan` begge sender `cta-scan`
# på **samme** gruppeindeks. Før rettelsen havde 201 af 208 trackere formen
# uden præfikset, så de målte ingen danske værktøjslinks — og `_fixture` skriver
# et `<a href="/da/scan">`, som den gamle form netop ikke kunne matche.
GOOD = _tracker(r"/^\/(?:da\/)?(scan|page-profile)(\.html)?(#[^#]*)?$/", 1)

# Kontrollen på `_tool_names`: de to former skal læse **samme** navne. Den
# gamle læsning klippede kilden på det første `)`, så `(?:da\/)?` blev læst
# som et værktøjsnavn, alle rigtige navne faldt væk, og porten blev grøn uden
# at advare om en eneste sti. Uden denne kontrol er hele advarselsdelen død,
# fordi en sti ingen måler ikke skal advares om.
for _literal, _want in (
    (r"/^\/(scan|page-profile|free-tools)(\.html)?(#[^#]*)?$/",
     {"scan", "page-profile", "free-tools"}),
    (r"/^\/(?:da\/)?(scan|page-profile|free-tools)(\.html)?(#[^#]*)?$/",
     {"scan", "page-profile", "free-tools"}),
    (r"/^\/(da\/)?(scan|page-profile|free-tools)(\.html)?(#[^#]*)?$/",
     {"scan", "page-profile", "free-tools"}),
):
    _compiled = _js_regex(_literal)
    _got = _tool_names(_compiled) if _compiled else set()
    if _got != _want:
        print(f"KONTROLFEJL: _tool_names læser {_got} fra {_literal!r}, "
              f"forventede {_want} — porten ville være grøn uden at se noget",
              file=sys.stderr)
        sys.exit(1)

# Den fælles trackers form, som den ser ud i `site/track.js` efter rettelsen i
# `track.js` den 28/9. Den skal læses af porten, ellers ville den advare om de
# præcis 70 sider rettelsen fik til at sende.
SHARED_GOOD = (
    "var CTA_MARKER = \"event:'cta-'\";\n"
    "var CTA_PATHS = /^\\/(?:da\\/)?(scan|page-profile|paid-templates)"
    "(\\.html)?\\/?(#.*)?$/;\n"
    "var inlineCta = null;\n"
    "document.addEventListener('click',function(e){try{\n"
    "if(inlineCta===null)inlineCta=hasInlineCtaTracker();if(inlineCta)return;\n"
    "var el=e.target;while(el&&el.tagName!=='A')el=el.parentNode;\n"
    "var raw=el&&el.getAttribute?el.getAttribute('href'):null;if(!raw)return;\n"
    "var m=CTA_PATHS.exec(raw);if(!m)return;\n"
    "var payload=JSON.stringify({path:p,event:'cta-'+m[1]});\n"
    "if(navigator.sendBeacon){navigator.sendBeacon('/api/track',new Blob("
    "[payload],{type:'application/json'}));}\n"
    "}catch(err){}} ,true);\n")

def self_test() -> int:
    """Bevis at porten fanger hver fejlform, den siger at fange."""
    import shutil
    import tempfile

    scenarios: list[tuple[str, list[str]]] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # kontrol: den korrekte form skal være grøn — og den skal faktisk *være
        # læst*. Uden denne tjek er en grøn port ligegyldig, fordi en tracker
        # der ikke kan kompileres ligner en side uden fejl.
        _fixture(root, {"ok.html": GOOD})
        control, _ = check(root)
        if control:
            for p in control:
                print(f"KONTROLFEJL: {p}", file=sys.stderr)
            return 1
        ok = _trackers((root / "site" / "ok.html").read_text(encoding="utf-8"))
        if not ok or any(t.pattern is None for t in ok):
            print("KONTROLFEJL: trackeren blev ikke læst — porten ville være grøn "
                  "uden at se noget", file=sys.stderr)
            return 1
        if ok[0].event_for("/scan") != "cta-scan":
            print(f"KONTROLFEJL: /scan sendte {ok[0].event_for('/scan')!r}, "
                  "forventede 'cta-scan'", file=sys.stderr)
            return 1

        # 1 — skiftet gruppeindeks: [2] på et regex uden (da\/)? rammer den
        #     valgfrie `(\.html)?`, som er None for /scan → cta-undefined.
        shutil.rmtree(root / "site")
        _fixture(root, {"a.html": _tracker(
            r"/^\/(scan|page-profile)(\.html)?(#[^#]*)?$/", 2)})
        scenarios.append(("gruppeindeks skiftet uden for værktøjsgruppen",
                          check(root)[0]))

        # 2 — (da\/)? foran gruppen, som i site/scan.html før rettelsen: [1] er
        #     sprogpræfikset. /scan giver cta-undefined, /da/scan giver cta-da/
        #     med et skråstreg, som handleTrack afviste med 400.
        shutil.rmtree(root / "site")
        _fixture(root, {"b.html": _tracker(
            r"/^\/(da\/)?(scan|page-profile)(\.html)?(#[^#]*)?$/", 1)})
        problems = check(root)[0]
        if not any("cta-da/" in p for p in problems):
            print(f"SELFTEST UFORVENTET: forventede cta-da/ blandt {problems}",
                  file=sys.stderr)
            return 1
        scenarios.append(("(da\\/)? som gruppe 1 (cta-da/ og cta-undefined)",
                          problems))

        # 3 — værktøjsnavnet fjernet fra gruppen: `(?:…)` er ikke-kapturerende,
        #     så [1] rammer igen den valgfrie `(\.html)?` → cta-undefined.
        shutil.rmtree(root / "site")
        _fixture(root, {"c.html": _tracker(
            r"/^\/(?:scan|page-profile)(\.html)?(#[^#]*)?$/", 1)})
        scenarios.append(("værktøjsnavnet fjernet fra gruppen", check(root)[0]))

        # 4 — kontrol: den rettede form fra site/scan.html skal være grøn. Den
        #     har stadig (da\/)? i regexet, bare ikke som gruppe 1 — så hvis
        #     porten afviste den, ville den umuliggøre den eneste rettelse der
        #     findes til fejlen.
        shutil.rmtree(root / "site")
        _fixture(root, {"f.html": _tracker(
            r"/^\/(da\/)?(scan|page-profile)(\.html)?(#[^#]*)?$/", 2)})
        if check(root)[0]:
            for p in check(root)[0]:
                print(f"KONTROLFEJL (den rettede form skal være lovlig): {p}",
                      file=sys.stderr)
            return 1

        # 5 — kontrol: advarslen om en umålt værktøjssti skal fange paid-templates,
        #     der stod i 1 af 207 lister. Den skal være en advarsel, ikke en fejl.
        shutil.rmtree(root / "site")
        _fixture(root, {
            "d.html": _tracker(
                r"/^\/(scan|page-profile)(\.html)?(#[^#]*)?$/", 1),
            "e.html": _tracker(
                r"/^\/(scan|page-profile|paid-templates)(\.html)?(#[^#]*)?$/", 1),
        })
        d = root / "site" / "d.html"
        d.write_text(d.read_text(encoding="utf-8").replace(
            '<a href="/page-profile">PP</a>',
            '<a href="/page-profile">PP</a><a href="/paid-templates">PT</a>'),
            encoding="utf-8")
        problems, warnings = check(root)
        if problems:
            for p in problems:
                print(f"KONTROLFEJL (umålt sti er en advarsel, ikke en fejl): {p}",
                      file=sys.stderr)
            return 1
        if not any("/paid-templates" in w for w in warnings):
            print("KONTROLFEJL: advarslen om en umålt værktøjssti kom ikke", file=sys.stderr)
            return 1

        # 6 — den fejlform denne iteration rettede: en side der linker til en
        #     værktøjssti og hverken har egen tracker eller indlæser en
        #     `track.js` med en. Uden advarslen er de 7 sådanne sider usynlige.
        #     Siden skal *ikke* have en egen tracker — ellers er den jo dækket,
        #     og så beviser scenariet ingenting.
        shutil.rmtree(root / "site")
        _bare(root, "g.html", track_js=True)
        # En side der *gør* måle, så `tool_paths` ikke er tom. Porten advarser
        # ikke om en sti ingen måler, og det er rigtigt — men så ville scenariet
        # advare af den grund og ikke af den, det skal bevise.
        _fixture(root, {"ok.html": GOOD})
        (root / "site" / "track.js").write_text(SHARED_GOOD, encoding="utf-8")
        problems, warnings = check(root)
        if problems:
            for p in problems:
                print(f"KONTROLFEJL (delt track.js skal gøre siden målbar): {p}",
                      file=sys.stderr)
            return 1
        if warnings:
            print(f"SELFTEST UFORVENTET: en side med fungerende track.js må ikke "
                  f"advares: {warnings}", file=sys.stderr)
            return 1

        # 6b — samme side, men `track.js`-taggen er væk: advarselsen skal komme.
        #     `ok.html` står der stadig, for porten advarser ikke om en sti
        #     *ingen* måler — så uden en målende side ville advarslen udløse af
        #     den grunde og ikke af den, den skal bevise.
        _bare(root, "g.html", track_js=False)
        warnings = check(root)[1]
        if not warnings:
            print("SELFTEST FEJLEDE: en side uden tracker og uden track.js gav "
                  "ingen advarsel — klikket kan ikke måles, og intet siger det",
                  file=sys.stderr)
            return 1
        scenarios.append(("link til værktøjssti uden nogen tracker at sende med",
                          warnings))

        # 6c — `track.js` indlæses, men har *kun* sidevisningen. Den skal
        #     advares: en hvidliste-sti uden en sender måler lige så lidt som
        #     ingen hvidliste, så en port der kun læser navnet på variablen
        #     ville være grøn på en fil der ikke gør noget.
        _bare(root, "g.html", track_js=True)
        (root / "site" / "track.js").write_text(
            "var CTA_PATHS = /^\\/(scan|page-profile)(\\.html)?$/;\n", encoding="utf-8")
        warnings = check(root)[1]
        if not warnings:
            print("SELFTEST FEJLEDE: en track.js uden sender gav ingen advarsel",
                  file=sys.stderr)
            return 1
        scenarios.append(("track.js med hvidliste men uden sender", warnings))

        # 6d — kontrol: `track.js` skal *læses*, ikke antaget. Uden denne
        #     kontrol er hele advarslen ligegyldig, fordi en port der aldrig
        #     åbner filen ville være grøn på enhver side der indlæser den.
        _bare(root, "g.html", track_js=True)
        (root / "site" / "track.js").write_text(SHARED_GOOD, encoding="utf-8")
        shared = _shared_has_cta_tracker(SHARED_GOOD)
        if shared is None or shared.pattern is None:
            print("KONTROLFEJL: track.js blev ikke læst — porten ville være grøn "
                  "uden at have set, at der står en sender i den", file=sys.stderr)
            return 1
        if shared.event_for("/scan") != "cta-scan":
            print(f"KONTROLFEJL: den delte tracker sendte "
                  f"{shared.event_for('/scan')!r} for /scan, forventede 'cta-scan'",
                  file=sys.stderr)
            return 1

        # 7 — kontrol på den **rigtige** `site/track.js`, ikke på en fixture.
        #     Den skal kunne se de former bygget faktisk producerer: en post på
        #     mahope.tools linker i `dist/` til `https://deskuptime.com/`, fordi
        #     bygget skriver krydsdomænelinks absolutte. Målt 28/9 i `dist/` lå
        #     2020 af de links, der peger på en udgivet route, som absolutte URL'er
        #     — og et mønron forankret i `^\/` kan ikke matche én af dem. Fjernes
        #     værts-præfikset igen, dør hele den her dækning, og intet i
        #     `check()` ville se det: porten læser `site/`, hvor linkene stadig
        #     er rodrelative. Derfor er det en kontrol mod filen, ikke mod
        #     portens egen syntaks.
        real = _shared_tracker(ROOT)
        real_tracker = _shared_has_cta_tracker(real)
        if real_tracker is None or real_tracker.pattern is None:
            print("KONTROLFEJL: site/track.js blev ikke læst — porten ville være "
                  "grøn uden at se den kode der faktisk udgives", file=sys.stderr)
            return 1
        home = _js_regex(RE_SHARED_HOME.search(real).group(1)
                         if RE_SHARED_HOME.search(real) else "")
        for href, want in (("https://cleancopy.tools/clean-copy-tool", "cta-clean-copy-tool"),
                           ("https://deskuptime.com/", "cta-deskuptime"),
                           ("https://mahope.tools/compliance-ai", "cta-compliance-ai"),
                           ("/scan", "cta-scan")):
            got = real_tracker.event_for(href)
            if got is None and home is not None:
                m = home.match(href)
                if m:
                    got = "cta-" + re.sub(r"\.[a-z]+$", "", m.group(1))
            if got != want:
                print(f"KONTROLFEJL: site/track.js sender {got!r} for {href!r}, "
                      f"forventede {want!r}", file=sys.stderr)
                return 1
        # En tredjeparts-URL der *ligner* en af vores må ikke tælles: ellers kunne
        # enhver `https://deskuptime.com.evil.tld/scan` se ud som et familielink.
        spoof = "https://deskuptime.com.evil.tld/scan"
        got = real_tracker.event_for(spoof)
        if got is None and home is not None and home.match(spoof):
            got = "tællet"
        if got is not None:
            print(f"KONTROLFEJL: site/track.js sender {got!r} for {spoof!r} — "
                  "en URL der kun ligner familiens skal ikke tælles", file=sys.stderr)
            return 1

    for name, problems in scenarios:
        if not problems:
            print(f"SELFTEST FEJLEDE: scenariet '{name}' gav ingen fejl — porten er død",
                  file=sys.stderr)
            return 1
        print(f"  fanget: {name} ({len(problems)} problem(er))")
    print(f"selftest grøn: {len(scenarios)} fejlformer fanget, 4 positive kontroller grønne")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true",
                    help="bevis at porten fanger de fejlformer den siger at fange")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    problems, warnings = check()
    for w in warnings:
        print(f"  advarsel: {w}", file=sys.stderr)
    if problems:
        print(f"inline-cta-events: {len(problems)} problem(er)", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"inline-cta-events: grøn — hvert match sender et navn handleTrack accepterer"
          + (f" ({len(warnings)} advarsler)" if warnings else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
