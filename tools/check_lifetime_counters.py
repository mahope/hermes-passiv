#!/usr/bin/env python3
"""Dom at en kumulativ KV-tæller aldrig kan læses som et tal for et vindue.

**Fælden, målt 6/10.** `readKvCounter()` læser nøgler der skrives med
`expirationTtl: 365 * 86400` og genoplades ved hvert skriv. Tallet er derfor
*scanninger, ventelistepladser og assistentespørgsmål siden tælleren sidst blev
nulstillet* — det kan kun stå stille eller stige. Tre af dem stod i to svar
hvor resten af tallene er vinduesbundne:

| Rute | Læser | Vinduesbundet i samme svar | Før |
|---|---|---|---|
| `GET /api/results` | `servedScans` (`handleResults`) | `totals.runs` = `days` | `served_scans` → rettet 5/10 |
| `GET /api/stats` | `waitlist`, `aiAsks`, `scans` (`handleStats`) | `stats` = `collectTraffic(env, days)` | `waitlist`, `ai_asks`, `scans` |
| `GET /api/health` | `waitlist`, `scans` (`handleHealth`) | de fire `recent*` = `collectTraffic(env, 2)` | `waitlist`, `scans` |

**Scenariet, målt med to `curl` 6/10.** Live svarer `/api/health` med
`{"recentVisits":12, …, "scans":50}` og `/api/results` med
`served_scans_lifetime 50` — samme tæller i begge svar. `/api/health` er
**offentlig** (ingen token), så en cron læser 12 to-dages besøg og 50
scanninger i ét objekt og rapporterer «50 scanninger på to dage». Fordi
tælleren kun kan stige, ser en læser to dage og en uge senere *aldrig et
fald* — selv om scanneren er død. Det er præcis den fælde `901566c5` lukkede
i én af tre ruter og efterlod de to andre åbne.

**Reglen er skrevet på *klassen*, ikke på de tre linjer.** Hver
`readKvCounter(env, '…')` skal have en afgørelse i `AFGOJRELSE`:

* `ruter=` — feltet i hver rute der læser tælleren. Et kumulativt tal skal
  bære `_lifetime`, fordi præfikset er en del af svarets kontrakt.
* `forbudt=` — feltnavne i samme rute der ligner et vinduestal. De skal være
  væk, ellers kan en læser stadig regne dem sammen med `totals.runs`.
* `vindue=` — en *begrundelse* for at beholde det korte navn. Kun tilladt når
  nøglen faktisk er saltet, fx pr. døgn.

En `readKvCounter` der ikke står i tabellen gør porten **rød**. Det er med
vilje: en ny tæller skal have en afgørelse, ikke arve en fælde fra en nabo.
Samme mønster som afgørelseslisten i `check_net_copies.py`.

**Kommentarer dømmes ikke.** Rettelsen efterlod netop en kommentar der
fortæller, hvorfor det gamle navn var forkert — og en port der dømmer den
ville gøre den umulig at skrive. Derfor fjernes `//` og `/* … */` fra kilden,
før navnene søges.

**Den dømmer også de læsende scripts.** `tools/weekly_report.py` skrev
«Compliance-scans (total)» fra et felt der hed `scans`, og holdt en *reserve*
på det korte navn. Uden præfikset i kilden er det kun en høflighed i
rapporten; de to rå svar gør ikke. Derfor skal læserne pege på
`_lifetime`-navnet, så en worker der ikke er opdateret endnu giver `None` —
altså «ukendt» — frem for et vinduestal.

    python3 tools/check_lifetime_counters.py
    python3 tools/check_lifetime_counters.py --self-test
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROD = Path(__file__).resolve().parent.parent
WORKER = ROD / "site/_worker.js"
RAPPORT = ROD / "tools/weekly_report.py"

# Hver `readKvCounter(env, '…')` skal stå her. `felt` er det navn svaret SKAL
# bruge pr. rute, `forbudt` de navne der ligner et vinduestal, og `vindue` er
# den begrundelse der gør det tilladt at beholde et kort navn.
AFGOJRELSE: dict[str, dict] = {
    # `expirationTtl: 365 * 86400` i scanneren. Rettet 5/10 i `/api/results`
    # som `served_scans_lifetime`, 6/10 i de to øvrige ruter som
    # `scans_lifetime`.
    "csc-count": {
        "kumulativ": "365 dages TTL, genoplades ved hvert skriv — kan kun stige",
        "rapport": 'get("scans_lifetime")',
        "ruter": {
            "handleResults": "served_scans_lifetime",
            "handleStats": "scans_lifetime",
            "handleHealth": "scans_lifetime",
        },
        "forbudt": {
            "handleResults": ("served_scans",),
            "handleStats": ("scans",),
            "handleHealth": ("scans",),
        },
    },
    # Samme TTL, samme skrivemønster i ventelisteruten.
    "wl-count": {
        "kumulativ": "365 dages TTL — ventelistepladser siden tælleren blev nulstillet",
        "rapport": 'get("waitlist_lifetime")',
        "ruter": {
            "handleStats": "waitlist_lifetime",
            "handleHealth": "waitlist_lifetime",
        },
        "forbudt": {
            "handleStats": ("waitlist",),
            "handleHealth": ("waitlist",),
        },
    },
    # Samme TTL i assistenten.
    "ai-ask-count": {
        "kumulativ": "365 dages TTL — assistentespørgsmål siden tælleren blev nulstillet",
        "rapport": 'get("ai_asks_lifetime")',
        "ruter": {"handleStats": "ai_asks_lifetime"},
        "forbudt": {"handleStats": ("ai_asks",)},
    },
    # `airl-hit:${dailySalt()}` — nøglen er saltet pr. døgn, så den *er* et
    # dagsvindue og beholder sit navn. Uden saltet ville denne også være
    # kumulativ, og derfor kræver porten at nøglen ligner det.
    "airl-hit:${dailySalt()}": {
        "vindue": "saltet pr. døgn med dailySalt()",
        "ruter": {"handleStats": "ai_limited_today"},
        "forbudt": {},
    },
}

LAESNING_LITERAL = re.compile(r"readKvCounter\(\s*env\s*,\s*'([^']*)'\s*\)")
LAESNING_MAL = re.compile(r"readKvCounter\(\s*env\s*,\s*`([^`]*)`\s*\)")
# TTL'en i skrivningen. 365 dage er *nok* til at kalde tælleren kumulativ: den
# kan kun forsvinde hvis ingen har skrevet i et helt år. `LANG_TTL_DAGE` er
# grænsen — under den er nøglen et vindue, og da må den ikke hedde `_lifetime`.
LANG_TTL_DAGE = 300
TTL = re.compile(r"expirationTtl:\s*((?:\d+\s*[*]\s*)+\d+|\d+)")
# `put(<modtager>, …, { expirationTtl: … })`. Modtageren er enten nøglen
# bogstavelig eller en variabel, så porten løser begge.
PUT = re.compile(r"\bput\(\s*([^,]+),")
# Kommentarer skal ikke dømmes: rettelsen efterlod netop en kommentar der
# forklarer, hvorfor det gamle navn var forkert, og porten skal kunne holde den.
#
# Begge mønstre er **forankret i linjens start**. Det er ikke dojlighed: en løs
# `/\*.*?\*/` startede ved `'/*', ` inde i en streng i `_worker.js:750` og slugte
# 3.200 linjer kode med sig, så `csc-count`s skrivning forsvandt og porten
# meldte «tælleren er væk». En worker er ikke en tekstfil man kan strippe med
# to regexer, så kun de former der *er* skrevet med indentation i denne fil
# fjernes. En kommentar der sidder bag en klamme på linjeslid (`} catch { /* … */`)
# bliver stående — den kan ikke indeholde et feltnavn i praksis, og porten skal
# hellere overse noget end slå rødt på en ren linje.
BLOK_KOMMENTAR = re.compile(r"(?m)^[ \t]*/\*.*?\*/")
LINJE_KOMMENTAR = re.compile(r"(?m)^[ \t]*//[^\n]*")


def uden_kommentarer(kilde: str) -> str:
    """Erstat hver kommentar med lige så mange mellemrum, så linjetallet holder."""
    renset = BLOK_KOMMENTAR.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), kilde)
    return LINJE_KOMMENTAR.sub(lambda m: " " * len(m.group(0)), renset)


def funktioner(kilde: str) -> dict[str, str]:
    """Kortlæg `async function nav(…) { … }` på navn → krop, uden kommentarer."""
    ren = uden_kommentarer(kilde)
    ud: dict[str, str] = {}
    for m in re.finditer(r"(?:async\s+)?function\s+([A-Za-z0-9_]+)\s*\([^)]*\)\s*\{", ren):
        dybde, i = 0, m.end() - 1
        while i < len(ren):
            if ren[i] == "{":
                dybde += 1
            elif ren[i] == "}":
                dybde -= 1
                if dybde == 0:
                    break
            i += 1
        ud[m.group(1)] = ren[m.end():i]
    return ud


def _dage(udtryk: str) -> float:
    dage = 1.0
    for tal in re.findall(r"\d+", udtryk):
        dage *= int(tal)
    return dage / 86400


# Skrivningen er én linje i denne worker: `await env.VISITS.put(<nøgle>, …,
# { expirationTtl: … })`. Derfor dømmes den linje for linje — en løs regex over
# hele filen fandt nøgler på tværs af linjeskift, fordi `[^,]+` spiser dem.
PUT_LINJE = re.compile(r"\bput\(\s*(\w+|'[^']*'|\"[^\"]*\")\s*,")
CONST_LINJE = re.compile(r"\b(?:const|let|var)\s+(\w+)\s*=\s*('[^']*'|\"[^\"]*\")")


def skrivninger(ren: str) -> dict[str, float]:
    """Find hvilken TTL hver KV-nøgle skrives med. `cKey`-variabler opløses."""
    variabler: dict[str, str] = {}
    for linje in ren.splitlines():
        for m in CONST_LINJE.finditer(linje):
            variabler[m.group(1)] = m.group(2).strip("'\"")
        m = PUT_LINJE.search(linje)
        if not m:
            continue
        modtager = m.group(1)
        noegle = modtager.strip("'\"") if modtager[:1] in ("'", '"') \
            else variabler.get(modtager)
        ttl = TTL.search(linje[m.end():])
        if noegle and ttl:
            variabler.setdefault(f"\x00{noegle}", _dage(ttl.group(1)))
    return {k.lstrip("\x00"): v for k, v in variabler.items() if k.startswith("\x00")}


def dom(kilde: str, rapport: str = "") -> list[str]:
    """Alle fund i én workerkilde. `rapport` dømmes kun når den er læst med."""
    fund: list[str] = []
    renset = uden_kommentarer(kilde)
    fun = funktioner(kilde)

    # 1. Hver læsning skal have en afgørelse. Uden en arver den fælden fra en nabo.
    laesninger = set(LAESNING_LITERAL.findall(renset)) | set(LAESNING_MAL.findall(renset))
    for noegle in sorted(laesninger):
        if noegle in AFGOJRELSE:
            continue
        fund.append(
            f"readKvCounter(env, {noegle!r}) står ikke i AFGOJRELSE. En ny "
            f"tæller skal have en afgørelse — enten et `_lifetime`-felt pr. rute, "
            f"eller en `vindue`-begrundelse. Uden den arver den fælden fra en nabo."
        )

    # 2. Hver tæller skal hedde ret i hver rute der læser den, og de korte navne
    #    skal være væk fra *samme* rute — ellers kan en læser stadig regne dem
    #    sammen med `totals.runs`.
    for noegle, krav in sorted(AFGOJRELSE.items()):
        grund = krav.get("kumulativ") or krav.get("vindue", "")
        for rute, felt in sorted(krav["ruter"].items()):
            krop = fun.get(rute)
            if krop is None:
                fund.append(f"{rute} findes ikke i workeren — porten ved ikke "
                            f"længere, hvad den dømmer imod for {noegle!r}")
                continue
            linjer = krop.splitlines()
            # 2a. Skal læseren overhovedet finde den tæller i den rute? Hvis
            #     `ruter` er gammel, ville resten af dommen være stille grøn.
            if not re.search(rf"readKvCounter\(\s*env\s*,\s*['\`]{re.escape(noegle)}['\`]\s*\)", krop):
                fund.append(f"{rute} læser ikke {noegle!r} længere, men porten "
                            f"dømmer {felt!r} dér. Ret `AFGOJRELSE`, eller "
                            f"ryd læsningen væk.")
                continue
            # 2b. Feltet skal findes i et svarobjekt.
            if not re.search(rf"(?<![\w$]){felt}\s*:", krop):
                fund.append(f"{rute} læser {noegle!r} ({grund}) men svaret har "
                            f"ikke `{felt}:` — et kumulativt tal må ikke læses "
                            f"som et tal for vinduet")
            # 2d. Polaritet: et *dagsvindue* må ikke få `_lifetime`. Sådan hedder
            #     en tæller der er blevet kumulativ uden at nogen lagde mærke
            #     til det — og porten skal kunne se at det er sket.
            if "vindue" in krav:
                if felt.endswith("_lifetime"):
                    fund.append(f"{rute} svarer med `{felt}` for {noegle!r}, som "
                                f"kun er et {krav['vindue']} vindue — et "
                                f"vinduestal må ikke hedde `_lifetime`")
                if "dailySalt()" not in krop:
                    fund.append(f"{rute} læser {noegle!r} uden `dailySalt()` — "
                                f"så er nøglen kumulativ, og AFGOJRELSE skal "
                                f"tage den med i de kumulative")
            # 2c. De korte navne skal være væk.
            for kort in krav.get("forbudt", {}).get(rute, ()):
                for m in re.finditer(rf"(?<![\w$]){re.escape(kort)}\s*[:,}}]", krop):
                    linje = krop[:m.start()].count("\n") + 1
                    fund.append(f"{rute} svarer med `{kort}` (linje {linje}) for "
                                f"den kumulative {noegle!r} — feltet skal hedde "
                                f"`{felt}`")

    # 3. Der skal være mindst én lang skrivning pr. kumulativ tæller. En TTL
    #    på 30 dage i stedet for 365 gør `_lifetime` til en løgn, og den fejl
    #    ligger i skrivningen — ikke i det navn svaret giver. Vinduesnøglerne
    #    (alt under `LANG_TTL_DAGE`) er ikke fund; de skal bare *ikke* hedde
    #    `_lifetime`, og det dømmer punkt 2.
    skrevet = skrivninger(renset)
    for noegle, krav in sorted(AFGOJRELSE.items()):
        if "kumulativ" not in krav:
            continue
        dage = skrevet.get(noegle)
        if dage is None:
            fund.append(f"{noegle!r} er registreret som kumulativ, men der er "
                        f"ingen `put()` i workeren der skriver den — enten er "
                        f"tælleren væk, eller peger AFGOJRELSE på det forkerte navn")
        elif dage < LANG_TTL_DAGE:
            fund.append(f"{noegle!r} er registreret som kumulativ, men skrives "
                        f"med expirationTtl på {dage:.0f} dage. Under "
                        f"{LANG_TTL_DAGE} dage er nøglen et vindue, så feltet må "
                        f"ikke hedde `_lifetime`")

    # 4. Rapporten skal pege på præfikset og må ikke have en reserve på det
    #    korte navn — så en gammel worker giver «ukendt», ikke et vinduestal.
    if rapport:
        for noegle, krav in sorted(AFGOJRELSE.items()):
            laes = krav.get("rapport")
            if laes and laes not in rapport:
                fund.append(f"tools/weekly_report.py læser ikke `{laes}` — "
                            f"{noegle!r} er kumulativ, så rapporten må ikke hente "
                            f"den under et navn der ligner et vinduestal")
            for kort, linjer in krav.get("forbudt", {}).items():
                for navn in linjer:
                    if re.search(rf'get\(\s*["\']{re.escape(navn)}["\']\s*\)', rapport):
                        fund.append(f"tools/weekly_report.py har stadig en reserve "
                                    f"på `{navn}` — det gør en forældet worker "
                                    f"til et vinduestal i stedet for «ukendt»")

    return fund


def _selftest() -> int:
    fejl: list[str] = []
    kørte = 0

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        nonlocal kørte
        kørte += 1
        print(f"  {'ok  ' if sand else 'FAIL'} {navn}{'' if sand else '  ' + detalje}")
        if not sand:
            fejl.append(navn)

    den = WORKER.read_text(encoding="utf-8")
    rap = RAPPORT.read_text(encoding="utf-8")

    # 1. Den virkelige kode skal være grøn — ellers lå porten i gaten og
    #    rødmer deploys for en fejl, der ikke findes.
    fund = dom(den, rap)
    tjek("worker og rapport er grønne", not fund, "; ".join(fund[:3]))

    # 2. Mutation: de korte navne tilbage i de to ruter. Det var fundet.
    gammel = den.replace("scans_lifetime: scansLifetime", "scans: scansLifetime")
    fund = dom(gammel, rap)
    tjek("mutation: `scans` i ruterne er rød",
         any("svarer med `scans`" in f for f in fund), str(fund[:2]))

    # 3. Mutation: ét felt ad gangen. En rettelse der rammer én tæller og lader
    #    de andre stå skal være rød — det er den mutation der afslører en port
    #    der kun dømmer det felt der står først i filen.
    for noegle, krav in sorted(AFGOJRELSE.items()):
        for rute, felt in sorted(krav["ruter"].items()):
            gammelt = den.replace(f"{felt}: ", f"{felt}_glemt: ")
            fund = dom(gammelt, rap)
            tjek(f"mutation: {rute} taber feltet {felt!r} er rød",
                 any(rute in f and felt in f for f in fund),
                 str([f for f in fund if rute in f][:2]))

    # 4. Mutation: en ny tæller uden afgørelse. Sådan kommer den næste fælde.
    ny = den.replace("readKvCounter(env, 'csc-count'),",
                     "readKvCounter(env, 'ny-tæller'),", 1)
    fund = dom(ny, rap)
    tjek("mutation: en ny readKvCounter uden afgørelse er rød",
         any("står ikke i AFGOJRELSE" in f for f in fund), str(fund[:2]))

    # 5. Mutation: døgnsaltet væk. Så er nøglen ikke længere et dagsvindue, og
    #    porten skal stoppe med at tro at den er det.
    salt = den.replace("readKvCounter(env, `airl-hit:${dailySalt()}`)",
                       "readKvCounter(env, 'airl-hit:fast')")
    fund = dom(salt, rap)
    tjek("mutation: et fjernet døgnsalt er rødt",
         any("står ikke i AFGOJRELSE" in f for f in fund)
         or any("læser ikke `airl-hit" in f for f in fund), str(fund[:2]))

    # 6. Mutation: en kumulativ tællers TTL bliver et vindue. Så er
    #    `_lifetime` en løgn, og det ligger i skrivningen — ikke i navnet.
    kort = den.replace("expirationTtl: 365 * 86400", "expirationTtl: 30 * 86400", 1)
    fund = dom(kort, rap)
    tjek("mutation: en kumulativ tællers TTL bliver 30 dage er rød",
         any("skrives med expirationTtl på" in f for f in fund), str(fund[:2]))

    # 6b. Mutation: rapporten læser det korte navn og slet ikke præfikset. Det
    #     var den høflighed der holdt rapportens række heddende «(total)» mens
    #     kilden sagde noget andet.
    gammelrap = rap.replace('get("scans_lifetime")', 'get("scans")')
    fund = dom(den, gammelrap)
    tjek("mutation: rapporten der læser det korte navn er rød",
         any("læser ikke" in f for f in fund), str(fund[:2]))

    # 7. Rapporten med en reserve på det korte navn.
    reserve = rap.replace('st.get("scans_lifetime")',
                          'st.get("scans_lifetime", st.get("scans"))')
    fund = dom(den, reserve)
    tjek("mutation: rapporten med en reserve på det korte navn er rød",
         any("reserve" in f for f in fund), str(fund[:2]))

    # 8. Kommentarer skal ikke dømmes. Rettelsen efterlod netop en kommentar
    #    der forklarer, hvorfor det gamle navn var forkert — porten skal kunne
    #    holde den.
    med = den.replace("scans_lifetime: scansLifetime",
                       "scans: scansLifetime  // scans_lifetime: det rigtige navn")
    fund = dom(med, rap)
    tjek("mutation: en kommentar der nævner det gamle navn dømmes ikke",
         all("kommentar" not in f for f in fund), str([f for f in fund if "kommentar" in f][:2]))

    for linje in fejl:
        print(f"  FEJL {linje}")
    print(f"lifetime-counters-selftest: {'OK' if not fejl else 'RØD'} "
          f"({kørte - len(fejl)}/{kørte} kontroller)")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true",
                    help="kør portens egen kontrol af sig selv")
    args = ap.parse_args(argv)

    if args.self_test:
        return _selftest()

    fund = dom(WORKER.read_text(encoding="utf-8"), RAPPORT.read_text(encoding="utf-8"))
    for linje in fund:
        print(linje)
    if fund:
        print(f"\nlifetime-counters: RØD — {len(fund)} fund. En kumulativ "
              f"tæller uden `_lifetime` kan læses som et tal for et vindue.")
        return 1

    kum = sorted(k for k, v in AFGOJRELSE.items() if "kumulativ" in v)
    vind = sorted(k for k, v in AFGOJRELSE.items() if "vindue" in v)
    ruter = sum(len(v["ruter"]) for v in AFGOJRELSE.values())
    print(f"lifetime-counters: GRØN — {len(kum)} kumulative KV-tællere "
          f"({', '.join(kum)}) bærer `_lifetime` i {ruter} ruter, "
          f"{len(vind)} døgnsaltet bevarer sit navn, og rapporten læser "
          f"præfikset uden reserve")
    return 0


if __name__ == "__main__":
    sys.exit(main())