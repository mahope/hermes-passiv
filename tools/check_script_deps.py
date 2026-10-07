#!/usr/bin/env python3
"""Dom at en side indlæser hver motor, den kalder.

Fejlformen er den stille: en side kalder en global fra et af vores egne scripts,
men `<script src="…">`-tagget mangler. Der er ingen syntaksfejl, ingen build-fejl,
og ingen port så vidt jeg har fundet, så koden ser rigtig ud hele vejen. I
browseren er den `ReferenceError: CleanCopyReadable is not defined`, og den
rammer præcis det øjeblik, en besøgende trykker «Convert».

Målt 2/10: `/url-to-markdown` og `/da/url-til-markdown` flyttede
`extractReadable` ud i `/readable.js` for at forsidekonverteringen kunne bruge
den, men lagde ikke script-tagget på de to sider der *allerede* kaldte den.
Resultatet var, at Clean Copies egen konverteringsværktøj ville kaste, når man
skrev en adresse — og hele gaten var grøn, fordi ingen af portene kørte koden.

Derfor dømmer porten to ting:

1. **Ingen brug uden indlæsning.** Bruger en side en af vores globale, skal den
   have et `<script src>` på den motor, der ejer globalen.
2. **Ejermotoren findes.** Er den aftalte fil væk, er det et fund — ellers ville
   punkt 1 være grøn ved at slette motoren.

Den dømmer kun *brug af en global*, altså et navn i et script på siden. Den
ser ikke efter config-globale siden selv sætter (`CC_DONATE`, `OC_DONATE`), og
den dømmer ikke `href="javascript:…"` — bookmarkletten indeholder hele kernen
inline, så den har ingen afhængighed at indlæse.

    python3 tools/check_script_deps.py            # dom alle kildesider
    python3 tools/check_script_deps.py --self-test # 8 kontroller
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# Global -> den fil der ejer den. Holdt her og ikke udledt af koden, fordi en
# global uden ejer netop er det porten skal finde; den må ikke have en dør der
# definerer den, så arver den intet.
EJERE: dict[str, str] = {
    "CleanCopyCore": "clean-copy-core.js",
    "CleanCopyReadable": "readable.js",
    "NET": "net.js",
    "ONE_OFF_CHECK": "one-off-check.js",
    "CONVERT_CHECK": "convert-check.js",
    # Paletgeneratoren slår farvenavnet op her; en side der kalder det uden at
    # indlæse tabellen ville vise en tom kolonne uden en fejl nogen steder.
    "COLOR_NAMES": "color-names.js",
}

SCRIPT_SRC = re.compile(r"""<script[^>]+src=["']([^"']+)["']""")
SCRIPT_TAG = re.compile(r"""<script\b([^>]*)>(.*?)</script\s*>""", re.S | re.I)
SRC_ATTR = re.compile(r"""src=["']([^"']+)["']""")
# Bookmarklettens href indeholder koden inline, og den kode har apostrofer i sig
# (`typeof module==='object'`), så de to skilletegn skal matches hver for sig —
# ellers stopper regexen ved den første apostrof og resten læses som markup.
JS_URL = re.compile(r"""(?:href|src)=(?:"javascript:[^"]*"|'javascript:[^']*')""")
# Kommentarer er ikke kald. `site/clean-copy.html` skriver i en kommentar at
# dens motor har «samme kontrakt som `window.ONE_OFF_CHECK` på de to andre
# frontdører», og det er en henvisning, ikke et kald. `//` springes over når
# det følger et `:` eller `\`, ellers skæres `https://` i to.
BLOK_KOM = re.compile(r"/\*.*?\*/", re.S)
LINJE_KOM = re.compile(r"(?<![:\\])//[^\n]*")


def rens_kode(kode: str) -> str:
    return LINJE_KOM.sub("", BLOK_KOM.sub("", kode))


def kodetekst(tekst: str) -> str:
    """Kun det der faktisk kører: sidens inline scripts og de lokale scripts
    den indlæser. Prosa nævner også motorernes navne, og en artikel der siger
    «bruger ikke CleanCopyReadable» skal ikke være et fund."""
    dele: list[str] = []
    for attribut, krop in SCRIPT_TAG.findall(tekst):
        src = SRC_ATTR.search(attribut)
        if src:
            fil = SITE / src.group(1).lstrip("/")
            # Kun vores egne scripts: en CDN-fil har vi ikke i repoet at læse.
            if fil.is_file():
                dele.append(fil.read_text(encoding="utf-8", errors="replace"))
        else:
            dele.append(krop)
    return "\n".join(dele)


def dom_fil(tekst: str, sti: str) -> list[str]:
    """Fund i én sides markup. `sti` er hvad der skrives i fundet."""
    # En javascript:-URL bærer sin egen kode, så den er ikke en afhængighed.
    tekst = JS_URL.sub("href=", tekst)
    indlaeste = SCRIPT_SRC.findall(tekst)
    kode = rens_kode(kodetekst(tekst))
    fund: list[str] = []
    for gnavn, fil in EJERE.items():
        if not re.search(rf"\b{re.escape(gnavn)}\b", kode):
            continue
        if any(src.rstrip("/").endswith(fil) for src in indlaeste):
            continue
        fund.append(
            f"{sti}: kalder `{gnavn}` men indlæser ikke /{fil} — "
            f"brug `ReferenceError` i browseren")
    return fund


def dom_alle() -> list[str]:
    fund: list[str] = []
    for fil in sorted(SITE.rglob("*.html")):
        fund.extend(dom_fil(fil.read_text(encoding="utf-8", errors="replace"),
                            str(fil.relative_to(SITE))))
    # Punkt 2: ejermotoren skal ligge i site/, ellers er punkt 1 grøn for intet.
    for fil in sorted(set(EJERE.values())):
        if not (SITE / fil).exists():
            fund.append(f"site/{fil} mangler — {len(EJERE)} global(e) ville være "
                        f"uden ejermotor")
    return fund


SELFTEST = [
    ("global uden script-tag", '<script>CleanCopyReadable.extract(h);</script>', 1),
    ("global med script-tag", '<script src="/readable.js"></script>'
                              '<script>CleanCopyReadable.extract(h);</script>', 0),
    ("alle tre frontdørs-motorer", '<script src="/net.js"></script>'
                                   '<script src="/one-off-check.js"></script>'
                                   '<script>NET.ask("/api/x");</script>', 0),
    ("kernen uden sin fil", '<script src="/clean-copy-core.js"></script>'
                             '<script>CleanCopyCore.htmlToMarkdown(h);</script>', 0),
    ("bookmarklet har kernen inline",
     '<a href="javascript:var%20CC%3Dself.CleanCopyCore;">x</a>', 0),
    ("navnet i løbende tekst", "<p>We do not send your text to CleanCopyReadable.</p>", 0),
    ("navnet i en kommentar",
     '<script>// samme kontrakt som window.ONE_OFF_CHECK på de andre</script>', 0),
    ("et kald i kommentaren fjernes ikke",
     '<script src="/net.js"></script><script>NET.ask("/api/x"); // NET.postJSON("y")</script>', 0),
    ("relateret global røres ikke", "<p>See clean-copy-core.js for details.</p>", 0),
    ("ren side", "<h1>Hello</h1>", 0),
]


def selvtest() -> int:
    fejl = 0
    for navn, kilde, forventet in SELFTEST:
        fund = dom_fil(kilde, "_selftest_script_deps.html")
        ok = len(fund) == forventet
        fejl += 0 if ok else 1
        print(f"{'ok   ' if ok else 'FEJL '} {navn} "
              f"({len(fund)} fund, forventede {forventet})")
    print(f"selvtest: {len(SELFTEST) - fejl}/{len(SELFTEST)} kontroller")
    return 1 if fejl else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return selvtest()
    fund = dom_alle()
    for f in fund:
        print(f"  {f}")
    if fund:
        print(f"\nmotor-afhængighed: RØD — {len(fund)} fund i site/")
        return 1
    print(f"motor-afhængighed: GRØN — {len(EJERE)} motorer, hver side indlæser "
          f"dem den kalder")
    return 0


if __name__ == "__main__":
    sys.exit(main())