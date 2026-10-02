#!/usr/bin/env python3
"""Dom at en sides `<h1>` er en overskrift og ikke produktets filnavn.

Målt 2/10 på den byggede side: `/site-icons` havde `<h1>site-icons</h1>`, mens
`<title>` siger «Generate favicons, OG images & PWA icons from one». Det er
produktets **filnavn** som overskrift — det største skrifttypefremhævende på
siden, og det siger intet om hvad siden gør. En måling i samme aflevering fandt
**to** mere: `/page-profile` (EN **og** DA) havde `<h1>page-profile</h1>`, og
`/bugbottle-demo` havde `<h1>bugbottle</h1>`. Så **4 af 322** byggede sider.

Ingen port så det. `seo_check.py` tæller `<h1>` og kræver at der er præcis én
— den dømmer *antallet*, ikke *indholdet*. `check_heading_levels.py` dømmer
niveauet i rækkefølge, og `check_duplicate_headings.py` kun gentagelser på
`<h2>`. Alle tre er grønne på `site-icons`, fordi `<h1>site-icons</h1>` er ét
`h1` på niveau 1.

Konsekvensen er reel. Siden er i sitemap, og `<h1>` er det en læser, en
skærmlæser og en søgemaskine ser først: overskriftslisten, dokumentets titel og
udsnittet i søgeresultatet. `/site-icons` stod der som sit eget filnavn, mens
`/url-to-markdown` (`<h1>URL to Markdown</h1>`) og `/text-diff`
(`<h1>Text Diff Checker</h1>`) — samme slags produktside — sagde hvad de gør.
De tre var ikke enige om, hvad en overskrift er.

Denne port gør de **to** dele af fejlen til røde porte, og de er hver især
præcise, så ingen af dem kan gå rød på en rigtig side:

  1. `SLUG_H1`   `<h1>` er et slug: kun små bogstaver, tal og bindestreger, **intet
                 mellemrum**. Det er definitionen af en fil- eller rutetoken, så
                 overskriften er et navn og ikke en sætning. Fanger `site-icons`,
                 `page-profile` og `bugbottle`.
  2. `ROUTE_H1`  `<h1>` er sidens **egen rute** udskrevet, uden at normalisere
                 skilletegn. `/site-icons` med `<h1>site-icons</h1>` er rød, selv
                 om den er skrevet `Site-Icons` — som dom 1 lader igennem, fordi
                 der står store bogstaver i.

**Ingen separator-normalisering i dom 2.** Det er den fælde, porten er skrevet
for at undgå: «Color Blindness Simulator» *er* sluget
`color-blindness-simulator` skrevet med mellemrum og store bogstaver, og 32
sider skriver overskriften sådan. Sammenligner man skilletegn, får man 32 røde
sider der alle er korrekte, og så skriver nogen dommen fra. Derfor sammenligner
dom 2 **råt** med rutens sidste led, så kun den der virkelig har skrevet routen
i overskriften bliver rød.

**Hvad porten *ikke* dømmer:** om overskriften er *god*. Den kan se at
`<h1>site-icons</h1>` er et filnavn; den kan ikke se om «Every icon your site
needs, from one SVG» er den bedste sætning vi kunne skrive. Den del er en
menneskeopgave, og den er lavet i samme opgave — de fire sider er rettet til
opskrifter der siger hvad siden gør, hver bygget af den linje siden selv havde
stående i `tagline`. Havde porten dømt «godt nok», var den en smagsdommer, og
sådan en port bliver slået fra.

    python3 tools/check_page_h1.py            # dom alle sider
    python3 tools/check_page_h1.py --list     # hvilke sider, kun talt
    python3 tools/check_page_h1.py --self-test # 40 kontroller
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

H1_RE = re.compile(r"<h1\b(?![0-9])((?:\s[^>]*)?)>(.*?)</h1\s*>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")
# Samme grund som i `check_heading_levels.py` og `check_duplicate_headings.py`:
# kommentarer og `<script>`/`<style>` er ikke indhold. Vores egen JS bygger
# markup som strenge, og en JSON-LD-blok har tekst der ligner en overskrift.
SPLIT_RE = re.compile(
    r"(<!--.*?-->|<(script|style|noscript|template|svg)\b.*?</\2\s*>)", re.S | re.I)
# Dom 1. Små bogstaver, tal og bindestreger, ét eller flere «ord», **intet
# mellemrum**: `site-icons`, `page-profile`, `bugbottle`, `url-to-markdown`.
# Matcher ikke `Color Blindness Simulator` (mellemrum), `URL to Markdown`
# (mellemrum), `Word Counter` (mellemrum) eller `eaa` i en sætning.
SLUG_H1_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def overskrift(html: str) -> str:
    """Teksten i sidens første `<h1>`, uden tags og entities.

    Samme normalisering som de to overskriftsporte: whitespace kollapser, så
    `<h1>site-icons</h1>` og `<h1>\\n    site-icons\\n  </h1>` er samme fejl.
    """
    for m in H1_RE.finditer(SPLIT_RE.sub("", html)):
        tekst = TAG_RE.sub("", m.group(2))
        # `&amp;` og `&nbsp;` er indhold — h1'er på dansk og engelsk bruger dem,
        # så de skal tælle med, ellers ville porten dømme en side med et
        # tegn, læseren ikke kan se.
        for ent, tegn in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                          ("&quot;", '"'), ("&nbsp;", " ")):
            tekst = tekst.replace(ent, tegn)
        tekst = re.sub(r"\s+", " ", tekst).strip()
        if tekst:
            return tekst
    return ""


def rute(rel: Path) -> str:
    """Sidens rute som den læses i `route_inventory.json`.

    `site/site-icons.html` → `/site-icons`, `site/da/page-profile.html` →
    `/da/page-profile`, `site/url-inspector/index.html` → `/url-inspector`,
    `site/index.html` → `/`. Kun stien, aldrig domænet: dom 2 skal se sidens
    **egen** navn, og det er det sidste led der bærer produktnavnet.
    """
    dele = list(rel.parts)
    if dele and dele[-1].lower() in ("index.html", "index.htm"):
        dele = dele[:-1]
    else:
        dele[-1] = dele[-1].rsplit(".", 1)[0]
    return "/" + "/".join(dele)


def dom(root: Path = SITE) -> list[str]:
    fund: list[str] = []
    for fil in sorted(root.rglob("*.html")):
        rel = fil.relative_to(root)
        h1 = overskrift(fil.read_text(encoding="utf-8", errors="replace"))
        if not h1:
            # Mangler `<h1>` helt, dømmer `seo_check.py` («h1 count 0»). To
            # domme for én fejl gør portens røde længere, ikke mere streng.
            continue
        sti = rute(rel)
        led = sti.rstrip("/").rsplit("/", 1)[-1]
        # Dom 1: overskriften er et slug.
        if SLUG_H1_RE.match(h1):
            fund.append(
                f"SLUG_H1 i {rel}: <h1>{h1}</h1> er produktets filnavn, ikke "
                f"en overskrift. Skriv hvad siden gør."
            )
        # Dom 2: overskriften er sidens egen rute, råt udskrevet. Fanger det
        # dom 1 lader igennem, fordi der står store bogstaver i.
        elif led and h1.lower() == led.lower():
            fund.append(
                f"ROUTE_H1 i {rel}: <h1>{h1}</h1> er sidens egen rute "
                f"({sti}) udskrevet. Skriv hvad siden gør."
            )
    return fund


def self_test() -> int:
    fejl: list[str] = []
    talt = [0]

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        talt[0] += 1
        if not sand:
            fejl.append(f"{navn}{': ' + detalje if detalje else ''}")

    def døm(h1: str, fil: str = "side.html") -> list[str]:
        """Skriv én syntetisk side med overskriften `h1` og døm den.

        De rigtige overskrifter skal dømmes **individuelt** — så porten kan
        bevises grøn på dem én for én, og ikke på en mængde hvor den måske
        springer en fejlform over.
        """
        with tempfile.TemporaryDirectory() as tmp:
            rod = Path(tmp)
            sti = rod / fil
            sti.parent.mkdir(parents=True, exist_ok=True)
            sti.write_text(f"<h1>{h1}</h1>", encoding="utf-8")
            return dom(rod)

    # 1. Dom 1 fanger præcis de fejlformer der lå i `site/`, skrevet som de
    #    stod, så porten ikke kan være grøn fordi den har tilpasset sig.
    for h1 in ("site-icons", "page-profile", "bugbottle", "url-to-markdown",
               "some-new-tool"):
        tjek(f"dom 1 fanger {h1!r}",
             any("SLUG_H1" in f for f in døm(h1)))
    # 2. Mutation: de overskrifter der *er* rigtige må ikke blive røde. De er
    #    hentet fra de sider porten skal lade være i fred — 32 af dem skriver
    #    produktnavnet med mellemrum og store bogstaver, så en forkert
    #    normalisering ville have gjort porten ubrugelig.
    for h1 in ("Color Blindness Simulator", "URL to Markdown", "Word Counter",
               "UUID Generator", "URL Inspector", "Free Downloads",
               "Every icon your site needs, from one SVG",
               "Tjek enhver websides tekniske sundhed",
               "Profile any web page from your terminal",
               "Report a bug and see exactly what gets sent"):
        tjek(f"dom 1 lader {h1[:34]!r} være",
             not any("SLUG_H1" in f for f in døm(h1)))
    # 3. Mutation: dom 2 skal være rød på routen, også når den er skrevet med
    #    store bogstaver — det er præcis det dom 1 lader igennem. Uden denne
    #    kontrol er dom 2 bare en langsommere udgave af dom 1.
    tjek("dom 2 fanger 'Site-Icons' på /site-icons",
         any("ROUTE_H1" in f for f in døm("Site-Icons", "site-icons.html")))
    tjek("dom 2 fanger 'Page-Profile' på /page-profile",
         any("ROUTE_H1" in f for f in døm("Page-Profile", "page-profile.html")))
    # 4. Og den må *ikke* fange det samme med mellemrum og store bogstaver, for
    #    sådan skriver 32 sider deres overskrift. Det er den fælde porten er
    #    skrevet for at undgå.
    for h1, fil in (("Color Blindness Simulator", "color-blindness-simulator.html"),
                    ("URL to Markdown", "url-to-markdown.html"),
                    ("Word Counter", "word-counter.html"),
                    ("UUID Generator", "uuid-generator.html"),
                    ("URL Inspector", "url-inspector/index.html"),
                    ("Free Downloads", "free-downloads.html")):
        tjek(f"dom 2 lader {h1!r} på /{fil} være",
             not any("ROUTE_H1" in f for f in døm(h1, fil)))
    # 5. Mutation: routen skal regnes ud af hele stien, så `/da/page-profile`
    #    ikke sammenlignes med `page-profile` ved et snævert fnug. Samme fejl
    #    på `/url-inspector/index.html`, der er en mappe og ikke en fil.
    with tempfile.TemporaryDirectory() as tmp:
        rod = Path(tmp)
        # Store bogstaver, så det er dom 2 der dømmer og ikke dom 1 — ellers
        # ville kontrollen være grøn af den forkerte grund.
        (rod / "da").mkdir()
        (rod / "da" / "page-profile.html").write_text(
            "<h1>Page-Profile</h1>", encoding="utf-8")
        (rod / "url-inspector").mkdir()
        (rod / "url-inspector" / "index.html").write_text(
            "<h1>URL-Inspector</h1>", encoding="utf-8")
        fund = dom(rod)
        tjek("falsk rute på /da/ er rød",
             any("ROUTE_H1 i da/page-profile.html" in f for f in fund), str(fund))
        tjek("mappe-rute på /url-inspector/ er rød",
             any("ROUTE_H1 i url-inspector/index.html" in f for f in fund),
             str(fund))
        # 6. Mutation: samme to sider efter rettelsen skal være grønne, så
        #    porten kan ikke være grøn fordi den afviser alt.
        (rod / "da" / "page-profile.html").write_text(
            "<h1>Tjek enhver websides tekniske sundhed</h1>", encoding="utf-8")
        (rod / "url-inspector" / "index.html").write_text(
            "<h1>URL Inspector</h1>", encoding="utf-8")
        tjek("rettede sider er grønne", dom(rod) == [], str(dom(rod)))
        # 7. Mutation: en side **uden** `<h1>` får ingen dom her. Det er
        #    `seo_check.py`s job («h1 count 0»), og to domme for én fejl gør
        #    bare portens røde længere.
        (rod / "uden.html").write_text("<h2>En overskrift</h2>", encoding="utf-8")
        tjek("side uden h1 giver ingen dom her", dom(rod) == [], str(dom(rod)))
        # 8. Mutation: `<h1>` i en kommentar eller i vores egen JS er ikke
        #    indhold. Ellers får porten en rød på sider der er korrekte.
        (rod / "kode.html").write_text(
            '<!-- <h1>draft</h1> --><script>el.innerHTML = "<h1>Total visits</h1>"'
            '</script><style>.x::after{content:"<h1>"}</style>'
            "<h1>Gratis værktøjer</h1>", encoding="utf-8")
        tjek("h1 i kommentar, script og style er ikke indhold",
             dom(rod) == [], str(dom(rod)))
        # 9. Mutation: whitespace, tags og entities i overskriften er ikke en
        #    ny fejl — de er den samme sætning skrevet tre måder.
        (rod / "kode.html").write_text(
            "  <h1 class=\"x\">\n    <em>Gratis</em>&amp;&nbsp;værktøjer\n  </h1>  ",
            encoding="utf-8")
        tjek("tags, entities og whitespace i h1 er normaliseret væk",
             dom(rod) == [], str(dom(rod)))
        # 10. Mutation: to sider med samme fejl skal give to domme, ikke ét. En
        #     port der kun rapporterer den første lader den næste stå.
        (rod / "a.html").write_text("<h1>site-icons</h1>", encoding="utf-8")
        (rod / "b.html").write_text("<h1>page-profile</h1>", encoding="utf-8")
        tjek("to sider giver to domme", len(dom(rod)) == 2, str(dom(rod)))
    # 11. Mutation: målingen skal være grøn på `site/` — ellers er den ude i
    #     gaten og blokerer en deploy for en fejl, der ikke findes.
    med_fejl = dom(SITE)
    tjek("målingen er grøn på site/", not med_fejl, "; ".join(med_fejl[:3]))
    # 12. Mutation: genskab den fundne fejlform i en kopi af den rigtige fil, og
    #     porten skal dømme den. Uden dette er kontrol 11 grøn fordi porten
    #     intet ser — og det er præcis fejlen i `check_heading_levels.py`s egen
    #     selvtest, som derfor også har denne kontrol.
    with tempfile.TemporaryDirectory() as tmp:
        rod = Path(tmp)
        (rod / "site-icons.html").write_text(
            (SITE / "site-icons.html").read_text(encoding="utf-8").replace(
                "<h1>Every icon your site needs, from one SVG</h1>",
                "<h1>site-icons</h1>", 1),
            encoding="utf-8")
        fund = dom(rod)
        tjek("genskabt fejl i den rigtige fil er rød",
             len(fund) == 1 and "SLUG_H1" in fund[0], str(fund))
        tjek("dommen peger på filen",
             any("site-icons.html" in f for f in fund), str(fund))
        tjek("dommen siger hvad der skal stå",
             any("Skriv hvad siden gør" in f for f in fund), str(fund))
    # 13. Mutation: porten skal dømme på tværs af domænerne, så en produktside
    #     der flytter til et andet site ikke slipper uden om den samme regel.
    with tempfile.TemporaryDirectory() as tmp:
        rod = Path(tmp)
        (rod / "bugbottle-demo.html").write_text(
            "<h1>bugbottle</h1>", encoding="utf-8")
        tjek("bugbottle-demo er rød",
             any("SLUG_H1" in f for f in dom(rod)), str(dom(rod)))
    # 14. Ratchet: de fire sider porten blev skrevet for skal være grønne, så
    #     en ny `<h1>site-icons</h1>` på en af dem er rød igen. Læst fra
    #     filerne og ikke fra en håndskrevet liste — listen ville være en port,
    #     der skal opdateres før en ny fejl kan grønne, og sådan en port bliver
    #     slået fra (samme grund som `wrong_repo` blev kasseret i
    #     `check_repo_readme.py`).
    for fil, gammelt in (("site-icons.html", "site-icons"),
                         ("page-profile.html", "page-profile"),
                         ("da/page-profile.html", "page-profile"),
                         ("bugbottle-demo.html", "bugbottle")):
        h1 = overskrift((SITE / fil).read_text(encoding="utf-8"))
        tjek(f"{fil} har en overskrift der ikke er filnavnet",
             bool(h1) and h1.lower() != gammelt, repr(h1))
    # 15. Mutation: den danske tvilling skal have en overskrift på dansk. En
    #     port der lader `/da/` få den engelske sætning ville være halvt løs.
    da = overskrift((SITE / "da" / "page-profile.html").read_text(encoding="utf-8"))
    en = overskrift((SITE / "page-profile.html").read_text(encoding="utf-8"))
    tjek("den danske side har sin egen overskrift", da.lower() != en.lower(),
         f"da={da!r} en={en!r}")

    for linje in fejl:
        print(f"  FEJL  {linje}")
    print(f"check-page-h1-selftest: {'OK' if not fejl else 'RØD'}"
          f" ({talt[0] - len(fejl)}/{talt[0]} kontroller)")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true",
                        help="vis hvilke sider der dømmes, kun talt")
    parser.add_argument("--self-test", action="store_true",
                        help="kør portens egen kontrol af sig selv")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    fund = dom()
    for linje in fund:
        print(linje)
    sider = len({l.split(" i ", 1)[1].split(":", 1)[0] for l in fund})
    antal = len(list(SITE.rglob("*.html")))
    if args.list:
        dømt = {l.split(" i ", 1)[1].split(":", 1)[0] for l in fund}
        for fil in sorted(dømt):
            print(f"  {fil}")
    if fund:
        print(f"check-page-h1: RØD — {len(fund)} domme på {sider} sider "
              f"af {antal}")
        return 1
    print(f"check-page-h1: OK — {antal} sider, ingen `<h1>` er et filnavn")
    return 0


if __name__ == "__main__":
    sys.exit(main())
