#!/usr/bin/env python3
"""Dom at forsidens tjek tager den indtastede adresse med videre til værktøjet.

Baggrund (2/10): `#url=` er ikke en ny idé i dette repo. Fem sider læser den
fragment altid og kører på den — `/scan`, `/scan-da`, `/cookie-check`,
`/cookie-check-da`, `/compliance-report` — og syv platform-guides i `/guides`
linker til `/scan#url=https%3A%2F%2Fwww.webflow.com`. Konventionen er ældre
end denne port.

Men **ingen side i familien producerede den**. Målt 2/10 på den levende
udgivelse: `mahope.tools/` og `/da/` erklærer hver to `next`-links ud af
forsidens tjek (`window.ONE_OFF_CHECK.next`), `/scan` og `/scan-da` læser
`#url=`, og alligevel skrev `grep -c 'takesUrl' site/*.html` 0 — fordi motoren
havde ingen måde at sætte den på. Den dybeste handling på forsiden — «Full
WCAG scan», den scanner der sælger EUComply Pro til $79 pr. år — endte altså
på en side med et tomt felt, der spurgte om den adresse læseren for et sekund
siden havde indtastet. Det er den slags friktion der ligger lige inden for
købet, og den er usynlig: ingen fejl, intet galt, bare et felt der skal fyldes
igen.

Fejlformen porten lukker er derfor **ikke** «en side glemte at læse `#url=`» —
det er nødvendigt, men ikke nok. En motor der læser flaget og en side der
erklærer det kan stadig være forskudt fra hinanden på tre måder, og alle tre er
stille:

1. **Siden erklærer ikke, men værktøjet læser.** Så rejser adressen ikke med,
   og intet viser at der gik noget tabt.
2. **Siden erklærer, men værktøjet ikke læser.** Så `#url=` hænger i adresselinjen
   på en side der ignorerer den — linket *ser* ud til at virke.
3. **Motoren bruger flaget ikke.** Så er `takesUrl: true` en død egenskab, og
   dom 1 og 2 er begge grønne.

Derfor dømmer porten **de tre ender mod hinanden** frem for at læse prosa:

- Hver `next`-post på en forside læses, og den rute den peger på slås op i
  `site/`. Læser den `#url=`, skal posten være `takesUrl: true` (dom 1).
- Er posten `takesUrl: true`, skal den rute læse `#url=` (dom 2).
- Motoren skal bygge fragmentet af flaget (dom 3).
- Og der skal være mindst én handoff i familien (dom 4), så porten ikke kan være
  grøn ved at der ingen er.

Forsiderne kommer fra **build-manifestet** (`frontpage_sources_or_empty()` i
`tools/check_article_paid_path.py`), ikke fra en håndlavet liste — samme kilde
som `tools/check_front_door.py`. Derfor kan svaret ikke blive nyt på en måde
porten ikke ser.

Kør:  python3 tools/check_url_handoff.py            # dom alle forsider
      python3 tools/check_url_handoff.py --self-test # 8 kontroller
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
sys.path.insert(0, str(ROOT / "tools"))

# Hvilken motor der hører til hvilken konfigurationsvindue på forsiden. En
# motor der mangler her får dom 3 på sin egen fil og en port-rød på forsiden,
# fordi vinduet så er «uden dom» — det er den fejl, der holder listen ærlig når
# en ny forside får sit eget tjek.
MOTORER: dict[str, str] = {
    "ONE_OFF_CHECK": "one-off-check.js",
    "CONVERT_CHECK": "convert-check.js",
}

FRAGMENT = "#url="
TAKES_URL = re.compile(r"\btakesUrl\s*:\s*true\b")
VINDUE = re.compile(r"window\.(?P<navn>[A-Z_]+)\s*=\s*\{")
# `window.X = { … \n};` — blokke er flade, så den næste `\n};` lukker den.
BLOK_SLUT = re.compile(r"\n\};")
NEXT_EGENSKAB = re.compile(r"next\s*:\s*\[")
# Én post: `{label: '…', href: '…'}` med valgfri `takesUrl` imellem.
POST = re.compile(
    r"""\{\s*label:\s*['"](?P<label>[^'"]*)['"]\s*,\s*href:\s*['"](?P<href>[^'"]+)['"]"""
    r"""(?P<rest>[^}]*)\}"""
)


def laes_urlfragment(kode: str) -> bool:
    """Læser kilden `#url=`-fragmentet?

    Begge dele skal være der: `location.hash` er hvor fragmentet læses, og
    `#url=` er nøglen. En side der nævner `#url=` i en kommentar, eller læser et
    hash uden at kigge efter nøglen, tæller ikke.
    """
    return FRAGMENT in kode and "location.hash" in kode


def dom_handoff(kode: str, rute: str, tag: str) -> list[str]:
    """Fund for én `next`-post. `kode` er målrutens egen kildekode."""
    fund: list[str] = []
    laes = laes_urlfragment(kode)
    erklæret = bool(TAKES_URL.search(tag))
    if laes and not erklæret:
        fund.append(
            f"{rute}: læser `{FRAGMENT}`, men `next`-linket er ikke "
            f"`takesUrl: true` — den adresse læseren tjekkede bliver liggende "
            f"og skal skrives ind igen")
    if erklæret and not laes:
        fund.append(
            f"{rute}: `next`-linket er `takesUrl: true`, men siden læser ikke "
            f"`{FRAGMENT}` med `location.hash` — adressen lander i "
            f"adresselinjen og ignoreres")
    return fund


def dom_motor(kode: str, fil: str) -> list[str]:
    """Dom 3: motoren skal bruge flaget, ellers er det en død egenskab."""
    fund: list[str] = []
    if "takesUrl" not in kode:
        fund.append(
            f"{fil}: læser ikke `takesUrl` — forsiden kan erklære at et link "
            f"vil have adressen med, og motoren gør det alligevel ikke")
    if FRAGMENT not in kode:
        fund.append(
            f"{fil}: bygger ikke `{FRAGMENT}` — der er ingen vej fra flaget til "
            f"et link der bærer adressen")
    return fund


def dom_forside(tekst: str, sti: str, motorer: dict[str, str],
                laeser: dict[str, str | None]) -> tuple[list[str], int]:
    """Fund for én forside. `laeser` er rute -> målrutens kode (None = filen
    findes ikke). Returnerer fundene og antallet af handoffs."""
    fund: list[str] = []
    handoffs = 0
    m = VINDUE.search(tekst)
    if m is None:
        return fund, 0
    navn = m.group("navn")
    slut = BLOK_SLUT.search(tekst, m.end())
    blok = tekst[m.start():slut.start()] if slut else tekst[m.start():]
    n = NEXT_EGENSKAB.search(blok)
    if n is None:
        return fund, 0
    for post in POST.finditer(blok, n.end()):
        href = post.group("href")
        # `#install` er et anker på siden selv og `/da/…` er rod-relative
        # ruter. Kun en rute i vores eget site er en handoff.
        if not href.startswith("/") or href.startswith("//") or "#" in href:
            continue
        rute = href.split("?")[0]
        kode = laeser.get(rute, None)
        if kode is None:
            fund.append(
                f"{sti}: `next`-linket peger på `{rute}`, og der er ingen "
                f"kildefil for den i site/ — linket fører ingen steder")
            continue
        if kode == "":
            fund.append(f"{rute}: kildefilen er tom")
            continue
        if laes_urlfragment(kode):
            handoffs += 1
        fund.extend(dom_handoff(kode, f"{sti} -> {rute}", post.group("rest")))
    if navn not in MOTORER:
        fund.append(
            f"{sti}: `window.{navn}` er ikke erklæret i MOTORER i "
            f"tools/check_url_handoff.py — motoren bag den er uden dom")
    return fund, handoffs


def dom_alle() -> list[str]:
    from check_article_paid_path import frontpage_manifest_error, frontpage_sources_or_empty

    fejl = frontpage_manifest_error()
    if fejl:
        return [f"kan ikke læse build-manifestet: {fejl}"]
    forsider = frontpage_sources_or_empty()
    if not forsider:
        return ["build-manifestet gav ingen forside — porten dømmer intet"]

    motor_filer = {navn: SITE / fil for navn, fil in MOTORER.items()}
    motor_kode = {navn: (p.read_text(encoding="utf-8", errors="replace")
                         if p.is_file() else "")
                  for navn, p in motor_filer.items()}

    fund: list[str] = []
    handoffs = 0
    maalt = 0
    for domaene, per_rute in forsider.items():
        for rute, kilde in sorted(per_rute.items()):
            if kilde is None:
                print(f"note: {domaene}{rute} har ingen kildefil i manifestet")
                continue
            tekst = kilde.read_text(encoding="utf-8", errors="replace")
            laeser: dict[str, str | None] = {}
            for post_href in alle_next_hrefs(tekst):
                maal = post_href.split("?")[0]
                sti = SITE / (maal.lstrip("/") + ".html")
                laeser[maal] = (sti.read_text(encoding="utf-8", errors="replace")
                                if sti.is_file() else None)
            side_fund, n = dom_forside(tekst, f"{domaene}{rute}", motor_kode, laeser)
            fund.extend(side_fund)
            handoffs += n
            maalt += 1

    for navn, kode in motor_kode.items():
        fund.extend(dom_motor(kode, MOTORER[navn]))

    if handoffs == 0:
        fund.append(
            "ingen `next`-link i familien peger på en side der læser "
            f"`{FRAGMENT}` — porten dømmer intet, og det er netop den "
            "tilstand opgaven skal lukke")
    print(f"note: {maalt} forside(r) dømt, {handoffs} handoff(s) "
          f"på ruter der læser `{FRAGMENT}`, {len(MOTORER)} motor(er) erklæret")
    return fund


def alle_next_hrefs(tekst: str) -> list[str]:
    """Alle `href`-værdier i `next`-listerne på siden."""
    fund: list[str] = []
    for m in VINDUE.finditer(tekst):
        slut = BLOK_SLUT.search(tekst, m.end())
        blok = tekst[m.start():slut.start()] if slut else tekst[m.start():]
        n = NEXT_EGENSKAB.search(blok)
        if n is None:
            continue
        fund.extend(p.group("href") for p in POST.finditer(blok, n.end()))
    return fund


# --------------------------------------------------------------------------
# Selvtest. Fixtures er markup, og målrutens kode lægges ind som dict — så
# porten dømmer de samme regler som `dom_alle`, uden at røre en rigtig fil.
# --------------------------------------------------------------------------
LAESER = {"/scan": "location.hash.match(/#url=(.+)$/)"}
LAESER_IKKE = {"/scan": "document.getElementById('urlInput').focus()"}

FORside = (
    '<script>window.ONE_OFF_CHECK = {\n'
    "  then: '…',\n"
    "  next: [{label: 'Full WCAG scan', href: '/scan', takesUrl: true}]\n"
    "};</script>"
)
FORside_IKKE_ERKLARET = FORside.replace(", takesUrl: true", "")
FORside_ANKER = FORside.replace("href: '/scan'", "href: '#install'")
FORside_FREMDE = FORside.replace("href: '/scan'", "href: 'https://example.com'")
FORside_MANGEL = FORside.replace("href: '/scan'", "href: '/findes-ikke'")
FORside_TOM = '<script>window.ONE_OFF_CHECK = {\n  then: "…"\n};</script>'

SELFTEST = [
    ("post erklæret, målruten læser fragment", FORside, LAESER, 0),
    ("post ikke erklæret, målruten læser", FORside_IKKE_ERKLARET, LAESER, 1),
    ("post erklæret, målruten læser ikke", FORside, LAESER_IKKE, 1),
    ("anker på egen side er ikke en handoff", FORside_ANKER, LAESER, 0),
    ("fremmed link er ikke en handoff", FORside_FREMDE, LAESER, 0),
    ("post på en rute uden kildefil", FORside_MANGEL, {}, 1),
    ("forside uden `next` er ikke en fejl", FORside_TOM, {}, 0),
    ("side uden konfigurationsvindue", "<p>ingen tjek her</p>", {}, 0),
]

MOTORTEST = [
    ("motoren bruger flaget og fragmentet",
     "if (item.takesUrl) return item.href + '#url=' + encodeURIComponent(u);", 0),
    ("motoren læser ikke flaget",
     "return item.href + '#url=' + v;", 1),
    ("motoren bygger ikke fragmentet",
     "if (item.takesUrl) return item.href;", 1),
    ("motoren bruger hverken flag eller fragment",
     "return item.href;", 2),
]

GRON_MOTOR = ("function medUrl(item, data) {\n"
              "  if (!item.takesUrl) return item.href;\n"
              "  return item.href + '#url=' + encodeURIComponent(data.finalUrl);\n"
              "}\n")


def selvtest() -> int:
    fejl = 0
    for navn, forside, laeser, forventet in SELFTEST:
        fund, _ = dom_forside(forside, "_selftest_url_handoff.html",
                              {"ONE_OFF_CHECK": GRON_MOTOR}, laeser)
        ok = len(fund) == forventet
        fejl += 0 if ok else 1
        print(f"{'ok   ' if ok else 'FEJL '} {navn} "
              f"({len(fund)} fund, forventede {forventet})")
        if not ok:
            for f in fund:
                print("        ", f)
    for navn, kode, forventet in MOTORTEST:
        fund = dom_motor(kode, "_selftest_motor.js")
        ok = len(fund) == forventet
        fejl += 0 if ok else 1
        print(f"{'ok   ' if ok else 'FEJL '} {navn} "
              f"({len(fund)} fund, forventede {forventet})")
        if not ok:
            for f in fund:
                print("        ", f)
    print(f"check-url-handoff-selftest: {'OK' if fejl == 0 else 'RØD'} "
          f"({len(SELFTEST) + len(MOTORTEST) - fejl}/"
          f"{len(SELFTEST) + len(MOTORTEST)} kontroller)")
    return 1 if fejl else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return selvtest()
    fund = dom_alle()
    if fund:
        print(f"url-handoff: RØD — {len(fund)} fund")
        for f in fund:
            print("  -", f)
        return 1
    print("url-handoff: GRØN — hvert `next`-link der peger på en side med "
          f"`{FRAGMENT}` er erklæret, og hver erklæret rute læser den")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())