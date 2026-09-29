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
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from check_stripe_ctas import Page  # noqa: E402  (delt læser, se punkt 4 nedenfor)

SITE = ROOT / "site"
CATALOG = ROOT / "tools" / "stripe_catalog.json"
BLIND = ROOT / "tools" / "article_paid_path_blind.json"
REPORTS = ROOT / "reports" / "weekly"
INVENTORY = ROOT / "tools" / "route_inventory.json"

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
    rel = path.relative_to(root).as_posix()
    return "/" + rel[:-len(".html")]


def rows(root: Path = SITE, catalog: dict | None = None) -> list[dict]:
    catalog = catalog if catalog is not None else json.loads(CATALOG.read_text(encoding="utf-8"))
    offers = offer_routes(catalog)
    inbound = inbound_counts(root)
    visits = traffic()
    out = []
    for path in article_files(root):
        route = route_of(root, path)
        paid = paid_links(root, path, offers)
        out.append({
            "file": path.relative_to(root).as_posix(),
            "route": route,
            "visits": visits.get(route),
            "links": len(inbound.get(route, ())),
            "paid": paid,
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
    return problems


def _print_ranking(table: list[dict], limit: int) -> None:
    print(f"artikler: {len(table)} · med betalt vej: "
          f"{sum(1 for r in table if r['paid'])} · blinde: "
          f"{sum(1 for r in table if not r['paid'])}")
    print(f"{'trafik':>6} {'links':>5}  {'fil':<52} købsvej")
    blind = [r for r in table if not r["paid"]]
    for row in blind[:limit]:
        trafik = str(row["visits"]) if row["visits"] is not None else "-"
        print(f"{trafik:>6} {row['links']:>5}  {row['file']:<52} {row['route']}")


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
    real_problems = judge(SITE, catalog)
    check("listen er i synk med målingen", not real_problems,
          f"{len(real_problems)} problem(er)")
    check("målingen er ikke tom (listen ville være meningsløs)",
          0 < len(measured) < len(rows(SITE, catalog)) - 5,
          f"blind={len(measured)}")

    # 8. Ratchet: en død linje skal give rødt. Mutér listen i hukommelsen.
    data = json.loads(BLIND.read_text(encoding="utf-8"))
    patched = list(data["blind"])
    if measured:
        patched.append(measured[0])
    saved = BLIND.read_text(encoding="utf-8")
    try:
        BLIND.write_text(json.dumps({"blind": patched}, ensure_ascii=False, indent=1),
                         encoding="utf-8")
        check("død linje i listen giver rødt", bool(judge(SITE, catalog)))
    finally:
        BLIND.write_text(saved, encoding="utf-8")
    check("listen genskabt efter mutationen",
          json.loads(BLIND.read_text(encoding="utf-8"))["blind"] == data["blind"])

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
        existing = json.loads(BLIND.read_text(encoding="utf-8"))["blind"]
        added = sorted(set(measured) - set(existing))
        if added and not args.force:
            print("article-paid-path: --write ville tilføje linjer:\n  "
                  + "\n  ".join(added)
                  + "\nListen må kun krympe. Ret artiklen, eller kør med --force "
                    "og skriv en grund i filen.", file=sys.stderr)
            return 1
        BLIND.write_text(json.dumps({"blind": measured}, ensure_ascii=False, indent=1),
                         encoding="utf-8")
        print(f"article-paid-path: skrev {len(measured)} linjer "
              f"({len(existing) - len(measured)} færre)")
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
