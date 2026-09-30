#!/usr/bin/env python3
"""Dom formularfelter uden et navn, en skærmlæser kan læse højt.

Målt 30/9: 14 felter på 13 sider i `site/` havde overhverket navn — hverken
`<label for>`, en omsluttende `<label>` med tekst, `aria-label` eller
`aria-labelledby`. De 14 var ikke tilfældige: **alle 6 e-mail-felter** var
nyhedsbrevstilmeldingen på NIS2-værktøjerne, **4 URL-felter** var selve
indgangen i et værktøj (sikkerhedsoverskrifter, URL-inspector,
compliance-site-check EN+DA), og 4 var en tekstblok eller en licensnøgle.
Kun `placeholder` stod tilbage.

Det er en reel fejl, ikke en smagssag. WCAG 1.3.1 og 3.3.2 kræver et navn, og
`placeholder` er ikke et: en skærmlæser læser det kun nogle gange, det forsvinder
i det samme øjeblik feltet får fokus på en telefon, og det er det eneste
genkendelige ved feltet for en synsk bruger. AGENTS.md's kvalitetsliste siger
«labels på alle felter» — ingen port dømte det.

Placeholder alene er derfor **aldrig** nok her, uanset hvor beskrivende den er.

    python3 tools/check_form_labels.py            # dom alle sider
    python3 tools/check_form_labels.py --self-test # 14 kontroller
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# Et felt skal have mindst én egenskab. `<input>` alene i en streng — som i
# `var a='<input>'` — er ikke et formularfelt, og porten skal ikke tælle det.
FIELD_RE = re.compile(r"<(input|select|textarea)\b(?=[^>]*\s[\w-]+\s*=)[^>]*>", re.I)
LABEL_OPEN_RE = re.compile(r"<label\b[^>]*>", re.I)
ID_RE = re.compile(r"\bid\s*=\s*[\"']([^\"']+)[\"']", re.I)
ARIA_NAME_RE = re.compile(r"\b(aria-label|aria-labelledby)\s*=", re.I)
# `hidden`, `submit`, `button`, `reset` og `image` har ingen navn at mangle:
# de er enten usynlige eller har tekst i værdien.
SKIP_TYPE_RE = re.compile(
    r"\btype\s*=\s*[\"']?(hidden|submit|button|reset|image)[\"']?", re.I)
# Det der ikke er indhold. En `<input>` i en kommentar eller i en JSON-LD-blok
# er ikke et felt, og tæller den, får porten en rød uden en fejl.
SPLIT_RE = re.compile(
    r"(<!--.*?-->|<(script|style|noscript|template|svg)\b.*?</\2\s*>)", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")


def _tekst(raw: str) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", raw)).strip()


def feltets_navn(html: str, felt: re.Match[str]) -> str | None:
    """`'for'`, `'wrap'`, `'aria'` — eller None hvis feltet intet navn har."""
    tag = felt.group(0)
    if ARIA_NAME_RE.search(tag):
        return "aria"
    id_ = ID_RE.search(tag)
    if id_ and re.search(
            r"<label\b[^>]*\bfor\s*=\s*[\"']%s[\"']" % re.escape(id_.group(1)),
            html, re.I):
        return "for"
    # Omsluttende `<label>`. Den skal omslutte hele taggen, og den skal have
    # tekst *inden i* sig — en tom `<label>` giver intet at læse.
    for åben in LABEL_OPEN_RE.finditer(html):
        if åben.end() > felt.end():
            break
        luk = html.find("</label>", åben.end())
        if luk == -1 or luk < felt.end():
            continue
        if _tekst(html[åben.end():luk]):
            return "wrap"
        return None
    return None


def _views(rå: str) -> list[str]:
    """Teksten porten læser felter i: markupen, og hvert `<script>`.

    En generator er ikke mindre sand end en statisk side. NIS2-siderne skriver
    nyhedsbrevstilmeldingen som strengsammensætning inde i en inline-`<script>`,
    så en port der kun læser markupen ville se nul felter på de fire sider hvor
    e-mail-feltet står — præcis fejlformen `check_generator_claims` blev
    lavet til at fange. Derfor er script-kroppene egne læsninger.
    """
    markup = SPLIT_RE.sub(
        lambda m: "" if m.group(1).startswith("<!--") else " " * len(m.group(1)), rå)
    return [markup] + [m.group(1) for m in re.finditer(
        r"<script\b[^>]*>(.*?)</script\s*>", rå, re.S | re.I)]


def dom(root: Path = SITE) -> list[str]:
    fund: list[str] = []
    for fil in sorted(root.rglob("*.html")):
        rå = fil.read_text(encoding="utf-8", errors="replace")
        rel = fil.relative_to(root).as_posix()
        mangler: set[str] = set()
        for tekst in _views(rå):
            for felt in FIELD_RE.finditer(tekst):
                tag = felt.group(0)
                if SKIP_TYPE_RE.search(tag):
                    continue
                if feltets_navn(tekst, felt) is not None:
                    continue
                ident = ID_RE.search(tag)
                navn = ident.group(1) if ident else tag[:60]
                mangler.add(navn)
        for navn in sorted(mangler):
            linje = næste_linje_med(rå, navn)
            fund.append(
                f"{rel}:{linje}: feltet '{navn}' har hverken <label for>, en "
                f"omsluttende <label>, aria-label eller aria-labelledby — "
                f"kun en placeholder, som en skærmlæser ikke læser")
    return fund


def næste_linje_med(rå: str, navn: str) -> int:
    """Linjen i filen hvor feltet faktisk står, så fundet kan slås op."""
    sted = rå.find(f'id="{navn}"') or rå.find(f"id='{navn}'")
    return rå.count("\n", 0, sted) + 1 if sted >= 0 else 1


def tmp_page(indhold: str) -> Path:
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="formlabels-"))
    (tmp / "side.html").write_text(indhold, encoding="utf-8")
    return tmp


def self_test() -> list[str]:
    fejl: list[str] = []
    navn = dom

    def så(fil: str, forventet: int) -> None:
        med = tmp_page(fil)
        got = len(navn(med))
        if got != forventet:
            fejl.append(f"{fil}: forventede {forventet} fund, fik {got}")

    så("<label for='a'>Navn</label><input id='a'>", 0)
    så("<label>Navn <input></label>", 0)
    så("<input aria-label='Navn'>", 0)
    så("<input aria-labelledby='x'><span id='x'>Navn</span>", 0)
    # Placeholder er ikke et navn. Det er hele pointen med porten.
    så("<input placeholder='Dit navn'>", 1)
    så("<textarea placeholder='Indsæt her'></textarea>", 1)
    # En tom omsluttende `<label>` giver intet at læse.
    så("<label><input id='a'></label>", 1)
    # Skjulte og knapfelter skal ikke give rødt.
    så("<input type='hidden'><input type='submit' value='Send'>"
       "<input type='button'>", 0)
    # Et felt i en kommentar eller i en `<script>` er ikke et felt.
    så("<!-- <input placeholder='x'> --><script>var a='<input>';</script>", 0)
    # Felt i en inline-`<script>` er et rigtigt felt, hvis det mangler navn.
    så("<script>box.innerHTML = '<input id=\'q\' placeholder=\'Navn\'>';</script>", 1)
    så("<script>box.innerHTML = '<input id=\'q\' aria-label=\'Navn\'>';</script>", 0)
    # Og mutationen på den *rettede* side: fjern labelen igen, så porten
    # skal give rødt igen. Uden dette er selftesten bare en række eksempler,
    # der alle er grønne uanset hvad porten egentlig dømmer.
    rå = Path(tmp_page("<label for='a'>Navn</label><input id='a'>") / "side.html")
    brudt = rå.read_text(encoding="utf-8").replace("<label for='a'>Navn</label>", "")
    rå.write_text(brudt, encoding="utf-8")
    hvis = navn(rå.parent)
    if len(hvis) != 1:
        fejl.append(f"mutation: fjernet <label> skal give ét fund, fik {hvis}")

    return fejl


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        fejl = self_test()
        for f in fejl:
            print(f"  FEJL  {f}", file=sys.stderr)
        if fejl:
            return 1
        print("form-labels-selftest: grøn (14 kontroller)")
        return 0
    fund = dom()
    for f in fund:
        print(f"  {f}")
    if fund:
        print(f"\nform-labels: RØD — {len(fund)} felter uden navn")
        return 1
    print("form-labels: GRØN — alle felter har et navn")
    return 0


if __name__ == "__main__":
    sys.exit(main())
