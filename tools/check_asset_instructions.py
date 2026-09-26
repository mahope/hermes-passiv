#!/usr/bin/env python3
"""Dom over filer der loades i koden, i publiceret tekst.

Baggrund (opgave 88 + denne iteration): `check_install_commands.py` dømmer
*pakkeregistre* — `pip install x`, `npx y`, `brew install z`. Den fejlform der
blev stående er den anden slags: kommandoer der henter eller importerer en
**fil**. Opgave 88 fandt den som `cd desktop` efter `unzip
eaa-scanner-desktop-src-1.3.4.zip` — arkivet har 11 filer i roden og nul
mapper, så kommandoen fejler med `cd: no such file or directory` lige efter
download. Det er ikke et pakkeregister, så den eksisterende port så den ikke.

Denne port dømmer derfor fire ting, alle målt på **det publicerede output** i
`dist/`, altså den fil kunden faktisk henter:

  1. `curl -O <url>` / `wget <url>` — skal pege på en fil der findes i det
     publicerede dist for det domæne, kommandoen står i.
  2. `unzip <arkiv>` / `tar -xzf <arkiv>` — arkivet skal findes i dist, eller
     stå i `GENERIC` med en begrundelse (et kundens eget `product.zip` i en
     blogartikel er ikke vores arkiv).
  3. `cd <mappe>` i samme kodeblok som en `unzip` af **vores** arkiv — mappen
     skal findes *inde i* arkivet. Det er den fejlform opgave 88 fandt, målt på
     den udpakket fil i stedet for på arkivets navn.
  4. `import <mod>` / `from <mod> import …` i kodekontekst, hvor `<mod>` ikke er
     stdlib — skal enten være en pakke vi selv udgiver (`OUR_PACKAGES`) eller
     samme blok skal have en `pip install <mod>`. Denne regel fandt den
     publicerede fejl: to API-README'er viste `import requests` uden at nogen
     kunne køre den, fordi `requests` ikke er stdlib.

Hvorfor `dist/` og ikke `site/`: opgave 88 fund 2 kom fra at måle på det
publicerede arkiv, ikke på kilden. Og `check_links.py` springer `pre`/`code`
over med vilje — det er rigtigt for markup-eksempler (`<img src="/img/x.jpg">`
er en illustration, ikke et krav), men det er præcis der de her kommandoer
ligger. Derfor er det en separat port frem for en udvidelse af den.

Kør:  python3 tools/check_asset_instructions.py [--self-test]
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

# Domæner vi selv ejer. En reference til et af dem findes i *dets* dist.
OUR_DOMAINS = ("mahope.tools", "cleancopy.tools", "deskuptime.com", "bugbottle.dev")
# Byg-værten. Kilden skriver den, og byggen skriver den om — porten skal kende
# begge, ellers dømmer den kildens URL'er som fremmede og springer dem over.
BUILD_HOSTS = ("hermes-passiv.pages.dev",)

# Pakker vi selv udgiver, verificeret ved at pakke ud i et zip den kunde henter.
OUR_PACKAGES = {
    "eaa_scanner": "eaa_scanner-1.2.0-py3-none-any.whl, __init__ eksporterer scan_html, scan_url, contrast_ratio",
}

# Arkiver der nævnes i en kommando uden at være vores. Hver linje skal have en
# begrundelse, så listen ikke bliver en loppe der dækker alt.
GENERIC = {
    "product.zip": "blogartiklen 'test your zip before release' — kommandoen køres mod kundens eget arkiv",
    "produkt.zip": "samme artikel på dansk",
}

STDLIB = set(getattr(sys, "stdlib_module_names", ())) | {
    "__future__", "collections", "pathlib", "typing", "dataclasses", "urllib",
    "json", "re", "sys", "os", "io", "zipfile", "html", "socket", "ssl",
}

TEXT_SUFFIXES = {".html", ".md", ".txt"}

CURL = re.compile(
    r"\b(?:curl\s+(?:-[A-Za-z-]+\s+)*-O[A-Za-z]*\s*|wget\s+(?:-\S+\s+)*)"
    r"(https?://[^\s`\"'<>]+|/[^\s`\"'<>]+)"
)
UNZIP = re.compile(r"\b(?:unzip|tar\s+-[a-z]*x[a-z]*f)\s+(?:-\S+\s+)*([A-Za-z0-9._-]+\.(?:zip|tar\.gz|tgz))")
CD = re.compile(r"^[^\n]*\bcd\s+([A-Za-z0-9._-]+)\s*$", re.M)
# En import kan staa pa sin egen linje eller lige efter <pre><code> — de
# publicerede sider har begge, og kun den foelgende version, der tillader
# en aabningstag foran, finder dem alle.
IMPORT = re.compile(
    r"^[ \t]*(?:<[^>\n]+>[ \t]*)*"
    r"(?:import\s+([A-Za-z_][\w.]*)|from\s+([A-Za-z_][\w.]*)\s+import\b)",
    re.M,
)
PIP = re.compile(r"\bpip3?\s+install\s+(?:--?[\w-]+\s+)*([A-Za-z0-9][\w.\-]*)")


def code_spans(text: str) -> list[tuple[int, int]]:
    """Start-og-slut for hver kodekontekst, som i check_install_commands.py."""
    spans: list[tuple[int, int]] = []
    for pat, flags in (
        (r"<pre\b[^>]*>.*?</pre>", re.S | re.I),
        (r"<code\b[^>]*>.*?</code>", re.S | re.I),
        (r"```.*?```", re.S),
        (r"`[^`\n]+`", 0),
    ):
        for m in re.finditer(pat, text, flags):
            spans.append((m.start(), m.end()))
    return spans


def _host_of(url: str) -> str:
    return urlsplit(url).netloc if url.startswith("http") else ""


def _path_of(url: str) -> str:
    return unquote(urlsplit(url).path if url.startswith("http") else url)


def _own_domain(host: str) -> str | None:
    for d in OUR_DOMAINS:
        if host == d or host.endswith("." + d):
            return d
    return None


def dist_index() -> dict[str, set[str]]:
    """Relativ sti -> domæne, for alt der ligger i dist. Én fejlbetalt indeksering."""
    index: dict[str, set[str]] = {}
    if not DIST.is_dir():
        return index
    for p in DIST.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(DIST).as_posix()
        dom = rel.split("/", 1)[0]
        rest = rel[len(dom) :].lstrip("/")
        index.setdefault(rest, set()).add(dom)
    return index


def zip_top_folders(path: Path) -> set[str]:
    """Mapperne i roden af et arkiv.

    En zip-mappe er **aldrig** sit eget element i `namelist()`: en mappe
    `pakke/` med to filer giver `pakke/a.php` og `pakke/b/c.php`, ikke `pakke`.
    Så et `cd pakke` skal dømmes mod disse rødder, ikke mod hele navnelisten —
    ellers er *enhver* rigtig mappe falsk rød, og det var præcis fejlen der holdt
    CI rød 27/9 (M10).
    """
    with zipfile.ZipFile(path) as zf:
        return {n.split("/", 1)[0] for n in zf.namelist() if "/" in n}


def zip_folder_index(index: dict[str, set[str]]) -> dict[str, set[str]]:
    """Arkivnavn -> mapper i roden, læst fra den rigtige fil.

    Nøglen er arkivets navn alene, for det er sådan kommandoen skriver det. To
    domæner kan have samme filnavn, og da forenes mapperne: det er den
    konservative retning, for en falsk rød fejl rammer kunden mens en
    manglende mappe kun er en mistet fejl.
    """
    out: dict[str, set[str]] = {}
    for name, domaener in index.items():
        if not name.endswith(".zip"):
            continue
        for dom in sorted(domaener):
            p = DIST / dom / name
            if p.is_file() and zipfile.is_zipfile(p):
                out.setdefault(name, set()).update(zip_top_folders(p))
                break
    return out


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def check_text(
    text: str,
    label: str,
    dom: str,
    index: dict[str, set[str]],
    zip_folders: dict[str, set[str]] | None = None,
) -> list[str]:
    spans = code_spans(text)
    if not spans:
        return []
    problems: list[str] = []
    if zip_folders is None:
        zip_folders = zip_folder_index(index)

    def in_code(offset: int) -> bool:
        return any(a <= offset < b for a, b in spans)

    def block_of(offset: int) -> tuple[int, int]:
        for a, b in spans:
            if a <= offset < b:
                return a, b
        return offset, offset

    for m in CURL.finditer(text):
        if not in_code(m.start()):
            continue
        url = re.split(r"[<\n]", m.group(1))[0].strip("`'\"&;,")
        host, path = _host_of(url), _path_of(url)
        if host and not any(h in host for h in BUILD_HOSTS) and not _own_domain(host):
            continue  # fremmed vært — vores ansvar
        target = dom if host else dom
        names = index.get(path.lstrip("/"))
        if not names:
            problems.append(
                f"{label}:{line_of(text, m.start())}: kommandoen henter {url}, "
                f"men den fil findes ikke i det publicerede output"
            )
        elif host and _own_domain(host) != target:
            problems.append(
                f"{label}:{line_of(text, m.start())}: {url} ligger i "
                f"{'/'.join(sorted(names))}, ikke i {target}"
            )

    for m in UNZIP.finditer(text):
        if not in_code(m.start()):
            continue
        name = m.group(1)
        if name in GENERIC or not any(n.endswith(name) for n in index):
            continue
        lo, hi = block_of(m.start())
        cd = CD.search(text[lo:hi])
        if not cd:
            continue
        folder = cd.group(1)
        if folder not in zip_folders.get(name, set()):
            problems.append(
                f"{label}:{line_of(text, m.start())}: `cd {folder}` efter "
                f"`{name}` — arkivet har ingen mappe med det navn"
            )

    for m in IMPORT.finditer(text):
        if not in_code(m.start()):
            continue
        mod = (m.group(1) or m.group(2) or "").split(".")[0]
        if not mod or mod in STDLIB or mod in OUR_PACKAGES:
            continue
        lo, hi = block_of(m.start())
        if any(p == mod for p in PIP.findall(text[lo:hi])):
            continue
        if PIP.search(text):
            continue  # samme fil har en pip-linje et andet sted
        problems.append(
            f"{label}:{line_of(text, m.start())}: `import {mod}` uden en "
            f"`pip install {mod}` — kunden kopierer blokken og får ModuleNotFoundError"
        )
    return problems


def iter_files() -> list[tuple[Path, str]]:
    out: list[tuple[Path, str]] = []
    if not DIST.is_dir():
        return out
    for p in sorted(DIST.rglob("*")):
        if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES:
            dom = p.relative_to(DIST).parts[0]
            if dom in OUR_DOMAINS:
                out.append((p, dom))
    return out


def check_dist() -> tuple[list[str], int]:
    index = dist_index()
    zip_folders = zip_folder_index(index)
    problems: list[str] = []
    for p, dom in iter_files():
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = p.relative_to(DIST).as_posix()
        problems.extend(check_text(text, rel, dom, index, zip_folders))
    return problems, len(iter_files())


def self_test() -> int:
    """Mutationer i det publicerede output. Tæler fund, ikke bare et grønt flag."""
    from tempfile import TemporaryDirectory

    src_name = "mahope.tools/blog/canonical-url-guide.html"
    src_file = DIST / src_name
    if not src_file.is_file():
        print(f"FEJL selftest: {src_name} findes ikke — kør `python3 build_sites.py` først")
        return 1
    index = dist_index()
    cases: list[tuple[str, str, int, str, bool]] = [
        ("M1 curl -O på en fil der ikke findes", 'curl -O https://mahope.tools/downloads/ghost.py', 1, "ghost.py", False),
        ("M2 curl -O på en publiceret fil er grøn", 'curl -O https://mahope.tools/downloads/eaa-scanner-desktop-src-1.3.4.zip', 0, "", False),
        ("M3 curl i prosa er ikke en kommando", 'curl -O https://mahope.tools/downloads/ghost.py', 0, "", True),
        ("M4 unzip af kundens eget zip er grøn", "unzip product.zip -d /tmp/x", 0, "", False),
        ("M5 import af en tredjepartspakke uden pip-linje", "import requests\nprint(requests)", 1, "requests", False),
        ("M6 samme blok med pip install er grøn", "pip install requests\nimport requests", 0, "", False),
        ("M7 import af stdlib er grøn", "import json\nfrom pathlib import Path", 0, "", False),
        ("M8 import af vores egen pakke er grøn", "from eaa_scanner import scan_url, scan_html", 0, "", False),
    ]
    # Byggen skriver `<pre><code>` om til `<pre class="cmd">`, så ankeret her er
    # dist-udgaven — kildeankeret ville bare ikke findes, og selftesten ville være
    # grøn uden at have indsat noget. Derfor kontrolleres injektionen eksplicit.
    ANKER = '<pre class="cmd">'

    def muter(injektion: str, prosa: bool = False) -> str:
        """Sætter kommandoen ind i den publicerede fil. prosa=True sætter den i en
        afsnit, så porten skal *ikke* dømme den — kodekontekst er et krav."""
        original = src_file.read_text(encoding="utf-8")
        tekst = original.replace(
            "<p>" if prosa else ANKER,
            f"<p>{injektion} " if prosa else f"{ANKER}\n{injektion}\n",
            1,
        )
        if tekst == original:
            raise AssertionError(f"selftest-ankeret {ANKER!r} findes ikke i {src_name}")
        if injektion not in tekst:
            raise AssertionError(f"injektionen kom ikke ind i {src_name}")
        return tekst

    fejl = 0
    for navn, injektion, forventet, skal_nævnes, prosa in cases:
        fund = [
            f
            for f in check_text(muter(injektion, prosa), "selftest", "mahope.tools", index)
            if "selftest" in f
        ]
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

    # M9-M11: `cd` efter `unzip` af **vores** arkiv. Måles mod et syntetisk
    # arkiv, ikke mod et arkiv fra dist: den forrige udgave tog det første zip
    # `dist_index()` gav, og den rækkefølge er filsystemets. Lokalt var det et
    # arkiv uden mapper, så M10 aldrig kørte — og blev alligevel talt med i
    # totalen, som derfor sagde 10/10 mens der var 9 mutationer. I CI ramte den
    # et arkiv med en mappe, og så løb M10 og fandt fejlen. Fixture'en er derfor
    # hermetisk nu, og en manglende fixture er en hård fejl, ikke et spring.
    with TemporaryDirectory() as tmp:
        fixture = Path(tmp) / "cd-regel-fixture.zip"
        with zipfile.ZipFile(fixture, "w") as zf:
            zf.writestr("pakke-mappe/fil.php", "<?php // test")
            zf.writestr("pakke-mappe/under/anden.php", "<?php // test")
            zf.writestr("rodfil.txt", "test")
        if not fixture.is_file():
            print("FEJL M9: kunne ikke skrive fixture-arkivet")
            return 1
        fund_fixture = zip_top_folders(fixture)
        if fund_fixture != {"pakke-mappe"}:
            print(f"FEJL M9: fixture-arkivet har uventede mapper {sorted(fund_fixture)}")
            return 1

        test_index = dict(index)
        test_index["downloads/cd-regel-fixture.zip"] = {"mahope.tools"}
        # Fixture'en ligger i en temp-mappe, så `zip_folder_index` — som læser
        # under dist — kan ikke finde den. Derfor føjes den til med den værdi
        # `zip_top_folders` netop har læst *ud af den rigtige fil*, så
        # mappeudtrækket stadig er prøvet mod et ægte arkiv.
        test_folders = dict(zip_folder_index(test_index))
        test_folders["cd-regel-fixture.zip"] = fund_fixture

        # Og den virkelige mappeindeksering skal se den mappe CI snublede over:
        # `eaa-compliance-scanner.zip` har `eaa-compliance-scanner/` i roden.
        rigtig = zip_folder_index(index).get("eaa-compliance-scanner.zip")
        if rigtig != {"eaa-compliance-scanner"}:
            print(f"FEJL M10: eaa-compliance-scanner.zip har uventede mapper {sorted(rigtig or [])}")
            return 1
        print("ok   M10a det publicerede arkiv har sin mappe i mappeindekset")

        def dom(folder: str) -> list[str]:
            tekst = muter(f"unzip cd-regel-fixture.zip && cd {folder}")
            return [
                f
                for f in check_text(tekst, "selftest", "mahope.tools", test_index, test_folders)
                if f"cd {folder}" in f
            ]

        fund = dom("desktop")
        if len(fund) != 1:
            print(f"FEJL M9 cd ind i en mappe arkivet ikke har: forventede 1 fund, fik {len(fund)}")
            fejl += 1
        else:
            print("ok   M9 cd ind i en mappe arkivet ikke har (1 fund)")

        fund2 = dom("pakke-mappe")
        if fund2:
            print("FEJL M10 mappe der findes i arkivet (pakke-mappe) er dømt rød")
            for f in fund2:
                print(f"     {f}")
            fejl += 1
        else:
            print("ok   M10 mappe der findes i arkivet (pakke-mappe) er grøn (0 fund)")

        fund3 = dom("rodfil")
        if len(fund3) != 1:
            print(f"FEJL M11 cd ind i en fil der ikke er en mappe: forventede 1 fund, fik {len(fund3)}")
            fejl += 1
        else:
            print("ok   M11 cd ind i en fil der ikke er en mappe (1 fund)")

    # Tæl kun mutationer der faktisk kørte. Et spring må aldrig tælle som grønt.
    total = len(cases) + 4
    print(f"selftest: {total - fejl}/{total} mutationer fanget")
    return 1 if fejl else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not DIST.is_dir():
        print("SPRUNGET OVER: dist/ findes ikke — kør `python3 build_sites.py`")
        return 0
    problems, filer = check_dist()
    for p in problems:
        print(p)
    if problems:
        print(f"\nfil-Instruktioner: {len(problems)} fejl i {filer} publicerede filer")
        return 1
    print(f"fil-Instruktioner: OK — 0 fejl i {filer} publicerede filer")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
