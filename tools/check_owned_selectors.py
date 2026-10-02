#!/usr/bin/env python3
"""Dom at `pagepass.OWNED_SELECTORS` er sande påstande, og ikke troen.

`tools/pagepass.py` slår **hver** sideregel for en selector i `OWNED_SELECTORS`
og gør derved den påstand, at designsystemet ejer den påstand og har en
erstatning. Påstanden blev aldrig efterprøvet — og da målingen 2/10 blev lavet,
viste den sig at være **delvis falsk**: 14 af 154 selectors havde ingen
erklæring i `site/style.css` overhovedet. Siderne skrev dem alligevel, så
byggetagen slettede dem og der var intet tilbage:

  `.plat-links a`      1 side   pille-styling -> almindelige links
  `.book-card-body`    2 sider  `min-width: 0` -> grid-item uden min-bredde
  `details.faq summary` 4 sider  `cursor: pointer` -> ingen pilemarkør
  `.book-header .tagline` 6 sider  18px + 12px luft -> 16.8px + 1.4rem
  `.gen label`/`.gen legend` 10 sider  generatorformens labels og fieldsets

Denne port gør påstanden til en målt ting: **hver selector i
`OWNED_SELECTORS` skal have en erklæring i `style.css`**, så byggetagen ikke kan
lave om på en side uden at have noget at erstatte den med.

**Sammenligningen er normaliseret, ikke rå.** Tre ting gør det samme udtryk, så
porten må ikke vælge mellem dem:

  1. **Attribut-citation** — `input[type=text]` og `input[type="text"]` er
     samme selector. Uden normaliseringen var 4 af de 14 fund *kun* en
     skrivefejl i `OWNED_SELECTORS`, og porten ville have været rød på en
     fejl der ikke findes.
  2. **Mellemrum** — `.book-header   .tagline` er `.book-header .tagline`.
  3. **Kommentarer** — `style.css` har en kommentar med `;` og `{` i sig. Uden
     at fjerne dem først læses de som en selector-prælude, og en hel klasse
     kan forsvinde fra listen og se ud som at være udokumenteret.

**Porten dømmer ikke** om style.css ser godt ud, om en erklæring har de
egenskaber siden bad om, eller om en side har mistet noget. Den dømmer den ene
påstand der gjorde at 14 sider mistede noget: *findes erstatningen?* Om en
sidesegenskab så virker, måles i browseren og i `check_built_css.py`.

Polaritet: `--self-test` fjerner en erklæring fra en kopi af style.css og
kræver at porten bliver rød, tilføjer en opfundet selector til kontrakten og
kræver det samme, og kræver at citation, mellemrum og kommentarer **ikke**
giver rødt — de tre normaliseringer, der ellers ville gøre porten ubrugelig.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = ROOT / 'site' / 'style.css'
PAGEPASS_PATH = ROOT / 'tools' / 'pagepass.py'

_RULE_HEAD_RE = re.compile(r'([^{}]+)\{')
_COMMENT_RE = re.compile(r'/\*.*?\*/', re.S)
_ATTR_RE = re.compile(r'\[\s*([\w-]+)\s*=\s*["\']?([^\]"\'\s]+)["\']?\s*\]')


def normalize(selector: str) -> str:
    """Én skriveform for det samme udtryk. Se docstringens tre punkter."""
    s = re.sub(r'\s+', ' ', selector.strip())
    s = s.replace('"', '').replace("'", '')
    s = _ATTR_RE.sub(r'[\1=\2]', s)
    s = re.sub(r'\s*>\s*', ' > ', s)
    return s


def declared_selectors(css: str) -> set:
    """Alle selectors style.css erklærer, efter normalisering."""
    bare = _COMMENT_RE.sub('', css)
    out = set()
    for m in _RULE_HEAD_RE.finditer(bare):
        for part in m.group(1).split(','):
            if part.strip():
                out.add(normalize(part))
    return out


def owned_selectors() -> list:
    """Kontrakten i pagepass.py, læst fra kilden og ikke importeret.

    Import ville trække hele modulet ind og genberegne `_SHELL_CLASSES` ved
    hver kørsel; her læses kun den ene samling, så porten ikke kan få sidevirkninger.
    """
    src = PAGEPASS_PATH.read_text(encoding='utf-8')
    m = re.search(r'OWNED_SELECTORS\s*=\s*\{(.*?)\n\}', src, re.S)
    if not m:
        raise SystemExit('check_owned_selectors: fandt ikke OWNED_SELECTORS i pagepass.py')
    body = m.group(1)
    # `re.findall` på en streng-tilfældesyntaks: find alle citaterede bidder.
    return [normalize(x) for x in re.findall(r'"([^"]+)"', body)]


def undocumented(owned: list, declared: set) -> list:
    return [s for s in owned if s not in declared]


# --------------------------------------------------------------------------
# Selvtest. Polaritet målt på rigtige filer, ikke på en syntetisk streng.
# --------------------------------------------------------------------------
def _selftest() -> int:
    css = CSS_PATH.read_text(encoding='utf-8')
    owned = owned_selectors()
    declared = declared_selectors(css)
    fails = []
    ran = 0

    def check(name: str, ok: bool, detail: str = '') -> None:
        nonlocal ran
        ran += 1
        if ok:
            print(f"  ok  {name}")
        else:
            print(f"  FAIL {name} {detail}")
            fails.append(name)

    # 1. Den rene fil er grøn, og kontrakten er ikke tom.
    check('ude på den rene fil er hver erklæring dokumentet',
          not undocumented(owned, declared),
          f"{undocumented(owned, declared)[:5]}")
    check('kontrakten er ikke tom', len(owned) > 100, f'kun {len(owned)}')

    # 2. POLARITET: fjern én erklæring -> porten skal blive rød. Derved er den
    #    fejl, porten er skrevet for, faktisk rød, og ikke bare grøn på en fil
    #    der tilfældigvis mangler det hele.
    victim = normalize('.gen label')
    check('ofnormaliationen rammer den rigtige erklæring', victim in declared)
    stripped = re.sub(r'^\.gen label\s*\{[^}]*\}\s*$', '', css, count=1, flags=re.M)
    check('mutationen fjernede faktisk en linje', stripped != css)
    check('efter at .gen label er fjernet, melder porten den',
          normalize('.gen label') in undocumented(owned, declared_selectors(stripped)))

    # 3. POLARITET: en opfundet selector i kontrakten skal give rødt, ellers
    #    dømmer porten intet.
    check('opfundet selector i kontrakten giver rødt',
          '.findes-ikke' in undocumented(owned + ['.findes-ikke'], declared))

    # 4. De tre normaliseringer må ikke give rødt på det samme udtryk.
    quoted = declared_selectors('input[type="text"], input[ type = url ] { width: 1px; }')
    check('attribut-citation er samme selector',
          'input[type=text]' in quoted and 'input[type=url]' in quoted)
    check('mellemrum i en sammensat selector er samme selector',
          '.book-header .tagline' in declared_selectors('.book-header   .tagline { color: red; }'))
    check('en kommentar skjuler ikke en erklæring',
          '.cli-demo' in declared_selectors('/* .cli-demo { display: none; } */\n.cli-demo { margin: 0; }'))
    check('en kommentar med klammer i sig læses ikke som en selector',
          normalize('details.faq summary') in declared_selectors(
              '/* se { .fj } */\ndetails.faq summary { cursor: pointer; }'))

    # 5. En regel i @media tæller — den er stadig en erklæring.
    check('en regel inde i @media tæller som erklæret',
          '.faq-item' in declared_selectors('@media (max-width: 600px) { .faq-item { padding: 0; } }'))

    if fails:
        print(f"\ncheck_owned_selectors selvtest: {len(fails)} fejl af {ran} domme")
        return 1
    print(f"\ncheck_owned_selectors selvtest: alle {ran} domme grønne")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test', action='store_true', help='polaritet: kræv at porten kan blive rød')
    args = ap.parse_args()
    if args.self_test:
        return _selftest()

    owned = owned_selectors()
    missing = undocumented(owned, declared_selectors(CSS_PATH.read_text(encoding='utf-8')))
    if missing:
        print(f"check_owned_selectors: RØD — {len(missing)} af {len(owned)} selectors i "
              f"pagepass.OWNED_SELECTORS har ingen erklæring i site/style.css.")
        for s in missing:
            print(f"  · {s}")
        print("\nByggetagen sletter hver sidesregel for disse, og der er intet tilbage. "
              "Erklær dem i style.css, eller tag dem ud af kontrakten.")
        return 1
    print(f"check_owned_selectors: GRØN — alle {len(owned)} selectors er dokumenteret i style.css")
    return 0


if __name__ == '__main__':
    sys.exit(main())
