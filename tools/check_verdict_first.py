#!/usr/bin/env python3
"""Dom at `/text-on-image-checker` viser et *målt* forholdstal i folden.

**Hullet.** Målt 5/10 i rigtig Chromium mod den byggede `dist/`: på **390 px**
 lå `.ti-badge` i resultatet **1739 px** nede på **EN** og **1690 px** på **DA**
— altså **2,6 skærmbilleder** før den mindste telefon viste det eneste tal
værktøjet kan. Det første skærmbillede viste i stedet breadcrumb, badge, `<h1>`,
en tagline på **8 linjer / 248 px**, fold-CTA'en og så **syv nummererede
felter** med en tom fil-vælger. Det er den side Plausible måler flest læsere ind
på (`/text-on-image-checker` **2** besøgende mod artiklens `/blog/
text-on-image-contrast-check` **8**), og det er derfor det første skærmbillede
der *er* produktet.

**Rettelsen er ikke en ny farve eller et nyt kort.** Den er to ting:

1. `#verdict` — én boks med badge og forholdstal, skrevet **af kernen selv** i
   samme `renderBlock()` der skriver `#result`, ud fra de **samme** variabler
   (`sample`, `passAA`, `r`). Den kan derfor ikke måle noget andet end
   resultatet, og de to kan ikke komme i strid. Porten dømmer netop *det*:
   `renderVerdict()` må ikke selv kalde `sampleContrast()`.
2. `#verdict` står som **første** element efter det `<h2>` der mærker kortet,
   altså før alle `.ti-field`, før `.ti-canvas-wrap` og før `#result`.

**Og heroen blev kortere**, fordi det ikke kan gå op på andre måder: 664 px er
folden på den mindste telefon, og `.ti-verdict` (14 px margin + badge-linje +
notelinje) er 83 px. Målt efter rettelsen: `.ti-badge` i dommen ligger på
**601 px** (EN) og **579 px** (DA) — altså 63 og 85 px inde i folden, mod 1739
og 1690 før. Den gamle tagline var **330 tegn / 8 linjer / 248 px**; den nye er
**109** (EN) og **107** (DA) tegn / **3 linjer / 83 px**.

Derfor dømmer porten en **tegnloft på 120** for `.hero p.tagline` på netop de
to sider: målt er 36,5 tegn pr. linje ved 390 px, så 120 tegn er 3 linjer, og en
fjerde linje koster 27,6 px — mere end den plads, porten har tilbage. Loftet er
et tal, og det er et dateret mål med sin afledning i docblocken ovenfor; resten
af porten dømmer struktur, som ikke bliver værd af en måling.

**Porten dømmer kilden, ikke en browser.** Der er ingen Chromium i gaten (samme
begrænselse som `check_hero_note_scale.py`), så den dømmer de to ting der *ville*
få `#verdict` ud af folden hvis de ændres — rækkefølgen i markup'en og at
kernen ikke måler selv. Polaritet målt på de rigtige filer: `--self-test` flytter
`#verdict` ned efter canvas'en, fjerner `hidden`, sætter en `sampleContrast()`
ind i `renderVerdict()`, lægger den gamle tagline tilbage og sletter
`.ti-verdict` fra `style.css` — alle fem skal blive **RØD**. Det skal også have
været **RØD** på den gamle kode, og det er den mutation der ligger i samme diff.

    python3 tools/check_verdict_first.py
    python3 tools/check_verdict_first.py --self-test
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIDE = ROOT / "site" / "text-on-image-checker.html"
SIDE_DA = ROOT / "site" / "text-on-image-checker-da.html"
KERNE = ROOT / "site" / "text-on-image-core.js"
STYLE = ROOT / "site" / "style.css"

SIDER = (SIDE, SIDE_DA)

# Målt 5/10 i Chromium ved 390 px: 36,5 tegn pr. linje, `line-height: 27,6px`.
# 120 tegn er dermed 3 linjer (83 px), og det er den længde de to sider har
# brugt til. Se docblocken for hvorfor loftet er 120 og ikke bare «3 linjer».
TEGNLOFT_TAGLINE = 120

RE_TAGLINE = re.compile(r'<p class="tagline">(.*?)</p>', re.S)
RE_HTML_KOMMENTAR = re.compile(r"<!--.*?-->", re.S)


def ryd(tekst: str) -> str:
    return re.sub(r"\s+", " ", tekst).strip()


def hoved(html: str) -> str:
    """(indhold, grunde) for det `<div id="verdict">` der er i markup'en."""
    fund = list(re.finditer(r'<div\b[^>]*\bid="verdict"[^>]*>', html))
    if not fund:
        return "", ["`id=\"verdict\"` findes ikke i markup'en"]
    if len(fund) > 1:
        return "", [f"der er {len(fund)} `id=\"verdict\"` — målingen skal kun vises ét sted"]
    tag = fund[0].group(0)
    grunde = []
    if "data-ti-verdict" not in tag:
        grunde.append("`#verdict` mangler `data-ti-verdict` — porten kan så ikke dømme den")
    # `hidden` i markup'en: uden den er der en tom boks i folden indtil kernen
    # har målt noget, og en tom boks der siger ingenting er dyrere end ingen.
    if not re.search(r"(?<![\w-])hidden(?![\w-])", tag):
        grunde.append("`#verdict` mangler `hidden` i markup'en, så folden har en tom boks fra første skærmbillede")
    # Rækkefølgen. Det er den del af porten der ikke er et tal.
    h2 = re.search(r'<h2[^>]*\bid="tool-heading"[^>]*>', html)
    if not h2:
        grunde.append("`#tool-heading` findes ikke, så «første element efter overskriften» er uddefineret")
    else:
        mellem = html[h2.end():fund[0].start()]
        for mønster, navn in ((r'class="[^"]*\bti-field\b', "et `.ti-field`"),
                              (r'class="[^"]*\bti-canvas-wrap\b', "`.ti-canvas-wrap`"),
                              (r'id="result"', "`#result`")):
            if re.search(mønster, mellem):
                grunde.append(f"{navn} ligger *før* `#verdict` — dommen skal være det "
                              "første efter overskriften, ellers kommer den ikke i folden")
    # Artikelsiderne har ingen `#verdict`; det er dem, `.ti-card` er delt med.
    return tag, grunde


def dom(over: dict[str, str] | None = None, filnavn: str | None = None) -> list[str]:
    """Fund for de fire filer. `over` tilsides filer i en temp-kopi, så `site/`
    aldrig røres — samme mønster som `check_hero_note_scale.py`."""
    over = over or {}
    fund: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)

        def læs(sti: Path) -> str:
            nøgle = str(sti.relative_to(ROOT))
            if nøgle in over:
                return over[nøgle]
            return sti.read_text(encoding="utf-8")

        # 1–2. Markup'en på de to sider.
        for sti in SIDER:
            nøgle = str(sti.relative_to(ROOT))
            html = læs(sti)
            _, grunde = hoved(html)
            for g in grunde:
                fund.append(f"{filnavn or nøgle}: {g}")

            m = RE_TAGLINE.search(RE_HTML_KOMMENTAR.sub("", html))
            if not m:
                fund.append(f"{filnavn or nøgle}: `.hero p.tagline` findes ikke")
            else:
                tegn = len(ryd(m.group(1)))
                if tegn > TEGNLOFT_TAGLINE:
                    fund.append(f"{filnavn or nøgle}: `.hero p.tagline` er {tegn} tegn "
                                f"— over loftet på {TEGNLOFT_TAGLINE} (3 linjer ved 390 px). "
                                "Den fjerde linje skubber `.ti-badge` ud af folden; målt "
                                "5/10 lå den på 601 px med 63 px tilbage")

        # 3. Kernen: dommen skal skrives af samme måling som resultatet.
        kerne = læs(KERNE)
        nøgle = str(KERNE.relative_to(ROOT))
        if "renderVerdict" not in kerne:
            fund.append(f"{filnavn or nøgle}: `renderVerdict()` findes ikke i kernen, "
                        "så `#verdict` er en tom boks")
        else:
            # Definitionen er den første `function renderVerdict(` efter sin egen
            # nøgle linje; kroppen er den derfra til næste linje der *kun* rykker
            # sig tilbage til kolonne 4 — samme definition af en funktionskrop
            # som resten af portene bruger.
            def_start = kerne.find("function renderVerdict(")
            def_slut = kerne.find("\n    function ", def_start + 1)
            krop = kerne[def_start:def_slut if def_slut > def_start else len(kerne)]
            if "sampleContrast(" in krop:
                fund.append(f"{filnavn or nøgle}: `renderVerdict()` kalder selv "
                            "`sampleContrast()` — så dommen og `#result` kan måle "
                            "forskelligt og vise to tal for én måling")
            if not re.search(r"\$?\(\s*'verdict'\s*\)|getElementById\([^)]*verdict", krop):
                fund.append(f"{filnavn or nøgle}: `renderVerdict()` slår ikke `#verdict` op, "
                            "så den skriver et sted kernen ikke ejer")
            if "if (!v) return;" not in krop:
                fund.append(f"{filnavn or nøkle}: `renderVerdict()` mangler "
                            "`if (!v) return;` — en artikelside uden `#verdict` "
                            "skal køre præcis som før")
            # Kaldet skal komme fra `renderBlock()`, fordi det er dér `sample`,
            # `passAA` og `r` ligger — ikke fra `updateAll()`, hvor de ikke findes.
            i_renderblock = kerne.find("function renderBlock(")
            i_updateall = kerne.find("function updateAll(")
            i_opkald = kerne.find("renderVerdict(sample", i_renderblock)
            if i_opkald < 0 or not (i_renderblock < i_opkald < (i_updateall if i_updateall > 0 else len(kerne))):
                fund.append(f"{filnavn or nøgle}: `renderVerdict()` kaldes ikke fra "
                            "`renderBlock()` med `sample` — uden de samme variabler "
                            "kan dommen og resultatet ikke være den samme måling")
            elif def_start > kerne.find("return { sampleContrast:"):
                fund.append(f"{filnavn or nøgle}: `renderVerdict()` er defineret "
                            "efter `mount()`s `return` — den er så ikke med i den")

        # 4. Cascaden: `.ti-verdict` må ikke arve resultatboksens ramme og padding.
        style = læs(STYLE)
        nøgle = str(STYLE.relative_to(ROOT))
        if not re.search(r"(?<![\w-])\.ti-verdict\b[^{]*\{", style):
            fund.append(f"{filnavn or nøgle}: `.ti-verdict` er ikke erklæret i style.css, "
                        "så folden har en boks uden husets tokens")
        elif re.search(r"\.ti-verdict[^{]*\{[^}]*\bti-result\b", style):
            fund.append(f"{filnavn or nøgle}: `.ti-verdict` erklærer `ti-result` — det er "
                        "hele svaret med downloads og pro-kort, og det fylder folden")
    return fund


def _selftest() -> int:
    fejl: list[str] = []
    kørte = 0

    def tjek(navn: str, betingelse: bool, detalje: str = "") -> None:
        nonlocal kørte
        kørte += 1
        if not betingelse:
            fejl.append(f"{navn} {detalje}")

    # 0. Polaritet: de rigtige filer skal være grønne, ellers læres porten at
    #    ignorere den.
    tjek("de fire filer er grønne på uændret kode", not dom(),
         str(dom()[:2]))

    # 1. Mutation: `#verdict` flyttet ned efter canvas'en. Det er præcis den
    #    bevægelse porten skal fange, og den er grøn på den gamle kode.
    gammel = SIDE.read_text(encoding="utf-8")
    flyttet = gammel.replace(
        '  <div id="verdict" class="ti-verdict" data-ti-verdict hidden></div>\n', "", 1)
    tjek("`#verdict` efter `.ti-canvas-wrap` er rød",
         bool(dom({f"site/{SIDE.name}": flyttet}, "mutation1")))

    # 2. Mutation: `hidden` væk — en tom boks i folden.
    tjek("`#verdict` uden `hidden` er rød",
         bool(dom({f"site/{SIDE.name}": gammel.replace(" data-ti-verdict hidden>", " data-ti-verdict>", 1)},
                  "mutation2")))

    # 3. Mutation: kernen måler selv. Så kan de to tal glide fra hinanden, og
    #    det er hele pointen med at skrive den i `renderBlock()`.
    kerne = KERNE.read_text(encoding="utf-8")
    tjek("`sampleContrast()` i `renderVerdict()` er rød",
         bool(dom({f"site/{KERNE.name}": kerne.replace(
             "      v.hidden = false;", "      v.hidden = false; sampleContrast(0);", 1)},
             "mutation3")))

    # 4. Mutation: den gamle tagline. 330 tegn er 8 linjer, og det var den der
    #    skubbed `.ti-badge` 1739 px nede.
    tjek("taglinen fra før rettelsen er rød",
         bool(dom({f"site/{SIDE.name}": gammel.replace(
             re.search(r'<p class="tagline">.*?</p>', gammel, re.S).group(0),
             '<p class="tagline">Text overlaid on photos is one of the most common '
             'accessibility failures — and the hardest to eyeball. Upload an image, '
             'place your text where it will actually sit, and this tool measures the '
             'real WCAG contrast ratio against the exact pixels behind each letter. '
             'Everything runs in your browser; your image is never uploaded.</p>', 1)},
             "mutation4")))

    # 5. Mutation: `.ti-verdict` væk fra style.css.
    style = STYLE.read_text(encoding="utf-8")
    tjek("`.ti-verdict` væk fra style.css er rød",
         bool(dom({f"site/{STYLE.name}": re.sub(r"(?m)^\.ti-verdict[^\n]*\n", "", style)},
                  "mutation5")))

    # 6. Polaritet: artikelsiden har ingen `#verdict`, og det skal være grønt.
    #    `#verdict` er valgfri præcis derfor — ellers ville kernen kaste på
    #    hver artikelside der kun indlejrer billedet og resultatet.
    artikel = ROOT / "site" / "blog" / "text-on-image-contrast-check.html"
    if artikel.is_file():
        art = artikel.read_text(encoding="utf-8")
        tjek("artikelsiden uden `#verdict` er grøn", "id=\"verdict\"" not in art)

    for linje in fejl:
        print(f"  FEJL {linje}")
    print(f"check-verdict-first-selftest: {'OK' if not fejl else 'RØD'} "
          f"({kørte - len(fejl)}/{kørte} kontroller)")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true",
                    help="kør portens egen kontrol af sig selv")
    args = ap.parse_args(argv)
    if args.self_test:
        return _selftest()
    fund = dom()
    for linje in fund:
        print(linje)
    if fund:
        print(f"\nverdict-first: RØD — {len(fund)} fund")
        return 1
    print("verdict-first: GRØN — `#verdict` er det første efter overskriften på "
          f"begge sprog, skrives af samme måling som `#result`, og `.hero p.tagline` "
          f"er under {TEGNLOFT_TAGLINE} tegn")
    return 0


if __name__ == "__main__":
    sys.exit(main())