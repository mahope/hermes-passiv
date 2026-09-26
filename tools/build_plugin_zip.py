#!/usr/bin/env python3
"""Byg `site/eaa-compliance-scanner.zip` af `scanner/wp-plugin/`.

Baggrunden er opgave 85: zip'en var en ældre build af motoren. Kilden havde
seks regler mere end den publicerede fil, og **siden talte 16, fordi den talte
det den lige gjorde**. Det tal var ikke en skrivefejl — det var sandt for den
fil kunden hentede, og falsk for den koden vi vedligeholder. Uden et byggetrin
kommer de to fra hinanden igen, og ingen opdager det, fordi en regel mere i en
kilde ikke ser ud som en fejl.

Derfor er bygningen et program og ikke en huskeliste:

- **Deterministisk.** Alle tidsstempler er fastsat, og posterne sorteres. Uden
  det ville zip'en få en ny checksum for hver kørsel, og porten kunne ikke
  skelne en reel ændring fra en ny byggetid.
- **Kun de tre filer.** Ikke mappa-struktur, skjulte filer eller `.DS_Store`.
  WordPress-plugin-arkivet skal indeholde præcis pluginens kode, så et kunstigt
  append i arkivet er umuligt at rette, når først det er lagt i et kundens
  `wp-content/plugins/`.

Kør: `python3 tools/build_plugin_zip.py [--check]`

`--check` bygger ikke, men siger om den committede zip er i sync med kilden.
Det er det, gaten bruger — porten skal aldrig selv skrive sit eget grundlag.
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO / "scanner" / "wp-plugin" / "eaa-compliance-scanner"
ZIP_PATH = REPO / "site" / "eaa-compliance-scanner.zip"

# De tre filer der udgør pluginet, i den rækkefølge de skal ligge i arkivet.
MEMBERS = (
    "eaa-compliance-scanner.php",
    "engine.php",
    "README.txt",
)

# Fast tidsstempel (2026-01-01 00:00). Ikke filernes mtime: en `git checkout`
# giver alle filer samme tid, og en redigering ændrer den. Denne værdi ændrer
# sig aldrig, så samme kode giver altid samme checksum.
FIXED_DATE = (2026, 1, 1, 0, 0, 0)

PREFIX = "eaa-compliance-scanner/"


def build() -> bytes:
    """Returnér zip'en som bytes, bygget af kildefilerne."""
    missing = [m for m in MEMBERS if not (SOURCE_DIR / m).is_file()]
    if missing:
        raise SystemExit(
            f"build_plugin_zip: mangler i {SOURCE_DIR}: {', '.join(missing)}")

    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in MEMBERS:
            info = zipfile.ZipInfo(PREFIX + name, date_time=FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            # 0o644: filerne skal kunne læses af webserveren efter unzip.
            info.external_attr = (0o644 & 0xFFFF) << 16
            zf.writestr(info, (SOURCE_DIR / name).read_bytes())
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="skriv ikke; exit 1 hvis zip'en ikke er i sync")
    args = ap.parse_args()

    data = build()

    if args.check:
        if not ZIP_PATH.is_file():
            print(f"FEJL: {ZIP_PATH.name} mangler — kør build_plugin_zip.py")
            return 1
        have = ZIP_PATH.read_bytes()
        if have == data:
            print(f"build_plugin_zip OK: {ZIP_PATH.name} er i sync med "
                  f"{len(MEMBERS)} kildefiler ({len(data)} byte)")
            return 0
        print(f"FEJL: {ZIP_PATH.name} afviger fra kilden. Den publicerede motor "
              f"er en anden end den vi vedligeholder — kør build_plugin_zip.py.")
        try:
            with zipfile.ZipFile(ZIP_PATH) as zf:
                drifted = [n for n in zf.namelist()
                           if not n.endswith("/")
                           and zf.read(n) != (SOURCE_DIR / n.split("/")[-1])
                           .read_bytes()]
        except (OSError, KeyError, zipfile.BadZipFile) as exc:
            drifted = [f"(arkivet er ikke læsbart: {exc})"]
        if drifted:
            # Navnene kan være ens og indholdet forskelligt, så "arkivet har /
            # kilden har" er ikke et svar. Sig hvilken fil der er ude af sync.
            print("  afviger i indhold: "
                  + ", ".join(d.split("/")[-1] for d in drifted))
        else:
            print("  filnavnene er ens, så forskellen er i arkivets struktur "
                  "(rejefølge, tidsstempler eller kompression).")
        return 1

    ZIP_PATH.write_bytes(data)
    print(f"build_plugin_zip: skrev {ZIP_PATH.name} — {len(data)} byte, "
          f"{len(MEMBERS)} filer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
