#!/usr/bin/env python3
"""Dom at ingen side lover, at et menneske frigør en plads — og at den der
gør, rent faktisk gør det.

Målt 3/10 på `site/`:

  - `site/license-lookup.html` skrev «Moving to a new computer? Deactivate the
    key in the old install first — **it is one click in the app** — or write to
    support@mahope.tools and **we free up the seat**». Begge halve er falske.
    Den første fordi de to betalte desktop-apps (`mahope/transmute` v0.2.1,
    `mahope/deskuptime` desktop-v0.2.7) ringer stadig til
    `api.lemonsqueezy.com`, så de har ingen deaktiveringsknap overhovedet — målt
    i de shippede binære, se ❓ i planen. Den anden fordi den er præcis den
    menneskelige indsats missionen forbyder: missionen spørger «tjener det stadig
    penge, når Mads rejser væk i tre måneder?», og en kunde der rammer
    «Device limit reached» på sin fjerde maskine kan kun skrive til ham.
  - `grep -rn "license/deactivate" uden for _worker.js` gav **én** træffer, og den
    var i `tests/stripe-worker.test.mjs`. Ruten virkede, var testet, og ingen
    side, klient eller dokument kaldte den.

Hvorfor en listering og ikke bare «tryk denne knap»: `device_id` er en
maskineidentitet **klienten selv danner** — `uuid4().hex` i
`site/downloads/page-profile/page_profile.py:1040`, `cc-<random>` i
`site/clean-copy-tool.html:613`, sitets hostname i WordPress-plugin'en. Ingen
kunde kan gætte den, så en knap der beder om en maskine *navn* kan ikke virke.
Derfor lister `/api/license/devices` de maskiner nøglen sidder på med deres
første og seneste brug, og frigørelsen går gennem den **allerede testede**
`/api/license/deactivate`.

**Hvad porten dømmer.** Pr. side i `site/` for løftet om menneskelig hjælp, og
så i `site/license-lookup.html` og `site/_worker.js` for mekanikken:

  1. `HUMAN_PROMISE`   siden lover at *vi* frigør pladsen, eller at appen
                       gør det i ét klik. Det er det løfte, der lå.
  2. `NO_LISTING`      siden kalder ikke `/api/license/devices`.
  3. `NO_RELEASE`      siden kalder ikke `/api/license/deactivate`.
  4. `UNGUARDED_SUCCESS`  siden siger «Machine freed» uden at se på
                       serverens `deactivated`. Det er den fare, der lærer op:
                       en `.then()` der antager at et 200 er en succes, så
                       kunden får besked om en frigjort plads, der ikke blev
                       frigjort, og prøver igen på den samme maskine.
5. `ROUTE_MISSING` / `ROUTE_NOT_POST` / `ROUTE_UNAUTHED`  workerens rute
                        mangler, svarer på GET, eller læser ikke nøglen.
  6. `SEAT_COUNT` / `SEAT_COUNTS_MISSING`  antallet i «Free up a machine» er
                        ikke katalogens `max_devices` for det produkt, eller et
                        licensprodukt mangler i listen.
  7. `ROUTE_UNLIMITED`  ruten `/api/license/devices` har ingen tæller.

Dom 4 er skrevet som en ** kontrol på strukturen**, ikke på en sætning: den
leder efter `deactivated` i den funktion der frigør, og en `return` der afbryder
inden succesteksten. Så kan copy'en skrives om, men dommen kan ikke gå grøn
på en side der lyver.

Dom 6 er målt på den sætning porten lå på 3/10: «three on DeskUptime Pro and
Transmute Desktop, **two websites on EUComply Pro, five elsewhere**». Den var
rigtig for to produkter og **forkert for to** — EUComply Pro har
`max_devices: 1` (ganges med antal købte websites ved checkout) og Page Profile
Pro har 3, ikke «five elsewhere». `/compliance-report`, `/pricing` og
`/page-profile` sagde alle tre modsatte af den, på den side kunden netop åbner
fordi de har ramt «Device limit reached». Derfor skriver siden nu **tal**, ikke
ord, og hvert tal er bundet til sin `product_key` med `data-seat-product`, så
dommen læser katalogen og den synlige tekst — ikke en håndskrevet liste.

Dom 7 er målt på review 3/10: de otte øvrige licens- og scanningsruter kalder
`rateLimitIp`, og `/api/license/lookup` har sin egen tæller på 10/time pr. IP —
mens `/api/license/devices`, den rute der netop skal findes i en browser, lå på
samme flade uden. Det er ikke et datalæk (nøglen er 128 bit), men en ubremse
forstærker af vores egen worker-kvota, som alle fire domæner deler.

    python3 tools/check_license_seat_release.py
    python3 tools/check_license_seat_release.py --list
    python3 tools/check_license_seat_release.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
SIDE = SITE / "license-lookup.html"
WORKER = SITE / "_worker.js"
CATALOG = ROOT / "tools" / "stripe_catalog.json"

# Dom 1. Løfter om at et menneske eller en knap i appen gør arbejdet for
# kunden. `we free|free up|release … the seat` er den sætning der lå, og
# `one click in the app` er den anden løftede halv — begge er hentet ordret fra
# den gamle side, så porten ikke kan have tilpasset sig dem.
HUMAN_RE = re.compile(
    r"(we\s+(?:will\s+|can\s+|would\s+)?(?:free|release|clear|deactivate)"
    r"|vi\s+(?:frigør|frigiver|frilæser|fritager)"
    r"|one\s+click\s+in\s+the\s+app"
    r"|ét\s+klik\s+i\s+appen"
    r"|we\s+free\s+up\s+the\s+seat)", re.I)

DEVICES_KALD_RE = re.compile(r"/api/license/devices")
DEACTIVATE_KALD_RE = re.compile(r"/api/license/deactivate")
# Dom 4. Funktionen der frigør en plads skal *læse* serverens `deactivated`
# og afbryde, før den skriver succesteksten. `deactivated` er feltnavnet i
# `docs/stripe-kontrakt.md` og i `site/_worker.js`, så det er det samme ord
# hele vejen — en side der opfinder sit eget feltnavn ville heller ikke få
# serverens svar.
DEACTIVATED_LÆST_RE = re.compile(r"\bdeactivated\b")
AFBRYD_RE = re.compile(r"\breturn\b")
# Dom 6. Hvert antal på siden er en `<span data-seat-product="…">` med **tal**
# i teksten. Ord-formen («three on …») lå i den gamle sætning, og den er
# umulig at dømme uden en ord-tabel; tallene kan dømmes mod katalogen, og det er
# det samme tal `max_devices` ganges med i workerens egen nøgletabel.
SEAT_SPAN_RE = re.compile(
    r"""<span[^>]*data-seat-product=["']([^"']+)["'][^>]*>([\s\S]*?)</span>""", re.I)
# Dom 7. Egen `rl:`-tæller i handleren (som `handleLicenseLookup` har) eller et
# `rateLimitIp`-kald med sit eget scope.
TÆLLER_RE = re.compile(r"rateLimitIp\s*\(\s*request\s*,\s*env\s*,|rl:")


def funktion_der_frigør(js: str) -> str:
    """Kroppen af den funktion der kalder `/api/license/deactivate`.

    Tager den tekst fra `function` frem for den kalder, så dommen gælder den kode
    der beskriver frigørelsen — ikke hele siden, hvor et kald et andet sted ville
    give grønt kort.

    Kroppen findes ved at gå **baglæns** fra kaldet til den omsluttende `{` og
    frem igen til dens match. Det er nødvendigt, fordi kaldet på den rigtige side
    ligger bag en linje som `function (b) { b.disabled = true; }` — en
    engangsfunktion, som en linjevis fremad-tælling ville stoppe ved, så dommen
    ville se en tom krop og være grøn på præcis den fejl den er skrevet for.
    """
    i = js.find(DEACTIVATE_KALD_RE.pattern)
    if i < 0:
        return ""
    åbne = -1
    dybde = 0
    for p in range(i, -1, -1):
        c = js[p]
        if c == "}":
            dybde += 1
        elif c == "{":
            if dybde == 0:
                åbne = p
                break
            dybde -= 1
    if åbne < 0:
        return js[max(0, i - 800) : i + 800]
    dybde = 0
    luk = len(js)
    for p in range(åbne, len(js)):
        c = js[p]
        if c == "{":
            dybde += 1
        elif c == "}":
            dybde -= 1
            if dybde == 0:
                luk = p + 1
                break
    f = js.rfind("function", 0, åbne)
    return js[f if f >= 0 else åbne : luk]


def krop_rundt_om(js: str, navn: str) -> str:
    """Kroppen af `async function <navn>(…)` i workeren.

    Adskiller fra `funktion_der_frigør`, der leder efter et *kald* — her skal
    dommen gælde hele handleren, også den kode der står før det kald den leder
    efter. Signaturen findes sidst (`rfind`), fordi routeren ovenfor også
    nævner handlerens navn, og kroppen åbnes ved den første `{` efter den.
    """
    i = js.rfind(f"async function {navn}")
    if i < 0:
        return ""
    åbne = js.find("{", i)
    if åbne < 0:
        return ""
    dybde = 0
    for p in range(åbne, len(js)):
        c = js[p]
        if c == "{":
            dybde += 1
        elif c == "}":
            dybde -= 1
            if dybde == 0:
                return js[åbne : p + 1]
    return js[åbne:]


def licensprodukter(katalog: Path = CATALOG) -> dict[str, dict]:
    """Produkterne med `kind: license` og deres `max_devices`.

    Katalogen er den ene kilde alle nøgleformler skriver ud fra
    (`max_devices: product.maxDevices * qty`), så et tal på siden skal kunne
    læses derfra — ellers er dommen en håndskrevet liste, der bliver grøn for
    sig selv.
    """
    data = json.loads(katalog.read_text(encoding="utf-8"))
    produkter = data.get("products", {})
    return {
        nøgle: v for nøgle, v in produkter.items()
        if isinstance(v, dict) and v.get("kind") == "license" and isinstance(v.get("max_devices"), int)
    }


def dom_antal(side: Path, katalog: Path = CATALOG) -> list[str]:
    """Dom 6: antallet i «Free up a machine» er katalogens egne."""
    where = sti(side, SITE)
    if not katalog.is_file():
        return [f"KATALOG_MISSING i {sti(katalog, ROOT)}: dommen kan ikke læse "
                f"`max_devices`, så antallet på {where} er udokumenteret."]
    produkter = licensprodukter(katalog)
    html = side.read_text(encoding="utf-8", errors="replace") if side.is_file() else ""
    fund: list[str] = []
    sette: dict[str, str] = {}
    for nøgle, indhold in SEAT_SPAN_RE.findall(html):
        sette[nøgle] = " ".join(indhold.split())

    for nøgle, tekst in sorted(sette.items()):
        produkt = produkter.get(nøgle)
        antal = produkter[nøgle]["max_devices"] if produkt is not None else None
        navn = (produkt or {}).get("name", nøgle)
        if produkt is None:
            fund.append(
                f"SEAT_COUNT i {where}: «{tekst}» er skrevet for produktet "
                f"`{nøgle}`, som ikke findes i katalogen som licensprodukt. "
                f"Tallet kan så ikke måles mod `max_devices`."
            )
            continue
        # EUComply Pro sælges pr. website, så «1 per website on EUComply Pro» er
        # den ærlige sætning — ordet kommer fra katalogens egen `price_note`, så
        # det ikke er en undtagelse, der kan miste mellem den og siden. Og for
        # det produkt er «1 on EUComply Pro» **ikke** samme oplysning: kunden har
        # købt websites, og to købte websites giver to pladser, så «per website»
        # skal med. Derfor er der kun én tilladt form pr. website-produkt.
        pr_side = bool(re.search(r"per website", str(produkt.get("price_note", "")), re.I))
        Former = [f"{antal} per website on {navn}"] if pr_side else [f"{antal} on {navn}"]
        if tekst not in Former:
            fund.append(
                f"SEAT_COUNT i {where}: «{tekst}» skal være en af "
                f"{' / '.join(repr(f) for f in Former)} — `max_devices` for "
                f"`{nøgle}` er {antal} i {sti(katalog, ROOT)}"
                + (" og sælges pr. website, så «per website» hører med."
                   if pr_side else ".")
            )
    mangler = [f"{n} ({p['name']}: {p['max_devices']})" for n, p in sorted(produkter.items()) if n not in sette]
    if mangler:
        fund.append(
            f"SEAT_COUNTS_MISSING i {where}: «Free up a machine» nævner ikke "
            f"{len(mangler)} af de {len(produkter)} licensprodukter: "
            f"{', '.join(mangler)}. Kunden skal kunne regne ud hvor mange pladser "
            f"deres eget produkt har — ellers står de med «five elsewhere»."
        )
    return fund


def dom_tæller(side: Path, worker: Path) -> list[str]:
    """Dom 7: ruten har en time-tæller pr. IP med sit eget scope."""
    js = worker.read_text(encoding="utf-8", errors="replace") if worker.is_file() else ""
    krop = krop_rundt_om(js, "handleLicenseDevices")
    if not krop:
        return []  # ROUTE_MISSING dømmer den manglende rute.
    if not TÆLLER_RE.search(krop):
        fund = [
            "ROUTE_UNLIMITED i site/_worker.js: handleLicenseDevices kalder hverken "
            "`rateLimitIp` eller sin egen `rl:`-tæller, så ruten er ubremset for "
            "et script. Målt 3/10: de otte øvrige licens- og scanningsruter har "
            "alle en tæller, og `/api/license/lookup` — samme nøgle-flade, samme "
            "menneskelige bruger — har sin egen på 10/time pr. IP. Alle fire "
            "domæner deler samme worker, så en løbet kvote tager også "
            "/api/license/validate med, altså den rute betalende kunder bruger."
        ]
        return fund
    return []


def dom_loefter(mappe: Path) -> list[str]:
    """Dom 1 pr. HTML-side i `mappe`."""
    fund: list[str] = []
    for fil in sorted(mappe.rglob("*.html")):
        tekst = fil.read_text(encoding="utf-8", errors="replace")
        for m in HUMAN_RE.finditer(tekst):
            start = max(0, m.start() - 60)
            snippet = " ".join(tekst[start : m.end() + 60].split())
            fund.append(
                f"HUMAN_PROMISE i {sti(fil, mappe)}: «{snippet}» lover at et "
                f"menneske (eller en knap i appen) frigør pladsen. Kunden skal "
                f"kunne gøre det selv — /license-lookup har en «Free up a "
                f"machine»-sektion der frigør pladsen med det samme."
            )
    return fund


def dom_mekanik(side: Path, worker: Path) -> list[str]:
    """Dom 2–5 på selve siden og workerens rute."""
    fund: list[str] = []
    html = side.read_text(encoding="utf-8", errors="replace") if side.is_file() else ""
    js = worker.read_text(encoding="utf-8", errors="replace") if worker.is_file() else ""
    where = sti(side, SITE)

    if not DEVICES_KALD_RE.search(html):
        fund.append(
            f"NO_LISTING i {where}: siden kalder ikke /api/license/devices, så "
            f"kunden kan ikke se hvilke maskiner nøglen sidder på. Uden listen "
            f"kan ingen frigøre en plads — `device_id` danner klienten selv."
        )
    if not DEACTIVATE_KALD_RE.search(html):
        fund.append(
            f"NO_RELEASE i {where}: siden kalder ikke /api/license/deactivate, "
            f"så «Free up a machine» gør ingenting. Ruten er testet i "
            f"tests/stripe-worker.test.mjs — den skal bruges."
        )

    krop = funktion_der_frigør(html)
    if krop:
        uden_afbryd = False
        if not DEACTIVATED_LÆST_RE.search(krop):
            fund.append(
                f"UNGUARDED_SUCCESS i {where}: frigørelsen læser ikke serverens "
                f"`deactivated`. Et 200 er ikke en succes — serveren svarer 200 "
                f"med `deactivated: false` når maskinen ikke sad på nøglen, og "
                f"siden må ikke sige at pladsen er fri i så fald."
            )
        else:
            # `deactivated` skal væregateret for succesteksten: en `return` der
            # afbryder, **inden** den første succestekst. Måles på rækkefølgen,
            # så en ny sætning enten kan flyttes foran afbrydningen eller slås
            # sammen med den.
            i_læs = krop.find("deactivated")
            i_succes = min(
                [p for p in (krop.find("Machine freed"), krop.find("Machine freed.")) if p >= 0]
                or [-1]
            )
            hvis_succes_er_efter = i_succes < 0 or i_succes < i_læs
            afbryder_mellem = AFBRYD_RE.search(krop, i_læs, i_succes if i_succes > 0 else len(krop))
            uden_afbryd = hvis_succes_er_efter or afbryder_mellem is None
            if uden_afbryd:
                fund.append(
                    f"UNGUARDED_SUCCESS i {where}: succesteksten skrives uden en "
                    f"`return` der afbryder, når serverens `deactivated` ikke er "
                    f"true. Se dommen overfor."
                )

    if not re.search(r"['\"]?/api/license/devices['\"]?\s*\)\s*return\s+handleLicenseDevices", js):
        fund.append(
            "ROUTE_MISSING i site/_worker.js: der er ingen rute til "
            "/api/license/devices, så listeringen svarer 404 og siden kan "
            "intet vise. Ruten skal være `POST`-only og kræve `license_key`."
        )
    else:
        if not re.search(r"handleLicenseDevices[\s\S]{0,900}request\.method\s*!==\s*'POST'", js):
            fund.append(
                "ROUTE_NOT_POST i site/_worker.js: /api/license/devices svarer "
                "ikke kun på POST. GET må ikke ændre noget, og en listering må "
                "ikke kunne ligge i en link-scanner."
            )
        if not re.search(r"handleLicenseDevices[\s\S]{0,1400}\^\[a-f0-9\]\{32\}\$", js):
            fund.append(
                "ROUTE_UNAUTHED i site/_worker.js: /api/license/devices læser "
                "ikke nøglen. Adgangskravet er `license_key` — nøglen er den "
                "hemmelighed hele licensemodellen bygger på, ikke ordreference "
                "og mail."
            )
    return fund


def sti(fil: Path, root: Path) -> str:
    """Sidens sti som den skal læses i en fejlmeddelelse."""
    try:
        return str(fil.relative_to(ROOT))
    except ValueError:
        return str(fil)


def dom(mappe: Path | None = None, side: Path | None = None, worker: Path | None = None) -> list[str]:
    fund = dom_loefter(mappe if mappe is not None else SITE)
    s = side if side is not None else SIDE
    w = worker if worker is not None else WORKER
    fund += dom_mekanik(s, w)
    fund += dom_antal(s)
    fund += dom_tæller(s, w)
    return fund


def self_test() -> int:
    fejl: list[str] = []
    talt = [0]

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        talt[0] += 1
        if not sand:
            fejl.append(f"{navn}{': ' + detalje if detalje else ''}")

    # Den korte, sande side: lister, frigør, oggater succesteksten.
    GOD_SIDE = """<html><body>
<form id="seatForm"><input id="seatKey"><button id="seatListBtn">Show</button></form>
<ul id="seatList" hidden></ul>
<script>
function frigør(deviceId, knap) {
  hent('/api/license/devices', { license_key: nøgle }).then(function (y) { tegn(y); });
  hent('/api/license/deactivate', { license_key: nøgle, device_id: deviceId }).then(function (x) {
    if (x.status !== 200 || !x.data || x.data.deactivated !== true) { seatSay('nej', 'error'); return; }
    seatSay('Machine freed. ' + x.data.devices_in_use + ' machines are still on this key.', null);
  });
}
</script></body></html>"""

    def døm_loefter(html: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            rod = Path(tmp)
            (rod / "license-lookup.html").write_text(html, encoding="utf-8")
            return dom_loefter(rod)

    def døm(side_html: str, worker_src: str = "") -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            rod = Path(tmp)
            (rod / "license-lookup.html").write_text(side_html, encoding="utf-8")
            (rod / "_worker.js").write_text(worker_src, encoding="utf-8")
            return dom_loefter(rod) + dom_mekanik(rod / "license-lookup.html", rod / "_worker.js")

    def døm_antal(side_html: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "license-lookup.html"
            f.write_text(side_html, encoding="utf-8")
            return dom_antal(f)

    def døm_tæller(worker_src: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "_worker.js"
            f.write_text(worker_src, encoding="utf-8")
            return dom_tæller(Path(tmp) / "license-lookup.html", f)

    # Dom 6. Den gode antalsætning bygges **af katalogen**, så selvtesten ikke
    # kan have et håndskrevet tal, der bliver grøn for sig selv. Den er lavet på
    # samme måde som den rigtige side: `<span data-seat-product>` med tallet i
    # teksten, og «per website» kun for det produkt katalogens `price_note` siger
    # sælges pr. website.
    def spans_fra_katalog() -> str:
        dele = []
        for nøgle, produkt in sorted(licensprodukter().items()):
            pr_side = bool(re.search(r"per website", str(produkt.get("price_note", "")), re.I))
            mellem = f"{produkt['max_devices']}{' per website' if pr_side else ''} on {produkt['name']}"
            dele.append(f'<span class="seat-limit" data-seat-product="{nøgle}">{mellem}</span>')
        return "<p>Your key works on a set number of machines — " + ", ".join(dele) + ".</p>"

    GOD_ANTAL = spans_fra_katalog()

    # 1. Dom 1 fanger præcis de to løfter der lå i `site/`, ordret som de stod.
    tjek("dom 1 fanger «we free up the seat»",
         any("HUMAN_PROMISE" in f for f in døm_loefter("<p>or write to support@mahope.tools and we free up the seat.</p>")))
    tjek("dom 1 fanger «one click in the app»",
         any("HUMAN_PROMISE" in f for f in døm_loefter("<p>Deactivate the key in the old install first — it is one click in the app.</p>")))
    tjek("dom 1 fanger den danske form",
         any("HUMAN_PROMISE" in f for f in døm_loefter("<p>skriv til os, så vi frigør pladsen.</p>")))
    # 2. Mutation: de sider der **ikke** lover menneskelig hjælp må ikke blive
    #    røde. De er hentet fra de filer porten skal lade være i fred.
    for ren in (
        "<p>Write to <a href=\"mailto:support@mahope.tools\">support@mahope.tools</a> with the email you paid with.</p>",
        "<p>Looking up your key is free. If it saved you a reply to support, a small donation keeps the free tools running.</p>",
        "<p>A machine that is still in use keeps working after you free a different one.</p>",
        "<p>The free version cannot hand you the annexes. The paid template ships them.</p>",
    ):
        tjek(f"ren tekst bliver ikke rød: {ren[:44]}…", not døm_loefter(ren))

    # 3. Den gode side er grøn på alle fire domme i `site/`.
    fund = døm(GOD_SIDE, GOD_WORKER)
    tjek("den gode side er grøn", not fund, " | ".join(fund))

    # 4. Polaritet: hver dom skal være rød, når præcis dens ting mangler.
    tjek("NO_LISTING er rød når listeringen mangler",
         any("NO_LISTING" in f for f in døm(GOD_SIDE.replace("/api/license/devices", "/api/naet-kun"), GOD_WORKER)))
    tjek("NO_RELEASE er rød når frigørelsen mangler",
         any("NO_RELEASE" in f for f in døm(GOD_SIDE.replace("/api/license/deactivate", "/api/naet-kun"), GOD_WORKER)))
    tjek("UNGUARDED_SUCCESS er rød uden serverens svar",
         any("UNGUARDED_SUCCESS" in f for f in døm(
             GOD_SIDE.replace("if (x.status !== 200 || !x.data || x.data.deactivated !== true) { seatSay('nej', 'error'); return; }\n    ", "")
                  .replace("!x.data.deactivated !== true", "true"),
             GOD_WORKER)))
    tjek("UNGUARDED_SUCCESS er rød når feltet ikke læses",
         any("UNGUARDED_SUCCESS" in f for f in døm(GOD_SIDE.replace("deactivated", "ok"), GOD_WORKER)))
    tjek("ROUTE_MISSING er rød uden rute",
         any("ROUTE_MISSING" in f for f in døm(GOD_SIDE, "")))
    tjek("ROUTE_NOT_POST er rød på en GET-rute",
         any("ROUTE_NOT_POST" in f for f in døm(
             GOD_SIDE, GOD_WORKER.replace("if (request.method !== 'POST')", "if (false)"))))
    tjek("ROUTE_UNAUTHED er rød uden nøgletjek",
         any("ROUTE_UNAUTHED" in f for f in døm(
             GOD_SIDE, GOD_WORKER.replace("/^[a-f0-9]{32}$/", "/^.*$/"))))

    # 5. Dom 6 og 7. Den gode antalsætning er bygget af katalogen ovenfor, så
    #    dommen kan kun være grøn fordi den læser den rigtige kilde.
    tjek("dom 6: antallet fra katalogen er grønt", not døm_antal(GOD_ANTAL), " | ".join(døm_antal(GOD_ANTAL)))
    tjek("dom 6: EUComply Pro skal sige 1 pr. website, ikke 2",
         "eucomply-pro\">1 per website on EUComply Pro" in GOD_ANTAL, GOD_ANTAL)
    tjek("SEAT_COUNT er rød på «two websites on EUComply Pro» — den gamle tekst",
         any("SEAT_COUNT" in f for f in døm_antal(
             GOD_ANTAL.replace("1 per website on EUComply Pro", "two websites on EUComply Pro"))))
    tjek("SEAT_COUNT er rød på «five elsewhere» for Page Profile Pro",
         any("SEAT_COUNT" in f for f in døm_antal(
             GOD_ANTAL.replace(">3 on Page Profile Pro", ">5 on Page Profile Pro"))))
    tjek("SEAT_COUNT er rød når «per website» mangler på det pr. website-produkt",
         any("SEAT_COUNT" in f for f in døm_antal(
             GOD_ANTAL.replace("1 per website on EUComply Pro", "1 on EUComply Pro"))))
    tjek("SEAT_COUNT er rød på et produkt der ikke findes i katalogen",
         any("SEAT_COUNT" in f for f in døm_antal(
             GOD_ANTAL.replace('data-seat-product="deskuptime-pro"', 'data-seat-product="opfindet-produkt"'))))
    tjek("SEAT_COUNTS_MISSING er rød når et produkt mangler i listen",
         any("SEAT_COUNTS_MISSING" in f for f in døm_antal(
             re.sub(r'<span class="seat-limit" data-seat-product="transmute-desktop">[\s\S]*?</span>', '', GOD_ANTAL))))
    tjek("dom 7: handleren med tæller er grøn", not døm_tæller(GOD_WORKER), " | ".join(døm_tæller(GOD_WORKER)))
    tjek("ROUTE_UNLIMITED er rød uden tæller — den gamle handler",
         any("ROUTE_UNLIMITED" in f for f in døm_tæller(GOD_WORKER_UDEN_TÆLLER)))
    tjek("ROUTE_UNLIMITED er rød når kun routerens egen tæller findes i filen",
         any("ROUTE_UNLIMITED" in f for f in døm_tæller(
             GOD_WORKER_UDEN_TÆLLER + "\nasync function handleAndet(request, env) { return rateLimitIp(request, env, 'x', 5); }")))

    print(f"self-test: {talt[0] - len(fejl)}/{talt[0]}")
    for f in fejl:
        print(f"FEJL: {f}")
    return 1 if fejl else 0


GOD_WORKER = """if (path === '/api/license/devices') return handleLicenseDevices(request, env);
async function handleLicenseDevices(request, env) {
  if (request.method !== 'POST') { return jsonResp({ ok: false, error: 'POST only' }, 405); }
  const limited = await rateLimitIp(request, env, 'license-devices', 30);
  if (limited) { return jsonResp({ ok: false, error: 'Too many machine lookups this hour.' }, 429); }
  const key = String(body.license_key || '').trim().toLowerCase();
  if (!/^[a-f0-9]{32}$/.test(key)) { return jsonResp({ ok: false, error: 'Invalid license key format.' }, 400); }
}"""

# Den handler som lå i `site/_worker.js` 3/10, ordret som den lå: POST-only,
# nøgletjek, ingen tæller. Den er nævnt i docstringens dom 7 og bruges som
# mutation — porten skal være rød på den.
GOD_WORKER_UDEN_TÆLLER = """if (path === '/api/license/devices') return handleLicenseDevices(request, env);
async function handleLicenseDevices(request, env) {
  if (request.method !== 'POST') { return jsonResp({ ok: false, error: 'POST only' }, 405); }
  const key = String(body.license_key || '').trim().toLowerCase();
  if (!/^[a-f0-9]{32}$/.test(key)) { return jsonResp({ ok: false, error: 'Invalid license key format.' }, 400); }
}"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--self-test", action="store_true", help="kør portens egen test")
    p.add_argument("--list", action="store_true", help="skriv portens kommando til stdout")
    args = p.parse_args(argv)

    if args.list:
        print("python3 tools/check_license_seat_release.py")
        return 0
    if args.self_test:
        return self_test()

    fund = dom()
    if fund:
        print("license-seat-release: RØD")
        for f in fund:
            print(f"  - {f}")
        return 1
    print("license-seat-release: GRØN — ingen side lover menneskelig hjælp, og "
          "/license-lookup frigør pladsen selv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
