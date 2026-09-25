#!/usr/bin/env python3
"""Byg det publicerede EAA-scanner-desktop-kildearkiv reproducerbart fra kilden.

Opgave 18 i `IMPLEMENTATION_PLAN.md`. Opgave 14 (`tools/check_versions.py`)
beviste, at `desktop/package.json`, `desktop/package-lock.json` og arkivets *navn*
alle sagde 1.3.3. Ingen af dem åbnede arkivet. Det gjorde porten grøn på et arkiv,
der indeholdt 1.3.0: lockfilens egen `version` var `1.3.0`, `electron-builder` stod
på `^25.0.0` — den advisory-remediering opgave 9 lavede i kilden, leveret uden om
kilden — og `engines` manglede helt.

Det er samme fejlform som opgave 10 og 15: en gaten der erklærer noget om en værdi
den aldrig læser det sted, værdien faktisk ligger. Derfor får arkivet nu den
behandling de tre Clean Copy-arkiver allerede har, i samme fil-form som
`tools/build_clean_copy_archives.py`:

    python3 tools/build_desktop_archive.py           # byg og skift arkivet
    python3 tools/build_desktop_archive.py --check   # byg i hukommelse og sammenlign

Determinismen er hele pointen: ZIP-formatet kan ikke gemme tidsstempler før 1980,
og membersættet, kompressionen og rettighederne er låst, så samme kilde giver
altid præcis samme bytes på en anden maskine og en senere dato. Uden det er
`--check` en løs sammenligning af to filer, der tilfældigvis er bygget samme dag.

Arkivet er et *kildearkiv*: kunden pakker det ud og byger selv. Derfor medtages
hele `desktop/` minus byggeoutput — `node_modules/` er en `npm ci`-artefakt på
30 MB, og `dist/` er Electron-packagerens resultat, ikke koden.

`--self-test` bygger et miniature-forkspace i en midlertidig mappe og kræver at
porten **fejler** på en række mutationer og **passerer** på en kilde der ikke er
rørt. Uden den positive kontrol er `--check` lige så lidt bevis som opgave 13,
15 og 17 måtte konstatere: en port, der siger "skal ikke fejle", uden at nogen
har set den fejle.

**Kendte begrænsning, opskrivet i stedet for skjult:** `--check` læser både
`desktop/` og det publicerede arkiv, men `deploy-sites.yml`s path-filter
udelukker med vilje `desktop/**` (opgave 14 og 16). En commit der *kun* retter
`desktop/package.json` udløser derfor ikke gaten. Gaten fanger enhver commit der
rører arkivet eller denne builder, og enhver kørsel lokalt. Se `❓ Til Mads` i
`IMPLEMENTATION_PLAN.md`.

    python3 tools/build_desktop_archive.py --self-test
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "desktop"
DOWNLOADS = ROOT / "site/downloads"

# Fast tidspunkt for alle medlemmer, samme som i `build_clean_copy_archives.py`.
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)

#: Byggeoutput der ikke skal med i et kildearkiv. `node_modules/` er resultatet
#: af `npm ci` — det er 30 MB, der genskabes af lockfilen i sekunder, og det
#: indeholder plattformsspecifik binærer der ikke kan virke på kundens maskine.
#: `dist/` er Electron-packagerens output, altså det færdige program.
EXCLUDED_DIRS = ("node_modules", "dist")


def package_version(source: Path) -> str:
    package = json.loads((source / "package.json").read_text(encoding="utf-8"))
    version = str(package.get("version", "")).strip()
    if not version:
        raise SystemExit(f"FEJL: {source}/package.json har ingen version")
    return version


def archive_name(source: Path) -> str:
    return f"eaa-scanner-desktop-src-{package_version(source)}.zip"


def members(source: Path) -> list[str]:
    """Kildefilerne i arkivet, sorteret så arkivet er reproducerbart.

    Sorteret på den relative sti med `/` som skilletegn, ikke på OS-stien: på
    macOS og Windows ville `sorted()` give forskellige rækkefølger, og så ville
    samme kilde give to forskellige arkiver.
    """
    out: list[str] = []
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        if relative.parts and relative.parts[0] in EXCLUDED_DIRS:
            continue
        out.append(relative.as_posix())
    return sorted(out)


def build_archive(source: Path) -> bytes:
    names = members(source)
    if not names:
        raise SystemExit(f"FEJL: {source} er tom — ville bygge et tomt arkiv")
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in names:
            info = zipfile.ZipInfo(name, date_time=ZIP_EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            # 0o644 uden Unix-bit, så arkivet er identisk uanset plattform.
            info.create_system = 0
            info.external_attr = 0o644 << 16
            zf.writestr(info, (source / name).read_bytes())
    return stream.getvalue()


def check(source: Path, downloads: Path | None = None) -> list[str]:
    folder = DOWNLOADS if downloads is None else downloads
    problems: list[str] = []
    expected = build_archive(source)
    name = archive_name(source)
    published = folder / name
    if not published.is_file():
        problems.append(f"{rel(published)} mangler")
    elif published.read_bytes() != expected:
        problems.append(
            f"{rel(published)} afviger fra en regeneration af {rel(source)}/ "
            f"— kunden henter en anden kode end den i repoet"
        )
    # Et arkiv fra en tidligere udgave i samme familie er en kunde, der stadig
    # kan hente gammel kode. Det samme princip som de Clean Copy-arkiver.
    for candidate in sorted(folder.glob("eaa-scanner-desktop-src-*.zip")):
        if candidate.name != name:
            problems.append(f"{candidate.name} er en forældet udgave, der stadig ligger publiceret")
    return problems


# --------------------------------------------------------------------------
# Selftest
# --------------------------------------------------------------------------

#: En kilde der ligner den rigtige: to filer, hvoraf den ene bærer versionen.
#: Lille nok til at en fejl i portens egen logik er synlig, stort nok til at
#: membersættet, `EXCLUDED_DIRS` og filnavnet alle er i spil.
SELF_TEST_SOURCE = {
    "package.json": '{\n  "name": "desktop",\n  "version": "1.3.3"\n}\n',
    "main.js": "console.log(1.3.3);\n",
    "node_modules/left-pad/index.js": "// 30 MB, der skal med igen\n",
    "dist/desktop-linux-x64/桌面": "// Electron-packagerens output\n",
}


def self_test() -> int:
    base = Path(tempfile.mkdtemp(prefix="build_desktop_archive_"))
    failures: list[str] = []

    def workspace(name: str, source_files: dict[str, str] | None = None) -> tuple[Path, Path]:
        source = base / name / "desktop"
        downloads = base / name / "site/downloads"
        for rel, body in (SELF_TEST_SOURCE if source_files is None else source_files).items():
            path = source / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        downloads.mkdir(parents=True, exist_ok=True)
        (downloads / archive_name(source)).write_bytes(build_archive(source))
        return source, downloads

    def run(name: str, source_files: dict[str, str] | None = None) -> list[str]:
        source, downloads = workspace(name, source_files)
        return check(source, downloads)

    # Positiv kontrol FØRST: en urørt kilde skal være grøn, ellers ved vi ikke
    # om mutationerne nogensinde har betydet noget.
    control = run("_control")
    if control:
        failures.append(f"positiv kontrol: uændret kilde fejlede med {control}")

    # Determinisme: samme kilde to gange skal give præcis samme bytes. Uden den
    # egenskab er `--check` afhængig af at buildet tilfældigvis sker samme dag.
    determinism_source, _ = workspace("_determinism")
    if build_archive(determinism_source) != build_archive(determinism_source):
        failures.append("determinisme: to builds af samme kilde gav forskellige bytes")

    # Determinisme alene fanger ikke en *ændret* tidskonstant: to builds i samme
    # proces er lige så ens hvad enten ZIP_EPOCH er 1980 eller 2020. Så konstanten
    # skal også testes for sin værdi, ellers er den bare en værdi ingen holder.
    if ZIP_EPOCH != (1980, 1, 1, 0, 0, 0):
        failures.append(f"ZIP_EPOCH er {ZIP_EPOCH} — ZIP-formatet kan ikke gemme tidsstempler før 1980")
    stamped = {info.date_time for info in read_infos(build_archive(determinism_source))}
    if stamped != {ZIP_EPOCH}:
        failures.append(f"medlemmer bærer tidsstemplet {stamped}, ikke ZIP_EPOCH")

    cases: list[tuple[str, list[str], str]] = []

    # 1. Den mutation der lå bag hele opgaven: en kildefil ændrer sig, men
    #    arkivet gør ikke.
    source, downloads = workspace("_stale_file")
    (downloads / archive_name(source)).write_bytes(build_archive(source))
    (source / "package-lock.json").write_text('{"version": "1.3.0"}\n', encoding="utf-8")
    cases.append((
        "arkivet er ældre end kilden",
        check(source, downloads),
        "afviger fra en regeneration",
    ))

    # 2. Samme fejlform, anden vegne: der er kommet en ny kildefil siden
    #    arkivet blev bygget, så kunden får ikke koden.
    source, downloads = workspace("_missing_file")
    (source / "scanner-core.js").write_text("// ny regel siden arkivet blev bygget\n", encoding="utf-8")
    cases.append((
        "en ny kildefil mangler i arkivet",
        check(source, downloads),
        "afviger fra en regeneration",
    ))

    # 3. Byggeoutput må ikke komme med — hvis `node_modules` slap med, ville et
    #    kunstigt eksempel være nok til at afvise portens egen undtagelse.
    source, downloads = workspace("_node_modules")
    leaked = [name for name in names_of(build_archive(source)) if name.startswith("node_modules/")]
    if leaked:
        cases.append((
            "node_nodes slap med i arkivet",
            [f"node_modules/{leaked} slap med i arkivet"],
            "slap med i arkivet",
        ))
    # Ellers: scenariet skal IKKE fejle. Det er her en unødigt streng undtagelse
    # ville have vist sig som en fejl.
    cases.append(("kilde uden byggeoutput er grøn", check(source, downloads), ""))

    # 4. Et forældet arkiv i samme familie ligger stadig publiceret.
    source, downloads = workspace("_stale_sibling")
    (downloads / "eaa-scanner-desktop-src-1.3.0.zip").write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    cases.append((
        "forældet arkiv ligger stadig publiceret",
        check(source, downloads),
        "forældet udgave",
    ))

    # 5. Arkivet mangler helt.
    source, downloads = workspace("_missing_archive")
    (downloads / archive_name(source)).unlink()
    cases.append((
        "arkivet mangler",
        check(source, downloads),
        "mangler",
    ))

    for index, (name, found, expected) in enumerate(cases):
        if not expected:
            if found:
                failures.append(f"{name}: forventede ingen fejl, fik {found}")
            continue
        if not any(expected in problem for problem in found):
            failures.append(f"{name}: forventede {expected!r}, fik {found}")

    shutil.rmtree(base, ignore_errors=True)
    if failures:
        for failure in failures:
            print(f"FEJL: {failure}")
        print(f"\nbuild_desktop_archive --self-test: {len(failures)} fejl")
        return 1
    caught = sum(1 for _n, _f, expected in cases if expected)
    print(f"build_desktop_archive --self-test: OK ({caught} mutationer fanget, "
          f"positiv kontrol + determinisme grøn, 1 falsk-positiv-test)")
    return 0


def names_of(payload: bytes) -> list[str]:
    with zipfile.ZipFile(BytesIO(payload)) as zf:
        return zf.namelist()


def read_infos(payload: bytes) -> list[zipfile.ZipInfo]:
    with zipfile.ZipFile(BytesIO(payload)) as zf:
        return zf.infolist()


def rel(path: Path) -> str:
    """Stien relativ til repoet, eller stien som den er.

    Selftesten bygger workspaces i en midlertidig mappe, og `relative_to` ville
    kaste `ValueError` på enhver sti uden for repoet. En fejlmeddelelse må aldrig
    være den, der får porten til at styrte.
    """
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="byg i hukommelse og sammenlign med det publicerede arkiv")
    parser.add_argument("--self-test", action="store_true",
                        help="mutationer porten skal fange, plus positiv kontrol og determinisme")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if args.check:
        problems = check(SOURCE)
        if problems:
            for problem in problems:
                print(f"FEJL: {problem}", file=sys.stderr)
            return 1
        print(f"desktop-arkiv: publiceret = regeneration af {rel(SOURCE)}/ "
              f"({len(members(SOURCE))} filer)")
        return 0

    payload = build_archive(SOURCE)
    name = archive_name(SOURCE)
    destination = DOWNLOADS / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    print(f"skrev {rel(destination)} ({destination.stat().st_size} bytes)")

    for candidate in sorted(DOWNLOADS.glob("eaa-scanner-desktop-src-*.zip")):
        if candidate.name != name:
            candidate.unlink()
            print(f"fjernede forældet {rel(candidate)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
