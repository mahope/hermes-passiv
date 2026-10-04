#!/usr/bin/env python3
"""Dom at en `.hero-note` er mindre end den brødtekst den står under.

**Hullet.** Revieweren fandt 5/10 at `site/clean-copy.html:48` —
fold-CTA'en der peger på pristabellen — blev **20,8 px** i stedet for de to
andre noters 13,6 px. Årsagen er ikke markup: den er kaskaden.
`site/style.css:435` siger `.hero p { font-size: 1.15rem }` (specificitet 0,1,1)
og `.hero-note` siger `font-size: 0.85rem` (0,1,0). `.hero p` **vinder**, så en
`.hero-note` der er et `<p>` bliver præcis så stor som brødteksten over den.
På `html[data-product="cleancopy"] .hero p` (0,2,1) bliver den 1,3 rem = 20,8 px.

Målt i rigtig Chromium 390 og 1280 px mod den byggede `dist/`, **før** rettelsen:
`.hero-note` var 13,6 / **20,8** / 13,6 px på `cleancopy.tools/` og 13,6 /
**20,8** / 13,6 px på `/da/`, mens `h1` var 33,6 px og brødteksten 20,8 px — altså
ligeså stor som den afsnit den efter sig udtrykker at være en note under. På de
**179** blog- og guidesider med `<p class="hero-note">` var den 18,4 px mod de
13,6 px den samme regel siger, så fundet var ikke to sider: det var hele klassen.

**Reglen her er derfor skrevet på årsagen og ikke på de to linjer.** Rettelsen var
`:not(.hero-note)` på begge `.hero p`-regler, så brødteksten kun regeres af
brødteksten. Denne port forsvares mod at det kommer tilbage, og den dømmer det
den selv gjorde i klæderne på: *enhver regel i `style.css` der erklærer
`font-size` på en `p` under `.hero`, skal enten ekskludere `.hero-note` med
`:not()`, eller have lavere specificitet end `.hero-note` og sige det samme.*

Uden `:not()` er den eneste måde at holde skæggen på, at vælge det rigtige tag.
Revieweren anbefalede selv `<span class="hero-note">`, som de to cleancopy-sider
allerede bruger til den anden note — men det er en rettelse af to filer, og de
**20** generatorer under `tools/` der skriver `<p class="hero-note">` (målt 5/10)
gør det igen ved næste artikel.

**Porten dømmer kilden, ikke en browserbaseret måling.** Der er ingen Chromium i
gaten, så en måling kunne ikke være dommen alligevel. Det den dømmer er den
egenskab, der gjorde at kaskaden galt: om nogen regel i `site/style.css` kan give
en `.hero-note` en anden `font-size` end sin egen.

Polaritet målt på den rigtige fil, ikke på en syntetisk streng: `--self-test`
sætter `:not()` tilbage på de to regler og kræver at porten bliver rød med
filnavn, og den bygger sine fixtures i en temp-kopi, så `site/` røres ikke.

    python3 tools/check_hero_note_scale.py
    python3 tools/check_hero_note_scale.py --self-test
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STYLE = ROOT / "site" / "style.css"

RE_COMMENT = re.compile(r"/\*.*?\*/", re.S)
RE_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
RE_DECL_FONT_SIZE = re.compile(r"(?<![\w-])font-size\s*:\s*([^;}]+)")


def _rules(css: str):
    """(selector-dele, krop) for hver regel, med kommentarer fjernet.

    Ét `@media … {`-niveau hænger stadig foran, hvis reglen ligger indeni — samme
    behandling som `check_design_tokens._rules`, så en regel i en breakpoint-blok
    ikke taber sin selector.
    """
    for match in RE_RULE.finditer(RE_COMMENT.sub("", css)):
        selector = match.group(1)
        if "{" in selector:
            selector = selector.rsplit("{", 1)[1]
        dele = [d.strip() for d in selector.split(",") if d.strip()]
        if dele:
            yield dele, match.group(2)


def _strip_pseudo(s: str) -> str:
    """Fjerne `:hover`, `:not(…)` og `:nth-child(…)` — kun tilstandsdelene.

    `:not(.hero-note)` skal *ikke* forsvinde: det er netop den undtagelse, der
    holder reglen ærlig, så den bliver håndteret eksplicit i stedet.
    """
    s = re.sub(r":(?:hover|focus|focus-visible|active|disabled|visited)\b", "", s)
    s = re.sub(r":(?:nth-child|nth-of-type|first-child|last-child|only-child)"
               r"\([^()]*\)", "", s)
    return s


def _excludes_note(selector: str) -> bool:
    """`(0,1,0)` hvis selectoren siger at `.hero-note` ikke er med.

    Både `:not(.hero-note)` og `:not([class~="hero-note"])` tæller. En `:not()`
    med noget andet i (`p:not(.x)`) gør ikke — den siger intet om noten.
    """
    for indhold in re.findall(r":not\(([^()]*)\)", selector):
        for stykke in indhold.split(","):
            hvis = re.search(r"\.([A-Za-z0-9_-]+)", stykke)
            if hvis and hvis.group(1) == "hero-note":
                return True
            if re.search(r"""class\s*[~|^$*]?=\s*["']?[^"'\]]*\bhero-note\b""", stykke):
                return True
    return False


def _specificitet(selector: str) -> tuple[int, int, int]:
    """`(id, klasse, element)` — kun de tre tal der afgør kaskaden."""
    s = re.sub(r":not\([^()]*\)", "", selector)
    s = _strip_pseudo(s)
    id_er = len(re.findall(r"#[\w-]+", s))
    attributter = len(re.findall(r"\[[^\]]*\]", s))
    klasser = len(re.findall(r"\.[\w-]+", s)) + attributter
    elementer = len(re.findall(r"(?:^|[\s>+~])[a-zA-Z][\w-]*", s)) - len(
        re.findall(r"::?[\w-]+", s))
    return (id_er, klasser, max(elementer, 0))


def _er_note_under_hero(selector: str) -> bool:
    """Matcher selectoren en `p` *under* en `.hero`?

    Kun den form der findes i skallen: et led på `.hero` og et sidste led der er
    `p` (eller `*`). `.book-header p` er ikke heroen — `.hero-note` er aldrig
    der, og porten skal ikke rødme på en regel der ikke kan ramme noten.
    """
    s = re.sub(r":not\([^()]*\)", "", selector).strip()
    dele = re.split(r"\s*[>+~]\s*|\s+", s)
    dele = [d for d in dele if d]
    if len(dele) < 2:
        return False
    if not any(re.search(r"\.hero\b", d) for d in dele[:-1]):
        return False
    sidste = _strip_pseudo(dele[-1])
    return bool(re.fullmatch(r"p|\*", sidste)) or sidste.startswith("p.") or sidste == "p"


def _font_size(krop: str) -> str | None:
    m = RE_DECL_FONT_SIZE.search(krop)
    return " ".join(m.group(1).split()) if m else None


def _note_regel(css: str) -> tuple[tuple[int, int, int], str] | None:
    """`(specificitet, font-size)` for skallens egen `.hero-note`-regel."""
    fund: list[tuple[tuple[int, int, int], str]] = []
    for dele, krop in _rules(css):
        for led in dele:
            if re.fullmatch(r"\.hero-note", led.strip()):
                størrelse = _font_size(krop)
                if størrelse is not None:
                    fund.append((_specificitet(led), størrelse))
    return fund[-1] if fund else None


def dom(css: str, *, filnavn: str = "style.css") -> list[str]:
    """Fund i én CSS-tekst. Rename til `filnavn` kun for læsbarhed."""
    egen = _note_regel(css)
    if egen is None:
        return [f"{filnavn}: skallen erklærer ingen `.hero-note`-regel med en "
                f"`font-size`, så porten kan ikke vide hvad noten skal være"]
    notens_sp, notens_størrelse = egen
    fund: list[str] = []
    for dele, krop in _rules(css):
        for led in dele:
            if _excludes_note(led):
                continue
            if not _er_note_under_hero(led):
                continue
            størrelse = _font_size(krop)
            if størrelse is None:
                continue
            sp = _specificitet(led)
            # Samme specificitet: senere i filen vinder, og reglen står *før*
            # heroen i style.css. Sammenlign på rækkefølge via tuplen her er
            # bevidst ikke gjort — ligestilling er den konservative dom.
            if sp > notens_sp:
                fund.append(
                    f"{filnavn}: `{led.strip()}` sætter font-size {størrelse} med "
                    f"specificitet {sp}, og den er højere end `.hero-note`'s "
                    f"{notens_sp} ({notens_størrelse}) — reglen vinder på alle sider, "
                    f"også når `.hero-note` er et `<p>`. Skriv "
                    f"`:not(.hero-note)` i stedet.")
    # Duplikater: samme regel kan stå i to led i én selector-liste.
    return list(dict.fromkeys(fund))


def _selftest() -> int:
    css = STYLE.read_text(encoding="utf-8")
    fejl: list[str] = []
    kørte = 0

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        nonlocal kørte
        kørte += 1
        print(f"  {'ok  ' if sand else 'FAIL'} {navn}{'' if sand else '  ' + detalje}")
        if not sand:
            fejl.append(navn)

    # 1. Den rene fil skal være grøn — ellers lå porten i gaten og rødmer
    #    deploys for en fejl, der ikke findes.
    rene = dom(css)
    tjek("den rene fil er grøn", not rene, "; ".join(rene[:3]))

    # 2. Mutation: `:not(.hero-note)` væk fra `.hero p` — præcis den gamle kode.
    #    Uden denne linje var fundet grønt, og det er hele pointen med porten.
    mut1 = css.replace(".hero p:not(.hero-note), .subtitle",
                       ".hero p, .subtitle")
    fund1 = dom(mut1, filnavn="mutation1")
    tjek("`:not()` væk fra `.hero p` er rød",
         any("mutation1" in f for f in fund1), str(fund1[:2]))

    # 3. Mutation: samme for produktreglen, der var årsagen på cleancopy.
    mut2 = css.replace('html[data-product="cleancopy"] .hero p:not(.hero-note)',
                       'html[data-product="cleancopy"] .hero p')
    fund2 = dom(mut2, filnavn="mutation2")
    tjek("`:not()` væk fra cleancopy-reglen er rød",
         any("mutation2" in f for f in fund2), str(fund2[:2]))

    # 4. Polaritet: en regel der *kun* rammer brødteksten skal være grøn, ellers
    #    rødmer porten på en korrekt regel og læres at ignoreres.
    tjek("`.hero h1` er grøn", not dom(css + "\n.hero h1 { font-size: 3rem; }\n"))
    tjek("`.hero-meta` er grøn", not dom(css + "\n.hero-meta { font-size: 9rem; }\n"))
    tjek("`.book-header p` er grøn",
         not dom(css + "\n.book-header p { font-size: 9rem; }\n"))

    # 5. Polaritet: en ny `.hero p`-regel skal give rødt, også den der skrives
    #    *efter* `.hero-note` — det er den eneste retning porten ikke dømmer.
    tjek("ny `.hero p { font-size }` efter noten er rød",
         bool(dom(css + "\n.hero p { font-size: 2rem; }\n", filnavn="ny")))

    # 6. Polaritet: `.hero-note` må gerne have HØJERE specificitet, så en side med
    #    sin egen `.hero .hero-note` ikke rødmer.
    tjek("`.hero .hero-note` er grøn",
         not dom(css + "\n.hero .hero-note { font-size: 0.8rem; }\n"))

    # 7. Polaritet med vilje: `:not()` med noget andet må ikke tælles som
    #    en undtagelse — ellers kunne `:not(.x)` skjule en rigtig regel.
    tjek("`:not(.noget-andet)` er ikke en undtagelse",
         bool(dom(css + "\n.hero p:not(.noget-andet) { font-size: 2rem; }\n",
                  filnavn="not-andet")))

    # 8. En port uden `.hero-note`-regel skal sige det, ikke tie.
    tjek("manglende `.hero-note`-regel er rød",
         any("hero-note" in f for f in dom(".hero p { font-size: 2rem; }\n")))

    for linje in fejl:
        print(f"  FEJL {linje}")
    print(f"check-hero-note-scale-selftest: {'OK' if not fejl else 'RØD'} "
          f"({kørte - len(fejl)}/{kørte} kontroller)")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true",
                    help="kør portens egen kontrol af sig selv")
    args = ap.parse_args(argv)
    if args.self_test:
        return _selftest()
    fund = dom(STYLE.read_text(encoding="utf-8"))
    for linje in fund:
        print(linje)
    egen = _note_regel(STYLE.read_text(encoding="utf-8"))
    if fund:
        print(f"\nhero-note-scale: RØD — {len(fund)} fund i style.css")
        return 1
    print(f"hero-note-scale: GRØN — `.hero-note` er "
          f"{egen[1]} med specificitet {egen[0]}, og ingen `.hero p`-regel kan "
          f"overrule den")
    return 0


if __name__ == "__main__":
    sys.exit(main())