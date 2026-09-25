#!/usr/bin/env python3
"""Hard gate for dead internal references in the built sites.

`build_sites.py` tæller rodrelative referencer under sin egen rewrite-pas, men
det er et regex-scan af hele filen: det kan ikke se, hvad der står i et
kodeeksempel. `site/blog/open-graph-checker.html` *viser* `<meta … content=
"/img/cover.jpg">` for at forklare, hvorfor relative og:image-fejl fejler. Det
er ikke en side vi skylder nogen, men regex-porten vidste ikke det — så de 18
"broken references" var en blanding af ni reelle døde links og to falske
positiver, og fordi porten aldrig fejlede, blev ingen af dem rettet i en måned.

Denne gate går den anden vej: den parser det **byggede output** med
`html.parser`, springer `pre`/`code`/`script`/`style` over, og kræver at hver
rodrelativ reference peger på en fil der faktisk findes i det dist, den står i.
Krydsdomæne-referencer til vores egne domæner tjekkes mod det domænes dist, så
et link fra cleancopy.tools til mahope.tools ikke kan være en 404, fordi
mahope.tools-distet ikke var bygget i det samme job.

Exit 1 ved én reel uopklaret reference. Springes over når intet er bygget, i
samme mønster som resten af distribution-gaten.

Brug:
    python3 tools/check_links.py
    python3 tools/check_links.py --only mahope.tools
    python3 tools/check_links.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
# Domæner vi selv ejer. En reference til et af dem skal findes i *dets* dist.
OUR_DOMAINS = ("cleancopy.tools", "deskuptime.com", "bugbottle.dev", "mahope.tools")
# Ruter som workeren svarer på. Findes ikke som fil, og skal ikke fejle.
WORKER_PREFIXES = ("/api/", "/scan-proxy")
# Interne søgemaskine- og 404-ruter, der findes i source men ikke som fil.
DECLARED = ("/404", "/search", "/sitemap.xml", "/robots.txt", "/.well-known/security.txt",
            "/build-info.json", "/humans.txt", "/llms.txt", "/llms-full.txt",
            "/favicon.ico", "/favicon.svg", "/apple-touch-icon.png", "/icon-192.png",
            "/icon-512.png", "/site.webmanifest", "/og.png", "/og-da.png", "/wrangler.toml",
            "/thanks")
# Artefakter en kunde kan hente. Et downloadlink der ikke findes, er en død
# købssti — de skal have en smoke test, ikke bare blive nævnt.
DOWNLOAD_EXT = (".zip", ".tgz", ".tar.gz", ".whl", ".dmg", ".exe", ".msi", ".deb", ".rpm",
                ".epub", ".pdf", ".py", ".yml", ".yaml", ".md", ".css", ".js", ".json", ".txt")
# Formularer der indsender et lead. Uden endpoint er de en kontaktformular,
# der ligner en formular.
LEAD_MARKERS = ("/api/", "mailto:", "formspree", "netlify")


class RefParser(HTMLParser):
    """Samler referencer uden at se ind i kodeeksempler."""

    SKIP_CONTENT = {"pre", "code", "script", "style", "textarea", "template"}

    def __init__(self, rel: str) -> None:
        super().__init__(convert_charrefs=True)
        self.rel = rel
        self.refs: list[tuple[str, int]] = []      # (reference, line)
        self.forms: list[tuple[str, int, str]] = []  # (action, line, method)
        self.downloads: list[tuple[str, int]] = []
        self._skip_depth = 0
        self._line = 1
        self._newline_re = re.compile("\n")

    # -- helpers ---------------------------------------------------------
    def _bump(self, chunk: str) -> None:
        self._line += self._newline_re.count(chunk)

    def _add(self, value: str | None, line: int) -> None:
        if not value:
            return
        value = value.strip()
        if not value or value.startswith(("#", "data:", "javascript:", "mailto:", "tel:")):
            return
        if is_download(value):
            self.downloads.append((value, line))

    # -- parser ----------------------------------------------------------
    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: D102
        self._line += 1
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag in self.SKIP_CONTENT:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        for key in ("href", "src", "action", "poster", "data-href", "cite"):
            if key in a:
                self._add(a[key], self._line)
                self.refs.append((a[key].strip(), self._line))
        if tag == "link" and a.get("rel", "").lower() in ("stylesheet", "icon", "apple-touch-icon"):
            self._add(a.get("href"), self._line)
            self.refs.append((a.get("href", "").strip(), self._line))
        if tag == "img" and a.get("srcset"):
            for part in a["srcset"].split(","):
                self._add(part.strip().split(" ")[0], self._line)
        if tag == "source" and a.get("srcset"):
            for part in a["srcset"].split(","):
                self._add(part.strip().split(" ")[0], self._line)
        if tag == "form":
            self.forms.append((a.get("action", "").strip(), self._line, a.get("method", "get").lower()))
        if tag == "meta":
            prop = (a.get("property") or a.get("name") or "").lower()
            if prop in ("og:image", "og:url") and a.get("content"):
                self._add(a["content"], self._line)
                self.refs.append((a["content"].strip(), self._line))

    def handle_startendtag(self, tag, attrs) -> None:  # noqa: D102
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:  # noqa: D102
        self._line += 1
        if tag in self.SKIP_CONTENT and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:  # noqa: D102
        if self._skip_depth:
            return
        # Kun urls i ren tekst (llms.txt, robots, txt-filer), ikke i markup.
        if "<" in data and ">" in data:
            return
        for m in re.finditer(r"https?://[^\s\"'<>)\]]+", data):
            self.refs.append((m.group(0), self._line))
            self._add(m.group(0), self._line)
        # Den anden skråstreg i "https://mahope.tools/x" er ikke en rodreference,
        # og heller ikke skråstregen i en protokol- relativ "//x". Se kun stier
        # der begynder med en rigtig skråsteg.
        for m in re.finditer(r"(?<![\w.:/])/(?!/)[^\s\"'<>)\]]*", data):
            self._add(m.group(0), self._line)

    def handle_entityref(self, name) -> None:  # noqa: D102
        pass

    def error(self, message) -> None:  # pragma: no cover - py<3.10 leftover
        pass


def is_download(ref: str) -> bool:
    path = urlsplit(ref).path if "://" in ref else ref.split("?")[0].split("#")[0]
    return path.lower().endswith(DOWNLOAD_EXT)


def split_ref(ref: str) -> tuple[str, str, str]:
    """(kind, domain, path) hvor kind er 'skip', 'external', 'root' eller 'rel'."""
    ref = ref.strip()
    if not ref or ref.startswith(("#", "data:", "javascript:", "mailto:", "tel:", "blob:")):
        return "skip", "", ""
    if "://" in ref:
        parts = urlsplit(ref)
        if parts.netloc.lower() not in OUR_DOMAINS:
            return "external", parts.netloc.lower(), parts.path
        return "root", parts.netloc.lower(), parts.path
    if ref.startswith("//"):
        return "external", "", ref
    if not ref.startswith("/"):
        return "rel", "", ref
    return "root", "", ref.split("#")[0].split("?")[0]


def route_exists(domain_dist: Path, path: str) -> bool:
    """Findes ruten i et dist? Ren sti, mappe med index.html, eller deklareret rute."""
    clean = path.rstrip("/")
    if any(clean == d or clean.startswith(d + "/") for d in DECLARED):
        return True
    if clean.startswith(WORKER_PREFIXES):
        return True
    if not clean or clean == "/":
        return (domain_dist / "index.html").is_file()
    target = domain_dist / clean.lstrip("/")
    if target.is_file():
        return True
    if (target / "index.html").is_file():
        return True
    if (domain_dist / (clean.lstrip("/") + ".html")).is_file():
        return True
    if (domain_dist / (clean.lstrip("/") + "/index.html")).is_file():
        return True
    return False


def built_domains() -> dict[str, Path]:
    if not DIST.is_dir():
        return {}
    return {d.name: d for d in sorted(DIST.iterdir()) if d.is_dir() and (d / "index.html").is_file()}


def check_domain(domain: str, dist: Path, dists: dict[str, Path], check_downloads: bool) -> list[str]:
    problems: list[str] = []
    downloads: list[str] = []
    forms: list[tuple[str, int, str]] = []
    for path in sorted(dist.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in (".html", ".htm", ".txt", ".xml"):
            continue
        rel = path.relative_to(dist).as_posix()
        parser = RefParser(rel)
        try:
            parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
            parser.close()
        except Exception as exc:  # noqa: BLE001 - en ugyldig fil må ikke slå gaten fra
            problems.append(f"{domain}: {rel} kunne ikke parses: {exc}")
            continue
        downloads += [(r, parser.rel) for r, _ in parser.downloads]
        forms += [(a, parser.rel, m) for a, _, m in parser.forms]
        for ref, line in parser.refs:
            kind, ref_domain, ref_path = split_ref(ref)
            if kind in ("skip", "external"):
                continue
            if kind == "rel":
                base_dir = (dist / rel).parent
                target = base_dir / ref_path.split("#")[0].split("?")[0]
                if not (target.is_file() or (target / "index.html").is_file()
                        or (base_dir / (ref_path + ".html")).is_file()):
                    problems.append(f"{domain}: {rel}:{line}: relativ reference {ref!r} findes ikke")
                continue
            if ref_domain and ref_domain != domain:
                # Kun domæner vi ejer *og* som faktisk er bygget i dette job.
                other = dists.get(ref_domain)
                if other is None:
                    continue
                if not route_exists(other, ref_path):
                    problems.append(
                        f"{domain}: {rel}:{line}: krydsdomæne-reference {ref!r} findes ikke i {ref_domain}")
                continue
            if not route_exists(dist, ref_path):
                problems.append(f"{domain}: {rel}:{line}: {ref!r} findes ikke i distet")
    if check_downloads:
        for ref, rel in downloads:
            kind, ref_domain, ref_path = split_ref(ref)
            if kind == "skip" or (kind == "external" and ref_domain not in OUR_DOMAINS):
                continue
            target_dist = dists.get(ref_domain) if ref_domain else dist
            if target_dist is None or not route_exists(target_dist, ref_path):
                problems.append(f"{domain}: {rel}: downloadlink {ref!r} kan ikke hentes")
    # Formularer: en lead-formular uden endpoint ligner en formular men
    # indsender intet. JS-formularer poster til en worker-rute, og den skal
    # findes i workeren — ellers er den en død knap.
    for action, rel, method in forms:
        if not action:
            continue
        kind, ref_domain, ref_path = split_ref(action)
        if kind == "skip":
            continue
        target_dist = dists.get(ref_domain) if ref_domain else dist
        if target_dist is not None and not route_exists(target_dist, ref_path) \
                and not any(m in action for m in LEAD_MARKERS):
            problems.append(f"{domain}: {rel}: formular-peger på {action!r}, som ikke findes")
    return problems


def check(only: str | None = None) -> tuple[int, list[str]]:
    dists = built_domains()
    if not dists:
        print("check_links: intet dist at kontrollere (kør build_sites.py først) — springer over")
        return 0, []
    if only:
        if only not in dists:
            print(f"check_links: {only} er ikke bygget i dist/ — springer over")
            return 0, []
        dists = {only: dists[only]}
    problems: list[str] = []
    for domain, dist in dists.items():
        found = check_domain(domain, dist, built_domains(), check_downloads=True)
        problems += found
        print(f"check_links: {domain}: {'OK' if not found else str(len(found)) + ' fejl'}")
    return len(problems), problems


# --------------------------------------------------------------------------
# Selftest — bevis at porten fanger fejlformen, ikke bare at den er kørt
# --------------------------------------------------------------------------
def _fixture(root: Path) -> dict[str, Path]:
    """To domæner med en sund start, inkl. et krydsdomænelink der *skal* virke."""
    dists: dict[str, Path] = {}
    for domain in ("mahope.tools", "cleancopy.tools"):
        d = root / domain
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            '<!doctype html><html><head><link rel="stylesheet" href="/style.css"></head>'
            '<body><a href="/findes">ok</a>'
            '<p><a href="https://mahope.tools/findes">tværsite</a></p>'
            '<p>Skriv til <a href="mailto:a@b.dk">os</a> eller ring <a href="tel:+4512345678">1234</a></p>'
            '<form action="/api/lead" method="post"></form>'
            '<pre><code>npm install /downloads/kan-ikke-hentes.tgz</code></pre>'
            '<code>&lt;meta content="/img/cover.jpg"&gt;</code>'
            '</body></html>', encoding="utf-8")
        (d / "style.css").write_text("body{}\n", encoding="utf-8")
        (d / "findes.html").write_text("<!doctype html><p>ja</p>", encoding="utf-8")
        dists[domain] = d
    return dists


def self_test() -> int:
    import tempfile

    ok = True
    with tempfile.TemporaryDirectory() as td:
        dists = _fixture(Path(td))
        main_dist, main_domain = dists["mahope.tools"], "mahope.tools"
        probe = main_dist / "probe.html"
        original = "<!doctype html><body><p>ren tekst</p></body>"

        def run(snippet: str, dist_map: dict[str, Path] | None = None):
            probe.write_text(f"<!doctype html><body>{snippet}</body>", encoding="utf-8")
            return check_domain(main_domain, main_dist, dist_map or dists, True)

        def expect(label: str, snippet: str, fragment: str) -> None:
            nonlocal ok
            found = run(snippet)
            if not any(fragment in f for f in found):
                print(f"FEJL: selftesten `{label}` forventede en fejl med {fragment!r}, "
                      f"fik: {found or 'ingen fejl'}", file=sys.stderr)
                ok = False

        def expect_clean(label: str, snippet: str, dist_map: dict[str, Path] | None = None) -> None:
            nonlocal ok
            found = run(snippet, dist_map)
            if found:
                print(f"FEJL: `{label}` må ikke fejle, men gav: {found}", file=sys.stderr)
                ok = False

        # 0. Den sunde fixture må ikke give en eneste fejl.
        found = check_domain(main_domain, main_dist, dists, True)
        if found:
            print(f"FEJL: selftestens sunde fixture gav fejl: {found}", file=sys.stderr)
            ok = False

        # 1. Hver fejlform skal fanges.
        expect("død href", '<a href="/findes-ikke">x</a>', "/findes-ikke")
        expect("død asset", '<img src="/logo.png">', "/logo.png")
        expect("død stylesheet", '<link rel="stylesheet" href="/mangler.css">', "/mangler.css")
        expect("død form-action", '<form action="/findes-ikke"></form>', "/findes-ikke")
        expect("død download", '<a href="/downloads/mangler.zip">x</a>', "/downloads/mangler.zip")
        expect("krydsdomæne 404", '<a href="https://cleancopy.tools/udenfor">x</a>', "udenfor")
        expect("død iframe", '<iframe src="/indlejret"></iframe>', "/indlejret")

        # 2. Kodeeksempler må ALDRIG fejle, uanset hvor døde de ser ud.
        for snippet in ('<pre><code>npm i /downloads/dod.zip</code></pre>',
                        '<code>&lt;img src="/img/cover.jpg"&gt;</code>',
                        '<script>var u="/api/nej";</script>',
                        '<style>.a{background:url(/img/dod.png)}</style>',
                        '<pre><a href="/findes-ikke">x</a></pre>'):
            expect_clean("kodeeksempel", snippet)

        # 3. Det sunde krydsdomænelink skal fortsat være grønt, og et link til
        #    et domæne vi ikke har bygget skal springes over — ellers dør
        #    matrix-jobbet i CI på en 404, der ikke findes.
        expect_clean(" sundt krydsdomænelink", '<a href="https://cleancopy.tools/findes">x</a>')
        one = {main_domain: main_dist}
        expect_clean("ubygget domæne", '<a href="https://bugbottle.dev/ukendt">x</a>', one)

        # 4. Positiv kontrol: mutationen skal give exit 1, ikke bare en liste.
        rc = len(run('<a href="/findes-ikke">x</a>'))
        if rc == 0:
            print("FEJL: selftesten fandt ingen fejl i den positive kontrol", file=sys.stderr)
            ok = False
        probe.write_text(original, encoding="utf-8")
        if probe.exists():
            probe.unlink()

    print("check_links --self-test: OK" if ok else "check_links --self-test: FEJL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", help="kontrollér kun dette domæne")
    ap.add_argument("--self-test", action="store_true", help="bevis at gaten fanger fejlformen")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    n, problems = check(args.only)
    if n:
        print(f"\ncheck_links: {n} uopklaret(e) reference(s):", file=sys.stderr)
        for p in problems[:40]:
            print(f"  {p}", file=sys.stderr)
        if n > 40:
            print(f"  … og {n - 40} mere", file=sys.stderr)
        return 1
    print("check_links: 0 uopklarede referencer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
