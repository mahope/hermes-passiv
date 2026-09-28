#!/usr/bin/env python3
"""Blindpletaudit: hvilke ruter i `tools/route_inventory.json` måles ingen steds?

Baggrund er fundet fra 28/9 i `IMPLEMENTATION_PLAN.md`: `check_inline_cta_events.py`
bygger sit `tool_paths`-saet *af de hvidlister porten selv kan laese*. En rute ingen
maaler er derfor usynlig for porten — den kan ikke advare om de klik, alle trackere
i familien taber. `/free-downloads` blev fundet paa den made; det var 6 sider.

Metoden er bevidst den modsatte af sidste iterations: **find ruten, gør den
maalbar ét sted, se hvilke sider porten sa advare om.** Her kortlægges blindpletten
helt, saa valget efterfoelger staar paa et tal.

Denne audit **genbruger portens egne laesere** — `_trackers`, `_tool_names`,
`_shared_has_cta_tracker` — i stedet for at genskrive dem. Det er hele pointen:
sidste gang blev `tool_paths` bygget ved at klippe i portens input, og da læsningen
var forkert, forsvandt advarslerne stille som *grönt* i stedet for rödt. En audit der
læser anderledes end porten kan ikke bruges til at sige "dette ser porten ikke".

To maalinger pr. rute, fordi de to fejl er forskellige:

- `site/`: rodrelative `href` i kilden.
- `dist/`: den *udgivne* markup, hvor `build_sites.py` har skrevet krydsdomenelinks
  om til absolute URL'er. Det er den blinde plet i sin anden halvdel: `track.js`'s
  `CTA_PATHS` har et valgfrit vaerts-præfiks, men de 207 inline-trackere er
  forankrede i `^\\/`, saa et absolut `https://cleancopy.tools/scan` matcher dem
  ikke. Inline-trackeren har dog `if(!a)return;` og sender intet, og `track.js`
  springer helt over, naar siden har sin egen inline-tracker. Saa et krydsdomeneklik
  fra en side med egen tracker er umaaleligt.

    python3 tools/audit_unmeasured_routes.py
    python3 tools/audit_unmeasured_routes.py --json
    python3 tools/audit_unmeasured_routes.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_inline_cta_events import (  # noqa: E402  (nyt path-loegning er her)
    RE_HREF,
    _shared_has_cta_tracker,
    _shared_tracker,
    _tool_names,
    _trackers,
)

ROOT = Path(__file__).resolve().parent.parent
DOMAINS = ("mahope.tools", "cleancopy.tools", "deskuptime.com", "bugbottle.dev")

# Ruter der **skal** forblive ubefalede, hver med sin grund. Holdt ude bevidst,
# ikke glemt — en undtagelse uden en grund er bare en fejl der venter på at blive
# læst som en regel.
#
# `/privacy` og `/terms` ligger i footeren på 320 sider. De får allerede en
# talt sidevisning, fordi `track.js` sender én pageview-begivenhed pr.
# sideindlæsning. En `cta-privacy` på hvert sideindlæsning er støj, ikke salg, og
# den ville fylde alt andet i tallet.
ALLOWED_UNMEASURED = {
    "privacy": "footerside på 320 sider; sidevisningen tæller den allerede",
    "terms": "footerside på 320 sider; sidevisningen tæller den allerede",
}

# Samme vaerts-præfiks som `track.js`'s `CTA_PATHS`, men i absolut form. En inline
# tracker i `site/` kan ikke se de her — den er forankret i `^\/`. Det er hele
# pointen med `dist/`-kolonnen: de to fejl er forskellige og skal rettes forskelligt.
RE_ABS = re.compile(
    r"^https?://(" + "|".join(d.replace(".", r"\.") for d in DOMAINS) + r")"
    r"(?:/da)?/?([a-z0-9-]+)/?(?:\.html)?(?:#[^#]*)?$"
)


def measured_names(root: Path) -> set[str]:
    """Alle værktøjsnavn nogen tracker i familien maaler. Portens egen læsning."""
    names: set[str] = set()
    site = root / "site"
    for path in sorted(site.rglob("*.html")):
        for t in _trackers(path.read_text(encoding="utf-8", errors="ignore")):
            if t.pattern is not None:
                names |= _tool_names(t.pattern)
    shared = _shared_has_cta_tracker(_shared_tracker(root))
    if shared is not None and shared.pattern is not None:
        names |= _tool_names(shared.pattern)
    names.discard("")
    return names


def _scan(root: Path, sub: str) -> dict[str, dict[str, int]]:
    """Linkindgange pr. rute i `root/sub/`, talt paa den form der faktisk findes."""
    hits: dict[str, dict[str, int]] = {}

    def bump(route: str, rel: str) -> None:
        e = hits.setdefault(route, {"links": 0, "pages": 0, "_p": set()})
        e["links"] += 1
        e["_p"].add(rel)

    base = root / sub
    if not base.is_dir():
        return {}
    for path in sorted(base.rglob("*.html")):
        rel = path.relative_to(base).as_posix()
        for href in RE_HREF.findall(path.read_text(encoding="utf-8", errors="ignore")):
            if href.startswith(("mailto:", "tel:", "javascript:", "//", "#")):
                continue
            if href.startswith(("http://", "https://")):
                m = RE_ABS.match(href)
                if m and m.group(2):
                    bump(m.group(2), rel)
                continue
            seg = re.fullmatch(r"/(?:da/)?([a-z0-9-]+)/?(?:\.html)?(?:#[^#]*)?", href)
            if seg:
                bump(seg.group(1), rel)
    for e in hits.values():
        e["pages"] = len(e.pop("_p"))
    return hits


def offenders(rows: list[dict]) -> list[dict]:
    """De ubefalede ruter der ikke står i `ALLOWED_UNMEASURED` med en grund.

    Denne funktion er portens *beslutning*, og derfor dømmer selftesten den
    direkte. En audit der kun kan finde fejl, men ikke afgøre om de er fejl, kan
    ikke være port — og netop det var den falske grøn i de tre forrige
    iterationer: en læsning der var forkert, gjorde advarslerne forsvinde som
    *grønt* i stedet for *rødt*.
    """
    return [r for r in rows if r["name"] not in ALLOWED_UNMEASURED]


def _self_test() -> int:
    """Positiv kontrol: kan porten overhovedet *finde* en ubefalet rute?

    Uden denne er `--self-test` tomt, fordi det lykkes at være grøn på et repo
    hvor alt er målt. Her dømmes beslutningen på to syntetiske sæt rader: ét med
    en rute porten aldrig har set, ét med kun de tilladte undtagelser. Den første
    **skal** give rødt, den anden skal være grøn. En audit der ikke kan rødde på
    syntetisk input, kan heller ikke troes på det virkelige.
    """
    blind = [{"name": "books", "route": "mahope.tools/books/", "total_links": 613}]
    allowed = [{"name": "privacy", "route": "mahope.tools/privacy/", "total_links": 325},
               {"name": "terms", "route": "mahope.tools/terms/", "total_links": 325}]
    cases = [
        ("en rute ingen måler bliver meldt", offenders(blind) == blind),
        ("en tilladt undtagelse meldes ikke", offenders(allowed) == []),
        ("blandet: kun den blinde meldes", offenders(blind + allowed) == blind),
        ("alle undtagelser har en grund",
         all(v.strip() for v in ALLOWED_UNMEASURED.values())),
    ]
    for label, ok in cases:
        print(f"  {'fanget' if ok else 'MISLYKKEDES'}: {label}")
    failed = [label for label, ok in cases if not ok]
    if failed:
        print(f"selftest RØD: {len(failed)} kontrol(ler) fejlede")
        return 1
    print(f"selftest grøn: {len(cases)} positive kontroller grønne")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return _self_test()

    root = ROOT
    names = measured_names(root)
    site_hits = _scan(root, "site")
    dist_hits = _scan(root, "dist")
    inventory = json.loads((root / "tools" / "route_inventory.json").read_text(encoding="utf-8"))

    rows = []
    for domain, routes in inventory.items():
        for route in routes:
            name = route.strip("/")
            # `/` og `/da/` er hjemmesiden; dem maaler `CTA_HOME`, ikke `CTA_PATHS`.
            if name in ("", "da"):
                continue
            if name in names:
                continue
            s = site_hits.get(name, {"links": 0, "pages": 0})
            d = dist_hits.get(name, {"links": 0, "pages": 0})
            if not s["links"] and not d["links"]:
                continue
            rows.append({
                "route": f"{domain}{route}",
                "name": name,
                "site_links": s["links"], "site_pages": s["pages"],
                "dist_links": d["links"], "dist_pages": d["pages"],
                "total_links": s["links"] + d["links"],
            })
    rows.sort(key=lambda r: -r["total_links"])

    if args.json:
        print(json.dumps({"measured": sorted(names), "unmeasured": rows}, indent=1))
        return 1 if offenders(rows) else 0

    print(f"Målte værktøjsnavn i familien: {len(names)}")
    print("Ruter i `route_inventory.json` som ingen måler, sorteret efter ubefalet indgang:\n")
    if not rows:
        print("  (ingen)")
    for r in rows:
        beslutning = "TILLADT" if r["name"] in ALLOWED_UNMEASURED else "UBELET"
        print(f"  {r['route']:<52} site {r['site_links']:>4} l/ {r['site_pages']:>3} s   "
              f"dist {r['dist_links']:>4} l/ {r['dist_pages']:>3} s   i alt {r['total_links']:>4}"
              f"   [{beslutning}]")

    bad = offenders(rows)
    if rows:
        print(f"\n{len(rows)} ubefalede ruter med mindst ét indgående link, "
              f"{len(rows) - len(bad)} af dem tillladt med en grund.")
    if bad:
        print(f"\nunmeasured-routes: RØD — {len(bad)} ruter i `route_inventory.json` "
              f"har indgående links, men ingen tracker i familien måler dem, så hvert "
              f"klik på dem tabes:")
        for r in bad:
            print(f"  {r['route']} — {r['total_links']} links, {r['name']}")
        print("\nRettelsen er den modsatte af portens egen fejlretning: gør ruten "
              "målbar ét sted (`site/track.js`'s `CTA_PATHS`), kør porten, og den "
              "advarsler om præcis de sider der mangler navnet i deres egen "
              "hvidliste. Så kør `tools/fix_inline_tool_names.py`.")
        return 1
    print("\nunmeasured-routes: grøn — hver rute med indgående links måles "
          "mindst ét sted, med undtagelse af dem der står i ALLOWED_UNMEASURED.")
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
