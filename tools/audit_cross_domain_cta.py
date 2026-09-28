"""Port: ingen CTA-link må være umålt, og ingen må tælles to gange.

Baggrund (målt 28/9 i `dist/`): 300 absolutte krydsdomenelinks sad på 87 sider
der har deres egen inline-tracker. `track.js` sprang hele siden over, når den
så en inline-tracker, og inline-trackeren læser det rå `getAttribute('href')`
gennem et mønster forankret i `^/` — så den kan ikke matche `https://…`.
Klikket blev sendt ingen vegne.

Rettelsen er strukturel: `track.js` overtager kun links der er **absolutte**, og
lader rodrelative være inline-trackerens. Det er sikkert, fordi mængderne er
disjunkte *af konstruktion* — en streng der starter med `https://` kan ikke
matche et mønster forankret i `^/`.

Derfor dømmer porten to ting, og intet tredje:

1. **Ingen døde links.** Ethvert absolutt krydsdomenelink til en route
   `track.js` kan tælle, på en side med inline-tracker, skal findes i
   `CROSS_DOMAIN`. Ellers er der ingen vej for klikket.
2. **Ingen dobbelttælling.** Enhver inline-trackers mønster skal være forankret
   i `^/`. Det er præcis den egenskab der gør (1) sikker; en mønsterform der
   ikke er forankret kan matche det samme link som `track.js`, og et klik der
   tælles to gange ser ud til at virke.

Havde porten genskrevet `CROSS_DOMAIN`s regex i sig selv, kunne den måle en
anden kode end den browseren kører. Derfor matcher den ikke regexer overhovedet
— den læser *kildedeklarationen* og bygger dens domæneliste af de fire domæner
fra `site/track.js`, så en femte vært ikke kan tilføjes i den ene og glemmes i
den anden.
"""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
TRACK_JS = ROOT / "site" / "track.js"
MARKER = "event:'cta-'"

# `event:'cta-'` i en inline <script> = siden har sin egen tracker. Dens mønster
# skal starte med `^\/` — det er hele disjunktheds-argumentet.
INLINE_RE = re.compile(r"match\(\s*/\^\\/")
# En ubetinget `if (inlineCta) return;` er præcis fejlen: track.js springer så
# hele siden over, og de absolutte links på den forsvinder igen. Uden denne
# kontrol ville porten være grøn, selv hvis rettelsen blev taget tilbage.
BLANKET_BAILOUT = re.compile(r"if\s*\(\s*inlineCta\s*\)\s*return")


def family_hosts() -> set[str]:
    """Domænerne vi ejer, læst ud af `build_sites.py`'s `SITES`."""
    src = (ROOT / "build_sites.py").read_text(encoding="utf-8")
    block = re.search(r"^SITES: dict\[str, dict\] = \{(.*?)^\}", src, re.S | re.M)
    if not block:
        raise SystemExit("audit_cross_domain_cta: SITES ikke fundet i build_sites.py")
    return set(re.findall(r'^\s{4}"([a-z.]+)": \{', block.group(1), re.M))


def cross_domain_hosts() -> set[str]:
    """Domænerne `track.js`' `CROSS_DOMAIN` faktisk erklærer."""
    src = TRACK_JS.read_text(encoding="utf-8")
    m = re.search(r"var CROSS_DOMAIN = /\^https\?:\\/\\\/\(\?:([^)]*)\)", src)
    if not m:
        raise SystemExit("audit_cross_domain_cta: CROSS_DOMAIN ikke fundet i site/track.js")
    return {part.replace("\\.", ".").strip() for part in m.group(1).split("|")}


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self._scripts: list[list[str]] = []
        self._in_script = False

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for k, v in attrs:
                if k == "href" and v:
                    self.hrefs.append(v)
        elif tag == "script" and not dict(attrs).get("src"):
            self._in_script = True
            self._scripts.append([])

    def handle_data(self, data):
        if self._in_script:
            self._scripts[-1].append(data)

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False

    def inline_source(self) -> str:
        return "\n".join("".join(s) for s in self._scripts if MARKER in "".join(s))


def is_family_absolute(href: str, hosts: set[str]) -> bool:
    m = re.match(r"^https?://([^/?#]+)", href)
    return bool(m) and m.group(1).lower() in hosts


def audit(owned: set[str], declared: set[str], dists: dict[str, list]) -> list[str]:
    """Tre regler. Hver eneste kan blive rød på rigtige data.

    1. **Dækning.** En vært `build_sites.py` bygger os, som `CROSS_DOMAIN`
       ikke erklærer, gør alle dens links usynlige igen. Det er den samme
       afdrift som før har slået de tre kopier af domænelisten i `track.js`
       fra hinanden.
    2. **Forankring.** Enhver inline-trackers mønster skal være forankret i
       `^/`. Det er præcis den egenskab der gør det sikkert for `track.js` at
       tage over de absolutte links; et mønster uden forankring kan matche det
       samme link, og et klik der tælles to gange ser ud til at virke.
    3. **Dækning i praksis.** Absolutte links i `dist/` til en vært vi ejer,
       på en side med inline-tracker, skal være noget `CROSS_DOMAIN` kan tage.
    """
    problems: list[str] = []
    if BLANKET_BAILOUT.search(TRACK_JS.read_text(encoding="utf-8")):
        problems.append(
            "site/track.js har en ubetinget `if (inlineCta) return;` — de absolutte "
            "krydsdomenelinks på inline-sider tælles ikke igen")
    missing = sorted(owned - declared)
    for host in missing:
        problems.append(
            f"build_sites.py bygger {host}, men track.js's CROSS_DOMAIN erklærer den ikke — "
            f"alle links til den tælles ikke")
    for domain, pages in sorted(dists.items()):
        for rel, page in pages:
            src = page.inline_source()
            if not src:
                continue
            if not INLINE_RE.search(src):
                problems.append(
                    f"{domain}: {rel}: inline-trackerens mønster er ikke forankret i '^/' — "
                    f"et klik kan tælles både i den og i track.js")
            for href in page.hrefs:
                m = re.match(r"^https?://([^/?#]+)", href)
                if m and m.group(1).lower() in owned and m.group(1).lower() not in declared:
                    problems.append(
                        f"{domain}: {rel}: {href!r} peger på en vært CROSS_DOMAIN ikke dækker")
                    break
    return problems


def read_dist() -> dict[str, list[Page]]:
    out: dict[str, list[Page]] = {}
    for dom in sorted(p for p in DIST.iterdir() if p.is_dir()):
        pages: list[Page] = []
        for f in sorted(dom.rglob("*.html")):
            page = Page()
            try:
                page.feed(f.read_text(encoding="utf-8", errors="ignore"))
            except Exception:  # noqa: BLE001
                continue
            pages.append((f.relative_to(dom).as_posix(), page))  # type: ignore[arg-type]
        out[dom.name] = pages  # type: ignore[assignment]
    return out


def self_test(owned: set[str], declared: set[str]) -> int:
    """Seks positive kontroller. Uden dem er `--self-test` tomt: en audit der
    ikke kan blive rød, kan heller ikke troes på når den er grøn."""
    fails = 0

    def check(name: str, got: list[str], want: int) -> None:
        nonlocal fails
        ok = len(got) == want
        print(f"  {'ok  ' if ok else 'FEJL'} {name}: {len(got)} problemer (forventede {want})")
        if not ok:
            for p in got:
                print(f"        {p}")
            fails += 1

    anchored = "var m=h.match(/^\\/(?:da\\/)?(scan)(\\.html)?$/);event:'cta-'+m[1];"
    loose = "var m=h.match(/(?:da\\/)?(scan)/);event:'cta-'+m[1];"

    def one(hrefs: list[str], src: str) -> dict:
        p = Page()
        p.hrefs = list(hrefs)
        p._scripts = [[src]] if src else []
        return {"t": [("x.html", p)]}

    # 1. Kan regel 2 blive rød: et inline-mønster uden forankring.
    check("kan blive rød (uforankret inline-mønster)",
          audit(owned, declared, one(["https://cleancopy.tools/scan"], loose)), 1)
    # 2. Rettet tilstand er grøn: forankret inline, krydsdomenelink dækket.
    check("rettet tilstand er grøn", audit(owned, declared, one(["https://cleancopy.tools/scan"], anchored)), 0)
    # 3. Kan regel 1 blive rød: en vært vi ejer, som CROSS_DOMAIN mangler.
    check("kan blive rød (vært uden for CROSS_DOMAIN)",
          audit(owned | {"nyttest.dk"}, declared, {}), 1)
    # 4. Kan regel 3 blive rød: et dist-link til den manglende vært. Regel 1
    #    fyrer også, fordi samme vært mangler i deklarationen.
    check("kan blive rød (link til ucoveret vært)",
          audit(owned, declared - {"cleancopy.tools"},
                one(["https://cleancopy.tools/scan"], anchored)), 2)
    # 5. En side uden inline-tracker må aldrig meldes om forankring.
    check("side uden inline-tracker meldes aldrig",
          audit(owned, declared, one(["https://cleancopy.tools/scan"], "")), 0)
    # 6. Rodrelative links er inline-trackerens, ikke track.js's.
    check("rodrelative links er ikke krydsdomenelinks",
          audit(owned, declared, one(["/scan", "/da/free-tools"], anchored)), 0)
    # 7. Et fremmed domæne tæller ikke som vores eget.
    check("fremmed domæne er ikke familiens",
          audit(owned, declared, one(["https://mahope.tools.evil.tld/scan"], anchored)), 0)
    print(f"  selftest: {7 - fails}/7 kontroller bestået")
    return fails


def main() -> int:
    owned, declared = family_hosts(), cross_domain_hosts()
    if "--self-test" in sys.argv:
        return 1 if self_test(owned, declared) else 0
    if not DIST.is_dir():
        print("audit_cross_domain_cta: intet dist (kør build_sites.py først) — springer over")
        return 0
    dists = read_dist()
    if not dists:
        print("audit_cross_domain_cta: intet dist at kontrollere — springer over")
        return 0
    problems = audit(owned, declared, dists)
    if problems:
        print(f"audit_cross_domain_cta: {len(problems)} problemer")
        for p in problems[:40]:
            print(f"  {p}")
        return 1
    print(f"audit_cross_domain_cta: OK — {len(owned)} domæner dækket af CROSS_DOMAIN, "
          f"alle inline-mønstre forankret i ^/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
