#!/usr/bin/env python3
"""Dømmer hvert beløb, der står ved siden af en konkurrent, mod én kilde.

Baggrund (30/9): `site/blog/desktop-website-monitor-cli.html` skrev «$7-12 per
month» for UptimeRobot, «$12» for Pingdom og «$10» for Better Stack, og
hovedlinjen «Kill Your $144/year SaaS Uptime Bill» stod på 16 sider. Slået op
30. september 2026 siger UptimeRobot €10/måned (€108/år), Better Stack sælger
oppetid pr. *responder-plads* til $34/måned ($408/år), og Pingdom har ingen
offentlig listepris — siden er en lommeberegner. Både brødtekst, `<title>`,
`og:description` og JSON-LD løj altså om priser, i en artikel der sælger
$19-produktet.

Derfor ligger alle tal nu i `tools/competitor_prices.json`, og denne port dømmer
kopien mod den fil:

* en konkurrent **uden** `plans` må ikke have et beløb ved siden af sig;
* et beløb ved siden af en konkurrent skal være ét af tallene i kilden
  (pr. måned, pr. måned ved årlig betaling, pr. år, eller 3 × pr. år);
* et beløb uden en konkument før sig i samme blok springes over — det er
  typisk vores egen pris.

Beløbet tilskrives den **nærmest foregående** konkurrent i blokken, så en
tabelrække med ét navn og ét beløb dømmes, og en sætning med to navn og to
beløb også dømmes. Blokke er `</tr>`, `</li>`, `</p>`, `</div>`, `<br>` og
`", "` — den sidste deler JSON-LD's felter, så en påstand dér ikke slipper ud.

**Alders-tjekket er en advarsel, ikke en dom.** En gammel `checked`-dato må
aldrig gøre gaten rød — så låste den alle fremtidige udgivelser, indtil en
menneske løb prisen op igen. Det er præcis det, der skete med `$7-12` her.

Brug: `python3 tools/check_competitor_prices.py [--json] [--self-test]`
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tools" / "competitor_prices.json"
SITE = ROOT / "site"

# Beløb: $, €, kr. Talgrupper med . eller som tusindtalsseparator.
AMOUNT = re.compile(r"(?:US\$|\$|€|&euro;|DKK\s|kr\.?\s*)\s?(\d[\d.,]*)", re.I)
# Ordgrænser, så «Better Stack» ikke matcher «Better Uptime».
# `</td>` er bevidst IKKE en blokgrænse: en tabelrække skal blive ved som én
# blok, ellers står navnet i én blok og beløbet i den næste og intet dømmes.
BLOCK_SPLIT = re.compile(r"</tr>|</li>|</p>|</div>|<br\s*/?>|</h1>|</title>|\", \"|\"\s*,")

# Vore egne produkter. Et beløb, der stås efter vores eget navn, er vores pris,
# ikke konkurrentens — ellers dømmer porten sin egen $19.
OUR_NAMES = re.compile(
    r"deskuptime|clean copy|cleancopy|eucomply|page profile|pageprofile|"
    r"transmute|bugbottle|mahope", re.I)


def load_source() -> dict:
    return json.loads(SOURCE.read_text())


def amount_value(raw: str) -> float:
    """'1,476' og '1.476' er begge 1476. '108' er 108."""
    digits = re.sub(r"[.,]", "", raw)
    try:
        return float(digits)
    except ValueError:
        return float("nan")


def amount_prefixed(raw: str, text: str, start: int) -> str:
    """Finde valutategnet umiddelbart foran tallet, så € og $ kan skelnes."""
    return text[max(0, start - 8):start]


def plans_allowed(entry: dict) -> dict[float, str]:
    """Alle beløb der må stå ved siden af konkurrenten, som tal -> forklaring."""
    out: dict[float, str] = {}
    for plan, data in (entry.get("plans") or {}).items():
        pairs = [("per_month", 1), ("per_month_annual", 1), ("per_year", 1)]
        for field, _ in pairs:
            val = data.get(field)
            if val:
                out[amount_value(val.lstrip("$€"))] = f"{plan} {field}"
        year = data.get("per_year")
        if year:
            v = amount_value(year.lstrip("$€"))
            out[v * 3] = f"{plan} per_year x 3"
    return out


def blocks(text: str):
    for part in BLOCK_SPLIT.split(text):
        if part.strip():
            yield part


def find_amounts(block: str) -> list[tuple[float, int]]:
    return [(amount_value(m.group(1)), m.start()) for m in AMOUNT.finditer(block)]


def check_tree(site: Path = SITE, source: dict | None = None) -> list[dict]:
    source = source or load_source()
    competitors = source.get("competitors", {})
    names = sorted(competitors, key=len, reverse=True)
    findings: list[dict] = []

    for page in sorted(site.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        rel = page.as_posix()
        if site is SITE:
            rel = page.relative_to(ROOT).as_posix()
        for index, block in enumerate(blocks(text)):
            lowered = block.lower()
            positions = []
            for name in names:
                for m in re.finditer(re.escape(name), block, re.I):
                    positions.append((m.start(), name))
            if not positions:
                continue
            positions.sort()
            for value, at in find_amounts(block):
                if value != value:  # NaN
                    continue
                before = [p for p in positions if p[0] < at]
                if not before:
                    continue  # egen pris, ingen konkurrent før sig
                start, name = before[-1]
                if OUR_NAMES.search(block[start + len(name):at]):
                    continue  # vores egen pris står imellem navnet og beløbet
                entry = competitors[name]
                allowed = plans_allowed(entry)
                if not allowed:
                    findings.append({
                        "file": rel, "block": index, "kind": "kan ikke efterprøves",
                        "detail": (f"{name} har ingen offentlig listepris i "
                                   f"competitor_prices.json, men der står "
                                   f"{value:g} ved siden af navnet. Skriv navnet "
                                   f"uden et tal, eller opdater kilden."),
                    })
                elif value not in allowed:
                    facts = ", ".join(sorted({f"{v:g} ({w})" for v, w in allowed.items()}))
                    findings.append({
                        "file": rel, "block": index, "kind": "forkert pris",
                        "detail": (f"{value:g} står ved siden af {name}, men kilden "
                                   f"siger: {facts}."),
                    })
    return findings


def warnings(source: dict) -> list[str]:
    checked = source.get("checked", "")
    try:
        age = (date.today() - date.fromisoformat(checked)).days
    except ValueError:
        return [f"\"checked\" er ikke en ISO-dato: {checked!r}"]
    if age > 120:
        return [f"ADVARSEL: konkurrentpriserne er {age} dage gamle (checked {checked}). "
                f"Slå dem op igen og sæt `checked` — ellers rådner artiklen igen."]
    return []


MUTATIONER = [
    # (navn, fil der ændres, gammel tekst, ny tekst)
    ("tabelpris byttet om",
     "site/blog/desktop-website-monitor-cli.html",
     "&euro;108 <small style=\"color:#666\">&euro;9/month",
     "$84 <small style=\"color:#666\">$9/month"),
    ("Pingdom får et tal",
     "site/blog/desktop-website-monitor-cli.html",
     "<td style=\"padding:10px;border:1px solid #ddd\">Pingdom</td>",
     "<td style=\"padding:10px;border:1px solid #ddd\">Pingdom Standard $144</td>"),
    ("månedspris ændret sig",
     "site/blog/desktop-website-monitor-cli.html",
     "Solo is &euro;10/month", "Solo is &euro;11/month"),
    ("vores egen pris dømt som konkurrentens",
     "site/blog/index.html",
     "a single Better Stack responder seat is $348. DeskUptime is $19 once.",
     "a single Better Stack responder seat is $19."),
    ("aarstal forvridt",
     "site/blog/desktop-website-monitor-cli.html",
     "&euro;492 <small style=\"color:#666\">&euro;35/month",
     "&euro;900 <small style=\"color:#666\">&euro;35/month"),
    # Review-fund 1/10: $408 var månedlig betaling sat ind som et årstal, fordi
    # den gamle kilde skrev "34 x 12 = 408". Mutationen lægger den fejl tilbage i
    # "1 year"-kolonnen, og porten skal sige nej — det er den dom, der manglede.
    ("maanedlig aarstal i aarskolonnen",
     "site/blog/desktop-website-monitor-cli.html",
     "$348 <small style=\"color:#666\">$29/month",
     "$408 <small style=\"color:#666\">$34/month"),
]


def self_test() -> int:
    import shutil
    import tempfile

    checks = 0
    failures = 0

    def ok(cond: bool, label: str) -> None:
        nonlocal checks, failures
        checks += 1
        if not cond:
            failures += 1
            print(f"  FEJL  {label}")
        else:
            print(f"  ok    {label}")

    baseline = check_tree()
    ok(not baseline, f"kilden er grøn ({len(baseline)} fund)")

    for name, rel, old, new in MUTATIONER:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "site"
            shutil.copytree(SITE, work)
            target = work / Path(rel).relative_to("site")
            body = target.read_text(encoding="utf-8")
            if old not in body:
                ok(False, f"mutation {name!r}: mønsteret findes ikke mere")
                continue
            target.write_text(body.replace(old, new, 1), encoding="utf-8")
            found = check_tree(site=work)
        ok(bool(found), f"mutation {name!r} fanges ({len(found)} fund)")

    # Kilden skal kunne dømme sig selv: en ny konkurrent uden tal er et fund.
    source = load_source()
    ok(plans_allowed(source["competitors"]["Pingdom"]) == {},
       "Pingdom har ingen planer at dømme mod")
    solo = plans_allowed(source["competitors"]["UptimeRobot"])
    ok(108.0 in solo and 324.0 in solo and 492.0 in solo and 1476.0 in solo,
       f"Solo/Team-tallene er med ({len(solo)} tilladte beløb)")
    ok(84.0 not in solo and 144.0 not in solo,
       "de gamle $84/$144-tal er ikke tilladt")

    # Review-fund 1/10: €108 var årlig betaling (€9 × 12) og $408 månedlig
    # betaling ($34 × 12) — begge sande, men de beskriver ikke det samme, så
    # kolonnen overdriv konkurrenten. Kilden må derfor kun give ÉT årstal pr.
    # plan, på det grundlag artiklen sammenligner på, og det andet grundlags
    # årstal skal være umuligt at genindsætte uden en bevidst kildeændring.
    bs = plans_allowed(source["competitors"]["Better Stack"])
    ok(348.0 in bs and 29.0 in bs and 34.0 in bs,
       "Better Stack har årlig, årlig-månedspris og månedspris i kilden")
    ok(408.0 not in bs,
       "408 er månedlig betaling, ikke årlig — må ikke kunne stå som \"et år\"")

    print(f"selvtest: {checks - failures}/{checks} kontroller")
    return 0 if failures == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    source = load_source()
    findings = check_tree(source=source)
    notes = warnings(source)
    if args.json:
        print(json.dumps({"findings": findings, "warnings": notes}, ensure_ascii=False, indent=2))
    else:
        for note in notes:
            print(note)
        for f in findings:
            print(f"{f['file']} [blok {f['block']}] {f['kind']}: {f['detail']}")
        pages = len(list(SITE.rglob('*.html')))
        print(f"{pages} sider, {len(findings)} fund, "
              f"{len(source.get('competitors', {}))} konkurrenter "
              f"(kilde tjekket {source.get('checked')})")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
