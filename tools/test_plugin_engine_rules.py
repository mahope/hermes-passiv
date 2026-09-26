#!/usr/bin/env python3
"""Kør pluginens egen PHP-motor og kræv, at den fyrer alle 22 regler.

Baggrunden er opgave 85. Det publicerede zip var en ældre build af
`scanner/wp-plugin/`, og siden talte 16 regler — rigtigt for den fil kunden
hentede, men seks bag den kode vi vedligeholder. Intet i porten kunne se det:
`check_rule_claims.py` læste **den publicerede zip**, så den målte motoren
korrekt og fandt 16, og 16 var altså ikke en fejl. Den var en *fuldstændig*
måling af det forkerte produkt.

Derfor må denne test ikke læse kode. Den indlæser motoren fra det publicerede
arkiv, kalder `scan_html()` på `tools/fixtures/eaa_engine_all_rules.html` og
kræver, at alle 22 regler fyrer. Tre ting skal holde samtidig:

1. **Arkivet er i sync med kilden.** Ellers måler vi en motor, der ikke er den
   vi udgiver, og portens 22 siger om kildens motor.
2. **Alle 22 fyrer.** Ikke "mindst 22" og ikke "22 forskellige id'er i
   koden" — 22 *fund* i et *dokument*. En regel, der er kodet men aldrig kan
   fyre, er en regel kunden ikke har.
3. **Den dynamiske mængde er den statiske.** De id'er der fyrer, skal være
   præcis de id'er `check_rule_claims.py` tæller. Uden dette krydscheck kan de
   to blive enige om et forkert tal, og en port der kun er en port.

Der står desuden to kommentar-prøver, fordi de er den fejl de 22 ikke kan se.
Alle fire byggere af denne motor er samme kode i fire sprog, men
`engine_disagreements` sammenligner kun **mængden af regel-id'er** — ikke hvad
de gør med det samme dokument. En motor kan derfor have præcis de 22 id'er og
svare noget helt andet end de tre andre, og ingen port så det. Det skete:
PHP-motoren læste tags inde i HTML-kommentarer, så en WordPress-kunde med en
udkommenteret `<marquee>` fik en blinkende-advarsel på en side uden blink, og en
side uden `<title>` blev meldt accessible. De tre andre motorer gjorde begge dele
rigtigt. Regelsæt var ens, svarene var ikke.

Derfor skal de to fixtures køres gennem **hver** motor og give **det samme**
svar. Ens regelsæt er ikke nok; det er det samme svar der er løftet.

Uden `php` springes den kørsel over — med en synlig besked, ikke med en stille
grøn linje. Resten af testen (1 og 3) kræver ikke PHP og kører alligevel, for
så en maskine uden PHP stadig fanger et ude af sync arkiv. Motor-armene i
kommentar-prøverne hopper tilsvarende over, hvis `node` mangler.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from check_rule_claims import (  # noqa: E402
    PLUGIN_ENGINE_IN_ZIP,
    py_engine_ids,
)

ZIP_PATH = REPO / "site" / "eaa-compliance-scanner.zip"
SOURCE_DIR = REPO / "scanner" / "wp-plugin" / "eaa-compliance-scanner"
PROBE = REPO / "tools" / "plugin_engine_probe.php"
FIXTURE = REPO / "tools" / "fixtures" / "eaa_engine_all_rules.html"

EXPECTED = 22

# To dokumenter der dømmer kommentarer, i hver sin retning. Begge er helt
# almindeligt HTML — de kommentarer de indeholder er testens data, og derfor
# står der ingen forklaring i filerne. Den ligger her.
COMMENT_FIXTURES = (
    # En side der er helt i orden, med et udkommenteret blok af gammelt markup.
    # Svar: ingen fund. En motor der læser kommentarer finder her IMG_ALT,
    # FORM_LABEL, LINK_TEXT, INPUT_TYPE_IMAGE_ALT, FIXED_PX_FONTS, IFRAME_TITLE,
    # TABLE_HEADER og to MARQUEE_BLINK — otte fejl, der alle er pure opsummering
    # af kode ingen har slettet endnu.
    ("comment_no_false_positive", frozenset(), 0),
    # En side der virkelig mangler <title> og <h1>, og hvor begge nævnes i en
    # kommentar. Svar: DOC_TITLE og HEADING_H1. Det er den anden retning, og den
    # er den farligere: en kompliance-rapport der tier om et WCAG-brud.
    ("comment_still_reports", frozenset({"DOC_TITLE", "HEADING_H1"}), 2),
)

# Hver motor køres for sig, så de kan sammenlignes. `zip` er den kunden
# installerer; de to andre er samme motor i de sprog den også findes i.


def fail(msg: str) -> None:
    print(f"FEJL: {msg}")
    raise SystemExit(1)


def check_zip_in_sync() -> list[str]:
    """(1) Det publicerede arkiv skal være den kode vi vedligeholder."""
    r = subprocess.run([sys.executable, "tools/build_plugin_zip.py", "--check"],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        fail(r.stdout.strip() or r.stderr.strip())

    with zipfile.ZipFile(ZIP_PATH) as zf:
        names = sorted(n for n in zf.namelist() if not n.endswith("/"))
    return names


def check_claims_say(expected: int) -> None:
    """Pluginens egne dokumenter skal nævne det samme tal som porten.

    `engine.php:7`, `README.txt:3` og pluginens WordPress-header sagde hver
    deres egen ting (21, 15, 15), og alle tre lå i det arkiv kunden hentede.
    De er ikke kosmetik: headeren er den tekst WordPress viser i
    plugin-katalogen, og `(15 rules)` stod i den skærm kunden så.
    """
    engine = (SOURCE_DIR / "engine.php").read_text(encoding="utf-8")
    readme = (SOURCE_DIR / "README.txt").read_text(encoding="utf-8")
    main = (SOURCE_DIR / "eaa-compliance-scanner.php").read_text(encoding="utf-8")

    # Ét tal i hver kilde, kunne være et hvilket som helst andet sted i filen.
    docblock = re.search(r"Act: (\d+) rules", engine)
    if not docblock:
        fail("engine.php's docblock nævner ikke længere et regeltal — "
             "fjern den, eller skriv hvorfor motoren ikke har et fast antal")
    if int(docblock.group(1)) != expected:
        fail(f"engine.php's docblock siger {docblock.group(1)} regler, "
             f"motoren kører {expected}")

    for name, src, pattern in (
        ("README.txt", readme, r"WCAG 2\.1 AA subset, (\d+) rules"),
        ("eaa-compliance-scanner.php", main, r"WCAG 2\.1 AA subset, (\d+) rules"),
        ("eaa-compliance-scanner.php (skærmen)", main,
         r"\((\d+) rules\)\. Runs entirely"),
    ):
        m = re.search(pattern, src)
        if not m:
            fail(f"{name} nævner ikke længere et regeltal")
        if int(m.group(1)) != expected:
            fail(f"{name} siger {m.group(1)} regler, motoren kører {expected}")

    ver = re.search(r"const EAA_SCANNER_VERSION = '([^']+)'", main)
    header = re.search(r"\* Version:\s*(\S+)", main)
    if not ver or not header:
        fail("plugin-headeren mangler Version eller EAA_SCANNER_VERSION")
    if ver.group(1) != header.group(1):
        fail(f"WordPress-headeren siger version {header.group(1)}, men "
             f"konstanten er {ver.group(1)} — de to er dem kunden ser")


def run_engine(fixture: Path = FIXTURE) -> list[str] | None:
    """(2) Kør motoren fra det publicerede arkiv. `None` hvis PHP mangler."""
    php = shutil.which("php")
    if php is None:
        print(" SPRUNGET OVER: `php` findes ikke i PATH, så motoren blev ikke "
              "kørt. Resten af testen kørte. Gaten måler fortsat de 22 fra "
              "koden, men ingen her bekræfter dem ved en kørsel.")
        return None

    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(ZIP_PATH) as zf:
            zf.extract(PLUGIN_ENGINE_IN_ZIP, tmp)
        engine = Path(tmp) / PLUGIN_ENGINE_IN_ZIP
        r = subprocess.run([php, str(PROBE), str(engine), str(fixture)],
                           cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"motoren kunne ikke køre: {r.stderr.strip() or r.stdout.strip()}")
    try:
        return json.loads(r.stdout.strip())["rule_ids"]
    except (ValueError, KeyError) as exc:
        fail(f"motorens svar var ikke JSON med rule_ids ({exc}): {r.stdout!r}")


def run_py_engine(fixture: Path) -> list[str]:
    """Samme motor på pip-siden. `html.parser` giver kommentar-skipping gratis."""
    code = (
        "import sys; sys.path.insert(0, 'scanner/packaging');"
        "from eaa_scanner.core import scan_html;"
        f"r = scan_html(open({str(fixture)!r}).read());"
        "assert r.get('ok') is not False, r.get('error');"
        "print(','.join(f['rule_id'] for f in r['findings']))"
    )
    r = subprocess.run([sys.executable, "-c", code], cwd=REPO,
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"pip-motoren kunne ikke køre: {r.stderr.strip() or r.stdout.strip()}")
    return [x for x in r.stdout.strip().split(",") if x]


def run_js_engine(fixture: Path) -> list[str]:
    """Samme motor i desktop-appens JavaScript. Den tokenizerer også kommentarer."""
    code = (
        "const {scanHtml} = require('./desktop/scanner-core.js');"
        "const r = scanHtml(require('fs').readFileSync(process.argv[1], 'utf8'));"
        "console.log(r.findings.map(f => f.rule_id).join(','));"
    )
    r = subprocess.run(["node", "-e", code, str(fixture)], cwd=REPO,
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"desktop-motoren kunne ikke køre: {r.stderr.strip() or r.stdout.strip()}")
    return [x for x in r.stdout.strip().split(",") if x]


def check_comments() -> None:
    """Kommentarer er ikke markup — i nogen af de fire motorer.

    To krav, fordi de er forskellige fejl:

    1. **Alle motorer giver det forventede svar.** Fixture'en med den
       komplette side skal give *nul* fund, og den med den manglende titel
       skal give DOC_TITLE + HEADING_H1.
    2. **Alle motorer giver det samme svar.** Det er den anden, der lukker
       fejlformen: `engine_disagreements` tæller regel-id'er, så fire motorer
       med ens id'er og forskellige svar lå som enige.

    En motor der hopper over, tæller ikke som en motor der er med — den skrives
    ud i loggen, så en grøn linje aldrig er en grøn linje fordi halvdelen af
    målingen ikke kørte.
    """
    if shutil.which("php") is None:
        print("  zip-motoren springes over: `php` mangler")
        engines = [("py", "pip", run_py_engine), ("js", "desktop", run_js_engine)]
    else:
        engines = [("zip", "det publicerede zip",
                    lambda f: run_engine(f)),
                   ("py", "pip", run_py_engine),
                   ("js", "desktop", run_js_engine)]

    for name, expect_ids, expect_n in COMMENT_FIXTURES:
        fixture = REPO / "tools" / "fixtures" / f"{name}.html"
        if not fixture.is_file():
            fail(f"{fixture} mangler — kommentar-prøverne skal have et dokument")

        answers: dict[str, frozenset[str]] = {}
        for key, label, runner in engines:
            got = frozenset(runner(fixture))
            answers[key] = got
            if got != expect_ids:
                extra = sorted(got - expect_ids)
                missing = sorted(expect_ids - got)
                fail(f"{label} svarer {sorted(got) or 'intet'} på {name}.html, "
                     f"men svaret er {sorted(expect_ids)}"
                     + (f". Den fandt {', '.join(extra)} som ikke er der." if extra else "")
                     + (f". Den glemte {', '.join(missing)}." if missing else ""))

        if len(answers) > 1:
            ref_key = engines[0][0]
            for key, _, _ in engines[1:]:
                if answers[key] != answers[ref_key]:
                    fail(f"motorerne er uenige om {name}.html: "
                         f"{engines[0][1]} siger {sorted(answers[ref_key]) or 'intet'}, "
                         f"men {dict((k, l) for k, l, _ in engines)[key]} siger "
                         f"{sorted(answers[key]) or 'intet'}. Samme motor, to svar — "
                         f"et regelsæt er ikke nok, kunden ser svaret.")

    print(f"  kommentarer: {len(engines)} motorer er enige om {len(COMMENT_FIXTURES)} "
          f"dokumenter (0 fund på den komplette side, DOC_TITLE + HEADING_H1 "
          f"på den manglende)")


def main() -> int:
    if not ZIP_PATH.is_file():
        fail(f"{ZIP_PATH} mangler")

    names = check_zip_in_sync()
    print(f"  arkiv i sync med kilden: {', '.join(n.split('/')[-1] for n in names)}")

    claimed = py_engine_ids(SOURCE_DIR / "engine.php")
    if len(claimed) != EXPECTED:
        fail(f"kilden har {len(claimed)} regel-id'er, porten forventer {EXPECTED}")
    check_claims_say(EXPECTED)

    fired = run_engine()
    if fired is None:
        print(f"test_plugin_engine_rules: OK (delvis — ingen PHP)")
        return 0

    if len(fired) != EXPECTED:
        missing = sorted(set(claimed) - set(fired))
        fail(f"motoren fyrer {len(fired)} regler, porten hævter {EXPECTED}. "
             + (f"Mangler i kørslen: {', '.join(missing)}." if missing
                else "Der fyrer regler porten ikke kender."))

    # (3) Den dynamiske mængde skal være præcis den statiske. Uden dette kan de
    # to være enige om et forkert tal, og porten er da ingen prøve.
    if set(fired) != set(claimed):
        only_run = sorted(set(fired) - set(claimed))
        only_code = sorted(set(claimed) - set(fired))
        fail("motoren og den statiske tælling er uenige: "
             + (f"kun i kørslen {', '.join(only_run)}; " if only_run else "")
             + (f"kun i koden {', '.join(only_code)}" if only_code else ""))

    check_comments()

    print(f"test_plugin_engine_rules OK: {len(fired)}/{EXPECTED} regler fyrer "
          f"på den publicerede motor, og de er præcis de {EXPECTED} porten tæller")
    return 0


if __name__ == "__main__":
    sys.exit(main())
