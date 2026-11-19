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
`html.parser`, springer kodeeksemplers tekst og indholdet af `script`/`style` over, og
opløser relative, rodrelative og absolutte referencer til de byggede sites.
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
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
# Domæner vi selv ejer. En reference til et af dem skal findes i *dets* dist.
OUR_DOMAINS = ("cleancopy.tools", "deskuptime.com", "bugbottle.dev", "mahope.tools")
# Ruter som workeren svarer på. Findes ikke som fil, og skal ikke fejle.
WORKER_PREFIXES = ("/api/", "/scan-proxy")
CLOUDFLARE_EMAIL_ROUTE = "/cdn-cgi/l/email-protection"
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


def canonical_url(relpath: str) -> str:
    """Spejler build_sites.py: filstien som den rute søgemaskinen ser."""
    p = "/" + relpath
    if p.endswith("/index.html"):
        return p[: -len("index.html")]
    if p.endswith(".html"):
        return p[:-5]
    return p


class RefParser(HTMLParser):
    """Samler referencer uden at se ind i kodeeksempler."""

    SKIP_CONTENT = {"script", "style", "textarea", "template"}

    def __init__(self, rel: str) -> None:
        super().__init__(convert_charrefs=True)
        self.rel = rel
        self.refs: list[tuple[str, int]] = []      # (reference, line)
        self.anchors: list[tuple[str, int]] = []   # (reference, line) — kun attributter
        self.forms: list[tuple[str, int, str]] = []  # (action, line, method)
        self.downloads: list[tuple[str, int]] = []
        # id="…"-værdier i filen. Ved duplikattributter tager browseren den
        # FØRSTE, så gør vi det samme — ellers ville `<main id="main"
        # id="platforms">` få os til at melde et levende #main-link dødt.
        self.ids: set[str] = set()
        # Læser siden sin egen location.hash? Så er `#url=…` en parameter og
        # ikke et anker, og porten skal ikke krave et id med det navn.
        self.reads_hash = False
        self._skip_depth = 0
        self._script_depth = 0
        self._code_depth = 0
        self._line = 1
        self._newline_re = re.compile("\n")

    # -- helpers ---------------------------------------------------------
    def _bump(self, chunk: str) -> None:
        self._line += self._newline_re.count(chunk)

    def _add(self, value: str | None, line: int, anchor: bool = False) -> None:
        if not value:
            return
        value = value.strip()
        if not value or value.startswith(("data:", "javascript:", "mailto:", "tel:")):
            return
        if anchor:
            self.anchors.append((value, line))
        if value.startswith("#"):
            return
        if is_download(value):
            self.downloads.append((value, line))

    def _attrs(self, attrs) -> dict[str, str]:
        """Første værdi vinner for duplikattributter — det er browserens regel."""
        out: dict[str, str] = {}
        for k, v in attrs:
            k = k.lower()
            if k not in out:
                out[k] = v or ""
        return out

    # -- parser ----------------------------------------------------------
    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: D102
        self._line += 1
        a = self._attrs(attrs)
        if tag in {"pre", "code"}:
            self._code_depth += 1
        if tag == "script":
            self._script_depth += 1
        # `id` på elementet *selv* er et gyldigt fragmentmål, også på en
        # `<textarea>` eller `<pre>` — springet gælder indholdet, ikke
        # attributterne. 5/10: `#input-box` på `/clean-copy-tool` var dødt for
        # porten, fordi den så springe-kun'en over elementets egen id, og
        # browseren fokuserer textarea'en fint. Kun id'er på dybde 0 tages med,
        # så et id *inde i* et kodeeksempel stadig ikke regnes som levende.
        if not self._skip_depth and a.get("id"):
            self.ids.add(a["id"].strip())
        if tag in self.SKIP_CONTENT:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "a" and a.get("name"):
            self.ids.add(a["name"].strip())
        for key in ("href", "src", "action", "poster", "data-href", "cite"):
            if key in a:
                self._add(a[key], self._line, anchor=True)
                self.refs.append((a[key].strip(), self._line))
        if tag == "link" and a.get("rel", "").lower() in ("stylesheet", "icon", "apple-touch-icon"):
            self._add(a.get("href"), self._line, anchor=True)
            self.refs.append((a.get("href", "").strip(), self._line))
        if tag == "img" and a.get("srcset"):
            for part in a["srcset"].split(","):
                self._add(part.strip().split(" ")[0], self._line, anchor=True)
        if tag == "source" and a.get("srcset"):
            for part in a["srcset"].split(","):
                self._add(part.strip().split(" ")[0], self._line, anchor=True)
        if tag == "form":
            self.forms.append((a.get("action", "").strip(), self._line, a.get("method", "get").lower()))
        if tag == "meta":
            prop = (a.get("property") or a.get("name") or "").lower()
            if prop in ("og:image", "og:url") and a.get("content"):
                self._add(a["content"], self._line, anchor=True)
                self.refs.append((a["content"].strip(), self._line))

    def handle_startendtag(self, tag, attrs) -> None:  # noqa: D102
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:  # noqa: D102
        self._line += 1
        if tag in {"pre", "code"} and self._code_depth:
            self._code_depth -= 1
        if tag == "script" and self._script_depth:
            self._script_depth -= 1
        if tag in self.SKIP_CONTENT and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:  # noqa: D102
        if self._script_depth:
            if "location.hash" in data or "window.location.hash" in data:
                self.reads_hash = True
            return
        if self._skip_depth or self._code_depth:
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


def split_target(ref: str, source_route: str) -> tuple[str, str, str, str]:
    """Klassificér referencen og opløs stien mod kildesidens offentlige URL."""
    ref = ref.strip()
    if not ref:
        return "skip", "", "", ""
    if ref.startswith("#"):
        return "same", "", source_route, unquote(ref[1:])
    parts = urlsplit(ref)
    if parts.scheme not in ("", "http", "https"):
        return "skip", "", "", ""
    domain = parts.hostname or ""
    if parts.netloc:
        default_port = 80 if parts.scheme == "http" else 443
        if domain not in OUR_DOMAINS or parts.port not in (None, default_port):
            return "external", domain, parts.path, unquote(parts.fragment)

    # Opløs kun stien her. Værten er allerede klassificeret, og absolutte
    # adresser uden sti peger på det pågældende domænes forside.
    base = "/" if parts.netloc else source_route
    path = parts.path
    if path.startswith("/"):
        base, path = "/", "." + path
    path = urljoin(base, path)
    return "cross" if domain else "local", domain, path, unquote(parts.fragment)


# `#url=https%3A%2F%2F…` er ikke et anker, men en parameter siden læser af
# location.hash. Fragmentet skal ligne en nøgle-til-værdi, ellers er det et id.
HASH_PARAM = re.compile(r"^[A-Za-z_][\w.-]*=")


def resolve_page(dist: Path, path: str) -> Path | None:
    """Hvilken fil i distet svarer ruten /path til? None hvis ingen."""
    clean = path.rstrip("/")
    if any(clean == d or clean.startswith(d + "/") for d in DECLARED):
        return None
    if not clean or clean == "/":
        return dist / "index.html" if (dist / "index.html").is_file() else None
    for cand in (clean.lstrip("/"), clean.lstrip("/") + ".html", clean.lstrip("/") + "/index.html"):
        target = dist / cand
        if target.is_file():
            return target
    return None


def route_exists(domain_dist: Path, path: str) -> bool:
    """Findes ruten i et dist? Ren sti, mappe med index.html, eller deklareret rute."""
    clean = path.rstrip("/")
    if any(clean == d or clean.startswith(d + "/") for d in DECLARED):
        return True
    if path == CLOUDFLARE_EMAIL_ROUTE or clean.startswith(WORKER_PREFIXES):
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


_ANCHORS: dict[Path, tuple[set[str], bool]] = {}


def page_anchors(path: Path) -> tuple[set[str], bool]:
    """(id'er + <a name>, læser siden location.hash?) for én fil, cachelagret."""
    hit = _ANCHORS.get(path)
    if hit is not None:
        return hit
    parser = RefParser(path.name)
    try:
        parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
        parser.close()
    except Exception:  # noqa: BLE001 - en ugyldig fil må ikke slå porten fra
        parser.ids = set()
    hit = (parser.ids, parser.reads_hash)
    _ANCHORS[path] = hit
    return hit


def anchor_problem(domain: str, rel: str, line: int, ref: str, own: Path,
                   dist: Path, dists: dict[str, Path], own_ids: set[str],
                   own_reads_hash: bool = False) -> str | None:
    """Én fejltekst hvis fragmentet i ref ikke findes, ellers None."""
    kind, ref_domain, ref_path, frag = split_target(ref, canonical_url(rel))
    if not frag or kind in ("skip", "external"):
        return None
    if kind == "same":
        # Samme fil: brug de id'er vi netop har parset. At læse filen igen
        # ville give en cache, der er forældet i selftesten, hvor probe.html
        # skrives om mellem hver kørsel.
        #
        # `reads_hash` kommer fra **samme** parser, der fandt `ids` — målt 5/10:
        # den blev sat til False, fordi et hash-fragment er sjældent et anker i
        # den fil det står i. Men eksempel-kortet på `/scan` (5/10) linker netop
        # til `#url=…` i sin egen side, så porten råbte døde `#url=`-links
        # som om siden ikke læste sin egen hash. Den gjorde — den gør.
        ids, reads_hash = own_ids, own_reads_hash
        target = own
    else:
        target_dist = dists.get(ref_domain) if ref_domain else dist
        if target_dist is None:
            return None
        target = resolve_page(target_dist, ref_path)
        if target is None:
            return None  # deklareret rute eller worker: ingen fil at slå ids op i
        ids, reads_hash = page_anchors(target)
    if HASH_PARAM.match(frag):
        # En hash-parameter skal læses af den side, den peger på — ellers er
        # den bare en død reference forklædt som en.
        if not reads_hash:
            return (f"{domain}: {rel}:{line}: {ref!r} — siden læser ikke sin egen "
                    f"location.hash, så #{frag} virker ikke")
        return None
    if frag in ids:
        return None
    try:
        where = target.relative_to(DIST).as_posix()
    except ValueError:  # selftesten kører på et midlertidigt dist
        where = target.name
    return f"{domain}: {rel}:{line}: ankeret {ref!r} findes ikke i {where}"


_CANONICALS: dict[Path, str | None] = {}
_LINK_TAG_RE = re.compile(r"<link\b[^>]*>", re.I)
_HREF_ATTR_RE = re.compile(r"""\bhref=["']([^"']+)["']""", re.I)


def norm_route(path: str) -> str:
    """Ruten uden afsluttende skråstreg, med undtagelse af rodens `/`."""
    return path.rstrip("/") or "/"


def page_canonical(path: Path) -> str | None:
    """Sidens egen `<link rel="canonical">`, cachelagret pr. fil."""
    if path in _CANONICALS:
        return _CANONICALS[path]
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        _CANONICALS[path] = None
        return None
    canon = None
    for m in _LINK_TAG_RE.finditer(text[:40000]):
        tag = m.group(0)
        if "canonical" not in tag.lower():
            continue
        h = _HREF_ATTR_RE.search(tag)
        if h:
            canon = h.group(1).strip()
            break
    _CANONICALS[path] = canon
    return canon


def duplicate_problem(source: str, rel: str, line: int, ref: str,
                      target: Path, target_dist: Path) -> str | None:
    """Én fejltekst hvis linket peger på en dublet, ellers None.

    En side der ligger på to ruter — eller på én rute med en canonical der
    peger et andet sted — er ikke død, så `route_exists` lader den passere.
    Men *alle* links vi skriver til den, sender linkværdi til en URL
    søgemaskinerne kasserer. Målt 27/9: cleancopy.tools udgiver forsiden fra
    `site/clean-copy.html`, så `/clean-copy` var 159 links værd (53 interne,
    106 krydsdomæne) på en byte-identisk dublet med canonical `/`.
    """
    canon = page_canonical(target)
    if not canon:
        return None  # ingen canonical at være uenig med
    parts = urlsplit(canon)
    netloc = parts.netloc.lower()
    if netloc and netloc not in OUR_DOMAINS:
        return None  # canonical peger uden for familien: ikke vores at dømme
    if netloc and netloc != target_dist.name:
        return None  # flyttet et andet sted hen i familien: ikke en dublet her
    try:
        own_route = canonical_url(target.relative_to(target_dist).as_posix())
    except ValueError:  # selftesten kører på et midlertidigt dist
        return None
    if norm_route(parts.path) != norm_route(own_route):
        return f"{source}: {rel}:{line}: {ref!r} peger på en dublet — {canon} er den kanoniske"
    return None


def check_domain(domain: str, dist: Path, dists: dict[str, Path], check_downloads: bool,
                 *, check_fragments: bool = True) -> list[str]:
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
            kind, ref_domain, ref_path, _ = split_target(ref, canonical_url(rel))
            if kind in ("skip", "external", "same"):
                continue

            def flag_dup(target: Path, target_dist: Path) -> None:
                bad = duplicate_problem(domain, rel, line, ref, target, target_dist)
                if bad:
                    problems.append(bad)

            if ref_domain and ref_domain != domain:
                # Kun domæner vi ejer *og* som faktisk er bygget i dette job.
                other = dists.get(ref_domain)
                if other is None:
                    continue
                if not route_exists(other, ref_path):
                    problems.append(
                        f"{domain}: {rel}:{line}: krydsdomæne-reference {ref!r} findes ikke i {ref_domain}")
                    continue
                page = resolve_page(other, ref_path)
                if page is not None:
                    flag_dup(page, other)
                continue
            if not route_exists(dist, ref_path):
                problems.append(f"{domain}: {rel}:{line}: {ref!r} findes ikke i distet")
                continue
            page = resolve_page(dist, ref_path)
            if page is not None:
                flag_dup(page, dist)
        if check_fragments:
            for ref, line in parser.anchors:
                bad = anchor_problem(domain, rel, line, ref, path, dist, dists,
                                     parser.ids, parser.reads_hash)
                if bad:
                    problems.append(bad)
    if check_downloads:
        for ref, rel in downloads:
            kind, ref_domain, ref_path, _ = split_target(ref, canonical_url(rel))
            if kind in ("skip", "external"):
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
        kind, ref_domain, ref_path, _ = split_target(action, canonical_url(rel))
        if kind in ("skip", "external"):
            continue
        target_dist = dists.get(ref_domain) if ref_domain else dist
        if target_dist is not None and not route_exists(target_dist, ref_path) \
                and not any(m in action for m in LEAD_MARKERS):
            problems.append(f"{domain}: {rel}: formular-peger på {action!r}, som ikke findes")
    return problems


def check(only: str | None = None, *, check_fragments: bool = True) -> tuple[int, list[str]]:
    _ANCHORS.clear()
    _CANONICALS.clear()
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
        found = check_domain(domain, dist, built_domains(), check_downloads=True,
                             check_fragments=check_fragments)
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
        (d / "findes.html").write_text(
            '<!doctype html><html><body><main id="main" id="platforms"><h2 id="her">ja</h2>'
            '<script>var u = location.hash.replace("#url=", "");</script>'
            "</main></body></html>", encoding="utf-8")
        (d / "findes2.html").write_text(
            '<!doctype html><html><body><h2 id="her">ja</h2></body></html>', encoding="utf-8")
        # Til `duplicate_problem`: en side med *rigtig* canonical, en dublet der
        # erklærer en anden rute som sin, og en side slet uden canonical.
        (d / "korrekt.html").write_text(
            f'<!doctype html><html><head><link rel="canonical" '
            f'href="https://{domain}/korrekt"></head><body>ok</body></html>', encoding="utf-8")
        (d / "dublet.html").write_text(
            f'<!doctype html><html><head><link rel="canonical" '
            f'href="https://{domain}/"></head><body>byte-identisk</body></html>', encoding="utf-8")
        (d / "uden-canonical.html").write_text(
            '<!doctype html><html><body>ingen canonical</body></html>', encoding="utf-8")
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

        def run(snippet: str, dist_map: dict[str, Path] | None = None, **options):
            probe.write_text(f"<!doctype html><body>{snippet}</body>", encoding="utf-8")
            return check_domain(main_domain, main_dist, dist_map or dists, True, **options)

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
        expect("død protokolrelativ href", '<a href="//cleancopy.tools/udenfor">x</a>', "udenfor")
        expect("aktivt link i kodeblok", '<pre><code><a href="/...">x</a></code></pre>', "/...")
        expect_clean("side med query og fragment", '<a href="findes?ref=test#her">x</a>')
        expect_clean("Cloudflares mailbeskyttelse",
                     '<a href="/cdn-cgi/l/email-protection#123">mail</a>')
        expect("standardport på eget domæne",
               '<a href="https://mahope.tools:443/dead">x</a>', "/dead")
        expect_clean("levende link med standardport", '<a href="//cleancopy.tools:443/findes">x</a>')
        expect_clean("anden port er ekstern", '<a href="https://mahope.tools:8443/dead">x</a>')
        (main_dist.parent / "outside.html").write_text("<p>uden for sitet</p>", encoding="utf-8")
        expect("relativt link må ikke bruge nabofiler", '<a href="../outside">x</a>', "../outside")
        expect_clean("relativt link normaliseres ved domænets rod", '<a href="../findes">x</a>')
        expect("ukendt rute nær Cloudflares mailbeskyttelse",
               '<a href="/cdn-cgi/l/email-protection-missing">x</a>', "email-protection-missing")
        if run('<a href="#missing">x</a><a href="/findes#missing">y</a>', check_fragments=False):
            print("FEJL: sidetjekket må ignorere fragmenter", file=sys.stderr)
            ok = False
        if not run('<a href="/dead#missing">x</a>', check_fragments=False):
            print("FEJL: sidetjekket skal stadig finde en død sti med fragment", file=sys.stderr)
            ok = False
        expect("død href", '<a href="/findes-ikke">x</a>', "/findes-ikke")
        expect("død asset", '<img src="/logo.png">', "/logo.png")
        expect("død stylesheet", '<link rel="stylesheet" href="/mangler.css">', "/mangler.css")
        expect("død form-action", '<form action="/findes-ikke"></form>', "/findes-ikke")
        expect("død download", '<a href="/downloads/mangler.zip">x</a>', "/downloads/mangler.zip")
        expect("krydsdomæne 404", '<a href="https://cleancopy.tools/udenfor">x</a>', "udenfor")
        expect("død iframe", '<iframe src="/indlejret"></iframe>', "/indlejret")

        # 1a. Dubletter. En dublet er ikke død, så `route_exists` lader den
        #     passere; men et link til den sender al linkværdi til en URL
        #     søgemaskinerne kasserer. Målt 27/9 på cleancopy.tools: 159 links
        #     på `/clean-copy`, en byte-identisk dublet af `/`.
        expect("link på en dublet", '<a href="/dublet">x</a>', "peger på en dublet")
        expect("krydsdomænelink på en dublet",
               '<a href="https://cleancopy.tools/dublet">x</a>', "peger på en dublet")
        expect("relativ reference på en dublet", '<a href="dublet.html">x</a>', "peger på en dublet")
        # Negativkontroller — uden dem kunne reglen bare forbyde at linke nogen
        # side med en canonical, og porten ville være grøn mod præcis den
        # fejl den skal fange.
        expect_clean("link på en side med rigtig canonical", '<a href="/korrekt">x</a>')
        expect_clean("krydsdomænelink med rigtig canonical",
                     '<a href="https://cleancopy.tools/korrekt">x</a>')
        expect_clean("side uden canonical", '<a href="/uden-canonical">x</a>')
        expect_clean("kodeeksempel med dublet", '<pre><code>&lt;a href="/dublet"&gt;</code></pre>')

        # 1b. Ankere. Før denne port tabte split_ref() fragmentet, så 199
        #     krydsside-ankere blev aldrig set — opgave 43.
        expect("dødt same-page-fragment", '<a href="#findes-ikke">x</a>', "#findes-ikke")
        expect("dødt krydsside-fragment", '<a href="/findes#mangler">x</a>', "#mangler")
        expect("dødt krydsdomæne-fragment", '<a href="https://cleancopy.tools/findes#mangler">x</a>', "#mangler")
        expect("dødt relativt fragment", '<a href="findes2.html#mangler">x</a>', "#mangler")
        expect("død hash-parameter", '<a href="/findes2.html#url=x">x</a>', "læser ikke sin egen")
        # 1b-2. Samme fejlform på **egen** side. Målt 5/10: eksempel-kortet på
        #       `/scan` linker til `#url=…` i den side det står på, og porten
        #       satte `reads_hash = False` for alle same-page-fragmenter, så den
        #       råbte to døde links som om siden ikke læste sin egen hash. Den
        #       gjorde — og uden disse to linjer ville portens rettelse være
        #       ubevisst, fordi ingen mutation ville kunne se den.
        expect("død hash-parameter på egen side", '<a href="#url=x">x</a>', "læser ikke sin egen")

        # 1c. Falsk-positive-kontroller. `#main` SKAL være grønt selv om
        #     <main> bærer to id'er: browseren bruger den første, så et
        #     "fix" på porten ville have hængt et levende skip-link. Det er
        #     præcis markup fra site/guides/platforms.html.
        expect_clean("levende same-page-fragment", '<h2 id="her"></h2><a href="#her">x</a>')
        expect_clean("duplikat-id: browseren tager den første",
                     '<main id="main" id="platforms"></main><a href="#main">x</a>')
        expect_clean("levende krydsside-fragment", '<a href="/findes#her">x</a>')
        expect_clean("levende krydsdomæne-fragment", '<a href="https://cleancopy.tools/findes#her">x</a>')
        expect_clean("hash-parameter læst af siden", '<a href="/findes#url=https%3A%2F%2Fx.dk">x</a>')
        expect_clean("hash-parameter på egen side læst af siden",
                     '<script>var u = location.hash;</script><a href="#url=https%3A%2F%2Fx.dk">x</a>')
        expect_clean("tomt fragment", '<a href="/findes#">x</a>')
        expect_clean("fragment på deklareret rute", '<a href="/thanks#mangler">x</a>')
        expect_clean("prose er ikke et link", '<p>brug /#products i din tekst</p>')
        expect_clean("kodeeksempel med fragment", '<pre><code>&lt;a href="/findes#mangler"&gt;</code></pre>')

        # 2. Kodeeksempler må ALDRIG fejle, uanset hvor døde de ser ud.
        for snippet in ('<pre><code>npm i /downloads/dod.zip</code></pre>',
                        '<code>&lt;img src="/img/cover.jpg"&gt;</code>',
                        '<script>var u="/api/nej";</script>',
                        '<style>.a{background:url(/img/dod.png)}</style>'):
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
    ap.add_argument("--skip-fragments", action="store_true", help="kontrollér stier uden at validere ankre")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    n, problems = check(args.only, check_fragments=not args.skip_fragments)
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
