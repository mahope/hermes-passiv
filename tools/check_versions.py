#!/usr/bin/env python3
"""Én versionskilde pr. produkt, og drift mellem dem bliver en fejl.

Opgave 14 (25. september 2026) fandt filer i repoet der alle sagde "version" om
hver sit produkt, og ingen af dem vidste om de andre: `manifest.json` i roden
sagde 1.0.1 om Obsidian-pluginet, `obsidian-plugin/manifest.json` sagde 1.0.10,
og arkivet kunden henter hed `clean-copy-obsidian-v1.0.10.zip`. Kun den sidste
er den brugeren får.

Det er ikke et versionsproblem, det er et *kildefejl*: når en værdi har to
hjemsteder, er spørgsmålet "hvad er versionen" ikke lenger et factum men en
mening. Derfor er der her én tabel, der erklærer hvilken fil der **er** sandheden
for hvert produkt, og fire checks der alle kan fejle:

1. **Sandheden findes.** Den kanoniske fil skal findes og have en version der
   ligner en version. Mangler den, er der ingen at måle de andre imod.
2. **Ingen spejling lyver.** Spejle (lockfil, `__version__`, Obsidians
   `versions.json`) skal være på samme version. En lockfil der er ude i takt
   med `package.json` bygger ikke den version man tror.
3. **Artefktet findes og er det nyeste.** For hvert produkt skal det
   publicerede arkiv findes på den kanoniske version, og **intet** arkiv i samme
   familie må ligge på en anden version. Et gammelt arkiv i mappen er ikke en
   fejl, indtil nogen kan hente det — og da er det en kunde der får gammel kode.
4. **Download-siden siger den samme version.** Hvert filnavn fra produktets
   arkivfamilier på `site/downloads.html` skal være den kanoniske version, og
   siden skal have en reference på den. Ellers lover siden en version kunden
   ikke kan hente.

Derudover holder porten fast i, at der findes *én* kilde pr. produkt:
`manifest.json` og `versions.json` i repo-roden er forbudt, fordi de er de to
ekstra versionskilder, opgaven handler om.

Selftesten mutationerer hver enkelt check mod et komplet fixture og kræver at
porten **fejler** på mutationen og **passer** på de uændrede filer. Uden den
positive kontrol er en gate, der siger "skal ikke fejle", intet bevis — samme
pointe som opgave 13 og 16.

    python3 tools/check_versions.py
    python3 tools/check_versions.py --self-test
"""
from __future__ import annotations

import io
import json
import re
import shutil
import sys
import tarfile
import tempfile
import zipfile
import zlib
from dataclasses import dataclass, replace
from fnmatch import fnmatch as _segment_match
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import mini_toml  # noqa: E402

SEMVER = re.compile(r"\d+\.\d+\.\d+")
EXACT_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
DOWNLOADS = "site/downloads.html"

#: Filer hvis versionserklæring er en RFC822-linje `Version: x.y.z` — setuptools'
#: `PKG-INFO` i en sdist og `*.dist-info/METADATA` i et hjul. Kun disse navne:
#: en vilkårlig tekstfil med en `Version:`-linje er ikke en versionserklæring, og
#: hvis porten læste den, ville den finde "versioner" i README'er og changelog'er.
METADATA_NAMES = ("PKG-INFO", "METADATA")


@dataclass(frozen=True)
class Product:
    """Ét produkt, én sandhed, og de steder sandheden skal kunne læses."""

    key: str
    canonical: str
    #: (fil, `#`-sti ind i filen) der skal have samme version. Stien
    #: `versions.json` betyder "filen skal kende udgaven som nøgle".
    mirrors: tuple[tuple[str, str], ...] = ()
    #: (glob, template): `template` har `{version}`, `glob` finder hele familien,
    #: så et gammelt arkiv i samme familie kan tælles.
    artifacts: tuple[tuple[str, str], ...] = ()
    #: (arkivglob, memberglob, notation) for filer **inde i** et publiceret arkiv.
    #: Byggeoutput — pip-hjul, sdists, `npm pack`-tgz — kan ikke sammenlignes fil
    #: for fil med kilden, fordi `python -m build` og `npm pack` skriver
    #: `PKG-INFO`, `setup.cfg` og `.dist-info/` ind i dem. Men de bærer deres
    #: egen versionserklæring, og *den* skal være den kanoniske version: en
    #: kunde der `pip install`er et 1.2.0-navngivet hjul med 1.1.0 indeni har
    #: fået gammel kode under et nyt navn. Tom tuple betyder "arkivet erklærer
    #: ingen indre version" — og så må porten **ikke** kræve en.
    inner: tuple[tuple[str, str, str], ...] = ()


PRODUCTS: tuple[Product, ...] = (
    Product(
        key="clean-copy-chrome",
        canonical="extension-clean-copy/manifest.json",
        artifacts=(
            ("site/downloads/clean-copy-v*.zip", "site/downloads/clean-copy-v{version}.zip"),
        ),
    ),
    Product(
        key="clean-copy-firefox",
        canonical="extension-clean-copy-firefox/manifest.json",
        artifacts=(
            ("site/downloads/clean-copy-firefox-v*.zip", "site/downloads/clean-copy-firefox-v{version}.zip"),
        ),
    ),
    Product(
        key="clean-copy-obsidian",
        canonical="obsidian-plugin/manifest.json",
        mirrors=(("obsidian-plugin/versions.json", "versions.json"),),
        artifacts=(
            ("site/downloads/clean-copy-obsidian-v*.zip", "site/downloads/clean-copy-obsidian-v{version}.zip"),
        ),
    ),
    Product(
        key="eaa-scanner-desktop",
        canonical="desktop/package.json",
        mirrors=(
            ("desktop/package-lock.json", "version"),
            # `packages.""` er lockfilens rod-pakke, og dens `version` skal
            # være samme som i `package.json`. Nøglen er den tomme streng, så
            # stien skriver den som `""` — ellers er den ikke at skelne fra
            # en rigtig nøgle med navnet "".
            ("desktop/package-lock.json", 'packages."".version'),
        ),
        artifacts=(
            (
                "site/downloads/eaa-scanner-desktop-src-*.zip",
                "site/downloads/eaa-scanner-desktop-src-{version}.zip",
            ),
        ),
    ),
    Product(
        key="eaa-scanner-python",
        canonical="scanner/packaging/pyproject.toml",
        mirrors=(("scanner/packaging/eaa_scanner/__init__.py", "__version__"),),
        artifacts=(
            ("site/downloads/eaa_scanner-*.whl", "site/downloads/eaa_scanner-{version}-py3-none-any.whl"),
            ("site/downloads/eaa_scanner-*.tar.gz", "site/downloads/eaa_scanner-{version}.tar.gz"),
        ),
        # Segmentvis glob: `*` matcher ikke `/`, ellers ville
        # `eaa_scanner-1.2.0/eaa_scanner.egg-info/PKG-INFO` også matche
        # `*/PKG-INFO` — og så ville porten tælle to erklæringer for én arkiv.
        inner=(
            ("site/downloads/eaa_scanner-*.whl", "*.dist-info/METADATA", "Version:"),
            ("site/downloads/eaa_scanner-*.tar.gz", "*/PKG-INFO", "Version:"),
        ),
    ),
    Product(
        key="eaa-scanner-npm",
        canonical="scanner/npm/eaa-scanner/package.json",
        artifacts=(
            ("site/downloads/mahope-eaa-scanner-*.tgz", "site/downloads/mahope-eaa-scanner-{version}.tgz"),
        ),
        inner=(
            ("site/downloads/mahope-eaa-scanner-*.tgz", "package/package.json", "version"),
        ),
    ),
    Product(
        key="page-profile",
        canonical="page-profile/pyproject.toml",
        mirrors=(("page-profile/page_profile.py", "__version__"),),
        artifacts=(
            (
                "site/downloads/page-profile/page-profile-*.tar.gz",
                "site/downloads/page-profile/page-profile-{version}.tar.gz",
            ),
        ),
        inner=(
            ("site/downloads/page-profile/page-profile-*.tar.gz", "*/PKG-INFO", "Version:"),
        ),
    ),
    Product(
        key="site-icons",
        canonical="site-icons/pyproject.toml",
        artifacts=(
            (
                "site/downloads/site-icons/site-icons-*.tar.gz",
                "site/downloads/site-icons/site-icons-{version}.tar.gz",
            ),
        ),
        # Planen antog at dette håndlavede tarball "er uden indre
        # versionserklæring", fordi det har to filer og ingen `PKG-INFO`. Den
        # ene af de to filer erklærer versionen alligevel, som `__version__` i
        # modulets egen rod: `site_icons.py:25`. Så den dækkes lige så vel som
        # de tre øvrige. (At arkivet er en håndlavet *gammel* kopi er en anden
        # fejl — den står som opgave 20.)
        inner=(
            ("site/downloads/site-icons/site-icons-*.tar.gz", "site_icons.py", "__version__"),
        ),
    ),
)

#: Filer i repo-roden der er en *første* versionskilde for et produkt, som har
#: sin egen. De lå her fra den første mono-repo-commit og bruges af intet build
#: — men de læses af det menneske, der leder efter versionen.
FORBIDDEN_SOURCES = ("manifest.json", "versions.json")


class Report:
    """Fund samles her, så både `run` og selftesten kan læse dem."""

    def __init__(self) -> None:
        self.problems: list[str] = []
        self.versions: dict[str, str] = {}

    def add(self, problem: str) -> None:
        self.problems.append(problem)


def read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def version_from_text(name: str, raw: str, path: str, report: Report) -> str | None:
    """Læs én version ud af en tekst, uanset om den kom fra disk eller fra et arkiv.

    `path` er den notation spejlene bruger: `version` i en JSON-fil,
    `__version__` i en Python-fil. `.toml` og metadatafiler bruger ingen notation
    for sig — de *er* notationsformen. `report` får kun JSON- og TOML-fejl, så en
    arkivfejl peger på arkivet og ikke på en fil der ikke findes.

    TOML læses med `mini_toml.loads(text, name)`, ikke `load(path)`: den
    indlejrede `tomllib.load` kræver et binært filobjekt, mens `mini_toml.load`
    tager en `Path`. `loads` findes i begge, så vejen er den samme på 3.9 og 3.12
    — samme løsning som opgave 13 fandt i CI.
    """
    if name.endswith(".toml"):
        try:
            data = mini_toml.loads(raw, name)
        except (mini_toml.TOMLDecodeError, ValueError) as exc:
            report.add(f"{name}: kan ikke læses som TOML ({exc})")
            return None
        version = data.get("project", {}).get("version")
        return None if version is None else str(version)
    if name.endswith(".json"):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            report.add(f"{name}: kan ikke læses som JSON ({exc})")
            return None
        for step in path.split("."):
            if not isinstance(data, dict):
                return None
            key = "" if step == '""' else step
            if key not in data:
                return None
            data = data[key]
        return str(data) if isinstance(data, (str, int, float)) else None
    if name.endswith(".py"):
        match = re.search(r"""^__version__\s*=\s*["']([^"']+)["']""", raw, re.MULTILINE)
        return match.group(1) if match else None
    if Path(name).name in METADATA_NAMES:
        match = re.search(r"^Version:[ \t]*(\S+)[ \t]*$", raw, re.MULTILINE)
        return match.group(1) if match else None
    return None


def json_version(root: Path, rel: str, path: str, report: Report) -> str | None:
    raw = read(root / rel)
    if raw is None:
        return None
    return version_from_text(rel, raw, path, report)


def source_version(root: Path, rel: str, report: Report) -> str | None:
    raw = read(root / rel)
    if raw is None:
        return None
    return version_from_text(rel, raw, "version", report)


def member_matches(name: str, pattern: str) -> bool:
    """Segmentvis glob: `*` matcher ikke `/`.

    `fnmatch` lader `*` spænde over skillestreger, så `*/PKG-INFO` ville ramme
    både `eaa_scanner-1.2.0/PKG-INFO` og
    `eaa_scanner-1.2.0/eaa_scanner.egg-info/PKG-INFO` — to erklæringer for ét
    arkiv, hvoraf kun den ene er sdistens egen. Segmentvis sammenligning er det
    samme som det globsystem de fleste byggeværktøjer bruger.
    """
    parts = name.split("/")
    wanted = pattern.split("/")
    if len(parts) != len(wanted):
        return False
    return all(_segment_match(part, want) for part, want in zip(parts, wanted))


def read_members(path: Path, report: Report) -> dict[str, str] | None:
    """{membernavn: tekst} for et arkiv, uanset format.

    ZIP til hjul og extension-arkiver, gzipped tar til sdists, `npm pack`-tgz og
    det håndlavede site-icons-tarball. Formatet læses af magiske bytes, ikke af
    endelsen: `.whl` er en ZIP men hedder ikke `.zip`, og en liste af endelser
    ville være en fejl, der bare venter på det nye format. `None` betyder at
    arkivet ikke kan læses, og så har fundet en fejl — en port der springer et
    korrupt arkiv over ville lade det være grønt, fordi den intet fandt.
    """
    try:
        with open(path, "rb") as handle:
            magic = handle.read(4)
    except OSError as exc:
        report.add(f"{path.name}: kan ikke læses ({exc})")
        return None

    def texts(names: Iterable[str], load) -> dict[str, str]:
        return {name: load(name).decode("utf-8", "replace") for name in names}

    try:
        if magic[:2] == b"PK":
            with zipfile.ZipFile(path) as archive:
                return texts(
                    (info.filename for info in archive.infolist() if not info.is_dir()),
                    archive.read,
                )
        if magic[:2] == b"\x1f\x8b":
            with tarfile.open(path, "r:gz") as archive:
                return texts(
                    (member.name for member in archive.getmembers() if member.isfile()),
                    lambda name: archive.extractfile(name).read(),  # type: ignore[union-attr]
                )
    except (OSError, EOFError, KeyError, tarfile.TarError, zipfile.BadZipFile, zlib.error) as exc:
        report.add(f"{path.name}: kan ikke åbnes som arkiv ({exc})")
        return None
    report.add(f"{path.name}: ukendt arkivformat (de første bytes er {magic!r})")
    return None


def family_versions(root: Path, glob: str) -> dict[str, str]:
    """{filnavn: version} for alle filer i arkivfamilien.

    Versionen læses ud af filnavnet alene, så `eaa_scanner-1.1.0-py3-none-any.whl`
    tælles som 1.1.0 — også når ingen fortæller os at det er det.
    """
    out: dict[str, str] = {}
    for path in sorted((root / glob).parent.glob(Path(glob).name)):
        found = SEMVER.findall(path.name)
        if found:
            out[path.name] = found[0]
    return out


def check_product(root: Path, product: Product, report: Report) -> None:
    version = source_version(root, product.canonical, report)
    if version is None:
        report.add(
            f"{product.key}: {product.canonical} mangler eller har ingen aflæselig version — "
            f"der er ingen sandhed at måle de andre filer imod"
        )
        return
    if not EXACT_VERSION.match(version):
        report.add(f"{product.key}: versionen {version!r} i {product.canonical} er ikke x.y.z")
        return
    report.versions[product.key] = version

    for rel, path in product.mirrors:
        if path == "versions.json":
            raw = read(root / rel)
            keys: list[str] = []
            if raw is not None:
                try:
                    keys = list(json.loads(raw))
                except json.JSONDecodeError as exc:
                    report.add(f"{rel}: kan ikke læses som JSON ({exc})")
            if raw is not None and version not in keys:
                report.add(
                    f"{product.key}: {rel} kender ikke udgaven {version} — Obsidian kan ikke "
                    f"installere den version, pluginet er bygget på"
                )
            continue
        found = json_version(root, rel, path, report) if rel.endswith(".json") else source_version(root, rel, report)
        if found is None:
            report.add(f"{product.key}: {rel} har ingen aflæselig version ({path})")
        elif found != version:
            report.add(f"{product.key}: {rel} ({path}) siger {found}, men {product.canonical} siger {version}")

    for glob, template in product.artifacts:
        expected = template.format(version=version)
        if not (root / expected).is_file():
            report.add(
                f"{product.key}: {expected} mangler — kunden kan ikke hente den version kilden er på"
            )
        for name, found in family_versions(root, glob).items():
            if found != version:
                report.add(
                    f"{product.key}: {name} ligger på {found}, mens kilden er på {version} — "
                    f"et gammelt arkiv i publiceringsmappen er en kunde der henter gammel kode"
                )


def check_inner_versions(root: Path, product: Product, report: Report) -> None:
    """Versionserklæringen *inde i* hvert publiceret byggeoutput-arkiv.

    Kun det kanoniske arkiv læses: et ældre arkiv i samme familie er allerede
    fundet ovenfor, og at læse det igen ville give to fejl for én.
    """
    version = report.versions.get(product.key)
    if version is None:
        return
    templates = {glob: template for glob, template in product.artifacts}
    for glob, member_glob, notation in product.inner:
        template = templates.get(glob)
        if template is None:
            raise AssertionError(
                f"selftest/opsætning: {product.key} erklærer en indre version for {glob!r}, "
                f"som ikke er en af dens arkivfamilier"
            )
        archive = root / template.format(version=version)
        if not archive.is_file():
            continue  # Already reported as missing.
        members = read_members(archive, report)
        if members is None:
            continue
        hits = sorted(name for name in members if member_matches(name, member_glob))
        if not hits:
            report.add(
                f"{product.key}: {archive.name} har ingen {member_glob} — filen der erklærer "
                f"hvilken version kunden får, findes ikke inde i arkivet"
            )
            continue
        for name in hits:
            found = version_from_text(name, members[name], notation, report)
            if found is None:
                report.add(
                    f"{product.key}: {archive.name} → {name} har ingen aflæselig version "
                    f"({notation}) — porten kan ikke bevise at kunden får {version}"
                )
            elif found != version:
                report.add(
                    f"{product.key}: {archive.name} → {name} siger {found}, mens kilden siger "
                    f"{version} — kunden henter gammel kode under et nyt filnavn"
                )


def check_download_page(root: Path, report: Report, products: tuple[Product, ...]) -> None:
    """Download-siden skal love den version der faktisk kan hentes."""
    raw = read(root / DOWNLOADS)
    if raw is None:
        report.add(f"{DOWNLOADS}: mangler")
        return
    for product in products:
        version = report.versions.get(product.key)
        if version is None:
            continue
        for glob, template in product.artifacts:
            pattern = re.escape(Path(glob).name).replace(r"\*", r"[0-9.]+")
            for mentioned in sorted(set(re.findall(pattern, raw))):
                for found in SEMVER.findall(mentioned):
                    if found != version:
                        report.add(f"{DOWNLOADS}: {product.key} nævner {mentioned}, men kilden er på {version}")
        if not any(Path(template).name.format(version=version) in raw for _glob, template in product.artifacts):
            report.add(f"{DOWNLOADS}: {product.key} har ingen reference på arkivet for {version}")


def check_single_source(root: Path, report: Report) -> None:
    for rel in FORBIDDEN_SOURCES:
        if (root / rel).exists():
            report.add(
                f"{rel} i repo-roden er en ekstra versionskilde — versionen har to hjemsteder, "
                f"og ingen ved hvilken der er rigtig (produktet har sin egen under sin egen mappe)"
            )


def run(root: Path, products: tuple[Product, ...] = PRODUCTS) -> tuple[list[str], dict[str, str]]:
    report = Report()
    check_single_source(root, report)
    for product in products:
        check_product(root, product, report)
    # Efter alle produkter, så `report.versions` er fuldt når `check_inner_versions`
    # slår op. Arkiverne læses kun for produkter hvis sandhed faktisk blev fundet.
    for product in products:
        check_inner_versions(root, product, report)
    check_download_page(root, report, products)
    return report.problems, report.versions


# --------------------------------------------------------------------------
# Selftest
# --------------------------------------------------------------------------

#: Ét komplet fixture: alle otte produkter, alle spejle, alle ni arkiver og en
#: downloads-side der kun nævner de aktuelle versioner. Mutationerne sker her,
#: så hver enkelt fejl måtte kun have ÉN årsag.
#:
#: Værdierne er enten tekst (skrives som fil) eller et arkiv-spec
#: `{"format": "zip"|"targz", "files": {member: tekst}}` (skrives som ægte arkiv).
#: Det er ikke pænthed: et fixture hvor arkiverne er teksten `"whl"` gør den
#: indre versionskontrol til teater, fordi `read_members` aldrig finder noget. De
#: skal være rigtige nok til at `zipfile` og `tarfile` kan åbne dem, og de skal
#: rumme de samme filer de rigtige byggeoutput har — inklusive et
#: `*.egg-info/PKG-INFO` på den *gamle* version, fordi det er præcis den der
#: beviser at `*/PKG-INFO` kun rammer sdistens egen og ikke dyret inde.
EAA_METADATA = "Metadata-Version: 2.1\nName: eaa-scanner\nVersion: {version}\n"
EAA_PKG_INFO = "Metadata-Version: 2.1\nName: eaa-scanner\nVersion: {version}\n"

FIXTURE: dict[str, object] = {
    "extension-clean-copy/manifest.json": json.dumps({"name": "Clean Copy", "version": "1.5.3"}),
    "extension-clean-copy-firefox/manifest.json": json.dumps({"name": "Clean Copy", "version": "1.5.3"}),
    "obsidian-plugin/manifest.json": json.dumps({"id": "clean-copy", "version": "1.0.10"}),
    "obsidian-plugin/versions.json": json.dumps({"1.0.9": "1.4.0", "1.0.10": "1.4.0"}),
    "desktop/package.json": json.dumps({"name": "desktop", "version": "1.3.3"}),
    "desktop/package-lock.json": json.dumps({"version": "1.3.3", "packages": {"": {"version": "1.3.3"}}}),
    "scanner/packaging/pyproject.toml": '[project]\nname = "eaa-scanner"\nversion = "1.2.0"\n',
    "scanner/packaging/eaa_scanner/__init__.py": '__version__ = "1.2.0"\n',
    "scanner/npm/eaa-scanner/package.json": json.dumps({"name": "@mahope/eaa-scanner", "version": "1.2.0"}),
    "page-profile/pyproject.toml": '[project]\nname = "page-profile"\nversion = "1.2.0"\n',
    "page-profile/page_profile.py": '__version__ = "1.2.0"\n',
    "site-icons/pyproject.toml": '[project]\nname = "site-icons"\nversion = "1.0.0"\n',
    "site/downloads/clean-copy-v1.5.3.zip": {"format": "zip", "files": {"manifest.json": "{}"}},
    "site/downloads/clean-copy-firefox-v1.5.3.zip": {"format": "zip", "files": {"manifest.json": "{}"}},
    "site/downloads/clean-copy-obsidian-v1.0.10.zip": {"format": "zip", "files": {"manifest.json": "{}"}},
    "site/downloads/eaa-scanner-desktop-src-1.3.3.zip": {"format": "zip", "files": {"package.json": "{}"}},
    "site/downloads/eaa_scanner-1.2.0-py3-none-any.whl": {
        "format": "zip",
        "files": {
            "eaa_scanner/__init__.py": '__version__ = "1.2.0"\n',
            "eaa_scanner-1.2.0.dist-info/METADATA": EAA_METADATA.format(version="1.2.0"),
            "eaa_scanner-1.2.0.dist-info/RECORD": "eaa_scanner/__init__.py,,\n",
        },
    },
    "site/downloads/eaa_scanner-1.2.0.tar.gz": {
        "format": "targz",
        "files": {
            "eaa_scanner-1.2.0/PKG-INFO": EAA_PKG_INFO.format(version="1.2.0"),
            "eaa_scanner-1.2.0/pyproject.toml": '[project]\nname = "eaa-scanner"\nversion = "1.2.0"\n',
            "eaa_scanner-1.2.0/eaa_scanner/__init__.py": '__version__ = "1.2.0"\n',
            # Stale byggeaffald. En segmentvis glob skal IGNORERE den; en fnmatch
            # der spænder over `/` ville tælle den og slå positiv kontrol rød.
            "eaa_scanner-1.2.0/eaa_scanner.egg-info/PKG-INFO": EAA_PKG_INFO.format(version="1.1.0"),
        },
    },
    "site/downloads/mahope-eaa-scanner-1.2.0.tgz": {
        "format": "targz",
        "files": {
            "package/package.json": json.dumps({"name": "@mahope/eaa-scanner", "version": "1.2.0"}),
            "package/index.js": "module.exports = {};\n",
            "package/README.md": "# eaa-scanner\n",
        },
    },
    "site/downloads/page-profile/page-profile-1.2.0.tar.gz": {
        "format": "targz",
        "files": {
            "page_profile-1.2.0/PKG-INFO": "Metadata-Version: 2.1\nName: page-profile\nVersion: 1.2.0\n",
            "page_profile-1.2.0/page_profile.py": '__version__ = "1.2.0"\n',
        },
    },
    "site/downloads/site-icons/site-icons-1.0.0.tar.gz": {
        "format": "targz",
        "files": {
            "site_icons.py": '__version__ = "1.0.0"\n',
            "README.md": "# site-icons\n",
        },
    },
    DOWNLOADS: "\n".join(
        f'<a href="/{rel}">{rel}</a>'
        for rel in (
            "downloads/clean-copy-v1.5.3.zip",
            "downloads/clean-copy-firefox-v1.5.3.zip",
            "downloads/clean-copy-obsidian-v1.0.10.zip",
            "downloads/eaa-scanner-desktop-src-1.3.3.zip",
            "downloads/eaa_scanner-1.2.0-py3-none-any.whl",
            "downloads/eaa_scanner-1.2.0.tar.gz",
            "downloads/mahope-eaa-scanner-1.2.0.tgz",
            "downloads/page-profile/page-profile-1.2.0.tar.gz",
            "downloads/site-icons/site-icons-1.0.0.tar.gz",
        )
    ),
}

#: Fast tidspunkt for alle arkivmedlemmer. Uden det er `--self-test` afhængig af
#: at filerne skrives samme sekund, og en archive-header tidsstempel ville gøre
#: hver kørsel til et nyt sammenligningsgrundlag.
ARCHIVE_EPOCH = (1980, 1, 1, 0, 0, 0)


def build_archive(spec: dict) -> bytes:
    """Byg et byte-arkiv af et spec, så fixture-filerne er ægte arkiver."""
    files: dict[str, str] = spec["files"]
    if spec["format"] == "zip":
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, body in files.items():
                info = zipfile.ZipInfo(name, date_time=ARCHIVE_EPOCH)
                info.external_attr = 0o644 << 16
                archive.writestr(info, body)
        return buffer.getvalue()

    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz", format=tarfile.GNU_FORMAT) as archive:
        for name, body in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(body.encode("utf-8"))
            info.mtime = 0
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(body.encode("utf-8")))
    return buffer.getvalue()


def write_fixture(root: Path, files: dict[str, object]) -> None:
    for rel, body in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(body, dict):
            path.write_bytes(build_archive(body))
        elif isinstance(body, (bytes, bytearray)):
            path.write_bytes(bytes(body))
        else:
            path.write_text(str(body), encoding="utf-8")


def edit(files: dict[str, object], rel: str, old: str, new: str) -> dict[str, object]:
    out = dict(files)
    if old not in out[rel]:
        raise AssertionError(f"selftest: {rel} indeholder ikke {old!r}")
    out[rel] = out[rel].replace(old, new)  # type: ignore[union-attr]
    return out


def edit_inside(
    files: dict[str, object], rel: str, member: str, old: str, new: str
) -> dict[str, object]:
    """Udskift tekst i ÉN fil inde i et fixture-arkiv.

    Bevidst en egen mutationstype: `edit` ville ændre arkiv-teksten, hvilket er
    umuligt, fordi arkivet er komprimeret. Og en mutation der bygger et helt nyt
    arkiv uden den medlem ville teste en anden ting end den tilsigtede.
    """
    out = dict(files)
    spec = out[rel]
    assert isinstance(spec, dict), f"selftest: {rel} er ikke et arkiv-spec"
    members = dict(spec["files"])  # type: ignore[index]
    if member not in members:
        raise AssertionError(f"selftest: {rel} har ikke medlemmet {member!r}")
    if old not in members[member]:
        raise AssertionError(f"selftest: {rel} → {member} indeholder ikke {old!r}")
    members[member] = members[member].replace(old, new)
    out[rel] = {**spec, "files": members}  # type: ignore[dict-item]
    return out


def drop_member(files: dict[str, object], rel: str, member: str) -> dict[str, object]:
    """Fjern ÉN medlem fra et fixture-arkiv, som en mutation der gør klar det."""
    out = dict(files)
    spec = out[rel]
    assert isinstance(spec, dict), f"selftest: {rel} er ikke et arkiv-spec"
    members = dict(spec["files"])  # type: ignore[index]
    if member not in members:
        raise AssertionError(f"selftest: {rel} har ikke medlemmet {member!r}")
    del members[member]
    out[rel] = {**spec, "files": members}  # type: ignore[dict-item]
    return out


def scenarios() -> list[tuple[str, dict[str, object], str]]:
    """(navn, mutation, forventet fejl)."""
    out: list[tuple[str, dict[str, object], str]] = []

    out.append(("kanonisk fil mangler", {k: v for k, v in FIXTURE.items() if k != "extension-clean-copy/manifest.json"}, "mangler eller har ingen aflæselig version"))
    out.append(("version er ikke x.y.z", edit(FIXTURE, "extension-clean-copy/manifest.json", '"1.5.3"', '"1.5.3-rc1"'), "er ikke x.y.z"))
    out.append(("arkiv mangler", {k: v for k, v in FIXTURE.items() if k != "site/downloads/clean-copy-v1.5.3.zip"}, "kan ikke hente den version kilden er på"))

    stale = dict(FIXTURE)
    stale["site/downloads/clean-copy-v1.5.2.zip"] = {"format": "zip", "files": {"manifest.json": "{}"}}
    out.append(("gammelt arkiv i mappen", stale, "gammelt arkiv i publiceringsmappen"))

    stale_dep = dict(FIXTURE)
    stale_dep["site/downloads/eaa_scanner-1.1.0-py3-none-any.whl"] = {"format": "zip", "files": {"x": ""}}
    out.append(("gammelt hjul i mappen", stale_dep, "gammelt arkiv i publiceringsmappen"))

    out.append(("siden nævner en anden version", edit(FIXTURE, DOWNLOADS, "clean-copy-v1.5.3.zip", "clean-copy-v1.5.2.zip"), "nævner"))
    out.append(("siden mangler referencen", {**FIXTURE, DOWNLOADS: "<p>Ingen downloads.</p>"}, "har ingen reference på arkivet"))
    out.append(("downloads.html mangler", {k: v for k, v in FIXTURE.items() if k != DOWNLOADS}, f"{DOWNLOADS}: mangler"))

    out.append(("kilden er foran arkivet", edit(FIXTURE, "extension-clean-copy/manifest.json", '"1.5.3"', '"1.5.4"'), "kan ikke hente den version kilden er på"))
    out.append(("spejl i roden", {**FIXTURE, "manifest.json": json.dumps({"id": "clean-copy-obsidian", "version": "1.0.1"})}, "ekstra versionskilde"))
    out.append(("versions.json i roden", {**FIXTURE, "versions.json": json.dumps({"1.0.0": "1.0.0"})}, "ekstra versionskilde"))
    out.append(("lockfile ude i takt", edit(FIXTURE, "desktop/package-lock.json", "1.3.3", "1.3.1"), "siger 1.3.1"))
    out.append(("__version__ ude i takt", edit(FIXTURE, "page-profile/page_profile.py", "1.2.0", "1.1.0"), "siger 1.1.0"))
    out.append(("versions.json kender ikke udgaven", edit(FIXTURE, "obsidian-plugin/versions.json", '"1.0.10"', '"1.0.99"'), "kender ikke udgaven"))
    out.append(("spejlfil mangler", {k: v for k, v in FIXTURE.items() if k != "desktop/package-lock.json"}, "har ingen aflæselig version"))
    out.append(("manifest.json ugyldig JSON", edit(FIXTURE, "extension-clean-copy/manifest.json", '"1.5.3"}', '"1.5.3",}'), "kan ikke læses som JSON"))
    out.append(("pyproject.toml ugyldig TOML", {**FIXTURE, "page-profile/pyproject.toml": "[project\nname = 'x'\n"}, "kan ikke læses som TOML"))

    # --- Den indre version: filerne INDE I byggeoutput-arkiverne -------------
    #
    # Disse otte filer hedder 1.2.0/1.0.0 i publiceringsmappen, og det er den
    # eneste måde de bliver kontrolleret på. Før denne kontrol fandt ingen noget
    # inde i dem — opgave 18 fandt den samme fejlform i et helt andet arkiv.

    out.append((
        "METADATA i hjulet siger 1.1.0",
        edit_inside(FIXTURE, "site/downloads/eaa_scanner-1.2.0-py3-none-any.whl", "eaa_scanner-1.2.0.dist-info/METADATA", "Version: 1.2.0", "Version: 1.1.0"),
        "kunden henter gammel kode under et nyt filnavn",
    ))
    out.append((
        "PKG-INFO i sdisten siger 1.1.0",
        edit_inside(FIXTURE, "site/downloads/eaa_scanner-1.2.0.tar.gz", "eaa_scanner-1.2.0/PKG-INFO", "Version: 1.2.0", "Version: 1.1.0"),
        "kunden henter gammel kode under et nyt filnavn",
    ))
    out.append((
        "METADATA mangler i hjulet",
        drop_member(FIXTURE, "site/downloads/eaa_scanner-1.2.0-py3-none-any.whl", "eaa_scanner-1.2.0.dist-info/METADATA"),
        "har ingen *.dist-info/METADATA",
    ))
    out.append((
        "tgz uden package/package.json",
        drop_member(FIXTURE, "site/downloads/mahope-eaa-scanner-1.2.0.tgz", "package/package.json"),
        "har ingen package/package.json",
    ))
    out.append((
        "PKG-INFO mangler i page-profile-sdisten",
        drop_member(FIXTURE, "site/downloads/page-profile/page-profile-1.2.0.tar.gz", "page_profile-1.2.0/PKG-INFO"),
        "har ingen */PKG-INFO",
    ))
    out.append((
        "site_icons.py i tarballet siger 0.9.0",
        edit_inside(FIXTURE, "site/downloads/site-icons/site-icons-1.0.0.tar.gz", "site_icons.py", '__version__ = "1.0.0"', '__version__ = "0.9.0"'),
        "kunden henter gammel kode under et nyt filnavn",
    ))
    out.append((
        "arkivet er slet ikke et arkiv",
        {**FIXTURE, "site/downloads/mahope-eaa-scanner-1.2.0.tgz": "disse bytes er ikke et arkiv"},
        "ukendt arkivformat",
    ))
    out.append((
        "arkivet er beskadiget",
        {**FIXTURE, "site/downloads/mahope-eaa-scanner-1.2.0.tgz": b"\x1f\x8b\x08\x00" + b"\x00" * 40},
        "kan ikke åbnes som arkiv",
    ))
    return out


def negative_controls() -> list[tuple[str, dict[str, object], tuple[Product, ...]]]:
    """Scenarier der skal VÆRE GRØNNE, fordi porten ikke skal gribe i dem.

    Samme pointe som opgave 13, 15, 16 og 17: en mutation der fanger en fejl
    uden at have set den fanget, er ingen bevismålstyring. Her er den fælde
    `inner` kan falde i: hvis porten kræver en indre versionserklæring også for
    et produkt der erklærer ingen, så fejler den de håndlavede arkiver uden
    grund — og så en fjerdes del af kundens downloads.
    """
    no_inner = tuple(
        replace(product, inner=()) if product.key == "eaa-scanner-npm" else product
        for product in PRODUCTS
    )
    # tgzen er her bevidst uden nogen indre versionserklæring overhovedet: kun
    # `package/cli.js`. Med `inner=()` skal porten tie om den.
    bare_tgz = {
        **FIXTURE,
        "site/downloads/mahope-eaa-scanner-1.2.0.tgz": {
            "format": "targz",
            "files": {"package/cli.js": "// ingen versionserklæring her\n"},
        },
    }
    return [("arkiv uden indre versionserklæring, erklæret som sådan", bare_tgz, no_inner)]


def self_test() -> int:
    base = Path(tempfile.mkdtemp(prefix="check_versions_"))
    failures: list[str] = []

    def collect(files: dict[str, object], name: str, products: tuple[Product, ...] = PRODUCTS) -> list[str]:
        root = base / name
        write_fixture(root, files)
        found, _versions = run(root, products)
        return found

    cases = scenarios()
    clean = negative_controls()

    # Positiv kontrol FØRST: de uændrede fixture skal være grønne. Ellers ved vi
    # ikke om mutationerne overhovedet betyder noget.
    control = collect(FIXTURE, "_control")
    if control:
        failures.append(f"positiv kontrol: fixture gav {control}")

    for index, (name, files, expected) in enumerate(cases):
        found = collect(files, f"case{index:02d}")
        if not any(expected in problem for problem in found):
            failures.append(f"{name}: forventede {expected!r}, fik {found}")

    for index, (name, files, products) in enumerate(clean):
        found = collect(files, f"clean{index:02d}", products)
        if found:
            failures.append(f"negativ kontrol ({name}): forventede ingen fund, fik {found}")

    # Og de rigtige filer skal være grønne, ellers gater vi det forkerte.
    real, _versions = run(ROOT)
    if real:
        failures.append(f"de rigtige filer fejler: {real}")

    shutil.rmtree(base, ignore_errors=True)
    if failures:
        for failure in failures:
            print(f"FEJL: {failure}")
        print(f"\ncheck_versions --self-test: {len(failures)} fejl")
        return 1
    print(
        f"check_versions --self-test: OK ({len(cases)} mutationer + "
        f"{len(clean)} negativ kontrol + positiv kontrol + rigtige filer)"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--self-test" in argv:
        return self_test()
    found, versions = run(ROOT)
    for product in PRODUCTS:
        print(f"  {product.key:<24} {versions.get(product.key, '?'):<10} {product.canonical}")
    if found:
        print(f"\ncheck_versions: {len(found)} fund")
        for problem in found:
            print(f"  - {problem}")
        return 1
    print(f"\ncheck_versions: OK ({len(PRODUCTS)} produkter, én versionskilde hver)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
