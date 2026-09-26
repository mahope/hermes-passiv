#!/usr/bin/env python3
"""Mål de fire veje `eaa-scanner-README.md` lover, og døm dem mod virkeligheden.

Baggrunden er opgave 88. `test_scanner_core_redirect.py` (opgave 87) dømte
*kommandoen* i README'en — at `python scan.py` kører de 22 regler. Men README'en
lover **fire** veje ind i produktet, og ingen port målte de andre tre. De blev
målt ved hånd i denne iteration, og tre af dem var i stykker:

**Fund 1 — installationsvejen pegede på en pakke der ikke findes.** README'ens
første kodeblok var `pip install eaa-scanner`. PyPI svarer **404** på
`/pypi/eaa-scanner/json`, så den første kommando en kunde kører fejler med
"No matching distribution found". Det er den mest synlige linje i hele filen.
Mærkeligt nok lå den rigtige kommando allerede to steder i repoet —
`site/downloads.html:62` siger `pip install /downloads/eaa_scanner-1.2.0-py3-none-any.whl`,
og `site/blog/accessibility-scanner-cli.html:89` siger "download the wheel".
Downloadsiden siger endda med egne ord: *"Once the package is on a registry, a
simple `pip install` will work — for now, use the URL above."* Så **README'en
var den eneste af de tre, der lå på den anden side af sandheden.**

**Fund 2 — kilde-zip'en har ingen mappe at gå ind i.** README'en befalede
`unzip eaa-scanner-desktop-src-1.3.4.zip && cd desktop`. Målt på det faktisk
publicerede arkiv: **11 filer i roden, nul mapper** (`unzip -Z1` giver 0 stier
med en `/`). Kommandoen fejler med `cd: no such file or directory` lige efter
at kunden har downloaded og unzippet. `site/downloads.html` havde den samme
fejl i en anden formulering (`cd eaa-scanner-desktop`), så **to sider lærte den
samme kommando fra hinanden** — den slags fejl der spreder sig, fordi ingen
kører den.

**Fund 3 — DMG'en var elleve releases gammel.** README'en linkede til
`eaa-scanner-desktop-v1.2.0`, mens `site/downloads.html` solgte **v1.3.3** og
kilden i repoet er **1.3.4**. De tre tal stod i tre filer, og ingen port
sammenlignede dem. En kunde der læser README'en fik 1.2.0; en der læser
downloadsiden fik 1.3.3. Det er ikke en død 404 — v1.2.0-assets findes stadig —
så det er den værre slags: den **ser** ud til at virke.

**Fund 4 — Actions-workflowet er Node, ikke Python.** README'en er skrevet som
et Python-dokument ("Zero dependencies. Pure Python standard library. Python
3.8+"), og dens GitHub Actions-sektion peger på en template der gør
`npm install --global …tgz`. Filen siger det selv i kommentaren, men README'en
sigde det ikke: en Python-kunde kopierer en template, der **stille** installerer
et andet produkt. Begge kører de 22 regler, så tallet er ikke i vejen — men
den løfter, der står i README'en, er ikke den template leverer.

Derfor dømmer denne port fem ting, alle offline og alle målt mod den fil
kunden faktisk får:

1. **Alle `/downloads/<fil>`-links i README'en findes** i `site/downloads/`.
   Et dødt download-link er den fejl der koster kunden mest.
2. **Installationslinjen er den der virker** — altså enten hjul-URL'en eller
   en ægte sdist, aldrig den pypi-genvej der 404'er.
3. **Byggekommandoerne mod kilden-zip'en passer til arkivets virkelige layout.**
   Det læses med `unzip -Z1` på det publicerede arkiv, ikke i kildeteksten.
4. **Desktop-versionen er den samme som downloadsiden sælger**, og
   asset-filnavnet har den form release-taggen bruger.
5. **CLI-navnet i README'en er det console_script hjulet erklærer.**

Porten læser README'en, `site/downloads.html` og de publicerede artefakter.
Den tæller ikke linjer og den læser ikke kode — den spørger om det, der står i
teksten, findes og virker. Det er sammeprincip som `test_plugin_engine_rules.py`
og `test_scanner_core_redirect.py`: mål det kunden får, ikke det der ligner det.

Brug:
    python3 tools/check_readme_paths.py            # døm de fem veje
    python3 tools/check_readme_paths.py --list     # vis hvad porten dømmer
    python3 tools/check_readme_paths.py --self-test # bevis at porten bider
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
README = REPO / "site" / "downloads" / "eaa-scanner-README.md"
DOWNLOADS_HTML = REPO / "site" / "downloads.html"
DOWNLOADS_DIR = REPO / "site" / "downloads"
WHEEL = DOWNLOADS_DIR / "eaa_scanner-1.2.0-py3-none-any.whl"
SRC_ZIP = DOWNLOADS_DIR / "eaa-scanner-desktop-src-1.3.4.zip"

# Find 1: den pypi-genvej der svarer 404. Vi rammer den kun når den står som
# en *installationskommando* — "pip install eaa-scanner" i en forklarende
# sætning ("er ikke på PyPI") skal ikke være en fejl, for så retter vi netop
# den tekst der forteller sandheden.
RE_PYPI_SHORTCUT = re.compile(r"^\s*pip install +eaa-scanner\s*$", re.M)

# Find 1: de rigtige veje. Mindst én skal være i README'en.
RE_WHEEL_INSTALL = re.compile(
    r"pip install +(\S*eaa_scanner-\d[\d.]*-py3-none-any\.whl)")
RE_SDIST = re.compile(r"eaa_scanner-\d[\d.]*\.tar\.gz")

# Find 2: et `cd <mappe>` umiddelbart efter en unzip af kilden.
RE_UNZIP_CD = re.compile(r"unzip +eaa-scanner-desktop-src-[\d.]+\.zip[^\n`]*"
                         r"(?:&& *)?cd +(\S+)")

# Find 4: release-asset-URL'en. Vi kan ikke nå GitHub fra porten, så vi dømmer
# den mod den form de faktiske assets har, og mod den version downloadsiden
# sælger — det er den krydsmåling, der fangede v1.2.0 mod v1.3.3.
RE_RELEASE_ASSET = re.compile(
    r"releases/download/eaa-scanner-desktop-v(\d+\.\d+\.\d+)/"
    r"EAA\.Compliance\.Scanner-\1-([a-z0-9-]+)\.(dmg|zip|exe|deb|AppImage)")

# Find 4: den version downloads.html sælger i sine links.
RE_SOLD_VERSION = re.compile(
    r"releases/download/eaa-scanner-desktop-v(\d+\.\d+\.\d+)/")


def readme() -> str:
    return README.read_text(encoding="utf-8")


def top_level_dirs(archive: Path) -> set[str]:
    """Mapperne i et publiceret arkiv.

    Find 2: kunden unzipper i *sin* mappe, så en `cd` er kun rigtig hvis
    arkivet har en mappe at gå ind i. Vi ser på arkivet som det ligger i
    `site/downloads/`, fordi det er den fil han henter.
    """
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
    return {n.split("/", 1)[0] for n in names if "/" in n}


def sold_version(html: str) -> str | None:
    found = RE_SOLD_VERSION.findall(html)
    if not found:
        return None
    # Nyeste version, så en side der nævner både gammel og ny sorterer rigtigt.
    return sorted(found, key=lambda v: [int(p) for p in v.split(".")])[-1]


def check_install_path(text: str) -> list[str]:
    """Fund 1: den første kommando kunden kører skal virke."""
    errs = []
    if RE_PYPI_SHORTCUT.search(text):
        errs.append(
            "README'en befaler `pip install eaa-scanner`, men pakken er ikke på "
            "PyPI (pypi.org/pypi/eaa-scanner/json svarer 404). Befal "
            "`pip install <wheel-URL>` fra site/downloads/ i stedet — det er "
            "den kommando site/downloads.html:62 og bloggen allerede bruger.")
    if not (RE_WHEEL_INSTALL.search(text) or RE_SDIST.search(text)):
        errs.append(
            "README'en har ingen installationsvej der virker: den skal pege på "
            "hjulet (eaa_scanner-<v>-py3-none-any.whl) eller sdist'en i "
            "site/downloads/.")
    return errs


def check_download_links(text: str) -> list[str]:
    """Fund 1: et dødt download-link er den dyreste fejl i filen.

    Vi ser på to slags navne: dem der står som `/downloads/<fil>` (et link) og
    dem der bare nævnes i prosa (fx sdist'en, der læses som "the sdist from the
    same downloads page"). En kunde der læser den anden slags skal kunne
    hente filen, så porten skal kunne se den — ellers er den prøve en tavshed.
    """
    errs = []
    linked = set(re.findall(r"/downloads/([A-Za-z0-9._-]+)", text))
    # Publicationsfiler, README'en beder kunden hente. Kun navne der ligner
    # filer i site/downloads/, så vi ikke dømmer almindelig tekst.
    named = {
        n for n in re.findall(
            r"\b([A-Za-z0-9._-]+\.(?:whl|tar\.gz|zip))\b", text)
        if "-" in n
    }
    # Release-assets ligger på GitHub, ikke i site/downloads/ — de dømmes af
    # versionstjekket, ikke af filnavnet. Ellers rødmer porten på et navn der
    # aldrig skulle ligge i downloads-mappen.
    release_assets = {m.group(0).rsplit("/", 1)[-1]
                      for m in re.finditer(r"releases/download/[^\s)\"']+", text)}
    for name in sorted(linked | (named - release_assets)):
        if not (DOWNLOADS_DIR / name).exists():
            errs.append(
                f"README'en navngiver {name}, som ikke findes i "
                f"site/downloads/. Kunden får en 404.")
    return errs


def check_src_zip_commands(text: str) -> list[str]:
    """Fund 2: `cd` efter unzip skal svare til arkivets virkelige layout."""
    errs = []
    if not SRC_ZIP.exists():
        errs.append(f"{SRC_ZIP.name} mangler i site/downloads/.")
        return errs
    dirs = top_level_dirs(SRC_ZIP)
    for target in RE_UNZIP_CD.findall(text):
        name = target.strip().strip("/")
        if name not in dirs:
            errs.append(
                f"README'en siger `unzip {SRC_ZIP.name} && cd {name}`, men "
                f"arkivet har ingen mappe `{name}`. Det publicerede arkiv har "
                f"{len(dirs)} top niveau-mappe(r) "
                f"({', '.join(sorted(dirs)) or 'ingen — filerne ligger i roden'}), "
                f" så kommandoen fejler med `cd: no such file or directory`. "
                f"Skriv `unzip {SRC_ZIP.name}` uden `cd`.")
    return errs


def check_desktop_version(text: str, html: str) -> list[str]:
    """Fund 3 og 4: samme version i README og downloads-side, gyldig asset-form."""
    errs = []
    versions = sorted({m.group(1) for m in RE_RELEASE_ASSET.finditer(text)})
    if not versions:
        errs.append(
            "README'en har ingen release-link til desktop-appen, men den "
            "lover en DMG. Uden linket er den vej død.")
        return errs

    for ver, platform, ext in RE_RELEASE_ASSET.findall(text):
        if not re.fullmatch(r"[a-z0-9-]+", platform) or ext != platform.split("-")[-1] \
                and ext not in ("AppImage", "zip", "exe", "dmg", "deb"):
            errs.append(
                f"README'en linker til et v{ver}-asset med platformen "
                f"'{platform}', som ikke er det navn release'en bruger "
                f"(f.eks. mac-arm64, mac-x64, linux-x86_64, win-x64).")

    sold = sold_version(html)
    if sold and versions and versions[-1] != sold:
        errs.append(
            f"README'en tilbyder desktop v{versions[-1]}, men site/downloads.html "
            f"sælger v{sold}. En kunde der læser README'en får en ældre "
            f"build end den han fik på downloadsiden.")

    # En build der er ældre end den, kilden er, giver ingen mening: kilden er
    # den eneste vej til det nyeste, og den siger det selv.
    src = RE_SRC_ZIP_VERSION.search(text)
    if src and sold:
        s_v = [int(p) for p in src.group(1).split(".")]
        d_v = [int(p) for p in sold.split(".")]
        if s_v < d_v:
            errs.append(
                f"README'en siger kilden er v{src.group(1)}, men den sælger "
                f"desktop v{sold} — den anbefaler altså en bygge-kilde der er "
                f"ældre end den installer den sender folk til.")
    return errs


RE_SRC_ZIP_VERSION = re.compile(r"eaa-scanner-desktop-src-(\d+\.\d+\.\d+)\.zip")


def check_cli_name(text: str) -> list[str]:
    """Fund 5: navnet i README'en skal være det hjulet erklærer."""
    errs = []
    if not WHEEL.exists():
        errs.append(f"{WHEEL.name} mangler i site/downloads/.")
        return errs
    with zipfile.ZipFile(WHEEL) as zf:
        try:
            entry = zf.read("eaa_scanner-1.2.0.dist-info/entry_points.txt").decode()
        except KeyError:
            errs.append(
                f"{WHEEL.name} har ingen entry_points.txt — porten kan ikke "
                f"finde ud af hvad CLI'en hedder.")
            return errs
    declared = re.search(r"^(\S+)\s*=", entry, re.M)
    if not declared:
        errs.append(f"{WHEEL.name} erklærer ingen console_script.")
        return errs
    if declared.group(1) not in text:
        errs.append(
            f"README'en bruger ikke CLI-navnet `{declared.group(1)}`, som er det "
            f"hjulet erklærer. Kommandoerne i README'en vil ikke virke.")
    return errs


def check_actions_language(text: str) -> list[str]:
    """Fund 4: README'en er Python, så den skal sige at templaten er Node."""
    if "eaa-scan-github-action.yml" not in text:
        return []
    if re.search(r"[Ww]orkflow.*\bnpm\b|\bNode\.js build\b|\bNode build\b", text):
        return []
    return [
        "README'en peger på et GitHub Actions-workflow uden at sige at det "
        "installerer npm-pakken. README'en lover en Python-pakke, så en "
        "Python-kunde kopierer en template der stille installerer et andet "
        "produkt. Sæt en linje om at templaten bruger Node 18+ og npm."]


def run_checks(readme_text: str, html_text: str) -> list[str]:
    errs: list[str] = []
    errs += check_install_path(readme_text)
    errs += check_download_links(readme_text)
    errs += check_src_zip_commands(readme_text)
    errs += check_desktop_version(readme_text, html_text)
    errs += check_cli_name(readme_text)
    errs += check_actions_language(readme_text)
    return errs


CHECKS = (
    "installationsvejen peger på noget der findes (ikke en pypi-genvej der 404'er)",
    "alle filer README'en beder kunden hente, findes i site/downloads/",
    "`cd` efter unzip svarer til det publicerede kildearkivs layout",
    "desktop-versionen er den downloadsiden sælger, og assets har gyldigt navn",
    "CLI-navnet i README'en er det console_script hjulet erklærer",
    "GitHub Actions-templaten er mærket som Node, siden README'en er Python",
)

# (navn, mutation) — hver mutation skal gøre porten RØD, ellers bæder den
# intet. Samme kontrakt som `check_rule_claims.py --self-test`.
MUTATIONS = (
    ("pypi-genvej ind i README'en igen",
     lambda r, h: (re.sub(r"^pip install \S+eaa_scanner-[\d.]+-py3-none-any\.whl$",
                          "pip install eaa-scanner", r, flags=re.M), h)),
    ("dødt download-link",
     lambda r, h: (r.replace("eaa_scanner-1.2.0.tar.gz", "eaa_scanner-9.9.9.tar.gz"), h)),
    ("`cd` ind i en mappe arkivet ikke har",
     lambda r, h: (re.sub(r"(unzip +eaa-scanner-desktop-src-[\d.]+\.zip)`?", r"\1 && cd desktop", r, count=1), h)),
    ("DMG'en falder tilbage til v1.2.0",
     lambda r, h: (re.sub(r"(eaa-scanner-desktop-v)1\.3\.3", r"\g<1>1.2.0", r), h)),
    ("CLI-navnet i README'en er forkert",
     lambda r, h: (r.replace("eaa-scan", "eaa_scan"), h)),
    ("Actions-templaten mærkes ikke længere som Node",
     lambda r, h: (re.sub(r"\*\*This workflow uses the Node\.js build.*?\n",
                          "", r, flags=re.S), h)),
)


def self_test() -> int:
    real_r, real_h = readme(), DOWNLOADS_HTML.read_text(encoding="utf-8")
    if run_checks(real_r, real_h):
        print("SELFTEST: den ægte README er rød — ret porten før mutationerne.")
        return 1
    print(f"selftest: den ægte README er grøn over {len(CHECKS)} prøver")
    bad = 0
    for name, mutate in MUTATIONS:
        m_r, m_h = mutate(real_r, real_h)
        if m_r == real_r and m_h == real_h:
            print(f"  MUTATION UDEN EFFEKT: {name}")
            bad += 1
            continue
        if run_checks(m_r, m_h):
            print(f"  rød som den skal: {name}")
        else:
            print(f"  MUTATION IKKE FANGET: {name}")
            bad += 1
    print(f"selftest: {len(MUTATIONS) - bad}/{len(MUTATIONS)} mutationer fanget")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true", help="vis hvad porten dømmer")
    ap.add_argument("--self-test", action="store_true",
                    help="bevis at porten bider på mutationer")
    args = ap.parse_args()

    if args.list:
        print("check_readme_paths dømmer:")
        for i, c in enumerate(CHECKS, 1):
            print(f"  {i}. {c}")
        return 0
    if args.self_test:
        return self_test()

    if not README.exists():
        print(f"FEJL: {README} mangler")
        return 1

    errs = run_checks(readme(), DOWNLOADS_HTML.read_text(encoding="utf-8"))
    if errs:
        print(f"check_readme_paths: {len(errs)} fejl i README'ens veje\n")
        for e in errs:
            print(f"  - {e}\n")
        return 1
    print(f"check_readme_paths OK: {len(CHECKS)} veje dømt, alle matcher "
          f"artefakterne ({len(CHECKS)} fund fra målingen 26/9 rettet)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
