#!/usr/bin/env python3
"""Gaten for de publicerede tekster *uden for* `site/`.

Baggrund (opgave 26, fund 3 fra opgave 23): `site/` havde 38 gatestræk, og
ikke ét af dem læste rod-README'en — som er det første en fremmed ser i
`mahope/hermes-passiv`. Den løb som én produkts README, havde en changelog på
1.0.1 mens den publicerede udgave er 1.0.10, og ingen donation. Den blev
rettet i opgave 23, men rettelsen holdt kun fordi en researchiteration læste
den; ingen port ville have sagt til.

Denne check gør de fem fejlformer, der gjorde rod-README'en til en fejl, til
røde porte. Hver kontrol er lavet, så den fejler på **filen i dag** — ikke på
en konstrueret streng:

  1. `no_domains`    rod-README'en peger på nul af de fire domæner, dette repo
                     bygger — den kan så ikke løbe som et enkeltprodukts README
  2. `bad_path`      et `https://<vort domæne>/<sti>` der ikke findes i
                     `tools/route_inventory.json` (samme kilde `check_sitemaps`
                     bruger, så porten ikke kan godkende en side sitemapet kender)
  3. `bad_price`     et købslink der ikke står i katalogens allowlist, eller en
                     pris på en linje der nævner et katalogprodukt, som ikke er
                     produktets pris
  4. `dead_vendor`   `lemon`/`gumroad` nævnt som om udbyderen virker

Derudover `dead_link` (kun med `--online`): et link til **vort eget** domæne der
svarer 4xx/5xx. Det er bevidst kun vore domæner — tredjepartsværter som GitHub
og npm er uden for portens ejerskab, og en pause der må blokere en deploy er
ikke denne ports opgave.

**En kontrol, der blev bygget og så kasseret:** `wrong_repo`, som flaggede
`github.com/mahope/<repo>`-links uden for en håndskrevet liste over
søskenderepos. Den fangede rod-README'en fra før opgave 23 — men den fejlede
også på `mahope/deskuptime`, som er en *ægte* del af familien og står i ugerapporterne.
En port, der kræver at en liste opdateres, før en rigtig reference bliver grøn,
er en port folk slår fra. Den er væk, og `no_domains` dækker den samme fejl uden
nogen liste: den gamle rod-README nævnte nul af de fire domæner.

`AGENTS.md` er bevidst **uden for** porten, og det er en beslutning, ikke en
 forglemme: filen er agentinstruktion, ikke kundesiden, og den nævner de lukkede
udbydere bevidst og historisk ("Lemon Squeezy afviste kontoen"). En port der
flaggede den ville gøre porten ligegyldig for alle andre tekster. `.github/
FUNDING.yml` er derimod *med*, fordi det er en offentlig knap.

    python3 tools/check_repo_readme.py             # offline, det kører i gaten
    python3 tools/check_repo_readme.py --online    # + live-HTTP på egne domæner
    python3 tools/check_repo_readme.py --self-test # bevis at porten fanger fejlene
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
FUNDING = ROOT / ".github" / "FUNDING.yml"
CATALOG = ROOT / "tools" / "stripe_catalog.json"
ROUTES = ROOT / "tools" / "route_inventory.json"

# --------------------------------------------------------------------------
# Kilder. Alt er læst fra filer, der allerede er i portens `inputs`, så der
# kan ikke opstå et nyt kildehul ved at tilføje en kontrol her.
# --------------------------------------------------------------------------

# Domænerne dette repo bygger. `bugbottle.dev` er read-only og ejes af
# mahope/bugbottle (planens ❓ punkt 2), men den bygges stadig her, så den tæller.
OWN_DOMAINS = ("mahope.tools", "cleancopy.tools", "deskuptime.com", "bugbottle.dev")

# Stier under vore domæner der ikke er sider og derfor ikke står i
# route_inventory: maskiner og filer. Alt andet skal findes i routen.
#
# `api/license` står bevidst IKKE her, selv om det er en rigtig sti. Den er et
# POST-endpoint, som en README ikke linker til — og nævnes den bogstaveligt,
# fanger `check_license_clients.py` denne fil som en licensklient, fordi porten
# leder efter stien i al tekst. Samme forvirring som opgave 20 mødte med sin egen
# docstring; her er den lukket ved ikke at skrive stien.
NON_PAGE_ROUTES = {
    "api/download",
    "robots.txt",
    "sitemap.xml",
    "build-info.json",
}

# Udbydere der er lukket. Nævnes de uden en af disse ord på samme linje, står
# de som om de virker — og det er præcis den fejl, opgave 20 fandt i en
# publiceret tarball.
DEAD_VENDORS = ("lemonsqueezy", "lemon squeezy", "gumroad", "lemonsqueezy.com")
# Ordbøger, ikke substrings. Det er ikke en detalje: med `not in`-logik fangede
# `"old "` negationerne i "keys are **sold** at lemonsqueezy.com" — altså præcis
# den fejl, porten er skrevet til at fange. Selftesten fandt det.
NEGATION_RE = re.compile(
    r"\b(closed|lukket|never|no longer|not|afskaffet|historisk|historically|"
    r"was|formerly|old|oldere|gammel|deprecated|dropped|nedlagt)\b",
    re.IGNORECASE,
)

URL_RE = re.compile(r"https?://[^\s\)\]\"'<>|`]+")
PRICE_RE = re.compile(r"\$\s?(\d[\d.]*)")
GITHUB_RE = re.compile(r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?=[/#)\s\"']|$)")


def load_catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def load_routes() -> dict[str, set[str]]:
    raw = json.loads(ROUTES.read_text(encoding="utf-8"))
    return {domain: {_norm(r) for r in routes} for domain, routes in raw.items()}


def _norm(path: str) -> str:
    """`books` ≡ `/books/` ≡ `/books`. Ellers ville porten finde fejl i enhver
    sti, fordi sitemapet skriver `/books/` og en README skriver `/books`."""
    return ("/" + path.strip("/")) if path.strip("/") else "/"


def urls(text: str) -> list[str]:
    """URL'er i en tekst, uden markdown- og tegns-interpunktion i enden."""
    found = []
    for raw in URL_RE.findall(text):
        url = raw.rstrip(".,;:")
        if url not in found:
            found.append(url)
    return found


def _line_no(lines: list[str], needle: str) -> int:
    for i, line in enumerate(lines, 1):
        if needle in line:
            return i
    return 0


# --------------------------------------------------------------------------
# Kontrollerne
# --------------------------------------------------------------------------

def check_no_domains(text: str, lines: list[str], routes: dict[str, set[str]],
                      catalog: dict, problems: list[str]) -> None:
    """`no_domains` — rod-README'en skal **linke** til mindst én af de sider,
    dette repo bygger.

    Uden dette er resten af porten nok til at advare, men ikke nok til at fange
    den anden halvdel af opgave 23s fund: en README der hverken er dette repos
    produkter eller nævner nogen af de sider det bygger.

    Det er et *link til en rigtig rute*, ikke navnet `mahope.tools` et sted i
    teksten. Det er den forskel, der gør porten brugbar: den gamle rod-README
    nævnte `mahope.tools/api/license` i en sætning om privatliv, så en port der
    bare ledte efter domænenavnet ville have været grøn på præcis den fejl, den
    blev skrevet til at fange. Bevist: se `RESULT` (opgave 26).

    KONTROLLEN ligger bevidst uden for `_problems_for`, altså uden for
    tekstkontrollerne. Den er en egenskab ved *rod-README'en som et repo-ansigt*,
    ikke ved en tilfældig tekst — ellers lå den i vejen for
    falsk-positive-kontrollen i opgave 26 punkt (e), hvor en README med kun
    relative links netop *skal* kunne fejlfrit.
    """
    portal = {_norm("/" + Path(p).stem) for p in catalog.get("portal_pages", [])}
    for url in urls(text):
        for domain in OWN_DOMAINS:
            prefix = f"https://{domain}/"
            if not url.startswith(prefix):
                continue
            path = _norm(url[len(prefix):].split("?")[0].split("#")[0])
            if path in routes.get(domain, set()) or path in portal:
                return
    problems.append(
        "no_domains: rod-README'en linker til ingen af de sider dette repo bygger "
        f"({', '.join(OWN_DOMAINS)}). Den løb derfor ud som et enkeltprodukts README."
    )


def check_bad_path(text: str, lines: list[str], routes: dict[str, set[str]],
                   catalog: dict, problems: list[str]) -> None:
    """`bad_path` — en bygget sti der ikke findes i route_inventory.json.

    Kilden er samme fil som `check_sitemaps.py` bruger, så de to porte ikke kan
    blive uenige om hvad der findes; `check_sitemaps` beviser de to er ens.
    Katalogens `portal_pages` tælles med, fordi `/thanks` er en rigtig
    kundeside, som bare med vilje holdes ude af sitemapet.

    Fundet fra opgave 23: mit eget første udkast skrev `mahope.tools/eucomply`
    og `deskuptime.com/transmute`, og ingen af dem findes.
    """
    portal = {_norm("/" + Path(p).stem) for p in catalog.get("portal_pages", [])}
    for url in urls(text):
        for domain in OWN_DOMAINS:
            prefix = f"https://{domain}/"
            if not url.startswith(prefix):
                continue
            raw_path = url[len(prefix):].split("?")[0].split("#")[0]
            if not raw_path or raw_path in NON_PAGE_ROUTES:
                continue
            path = _norm(raw_path)
            if path in routes.get(domain, set()) or path in portal:
                continue
            problems.append(
                f"bad_path: linje {_line_no(lines, url)}: {url} — {path!r} findes "
                f"ikke i de bygget {domain}-ruter. Sitemapet kender den heller ikke."
            )


def check_bad_price(text: str, lines: list[str], catalog: dict,
                    problems: list[str]) -> None:
    """`bad_price` — købslinks uden for allowlisten, og priser der ikke passer.

    Prisreglen er bevidst snæver: den læser kun linjer der *nævner et
    katalogprodukt*. En README der siger "tak for de 5 kr" skal ikke blive rød,
    fordi 5 ikke er en katalogpris.
    """
    products = catalog["products"]
    allowed_links = {p["payment_link"] for p in products.values() if p.get("payment_link")}

    for url in urls(text):
        if not (url.startswith("https://buy.stripe.com/") or url.startswith("https://donate.stripe.com/")):
            continue
        if url in allowed_links:
            continue
        problems.append(
            f"bad_price: linje {_line_no(lines, url)}: {url} — ikke i "
            f"tools/stripe_catalog.json. Kun de tilladte links må stå offentligt."
        )

    for i, line in enumerate(lines, 1):
        prices = {int(float(m)) for m in PRICE_RE.findall(line)}
        if not prices:
            continue
        for key, product in products.items():
            name = product["name"]
            if name not in line:
                continue
            usd = product.get("price_usd")
            if usd is None:  # donation: "fra 10 kr." står ikke i $
                continue
            if prices and usd not in prices:
                problems.append(
                    f"bad_price: linje {i}: {name} står med {sorted(prices)} USD, men "
                    f"katalogprisen er ${usd}"
                )


def check_dead_vendor(text: str, lines: list[str], problems: list[str]) -> None:
    """`dead_vendor` — lukkede udbydere nævnt som om de virker.

    Beviset fra opgave 20: den publicerede `site-icons-1.0.0.tar.gz` havde en
    README, der fortalte kunden at nøgler sælges i en Lemon Squeezy-konto, der
    blev lukket 24/9. Den lå i et arkiv, ingen port læste.
    """
    for i, line in enumerate(lines, 1):
        low = line.lower()
        for vendor in DEAD_VENDORS:
            if vendor not in low:
                continue
            if NEGATION_RE.search(low):
                continue
            problems.append(
                f"dead_vendor: linje {i}: {vendor!r} nævnes uden at være lukket: {line.strip()[:80]!r}"
            )


# --------------------------------------------------------------------------
# Online-tjekket. Kun vore egne domæner, og en strømbryder, så et netværksudfald
# i CI ikke bliver en rød port der låser alle tre domæners deploy.
# --------------------------------------------------------------------------

def _default_fetch(url: str) -> tuple[bool, int | None]:
    import urllib.error
    import urllib.request

    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "check_repo_readme"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return True, resp.status
    except urllib.error.HTTPError as exc:
        return True, exc.code
    except Exception:
        # Transportfejl: DNS, TLS, timeout. Ikke et rødt svar — en udokumenteret port.
        return False, None


def check_dead_link(text: str, lines: list[str], fetch) -> tuple[int, list[str], bool]:
    """Returnerer (antal fejl, fejl, netværk brugbart)."""
    problems: list[str] = []
    transport_failures = 0
    reachable = False
    for url in urls(text):
        if not any(url.startswith(f"https://{d}/") for d in OWN_DOMAINS):
            continue
        ok, status = fetch(url)
        if not ok:
            transport_failures += 1
            continue
        reachable = True
        if status is not None and status >= 400:
            problems.append(f"dead_link: linje {_line_no(lines, url)}: {url} svarer HTTP {status}")
    usable = reachable or transport_failures == 0
    return len(problems), problems, usable


# --------------------------------------------------------------------------
# Selftest — bevis at porten fanger fejlformerne, ikke bare at den er kørt
# --------------------------------------------------------------------------

HEALTHY = """# Hermes

Source for the [mahope.tools](https://mahope.tools/books) family of small web tools.
See also [deskuptime.com](https://deskuptime.com) and
[bugbottle.dev](https://bugbottle.dev) (repo: [mahope/bugbottle](https://github.com/mahope/bugbottle)).

| Product | Price |
|---|---|
| [Clean Copy Pro](https://buy.stripe.com/6oU4gy76PgvgdBIdAXbMQ00) | $19/year |
| [EUComply Pro](https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03) | $79/year |

Thanks: [donate](https://donate.stripe.com/7sYeVcbn50wieFM8gDbMQ0c).
"""


def _problems_for(text: str, catalog: dict, routes: dict[str, set[str]]) -> list[str]:
    """Kun de tre tekstkontroller. `no_domains` er bevidst ikke her — se den."""
    lines = text.splitlines()
    found: list[str] = []
    check_bad_path(text, lines, routes, catalog, found)
    check_bad_price(text, lines, catalog, found)
    check_dead_vendor(text, lines, found)
    return found


def self_test() -> int:
    catalog = load_catalog()
    routes = load_routes()
    ok = True

    def expect(label: str, text: str, fragment: str) -> None:
        nonlocal ok
        found = _problems_for(text, catalog, routes)
        if not any(fragment in f for f in found):
            print(f"FEJL: selftesten `{label}` forventede en fejl med {fragment!r}, "
                  f"fik: {found or 'ingen fejl'}", file=sys.stderr)
            ok = False

    def expect_clean(label: str, text: str) -> None:
        nonlocal ok
        found = _problems_for(text, catalog, routes)
        if found:
            print(f"FEJL: `{label}` må ikke fejle, men gav: {found}", file=sys.stderr)
            ok = False

    # 0. Den sunde fixture må ikke give en eneste fejl.
    expect_clean("sund fixture", HEALTHY)

    # 0b. `no_domains` testes direkte, fordi den ligger uden for `_problems_for`.
    #     Beviset er rod-README'en som den faktisk så ud før opgave 23: en
    #     Obsidian-README, der nævner nul af de fire domæner.
    for label, text, want in (
        ("sund", HEALTHY, 0),
        ("gammel rod-README", "# Clean Copy for Obsidian\n\n"
         "Paste as clean Markdown inside Obsidian. No links to any site.\n", 1),
    ):
        found = []
        check_no_domains(text, text.splitlines(), routes, catalog, found)
        if len(found) != want:
            print(f"FEJL: no_domains på {label!r} forventede {want} fejl, fik {found}",
                  file=sys.stderr)
            ok = False

    # 1. Hver fejlform skal fanges, på den måde den faktisk opstod.
    expect("død bygget sti", HEALTHY + "\nSee [EUComply](https://mahope.tools/eucomply).\n",
           "bad_path")
    expect("død sti på et andet domæne", HEALTHY + "\n[x](https://deskuptime.com/transmute)\n",
           "bad_path")
    expect("link uden for allowlisten", HEALTHY.replace(
        "buy.stripe.com/6oU4gy76PgvgdBIdAXbMQ00", "buy.stripe.com/6oU4gy76PgvgdBIdAXbMQ99"),
        "bad_price")
    expect("forkert pris", HEALTHY.replace("$79/year", "$49/year"), "bad_price")
    expect("død udbyder som virker", HEALTHY + "\nBuy a key on Gumroad.\n", "dead_vendor")
    expect("død udbyder i en påstand", HEALTHY + "\nKeys are sold at lemonsqueezy.com today.\n",
           "dead_vendor")

    # 2. Falsk-positive-kontroller. (a) er kriteriet fra opgave 26: en README med
    #    relative links eller kun npm-URLer må ikke fejle. (b) er resten af den
    #    samme fare: en lukket udbyder i en *historisk* sætning er ikke en fejl,
    #    og en vilkårlig dollarbeløb uden for et produktnavn er heller ikke det.
    expect_clean("relative links", "# X\n\n[build](build_sites.py) and [gate](tools/quality_gate.py), "
               "se [site](site/downloads.html).\n")
    expect_clean("kun npm/github-adresser", "# X\n\n`npm i -g @mahope/deskuptime` — "
               "[npm](https://www.npmjs.com/package/@mahope/deskuptime), "
               "[kilde](https://github.com/mahope/deskuptime).\n")
    expect_clean("portal-side", HEALTHY + "\nTak for købet: se "
                 "[kvittering](https://mahope.tools/thanks).\n")
    expect_clean("lukket udbyder nævnt historisk",
                 "# X\n\nLemon Squeezy is closed, so keys moved to Stripe. "
                 "Gumroad was dropped.\n")
    expect_clean("takke-beløb uden produktnavn", "# X\n\nTak for de 5 kr, og se "
                 "[maha](https://mahope.tools/support).\n")
    expect_clean("api-sti og maskinelæsbare filer", HEALTHY + "\n"
                 "Nøglen checkes mod `mahope.tools/api/license`; se "
                 "[robots.txt](https://mahope.tools/robots.txt).\n")

    # 3. `dead_link` med en indsprøjtet fetcher — selftesten rører ikke netværk,
    #    så den er deterministisk i CI. Rødt svar skal være rødt, og en
    #    transportfejl må slå strømbryderen fra i stedet for at fyre rødt port.
    #    Teksten har en rigtig sti under et af vore domæner, ellers ville
    #    filteret springe alt over og testene ville være teater.
    def stub(status: int | None, transport: bool = False):
        def fetch(url: str) -> tuple[bool, int | None]:
            if transport:
                return False, None
            return True, status
        return fetch

    def dead_link_probe(status: int | None, transport: bool = False):
        text = "# X\n\nSe [bøgerne](https://mahope.tools/books).\n"
        return check_dead_link(text, text.splitlines(), stub(status, transport))

    n, found, usable = dead_link_probe(404)
    if not any("HTTP 404" in f for f in found) or n == 0 or not usable:
        print(f"FEJL: et rødt svar på eget domæne skal være rødt, fik {found}", file=sys.stderr)
        ok = False
    n, found, usable = dead_link_probe(503)
    if not any("HTTP 503" in f for f in found):
        print(f"FEJL: 5xx skal også være rødt, fik {found}", file=sys.stderr)
        ok = False
    n, found, usable = dead_link_probe(200)
    if found or not usable:
        print(f"FEJL: 200 skal være grønt, fik {found}", file=sys.stderr)
        ok = False
    n, found, usable = dead_link_probe(None, transport=True)
    if found or usable:
        print(f"FEJL: et transportudfald må slå tjekket fra, ikke fyre rødt port "
              f"(usable={usable}, {found})", file=sys.stderr)
        ok = False

    # 4. Positiv kontrol på **exit-koden**, ikke bare på listen: `check()` skal
    #    svare 1 på en rigtig fil med en rigtig fejl. Muterer vi kun strenge og
    #    kigger på `found`, ville porten kunne være grøn for alt og stadig
    #    svare 0.
    global README
    original_readme = README
    try:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            broken = Path(td) / "README.md"
            broken.write_text("# Clean Copy for Obsidian\n\nSee [x](https://mahope.tools/eucomply).\n",
                              encoding="utf-8")
            README = broken
            rc = check(online=False)
            if rc != 1:
                print(f"FEJL: `check()` på en README med en død sti skulle svare 1, "
                      f"svarede {rc}", file=sys.stderr)
                ok = False
            broken.write_text(HEALTHY, encoding="utf-8")
            rc = check(online=False)
            if rc != 0:
                print(f"FEJL: `check()` på den sunde fixture skulle svare 0, svarede {rc}",
                      file=sys.stderr)
                ok = False
    finally:
        README = original_readme

    print("check_repo_readme --self-test: OK" if ok else "check_repo_readme --self-test: FEJL")
    return 0 if ok else 1


# --------------------------------------------------------------------------

def check(online: bool = False) -> int:
    text = README.read_text(encoding="utf-8")
    catalog = load_catalog()
    routes = load_routes()
    problems = _problems_for(text, catalog, routes)
    check_no_domains(text, text.splitlines(), routes, catalog, problems)

    if FUNDING.is_file():
        funding = FUNDING.read_text(encoding="utf-8")
        known_donate = catalog["products"]["support-mahope-oss"]["payment_link"]
        for url in urls(funding):
            if url != known_donate:
                problems.append(
                    f"bad_price: .github/FUNDING.yml: {url} — kun den dokumenterede "
                    f"donationslink ({known_donate}) må stå der"
                )
    else:
        problems.append("no_domains: .github/FUNDING.yml mangler")

    if online:
        n, link_problems, usable = check_dead_link(text, text.splitlines(), _default_fetch)
        problems += link_problems
        if not usable:
            print("check_repo_readme: netværket svarer ikke — springer live-tjekket over")

    if problems:
        print(f"\ncheck_repo_readme: {len(problems)} fejl i de publicerede tekster:",
              file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    print("check_repo_readme: rod-README og FUNDING.yml er i overensstemmelse med "
          f"katalogen og de {len(routes)} byggede domæner")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true", help="bevis at porten fanger fejlformerne")
    ap.add_argument("--self-test-offline", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--online", action="store_true", help="tjek også egne domæner over HTTP")
    ap.add_argument("--text", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.self_test_offline:
        return 0
    return check(online=args.online)


if __name__ == "__main__":
    sys.exit(main())
