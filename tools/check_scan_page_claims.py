#!/usr/bin/env python3
"""Dom at `/scan`s sider og ruter taler om det **samme** antal sider.

**Hullet (målt 6/10, review-fund MIDDEL).** `a4277574` gjorde `/scan-proxy`
flersidet og lagde den begrundelse ind som en kommentar over
`SCAN_PROXY_MAX_URLS`:

    «Fem er samme tal som `/api/compliance-scan` tager, så de to ruter ikke
    kan sammenlignes på hvor meget én besøger får pr. klik.»

**Begge halve er usande.** Målt på koden, ikke læst:

  * `CSC_MAX_PAGES = 12` (`site/_worker.js:3681`) med kommentaren «samlet
    budget for hele kaldet», og den bruges både som samlet loft
    (`cscBudget(CSC_MAX_PAGES)`) og som fordeler i
    `Math.floor(CSC_MAX_PAGES / antal)` (`cscBudgetAndele`). Summen pr. kald
    er præcis 12. Den betalte rute tager altså **12**, ikke 5.
  * De to ruter er **allerede** ulige på en anden måde, som er den egentlige
    og målbare forskel: `/scan-proxy` læser **præcis den side du skrev** —
    `handleScanProxy` kalder `scanProxyReadPage` én gang pr. linje og følger
    ingen links — mens `/api/compliance-scan` læser forsiden og følger de
    links, der peger på de juridiske sider. Det er derfor pro-kortet på
    `/scan` siger «It crawls the whole site».

Så var kommentarens begrundelse for tallet 5 ikke bare unødigt lang — den
påstand den skulle bære, var **falsk**, og den stod i en produktionskritisk
fil. Det værre er, at ingen port kunne se den: `check_catalog_where` dømmer
linjer og citater, `check_pro_table` dømmer tabellen mod katalogen, og
`check_inline_js` dømmer JS-mønstre. Ingen af dem læser et **antal** i en
kommentar mod **samme antal** i koden.

**Hvad porten dømmer.** Fire domme, og de er alle sammen om tal der står i
to steder og skal være ens:

  1. **Konstanterne skal findes og være tal.** `SCAN_PROXY_MAX_URLS` og
     `CSC_MAX_PAGES` læses ud af `site/_worker.js` med ét regex. Uden dem
     ville resten af dommene være grønne ved at slå alt sammen, så det er
     den første fejl, der kommer.
  2. **De to tal må ikke være lige, hvis kommentaren siger de er.** Og mere
     vigtigt: **kommentaren må ikke påstå lighed mellem dem overhovedet.**
     Det er præcis den fejl, fundet beskriver — en kommentar der siger «samme
     tal», som ingen port kan holde sand. Ligegyldigt om tallene en dag bliver
     ens: påstanden skal kunne efterprøves, så den skal pege på tallene.
  3. **Klientens synlige tekst skal nævne det samme antal som konstanten.**
     `site/scan.html` siger «up to 5 pages» i sit felt-label, og
     `site/scan-da.html` «op til 5 sider». Hæver nogen `SCAN_PROXY_MAX_URLS`
     til 6, skal porten blive rød, fordi teksten ikke længer svarer til det
     værktøjet gør. Ordformene dømmes på **tallet** («5», «fem», «five»),
     så en ny sætning på dansk eller engelsk ikke fejler på grund af sprog.
  4. **Pro-kortet må ikke love en flersidet-rute, der ikke findes.** Her er
     den anden målte sandhed, og den er den største: **`/api/report` — den
     rute en betalt licens låser op — kalder `cscFetch` præcis én gang.**
     Målt ved at køre den rigtige worker med en gyldig nøgle i en falsk KV og
     en stub-fetch: ét ude-kald, `findings` med 18 fund-typer. Den læser én
     side og ser dens **response-headere** (`SEC_HSTS`, `SEC_CSP`), som et
     browser-side DOM-tjek aldrig kan se. Den crawler ikke.
     «It crawls the whole site» stod i **18** kort på **9** sider, og ingen
     af dem var sande for den rute licensen låser. Porten tæller derfor de
     `cscFetch(`-kald i `handleReport` og kræver at **pro-kortet** på `/scan`
     og `/scan-da` ikke bruger et krybende verb.

     Dommen læser **kun kortet**, ikke hele siden, og det er en målt afgrønsning
     ikke en bekvemmelighed: `/scan` har også en sektion om desktop-appen
     (`scan.html:169`), der *skal* sige «crawl hele sitet op til 200 sider» —
     det er et andet program med sin egen krybning, og det er sandt for det.
     Samme for `/scan-da.html:166`. En port der dømte hele filen ville være
     rød på en sand påstand, og så ville den blive slået fra.

Målt på den kode, porten skal dømme — altså `origin/main` **før** denne
     commit: **6 fund**. Ikke to af dem tilfældige: kommentaren siger «samme tal»
     mellem to ruter, hvis tal er 5 og 12, og den peger på **intet** af dem; og
     pro-kortet på begge sprog lover «crawls the whole site» / «gennemgår hele
     sitet» om den rute, `handleReport` henter **én** side fra. De to sidste fund
     er den egentlige læring: de ville være fundet, **fordi de er usande** — ikke
     fordi en tekstform var forældet.

**Dom 5 (6/10) — samme dom over *alle* kortene, ikke kun de to.** Dom 4 læste
     `proCard()` på `/scan` og `/scan-da`, fordi det var de to sider med et
     håndskrevet kort. Målt på den færdige fil: «It crawls the whole site» /
     «Den gennemgår hele sitet» stod i **16** kort på **9** sider — dom 4 så to
     af dem. De anden syv lå i `tools/stripe_catalog.json`, som er den fælles
     sandhed for alle **21** pro-blokke (`pro_table.py` tegner dem derfra), så
     dommen læser nu katalogen i stedet for filerne. Rettet på alle ni sider, og
     hver fik **sin egen** ærlige sætning, fordi de frie værktøjer ikke er ens:
     `/scan` og `contrast-checker` læser slet ingen side i browseren, så Pro
     læser den fra serveren; `cookie-check` læser kilden, så Pro læser også
     svarheaderne; `security-headers-check` læser kun headerne, så Pro læser
     kilden; `compliance-site-check` følger de juridiske links, så Pro gør
     **ikke** mere sider — den læser dybere.

     Dom 5 er låst til samme måling som dom 4 (`kald == 1`), så en *ægte*
     flersidet `handleReport` slår begge fra. Det er selvtest 12: med to
     `cscFetch`-kald og den gamle løgnest i katalogen er porten grøn. Ellers
     ville porten gøre det umuligt at bygge den rigtige krybning — og så bliver
     den slået fra i stedet for at lyve.

     python3 tools/check_scan_page_claims.py             # dom
     python3 tools/check_scan_page_claims.py --self-test # 12 mutationer
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKER = ROOT / "site" / "_worker.js"
SCAN_EN = ROOT / "site" / "scan.html"
SCAN_DA = ROOT / "site" / "scan-da.html"

# Konstanterne i `_worker.js`. Kun heltal — `const SCAN_PROXY_MAX_URLS = 5;`
RE_MAX_URLS = re.compile(r"^const SCAN_PROXY_MAX_URLS = (\d+)\s*;", re.M)
RE_CSC_PAGES = re.compile(r"^const CSC_MAX_PAGES = (\d+)\s*;", re.M)

# Kommentaren over `SCAN_PROXY_MAX_URLS`: de linjer der står lige før
# konstanten, og kun dem. En kommentar længere nede i filen skal ikke tælle.
def _kommentar_over_konstant(src: str, navn: str) -> str:
    linjer = src.splitlines()
    tal = RE_MAX_URLS.search(src)
    if not tal:
        return ""
    i = tal.start() and src[:tal.start()].count("\n")
    ud: list[str] = []
    # Gå op over `//`-linjer. Den første ikke-kommentarlinje stopper.
    j = i - 1
    while j >= 0 and (linjer[j].lstrip().startswith("//") or not linjer[j].strip()):
        if linjer[j].lstrip().startswith("//"):
            ud.append(linjer[j])
        j -= 1
    return "\n".join(reversed(ud))

# Ord der påstår at ruten kryber. Dansk og engelsk, fordi kortene findes i
# begge sprog. «crawls», «crawl», «gennemgår», «kravler», «gennemsøger».
RE_KRYB = re.compile(
    r"\bcrawl\w*|\bgennemg(?:å|ør)\b|\bkravler\b|\bgennemsøger\b|"
    r"\bskraver\b|\bwhole site\b|\bhel(e|t) sitet\b", re.I)

# Ord der påstår at den betalte rute læser flere sider end den frie.
# «hver side den finder» / «every page it finds» er samme påstand.
RE_FLERE_ENDEN = re.compile(
    r"every page it finds|hver side den finder|same check on every|"
    r"samme tjek på hver", re.I)


def _naar_kun(ré: re.Pattern[str], src: str, hvad: str,
              fund: list[str]) -> str | None:
    """Første gruppe i `ré` i `src`, eller en fejl hvis mønsteret mangler."""
    m = ré.search(src)
    if not m:
        fund.append(f"{hvad}: mønsteret {ré.pattern!r} blev ikke fundet")
        return None
    return m.group(1)


def dom(worker: str = None, scan_en: str = None, scan_da: str = None,
        root: Path = ROOT, katalog: dict = None) -> list[str]:
    fund: list[str] = []
    wsrc = worker if worker is not None else WORKER.read_text(encoding="utf-8")
    en = scan_en if scan_en is not None else SCAN_EN.read_text(encoding="utf-8")
    da = scan_da if scan_da is not None else SCAN_DA.read_text(encoding="utf-8")
    kat = katalog if katalog is not None else json.loads(
        (root / "tools" / "stripe_catalog.json").read_text(encoding="utf-8"))

    # Dom 1 — konstanterne skal findes og være tal.
    max_urls = _naar_kun(RE_MAX_URLS, wsrc, "worker", fund)
    csc_pages = _naar_kun(RE_CSC_PAGES, wsrc, "worker", fund)
    if max_urls is None or csc_pages is None:
        return fund
    max_urls_i, csc_pages_i = int(max_urls), int(csc_pages)

    # Dom 2 — kommentaren må ikke påstå at de to tal er ens, og må pege på
    # begge. En påstand uden tal kan ikke efterprøves, så den er ikke bedre
    # end den falske den afløser.
    kommentar = _kommentar_over_konstant(wsrc, "SCAN_PROXY_MAX_URLS")
    if not kommentar.strip():
        fund.append("worker: der er ingen kommentar over SCAN_PROXY_MAX_URLS "
                    "— begrundelsen for tallet skal kunne læses")
    else:
        lighed = re.search(
            r"samme tal|same (?:number|count)|identisk|er lig\b|equal", kommentar, re.I)
        if lighed:
            fund.append(
                f"kommentaren over SCAN_PROXY_MAX_URLS siger «{lighed.group(0)}» "
                f"om de to ruter — men SCAN_PROXY_MAX_URLS={max_urls_i} og "
                f"CSC_MAX_PAGES={csc_pages_i}. Påstanden skal pege på begge tal, "
                f"ikke på en lighed ingen port kan holde sand")
        for navn, værdi in (("SCAN_PROXY_MAX_URLS", max_urls_i),
                            ("CSC_MAX_PAGES", csc_pages_i)):
            if not re.search(rf"\b{navn}\b[^.\n]*\b{værdi}\b|\b{værdi}\b[^.\n]*\b{navn}\b",
                             kommentar):
                fund.append(
                    f"kommentaren over SCAN_PROXY_MAX_URLS nævner ikke "
                    f"{navn}={værdi} — tallet skal kunne slås op mod koden")

    # Dom 3 — klientens synlige tekst skal sige det samme antal.
    # Ordformene accepteres på tallet, så EN og DA kan hver skrive sit sprog.
    for fil, src, konstant in ((SCAN_EN, en, max_urls_i), (SCAN_DA, da, max_urls_i)):
        # Find feltet labelet — det er det brugeren ser, ikke en kommentar.
        label = re.search(r'<label[^>]*class="scanbox-label"[^>]*>([^<]*)</label>', src)
        if not label:
            fund.append(f"{fil.name}: fandt ikke <label class=\"scanbox-label\"> "
                        f"— porten kan ikke vide hvad brugeren bliver lovet")
            continue
        tekst = label.group(1)
        # Tallet som et heltal i teksten.
        tal = re.findall(r"\d+", tekst)
        if not tal:
            fund.append(f"{fil.name}: labelet «{tekst.strip()[:50]}» nævner intet "
                        f"antal sider, men SCAN_PROXY_MAX_URLS={konstant}")
        elif all(int(t) != konstant for t in tal):
            fund.append(f"{fil.name}: labelet siger {tal} sider, men "
                        f"SCAN_PROXY_MAX_URLS={konstant} — teksten skal svare "
                        f"til det værktøjet gør")

    # Dom 4 — pro-kortet må ikke love at den betalte rute kryber hele sitet,
    # når den henter én side. Tallet kommer fra koden, ikke fra en antagelse.
    i = wsrc.find("async function handleReport")
    if i < 0:
        fund.append("worker: fandt ikke handleReport — dom 4 kan ikke dømme")
    else:
        # Find slutningen på funktionen ved den næste topniveau-funktion.
        rest = wsrc[i:]
        næste = re.search(r"\n(?:async )?function \w+\(", rest[10:])
        krop = rest[:10 + næste.start()] if næste else rest
        kald = len(re.findall(r"\bcscFetch\(", krop))
        if kald == 1:
            for fil, src in ((SCAN_EN, en), (SCAN_DA, da)):
                # Kun **pro-kortet**: fra `function proCard()` til dens slut.
                # Se målingen i docstrengen — desktop-sektionen på
                # `scan.html:169` er et andet program og siger «crawl» med
                # ret, så hele filen ville være rød på en sand påstand.
                i0 = src.find("function proCard(")
                if i0 < 0:
                    fund.append(f"{fil.name}: fandt ikke proCard() — dom 4 kan "
                                f"ikke finde det pro-kort, den skal dømme")
                    continue
                slutt = src.find("\nfunction ", i0 + 10)
                kort = src[i0:slutt if slutt > 0 else len(src)]
                for m in RE_KRYB.finditer(kort):
                    linje = src[:i0 + m.start()].count("\n") + 1
                    fund.append(
                        f"{fil.name}:{linje} pro-kortet bruger «{m.group(0)}» om "
                        f"den betalte rute, men handleReport henter {kald} side "
                        f"(ét cscFetch-kald) — den crawler ikke hele sitet")
        elif kald == 0:
            fund.append("worker: handleReport kalder ikke cscFetch overhovedet "
                        "— dom 4 kan ikke dømme ruten")

    # Dom 5 — **hver** pro-række for `eucomply-pro` i katalogen skal sige det
    # samme. Dom 4 dømmer de to `/scan`-siders håndskrevede `proCard()`, og det
    # var nok, fordi de var de eneste kort der løj. Målt 6/10: «It crawls the
    # whole site» stod i **16** kort på **9** sider, og dom 4 så kun to af dem.
    # Katalogen er den fælles sandhed — `pro_table.py` tegner alle otteogtyve
    # blokke fra den, så dommen skal læse den, ikke filerne.
    #
    # Kun produkter hvis betalte rute er `handleReport`. `page-profile-pro`
    # (`/api/profile`) er en anden rute med sit eget argument, og dens kort er
    # dømt af `check_deskuptime_claims.py`/`check_pro_table.py`.
    #
    # Dømningen er låst til `kald == 1` — samme måling som dom 4. Det er point
    # 2 i selvtesten: hvis nogen faktisk bygger flersided ind i `handleReport`,
    # skal porten holde kravet op i stedet for at dømme en sand påstand som
    # løgn. Ellers gør porten den ægte krybning umulig at bygge.
    if kald != 1:
        return fund
    for side in kat.get("pro_table_pages", []):
        if side.get("product") != "eucomply-pro":
            continue
        for feat in side.get("pro_features", []):
            labels = feat.get("labels") or {}
            for lang, tekst in labels.items():
                for sætning in (tekst if isinstance(tekst, list) else [tekst]):
                    if not isinstance(sætning, str):
                        continue
                    m = RE_KRYB.search(sætning)
                    if m:
                        fund.append(
                            f"katalog: {side['path']} ({lang}) "
                            f"pro_features «{feat['id']}» siger «{m.group(0)}», men "
                            f"handleReport henter én side (ét cscFetch-kald) — "
                            f"kortet skal sige hvad den rute faktisk gør")
    return fund


def _selftest() -> int:
    """Hver mutation skal gøre porten rød, og kun de må gøre det."""
    base_w = WORKER.read_text(encoding="utf-8")
    base_en = SCAN_EN.read_text(encoding="utf-8")
    base_da = SCAN_DA.read_text(encoding="utf-8")
    base_k = json.loads(
        (ROOT / "tools" / "stripe_catalog.json").read_text(encoding="utf-8"))

    grøn = dom(base_w, base_en, base_da, katalog=base_k)
    # Kildens egen tekst skal være grøn nu — ellers må mutationerne ikke
    # bevise noget, for så ville de være grønne fordi porten intet dømmer.
    if grøn:
        print("SELFTEST: kilden er RØD før nogen mutation — dommen er død")
        for f in grøn:
            print("   ", f)
        return 1

# Hver mutation giver de **filer** den rører ved navn. En mutation der
    # ingen fil ændrer, ville være grøn og lyde som en fejlslået dom — så
    # sidst i `_selftest` dømmes det: en mutation skal kunne ramme noget.
    HÆV = lambda s: s.replace("const SCAN_PROXY_MAX_URLS = 5;",
                              "const SCAN_PROXY_MAX_URLS = 6;")
    mutationer = [
        # 1. Den oprindelige fejl: kommentaren siger de to tal er ens. Det er
        #    fundet fra 6/10, hvervet 1:1 — mutationen skal ramme præcis den.
        ("kommentaren påstår lighed mellem ruterne",
         {"w": base_w.replace("De **to ruter er ulige**",
                              "Fem er samme tal som `/api/compliance-scan` tager")}),
        # 2. Kommentaren mister det betalte tal helt, så dens begrundelse kun
        #    peger på det ene. Uden denne dom kan man slette 12 og være grøn.
        ("kommentaren nævner ikke CSC_MAX_PAGES",
         {"w": base_w.replace("så dens\n// loft er `CSC_MAX_PAGES = 12` pr. kald.",
                              "så dens\n// loft er sat lavere end på den anden rute.")}),
        # 3. Nogen hæver konstanten og glemmer teksten. Skal være rød på
        #    Både kommentaren og labelet — de er to uafhængige fejlsteder.
        ("konstanten hævet uden at teksten følger", {"w": HÆV(base_w)}),
        # 4. Samme hævelse, men kun den engelske tekst følger med. Så porten
        #    dømmer den ene fil og den anden fejler ikke.
        ("kun EN-teksten følger konstanten",
         {"w": HÆV(base_w), "en": base_en.replace("up to 5 pages", "up to 6 pages")}),
        # 5. Og kun den danske. Uden denne mutation kunne dom 3 være en
        #    engelsk-eftersyn, der lader scan-da.html ligge.
        ("kun DA-teksten følger konstanten",
         {"w": HÆV(base_w), "da": base_da.replace("op til 5 sider", "op til 6 sider")}),
        # 6. Pro-kortet på EN lover igen at ruten kryber hele sitet.
        ("EN-pro-kortet siger 'crawls the whole site'",
         {"en": base_en.replace("It reads the page from the server too",
                                "It crawls the whole site")}),
        # 7. Samme på DA med et dansk krybende verb, så dommen ikke bare
        #    kan læse engelsk.
        ("DA-pro-kortet siger 'gennemgår hele sitet'",
         {"da": base_da.replace("Den læser siden fra serveren",
                                "Den gennemgår hele sitet")}),
        # 8. Konstanten er væk. Dom 1 skal sige det, ellers ville resten af
        #    dommene være grønne ved at slå alt sammen.
        ("SCAN_PROXY_MAX_URLS er slettet",
         {"w": re.sub(r"^const SCAN_PROXY_MAX_URLS = \d+;\n", "", base_w, flags=re.M)}),
        # 9. Dom 4 skal være **robust mod en ny krybende rute**: hvis nogen
        #    faktisk bygger flersidet ind i handleReport, skal porten holde
        #    kravet op i stedet for at dømme en sand påstand som løgn.
        ("handleReport henter to sider (porten skal så tie)",
         {"w": base_w.replace(
             "const page = await cscFetch(target.toString(), REPORT_FETCH_TIMEOUT_MS);",
             "const page = await cscFetch(target.toString(), REPORT_FETCH_TIMEOUT_MS);\n"
             "  const mere = await cscFetch(target.toString(), REPORT_FETCH_TIMEOUT_MS);")}),
    ]
    # 10. Den oprindelige løgnest, genindsat i katalogen på en side dom 4
    #     **aldrig** så. Mutationen rammer den første `eucomply-pro`-side med
    #     et crawl-id i katalogen, altså `text-on-image-checker` — den ligger i
    #     katalogens `pro_features`, ikke i nogen `proCard()`, så uden dom 5
    #     ville mutationen være grøn og lyde som en fejlslået dom.
    # 11. Samme løgnest på dansk — ellers kunne dommen bare læse engelsk.
    # 12. En **fremtidig** flersidet `handleReport` skal slå dom 5 fra, ligesom
    #     den slår dom 4 fra. Ellers gør porten det umuligt at bygge den ægte
    #     krybning, og så bliver den slået fra i stedet for at lyve.
    for num, (fejl_txt, rute_tekst) in enumerate((
        ("crawl-claim på en side dom 4 ikke ser",
         "It crawls the whole site — the same check on every page it finds"),
        ("dansk crawl-claim i katalogen",
         "Den gennemgår hele sitet — samme tjek på hver side den finder"),
    ), start=10):
        k = json.loads(json.dumps(base_k))
        ramt = 0
        for side in k["pro_table_pages"]:
            if side.get("product") != "eucomply-pro":
                continue
            for f in side.get("pro_features", []):
                if f["id"] in ("crawl", "whole-site") and ramt == 0:
                    f["labels"]["en"] = [rute_tekst] if num == 10 else f["labels"]["en"]
                    if num == 11:
                        f["labels"]["da"] = [rute_tekst]
                    ramt += 1
        mutationer.append((fejl_txt, {"k": k}))

    flersidet = base_w.replace(
        "const page = await cscFetch(target.toString(), REPORT_FETCH_TIMEOUT_MS);",
        "const page = await cscFetch(target.toString(), REPORT_FETCH_TIMEOUT_MS);\n"
        "  const mere = await cscFetch(target.toString(), REPORT_FETCH_TIMEOUT_MS);")
    k12 = json.loads(json.dumps(base_k))
    for side in k12["pro_table_pages"]:
        if side.get("product") != "eucomply-pro":
            continue
        for f in side.get("pro_features", []):
            if f["id"] in ("crawl", "whole-site"):
                f["labels"]["en"] = ["It crawls the whole site — the same check on every page it finds"]
                f["labels"]["da"] = ["Den gennemgår hele sitet — samme tjek på hver side den finder"]
    mutationer.append(("katalog-crawl-claim + flersidet handleReport (porten skal så tie)",
                       {"w": flersidet, "k": k12}))
    fejl = 0
    for navn, ændringer in mutationer:
        w = ændringer.get("w", base_w)
        en = ændringer.get("en", base_en)
        da = ændringer.get("da", base_da)
        k = ændringer.get("k", base_k)
        fund = dom(w, en, da, katalog=k)
        # Mutation 9 og 12 er den modsatte retning: de skal være **grønne**,
        # fordi dommen kun dømmer det koden faktisk gør. Så de tælles separat.
        hverket = (w, en, da, k) != (base_w, base_en, base_da, base_k)
        forventer_rød = "porten skal så tie" not in navn
        if fund and forventer_rød:
            print(f"  RØD  {navn}")
            for f in fund[:2]:
                print(f"        {f}")
        elif fund and not forventer_rød:
            print(f"  ** RØD (skulle være GRØN) — {navn}")
            for f in fund[:2]:
                print(f"        {f}")
            fejl += 1
        elif not fund and forventer_rød:
            print(f"  ** GRØN (skulle være RØD) — {navn}")
            fejl += 1
        else:
            print(f"  GRØN som forventet — {navn}")
        if not hverket:
            print(f"  ** mutationen rørte ingen fil — {navn}")
            fejl += 1
    print(f"scan-page-claims: selftest {len(mutationer) - fejl}/{len(mutationer)} "
          f"mutationer som forventet")
    return 1 if fejl else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return _selftest()
    fund = dom()
    if fund:
        print("scan-page-claims: RØD — %d fund" % len(fund))
        for f in fund:
            print("  -", f)
        return 1
    wsrc = WORKER.read_text(encoding="utf-8")
    print("scan-page-claims: GRØN — SCAN_PROXY_MAX_URLS=%s og CSC_MAX_PAGES=%s "
          "er to tal, kommentaren over det første peger på begge, "
          "felt-labelet på /scan og /scan-da siger det samme antal, og intet "
          "pro-kort for eucomply-pro i katalogen lover en krybende rute som "
          "handleReport ikke er"
          % (RE_MAX_URLS.search(wsrc).group(1), RE_CSC_PAGES.search(wsrc).group(1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())