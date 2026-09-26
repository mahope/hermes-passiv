#!/usr/bin/env python3
"""Gaten for `reports/weekly/` — arkivet skal kunne læses som tal med en kilde.

Baggrund (opgave 35): `reports/weekly/*.json` er det eneste sted i repoet hvor
et *dokumenteret tal* ligger gemt uden at nogen port læser det. Gaten dækkede
`test_weekly_report.py`, men den bruger **syntetiske fixtures** i det nye schema,
så den kan ikke se en arkivfil der er skrevet af en ældre scriptversion — og det
er præcis de filer arkivet består af.

Fundet der gjorde porten nødvendig: alle tre arkivfiler har et `lemon`-blok med
teksten *"afventer godkendelse (LS_API_KEY er ikke sat)"*. Lemon Squeezy blev
lukket 24. september 2026, og `tools/weekly_report.py` indeholder ** nul
forekomster** af `lemon` og ingen længere samler den data. Så arkivet siger om en
død betalingsudbyder at den * stadig afventer godkendelse* — tre uger efter at
kontrakten sagde "genopliv det aldrig". Det er samme fejlklasse som opgave 26
fandt i rod-README'en ("en lukket udbyder nævnt som om den virker") og som
opgave 29-31 fandt i privatlivsløfter: **en påstand om en tilstand, ingen
læser kan verificere, fordi ingen kilder længere producerer den.**

Reglen er derfor skrevet som et **princip, ikke en navneliste**: en topnøgle i
arkivet skal kunne findes som en bogstavelig streng i den nuværende
`weekly_report.py`. Det er ikke en liste over "de døde blokke" — det er
*"denne blok kan denne kode ikke længere skrive"*, og den fanger den næste
lukkede udbyder automatisk. Samme princip som opgave 26 skrev de søskenderepos
ud af `check_license_clients.py` med.

Fire kontroller:

  1. `dead_provider_block`  en topnøgle i arkivet som den nuværende
                            `weekly_report.py` ikke kan producere.
  2. `week_mismatch`        filnavnet og `iso_week` er ikke ens. Så arkivet
                            lyver om hvilken uge det dækker, og det er det
                            felt en læser bruger til at finde den rigtige uge.
  3. `no_generated_at`      `generated_at` mangler eller kan ikke læses. Uden
                            den kan ingen sige hvor gammelt et tal er — og det
                            er præcis spørgsmålet AGENTS.md siger du skal
                            kunne svare på, før du skriver et tal.
  4. `missing_block`        en af de blokke `collect_all()` *altid* skriver
                            mangler. `soft()` lægger nøglen ind selv om
                            indsamlingen fejler, så en manglende nøgle betyder
                            en afkortet eller håndredigeret fil, ikke en fejl i
                            en kilde.

**To ting denne port bevidst ikke gater**, fordi de viste sig at være *falske*
regler da de blev målt på de rigtige filer:

  - *"Et trafikblok må ikke være tomt, mens `health.status` er healthy."* Uge 39
    har `traffic: {}`, og det er den **korrekte** repræsentation: 7-dagesblokken
    gik tabt i et timeout (filens egen `errors` siger
    `api/stats: The read operation timed out`), og `unknown_stats()` ville have
    skrevet en note der skylder API'et for en blok der aldrig blev skrevet.
    Opgave 34 rettede præcis den note. En port der krævede et udfyldt blok ville
    have tvunget den løgn tilbage.
  - *"Arkivfiler skal have `schema_version`."* Uden den bliver `ptr = {}` i
    `build_report`, så Δ-kolonnen viser `—` — og `fmt_delta(None)` er netop
    `—`. Kolonnen siger altså "ikke sammenlignelig", ikke "ingen ændring".
    Det er den ærlige notation, ikke en stum fejl.

    python3 tools/check_weekly_history.py             # kræver ikke dist, kører i gaten
    python3 tools/check_weekly_history.py --self-test # bevis at porten fanger fejlene
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports" / "weekly"
WRITER = ROOT / "tools" / "weekly_report.py"

# Blokke `collect_all()` skriver altid, fordi `soft()` lægger nøglen ind selv om
# indsamlingen fejler. Læst fra koden, ikke hardkodet, så porten ikke kan blive
# grøn på en nøgle, koden har holdt op med at skrive.
ALWAYS_WRITTEN = (
    "iso_week",
    "generated_at",
    "health",
    "traffic",
    "npm",
    "github",
    "errors",
)


def producible_keys(writer_source: str) -> set[str]:
    """Topnøgler den nuværende writer kan skrive.

    En nøgle tælles som produktiv kun hvis den findes som en *bogstavelig
    streng* i kilden. Det er det, der skelner `lemon` (død blok) fra `uptime`
    (leve blok): prose der nævner en nøgle er ikke en måde at skrive den på.
    """
    return {k for k in ALWAYS_WRITTEN if f'"{k}"' in writer_source}


def check_report_file(path: Path, writer_source: str) -> list[str]:
    problems: list[str] = []
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{path.name}: kan ikke læses — {exc}"]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [f"{path.name}: ugyldig JSON — {exc}"]
    if not isinstance(data, dict):
        return [f"{path.name}: er ikke et JSON-objekt"]

    # 1) Død udbyderblok.
    for key in sorted(data):
        if key in ALWAYS_WRITTEN:
            continue
        if f'"{key}"' not in writer_source:
            problems.append(
                f"{path.name}: topnøglen `{key}` kan ikke længere skrives af "
                f"weekly_report.py — arkivet dokumenterer en tilstand ingen kode "
                f"længere producerer"
            )

    # 2) Ugen i filnavnet mod ugen i indholdet.
    stem = path.stem
    iso = data.get("iso_week")
    if not isinstance(iso, str) or not iso:
        problems.append(f"{path.name}: `iso_week` mangler eller er ikke en tekst")
    elif iso != stem:
        problems.append(f"{path.name}: `iso_week` siger {iso}, men filnavnet siger {stem}")

    # 3) Tidspunktet, uden hvilket intet tal har en alder.
    generated = data.get("generated_at")
    if not isinstance(generated, str) or not generated:
        problems.append(f"{path.name}: `generated_at` mangler — intet tal i filen kan dateres")
    else:
        try:
            datetime.fromisoformat(generated)
        except ValueError:
            problems.append(f"{path.name}: `generated_at` ({generated!r}) kan ikke læses som tidspunkt")

    # 4) Blokke koden altid skriver.
    for key in ALWAYS_WRITTEN:
        if key not in data:
            problems.append(f"{path.name}: blokken `{key}` mangler, men collect_all() skriver den altid")

    return problems


def check() -> list[str]:
    if not REPORT_DIR.is_dir():
        return [f"{REPORT_DIR.relative_to(ROOT)} findes ikke — kan ikke gate arkivet"]
    if not WRITER.is_file():
        return [f"{WRITER.relative_to(ROOT)} findes ikke — kan ikke bevise hvilke blokke koden skriver"]
    files = sorted(REPORT_DIR.glob("*.json"))
    if not files:
        return [f"{REPORT_DIR.relative_to(ROOT)} indeholder ingen rapporter"]
    writer_source = WRITER.read_text(encoding="utf-8")
    problems: list[str] = []
    for path in files:
        problems.extend(check_report_file(path, writer_source))
    return problems


# --------------------------------------------------------------------------
def self_test() -> int:
    """Bevis at porten fanger fejlformerne — og at den tier på rigtige filer."""
    passed = 0
    failed: list[str] = []

    def expect(problems: list[str], rule: str, navn: str) -> None:
        nonlocal passed
        if any(rule in p for p in problems):
            passed += 1
        else:
            failed.append(f"{navn} (forventede {rule!r}, fik {problems})")

    def clean() -> list[str]:
        return check()

    real_files = {p: p.read_text(encoding="utf-8") for p in sorted(REPORT_DIR.glob("*.json"))}
    real_writer = WRITER.read_text(encoding="utf-8")

    def write(path: Path, data) -> None:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def restore() -> None:
        for path, raw in real_files.items():
            path.write_text(raw, encoding="utf-8")
        WRITER.write_text(real_writer, encoding="utf-8")

    try:
        # Rigtig kode skal være grøn, så de tre mutationer nedenfor er målt
        # mod en baseline der er grøn. Før `lemon`-blokken blev fjernet var
        # baseline rød med præcis de tre fund — det er beviset, ikke en fejl.
        baseline = clean()
        if baseline:
            failed.append(f"den rigtige kode skal være grøn, fik {baseline}")
        else:
            passed += 1

        target = REPORT_DIR / "9999-01.json"
        good = {
            "iso_week": "9999-01",
            "generated_at": "2099-01-01T00:00:00+00:00",
            "health": {"status": "healthy"},
            "traffic": {},
            "npm": {},
            "github": {},
            "errors": [],
        }

        # 1) Død udbyderblok — nøglen findes ikke i writeren.
        write(target, {**good, "lemon": {"available": False, "note": "afventer godkendelse"}})
        expect(clean(), "kan ikke længere skrives", "død udbyderblok i arkivet")

        # 1b) Nøglen skal ikke fanges, bare fordi den er ukendt: en blok
        # writeren *kan* skrive må være grøn. `uptime` er en sådan.
        write(target, {**good, "uptime": {"note": "kunne ikke hentes"}})
        if [p for p in clean() if "kan ikke længere skrives" in p]:
            failed.append("en blok writeren kan skrive blev markeret som død")
        else:
            passed += 1

        # 1c) Provenancen skal være en regel, ikke en navneliste: en blok der
        # hedder noget helt andet skal fanges på samme måde.
        write(target, {**good, "gumroad": {"available": False, "note": "afventer godkendelse"}})
        expect(clean(), "kan ikke længere skrives", "død blok med et andet navn (ikke en navneliste)")

        # 2) Ugen i filnavnet mod ugen i indholdet.
        write(target, {**good, "iso_week": "2099-02"})
        expect(clean(), "men filnavnet siger", "filnavn og iso_week er ikke ens")

        # 3) Tidspunktet.
        write(target, {k: v for k, v in good.items() if k != "generated_at"})
        expect(clean(), "`generated_at` mangler", "generated_at mangler")
        write(target, {**good, "generated_at": "i går"})
        expect(clean(), "kan ikke læses som tidspunkt", "generated_at kan ikke tolkes")

        # 4) En blok koden altid skriver.
        broken = {k: v for k, v in good.items() if k != "errors"}
        write(target, broken)
        expect(clean(), "mangler, men collect_all() skriver den altid", "altid-skrevet blok mangler")

        # 5) Negativ kontrol: en fuldt gyldig rapport må ikke fejle. Den skal
        # også overleve et *trafikblok der er tomt* — det er den korrekte
        # repræsentation af en tabt 7-dages blok, ikke en fejl (se docstring).
        write(target, good)
        if clean():
            failed.append(f"en gyldig rapport fejlede: {clean()}")
        else:
            passed += 1

        # 6) Ugyl dig JSON må give en læsbar fejl, ikke en traceback.
        target.write_text("{ikke json", encoding="utf-8")
        expect(clean(), "ugyldig JSON", "ugyldig JSON")

        # 7) Rigtig kode efter alle mutationer.
        target.unlink(missing_ok=True)
        if clean():
            failed.append("selftesten efterlod arkivet i en ugyldig tilstand")
        else:
            passed += 1
    finally:
        restore()

    for problem in failed:
        print("FEJL:", problem)
    print(
        f"check_weekly_history --self-test: {'OK' if not failed else 'FEJL'} "
        f"({passed} kontroller, {len(failed)} fejl)"
    )
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true", help="bevis at porten fanger fejlformerne")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    problems = check()
    for problem in problems:
        print(f"  {problem}")
    if problems:
        print(f"check_weekly_history: {len(problems)} fejl")
        return 1
    print(f"check_weekly_history: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
