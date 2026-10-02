#!/usr/bin/env python3
"""Dom at hver frontdørs-tjek faktisk er tjekket.

Fejlformen er fra 2/10, fundet to gange på to forskellige måder. Begge
forsiderne **lignede** et fungerende tjek: en `<form>` med en knap, en statuslinje
og en `#…-result`-boks i markup, og hele gaten grøn. Men:

1. `extractReadable` blev flyttet ud i `/readable.js`, og de to sider der
   allerede kaldte den fik ikke `<script src="/readable.js">` — ReferenceError
   i browseren, `tools/check_script_deps.py` dømmer det nu.
2. **Den stille variant, som ingen port dømmer.** Begge frontdørsmotorer begynder
   med `if (!form || !window.NET) return;`. Dvs. hvis en forside omdøber sit
   `<form id>`, glemmer `/net.js`, eller indlæser motoren med en skrivefejl i
   `src`, så **gør motoren ingenting**: ingen fejl, ingen konsolfejl, ingen
   undtagelse. Siden ligner stadig et tjek, en besøgende trykker, intet sker, og
   den eneste målebare effekt er at bounce stiger.

Derfor dømmer porten de to ender af den samme ledning frem for at læse prosa:

1. **Én motor pr. form-id.** Formens `id` skal stå i `MOTORER` her, så et nyt
   frontdørstjek ikke kan udgives uden at erklære hvilken motor der hører til.
2. **Motoren hentes på forsiden.** `<script src>` skal pege på den fil, og
   `/net.js` skal være der — uden den er `window.NET` undefined og motoren
   returnerer stille.
3. **Motoren leder formen op i *netop* det id.** Det er den krydsreference der
   fanger punkt 2 ovenfor: en motor der kigger efter `cc-check-form` på en side
   der har `cc-check-form-2` er grøn for enhver anden læsning.
4. **Ingen rute uden `NET`.** Motoren må ikke selv kalde `fetch(` eller en rute,
   fordi 429-er-reglen og retry'en ligger i `/net.js` — det er samme krav som
   `tools/check_net_copies.py` stiller de andre klienter.
5. **Uden JavaScript skal formen stadig være brugbar.** `method="get"` og et
   `action` der ikke er tomt — så den der har slået JS fra lander i det rigtige
   værktøj og ikke på en død knap.

Forsiderne kommer fra **build-manifestet**, ikke fra en håndlavet liste:
`frontpage_sources()` i `tools/check_article_paid_path.py` spørger
`build_sites.SITES` + `select_files()` om den samme fil hvert domæne serverer
som `index.html`. Derfor kan svaret ikke blive *nyt* på en måde porten ikke ser —
en ny `index_from`, et nyt `remap` eller et nyt domæne giver automatisk en ny
forside at dømme.

**Målt 2/10:** 6 forsider har et `#check`-afsnit (mahope.tools, cleancopy.tools
og deskuptime.com i EN + DA), og bugbottle.dev har ingen endnu.

    python3 tools/check_front_door.py            # dom alle forsider
    python3 tools/check_front_door.py --self-test # 12 kontroller
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
sys.path.insert(0, str(ROOT / "tools"))

# Formens id på forsiden -> motoren der skal finde den. Holdt her og ikke udledt
# af koden, fordi en motor uden en side (eller en side uden en motor) er præcis
# det porten skal finde. En ny frontdør skal skrive sig ind her — det er det
# eneste sted, hvorfra man kan glemme det.
MOTORER: dict[str, str] = {
    "oc-check-form": "one-off-check.js",
    "cc-check-form": "convert-check.js",
}

NET = "net.js"
SECTION = re.compile(r"""<section\b[^>]*\bid=["']check["']""", re.I)
SECTION_OPEN = re.compile(r"<section\b", re.I)
SECTION_CLOSE = re.compile(r"</section\s*>", re.I)
FORM = re.compile(r"<form\b([^>]*)>", re.I)
ID = re.compile(r"""\bid=["']([^"']+)["']""")
ATTR = re.compile(r"""\b(method|action)=["']([^"']*)["']""", re.I)
SCRIPT_SRC = re.compile(r"""<script[^>]+src=["']([^"']+)["']""", re.I)
# `fetch` som sit eget kald. `NET.askGet` kalder fetch, men det er net.js der
# gør det, og det er også net.js der bærer 429-reglen — så motoren må ikke.
BARE_FETCH = re.compile(r"(?<![.\w])fetch\s*\(")
# Ethvert kalder på en rute: `.askGet(`, `.ask(`, `.postJSON(` foran en streng
# der starter med `/`. Kun kalder på `NET` (eller på et andet klient-objekt med
# samme kontrakt) er grønt; en motor der skriver `fetch('/api/url-inspect…')`
# er rød, fordi så springer den både retry'en og den endelige 429.
RUTE_KALD = re.compile(
    r"""(?P<obj>[A-Za-z_$][\w$.]*)\s*\(\s*(?P<rute>['"]/(?:api/|scan-proxy)[^'"]*)"""
)


def sektion_check(tekst: str) -> str | None:
    """Kroppen af `<section id="check">` — kun den sektion, ikke resten.

    Tæller åbne/lukkede `<section>` frem til den lukker, fordi et flad
    `.*?</section>` ville stoppe ved en *indre* sektion og dømme halve af den.
    """
    m = SECTION.search(tekst)
    if not m:
        return None
    dybde = 0
    for t in re.finditer(r"<section\b|</section\s*>", tekst[m.start():], re.I):
        dybde += 1 if t.group(0).lower().startswith("<section") else -1
        if dybde == 0:
            return tekst[m.start():m.start() + t.end()]
    return tekst[m.start():]


def src_til_fil(src: str) -> str:
    return src.split("?", 1)[0].lstrip("/")


def dom_motor(kode: str, fil: str) -> list[str]:
    """Fund i én motors kode. `fil` er hvad der står i fundet."""
    fund: list[str] = []
    eget_fetch = bool(BARE_FETCH.search(kode))
    if eget_fetch:
        fund.append(
            f"{fil}: kalder `fetch(` selv — gå gennem NET, så 429 er endelig "
            f"og et 5xx bliver prøvet igen")
    for m in RUTE_KALD.finditer(kode):
        obj = m.group("obj")
        # `NET.askGet('/api/x')` læses som obj=`NET`, fordi `askGet(` ikke kan
        # være en del af objektvej-udtrykket. Alt uden om `NET` er rødt — men et
        # kald på `fetch` er allerede meldt én gang ovenfor, så det tælles ikke
        # to gange for den samme linje.
        if obj.split(".")[0] == "NET" or (eget_fetch and obj.split(".")[0] == "fetch"):
            continue
        fund.append(
            f"{fil}: kalder `{obj}(` med ruten `{m.group('rute')}` — kun "
            f"NET.ask/askGet/postJSON bærer retry og den endelige 429")
    return fund


def dom_forside(tekst: str, sti: str, motor_filer: dict[str, Path]) -> list[str]:
    """Fund i én forside. `motor_filer` er fil-id -> stien til motorens kode."""
    krop = sektion_check(tekst)
    if krop is None:
        return []
    fund: list[str] = []

    forms = FORM.findall(krop)
    if len(forms) != 1:
        fund.append(f"{sti}: #check har {len(forms)} formularer, forventede 1 — "
                    f"et frontdørstjek er én adresse ind")
        return fund

    attributer = forms[0]
    form_id = (ID.search(attributer) or [None, None])[1] if ID.search(attributer) else None
    if not form_id:
        fund.append(f"{sti}: formularen i #check har intet id — motoren kan ikke "
                    f"finde den")
        return fund
    motor_fil = MOTORER.get(form_id)
    if motor_fil is None:
        fund.append(f"{sti}: #check bruger form-id `{form_id}`, som ingen motor "
                    f"er erklæret for — skriv den i MOTORER i "
                    f"tools/check_front_door.py")
        return fund

    # 5. Uden JavaScript: en rigtig GET med en rute.
    attributer_kv = {k.lower(): v for k, v in ATTR.findall(attributer)}
    if attributer_kv.get("method", "").lower() != "get":
        fund.append(f"{sti}: #{form_id} er ikke `method=\"get\"` — uden "
                    f"JavaScript kan den så ikke aflevere adressen")
    if not attributer_kv.get("action"):
        fund.append(f"{sti}: #{form_id} har intet `action` — uden JavaScript er "
                    f"knappen en død knap")

    # 2. Motoren og NET hentes på siden.
    indlaeste = {src_til_fil(s) for s in SCRIPT_SRC.findall(tekst)}
    if motor_fil not in indlaeste:
        fund.append(f"{sti}: #{form_id} er motor for /{motor_fil}, men siden "
                    f"indlæser den ikke — motoren returnerer stille, og der "
                    f"kommer ingen fejl")
    if NET not in indlaeste:
        fund.append(f"{sti}: /{NET} mangler — uden `window.NET` returnerer "
                    f"/{motor_fil} stille")

    # 3. Motoren leder formen op i netop det id.
    sti_motor = motor_filer.get(motor_fil)
    if sti_motor is None or not sti_motor.is_file():
        fund.append(f"{sti}: /{motor_fil} findes ikke i site/ — #{form_id} "
                    f"ville være uden motor")
        return fund
    kode = sti_motor.read_text(encoding="utf-8", errors="replace")
    if f"getElementById('{form_id}')" not in kode and \
            f'getElementById("{form_id}")' not in kode:
        fund.append(f"{sti}: /{motor_fil} leder ikke #{form_id} op — siden og "
                    f"motoren er ikke koblet, så tjekket gør intet")
    fund.extend(dom_motor(kode, f"{sti}:/{motor_fil}"))
    return fund


def dom_alle() -> list[str]:
    # Manifestet må kunne læses. Kan det ikke, er dommen over forsidefiler
    # meningsløs — og stille grøn ville være værre end rød.
    from check_article_paid_path import frontpage_sources_or_empty, frontpage_manifest_error

    fejl = frontpage_manifest_error()
    if fejl:
        return [f"kan ikke læse build-manifestet: {fejl}"]
    forsider = frontpage_sources_or_empty()
    if not forsider:
        return ["build-manifestet gav ingen forside — porten dømmer intet"]
    motor_filer = {fil: SITE / fil for fil in set(MOTORER.values())}

    fund: list[str] = []
    maalt = 0
    for domaene, per_rute in forsider.items():
        for rute, kilde in sorted(per_rute.items()):
            if kilde is None:
                print(f"note: {domaene}{rute} har ingen kildefil i manifestet")
                continue
            fund.extend(dom_forside(kilde.read_text(encoding="utf-8", errors="replace"),
                                   f"{domaene}{rute}", motor_filer))
            maalt += 1
    print(f"note: {maalt} forside(r) dømt, {len(MOTORER)} motorer erklæret")
    return fund


# Motor-kode der skal være grøn. Kun det der faktisk *kalder* en rute tæller,
# så `#` og «» i prosa ikke gør porten rød.
GRON_MOTOR = """
(function () {
  var form = document.getElementById('oc-check-form');
  if (!form || !window.NET) return;
  NET.askGet('/api/url-inspect?url=' + encodeURIComponent(url), 3, function () {});
  /* Ruten er nået, og 429 er endelig: se /net.js. */
}());
"""

# Sidens markup. Formens id står i markup, så porten selv finder motoren —
# mutationerne ændrer derfor kun markup og ikke portens kort.
SELFTEST = [
    # 1 + 2 + 3: form, motor og NET hver i sin rette ende.
    ("ren forside med ét tjek",
     '<section id="check"><form id="oc-check-form" method="get" '
     'action="/api/url-inspect"></form></section>'
     '<script src="/net.js"></script><script src="/one-off-check.js"></script>', 0),
    ("motoren hentes ikke på siden",   # mutation 1
     '<section id="check"><form id="oc-check-form" method="get" '
     'action="/api/url-inspect"></form></section>'
     '<script src="/net.js"></script>', 1),
    ("/net.js mangler",                 # mutation 2
     '<section id="check"><form id="oc-check-form" method="get" '
     'action="/api/url-inspect"></form></section>'
     '<script src="/one-off-check.js"></script>', 1),
    ("motoren leder et andet id op",    # mutation 3
     '<section id="check"><form id="cc-check-form" method="get" '
     'action="/url-to-markdown"></form></section>'
     '<script src="/net.js"></script><script src="/one-off-check.js"></script>', 1),
    ("formular uden deklareret motor",
     '<section id="check"><form id="xx-check-form" method="get" action="/x">'
     '</form></section>', 1),
    ("to formularer i #check",
     '<section id="check"><form id="oc-check-form" method="get" action="/x">'
     '</form><form id="cc-check-form" method="get" action="/y"></form></section>'
     '<script src="/net.js"></script><script src="/one-off-check.js"></script>'
     '<script src="/convert-check.js"></script>', 1),
    ("uden JavaScript: post-form",
     '<section id="check"><form id="oc-check-form" method="post" '
     'action="/api/url-inspect"></form></section>'
     '<script src="/net.js"></script><script src="/one-off-check.js"></script>', 1),
    ("uden JavaScript: intet action",
     '<section id="check"><form id="oc-check-form" method="get" action="">'
     '</form></section><script src="/net.js"></script>'
     '<script src="/one-off-check.js"></script>', 1),
    ("side uden #check er ikke en forside-fejl",
     '<section id="pricing"><form id="kontakt" method="post" action="/x">'
     '</form></section>', 0),
    ("en indre <section> lukker ikke #check for tidligt",
     '<section id="check"><form id="oc-check-form" method="get" '
     'action="/api/url-inspect"></form><section id="note"><p>hej</p></section>'
     '</section><script src="/net.js"></script>'
     '<script src="/one-off-check.js"></script>', 0),
]

MOTORTEST = [
    ("motor med sit eget fetch", GRON_MOTOR.replace(
        "NET.askGet('/api/url-inspect", "fetch('/api/url-inspect"), 1),
    ("motor der kalder ruten uden NET", GRON_MOTOR.replace(
        "NET.askGet(", "sendJson("), 1),
    ("motor der går gennem NET", GRON_MOTOR, 0),
    ("prosa der nævner en rute", "/* se /api/url-inspect og /scan-proxy */", 0),
]


def _motor_filer() -> dict[str, Path]:
    """Begge motorer, uanset hvilken form-id fixtureen bruger."""
    return {fil: SITE / fil for fil in sorted(set(MOTORER.values()))}


def selvtest() -> int:
    fejl = 0
    for navn, kilde, forventet in SELFTEST:
        fund = dom_forside(kilde, "_selftest_front_door.html", _motor_filer())
        # Findes der intet #check, er siden ikke en forside-fejl — mutationen
        # skal kunne måles på de fund den faktisk skal give.
        if SECTION.search(kilde) and not fund and forventet:
            fund = ["(porten så ingen fund)"]
        ok = len(fund) == forventet
        fejl += 0 if ok else 1
        print(f"{'ok   ' if ok else 'FEJL '} {navn} "
              f"({len(fund)} fund, forventede {forventet})")
        for f in fund:
            print(f"        {f}")

    for navn, kode, forventet in MOTORTEST:
        fund = dom_motor(kode, "_selftest_motor.js")
        ok = len(fund) == forventet
        fejl += 0 if ok else 1
        print(f"{'ok   ' if ok else 'FEJL '} {navn} "
              f"({len(fund)} fund, forventede {forventet})")
        for f in fund:
            print(f"        {f}")

    # Dom 3 skal være grøn ved at slætte motoren helt, så de virkelige filers
    # ledning dømmes her — ikke en fixture.
    for form_id, motor_fil in sorted(MOTORER.items()):
        kode = (SITE / motor_fil).read_text(encoding="utf-8", errors="replace")
        fund = dom_motor(kode, motor_fil)
        koblet = (f"getElementById('{form_id}')" in kode
                  or f'getElementById("{form_id}")' in kode)
        ok = (not fund) and koblet
        fejl += 0 if ok else 1
        print(f"{'ok   ' if ok else 'FEJL '} {motor_fil} kalder NET og leder "
              f"{form_id} op ({len(fund)} fund)"
              + ("" if koblet else "  ← leder ikke sit eget form-id"))
    n = len(SELFTEST) + len(MOTORTEST) + len(MOTORER)
    print(f"selvtest: {n - fejl}/{n} kontroller")
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
        print(f"\nfrontdør: RØD — {len(fund)} fund i forsidernes tjek")
        return 1
    print("frontdør: GRØN — hver forside med et #check har ét tjek, sin motor "
          "og NET, og motoren går gennem NET")
    return 0


if __name__ == "__main__":
    sys.exit(main())