#!/usr/bin/env python3
"""Hvor mange links i det **byggede** site sender en CTA-begivenhed, og hvor
mange gør det ikke. Porten til NEXT_TASK 1 fra iterationen 28/9.

Baggrund, målt i `dist/` 28/9. `check_inline_cta_events.py` læser `site/`, og
det er den fejlform den ikke kan se: bygget skriver krydsdomænelinks til
**absolutte** URL'er (`https://cleancopy.tools`, ikke `/clean-copy`), så en
kilde-åben mil måling er måling af en anden kode end den browseren kører. Den
forrige iteration rettede `CTA_PATHS` for præcis den grund. `CTA_HOME` fik den
ikke, og det er denne port der fandt det: `CTA_HOME` krævede både et scheme og
en skråstreg efter værten, så **de 2184 links der skriver domænet uden
slutstreg** (`https://cleancopy.tools`, skrevet af `build_sites.py`'s
link-omskrivning) og **alle rodrelative `href="/"` og `href="/da/"`** sendte
intet. Det er flere klik end de 1781 sidste iteration rettede.

Hvorfor porten er sin egen, og ikke en ekstra advarsel i den indlejrede:
`check_inline_cta_events.py` dømmer *én sides egen* tracker mod *sidens egne*
`href`. Den skal ikke have en opsummering på tværs af domæner, fordi dens
fejlregel er "denne sides links skal kunne måles" — en port der samler alle
siders links ind i én sum ville hæve advarslerne til fejl for sider, hvis
linket er korrekt målt af den delte lytter. Denne port har den modsatte
opgave: at tælle den delte lytter alene.

Forventningen er uafhængig af `track.js`. Det er hele pointen: hvis
`REQUIRED_SLUGS` blev læst ud af `CTA_PATHS`, ville porten være grøn i præcis
det tilfælde den skal være rød i — en hvidliste der mister et navn. Derfor er
listen skrevet ud her, og selftesten kræver at hvert navn faktisk er en
udgivet rute, så den heller ikke kan råne i stilhed.

    python3 tools/check_cta_coverage_dist.py              # målingen, rød/grøn
    python3 tools/check_cta_coverage_dist.py --report     # alle ruter, sorteret
    python3 tools/check_cta_coverage_dist.py --self-test  # selftestens egne krav
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# Hvad der SKAL kunne måles. Håndskrevet, ikke udledt, og ikke læst af track.js.
# --------------------------------------------------------------------------
# De fire forside-domæner. Værten *er* navnet på dem, så der er ingen slug.
FAMILY_HOSTS = ("mahope.tools", "cleancopy.tools", "deskuptime.com", "bugbottle.dev")

# Hver slug er et værktøj i familien og en udgivet rute. Listen er kilden til
# portens rødregel: ethvert link der peger på en af dem skal sende
# `cta-<slug>`. Tilføjes der et nyt produkt, kommer det her — *ikke* i
# `track.js` alene, for da ville porten ikke kunne se at det manglede.
#
# `/deskuptime` står her, fordi `site/page-profile.html`'s gamle lister navngiver
# det; målt 28/9 at det ikke er en rute på mahope.tools, så det tælles kun der
# hvor det faktisk er en udgivet rute (på deskuptime.com som `deskuptime`).
REQUIRED_SLUGS = frozenset({
    "scan", "scan-da", "clean-copy-tool", "page-profile", "site-icons",
    "text-diff", "url-to-markdown", "free-tools", "compliance-report",
    "compliance-ai", "compliance-guide", "compliance-site-check",
    "paid-templates", "deskuptime",
})

# Bevidst *ikke* målt, og det er beslutningen deres (28/9), ikke en mangel:
# `/blog/*`, `/books/*`, `/support`, `/api/*` og `/activate/` er chrome og
# indhold, ikke værktøjer. De klassificeres som "ikke et familieværktøj" af
# `_classify`, så de går aldrig ind i portens rødregel. Listen er derfor tom —
# og det er en klove: en undtagelse skal skrives her med en grund, ikke
# smugles ind ved at slå et navn ud af REQUIRED_SLUGS.
EXEMPT: dict[str, str] = {}

RE_HREF = re.compile(r"""<a\b[^>]*?\bhref=["']([^"']+)["']""", re.I)
RE_SHARED_SEND = re.compile(r"event:\s*'cta-'\s*\+|\['cta-'\s*\+")
RE_SHARED_CTA = re.compile(r"CTA_PATHS\s*=\s*(/[^\n;]+)")
RE_SHARED_HOME = re.compile(r"CTA_HOME\s*=\s*(/[^\n;]+)")
RE_SHARED_HOSTS = re.compile(r"CTA_HOSTS\s*=\s*(/[^\n;]+)")
# Værten i en *absolut* hjemmeform-gren. Gruppe 1 i `CTA_HOME`, som er
# `undefined` for den rodrelative, fordi den ikke kender sit eget domæne.
RE_HOME_GROUP = re.compile(r"\(\?\:https\?[^)]*?\((?:[^()]|\\\.)*\)")
# Navnet på en udgivet rute, som buildets sitemap-form: `/scan`, `/da/scan/`.
RE_ROUTE = re.compile(r"\A/(?:da/)?([a-z0-9-]+)(?:\.html)?/?\Z")


def _js_regex(source: str) -> re.Pattern[str] | None:
    """Python-kompilér et JavaScript-regex-literal. `\/` betyder `/` i begge."""
    try:
        return re.compile(source.strip("/").replace(r"\/", "/"))
    except re.error:
        return None


class Shared:
    """Den delte lytter i `site/track.js`, læst som den er skrevet."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.sends = bool(RE_SHARED_SEND.search(source))
        cta = RE_SHARED_CTA.search(source)
        home = RE_SHARED_HOME.search(source)
        hosts = RE_SHARED_HOSTS.search(source)
        self.paths = _js_regex(cta.group(1)) if cta else None
        self.home = _js_regex(home.group(1)) if home else None
        self.hosts = _js_regex(hosts.group(1)) if hosts else None
        # Er den relative gren overhovedet dækket af en værtsliste? Uden den
        # sender `href="/"` intet, fordi lytteren ikke kender sit eget domæne.
        self.relative = bool(self.home and self.home.search("/da/"))
        self.family_hosts = set()
        if self.hosts:
            self.family_hosts = {m for h in FAMILY_HOSTS
                                 if (m := self.hosts.match(h))}

    def event_for(self, href: str, own_host: str) -> str | None:
        """Begivenhedsnavnet et klik på `href` sender, eller None (intet sendes).

        Samme rækkefølge som `site/track.js`: `CTA_PATHS` først, `CTA_HOME` som
        fallback, fordi slaget står i den ternære kæde i den fil.
        """
        if self.paths:
            m = self.paths.search(href)
            if m:
                return f"cta-{m.group(1)}"
        if self.home:
            m = self.home.search(href)
            if m:
                # Group 1 is the host, but only in the absolute form — where it
                # is one of the four by construction, so it needs no membership
                # test. The root-relative form has no group 1, so it takes the
                # page's own hostname and *does* need one: a fork or a
                # `*.pages.dev` preview hostname is not a click we sell on.
                if m.group(1):
                    return f"cta-{re.sub(r'[.][a-z]+$', '', m.group(1))}"
                if not self.hosts or not self.hosts.match(own_host):
                    return None
                return f"cta-{re.sub(r'[.][a-z]+$', '', own_host)}"
        return None


def _split_href(href: str) -> tuple[str | None, str]:
    """(domæne, sti) for ét `href` i `dist/`, eller (None, "") når det ikke er en
    intern link. Absolutte URL'er på et af familiens domæner tages med, fordi
    dem skriver bygget — det er hele grunden til at porten læser `dist/`."""
    if href.startswith(("http://", "https://")):
        rest = href.split("://", 1)[1]
        host, _, path = rest.partition("/")
        if host.lower() not in FAMILY_HOSTS:
            return None, ""
        return host.lower(), "/" + path
    if href.startswith(("#", "mailto:", "tel:", "javascript:", "//", "")):
        return None, ""
    return "own", href


def _classify(host: str | None, path: str) -> str:
    """`tool`, `home` eller `other` — skal et link til den rute kunne måles?"""
    if host is None:
        return "other"
    clean = path.split("#")[0].split("?")[0]
    if clean.endswith(".html"):
        clean = clean[:-5]
    if clean in ("", "/", "/da", "/da/"):
        return "home"
    if clean.endswith("/") and clean.count("/") == 2 and clean.startswith("/da/"):
        return "home"
    seg = RE_ROUTE.match(clean)
    if seg and seg.group(1) in REQUIRED_SLUGS:
        return "tool"
    return "other"


def _pages(dist: Path) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    for dom in FAMILY_HOSTS:
        base = dist / dom
        if not base.is_dir():
            continue
        for page in sorted(base.rglob("*.html")):
            out.append((dom, page))
    return out


def measure(root: Path = ROOT) -> tuple[dict, list[str], list[str]]:
    """(tallene pr. rute, fejl, advarsler) for det byggede site."""
    shared = Shared(_read(root / "site" / "track.js"))
    rows: dict[str, dict] = {}
    problems: list[str] = []
    warnings: list[str] = []
    pages = _pages(root / "dist")
    if not pages:
        return rows, problems, ["intet bygget i dist/ — springer målingen over"]

    # Uden en af delene sender lytteren intet, og det skal være en fejl og ikke
    # en stille grøn: det er præcis den fejlform porten er skrevet imod.
    for label, obj in (("CTA_PATHS", shared.paths), ("CTA_HOME", shared.home),
                       ("CTA_HOSTS", shared.hosts)):
        if obj is None:
            problems.append(f"site/track.js: {label} mangler eller kunne ikke "
                            "læses — lytteren sender intet, så intet kan måles")
    if not shared.sends:
        problems.append("site/track.js: ingen `cta-`-afsendelse fundet")
    if problems:
        return rows, problems, warnings
    if not shared.relative:
        problems.append("site/track.js: CTA_HOME dækker ikke den rodrelative "
                        "form (`/`, `/da/`) — sidens egne hjemmelinks sender intet")
    if len(shared.family_hosts) != len(FAMILY_HOSTS):
        missing = sorted(set(FAMILY_HOSTS) - shared.family_hosts)
        problems.append(f"site/track.js: CTA_HOSTS mangler {missing} — en "
                        "rodrelative hjemmelink på det domæne sender intet")

    for dom, page in pages:
        try:
            text = page.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for href in RE_HREF.findall(text):
            host, path = _split_href(href)
            if host is None:
                continue
            kind = _classify(host, path)
            if kind == "other":
                continue
            target = host if host != "own" else dom
            key = f"{target}{_norm(path)}"
            row = rows.setdefault(key, {"in": 0, "counted": 0, "kind": kind})
            row["in"] += 1
            if shared.event_for(href, dom):
                row["counted"] += 1
            elif key not in EXEMPT:
                problems.append(
                    f"{page.relative_to(root)}: `href=\"{href}\"` peger på "
                    f"{key} ({kind}) men sender ingen cta-begivenhed")

    for key, row in rows.items():
        row["missing"] = row["in"] - row["counted"]
    return rows, problems, warnings


def _norm(path: str) -> str:
    clean = path.split("#")[0].split("?")[0]
    if clean.endswith(".html"):
        clean = clean[:-5]
    if clean in ("", "/"):
        return "/"
    return clean if clean.endswith("/") else clean + "/"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


# --------------------------------------------------------------------------
# Selftest. Den skal fange de fejl, der gjorde *denne* port tom: en læser der
# ikke kan læse `track.js`, og en måling der kun tæller det den selv vil se.
# --------------------------------------------------------------------------
FOUR = r"mahope\.tools|cleancopy\.tools|deskuptime\.com|bugbottle\.dev"
GOOD_HOME = (r"  var CTA_HOME = /^(?:https?:\/\/(" + FOUR + r")(?:\/da)?\/?"
             r"|\/(?:da\/)?\/?)(?:#.*)?$/;\n")
GOOD_TRACK = (
    r"  var CTA_PATHS = /^(?:https?:\/\/(?:mahope\.tools|cleancopy\.tools))?\/(?:da\/)?"
    r"(scan|free-tools)(\.html)?\/?(#.*)?$/;" "\n"
    + GOOD_HOME
    + r"  var CTA_HOSTS = /^(" + FOUR + r")$/;" "\n"
    + r"  var payload = JSON.stringify({ path: p, event: 'cta-' + name });" "\n"
)
# Uden den tredje literal sender `href="/"` intet, fordi lytteren så ikke ved
# hvilket domæne siden ligger på. Det var den rigtige fejl 28/9.
NO_HOSTS_TRACK = GOOD_TRACK.replace(
    r"  var CTA_HOSTS = /^(" + FOUR + r")$/;" "\n", "")
# Uden tolerancen for den manglende slutstreg sender de 2184 `https://host`
# links intet — samme fejlform, anden halvdel. Den rodrelative gren er bevaret
# med vilje, så mutationen rammer præcis den linje den påstår at ramme.
NO_SLASH_TRACK = GOOD_TRACK.replace(
    GOOD_HOME,
    r"  var CTA_HOME = /^(?:https?:\/\/(" + FOUR + r")\/(?:da\/)?"
    r"|\/(?:da\/)?\/?)(?:#.*)?$/;" "\n")
# Fjerner en af de to hovedliteraler: lytteren holder op med at sende.
NO_HOME_TRACK = GOOD_TRACK.replace(GOOD_HOME, "")


def _expected(source: str, href: str, own: str = "mahope.tools") -> str | None:
    return Shared(source).event_for(href, own)


def self_test() -> int:
    fails: list[str] = []

    def want(cond: bool, msg: str) -> None:
        if not cond:
            fails.append(msg)

    # 1. Positiv kontrol: læseren læser virkelig de tre literals. Uden den ville
    #    en port, der ikke kan læse `track.js`, være grøn uden at have set noget.
    good = Shared(GOOD_TRACK)
    want(good.sends and good.paths is not None and good.home is not None
         and good.hosts is not None,
         "selftest: GOOD_TRACK blev ikke læst — alle tre literals skal findes")
    want(good.relative, "selftest: CTA_HOME i GOOD_TRACK dækker ikke `/`")

    # 2. De former bygget faktisk producerer. Målt 28/9 i `dist/`.
    cases_pos = [
        ("https://cleancopy.tools", "cta-cleancopy"),
        ("https://cleancopy.tools/", "cta-cleancopy"),
        ("https://cleancopy.tools/da/", "cta-cleancopy"),
        ("https://deskuptime.com/da/#top", "cta-deskuptime"),
        ("https://mahope.tools", "cta-mahope"),
        ("/", "cta-mahope"),
        ("/da/", "cta-mahope"),
        ("/#pris", "cta-mahope"),
        ("https://mahope.tools/scan", "cta-scan"),
        ("https://cleancopy.tools/da/free-tools#top", "cta-free-tools"),
        ("/free-tools", "cta-free-tools"),
    ]
    for href, event in cases_pos:
        got = _expected(GOOD_TRACK, href)
        want(got == event, f"selftest: `{href}` burde sende {event}, sendte {got}")

    # 3. Negativ kontrol. `/blog/*`, `/support` og `#anker` er ikke en
    #    hjemmeside, og en tredjeparts-URL der ligner familiens er ikke en af
    #    vores. Begge dele skal sende intet — ellers tæller porten klik der
    #    ikke er salg.
    cases_neg = [
        "https://deskuptime.com.evil.tld/",
        "https://deskuptime.com.evil.tld/scan",
        "https://example.com/scan",
        "//evil.com/",
        "#pricing",
        "/blog/xyz",
        "/support",
        "/api/track",
        "",
        "/activate/",
        "https://mahope.tools/blog/xyz",
    ]
    for href in cases_neg:
        got = _expected(GOOD_TRACK, href)
        want(got is None, f"selftest: `{href}` må ikke sende noget, sendte {got}")

    # 4. De tre mutationer, der hver især gør porten rød på den rigtige kode.
    want(_expected(NO_HOSTS_TRACK, "/") is None,
         "selftest: uden CTA_HOSTS skal `/` sende intet (mutationen virker ikke)")
    want(_expected(NO_SLASH_TRACK, "https://cleancopy.tools") is None,
         "selftest: uden slutstreg-tolerancen skal `https://cleancopy.tools` "
         "sende intet (mutationen virker ikke)")
    want(_expected(NO_HOME_TRACK, "https://cleancopy.tools") is None
         and _expected(NO_HOME_TRACK, "/scan") == "cta-scan",
         "selftest: uden CTA_HOME skal hjemmelink sende intet mens "
         "`/scan` stadig tælles (mutationen virker ikke)")

    # 5. Mutationen må kun slå *én* ting ihvert, ellers beviser den intet.
    want(_expected(NO_HOSTS_TRACK, "https://cleancopy.tools") == "cta-cleancopy",
         "selftest: mutationen må ikke tage de absolutte links med")
    want(_expected(NO_SLASH_TRACK, "/") == "cta-mahope",
         "selftest: mutationen må ikke tage den rodrelative form med")

    # 6. Forventningen er uafhængig af track.js. Hvis `REQUIRED_SLUGS` blev
    #    læst ud af `CTA_PATHS`, ville porten være grøn præcis når den skal
    #    være rød, så den må heller ikke *indeholde* navne den ikke tæller.
    want("scan" in REQUIRED_SLUGS and "free-tools" in REQUIRED_SLUGS,
         "selftest: REQUIRED_SLUGS skal rumme de to navne porten adskiller på")
    want(not (REQUIRED_SLUGS & {"blog", "support", "books", "activate", "api"}),
         "selftest: chrome og indhold hører ikke i REQUIRED_SLUGS — de er "
         "bevidst ikke målt, se EXEMPT")

    # 7. Den virkelige kode og det virkelige dist skal være grøn, *og* have
    #    målt noget. En grøn port der tæller nul er den fejl, porten er skrevet
    #    imod, så kravet er begge dele.
    if (ROOT / "dist").is_dir() and any((ROOT / "dist").iterdir()):
        real = _read(ROOT / "site" / "track.js")
        shared = Shared(real)
        want(bool(shared.sends) and shared.paths is not None
             and shared.home is not None and shared.hosts is not None,
             "selftest: den rigtige site/track.js har ikke alle tre literals")
        want(len(shared.family_hosts) == len(FAMILY_HOSTS),
             "selftest: den rigtige site/track.js kender ikke alle fire domæner")
        rows, problems, warnings = measure(ROOT)
        want(not problems,
             "selftest: den rigtige kode + det rigtige dist skal være grøn, "
             f"men: {problems[:3]}")
        counted = sum(r["counted"] for r in rows.values())
        inbound = sum(r["in"] for r in rows.values())
        want(counted > 0 and counted == inbound,
             f"selftest: porten skal tælle noget ({counted}/{inbound})")
    else:
        print("selftest: intet dist/ — springer den rigtige-kode-kontrol over")

    for f in fails:
        print(f"  {f}", file=sys.stderr)
    if fails:
        print(f"check_cta_coverage_dist: selftest RØD — {len(fails)} krav "
              f"overholdt ikke", file=sys.stderr)
        return 1
    print("check_cta_coverage_dist: selftest grøn (7 kontrolgrupper)")
    return 0


def _print_report(rows: dict) -> None:
    total_in = sum(r["in"] for r in rows.values())
    total_ok = sum(r["counted"] for r in rows.values())
    print(f"link-instanser til et familieværktøj eller en forside: {total_in}")
    print(f"  heraf sender en cta-begivenhed:                     {total_ok}")
    print(f"  heraf sender intet:                                {total_in - total_ok}")
    print("\n rute                                          ind    talt   intet")
    for key in sorted(rows, key=lambda k: (-rows[k]["missing"], -rows[k]["in"])):
        r = rows[key]
        flag = "  <-- intet" if r["missing"] else ""
        print(f"  {key:44s} {r['in']:5d} {r['counted']:6d} {r['missing']:6d}{flag}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", action="store_true",
                        help="print hver rute med ind/talt/intet")
    parser.add_argument("--self-test", action="store_true",
                        help="kør portens egen selftest")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    rows, problems, warnings = measure(ROOT)
    for w in warnings:
        print(f"  advarsel: {w}", file=sys.stderr)
    if args.report and rows:
        _print_report(rows)
    for p in problems:
        print(f"  {p}", file=sys.stderr)
    if problems:
        # Når lytteren ikke kan læses, er `problems` lister af *manglende
        # literaler*, ikke af links — at skrive "N links" for dem ville være et
        # tal uden grund, altså præcis den fejlform porten er skrevet imod.
        blind = [p for p in problems if p.startswith("site/track.js:")]
        if blind:
            print(f"\ncheck_cta_coverage_dist: RØD — track.js er ikke læst, så "
                  f"målingen dømmer intet ({len(blind)} problemer i lytteren)",
                  file=sys.stderr)
            return 1
        unmeasured = sum(r.get("missing", 0) for r in rows.values())
        print(f"\ncheck_cta_coverage_dist: RØD — {len(problems)} links til et "
              f"familieværktøj eller en forside sender ingen cta-begivenhed"
              + (f" ({unmeasured} link-instanser)" if unmeasured else ""),
              file=sys.stderr)
        return 1
    total_in = sum(r["in"] for r in rows.values())
    print(f"check_cta_coverage_dist: GRØN — {len(rows)} ruter, "
          f"{total_in} link-instanser, alle målbare")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
