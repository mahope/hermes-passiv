#!/usr/bin/env python3
"""Byg de to publicerede site-icons-filer reproducerbart fra `site-icons/`.

Opgave 20 i `IMPLEMENTATION_PLAN.md`. Opgave 18 (`tools/build_desktop_archive.py`)
gjorde det samme for EAA-scannerens kildearkiv, fordi det viste sig at være et
1.3.0-arkiv under et 1.3.3-navn. Opgave 19 (`tools/check_versions.py`) læste så
ind i de fem byggeoutput-arkiver — og fandt at `site-icons-1.0.0.tar.gz` er en
**håndlavet kopi fra 24. august**, ikke bygget af `site-icons/`. Begge filer i
arkivet afviger fra kilden, og forskellen er ikke kosmetik:

    arkiv  site_icons.py:45  "Lemon Squeezy API when available"
    kilde  site_icons.py:45  "the mahope.tools license API"

    arkiv  README.md:69  "When Mads opens Bitwarden (Lemon Squeezy API), keys
                            are sold there"
    kilde  README.md:69  "Pro will require a license key from the mahope.tools
                            license API"

Lemon Squeezy blev lukket 24. september. Det er den døde udbyder fra kontrakten,
serveret i et publiceret download til kunder, i en README der fortæller dem hvor
de kan købe en nøgle. Samme fejlform som opgave 10, 15 og 18: en værdi der er
påstand om leveringen, og ingen der læser den der den ligger.

Derfor får site-icons samme behandling som de tre Clean Copy-arkiver og
desktop-kildearkivet:

    python3 tools/build_site_icons_archive.py           # byg og skift filerne
    python3 tools/build_site_icons_archive.py --check   # byg i hukommelse og sammenlign
    python3 tools/build_site_icons_archive.py --self-test

**Hvorfor også de to løse filer.** `site/downloads.html` linker både
`site_icons.py` (curl -O) og tarballet. De løse kopier lå også i hånden, og
README'en havde derfor fået en håndredigeret linje med det rigtige domæne, mens
tarballet beholdt den døde. Ét build, én kilde: ellers kan de to igen glide fra
hinanden, og det er præcis det der skete. Derfor bygges alle tre output fra
`site-icons/`, og `--check` kræver at de er byte-identiske med kilden.

Determinismen er pointen. Tar-formatet gemmer tidsstempel, uid/gid, ejer-navne og
rettigheder, og gzip gemmer sin egen tid — så et "identisk" arkiv bygget på en
anden maskine eller en senere dato ville ellers afvige i de bytes, porten ikke kan
forklare. Her låses medlemmer, rækkefølge, tidsstempel, ejer og rettigheder, og
gzip får `mtime=0` og intet filnavn i headeren.

`--self-test` bygger et miniature-workspace i en midlertidig mappe og kræver at
porten **fejler** på en række mutationer og **passerer** på en kilde, der ikke er
rørt. Uden den positive kontrol er `--check` lige så lidt bevis som opgave 13, 15,
17 og 19 måtte konstatere: en port, der siger "skal ikke fejle", uden at nogen har
set den fejle.

**Kendte begrænsninger, opskrivet i stedet for skjult:**

1. Arkivet er fladt, to filer i roden, fordi det er det kunden har hentet siden
   24. august. Det er ikke en sdist: der er ingen `PKG-INFO`, ingen topniveau-mappe
   og ingen `LICENSE`. `pyproject.toml` og `cli.py` medtages bevidst ikke — de er
   byggeinput til en wheel vi ikke udgiver, og kunden skal kunne køre filen.
2. `--check` læser både `site-icons/` og de publicerede filer, og path-filteret
   dækker `site-icons/**` (se `quality_gate.py`s step). Her er altså ingen af de
   huller opgave 18 måtte oplyse.
"""
from __future__ import annotations

import argparse
import gzip
import io
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import mini_toml  # noqa: E402

SOURCE = ROOT / "site-icons"
DOWNLOADS = ROOT / "site/downloads/site-icons"

#: Fast tidspunkt for alle medlemmer. Tar har tidsstempel med sekundopløsning, så
#: et build kl. 10:00:42 ville ellers give et andet arkiv end et kl. 10:00:43, og
#: `--check` ville fejle uden at nogen havde rørt en fil.
#:
#: 2000-01-01 er ikke tilfældigt: 0 er det samme som "ukendt" i flere
#: tar-læsere, så det er en værdi man hellere ikke lægger i et arkiv, en kunde skal
#: kunne å på en Windows-maskine.
TAR_MTIME = 946_684_800

#: Kun de to filer kunden skal have. Sorteret, så arkivet er reproducerbart
#: uanset rækkefølgen på disken. `pyproject.toml` og `cli.py` er byggeinput til
#: en wheel vi ikke udgiver (se docstringens begrænsning 1).
MEMBERS = ("README.md", "site_icons.py")

#: Den lukkede udbyder. Kontrakten af 24. september lukkede Lemon Squeezy, så
#: ingen publiceret fil må nævne den: en kunde der læser det, kan ikke købe
#: noget. Samme liste som `tools/check_license_clients.py` bruger, fordi det er
#: én fejlform, ikke to.
BANNED_TERMS = (b"lemon squeezy", b"lemonsqueezy", b"lemon-squeezy")


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


def product_version(source: Path) -> str:
    """Versionen fra `pyproject.toml` — samme kilde `check_versions.py` bruger."""
    manifest = source / "pyproject.toml"
    try:
        data = mini_toml.loads(manifest.read_text(encoding="utf-8"), manifest)
    except (mini_toml.TOMLDecodeError, ValueError) as exc:
        raise SystemExit(f"FEJL: {rel(manifest)} kan ikke læses som TOML ({exc})")
    version = str(data.get("project", {}).get("version", "")).strip()
    if not version:
        raise SystemExit(f"FEJL: {rel(manifest)} har ingen project.version")
    return version


def archive_name(source: Path) -> str:
    return f"site-icons-{product_version(source)}.tar.gz"


def read_members(source: Path) -> dict[str, bytes]:
    """{membernavn: bytes} for de to filer, der skal med.

    En kildefil der mangler er en fejl, ikke noget der springes over: et arkiv
    uden README er ikke det kunden har hentet, og en port der bygger videre på
    en kilde der ikke findes, ville erklære et arkiv gyldigt uden at have læst
    det, der gør det gyldigt.
    """
    out: dict[str, bytes] = {}
    for name in MEMBERS:
        path = source / name
        if not path.is_file():
            raise SystemExit(f"FEJL: {rel(path)} mangler i kilden")
        out[name] = path.read_bytes()
    return out


def build_archive(source: Path) -> bytes:
    """Deterministisk `.tar.gz` af de to filer."""
    payloads = read_members(source)
    raw = io.BytesIO()
    # GNU_FORMAT, ikke Pythons standard (PAX): PAX skriver udvidede headere med
    # tidsstempel i sub-sekund-præcision, og de er afhængige af hvornår i
    # sekunden buildet kørte. USTAR ville også virke her, men GNU er det samme
    # som `tar czf` skriver på en Linux-maskine, så arkivet kan valideres mod
    # kommandolinjens `tar`.
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.GNU_FORMAT) as tf:
        for name in MEMBERS:
            body = payloads[name]
            info = tarfile.TarInfo(name)
            info.size = len(body)
            info.mtime = TAR_MTIME
            info.mode = 0o644
            info.type = tarfile.REGTYPE
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            tf.addfile(info, io.BytesIO(body))
    return gzip_bytes(raw.getvalue())


def gzip_bytes(payload: bytes) -> bytes:
    """Gzip deterministisk: samme input giver altid samme output.

    `mtime=0` tømmer gzip-headerens tidsfelt, og `filename=""` forhindrer at
    GzipFile skriver arkivets eget navn ind i headeren — ellers ville samme
    kilde give forskellige bytes alt efter hvad filen hedder, og `--check` ville
    fejle på en omdøbning.
    """
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", compresslevel=9, mtime=0, filename="") as gz:
        gz.write(payload)
    return buffer.getvalue()


def members_of(payload: bytes) -> dict[str, bytes]:
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as tf:
        return {m.name: tf.extractfile(m).read() for m in tf.getmembers() if m.isfile()}  # type: ignore[union-attr]


def banned_hits(blob: bytes) -> list[str]:
    """Termer fra den lukkede udbyder, fundet i en fil kunden kan læse."""
    lowered = blob.lower()
    return sorted({term.decode() for term in BANNED_TERMS if term in lowered})


def check(source: Path, downloads: Path | None = None) -> list[str]:
    folder = DOWNLOADS if downloads is None else downloads
    problems: list[str] = []
    expected_members = read_members(source)
    payload = build_archive(source)
    name = archive_name(source)

    published = folder / name
    if not published.is_file():
        problems.append(f"{rel(published)} mangler")
    elif published.read_bytes() != payload:
        problems.append(
            f"{rel(published)} afviger fra en regeneration af {rel(source)}/ "
            f"— kunden henter en anden kode end den i repoet"
        )

    # Indholdet, ikke kun bytesene. En håndlavet tarball kan have de rigtige
    # membernavne og stadig den forkerte tekst, så arkivet åbnes og læses uanset
    # hvad bytes-sammenligningen lige sagde. Ellers ville den lukkede udbyder
    # først blive fundet *efter* at nogen har genbygget arkivet — altså en
    # manuel rettelse, som er præcis den håndlavede kopi vi er ved at fjerne.
    if published.is_file():
        try:
            inside = members_of(published.read_bytes())
        except (OSError, EOFError, tarfile.TarError) as exc:
            inside = {}
            problems.append(f"{rel(published)} kan ikke åbnes ({exc})")
        for member, blob in expected_members.items():
            if member not in inside:
                problems.append(f"{rel(published)} mangler medlemmet {member}")
            elif inside[member] != blob:
                problems.append(
                    f"{rel(published)}/{member} afviger fra {rel(source)}/{member}"
                )
        for member, blob in sorted(inside.items()):
            for term in banned_hits(blob):
                problems.append(
                    f"{rel(published)}/{member} nævner den lukkede udbyder ({term})"
                )

    # `downloads.html` linker også de to filer løst, så de er lige så meget
    # publicerede output som tarballet.
    for member, blob in expected_members.items():
        loose = folder / member
        if not loose.is_file():
            problems.append(f"{rel(loose)} mangler")
            continue
        if loose.read_bytes() != blob:
            problems.append(
                f"{rel(loose)} afviger fra {rel(source)}/{member} — "
                f"kunden henter en anden kode end den i repoet"
            )
        for term in banned_hits(loose.read_bytes()):
            problems.append(f"{rel(loose)} nævner den lukkede udbyder ({term})")

    # Et arkiv fra en tidligere udgave i samme familie er en kunde, der stadig kan
    # hente gammel kode. Samme princip som de Clean Copy-arkiver.
    for candidate in sorted(folder.glob("site-icons-*.tar.gz")):
        if candidate.name != name:
            problems.append(f"{candidate.name} er en forældet udgave, der stadig ligger publiceret")
    return problems


# --------------------------------------------------------------------------
# Selftest
# --------------------------------------------------------------------------

#: En kilde der ligner den rigtige: de to filer der publiceres, de to der ikke
#: gør, og en der ligner en byggefil. Lille nok til at en fejl i portens egen
#: logik er synlig.
SELF_TEST_SOURCE = {
    "pyproject.toml": '[project]\nname = "site-icons"\nversion = "1.0.0"\n',
    "README.md": "# site-icons\n\ncurl -O https://mahope.tools/downloads/site-icons/site_icons.py\n",
    "site_icons.py": '__version__ = "1.0.0"\n',
    "cli.py": "from site_icons import main\n",
    "test-icon.svg": "<svg xmlns='http://www.w3.org/2000/svg'/>\n",
}


def self_test() -> int:
    base = Path(tempfile.mkdtemp(prefix="build_site_icons_archive_"))
    failures: list[str] = []

    def write_all(source: Path, downloads: Path) -> None:
        """Skriv de tre publicerede artefakter, som `main()` gør det."""
        (downloads / archive_name(source)).write_bytes(build_archive(source))
        for member in MEMBERS:
            (downloads / member).write_bytes((source / member).read_bytes())

    def workspace(name: str) -> tuple[Path, Path]:
        source = base / name / "site-icons"
        downloads = base / name / "site/downloads/site-icons"
        for rel_name, body in SELF_TEST_SOURCE.items():
            path = source / rel_name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        downloads.mkdir(parents=True, exist_ok=True)
        write_all(source, downloads)
        return source, downloads

    def run(name: str) -> list[str]:
        source, downloads = workspace(name)
        return check(source, downloads)

    # Positiv kontrol FØRST: en urørt kilde skal være grøn, ellers ved vi ikke om
    # mutationerne nogensinde har betydet noget.
    control = run("_control")
    if control:
        failures.append(f"positiv kontrol: uændret kilde fejlede med {control}")

    # Determinisme: samme kilde to gange skal give præcis samme bytes. Uden den
    # egenskab er `--check` afhængig af at buildet tilfældigvis sker samme dag.
    determinism_source, _ = workspace("_determinism")
    if build_archive(determinism_source) != build_archive(determinism_source):
        failures.append("determinisme: to builds af samme kilde gav forskellige bytes")

    # Determinisme alene fanger ikke en *ændret* tidskonstant: to builds i samme
    # proces er lige så ens, hvad enten TAR_MTIME er 0 eller 2020. Så konstanten
    # skal også testes for sin værdi, ellers er den bare en værdi, ingen holder.
    if TAR_MTIME != 946_684_800:
        failures.append(f"TAR_MTIME er {TAR_MTIME}, ikke det låste tidspunkt")
    with tarfile.open(fileobj=io.BytesIO(build_archive(determinism_source)), mode="r:gz") as tf:
        infos = tf.getmembers()

    # Samme pointe for gzip: `mtime=0` i headeren er det, der gør to builds på to
    # maskiner ens. Uden testen af værdien er det en konstant uden bevis.
    if build_archive(determinism_source)[4:8] != b"\x00\x00\x00\x00":
        failures.append("gzip-headerens tidsfelt er ikke nulstillet")

    cases: list[tuple[str, list[str], str]] = []

    def stamps() -> dict[str, object]:
        return {
            "mtime": {i.mtime for i in infos},
            "ejer": {(i.uid, i.gid, i.uname, i.gname) for i in infos},
            "rettigheder": {i.mode for i in infos},
            "rækkefølge": [i.name for i in infos],
        }

    found_stamps = stamps()
    if found_stamps["mtime"] != {TAR_MTIME}:
        failures.append(f"medlemmer bærer tidsstemplet {found_stamps['mtime']}, ikke TAR_MTIME")
    if found_stamps["ejer"] != {(0, 0, "", "")}:
        failures.append(f"medlemmer bærer ejerskab {found_stamps['ejer']}, ikke (0, 0, '', '')")
    if found_stamps["rettigheder"] != {0o644}:
        failures.append(f"medlemmer bærer rettigheder {found_stamps['rettigheder']}, ikke 0o644")
    if found_stamps["rækkefølge"] != sorted(MEMBERS):
        failures.append(f"medlemmer er ikke i sorteret rækkefølge: {found_stamps['rækkefølge']}")

    # 1. Den mutation der lå bag hele opgaven: kilden har fået rettet den døde
    #    udbyder, men arkivet er stadig den gamle håndlavede kopi. Mutationen
    #    laves som et tarball bygget med *samme* låste headere, så den fejl der
    #    fanges altså er indholdet og ikke tilfældige metadata.
    source, downloads = workspace("_stale_archive")
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.GNU_FORMAT) as tf:
        for member in MEMBERS:
            body = (source / member).read_bytes().replace(
                b"mahope.tools", b"Lemon Squeezy API")
            info = tarfile.TarInfo(member)
            info.size = len(body)
            info.mtime = TAR_MTIME
            info.mode = 0o644
            info.uid = info.gid = 0
            tf.addfile(info, io.BytesIO(body))
    (downloads / archive_name(source)).write_bytes(gzip_bytes(raw.getvalue()))
    cases.append((
        "arkivet er den gamle håndlavede kopi",
        check(source, downloads),
        "afviger fra en regeneration",
    ))

    # 2. Samme fejlform som opgave 18: versionen stiger, men arkivet gør ikke. Da
    #    er det nye navn der mangler, og det gamle ligger stadig som en kunde kan
    #    hente gammel kode fra — begge dele er fund.
    source, downloads = workspace("_stale_version")
    (source / "pyproject.toml").write_text(
        '[project]\nname = "site-icons"\nversion = "1.1.0"\n', encoding="utf-8")
    problems = check(source, downloads)
    cases.append((
        "versionen stiger uden at arkivet følger",
        problems,
        "mangler",
    ))
    if not any("forældet udgave" in problem for problem in problems):
        failures.append(
            f"gammelt arkiv blev ikke meldt som forældet: {problems}")

    # 3. Den løse fil kunden curl'er kan være ældre end tarballet, selv når
    #    tarballet er rigtig. Uden denne kontrol kunne de to glide fra hinanden
    #    igen, og det er præcis det der skete med README'ens domæne før denne
    #    port — håndredigeret i den løse kopi, gammelt i tarballet.
    source, downloads = workspace("_stale_loose")
    (downloads / "README.md").write_text(
        "# site-icons\n\ncurl -O https://hermes-passiv.pages.dev/site_icons.py\n",
        encoding="utf-8")
    cases.append((
        "den løse fil er ældre end tarballet",
        check(source, downloads),
        "README.md afviger fra",
    ))

    # 4. Den lukkede udbyder i en publiceret løs fil — den fejl, opgaven rejste.
    source, downloads = workspace("_banned_loose")
    (downloads / "README.md").write_text(
        "# site-icons\n\nWhen Mads opens Bitwarden (Lemon Squeezy API), keys are sold there\n",
        encoding="utf-8")
    cases.append((
        "publiceret løs fil nævner den lukkede udbyder",
        check(source, downloads),
        "lukkede udbyder",
    ))

    # 5. Samme tekst i tarballet. Løse filer sættes til *kildefilerne* her, så
    #    arkivet er det eneste, der afviger — ellers ville mutationen aldrig nå
    #    den kontrol, den er skrevet til at bevise.
    source, downloads = workspace("_banned_archive")
    stale_readme = b"Pro requires a license key. Lemon Squeezy API when available.\n"
    stale_module = b'"""Lemon Squeezy API when available."""\n'
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.GNU_FORMAT) as tf:
        for member, body in (("README.md", stale_readme), ("site_icons.py", stale_module)):
            info = tarfile.TarInfo(member)
            info.size = len(body)
            info.mtime = TAR_MTIME
            info.mode = 0o644
            info.uid = info.gid = 0
            tf.addfile(info, io.BytesIO(body))
    write_all(source, downloads)
    (downloads / archive_name(source)).write_bytes(gzip_bytes(raw.getvalue()))
    cases.append((
        "teksten i tarballet nævner den lukkede udbyder",
        check(source, downloads),
        "lukkede udbyder",
    ))

    # 6. Arkivet mangler helt.
    source, downloads = workspace("_missing_archive")
    (downloads / archive_name(source)).unlink()
    cases.append(("arkivet mangler", check(source, downloads), "mangler"))

    # 7. En løs fil mangler. `downloads.html` linker den, så den er publiceret.
    source, downloads = workspace("_missing_loose")
    (downloads / "site_icons.py").unlink()
    cases.append(("den løse fil mangler", check(source, downloads), "mangler"))

    # 8. Et forældet arkiv i samme familie ligger stadig publiceret.
    source, downloads = workspace("_stale_sibling")
    (downloads / "site-icons-0.9.0.tar.gz").write_bytes(b"\x1f\x8b" + b"\x00" * 18)
    cases.append((
        "forældet arkiv ligger stadig publiceret",
        check(source, downloads),
        "forældet udgave",
    ))

    # 9. Scenarier der skal *ikke* fejle. Uden dem ville en unødigt streng port
    #    bare have vist sig som en fejl.
    source, downloads = workspace("_extra_source_file")
    # Kilden må gerne have flere filer end de to der publiceres — ellers kunne
    # `MEMBERS` aldrig vokse, og det er netop nye kildefiler der skal kunne
    # publiceres uden at arkivet bliver ved at være grønt på en løs sammenligning.
    (source / "extra_module.py").write_text("# ny hjælpefunktion\n", encoding="utf-8")
    cases.append((
        "kilde med flere filer end de publicerede er grøn",
        check(source, downloads),
        "",
    ))

    source, downloads = workspace("_banned_in_unpublished_file")
    # Kun publiceret indhold undersøkes. `cli.py` medtages ikke i arkivet, så det
    # må gerne nævne den lukkede udbyder — fx i en kommentar om hvorfor den gamle
    # betalingsvej forsvandt. En port der også skannede ikke-publicerede
    # kildefiler, ville tvinge os til at slette historikken i stedet for at rette
    # det, der faktisk er publiceret.
    (source / "cli.py").write_text(
        "# Lemon Squeezy blev lukket; licensen kommer fra mahope.tools\n"
        "from site_icons import main\n", encoding="utf-8")
    cases.append((
        "kun ikke-publicerede kildefiler må nævne den lukkede udbyder",
        check(source, downloads),
        "",
    ))

    for name, found, expected in cases:
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
        print(f"\nbuild_site_icons_archive --self-test: {len(failures)} fejl")
        return 1
    caught = sum(1 for _n, _f, expected in cases if expected)
    print(f"build_site_icons_archive --self-test: OK ({caught} mutationer fanget, "
          f"positiv kontrol + determinisme grøn, 2 falsk-positiv-tests)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="byg i hukommelse og sammenlign med de publicerede filer")
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
        print(f"site-icons: publiceret = regeneration af {rel(SOURCE)}/ "
              f"({len(MEMBERS)} filer i tarballet + {len(MEMBERS)} løse filer)")
        return 0

    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    name = archive_name(SOURCE)
    destination = DOWNLOADS / name
    payload = build_archive(SOURCE)
    destination.write_bytes(payload)
    print(f"skrev {rel(destination)} ({destination.stat().st_size} bytes)")

    for member in MEMBERS:
        loose = DOWNLOADS / member
        blob = (SOURCE / member).read_bytes()
        loose.write_bytes(blob)
        print(f"skrev {rel(loose)} ({len(blob)} bytes)")

    for candidate in sorted(DOWNLOADS.glob("site-icons-*.tar.gz")):
        if candidate.name != name:
            candidate.unlink()
            print(f"fjernede forældet {rel(candidate)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
