#!/usr/bin/env python3
"""Tallet i løfterne skal være målt, ikke husket.

Baggrund (opgave 84, 26. september 2026): tre iterationer i træk har rettet det
samme løfte på hver sin måde, og alle tre var forkert, fordi ingen målte motoren
rigtigt.

  - Opgave 80: den danske EUComply-tabel sagde 24 tjek, koden sagde 29.
  - Opgave 83: tællede `add('…')`-kaldene i `runScan()` og fandt **elleve**.
    Men motoren har også fire `findings.push({id:'…'})` uden `add()`, så den
    kører **15** regler. "11" blev skrevet på fire steder, heraf den dyreste
    købsside.
  - Opgave 84: de 15 `/guides/*`-sider sagde "16 automated rules" — også
    forkert, sandheden er 15.
  - Opgave 85: `site/wordpress-plugin.html` holdt pluginsiden undtaget, fordi
    motoren "ligger i ../auditedwp". Den gør ikke: `scanner/wp-plugin/` er i
    *dette* repo, og det tal, siden lovede, var hverken 15 eller 16.

Fejlen var ikke en skrivefejl. Den var, at **regeltallet aldrig blev defineret
et sted** — hver side gættede sit eget tal, og intet checkede det mod koden.
Denne fil gør opgaven umulig at gentage: den tæller reglerne i koden og fejler
på hvert løfte, der ikke matcher.

    python3 tools/check_rule_claims.py             # alle løfter mod målt kode
    python3 tools/check_rule_claims.py --list      # de målte tal, med kilde
    python3 tools/check_rule_claims.py --self-test # beviser at porten kan rødme

**Målt dækning, 30/9.** Porten læser **alle 303** sider i `site/`
(`Layout.site.rglob("*.html")`) — altså hele overfladen, ingen fil-liste som i
`check_product_copy.py`'s 13 navngivne filer. Dømtekraften er smallere end
overfladen, og det er værd at skrive ned:

* **79** af 303 sider har mindst ét løfte porten dømmer. De øvrige **224**
  læses, men ingen regel fyrer på dem.
* Alle fem arter giver **239** dømte løfter, og alle matcher koden
  (15 frie + 18 Pro = 33): 185 frie, **28** `RE_PRO`, 26 totaler. Før denne
  iteration var det 201, fordi Pro-tallet og de 12 totaler uden "in all" var
  **udømte** — `grep server-side` gav kun kommentarer. Målt, ikke gættet:
  alle 28 forekomster i korpus har tallet 18.
* `RE_HERO` fyrer **15** gange, på **15** sider. Der er **198** sider med et
  `hero-note`-element, så porten dømmer bevidst kun en brøkdel af dem — den
  kræver et regel- eller tjekord, fordi `guides/platforms.html` siger
  "15 platforms" i præcis samme design. Det er målt, ikke valgt; grunden står
  ved `RE_HERO`.

    Forsigtig ved at måle denne port med et eget regex. Grene af `RE_CLAIM`
    ser hver især ud som døde — en håndudtrukket optælling fandt 12 af 26 med
    nul fund, bl.a. "nøgne N rules", som `downloads.html` skriver *én* gang.
    Sammensætningen er bredere end grenene, så kun portens egen tæller er
    gyldig. Det er samme fejl som i `check_product_copy.py`: mål med portens
    egen normalisering, ellers måler du en anden kode end den der gater.
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Fri regel = `add('ID'` **eller** en `findings.push({id:'ID'`. At tælle kun
# `add()` er præcis den fejl opgave 83 lavede.
RE_FREE_ID = re.compile(r"""add\('([A-Z_0-9]+)'|findings\.push\(\{\s*id:'([A-Z_0-9]+)'""")
RE_PRO_ID = re.compile(r"push\('([A-Z_0-9]+)'")
RE_ELSE_IF = re.compile(r"\belse\s+if\s*\(")

# PHP-motoren skriver sit regel-id på to måder: `$add( 'ID', …)` og
# `$findings[] = array( 'rule_id' => 'ID', … )`. Den tredje form i JS,
# `findings.push({id:'ID'})`, findes ikke i PHP.
RE_PHP_FREE_ID = re.compile(
    r"""add\(\s*'([A-Z_0-9]+)'|'rule_id'\s*=>\s*'([A-Z_0-9]+)'""")

# Desktop-appen og npm-CLI'en skriver deres fund med nøglen `rule_id` i stedet
# for `id`, så `RE_FREE_ID` ville måle 11 i stedet for 22 i dem. Derfor måles
# alle tre JS-former.
RE_JS_ID = re.compile(
    r"""add\('([A-Z_0-9]+)'|findings\.push\(\{\s*id:'([A-Z_0-9]+)'"""
    r"""|rule_id\s*:\s*'([A-Z_0-9]+)'""")

# Python bruger dobbelte anførselstegn og skriver desuden regel-id'et på den
# næste linje end kaldet. Derfor måles denne motor på hele filen.
RE_PY_ID = re.compile(
    r"""add\(\s*['"]([A-Z_0-9]+)['"]"""
    r"""|['"]?rule_id['"]?\s*(?:=>|:)\s*['"]([A-Z_0-9]+)['"]"""
    r"""|Finding\(\s*['"]([A-Z_0-9]+)['"]""",
    re.DOTALL,
)

# Motoren i det zip, kunden henter. Ikke `scanner/wp-plugin/`: kilden er
# versioneret i dette repo, men **den publicerede fil er det, løftet gælder** —
# og den er ikke den samme (opgave 85 målte 16 i zip'en mod 22 i kilden).
PLUGIN_ENGINE_IN_ZIP = "eaa-compliance-scanner/engine.php"

# Et løfte er et tal umiddelbart før en af disse. Kun disse former gater:
# opgaven er at holde *regel*-tal sande, ikke at tælle alle tal på en side.
#
# `automated (WCAG N.N AA )?rules` dækker *også* "16 WCAG 2.1 AA rules". Den
# lange form lå uden om porten indtil opgave 86, fordi den gav 34 løfter porten
# ikke kunne dømme. Årsagen var ikke de 34, men at porten havde **én** motor
# (`scan.html`) som svar på alle spørgsmål. Med produkt→motor-kortet nedenfor er
# de 34 dømmelige, så den lange form er sat i igen.
RE_CLAIM = re.compile(
    r"(?:"
    r"(?P<n>\d+)\s+"
    r"(?:"
    r"automatiske\s+regler"           # 16 automatiske regler
    r"|automated\s+(?:WCAG\s+[\d.]+\s+AA\s+)?rules"   # 16 automated rules
    r"|WCAG\s+[\d.]+\s+AA\s+rules"     # 16 WCAG 2.1 AA rules
    r"|automatiske\s+tjek"             # 11 automatiske tjek
    r"|automated\s+checks"             # 11 automated checks
    r"|automated\s+accessibility\s+rules"
    r"|WCAG-regler"                    # 16 WCAG-regler
    r"|accessibility\s+(?:rules|checks)"
    r"|WCAG\s+[\d.]+\s+AA\s+regler"
    r"|WCAG\s+[\d.]+\s+AA-regler"         # 22 WCAG 2.1 AA-regler (dansk, bindestreg)
    r"|regler"                            # 22 regler
    # De tre nedenfor er ikke flere synonymer, de er de **formuler den målte
    # fejl havde**. Før denne iteration stod fire publicerede sider med "16" om
    # en motor der kører 15, og `RE_CLAIM` fangede præcis **én** af dem:
    # "16 WCAG-regler". De tre andre slap igennem, fordi mønstret lister
    # ordformer i stedet for begrebet:
    #   "16 automatiserede WCAG 2.1 AA-regler" — "automatiserede" er ikke
    #     "automatiske", så intet før "WCAG" passerede.
    #   "16 automated WCAG rules" — der står et ord ("WCAG") mellem
    #     "automated" og "rules", så `automated\s+rules" passede ikke.
    #   "16 WCAG compliance rules" — samme fejl, plus "compliance" mellem
    #     "WCAG" og "rules" og ingen versionsstreng.
    # Derfor er der nu tilladt *ét* valgfrit kvalificerende ord mellem
    # "automated" og regelordet, og tilladt at en WCAG-streng mangler både
    # version og A/N-niveau. Det er målt, ikke valgt: se `SUPERSEDED` nedenfor
    # og selftestens tre nye arme, der genskaber præcis de tre oversete former.
    r"|automatis(?:ke|erede)\s+(?:[\d.]+\s+)?(?:WCAG\s+)?(?:[\d.]+\s+AA[- ]?)?(?:regler|tjek)"
    r"|automated\s+(?:[\d.]+\s+AA\s+)?(?:WCAG|compliance|accessibility|EAA)\s*"
    r"(?:[\d.]+\s+AA\s+)?(?:rules|checks)"
    r"|WCAG\s*(?:[\d.]+\s*AA\s*)?(?:compliance\s+|-\s*)?(?:rules|regler)"
    # Den fjerde oversete form, målt 29/9 af review: et tal foran et
    # **sammensat** dansk ord. Den danske købsside skrev "kører 11
    # tilgængelighedsregler" i linje 171, mens linje 99, 153 og 179 på *samme
    # side* skrev 15 — og ingen af dem blev dømt, fordi mønstret kendte
    # `regler` som et selvstændigt ord og ikke som halvdel af
    # `tilgængelighedsregler`. Samme fejl som de tre ovenfor, en linje dybere:
    # en sprogform der mangler i listen er usynlig. Derfor er kun denne ene
    # sammensætning taget med — ikke et generelt `[\w-]+regler`, der ville
    # dømme enhver opdiget sammensætning. Selftestens arm genskaber formen på
    # den rigtige fil.
    r"|tilgængeligheds(?:regler|tjek)"     # 11 tilgængelighedsregler
    r")"
    # Nøgne regelord — "16 rules", "22 regler" — kræver et **to-cifret** tal.
    # Det er målt, ikke valgt, og begge halve er målt:
    #
    #  * Uden engelsk tvilling lå der seks publicerede løfter om "16 rules" om
    #    en motor der kører 15 (fire i JSON-LD-FAQ på CMS-guides, én i en
    #    `<meta name="description">`, ét i brødteksten på CLI-siden som sælger
    #    en motor på 22). `downloads.html`'s "Same 22 rules" er rigtig. Den
    #    danske linje ovenfor dømte nøgne "22 regler" hele tiden, så mønstret
    #    kendte den danske *form* af regelordet og ikke den engelske — samme
    #    fejl som fund 5 ovenfor, en linje dybere: en sprogform der mangler i
    #    listen er usynlig.
    #  * Uden to-cifret-grænsen dør porten på `blog/nis2-incident-report-checklist`,
    #    der skriver "2 rules" om NIS2-forretninger. Det er brødtekst om en hel
    #    anden ting, ikke et løfte om vores motor.
    #
    # Grænsen er ikke et arbitrært tal: **alle** motorer i dette repo kører 15
    # eller 22, og Pro-total er 33. Et ett-cifret tal foran et nøgt regelord kan
    # derfor ikke være et af vores løfter. Den skal bare fange den næste fejl
    # skjule sig i, så den måles ligesom alt andet i selftesten.
    r"|(?P<bare>\d{2,3})\s+(?:rules|regler)\b"
    r")",
    re.IGNORECASE,
)

# `hero-note` er sidens *egen* resumé-linje: den står i heroen lige ved den CTA
# der kører motoren, og på guidesiderne siger den "15 checks · No signup ·
# Instant grade". Opgave 89 målte den: 14 CMS-guides sagde **16** i den linje,
# fire linjer under en undertitel der sagde **15** — samme side, samme tal, to
# sandheder, fordi webkernen kører 15. Ingen form i `RE_CLAIM` så den, fordi den
# siger "checks" uden et modifierende ord.
#
# Derfor dømmes *kun* tal i en `hero-note`, og kun når enheden er et regel- eller
# tjekord. Det er målt, ikke valgt: `guides/platforms.html` siger "15 platforms ·
# No signup · Instant grade" i præcis samme design — samme tal ved en
# tilfældighed, en helt anden opgave — og `da/blog/wcag-22-krav-liste.html` siger
# "50 kriterier (A + AA)". En regel der dømte ethvert tal i en hero-note, ville være
# grøn på `platforms.html` af en tilfældighed, og det er præcis den slags
# tilfældighed, der gør en port ubrugelig.
RE_HERO = re.compile(
    r'class="hero-note"[^>]*>\s*(?P<n>\d+)\s+'
    r"(?:automatiske\s+regler|automatiske\s+tjek|automatiske\s+checks"
    r"|automated\s+rules|automated\s+checks|automated\s+accessibility\s+rules"
    r"|WCAG\s+[\d.]+\s+AA[- ]?regler|WCAG\s+[\d.]+\s+AA\s+rules|WCAG-regler"
    r"|accessibility\s+(?:rules|checks)|regler|checks?|tjek)\b",
    re.IGNORECASE,
)

# Et *totaltal* er fri + Pro. Det kendes ved to former: "33 checks in all" og
# den danske tabelrække "Alle 33 automatiske tjek", hvor fri-spalten er "—".
# Formerne lå adskilt, fordi linjen ofte rummer begge tal — "33 checks in all —
# the free 15 accessibility rules" — og et linje-vis tjek ville regne den frie
# 15 som om den også skulle være 33.
RE_TOTAL = re.compile(
    r"(?P<n>\d+)\s+(?:checks?|tjek)\s+(?:in\s+all|i\s+alt)"
    r"|Alle\s+(?P<n2>\d+)\s+automatiske\s+tjek",
    re.IGNORECASE,
)

# **Pro-løftet, målt 30/9.** `reportProFindings()` kører 18 checks, og 27 sider
# skriver dem som "18 server-side checks" / "18 server-side tjek" — men ingen
# form i `RE_CLAIM` eller `RE_TOTAL` så den, så hele Pro-tallet var et udømt
# løfte: `grep server-side` gav kun kommentarer. Beviset er målt, ikke læst:
# alle 28 forekomster i korpus har tallet 18, og porten dømmer ingen af dem.
#
# Formen er valgt efter måling, fordi tallet 18 også findes et andet sted: en
# blogtitel siger "GDPR Website Compliance Checklist: 18 Checks Every Site
# Should Pass" om *artiklens* 18 punkter. Ordformen "18 server-side checks" er
# derimod entydig — den kan kun være vores Pro-motor, fordi ingen anden måling i
# repoet hedder server-side. Derfor er mønstret **ikke** det kortere
# `(\d+)\s+checks`, som ville have dømt artiklens 18 og NIS2' 25 og 20.
RE_PRO = re.compile(
    r"(?P<p>\d+)\s+server-side\s+(?:checks?|tjek)\b",
    re.IGNORECASE,
)

# **Et total uden "in all"**, målt 30/9. `RE_TOTAL` krævede enten "in all" eller
# den danske tabelrække, så den mest almindelige sætning i huset —
# "runs 33 checks — the same 15 accessibility rules, plus 18 server-side
# checks" — var usynlig. Der er 30 forekomster af "33 checks/tjek" i korpus,
# og kun de med både fri- og Pro-tallet i samme sætning er et total: de 11
# øvrige er en overskrift, en tabelrække eller en linje med kun ét af tallene.
#
# Derfor er reglen ikke "33 skal være 33" — det ville være cirkulært og ville
# heller ikke fange et tal der *bliver* 33. Den lyder: **når en sætning både
# oplyser det frie regeltal og Pro-tallet, er et tjek-tal i den samme sætning
# summen.** Det er målt på hele korpus: 12 sætninger matcher, alle med 33, og
# ingen af dem er en artikel, en NIS2-tjekliste eller en hero-note. Sætningen
# afgrænses på `.`/`!`/`?`/`;`/`:` — efter `normalize_text()` er markupken
# mellemrum, så punktummerne er sætningsens egne.
# Hvor en sætning slutter. `;` og `:` er med, fordi en kortere sætning fyrer
# art 3 færre gange — målt 30/9 er korpus **ufølsomt** for valget (239 løfter og
# 0 fejl med begge), så den korte form er bevaret uden begrundelse.
SENT_SPLIT = re.compile(r"[.!?;:]")

# Det tjek-tal art 3 dømmer på. Kun tal med **to eller tre cifre**: et-cifrede
# tjek-tal i huset er artiklers egne ("6 checks" i en NIS2-opsummering), og
# de skal ikke dømmes mod vores motor. To-cifret-grænsen er målt på samme måde
# som `RE_CLAIM`s egen: de målte motorer kører 15, 18 og 22, så to-cifrede
# tjek-tal i korpus er 9→9(ni-cifret), 15, 18, 20, 22, 25 og 33 — og art 3
# fyrer kun når sætningen *selv* oplyser både fri- og Pro-tallet, så 20, 22 og
# 25 kan ikke nå gennem porten.
RE_CHECK_NUM = re.compile(r"\b(?P<n>\d{2,3})\s+(?:checks?|tjek)\b", re.IGNORECASE)

# Det frie regeltal i en sætning. Kun `RE_CLAIM` — `RE_HERO` er en hel linje i
# en hero, ikke en sætning, og `RE_TOTAL` er det tal vi netop er ved at finde.
FREE_CLAIM = RE_CLAIM

# Hvor `reportProFindings()` slutter i `_worker.js`. Findes ved at læse til den
# næste topniveau-funktion, så en ny push til sidst i funktionen tælles med.
PRO_FN = "function reportProFindings("


@dataclass(frozen=True)
class Layout:
    """Hvor motorerne ligger i et givet checkout."""

    site: Path

    @property
    def repo(self) -> Path:
        return self.site.parent

    @property
    def worker(self) -> Path:
        return self.site / "_worker.js"

    @property
    def engines(self) -> tuple[Path, ...]:
        return (self.site / "scan.html", self.site / "scan-da.html",
                self.site / "compliance-report.html")

    @property
    def primary(self) -> Path:
        return self.site / "scan.html"

    @property
    def plugin_zip(self) -> Path:
        """Det zip kunden henter. Kilden til pluginsidens regeltal."""
        return self.site / "eaa-compliance-scanner.zip"

    @property
    def plugin_page(self) -> Path:
        """Siden der sælger pluginet — målt mod `plugin_zip`, ikke mod JS."""
        return self.site / "wordpress-plugin.html"

    def rel(self, path: Path) -> str:
        return str(path.relative_to(self.site.parent))


# --- Motorerne -------------------------------------------------------------
#
# Der er **fire** motorer i dette repo, og de er ikke ens. Opgave 86 målte dem,
# og denne opgave flyttede pluginet ind i den store gruppe:
#
#   web      site/scan.html + scan-da + compliance-report   15
#   desktop  desktop/scanner-core.js                         22
#   cli      scanner/npm/eaa-scanner/index.js                22
#            scanner/packaging/eaa_scanner/core.py           22
#   plugin   site/eaa-compliance-scanner.zip (den publicerede) 22
#
# `plugin` var **seks regler bag de øvrige**, fordi zip'en var en ældre build af
# den samme motor — sådan som en 16-tals påstand på en 22-reglers motorside er
# sand for det publicerede arkiv og falsk for koden. Det er rettet ved at bygge
# kilden ind som v1.1.0, så de fem byggere der kører 22 er det samme regelsæt —
# ikke tilfældigt, men fordi de er samme motor. Det er derfor
# `engine_disagreements` tjekker det: hvis de divergerer, er der en reel fejl,
# ikke en ny regel.
#
# `test_plugin_engine_rules.py` er modstykket. Denne port læser koden og kan
# aldrig alene se, at det publicerede arkiv ikke er den kode vi udgiver.
#
# Et løfte skal måles mod den motor **den side sælger**. Det er derfor
# `PRODUCT_ENGINE` findes: et kort fra produkt til motor. Uden det svarede
# porten "15" på alt, og de 34 løfter i den lange `WCAG N.N AA rules`-form kunne
# ikke dømmes — de fleste af dem handler om en motor porten aldrig spurgte.

@dataclass(frozen=True)
class Engine:
    """Én motor, målt i den kode der faktisk kører."""

    key: str
    label: str
    ids: tuple[str, ...]
    source: str

    @property
    def n(self) -> int:
        return len(self.ids)


def _missing(path: Path) -> SystemExit:
    return SystemExit(
        f"check_rule_claims: motoren {path} mangler — et løfte på den side der "
        f"sælger den kan ikke måles, og det er ikke det samme som 0")


def js_engine_ids(path: Path) -> tuple[str, ...]:
    """Regel-id'er i en JS-motor. Ét kald pr. linje, som de står.

    Samme form som `free_rule_ids`, plus `rule_id: 'ID'`: desktop-appen og
    npm-CLI'en skriver deres fund som `findings.push({ rule_id: 'ID' })` og ikke
    som `findings.push({ id: 'ID' })`. Den forskel er præcis den fejl opgave 83
    lavede, bare i en anden retning — så den måles, ikke antages.
    """
    if not path.is_file():
        raise _missing(path)
    seen: list[str] = []
    for line in _read(path).splitlines():
        if RE_ELSE_IF.search(line):
            continue
        for m in RE_JS_ID.finditer(line):
            rid = m.group(1) or m.group(2) or m.group(3)
            if rid not in seen:
                seen.append(rid)
    return tuple(seen)


def py_engine_ids(path: Path) -> tuple[str, ...]:
    """Regel-id'er i en Python-motor — målt på hele filen, ikke linje for linje.

    Python bryder et kald over flere linjer:

        findings.append(Finding(
            "TABLE_HEADER", "warning", …))

    En linje-vis måling så derfor 17 i stedet for 22, fordi de fem lange kalde
    skriver id'en på næste linje. Det er samme fejlklasse som opgave 83 og 85,
    bare fordi sproget bryder linjer. Derfor måles Python helt.
    """
    if not path.is_file():
        raise _missing(path)
    seen: list[str] = []
    for m in RE_PY_ID.finditer(_read(path)):
        rid = m.group(1) or m.group(2) or m.group(3)
        if rid not in seen:
            seen.append(rid)
    return tuple(seen)


# De bygger der skal være ens. Rækkefølgen er den rækkefølge `--list` printer
# dem i, og den første er den målte resten sammenlignes mod.
#
# `plugin` er her for første gang. Opgave 85 holdt det ude, fordi zip'en var en
# ældre build med 16 mod kildens 22. Det er bygget ind som v1.1.0, så de to er
# ens og kan dømmes af samme port. Havde det stadig været 16, ville `plugin` have
# stået uden for gruppen igen — ikke fordi pluginet så anderledes ud, men fordi
# det er *forskert*, og en forskert motor må ikke bruges som mål for de andre.
CLONE_GROUP = ("desktop", "cli-npm", "cli-pip", "plugin-source", "plugin")


def engines(lay: Layout) -> dict[str, Engine]:
    """Alle motorerne, målt i den kode der kører."""
    zip_ids = php_rule_ids(lay.plugin_zip)
    return {
        "web": Engine("web", "webscanneren i browseren",
                      free_rule_ids(lay.primary), "site/scan.html"),
        "plugin": Engine("plugin", "WordPress-pluginet i det publicerede zip",
                         zip_ids, f"site/eaa-compliance-scanner.zip → "
                                  f"{PLUGIN_ENGINE_IN_ZIP}"),
        "desktop": Engine("desktop", "desktop-appen (Electron)",
                          js_engine_ids(lay.repo / "desktop" / "scanner-core.js"),
                          "desktop/scanner-core.js"),
        "cli-npm": Engine("cli-npm", "CLI'en på npm",
                          js_engine_ids(lay.repo / "scanner" / "npm"
                                        / "eaa-scanner" / "index.js"),
                          "scanner/npm/eaa-scanner/index.js"),
        # Ikke `scanner/scanner_core.py`: det er en efterlader på 16 regler.
        # Hjulene bygges af `scanner/packaging/eaa_scanner/core.py` — målt på
        # den fil, ellers ville porten robre en motor ingen downloader.
        "cli-pip": Engine("cli-pip", "CLI'en på pip",
                          py_engine_ids(lay.repo / "scanner" / "packaging"
                                        / "eaa_scanner" / "core.py"),
                          "scanner/packaging/eaa_scanner/core.py"),
        "plugin-source": Engine("plugin-source", "pluginens kildekode @1.1.0",
                                py_engine_ids(lay.repo / "scanner" / "wp-plugin"
                                              / "eaa-compliance-scanner"
                                              / "engine.php"),
                                "scanner/wp-plugin/eaa-compliance-scanner/"
                                "engine.php"),
    }


# Kortet produkt → motor. Rækkefølgen betyder: første match vinder, så de
# specifikke mønster skal stå før `guides/*`.
#
# Hver post er et produktvalg, ikke en undtagelse: den siger *hvilken motor
# siden sælger*, så løftet måles mod den motor kunden får regler fra. Kortet
# er fuldt udskrevet i `--list`, så det kan efterprøves af en læser.
PRODUCT_ENGINE: tuple[tuple[str, str], ...] = (
    # Sælger pluginet → den publicerede zip, ikke kilden og ikke webkernen.
    ("wordpress-plugin.html", "plugin"),
    # Sider der sælger eller omtaler CLI'en og desktop-appen. Begge kører 22.
    ("downloads.html", "desktop"),
    ("free-downloads.html", "desktop"),
    # Den engelske CLI-side. Den siger "The eaa-scanner applies 16 rules" i
    # brødteksten, og den sælger `scanner/npm/eaa-scanner` — altså den samme
    # motor på 22 som desktop-appen og resten af `CLONE_GROUP`. Den lå ikke i
    # kortet, fordi dens løfte ikke blev *fundet* (se `RE_CLAIM`: nøgne
    # engelske "rules" var ikke en dømt form). Så løftet slap forbi porten
    # uden at spørge efter en motor — præcis fejlen `PRODUCT_ENGINE` findes for.
    ("blog/accessibility-scanner-cli.html", "desktop"),
    ("blog/eaa-compliance-scanner-desktop.html", "desktop"),
    ("blog/free-accessibility-testing-tools.html", "desktop"),
    # De tre danske sider der sælger desktop-scanneren. De siger "Kør alle 22
    # WCAG 2.1 AA-regler lokalt på din maskine" i den fælles CTA-blok, altså om
    # *offline*-scanneren — ikke om webkernen. Før denne linje var de tre ikke i
    # kortet, så et fund ville have været en fejl i stedet for et mål.
    ("da/blog/eaa-compliance-scanner-desktop-download.html", "desktop"),
    ("da/blog/tilgaengeligheds-overlays-eaa.html", "desktop"),
    ("da/blog/wcag-22-krav-liste.html", "desktop"),
    # Købssiden for EUComply Pro: kører `compliance-report.html`.
    ("compliance-report.html", "web"),
    ("da/compliance-report.html", "web"),
    # Kontrastartiklen og dens danske spejling (29/9). De sælger den samme
    # licens og lover derfor de samme tal: "15 WCAG-regler" i gratis-spalten
    # og "18 mere, 33 i alt" i Pro-spalten — altså webkernens 15 plus
    # `reportProFindings()`'s 18, præcis som `compliance-report.html`. Før
    # denne linje var de to ikke i kortet, så et fund ville have været en
    # fejl i stedet for et mål. Det er samme fejlform som de tre linjer
    # ovenfor: siden der sælger en motor skal stå i kortet, ellers er
    # løftet udømt.
    ("blog/text-on-image-contrast-check.html", "web"),
    ("da/blog/tekst-paa-billede-kontrasttjek.html", "web"),
    # EAA-tjeklisten og dens danske spejling (30/9) — den mest linkede artikel i
    # `site/` med 41 indgående sider, målt af `check_article_paid_path.py`.
    # Samme licens og samme to tal som de to ovenfor, af samme grund: de er
    # skrevet med `compliance-report.html`'s egen gratis-mod-betalt-tabel.
    ("blog/eaa-accessibility-checklist.html", "web"),
    ("da/blog/eaa-tjekliste-2026.html", "web"),
    # NIS2-guiden og dens danske spejling (30/9) — nr. 2 på blindlisten fra
    # `check_article_paid_path.py` med 25 indgående sider. Samme licens og
    # samme to tal som de to ovenfor: NIS2 står i Pro-spalten som et af de
    # 18 server-side tjek, så artiklen sælger præcis den motor den læver.
    ("blog/nis2-readiness-guide.html", "web"),
    ("da/blog/nis2-beredskabstjek-2026.html", "web"),
    ("da/compliance-ai.html", "web"),
    # Wix-EAA-guiden og dens danske spejling (30/9) — nr. 1 på blindlisten
    # efter html-til-markdown, 17 indgående sider målt af samme port. Samme
    # licens og samme to tal som de fire ovenfor: artiklens eget trin 5 siger
    # "deliver a findings report", og det er præcis den fil Pro leverer.
    ("blog/wix-eaa-accessibility.html", "web"),
    ("da/blog/wix-tilgaengelighed-eaa.html", "web"),
    # PrestaShop-EAA-guiden og dens danske spejling (30/9) — nr. 1 på
    # blindlisten efter nedbruds-guiden, 4 indgående sider på den danske målt
    # af `check_article_paid_path.py`. Samme licens og samme to tal som de to
    # ovenfor, og grunden er artiklens egen trin 5: den siger at du skal
    # levere en fundrapport, en re-scan-verifikation og en
    # tilgængelighedserklæring, hvilket er præcis den fil Pro leverer.
    ("blog/prestashop-eaa-accessibility.html", "web"),
    ("da/blog/prestashop-tilgaengelighed-eaa.html", "web"),
    # GDPR-vs-NIS2-artiklen og dens danske spejling (30/9) — toppen på
    # blindlisten fra `check_article_paid_path.py` med 9 indgående sider.
    # Samme licens og samme to tal som de otte ovenfor: artiklens egen
    # pointe er at ét dokumentsæt dækker begge regværker, og GDPR/NIS2-
    # tjekkene er præcis de 18 server-side fund i Pro-spalten. Uden denne
    # linje var artiklens "15 WCAG rules" et fund uden motor — altså en
    # fejl i stedet for et mål, præcis som de foregående linjer.
    ("blog/gdpr-vs-nis2-overlap.html", "web"),
    ("da/blog/gdpr-vs-nis2-overlap-da.html", "web"),
    # Cookie-consent-guiden og dens danske spejling (30/9) — 14 indgående
    # sider, målt af samme port. Samme licens og samme to tal som de fem
    # ovenfor: artiklens eget punkt 3 siger "if you cannot produce a
    # timestamped record, you cannot prove consent", og det er præcis den
    # fil Pro leverer. Bemærk at den her *er* om GDPR/cookie-tjek — de 18
    # server-side tjek er altså ikke en side-note, men artiklens emne.
    ("blog/cookie-consent-gdpr-compliance.html", "web"),
    ("da/blog/cookie-consent-gdpr-2026.html", "web"),
    # EAA-CLI-guiden på dansk (30/9) — 7 indgående sider, målt af
    # `check_article_paid_path.py` som blindlistens nr. 1 da --write kørte.
    # **Kun den danske.** Den engelske spejling `blog/accessibility-scanner-cli`
    # står allerede i kortet som `desktop` ovenfor (med sine 22 regler fra
    # scanneren), og de to sider sælger to forskellige motorer: artiklen er om
    # CLI'en, den nye sektion om webkernen. Samme slug med to kortværdier er
    # umulig — `engine_key_for` returnerer den første match — så spejlingen
    # får ingen købsknap, og dens 3 indirekte veje er allerede målt med
    # `paid_links()`. Uden denne linje var sektionens "18 mere, 33 i alt" et
    # fund uden motor, altså en fejl i stedet for et mål.
    ("da/blog/tilgaengelighedsscanner-cli.html", "web"),
    # GitHub-Action-guiden og dens danske spejling (30/9) — 8 indgående
    # sider, målt af `check_article_paid_path.py`. Samme licens og samme to
    # tal som de otte ovenfor, og her er målingen af *hvorfor* særlig
    # tydelig: artiklens egen tekst siger at action'en prober for
    # `/privacy` og genkender 15+ samtykkeplatforme, mens Pro's 18
    # server-side fund er GA_NO_CONSENT, FB_NO_CONSENT og PRIVACY_LINK —
    # altså forskellen på "siden findes" og "samtykket virker". Det er
    # artiklens egen pointe, ikke en tilføjet vinkel.
    ("blog/compliance-check-github-action.html", "web"),
    ("da/blog/compliance-tjek-github-action.html", "web"),
    # Webflow-vs-Squarespace-sammenligningen og dens danske spejling (30/9) —
    # 10 indgående sider, målt af `check_article_paid_path.py`. Samme licens og
    # samme to tal som de syv ovenfor: artiklens eget kort "Statement Required"
    # siger "publish an accessibility statement with conformance status and
    # known limitations", og det er præcis den fil Pro leverer. Begge sider
    # lå uden denne linje ikke i kortet, så et fund ville have været en fejl i
    # stedet for et mål — samme fejlform som de tre linjer ovenfor.
    ("blog/webflow-vs-squarespace-accessibility.html", "web"),
    ("da/blog/webflow-vs-squarespace-tilgaengelighed.html", "web"),
    # Den engelske `compliance-ai.html` lå her ikke, kun den danske spejling.
    # Det var usynligt, fordi løftet på den engelske side ("16 WCAG compliance
    # rules") ikke blev fundet af `RE_CLAIM` — så porten nåede aldrig at spørge
    # efter en motor. Målt i denne iteration: den side løfter 15, og det er
    # webkernen der kører den.
    ("compliance-ai.html", "web"),
    # Erklæringsgeneratoren (30/9) — 29 indgående sider, nr. 1 på
    # `check_tool_paid_path.py`'s blindliste da `--write` kørte. Den sælger
    # EUComply Pro og låfter derfor de samme tal som de artikler ovenfor:
    # "33 checks", "de samme 15 accessibility rules, plus 18 server-side …".
    # Motoren er webkernen — det er den `/compliance-report` kører, og det er
    # også den scanneren på `/scan` kører, som sidens egen disclaimer
    # henviser til. Uden denne linje var løfterne **udømte**, altså en fejl i
    # stedet for et mål: præcis den fejlform porten findes for.
    ("accessibility-statement-generator.html", "web"),
    # E-bog-bundlens side (30/9) — 199 indgående sider, største blinde
    # værktøjsside målt af `check_tool_paid_path.py`. Den sælger EUComply Pro
    # og lover derfor de samme tal som de otte artikler ovenfor: "33 checks",
    # "de samme 15 accessibility rules, plus 18 server-side …". Uden denne
    # linje var løfterne **udømte**, altså en fejl i stedet for et mål —
    # præcis den fejlform porten findes for.
    ("books/compliance-bundle.html", "web"),
    ("scan.html", "web"),
    ("scan-da.html", "web"),
    # De otve gratis tjek og deres næste-vej til EUComply Pro (30/9). Målt før
    # ændringen: de otve sider havde 0 `buy.stripe.com` og 0 enklaver mod
    # betalt, og de løver alle den samme licens med de samme to tal som
    # `compliance-report.html` — "15 accessibility checks" i den ene sætning og
    # "18 server-side … 33 in all" i den næste. Uden disse ni linjer var
    # løfterne **udømte**, altså en fejl i stedet for et mål: præcis den
    # fejlform porten findes for, og samme som de artikler ovenfor.
    #
    # `security-headers-check.html` står her **uden** dansk spejling, fordi
    # der ikke findes nogen: sitemap målt 30/9, kun `/security-headers-check`.
    # Det er ni sider, ikke ti — den tidligere optælling regnede den med.
    #
    # Alle ni sælger webkernen, altså motoren der kører 15 frie fund og 18 i
    # `reportProFindings()`.
    ("nis2-check.html", "web"),
    ("nis2-check-da.html", "web"),
    ("cookie-check.html", "web"),
    ("cookie-check-da.html", "web"),
    ("contrast-checker.html", "web"),
    ("contrast-checker-da.html", "web"),
    # Sidens danske tvilling. Den lå ikke i kortet fordi den *kun* omtalte
    # Pro i brødteksten uden et regeltal — den skrev «ét af de 15
    # tilgængelighedsregler» i sit eget afsnit, altså et løfte på den frie
    # motor, men i en form `RE_CLAIM` ikke greb. 1/10 fik den en boks i
    # resultatet der skriver «15 tilgængelighedstjek», og så blev løftet
    # dømmeligt — og da kom den rød med «står ikke i PRODUCT_ENGINE». Det er
    # porten der virker: et løfte uden motor kan ikke dømmes, så motoren skal
    # ind, ikke løftet væk. Samme fejl som `blog/accessibility-scanner-cli`
    # ovenfor, en linje længere nede i korpus.
    ("text-on-image-checker.html", "web"),
    ("text-on-image-checker-da.html", "web"),
    ("security-headers-check.html", "web"),
    ("compliance-site-check.html", "web"),
    ("da/compliance-site-check.html", "web"),
    # De tre næste blinde værktøjssider (30/9) — målt af
    # `check_tool_paid_path.py`: 49, 49 og 43 indgående sider i `site/`, samme
    # top-3 som den forrige iteration målte på 199/97/92. Samme licens og
    # samme tal som de to ovenfor: `books/index.html` siger "the same 15
    # accessibility rules, plus 18 server-side checks", og de to bogsider
    # siger det samme. Uden disse tre linjer var løfterne **udømte** — altså
    # en fejl i stedet for et mål, præcis som de otte artikler ovenfor.
    #
    # `books/nis2-for-agencies.html` nævner **kun** de 18, fordi NIS2 ikke
    # handler om de 15 tilgængelighedsregler: dens server-side halvdel er
    # HSTS/CSP, formularer over http, samtykkebanner og privatlivslink. Det
    # er de fund `reportProFindings()` faktisk skubber, målt i kilden. Linjen
    # står her alligevel, så det næste løfte på siden bliver dømt frem for at
    # være udømt — `RE_CLAIM` fanger "18 server-side checks" ikke i dag
    # (samme blinde plet som "33 checks"), og det er porten der skal ændres,
    # ikke kortet.
    ("books/eaa-checklist.html", "web"),
    ("books/nis2-for-agencies.html", "web"),
    ("books/index.html", "web"),
    # GDPR-bogen for bureauer (30/9) — 14 indgående sider, målt af
    # `check_tool_paid_path.py`. Den sælger den samme licens og lover de samme
    # to tal som de tre ovenfor, og grunden er bogens egen opbygning: kapitel
    # 3 og appendiks B er dokumenterne (DPA, RoPA, hændelsesplan) og den
    # klar-til-indsæt DPA-klausul, og pro-note'en siger præcis det en bog ikke
    # kan — åbne det site man leverede og se hvilke af dem der fejer i dag.
    ("books/gdpr-for-agencies.html", "web"),
    # Cookie-bogen (30/9) — 11 indgående sider, målt af
    # `check_tool_paid_path.py`. Samme licens og samme to tal som de tre
    # ovenfor, og her er motoren den tætteste match endnu: kapitel 2 er
    # inventaret, kapitel 3 banneret og kapitel 5 privatlivspolitikken, mens
    # `reportProFindings()` faktisk har seks cookie-fund her — COOKIE_BANNER,
    # COOKIE_SCRIPTS, GA_NO_CONSENT, FB_NO_CONSENT, PRIVACY_LINK og
    # NO_ANALYTICS. Målt i `_worker.js:1242-1246`.
    ("books/cookie-consent-guide.html", "web"),
    # Shopify-bogen (30/9) — 10 indgående sider, målt af
    # `check_tool_paid_path.py`. Samme licens og samme tal som de tre ovenfor, og
    # grunden er målt to steder: `/scan.html`'s egen JSON-LD-FAQ siger at
    # scanneren virker på "Any website — WordPress, Shopify, Webflow, Wix,
    # Squarespace, Drupal, Joomla, Next.js, hand-written HTML", og de 15
    # gratisregler er netop bogens kapitel 3-6 (alt-tekst, formularfelter,
    # overskrifter, kontrast, ARIA, frames, tabeller) som tjekliste frem for
    # råd. `books/eaa-checklist.html` står ovenfor med samme begrundelse for
    # WordPress-siden af samme bog.
    ("books/eaa-shopify.html", "web"),
    # Den danske DPA-generator (30/9) — 9 indgående sider, målt af
    # `check_tool_paid_path.py`. Den sælger `/da/compliance-report`, altså
    # webkernen, og dens pro-note lover præcis de 18 server-side tjek og de 33
    # i alt. Det er ikke et valg: generatorens egen `renderHTML()` danner alle
    # de obligatoriske artikel 28(3)-klausuler, så det er samme licens der
    # sælger det der mangler — om de lovede foranstaltninger er på plads.
    ("dpa-generator-da.html", "web"),
    # Den engelske DPA-generator (30/9) — 8 indgående sider, målt af
    # `check_tool_paid_path.py`. Den er den engelske søster til linjen ovenfor
    # og sælger `/compliance-report`, altså webkernen. Samme måleform: den
    # betalte $59 DPA-skabelon dækker præcis de bilag `renderHTML()` danner,
    # så det er samme licens der sælger det dokumentet ikke kan — om de
    # lovede foranstaltninger er på plads. Pro-note'en lover præcis de 18
    # server-side tjek, de 15 accessibility rules og de 33 i alt.
    ("dpa-generator.html", "web"),
    # De to privatlivspolitik-generatorer (30/9) — 9 indgående sider hver, målt
    # af `check_tool_paid_path.py`. De sælger `/compliance-report` og
    # `/da/compliance-report`, altså webkernen, og deres pro-note lover de 15
    # automatiske tjek og "33 tjek i alt". Det er ikke et valg: ingen betalt
    # vare i katalogen sælger en privatlivspolitik, så den samme licens er
    # det der sælger det dokumentet *ikke* kan — om det er linket fra sitet,
    # og om et samtykkebanner mangler. Samme måleform som de tre linjer
    # ovenfor.
    ("privacy-notice-generator.html", "web"),
    ("privacy-notice-generator-da.html", "web"),
    # Den danske farvepalet-generator (30/9) — 9 indgående sider, målt af
    # `check_tool_paid_path.py`. Den sælger `/da/compliance-report` og
    # nævner de 15 automatiske tjek som dem, den *gratis* scanner
    # `/scan-da` allerede kører — kontrast er den ene af dem
    # (`site/compliance-report.html:190`), så det er ikke en betalt streng
    # der gemmer sig i teksten. Det betalte er de 18 server-side tjek og de
    # 33 i alt, og det er samme licens som resten af familien.
    ("palette-generator-da.html", "web"),
    # Den engelske farvepalet-generator (30/9) — 8 indgående sider, målt af
    # `check_tool_paid_path.py`. Den er den engelske søster til linjen ovenfor
    # og sælger `/compliance-report`. Samme måleform: kontrast er den ene af de
    # 15 tjek den *gratis* scanner `/scan` allerede kører, så det der ikke er
    # en betalt streng. Det betalte er de 18 server-side tjek og de 33 i alt.
    ("palette-generator.html", "web"),
    # De to RoPA-generatorer (30/9) — 9 indgående sider hver, målt af
    # `check_tool_paid_path.py`. Samme måleform som de to privatlivs-
    # generatorer ovenfor: ingen af de syv betalte skabelonprodukter er en
    # behandlingsaktivitetsregistrering, så det samme `eucomply-pro` er det
    # der sælger det dokumentet *ikke* kan — om sitet stadig indlæser det,
    # registret siger, at I gør. Pro-note'en lover de 15 automatiske tjek og
    # "33 tjek i alt", altså webkernen plus `reportProFindings()`'s 18.
    ("ropa-generator.html", "web"),
    ("ropa-generator-da.html", "web"),
    # RoPA-*skabelonen* (30/9) — 7 indgående sider, målt af
    # `check_tool_paid_path.py`. Den er ikke en generator men et tomt
    # dokument, og målingen i `stripe_catalog.json` siger at ingen af de
    # syv betalte skabelonprodukter er en behandlingsaktivitetsregistrering,
    # så der er ingen betalt udgave af selve filen at love. Det er den
    # samme `eucomply-pro` som de to linjer ovenfor, og af samme grund:
    # note'en sælger det dokumentet *ikke* kan — om sitet stadig indlæser
    # det, registret siger, at I gør.
    ("ropa-template.html", "web"),
    # De to farveblindhedssimulatorer (30/9) — 7 og 5 indgående sider,
    # målt af samme port. Samme måleform som palet-generatorerne ovenfor:
    # simulatoren er gratis og komplet, kontrast er den ene af de 15 tjek
    # den *gratis* scanner `/scan` allerede kører, så det der ikke er en
    # betalt streng. Det betalte er de 18 server-side tjek og de 33 i alt.
    ("color-blindness-simulator.html", "web"),
    ("color-blindness-simulator-da.html", "web"),
    # NIS2-gapanalysen på dansk (30/9) — 6 indgående sider, målt af
    # `check_tool_paid_path.py`. Samme måleform som de to simulatorer
    # ovenfor: gapanalysen er gratis og stiller alle tyve spørgsmål i
    # artikel 21, stk. 2, så det der ikke er en betalt streng er selve
    # spørgsmålene. Det betalte er de 18 server-side tjek, fordi det er det
    # eneste af de ti områder der kan måles på en adresse — og de 33 i alt.
    ("nis2-gap-assessment-da.html", "web"),
    # Erklæringsgeneratoren på dansk (30/9) — 6 indgående sider, målt af
    # samme port. Samme måleform igen: generatoren er gratis og udsender
    # hele erklæringen efter EU's model, så det betalte er ikke selve
    # dokumentet men den test, der gør påstanden i det målbar. Note'en
    # bygger derfor direkte på sidens egen ansvarsfraskrivelse ("kun
    # test kan det") i stedet for at finde en egen vinkel på den.
    ("tilgaengelighedserklaering-generator-da.html", "web"),
    # Privatlivspolitik-skabelonen (30/9) — 6 indgående sider, målt af
    # samme port. Samme måleform: filen er gratis og komplet, så intet
    # gemmes bag en licens. Det betalte er at måle det levende site imod
    # det, dokumentet siger, at I gør.
    ("privacy-policy-template.html", "web"),
    # Guidesiderne beskriver webscanneren ("nothing to install, no signup").
    ("guides/*", "web"),
)


def engine_key_for(rel_to_site: str) -> str | None:
    """Hvilken motor siden sælger, eller `None` hvis siden ikke står i kortet.

    `None` er en **fejl**, ikke et fallback. Før opgave 86 faldt alt ukendte
    tilbage på `scan.html`, og det var netop derfor de 34 løfter i den lange
    form ikke kunne dømmes: de var ikke forkerte, de var udømt.
    """
    for pattern, key in PRODUCT_ENGINE:
        if fnmatch.fnmatch(rel_to_site, pattern):
            return key
    return None


def engine_disagreements(eng: dict[str, Engine]) -> list[str]:
    """De fire bygger af samme motor skal køre præcis samme regelsæt."""
    ref = eng[CLONE_GROUP[0]]
    ref_set = set(ref.ids)
    errs: list[str] = []
    for key in CLONE_GROUP[1:]:
        other = set(eng[key].ids)
        if other == ref_set:
            continue
        only_ref = sorted(ref_set - other)
        only_other = sorted(other - ref_set)
        parts = []
        if only_other:
            parts.append(f"kun her: {', '.join(only_other)}")
        if only_ref:
            parts.append(f"mangler hos {key}: {', '.join(only_ref)}")
        errs.append(f"{ref.source} kører {ref.n} regler, {eng[key].source} "
                    f"kører {eng[key].n} — samme motor, to tal "
                    f"({'; '.join(parts)})")
    return errs


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


_TAG = re.compile(r"<[^>]*>", re.DOTALL)
_ATTR_VALUE = re.compile(r"\"[^\"]*\"|'[^']*'")


def normalize_text(path: Path) -> str:
    """Tags bliver mellemrum — **samme længde** — og attributværdierne bliver.

    Målt 30/9 som svar på opgave 9(b): `collect()` læste linje for linje, så et
    løfte der ombrydes midt i sætningen var usynligt. Nu læses hele filen, og
    det er her markupken skal væk: ellers ville "33" i `<h1>33</h1>` og "checks"
    i næste `<p>` blive ét løfte, fordi der står whitespace imellem dem.

    To ting bevares bevidst, og begge er målt som fund:

    * **Attributværdier.** `content="… scans any URL against 22 WCAG 2.1 AA
      rules …"` på `wordpress-plugin.html` er tre af sidens løfter, og de lå i
      `<meta>`- attributter. Første version af normaliseringen blankede hele
      taggen, og porten mistede dem — samme fejl som da JSON-LD'en forsvandt.
      Derfor overlever kun indholdet mellem anførselstegn; tagnavne og
      attributnavne bliver mellemrum, så de ikke kan limme to tal sammen.
    * **Længden.** Alt andet bliver mellemrum tegn for tegn, og et linjeskift
      *inde* i en tag bliver ved et linjeskift. Derfor kan `line_of()` regne
      linjen fra offsetten, og derfor fejler porten aldrig med en forkert linje.

    Og to ting bevares fordi de *er* løfter: tekst inde i `<script>` og
    `<style>` røres ikke — det er JSON-LD-FAQ'en, hvor review 29/9 fandt fire af
    de seks publicerede "16 rules". Mønstre der læser en attribut *selv* —
    `RE_HERO` med `class="hero-note"` — kan ikke bruge denne tekst og læser
    derfor kilden med `_read()`.

    **Ingen blokgrænser.** Første version satte et punktum hvor hvert blokelement
    lukker, fordi `guides/magento-accessibility-check.html` så ud til at dømme
    sin hero-note ("15 checks · No signup") som et total. Målt 30/9: med og uden
    grænser er resultatet **identisk** — 239 løfter, 0 fejl — fordi fejlen lå et
    andet sted, i at sætningsudjævningen læste hele filen i stedet for
    sætningen. Mekanismen er derfor fjernet igen i stedet for at blive stående
    med en begrundelse der ikke holder.
    """
    raw = _read(path)

    def blank(m: re.Match[str]) -> str:
        tag = m.group(0)
        out = ["\n" if c == "\n" else " " for c in tag]
        for v in _ATTR_VALUE.finditer(tag):
            out[v.start():v.end()] = list(v.group(0))
        return "".join(out)

    return _TAG.sub(blank, raw)


def line_of(text: str, offset: int) -> int:
    """Linjenheden for en match, målt i den normaliserede tekst."""
    return text.count("\n", 0, offset) + 1


def sentence_span(text: str, start: int, end: int) -> tuple[int, int]:
    """Sætningen en match ligger i — afgrænset af `SENT_SPLIT`."""
    beg = 0
    for m in SENT_SPLIT.finditer(text, 0, start):
        beg = m.end()
    fin = SENT_SPLIT.search(text, end)
    return beg, fin.start() if fin else len(text)


def _blank(text: str, span: tuple[int, int]) -> str:
    """Samme tekst med et interval erstattet af mellemrum."""
    a, b = span
    return text[:a] + " " * (b - a) + text[b:]


def free_rule_ids(path: Path) -> tuple[str, ...]:
    """Alle frie regel-id'er i én motor, i den rækkefølge de står.

    Et id der kun kan fyre i en `else if`-gren af samme betingelse er **ikke** en
    egen regel, men et andet udfald af den samme. `HTML_LANG_SHORT` kan aldrig
    fyre sammen med `HTML_LANG`, så de to medregnes som én — ellers målte
    `compliance-report.html` 16, mens motoren faktisk kører 15.
    """
    seen: list[str] = []
    for line in _read(path).splitlines():
        if RE_ELSE_IF.search(line):
            continue
        for m in RE_FREE_ID.finditer(line):
            rid = m.group(1) or m.group(2)
            if rid not in seen:
                seen.append(rid)
    return tuple(seen)


def php_rule_ids(zip_path: Path) -> tuple[str, ...]:
    """Regel-id'erne i PHP-motoren **i det publicerede zip**.

    Måler det, brugeren faktisk installerer, og ikke `scanner/wp-plugin/`.
    De to er ikke ens: opgave 85 målte 16 i zip'en mod 22 i kilden, fordi
    kilden har seks v1.2.0-regler der endnu ikke er bygget ind i zip'en.

    En manglende motor er en fejl, ikke nul — ellers ville porten tie om at
    løftet ikke kan måles, hvilket er præcis det den blev undtaget for.
    """
    try:
        with zipfile.ZipFile(zip_path) as zf:
            src = zf.read(PLUGIN_ENGINE_IN_ZIP).decode("utf-8")
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        raise SystemExit(
            f"check_rule_claims: kan ikke læse {PLUGIN_ENGINE_IN_ZIP} fra "
            f"{zip_path.name} ({exc}) — pluginsidens regeltal kan ikke måles")
    seen: list[str] = []
    for line in src.splitlines():
        if RE_ELSE_IF.search(line) or re.search(r"\belseif\s*\(", line):
            continue
        for m in RE_PHP_FREE_ID.finditer(line):
            rid = m.group(1) or m.group(2)
            if rid not in seen:
                seen.append(rid)
    return tuple(seen)


def pro_rule_ids(worker: Path) -> tuple[str, ...]:
    """Id'erne i `reportProFindings()` — de betalte checks."""
    src = _read(worker)
    start = src.find(PRO_FN)
    if start < 0:
        return ()
    rest = src[start + len(PRO_FN):]
    nxt = re.search(r"^(?:async )?function ", rest, re.MULTILINE)
    body = rest[: nxt.start()] if nxt else rest
    seen: list[str] = []
    for m in RE_PRO_ID.finditer(body):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return tuple(seen)


def engine_for(path: Path, lay: Layout) -> Engine:
    """Hvilken motor et løfte på denne side henviser til.

    Kortet `PRODUCT_ENGINE` afgør det. **Der er intet fallback**: en side med et
    løfte, der ikke står i kortet, er en fejl. Før opgave 86 faldt alt ukendte
    tilbage på `scan.html`, og det skjulte præcis de løfter der handlede om en
    anden motor.
    """
    rel = path.relative_to(lay.site).as_posix()
    key = engine_key_for(rel)
    if key is None:
        raise SystemExit(
            f"check_rule_claims: {rel} har et regel-løfte men står ikke i "
            f"PRODUCT_ENGINE — mål den mod den motor siden sælger, eller fjern "
            f"løftet")
    eng = engines(lay)
    if key not in eng:                      # kortet kan ikke nå motoren
        raise SystemExit(f"check_rule_claims: {rel} peger på ukendte motoren "
                         f"{key!r}")
    return eng[key]


# Hvilken art løftet er: `fri`, `pro` eller `total`. Navngivet strenge fordi
# `collect()`'s returværdi læses af `check()` og af selftestens kontrol — et
# tal uden art ville være dømt mod summen altid, hvilket var den fejl.
KIND_FREE = "fri"
KIND_PRO = "pro"
KIND_TOTAL = "total"


def collect(lay: Layout) -> list[tuple[Path, int, int, str]]:
    """Alle regel-løfter som `(fil, linje, tal, art)`.

    Hele filen læses ad gangen (opgave 9(b)) — `normalize_text()` gør markup
    til mellemrum uden at flytte en eneste tegn, så et løfte der står delt over
    to linjer dømmes, og linjetallet i en fejlmeddelelse stadig er rigtigt.

    Rækkefølgen er målt, ikke valgt, fordi to af arterne deler et tal: en
    sætning som "33 checks in all — the free 15 accessibility rules, plus 18
    server-side checks" indeholder **tre** løfter, og kun de to første skal
    regnes som total. Derfor tages de brede arter først og klippes væk af den
    tekst, de resterende arter læser:

    1. `RE_TOTAL` ("33 checks in all", "Alle 33 automatiske tjek")
    2. `RE_PRO` ("18 server-side checks")
    3. et tjek-tal i en sætning der har både et fri- og et Pro-løfte
    4. `RE_HERO` (sidens egen hero-linje, på råteksten)
    5. `RE_CLAIM` (de kvalificerede regelformer + de nøgne "NN rules")

    `RE_HERO` står før `RE_CLAIM` fordi det er den *mere* specifikke match: den
    kender klassen, så den skal have det tal, ikke det generelle mønster.

    **Overlap.** "33 checks in all" matcher både art 1 og art 3, fordi sætningen
    også rummer fri- og Pro-tallet. Uden en overlap-udjævning blev det talt som
    to løfter, og `tælleren i udskriften` sagde 30 totaler for 25 sider. Derfor
    bruges **første** match: arterne er listet i prioriteret rækkefølge, så den
    mest specifikke vinder. Samme regel gør at et "18 server-side checks" ikke
    også regnes som et frit "… checks"-tal.
    """
    claims: list[tuple[Path, int, int, str]] = []
    for path in sorted(lay.site.rglob("*.html")):
        text = normalize_text(path)
        rest = text
        taken: list[tuple[int, int]] = []
        found: list[tuple[int, int, int, str]] = []   # (start, end, tal, art)

        def claim(m: re.Match[str], group: str, kind: str) -> None:
            """Talet i et fund. Mangler det, dør porten — den dømmer ikke på et gæt."""
            number = m.group(group)
            if number is None:
                raise SystemExit(
                    f"check_rule_claims: mønsteret matchede uden tallet: "
                    f"{m.group(0)!r} i {path.name}:{line_of(text, m.start())}")
            found.append((*m.span(), int(number), kind))

        for m in RE_TOTAL.finditer(text):
            total = m.group("n") or m.group("n2")
            if total is not None:
                found.append((*m.span(), int(total), KIND_TOTAL))
            taken.append(m.span())

        for m in RE_PRO.finditer(text):
            claim(m, "p", KIND_PRO)
            taken.append(m.span())

        # Et tjek-tal uden "in all": kun et total hvis **sætningen** også har
        # både det frie regeltal og Pro-tallet. Se målingen ovenfor i RE_TOTAL.
        for m in RE_CHECK_NUM.finditer(text):
            a, b = sentence_span(text, m.start(), m.end())
            sent = text[a:b]
            if not (RE_PRO.search(sent) and FREE_CLAIM.search(sent)):
                continue
            claim(m, "n", KIND_TOTAL)
            taken.append(m.span())

        # Sidens egen resumé-linje i heroen. Den er altid et *frit* tal, fordi
        # den står ved CTA'en der kører den frie motor — "15 checks · No
        # signup" — så den løftes til et fri-regel-løfte og ikke til et
        # total. Samme tal kan stå to steder i linjen (undertitel + hero-note),
        # og begge skal dømmes: det er præcis den dobbelttydighed der gemte
        # de 14 forkerede 16'ere.
        #
        # Den læses på **råteksten**, fordi den skal se attributten
        # `class="hero-note"`, og dens span klippes væk fra `rest` — ellers
        # finder `RE_CLAIM` det samme "15 automated rules" lige efter, og
        # overlap-udjævningen ville beholde det og tabe hero-armen. Målt 30/9:
        # hero-note-mutationen på `guides/comparison.html` var grøn af den
        # grund, altså rød af arbejde der lykkedes.
        for m in RE_HERO.finditer(_read(path)):
            found.append((m.start(), m.end(), int(m.group("n")), KIND_FREE))
            taken.append(m.span())
        for start, end in reversed(taken):
            rest = _blank(rest, (start, end))

        for m in RE_CLAIM.finditer(rest):
            # To grupper bærer tallet: `n` for de kvalificerede former og
            # `bare` for de nøgne regelord. Begge er løfter.
            claim(m, "n" if m.group("n") is not None else "bare", KIND_FREE)

        # Første match vinder, så en sætning der matcher to arter tælles én
        # gang. Se overlappet i docstringen. `taken` er de arter der allerede er
        # klippet væk fra `rest`; `valgt` er dem der tæller — de to må ikke
        # forveksles, ellers ville arterne 1-3 filtrere sig selv væk.
        valgt: list[tuple[int, int]] = []
        for start, end, number, kind in found:
            if any(start < b and a < end for a, b in valgt):
                continue
            valgt.append((start, end))
            claims.append((path, line_of(text, start), number, kind))
    return claims


def check(lay: Layout) -> list[str]:
    """Fejlmeldinger for alle løfter der ikke matcher den målte kode."""
    eng = engines(lay)
    pro = len(pro_rule_ids(lay.worker))
    errs: list[str] = list(engine_disagreements(eng))
    for path, line_no, claimed, kind in collect(lay):
        # Hver side måles mod den motor den sælger, ikke mod én global motor.
        base = engine_for(path, lay).n
        if kind == KIND_PRO:
            # Pro-løftet er ikke sideafhængigt: `reportProFindings()` er én
            # funktion for hele huset, så der er ingen grund til at spørge
            # hvilken motor siden sælger. Det er målt — de 28 forekomster
            # ligger på web-, bog-, guide-, plugin- og DA-sider.
            expected = pro
        elif kind == KIND_TOTAL:
            expected = base + pro
        else:
            expected = base
        if claimed != expected:
            errs.append(f"{lay.rel(path)}:{line_no}: {kind} løfter {claimed}, "
                        f"koden kører {expected}")
    # Fund skal kunne få en fix-tekst. Kun de to frie motorer renderer FIX i
    # browseren; `compliance-report.html` bruger FIXES og dækkes af porten her.
    for p in (lay.site / "scan.html", lay.site / "scan-da.html"):
        errs.extend(findings_without_fix(p))
    return errs


def show_list(lay: Layout) -> str:
    eng = engines(lay)
    pro = pro_rule_ids(lay.worker)
    lines = ["Målte regeltal (kilden er koden, ikke en note):", "",
             f"  {'motor':<14}{'regler':>7}  hvad den er"]
    for key, e in eng.items():
        lines.append(f"  {key:<14}{e.n:>7}  {e.label}")
        lines.append(f"  {'':<14}{'':>7}    {e.source}")
    lines.append("")
    for key, e in eng.items():
        lines.append(f"  {key} ({e.n}):")
        lines.append(f"    {', '.join(e.ids)}")
    lines += ["",
              f"  site/_worker.js reportProFindings(): {len(pro)} betalte checks",
              f"    {', '.join(pro)}", ""]
    web = eng["web"].n
    lines.append(f"  Pro-total = {web} + {len(pro)} = {web + len(pro)}")
    lines += ["", "Produkt → motor (hvert løfte måles mod den motor siden sælger):"]
    for pattern, key in PRODUCT_ENGINE:
        lines.append(f"  {pattern:<42} → {key} ({eng[key].n})")
    return "\n".join(lines)


def pro_count(lay: Layout) -> int:
    return len(pro_rule_ids(lay.worker))


RE_FIX_KEY = re.compile(r"^\s{4}([A-Z_0-9]+):'", re.MULTILINE)
RE_PUSH_ANY = re.compile(
    r"""add\('([A-Z_0-9]+)'|findings\.push\(\{\s*id:'([A-Z_0-9]+)'"""
)


def findings_without_fix(path: Path) -> list[str]:
    """Fund der skubbes uden id, eller med et id `FIX` ikke kender.

    Opgave 84 fandt fire af slagsen på `site/scan.html` og `site/scan-da.html`:
    de skubbede `findings.push({sev,msg})` uden id, så renderingen
    `FIX[f.id] || ''` gav en tom linje. Brugeren fik altså besked på fire af de
    femten problemer — inkl. *manglende `<title>`* og *manglende viewport* —
    uden at få sagt hvad der skulle gøres. Samme fejlform kan ikke komme igen:
    et fund skal have en id, og id'en skal have en fix-tekst.
    """
    src = _read(path)
    fixes = set(RE_FIX_KEY.findall(src))
    bad: list[str] = []
    for i, line in enumerate(src.splitlines(), 1):
        if "const add=" in line:      # definitionen af hjælperen, ikke et fund
            continue
        if re.search(r"else\s+if\s*\(", line):
            continue                 # andet udfald af samme regel, egen nøgle
        for m in RE_PUSH_ANY.finditer(line):
            rid = m.group(1) or m.group(2)
            if rid is None:
                bad.append(f"{path.name}:{i}: fund uden id — FIX[f.id] bliver tom")
            elif rid not in fixes:
                bad.append(f"{path.name}:{i}: id {rid} har ingen fix-tekst i FIX")
    return bad


def self_test() -> int:
    """Bevis at porten rødmER på et forkert tal, og er grøn på det rigtige."""
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "repo"
        shutil.copytree(ROOT, tmp, ignore=shutil.ignore_patterns(
            ".git", "dist", "node_modules", "__pycache__", ".wrangler"))
        lay = Layout(site=tmp / "site")

        base = check(lay)
        if base:
            fails.append(f"selftest: fersk checkout har allerede {len(base)} fejl:\n  "
                         + "\n  ".join(base[:5]))
            print("\n".join(fails))
            return 1

        real = len(free_rule_ids(lay.primary))

        def first_claim(path: Path, rx: re.Pattern[str]) -> str | None:
            """Det første løftet af den form i filen, læst live."""
            m = rx.search(path.read_text(encoding="utf-8"))
            return m.group(0) if m else None

        # Hver mutation skal flytte præcis ét løfte i en fil porten ejer. Tallene
        # læses live, så selftesten ikke går i stykker når regelsættet ændrer sig.
        cases = []
        guide = tmp / "site" / "guides" / "comparison.html"
        here = first_claim(guide, re.compile(r"\d+(?=\s+automated\s+rules)"))
        if here:
            cases.append(("guidespejl", guide, here, f"{real + 1} automated rules"))
        buy = tmp / "site" / "compliance-report.html"
        there = first_claim(buy, re.compile(r"\d+(?=\s+automated\s+checks)"))
        if there:
            cases.append(("købsside", buy, there, f"{real - 1} automated checks"))
        da = tmp / "site" / "da" / "compliance-report.html"
        total = first_claim(da, re.compile(r"\d+(?=\s+tjek\s+i\s+alt)"))
        if total:
            wrong = real + pro_count(lay) + 1
            cases.append(("dansk total", da, total, f"{wrong} tjek i alt"))
        # Den pluginside-port, opgave 85 tilføjede. Uden denne arm er den nye
        # PHP-måling ubevistet: en fejl i zip-udpakningen ville give 0 og alt
        # gå grønt, fordi ingen løfte på siden matcher et målt tal.
        wp = lay.plugin_page
        wp_claim = first_claim(wp, re.compile(r"\d+(?=\s+WCAG\s+[\d.]+\s+AA\s+rules)"))
        if wp_claim:
            php_real = len(php_rule_ids(lay.plugin_zip))
            cases.append(("pluginside", wp, wp_claim, f"{php_real + 1} WCAG 2.1 AA rules"))
        # Den femte arm: produkt→motor-kortet. Den skriver **webscannerens** tal
        # ind på en side der sælger desktop-appen. Hvis kortet ikke virkede, faldt
        # siden tilbage på `scan.html`, og 15 ville være grønt — så mutationen
        # ville *ikke* fange, at kortet var dødt. Den skal derfor skrive netop
        # det tal der er forkert for den motor siden sælger.
        dl = lay.site / "downloads.html"
        dl_claim = first_claim(dl, re.compile(r"\d+(?=\s+WCAG\s+[\d.]+\s+AA\s+rules)"))
        if dl_claim:
            cases.append(("motor-kort", dl, dl_claim,
                          f"{len(free_rule_ids(lay.primary))} WCAG 2.1 AA rules"))

        if len(cases) != 5:
            fails.append(f"selftest: fandt {len(cases)}/5 løfter at mutere")

        # Den sjette arm: `hero-note` på en rigtig CMS-guide. De 14 guides sagde
        # "16 checks" i den linje og "15" i undertitlen fire linjer under — så
        # mutationen skriver et *forskert* tal ind i heroen og lader undertitlen
        # være urørt. Gør porten den rød, er den i stand til at se en side der
        # modsiger sig selv, hvilket var hele fejlformen.
        hero_file = None
        for cand in sorted((tmp / "site" / "guides").glob("*.html")):
            if RE_HERO.search(cand.read_text(encoding="utf-8")):
                hero_file = cand
                break
        if hero_file is None:
            fails.append("selftest: ingen guide har en hero-note med et regeltal — "
                         "`RE_HERO` dømmer så ikke den linje den er skrevet for")
        else:
            hero_note = RE_HERO.search(hero_file.read_text(encoding="utf-8"))
            # Kun **tallet** muteres. Før denne rettelse erstattede armen hele
            # `m.group(0)` — altså også `class="hero-note">` — så den efterlod
            # `<span 16 automated rules …>` uden klassen. `RE_HERO` fandt så
            # intet, og armen blev grøn *fordi* `RE_CLAIM` greb tallet på den
            # ødelagte linje. Den testede altså ikke `RE_HERO` men sig selv.
            # Målt 30/9, da art 3 og overlap-udjævningen gjorde den forkerte
            # udgang til den eneste.
            wrong_hero = hero_note.group(0).replace(
                str(hero_note.group("n")), str(real + 1), 1)
            original = hero_file.read_text(encoding="utf-8")
            hero_file.write_text(original.replace(hero_note.group(0), wrong_hero, 1),
                                 encoding="utf-8")
            hero_errs = check(lay)
            hero_file.write_text(original, encoding="utf-8")
            if not hero_errs:
                fails.append("selftest: en hero-note med et forkert regeltal gav "
                             "ingen fejl")
            elif not any(hero_file.name in e for e in hero_errs):
                fails.append("selftest: hero-note-mutationen gav en fejl der ikke "
                             "nævner den side der blev muteret: "
                             + "; ".join(hero_errs[:3]))
            # Negativ kontrol: de tre danske sider siger "Kør alle 22 WCAG 2.1
            # AA-regler lokalt" i en fælles CTA-blok. Mutér den til 21 — så skal
            # *webkernens* rigtige tal stadig være grønt på de andre sider, så
            # fejlen kun kan komme fra den danske sides egen motor.
            da_dl = tmp / "site" / "da" / "blog" / "eaa-compliance-scanner-desktop-download.html"
            da_line = "Kør alle 22 WCAG 2.1 AA-regler"
            if da_line in da_dl.read_text(encoding="utf-8"):
                original = da_dl.read_text(encoding="utf-8")
                da_dl.write_text(original.replace(da_line, da_line.replace("22", "21")),
                                 encoding="utf-8")
                da_errs = check(lay)
                da_dl.write_text(original, encoding="utf-8")
                if not any("eaa-compliance-scanner-desktop-download" in e for e in da_errs):
                    fails.append("selftest: den danske sides '22 WCAG 2.1 AA-regler' "
                                 "dømmes ikke — `regler`-formen fanger ikke dansk")
            else:
                fails.append("selftest: den danske desktop-side har ikke længere "
                             "CTA-teksten med 22 regler — den danske arm er død")

        # Den anden negative kontrol, og den er den derfor er skrevet: samme
        # designsom `hero-note` med et tal der *ikke* er et regeltal. Hvis
        # `RE_HERO` dømte ethvert tal i en hero, ville denne blive rød — eller
        # grøn af en tilfældighed, fordi 15 også er webkernens tal.
        plat = (tmp / "site" / "guides" / "platforms.html")
        plat_original = plat.read_text(encoding="utf-8")
        plat.write_text(plat_original.replace("15 platforms", "17 platforms"), encoding="utf-8")
        plat_errs = check(lay)
        plat.write_text(plat_original, encoding="utf-8")
        if plat_errs:
            fails.append("selftest: '17 platforms' i en hero-note dømmes som et "
                         "regeltal — `RE_HERO` er bredere end sit formål: "
                         + "; ".join(plat_errs[:3]))

        # Den tredje fejlform fra denne iteration: et **nøgt** regelord i
        # engelsk. `regler` stod i mønstret hele tiden, `rules` gjorde ikke, så
        # seks publicerede løfter ("16 rules" i JSON-LD-FAQ, i en
        # `<meta name="description">` og i CLI-sidens brødtekst) lå uden for
        # portens synsfelt. Armen genskaber formen på en rigtig fil.
        bare_guide = None
        for cand in sorted((tmp / "site" / "guides").glob("*.html")):
            if RE_CLAIM.search(cand.read_text(encoding="utf-8")) and \
                    re.search(r"\b\d{2,3}\s+rules\b",
                              cand.read_text(encoding="utf-8")):
                bare_guide = cand
                break
        if bare_guide is None:
            fails.append("selftest: ingen guide har et nøgt 'N rules' — armen "
                         "gen skaber en form porten ikke længere ser")
        else:
            body = bare_guide.read_text(encoding="utf-8")
            hit = re.search(r"\b\d{2,3}\s+rules\b", body)
            wrong_bare = f"{real + 1} rules"
            bare_guide.write_text(
                body.replace(hit.group(0), wrong_bare, 1), encoding="utf-8")
            bare_errs = check(lay)
            bare_guide.write_text(body, encoding="utf-8")
            if not bare_errs:
                fails.append(f"selftest: nøgt {wrong_bare!r} på "
                             f"{bare_guide.name} gav ingen fejl")
            elif not any(bare_guide.name in e for e in bare_errs):
                fails.append(f"selftest: nøgt-regelord-mutationen på "
                             f"{bare_guide.name} gav en fejl der ikke nævner den "
                             f"muterede side: " + "; ".join(bare_errs[:3]))

        # Den fjerde arm, og den er den der adskiller *målt* fra *antaget*:
        # CLI-siden sælger `scanner/npm`, som kører 22 — ikke webkernens 15.
        # Før denne iteration lå siden ikke i `PRODUCT_ENGINE` overhovedet,
        # fordi dens løfte ikke blev *fundet*. Mutér dens rigtige 22 til
        # webkernens 15: uden kortet dør porten med "står ikke i PRODUCT_ENGINE",
        # og med et forkert kort ville 15 være grønt. Den skal altså være rød
        # **og** nævne netop den side.
        cli = tmp / "site" / "blog" / "accessibility-scanner-cli.html"
        cli_body = cli.read_text(encoding="utf-8")
        cli_hit = re.search(r"\b22\s+rules\b", cli_body)
        if cli_hit is None:
            fails.append("selftest: CLI-siden har ikke længere '22 rules' — "
                         "motor-kort-armen er død")
        else:
            cli.write_text(cli_body.replace(cli_hit.group(0), f"{real} rules", 1),
                           encoding="utf-8")
            try:
                cli_errs = check(lay)
            except SystemExit as exc:
                fails.append(f"selftest: CLI-siden med et nøgt regelord døde med "
                             f"SystemExit i stedet for en fejl — den mangler i "
                             f"produkt→motor-kortet: {exc}")
            else:
                if not cli_errs:
                    fails.append("selftest: CLI-siden løfter webkernens 15 for en "
                                 "motor der kører 22, og porten siger intet")
                elif not any(cli.name in e for e in cli_errs):
                    fails.append("selftest: CLI-armen gav en fejl der ikke nævner "
                                 f"{cli.name}: " + "; ".join(cli_errs[:3]))
            cli.write_text(cli_body, encoding="utf-8")

        # Den negative kontrol på **to-cifret-grænsen**. Uden den dør porten på
        # `blog/nis2-incident-report-checklist.html`, der skriver "2 rules" om
        # NIS2-forretninger. Den arm beviser derfor to ting på én fil: at et
        # ett-cifret nøgt regelord *ikke* er et løfte, og at filen derfor ikke
        # skal stå i produkt→motor-kortet.
        prose = lay.site / "nis2-artikel-om-forretninger.html"
        prose.write_text(
            "<p>Article 21 still boils down to 2 rules for most suppliers.</p>\n",
            encoding="utf-8")
        prose_errs = check(lay)
        prose.unlink()
        if prose_errs:
            fails.append("selftest: '2 rules' i brødtekst dømmes som et "
                         "regelløfte — to-cifret-grænsen virker ikke: "
                         + "; ".join(prose_errs[:3]))

        # De tre nye arter (opgave 9). Hver arm finder sit offer på en rigtig
        # fil, fordi en arm der skriver en syntetisk side ind i `site/` ville
        # være grøn af en grund der intet siger om porten — det er præcis den
        # fejl `check_tool_paid_path.py` havde med sit hårdkodede
        # `json-formatter.html`.
        def mutate(rel: str, old: str, new: str) -> list[str]:
            p = lay.site / rel
            body = p.read_text(encoding="utf-8")
            if old not in body:
                fails.append(f"selftest: {rel} har ikke længere {old!r} — "
                             "mutationen kan ikke genskabe den fejl den er skrevet for")
                return []
            p.write_text(body.replace(old, new, 1), encoding="utf-8")
            errs = check(lay)
            p.write_text(body, encoding="utf-8")
            return errs

        def must_red(rel: str, old: str, new: str, label: str) -> None:
            errs = mutate(rel, old, new)
            if not errs:
                fails.append(f"selftest: {label} ({new!r} i {rel}) gav ingen fejl")
            elif not any(rel.rsplit("/", 1)[-1] in e for e in errs):
                fails.append(f"selftest: {label} gav en fejl der ikke nævner den "
                             f"muterede side {rel}: " + "; ".join(errs[:3]))

        # (1) Pro-tallet. 27 sider skriver "18 server-side checks", og ingen
        # form dømte dem; `grep server-side` gav kun kommentarer. Offeret er
        # valgt som en af de synlige købssider, fordi det er dér et forkert
        # Pro-tal koster mest.
        must_red("compliance-report.html",
                 f"{pro_count(lay)} server-side checks",
                 f"{pro_count(lay) + 1} server-side checks",
                 "Pro-tallet i '18 server-side checks'")

        # (2) Et total uden "in all". Sætningen skal stadig have både fri- og
        # Pro-tallet, ellers er den ikke et total — derfor muteres kun tallet
        # foran "checks", ikke sætningen omkring.
        must_red("books/index.html", "runs 33 checks", "runs 34 checks",
                 "totaltallet i 'runs 33 checks'")

        # (3) Et løfte der ombrydes over to linjer. Før denne iteration læste
        # `collect()` linje for linje, så armen ville være grøn. Den skal både
        # findes *og* dømmes: tal og regelord står hver for sig, som de gør når
        # en formatter bryder en linje.
        must_red("books/index.html",
                 "the same 15 accessibility rules",
                 "the same 16\n  accessibility rules",
                 "et løfte der er ombrudt over to linjer")

        # (4) attributværdier. `content="… 22 WCAG 2.1 AA rules …"` er tre af
        # sidens løfter, og normaliseringen blanker hele taggen hvis den ikke
        # lader værdierne stå. Uden denne arm ville porten miste dem i stilhed.
        must_red("wordpress-plugin.html",
                 "against 22 WCAG 2.1 AA rules",
                 "against 21 WCAG 2.1 AA rules",
                 "et løfte i en meta-attribut")

        # Den negative kontrol på art 3, og den er den der adskiller målt fra
        # antaget: "25 Checks" i NIS2-artiklen er *artiklens* egne 25 punkter,
        # ikke vores motor. Uden denne arm ville en for brede art 3 være grøn
        # af en tilfældighed.
        for rel, old, new in (
            ("blog/nis2-checklist-pdf.html", "25 Checks", "26 Checks"),
            ("blog/free-website-compliance-checker.html",
             "9 Checks on Any Site", "10 Checks on Any Site"),
        ):
            errs = mutate(rel, old, new)
            if errs:
                fails.append(f"selftest: {new!r} i {rel} dømmes som et løfte om "
                             "vores motor — art 3 er bredere end sit formål: "
                             + "; ".join(errs[:3]))

        for name, path, old, new in cases:
            original = path.read_text(encoding="utf-8")
            if old not in original:
                fails.append(f"selftest: mutationen {name!r} fandt ikke {old!r}")
                continue
            path.write_text(original.replace(old, new, 1), encoding="utf-8")
            if not check(lay):
                fails.append(f"selftest: mutationen {name!r} ({new!r}) gav ingen fejl")
            path.write_text(original, encoding="utf-8")

        # Den syvende fejlform, og den derfra forløberne her. Før denne
        # iteration stod der fire publicerede sider med "16" om en motor der
        # kører 15, og `RE_CLAIM` fangede **én** af dem. De tre oversete var
        # ikke tilfældigt valgte former — de var de former `RE_CLAIM` ikke
        # skrev ned, så en arm der kun testede den fangne form ville have været
        # grøn på præcis den fejl der slap igennem. Derfor genskabes alle fire
        # på deres rigtige filer, og porten skal rødme hver især *og* nævne
        # den fil der blev muteret.
        for name, rel, published in (
            ("dansk automatiserede", "site/scan-da.html",
             "15 automatiserede WCAG 2.1 AA-regler"),
            ("engelsk ord imellem", "site/guides/platforms.html",
             "Check any site against 15 WCAG rules."),
            ("engelsk compliance-rules", "site/compliance-ai.html",
             "15 WCAG compliance rules"),
            # Den negative kontrol: den form porten *allerede* fangede. Uden
            # den er der intet bevis for at de tre nye arme ikke har gjort
            # mønstret så bredt at alt går rødt.
            ("dansk WCAG-regler", "site/da/compliance-ai.html",
             "mod 15 WCAG-regler"),
        ):
            target = tmp / rel
            body = target.read_text(encoding="utf-8")
            if published not in body:
                fails.append(f"selftest: {rel} indeholder ikke længere {published!r} "
                             f"— armen {name!r} genskaber en form der ikke findes")
                continue
            claim = RE_CLAIM.search(body)
            if claim is None:
                fails.append(f"selftest: {rel} har intet løfte i den form armen "
                             f"gen skaber — armen {name!r} dør stille")
                continue
            wrong = re.sub(r"\d+", str(real + 1), claim.group(0), count=1)
            target.write_text(body.replace(claim.group(0), wrong, 1), encoding="utf-8")
            errs = check(lay)
            target.write_text(body, encoding="utf-8")
            if not errs:
                fails.append(f"selftest: mutationen {name!r} på {rel} ({wrong!r}) "
                             f"gav ingen fejl")
            elif not any(Path(rel).name in e for e in errs):
                fails.append(f"selftest: mutationen {name!r} på {rel} gav en fejl "
                             f"der ikke nævner den muterede side: "
                             + "; ".join(errs[:3]))

        # Den anden fejlform: et fund igen uden id, som på `main` gav fire fund
        # uden fix-tekst. Den skal give en fejl, ikke gå ubemærket.
        scan = lay.site / "scan.html"
        original = scan.read_text(encoding="utf-8")
        for name, old, new in (
            ("fund uden id", "{id:'VIEWPORT',sev:", "{sev:"),
            ("fix-tekst væk", "VIEWPORT:'Fix: add <meta name=\"viewport\"",
             "VIEWPORT_UNUSED:'Fix: add <meta name=\"viewport\""),
        ):
            if old not in original:
                fails.append(f"selftest: mutationen {name!r} fandt ikke {old!r}")
                continue
            scan.write_text(original.replace(old, new, 1), encoding="utf-8")
            if not check(lay):
                fails.append(f"selftest: mutationen {name!r} gav ingen fejl")
            scan.write_text(original, encoding="utf-8")

        # Den sjette fejlform: en side med et løfte, der ikke står i
        # produkt→motor-kortet. Før opgave 86 faldt den tilbage på `scan.html`
        # i stilhed, og det er præcis derfor de 34 løfter i den lange form ikke
        # kunne dømmes. Kortet skal derfor være lukket: en ukendt side er en
        # fejl, ikke et gæt.
        stray = lay.site / "omtalt-men-ikke-i-kortet.html"
        stray.write_text(
            '<meta name="description" content="15 automated rules, free.">\n',
            encoding="utf-8")
        try:
            check(lay)
        except SystemExit as exc:
            if "PRODUCT_ENGINE" not in str(exc):
                fails.append(f"selftest: ukendt side gav en anden fejl end den "
                             f"forventede: {exc}")
        else:
            fails.append("selftest: en side med et løfte, som ikke står i "
                         "produkt→motor-kortet, gav ingen fejl — kortet lækker")
        stray.unlink()

        # Den ottende fejlform, målt 29/9: et tal foran et **sammensat** dansk
        # ord. `da/compliance-report.html` skrev "kører 11 tilgængelighedsregler"
        # i den ene linje, mens tre andre linjer på samme side sagde 15, og
        # porten dømte ingen af dem. Armen genskaber præcis den form på den
        # rigtige fil — en arm der kun testede den fangne form ville være grøn
        # på præcis den fejl der slap igennem. Den negative kontrol er den
        # linje lige under, som porten *allerede* dømte: uden den er der intet
        # bevis for at den nye gren ikke har gjort mønstret så bredt at alt
        # går rødt.
        comp = tmp / "site" / "da" / "compliance-report.html"
        comp_body = comp.read_text(encoding="utf-8")
        # Hele frasen og ikke kun tallet: `.replace("15", …, 1)` ville ramt det
        # første 15 i filen, som er et andet løfte, og armen ville så have
        # dømt noget andet end den form den er skrevet for.
        comp_hit = re.search(r"\d+\s+tilgængelighedsregler", comp_body)
        if comp_hit is None:
            fails.append("selftest: den danske købsside har ikke længere 'N "
                         "tilgængelighedsregler' — armen genskaber en form der "
                         "ikke findes")
        else:
            wrong_comp = f"{real + 1} tilgængelighedsregler"
            comp.write_text(
                comp_body.replace(comp_hit.group(0), wrong_comp, 1),
                encoding="utf-8")
            comp_errs = check(lay)
            comp.write_text(comp_body, encoding="utf-8")
            if not comp_errs:
                fails.append(f"selftest: {wrong_comp!r} på "
                             f"{comp.name} gav ingen fejl")
            elif not any(comp.name in e for e in comp_errs):
                fails.append(f"selftest: sammensat-ords-mutationen på "
                             f"{comp.name} gav en fejl der ikke nævner den "
                             f"muterede side: " + "; ".join(comp_errs[:3]))

        # Negativ kontrol på den nye gren: et tal foran `automatiske regler` er
        # den form porten dømte længe før denne arm, så den skal *stadig* være
        # grøn når den rigtige 15 står der. Uden denne linje beviser armen over
        # for sig selv, fordi den ville være rød af den mutation den selv lavede.
        if check(lay):
            fails.append("selftest: den danske købsside med det rigtige tal "
                         "15 tilgængelighedsregler giver stadig fejl")

    for f in fails:
        print(f)
    if fails:
        return 1
    print(f"selftest OK: porten rødmer på et forkert tal og er grøn på det "
          f"rigtige ({real} regler)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true", help="vis de målte tal")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    lay = Layout(site=ROOT / "site")
    if args.list:
        print(show_list(lay))
        return 0

    errs = check(lay)
    if errs:
        print(f"check_rule_claims: {len(errs)} fejl — et løfte taler ikke om koden\n")
        for e in errs:
            print("  " + e)
        return 1
    n = len(collect(lay))
    free_n = len(free_rule_ids(lay.primary))
    pro_n = len(pro_rule_ids(lay.worker))
    print(f"check_rule_claims OK: {n} regel-løfter, alle matcher koden "
          f"({free_n} frie + {pro_n} Pro = {free_n + pro_n})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
