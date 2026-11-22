#!/usr/bin/env python3
"""Gør købsknappen i hvert pro-kort til katalogens.

Baggrund (målt 2/10): de tretten værktøjssider har hver sit pro-kort, og hver
af dem skriver **pris og købslink i hånden** inde i en inline `<script>`:

    html += '<a class="btn" href="https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03"
             rel="nofollow noopener">Buy EUComply Pro — $79/year per website</a>';

`check_own_prices.py` læser beløb i sidernes **markup**, og en pris i et inline
script er en pris ingen port kan se — målt 1/10 på præcis denne måde. Så de tretten
knapper kunne stå på $79, mens Stripe sagde $89, og ingen kørsel ville have sagt
det. Samme fejlform som `check_pro_table.py` blev skrevet for (dom 6): listen var
skrevet til én side, mens den blev tegnet på tretten.

Derfor er knappen her **generatorens**, ikke sidens:

    python3 tools/pro_card.py             # vis siderne og deres knap
    python3 tools/pro_card.py --check     # dom, exit 1 ved afvigelse
    python3 tools/pro_card.py --apply     # ret knappen, så den bliver katalogens
    python3 tools/pro_card.py --self-test # 9 kontroller

Dommen er tre ting, fordi hver især kan være grøn mens den anden er rød:

  1. **Linket skal være katalogets eget.** Hvert `buy.stripe.com`-link i et
     pro-kort skal være `payment_link` for et produkt i `stripe_catalog.json`.
     Et krydsprodukt (kontakt-Clean-Copys knap på `/cookie-check`) er rødt,
     og det er den fejlform der får en køber til at betale for det forkerte.
  2. **Teksten skal være katalogens**, sammensat af produktnavn + `price_usd` +
     et ord fra `billing_periods.words` + `scope`. Samme ordliste som dom 4 i
     `check_own_prices.py` bruger, så de to kan ikke være uenige, og
     `pro_table.beløb()` er den ene sted, der gør sig den stramme.
  3. **Sproget kommer fra stien**, ikke fra den eksisterende knap. Ellers ville
     «Buy» på en dansk side være grøn, fordi porten bare valgte det samme sprog
     som den fandt. Sådan er `/da/cookie-check` dømt på sin egen tekst.

Og en ratchet på antallet af sider med en købsknap i pro-kortet: en side hvis
pro-kort mister knappen, eller hvor knappen flyttes ud af kortet, skal være
rød — ellers kunne en fejlretelse slette salgsmuligheden og porten være grøn.
Ratchet'en var 14 indtil 22/11-2026, hvor salget af EUComply Pro og Clean Copy
Pro blev lukket; nu er den 1 (`/url-inspector`, Page Profile Pro).

  4. **Et lukket produkt må ikke sælges.** Et link til et produkt med
     `"status": "inactive"` i katalogen er rødt i ethvert pro-kort — Stripe har
     deaktiveret linket, så knappen ender blindt.

Knappens `class` og `style` er sidens egen design (`btn` på nogen, `btn-primary`
på andre) og røres ikke. Kun `href` og knapteksten er generatorens.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pro_table  # noqa: E402  — `beløb()` er den ene sandhed om en pris

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# Målt 2/10: elleve sider sælger EUComply Pro, `/clean-copy-tool` sælger Clean
# Copy Pro og `/url-inspector` sælger Page Profile Pro. De to artikler med et
# pro-kort (`/blog/text-on-image-contrast-check` + den danske) har **ingen**
# købsknap — de linker til `#report` — så de tæller ikke med.
# 9/10: `/da/clean-copy-tool` er det samme værktøj på dansk med den samme
# købsknap, så den tæller som den fjortende. Ratchet'en stiger kun, når en ny
# side rent faktisk får en knap sat op.
# 22/11-2026: salget af EUComply Pro og Clean Copy Pro er lukket, så de tretten
# knapper er fjernet, og `/url-inspector` (Page Profile Pro) er den eneste side
# tilbage med en købsknap i pro-kortet. Ratchet'en går ned med vilje her, og
# dom 4 sørger for at de lukkede knapper ikke kommer tilbage.
VÆRKTØJSSIDER = 1

# Åbningen af et pro-kort: den `<div …>` hvis attributter indeholder `pro-card`.
KORT_RE = re.compile(r'<div\b[^>]*\bclass="[^"]*\bpro-card\b[^"]*"[^>]*>', re.S)

DIV_ÅBN = re.compile(r"<div\b[^>]*>", re.I)
DIV_LUK = re.compile(r"</div\s*>", re.I)


def kort(hl: str) -> tuple[int, int] | None:
    """Hele pro-kortet, målt med balancerede `<div>`-er — ikke med et mønster.

    Målt 2/10, og det er en fejl denne port selv havde: kortene lå i inline
    scripts, så grænsen var «den første `</div>` efter `class="pro-card"`», og
    det holdt kun for kort med **ét** niveau. Da to værktøjssider fik den
    genererede gratis-mod-Pro-tabel, kom der et `.table-wrap`-`<div>` ind i kortet,
    og den første `</div>` blev så tabelens indpakning. Følgen var ikke en rød
    port men en **grøn** én: knappen lå stadig på de to sider, men uden for det
    fundne kort, så ratchet'en på 13 sagde 11, og en knap der flyttes *ud* af
    kortet ville være usynlig for dom 1-3.

    Derfor tælles nu åbne og lukkede tags fra kortets egen `<div>`, og kortet er
    det hele. Uden en afsluttende `</div>` returneres `None`, så kalderen kan
    sige det.
    """
    åb = KORT_RE.search(hl)
    if not åb:
        return None
    dybde = 0
    for m in re.finditer(r"<div\b[^>]*>|</div\s*>", hl[åb.start():], re.I):
        dybde += 1 if not m.group(0).startswith("</") else -1
        if dybde == 0:
            return åb.start(), åb.start() + m.end()
    return None

# En købsknap i et pro-kort: `<a … href="https://buy.stripe.com/…" …>Buy …</a>`.
# `href` og teksten er de to grupper, generatoren ejer.
KNAP_RE = re.compile(
    r'(<a\b[^>]*?href=")(https://buy\.stripe\.com/[A-Za-z0-9]+)("[^>]*>)'
    r'((?:Buy|Køb)[^<]*)(</a>)')


def katalog() -> dict:
    return pro_table.load()


def sprog(rel: str) -> str:
    """Sproget fra **stien**, ikke fra den knap vi er ved at dømme.

    Stierne i porten er relative til `site/`, så den danske mappe hedder `da/`
    og ikke `/da/`. Målt 2/10: kun `/da/` gav engelsk på alle fire
    scanner-sider, fordi de ligger i mappen.
    """
    dele = rel.split("/")
    return "da" if (dele[0] == "da" or "da" in dele[:-1]
                    or rel.endswith("-da.html")) else "en"


def knaptekst(nøgle: str, produkt: dict, lang: str, perioder: dict) -> str:
    """«Buy EUComply Pro — $79/year per website» / «Køb … — $79/år pr. website».

    Prisen er `pro_table.beløb()`, altså `price_usd` + et ord fra
    `billing_periods.words` + `scope`. Den kan derfor ikke glide fra Stripe, og
    den er samme streng som produktsidernes tabel.
    """
    verb = "Køb" if lang == "da" else "Buy"
    return f'{verb} {produkt["name"]} — {pro_table.beløb(nøgle, produkt, lang, perioder)}'


def sider(rod: Path = SITE) -> list[Path]:
    """Alle sider med et pro-kort, i sti-rækkefølge, så porten er deterministisk.

    Målt 2/10: de fire scanner-sider har `class="result-card pro-card"`, de ni
    andre `class="pro-card"`. Søgningen skal derfor ramme **begge** — kun at
    læse den korte form ville have fundet ni af tretten og ratchet'en ville have
    sagt «9 sider», altså grøn på en port der dømmer fire færre.
    """
    # 22/11-2026: søgningen er klassen (`KORT_RE`), ikke strengen
    # «pro-card». Licensnoten på `/scan` sender hændelsen `pro-card-click`,
    # så konverteringstallet i /api/stats lever videre, men den er ikke et
    # pro-kort — en ren strengsøgning dømte den som et kort uden </div>.
    return sorted(p for p in rod.rglob("*.html")
                  if KORT_RE.search(p.read_text(encoding="utf-8")))


def dom(kat: dict | None = None, rod: Path = SITE) -> list[str]:
    kat = kat or katalog()
    perioder = kat.get("billing_periods") or {}
    produkter = kat.get("products") or {}
    links = {p["payment_link"]: (nøgle, p) for nøgle, p in produkter.items()
             if isinstance(p, dict) and p.get("payment_link")}
    fund: list[str] = []
    med_knap = 0
    for fil in sider(rod):
        rel = fil.relative_to(rod).as_posix()
        html = fil.read_text(encoding="utf-8")
        sted = kort(html)
        if not sted:
            fund.append(f"{rel}: pro-kort uden afsluttende </div> — porten kan "
                        f"ikke finde ud hvor knappen hører hjemme")
            continue
        knapper = KNAP_RE.findall(html[sted[0]:sted[1]])
        if not knapper:
            # De to artikler har ingen købsknap, og det er et valg, ikke en fejl.
            continue
        med_knap += 1
        if len(knapper) > 1:
            fund.append(f"{rel}: {len(knapper)} købsknapper i ét pro-kort")
            continue
        for før, link, mellem, tekst, luk in knapper:
            if link not in links:
                fund.append(f"{rel}: købslinket {link} står ikke i katalogen — "
                            f"det er ikke et payment_link for noget produkt")
                continue
            nøgle, produkt = links[link]
            if produkt.get("status") == "inactive":
                fund.append(f"{rel}: pro-kortet sælger {nøgle}, som er lukket for salg "
                            f"({produkt.get('closed')}) — fjern knappen")
                continue
            lang = sprog(rel)
            forventet = knaptekst(nøgle, produkt, lang, perioder)
            if tekst != forventet:
                fund.append(f"{rel}: knappen siger {tekst!r}, katalogen siger "
                            f"{forventet!r} ({nøgle})")
    if med_knap != VÆRKTØJSSIDER:
        fund.append(f"site/: {med_knap} sider har en købsknap i sit pro-kort — "
                    f"porten dømmer {VÆRKTØJSSIDER}. En knap er flyttet ud, "
                    f"slettet eller sat op i en ny side uden at ratchet'en er "
                    f"fulgt med")
    return fund


def ret(kat: dict, rod: Path = SITE) -> int:
    """Sæt hver knaps `href` og tekst til katalogens. Klassen røres ikke."""
    perioder = kat.get("billing_periods") or {}
    links = {p["payment_link"]: (nøgle, p) for nøgle, p in
             (kat.get("products") or {}).items()
             if isinstance(p, dict) and p.get("payment_link")}
    ændret = 0
    for fil in sider(rod):
        html = fil.read_text(encoding="utf-8")
        rel = fil.relative_to(rod).as_posix()
        lang = sprog(rel)
        # Kun **inde i kortet**. En sides hovedknap ligger uden for pro-kortet
        # og er skrevet med vilje pr. side, så en erstatning over hele filen
        # ville slå den i stykker.
        sted = kort(html)
        if not sted:
            continue

        def ny(m: re.Match) -> str:
            før, link, mellem, tekst, luk = m.groups()
            if link not in links:
                return m.group(0)
            nøgle, produkt = links[link]
            return før + link + mellem + knaptekst(nøgle, produkt, lang, perioder) + luk

        ny_kort = KNAP_RE.sub(ny, html[sted[0]:sted[1]])
        ny_html = html[:sted[0]] + ny_kort + html[sted[1]:]
        if ny_html != html:
            fil.write_text(ny_html, encoding="utf-8")
            ændret += 1
            print(f"  knap sat til katalogens: {rel}")
    return ændret


def _kopi(rod: Path, muter) -> Path:
    for fil in sider(ROOT / "site"):
        mål = rod / fil.relative_to(ROOT / "site")
        mål.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fil, mål)
    muter(rod)
    return rod


def self_test() -> int:
    fejl: list[str] = []
    talt = [0]

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        talt[0] += 1
        if not sand:
            fejl.append(f"{navn}{': ' + detalje if detalje else ''}")

    kat = katalog()

    tjek("målingen er grøn på site/", not dom(kat), "; ".join(dom(kat)[:3]))

    def skriv(rod: Path, rel: str, gammel: str, ny: str) -> None:
        fil = rod / rel
        tekst = fil.read_text(encoding="utf-8")
        assert gammel in tekst, (rel, gammel)
        fil.write_text(tekst.replace(gammel, ny, 1), encoding="utf-8")

    CC = "https://buy.stripe.com/6oU4gy76PgvgdBIdAXbMQ00"
    PP = "https://buy.stripe.com/9B6eVcgHp7YK69ggN9bMQ04"
    SIDE = "url-inspector/index.html"
    KNAP = "Buy Page Profile Pro — $19/year"
    # Indtil 22/11-2026 kørte mutationerne på `/cookie-check` (EUComply Pro).
    # Den side har ikke længere en købsknap, så de kører på den eneste side,
    # der har: `/url-inspector`.

    # 1. Et lukket produkt: Clean Copys knap i Page Profiles pro-kort. Linket
    #    er deaktiveret i Stripe, så knappen fører ingen steder hen.
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), lambda rod: skriv(rod, SIDE, PP, CC))
        fund = dom(kat, rod)
        tjek("et lukket produkts link er rødt",
             any("lukket for salg" in f and "clean-copy-pro" in f for f in fund), str(fund[:2]))

    # 1b. Samme link i et katalog, hvor Clean Copy Pro stadig sælges: så er det
    #     et krydsprodukt, og knapteksten skal være Clean Copys — kunden ville
    #     ellers betale for det forkerte produkt.
    åben = {**kat, "products": {**kat["products"], "clean-copy-pro": {
        k: v for k, v in kat["products"]["clean-copy-pro"].items() if k != "status"}}}
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), lambda rod: skriv(rod, SIDE, PP, CC))
        fund = dom(åben, rod)
        tjek("krydsprodukt-link er rødt",
             any("Buy Clean Copy Pro" in f for f in fund), str(fund[:2]))

    # 2. En håndskrevet pris i knappen. Mutationen rammer **knappens egen
    #    tekst** og ikke den første `$19` på siden: siden har også en genereret
    #    tabel med samme beløb, så en almindelig erstatning ville ramme tabellen.
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), lambda rod: skriv(
            rod, SIDE, KNAP, "Buy Page Profile Pro — $15/year"))
        fund = dom(kat, rod)
        tjek("håndskrevet pris i knappen er rød",
             any("katalogen siger" in f for f in fund), str(fund[:2]))

    # 3. Et link der ikke findes i katalogen — et dødt eller fremmed link.
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), lambda rod: skriv(
            rod, SIDE, PP, "https://buy.stripe.com/0UkIk4StpN"))
        fund = dom(kat, rod)
        tjek("ukendt købslink er rødt",
             any("står ikke i katalogen" in f for f in fund), str(fund[:2]))

    # 4. Dansk sti med engelsk tekst. Sproget læses fra stien, så en engelsk
    #    knap på en dansk side kan ikke være grøn ved at porten bare følger den
    #    knap den finder. Der er ingen dansk side med pro-kort i dag, så
    #    kopien lægges under `da/`.
    def dansk_kopi(rod: Path) -> None:
        (rod / "da" / "url-inspector").mkdir(parents=True, exist_ok=True)
        shutil.copy2(rod / SIDE, rod / "da" / SIDE)
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), dansk_kopi)
        fund = dom(kat, rod)
        tjek("engelsk knap på dansk side er rød",
             any(f.startswith("da/url-inspector") and "Køb Page Profile Pro" in f for f in fund),
             str(fund[:2]))

    # 5. Ratchet'en: knappen forsvinder fra et pro-kort. Uden denne tjek ville
    #    dom 1–3 være grønne, fordi der så ikke var noget at dømme — og den
    #    tabte salgsmulighed ville være usynlig.
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), lambda rod: skriv(rod, SIDE, KNAP, "Se hvad Pro tilføjer"))
        fund = dom(kat, rod)
        tjek("tabt købsknap er rød",
             any("købsknap i sit pro-kort" in f for f in fund), str(fund[:2]))

    # 6. Et pro-kort med et **niveau mere** — som den genererede gratis-mod-
    #    Pro-tabel i sin `.table-wrap`. Grænsen var engang «den første
    #    `</div>`», så indpakningen om tabellen blev kortets afslutning, og
    #    knappen lå uden for det fundne kort.
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), lambda rod: skriv(
            rod, SIDE,
            "<!-- pro-table:start -->",
            "<div class=\"table-wrap\"><table class=\"compare\"><tr>"
            "<td>free</td></tr></table></div>"
            "<!-- pro-table:start -->"))
        fund = dom(kat, rod)
        tjek("kort med et indlejret div taber ikke knappen",
             not any("købsknap i sit pro-kort" in f for f in fund), str(fund[:2]))

    # 7. Ret skal gøre det røde grønt igen — ellers er `--apply` død kode.
    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp), lambda rod: skriv(
            rod, SIDE, KNAP, "Buy Page Profile Pro — $15/year"))
        ret(kat, rod)
        tjek("ret gør en håndskrevet pris grøn igen", not dom(kat, rod),
             "; ".join(dom(kat, rod)[:2]))

    for linje in fejl:
        print(f"  FEJL  {linje}")
    print(f"check-pro-card-selftest: {'OK' if not fejl else 'RØD'} "
          f"({talt[0] - len(fejl)}/{talt[0]} kontroller)")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="sæt hver pro-kort-knap til katalogens")
    parser.add_argument("--check", action="store_true", help="dom (standard)")
    parser.add_argument("--self-test", action="store_true",
                        help="kør portens egen kontrol af sig selv")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    kat = katalog()
    if args.apply:
        antal = ret(kat)
        fund = dom(kat)
        if fund:
            for linje in fund:
                print(linje)
            return 1
        print(f"pro-card: {antal} knapper sat til katalogens, "
              f"{VÆRKTØJSSIDER} sider dømt grønne")
        return 0
    fund = dom(kat)
    for linje in fund:
        print(linje)
    if fund:
        print(f"\npro-card: RØD — {len(fund)} fund")
        return 1
    print(f"pro-card: GRØN — {VÆRKTØJSSIDER} pro-kort køber til katalogens "
          f"eget link og pris")
    return 0


if __name__ == "__main__":
    sys.exit(main())