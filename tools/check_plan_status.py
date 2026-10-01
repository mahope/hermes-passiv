#!/usr/bin/env python3
"""Dom at planen er en arbejdskø: STATUS må ikke blive en dagbog.

Opgave 42 (1/10) bad om at koge STATUS fra 66 linjer ned til de 25 kontrakten
tillader. Den skrev sit eget acceptkriterium som et awk-kommando:

    awk '/^## STATUS/{f=1;next}/^## /{f=0}f' IMPLEMENTATION_PLAN.md

Det kommando gav **0 linjer** — for enhver plan. Overskriften hedder `# STATUS`,
ikke `## STATUS`, så mønsteret matcher aldrig, `f` bliver aldrig 1, og awk
skriver nul linjer ud. Kriteriet var altså grønt, før rettelsen var lavet, og
grønt efter. Det er præcis den fejlform de seneste fund har lukket fire gange:
en regel skrevet ned uden en dom der kan fejle.

Derfor ligger dommen her, og den har **fire** domme hvoraf den første er
«afsnittet skal findes» — for uden den er de tre ande lige så døde som awk'en
var, bare i Python.

1. **STATUS-afsnittet findes.** Overskriften læses på *alle* niveauer, så
   både `# STATUS` og `## STATUS` tæller. Det afsnit, der følger, er kroppen
   indtil næste overskrift på samme eller højere niveau. Findes intet afsnit,
   er det rødt med beskeden «afsnit ikke fundet» — aldrig grønt.
2. **Højst 25 linjer** i kroppen. Alle linjer tælles, også tomme, så «25 linjer
   plus en halv side af luft» ikke kan være det samme som 25.
3. **Hele planen under 40 KB**, som kontrakten kræver. 40 KB *er* 40000 tegn
   på tegn, ikke på bytes — en plan med 30.000 danske tegn vejer mere end
   40.000 bytes, så bytes ville være en strammere regel end den der står i
   kontrakten, og det ville være min egen invention.
4. **Hvert punkt i STATUS har et tal.** Et afsnit uden tal er en måling uden
   måling: det er den måde denne plan har vokset — otte afsnit med rigtige
   fejlformer og ingen tal, der viste hvor de var rettet. Tal er ikke hele
   sandheden, men *manglende* tal er næsten altid en påstand.

Dommene er ikke «pænhed», de er holdbare: en framtidig STATUS må kun vokse,
hvis den koger noget andet væk, og det er præcis aftalen med Mads.

    python3 tools/check_plan_status.py            # dom planen
    python3 tools/check_plan_status.py --self-test # 11 kontroller
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "IMPLEMENTATION_PLAN.md"

MAX_STATUS_LINES = 25
MAX_PLAN_CHARS = 40_000
# Ét tal pr. punkt. `0` og `25` er tal; et årstal i en filsti er også et tal,
# og det er ikke pointen — pointen er at porten kan se, at *noget* er målt.
TAL_RE = re.compile(r"\d")
HEADING_RE = re.compile(r"^(#{1,6})\s+(\S.*?)\s*$")
BULLET_RE = re.compile(r"^\s*[-*]\s+\S")


# Afsnittet slutter ved næste overskrift på niveau 1 eller 2. Det er planens
# egen konvention: `# STATUS`, `## Verificér deploy`, `## Åbne opgaver` er
# *sidestøende*, ikke en del af STATUS. En `###` underaf ligger stadig inde i
# afsnittet, så en indskudt underrubrik ikke kan skjule den tekst den dækker.
AFSLUT_NIVEAUER = (1, 2)


def _krop(linjer: list[str]) -> list[str]:
    """Kroppen uden de tomme linjer der adskiller den fra overskrifterne.

    Kun *kantens* tomme linjer fjernes. En tom linje mellem to punkter tæller,
    for den er en del af det afsnit, porten skal holde sig under 25 linjer — de
    to linjer der skiller `# STATUS` fra `## Åbne opgaver` er derimod hverken
    indhold i det ene eller det andet.
    """
    krop = list(linjer)
    while krop and not krop[0].strip():
        krop.pop(0)
    while krop and not krop[-1].strip():
        krop.pop()
    return krop


def find_status(tekst: str) -> tuple[int, int, list[str]] | None:
    """`(linje, niveau, krop)` for det første `STATUS`-afsnit, ellers None."""
    linjer = tekst.splitlines()
    start = niveau = None
    for i, linje in enumerate(linjer):
        m = HEADING_RE.match(linje)
        if not m:
            continue
        if start is None:
            if m.group(2).strip().casefold() == "status":
                start, niveau = i, len(m.group(1))
            continue
        if len(m.group(1)) in AFSLUT_NIVEAUER:
            return start, niveau, _krop(linjer[start + 1:i])
    if start is None:
        return None
    return start, niveau, _krop(linjer[start + 1:])


def dom(tekst: str) -> list[str]:
    fund: list[str] = []
    fundtagt = find_status(tekst)
    if fundtagt is None:
        # Dom 1. Uden denne linje ville en plan uden STATUS være grøn, fordi
        # ingen af de tre andre domme har noget at dømme — awk-versionens fejl.
        fund.append("STATUS: afsnit ikke fundet — planen skal have en "
                    "`# STATUS`-overskrift, ellers dømmer de tre andre regler "
                    "intet (overskriften læses på alle niveauer)")
        return fund
    _, _, krop = fundtagt
    # Dom 2. Alle linjer, også tomme.
    if len(krop) > MAX_STATUS_LINES:
        fund.append(f"STATUS: {len(krop)} linjer, højst {MAX_STATUS_LINES} "
                    f"tilladt ({len(krop) - MAX_STATUS_LINES} for mange)")
    # Dom 3. Tegn, ikke bytes — se docstringen.
    if len(tekst) > MAX_PLAN_CHARS:
        fund.append(f"PLAN: {len(tekst)} tegn, højst {MAX_PLAN_CHARS} "
                    f"tilladt ({len(tekst) - MAX_PLAN_CHARS} for mange)")
    # Dom 4. Domt på hele punktet, ikke på dets første linje: et tal må stå
    # hvor det læses bedst, og «se ❓ nedenfor: 2 secrets» på en fortsættelses
    # linje er ikke dårligere end et tal presset op på linjen med punktet. Et
    # punkt uden *noget* tal er en måling uden måling.
    punkt: list[str] = []

    def dom_punkt(linjer: list[str]) -> None:
        if linjer and not any(TAL_RE.search(p) for p in linjer):
            fund.append(f"STATUS: punkt uden tal — «{linjer[0].strip()[:70]}»")

    for linje in krop:
        if BULLET_RE.match(linje):
            dom_punkt(punkt)
            punkt = [linje]
        elif punkt and linje.strip():
            punkt.append(linje)
    dom_punkt(punkt)
    return fund


def _plan(status_krop: str, *, overskrift: str = "# STATUS",
          efter: str = "## Åbne opgaver\n") -> str:
    """En syntetisk plan hvor STATUS-kroppen er *præcis* `status_krop`.

    Kroppen skal slutte med et linjeskift; så er kroppen i den byggede plan
    lige så lang som den er lavet til, uden at testen skal regne efter. Det
    var den fejl i den første version af denne fil: porten sagde 31 linjer,
    testen mente 26, og porten havde ret.
    """
    return f"{overskrift}\n\n{status_krop}{efter}\n- 1. noget\n"


def self_test() -> int:
    fejl: list[str] = []

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        if not sand:
            fejl.append(f"{navn}{': ' + detalje if detalje else ''}")

    # 1. Mutation: afsnittet skal *findes* på niveau 1 — den form planen
    #    faktisk har. Dår ville awk-kriteriet givet 0 linjer.
    tjek("niveau 1 findes", find_status(_plan("- **1** målt\n")) is not None)
    # 2. Mutation: samme afsnit på niveau 2. Dommen skal ikke være bundet til
    #    den niveauplanen lige nu tilfældigvis bruger — en `# STATUS` → `##`-
    #    omskrivning må ikke slå porten i gul.
    tjek("niveau 2 findes",
         find_status(_plan("- **1** målt\n", overskrift="## STATUS")) is not None)
    tjek("niveau 3 findes",
         find_status(_plan("- **1** målt\n", overskrift="### STATUS")) is not None)
    # 3. Mutation: STATUS som *sidste* afsnit, uden overskrift bagefter. Den
    #    anden awk-form (`/^# /` som afslutter) læser resten af filen med.
    tjek("sidste afsnit findes",
         find_status("# STATUS\n\n- **1** målt\n") is not None)
    # 4. Mutation: en plan uden STATUS skal være RØD, ikke grøn. Det er hele
    #    pointen med porten: awk-kriteriet gav 0 linjer og dømte intet.
    tjek("manglende afsnit er rød", "ikke fundet" in "\n".join(dom("# Ryggrad\n\n- 1\n")))
    # 5. Mutation: 26 linjer skal være røde med det rigtige antal nævnt.
    lang = "- **1** målt\n" + "".join(f"  fortsættelse {i}\n" for i in range(25))
    fund = dom(_plan(lang))
    tjek("26 linjer er rød", any("26 linjer" in f for f in fund), str(fund))
    # 6. Mutation: præcis 25 linjer er grøn — så dommen kan ikke være rød for
    #    enhver voks, kun for en ulovlig.
    krop_25 = "- **1** målt\n" + "".join(f"  fortsættelse {i}\n" for i in range(24))
    tjek("25 linjer er grøn", dom(_plan(krop_25)) == [], str(dom(_plan(krop_25))))
    # 6b. Mutation: en `###` *inde* i STATUS hører til afsnittet, så den
    #     kan ikke skjule den tekst den dækker for dommen.
    tjek("### tæller med i afsnittet",
         len(find_status("# STATUS\n\n- **1** målt\n### under\n  tekst\n"
                         "## andet\n")[2]) == 3)
    # 7. Mutation: et punkt uden tal er rødt.
    fund = dom(_plan("- målt på live i går\n  se ❓ nedenfor\n"))
    tjek("punkt uden tal er rød", any("uden tal" in f for f in fund), str(fund))
    # 7b. Mutation: et tal på en *fortsættelseslinje* tæller, ellers tvinger
    #     dommen tal op på første linje og skriver dårligere tekst.
    tjek("tal på fortsættelse tæller",
         dom(_plan("- se ❓ nedenfor\n  2 secrets mangler\n")) == [])
    # 8. Mutation: en *fortsættelseslinje* uden tal er grøn, ellers dømmer
    #    dommen sin egen pyntning.
    tjek("fortsættelseslinje er grøn", dom(_plan("- **2** målt\n  se arkivet\n")) == [])
    # 9. Mutation: en plan over 40.000 tegn er rød.
    tjek("for stor plan er rød",
         any("PLAN:" in f for f in dom(_plan("- **1** målt\n", efter="x" * 40_100))))
    # 10. Mutation: den rigtige plan skal være grøn — ellers ligger porten i
    #     gaten og rødmer deploys for en fejl, der ikke findes.
    reel = dom(PLAN.read_text(encoding="utf-8"))
    tjek("den rigtige plan er grøn", not reel, "; ".join(reel[:3]))

    for linje in fejl:
        print(f"  FEJL  {linje}")
    print(f"check-plan-status-selftest: {'OK' if not fejl else 'RØD'}"
          f" ({11 - len(fejl)}/11 kontroller)")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true",
                        help="kør portens egen kontrol af sig selv")
    parser.add_argument("--plan", help="døm en anden planfil end repoets")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    plan = Path(args.plan) if args.plan else PLAN
    tekst = plan.read_text(encoding="utf-8")
    fund = dom(tekst)
    for linje in fund:
        print(linje)
    fundtagt = find_status(tekst)
    if fund:
        print(f"\nplan-status: RØD — {len(fund)} fund i {plan.name}")
        return 1
    _, _, krop = fundtagt
    print(f"plan-status: GRØN — STATUS er {len(krop)} af {MAX_STATUS_LINES} "
          f"linjer, {sum(1 for l in krop if BULLET_RE.match(l))} punkter "
          f"med tal hver, planen er {len(tekst)} af {MAX_PLAN_CHARS} tegn")
    return 0


if __name__ == "__main__":
    sys.exit(main())