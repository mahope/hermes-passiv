#!/usr/bin/env python3
"""Dommer gratis-mod-Pro-tabellen på hver produktside mod `tools/stripe_catalog.json`.

Baggrund (målt 2/10, se `tools/pro_table.py`): de fire produktsider viste
gratis og Pro på fire måder, og de tre af dem skrev prisen i hånden. Ingen port
dømte den — `check_own_prices.py` læser kun **købsknapper**, og ingen af
siderne havde sin sammenligning i en knap. En prisændring i Stripe ville derfor
kunne glide fra `/page-profile` uden at nogen så det, og en læser ville se to
forskellige priser på to sider om det samme produkt.

Tabellen er derfor tegnet af katalogen, og denne port dommer den:

  1. **Én blok pr. side**, og den skal være tegnet af katalogen — byte for byte.
     En håndredigering, en gammel pris eller den danske blok på den engelske
     side er alle røde, fordi de afviger fra `pro_table.blok()`.
  2. **To rækker**: en gratis og en Pro. Tabellen må ikke vokse til et andet
     gitter, for så er den igen en af fire måder at vise det samme på.
3. **Prisen skal være katalogens** — beløb fra `price_usd` og et ord fra
      `billing_periods.words`, altså samme ordliste dom 4 i `check_own_prices.py`
      bruger på købsknapper. Så kan «$19» ikke være årssubscription på den ene
      side og engangskøb på den anden.
   3b. **Livstidsprisen skal have samme omfang som årsprisen i samme tabel.**
      Fund fra review 2/10: priscellen skrev «$79/year per website» over en
      note der sagde «$149 once — lifetime», altså «149 engang for alle
      websites» — en licens der kun gælder for ét.
  4. **Hver funktion i katalogen skal stå i tabellen.** Ellers sælger siden
     noget den ikke viser, og det er præcis den fejl `check_stripe_ctas.py`
     målte på `/clean-copy-tool` og `/activate/`.
  5. **Ingen håndskrevet sammenligning ved siden af.** De otte sider må ikke
     have en anden `<table class="compare">` uden for det genererede område —
     det er det, der gjorde fire sider til fire svar.

    python3 tools/check_pro_table.py             # dom
    python3 tools/check_pro_table.py --self-test # 28 kontroller
"""
from __future__ import annotations

import argparse
import contextlib
import html as html_lib
import io
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pro_table  # noqa: E402  — generatoren er den ene sandhed

ROOT = Path(__file__).resolve().parent.parent
# Målt 2/10 på den niende side: produktets feature-liste passer ikke overalt.
# `page-profile-pro`s frie funktioner er alle sange i `page_profile.py` —
# historik, terminalrapport, score og karakter — mens `/url-inspector` er
# browseren, der hverken gemmer historik eller kører i en terminal. Havde
# listen bare været tegnet ind, ville den have løjet på 12 værktøjssider.
# Derfor er der to slags sider, og dom 6 holder dem ude af hinanden.
PRODUKTSIDE = 8

# Målt 2/10: elleve af de tretten værktøjssider har et pro-kort, men ingen af dem
# viste i en tabel hvad den **frie** udgave gør på netop det værktøj. Nu er alle
# elleve tegnet — først de to mest besøgte (EN + DA på `/text-on-image-checker`),
# så de ni øvrige: `/scan`, `/compliance-site-check`, `/cookie-check`,
# `/contrast-checker` og `/security-headers-check` i begge sprog. Ratchet'en er
# derfor på elleve, så en side der mister sin tabel eller kommer i katalogen uden
# den skal være rød.
#
# Målt 2/10, siddende på de to værktøjssider der lå udenfor ratchet'en helt:
# `/clean-copy-tool` havde en gratis-mod-Pro-tabel, men en **håndskrevet** —
# otte rækker i markup med «19 USD per year» — altså to filer i katalogen
# ville have svaret forskelligt, og ingen af dem blev dømt. Den er nu tegnet af
# `pro_table.py` fra katalogens egen `clean-copy-pro`-post, ligesom
# `/clean-copy` og `/da/clean-copy`, så de tre sider giver ét svar.
# `/url-inspector` havde **ingen** tabel, kun «See what Pro adds before you
# buy» og et link til `/page-profile`; den læser nu `page-profile-pro`-posten,
# så de to sider heller ikke kan svare forskelligt.
VÆRKTØJSSIDE = 13


def _scripts(rel: str) -> set[str]:
    """De filer siden selv indlæser med `<script src>`, som `site/`-stier."""
    fil = ROOT / rel
    if not fil.exists():
        return set()
    html = fil.read_text(encoding="utf-8")
    return {f"site/{s.lstrip('./')}" for s in
            re.findall(r'<script[^>]+src="([^"]+\.js)"', html)}


def synlig_pris(tekst: str) -> set[str]:
    """Beløb i en priscelle. Kun tal med `$` foran: «første 100 køb» og
    «5 enheder» står i samme celle, og de er ikke priser."""
    return set(re.findall(r"\$(\d+(?:\.\d+)?)", tekst))


def dom(catalog: dict, root: Path = ROOT) -> list[str]:
    fund: list[str] = []
    perioder = catalog.get("billing_periods") or {}
    produkter = catalog.get("products") or {}
    sider = catalog.get("pro_table_pages")
    if not isinstance(sider, list) or len(sider) != PRODUKTSIDE + VÆRKTØJSSIDE:
        fund.append(f"katalog: pro_table_pages skal være præcis "
                    f"{PRODUKTSIDE} produktsider + {VÆRKTØJSSIDE} værktøjssider "
                    f"= {PRODUKTSIDE + VÆRKTØJSSIDE}, fandt "
                    f"{len(sider) if isinstance(sider, list) else sider!r}")
        return fund
    for post in sider:
        if not isinstance(post, dict):
            fund.append("katalog: en pro-table-side er ikke et objekt")
            continue
        rel = str(post.get("path"))
        nøgle = post.get("product")
        lang = post.get("lang")
        if not str(post.get("why", "")).strip():
            fund.append(f"{rel}: mangler begrundelse")
        produkt = produkter.get(nøgle)
        if not isinstance(produkt, dict):
            fund.append(f"{rel}: ukendt produkt {nøgle!r}")
            continue
        if lang not in pro_table.TEKST:
            fund.append(f"{rel}: ukendt sprog {lang!r}")
            continue
        # 6. En side der ikke *er* produktets egen side må ikke låne
        #    produktets funktionsliste. Målt 2/10: `page-profile-pro`s fem frie
        #    funktioner peger alle på `page_profile.py` — `--history`, en
        #    terminalrapport, score og karakter — mens `/url-inspector` er en
        #    browser, der hverken gemmer historik eller skriver til en
        #    terminal. Tegnet der ville den have løjet om browseren. Samme
        #    fælde for `eucomply-pro`: listen er `compliance-report.html`s
        #    egen tjekrække, ikke hvad `/cookie-check` gør.
        #    Sådan må en sådan side se ud: `kind: "tool"` og en `free_features`
        #    hvis `where` peger på sidens **egen** fil.
        egen_side = rel.lstrip("./") in (produkt.get("own_pages") or [])
        if post.get("layout") not in (None, "block", "inline"):
            fund.append(f"{rel}: ukendt layout {post.get('layout')!r}")
        if not egen_side:
            if post.get("kind") != "tool":
                fund.append(f"{rel}: er ikke {nøgle}s egen side, så den skal "
                            f"mærkes kind=tool med sine egne free_features "
                            f"(nu låner den {nøgle}s liste, der er skrevet "
                            f"til en anden side)")
            # `where` skal pege på siden selv **eller** på et script siden
            # indlæser. Målt 2/10 på `/text-on-image-checker`: de tre frie
            # funktioner ligger ikke i HTML'en, men i `text-on-image-core.js`,
            # som siden indlæser og kalder med sine egne tekster. Uden den
            # undtagelse ville dommen kræve at siden **havde** koden liggende
            # selv — altså at den kopierede kernen ind i to filer, så ét sted
            # kunne rettes. Undtagelsen er derfor ikke «et andet navn»: den
            # kræver at filen faktisk står i sidens egen `<script src>`.
            egne_script = _scripts(rel)
            for felt, hvad in (("free_features", "free"), ("pro_features", "Pro")):
                egne = post.get(felt)
                if not isinstance(egne, list) or not egne:
                    fund.append(f"{rel}: mangler egne {felt}")
                    continue
                for feature in egne:
                    if not ((feature.get("labels") or {}).get(lang) or []):
                        fund.append(f"{rel}: egne {felt} "
                                    f"{feature.get('id')!r} har ingen "
                                    f"{lang}-labels")
                    hvor = str(feature.get("where") or "")
                    fil = hvor.split(":")[0].split(" ")[0].strip()
                    if hvor.startswith(rel) or fil in egne_script:
                        continue
                    fund.append(f"{rel}: egne {felt} {feature.get('id')!r} "
                                f"peger på {hvor[:60]!r}, som hverken er siden "
                                f"selv eller et script den indlæser "
                                f"({sorted(egne_script)[:2]}) — så "
                                f"{hvad}-funktionen er ikke dokumenteret her")
            egne = post.get("free_features")
            if not isinstance(egne, list) or not egne:
                fund.append(f"{rel}: mangler egne free_features")
            else:
                for feature in egne:
                    labels = (feature.get("labels") or {}).get(lang) or []
                    if not labels:
                        fund.append(f"{rel}: egne free_features "
                                    f"{feature.get('id')!r} har ingen {lang}-labels")
        fil = root / rel
        if not fil.exists():
            fund.append(f"{rel}: filen findes ikke")
            continue
        html = fil.read_text(encoding="utf-8")

        # 1. Præcis ét område, tegnet af katalogen.
        områder = pro_table.EJER_RE.findall(html)
        if len(områder) != 1:
            fund.append(f"{rel}: {len(områder)} pro-table-områder — "
                        f"en side skal have præcis ét")
            continue
        blok = områder[0]
        forventet = pro_table.blok(nøgle, produkt, lang, perioder,
                                   str(post.get("anchor") or ""),
                                   post.get("free_features"),
                                   post.get("pro_features"),
                                   str(post.get("layout") or "block")).strip()
        if (post.get("layout") or "block") == "inline":
            forventet = pro_table.kompakt_blok(forventet, rel)
        if blok.strip() != forventet:
            fund.append(f"{rel}: tabellen er ikke tegnet af katalogen "
                        f"(kør `python3 tools/pro_table.py --apply`)")

        # 2. To rækker, og de har hver tre celler: rækkens navn, gratis og Pro.
        rækker = re.findall(r"<tr>(.*?)</tr>", blok, re.S)
        krop = [r for r in rækker if "scope=\"row\"" in r]
        if len(krop) != 2:
            fund.append(f"{rel}: {len(krop)} rækker i tabellen — "
                        f"den skal have én gratis og én Pro")
            continue
        for række in krop:
            celler_ = re.findall(r"<t[hd]\b", række)
            if len(celler_) != 3:
                fund.append(f"{rel}: en række har {len(celler_)} celler — "
                            f"navn, gratis og Pro")

        # 3. Priserne skal være katalogens, og Pro-prisen skal have et ord fra
        #    periodeordlisten. Beløbene læses i hele blokken: gratisprisen,
        #    Pro-prisen og livstidsprisen i noten under tabellen. Kun tal med
        #    `$` foran tæller — «30-second polling interval» er ikke en pris.
        tilladt_ord = [o for periode in
                       ((perioder.get("products") or {}).get(nøgle) or [])
                       for o in ((perioder.get("words") or {}).get(periode) or [])]
        pro_celle = re.findall(r"<td>(.*?)</td>", krop[-1], re.S)
        priscelle = pro_celle[-1] if pro_celle else ""
        beløb = synlig_pris(blok)
        forventet_beløb = {"0", str(produkt["price_usd"])}
        livstid = produkt.get("lifetime")
        if isinstance(livstid, dict) and livstid.get("price_usd"):
            forventet_beløb.add(str(livstid["price_usd"]))
        if beløb != forventet_beløb:
            fund.append(f"{rel}: Pro-prisen viser {sorted(beløb) or 'intet'}, "
                        f"katalogen siger {sorted(forventet_beløb)}")
        if tilladt_ord and not [o for o in tilladt_ord if o in priscelle]:
            fund.append(f"{rel}: Pro-prisen nævner ingen af katalogens "
                        f"periodeord {sorted(set(tilladt_ord))[:4]}")

        # 3b. Livstidsprisen skal have **samme omfang** som årsprisen i samme
        #     tabel. Målt 2/10 af review: katalogen sælger `eucomply-pro`s
        #     livstidspris som «$149 engang pr. website», og priscellen skrev
        #     «$79/year per website» — men noten under tabellen skrev «$149 once
        #     — lifetime», altså uden omfang, på 13 sider. Den naturlige læsning
        #     af et par hvor den ene pris er afgrænset til ét website og den
        #     anden ikke er afgrænset til noget er «149 engang for alle
        #     websites», og så får køberen en licens der kun gælder for ét.
        #     Dommen læser omfanget i **priscellen** og ikke i katalogen, så den
        #     fanger også det tilfælde hvor nogen tager `{scope}` ud af
        #     generatorens livstidsskabelon og kører `--apply` bagefter: dom 1
        #     er grøn ved konstruktion, fordi den sammenligner katalog →
        #     markup med den samme skabelon.
        scope = produkt.get("scope")
        omfang = (scope.get(lang) or "").strip() if isinstance(scope, dict) else ""
        if omfang and isinstance(livstid, dict) and livstid.get("price_usd"):
            noter = re.findall(r'<p class="pro-note">(.*?)</p>', blok, re.S)
            livstidsnote = next((n for n in noter
                                 if f"${livstid['price_usd']}" in n), "")
            if omfang not in priscelle:
                fund.append(f"{rel}: priscellen skriver ikke katalogens omfang "
                            f"{omfang!r} for {nøgle}")
            elif omfang not in livstidsnote:
                fund.append(f"{rel}: livstidsprisen ${livstid['price_usd']} "
                            f"står i en note uden omfang, mens priscellen over "
                            f"den siger {omfang!r} — katalogen sælger også "
                            f"livstidsprisen {omfang}, så noten læses som om "
                            f"den gjaldt alle")

        # 4. Alle katalogens funktioner skal stå i tabellen.
        for nøgle_fil in ("free_features", "pro_features"):
            kilder = post.get(nøgle_fil) or produkt.get(nøgle_fil) or []
            for feature in kilder:
                varianter = (feature.get("labels") or {}).get(lang) or []
                if not varianter:
                    fund.append(f"{rel}: {nøgle} {feature.get('id')!r} har "
                                f"ingen {lang}-labels i katalogen")
                    continue
                # Slås op i **tabellen**, ikke i hele blokken. Målt 6/10: grænsen
                # under tabellen for clean-copy siger «Batch conversion is
                # web-tool only …», så dommen læste den som bevis på at
                # funktionen stod i tabellen — og selftestens «manglende
                # Pro-funktion» faldt rød, fordi porten så var svækket. En
                # funktion skal stå i cellen den sælges i; en note under
                # tabellen er ikke en celle.
                if not any(v.lower() in "".join(krop).lower() for v in varianter):
                    fund.append(f"{rel}: tabellen nævner ikke "
                                f"{nøgle_fil} {feature.get('id')!r} "
                        f"(første label: {varianter[0]!r})")

        # 4b. `layout=inline` ligger inde i en JavaScript-streng, så blokken må
        #     ikke have et linjeskift og må ikke lukke strengen. Uden denne dom
        #     ville `--apply` skrive en blok der ikke kan indlæses, og porten
        #     ville være grøn fordi den bare sammenligner de samme bytes.
        if (post.get("layout") or "block") == "inline":
            for tegn, hvad in (("\n", "linjeskift"), ("'", "apostrof"),
                               ("\\", "backslash"), ("</script", "</script")):
                if tegn in blok:
                    fund.append(f"{rel}: layout=inline, men blokken har en "
                                f"{hvad} — den ville lukke JavaScript-strengen")

        # 4c. Hvert pro-kort skal have én ærlig grænse — en ting Pro *ikke* gør,
        #     som en kunde kunne forvente. Uden den køber nogen en licens for
        #     noget de troede var inkluderet, og annulleringen kommer bagefter.
        #     Dommen læser katalogens `pro_limit` og kræver at teksten står på
        #     **grænselinjen** (`pro-limit`), så den hverken kan forsvinde
        #     uden at blive dømt, eller flytte op i prisnoten hvor den så læses
        #     som en pris. Teksten skal stå i hele blokken, så et site der
        #     skriver den i markup uden klassen stadig er rødt på den anden
        #     arm — ellers ville en klasseløs linje være nok.
        #     Sammenligningen sker på **unescapet** tekst. Generatoren skriver
        #     grænsen med `h()` (`tools/pro_table.py`), så en sætning med `&`,
        #     `<` eller `>` står i markup'en som `&amp;` — den rå katalogtekst
        #     findes da ikke, selv om siden er korrekt. Målt 6/10 med
        #     `&mdash;` i `page-profile-pro`: `--apply` skrev den rigtige
        #     `<p …>No alerts &amp;mdash; …</p>`, og dommen meldte «står ikke
        #     i blokken». Det er en dom, der dømmer det læseren ser.
        grænse = produkt.get("pro_limit")
        grænselinje = next((n for n in re.findall(r'<p class="pro-note pro-limit">(.*?)</p>',
                                                 blok, re.S)), "")
        laest_tekst = html_lib.unescape(grænselinje)
        laest_blok = html_lib.unescape(blok)
        if not isinstance(grænse, dict) or not grænse.get(lang):
            fund.append(f"{rel}: katalogen har ingen pro_limit for {nøgle} "
                        f"på {lang} — hvert pro-kort skal have én ærlig grænse")
        elif str(grænse[lang]) not in laest_blok:
            fund.append(f"{rel}: pro_limit {str(grænse[lang])!r} står ikke "
                        f"i blokken")
        elif str(grænse[lang]) not in laest_tekst:
            fund.append(f"{rel}: pro_limit {str(grænse[lang])!r} står ikke "
                        f"på grænselinjen (class=\"pro-note pro-limit\")")

        # 5. Ingen håndskrevet sammenligning ved siden af.
        udenfor = pro_table.EJER_RE.sub("", html)
        for ekstra in re.findall(r'<table class="compare"[^>]*>', udenfor):
            fund.append(f"{rel}: en håndskrevet {ekstra} står ved siden af "
                        f"den genererede tabel")

    return fund


def _kopi(root: Path, muter) -> Path:
    """En kopi af de otte sider, hvor `muter` ændrer filerne."""
    for post in json_sider():
        mål = root / post
        mål.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / post, mål)
    muter(root)
    return root


def json_sider() -> list[str]:
    return [post["path"] for post in pro_table.load()["pro_table_pages"]]


def _tegn(root: Path, catalog: dict) -> None:
    """Kør `pro_table.anvend` på en kopi, med generatorens rod flyttet.

    Mutationerne skal ramme **generatoren** og ikke siden, ellers ville dom 1
    (byte for byte mod `pro_table.blok()`) være rød af sig selv, og selftesten
    ville grønne uden at teste den dom den er skrevet for. Derfor kaldes den
    samme `--apply` som en redaktør ville, og rodens `ROOT` peger på kopien.
    """
    gammel = pro_table.ROOT
    pro_table.ROOT = root
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            pro_table.anvend(catalog)
    finally:
        pro_table.ROOT = gammel


def self_test() -> int:
    fejl: list[str] = []

    talt = [0]

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        talt[0] += 1
        if not sand:
            fejl.append(f"{navn}{': ' + detalje if detalje else ''}")

    catalog = pro_table.load()

    def skriv(rod: Path, rel: str, gammel: str, ny: str) -> None:
        fil = rod / rel
        tekst = fil.read_text(encoding="utf-8")
        assert gammel in tekst, (rel, gammel)
        fil.write_text(tekst.replace(gammel, ny, 1), encoding="utf-8")

    def skriv_i_tabel(rod: Path, rel: str, gammel: str, ny: str) -> None:
        """Ændr **inde i** den genererede tabel. «$19/year» står også i
        Tires-kortets knap, så en almindelig erstatning rammer den og lader
        tabellen være urørt — mutationen ville være grøn uden en fejl."""
        fil = rod / rel
        tekst = fil.read_text(encoding="utf-8")
        m = pro_table.EJER_RE.search(tekst)
        assert m and gammel in m.group(0), (rel, gammel)
        fil.write_text(tekst[:m.start()] + m.group(0).replace(gammel, ny, 1)
                       + tekst[m.end():], encoding="utf-8")

    # 1. Målingen på den virkelige site/ skal være grøn, ellers er den
    #    ubrugelig — samme mutation som de andre porte.
    rød = dom(catalog)
    tjek("målingen er grøn på site/", not rød, "; ".join(rød[:3]))

    with tempfile.TemporaryDirectory() as tmp:
        rod_med = _kopi(Path(tmp), lambda rod: None)
        fund = dom(catalog, rod_med)
        tjek("kopien er grøn", not fund, "; ".join(fund[:2]))

    # 2. En gammel pris i blokken er rød — det var fejlen der gjorde fire sider
    #    til fire svar.
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), lambda rod: skriv_i_tabel(
            rod, "site/page-profile.html", "$19/year", "$29/year"))
        tjek("gammel pris i tabellen er rød", bool(dom(catalog, rod)))

    # 3. Dansk blok på en engelsk side er rød.
    with tempfile.TemporaryDirectory() as tmp:
        def byt_sprog(rod: Path) -> None:
            fil = rod / "site/clean-copy.html"
            tekst = fil.read_text(encoding="utf-8")
            blok = pro_table.EJER_RE.search(tekst).group(0)
            dansk = pro_table.blok(
                "clean-copy-pro", catalog["products"]["clean-copy-pro"],
                "da", catalog["billing_periods"])
            fil.write_text(tekst.replace(blok, dansk), encoding="utf-8")
        rod = _kopi(Path(tmp), byt_sprog)
        tjek("dansk tabel på engelsk side er rød", bool(dom(catalog, rod)))

    # 4. Blokken mangler.
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), lambda rod: skriv(
            rod, "site/deskuptime/index.html",
            pro_table.START, "<!-- tabellen er væk -->"))
        fund = dom(catalog, rod)
        tjek("manglende tabel er rød",
             any("pro-table-områder" in f for f in fund), str(fund))

    # 5. To tabeller på én side.
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), lambda rod: skriv(
            rod, "site/compliance-report.html", pro_table.END,
            pro_table.END + "\n" + pro_table.START + "x" + pro_table.END))
        tjek("to tabeller er røde", bool(dom(catalog, rod)))

    # 6. Håndredigering i markørland.
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), lambda rod: skriv_i_tabel(
            rod, "site/da/clean-copy.html", "</table>",
            "</table>\n    <p>Og 20 % rabat til dig, Code: MAD2026</p>"))
        tjek("håndredigering i tabellen er rød", bool(dom(catalog, rod)))

    # 7. En Pro-funktion fjernet fra tabellen, som om kunden betalte for
    #    noget siden ikke viser.
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), lambda rod: skriv_i_tabel(
            rod, "site/clean-copy.html", "<li>Batch conversion</li>", ""))
        fund = dom(catalog, rod)
        tjek("manglende Pro-funktion er rød",
             any("pro_features" in f for f in fund), str(fund))

    # 8. En håndskrevet sammenligning ved siden af den genererede.
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), lambda rod: skriv(
            rod, "site/page-profile.html", pro_table.END,
            pro_table.END + '\n<table class="compare"><tr><td>Pris</td></tr></table>'))
        fund = dom(catalog, rod)
        tjek("håndskrevet tabel ved siden af er rød",
             any("håndskrevet" in f for f in fund), str(fund))

    # 9. Katalogen uden begrundelse, og med en ukendt nøgle.
    svag = {**catalog, "pro_table_pages": [
        {**post, "why": ""} if post["path"] == "site/clean-copy.html" else post
        for post in catalog["pro_table_pages"]]}
    tjek("manglende begrundelse er rød",
         any("mangler begrundelse" in f for f in dom(svag)))
    ukendt = {**catalog, "pro_table_pages": [
        {**post, "product": "findes-ikke"} if post["path"] == "site/clean-copy.html"
        else post for post in catalog["pro_table_pages"]]}
    tjek("ukendt produkt er rødt",
         any("ukendt produkt" in f for f in dom(ukendt)))
    tjek("for få sider i katalogen er røde",
         bool(dom({**catalog, "pro_table_pages": catalog["pro_table_pages"][:3]})))

    # 10. En værktøjsside, der låner produktets liste. Det er den fejl, dom 6
    #     blev skrevet for: `page-profile-pro`s frie funktioner er alle sange
    #     i `page_profile.py` — historik, terminalrapport, score og karakter
    #     — mens browseren på `/url-inspector` ingen af delene har. Uden dom
    #     6 ville løjet stå på 12 værktøjssider, og ingen anden dom så den.
    værktøj = {**catalog, "pro_table_pages": [
        {**post, "path": "site/url-inspector/index.html"} if post["path"] ==
        "site/page-profile.html" else post
        for post in catalog["pro_table_pages"]]}
    fund = dom(værktøj)
    tjek("værktøjsside der låner produktets liste er rød",
         any("egne free_features" in f for f in fund), str(fund))
    # Og den skal kun blive grøn med sin egen liste, der peger på siden selv.
    med_egne = {**værktøj, "pro_table_pages": [
        {**post, "kind": "tool", "free_features": [
            {"id": "redirect-chain",
             "where": "site/url-inspector/index.html:275 hopHeaders -> redirectChain",
             "labels": {"en": ["redirect chain trace"], "da": ["redirect-kæde"]}}]}
        if post["path"] == "site/url-inspector/index.html" else post
        for post in værktøj["pro_table_pages"]]}
    fund = dom(med_egne, ROOT)
    tjek("værktøjsside med sin egen liste er ikke rød på dom 6",
         not any("egne free_features" in f or "kind=tool" in f for f in fund),
         str(fund))
    # Mutation: egen liste der peger et andet sted end siden selv.
    fremmed = {**med_egne, "pro_table_pages": [
        {**post, "free_features": [
            {**post["free_features"][0],
             "where": "page-profile/page_profile.py:1040 --history"}]}
        if post["path"] == "site/url-inspector/index.html" else post
        for post in med_egne["pro_table_pages"]]}
    tjek("egne funktioner der peger på en anden fil er røde",
         any("ikke dokumenteret her" in f for f in dom(fremmed, ROOT)))

    # 11. Mutation: en ny funktion i katalogen uden label på den side, den
    #     sælger på, skal være rød — så katalogen ikke kan vokse i det stille.
    vokset = {**catalog, "products": {**catalog["products"], "clean-copy-pro": {
        **catalog["products"]["clean-copy-pro"],
        "pro_features": catalog["products"]["clean-copy-pro"]["pro_features"]
        + [{"id": "synk", "labels": {"en": ["cloud sync"], "da": ["cloudsynk"]}}]}}}
    fund = dom(vokset)
    tjek("funktion uden label på siden er rød",
         any("pro_features" in f for f in fund), str(fund[:2]))

    # 12. `layout=inline`: en blok med et linjeskift eller en apostrof kan ikke
    #     ligge i en JavaScript-streng. Uden dom 4b ville porten være grøn, fordi
    #     den sammenligner de samme bytes `pro_table.py` skrev — og siden ville
    #     ikke indlæse. Kortene ligger i inline scripts på elleve af de tretten
    #     værktøjssider, så det er en syntaksfejl i *browseren*, ikke en skærv.
    for tegn, navn in (("\n", "linjeskift"), ("'", "apostrof")):
        med = tempfile.TemporaryDirectory()
        rod = _kopi(Path(med.name), lambda rod: skriv_i_tabel(
            rod, "site/text-on-image-checker.html", "</table>",
            "</table>" + tegn))
        fund = dom(catalog, rod)
        tjek(f"layout=inline med {navn} er rød",
             any("layout=inline" in f for f in fund), str(fund[:2]))
        med.cleanup()
    # Og `kompakt_blok` skal sige fra i stedet for at skrive en død blok.
    blok = pro_table.blok("eucomply-pro", catalog["products"]["eucomply-pro"],
                          "en", catalog["billing_periods"], "",
                          catalog["products"]["eucomply-pro"]["free_features"])
    try:
        pro_table.kompakt_blok(blok.replace("</table>", "</table>'"), "test.html")
        tjek("kompakt_blok afviser en apostrof", False, "ingen fejl kastet")
    except SystemExit:
        tjek("kompakt_blok afviser en apostrof", True)
    tjek("kompakt_blok er én linje",
         "\n" not in pro_table.kompakt_blok(blok, "test.html"))

    # 13. Ratchet'en: en værktøjsside forsvinder fra katalogen.
    færre = {**catalog, "pro_table_pages": [
        post for post in catalog["pro_table_pages"]
        if post["path"] != "site/text-on-image-checker.html"]}
    tjek("tabt værktøjsside er rød",
         any("værktøjssider" in f for f in dom(færre)), str(dom(færre)[:1]))

    # 14. Livstidsprisen må ikke tabe omfanget (dom 3b). Mutationen ligger i
    #     **generatorens skabelon**, ikke på siden: lå den på siden, ville dom 1
    #     være rød af sig selv, og porten ville være grøn ved konstruktion —
    #     præcis den fejl dommen er skrevet for. Så her sætter vi skabelonen
    #     tilbage til den fra 2/10, tegner alle nitten sider forfra og spørger
    #     så dommen.
    ægte = (ROOT / "site/compliance-report.html").read_text(encoding="utf-8")
    ægte_blok = pro_table.EJER_RE.search(ægte).group(0)
    tjek("livstidsnoten på /compliance-report har omfanget med",
         "$149 once per website" in ægte_blok, "negativ kontrol")
    gemt = {lang: pro_table.TEKST[lang]["lifetime"] for lang in ("en", "da")}
    try:
        for lang, skabelon in gemt.items():
            pro_table.TEKST[lang]["lifetime"] = skabelon.replace("{scope}", "")
        with tempfile.TemporaryDirectory() as tmp:
            rod = _kopi(Path(tmp), lambda rod: _tegn(rod, catalog))
            fund = dom(catalog, rod)
            tjek("livstidspris uden omfang er rød",
                 any("livstidsprisen" in f for f in fund), str(fund[:2]))
    finally:
        for lang, skabelon in gemt.items():
            pro_table.TEKST[lang]["lifetime"] = skabelon
    # Og porten skal være grøn igen med den rigtige skabelon — ellers ville
    # mutationen bare have gjort den rød for alt.
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), lambda rod: _tegn(rod, catalog))
        fund = dom(catalog, rod)
        tjek("genoptegnede sider er grønne", not fund, "; ".join(fund[:2]))

# 15. Den ærlige grænse (dom 4c). Tre mutationer, fordi dommen har tre
    #     arme, og hver af dem skal kunne stå alene:
    #     (a) katalogen mister `pro_limit` — så er der ingen grænse at kræve,
    #     (b) generatoren lader grænselinjen forsvinde — så dom 1 (byte mod
    #         `pro_table.blok()`) er grøn, og kun dom 4c kan være rød. Ligesom
    #         i mutation 14 skal mutationen ligge i **generatoren**, ellers
    #         ville porten være rød af sig selv og testen intet bevise.
    #     (c) generatoren flytter samme tekst op i prisnoten uden klassen — så
    #         læses grænsen som en pris. Det er præcis den læsefejl dommen er
    #         skrevet for, og uden den tredje arm ville den være grøn.
    nøgle = "deskuptime-pro"
    uden = {**catalog, "products": {**catalog["products"], nøgle: {
        **catalog["products"][nøgle]}}}
    del uden["products"][nøgle]["pro_limit"]
    fund = dom(uden)
    tjek("produkt uden pro_limit i katalogen er rød",
         any("ingen pro_limit" in f for f in fund), str(fund[:2]))

    ægte_blok = pro_table.blok  # mutationen skal kun ramme `blok`
    for navn, mutation, forventet in (
        ("grænselinjen forsvinder fra generatoren",
         lambda b: re.sub(r'\n<p class="pro-note pro-limit">.*?</p>', "", b),
         "står ikke i blokken"),
        ("grænsen flyttes op i prisnoten uden klassen",
         lambda b: re.sub(r'\n<p class="pro-note pro-limit">(.*?)</p>',
                          lambda m: "", b).replace(
             '<p class="pro-note">',
             f'<p class="pro-note">{catalog["products"][nøgle]["pro_limit"]["en"]} · ', 1),
         "grænselinjen"),
    ):
        try:
            pro_table.blok = lambda *a, _m=mutation, **kw: _m(ægte_blok(*a, **kw))
            with tempfile.TemporaryDirectory() as tmp:
                rod = _kopi(Path(tmp), lambda rod: _tegn(rod, catalog))
                fund = dom(catalog, rod)
                tjek(f"{navn} er rød",
                     any(forventet in f for f in fund), str(fund[:2]))
        finally:
            pro_table.blok = ægte_blok

    # Og med den rigtige generator er alt grønt igen — ellers har mutationerne
    # bare gjort porten rød for alt.
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), lambda rod: _tegn(rod, catalog))
        fund = dom(catalog, rod)
        tjek("genoptegnede sider med grænse er grønne", not fund, "; ".join(fund[:2]))

    # 15b. En `pro_limit` med `&`. To kontroller, fordi dommen skal dømme
    #     **det læseren ser** og ikke den rå markup:
    #     (a) korrekt tegnet med `h()` skal være grøn. Generatoren escaper
    #         ampersanden til `&amp;`, så den rå katalogtekst findes ikke i
    #         siden — før 6/10 var dommen rød på præcis den korrekte side
    #         (målt med `&mdash;` i `page-profile-pro`).
    #     (b) en Mutation der skriver en **anden** tekst i grænselinjen skal
    #         stadig være rød. Uden den arm ville unescaping gøre dommen
    #         blind: enhver tekst ville findes, fordi enhver tekst unescapes
    #         til sig selv.
    med_amp = {**catalog, "products": {**catalog["products"], nøgle: {
        **catalog["products"][nøgle],
        "pro_limit": {**catalog["products"][nøgle]["pro_limit"],
                      "en": "No SMS &mdash; no email, check manually"}}}}
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), lambda rod: _tegn(rod, med_amp))
        fund = dom(med_amp, rod)
        tjek("pro_limit med & er grøn når siden er tegnet korrekt",
             not fund, "; ".join(fund[:2]))

    forkert = pro_table.blok
    try:
        pro_table.blok = lambda *a, **kw: re.sub(
            r'(<p class="pro-note pro-limit">)No SMS &amp;mdash; no email, check manually(</p>)',
            r"\1No alerts at all\2",
            forkert(*a, **kw).replace(
                '<p class="pro-note">',
                '<p class="pro-note">No SMS &amp;mdash; no email, '
                'check manually · ', 1), 1)
        with tempfile.TemporaryDirectory() as tmp:
            rod = _kopi(Path(tmp), lambda rod: _tegn(rod, med_amp))
            fund = dom(med_amp, rod)
            tjek("pro_limit med & er rød når grænselinjen siger noget andet",
                 any("grænselinjen" in f for f in fund), str(fund[:2]))
    finally:
        pro_table.blok = forkert

    for linje in fejl:
        print(f"  FEJL  {linje}")
    print(f"check-pro-table-selftest: {'OK' if not fejl else 'RØD'}"
          f" ({talt[0] - len(fejl)}/{talt[0]} kontroller)")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="kør portens egen kontrol af sig selv")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    fund = dom(pro_table.load())
    for linje in fund:
        print(linje)
    if fund:
        print(f"\npro-table: RØD — {len(fund)} fund")
        return 1
    print(f"pro-table: GRØN — {PRODUKTSIDE} produktsider og {VÆRKTØJSSIDE} "
          f"værktøjssider har den samme to-rækkers-tabel, tegnet af katalogen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
