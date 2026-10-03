#!/usr/bin/env python3
"""Dom over installationskommandoer i publiceret tekst og i blog-generatorer.

Baggrund: `npx page-profile` stod i 10 publicerede blog-sider (EN+DA), men
pakken findes hverken paa npm (404) eller som et GitHub-repo, og
page-profile er et enkelt Python-script uden npm-vej overhovedet. Kunden fik
en kommando der fejlede med det samme den laeste.

Samme fejlform vaer opdaget i README'en (opgave 87: `pip install eaa-scanner`
var en 404), saa porten dommer hele overfladen i stedet for den enkelte tekst.

Reglerne er bevidst stramme, fordi de skal kunne faa nye sider skrevet af de 40+
`make_blog_*.py`-generatorer:

  1. Kun kommandoer i kodekontekst dommes: `<pre>`, `<code>`, ```-blokke og
     inline-backticks. Prosa som "brew install of the HTML-to-Markdown CLI" er
     en naervne, ikke en kommando, og skal ikke give en fejl.
  2. Et pakkenaevn skal vaere i kataloget (verificeret findes) eller i
     `PENDING` (verificeret findes IKKE) — og sidst i det sidste skal teksten
     sige, at det ikke er publiceret endnu. Ellers er den en loppe.
  3. `github:owner/repo` og `brew tap owner/tap` kræver, at repoet er i
     `GITHUB_REPOS` — verificeret via `gh api`, derfor ikke et netvaerkskald i
     selve porten (samme begrundelse som i check_readme_paths.py).
  4. Vores egne download-URL'er skal vaere i `OWN_URLS`, verificeret med et
     rigtigt HTTP-kald.

Kør:  python3 tools/check_install_commands.py [--self-test]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Hvilke filer porten laeser. `site/` er det publicerede, `make_blog_*.py` og
# `tools/*blog*.py` er de generatorer der skriver de publicerede sider — de
# skal dommes, ellers kommer fejlen tilbage naar en generator koeres igen.
SITE_ROOTS = ("site",)
GENERATOR_GLOBS = ("make_blog_*.py", "tools/*blog*.py", "tools/iter*.py", "tools/make_*blog*.py")
DOC_GLOBS = ("README.md", "site/**/*.md", "desktop/*.md", "obsidian-plugin/*.md", "page-profile/*.md")

# Verificeret 27/9-2026 med `curl -o /dev/null -w '%{http_code}'` mod
# pypi.org/pypi/<navn>/json og registry.npmjs.org/<navn>.
PENDING = {
    "eaa-scanner": "pypi.org/pypi/eaa-scanner/json -> 404",
    "site-icons": "pypi.org/pypi/site-icons/json -> 404",
}

# Hvis et navn staar her, skal teksten i naerheden sige at det ikke er
# publiceret endnu. Ellers er det en loppe, der fejler med 404 for kunden.
PENDING_MARKERS = (
    "when published",
    "not on pypi",
    "not yet on pypi",
    "ikke paa pypi",
    "ikke endnu paa pypi",
    "endnu ikke",
    "naar det udkommer",
    "saa snart det udkommer",
    "officially published",
)

# Findes, verificeret 27/9-2026.
PYPI = {
    "Pillow": "pypi.org/pypi/Pillow/json -> 200",
    # Vores to API-README'er viste et Python-eksempel med `import requests`
    # uden nogen pip-linje, saa kunden kopierede blokken og fik
    # ModuleNotFoundError. 27/9 efterfulgende fik de linjen — og saa dømte
    # denne port den nye linje, fordi pakken ikke var katalogiseret.
    "requests": "pypi.org/pypi/requests/json -> 200",
}

# Vores egne filer. Verificeret med et rigtigt HTTP-kald 27/9-2026.
OWN_URLS = {
    "https://mahope.tools/downloads/eaa_scanner-1.2.0-py3-none-any.whl": "200, 22 regler i det udpakket hjul",
    "https://mahope.tools/downloads/page-profile/page_profile.py": "200, 41403 byte",
    "https://mahope.tools/downloads/mahope-eaa-scanner-1.2.0.tgz": "200, npm-pakke @mahope/eaa-scanner",
}

# Vores egne værter. Kilden bruger build-værten, og build_sites.py skriver den
# om til produktionsdomænet i den publicerede HTML — porten skal derfor kende
# begge, ellers dommer den kildens URL'er som fremmede.
OWN_HOSTS = ("mahope.tools", "hermes-passiv.pages.dev")

# Binaries vi selv leverer i en af vores npm-pakker. `npx eaa-scan` er gyldigt
# *efter* `npm install -g <vores tgz>` — det er ikke et navn på npm.
OUR_NPM_BINS = {"eaa-scan", "deskuptime", "passiv-mcp", "clean-copy"}

# Pakker vi selv har publiceret på npm, så `npx @mahope/<pakke>` er gyldigt
# uden en `npm install` først. verificeret 3/10 med
# `curl -s https://registry.npmjs.org/@mahope%2Fpassiv-mcp` → 200 og
# `npm pack @mahope/passiv-mcp` → 4 filer; `dist-tags.latest` = 1.2.1.
#
# Skilt fra `OUR_NPM_BINS` fordi de er to forskellige ting: en *bin* her er et
# navn vi leverer inde i en tarball, der skal installeres først, mens en
# *pakke* her er noget npx henter direkte. Skilt også fra `GITHUB_REPOS`,
# fordi `npx github:…` henter fra git hver gang, mens denne kommer fra
# npm'ens cache — hurtigere, og uden at klonere.
OUR_NPM_PACKAGES = {
    "@mahope/passiv-mcp": "publiceret, latest 1.2.1, verificeret 3/10",
}


# npm/github-genveje. `github:owner/repo` verificeret med `gh api repos/...`
# (exists + public) 27/9-2026.
GITHUB_REPOS = {
    "mahope/deskuptime": "public, pushed 26/9",
    "mahope/passiv-mcp": "public, pushed 7/9",
    "mahope/clean-copy-cli": "public",
    "mahope/clean-copy": "public, pushed 25/9",
    "mahope/homebrew-tap": "public, canonical tap",
    "mahope/bugbottle": "public",
    "mahope/homebrew-clean-copy": "public, deprecated (bemaerket i tap'ens egen README)",
}

# Formulaer i de to taps, verificeret med `gh api .../contents/Formula` 27/9-2026.
# Nøglen er tap-stien som den skrives i kommandoen (`brew install mahope/tap/x`).
TAPS = {
    "mahope/tap": ("mahope/homebrew-tap", {"clean-copy", "deskuptime", "transmute"}),
    "mahope/clean-copy": ("mahope/homebrew-clean-copy", {"clean-copy"}),
}

# Eksterne formulaer, der optraeder i vores tekster. Findes i Homebrew core.
BREW = {"librsvg", "xz", "snapcraft", "dotenvx"}

URL = r"(?:https?://[^\s<>\"'`]+)"
# Et npm-navn er `@scope/name` eller `name`. Uden scope-leddet fanger mønsteret
# kun `@mahope` i `npx @mahope/passiv-mcp`, og porten så en pakke der hed
# «@mahope» — som ikke findes. Målt 3/10: skiftet til den publicerede pakke
# gjorde den port rød med præcis denne fejl, så mønsteret er rettet her
# frem for at skrive `github:` ind i siden for at gå uden om porten.
NAME = r"(?!-)(?:@[a-z0-9][\w.\-]*/[\w.\-]+|@?[a-z0-9][\w.\-]*(?::[\w.\-/]+)*)"

# Kommando-former. Hver gruppe: (regex, gruppe-indeks for navnet).
CMD_PATTERNS = [
    re.compile(rf"\bpip3?\s+install[ \t]+(?:--?[^ \t]+[ \t]+)*({URL}|[A-Za-z0-9][\w.\-]*(?:\[[^\]]+\])?)"),
    re.compile(rf"\bnpm[ \t]+(?:install|i)[ \t]+(?:-g[ \t]+|--global[ \t]+)?({URL}|{NAME})"),
    re.compile(rf"\bnpx[ \t]+(?:--yes[ \t]+|-y[ \t]+)?({URL}|{NAME})"),
    re.compile(r"\bbrew[ \t]+install[ \t]+(\S+)"),
    re.compile(r"\bbrew[ \t]+tap[ \t]+(\S+)"),
    re.compile(r"\bcargo\s+install\s+([\w.\-]+)"),
    re.compile(r"\bgo\s+install\s+([\w.\-/]+)"),
]

# Placeholdere i tekster: `npm install -g <url>` er en instruktion, ikke en
# kommando. Dommes ikke.
PLACEHOLDER = re.compile(r"^[<{\[]")


def _clean(token: str) -> str:
    """Skar token ved markup og citat: `mahope/tap/clean-copy</code>,` -> `mahope/tap/clean-copy`."""
    return re.split(r"[<\n]", token)[0].strip("`'\"&;,")


def is_own_url(url: str) -> bool:
    return any(host in url for host in OWN_HOSTS)


# Hvilke filer vi lader ligge, og hvorfor. Skal vaere en *begrundelse*, ikke en
# port, der er gammel.
SKIP_GLOBS = ("desktop/dist/**", "**/node_modules/**", "dist/**", ".wrangler/**", "*.tar.gz", "*.zip")


def code_spans(text: str) -> list[tuple[int, int]]:
    """Start-og-slut for hver kodekontekst i teksten."""
    spans: list[tuple[int, int]] = []
    for m in re.finditer(r"<pre\b[^>]*>.*?</pre>", text, re.S | re.I):
        spans.append((m.start(), m.end()))
    for m in re.finditer(r"<code\b[^>]*>.*?</code>", text, re.S | re.I):
        spans.append((m.start(), m.end()))
    for m in re.finditer(r"```.*?```", text, re.S):
        spans.append((m.start(), m.end()))
    for m in re.finditer(r"`[^`\n]+`", text):
        spans.append((m.start(), m.end()))
    return spans


def iter_files() -> list[Path]:
    files: set[Path] = set()
    for root in SITE_ROOTS:
        base = ROOT / root
        if base.is_dir():
            files.update(p for p in base.rglob("*") if p.is_file())
    for pattern in GENERATOR_GLOBS:
        files.update(ROOT.glob(pattern))
    for pattern in DOC_GLOBS:
        files.update(ROOT.glob(pattern))
    out = []
    for p in sorted(files):
        rel = p.relative_to(ROOT).as_posix()
        if any(rel.endswith(sfx) or fnmatch(rel, pat) for pat in SKIP_GLOBS for sfx in ((),)):
            continue
        if p.suffix in {".zip", ".gz", ".png", ".jpg", ".ico", ".whl", ".dmg"}:
            continue
        out.append(p)
    return out


def fnmatch(rel: str, pat: str) -> bool:
    import fnmatch as f

    return f.fnmatch(rel, pat)


def check_line(cmd: str, context: str, tap: str | None) -> list[str]:
    """Returner fejllinjer for én kommando. Kontekst er +/- 200 tegn omkring."""
    problems: list[str] = []

    def target_of(*patterns: re.Pattern[str]) -> str | None:
        for pat in patterns:
            m = pat.search(cmd)
            if m:
                # Skar ved HTML-lukketag: `brew install mahope/tap/clean-copy</code>,`
                # er formulaen `mahope/tap/clean-copy` og ikke markupket med.
                return re.split(r"[<\n]", m.group(1))[0].strip("`'\"&;,")
        return None

    pip_pat = re.compile(r"\bpip3?\s+install[ \t]+(?:--?[^ \t]+[ \t]+)*(\S+)")
    npm_pat = re.compile(r"\bnpm[ \t]+(?:install|i)[ \t]+(?:-g[ \t]+|--global[ \t]+)?(\S+)")
    npx_pat = re.compile(r"\bnpx[ \t]+(?:--yes[ \t]+|-y[ \t]+)?(\S+)")
    brew_inst = re.compile(r"\bbrew[ \t]+install[ \t]+(\S+)")
    brew_tap = re.compile(r"\bbrew[ \t]+tap[ \t]+(\S+)")

    target = target_of(pip_pat)
    if target is not None:
        if PLACEHOLDER.match(target):
            return problems
        if target.startswith(("http://", "https://")):
            if target not in OWN_URLS and not is_own_url(target):
                problems.append(f"{target} er ikke en af vores filer — læg den i OWN_URLS hvis den er det")
            return problems
        if re.search(r"pip3?\s+install[ \t]+(?:-r|--requirement)\b", cmd):
            return problems  # kravsfil, ikke et pakkenaevn
        if target.startswith(("/", "./", "~")):
            return problems  # lokal sti, kan ikke dømmes offline
        base = re.split(r"[<>=!\[]", target)[0]
        if base in PYPI:
            return problems
        if base in PENDING:
            if not any(marker in context.lower() for marker in PENDING_MARKERS):
                problems.append(
                    f"pip-pakken {base} findes ikke ({PENDING[base]}), "
                    "og teksten siger ikke at den endnu ikke er publiceret"
                )
            return problems
        problems.append(
            f"pip-pakken {base} er ikke i kataloget — verificér den, og læg den i PYPI eller PENDING"
        )
        return problems

    target = target_of(npm_pat, npx_pat)
    if target is not None:
        if PLACEHOLDER.match(target):
            return problems
        if target.startswith(("http://", "https://")):
            if target not in OWN_URLS and not is_own_url(target):
                problems.append(f"{target} er ikke en af vores filer")
            return problems
        if target.startswith("github:"):
            repo = target[len("github:") :].split("#")[0].rstrip("/")
            if repo not in GITHUB_REPOS:
                problems.append(f"github:{repo} er ikke et verificeret offentligt repo")
            return problems
        if cmd.lstrip().startswith("npx") and target in OUR_NPM_BINS:
            return problems  # bin fra en af vores egne npm-pakker
        if target in OUR_NPM_PACKAGES:
            return problems  # pakke vi selv har publiceret under vores scope
        problems.append(
            f"npm-pakken {target} er ikke i kataloget — npm har ingen {target} "
            "(verificér med registry.npmjs.org/<navn>)"
        )
        return problems

    if brew_tap.search(cmd):
        problems.extend(_check_tap(_clean(brew_tap.search(cmd).group(1))))
        return problems

    m = brew_inst.search(cmd)
    if m:
        formula = _clean(m.group(1))
        if PLACEHOLDER.match(formula):
            return problems
        if formula in BREW:
            return problems
        if tap and "/" not in formula:
            return _check_formula(tap, formula)
        if "/" in formula:
            parts = formula.strip("/").split("/")
            if len(parts) == 3 and "/".join(parts[:2]) in TAPS:
                return _check_formula("/".join(parts[:2]), parts[2])
            problems.append(
                f"brew-formulaen {formula} peger på en tap der ikke er verificeret: {'/'.join(parts[:2])}"
            )
            return problems
        problems.append(
            f"brew-formulaen {formula} er ikke i kataloget — læg den i BREW hvis den findes i Homebrew core"
        )
        return problems

    for pat in CMD_PATTERNS[5:]:
        m = pat.search(cmd)
        if m:
            problems.append(f"{m.group(1)} er ikke i kataloget ({pat.pattern[:12]}…)")
    return problems


def _check_tap(tap: str) -> list[str]:
    if PLACEHOLDER.match(tap):
        return []
    if tap not in TAPS:
        return [f"tap {tap} er ikke verificeret — `gh api repos/{tap.replace('/', '/homebrew-')} med et tomt navn er ikke et tap"]
    repo, _ = TAPS[tap]
    if repo not in GITHUB_REPOS:
        return [f"tap {tap} peger på {repo}, som ikke er verificeret offentligt"]
    return []


def _check_formula(tap: str, formula: str) -> list[str]:
    if tap not in TAPS:
        return [f"tap {tap} er ikke verificeret"]
    repo, formulae = TAPS[tap]
    if formula not in formulae:
        return [f"{repo} har ikke formulaen {formula} (har: {', '.join(sorted(formulae))})"]
    return []



def check_text(text: str, label: str) -> list[str]:
    spans = code_spans(text)
    if not spans:
        return []
    problems: list[str] = []
    # Finditer over HELE teksten, ikke per linje: en kommando paa linje 2 i en
    # <pre>-blok har en absolut offset, der ikke er lig linjens start. Den foelste
    # udgave brugte linje-relative offsets mod heltekst-spans, og var derfor
    # gron paa 439 filer og fangede ingen af mutationerne i selftesten.
    linjes: list[int] = [0]
    for idx, ch in enumerate(text):
        if ch == "\n":
            linjes.append(idx + 1)

    def linje_for(offset: int) -> int:
        lo, hi = 0, len(linjes) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if linjes[mid] <= offset:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    for pat in CMD_PATTERNS:
        for m in pat.finditer(text):
            span = next(((a, b) for a, b in spans if a <= m.start() < b), None)
            if span is None:
                continue  # prosa, ikke en kommando
            cmd = m.group(0)
            lo = max(0, m.start() - 200)
            hi = min(len(text), m.end() + 200)
            # `brew tap X && brew install y` er én kommando. Find det nærmeste
            # `brew tap` før kommandoen i samme kodeblok, ellers dømmer vi
            # formulaen `deskuptime` som en ukendt Homebrew-formula.
            tap = None
            for t in re.finditer(r"\bbrew[ \t]+tap[ \t]+(\S+)", text[span[0] : m.start()]):
                tap = t.group(1).strip("`'\"&;")
            for problem in check_line(cmd, text[lo:hi], tap):
                problems.append(f"{label}:{linje_for(m.start())}: {problem} [{cmd.strip()}]")
    return problems


def check_repo() -> list[str]:
    problems: list[str] = []
    files = iter_files()
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        problems.extend(check_text(text, rel))
    return problems


def self_test() -> int:
    """Mutationer paa virkelige filer. Tæler fund, ikke bare et grønt flag."""
    src = (ROOT / "site/blog/canonical-url-guide.html").read_text(encoding="utf-8")
    good = "npx github:mahope/deskuptime check https://example.com"
    pending_ok = "pip install site-icons  # (when published)"
    cases = [
        ("M1 npx page-profile i <pre>", src.replace("<pre class=\"cmd\"><code>", f"<pre class=\"cmd\"><code>$ {good}\nnpx page-profile https://x", 1), 1, "page-profile"),
        ("M2 kendt github-repo er grøn", src.replace("<pre class=\"cmd\"><code>", f"<pre class=\"cmd\"><code>$ {good}", 1), 0, ""),
        ("M3 samme kommando i prosa er ikke en kommando", src.replace("<p>", f"<p>{good} ", 1), 0, ""),
        ("M4 pip-pakke der ikke findes uden markering", src.replace("<pre class=\"cmd\"><code>", '<pre class="cmd"><code>$ pip install site-icons', 1), 1, "site-icons"),
        ("M5 samme pakke med 'when published' er grøn", src.replace("<pre class=\"cmd\"><code>", f"<pre class=\"cmd\"><code>$ {pending_ok}", 1), 0, ""),
        ("M6 uverificeret github-repo", src.replace("<pre class=\"cmd\"><code>", "<pre class=\"cmd\"><code>$ npx github:mahope/fin-ikke", 1), 1, "fin-ikke"),
        ("M7 tap-formula der ikke findes", src.replace("<pre class=\"cmd\"><code>", "<pre class=\"cmd\"><code>$ brew install mahope/tap/ghost", 1), 1, "ghost"),
    ]
    fejl = 0
    for navn, tekst, forventet, skal_nævnes in cases:
        fund = check_text(tekst, "selftest")
        if len(fund) != forventet:
            print(f"FEJL {navn}: forventede {forventet} fund, fik {len(fund)}")
            for f in fund:
                print(f"     {f}")
            fejl += 1
            continue
        if skal_nævnes and not any(skal_nævnes in f for f in fund):
            print(f"FEJL {navn}: ingen fejl nævner {skal_nævnes!r}")
            fejl += 1
            continue
        print(f"ok   {navn} ({len(fund)} fund)")
    print(f"selftest: {len(cases) - fejl}/{len(cases)} mutationer fanget")
    return 1 if fejl else 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    problems = check_repo()
    for p in problems:
        print(p)
    filer = len(iter_files())
    if problems:
        print(f"\ninstall-kommandoer: {len(problems)} fejl i {filer} filer")
        return 1
    print(f"install-kommandoer: OK — 0 fejl i {filer} filer")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
