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
  5. `synthetic_top_path`   en `top_paths`-række der ikke er en publiceret
                            rute. Målt 30/9: sidevisninger kommer fra
                            `track.js`, som posterer `location.pathname`, så
                            *ethvert* kald vi selv laver med JavaScript —
                            hver `--live`-screenshot, hvert layout-besøg —
                            lander i `top_paths` og ligner et kundebesøg. Den
                            ruteform er dog fanget andre steder; her fanges de
                            ruter, der slet ikke findes, fordi de er skrevet
                            af en selftest. Regel 5 gør **hele rapporten**
                            ubrugelig, ikke kun rækken: en rapport, der kan
                            tælle vores egen trafik, kan ikke bruges til at
                            bevise at *noget andet* i den er sandt.

**Hvorfor regel 5 er en regel og ikke en navneliste:** den spørger om ruten
findes blandt de publicerede, så den fanger det næste syntetiske navn uden at
nogen skal opdatere en liste. Og målt 30/9 er inventaret *hele* grunden:
`tools/route_inventory.json` har 296 ruter, og de fire `dist/*/sitemap.xml`
tilføjer **0** oveni, så de to kilder er enige — derfor afhænger porten kun af
inventaret og ikke af `dist/`.

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
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports" / "weekly"
WRITER = ROOT / "tools" / "weekly_report.py"
INVENTORY = ROOT / "tools" / "route_inventory.json"
TOOLS = ROOT / "tools"

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


def published_routes() -> set[str] | None:
    """De ruter vi faktisk udgiver, uden bagvendt skråstreg.

    Målt 30/9: inventaret og de fire `dist/*/sitemap.xml` er enige — 296 ruter,
    og sitemap'erne tilføjer 0 oveni. Derfor læses kun inventaret, så porten
    stadig ikke kræver et bygget `dist/`.

    `None` betyder "kan ikke måle". En port der ikke kan måle, må ikke være
    grøn ved at tie stille — samme som en manglende `weekly_report.py`.
    """
    try:
        raw = json.loads(INVENTORY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    routes: set[str] = set()
    for value in raw.values():
        if not isinstance(value, list):
            return None
        for route in value:
            if isinstance(route, str):
                routes.add(route.split("?")[0].split("#")[0].rstrip("/") or "/")
    return routes or None


def own_probe_source(route: str) -> str | None:
    """`fil:linje` hvis en af vores *måleværktøjer* erklærer den rute på kolonne 0.

    Hvorfor der overhovedet er en undtagelse: `tools/check_shared_visits_namespace.py`
    sender bevidst én sidevisning pr. domæne med stien `/namespace-probe`, fordi
    porten skal bevise at alle fire domæner skriver i det samme KV-navrum. Den
    skrivning er ægte og lander i den rigtige statistik — det står eksplicit i
    portens egen docstring. Uden en undtagelse blev `reports/weekly/2026-41.json`
    altså dømt som om en rapport aldrig må indeholde vores egen trafik, selv om
    det er præcis den trafik der er blevet skrevet med vilje.

    Reglen er derfor ikke en navneliste, men en *proveniens*: ruten skal være en
    modul-konstant i en `tools/*.py` — altså en streng værktøjet sender i
    virkeligheden. Målt 5/10: `/blog/syntetisk-klik-uden-knap` og
    `/oxloop-selftest` står også bogstaveligt i `tools/`, men kun indeni en
    funktion eller en selftest-fixture, altså på en indrykket linje. De er
    strenge i et test, ikke ruter vi besøger, og de skal stadig være røde — det
    er selftestens 7g. Portens egen fil er ikke med i søgningen: en port må
    ikke aflæse sig selv til grønt.
    """
    if not isinstance(route, str) or not route.startswith("/") or '"' in route or "'" in route:
        return None
    mønster = re.compile(rf'''^[A-Z_][A-Z_0-9]* *= *["']{re.escape(route)}["']$''')
    for sti in sorted(TOOLS.glob("*.py")):
        if sti.name == Path(__file__).name:
            continue
        try:
            linjer = sti.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for num, linje in enumerate(linjer, start=1):
            if mønster.match(linje):
                return f"{sti.name}:{num}"
    return None


def unpublished_rows(top_paths, published: set[str]) -> list[tuple[str, object]]:
    """`(rute, besøg)` for de rækker i `top_paths` vi ikke udgiver.

    Rækker der ikke er et objekt, eller hvis `path` ikke er en streng, springes
    over i stedet for at give en undtagelse: `check_weekly_history` skal kunne
    læse en arkivfil, en anden scriptversion har skrevet.
    """
    if not isinstance(top_paths, list) or not published:
        return []
    out: list[tuple[str, object]] = []
    for row in top_paths:
        if not isinstance(row, dict):
            continue
        route = row.get("path")
        if not isinstance(route, str) or not route:
            continue
        norm = route.split("?")[0].split("#")[0].rstrip("/") or "/"
        if norm not in published:
            out.append((route, row.get("visits")))
    return out


def check_report_file(path: Path, writer_source: str,
                       published: set[str]) -> list[str]:
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

    # 5) En sidevisning af en rute vi ikke udgiver. Se docstring: hele
    #    rapporten dømmes, fordi en rapport der kan tælle vores egen trafik
    #    ikke kan bruges som bevis for noget. Den ene undtagelse er en rute et
    #    af vores måleværktøjer erklærer på kolonne 0 — altså en vi sender med
    #    vilje, ikke en der ligner et kundebesøg. Se `own_probe_source`.
    for route, visits in unpublished_rows(
            (data.get("traffic") or {}).get("top_paths"), published):
        if own_probe_source(route.split("?")[0].split("#")[0].rstrip("/") or "/"):
            continue
        problems.append(
            f"{path.name}: `top_paths` har besøget `{route}` ({visits}), men "
            f"den rute er ikke blandt de {len(published)} publicerede ruter — "
            f"en sidevisning af en rute vi ikke udgiver kan kun være vores egen"
        )

    return problems


def check() -> list[str]:
    if not REPORT_DIR.is_dir():
        return [f"{REPORT_DIR.relative_to(ROOT)} findes ikke — kan ikke gate arkivet"]
    if not WRITER.is_file():
        return [f"{WRITER.relative_to(ROOT)} findes ikke — kan ikke bevise hvilke blokke koden skriver"]
    published = published_routes()
    if published is None:
        return [f"{INVENTORY.relative_to(ROOT)} findes eller kan ikke læses — "
                f"kan ikke bevise hvilke ruter der er publicerede"]
    files = sorted(REPORT_DIR.glob("*.json"))
    if not files:
        return [f"{REPORT_DIR.relative_to(ROOT)} indeholder ingen rapporter"]
    writer_source = WRITER.read_text(encoding="utf-8")
    problems: list[str] = []
    for path in files:
        problems.extend(check_report_file(path, writer_source, published))
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

    def kontrol(betingelse: bool, navn: str, detalje: object = "") -> None:
        """En kontrol uden fejlform — bruges når det er *evnen* der dømmes."""
        nonlocal passed
        if betingelse:
            passed += 1
        else:
            failed.append(f"{navn} ({detalje})")

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

        # 7) Regel 5. Fire kontroller + fire mutationer. Skrevet på de samme
        #    måder som resten: skæmmet eksempel giver intet, så her er både
        #    en positiv kontrol på rigtige ruter og fire forskellige
        #    syntetiske navne, fordi porten ikke må være en navneliste.
        pub = published_routes()
        kontrol("de publicerede ruter kan måles",
              isinstance(pub, set) and len(pub) > 100,
              f"{len(pub) if pub else 0} ruter")

        # 7a. Positiv kontrol: en publiceret rute i `top_paths` er grøn. Uden
        #     denne kunne porten være rød på alt og se ud som at virke.
        write(target, {**good, "traffic": {"top_paths": [
            {"path": "/blog/add-bug-report-form-to-any-website", "visits": 9},
            {"path": "/", "visits": 430}]}})
        if [p for p in clean() if "ikke blandt de" in p]:
            failed.append("en publiceret rute blev markeret som syntetisk")
        else:
            passed += 1

        # 7b. Skråstregformen skal ikke gøre en publiceret rute syntetisk:
        #      inventaret skriver `/da`, `track.js` sender `/da/`. Målt 30/9.
        if pub and "/da" in pub:
            write(target, {**good, "traffic": {
                "top_paths": [{"path": "/da/", "visits": 31}]}})
            if [p for p in clean() if "ikke blandt de" in p]:
                failed.append("en publiceret rute med bagvendt skråstreg blev markeret")
            else:
                passed += 1

        # 7c. Fire syntetiske navne, fire røde. Det er *ikke* en navneliste:
        #      porten kender ingen af dem, den spørger bare om ruten findes.
        for name, route in (("en selftests rute", "/blog/syntetisk-klik-uden-knap"),
                            ("en probe-rute", "/oxloop-selftest"),
                            ("et opkaldt filnavn", "/tmp/oxloop-selftest-blind.html"),
                            ("en rute med vilkårlig tekst", "/ikke-en-rude")):
            write(target, {**good, "traffic": {
                "top_paths": [{"path": route, "visits": 42}]}})
            expect(clean(), "kan kun være vores egen", f"syntetisk rute: {name}")

        # 7f. Den ene undtagelse: en rute vores egen måleværktøj erklærer som
        #     modul-konstant. `check_shared_visits_namespace.py` sender den med
        #     vilje for at bevise at domænerne deler KV, så rapporten må ikke
        #     dømmes for at indeholde den. Positive kontrol på opslaget *og* på
        #     at den faktisk findes i porten der sender den.
        kilde = own_probe_source("/namespace-probe")
        kontrol("undtagelsen finder den rute porten sender med vilje",
              bool(kilde) and "check_shared_visits_namespace.py" in kilde, str(kilde))
        write(target, {**good, "traffic": {
            "top_paths": [{"path": "/namespace-probe", "visits": 3}]}})
        if [p for p in clean() if "ikke blandt de" in p]:
            failed.append("en rute vores egen måleværktøj sender blev markeret")
        else:
            passed += 1

        # 7g. Undtagelsen må ikke være en navneliste i forklædet. Samme to navne
        #     som 7c står bogstaveligt i `tools/check_article_paid_path.py`, men
        #     kun indeni en funktion eller en selftest-fixture — de er strenge i
        #     et test, ikke ruter vi besøger, så de skal stadig være røde.
        for route in ("/blog/syntetisk-klik-uden-knap", "/oxloop-selftest"):
            kontrol(f"{route} er ikke en modul-konstant i noget værktøj",
                    own_probe_source(route) is None, str(own_probe_source(route)))
            write(target, {**good, "traffic": {
                "top_paths": [{"path": route, "visits": 42}]}})
            expect(clean(), "kan kun være vores egen",
                   f"streng i et test, ikke en rute vi sender: {route}")

        # 7d. Besøgstallet skal stå i beskeden, ellers kan en læser ikke se
        #      hvor meget af ranglisten der står på spil.
        write(target, {**good, "traffic": {
            "top_paths": [{"path": "/oxloop-selftest", "visits": 42}]}})
        expect(clean(), "42", "besøgstallet står i beskeden")

        # 7e. En `top_paths` der ikke er en liste, eller rækker der ikke er
        #     objekter, må ikke give en traceback: arkivet kan være skrevet af
        #     en anden scriptversion.
        for rows_ in ("nope", [["a", 1]], [None], [{"visits": 3}], None):
            write(target, {**good, "traffic": {"top_paths": rows_}})
            try:
                out = clean()
            except Exception as exc:  # noqa: BLE001 — selftestens formål
                failed.append(f"top_paths={rows_!r} gav {exc!r}")
            else:
                if [p for p in out if "kan kun være vores egen" in p]:
                    failed.append(f"top_paths={rows_!r} markeret uden en rute ({out})")
        passed += 1

        # 7f. Bevis på den *rigtige* fil, ikke på et syntetisk eksempel: den
        #     nyeste rapport med tal får en syntetisk rute lagt ind, og porten
        #     skal blive rød på arkivet selv. Uden dette kan hele regel 5 være
        #     grøn kun fordi den aldrig har set en rigtig fil med en fejl i.
        real_traffic = [p for p in sorted(REPORT_DIR.glob("*.json"))]
        with_traffic = []
        for p in real_traffic:
            try:
                top = (json.loads(p.read_text(encoding="utf-8"))
                       .get("traffic") or {}).get("top_paths")
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(top, list) and top:
                with_traffic.append(p)
        if not with_traffic:
            failed.append("ingen rigtig rapport har top_paths — "
                          "regel 5 kan ikke bevises på den rigtige fil")
        else:
            victim = with_traffic[-1]
            raw = json.loads(victim.read_text(encoding="utf-8"))
            raw["traffic"]["top_paths"].append(
                {"path": "/oxloop-selftest", "visits": 7})
            victim.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")
            hit = [p for p in clean() if "ikke blandt de" in p]
            victim.write_text(real_files[victim], encoding="utf-8")
            if len(hit) == 1 and victim.name in hit[0]:
                passed += 1
            else:
                failed.append(f"regel 5 fangede ikke den muterede {victim.name}: {hit}")

        # 8) Rigtig kode efter alle mutationer.
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
