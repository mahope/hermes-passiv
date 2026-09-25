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

import json
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import mini_toml  # noqa: E402

SEMVER = re.compile(r"\d+\.\d+\.\d+")
EXACT_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
DOWNLOADS = "site/downloads.html"


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
    ),
    Product(
        key="eaa-scanner-npm",
        canonical="scanner/npm/eaa-scanner/package.json",
        artifacts=(
            ("site/downloads/mahope-eaa-scanner-*.tgz", "site/downloads/mahope-eaa-scanner-{version}.tgz"),
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


def toml_version(root: Path, rel: str, report: Report) -> str | None:
    """`[project] version` — læst med `loads(text)`.

    Ikke `load(path)`: den indlejrede `tomllib.load` kræver et binært filobjekt,
    mens `mini_toml.load` tager en `Path`. `loads` findes i begge, så vejen er
    den samme på 3.9 og 3.12 — samme løsning som opgave 13 fandt i CI.
    """
    raw = read(root / rel)
    if raw is None:
        return None
    try:
        data = mini_toml.loads(raw, root / rel)
    except (mini_toml.TOMLDecodeError, ValueError) as exc:
        report.add(f"{rel}: kan ikke læses som TOML ({exc})")
        return None
    version = data.get("project", {}).get("version")
    return None if version is None else str(version)


def json_version(root: Path, rel: str, path: str, report: Report) -> str | None:
    raw = read(root / rel)
    if raw is None:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        report.add(f"{rel}: kan ikke læses som JSON ({exc})")
        return None
    for step in path.split("."):
        if not isinstance(data, dict):
            return None
        key = "" if step == '""' else step
        if key not in data:
            return None
        data = data[key]
    return str(data) if isinstance(data, (str, int, float)) else None


def source_version(root: Path, rel: str, report: Report) -> str | None:
    if rel.endswith(".toml"):
        return toml_version(root, rel, report)
    if rel.endswith(".json"):
        return json_version(root, rel, "version", report)
    if rel.endswith(".py"):
        raw = read(root / rel)
        if raw is None:
            return None
        match = re.search(r"""^__version__\s*=\s*["']([^"']+)["']""", raw, re.MULTILINE)
        return match.group(1) if match else None
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


def check_download_page(root: Path, report: Report) -> None:
    """Download-siden skal love den version der faktisk kan hentes."""
    raw = read(root / DOWNLOADS)
    if raw is None:
        report.add(f"{DOWNLOADS}: mangler")
        return
    for product in PRODUCTS:
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


def run(root: Path) -> tuple[list[str], dict[str, str]]:
    report = Report()
    check_single_source(root, report)
    for product in PRODUCTS:
        check_product(root, product, report)
    check_download_page(root, report)
    return report.problems, report.versions


# --------------------------------------------------------------------------
# Selftest
# --------------------------------------------------------------------------

#: Ét komplet fixture: alle otte produkter, alle spejle, alle ni arkiver og en
#: downloads-side der kun nævner de aktuelle versioner. Mutationerne sker her,
#: så hver enkelt fejl måtte kun have ÉN årsag.
FIXTURE: dict[str, str] = {
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
    "site/downloads/clean-copy-v1.5.3.zip": "zip",
    "site/downloads/clean-copy-firefox-v1.5.3.zip": "zip",
    "site/downloads/clean-copy-obsidian-v1.0.10.zip": "zip",
    "site/downloads/eaa-scanner-desktop-src-1.3.3.zip": "zip",
    "site/downloads/eaa_scanner-1.2.0-py3-none-any.whl": "whl",
    "site/downloads/eaa_scanner-1.2.0.tar.gz": "tar",
    "site/downloads/mahope-eaa-scanner-1.2.0.tgz": "tgz",
    "site/downloads/page-profile/page-profile-1.2.0.tar.gz": "tar",
    "site/downloads/site-icons/site-icons-1.0.0.tar.gz": "tar",
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


def write_fixture(root: Path, files: dict[str, str]) -> None:
    for rel, body in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")


def edit(files: dict[str, str], rel: str, old: str, new: str) -> dict[str, str]:
    out = dict(files)
    if old not in out[rel]:
        raise AssertionError(f"selftest: {rel} indeholder ikke {old!r}")
    out[rel] = out[rel].replace(old, new)
    return out


def scenarios() -> list[tuple[str, dict[str, str], str]]:
    """(navn, mutation, forventet fejl)."""
    out: list[tuple[str, dict[str, str], str]] = []

    out.append(("kanonisk fil mangler", {k: v for k, v in FIXTURE.items() if k != "extension-clean-copy/manifest.json"}, "mangler eller har ingen aflæselig version"))
    out.append(("version er ikke x.y.z", edit(FIXTURE, "extension-clean-copy/manifest.json", '"1.5.3"', '"1.5.3-rc1"'), "er ikke x.y.z"))
    out.append(("arkiv mangler", {k: v for k, v in FIXTURE.items() if k != "site/downloads/clean-copy-v1.5.3.zip"}, "kan ikke hente den version kilden er på"))

    stale = dict(FIXTURE)
    stale["site/downloads/clean-copy-v1.5.2.zip"] = "zip"
    out.append(("gammelt arkiv i mappen", stale, "gammelt arkiv i publiceringsmappen"))

    stale_dep = dict(FIXTURE)
    stale_dep["site/downloads/eaa_scanner-1.1.0-py3-none-any.whl"] = "whl"
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
    return out


def self_test() -> int:
    base = Path(tempfile.mkdtemp(prefix="check_versions_"))
    failures: list[str] = []

    def collect(files: dict[str, str], name: str) -> list[str]:
        root = base / name
        write_fixture(root, files)
        found, _versions = run(root)
        return found

    cases = scenarios()

    # Positiv kontrol FØRST: de uændrede fixture skal være grønne. Ellers ved vi
    # ikke om mutationerne overhovedet betyder noget.
    control = collect(FIXTURE, "_control")
    if control:
        failures.append(f"positiv kontrol: fixture gav {control}")

    for index, (name, files, expected) in enumerate(cases):
        found = collect(files, f"case{index:02d}")
        if not any(expected in problem for problem in found):
            failures.append(f"{name}: forventede {expected!r}, fik {found}")

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
    print(f"check_versions --self-test: OK ({len(cases)} mutationer + positiv kontrol + rigtige filer)")
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
