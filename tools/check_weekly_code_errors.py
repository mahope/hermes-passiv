#!/usr/bin/env python3
"""Gaten for kodefejl i `reports/weekly/` — en fejl i vores kode må ikke hedde "ukendt".

Baggrund: `reports/weekly/2026-40.json` skriver
`api/stats: name 'count' is not defined` i sin `errors`, og resten af filen siger
`traffic.available: false` og `ranking_basis: unknown`. Læst ovenfra lyder det som
en kilde der svarede forkert. Det var det ikke: `weekly_report.py` skrev
`{"file": file_name, "hits": count}` i en listeforståelse hvis krop kun
evalueres når `top_downloads` ikke er tom. `soft()` fangede `NameError` og skrev
den som en note, så `collect_stats` døde med hele trafikblokken og fire ugers
rapporter sagde "ukendt" om en fejl i os selv.

**Den måling der afgør hele porten:** `str(NameError(...))` er
`"name 'count' is not defined"`. Python skriver *aldrig* klassenavnet i
beskeden, så den arkiverede linje kan ikke læses som en kodefejl. En port der
søger efter `NameError` i arkivet ville være grøn på præcis den fil, den blev
skrevet til at fange. Derfor skriver `note_error()` nu klassenavnet med
(`source: Class: besked`), og porten dømmer på **klassen, ikke på teksten**.

Reglen er en skelnen mellem to klasser af fejl, ikke en navneliste på fejl:

  * `CODE_ERRORS` — `Exception`-subklasser Python rejser, fordi *vi* skrev
    noget forkert. De må aldrig ende som "ukendt".
  * alt derimod (timeouts, netværksfejl, `RuntimeError` om manglende data) er
    forbigående. `unknown` er det *rigtige* svar på en kilde der ikke svarede,
    og uge 39s `The read operation timed out` er den korrekte repræsentation af
    det — ikke en fejl.

Fire kontroller på arkivet:

  1. `code_error_in_report`  en `errors`-linje med en klasse i `CODE_ERRORS`.
                             Bruddet fra uge 40.
  2. `error_without_class`   en `errors`-linje uden klassenavn. Uden den er
                             linjen igen ulæselig, så kontrol 1 kan ikke regnes.
  3. `unknown_class`         en "klasse" der ikke findes blandt undtagelserne.
                             En skrivefejl i `note_error` må ikke kunne få
                             `Noteerror` til at ligne `NameError` — eller få
                             porten til at tie om en ægte kodefejl.
  4. `bad_format`            en linje der ikke kan læses som
                             `source: Class: besked` overhovedet.

Og én på koden, fordi de fire ovenfor alle læser *arkivet*:

  5. `note_error_uden_klasse` porten **kører** `note_error` med en `NameError`
                             og med en ren tekst og læser svaret. Uden denne
                             kontrol fanges en regression i `note_error` først
                             **en uge senere**, når næste rapport er landet i
                             det gamle format — hvilket er præcis den
                             forsinkelse `JUDGED_FROM` er skrevet for at undgå.

Kontrol 3, 4 og 5 er ikke pænhed: de er forudsætningen for at 1 og 2 overhovedet
kan regnes, og uden dem ville porten være grøn på en linje den ikke forstår.

**Hvilke filer porten dømmer, og hvorfor grænsen ikke er en hvidliste.**
`JUDGED_FROM` er den ældste rapport hvor den nye regel kan dømme noget:

  * `2026-40.json` indeholder præcis den fejl porten skal fange, i et format den
    ikke kan læse (klasse-navnet står ikke i filen), og kan ikke regenereres
    herfra fordi den kræver `STATS_TOKEN` på workeren.
  * `2026-37` … `2026-39` er skrevet før bruddet. Selftesten måler dem, og de
    ville være grønne alligevel — så grænsen skjuler ingen fejl, den sætter bare
    en regel på den første rapport den kan gælde for.

Slet `JUDGED_FROM` den dag uge 40 kan regenereres, og porten dømmer hele
arkivet. Det er en konstant med en begrundelse, ikke en undtagelsesliste over
filer der er syndet væk.

**Hvad porten bevidst ikke dømmer:**

  * *At trafikken virker nu.* Det kan kun ses i næste rapport: bruddet lå i
    `weekly_report.py`, der kører på workerens tidsplan, ikke i
    `site/_worker.js`. At finde fejlen i koden er `test_weekly_report.py`s
    opgave, ikke portens — en `NameError` i `collect_stats` kan ikke genskabes
    uden de data den døde på.
  * *At `soft()` skelner mellem kodefejl og forbigående.* Det er den dybere
    rettelse, og den ændrer teksten i fire arkiverede rapporter, så den er en
    port-opgave og ikke en diff. Porten her gør den synlig uden at gøre den.
  * *Uge 39s timeout.* Det er den korrekte repræsentation af en tabt kilde, og
    `check_weekly_history.py`'s docstring siger hvorfor.

    python3 tools/check_weekly_code_errors.py             # kræver ikke dist, kører i gaten
    python3 tools/check_weekly_code_errors.py --self-test # bevis at porten fanger fejlene
"""
from __future__ import annotations

import argparse
import builtins
import importlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports" / "weekly"
WRITER = ROOT / "tools" / "weekly_report.py"
# Opgave 32: `weekly_report.py` flyttede sin egen `_transient` til
# `tools/transient.py`, fordi `check_live_sitemaps.py` havde en anden. Det gjorde
# `known_kinds()` blind for `URLError` igen — portens egen selftest fangede det
# med det samme, fordi de to filer læses, ikke én. `NETWORK_ERRORS` i modulet er
# netop de klasser `soft()` oftest fanger, så de skal læses herfra.
KIND_SOURCES = (WRITER, ROOT / "tools" / "transient.py")

# Undtagelser der betyder "vi skrev noget forkert". En `SyntaxError` er ikke et
# `Exception` (den arver fra `BaseException`), men den skal dømmes med de andre,
# så listen er navngivet og ikke udledt af `issubclass(..., Exception)`.
CODE_ERRORS = frozenset({
    "NameError",
    "AttributeError",
    "TypeError",
    "KeyError",
    "IndexError",
    "AssertionError",
    "ZeroDivisionError",
    "UnboundLocalError",
    "IndentationError",
    "SyntaxError",
})

# `note_error()` kaldes nogle steder med en ren tekst i stedet for en undtagelse.
# Dem får denne klasse, så arkivet har ét format og porten én læsning.
TEXT_ERROR_KIND = "Note"

# Ældste rapport porten dømmer. Se docstring: `2026-40` kan ikke læses af den
# nye regel (klassenavnet står ikke i filen) og kan ikke regenereres herfra.
JUDGED_FROM = "2026-41"


def known_kinds() -> frozenset[str]:
    """Alle klassenavne en `errors`-linje kan have.

    **Målt, ikke hardkodet.** Første version af denne port byggede sættet af
    `builtins` alene, og selftesten fangede det med det samme: `URLError` er
    *ikke* en indbygget undtagelse, den kommer fra `urllib.error` — så porten var
    blind over for den forbigående fejl, `soft()` er mest bundet til at fange.
    En hårdkodet liste ville have skullet vedligeholdes, og en fejl i den ville
    have set ud som en grøn port.

    Derfor læses sættet fra koden: undtagelserne i `weekly_report.py`'s egne
    `except`-klausuler — de er præcis de klasser `note_error` kan få — plus
    indbyggede undtagelser, plus `CODE_ERRORS` (som ikke alle står i en
    `except`-klausule, fordi de aldrig er blevet kastet) og `Note`. Ligeså læses
    `tools/transient.py`, hvor klasserne der afgør om noget prøves igen nu står:
    læses der kun `weekly_report.py`, forsvinder `URLError` fra sættet den dag
    reglen flytter, og porten bliver blind for præcis den fejl `soft()` oftest
    fanger.
    """
    kinds = {
        name
        for name in dir(builtins)
        if isinstance(getattr(builtins, name, None), type)
        and issubclass(getattr(builtins, name), BaseException)
    }
    kinds.add(TEXT_ERROR_KIND)
    kinds.update(CODE_ERRORS)
    for source_path in KIND_SOURCES:
        if not source_path.is_file():
            continue
        source = source_path.read_text(encoding="utf-8")
        # Kvalificerede navne (`urllib.error.URLError`) står både i
        # `except`-klausuler og i `isinstance(...)`-kald, så en regex kun på
        # `except` missede `URLError` — den klasse `soft()` oftest fanger.
        # Derfor læses *alle* kvalificerede navne og resolvingen spørger Python,
        # ikke et mønster, om det virkelig er en undtagelsesklasse.
        for dotted in set(re.findall(r"\b([A-Za-z_][\w]*\.[A-Za-z_][\w.]*)\b", source)):
            resolved = _resolve_exception(dotted)
            if resolved:
                kinds.add(resolved)
    return frozenset(kinds)


def _resolve_exception(dotted: str) -> str | None:
    """Klassenavnet bag et kvalificeret navn, hvis det virkelig er en undtagelse."""
    parts = dotted.split(".")
    for split in range(len(parts) - 1, 0, -1):
        module_name, attrs = ".".join(parts[:split]), parts[split:]
        try:
            obj: object = importlib.import_module(module_name)
        except Exception:  # noqa: BLE001 — et navn der ikke er et modul er ikke en fejl
            continue
        for attr in attrs:
            obj = getattr(obj, attr, None)
            if obj is None:
                break
        if isinstance(obj, type) and issubclass(obj, BaseException):
            return obj.__name__
    return None


def parse_error_line(line: str) -> tuple[str, str]:
    """Del `source: Class: besked` i `(source, Class)`.

    Kilden kan indeholde kolon (`api/stats` har ingen, men `npm @scope/pkg` og
    `gh repo owner/name` slår ikke entydigt), så den *første* del der ligner en
    undtagelsesklasse vinder. Er der ingen, er der heller ingen at dømme — det er
    kontrol 2 og 4s opgave, ikke denne funktions.
    """
    parts = line.split(": ")
    kinds = known_kinds()
    for index in range(1, len(parts) - 1):
        candidate = parts[index].strip()
        if candidate in kinds:
            return ": ".join(parts[:index]), candidate
    return "", ""


def check_report_file(path: Path) -> list[str]:
    problems: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        # `check_weekly_history.py` dømmer begge dele; her lader vi den gøde det,
        # så to porte ikke melder samme fejl to gange.
        return []
    if not isinstance(data, dict):
        return []
    week = data.get("iso_week")
    if not isinstance(week, str) or week < JUDGED_FROM:
        return []
    errors = data.get("errors")
    if not isinstance(errors, list):
        return [f"{path.name}: `errors` mangler eller er ikke en liste"]

    kinds = known_kinds()
    for raw in errors:
        if not isinstance(raw, str) or not raw.strip():
            problems.append(f"{path.name}: `errors` indeholder en linje der ikke er tekst")
            continue
        line = raw.strip()
        source, kind = parse_error_line(line)
        if not kind:
            # Ingen genkendt klasse. Er linjen i det hele taget
            # `source: Class: besked`, eller er den gammel format?
            segments = line.split(": ")
            if len(segments) >= 2 and segments[-1] in kinds:
                problems.append(
                    f"{path.name}: `errors`-linjen {line!r} har klassenavnet til sidst "
                    f"i stedet for efter kilden"
                )
            elif len(segments) >= 2:
                problems.append(
                    f"{path.name}: `errors`-linjen {line!r} mangler klassenavn — den "
                    f"skrives `source: Class: besked`, så en fejl i vores egen kode kan "
                    f"skelnes fra en kilde der ikke svarer"
                )
            else:
                problems.append(
                    f"{path.name}: `errors`-linjen {line!r} kan ikke læses som "
                    f"`source: Class: besked`"
                )
            continue
        if kind in CODE_ERRORS:
            problems.append(
                f"{path.name}: `{source}` fejlede med {kind} — det er en fejl i "
                f"weekly_report.py, ikke en kilde der ikke svarer, og må aldrig "
                f"skrives som \"ukendt\": {line!r}"
            )
    return problems


def check_note_error() -> list[str]:
    """Kør `note_error` og se, om den skriver klassenavnet.

    Resten af porten læser arkivet, så en regression i `note_error` ville først
    vise sig i næste uges rapport. Her fanges den nu, fordi porten *kører*
    funktionen i stedet for at læse den — samme principle som de øvrige porte i
    denne familie, der genskriver ikke `track.js` men indlæser den.
    """
    if not WRITER.is_file():
        return [f"{WRITER.relative_to(ROOT)} findes ikke — kan ikke bevise formatet"]
    sys.path.insert(0, str(WRITER.parent))
    try:
        import weekly_report  # noqa: PLC0415 — skal først kunne indsætte stien
        # Genindlæses hver gang. Uden det læser porten den cachede kode fra en
        # tidligere import, og mutationen i selftesten — der skriver det gamle
        # format tilbage til *filen* — ville ikke give rødt. Det er præcis det
        # fejl `check_inline_cta_events.py` har en `_js_regex`-reparation mod, og
        # grunden til at porten i stedet *kører* koden den dømmer.
        weekly_report = importlib.reload(weekly_report)
    except Exception as exc:  # noqa: BLE001
        return [f"weekly_report.py kan ikke indlæses: {exc}"]
    finally:
        sys.path.pop(0)

    problems: list[str] = []
    cases = (
        ("undtagelse", NameError("name 'count' is not defined"), "NameError"),
        ("ren tekst", "RESEND_API_KEY mangler", TEXT_ERROR_KIND),
    )
    for navn, exc, forventet in cases:
        weekly_report.ERRORS.clear()
        weekly_report.note_error("selftest", exc)
        if not weekly_report.ERRORS:
            problems.append(f"note_error({navn}) skrev ingen linje")
            continue
        _, kind = parse_error_line(weekly_report.ERRORS[0])
        if kind != forventet:
            problems.append(
                f"note_error({navn}) skrev {weekly_report.ERRORS[0]!r} — læst som "
                f"{kind or '(ingen klasse)'!r}, forventet {forventet!r}. En rapport "
                f"uden klassenavn kan ikke skelne en kodefejl fra en kilde der "
                f"ikke svarer"
            )
    weekly_report.ERRORS.clear()
    return problems


def check() -> list[str]:
    if not REPORT_DIR.is_dir():
        return [f"{REPORT_DIR.relative_to(ROOT)} findes ikke — kan ikke gate arkivet"]
    files = sorted(REPORT_DIR.glob("*.json"))
    if not files:
        return [f"{REPORT_DIR.relative_to(ROOT)} indeholder ingen rapporter"]
    problems = check_note_error()
    for path in files:
        problems.extend(check_report_file(path))
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

    real_files = {p: p.read_text(encoding="utf-8") for p in sorted(REPORT_DIR.glob("*.json"))}
    target = REPORT_DIR / "9999-01.json"

    def write(data) -> None:
        target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def good(errors: list[str]) -> dict:
        return {
            "iso_week": "9999-01",
            "generated_at": "2099-01-01T00:00:00+00:00",
            "health": {"status": "healthy"},
            "traffic": {},
            "npm": {},
            "github": {},
            "errors": errors,
        }

    def restore() -> None:
        target.unlink(missing_ok=True)
        for path, raw in real_files.items():
            path.write_text(raw, encoding="utf-8")

    try:
        # Rigtig kode skal være grøn, så mutationerne nedenfor måles mod en
        # baseline der er grøn. `2026-40` ligger før `JUDGED_FROM`, så det er
        # `NameError`-linjen i den, porten *ikke* dømmer — det er grænsens
        # begrundelse, og selftesten måler den direkte nedenfor.
        baseline = check()
        if baseline:
            failed.append(f"den rigtige kode skal være grøn, fik {baseline}")
        else:
            passed += 1

        # 0) Negativ kontrol: en forbigående fejl er ikke en kodefejl. Uge 39s
        # timeout skal være grøn, ellers reglen kan ikke bruges.
        write(good(["api/stats: URLError: <urlopen error timed out>"]))
        if [p for p in check() if "9999-01" in p]:
            failed.append(f"en forbigående fejl blev dømt som kodefejl: {check()}")
        else:
            passed += 1
        write(good(["api/stats: TimeoutError: The read operation timed out"]))
        if [p for p in check() if "9999-01" in p]:
            failed.append("et timeout blev dømt som kodefejl")
        else:
            passed += 1
        write(good(["købsinventar: Note: katalogens tilbud er ufuldstændige"]))
        if [p for p in check() if "9999-01" in p]:
            failed.append("en Note-linje blev dømt som kodefejl")
        else:
            passed += 1

        # 1) Kodefejl i en dømt rapport.
        write(good(["api/stats: NameError: name 'count' is not defined"]))
        expect(check(), "må aldrig skrives som", "NameError i rapporten")

        write(good(["npm @scope/pkg: TypeError: object is not subscriptable"]))
        expect(check(), "TypeError", "TypeError i rapporten")

        # 1b) Samme kodefejl med en kilde der selv indeholder et kolon. Kilden
        # må ikke få porten til at læse `https://x` som klassenavn — første del
        # der ligner en *rigtig* undtagelsesklasse skal være den rigtige.
        write(good(["api: https://x: NameError: name 'hits' is not defined"]))
        expect(check(), "fejlede med NameError", "kilde med kolon")

        write(good(["npm pkg: URLError: <urlopen error timed out>"]))
        if any("9999-01" in p for p in check()):
            failed.append(f"et kolon i kilden fik en forbigående fejl dømt: {check()}")
        else:
            passed += 1

        # 2) En linje uden klassenavn er ulæselig.
        write(good(["api/stats: name 'count' is not defined"]))
        expect(check(), "mangler klassenavn", "klasse mangler (gammelt format)")

        # 3) En opfundet klasse må ikke ligne en rigtig, og må ikke tie.
        write(good(["api/stats: Noteerror: name 'count' is not defined"]))
        expect(check(), "mangler klassenavn", "opfundet klassenavn")

        write(good(["api/stats: NameErr0r: name 'count' is not defined"]))
        expect(check(), "mangler klassenavn", "klasse med et nul i stedet for o")

        # 4) En linje der overhovedet ikke kan læses.
        write(good(["api/stats"]))
        expect(check(), "kan ikke læses som", "linje uden kolon")

        # 5) `errors` skal være en liste. Mangler den, dømmer `check_weekly_history`
        # den, fordi `collect_all()` skriver den altid — her skal vi heller ikke
        # tie på det, så en håndredigeret fil ikke slipper igennem på en fejlvis
        # måde.
        write({k: v for k, v in good([]).items() if k != "errors"})
        expect(check(), "mangler eller er ikke en liste", "errors mangler")

        # 6) Negativ kontrol igen: en helt gyldig rapport må ikke fejle.
        write(good([]))
        if [p for p in check() if "9999-01" in p]:
            failed.append(f"en gyldig rapport fejlede: {check()}")
        else:
            passed += 1

        # 7) Grænsen skal være ærlig: `2026-40` ligger før `JUDGED_FROM` og må
        # derfor ikke dømmes. Det er ikke en hvidliste over synd — det er den
        # rapport med den kodefejl, porten blev skrevet til at fange, så hvis
        # den nogensinde flyttes ind i dømmet srange, skal selftesten sige det.
        week40 = REPORT_DIR / "2026-40.json"
        if week40.is_file():
            data = json.loads(week40.read_text(encoding="utf-8"))
            if any("NameError" in str(e) for e in data.get("errors", [])):
                failed.append(
                    "2026-40.json har en NameError-linje med klassenavn, og så er "
                    "JUDGED_FROM for gammel — sæt den ned"
                )
            else:
                passed += 1

        # 8) Mutationen der beviser kontrol 5: `note_error` skriver det gamle
        # format igen. Resten af porten læser arkivet og ville være grøn, så
        # uden kontrol 5 ville denne regression være usynlig indtil næste
        # rapport var landet.
        real_writer = WRITER.read_text(encoding="utf-8")
        mutated = real_writer.replace(
            'ERRORS.append(f"{source}: {kind}: {msg[:200]}")',
            'ERRORS.append(f"{source}: {msg[:200]}")',
        )
        if mutated == real_writer:
            failed.append(
                "kontrol 5 mutationen fandt ikke note_error-linjen den skriver — "
                "porten kan altså ikke bevise sit eget krav"
            )
        else:
            WRITER.write_text(mutated, encoding="utf-8")
            expect(check(), "kan ikke skelne en kodefejl", "note_error uden klassenavn")
            WRITER.write_text(real_writer, encoding="utf-8")
        if check():
            failed.append("selftesten efterlod weekly_report.py i en ugyldig tilstand")
        else:
            passed += 1

        # 9) Rigtig kode efter alle mutationer.
        target.unlink(missing_ok=True)
        if check():
            failed.append("selftesten efterlod arkivet i en ugyldig tilstand")
        else:
            passed += 1
    finally:
        restore()

    for problem in failed:
        print("FEJL:", problem)
    print(
        f"check_weekly_code_errors --self-test: {'OK' if not failed else 'FEJL'} "
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
        print(f"check_weekly_code_errors: {len(problems)} fejl")
        return 1
    print("check_weekly_code_errors: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
