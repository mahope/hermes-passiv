#!/usr/bin/env python3
"""Port: hvilke absolutte krydsdomenelinks i `dist/` sender ingen CTA-begivenhed?

Baggrund er målingen 29/9 i `IMPLEMENTATION_PLAN.md`: 604 absolutte
krydsdomenelinks sendte ingen begivenhed, fordi 21 ruter ikke stod i
`site/track.js`'s `CTA_PATHS`. Rettelsen lagde navnene ind, og de tre forrige
iterationers blindplet lukkede med `tools/audit_unmeasured_routes.py` — men den
port spørger om *ruter i inventaret*, ikke om *links i det byggede site*.

Den her port spørger om den anden halvdel, som de andre ikke gør: for hvert
enkelt absolutt krydsdomenelink i `dist/`, sender den kode browseren kører en
`cta-`-begivenhed? Det er det spørgsmål, der svarer på "kan vi se vores egen
trafik", fordi bygget skriver krydsdomenelinks om til absolutte URL'er, mens de
207 sides egne trackere er forankrede i `^\/`.

Den **genbruger `check_inline_cta_events.py`'s og `check_cta_coverage_dist.py`'s
egne læsere** af `site/track.js` i stedet for at genskrive dem. Det er hele
pointen: en port der læser anderledes end browseren kan ikke bruges til at sige
"dette ser `track.js` ikke", og de tre sidste fejl i denne familie var alle
variationer over den.

Undtagelserne ligger i `ALLOWED_UNMEASURED` som *(regel, grund)* — ikke navne,
fordi to af klasserne er hele URL-mønstre. En undtagelse uden en grund er en fejl
der venter på at blive læst som en regel.

    python3 tools/audit_dist_cta_routes.py
    python3 tools/audit_dist_cta_routes.py --json
    python3 tools/audit_dist_cta_routes.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_cta_coverage_dist import (  # noqa: E402  (path-loegning er her)
    FAMILY_HOSTS,
    RE_SHARED_CTA,
    RE_SHARED_HOME,
    _js_regex,
)
from check_inline_cta_events import RE_HREF  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

# Den absolute form, som bygget skriver. Kun `https?://` + et af familiens egne
# fire domæner: et link til `deskuptime.com.evil.tld` er ikke en af vores og må
# ikke tælles som ubefalet — det er heller ikke målbart, men det er ikke vores
# trafik, og at advare om det ville være en advarsel uden rettelse.
RE_FAMILY_ABS = re.compile(
    r"^https?://(?:" + "|".join(h.replace(".", r"\.") for h in FAMILY_HOSTS) + r")"
)

# Nyden: alt efter værten, uden scheme og vært. `/da/support`, `/privacy/`, osv.
RE_PATH_ONLY = re.compile(r"^https?://[a-z.]+(?P<path>/[^#?]*)")

# `/books/<slug>` har sit eget mønster i `track.js`, fordi en tosegmentsti ikke
# kan give et gyldigt begivenhedsnavn. Læses med samme form som de to andre, så
# en mutation i filen kan slå porten rød i stedet for at tie.
RE_BOOK_PAGES = re.compile(r"CTA_BOOK_PAGES\s*=\s*(/[^\n;]+)")


# Undtagelserne, hver med sin grund. **Målt 29/9 i `dist/`: 765 absolutte
# krydsdomenelinks uden en `cta-`-begivenhed, i præcis disse klasser og ingen
# andre.** Tallene står i kommentaren ved hver regel, så en fremtidig ændring
# kan ses mod dem.
#
# Rækkefølgen er væsentlig: `privacy`/`terms` står *før* blogreglen, fordi en
# fremtidig `/blog/…/terms`-lignende sti ellers ville blive regeret af den
# bredere regel. Den strammeste regel skal altid stå først.
ALLOWED_UNMEASURED: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"^/(?:da/)?(?:privacy|terms)/?$"),
        "footerside på 320 sider; sidevisningen tæller den allerede, så et "
        "`cta-privacy` pr. sideindlæsning ville være støj (116 links, målt 29/9)",
    ),
    (
        re.compile(r"^/(?:da/)?blog(?:/.*)?$"),
        "indholdsside: den sender sin egen `pageview` ved indlæsning, og et "
        "`cta-navn` pr. indlæg ville være et ubegrænset navnerum som "
        "`handleTrack` afviser over 64 tegn (609 links, målt 29/9)",
    ),
    (
        re.compile(r"^/(?:da/)?search/?$"),
        "ikke en rute: søgningen er et `#`-anker på forsiden, der skriver i "
        "`location`, så der er ingen server-side side at linke til "
        "(16 links, målt 29/9)",
    ),
    (
        re.compile(r"^/(?:da/)?downloads/"),
        "fil, ikke rute: bygget skriver `/downloads/*.zip` som en statisk "
        "artefakt, og et klik på en fil er ikke en navigation `track.js` kan "
        "fange (5 links, målt 29/9)",
    ),
    (
        re.compile(r"^/(?:da/)?openapi\.yaml$"),
        "fil, ikke rute: OpenAPI-specet er en maskinlæsbar fil under rod, der "
        "linkes fra dokumentationen (1 link, målt 29/9)",
    ),
)


def shared_tracker(
    root: Path,
) -> tuple[re.Pattern[str] | None, re.Pattern[str] | None,
           re.Pattern[str] | None]:
    """(`CTA_PATHS`, `CTA_HOME`, `CTA_BOOK_PAGES`) som skrevet i `site/track.js`.

    Læser den **kompilerede** regex, ikke navnene i den: porten skal svare på
    hvad browseren sender ved et *givet* href, og kun det kan besvare det.
    Returnerer `(None, …)` når filen mangler eller en af dem ikke læses — aldrig
    en erstatning, for en port der læser forkert bliver grøn netop når den skal
    være rød.
    """
    try:
        source = (root / "site" / "track.js").read_text(encoding="utf-8",
                                                       errors="ignore")
    except OSError:
        return (None, None, None)
    cta = RE_SHARED_CTA.search(source)
    home = RE_SHARED_HOME.search(source)
    books = RE_BOOK_PAGES.search(source)
    return (_js_regex(cta.group(1)) if cta else None,
            _js_regex(home.group(1)) if home else None,
            _js_regex(books.group(1)) if books else None)


def event_name(href: str, cta: re.Pattern[str] | None,
               home: re.Pattern[str] | None,
               books: re.Pattern[str] | None = None) -> str | None:
    """Begivenhedsnavnet et klik på `href` sender, eller None for intet.

    Samme rækkefølge som `site/track.js`: `CTA_PATHS` først, så
    `CTA_BOOK_PAGES` for tosegmentstier, så `CTA_HOME` som sidste udvej. For den
    **absolutte** krydsdomeneform er `CTA_HOME`s gruppe 1 en af familiens fire
    værter, så den skal ikke have en ekstra medlemskabskontrol — den relative
    form har ingen gruppe 1 og tager i stedet sidens egen værtsnavn. Den forme
    giver porten ikke dømmer på her: hele spørgsmålet er de absolutte links, dem
    bygget skriver.

    Bogsidens navn får et `books-`-præfik, præcis som i `track.js`, så det er
    `cta-books-compliance-bundle` og ikke et navn med en skråstreg i — dem
    afviser `handleTrack` med 400.
    """
    if cta is not None:
        m = cta.search(href)
        if m and m.group(1):
            return f"cta-{m.group(1)}"
    if books is not None:
        m = books.search(href)
        if m and m.group(1):
            return f"cta-books-{m.group(1)}"
    if home is not None:
        m = home.search(href)
        if m and m.group(1):
            return f"cta-{re.sub(r'[.][a-z]+$', '', m.group(1))}"
    return None


def _pages(dist: Path) -> list[Path]:
    out: list[Path] = []
    for dom in FAMILY_HOSTS:
        base = dist / dom
        if base.is_dir():
            out.extend(sorted(base.rglob("*.html")))
    return out


def scan(dist: Path, cta: re.Pattern[str] | None,
         home: re.Pattern[str] | None,
         books: re.Pattern[str] | None) -> tuple[int, dict[str, dict]]:
    """(alle absolutte krydsdomenelinks, ubefalede pr. sti) i `dist/`.

    Tæller *link-instanser*, ikke sider: 116 links til `/terms` er 58 sider,
    og det er klikene der forsvinder, ikke siderne.
    """
    total = 0
    unmeasured: dict[str, dict] = {}
    for page in _pages(dist):
        rel = page.relative_to(dist).as_posix()
        for href in RE_HREF.findall(page.read_text(encoding="utf-8",
                                                   errors="ignore")):
            if not RE_FAMILY_ABS.match(href):
                continue
            total += 1
            if event_name(href, cta, home, books) is not None:
                continue
            path = RE_PATH_ONLY.match(href)
            key = path.group("path") if path else href
            entry = unmeasured.setdefault(key, {"links": 0, "pages": set()})
            entry["links"] += 1
            entry["pages"].add(rel)
    for entry in unmeasured.values():
        entry["pages"] = sorted(entry["pages"])
    return total, unmeasured


def allowed_reason(key: str) -> str | None:
    """Grunden hvis stien er tilladt ubefalet, ellers None."""
    for rule, reason in ALLOWED_UNMEASURED:
        if rule.match(key):
            return reason
    return None


def offenders(unmeasured: dict[str, dict]) -> list[tuple[str, dict]]:
    """De ubefalede stier der **ikke** står i `ALLOWED_UNMEASURED` med en grund.

    Denne funktion er portens *beslutning*, og derfor dømmer selftesten den
    direkte. En port der kun kan finde fejl, men ikke afgøre om de er fejl, er
    ikke en port — og netop det var den falske grøn i de tre forrige
    iterationer: en læsning der var forkert, gjorde advarslerne forsvinde som
    *grønt* i stedet for *rødt*.
    """
    return [(k, v) for k, v in sorted(unmeasured.items())
            if allowed_reason(k) is None]


def _self_test() -> int:
    """Positive kontroller: kan porten overhovedet *finde* en ubefalet sti?

    Uden dem er `--self-test` tomt, fordi den lykkes at være grøn i et repo hvor
    alt er målt. Fire ting dømmes, og de fire er de fire måder denne port kan
    lade sig nar:

    1. Beslutningen på syntetiske rækker — en sti ingen regel dækker skal give
       rødt, en tilladt skal være grøn.
    2. At `track.js` er læst **kompileret**: et href `CTA_PATHS` faktisk
       matcher skal give et navn. Uden `/`-strippingen i `_js_regex` rammer
       mønstret aldrig, og porten ville melde *alle 4507* links ubefalede —
       altså rød på en fejl, der ligner en ny måling.
    3. At porten kan blive rød på den kode den læser: en `CTA_PATHS` med ét
       navn fjernet fra `track.js`' *egne* kildekopi skal give præcis ét
       ubefalet link, ikke nul.
    4. At `ALLOWED_UNMEASURED` kun rummer regler med en grund, og at ingen
       regel overlapper så meget at den dækker det hele.
    """
    cta, home, books = shared_tracker(ROOT)
    cases: list[tuple[str, bool]] = []

    blind = {"links": 3, "pages": ["a.html"]}
    ok_rule = {"/privacy/": {"links": 1, "pages": []}}
    cases.append(("en sti ingen regel dækker meldes", offenders({"/support": blind}) == [("/support", blind)]))
    cases.append(("en tilladt undtagelse meldes ikke", offenders(ok_rule) == []))
    cases.append(("blandet: kun den blinde meldes",
                  [k for k, _ in offenders({**ok_rule, "/books/x": blind})] == ["/books/x"]))

    # 2. Den læser track.js kompileret, ikke som tekst.
    measured = event_name("https://cleancopy.tools/scan", cta, home, books)
    cases.append(("et href CTA_PATHS matcher giver et navn", measured == "cta-scan"))
    home_only = event_name("https://deskuptime.com", cta, home, books)
    cases.append(("en krydsdomene-hjemme giver et værtsnavn", home_only == "cta-deskuptime"))
    cases.append(("et helt fremmed domæne giver intet",
                  event_name("https://deskuptime.com.evil.tld/scan", cta, home,
                             books) is None))
    # Bogsiden: præfikset skal være med, så navnet bliver `^[a-z0-9-]+$` — dem
    # `handleTrack` i `_worker.js` afviser med 400. Det er ikke en detalje: et
    # navn med skråstreg i er en begivenhed, der aldrig kommer i tallet.
    book = event_name("https://mahope.tools/books/compliance-bundle", cta, home,
                      books)
    cases.append(("en bogside giver et præfikset navn",
                  book == "cta-books-compliance-bundle"))
    cases.append(("et bog-navn er gyldigt for `handleTrack`",
                  bool(book) and bool(re.fullmatch(r"cta-[a-z0-9-]+", book))))
    # Uden `CTA_BOOK_PAGES` skal bogsiden blive *ubealet*, altså rød. Ellers
    # ville porten være grøn fordi den læser en mønsterfil, der ikke findes.
    cases.append(("uden CTA_BOOK_PAGES er bogsiden ubefalet",
                  _unmeasured_for("https://mahope.tools/books/compliance-bundle",
                                  cta, home, None)
                  == ["https://mahope.tools/books/compliance-bundle"]))

    # 3. Kan porten blive rød på den kode den læser?
    source = (ROOT / "site" / "track.js").read_text(encoding="utf-8", errors="ignore")
    mutated = source.replace("|support|", "|", 1)
    check = re.search(r"var CTA_PATHS = (/\^.*?/);", mutated, re.S)
    if check is None:
        cases.append(("mutationen kunne ikke bygges", False))
    else:
        m_cta = _js_regex(check.group(1))
        cases.append((
            "mutationen uden `support` gør nøjagtig den rute ubefalet",
            _unmeasured_for("https://mahope.tools/support", m_cta, home, books)
            == ["https://mahope.tools/support"],
        ))
    # Og den skal blive grøn igen, ellers er mutationen et vakuum.
    cases.append(("uden mutationen er `/support` målt igen",
                  _unmeasured_for("https://mahope.tools/support", cta, home,
                                  books) == []))

    # 4. Undtagelserne er regler med en grund, og de dækker ikke alting.
    cases.append(("alle undtagelser har en grund",
                  all(reason.strip() and pattern.pattern
                      for pattern, reason in ALLOWED_UNMEASURED)))
    cases.append(("blogreglen dækker ikke en værktøjssti",
                  allowed_reason("/compliance-report") is None))
    cases.append(("privacy-reglen dækker ikke `/terms-and-conditions`",
                  allowed_reason("/terms-and-conditions") is None))

    for label, ok in cases:
        print(f"  {'fanget' if ok else 'MISLYKKEDES'}: {label}")
    failed = [label for label, ok in cases if not ok]
    if failed:
        print(f"selftest RØD: {len(failed)} kontrol(ler) fejlede")
        return 1
    print(f"selftest grøn: {len(cases)} positive kontroller grønne")
    return 0


def _unmeasured_for(href: str, cta: re.Pattern[str] | None,
                    home: re.Pattern[str] | None,
                    books: re.Pattern[str] | None = None) -> list[str]:
    """De ubefalede stier for ét syntetisk href. Selftestens arbejdsredskab."""
    if event_name(href, cta, home, books) is not None:
        return []
    path = RE_PATH_ONLY.match(href)
    key = path.group("path") if path else href
    return [] if allowed_reason(key) else [href]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return _self_test()

    cta, home, books = shared_tracker(ROOT)
    if cta is None or home is None or books is None:
        print("dist-cta-routes: RØD — `site/track.js` mangler, eller "
              "`CTA_PATHS`/`CTA_HOME`/`CTA_BOOK_PAGES` kunne ikke læses. En port "
              "der ikke kan læse den kode den skal dømme, må ikke sige 'grøn'.")
        return 1
    if not DIST.is_dir():
        print("dist-cta-routes: RØD — `dist/` findes ikke. Kør `python3 "
              "build_sites.py` først; porten måler det *byggede* site, fordi bygget "
              "skriver krydsdomenelinks om til absolutte URL'er.")
        return 1

    total, unmeasured = scan(DIST, cta, home, books)
    unmeasured = dict(sorted(unmeasured.items(), key=lambda kv: -kv[1]["links"]))
    bad = offenders(unmeasured)
    measured = total - sum(v["links"] for v in unmeasured.values())

    if args.json:
        print(json.dumps({
            "absolute_family_links": total,
            "measured": measured,
            "unmeasured": {k: {"links": v["links"], "pages": len(v["pages"]),
                                "reason": allowed_reason(k)}
                           for k, v in unmeasured.items()},
        }, indent=1, ensure_ascii=False))
        return 1 if bad else 0

    print(f"Absolutte krydsdomenelinks i `dist/`: {total}")
    print(f"Målbar af `CTA_PATHS`/`CTA_HOME`: {measured}")
    print(f"Uden en `cta-`-begivenhed: {sum(v['links'] for v in unmeasured.values())}"
          f" links i {len(unmeasured)} stier\n")
    if not unmeasured:
        print("  (ingen)")
    for key, v in unmeasured.items():
        reason = allowed_reason(key)
        print(f"  {key:<46} {v['links']:>4} l/ {len(v['pages']):>3} sider   "
              f"[{reason[:44] + '…' if reason else 'UBELET'}]")

    if bad:
        print(f"\ndist-cta-routes: RØD — {len(bad)} absolutte krydsdomenelinks "
              f"({sum(v['links'] for _, v in bad)} klik) sender ingen "
              f"`cta-`-begivenhed, og ingen regel i `ALLOWED_UNMEASURED` har en "
              f"grund til dem:")
        for key, v in bad:
            print(f"  {key} — {v['links']} links på {len(v['pages'])} sider")
        print("\nRettelsen er at gøre stien målbar i `site/track.js`' `CTA_PATHS`, "
              "eller at skrive en ny regel med sin grund i `ALLOWED_UNMEASURED`. "
              "Begge dele er valg, og begge skal kunne forklares.")
        return 1
    print("\ndist-cta-routes: grøn — hvert absolutt krydsdomenelink i `dist/` "
          "sender en `cta-`-begivenhed, med undtagelse af dem der har en "
          "registreret grund i `ALLOWED_UNMEASURED`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
