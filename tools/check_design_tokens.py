#!/usr/bin/env python3
"""Gate for at én side kun har ét designsystem, opgave 17 i `IMPLEMENTATION_PLAN.md`.

DeskUptime er det eneste domæne, der publicerer sider fra to forskellige
designsystemer. `/tools/` er skrevet her i repoet og bruger kun skallen, men de
to sider under `/bulk-url-checker/` og `/security-headers-checker/` kommer fra
`../auditedwp` og indlæser deres egen
`/assets/site.css` — et komplet skeln med sit eget farvepalet (en grøn) og sin
egen skrifttype (Inter). Deres eget `<style>`-blok og deres eget `site.js`
tegner resultater med de klassenavne, kun den fil kender, så filen *skal* rejse
med. Men de tokens den erklærer, må ikke: ellers får headeren, footeren og
knapperne fra denne repos skal (blå, IBM Plex) grønne knapper oveni.

Samme fejlform som opgave 10 og opgave 15: en tælling der så rigtig ud og
rettede ingenting. Her var den usynlig, fordi bygget *allerede* havde indsat
`/style.css` på de tre sider, så siden lignede næsten hinanden — kun de
farver, der blev arvet fra det andet system, stod tilbage.

Gaten fejler ved:

1. En bygget side indlæser et lokalt stylesheet ud over `/style.css`, og
   `site/style.css` erklærer ikke *alle* de custom properties, det indlæser på
   `:root` (eller under `data-theme="dark"`), i sideens egen produktregel.
   Uden erklæringen vinder det andet systems `:root` på grund af
   dokumentrækkefølgen, og siden får to farver.
2. `/style.css` kommer *før* det andet stylesheet i dokumentet. Bridgen har
   samme specificitet som det andet systems `:root`, så kun rækkefølgen
   afgør hvem der vinder — og den er ikke til at regne med uden en port.
3. Siden mangler `data-product` på `<html>`, så gaten ikke kan bevise hvilken
   identitet der skulle gælde.

Kun lokale stylesheets. `/style.css` selv er vores skal. Absolutte URL'er
(Google Fonts) springes over: de erklærer ingen custom properties, og hvilken
familie de indlæser, afgøres af `data-product`.

    python3 tools/check_design_tokens.py
    python3 tools/check_design_tokens.py --self-test

Springes over, når intet er bygget, i samme mønster som de øvrige dist-gates.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Vores skal. Alle dists får den, og den skal altid indlæses.
HOST_STYLESHEET = "/style.css"

# Regler hvis custom properties *er* designsystemets identitet. Alt andet
# (`.btn { … }`, `h1 span { … }`) er komponenter, der skal beholde sit udseende.
TOKEN_SELECTORS = (
    ":root",
    ":root[data-theme='dark']",
    ':root[data-theme="dark"]',
    "html[data-theme='dark']",
    'html[data-theme="dark"]',
)

RE_HTML_OPEN = re.compile(r"<html\b[^>]*>", re.IGNORECASE)
RE_DATA_PRODUCT = re.compile(r"""data-product\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
RE_STYLESHEET = re.compile(
    r"""<link\b[^>]*\brel\s*=\s*["']stylesheet["'][^>]*\bhref\s*=\s*["']([^"']+)["']""",
    re.IGNORECASE)
RE_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
# En regel = selector + klammeindhold. Deklarationer er fundet i *kroppen*, så
# flere på én linje tæller alle — en linjebaseret scanner så kun den første, og
# gaten erklærede så 15 tokens dækket da kun 12 var det.
RE_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
RE_DECL = re.compile(r"(--[A-Za-z0-9_-]+)\s*:\s*([^;}]+)")

# Elementer hvor skallen erklærer en default, så en strippet sidelinje altid
# efterlader noget synligt. Se `check_owned_selectors_exist`.
FORM_CONTROL_TAGS = {"button", "input", "select", "textarea"}


def _rules(css: str):
    """(selector-dele, krop) for hver regel, med kommentarer fjernet."""
    for match in RE_RULE.finditer(RE_COMMENT.sub("", css)):
        selector = match.group(1)
        # Ét niveau `@media … {` hænger stadig foran, hvis reglen ligger indeni.
        if "{" in selector:
            selector = selector.rsplit("{", 1)[1]
        parts = [p.strip() for p in selector.split(",") if p.strip()]
        if parts:
            yield parts, match.group(2)


def _properties(css: str, accept) -> dict[str, str]:
    found: dict[str, str] = {}
    for parts, body in _rules(css):
        if not accept(parts):
            continue
        for name, value in RE_DECL.findall(body):
            found[name] = " ".join(value.split())
    return found


def parse_token_properties(css: str) -> dict[str, str]:
    """Custom properties i `:root`-regler: designsystemets basistokens."""
    return _properties(css, lambda parts: all(p in TOKEN_SELECTORS for p in parts))


# Kun `:root`/`html` med attribut-kvalifikatorer (`[data-theme="dark"]`) er
# identitetsregler. `.rcard.pass .pill` er en komponent, ikke et token — de
# erklærer også custom properties, og de skal have lov til at gøre det.
# `data-product` er undtaget: den hører til `parse_product_properties`, og
# tæller den med her, så en bro til *et andet* produkt dækker alle — præcis
# den fejlform porten skal finde.
RE_ROOT_SCOPE = re.compile(r"^(html|:root)(\[(?!data-product)[^\]]+\])*$")


def _is_root_scope(parts: list[str]) -> bool:
    return all(RE_ROOT_SCOPE.match(p) for p in parts)


def parse_scoped_properties(css: str) -> dict[str, str]:
    """Custom properties i identitetsregler som `html[data-theme="dark"]`.

    Disse har højere specificitet end `:root`, så de skal dækkes *eksplicit* i
    vores egen mørk-regel eller produktregel — dokumentrækkefølgen redder dem
    ikke, fordi de ikke er på hverken side af den.
    """
    return _properties(css, lambda parts: not all(p in TOKEN_SELECTORS for p in parts)
                       and _is_root_scope(parts))


def parse_product_properties(css: str, product: str) -> dict[str, str]:
    """Alle custom properties, vores skal erklærer i sideens produktregel."""
    wanted = f'html[data-product="{product}"]'
    return _properties(css, lambda parts: wanted in parts)


def _local_path(href: str) -> str:
    return href.split("?", 1)[0].split("#", 1)[0]


def _html_files(dist: Path) -> list[Path]:
    return sorted(p for p in dist.rglob("*.html") if p.is_file())


def _find_sibling_css(root: Path) -> Path:
    return root / "site" / "style.css"


def check_one_page(page: Path, dist: Path, host_css: str) -> list[str]:
    html = page.read_text(encoding="utf-8", errors="replace")
    rel = page.relative_to(dist).as_posix()
    hrefs = [_local_path(h) for h in RE_STYLESHEET.findall(html)]

    others = [h for h in hrefs if h.startswith("/") and h != HOST_STYLESHEET]
    if not others:
        return []

    opened = RE_HTML_OPEN.search(html)
    if not opened:
        return [f"{rel}: indlæser {others[0]} men <html> mangler — sidekilden er ikke gyldig"]
    found = RE_DATA_PRODUCT.search(opened.group(0))
    if not found:
        return [f"{rel}: indlæser {others[0]} men <html> mangler data-product — "
                f"gaten kan ikke bevise hvilken identitet der gælder"]
    product = found.group(1)

    base = parse_token_properties(host_css)
    # Vores egen mørke identitetsregler dækker lige så vel som produktreglen:
    # de har samme specificitet som deres `html[data-theme="dark"]` og kommer
    # senere i dokumentet.
    ours = set(parse_product_properties(host_css, product)) | set(parse_scoped_properties(host_css))
    problems = []
    for href in others:
        css_path = dist / href.lstrip("/")
        if not css_path.is_file():
            # En lokal reference der ikke findes er `check_links.py`s job.
            continue
        foreign = css_path.read_text(encoding="utf-8", errors="replace")
        # `html[data-theme="dark"]` vinder over `:root` på specificitet, så
        # vores `:root` kan ikke dække den. Alt andet fra deres `:root` taber
        # til vores `:root` på dokumentrækkefølgen — fordi vi indlæses senest.
        base_only = set(parse_token_properties(foreign)) - set(base) - ours
        scoped = set(parse_scoped_properties(foreign)) - ours
        diverging = sorted(base_only | scoped)
        if diverging:
            where = ", ".join(diverging[:6]) + (f" … (+{len(diverging) - 6})" if len(diverging) > 6 else "")
            problems.append(
                f"{rel}: /assets/{css_path.name} erklærer {len(diverging)} token(s) som "
                f"hverken vores :root eller html[data-product=\"{product}\"] dækker "
                f"({where}) — de vinder, så siden får to designsystemer")
        if HOST_STYLESHEET not in hrefs:
            problems.append(f"{rel}: indlæser {href} men ikke {HOST_STYLESHEET}")
        elif hrefs.index(HOST_STYLESHEET) < hrefs.index(href):
            problems.append(
                f"{rel}: {HOST_STYLESHEET} indlæses FØR {href}, så det andet systems "
                f":root vinder på lige specificitet — bridgen virker ikke")
    return problems


def check_dist_has_one_design_system(root: Path) -> list[str]:
    dist = root / "dist"
    host_path = _find_sibling_css(root)
    if not dist.is_dir() or not host_path.is_file():
        return []
    domains = [d for d in sorted(dist.iterdir()) if d.is_dir() and (d / "index.html").is_file()]
    if not domains:
        return []
    host_css = host_path.read_text(encoding="utf-8", errors="replace")
    problems: list[str] = []
    for domain in domains:
        for page in _html_files(domain):
            problems += check_one_page(page, domain, host_css)
    return problems


def check_owned_selectors_exist(root: Path) -> list[str]:
    """Ingen formkontrol må være påstået ejet af designsystemet uden at være deklareret.

    `pagepass.OWNED_SELECTORS` er skallens kontrakt: en side må ikke selv style de
    klasser, fordi style.css ejer dem. Men kontrakten er en *påstand* — den
    efterprøves ikke, og da `.input-group button` stod på listen uden at være
    deklaret i style.css, fjernede `scrub_css()` sidens regel. Knappen faldt så
    tilbage på `button:not([class])`: hvid baggrund med mørk tekst, og 2,5:1 mod
    blå baggrund ved hover. Målt 1/10 på den publicerede
    `/compliance-site-check` — en synlig fejl på den mest besøgte scanner, som
    ingen port meldte.

    Kun **formkontroller** dømmes (`button`, `input`, `select`, `textarea`).
    De er den ene gruppe hvor tabet *altid* er synligt: skallen erklærer en
    default for hver af dem, så en strippet sidelinje efterlader et element med
    et udseende ingen har bedt om. For `.gen label` eller `pre.cmd code` er
    påstanden derimod ofte korrekt — skallen erklærer `.gen`, `label`,
    `pre.cmd` og `code` hver for sig, og det er ikke denne ports opgave at
    dømme om delene tilsammen giver det samme udseende. At dømme hele listen
    ville give en port, der rødmer på ti kodelinjer uden ét synligt brud, og
    så en port man lærer at ignorere.

    Kun basis-selectoren tælles, så `.input-group button:hover` ikke kræver en
    egen erklæring uden `:hover`.
    """
    sys.path.insert(0, str(root / "tools"))
    try:
        import pagepass  # noqa: E402
    except ImportError:
        return []

    style = root / "site" / "style.css"
    if not style.is_file():
        return []

    def base(selector: str) -> str:
        # Samme normalisering som `pagepass._norm_sel` — ellers er
        # `input[type="text"]` i style.css et andet navn end
        # `input[type=text]` på siden, og porten melder en fejl der ikke er der.
        s = re.sub(r"\s+", " ", re.sub(r"""["']""", "", selector.strip()))
        return re.sub(r":(?:hover|focus|focus-visible|active|disabled|not\(\[class\]\))", "", s).strip()

    declared = {base(sel) for group, _ in _rules(style.read_text(encoding="utf-8", errors="replace"))
                for sel in group}

    used: dict[str, set[str]] = {}
    for page in sorted((root / "site").rglob("*.html")):
        text = page.read_text(encoding="utf-8", errors="replace")
        for style_body in re.findall(r"<style[^>]*>(.*?)</style>", text, re.DOTALL | re.IGNORECASE):
            for group, _ in _rules(RE_COMMENT.sub("", style_body)):
                for sel in group:
                    name = base(pagepass._norm_sel(sel))
                    # Selectorens *sidste* del skal være formkontrollen:
                    # `.input-group button` og `button:not([class])` begge.
                    parts = name.split()
                    if parts and parts[-1] in FORM_CONTROL_TAGS and pagepass._owned(name):
                        used.setdefault(name, set()).add(str(page.relative_to(root / "site")))

    return [f"{sel} er på OWNED_SELECTORS-listen, men style.css erklærer den ikke — "
            f"brugt på {len(paths)} side(r), fx {sorted(paths)[0]}, så bygget "
            f"stripper reglen og knappen falder tilbage på skallens default"
            for sel, paths in sorted(used.items()) if sel not in declared]


def _owned_selectors_fixture(root: Path, *, drop: bool) -> None:
    """(site, site/style.css) med en side der styler `.input-group button`.

    `drop=False` efterlader style.css med den erklæring, siden kræver. `drop=True`
    fjerner den — mutationen der skal give en rød port.
    """
    (root / "site").mkdir(parents=True, exist_ok=True)
    (root / "site" / "style.css").write_text(
        ".btn { background: #4a3fc4; color: #fff; }\n"
        + ("" if drop else ".input-group button { background: #4a3fc4; color: #fff; }\n"),
        encoding="utf-8")
    (root / "site" / "værktøj.html").write_text(
        "<html lang=\"da\"><head><style>\n"
        ".input-group { display: flex; }\n"
        ".input-group button { background: #2563eb; color: #fff; }\n"
        "</style></head><body><div class=\"input-group\"><button>Tjek</button></div></body></html>\n",
        encoding="utf-8")


def _fixtures(root: Path, *, bridge: bool = True, order: bool = True,
              product: str = "deskuptime", bridge_product: str = "deskuptime") -> None:
    """Skriver et minimalt, sundt (dist, site/style.css) par."""
    dist = root / "dist" / "deskuptime.com"
    (dist / "assets").mkdir(parents=True, exist_ok=True)
    (root / "site").mkdir(parents=True, exist_ok=True)

    (dist / "assets" / "site.css").write_text(
        ":root {\n  --bg: #f6f7f4;\n  --panel: #ffffff;\n  --ink: #15201b;\n"
        "  --accent: #0b6e4f;\n  --w-page: 1200px;\n}\n", encoding="utf-8")
    (root / "site" / "style.css").write_text(
        ':root {\n  --color-bg: #ffffff;\n  --color-surface: #ffffff;\n'
        '  --color-text: #101010;\n  --color-accent: #2456d6;\n  --w-page: 1200px;\n}\n'
        f'html[data-product="{bridge_product}"] {{\n  --font: "IBM Plex Sans", sans-serif;\n'
        + ("  --bg: var(--color-bg);\n  --panel: var(--color-surface);\n"
           "  --ink: var(--color-text);\n  --accent: var(--color-accent);\n" if bridge else "")
        + "}\n", encoding="utf-8")

    head = f'<html lang="en" data-product="{product}">\n'
    if order:
        head += '<link rel="stylesheet" href="/assets/site.css">\n<link rel="stylesheet" href="/style.css">\n'
    else:
        head += '<link rel="stylesheet" href="/style.css">\n<link rel="stylesheet" href="/assets/site.css">\n'
    (dist / "index.html").write_text(head + "<body>x</body>\n", encoding="utf-8")


def self_test() -> int:
    """Bevis at gaten fanger hver fejlform, den siger at fange."""
    import tempfile

    scenarios: list[tuple[str, list[str]]] = []

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _fixtures(root)

        control = check_dist_has_one_design_system(root)
        if control:
            for problem in control:
                print(f"KONTROLFEJL: {problem}", file=sys.stderr)
            return 1

        # 1 — bridgen fjernes: det andet systems grønne vinder igen
        _fixtures(root, bridge=False)
        scenarios.append(("broen mellem designsystemerne er væk",
                          check_dist_has_one_design_system(root)))

        # 2 — /style.css flyttes foran det andet stylesheet
        _fixtures(root, order=False)
        scenarios.append(("/style.css indlæses før det andet stylesheet",
                          check_dist_has_one_design_system(root)))

        # 3 — siden taber sin data-product
        _fixtures(root)
        page = root / "dist" / "deskuptime.com" / "index.html"
        page.write_text(page.read_text(encoding="utf-8").replace(' data-product="deskuptime"', ""),
                        encoding="utf-8")
        scenarios.append(("siden kan ikke bevise sin identitet",
                          check_dist_has_one_design_system(root)))

        # 4 — en side der kun indlæser vores skal må ikke fejle
        _fixtures(root)
        dist = root / "dist" / "deskuptime.com"
        (dist / "ren.html").write_text(
            '<html lang="en" data-product="deskuptime">\n'
            '<link rel="stylesheet" href="/style.css">\n</html>\n', encoding="utf-8")
        no_false_positive = check_dist_has_one_design_system(root)
        if no_false_positive:
            for problem in no_false_positive:
                print(f"FALSK POSITIV: {problem}", file=sys.stderr)
            return 1

        # 5 — en extern font-udfyldning er ikke et designsystem
        _fixtures(root)
        (dist / "ren.html").write_text(
            '<html lang="en" data-product="deskuptime">\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter">\n'
            '<link rel="stylesheet" href="/style.css">\n</html>\n', encoding="utf-8")
        if check_dist_has_one_design_system(root):
            print("FALSK POSITIV: en ekstern font blev taget for et designsystem", file=sys.stderr)
            return 1

        # 6 — det andet system får en ny token, der ikke er dækket
        _fixtures(root)
        (dist / "assets" / "site.css").write_text(
            ":root {\n  --bg: #f6f7f4;\n  --accent: #0b6e4f;\n  --brand-neon: #ff00ff;\n}\n",
            encoding="utf-8")
        scenarios.append(("det andet designsystem får en udækket token",
                          check_dist_has_one_design_system(root)))

        # 7 — komponentregler i det andet system er ikke tokens
        _fixtures(root)
        (dist / "assets" / "site.css").write_text(
            ":root {\n  --bg: #f6f7f4;\n  --panel: #ffffff;\n  --ink: #15201b;\n"
            "  --accent: #0b6e4f;\n}\n.btn {\n  --btn-pad: 11px;\n}\n", encoding="utf-8")
        no_component_fp = check_dist_has_one_design_system(root)
        if no_component_fp:
            for problem in no_component_fp:
                print(f"FALSK POSITIV: komponentregel taget for token: {problem}", file=sys.stderr)
            return 1

        # 8 — et design-system på en side med en ANDEN produktregel må fejle,
        # fordi broen kun findes under deskuptime. Reglen må ikke være
        # "findes der en bro nogen steder".
        _fixtures(root, product="cleancopy", bridge_product="deskuptime")
        scenarios.append(("broen findes kun under et andet produkt",
                          check_dist_has_one_design_system(root)))

        # 9 — `pagepass.OWNED_SELECTORS` påstår at designsystemet ejer en
        # formkontrol, style.css erklærer den ikke. Det er fejlen der gjorde
        # «Check Site» hvid på den publicerede scanner.
        _owned_selectors_fixture(root, drop=True)
        scenarios.append(("en OWNED_SELECTOR uden erklæring i style.css",
                          check_owned_selectors_exist(root)))

        # 10 — samme sag uden fejlen må ikke rødme porten.
        _owned_selectors_fixture(root, drop=False)
        if check_owned_selectors_exist(root):
            print("FALSK POSITIV: en korrekt OWNED_SELECTOR blev meldt som fejl", file=sys.stderr)
            return 1

    failed = 0
    for name, problems in scenarios:
        if problems:
            print(f"OK   {name} -> {problems[0]}")
        else:
            print(f"FEJL mutationen blev ikke fanget: {name}", file=sys.stderr)
            failed += 1
    if not scenarios:
        print("FEJL: ingen scenarier", file=sys.stderr)
        return 1
    print(f"design-tokens selftest OK — {len(scenarios)} mutationer fanget, "
          f"positiv kontrol grøn, ingen falske positiver")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="bevis at gaten fanger hver fejlform, den siger at fange")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    problems = check_dist_has_one_design_system(ROOT) + check_owned_selectors_exist(ROOT)
    for problem in problems:
        print(f"FEJL: {problem}", file=sys.stderr)
    if problems:
        return 1
    if not (ROOT / "dist").is_dir():
        print("design-tokens OK — intet bygget, porten springes over")
        return 0
    print("design-tokens OK — ingen side indlæser et designsystem ud over /style.css "
          "uden at alle dets tokens er dækket af sideens produktregel")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
