#!/usr/bin/env python3
"""Gate for Page Profiles publicerede kopi: den skal være den kanoniske kode.

Opgave 6 i `IMPLEMENTATION_PLAN.md`. Opgave 4E (`ea4e6c3`) rettede selve
licensen, men `site/downloads/page-profile/` er en manuelt kopieret udgave af
`page-profile/`, og intet holdt de to sammen. En divergerende kopi er en
købsfejl: køberen får en CLI der afviser sin egen Stripe-nøgle, eller en
downloadside der lover en udgave, der ikke kan downloades.

Gaten fejler ved:

1. Den kanoniske kode mangler en fil, eller `pyproject.toml` og `__version__`
   ikke er samme udgave.
2. Den publicerede `page_profile.py` mangler eller afviger fra den kanoniske kode.
3. Der mangler præcis ét source-arkiv, eller dets navn og rodmappe afviger fra
   versionen, eller en kildefil i det afviger fra den kanoniske kode.
4. EN/DA-siderne linker på et arkiv eller viser en udgave, der ikke findes.
5. `dist/`-kopien afviger fra den kanoniske kode (springes over, hvis intet er bygget).
6. EN/DA-siderne har igen en offline-påstand om licensen, eller mangler den
   online-aktivering og syvdages cache ved serverfejl.

    python3 tools/check_page_profile_distribution.py
    python3 tools/check_page_profile_distribution.py --self-test

Udgivelse af en ny udgave (gaten er bygget til at blive grøn, når alle seks skridt
er gjort — den kan ikke glemme et af dem):

    1. Sæt `version` i `page-profile/pyproject.toml` og `__version__` i
       `page-profile/page_profile.py` til den nye udgave.
    2. `python3 -m build --sdist --outdir /tmp/pp page-profile`
    3. `cp /tmp/pp/page_profile-<udgave>.tar.gz \\
          site/downloads/page-profile/page-profile-<udgave>.tar.gz`
       (setuptools døber arkivet med bindestreg; filen publiceres med bindestreg
       i arkivnavnet og som navnet på `/downloads/page-profile/`, fordi det er det
       download-linket peger på.)
    4. `cp page-profile/page_profile.py site/downloads/page-profile/page_profile.py`
    5. Sæt udgaven og `cd`-mappen på `site/page-profile.html` og
       `site/da/page-profile.html`, og slet det gamle arkiv.
    6. Kør gaten. Den grønne gate er beviset på, at alle kopier stammer fra
       den samme kode.
"""
from __future__ import annotations

import argparse
import re
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "page-profile"
PUBLISHED = ROOT / "site/downloads/page-profile"
DIST_COPY = ROOT / "dist/mahope.tools/downloads/page-profile"
PAGES = {
    "site/page-profile.html": ROOT / "site/page-profile.html",
    "site/da/page-profile.html": ROOT / "site/da/page-profile.html",
}
DA_PAGES = {"site/da/page-profile.html"}

# Filer der skal være byte-identiske mellem den kanoniske kode, den publicerede
# kopi og source-arkivet. `pyproject.toml` og `README.md` er med, fordi en
# version, der kun opdateres i ét sted, giver en side der lyder om en gammel udgave.
CANON_FILES = ("page_profile.py", "cli.py", "README.md", "pyproject.toml")
COPIES = ("page_profile.py",)

PYPROJECT_VERSION = re.compile(r'^\s*version\s*=\s*"([^"]+)"', re.MULTILINE)
CODE_VERSION = re.compile(r'^__version__\s*=\s*"([^"]+)"', re.MULTILINE)
VERSION_TOKEN = r"[0-9][0-9A-Za-z.+-]*"
SDIST_NAME = re.compile(rf"^page-profile-({VERSION_TOKEN})\.tar\.gz$")
ARCHIVE_REF = re.compile(rf"page-profile-({VERSION_TOKEN})\.tar\.gz")
SHOWN_VERSION = re.compile(rf"page-profile v({VERSION_TOKEN})")
CD_DIR = re.compile(r"\bcd\s+([A-Za-z0-9._-]+)")

# Offline-påstande om licensen. Kun formuleringer der entydigt handler om
# licensen — ikke "no pip install", som stadig er sandt for gratisudgaven.
FORBIDDEN_CLAIMS = {
    "licensen virker helt offline": r"helt offline",
    "licensen kræver ingen internetforbindelse": r"kræver ingen internetforbindelse",
    "licensen aktiveres offline": r"aktiveres offline",
    "licenstjekket kontakter aldrig": r"licenstjek[^.]{0,40}aldrig",
    "license works offline": r"licen[cs]e works offline",
    "license requires no internet connection": r"licen[cs]e requires no internet",
    "activates offline": r"activates offline",
    "license check never contacts": r"licen[cs]e check[^.]{0,40}never",
}
FORBIDDEN = {label: re.compile(needle) for label, needle in FORBIDDEN_CLAIMS.items()}

# Hvad siden skal sige, for at Pro-licensen er beskrevet sandt.
REQUIRED_CLAIMS = {
    "online aktivering": (re.compile(r"online activation", re.IGNORECASE),
                         re.compile(r"online aktivering", re.IGNORECASE)),
    "syvdages cache ved serverfejl": (re.compile(r"seven days", re.IGNORECASE),
                                      re.compile(r"syv dage", re.IGNORECASE)),
}


def read(path: Path) -> str | None:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else None


def read_canon() -> dict[str, str | None]:
    return {name: read(CANON / name) for name in CANON_FILES}


def declared_version(text: str | None) -> str | None:
    if not text:
        return None
    match = PYPROJECT_VERSION.search(text)
    return match.group(1) if match else None


def code_version(text: str | None) -> str | None:
    if not text:
        return None
    match = CODE_VERSION.search(text)
    return match.group(1) if match else None


def read_pages() -> dict[str, str | None]:
    return {rel: read(path) for rel, path in PAGES.items()}


def copies(directory: Path) -> list[tuple[str, str, str | None]]:
    return [(name, str((directory / name).relative_to(ROOT)), read(directory / name))
            for name in COPIES]


def check_version(canon: dict[str, str | None]) -> list[str]:
    """Kildene skal være samme udgave, og ingen må mangle."""
    problems = [f"kanonisk kilde: page-profile/{name} mangler"
                for name in CANON_FILES if canon.get(name) is None]
    manifest = declared_version(canon.get("pyproject.toml"))
    source = code_version(canon.get("page_profile.py"))
    if canon.get("pyproject.toml") and manifest is None:
        problems.append("kanonisk kilde: pyproject.toml erklærer ingen version")
    if canon.get("page_profile.py") and source is None:
        problems.append("kanonisk kilde: page_profile.py erklærer ingen __version__")
    if manifest and source and manifest != source:
        problems.append(f"version: pyproject.toml siger {manifest}, koden siger {source}")
    return problems


def check_copies(canon: dict[str, str | None], published: list[tuple[str, str, str | None]]) -> list[str]:
    """Hver publiceret kopi skal være byte-identisk med den kanoniske fil."""
    return [f"drift: {where} er ikke den kanoniske {name}"
            for name, where, text in published
            if canon.get(name) is None or text != canon[name]]


def load_sdist(name: str) -> dict | None:
    """Rodmappe og kildefiler fra et source-arkiv, som tekst."""
    path = PUBLISHED / name
    if not path.is_file():
        return None
    roots: set[str] = set()
    members: dict[str, str] = {}
    with tarfile.open(path, "r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            head, _, name = member.name.partition("/")
            roots.add(head)
            if name in CANON_FILES:
                handle = tar.extractfile(member)
                members[name] = handle.read().decode("utf-8", "replace") if handle else ""
    return {"roots": sorted(roots), "members": members}


def archive_roots(sdists: dict[str, dict | None]) -> set[str]:
    """Alle rodmapper i de publicerede arkiver — dem skal `cd` i vejledningen pege på."""
    return {root for content in sdists.values() if content for root in content["roots"]}


def check_sdist(canon: dict[str, str | None], version: str | None,
                sdists: dict[str, dict | None]) -> list[str]:
    """Præcis ét arkiv, med navn og indhold fra den kanoniske kode."""
    problems: list[str] = []
    if not sdists:
        problems.append(f"publiceret kopi: {PUBLISHED.relative_to(ROOT)} har intet source-arkiv")
        return problems
    if len(sdists) > 1:
        listed = ", ".join(sorted(sdists))
        problems.append(
            f"publiceret kopi: {len(sdists)} source-arkiver i "
            f"{PUBLISHED.relative_to(ROOT)} ({listed}) — "
            f"kun den aktuelle udgave må ligge der")
    for name, content in sorted(sdists.items()):
        match = SDIST_NAME.match(name)
        if not match:
            problems.append(f"publiceret kopi: {name} følger ikke page-profile-<version>.tar.gz")
            continue
        archive_version = match.group(1)
        if version and archive_version != version:
            problems.append(f"drift: {name} er version {archive_version}, koden er {version}")
        if content is None:
            problems.append(f"publiceret kopi: {name} kunne ikke læses")
            continue
        roots = content["roots"]
        if len(roots) != 1 or archive_version not in roots[0]:
            problems.append(
                f"arkiv {name}: rodmappen {roots} følger ikke den pakkede udgave "
                f"{archive_version}")
        for source in CANON_FILES:
            if source not in content["members"]:
                problems.append(f"arkiv {name}: mangler {source}")
            elif content["members"][source] != canon.get(source):
                problems.append(f"arkiv {name}: {source} afviger fra den kanoniske kode")
    return problems


def check_pages(pages: dict[str, str | None], version: str | None,
                available: set[str], roots: set[str]) -> list[str]:
    """Siderne skal linke på en udgave, der findes, og lyve om licensen."""
    problems: list[str] = []
    for path, text in sorted(pages.items()):
        if text is None:
            problems.append(f"landingsside: {path} mangler")
            continue
        for archive in sorted(set(ARCHIVE_REF.findall(text))):
            if f"page-profile-{archive}.tar.gz" not in available:
                problems.append(
                    f"landingsside: {path} linker på page-profile-{archive}.tar.gz, "
                    f"som ikke findes i den publicerede kopi")
        for target in sorted(set(CD_DIR.findall(text))):
            if target not in roots:
                problems.append(
                    f"landingsside: {path} beder om `cd {target}`, som ikke er en mappe i arkivet")
        if version:
            for shown in sorted(set(SHOWN_VERSION.findall(text))):
                if shown != version:
                    problems.append(
                        f"landingsside: {path} viser version {shown}, koden er {version}")
        lowered = text.lower()
        for label, pattern in FORBIDDEN.items():
            if pattern.search(lowered):
                problems.append(f"landingsside: {path} har offline-påstanden {label!r}")
        for label, patterns in REQUIRED_CLAIMS.items():
            if not patterns[1 if path in DA_PAGES else 0].search(text):
                problems.append(f"landingsside: {path} siger ikke eksplicit om {label}")
    return problems


def run() -> list[str]:
    canon = read_canon()
    version = declared_version(canon.get("pyproject.toml"))
    sdists = {path.name: load_sdist(path.name) for path in sorted(PUBLISHED.glob("*.tar.gz"))}
    roots = archive_roots(sdists)
    problems = check_version(canon)
    problems += check_copies(canon, copies(PUBLISHED))
    problems += check_sdist(canon, version, sdists)
    problems += check_pages(read_pages(), version, set(sdists), roots)
    if DIST_COPY.is_dir() and any(DIST_COPY.iterdir()):
        problems += check_copies(canon, copies(DIST_COPY))
    return problems


def self_test() -> int:
    """Bevis at gaten fanger hver fejlform, den siger at fange."""
    canon = read_canon()
    version = declared_version(canon.get("pyproject.toml"))
    sdist_name = f"page-profile-{version}.tar.gz"
    sdists = {sdist_name: load_sdist(sdist_name)}
    roots = archive_roots(sdists)
    pages = read_pages()

    # En arkivkop, hvor koden er ændret, så arkiv-fejlen læses fra et rigtigt arkiv.
    drifted = {sdist_name: {**sdists[sdist_name], "members": {
        **sdists[sdist_name]["members"],
        "page_profile.py": canon["page_profile.py"].replace("__version__ =", "__version__  =")}}}
    old_version = {sdist_name: {**sdists[sdist_name], "members": {
        **sdists[sdist_name]["members"], "pyproject.toml": ""}}}

    scenarios: list[tuple[str, list[str]]] = [
        ("en manglende kanonisk fil",
         check_version({**canon, "cli.py": None})),
        ("en version der ikke matcher mellem manifest og kode",
         check_version({**canon, "pyproject.toml": canon["pyproject.toml"].replace(
             f'version = "{version}"', 'version = "0.0.1"')})),
        ("en publiceret kopi der mangler",
         check_copies(canon, [("page_profile.py",
                               "site/downloads/page-profile/page_profile.py", None)])),
        ("en publiceret kopi der afviger fra koden",
         check_copies(canon, [("page_profile.py", "site/downloads/page-profile/page_profile.py",
                               canon["page_profile.py"] + "\n# lokalt ændret\n")])),
        ("et source-arkiv der mangler",
         check_sdist(canon, version, {})),
        ("flere source-arkiver i den publicerede kopi",
         check_sdist(canon, version, {sdist_name: sdists[sdist_name],
                                      "page-profile-0.0.1.tar.gz": sdists[sdist_name]})),
        ("et source-arkiv på en gammel udgave",
         check_sdist(canon, "0.0.1", {"page-profile-0.0.1.tar.gz": sdists[sdist_name]})),
        ("et source-arkiv med rodmappen i en forkert udgave",
         check_sdist(canon, version, {sdist_name: {
             **sdists[sdist_name], "roots": ["page-profile-0.0.1"]}})),
        ("en kildefil i arkivet der afviger fra koden",
         check_sdist(canon, version, drifted)),
        ("en kildefil der mangler i arkivet",
         check_sdist(canon, version, {sdist_name: {"roots": sdists[sdist_name]["roots"],
                                                  "members": old_version[sdist_name]["members"]}})),
        ("et arkiv der ikke kan læses",
         check_sdist(canon, version, {sdist_name: None})),
        ("en landingsside der linker på et arkiv, der ikke findes",
         check_pages({"site/page-profile.html": pages["site/page-profile.html"].replace(
             sdist_name, "page-profile-0.0.1.tar.gz")}, version, {sdist_name}, roots)),
        ("en landingsside der viser en gammel udgave i eksemplet",
         check_pages({"site/page-profile.html": f"<p>page-profile v0.0.1</p>"},
                     version, {sdist_name}, roots)),
        ("en landingsside der cd'er ind i en mappe, der ikke findes i arkivet",
         check_pages({"site/page-profile.html": "cd page-profile-1.2.0"},
                     version, {sdist_name}, roots)),
        ("en landingsside med offline-påstand",
         check_pages({"site/page-profile.html":
                      "<p>Online activation. Cached for seven days.</p>"
                      "<p>Licensen aktiveres offline.</p>"}, version, {sdist_name}, roots)),
        ("en landingsside uden online-aktivering",
         check_pages({"site/page-profile.html":
                      "<p>Cached for seven days. Licenstjek aldrig kontakter.</p>"},
                     version, {sdist_name}, roots)),
        ("en dansk side uden syvdages cache",
         check_pages({"site/da/page-profile.html": "<p>Online aktivering og validering.</p>"},
                     version, {sdist_name}, roots)),
        ("en manglende landingsside",
         check_pages({"site/page-profile.html": None}, version, {sdist_name}, roots)),
        ("en dist-kopi der afviger fra koden",
         check_copies(canon, [("page_profile.py",
                               "dist/mahope.tools/downloads/page-profile/page_profile.py",
                               canon["page_profile.py"].replace("__version__ =", "__version__  ="))])),
    ]

    missed = [label for label, problems in scenarios if not problems]
    for label in missed:
        print(f"SELFTEST FEJLER: {label} blev ikke fanget")

    green = (check_version(canon) + check_copies(canon, copies(PUBLISHED))
             + check_sdist(canon, version, sdists)
             + check_pages(pages, version, set(sdists), archive_roots(sdists)))
    if green:
        print("SELFTEST FEJLER: den rigtige kopi skal være grøn, men fandt:")
        for problem in green:
            print(f"  {problem}")
        missed.append("den rigtige kopi")

    print(f"selftest: {len(scenarios) + 1 - len(missed)}/{len(scenarios) + 1} "
          f"fejlformer fanget")
    return 1 if missed else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true",
                        help="bevis at gaten fanger drift")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    problems = run()
    for problem in problems:
        print(f"PROBLEM: {problem}")
    print(f"check_page_profile_distribution: {len(problems)} problemer")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
