#!/usr/bin/env python3
"""Port for at dømme, om en sides CSS overlever bygget — opgave 15.

Samme fejlform tre gange i træk: en tæller der så rigtig ud og rettede
ingenting. `RE_CLAIM` tæller 171 løfter og dømmer fire, `tool_paid_path_blind`
kan ikke se en tilbagefaldet rute, og `check_design_tokens` troede på
`style.css:128-136` som dækning af ni tokens, mens de lå i
`html[data-product="deskuptime"]` — altså kun på ét domæne. Konsekvensen var
hvid tekst på hvid knap på `/url-inspector` i otte dage, fordi ingen spurgte
om `--accent` overhovedet var *opløst* der.

Denne port stiller det spørgsmål direkte, på de byggede filer:

**1. Tabte regler.** En regel i `site/<side>.html` der ikke findes i
`dist/<domæne>/<side>.html` er kun en fejl når tre ting alle er sande: elementet
er stadig i dist-markup, skallens egen `style.css` erklærer ikke den klasse,
og bygget altså ikke har erstattet reglen. Uden den tredje betingelse ville
porten rødme på hver eneste `.btn`-regel, som `pagepass.OWNED_SELECTORS` med
rette fjerner — de *er* erstattet af skallen. Derfor måles der på de rigtige
filer, og derfor tælles `.input-wrap`-tabet fra 30/9 som en fejl: elementet er
i markup, og `style.css` siger intet om klassen.

**2. Uopløste tokens.** Ethvert `var(--x)` i en sides *dist*-CSS skal være
opløst for den sides `data-product`. Ikke "nævnt et sted i style.css" — det var
præcis den forkerte læsning, der lod fejlen stå. Erklæres `--accent` kun under
`html[data-product="deskuptime"]`, er den uopløst på `data-product="mahope"`.
Målingen er statisk og scope-bevidst: tokens under et produktscope tæller kun
for den side, hvis `data-product` matcher.

Begge dele springes over når intet er bygget, i samme mønster som de øvrige
dist-gates, så porten kan bruges på et delvis checkout uden at lyve om grønt.

    python3 tools/check_built_css.py
    python3 tools/check_built_css.py --self-test

Selvtesten muterer de rigtige filer — `pagepass.py` og `style.css` — og forlanger
at porten bliver rød med filnavn på hver mutation. Den må derfor ikke finde sin
udgangstilfælde ved at navngive en fil i `site/` (opgave 10): den læser det
målte tal og slår på det.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DIST = ROOT / "dist"

# Vores skal. Den erklærer klasser og tokens for alle dists.
STYLE_CSS = SITE / "style.css"

RE_COMMENT_CSS = re.compile(r"/\*.*?\*/", re.DOTALL)
RE_STYLE_BLOCK = re.compile(r"<style\b[^>]*>(.*?)</style>", re.S | re.I)
RE_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
RE_DECL = re.compile(r"(--[A-Za-z0-9_-]+)\s*:")
# En `var(--x)` *uden* fallback er en fejl, når `--x` ingen regel for siden
# erklærer. Med fallback (`var(--x, #94a3b8)`) er den opløst uanset hvad — så
# porten skal ikke tælle den, ellers rødmer den på sider der er korrekte.
# Første måling fandt 9 fund hvoraf 5 var af denne art.
RE_VAR_USE = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)\s*([,)])")
RE_CLASS_ATTR = re.compile(r"""class\s*=\s*["']([^"']*)["']""", re.I)
RE_DATA_PRODUCT = re.compile(r"""data-product\s*=\s*["']([^"']+)["']""", re.I)
RE_HTML_OPEN = re.compile(r"<html\b[^>]*>", re.I)
# En regel der erklærer tokens, skal kunne spores til sit scope, ellers tæller
# en produktregel som dækning på alle domæner — den fejl der skjulte `--accent`.
RE_SCOPED_ROOT = re.compile(
    r"""^(?P<scope>[^{}]*?)\b(?:html|:root)\s*(?P<attrs>\[[^{}]*\])\s*\{""",
    re.I,
)
RE_PROD_ATTR = re.compile(r"""data-product\s*=\s*["']?([\w-]+)""", re.I)
# En temabundet erklæring (`[data-theme="dark"]`, `:not([data-theme="light"])`)
# dækker ikke et ubetinget `var(--x)`: tokenet er uopløst i det andet tema.
RE_THEME_ATTR = re.compile(r"""data-theme\s*=\s*["']?[\w-]+""", re.I)


def strip_comments(css: str) -> str:
    return RE_COMMENT_CSS.sub("", css)


def _split_top_level(css: str) -> list[tuple[str, str]]:
    """(prelude, body) for hver regel på øverste niveau. @media foldes ud.

    Samme form som `pagepass._split_rules`, fordi porten skal se de samme regler
    som bygget så — en anden opdeling ville selv skabe forskelle.
    """
    rules: list[tuple[str, str]] = []
    i, n = 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            break
        prelude = css[i:j].strip()
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == "{":
                depth += 1
            elif css[k] == "}":
                depth -= 1
            k += 1
        body = css[j + 1:k - 1]
        if prelude.lower().startswith(("@media", "@supports")):
            rules.extend(_split_top_level(body))
        else:
            rules.append((prelude, body))
        i = k
    return rules


def rules_of(css: str) -> dict[str, str]:
    """selector -> normaliseret krop, for hver regel i en CSS-streng."""
    out: dict[str, str] = {}
    for prelude, body in _split_top_level(strip_comments(css)):
        p = " ".join(prelude.split())
        if not p or p.startswith("@"):
            continue
        # Bygget skriver en regel på én linje, kilden har den ombrudt. Uden
        # whitespace-normaliseringen meldte porten 2 falske fund på
        # `/text-on-image-checker` — en port der rødmer på sin egen
        # formatering kan ikke bruges.
        decls = "; ".join(" ".join(d.split()) for d in body.split(";") if d.strip())
        # En regel med to selektorer måles på hver: `.a, .b { … }` er to regler
        # for designsystemets formål, og kun den ene kan være tabt.
        for sel in p.split(","):
            s = sel.strip()
            if s:
                out.setdefault(s, decls)
    return out


def selectors_of(html: str) -> dict[str, str]:
    """Reglerne i sidens egne <style>-blokke."""
    found: dict[str, str] = {}
    for block in RE_STYLE_BLOCK.findall(html):
        for sel, decls in rules_of(block).items():
            found.setdefault(sel, decls)
    return found


def shell_classes(css: str) -> set[str]:
    return set(re.findall(r"\.([A-Za-z][\w-]*)", strip_comments(css)))


def markup_classes(html: str) -> set[str]:
    out: set[str] = set()
    for value in RE_CLASS_ATTR.findall(html):
        out.update(value.split())
    return out


def class_of(selector: str) -> str | None:
    """Den klasse en selektor erklærer, hvis den erklærer præcis én."""
    m = re.search(r"\.([A-Za-z][\w-]*)", selector)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Tokens. En deklaration er kun dækning for den side hvis scope den matcher.
# ---------------------------------------------------------------------------
def token_coverage(css: str) -> tuple[set[str], dict[str, set[str]]]:
    """(uden for scope, per produkt) — hvilke tokens style.css erklærer hvor.

    Kun regler der gælder i **alle** temaer tæller som dækning. En token der
    kun er erklæret under `[data-theme="dark"]` er uopløst i lyst tema, så at
    tælle den ville være præcis den fejlform porten skal fange: `style.css`
    erklærer 21 tokens i mørktemaet, og de fleste af dem findes også i `:root`,
    men ikke alle. Første måling af mutationen viste præcis det.
    """
    plain: set[str] = set()
    per_product: dict[str, set[str]] = {}
    for prelude, body in _split_top_level(strip_comments(css)):
        names = set(RE_DECL.findall(body))
        if not names:
            continue
        if RE_THEME_ATTR.search(prelude):
            # Temabundet erklæring: gælder ikke i lyst tema (eller i mørkt, for
            # `:not([data-theme="light"])`), så den dækker ikke et ubetinget
            # `var(--x)`. Ændres dette, skal porten sige det.
            continue
        prod = RE_PROD_ATTR.search(prelude)
        if prod:
            per_product.setdefault(prod.group(1).lower(), set()).update(names)
        else:
            plain.update(names)
    return plain, per_product


def tokens_used(css_or_html: str) -> set[str]:
    """Tokens der bruges *uden* fallback. En med fallback er allerede opløst."""
    return {tok for tok, closing in RE_VAR_USE.findall(css_or_html) if closing == ")"}


def unresolved_tokens(page_html: str, shell_css: str) -> list[str]:
    """Tokens siden bruger, som ingen regel den side rammer erklærer."""
    used = tokens_used(page_html)
    if not used:
        return []
    plain, per_product = token_coverage(shell_css)
    product = ""
    m = RE_HTML_OPEN.search(page_html)
    if m:
        pm = RE_DATA_PRODUCT.search(m.group(0))
        if pm:
            product = pm.group(1).strip().lower()
    # Sidens egen <style> tæller: en side må gerne erklære sine egne tokens.
    own: set[str] = set()
    for block in RE_STYLE_BLOCK.findall(page_html):
        for _, body in _split_top_level(strip_comments(block)):
            own.update(RE_DECL.findall(body))
    covered = plain | own | per_product.get(product, set())
    # En token, der kun *aliaser* en anden, skal have den aliasede med. Så
    # `--accent: var(--color-accent)` tæller kun hvis `--color-accent` også er
    # dækket — ellers ville porten genindføre præcis den fejl den skal fange,
    # hvor `--accent` lå i et produktscope og trak `--color-accent` med ud.
    def aliased(value: str) -> set[str]:
        return {tok for tok, _ in RE_VAR_USE.findall(value)}

    # Kun aliaser der er erklæret i et scope siden rammer, må løses op.
    scoped_rules: list[tuple[str, str]] = _split_top_level(strip_comments(shell_css))
    changed = True
    while changed:
        changed = False
        for prelude, body in scoped_rules:
            # Samme scope-regel som ovenfor: et alias i et scope siden ikke
            # rammer, løser ingenting.
            if RE_THEME_ATTR.search(prelude):
                continue
            prod = RE_PROD_ATTR.search(prelude)
            if prod and prod.group(1).lower() != product:
                continue
            for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+)", body):
                if name in covered and any(v.strip() in covered for v in aliased(value)):
                    for used_tok in aliased(value):
                        if used_tok not in covered:
                            covered.add(used_tok)
                            changed = True
    return sorted(used - covered)


# ---------------------------------------------------------------------------
# Fund
# ---------------------------------------------------------------------------
class Finding:
    __slots__ = ("page", "kind", "detail")

    def __init__(self, page: str, kind: str, detail: str):
        self.page, self.kind, self.detail = page, kind, detail

    def __str__(self) -> str:
        return f"{self.page}: {self.kind}: {self.detail}"


def dist_pages() -> list[tuple[str, Path]]:
    """(rute, fil) for hver bygget HTML-side."""
    out: list[tuple[str, Path]] = []
    if not DIST.is_dir():
        return out
    for domain_dir in sorted(p for p in DIST.iterdir() if p.is_dir()):
        for page in sorted(domain_dir.rglob("*.html")):
            route = "/" + page.relative_to(domain_dir).as_posix()
            if route.endswith("/index.html"):
                route = route[: -len("index.html")]
            out.append((f"{domain_dir.name}{route}", page))
    return out


def source_map() -> dict[str, Path]:
    """dist-rute -> kildefil, fra byggets egen filudvalg.

    Kortlagget læses fra `build_sites` selv, så porten ikke gætter en route
    til en fil: en forkeret antagelse ville give en stille port. Sider der
    kommer uden om `site/` (auditedwp's tre værktøjssider, `bugbottle-landing/`)
    har ingen kilde her og måles ikke for tabte regler — de er undtagelsen,
    ikke reglen.
    """
    try:
        build = importlib.import_module("build_sites")
    except Exception:
        return {}
    sites = {d: build.Site(d, c) for d, c in build.SITES.items()}
    try:
        build.select_files(sites)
    except Exception:
        return {}
    out: dict[str, Path] = {}
    for domain, site in sites.items():
        for _key, (src, dest) in site.files.items():
            out[f"{domain}/{dest}"] = src
    return out


def check() -> list[Finding]:
    shell_css_path = SITE / "style.css"
    if not shell_css_path.exists():
        return [Finding("site/style.css", "mangler", "skallen skal erklære tokens")]
    shell_css = shell_css_path.read_text(encoding="utf-8")
    classes = shell_classes(shell_css)
    sources = source_map()

    findings: list[Finding] = []
    for route, page in dist_pages():
        html = page.read_text(encoding="utf-8", errors="replace")
        domain = route.split("/", 1)[0]
        rel = route[len(domain) + 1:]

        # (2) Tokens. Måles på den byggede fil, uafhængigt af kilden.
        for token in unresolved_tokens(html, shell_css):
            findings.append(Finding(route, "uopløst token",
                                    f"var({token}) bruges, men ingen regel for "
                                    f"denne side erklærer den"))

        # (1) Tabte regler. Kræver kilden, så det måles på de rigtige filer.
        src = sources.get(route)
        if src is None or not src.exists():
            continue
        if not src.suffix.lower() in (".html", ".htm"):
            continue
        src_html = src.read_text(encoding="utf-8", errors="replace")
        before = selectors_of(src_html)
        after = selectors_of(html)
        present = markup_classes(html)
        for sel, decls in before.items():
            if sel in after and after[sel] == decls:
                continue
            cls = class_of(sel)
            if cls is None:
                # Selektorer uden klasse (`main`, `.a .b`) er designsystemets
                # kontrakt og erstattes af skallen; porten kan ikke bevise
                # det modsige, så den tier ikke.
                continue
            if cls not in present:
                # Elementet er væk fra markup. Reglen var overflødig.
                continue
            if cls in classes:
                # Skallen erklærer klassen: reglen er erstattet, ikke tabt.
                continue
            findings.append(Finding(route, "tabt regel",
                                    f"{sel} findes i {src.relative_to(ROOT)} "
                                    f"men ikke i dist, og style.css erklærer "
                                    f"ikke .{cls}"))
    return findings


# ---------------------------------------------------------------------------
# Selvtest. Muterer de rigtige filer og forlanger rødt med filnavn.
# ---------------------------------------------------------------------------
def _run_check() -> list[Finding]:
    return check()


def _mutate_pagepass(root: Path) -> None:
    """Gendan den gamle fejl: `*-wrap` spises uden at skallen erklærer klassen.

    Mutationen er bevidst *på `pagepass.py`*, fordi det er dér fejlen lå. En
    syntetisk side ville kun bevise at portens regex virker; denne beviser at
    porten kan se netop denne regression i vores egen kode.
    """
    target = root / "tools" / "pagepass.py"
    text = target.read_text(encoding="utf-8")
    before = """    if WRAP_SELECTOR_RE.match(s):
        return s.rsplit(".", 1)[1] in _SHELL_CLASSES"""
    after = """    if WRAP_SELECTOR_RE.match(s):
        return True  # MUTATION: troede på egen påstand om skallens ejerskab"""
    if before not in text:
        raise AssertionError("pagepass.py har ikke længere formen mutationen forventer")
    target.write_text(text.replace(before, after), encoding="utf-8")


def _mutate_style_css(root: Path) -> None:
    """Fjern én token fra `:root`, så den kun findes i et produktscope.

    Det er præcis fejlen fra 30/9: `--color-accent` lå kun under
    `html[data-product="deskuptime"]`, så den var uopløst på mahope.tools, og
    en regex over hele filen så den alligevel. Mutationen leder efter
    *tokenens værdi* og ikke efter en bestemt linje, så den rammer den rigtige
    regel også hvis `style.css` flytter sig.
    """
    target = root / "site" / "style.css"
    text = target.read_text(encoding="utf-8")
    decl = re.search(r"^(\s*)--color-accent:\s*(#[0-9a-fA-F]{3,8});\s*$", text, re.M)
    if not decl:
        raise AssertionError("style.css erklærer ikke --color-accent i :root")
    # Fjern kun fra det første blok (`:root` ligger før produktscoperne), så
    # mutationen er præcis "tokenen er ikke længere global".
    text = text[:decl.start()] + f"{decl.group(1)}--color-accent-mutation: {decl.group(2)};\n" + text[decl.end():]
    # Og erklær den i et produktscope, så den stadig findes i filen — en port der
    # kun greb "nævnt nogen steds" skulle være grøn på præcis denne mutation.
    scope = 'html[data-product="deskuptime"] {'
    if scope not in text:
        raise AssertionError("style.css har ikke produktscopet mutationen forventer")
    text = text.replace(scope, f'{scope}\n  --color-accent: {decl.group(2)};', 1)
    target.write_text(text, encoding="utf-8")


def self_test() -> int:
    """Selvtesten kopierer repoet, muterer de rigtige filer og dømmer porten.

    Den bygger en dist i kopien, så mutationerne måles på en bygget side — en
    port der læser `site/` alene ville være grøn fordi mutationen ikke nåede
    dist. Kopien er derfor ændret *før* buildet.
    """
    failures: list[str] = []
    checks = 0

    def ok(cond: bool, label: str) -> None:
        nonlocal checks
        checks += 1
        if not cond:
            failures.append(label)

    with tempfile.TemporaryDirectory(prefix="built-css-selftest-") as tmp:
        tmp_path = Path(tmp)
        work = tmp_path / "repo"
        work.mkdir()
        for item in ("site", "tools", "tests"):
            shutil.copytree(ROOT / item, work / item,
                            ignore=shutil.ignore_patterns("__pycache__"))
        for item in ("build_sites.py", "bugbottle-landing"):
            src_item = ROOT / item
            if src_item.is_dir():
                shutil.copytree(src_item, work / item)
            else:
                shutil.copy2(src_item, work / item)
        # `build_sites` henter auditedwp's tre værktøjssider via
        # `AUDITEDWP_DIR`, og buildet fejler på route inventory uden dem.
        # Sibling-repoet er read-only for os, så der peges på den rigtige
        # mappe i stedet for at kopiere den.
        #
        # `AUDITEDWP_DIR` skal *respekteres*, ikke overskrives: CI tjekker
        # auditedwp ud som `github.workspace/auditedwp-src` og sætter
        # miljøvariablen, fordi der ikke ligger et `../auditedwp` ved siden af
        # repoet. Et hårdkodet `ROOT.parent / "auditedwp"` peger der på en mappe
        # der ikke findes, og selvtesten døde så med "route inventory mismatch"
        # i CI — altså rød af en fejl i portens egen opsætning, ikke af et fund.
        env = dict(os.environ)
        auditedwp = Path(env.get("AUDITEDWP_DIR") or (ROOT.parent / "auditedwp"))
        if not (auditedwp / "site" / "deskuptime").is_dir():
            raise AssertionError(
                f"auditedwp's værktøjssider mangler i {auditedwp} — sæt "
                f"AUDITEDWP_DIR til auditedwp-checkouten (CI bruger "
                f"github.workspace/auditedwp-src)")
        env["AUDITEDWP_DIR"] = str(auditedwp)

        def build_in(work_root: Path) -> list[Finding]:
            """Byg i kopien og kør porten *der* — aldrig mod hovedrepoet."""
            # `detail` med i transporten: uden den kan selvtesten ikke kræve at
            # fundet rammer den *konkrete* regel eller token mutationen skaber,
            # og så ville enhver fejl i samme fjerde våre som bevis.
            code = (
                "import sys, json;"
                f"sys.path.insert(0, {str(work_root)!r});"
                "import build_sites, check_built_css as C;"
                "build_sites.main();"
                "print('<<<'+json.dumps([[f.page, f.kind, f.detail]"
                " for f in C.check()])+'>>>')"
            )
            proc = subprocess.run(
                [sys.executable, "-c", code], cwd=work_root, env=env,
                capture_output=True, text=True, timeout=900)
            if "<<<" not in proc.stdout:
                raise AssertionError(
                    f"kopiens build/portkørsel fejlede:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
            raw = proc.stdout.rsplit("<<<", 1)[1].split(">>>", 1)[0]
            return [Finding(row[0], row[1], row[2]) for row in json.loads(raw)]

        # Baseline: den umodificerede kopi skal være grøn. Uden dette krav er
        # en port, der er rød på alt, lige så "grøn" i mutationstesten. Og
        # den skal måles på en *bygget* dist — en port der læser `site/` alene
        # ville være grøn fordi mutationerne ikke når dist.
        baseline = build_in(work)
        ok(not baseline, f"baseline er grøn (fandt {len(baseline)}: "
                         f"{[str(f) for f in baseline[:3]]})")
        ok(bool((work / "dist").is_dir()) and any((work / "dist").iterdir()),
           "baseline måles på en rigtig bygget dist")

        # Mutation 1: pagepass spiser igen ethvert `*-wrap`.
        _mutate_pagepass(work)
        mutated = build_in(work)
        wrap_finds = [f for f in mutated if f.kind == "tabt regel"]
        ok(bool(wrap_finds),
           "pagepass-mutationen gør porten rød med tabte regler")
        # Fundet skal *navngive filen* — en tæller uden navn kan ikke rettes.
        # Og det skal ramme de klasser mutationen faktisk skaber: `.ti-canvas-wrap`
        # er i markup på `/text-on-image-checker` og i ingen `:root`-regel, så
        # den er det bevis, mutationen gav. Navnet er fundet i kilden, ikke
        # navngivet her — ellers ville porten være grøn fordi den mødte sig selv.
        ok(all("/" in f.page for f in wrap_finds),
           "mutationen navngiver den ramte side")
        ok(any("ti-canvas-wrap" in f.detail for f in wrap_finds),
           f"mutationen rammer den tabte `*-wrap`-regel, ikke en vilkårlig "
           f"fejl ({[f.detail[:60] for f in wrap_finds[:2]]})")
        shutil.copy2(ROOT / "tools" / "pagepass.py", work / "tools" / "pagepass.py")

        # Mutation 2: en token forlader `:root` og bliver produktsbundet.
        _mutate_style_css(work)
        mutated2 = build_in(work)
        token_finds = [f for f in mutated2 if f.kind == "uopløst token"]
        ok(bool(token_finds),
           "style.css-mutationen gør porten rød med uopløste tokens")
        ok(any("var(--color-accent)" in f.detail for f in token_finds),
           f"tokenfejlen rammer den flyttede token, ikke en anden "
           f"({[f.detail[:50] for f in token_finds[:2]]})")
        # `--color-accent` flytter ind i deskuptimes scope, så den skal være
        # uopløst på de domæner der *ikke* er deskuptime.
        ok(any(f.page.startswith("mahope.tools/") for f in token_finds),
           "tokenfejlen rammer et domæne, ikke bare DeskUptime")

    for label in failures:
        print(f"  FEJL  {label}")
    if failures:
        print(f"\ncheck_built_css --self-test: {len(failures)} fejl af {checks} kontroller")
        return 1
    print(f"check_built_css --self-test: OK ({checks} kontroller, "
          f"mutationerne gør porten rød med filnavn)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true",
                    help="mutér de rigtige filer og kræv at porten bliver rød")
    ap.add_argument("--quiet", action="store_true", help="kun exit-koden")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    if not dist_pages():
        print("intet bygget, porten springes over")
        return 0

    findings = check()
    if findings:
        if not args.quiet:
            for f in findings:
                print(f"  FEJL  {f}")
        print(f"\ncheck_built_css: RØD — {len(findings)} fund "
              f"(regler eller tokens der ikke overlever bygget)")
        return 1
    print("check_built_css: GRØN — hver sides CSS og tokens overlever bygget")
    return 0


if __name__ == "__main__":
    sys.exit(main())
