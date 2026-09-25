#!/usr/bin/env python3
"""Byg de publicerede Clean Copy-arkiver reproducerbart fra kilden.

Opgave 7 del 2 punkt 2 i `IMPLEMENTATION_PLAN.md`. `site/downloads/*.zip` er den
kode en køber faktisk henter, og de indeholdt den gamle licensklient med det døde
`hermes-passiv.pages.dev`-endepunkt og uden `product`. Uden dette script er der
intet, der holder et publiceret arkiv på linje med `extension-clean-copy/`,
`extension-clean-copy-firefox/` og `obsidian-plugin/`.

Arkiverne er deterministiske: samme kilde giver altid præcis samme bytes, så
`tools/check_clean_copy_distribution.py` kan kræve byte-identitet mellem
det publicerede arkiv og en regeneration. Det er sammePrincip som Page
Profile-gaten, bare for zips.

    python3 tools/build_clean_copy_archives.py           # byg og skift arkiver
    python3 tools/build_clean_copy_archives.py --check   # byg i hukommelse og sammenlign

Udgivelse af en ny udgave:

    1. Ret `version` i det relevante `manifest.json` (og `obsidian-plugin/versions.json`).
    2. Ret de sider, der linker på arkivet, så de peger på den nye udgave.
    3. `python3 tools/build_clean_copy_archives.py`
    4. `python3 tools/check_clean_copy_distribution.py`
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOWNLOADS = ROOT / "site/downloads"
EXTENSION_ZIPS = ROOT / "site/extension-zips"

# Fast tidspunkt for alle medlemmer. ZIP-formatet kan ikke gemme tidsstempler
# før 1980, og et fast tidspunkt er hele pointen: et arkiv bygget på en anden
# maskine eller en senere dato skal stadig have samme bytes.
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)

# Fælles filer for de to browserarkiver. `license.js` kom først med i del 2, så det
# gamle publicerede arkiv havde ikke den fil — uden den får options.html en 404.
BROWSER_FILES = [
    "background.js",
    "icons/icon128.png",
    "icons/icon16.png",
    "icons/icon48.png",
    "license.js",
    "manifest.json",
    "offscreen.html",
    "options.html",
    "options.js",
    "popup.html",
    "popup.js",
]

# Firefox-arkivet har altid medbragt licens og README.
FIREFOX_EXTRA = ["LICENSE", "README.md"]

# Obsidian-arkivet er selvkørende: main.js indlejrer både kernen og
# licensmodulet, så der skal kun med tre filer.
OBSIDIAN_FILES = ["main.js", "manifest.json", "styles.css"]

TARGETS = [
    {
        "key": "chrome",
        "source": "extension-clean-copy",
        "prefix": "clean-copy",
        "files": BROWSER_FILES,
        "extra_destinations": ["site/extension-zips"],
    },
    {
        "key": "firefox",
        "source": "extension-clean-copy-firefox",
        "prefix": "clean-copy-firefox",
        "files": BROWSER_FILES + FIREFOX_EXTRA,
        "extra_destinations": [],
    },
    {
        "key": "obsidian",
        "source": "obsidian-plugin",
        "prefix": "clean-copy-obsidian",
        "files": OBSIDIAN_FILES,
        "extra_destinations": [],
    },
]


def manifest_version(source: Path) -> str:
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    version = str(manifest.get("version", "")).strip()
    if not version:
        raise SystemExit(f"FEJL: {source}/manifest.json har ingen version")
    return version


def archive_name(target: dict) -> str:
    version = manifest_version(ROOT / target["source"])
    return f"{target['prefix']}-v{version}.zip"


def build_archive(target: dict) -> bytes:
    source = ROOT / target["source"]
    version = manifest_version(source)
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in target["files"]:
            path = source / name
            if not path.is_file():
                raise SystemExit(f"FEJL: {path} mangler — kan ikke bygge {target['key']}")
            info = zipfile.ZipInfo(name, date_time=ZIP_EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            # 0o644 uden Unix-bit, så arkivet er identisk uanset plattform.
            info.create_system = 0
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())
        # `version.txt` gør udgaven synlig inde i arkivet, så en køber kan se
        # hvilken udgave de har udpakket.
        info = zipfile.ZipInfo("version.txt", date_time=ZIP_EPOCH)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.create_system = 0
        info.external_attr = 0o644 << 16
        zf.writestr(info, f"{target['prefix']} {version}\n".encode("utf-8"))
    return stream.getvalue()


def destinations(target: dict) -> list[Path]:
    name = archive_name(target)
    return [DOWNLOADS / name] + [ROOT / d / name for d in target["extra_destinations"]]


def stale_archives(target: dict) -> list[Path]:
    """Publicerede arkiver i samme familie med en anden udgave end den aktuelle."""
    name = archive_name(target)
    stale: list[Path] = []
    for folder in [DOWNLOADS, *[ROOT / d for d in target["extra_destinations"]]]:
        for candidate in sorted(folder.glob(f"{target['prefix']}-v*.zip")):
            if candidate.name != name:
                stale.append(candidate)
    return stale


def check(target: dict) -> list[str]:
    problems: list[str] = []
    expected = build_archive(target)
    for dest in destinations(target):
        if not dest.is_file():
            problems.append(f"{dest.relative_to(ROOT)} mangler")
        elif dest.read_bytes() != expected:
            problems.append(f"{dest.relative_to(ROOT)} afviger fra en regeneration af kilden")
    for stale in stale_archives(target):
        problems.append(f"{stale.relative_to(ROOT)} er en forældet udgave, der stadig ligger publiceret")
    return problems


def write(target: dict) -> list[Path]:
    payload = build_archive(target)
    written: list[Path] = []
    for dest in destinations(target):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload)
        written.append(dest)
    for stale in stale_archives(target):
        stale.unlink()
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="byg i hukommelse og sammenlign med de publicerede arkiver")
    args = parser.parse_args()

    problems: list[str] = []
    for target in TARGETS:
        if args.check:
            problems += check(target)
            continue
        for dest in write(target):
            print(f"skrev {dest.relative_to(ROOT)} ({dest.stat().st_size} bytes)")

    if problems:
        for problem in problems:
            print(f"FEJL: {problem}", file=sys.stderr)
        return 1
    if args.check:
        print("clean copy-arkiver: publiceret = regeneration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
