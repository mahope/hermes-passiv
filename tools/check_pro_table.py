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
  4. **Hver funktion i katalogen skal stå i tabellen.** Ellers sælger siden
     noget den ikke viser, og det er præcis den fejl `check_stripe_ctas.py`
     målte på `/clean-copy-tool` og `/activate/`.
  5. **Ingen håndskrevet sammenligning ved siden af.** De otte sider må ikke
     have en anden `<table class="compare">` uden for det genererede område —
     det er det, der gjorde fire sider til fire svar.

    python3 tools/check_pro_table.py             # dom
    python3 tools/check_pro_table.py --self-test # 16 kontroller
"""
from __future__ import annotations

import argparse
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


def synlig_pris(tekst: str) -> set[str]:
    """Beløb i en priscelle. Kun tal med `$` foran: «første 100 køb» og
    «5 enheder» står i samme celle, og de er ikke priser."""
    return set(re.findall(r"\$(\d+(?:\.\d+)?)", tekst))


def dom(catalog: dict, root: Path = ROOT) -> list[str]:
    fund: list[str] = []
    perioder = catalog.get("billing_periods") or {}
    produkter = catalog.get("products") or {}
    sider = catalog.get("pro_table_pages")
    if not isinstance(sider, list) or len(sider) != PRODUKTSIDE:
        fund.append(f"katalog: pro_table_pages skal være præcis {PRODUKTSIDE} "
                    f"sider, fandt {len(sider) if isinstance(sider, list) else sider!r}")
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
        if not egen_side:
            if post.get("kind") != "tool":
                fund.append(f"{rel}: er ikke {nøgle}s egen side, så den skal "
                            f"mærkes kind=tool med sine egne free_features "
                            f"(nu låner den {nøgle}s liste, der er skrevet "
                            f"til en anden side)")
            egne = post.get("free_features")
            if not isinstance(egne, list) or not egne:
                fund.append(f"{rel}: mangler egne free_features")
            else:
                for feature in egne:
                    hvor = str(feature.get("where") or "")
                    labels = (feature.get("labels") or {}).get(lang) or []
                    if not labels:
                        fund.append(f"{rel}: egne free_features "
                                    f"{feature.get('id')!r} har ingen {lang}-labels")
                    if not hvor.startswith(rel):
                        fund.append(f"{rel}: egne free_features "
                                    f"{feature.get('id')!r} peger på {hvor[:60]!r} "
                                    f"og ikke på siden selv — så funktionen er "
                                    f"ikke dokumenteret her")
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
                                   post.get("free_features")).strip()
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

        # 4. Alle katalogens funktioner skal stå i tabellen.
        for nøgle_fil in ("free_features", "pro_features"):
            kilder = (post.get("free_features") if nøgle_fil == "free_features"
                      else None) or produkt.get(nøgle_fil) or []
            for feature in kilder:
                varianter = (feature.get("labels") or {}).get(lang) or []
                if not varianter:
                    fund.append(f"{rel}: {nøgle} {feature.get('id')!r} har "
                                f"ingen {lang}-labels i katalogen")
                    continue
                if not any(v.lower() in blok.lower() for v in varianter):
                    fund.append(f"{rel}: tabellen nævner ikke "
                                f"{nøgle_fil} {feature.get('id')!r} "
                        f"(første label: {varianter[0]!r})")

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
    print(f"pro-table: GRØN — {PRODUKTSIDE} produktsider har den samme "
          f"to-rækkers-tabel, tegnet af katalogen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
