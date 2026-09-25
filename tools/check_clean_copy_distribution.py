#!/usr/bin/env python3
"""Gate for de publicerede Clean Copy-arkiver: de skal være den aktuelle kode.

Opgave 7 del 2 punkt 2 i `IMPLEMENTATION_PLAN.md`. Del 1 og 2 rettede
licensklienterne i `extension-clean-copy/`, `extension-clean-copy-firefox/` og
`obsidian-plugin/`, men `site/downloads/*.zip` — den kode en køber henter — var
stadig den gamle version med det døde `hermes-passiv.pages.dev`-endepunkt og
uden `product`. Uden denne gate kommer det til at ske igen, fordi intet holdt
arkiverne på linje med kilden.

Gaten fejler ved:

1. Et publiceret arkiv der mangler, eller som afviger fra en regeneration af
   kilden (`tools/build_clean_copy_archives.py` er deterministisk).
2. En kildefil i et arkiv der mangler, eller som afviger fra kilden, så arkivet
   ikke bærer den kode, der er testet.
3. En kilde-`manifest.json` uden version, eller en Obsidian-`versions.json` der
   ikke kender den udgave, der publiceres.
4. Et arkiv med den døde vært i en licenskald, eller uden `product` — altså præcis
   den fejl, del 1 og 2 fjernede fra kilden.
5. En side i `site/` der linker på et arkiv, der ikke findes.
6. En side der stadig viser en gammel udgave af et af de tre produkter.
7. En `dist/`-kopi af et arkiv der afviger fra det publicerede (springes over,
   hvis intet er bygget).

    python3 tools/check_clean_copy_distribution.py
    python3 tools/check_clean_copy_distribution.py --self-test

Udgivelse af en ny udgave: se docstringen i `tools/build_clean_copy_archives.py`.
Sider, der nævner en tidligere udgave som feature-historik, skal stå i
`HISTORICAL_VERSIONS` — ellers fejler gaten, fordi den ikke kan skelne en
historiske omtale fra en gammel download.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_clean_copy_archives import (  # noqa: E402
    TARGETS,
    archive_name,
    build_archive,
    destinations,
    manifest_version,
    stale_archives,
)

ROOT = Path(__file__).resolve().parent.parent
DEAD_HOST = "hermes-passiv.pages.dev"
PRODUCT = "clean-copy-pro"

# Sider der linker på de publicerede arkiver. Findes automatisk i `check_pages`;
# listen bruges kun til at slå den korrekte fejlmeddelelse ud.
VERSION_TOKEN = re.compile(r"(?<![\w.])(?:[vV])?(\d+\.\d+\.\d+)(?![\w.])")
VERSION_CONTEXT = re.compile(r"clean[- ]copy|obsidian|softwareVersion|covers|version", re.I)

# Omtaler af en tidligere udgave som feature-historik. Alt andet end den aktuelle
# udgave på en af siderne er en fejl.
HISTORICAL_VERSIONS: dict[str, set[str]] = {
    "site/blog/install-obsidian-plugin-clean-copy.html": {"1.0.8", "1.0.9"},
    "site/da/blog/installer-clean-copy-obsidian.html": {"1.0.8", "1.0.9"},
    "tools/make_blog_da_mirrors_461.py": {"1.0.8", "1.0.9"},
}


# --------------------------------------------------------------------------
# Indlæsning
# --------------------------------------------------------------------------
def read_text(rel: str) -> str | None:
    path = ROOT / rel
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def site_pages() -> dict[str, str]:
    """Alle HTML-sider under `site/` der nævner et Clean Copy-arkiv."""
    pages: dict[str, str] = {}
    for path in sorted((ROOT / "site").rglob("*.html")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"clean-copy[a-z-]*-v\d+\.\d+\.\d+\.zip", text):
            pages[str(path.relative_to(ROOT))] = text
    return pages


def archive_members(payload: bytes) -> dict[str, bytes] | None:
    try:
        with zipfile.ZipFile(BytesIO(payload)) as zf:
            return {info.filename: zf.read(info.filename) for info in zf.infolist()}
    except (zipfile.BadZipFile, OSError):
        return None


def load() -> dict:
    """Alt gaten har brug for, som ren data, så selftesten kan mutere det."""
    archives: dict[str, dict] = {}
    for target in TARGETS:
        name = archive_name(target)
        expected = build_archive(target)
        published: dict[str, bytes | None] = {}
        for dest in destinations(target):
            path = dest.relative_to(ROOT)
            published[str(path)] = path.read_bytes() if path.is_file() else None
        source = ROOT / target["source"]
        source_members = {
            member: (source / member).read_bytes()
            for member in target["files"]
            if (source / member).is_file()
        }
        archives[target["key"]] = {
            "key": target["key"],
            "prefix": target["prefix"],
            "source": target["source"],
            "name": name,
            "version": manifest_version(source),
            "expected": expected,
            "published": published,
            "source_members": source_members,
            "expected_members": archive_members(expected),
            "stale": [str(p.relative_to(ROOT)) for p in stale_archives(target)],
        }

    versions_json = read_text("obsidian-plugin/versions.json")
    dist: dict[str, bytes | None] = {}
    for target in TARGETS:
        for dest in destinations(target):
            folder = str(dest.parent.relative_to(ROOT))
            for domain in ("cleancopy.tools", "mahope.tools"):
                path = ROOT / "dist" / domain / folder / dest.name
                # Kun en mappe der findes i dist tæller: ellers ville gaten kræve
                # et build for hvert site, arkivet ikke publiceres på.
                if path.parent.is_dir():
                    dist[str(path.relative_to(ROOT))] = (
                        path.read_bytes() if path.is_file() else None
                    )

    return {
        "archives": archives,
        "versions_json": versions_json,
        "pages": site_pages(),
        "dist": dist,
    }


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------
def check_manifests(archives: dict[str, dict]) -> list[str]:
    problems: list[str] = []
    for entry in archives.values():
        if not entry["version"]:
            problems.append(f"{entry['source']}/manifest.json har ingen version")
    obsidian = archives.get("obsidian")
    if obsidian and obsidian["version"]:
        return problems + check_versions_json(obsidian["version"])
    return problems


def check_versions_json(version: str, raw: str | None = None) -> list[str]:
    raw = read_text("obsidian-plugin/versions.json") if raw is None else raw
    if raw is None:
        return ["obsidian-plugin/versions.json mangler"]
    try:
        versions = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [f"obsidian-plugin/versions.json er ugyldig JSON: {exc}"]
    if not isinstance(versions, dict):
        return ["obsidian-plugin/versions.json er ikke et objekt"]
    if version not in versions:
        return [f"obsidian-plugin/versions.json kender ikke den publicerede udgave {version}"]
    return []


def check_archives(archives: dict[str, dict]) -> list[str]:
    """Det publicerede arkiv skal være præcis en regeneration af kilden."""
    problems: list[str] = []
    for entry in archives.values():
        for rel, payload in entry["published"].items():
            if payload is None:
                problems.append(f"{rel} mangler — kør tools/build_clean_copy_archives.py")
            elif payload != entry["expected"]:
                problems.append(f"{rel} afviger fra en regeneration af {entry['source']}")
        for rel in entry["stale"]:
            problems.append(f"{rel} er en forældet udgave, der stadig ligger publiceret")
    return problems


def check_members(archives: dict[str, dict]) -> list[str]:
    """Arkivet skal bære den kode, der ligger i kilden — ikke en gammel kopi."""
    problems: list[str] = []
    for entry in archives.values():
        payload = entry["published"].get(
            f"site/downloads/{entry['name']}"
        ) or next(iter(entry["published"].values()))
        members = archive_members(payload or b"")
        if members is None:
            problems.append(f"{entry['name']} kan ikke læses som et zip-arkiv")
            continue
        for member, expected_bytes in entry["source_members"].items():
            if member not in members:
                problems.append(f"{entry['name']} mangler {member}")
            elif members[member] != expected_bytes:
                problems.append(f"{entry['name']}/{member} afviger fra {entry['source']}/{member}")
        for member in members:
            if member != "version.txt" and member not in entry["source_members"]:
                problems.append(f"{entry['name']} indeholder {member}, som ikke er i kilden")
        version_txt = members.get("version.txt", b"").decode("utf-8", "replace")
        if entry["version"] not in version_txt:
            problems.append(f"{entry['name']}/version.txt nævner ikke udgaven {entry['version']}")
    return problems


def check_license_contract(archives: dict[str, dict]) -> list[str]:
    """Ingen død licensvært og intet licenskald uden `product` i et publiceret arkiv."""
    problems: list[str] = []
    for entry in archives.values():
        payload = entry["published"].get(f"site/downloads/{entry['name']}")
        members = archive_members(payload or b"")
        if members is None:
            continue
        for member, data in members.items():
            if not member.endswith(".js"):
                continue
            text = data.decode("utf-8", "replace")
            if DEAD_HOST in text:
                problems.append(f"{entry['name']}/{member} kalder den døde vært {DEAD_HOST}")
            if "api/license" in text and f"'{PRODUCT}'" not in text and f'"{PRODUCT}"' not in text:
                problems.append(f"{entry['name']}/{member} kalder licens-API'et uden product {PRODUCT}")
    return problems


def check_pages(pages: dict[str, str], published: set[str]) -> list[str]:
    """Alle links skal findes, og ingen side må vise en gammel udgave."""
    problems: list[str] = []
    for rel, text in pages.items():
        for name in re.findall(r"clean-copy[a-z-]*-v\d+\.\d+\.\d+\.zip", text):
            if name not in published:
                problems.append(f"{rel} linker på {name}, som ikke ligger publiceret")
        for match in VERSION_TOKEN.finditer(text):
            window = text[max(0, match.start() - 70):match.end() + 70]
            if not VERSION_CONTEXT.search(window):
                continue
            token = match.group(1)
            if token in published_versions() or token in HISTORICAL_VERSIONS.get(rel, set()):
                continue
            problems.append(f"{rel} viser udgaven {token}, som ikke er den publicerede")
    return problems


def published_versions() -> set[str]:
    return {manifest_version(ROOT / target["source"]) for target in TARGETS}


def check_dist(dist: dict[str, bytes | None], archives: dict[str, dict]) -> list[str]:
    problems: list[str] = []
    sources: dict[str, bytes] = {}
    for entry in archives.values():
        for rel, payload in entry["published"].items():
            if payload is not None:
                sources[Path(rel).name] = payload
    for rel, payload in dist.items():
        name = Path(rel).name
        if payload is None:
            problems.append(f"{rel} mangler i dist — dist/ er fra en ældre build, "
                            f"kør python3 build_sites.py")
        elif name not in sources:
            problems.append(f"{rel} er bygget fra et arkiv, der ikke ligger publiceret")
        elif payload != sources[name]:
            problems.append(f"{rel} afviger fra det publicerede arkiv")
    return problems


def run(data: dict) -> list[str]:
    archives = data["archives"]
    return (
        check_manifests(archives)
        + check_archives(archives)
        + check_members(archives)
        + check_license_contract(archives)
        + check_pages(data["pages"], {entry["name"] for entry in archives.values()})
        + check_dist(data["dist"], archives)
    )


# --------------------------------------------------------------------------
# Selftest
# --------------------------------------------------------------------------
def self_test() -> int:
    """Bevis at gaten fanger hver fejlform, den siger at fange."""
    data = load()
    archives = data["archives"]
    published = {entry["name"] for entry in archives.values()}
    pages = data["pages"]
    chrome = archives["chrome"]
    chrome_name = chrome["name"]

    def mutated_archive(key: str, replacement: bytes) -> dict[str, dict]:
        copy = {k: dict(v) for k, v in archives.items()}
        entry = dict(copy[key])
        entry["published"] = {
            rel: (replacement if rel == f"site/downloads/{entry['name']}" else payload)
            for rel, payload in entry["published"].items()
        }
        copy[key] = entry
        return copy

    drifted = build_archive(dict(next(t for t in TARGETS if t["key"] == "chrome"),
                                 files=["background.js", "manifest.json"]))
    without_product = build_archive(dict(
        next(t for t in TARGETS if t["key"] == "chrome"),
        files=["background.js", "manifest.json", "license.js"]))
    without_product = _replace_member(
        without_product, "license.js",
        b"var API_BASE = 'https://mahope.tools/api/license';\nvar PRODUCT = '';\n")
    dead_host = _replace_member(
        build_archive(dict(next(t for t in TARGETS if t["key"] == "chrome"),
                           files=["background.js", "manifest.json", "license.js"])),
        "license.js", b"var API_BASE = 'https://hermes-passiv.pages.dev/api/license';\n")

    scenarios: list[tuple[str, list[str]]] = [
        ("et kilde-manifest uden version",
         check_manifests({**archives, "chrome": {**chrome, "version": ""}})),
        ("en Obsidian-versions.json der ikke kender udgaven",
         check_versions_json("9.9.9")),
        ("et publiceret arkiv der mangler",
         check_archives({**archives, "chrome": {
             **chrome, "published": {rel: None for rel in chrome["published"]}}})),
        ("et publiceret arkiv der afviger fra kilden",
         check_archives(mutated_archive("chrome", drifted))),
        ("en forældet udgave der stadig ligger publiceret",
         check_archives({**archives, "chrome": {**chrome, "stale": ["site/downloads/clean-copy-v0.0.1.zip"]}})),
        ("et arkiv der mangler en kildefil",
         check_members(mutated_archive("chrome", drifted))),
        ("et arkiv med en kildefil der afviger fra kilden",
         check_members(mutated_archive("chrome", _replace_member(
             build_archive(dict(next(t for t in TARGETS if t["key"] == "chrome"),
                                files=["background.js", "manifest.json", "license.js"])),
             "license.js", "// lokalt ændret\n".encode("utf-8"))))),
        ("et arkiv med en ekstra fil, der ikke er i kilden",
         check_members(mutated_archive("chrome", _append_member(
             build_archive(dict(next(t for t in TARGETS if t["key"] == "chrome"),
                                files=["background.js", "manifest.json", "license.js"])),
             "hemmelig.js", b"x\n")))),
        ("et arkiv med den døde licensvært",
         check_license_contract(mutated_archive("chrome", dead_host))),
        ("et arkiv der kalder licens-API'et uden product",
         check_license_contract(mutated_archive("chrome", without_product))),
        ("en side der linker på et arkiv, der ikke findes",
         check_pages({"site/downloads.html": f'<a href="/downloads/{chrome_name}">x</a>'},
                     set() if chrome_name not in published else set())),
        ("en side der viser en gammel udgave",
         check_pages({"site/downloads.html": f'<p>Clean Copy v0.0.1</p>'}, published)),
        ("en side der viser den aktuelle udgave (skal ikke fejle)",
         check_pages({"site/downloads.html": f'<p>Clean Copy v{chrome["version"]}</p>'}, published)),
        ("en dist-kopi der afviger fra det publicerede arkiv",
         check_dist({f"dist/mahope.tools/downloads/{chrome_name}": b"drift"}, archives)),
        ("en dist-kopi der mangler",
         check_dist({f"dist/mahope.tools/downloads/{chrome_name}": None}, archives)),
    ]

    missed = [label for label, problems in scenarios if not problems and "skal ikke fejle" not in label]
    for label in missed:
        print(f"SELFTEST FEJLER: {label} blev ikke fanget")

    green_problems = run(data)
    for problem in green_problems:
        print(f"SELFTEST FEJLER: den rigtige kode fejler: {problem}")

    negative = [label for label, problems in scenarios
                if not problems and "skal ikke fejle" not in label]
    print(f"clean copy-distribution: {len(scenarios) - len(negative)}/{len(scenarios)} "
          f"fejlformer fanget, {len(green_problems)} problemer på den rigtige kode")
    return 1 if missed or green_problems else 0


def _replace_member(payload: bytes, member: str, data: bytes) -> bytes:
    with zipfile.ZipFile(BytesIO(payload)) as zf:
        members = {info.filename: zf.read(info.filename) for info in zf.infolist()}
    members[member] = data
    return _repack(members)


def _append_member(payload: bytes, member: str, data: bytes) -> bytes:
    with zipfile.ZipFile(BytesIO(payload)) as zf:
        members = {info.filename: zf.read(info.filename) for info in zf.infolist()}
    members[member] = data
    return _repack(members)


def _repack(members: dict[str, bytes]) -> bytes:
    from build_clean_copy_archives import ZIP_EPOCH

    stream = BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, date_time=ZIP_EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0o644 << 16
            zf.writestr(info, members[name])
    return stream.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="bevis at gaten fanger hver fejlform, den siger at fange")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    data = load()
    if not data["pages"]:
        print("FEJL: ingen side i site/ linker på et Clean Copy-arkiv", file=sys.stderr)
        return 1
    problems = run(data)
    for problem in problems:
        print(f"FEJL: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"clean copy-distribution OK — {len(data['archives'])} arkiver, "
          f"{len(data['pages'])} sider, publiceret = regeneration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
