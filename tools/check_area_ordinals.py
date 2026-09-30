#!/usr/bin/env python3
"""Et ordtal i brødteksten skal være målt mod den liste siden selv udgiver.

Baggrund (review 30/9): `site/nis2-gap-assessment-da.html:125` skrev "Det tiende
område — sikkerhed ved anskaffelse, udvikling og vedligeholdelse". Siden
publicerer de ti områder i en nummereret liste to afsnit ovenfor, og i den er
"anskaffelse, udvikling og vedligeholdelse" **det femte**. Ni linjes række ned
på samme side stod "det fjerde område" for leverandørsikkerhed, som *er* nr. 4 —
så sidekonventionen afgjorde det, ikke en tolkningssag. Den note er den der
sælger EUComply Pro ("er det eneste, der kan måles på en rigtig adresse"), så
den pegede på det forkerte område i sin egen salgstale.

Fejlen overlevede to læsninger, fordi ingen målte den:

  * `check_rule_claims.py` tæller tal og priser, ikke ordtal mod en række.
    Sådan et løfte er en påstand om **rækkefølge**, og porten kendte slet ikke
    begrebet.
  * Den publicerede liste er statisk HTML, mens spørgsmålstabellen er JS. De to
    rækker er ens i dag, men intet holdt dem sammen, og en læser tæller ned ad
    den han kan *se* — altså HTML-listen.

Denne port gør derfor to ting, begge målt og ikke husket:

  1. **Ordtal.** Enhver "det Nte område" / "the Nth area" i brødteksten skal have
     et navn ved siden af sig, og det navn skal stå på den plads i den liste
     siden selv udgiver. Kan navnet ikke findes, eller står det på flere pladser,
     er løftet **udømt** — det er en fejl, ikke et grønt kort. En port der
     springer over det den ikke kan dømme, er grøn ved præcis den fejl den er
     skrevet imod.
  2. **Antal.** "de ti foranstaltningsområder" måles mod længden af den liste
     siden udgiver, så listen og overskriften ikke kan glide fra hinanden.

Kun sider med en publiceret, nummereret liste af hele navne kan dømme et
**ordtal** — porten skal kunne slå navnet op i en liste læseren kan tælle ned
ad. Målt 30/9: præcis fire sider i `site/` har en sådan liste (`<ul
class="findings">` med mindst fire `<li><strong>`) — de to NIS2-gapanalyser
(10 områder) og de to cookie-tjek (4).

Resten af overfladen har syv **antalsløfte** ("de ti minimumsområder"), og de
blev målt uden at blive dømt. Det var portens egen fejlform: dens docstring
siger «et løfte den ikke kan dømme er en fejl, ikke et grønt kort», og sådan
udskrev den dem — grøn. Nu dømmes de:

  3. **Antal uden egen liste.** Et antalsløfte der handler om NIS2's
     *minimums*-sæt ("de ti minimumsområder", "the ten minimum
     risk-measure areas") er en påstand om direktivets ti foranstaltningsområder,
     og den kan dømmes uden sidens egen liste: `NIS2_AREAS` er antallet i
     NIS2 art. 21(2)(a)–(j), og porten kræver selv at tallet findes i en
     publiceret liste i repoet, så konstanten ikke kan glide fra det site der
     understøtter den. Ordtal på en sådan side kan *derimod* ikke dømmes —
     rækkefølgen findes kun i en liste siden udgiver — og så siger porten
     "kan ikke dømmes" i stedet for at tie.

Alt, hvad porten stadig ikke dømmer, udskrives i `--list` og tælles **uden** i
OK-tallet. Målt 30/9 på hele `site/`: nul.

    python3 tools/check_area_ordinals.py             # alle ordtal mod den liste
    python3 tools/check_area_ordinals.py --list      # de målte lister
    python3 tools/check_area_ordinals.py --self-test # beviser at porten rødmer
"""
from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Den publicerede liste. Kun statisk HTML tæller: en `<ul>` der bygges i JS
# (`'<ul class="findings">'+…`) er et resultat, ikke den liste læseren tæller
# ned ad, og den skal ikke kunne bruges som måleværktøj.
RE_LIST = re.compile(r'<ul[^>]*class="findings"[^>]*>(.*?)</ul>', re.DOTALL)
RE_ITEM = re.compile(r"<li[^>]*>\s*<strong>(.*?)</strong>", re.DOTALL)
RE_SCRIPT = re.compile(r"<script\b.*?</script>", re.DOTALL | re.IGNORECASE)
RE_TAG = re.compile(r"<[^>]+>")
RE_PARA = re.compile(r"<p\b[^>]*>(.*?)</p>", re.DOTALL | re.IGNORECASE)

# Fire navne er målet for at en liste er en *nummereret* liste og ikke en
# tilfældig `findings`-række. Målt 30/9 på hele `site/`: de fire lister har
# henholdsvis 10, 10, 4 og 4 `<li><strong>`, og ingen anden `<ul class="findings">`
# i repoet har fire eller mere. Grænsen er ikke et arbitrært tal — den er
# målt, og selftesten genskaber den.
MIN_ITEMS = 4

# Ordtal i de to sprog siderne faktisk skriver. Tabellen er ord, ikke tal,
# fordi et tal i brødteksten ("10 områder") er et *antal* og dømmes af
# `RE_COUNT` nedenfor — de to skal ikke blandes, ellers ville "det 5. område"
# og "de 5 områder" blive dømt af den samme regel.
ORDINALS: dict[str, int] = {
    # Dansk
    "første": 1, "anden": 2, "tredje": 3, "fjerde": 4, "femte": 5,
    "sjette": 6, "syvende": 7, "ottende": 8, "niende": 9, "tiende": 10,
    # Engelsk
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
}

# Antalsord i de to sprog. Kun 1–12, fordi det er det en NIS2- eller
# cookie-liste kan indeholde; en længere række ville være en påstand om en
# liste porten ikke kan finde, og den skal dømmes som udømt, ikke som rigtig.
COUNT_WORDS: dict[str, int] = {
    "en": 1, "et": 1, "to": 2, "tre": 3, "fire": 4, "fem": 5, "seks": 6,
    "syv": 7, "otte": 8, "ni": 9, "ti": 10, "elleve": 11, "tolv": 12,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}

# Antallet i NIS2's minimumssæt. Kilden er direktivet, ikke denne kode:
# NIS2 (Directive (EU) 2022/2555) art. 21(2)(a)–(j) opremser **ti**
# foranstaltningsområder. Tallet bruges kun til at dømme antalsløfter på sider
# der ikke udgiver deres egen liste, og `check()` kræver at netop så mange
# rækker findes i en publiceret liste i `site/` — ellers er konstanten ikke
# længere understøttet af noget, porten kan efterprøve, og den fejler.
NIS2_AREAS = 10

# Hvad der gør et antalsløfte til et løfte om *minimumssæt*. Ordet "minimum"
# (dansk "mindste", "minimumsområder") er skelningen, fordi det er den
# betegnelse NIS2 selv bruger for art. 21(2)-sættet. Målt 30/9: alle syv
# løfter på sider uden liste rammer denne skelningslinje, og ingen anden
# antalspåstand på en side uden liste gør det — så porten dømmer hele det
# overflade den siger den dømmer, og intet mere.
MIN_SCOPE = re.compile(r"\bminimum\w*|\bmindste\b", re.IGNORECASE)


def _rel(path: Path) -> str:
    """Stien relativ til `site/`, ikke kun filnavnet.

    Målt 30/9: `site/free-tools.html` og `site/da/free-tools.html` findes begge,
    og kun basenavnet gav to fejlmeldinger der så ens ud. Det er ikke en
    kosmetisk forskel — en mutation der rammer den forkerte fil ligner
    fuldstændig en rettelse, fordi porten ikke kan sige hvilken side den
    dømte.
    """
    try:
        return str(path.relative_to(ROOT / "site"))
    except ValueError:
        # Selftesten arbejder i en kopi under /tmp, så stien ligger ikke under
        # `ROOT`. Alt efter `site/` er den samme side, og det er den der skal
        # stå i fejlmeldingen.
        parts = path.parts
        if "site" in parts:
            return str(Path(*parts[parts.index("site") + 1:]))
        return path.name

_ORD_ALT = "|".join(sorted(ORDINALS, key=len, reverse=True))
RE_ORDINAL = re.compile(
    rf"\b(?P<ord>{_ORD_ALT})\s+"
    rf"(?:foranstaltnings\s+|mål\s+|tekniske\s+)?"
    rf"(?:område|areas?|measures?)\b",
    re.IGNORECASE,
)

_COUNT_ALT = "|".join(sorted(COUNT_WORDS, key=len, reverse=True))
# Hovedordet må være sammensat: den danske overskrift siger "De ti
# **foranstaltningsområder**", ét ord, ikke "foranstaltnings områder". En
# mønster der kræver et mellemrum rammer aldrig den danske sætning — målt
# 30/9 i selftestens tredje arm, som var grøn fordi porten aldrig så
# påstanden. Derfor er der et vilkårligt præfiks *inden i* ordet, plus op til
# to løse ord foran ("the ten minimum risk-measure areas").
RE_COUNT = re.compile(
    rf"\b(?:de|the)\s+(?P<word>{_COUNT_ALT})\s+"
    rf"(?:[a-zæøåéü-]+\s+){{0,2}}"
    rf"[a-zæøåéü-]*"
    rf"(?:områder|areas?|measures?)\b",
    re.IGNORECASE,
)


def _text(raw: str) -> str:
    """Tags væk, entities løst, mellemrum foldet, casing væk.

    Casingsen er væk med vilje: prosaen skriver "leverandørsikkerhed" i flere
    små bogstaver, listen skriver "Leverandørsikkerhed". Det er det samme
    navn, og en port der skelner på casing ville dømme en skrivefejl som et
    ubevis løfte.
    """
    return " ".join(html.unescape(RE_TAG.sub(" ", raw)).split()).lower()


def published_list(src: str) -> list[str]:
    """Den nummererede liste siden udgiver, som navne i den rækkefølge.

    scripts er klippet væk først. Det er ikke en brugervis optimering: en
    resultat-liste bygget i JS har hele navne i elementer, der ikke findes i
    kilden, så den ville måle en liste læseren aldrig ser tælle ned ad.
    """
    body = RE_SCRIPT.sub(" ", src)
    best: list[str] = []
    for m in RE_LIST.finditer(body):
        items = [_text(t) for t in RE_ITEM.findall(m.group(1))]
        items = [i for i in items if i]
        if len(items) > len(best):
            best = items
    return best if len(best) >= MIN_ITEMS else []


def _paragraph_of(src: str, pos: int) -> str:
    """Brødteksten i det `<p>` der omslutter `pos`.

    Ordstal læses i afsnit, ikke i linjer: på den danske side står "Det femte
    område" i linje 125 og navnet i linje 126, fordi HTML'en er linjebrudt for
    læsbarhed. En linje-vis læsning ville aldrig finde navnet ved siden af
    ordtallet — samme fejl som `collect()` i `check_rule_claims.py` har med
    ombrudte løfter.
    """
    starts = [m.start() for m in RE_PARA.finditer(src)]
    if not starts:
        return _text(src[max(0, pos - 400):pos + 400])
    start = max((s for s in starts if s <= pos), default=starts[0])
    end = src.find("</p>", start)
    return _text(src[start:end if end != -1 else start + 600])


def _claims(src: str) -> list[re.Match[str]]:
    """Alle ordtals- og antalsløfter i kilden.

    Scripts er **ikke** klippet væk her, i modsætning til `published_list()`:
    to af de syv antalsløfter ligger i inline-JS og er tekst læseren ser, fordi
    siden skriver dem ud. Kilde: `--list` 30/9, målt på hele `site/`.
    """
    return [*RE_ORDINAL.finditer(src), *RE_COUNT.finditer(src)]


def _count_claims(src: str) -> list[re.Match[str]]:
    return list(RE_COUNT.finditer(src))


def anchored_to_nis2(src: str) -> bool:
    """Sider uden egen liste, hvis antalsløfte handler om NIS2's minimumssæt."""
    if published_list(src):
        return False
    return any(MIN_SCOPE.search(m.group(0)) for m in _count_claims(src))


def unjudged_claims(path: Path) -> list[str]:
    """Løfter porten stadig ikke dømmer — målt, men uden dom.

    Målt 30/9 på hele `site/`: nul. De syv antalsløfter der stod her i portens
    første udgave dømmes nu mod `NIS2_AREAS`. Det der kan blive stående er et
    antalsløfte på en side uden liste der ikke handler om minimumssættet — det
    porten ikke kan forankre i noget, og derfor heller ikke skal grønne ved at
    tie om det.
    """
    src = path.read_text(encoding="utf-8")
    if published_list(src) or anchored_to_nis2(src):
        return []
    out = []
    for rx, kind in ((RE_ORDINAL, "ordtal"), (RE_COUNT, "antal")):
        for m in rx.finditer(src):
            out.append(f"{_rel(path)}:{src.count(chr(10), 0, m.start()) + 1}: "
                       f"{kind} {m.group(0)!r}")
    return out


def check_file(path: Path) -> list[str]:
    """Fejlmeldinger for den ene side."""
    src = path.read_text(encoding="utf-8")
    own = published_list(src)
    areas = own
    if not own and anchored_to_nis2(src):
        areas = [""] * NIS2_AREAS   # antal uden navne: kun længden dømmes
    if not areas:
        return []          # ingen publiceret liste og intet at forankre i
    rel = _rel(path)
    errs: list[str] = []

    for m in RE_ORDINAL.finditer(src):
        line = src.count("\n", 0, m.start()) + 1
        claimed = ORDINALS[m.group("ord").lower()]
        if not own:
            errs.append(
                f"{rel}:{line}: {m.group(0)!r} kan ikke dømmes — siden udgiver "
                f"ingen liste, så rækkefølgen i NIS2's {NIS2_AREAS} områder "
                f"findes kun et andet sted")
            continue
        para = _paragraph_of(src, m.start())
        # Alle listerækker hvis navn står i afsnittet. Flere fund er ikke en
        # lighed — det er et løfte porten ikke kan dømme, fordi den ikke ved
        # hvilken række der er tale om.
        hits = [i for i, name in enumerate(areas, 1) if name and name in para]
        if not hits:
            errs.append(
                f"{rel}:{line}: {m.group(0)!r} kan ikke dømmes — ingen af de "
                f"{len(areas)} navne i sidens liste står i samme afsnit")
        elif claimed not in hits:
            found = ", ".join(f"nr. {i} ({areas[i - 1][:40]})" for i in hits)
            errs.append(
                f"{rel}:{line}: {m.group(0)!r} er det {claimed}. område, men "
                f"afsnittet navngiver {found}")
        elif len(hits) > 1:
            errs.append(
                f"{rel}:{line}: {m.group(0)!r} er tvetydigt — afsnittet navngiver "
                + " og ".join(f"nr. {i}" for i in hits))

    # Hvad porten måler løftet imod. Det er ikke det samme på de to veje: en
    # side med egen liste måles mod den, en side uden måles mod art. 21(2)(a)–(j).
    # At skrive "sidens liste" på en side uden liste ville sende en læser ud
    # på en jagt efter noget der ikke findes.
    source = ("sidens liste" if own
              else f"NIS2's minimumssæt (art. 21(2)(a)-(j))")
    for m in RE_COUNT.finditer(src):
        line = src.count("\n", 0, m.start()) + 1
        claimed = COUNT_WORDS[m.group("word").lower()]
        if claimed != len(areas):
            errs.append(
                f"{rel}:{line}: {m.group(0)!r} siger {claimed}, men {source} "
                f"har {len(areas)}")
    return errs


def canonical_ok() -> str | None:
    """Fejl hvis ingen publiceret liste har `NIS2_AREAS` rækker — ellers er
    direktiv-citatet i porten ubekræftet, og de forankrede antalsløfter ville
    være dømt mod et tal intet i repoet understøtter."""
    lengths = set()
    for p in sorted((ROOT / "site").rglob("*.html")):
        areas = published_list(p.read_text(encoding="utf-8"))
        if areas:
            lengths.add(len(areas))
    if NIS2_AREAS in lengths:
        return None
    return (f"canonical: ingen publiceret liste i site/ har {NIS2_AREAS} "
            f"rækker (målte længder: {sorted(lengths)}) — art. 21(2)(a)–(j) "
            f"siger ti, så portens egen forankring kan ikke efterprøves")


def check() -> tuple[list[str], int, int, int, int]:
    """Fejl, sider med liste, sider forankret til NIS2, dømte løfter, udømte."""
    errs: list[str] = []
    canon = canonical_ok()
    if canon:
        errs.append(canon)
    listed = anchored = judged = unjudged = 0
    for path in sorted((ROOT / "site").rglob("*.html")):
        errs.extend(check_file(path))
        src = path.read_text(encoding="utf-8")
        if published_list(src):
            listed += 1
            judged += len(_claims(src))
        elif anchored_to_nis2(src):
            anchored += 1
            judged += len(_claims(src))
        unjudged += len(unjudged_claims(path))
    return errs, listed, anchored, judged, unjudged


def show_list() -> str:
    out = ["Publicerede lister (kilden er den HTML læseren ser):", ""]
    for path in sorted((ROOT / "site").rglob("*.html")):
        src = path.read_text(encoding="utf-8")
        areas = published_list(src)
        if not areas:
            continue
        out.append(f"  {_rel(path)} ({len(areas)}):")
        for i, name in enumerate(areas, 1):
            out.append(f"    {i:>2}. {name}")
        out.append("")

    anchored = [p for p in sorted((ROOT / "site").rglob("*.html"))
                if not published_list(p.read_text(encoding="utf-8"))
                and anchored_to_nis2(p.read_text(encoding="utf-8"))]
    if anchored:
        out += [f"Forankret til NIS2's {NIS2_AREAS} minimumsområder "
                f"(art. 21(2)(a)–(j)) — siden udgiver ingen liste, så kun "
                f"antallet dømmes:", ""]
        for p in anchored:
            src = p.read_text(encoding="utf-8")
            claims = ", ".join(repr(m.group(0)) for m in _claims(src))
            out.append(f"  {_rel(p)}: {claims}")
        out.append("")

    unjudged = [s for p in sorted((ROOT / "site").rglob("*.html"))
                for s in unjudged_claims(p)]
    if unjudged:
        out += ["Målt men ikke dømt — hverken egen liste eller et løfte om "
                "NIS2's minimumssæt at forankre i:", ""]
        out += [f"  {s}" for s in unjudged]
        out.append("")
    return "\n".join(out)


def self_test() -> int:
    """Bevis at porten rødmER på et forkert ordtal, på de rigtige filer."""
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "repo"
        shutil.copytree(ROOT, tmp, ignore=shutil.ignore_patterns(
            ".git", "dist", "node_modules", "__pycache__", ".wrangler"))
        site = tmp / "site"

        # FINDET_MER skriver bare den fejl, mutationen gav, så mutationerne
        # kan genbruges af både ordtal- og antalsarmen.
        def mutate(rel: str, old: str, new: str, label: str) -> list[str]:
            f = site / rel
            original = f.read_text(encoding="utf-8")
            if old not in original:
                fails.append(f"selftest: {label} — {old!r} står ikke i {rel}, så "
                             "mutationen ville springe porten over")
                return []
            f.write_text(original.replace(old, new, 1), encoding="utf-8")
            errs = [e for f2 in sorted(site.rglob("*.html")) for e in check_file(f2)]
            f.write_text(original, encoding="utf-8")
            if not errs:
                fails.append(f"selftest: {label} gav ingen fejl")
            elif not any(rel.split("/")[-1] in e for e in errs):
                fails.append(f"selftest: {label} gav en fejl der ikke nævner den "
                             f"muterede side: " + "; ".join(errs[:3]))
            return errs

        base = [e for f in sorted(site.rglob("*.html")) for e in check_file(f)]
        if base:
            fails.append(f"selftest: fersk checkout har allerede {len(base)} fejl:\n  "
                         + "\n  ".join(base[:5]))
            print("\n".join(fails))
            return 1

        da = "nis2-gap-assessment-da.html"
        # (a) Den fejl reviewen fandt, genskabt præcis som den stod. Mutationen
        # er målet på den rigtige fil, ikke på et syntetisk eksempel — så
        # hvis porten er grøn her, dømmer den ikke sin egen fejlform.
        mutate(da, "Det femte område", "Det tiende område",
               "det tiende område på den danske gapanalyse")
        # (b) Den anden ordtals-påstand på samme side, som *er* rigtig. Uden
        # denne arm ville porten være grøn fordi den afviser alt.
        mutate(da, "det fjerde område", "det tiende område",
               "det fjerde område, der er rigtigt, muteret til tiende")
        # (c) Antalsordet i overskriften, mod listens længde.
        mutate(da, "De ti foranstaltningsområder", "De ni foranstaltningsområder",
               "antallet i overskriften")
        # (d) Negativ kontrol på "kan ikke dømmes": fjerner vi navnet ved
        # siden af ordtallet, må porten IKKE blive grøn. Uden denne arm er
        # armen ovenfor grøn bare fordi porten ignorerer alt den ikke kan
        # slå op — præcis det samme hul som `x-no-paid-path` efterlod.
        f = site / da
        original = f.read_text(encoding="utf-8")
        f.write_text(original.replace("sikkerhed ved anskaffelse, udvikling og "
                                      "vedligeholdelse — er det eneste",
                                      "er det eneste", 1), encoding="utf-8")
        orphan = check_file(f)
        f.write_text(original, encoding="utf-8")
        if not any("kan ikke dømmes" in e for e in orphan):
            fails.append("selftest: et ordtal uden navn ved siden af sig gav ingen "
                         "'kan ikke dømmes'-fejl — porten springer over løfter den "
                         "ikke kan slå op")
        elif not any(da in e for e in orphan):
            fails.append("selftest: 'kan ikke dømmes'-fejlen nævner ikke den "
                         "muterede side: " + "; ".join(orphan[:3]))

        # (e) Selvporten skal dømme den ENGISKE tvilling. Den har samme liste,
        # men ingen ordtalsløfte i dag, så armen tilføjer ét. Sætningen skal
        # *navngive* et listeelement, ellers er den et udømt løfte — se arm (f),
        # der er derfor skrevet som den positive kontrol af præcis det.
        en = site / "nis2-gap-assessment.html"
        orig_en = en.read_text(encoding="utf-8")
        fifth = published_list(orig_en)[4]      # nr. 5 i den målte liste

        def with_english(sentence: str) -> list[str]:
            en.write_text(orig_en.replace(
                '<h2 id="what-heading">',
                f"  <p>{sentence}</p>\n  <h2 id=\"what-heading\">", 1),
                encoding="utf-8")
            errs = check_file(en)
            en.write_text(orig_en, encoding="utf-8")
            return errs

        wrong = with_english(
            f"The tenth area — {fifth} — is the only one we can measure.")
        if not wrong:
            fails.append("selftest: et engelsk 'the tenth area' med navn ved "
                         "siden af sig gav ingen fejl")
        elif not any("nis2-gap-assessment.html" in e for e in wrong):
            fails.append("selftest: den engelske mutation gav en fejl der ikke "
                         "nævner den engelske side: " + "; ".join(wrong[:3]))
        # (f) Positiv kontrol på præcis den fejlform (e) netop dømte: et ordtal
        # uden navn ved siden af sig skal give "kan ikke dømmes", **ikke** være
        # grønt. Uden denne arm er (e) grøn bare fordi porten afviser alt den
        # ikke kan slå op — det samme hul `x-no-paid-path` efterlod.
        orphan_en = with_english("The tenth area is the only one we can measure.")
        if not any("kan ikke dømmes" in e for e in orphan_en):
            fails.append("selftest: et engelsk ordtal uden navn ved siden af sig "
                         "gav ingen 'kan ikke dømmes'-fejl")
        # (f2) Og den positive kontrol der slår imod afvisning: det *rigtige*
        # engelske ordtal med navnet ved siden af sig skal være grønt.
        right = with_english(
            f"The fifth area — {fifth} — is the only one we can measure.")
        if right:
            fails.append("selftest: det rigtige engelske 'the fifth area' med "
                         "navn ved siden af sig giver stadig fejl: "
                         + "; ".join(right[:3]))

        # (g) Ratchet-armen: listen skal kunne *vokse*, så porten ikke låser
        # en fremtidig side fast ved dagens indhold. Tilføjes et navn, skal
        # både ordtal og antal dømme det nye tal. Mutationen indsættes i den
        # `<ul>` der faktisk er statisk — dens closing `</ul>` er den første
        # efter den tiende `<li>`, ikke sideens sidste.
        f = site / da
        original = f.read_text(encoding="utf-8")
        tenth = original.index("<li><strong>Multifaktorgodkendelse")
        grown_at = original.index("</ul>", tenth)
        f.write_text(original[:grown_at]
                     + "    <li><strong>Et nyt område</strong></li>\n"
                     + original[grown_at:], encoding="utf-8")
        grown = check_file(f)
        f.write_text(original, encoding="utf-8")
        if len(published_list(f.read_text(encoding="utf-8"))) != 10:
            fails.append("selftest: ratchet-armen gendannede ikke listen — "
                         "mutationen ramte ikke den tiende række")
        elif not grown:
            fails.append("selftest: listen voksede fra 10 til 11 rækker, men "
                         "ingen fejl — porten har låst listen fast ved dagens "
                         "indhold")

        # (h) De syv antalsløfter der FØR var målt men ikke dømt. Armen
        # muterer tre af dem — to danske og den engelske tvilling — på de
        # rigtige filer. Uden disse ville portens egen docstring lyve: den siger at et
        # løfte den ikke kan dømme er en fejl, og netop disse syv var det
        # undtagelsen den selv havde lavet.
        for rel, old, new, label in (
            ("nis2-check-da.html", "de ti minimumsområder",
             "de tolv minimumsområder", "dansk antalsløfte på /nis2-check-da"),
            ("nis2-check.html", "the ten minimum risk-measure areas",
             "the twelve minimum risk-measure areas",
             "engelsk antalsløfte på /nis2-check"),
            ("da/free-tools.html", "de ti mindste foranstaltningsområder",
             "de ni mindste foranstaltningsområder",
             "dansk antalsløfte på /da/free-tools"),
        ):
            errs_h = mutate(rel, old, new, label)
            if errs_h and not any("siger" in e for e in errs_h):
                fails.append(f"selftest: {label} gav en fejl uden at sige hvad "
                             "løftet sagde: " + "; ".join(errs_h[:3]))

        # (i) Positiv kontrol på præcis de mutationer (h) lige dømte: uændrede
        # skal de være grønne. Uden denne arm er (h) grøn bare fordi porten
        # afviser *alle* antalsløfter på sider uden liste.
        for rel, claim in (("nis2-check-da.html", "de ti minimumsområder"),
                           ("nis2-check.html",
                            "the ten minimum risk-measure areas")):
            f = site / rel
            text = f.read_text(encoding="utf-8")
            if claim not in text:
                fails.append(f"selftest: {rel} indeholder ikke {claim!r}, så "
                             "mutationsarmene ville springe porten over")
            elif check_file(f):
                fails.append(f"selftest: det rigtige løfte {claim!r} i {rel} "
                             "giver fejl: " + "; ".join(check_file(f)[:3]))

        # (j) Et ordtal på en side uden liste kan *ikke* dømmes mod rækkefølgen,
        # fordi porten kun har længden at gå efter. Den skal sige det frem for
        # at være grøn ved et løfte den ikke kan slå op.
        f = site / "nis2-check-da.html"
        original = f.read_text(encoding="utf-8")
        f.write_text(original.replace(
            "de ti minimumsområder",
            "det tredje område i NIS2's minimumssæt, og de ti minimumsområder", 1),
            encoding="utf-8")
        orphan_scope = check_file(f)
        f.write_text(original, encoding="utf-8")
        if not any("kan ikke dømmes" in e for e in orphan_scope):
            fails.append("selftest: et ordtal på en side uden egen liste gav "
                         "ingen 'kan ikke dømmes'-fejl — porten springer over "
                         "løfter den ikke kan dømme")
        elif not any("nis2-check-da.html" in e for e in orphan_scope):
            fails.append("selftest: 'kan ikke dømmes'-fejlen nævner ikke den "
                         "muterede side: " + "; ".join(orphan_scope[:3]))

    for f in fails:
        print(f)
    if fails:
        return 1
    print("selftest OK: porten rødmer på et forkert ordtal, på et antal der "
          "ikke matcher listen, og på et løfte den ikke kan dømme")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true", help="vis de målte lister")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if args.list:
        print(show_list())
        return 0

    errs, listed, anchored, judged, unjudged = check()
    if errs:
        print(f"check_area_ordinals: {len(errs)} fejl — et ordtal i brødteksten "
              f"stemmer ikke med den liste siden udgiver\n")
        for e in errs:
            print("  " + e)
        return 1
    tail = (f", {unjudged} løfter målt men ikke dømt (--list)"
            if unjudged else ", ingen løfter uden dom")
    print(f"check_area_ordinals OK: {judged} ordtals- og antalsløfter dømt, alle "
          f"matcher deres mål ({listed} sider med egen publiceret liste, "
          f"{anchored} forankret til NIS2's {NIS2_AREAS} minimumsområder){tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
