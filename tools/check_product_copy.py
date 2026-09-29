#!/usr/bin/env python3
"""Gate produkttekster, der lover noget produkterne ikke kan holde.

To klasser:

* **DeskUptime** — de absolutte claims ("no phone-home", "no central server",
  "no telemetry"), opgave 2 trak tilbage fordi Pro-licensen er online.
* **Clean Copies Pro-flader** — de sider hvor licensnøglen *indtastes*, altså
  hvor et absolutt løfte om at intet forlader maskinen er en løgnest i samme
  dokument. Opgave 27 rettede FAQ'en på /clean-copy, men hero-noten og
  privatlivsnoten på /clean-copy-tool sagde videre det samme.
* **Guide-sider** — de publicerede FAQ'er der lovede at Clean Copy "works
  entirely inside your browser" / "everything runs locally in your browser".
  Tre af dem bliver skrevet af generatorer, så rettelsen skal ske i
  *generatoren* — ellers skriver næste kørslest den gamle tekst tilbage.
* **EAA-scanneren** — dens egen hentning går server-side gennem
  `/scan-proxy`, så "runs entirely in your browser" er modbevist af sidens
  egen `fetch` (opgave fra `scanner-proxy-aelthed`).

**Målt dækning, 27/9.** Porten dømmer **13 navngivne filer**; `site/` har
**299** sider. Målt med portens *egen* `semantic_html`, ikke et råt grep:

* **37** forbudte strenge i alt. **11** har mindst ét fund i `site/`, altså
  kan gøre en publiceret side rød. **19 har nul fund i hele `site/`** — de
  fanger altså kun en regression i en generator, aldrig en redigeret side.
  Det er ikke dækning, det er genbrug af de publicerede sætninger, og det er
  skrevet her så porten ikke ser ud til at dække mere end den gør.
* **44** krav-strenge, alle fundet i deres egen fil (målt: 0 mangler).
* **57 sider uden for fil-listen** siger et løfte fra den forbudte liste, og
  **alle 57 er sande**: de er klient-side-værktøjer uden upload og uden
  Pro-licens. Sandheden afhænger derfor af om siden *også* kalder
  licens-API'et, og det dømmer `check_claim_surface` — målt **0** af 299.

    python3 tools/check_product_copy.py
    python3 tools/check_product_copy.py --self-test
"""
from html.parser import HTMLParser
import argparse
import ast
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
GENERATOR = ROOT / "tools/make_blog_da_mirrors_461.py"
STANDARD_HIDDEN = {"head", "script", "style", "template", "noscript"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
PUBLIC_CHECKS = (
    (
        "site/deskuptime/index.html",
        (
            "no phone-home",
            "no central server",
            "no telemetry",
            "your data never leaves your computer",
        ),
        (
            "the desktop app asks for the key the first time you start it",
            "your url list and check results stay on your machine and are not uploaded to a central monitoring service",
            "the licence key, a stable device id and the product identifier deskuptime-pro",
            "and receives the licence status",
        ),
    ),
    (
        "site/da/deskuptime/index.html",
        (
            "ingen phone-home",
            "ingen central server",
            "ingen telemetri",
        ),
        (
            "desktop-appen beder om nøglen, første gang du starter den",
            "din url-liste og dine tjekresultater bliver på din maskine og uploades ikke til en central monitoreringstjeneste",
            "licensnøglen, et stabilt device-id og produktidentifieren deskuptime-pro",
            "og modtager licensstatus",
        ),
    ),
    (
        "site/blog/desktop-website-monitor-cli.html",
        (
            "no cloud",
            "no phone-home",
            "no central server",
            "no telemetry",
            "your data never leaves your computer",
            "no license server",
        ),
        (
            "your monitoring urls and check results stay on your machine and are not uploaded to a central monitoring service",
            "sends the licence key, a stable device id and the product identifier deskuptime-pro to a licence server over https",
        ),
    ),
    (
        "site/da/blog/overvaag-hjemmeside-fra-terminalen.html",
        (
            "licensaktivering, state og konfiguration er helt offline",
            "licensnøglen aktiveres offline",
            "pro-nøglen er en checksum genereret fra din hardware",
            "ingen licensserver",
        ),
        (
            "i version 0.2.7 tjekker appen stadig nøglen hos appens tidligere licensudbyder",
            "url-liste og tjekresultater bliver på din maskine og uploades ikke til en central monitoreringstjeneste",
            "i version 0.2.7 tjekker appen stadig nøglen hos appens tidligere licensudbyder",
        ),
    ),
)
GENERATOR_FORBIDDEN = (
    "licensaktivering, state og konfiguration er helt offline",
    "licensnøglen aktiveres offline",
    "pro-nøglen er en checksum genereret fra din hardware",
    "ingen licensserver",
)
GENERATOR_REQUIRED = (
    "i version 0.2.7 tjekker appen stadig nøglen hos appens tidligere licensudbyder",
    "url-liste og tjekresultater bliver på din maskine og uploades ikke til en central monitoreringstjeneste",
    "i version 0.2.7 tjekker appen stadig nøglen hos appens tidligere licensudbyder",
)

# Sider hvor kunden indtaster en Clean Copy Pro-nøgle. Her er et absolutt
# løfte om at intet forlader maskinen ikke bare upræcist — det er modbevist af
# dokumentets egen `fetch('/api/license/activate')`. Samme fejlform som
# opgave 2 (DeskUptime) og opgave 27 (shippede tekster), i en tredje klasse.
CLEAN_COPY_CHECKS = (
    (
        "site/clean-copy-tool.html",
        (
            "nothing leaves your device",
            "runs entirely in your browser",
            "runs entirely client-side",
            "100% in your browser",
            "nothing is uploaded",
        ),
        (
            "your text never leaves this page",
            "if you activate a pro key",
            "sent to our license api on mahope.tools so the license can be validated",
        ),
    ),
    (
        "site/clean-copy.html",
        (
            "runs entirely on your machine",
            "no data sent anywhere",
        ),
        (
            "your text is converted on your own machine",
            "a pro license key is checked online against mahope.tools",
        ),
    ),
    (
        "site/da/clean-copy.html",
        (
            "kører udelukkende på din egen maskine",
            "ingen data sendes nogen steder hen",
        ),
        (
            "din tekst konverteres på din egen maskine",
            "en pro-licensnøgle tjekkes online mod mahope.tools",
        ),
    ),
)

# Den afsløring alle fire guides skal stå med. Den er ens fordi den er sand
# for alle fire: selve tabellen bliver i browseren, og de to ting der faktisk
# forlader den sker kun på kundens egen handling.
GUIDE_REQUIRED = (
    "the table does not",
    "an anonymous page-view count",
    "if you activate a clean copy pro key",
    "sent to our license api on mahope.tools so the license can be validated",
)

# Guide-siderne. Tre af de fire skrives af en generator, så den publicerede
# tekst er her kun *resultatet* — men det er den læseren ser, og det er den
# der skal gates. Airtable-siden er håndskrevet (ingen generator findes), de
# tre andre regenereres af make_blog_sheets_en.py, make_blog_notion_en.py og
# make_hub_copy_clean.py.
GUIDE_CHECKS = (
    (
        "site/blog/copy-table-website-to-google-sheets.html",
        ("works entirely inside your browser",),
        GUIDE_REQUIRED,
    ),
    (
        "site/blog/copy-table-website-to-notion.html",
        ("works entirely inside your browser",),
        GUIDE_REQUIRED,
    ),
    (
        "site/blog/copy-table-website-to-airtable.html",
        ("works entirely inside your browser",),
        GUIDE_REQUIRED,
    ),
    (
        "site/copy-clean-guide.html",
        ("everything runs locally in your browser", "nothing is uploaded until you paste"),
        GUIDE_REQUIRED,
    ),
)

# Generatorerne skal og give den rigtige tekst. Ellers skriver næste kørsel
# den gamle løgnest tilbage, og porten på de publicerede sider fanger den først
# når nogen har kørt generatoren.
GUIDE_GENERATOR_CHECKS = (
    ("tools/make_blog_sheets_en.py", ("works entirely inside your browser",), GUIDE_REQUIRED),
    ("tools/make_blog_notion_en.py", ("works entirely inside your browser",), GUIDE_REQUIRED),
    ("tools/make_hub_copy_clean.py", ("everything runs locally in your browser", "nothing is uploaded until you paste"), GUIDE_REQUIRED),
)

# Den gratis EAA-scanner henter den URL man indtaster server-side gennem
# `/scan-proxy` (site/scan.html:191) og analyserer svaret i browseren. Derfor
# er "kører helt i din browser" ikke bare upræcist her — det er modbevist af
# sidens egen `fetch`, og det modsiger den præcise og sande formulering i
# scannerens egen FAQ ("Siden hentes server-side gennem vores Cloudflare-proxy,
# analyseres i din browser og kasseres straks"). Fjerde klasse efter opgave 2
# (DeskUptime), opgave 27 (Clean Copy) og guide-siderne.
#
# Antallet af regler gates også, men ikke med et tal-parsér: scanneren siger
# selv 15 (site/scan.html:21 og FAQSchema), og "15 WCAG..." som *krævet*
# sætning gør den rød, hvis nogen skriver 16 igen. Så tæller fejlen sig
# selv, i stedet for at en maintainer skal huske at tjekke tallet.
#
# **Tallet var 16 her, og det gjorde denne port til årsagen til et rødt CI.**
# Da `check_rule_claims` målte motoren og sagde 15, var det denne ports
# *krævede* sætning der holdt de to sider på 16 — så de to gater modsagde
# hinanden, og CI blev rød på merge. Sandheden er målt i koden: webkernen
# kører 15 regler (`free_rule_ids` i `check_rule_claims.py`), og scannerens
# egen engelske FAQ siger 15. Et *krav* i en port skal derfor aldrig være
# stærkere end den målte kode.
SCANNER_REQUIRED_EN = (
    "the page is fetched server-side through our cloudflare proxy",
    "analysed in your browser, and discarded",
    "salted hash of your ip address",
    "15 wcag compliance rules",
)
SCANNER_REQUIRED_DA = (
    "siden hentes server-side gennem vores cloudflare-proxy",
    "analyseres i din browser og kasseres",
    "salt-hash af din ip-adresse",
    "15 wcag-regler",
)
SCANNER_CHECKS = (
    (
        "site/compliance-ai.html",
        (
            "runs entirely in your browser",
            "no data is stored",
            "privacy-preserving cors proxy",
        ),
        SCANNER_REQUIRED_EN,
    ),
    (
        "site/da/compliance-ai.html",
        (
            "kører helt i din browser",
            "ingen data gemmes",
            "privatlivsvennligt proxy-kald",
        ),
        SCANNER_REQUIRED_DA,
    ),
)
# Generatoren skal give den samme ærlige tekst, ellers skriver næste kørsel
# den gamle løgnest tilbage — præcis som det skete for guide-siderne.
SCANNER_GENERATOR = "tools/make_compliance_ai_da.py"
SCANNER_GENERATOR_FORBIDDEN = (
    "kører helt i din browser",
    "privatlivsvennligt proxy-kald",
    "ingen data gemmes",
)
# porten er at den bliver rød på *den rigtige fil* med lige præcis den gamle
# tekst — ikke på en syntetisk streng, der ligner den.
SUPERSEDED_COPY = {
    "site/clean-copy-tool.html": (
        '<span><strong>Nothing leaves your device.</strong> The conversion runs in JavaScript on this page.\n'
        '      No upload, no server, no cookies, no tracking of your text.</span>',
        '<span><strong>Your text never leaves this page.</strong> The conversion runs in JavaScript\n'
        '      here. No upload, no cookies, no tracking of your text. Two things do leave your browser,\n'
        '      and only when you ask for them: an anonymous page-view count, and — if you activate a Pro\n'
        '      key — that key and a device id, sent to our license API on\n'
        '      <code>mahope.tools</code> so the license can be validated.</span>',
    ),
    "site/clean-copy.html": (
        "Runs entirely on your machine — no account, no server, no data sent anywhere.",
        "Your text is converted on your own machine — no account, no server, no text sent anywhere. "
        "A Pro license key is checked online against mahope.tools.",
    ),
    "site/da/clean-copy.html": (
        "Kører udelukkende på din egen maskine — ingen konto, ingen server, ingen data sendes nogen steder hen.",
        "Din tekst konverteres på din egen maskine — ingen konto, ingen server, ingen tekst sendes nogen steder hen. "
        "En Pro-licensnøgle tjekkes online mod mahope.tools.",
    ),
}


# De publicerede sætninger fra før rettelsen, kun brugt i selftestens bevis på
# de rigtige filer — samme (gammel, ny) rækkefølge som SUPERSEDED_COPY.
# De to revisioner af den samme løgn, begge publiceret. Den første sagde at
# værktøjet slet ikke nåede vores server; den næste sagde at det gjorde, men
# "no logs, no storage, no cookies" — hvilket er sandt for *siden* og falsk for
# det IP-hash, `rateLimitIp` skriver i to timer. Begge er i portens egen
# historik, og selftesten bruger dem som de fejlformer den siger at fange.
SCANNER_SUPERSEDED = {
    "site/compliance-ai.html": (
        "It runs entirely in your browser (client-side) with a privacy-preserving CORS proxy. No data is stored.",
        "The page is fetched server-side through our Cloudflare proxy, analysed in your browser, and discarded. We store nothing about the page itself and set no cookies; the one thing we keep is a salted hash of your IP address, which expires after two hours.",
    ),
    "site/da/compliance-ai.html": (
        "Den kører helt i din browser med et privatlivsvennligt proxy-kald. Ingen data gemmes.",
        "Siden hentes server-side gennem vores Cloudflare-proxy, analyseres i din browser og kasseres. Vi gemmer intet om selve siden og sætter ingen cookies; det eneste vi beholder, er et salt-hash af din IP-adresse, som udløber efter to timer.",
    ),
}


LICENSE_CALL = re.compile(r"/api/license|license/activate|license_api", re.I)


def _check_tables(value: object) -> list[tuple]:
    """(fil, forbudte-strenge) og (fil, forbudte-strenge, krav-strenge) rækker.

    Samlet over modulens egne tabeller, så porten ikke kan have en streng
    stående i en tabel, der ikke tæller med i overfladetællingen. Samme
    rytme som de øvrige `*_CHECKS`-tabeller, så en ny streng arves med.
    """
    out = []
    for item in value if isinstance(value, tuple) else ():
        if not isinstance(item, tuple) or len(item) not in (2, 3):
            continue
        if not isinstance(item[0], str) or not item[0].endswith(".html"):
            continue
        if not isinstance(item[1], tuple) or not item[1]:
            continue
        if not all(isinstance(s, str) for s in item[1]):
            continue
        out.append(item)
    return out


def forbidden_claims() -> set[str]:
    """Alle forbudte påstande i denne fil, normaliseret."""
    claims: set[str] = set()
    for value in globals().values():
        for item in _check_tables(value):
            claims.update(normalize(s) for s in item[1])
    return claims


def gated_files() -> set[str]:
    """De filer porten dømmer direkte — den lange, navngivne liste."""
    return {item[0] for value in globals().values() for item in _check_tables(value)}


def site_pages() -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "site").rglob("*.html"))
    }


def check_claim_surface(pages: dict[str, str]) -> list[str]:
    """Ingen side uden for fil-listen må løfte "kun i browseren" *og* kalde licens-API'et.

    Målt, ikke gættet. Porten dømmer 13 navngivne filer, men `site/` har 299
    sider, og 57 af dem siger et løfte fra portens egen forbudte liste. 57 af
    dem er sande: de er rene klient-side-værktøjer uden upload og uden
    Pro-licens, så "runs entirely in your browser" er sandt dér.

    Det er netop derfor fil-listen ikke kan dømme overfladen: sandheden afhænger
    af om siden *også* kalder licens-API'et. En side med begge dele er en
    modsigelse i sig selv — præcis fejlen i `clean-copy-tool.html` og
    `compliance-ai.html`, to gange fundet ved hånd. Målingen siger **0** af
    299 i dag, så denne regel koster intet på den nuværende overflade og
    fanger den næste side, der blander de to ting.

    Uden denne port ville en ny Pro-side kunne arve "runs entirely in your
    browser" fra en søskendeside og få en licens-kald tilføjet uden at nogen
    fil-liste nogensinde ville dømme den.
    """
    gated = gated_files()
    claims = forbidden_claims()
    problems = []
    for relative, raw in sorted(pages.items()):
        if relative in gated:
            continue
        found = sorted(c for c in claims if c in semantic_html(raw)[1])
        if not found:
            continue
        calls = sorted({m.group(0).lower() for m in LICENSE_CALL.finditer(raw)})
        if not calls:
            continue
        problems.append(
            f"{relative}: siger {found[0]!r} men kalder licens-API'et ({', '.join(calls)}) — "
            f"løftet er modbevist af sidens egen kode. Filen staar ikke i portens liste, "
            f"saa ingen anden regel dømmer den."
        )
    return problems


def anchor_problems(relative: str, source_relative: str, generator_source: Optional[str] = None) -> list[str]:
    """Hvert `old` i generatorens REPLACEMENTS skal findes i kilden.

    En død anchor fejler *stille*: `make_compliance_ai_da.py` renderer færdig,
    skriver den danske side, og lader bare den uoversatte engelske original stå
    i stedet for den danske sætning. Det er præcis sådan den danske side fik
    "15 WCAG-regler" imens generatoren sagde 16, og sådan et engelsk hero-
    undertitel slap igennem. Uden denne port er en sådan regression usynlig,
    fordi kørslen siger "Wrote ..." og går med grønt.

    `generator_source` gør det muligt at teste porten mod en muteret
    generator, som selftestens død-anchor-arm gør.
    """
    spec = importlib.util.spec_from_file_location("compliance_ai_da", ROOT / relative)
    if spec is None or spec.loader is None:
        return [f"{relative}: could not load generator"]
    try:
        if generator_source is None:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            replacements = module.REPLACEMENTS
        else:
            # Muteret generator: den skal stadig kunne importeres, så
            # `exec` sker i et frist navnerum med kun de to navne generatoren
            # bruger på modulniveau.
            namespace: dict = {"__file__": str(ROOT / relative), "__name__": "compliance_ai_da"}
            exec(compile(generator_source, str(ROOT / relative), "exec"), namespace)
            replacements = namespace["REPLACEMENTS"]
    except Exception as error:
        return [f"{relative}: generator failed to load: {error}"]
    source = (ROOT / source_relative).read_text(encoding="utf-8")
    return [
        f"{relative}: dead anchor — {old[:70]!r} is not in {source_relative}, "
        f"so the generator silently leaves the English original"
        for old, _new in replacements
        if old not in source
    ]



# De præcise FAQ-sætninger der var publiceret indtil denne iteration, for de
# fire guidesider. Samme (gammel, ny) rækkefølge som SUPERSEDED_COPY, og kun
# de bruges i selftestens bevis på de rigtige filer.
GUIDE_SUPERSEDED = {
    "site/blog/copy-table-website-to-google-sheets.html": (
        "No. Clean Copy works entirely inside your browser. The table never leaves your machine "
        "until you paste it where you want it.",
        "The table does not. Clean Copy reads and converts it in your own browser, so it never "
        "reaches a server — the result only exists on your clipboard until you paste it. Two "
        "other things do leave your browser, and both only when you ask for them: an anonymous "
        "page-view count, and — if you activate a Clean Copy Pro key — that key and a device "
        "id, sent to our license API on mahope.tools so the license can be validated.",
    ),
    "site/blog/copy-table-website-to-notion.html": (
        "No. Clean Copy works entirely inside your browser. The table never leaves your machine "
        "until you paste it where it needs to go yourself.",
        "The table does not. Clean Copy reads and converts it in your own browser, so it never "
        "reaches a server — the result only exists on your clipboard until you paste it where "
        "it needs to go. Two other things do leave your browser, and both only when you ask "
        "for them: an anonymous page-view count, and — if you activate a Clean Copy Pro key — "
        "that key and a device id, sent to our license API on mahope.tools so the license can "
        "be validated.",
    ),
    "site/blog/copy-table-website-to-airtable.html": (
        "No. Clean Copy works entirely inside your browser. The table never leaves your machine "
        "until you paste it where you want it.",
        "The table does not. Clean Copy reads and converts it in your own browser, so it never "
        "reaches a server — the result only exists on your clipboard until you paste it. Two "
        "other things do leave your browser, and both only when you ask for them: an anonymous "
        "page-view count, and — if you activate a Clean Copy Pro key — that key and a device "
        "id, sent to our license API on mahope.tools so the license can be validated.",
    ),
    "site/copy-clean-guide.html": (
        "No. The clipboard work happens entirely in your browser. Nothing is uploaded until you "
        "paste it somewhere yourself.",
        "The table does not. The clipboard work happens in your own browser and nothing you copy "
        "is uploaded — it only exists on your clipboard until you paste it yourself. Two other "
        "things do leave your browser, and both only when you ask for them: an anonymous "
        "page-view count, and — if you activate a Clean Copy Pro key — that key and a device "
        "id, sent to our license API on mahope.tools so the license can be validated.",
    ),
}

def collect_strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in collect_strings(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in collect_strings(item)]
    return []


class CopyHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.public_parts: list[str] = []
        self.claim_parts: list[str] = []
        self.hidden_counts: dict[str, int] = {}
        self.json_ld_parts: list[str] | None = None

    def is_hidden(self) -> bool:
        return any(self.hidden_counts.values())

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}
        style = attributes.get("style", "")
        tag_hidden = (
            tag in STANDARD_HIDDEN
            or "hidden" in attributes
            or attributes.get("aria-hidden", "").casefold() == "true"
            or re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", style, re.I) is not None
        )
        for key in ("alt", "aria-label", "content", "title"):
            value = attributes.get(key)
            if not value:
                continue
            self.claim_parts.append(value)
            if tag != "meta" and not tag_hidden and not self.is_hidden():
                self.public_parts.append(value)
        if tag == "meta":
            return
        if tag == "script" and attributes.get("type", "").casefold() == "application/ld+json":
            self.json_ld_parts = []
        if tag_hidden and tag not in VOID_TAGS:
            self.hidden_counts[tag] = self.hidden_counts.get(tag, 0) + 1

    def handle_data(self, data: str) -> None:
        if self.json_ld_parts is not None:
            self.json_ld_parts.append(data)
            return
        self.claim_parts.append(data)
        if not self.is_hidden():
            self.public_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.json_ld_parts is not None:
            document = json.loads("".join(self.json_ld_parts))
            self.claim_parts.extend(collect_strings(document))
            self.json_ld_parts = None
        if tag in self.hidden_counts and self.hidden_counts[tag] > 0:
            self.hidden_counts[tag] -= 1


def normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def generator_literals(relative, source=None) -> str:
    """Alle tekststrenge i en generator, som én søgbar streng.

    En generator skriver sin tekst i Python-strenge der ofte er linjebrudte
    og limt sammen med implicit konkatenering. Et simpelt grep rammer derfor
    aldrig hele sætningen, og det er netop derfor et forbudt løfte har kunnet
    ligge fordelt på to linjer. `ast` folder de sammensatte strenge ind i én
    `Constant` pr. stykke, så hele sætningen bliver søgbar — uden at vi
    kører generatoren, som ville skrive filer.
    """
    if source is None:
        source = (ROOT / relative).read_text(encoding="utf-8")
    pieces = [
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    return normalize("\n".join(pieces))


def check_generator(relative, forbidden, required, source=None) -> list[str]:
    literals = generator_literals(relative, source)
    problems = []
    for phrase in forbidden:
        if normalize(phrase) in literals:
            problems.append(f"{relative}: forbidden claim {phrase!r} in generator text")
    for phrase in required:
        if normalize(phrase) not in literals:
            problems.append(f"{relative}: missing required disclosure {phrase!r} in generator text")
    return problems


def semantic_html(text: str) -> tuple[str, str]:
    parser = CopyHTMLParser()
    parser.feed(text)
    parser.close()
    return normalize(" ".join(parser.public_parts)), normalize(" ".join(parser.claim_parts))


def check_text(identifier: str, text: str, forbidden: tuple[str, ...], required: tuple[str, ...]) -> list[str]:
    public, claims = semantic_html(text)
    problems = []
    for phrase in forbidden:
        if normalize(phrase) in claims:
            problems.append(f"{identifier}: forbidden claim {phrase!r}")
    for phrase in required:
        if normalize(phrase) not in public:
            problems.append(f"{identifier}: missing required disclosure {phrase!r}")
    return problems


def generated_blog_copy() -> tuple[str, Path]:
    spec = importlib.util.spec_from_file_location("deskuptime_blog_source", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load DeskUptime blog generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    page = next(page for page in module.PAGES if page["slug"] == "overvaag-hjemmeside-fra-terminalen")
    return module.m.build(page), Path(module.m.ROOT).resolve()


def collect_problems() -> list[str]:
    problems = []
    for relative, forbidden, required in PUBLIC_CHECKS:
        text = (ROOT / relative).read_text(encoding="utf-8")
        problems.extend(check_text(relative, text, forbidden, required))
    for relative, forbidden, required in CLEAN_COPY_CHECKS:
        text = (ROOT / relative).read_text(encoding="utf-8")
        problems.extend(check_text(relative, text, forbidden, required))
    for relative, forbidden, required in GUIDE_CHECKS:
        text = (ROOT / relative).read_text(encoding="utf-8")
        problems.extend(check_text(relative, text, forbidden, required))
    for relative, forbidden, required in GUIDE_GENERATOR_CHECKS:
        problems.extend(check_generator(relative, forbidden, required))
    for relative, forbidden, required in SCANNER_CHECKS:
        text = (ROOT / relative).read_text(encoding="utf-8")
        problems.extend(check_text(relative, text, forbidden, required))
    problems.extend(check_generator(SCANNER_GENERATOR, SCANNER_GENERATOR_FORBIDDEN, SCANNER_REQUIRED_DA))
    problems.extend(anchor_problems(SCANNER_GENERATOR, "site/compliance-ai.html"))
    problems.extend(check_claim_surface(site_pages()))
    try:
        generated, generator_root = generated_blog_copy()
    except Exception as error:
        problems.append(f"tools/make_blog_da_mirrors_461.py: generator failed: {error}")
    else:
        problems.extend(check_text("tools/make_blog_da_mirrors_461.py", generated, GENERATOR_FORBIDDEN, GENERATOR_REQUIRED))
        if generator_root != ROOT.resolve():
            problems.append(f"tools/make_blog_da_mirrors_461.py: unsafe checkout root {generator_root}")
    return problems


def self_test() -> int:
    """Bevis at porten fanger hver fejlform, den siger at fange.

    Scenarierne er bygget af de *rigtige* filer, ikke af syntetiske strenge:
    en fejlform, der kun findes i en streng porten selv har fundet, er ingen
    fejlform. Derfor læses hver fil, og kun den påstand der testes, muteres.
    """
    cases = {relative: (forbidden, required) for relative, forbidden, required in CLEAN_COPY_CHECKS}
    tool = cases["site/clean-copy-tool.html"]
    real = {relative: (ROOT / relative).read_text(encoding="utf-8") for relative in cases}

    def mutated(relative: str, old: str, new: str) -> str:
        text = real[relative]
        if old not in text:
            raise AssertionError(f"{relative}: mutation anchor not found: {old[:60]!r}")
        return text.replace(old, new, 1)

    scenarios: list[tuple[str, list[str]]] = [
        # Bevis på de rigtige filer: den publicerede tekst fra før rettelsen.
        ("den gamle privatlivsnote på /clean-copy-tool",
         check_text("tool", real["site/clean-copy-tool.html"].replace(
             SUPERSEDED_COPY["site/clean-copy-tool.html"][1],
             SUPERSEDED_COPY["site/clean-copy-tool.html"][0], 1), *tool)),
        ("den gamle hero-note på /clean-copy",
         check_text("landing", real["site/clean-copy.html"].replace(
             SUPERSEDED_COPY["site/clean-copy.html"][1],
             SUPERSEDED_COPY["site/clean-copy.html"][0], 1), *cases["site/clean-copy.html"])),
        ("den gamle hero-note på /da/clean-copy",
         check_text("landing-da", real["site/da/clean-copy.html"].replace(
             SUPERSEDED_COPY["site/da/clean-copy.html"][1],
             SUPERSEDED_COPY["site/da/clean-copy.html"][0], 1), *cases["site/da/clean-copy.html"])),
        # Den klassiske fejl: afsløringen er væk, løftet står.
        ("en Pro-side uden nogen afsløring",
         check_text("tool", re.sub(r"if you activate a Pro", "if you never activate a Pro",
                                   real["site/clean-copy-tool.html"], count=1), *tool)),
        ("en landingsside hvor afsløringen kun står i en meta-description",
         check_text("landing", real["site/clean-copy.html"].replace(
             "<span class=\"hero-note\">", "<span class=\"hero-note\" aria-hidden=\"true\">", 1),
             *cases["site/clean-copy.html"])),
        # Meta og JSON-LD er ikke synlige, men de er læst: en søgemaskine
        # eller en browser-udvidelse skal ikke kunne finde det gamle løfte.
        ("det gamle løfte kun i meta-description",
         check_text("tool", real["site/clean-copy-tool.html"].replace(
             'content="Free online tool:', 'content="Nothing leaves your device. Free online tool:', 1), *tool)),
        ("et forbudt løfte i JSON-LD",
         check_text("tool", real["site/clean-copy-tool.html"].replace(
             '"description": "Paste messy formatted text and get clean Markdown or plain text back. Your text never leaves your browser."',
             '"description": "Nothing leaves your device."', 1), *tool)),
        # Forskelle porten selv har gjort for fejl, den så ud til at dække.
        ("et løfte med anden store-og-mellemrum",
         check_text("tool", real["site/clean-copy-tool.html"].replace(
             "Your text never leaves this page.", "Your   text\n never leaves your device.", 1), *tool)),
        ("et løfte der kun er enlig med et tegn",
         check_text("landing", real["site/clean-copy.html"].replace(
             "no text sent anywhere", "no data sent anywhere.", 1), *cases["site/clean-copy.html"])),
    ]

    # Bevis på de rigtige filer: de publicerede FAQ'er fra før rettelsen, i
    # alle fire. Det er den tekst læseren faktisk har læst.
    guide_cases = {relative: (forbidden, required) for relative, forbidden, required in GUIDE_CHECKS}
    guide_real = {relative: (ROOT / relative).read_text(encoding="utf-8") for relative in guide_cases}
    for relative, (old, new) in GUIDE_SUPERSEDED.items():
        if new not in guide_real[relative]:
            raise AssertionError(f"{relative}: current text not found in the real file: {new[:60]!r}")
        if old in guide_real[relative]:
            raise AssertionError(f"{relative}: superseded text still present in the real file")
        scenarios.append((
            f"den gamle FAQ-påstand på {relative}",
            check_text(relative, guide_real[relative].replace(new, old, 1), *guide_cases[relative]),
        ))

    # Bevis på de rigtige generatorer: løftet der skriver den gamle tekst
    # tilbage skal fanges i selve kilden, ikke først i det publicerede
    # resultat. `make_hub_copy_clean.py` er valgt fordi dens gamle sætning
    # var delt på to Python-strenge — et grep ville ikke have fundet den.
    for relative, forbidden, required in GUIDE_GENERATOR_CHECKS:
        source = (ROOT / relative).read_text(encoding="utf-8")
        old_claim = "The table does not."
        if old_claim not in source:
            raise AssertionError(f"{relative}: mutation anchor not found: {old_claim!r}")
        scenarios.append((
            f"generatoren {relative} der skriver det gamle løfte tilbage",
            check_generator(relative, forbidden, required, source.replace(old_claim, "Everything runs locally in your browser.", 1)),
        ))
        scenarios.append((
            f"generatoren {relative} uden nogen afsløring",
            check_generator(relative, forbidden, required,
                            source.replace("page-view count", "view count", 1)),
        ))
        # Scenariet ovenfor er grønt kun hvis mutationen overhovedet ramte.
        # `page-view count` står i alle tre generatorer som ét lig streng; de
        # lange sætninger er delt på to Python-strenge, så et rent grep ville
        # aldrig have fundet det gamle løfte.
        if "page-view count" not in source:
            raise AssertionError(f"{relative}: generator anchor not found: 'page-view count'")

    # Scanner-klassen. Beviset er de publicerede sætninger fra før rettelsen,
    # i begge sprog, fordi det er den tekst læseren faktisk har læst.
    scanner_cases = {relative: (forbidden, required) for relative, forbidden, required in SCANNER_CHECKS}
    scanner_real = {relative: (ROOT / relative).read_text(encoding="utf-8") for relative in scanner_cases}
    for relative, (old, new) in SCANNER_SUPERSEDED.items():
        if new not in scanner_real[relative]:
            raise AssertionError(f"{relative}: current text not found in the real file: {new[:60]!r}")
        if old in scanner_real[relative]:
            raise AssertionError(f"{relative}: superseded text still present in the real file")
        scenarios.append((
            f"den gamle scanner-påstand på {relative}",
            check_text(relative, scanner_real[relative].replace(new, old, 1), *scanner_cases[relative]),
        ))
    # Antallet af regler skal også gates, ikke bare løftet. `16` i stedet for
    # `15` er den fejl de fire sider faktisk havde, og den fanges kun fordi
    # det rigtige antal står som *krævet* sætning.
    scenarios.append((
        "scanneren der lover et forkert antal WCAG-regler",
        check_text("scanner-da", scanner_real["site/da/compliance-ai.html"].replace(
            "15 WCAG-regler", "16 WCAG-regler", 1), *scanner_cases["site/da/compliance-ai.html"]),
    ))
    scenarios.append((
        "scanneren uden nogen afsløring af proxy-kaldet",
        check_text("scanner", scanner_real["site/compliance-ai.html"].replace(
            "The page is fetched server-side through our Cloudflare proxy,", "The page is fetched on your device,", 1),
            *scanner_cases["site/compliance-ai.html"]),
    ))
    # Generatoren skal give den ærlige tekst, ellers skriver næste kørsel
    # løgnesten tilbage. Beviset er den gamle sætning i den rigtige kilde.
    generator_source = (ROOT / SCANNER_GENERATOR).read_text(encoding="utf-8")
    scanner_anchor = "Siden hentes server-side gennem vores Cloudflare-proxy"
    if scanner_anchor not in generator_source:
        raise AssertionError(f"{SCANNER_GENERATOR}: mutation anchor not found")
    scenarios.append((
        f"generatoren {SCANNER_GENERATOR} der skriver det gamle løfte tilbage",
        check_generator(SCANNER_GENERATOR, SCANNER_GENERATOR_FORBIDDEN, SCANNER_REQUIRED_DA,
                        generator_source.replace(
                            scanner_anchor,
                            "Den kører helt i din browser", 1)),
    ))
    # Den stille fejl: en død anchor. Generatoren kører færdig og siger
    # "Wrote ...", men lader den uoversatte engelske original stå. Beviset er
    # den mutation der dræber præcis den anchor, der døde i virkeligheden.
    dead = ("<p class=\"subtitle\">Free Q&A for small web agencies.",
            "<p class=\"subtitle\">Free AI-powered Q&A for small web agencies.")
    if dead[0] not in (ROOT / "site/compliance-ai.html").read_text(encoding="utf-8"):
        raise AssertionError("site/compliance-ai.html: subtitle anchor not found for the dead-anchor case")
    broken_source = (ROOT / SCANNER_GENERATOR).read_text(encoding="utf-8").replace(dead[0], dead[1], 1)
    scenarios.append((
        f"{SCANNER_GENERATOR} med en død anchor",
        anchor_problems(SCANNER_GENERATOR, "site/compliance-ai.html", broken_source),
    ))

    # Overfladen uden for fil-listen. Beviset er en *rigtig* side fra `site/`
    # der siger et løfte fra portens egen liste, og som så får et licens-kald
    # lagt på. Det er den modsigelse `check_claim_surface` er skrevet for, og
    # den er fundet to gange ved hånd — først på /clean-copy-tool, så på
    # /compliance-ai — altså ikke en konstrueret fejlform.
    surface = site_pages()
    # `word-counter.html` er valgt fordi det er en side *uden for* listen,
    # der faktisk siger løftet. Mutationen rammer derfor en side, porten
    # ellers ikke læser — ellers ville armen bevise noget, porten gør.
    surface_probe = "site/word-counter.html"
    if surface_probe in gated_files():
        raise AssertionError(f"{surface_probe}: probe page is in the gate's own file list")
    probe_found = sorted(c for c in forbidden_claims() if c in semantic_html(surface[surface_probe])[1])
    if not probe_found:
        raise AssertionError(f"{surface_probe}: probe page carries no forbidden claim, "
                             f"so the mutation would prove nothing")
    license_anchor = "<script defer src=\"/track.js\"></script>"
    if license_anchor not in surface[surface_probe]:
        raise AssertionError(f"{surface_probe}: mutation anchor not found")
    mutated_surface = dict(surface)
    mutated_surface[surface_probe] = surface[surface_probe].replace(
        license_anchor,
        license_anchor + "\n<script>fetch('/api/license/activate',"
        "{method:'POST',body:'{}'});</script>", 1)
    scenarios.append((
        "en side uden for fil-listen der lover \"kun i browseren\" og kalder licens-API'et",
        check_claim_surface(mutated_surface),
    ))
    # Negativ kontrol for den samme arm: løftet *alene* på en side uden for
    # listen er sandt og må ikke være rødt. Uden denne kontrol ville porten
    # bare være en ny rød-maskine over 57 rigtige sider. Den hænger på den
    # `negative`-liste nedenfor, fordi et grønt scenarie i `scenarios` tælles
    # som et fejlende scenarie.

    # Positiv kontrol: de rigtige filer skal være grønne, ellers er porten
    # grøn fordi den intet kan.
    positive = [f"{relative}: {problem}" for relative, (forbidden, required) in cases.items()
                for problem in check_text(relative, real[relative], forbidden, required)]
    positive += [f"{relative}: {problem}" for relative, (forbidden, required) in guide_cases.items()
                 for problem in check_text(relative, guide_real[relative], forbidden, required)]
    positive += [f"{relative}: {problem}" for relative, forbidden, required in GUIDE_GENERATOR_CHECKS
                 for problem in check_generator(relative, forbidden, required)]
    positive += [f"{relative}: {problem}" for relative, (forbidden, required) in scanner_cases.items()
                 for problem in check_text(relative, scanner_real[relative], forbidden, required)]
    positive += [f"{SCANNER_GENERATOR}: {problem}" for problem
                 in check_generator(SCANNER_GENERATOR, SCANNER_GENERATOR_FORBIDDEN, SCANNER_REQUIRED_DA)]
    positive += anchor_problems(SCANNER_GENERATOR, "site/compliance-ai.html")
    # Overfladeposten skal være grøn på de *rigtige* 299 sider. Uden denne
    # kontrol kan den nye regel være grøn fordi den ingenting kan se.
    positive += [f"overflade: {problem}" for problem in check_claim_surface(site_pages())]
    positive_controls = (len(cases) + len(guide_cases) + len(GUIDE_GENERATOR_CHECKS)
                         + len(scanner_cases) + 3)

    # Negativ kontrol: en kvalificeret påstand er ikke en forbudt påstand.
    qualified = ('<p>Your text never leaves this page. If you activate a Pro key, that key and a '
                 'device id are sent to our license API on <code>mahope.tools</code> so the license '
                 'can be validated. A Pro license key is checked online against mahope.tools.</p>')
    negative = [problem for problem in check_text("qualified", qualified, *tool) if "forbidden" in problem]
    # Negativ kontrol for overfladeposten: 57 rigtige sider siger et løfte fra
    # portens egen liste, og alle 57 er sande — de er klient-side-værktøjer
    # uden licens-kald. Porten skal være stille på dem.
    surface_only = site_pages()
    if surface_probe in gated_files():
        raise AssertionError(f"{surface_probe}: probe page is in the gate's own file list")
    negative += [f"falsk alarm på en ærlig klient-side-side: {problem}"
                 for problem in check_claim_surface({surface_probe: surface_only[surface_probe]})]

    failed = 0
    for name, problems in scenarios:
        if not problems:
            print(f"FEJLET (blev ikke fanget): {name}")
            failed += 1
        else:
            print(f"fanget: {name} — {problems[0]}")
    for problem in positive:
        print(f"FEJLET (rigtige filer er røde): {problem}")
        failed += 1
    for problem in negative:
        print(f"FEJLET (falsk alarm på kvalificeret tekst): {problem}")
        failed += 1
    if not negative:
        print("falsk-alarm-kontrol: en kvalificeret påstand fejler ikke")
    if not positive:
        print(f"positiv kontrol: {positive_controls} rigtige filer og generatorer er grønne")
    print(f"self-test: {'OK' if not failed else 'FEJLET'} — {len(scenarios)} fejlformer, "
          f"{failed} fejlede")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="bevis at porten fanger de fejlformer, den siger at fange")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    problems = collect_problems()
    print(f"{len(PUBLIC_CHECKS) + 1} DeskUptime copy sources checked")
    print(f"{len(CLEAN_COPY_CHECKS)} Clean Copy Pro copy sources checked")
    print(f"{len(GUIDE_CHECKS)} guide pages + {len(GUIDE_GENERATOR_CHECKS)} guide generators checked")
    print(f"{len(SCANNER_CHECKS)} scanner pages + 1 scanner generator + its anchors checked")
    print(f"problems: {len(problems)}")
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
