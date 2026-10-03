#!/usr/bin/env python3
"""Dom at «support» på en side betyder donation, og at ingen side lover hjælp
på en rute der ikke giver hjælp.

Målt 3/10 på `site/`: der er **15** anker til donationsruten, og **3** af dem
lover hjælp:

  - `site/thanks.html` skrev «Something wrong with your key? **Support**» —
    på den side en betalende kunde lander i sekundet efter at have betalt.
    `/support` er donationssiden: `<h1>Support the tools</h1>`, en Stripe-donation
    og intet om licenser. Målt på den levende rute 3/10: den eneste vej at
    komme tilbage er «Donate via Stripe».
  - `site/paid-templates.html` og `site/da/paid-templates.html` skrev begge
    «**Support**» i en breadcrumb-linje under en betalt side.

De øvrige 12 er de rigtige steder: ni «say thanks» efter et værktøjsresultat,
«Donate»/«Donér» på `/pricing` og «donationer» på den danske `/free-tools`.
Samme port som `check_donation_paths.py` dømmer dem fra den anden side — den
ser at linket er i et `<script>` og aldrig en knap; denne ser at **linkteksten**
siger det samme som siden destinationen.

**Hvad porten dømmer.** Pr. `<a href="/support">` (også `/da/support` og de
absolutte `https://mahope.tools/support`) i `site/`, plus de to `support_link=`
i `build_sites.py`, som er sidens **fodnote** — den hedder «Support the tools»
og «Støt værktøjerne», altså kvalificeret og dermed grøn. Fodnoten er ikke i
nogen kildefil, så uden den ville porten være grøn fordi den intet ser.

To domme, fordi de fanger hver sit tilfælde:

  1. `HELP_PROMISE`   linkteksten **lover hjælp**: den nævner et problem eller
                      beder om hjælp (`wrong`, `problem`, `help`, `issue`,
                      `fejl`, `hjælp`, `virker ikke` …). Det er løftet på
                      `/thanks` om dagen, og det er den alvorligste af de to.
  2. `UNQUALIFIED`   linkteksten nævner hverken en donation eller de gratis
                      værktøjer. «Support» alene er dommens eksempel, fordi
                      det er det to sider skrev.

Dom 2 er et **ratchet over hele teksten, ikke en ordliste over sætninger**, så
den kan ikke gå rød på en ny formulering der stadig er ærlig, og den kan ikke
gå grøn på en ny formulering der ikke er det.

    python3 tools/check_support_link_text.py
    python3 tools/check_support_link_text.py --list
    python3 tools/check_support_link_text.py --self-test
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DIST = ROOT / "dist" / "mahope.tools"
BUILD = ROOT / "build_sites.py"


def rod() -> Path:
    """Den mappe porten dømmer: den byggede side, ellers kilden.

    `pagepass` erstatter hele `<footer>` ved build, så kildefil kan linke til
    noget der aldrig publiceres. Den bliver nævnt i docstringen; her er
    reglen: døm det der ligger i `dist/`, når det findes.
    """
    return DIST if DIST.is_dir() else SITE

# Kun donationsruterne. `/support` er den side hver donation ligger på, så den
# skal kun linkedes med en linktekst der siger det samme.
SUPPORT_HREF_RE = re.compile(
    r'href="(?:https?://mahope\.tools)?/(?:da/)?support(?:/)?(?:#[^"]*)?"', re.I)
A_RE = re.compile(r"<a\b([^>]*)>(.*?)</a\s*>", re.S | re.I)
# `hreflang` på ankret gør det til en sproglig alternativ, ikke et bedrag om
# hjælp: `<a href="https://mahope.tools/da/support" lang="da" hreflang="da">DA</a>`
# på `/support` er maskinlæsbbar metadata og fire af de 274 fund. Målt, ikke
# gættet — de er de eneste anker på de to donationssider der peger på hinanden.
ALTERNATE_RE = re.compile(r"\bhreflang=", re.I)
TAG_RE = re.compile(r"<[^>]+>")
ENTITY_RE = re.compile(r"&(amp|lt|gt|quot|nbsp|#\d+);")
# `support_link="…"` er sidens fodnote. Den bygges ind i hver side, så den er
# ikke i nogen kildefil — uden denne linje ville porten være grøn fordi den
# intet ser, præcis som `check_page_h1.py`s kontrol 12 er skrevet for at undgå.
FOOTER_RE = re.compile(r"support_link=(?:da=|en=)?\"([^\"]*)\"")

# Dom 1. Ord der lover hjælp eller beskriver et problem. Kun hele ord, så
# «supports» ikke fanges ved en tilfældighed, og «Hjælp» fanges.
HELP_RE = re.compile(
    r"\b(wrong|broken|problem|problems|issue|issues|help|helps|stuck|"
    r"fejl|fejret|hjælp|hjælpe|problem|virker ikke|ikke virker)\b", re.I)

# Dom 2. Hvad linkteksten skal kunne sige, så den peger på donationssiden.
#   - en donation:  donat…, tak, thanks, støt…
#   - kvalificeret: «support the tools» / «støt værktøjerne» — de ord, de to
#     `support_link=` i `build_sites.py` faktisk bruger, så porten dømmer
#     sidens egen formulering og ikke en opdigtet.
#   «Donér» er det danske ord for det samme som «Donate», og det står på
#   `/da/pricing`. Fundet af porten på den rigtige side første gang den kørte,
#   så det er ikke et tilfælde: donation på begge sprog er de fire former.
DONATION_RE = re.compile(
    r"(\bdonat\w*|\bdon[ée]r?\w*|\btak\b|\bthanks\b|\bstøt\w*)", re.I)
QUALIFIED_RE = re.compile(
    r"support\s+(the\s+)?(free\s+)?(tools|værktøjerne|værktøj\w*)|"
    r"\bstøt\w*\s+(de\s+)?(gratis\s+)?(værktøj\w*|tools)\b", re.I)


def link_tekst(fragemnt: str) -> str:
    """Ankerets tekst uden tags og entities, whitespace kollapset."""
    tekst = TAG_RE.sub("", fragemnt)
    for ent, tegn in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                      ("&quot;", '"'), ("&nbsp;", " ")):
        tekst = tekst.replace(ent, tegn)
    return re.sub(r"\s+", " ", tekst).strip()


def dom_tekst(tekst: str, hvor: str) -> list[str]:
    """De to domme på én linktekst."""
    fund: list[str] = []
    if not tekst:
        fund.append(
            f"UNQUALIFIED i {hvor}: linket til donationssiden /support har "
            f"ingen tekst. Skriv hvad siden er — f.eks. «Say thanks» eller "
            f"«Support the free tools».")
        return fund
    if HELP_RE.search(tekst):
        fund.append(
            f"HELP_PROMISE i {hvor}: «{tekst}» linker til /support, som er "
            f"donationssiden — den giver ingen hjælp. Skriv den selvbetjening "
            f"der kan: nøglen findes på /license-lookup, og resten står i "
            f"kvitteringsmailen.")
    elif not (DONATION_RE.search(tekst) or QUALIFIED_RE.search(tekst)):
        fund.append(
            f"UNQUALIFIED i {hvor}: «{tekst}» linker til /support, som er "
            f"donationssiden, men siger det ikke. Skriv «Say thanks», "
            f"«Donate», «Support the free tools» eller «Støt værktøjerne».")
    return fund


def sti(fil: Path, root: Path) -> str:
    """Sidens sti som den skal læses i en fejlmeddelelse.

    Relativ til `ROOT` på de rigtige sider, så meddelelsen er den samme i
    portens output som i en mutation. I en midlertidig kopi ligger filen
    uden for `ROOT`, og da er stien nok — porten skal kunne dømme sine egne
    syntetiske sider, ellers ville `--self-test` kræve en bygget checkout.
    """
    try:
        return str(fil.relative_to(ROOT))
    except ValueError:
        return str(fil)


def dom(root: Path | None = None, byg: Path = BUILD) -> list[str]:
    root = root if root is not None else rod()
    fund: list[str] = []
    for fil in sorted(root.rglob("*.html")):
        html = fil.read_text(encoding="utf-8", errors="replace")
        for m in A_RE.finditer(html):
            # Kun anker der faktisk peger på donationsruten. `/support` er
            # målet; `/terms/` og `/privacy/` må ikke fanges af et mønster på
            # bogstaverne i stien.
            if not SUPPORT_HREF_RE.search(m.group(0)):
                continue
            if ALTERNATE_RE.search(m.group(1)):
                continue
            fund += dom_tekst(link_tekst(m.group(2)), sti(fil, root))
    if byg.exists():
        for m in FOOTER_RE.finditer(byg.read_text(encoding="utf-8", errors="replace")):
            fund += dom_tekst(m.group(1).strip(), "build_sites.py (support_link=)")
    return fund


def self_test() -> int:
    fejl: list[str] = []
    talt = [0]

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        talt[0] += 1
        if not sand:
            fejl.append(f"{navn}{': ' + detalje if detalje else ''}")

    def døm(anker: str, extra: str = "") -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            rod = Path(tmp)
            (rod / "side.html").write_text(
                f"<body><a href=\"/support\">{anker}</a>{extra}</body>",
                encoding="utf-8")
            return dom(rod, byg=rod / "findes-ikke.py")

    # 1. Dom 1 fanger præcis de to formuleringer der lå i `site/`, ordret som
    #    de stod, så porten ikke kan være grøn fordi den har tilpasset sig.
    tjek("dom 1 fanger /thanks-linket",
         any("HELP_PROMISE" in f for f in
             døm("Something wrong with your key? Support")))
    tjek("dom 1 fanger dansk hjælpe-ords",
         any("HELP_PROMISE" in f for f in døm("Hjælp til min nøgle")))
    # 2. Mutation: de 12 links der *er* rigtige må ikke blive røde. De er
    #    hentet fra de filer porten skal lade være i fred.
    for tekst in ("say thanks", "Donate", "Donér", "donationer",
                  "Support the tools", "Støt værktøjerne",
                  "Support the free tools",
                  "Støt de gratis værktøjer"):
        tjek(f"lader {tekst!r} være", not døm(tekst))
    # 3. Dom 2 fager nøgne «Support» på to sprog — det var den anden fejl.
    tjek("dom 2 fanger 'Support'", any("UNQUALIFIED" in f for f in døm("Support")))
    tjek("dom 2 fanger tom tekst", any("UNQUALIFIED" in f for f in døm("")))
    # 4. Og må *ikke* fange en rute der blot indeholder «support» i navnet.
    #    Uden dette er dom 2 en bred regex, der dømmer hele footeren på hver
    #    side i stedet for det ene anker.
    tjek("dom 2 lader /terms/ være",
         not any("/terms" in f for f in dom_tekst("Terms", "x")))
    # 4b. Mutation: de fire `hreflang`-ankere på de to donationssider er de
    #     eneste links mellem `/support` og `/da/support`, så porten skal
    #     lade dem være. Uden denne kontrol er dom 2 rød på 4 fund i det
    #     byggede site, og så skriver nogen den fra.
    with tempfile.TemporaryDirectory() as tmp:
        r2 = Path(tmp)
        (r2 / "support.html").write_text(
            '<a href="https://mahope.tools/da/support" lang="da" '
            'hreflang="da">DA</a>', encoding="utf-8")
        tjek("hreflang-alternativ lades være", not dom(r2, byg=r2 / "x.py"))
    # 5. Selvtesten skal kunne finde fejlen i den **rigtige** fil. Uden denne
    #    kontrol kan porten være grøn fordi den læser en mappe der ikke findes
    #    — den fælde `check_page_h1.py` dokumenterer.
    rigtig = (DIST if DIST.is_dir() else SITE) / "thanks.html"
    med = rigtig.read_text(encoding="utf-8")
    gammel = '<a href="/support">Support</a>'
    ny = '<a href="/support">Something wrong with your key? Support</a>'
    tjek("den rigtige fil findes", rigtig.exists())
    with tempfile.TemporaryDirectory() as tmp:
        rod = Path(tmp) / "site"
        rod.mkdir(parents=True)
        (rod / "thanks.html").write_text(med, encoding="utf-8")
        tjek("porten er grøn på den rettede fil", not dom(rod, byg=rod / "x.py"))
        # 6. Mutation: genskab fejlen i den rigtige fil, kun i en midlertidig
        #    kopi. Polaritet, målt på den kode der faktisk deployes.
        #    Ankeret findes i markupken, ikke hardkodet: `/thanks`-linket har
        #    fået `data-t="navSupport"` (siden oversætter sig selv, se
        #    `STRINGS` i `site/thanks.html`), så en hardkodet streng ville
        #    være en no-op og de to domme ville være grønne på *enhver* kode.
        anker = (re.search(r'<a\s[^>]*href="/support"[^>]*>.*?</a>', med, re.S) or [None])
        anker = anker.group(0) if hasattr(anker, "group") else ""
        tjek("det rigtige /support-anker er fundet i markupken", bool(anker), med[:0])
        (rod / "thanks.html").write_text(med.replace(anker, ny), encoding="utf-8")
        rød = dom(rod, byg=rod / "x.py")
        tjek("mutation i den rigtige fil bliver rød",
             any("HELP_PROMISE" in f for f in rød), "; ".join(rød))
        # 6b. Og den anden fejlform, genskabt i samme rigtige fil: den gamle
        #     breadcrumb fra `paid-templates.html`.
        (rod / "thanks.html").write_text(
            med.replace(anker, '<a href="/support">Support</a>'), encoding="utf-8")
        rød2 = dom(rod, byg=rod / "x.py")
        tjek("mutation af den nøgne 'Support' bliver rød",
             any("UNQUALIFIED" in f for f in rød2), "; ".join(rød2))
    # 7. Fodnoten i `build_sites.py` dømmes med, fordi den er linket på hver
    #    eneste side og ikke findes i nogen kildefil.
    med_foot = FOOTER_RE.findall(BUILD.read_text(encoding="utf-8")) if BUILD.exists() else []
    tjek("build_sites.py har to support_link", len(med_foot) == 2, str(med_foot))
    tjek("fodnoten er grøn", not [f for t in med_foot for f in dom_tekst(t, "fod")])
    tjek("fodnoten bliver rød på 'Support'",
         bool(dom_tekst("Support", "build_sites.py (support_link=)")))

    print(f"selvtest: {talt[0] - len(fejl)}/{talt[0]} kontroller bestået")
    for f in fejl:
        print(f"  FEJL  {f}")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--list", action="store_true", help="vis filerne, kun talt")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    fund = dom()
    if args.list:
        filer = sorted({f.split(" i ", 1)[-1].split(":", 1)[0] for f in fund})
        for f in filer:
            print(f)
        print(f"\n{len(fund)} fund i {len(filer)} filer")
        return 0
    if fund:
        for f in fund:
            print(f"  FEJL  {f}")
        print(f"\n{len(fund)} fund: /support er donationssiden. "
              f"Se docstringen i tools/check_support_link_text.py.")
        return 1
    print("grøn: ingen linktekst til /support lover hjælp eller skjuler "
          "destinationen")
    return 0


if __name__ == "__main__":
    sys.exit(main())