#!/usr/bin/env python3
"""Gate for købsrejsen: kun tilladte Stripe-links, én CTA pr. tilbud, ingen falske priser.

Opgaverne er:

1. `tools/stripe_catalog.json` er den eneste maskinlæsbare allowlist, og den
   skal være identisk med `docs/stripe-kontrakt.md` og med produkterne i
   `site/_worker.js`.
2. Hvert `buy.stripe.com`/`donate.stripe.com`-link i source og i shippede
   klienter skal stå i allowlisten.
3. Inventoret af synlige Pro-tilbud (`offers`) skal være fuldt: ingen side med
   en købsknap må stå udenfor, ingen inventeret side må mangle, og hver side
   skal have præcis én synlig CTA med det rette link og kun dokumenterede priser.
4. Ingen side må love et køb der ikke findes ("coming soon", "når butikken
   åbner", "paid checkout is not wired up").
5. Et download-produkt må kun sælges, når dets filer faktisk kan leveres.
   `tools/paid_content.json` er den eneste kilde til det (`kv_verified`), og
   et produkt uden `kv_verified: true` må ikke have sit betalingslink nogen
   sted i `site/`. Modsat retning tæller også som fejl: et leverbart produkt
   uden købsside ville blive solgt helt uden.
6. Hver købsside skal have mindst én indgang fra en side læser kan nå, målt
   i det byggede `dist/` — se `check_buy_page_entry`.
7. Hver side med et synligt kassalink skal indlæse `/track.js`, og trackeren
   skal stadig have kliklytteren — se `check_buy_click_tracking`.

    python3 tools/check_stripe_ctas.py           # gate
    python3 tools/check_stripe_ctas.py --report  # inventaret, uden at fejle
    python3 tools/check_stripe_ctas.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from typing import Any
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "tools/stripe_catalog.json"
CONTRACT = ROOT / "docs/stripe-kontrakt.md"
PAID_CONTENT = ROOT / "tools/paid_content.json"
WORKER = ROOT / "site/_worker.js"
TRACK_JS = ROOT / "site/track.js"

KNOWN_DOMAINS = ("cleancopy.tools", "deskuptime.com", "bugbottle.dev", "mahope.tools")

# Kundeportalen har sti-segmenter (billing.stripe.com/p/login/…), betalingslinks ikke.
LINK_PATTERN = re.compile(r"https://(?:buy|donate|billing)\.stripe\.com/[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*")
PRICE_TOKEN = re.compile(r"\$\s?\d[\d.]*")
PRODUCT_KEY = re.compile(r"^[a-z0-9-]+$")

# Filer der scanst for links: hele site-kilden plus de shippede licensklienter.
SCAN_ROOTS = (
    "site",
    "page-profile",
    "obsidian-plugin",
    "extension-clean-copy",
    "extension-clean-copy-firefox",
    "extension-clean-copy-vscode",
)
SCAN_FILES = ("main.js", "core.js")
SKIP_DIRS = {"__pycache__", ".wrangler"}

HIDDEN_TAGS = {"head", "script", "style", "template", "noscript"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
             "meta", "param", "source", "track", "wbr"}

#: Tags der kun er struktur *i dokumenthovedet*. Skrevet i brødteksten er de
#: bogstavelig tekst — en browser ignorerer dem — så de må ikke åbne en skjult
#: region. Målt: `site/blog/canonical-url-guide.html` skriver "a `<head>` tag"
#: i to afsnit, og porten holdt resten af artiklen for usynlig resten af
#: dokumentet, fordi de to aldrig lukkes.
HEAD_LEVEL_TAGS = {"head", "title", "meta", "link", "base"}


class HiddenStack:
    """De skjulte regioner i et dokument, som en stak.

    Målt, ikke antaget. Før denne iteration var de en tæller pr. tag, og den
    kunne blive falsk på to måder, begge målt på rigtige filer:

    1. **Ned under nul.** `TierBlocks.handle_endtag` trak `span` ned for en
       `</span>` inde i en lukket `<details>`, selv om den `span` aldrig var
       talt op, fordi `<span>` selv ikke er skjult. `any(dict.values())` så
       `-1` som *sandt*, så hele resten af siden blev dømt usynlig. Målt på
       `site/clean-copy-tool.html`: parseren endte med `{'span': -2}` og så
       altså ikke Pro-afsnittet, footeren eller FAQ'en — på den købsside hvor
       Clean Copy Pro sælges.
    2. **Op men aldrig ned.** Se `HEAD_LEVEL_TAGS`: en region der aldrig
       lukkes, gør hele dokumentets bagside usynlig.

    En stak kan ingen af delene. En `</tag>` lukker hele den region den
    afslutter, også de tællere der lå indeni, og en tag der ikke åbnede en
    region kan ikke lukke en. Det er præcis en browsers egen model.
    """

    def __init__(self) -> None:
        self.tags: list[str] = []
        self.in_body = False

    def __bool__(self) -> bool:
        return bool(self.tags)

    def open(self, tag: str) -> None:
        if tag in HEAD_LEVEL_TAGS and self.in_body:
            return  # Bogstavelig tekst i brødteksten, ikke en beholder.
        self.tags.append(tag)

    def close(self, tag: str) -> None:
        for index in range(len(self.tags) - 1, -1, -1):
            if self.tags[index] == tag:
                del self.tags[index:]
                return

    def enter_body(self) -> None:
        self.in_body = True

FORBIDDEN_CLAIMS = (
    "pro is coming",
    "coming soon",
    "available soon",
    "available when store launches",
    "when store launches",
    "kommer når butikken åbner",
    "kommer når butikken åbner.",
    "paid checkout is not wired up",
    "ikke er koblet en betalt checkout",
    "there are no recurring charges",
)

# Hvor analysen sker. Kun den *anden* halvdel af parret er et problem, og
# begge halve er strukturelle: se `check_analysis_location`.
SERVER_ANALYSIS_ROUTES = ("/api/report",)
BROWSER_LOCATION_RE = re.compile(
    r"\b(?:in|inside|runs? in|processed in)\s+(?:your|the)\s+browser\b"
    r"|\bi\s+din\s+browser\b",
    re.IGNORECASE,
)
ANALYSIS_VERB_RE = re.compile(
    r"\banaly[sz]|\banalys|\bbereg|\bfind|\bfund|\bgrade[sd]?\b|\bscor",
    re.IGNORECASE,
)
# "browserens print-dialog" er sandt: siden kalder stadig `window.print()`.
# Derfor matcher lokationen kun en *analys påstand*, aldrig et print-virk.
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")

REQUIRED_PRODUCT_KEYS = (
    "clean-copy-pro",
    "deskuptime-pro",
    "transmute-desktop",
    "eucomply-pro",
    "page-profile-pro",
    "eucomply-dpa",
    "eucomply-nis2-clauses",
    "eucomply-nda-clauses",
    "eucomply-eaa-statement",
    "eucomply-report-kit",
    "eucomply-template-bundle",
    "eu-compliance-ebook-bundle",
    "support-mahope-oss",
)

REQUIRED_KINDS = {
    "clean-copy-pro": "license",
    "deskuptime-pro": "license",
    "transmute-desktop": "license",
    "eucomply-pro": "license",
    "page-profile-pro": "license",
    "eucomply-dpa": "download",
    "eucomply-nis2-clauses": "download",
    "eucomply-nda-clauses": "download",
    "eucomply-eaa-statement": "download",
    "eucomply-report-kit": "download",
    "eucomply-template-bundle": "download",
    "eu-compliance-ebook-bundle": "download",
    "support-mahope-oss": "donation",
}


class Page(HTMLParser):
    """Synlig tekst, synlige links og alle links — også dem i JSON-LD."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden = HiddenStack()
        self.visible_parts: list[str] = []
        self.all_links: list[str] = []
        self.in_json_ld = False
        self.current_href: str | None = None
        self.current_anchor_parts: list[str] = []

    def _is_hidden(self) -> bool:
        return bool(self.hidden)

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}
        href = attributes.get("href", "")
        if href:
            self.all_links.append(href)
            self.current_href = href
            self.current_anchor_parts = []
        style = attributes.get("style", "")
        hidden = (
            tag in HIDDEN_TAGS
            or "hidden" in attributes
            or attributes.get("aria-hidden", "").casefold() == "true"
            or re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", style, re.I) is not None
        )
        if tag == "script" and attributes.get("type", "").casefold() == "application/ld+json":
            self.in_json_ld = True
        if tag == "body":
            self.hidden.enter_body()
        if hidden and tag not in VOID_TAGS:
            self.hidden.open(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_json_ld:
            self.in_json_ld = False
        self.hidden.close(tag)
        if tag == "a":
            self.current_href = None
            self.current_anchor_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_json_ld or self._is_hidden():
            return
        self.visible_parts.append(data)
        if self.current_href is not None:
            self.current_anchor_parts.append(data)

    @property
    def text(self) -> str:
        return normalize(" ".join(self.visible_parts))


class AnchorCollector(HTMLParser):
    """Ankre med synlig tekst, i dokumentrækkefølge."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden = HiddenStack()
        self.anchors: list[tuple[str, str]] = []
        self.open: list[tuple[str, list[str]]] = []
        self.in_json_ld = False

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}
        if tag == "script" and attributes.get("type", "").casefold() == "application/ld+json":
            self.in_json_ld = True
        style = attributes.get("style", "")
        hidden = (
            tag in HIDDEN_TAGS
            or "hidden" in attributes
            or attributes.get("aria-hidden", "").casefold() == "true"
            or re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", style, re.I) is not None
        )
        if tag == "body":
            self.hidden.enter_body()
        if hidden and tag not in VOID_TAGS:
            self.hidden.open(tag)
        if tag == "a" and not self._hidden():
            self.open.append((attributes.get("href", ""), []))

    def _hidden(self) -> bool:
        return self.in_json_ld or bool(self.hidden)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_json_ld:
            self.in_json_ld = False
        if tag == "a" and self.open:
            href, parts = self.open.pop()
            text = normalize(" ".join(parts))
            if text:
                self.anchors.append((href, text))
        self.hidden.close(tag)

    def handle_data(self, data: str) -> None:
        if self._hidden():
            return
        for _, parts in self.open:
            parts.append(data)


def normalize(text: str) -> str:
    return " ".join(text.split())


# ── Hvad en Pro-side skal vise om den gratis udgave ──────────────────────
#
# Missionens punkt 4: "hver Pro-side klart viser, hvad gratis og betalt
# giver". Indtil nu var det kun en hensigtserklæring i katalogens `why`, og
# ingen port læste den — så /clean-copy-tool, siden hvor Clean Copy Pro
# faktisk købes og aktiveres, ikke nævnte den gratis udgave overhovedet.
# Ordet "free" stod kun i "More free tools"-linket nederst på siden.
#
# Både en sætning og en tabel tæller, fordi de sunde sider bruger begge
# former: DeskUptime og Page Profile har en "Free and Pro"-tabel, mens
# /clean-copy og /activate har en sætning. En port der krævede den ene
# form ville gøre de andre sider røde uden grund.
FREE_TIER_PHRASES = re.compile(
    r"\bfree (?:version|tier|tool|cli|web|edition|plan)\b"
    r"|\bstays free\b"
    r"|\bnot a trial\b"
    r"|\bis free\b"
    r"|\bgratis (?:version|udgave|værktøj|web|plan|cli)\b"
    r"|\ber gratis\b"
    r"|\bgratis og\b"
    r"|\bgratis cli\b"
    r"|\bingen prøveversion\b"
)
FREE_LABEL = re.compile(r"\bfree\b|\bgratis\b", re.I)
PAID_LABEL = re.compile(r"\bpro\b|\bpaid\b|\bpremium\b|\$|\busd\b|\bkr\.?|\beur\b|\bdkk\b", re.I)

#: En tabelcelle der kun svarer ja eller nej. Den siger intet om hvad
#: funktionen er — den siger kun hvilken spalte funktionen står i. Målt på
#: de tre tabeller porten dømmer: `deskuptime.com` skriver "yes"/"—",
#: bloggen skriver "✓"/"—", og `page-profile` skriver "yes"/"—".
#:
#: Uden disse to mønstre taber `paid_contexts` hele rækkens *navn*, fordi
#: den kun samler cellens egen tekst, og en celle der siger "✓" forteller
#: intet. Det var målt, ikke formodet: `Webhook alerts (CLI) | — | ✓` gav
#: en betalt spalte der indeholdt fire tegn, ikke navnet på funktionen.
YES_CELL = re.compile(r"^[\s]*(?:yes|ja|ok)[\s.]*$|^\s*[✓✔xX]\s*$", re.I)
NO_CELL = re.compile(r"^(?:[—–\-‐]\s*)+$|^\s*(?:no|nej)[\s.]*$", re.I)

# `PRICE_TOKEN` kræver et `$`, og det er ikke nok. `/clean-copy-tool` skriver
# sin Pro-pris som "19 USD per year" — hele den families vigtigste købsside
# står altså med en pris, en `$`-baseret regel ikke kan se. Derfor tæller
# valutaord og symboler begge, ellers er porten grøn på præcis den
# forsvundne købsmulighed den er skrevet til at fange.
CURRENCY_AMOUNT = re.compile(
    r"[$€£]\s?\d[\d.]*"
    r"|\b\d[\d.,]*\s?(?:usd|eur|dkk|kr\.?)\b",
    re.I,
)


def amount_value(token: str) -> float | None:
    """Tallet i et valutatoken, eller `None` hvis det ikke er et tal.

    Nødvedig for nul-prisen. `$0` og `"0"` er ikke et løfte om at betale —
    de er en *sand* måde at sige "den her er gratis" — så reglen må kun
    slå ned på positive beløb. Uden denne skelnen ville porten være rød på
    `site/site-icons.html`, der skriver `$0` under en gratis pakke.
    """
    digits = re.sub(r"[^\d.,]", "", token)
    if not digits:
        return None
    # Dansk og tysk notation bruger komma som decimaltegn ("1.299 kr").
    if "," in digits and "." in digits:
        digits = digits.replace(".", "").replace(",", ".")
    elif "," in digits:
        head, _, tail = digits.rpartition(",")
        digits = f"{head}.{tail}" if len(tail) in (1, 2) and head else digits.replace(",", "")
    try:
        return float(digits)
    except ValueError:
        return None


#: Tags hvis indhold er en *meddelelse om* vores produkter. Indholdet i et
#: `<pre>` eller `<code>` er derimod det en læser kopierer — en
#: kommandolinje, en fejlmelding, en pythonsnit, et eksempel på markup.
#: Det er ikke prosa, og det må ikke læses som en påstand om, hvad noget
#: koster.
#:
#: To forskellige ting er holdt ude her, og det er værd at skelne dem:
#:
#: **Bloksegmenteringen** (`ProseBlocks`) er den, der rettede
#: `site/site-icons.html`. `parse_page` normaliserer alle linjeskift væk, så
#: `$ pip install Pillow … site-icons-1.0.0.tar.gz` og den ærlige sætning
#: "not for sale yet" blev ét enkelt segment med både et tal og et
#: løfteord. Det var en *sand* side, som reglen ville have gjort rød.
#:
#: **`CODE_TAGS`** er den, der holder `'# $1'` ude — en regex i et
#: JavaScript-eksempel på `/blog/building-html-to-markdown-converter`, hvor
#: `$1` er en gruppe-reference og ikke en dollar. Den fangede intet i det
#: øjeblik reglen blev skrevet, og det er opført her fordi den er billig og
#: fordi selftesten beviser at den virker: en dokumentationsside skal kunne
#: vise et eksempel på en pris uden at blive anklaget for at løfte om den.
CODE_TAGS = {"pre", "code", "kbd", "samp"}


class ProseBlocks(HTMLParser):
    """Synlig prosa i blokke, med `<pre>`/`<code>` holdt ude.

    `VisibleBlocks` giver hele sidens tekst, og `parse_page` giver den
    normaliseret — altså uden linjeskift. Det er nok til en sætning, men
    ikke til at segmentere *afsnit*, fordi en kommandolinje og en sætning
    derefter bliver ét. Her følges derfor de synlige blokke, så hver enhed
    er noget en læser kunne læse som ét.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden = HiddenStack()
        self.in_json_ld = False
        self.in_code = 0
        self.blocks: list[str] = []
        self._parts: list[str] = []

    def _is_hidden(self) -> bool:
        return bool(self.hidden)

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}
        style = attributes.get("style", "")
        hidden = (
            tag in HIDDEN_TAGS
            or "hidden" in attributes
            or attributes.get("aria-hidden", "").casefold() == "true"
            or re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", style, re.I) is not None
            or (tag == "details" and "open" not in attributes)
        )
        if tag == "script" and attributes.get("type", "").casefold() == "application/ld+json":
            self.in_json_ld = True
        if tag == "body":
            self.hidden.enter_body()
        if hidden and tag not in VOID_TAGS:
            self.hidden.open(tag)
        if tag in CODE_TAGS and tag not in VOID_TAGS and not self._is_hidden():
            self.in_code += 1
        # Et nyt blokelement afslutter det foregående afsnit. Uden det ville
        # en hel side være ét segment, fordi tekstnoderne løber sammen.
        if (not self._is_hidden() and not self.in_code
                and tag in ("p", "li", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6",
                            "div", "section", "article", "blockquote", "figcaption", "tr")):
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_json_ld:
            self.in_json_ld = False
        if tag in CODE_TAGS and self.in_code > 0:
            self.in_code -= 1
        if tag in ("p", "li", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6",
                   "div", "section", "article", "blockquote", "figcaption", "tr"):
            self._flush()
        self.hidden.close(tag)

    def handle_data(self, data: str) -> None:
        if self.in_json_ld or self._is_hidden() or self.in_code:
            return
        if data.strip():
            self._parts.append(data)

    def _flush(self) -> None:
        text = normalize(" ".join(self._parts))
        if text:
            self.blocks.append(text)
        self._parts = []


def prose_blocks(text: str) -> list[str]:
    blocks = ProseBlocks()
    blocks.feed(text)
    blocks.close()
    blocks._flush()
    return blocks.blocks


class VisibleBlocks(HTMLParser):
    """Synlig tekst plus overskrifterne i de tabeller der er synlige.

    En lukket `<details>` er ikke synlig uden et klik, så dens indhold tæller
    ikke. Det er den tunge del: en gratis- forklaring gemt i en lukket FAQ
    er netop den måde denne fejlform kommer tilbage på.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden = HiddenStack()
        self.parts: list[str] = []
        self.in_json_ld = False
        self.table_headers: list[list[str]] = []
        self.comparisons: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._in_header = False

    def _is_hidden(self) -> bool:
        return bool(self.hidden)

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}
        style = attributes.get("style", "")
        hidden = (
            tag in HIDDEN_TAGS
            or "hidden" in attributes
            or attributes.get("aria-hidden", "").casefold() == "true"
            or re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", style, re.I) is not None
            # En <details> uden `open` er lukket. `hidden` i attributerne
            # dækker ikke dette, og det er den vigtigste skjulested.
            or (tag == "details" and "open" not in attributes)
        )
        if tag == "script" and attributes.get("type", "").casefold() == "application/ld+json":
            self.in_json_ld = True
        if tag == "body":
            self.hidden.enter_body()
        if hidden and tag not in VOID_TAGS:
            self.hidden.open(tag)
        if self._is_hidden():
            return
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
            if tag == "th":
                self._in_header = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_json_ld:
            self.in_json_ld = False
        if tag in ("td", "th"):
            if self._cell is not None and self._row is not None:
                self._row.append(normalize(" ".join(self._cell)))
            self._cell = None
            if tag == "th":
                self._in_header = False
        elif tag == "tr" and self._row is not None and self._table is not None:
            self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            if self._table:
                self.table_headers.append(self._table[0])
                self.comparisons.append(self._table)
            self._table = None
        self.hidden.close(tag)

    def handle_data(self, data: str) -> None:
        if self.in_json_ld or self._is_hidden():
            return
        self.parts.append(data)
        if self._cell is not None:
            self._cell.append(data)

    @property
    def text(self) -> str:
        return normalize(" ".join(self.parts))


def free_pro_tables(text: str) -> list[tuple[list[list[str]], int]]:
    """Synlige gratis/Pro-sammenligningstabeller, med Pro-kolonnens index.

    Kun synlige: en lukket `<details>`, `<head>`, JSON-LD eller en `style`
    med `display:none` tæller ikke, fordi det er præcis de steder en
    sammenligning bliver usynlig uden at forsvinde fra koden.

    Pro-kolonnen er den første overskrift der ligner en betalt udgave, men
    ikke ligner den gratis. `Feature` og `Free` kan ikke være den, og
    `Pro (not released)` kan godt være det — en kolonne der siger "Pro,
    ikke udgivet endnu" er stadig den kolonne, der lover noget.
    """
    blocks = VisibleBlocks()
    blocks.feed(text)
    blocks.close()
    tables: list[tuple[list[list[str]], int]] = []
    for rows in blocks.comparisons:
        header = rows[0]
        if not any(FREE_LABEL.search(cell) for cell in header):
            continue
        paid_column = next(
            (index for index, cell in enumerate(header)
             if PAID_LABEL.search(cell) and not FREE_LABEL.search(cell)),
            None,
        )
        if paid_column is not None:
            tables.append((rows, paid_column))
    return tables


def check_comparisons(catalog: dict, pages: list[tuple[str, str]]) -> list[str]:
    """En gratis/Pro-tabel skal vise forskellen, og den skal kun prise noget
    der kan købes.

    To regler, begge på *alle* sider og ikke kun på dem, der sælger et
    katalogprodukt — det var præcis det hul, der lod en helt ukendt
    "EAA Scanner Pro — $19/år" stå på en publiceret side i ugevisninger:

    1. **Tomme celler.** En sammenligningstabel med tomme celler er
       værre end ingen tabel: den lader som om den viser forskellen, og
       en køber kan ikke se den. Oprindelsen var ikke sløshed, men en
       oprydning (`2c9909d`) der fjernede `✓`-ikoner: de tre celler der
       kun indeholdt et `✓`, blev tomme, da symbolet forsvandt.
    2. **En pris uden en købsknap.** En Pro-kolonne der viser en pris, er
       et løfte om at pengene kan bruges. Hvis siden ingen steder har et
       betalingslink fra katalogen, er prisen ubetalingsbar — og den er
       dobbelt sådan, fordi produktet ikke findes i katalogen overhovedet.
       Samme fejl som en død knap, bare uden knappen.
    """
    links = catalog_links(catalog)
    problems: list[str] = []
    for relative, text in pages:
        has_payment_link = any(href in links for href, _ in parse_page(text)[1])
        for rows, paid_column in free_pro_tables(text):
            for index, row in enumerate(rows[1:], start=2):
                if len(row) < paid_column + 1:
                    continue
                blanks = [position for position, cell in enumerate(row[1:], start=2)
                          if not cell.strip()]
                if blanks:
                    problems.append(
                        f"{relative}: gratis/Pro-tabellen har tomme celler i række {index} "
                        f"({row[0][:40]!r}, kolonne {blanks[0]}) — den viser ikke, hvad niveauet giver"
                    )
                price = row[paid_column]
                if CURRENCY_AMOUNT.search(price) and not has_payment_link:
                    problems.append(
                        f"{relative}: Pro-kolonnen viser prisen {normalize(price)[:40]!r} i "
                        f"række {index} ({row[0][:40]!r}), men siden har ingen købsknap — "
                        f"prisen kan ikke betales, og produktet findes ikke i katalogen"
                    )
    return problems


#: Et element hvis hele formål er at vise en pris. Ikke en tilfældig
#: omtale i en løbende tekst — det er den forskel, der gør reglen brugbar.
#: `site/guides.html` og en GDPR-blogpost må gerne nævne $19 og €900.000;
#: de *tilbyder* ikke noget til det beløb.
PRICE_LABEL_CLASS = re.compile(r"^(?:[\w-]*-)?price(?:-(?:tag|now|amount|value))?$")

#: Et købssted uden for katalogen. Vi sælger gennem Stripe Payment Links,
#: så en pris ved siden af en tredjeparts-butik er enten en vare vi ikke
#: har, eller en markedsplads vi ikke kan levere fra.
FOREIGN_VENUE = re.compile(
    r"\bon\s+amazon\b|\bp[åa]\s+amazon\b|amazon\.(?:com|co|dk|de|deals)"
    r"|\bapp\s+store\b|\bgoogle\s+play\b|\bitch\.io\b|\bgumroad\b",
    re.I,
)

#: En betalt udgave, der er lovet men ikke findes. Opgave 41 fandt seks
#: sider med "Paid individual editions ($9.99 each) are planned once our
#: payment setup is complete" — og betalingsopsætningen har været komplet
#: siden 24/9, så påstanden var falsk om virksomhedens egen tilstand.
UNFULFILLED_CLAIM = re.compile(
    r"paid\s+(?:edition|individual|version|premium)"
    r"|individuel\w*\s+udgave|betalte\s+udgave"
    r"|\(\s*coming\s*\)|\bcoming\b|\bplanned\b(?!.*\bgratis\b)|\bkommende\b"
    r"|\bnot\s+for\s+sale\b|\bikke\s+til\s+salg\b|\bnot\s+released\b",
    re.I,
)


class PriceLabels(HTMLParser):
    """Synlig tekst i elementer der *er* en prislabel."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden = HiddenStack()
        self.in_json_ld = False
        self.in_code = 0
        self.depth = 0
        self.parts: list[str] = []
        self.labels: list[str] = []

    def _is_hidden(self) -> bool:
        return bool(self.hidden)

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}
        style = attributes.get("style", "")
        hidden = (
            tag in HIDDEN_TAGS
            or "hidden" in attributes
            or attributes.get("aria-hidden", "").casefold() == "true"
            or re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", style, re.I) is not None
            or (tag == "details" and "open" not in attributes)
        )
        if tag == "script" and attributes.get("type", "").casefold() == "application/ld+json":
            self.in_json_ld = True
        if tag == "body":
            self.hidden.enter_body()
        if hidden and tag not in VOID_TAGS:
            self.hidden.open(tag)
        if tag in CODE_TAGS and tag not in VOID_TAGS and not self._is_hidden():
            self.in_code += 1
        if self.depth:
            self.depth += 1
            return
        if self._is_hidden() or tag in VOID_TAGS:
            return
        signature = " ".join((attributes.get("class", "") + " " + attributes.get("id", "")).split())
        if signature and PRICE_LABEL_CLASS.match(signature):
            self.depth = 1
            self.parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_json_ld:
            self.in_json_ld = False
        if tag in CODE_TAGS and self.in_code > 0:
            self.in_code -= 1
        self.hidden.close(tag)
        if self.depth:
            self.depth -= 1
            if self.depth == 0:
                text = normalize(" ".join(self.parts))
                if text:
                    self.labels.append(text)
                self.parts = []

    def handle_data(self, data: str) -> None:
        if self.depth and not self.in_json_ld and not self._is_hidden() and not self.in_code:
            self.parts.append(data)


def price_labels(text: str) -> list[str]:
    labels = PriceLabels()
    labels.feed(text)
    labels.close()
    return labels.labels


def structured_offers(text: str) -> list[tuple[str, str | None]]:
    """`(price, availability)` fra JSON-LD `offers`, i dokumentrækkefølge.

    En `offers`-pris er en *maskinlæsbar* påstand om at noget kan købes til
    beløbet. Den er derfor strengere end en pris i løbende tekst: den er
    skrevet til søgemaskiner og til enhver der læser siden som data.
    """
    found: list[tuple[str, str | None]] = []
    for block in re.findall(
        r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", text, re.S | re.I
    ):
        try:
            data = json.loads(block)
        except (ValueError, TypeError):
            continue
        stack = [data]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                offers = item.get("offers")
                if isinstance(offers, dict) and "price" in offers:
                    found.append((str(offers.get("price")), offers.get("availability")))
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
    return found


def check_unbuyable_prices(catalog: dict, pages: list[tuple[str, str]]) -> list[str]:
    """En pris skal kun stå på en side, hvor den kan betales.

    Opgave 41 rettede 15 filer med **ingen port**. Det er præcis det
    mønster, opgave 26 fandt i rod-README'en: en rettelse uden gaten
    holder kun til næste researchiteration ved et tilfældigt læs. Tre
    former af den samme løgne, målt på de rigtige gamle filer:

    1. **Struktureret data.** `"price": "9.99"` med `PreOrder` i JSON-LD,
       på en side med nul betalingslinks. Søgemaskiner læser den.
    2. **En prislabel.** `<div class="price">$9.99</div>` — elementet
       *er* tilbudet, så beløbet er en invitation, ikke en omtale.
    3. **En løftet pris i prosa.** "Paid edition: $9.99 (coming)" og
       "NIS2 Compliance Kit e-book ($9.99 on Amazon)" — en pris ved
       siden af et købssted eller en udgave, der ikke findes.

    **Kriteriet er ikke "har siden en købsknap", men "kan beløbet betales
    her".** En side må gerne linke til et produkt den ikke sælger — det er
    sådan en tværhenvisning ser ud — men en pris der ikke kan betales på
    den side, hvor den står, er enten en løgn eller en død vej. Derfor
    afgøres hvert beløb mod den pris, katalogens produkter har, og kun
    det beløb der står ved siden af et betalingslink på *samme* side
    regnes som betalingsbart.

    **Nul er ikke en fejl.** `$0` og `"0"` er en sand måde at sige
    "gratis" på, og de er lige så sande som "Free". Uden den skelnelse
    ville porten være rød på `site/site-icons.html`, der skriver `$0`.

    **Prose, ikke kommandoer.** `<pre>` og `<code>` er holdt ude: en
    `$`-prompt i en terminal er ikke et pristilbud. Det er ikke en
    kosmetisk undtagelse — `parse_page` normaliserer linjeskift væk, så
    `$ pip install …` og den ærlige "not for sale yet" blev ét segment,
    og reglen fangede en *sand* side.
    """
    products = catalog["products"]
    link_to_key = {product["payment_link"]: key for key, product in products.items()}
    problems: list[str] = []

    for relative, text in pages:
        _, anchors = parse_page(text)
        # Hvilke beløb kan betales på netop denne side? Sammenlignes på
        # *tallet*, ikke på teksten: katalogens `$79/år pr. website` og
        # sidens `$79` er det samme beløb, og en streng tekstsammenligning
        # gjorde alle fire købssider røde på deres *egne* priser.
        sold = {link_to_key[href] for href, _ in anchors if href in link_to_key}
        payable = {value for value in
                   (amount_value(str(products[key]["price"])) for key in sold)
                   if value is not None}

        def unpayable(token: str) -> bool:
            """Er `token` et beløb uden tilsvarende købsmulighed på siden?"""
            value = amount_value(token)
            return value is not None and value > 0 and value not in payable

        def sold_text() -> str:
            return ", ".join(sorted(sold)) or "intet"

        for price, availability in structured_offers(text):
            if amount_value(price) in (None, 0.0):
                continue  # `price: "0"` er en sand gratis-angivelse
            if not unpayable(price):
                continue
            problems.append(
                f"{relative}: JSON-LD angiver et tilbud til {price!r}"
                f"{f' ({availability})' if availability else ''}, men siden kan ikke "
                f"betale det beløb — den sælger {sold_text()}. "
                f"Ret structured data, eller fjern den"
            )

        for label in price_labels(text):
            for token in CURRENCY_AMOUNT.findall(label):
                if unpayable(token):
                    problems.append(
                        f"{relative}: prislabelen viser {token!r} ({label[:50]!r}), men "
                        f"siden har ingen købsknap til det beløb — beløbet kan ikke betales"
                    )
                    break

        for block in prose_blocks(text):
            for sentence in re.split(r"(?<=[.!?])\s+|\s+[•·|]\s+", block):
                markers = [name for name, pattern in
                           (("et købssted uden for katalogen", FOREIGN_VENUE),
                            ("en betalt udgave der ikke findes", UNFULFILLED_CLAIM))
                           if pattern.search(sentence)]
                if not markers:
                    continue
                for token in CURRENCY_AMOUNT.findall(sentence):
                    if unpayable(token):
                        problems.append(
                            f"{relative}: {normalize(sentence)[:90]!r} nævner {token!r} "
                            f"ved siden af {' og '.join(markers)} — beløbet kan ikke betales "
                            f"på denne side"
                        )
                        break
    return problems


# ── Hvor en kunde bliver sendt hen for at købe ───────────────────────────
#
# `check_comparisons` læser HTML-sider. Den læser ikke de filer, en kunde
# *installerer* — og det var præcis der den værste fejl stod: `desktop/index.html`
# skrev "Purchase a license at <død vært>" og opgav en $19-pris på et produkt,
# der ikke findes i kontrakten. Brugeren får den besked i en Electron-app,
# hvor der ikke er en side ved siden af med en købsknap, så den er en
# dødsport, ikke en konverteringsmulighed.
#
# Reglen er derfor skærpet i forhold til siderne: på en *side* er en Pro-pris
# uden købsknap en konverteringsfejl, fordi produktet sælges et andet sted.
# I en *klient* er den en løgn, fordi klienten er det eneste sted brugeren
# ser. Derfor gælder kravet om et betalingslink hele klientens fil.
#
# **Kendte begrænsning, opskrevet frem for skjult:** porten kræver, at linjen
# peger et sted hen (`DESTINATION`). En ren "Purchase a licence" uden nogen
# adresse giver intet fund, fordi den ikke kan skelnes fra en knap, der gør
# noget i appen. Til gengæld kan reglen ikke slås fra med en advarsel.
CLIENT_DIRS = (
    "desktop",
    "extension-clean-copy",
    "extension-clean-copy-firefox",
    "extension-clean-copy-vscode",
    "obsidian-plugin",
    "page-profile",
    "scanner",
    "companion",
)
CLIENT_SKIP_DIRS = {"node_modules", "dist", "__pycache__", ".wrangler"}
CLIENT_SUFFIXES = {".html", ".js", ".mjs", ".cjs", ".py", ".md", ".json", ".txt", ".ts"}
BUY_INSTRUCTION = re.compile(
    r"\b(?:purchase|purchasing|buy|order|order now|shop|checkout|get (?:a|your) licen[cs]e"
    r"|køb|bestil)\b",
    re.I,
)
LICENCE_WORD = re.compile(r"\b(?:licen[cs]e|pro|premium|paid)\b", re.I)
#: En *henvisning* til et købssted: et anker, en URL eller et værtnavn.
#:
#: Uden den var porten rød på den ærlige sætning. Den rettede tekst siger
#: "There is no Pro licence ... and no price to pay for one — so there is
#: nothing to buy yet", og den har både "licence" og "buy" på samme linje.
#: Det er ikke en død vej, det er modsatte: en tekst der fortæller, at
#: der intet er at købe. Derfor skal fejlen være en *henvisning* — noget der
#: peger et sted hen — og ikke et ord. Så kan reglen ikke slås fra ved at
#: skrive en advarsel ind i den.
DESTINATION = re.compile(
    r"<a\s[^>]*href|https?://|\b[\w-]+(?:\.[\w-]+)*\.(?:dev|com|tools|dk|io|app|net)\b",
    re.I,
)


def client_sources() -> list[Path]:
    """Kildefiler der en kunde får i hånden: de shippede klienter.

    Ikke `site/` — siderne er dækket af `check_comparisons` med den anden
    regel. Ikke `dist/` — det er bygget, og bygget er gaten's første step.
    """
    files: list[Path] = []
    for name in CLIENT_DIRS:
        base = ROOT / name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or CLIENT_SKIP_DIRS & set(path.parts):
                continue
            if path.suffix.lower() in CLIENT_SUFFIXES:
                files.append(path)
    return files


def check_client_purchase_targets(
    catalog: dict, paths: list[Path] | None = None
) -> list[str]:
    """En klient må ikke sende brugeren hen for at købe noget uden et købssted.

    Kun ét fund gjaldt i hele familien, og det var den alvorlige fejl:
    `desktop/index.html:72`. Alt andet — extensionernes "Pro $19/år" og
    "Clean Copy Pro ($19/year)" — er *sandt*, fordi `clean-copy-pro` findes i
    kontrakten; de linker bare ikke til kassen i den samme fil, hvilket er en
    anden fejl end at sende nogen ud i det blå.
    """
    links = catalog_links(catalog)
    problems: list[str] = []
    for path in client_sources() if paths is None else paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        # Selftesten sender syntetiske filer ind uden for repoet, så et
        # `relative_to(ROOT)` ville kaste i selve porten. Opgave 28 gjorde
        # det samme med en sti, der pegede ud af repoet, og den dræbte alle
        # tre deploys i stedet for at advare om sig selv.
        try:
            label = str(path.relative_to(ROOT))
        except ValueError:
            label = str(path)
        if any(link in text for link in links):
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if (BUY_INSTRUCTION.search(line) and LICENCE_WORD.search(line)
                    and DESTINATION.search(line)):
                problems.append(
                    f"{label}:{number}: beder brugeren om at købe eller "
                    f"bestille en licens ({normalize(line)[:60]!r}), men filen indeholder intet "
                    f"betalingslink fra katalogen. I en klient er det en død vej — der er ingen "
                    f"købsside ved siden af den."
                )
    return problems


CHECKOUT_LINK_RE = re.compile(r"https://(?:buy|donate)\.stripe\.com/")
TRACKER_SRC_RE = re.compile(r"""<script[^>]*\bsrc=["']/track\.js["']""")
BUY_CLICK_RE = re.compile(r"""event:\s*['"]buy-click['"]""")
CLICK_LISTENER_RE = re.compile(r"""addEventListener\(\s*['"]click['"]""")


def check_buy_click_tracking(
    catalog: dict,
    pages: list[tuple[str, str]] | None = None,
    track_text: str | None = None,
) -> list[str]:
    """En købsknap ingen måler, er en købsknap ingen ved om virker.

    Målt før reglen blev skrevet: 1 af 13 købssider sendte et `buy-click`, og
    de tre sider med et kassalink uden `/track.js` (`/activate/`, `/da/activate/`
    og `/support`) sendte slet ingen begivenheder. Det er den fejl, der gør
    "0 salg" uden et datagrundlag — vi kunne ikke se et eneste forsøg på at
    købe, fordi ingen af knapperne meldte sig. Derfor skal både siden og
    sporingen findes: en side med en kassalink skal indlæse trackeren, og
    trackeren skal stadig have kliklytteren.

    Matcherens selve regex (`^https://(buy|donate).stripe.com/`) kan ikke
    dømmes statisk, så reglen lover præcis det den kan bevise: siden indlæser
    en tracker, og trackeren lytter på klik og sender `buy-click`.
    """
    if track_text is None:
        try:
            track_text = TRACK_JS.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return [f"{TRACK_JS.relative_to(ROOT)}: kan ikke læses, så intet købsklik kan måles"]
    problems: list[str] = []
    if not BUY_CLICK_RE.search(track_text):
        problems.append(
            f"{TRACK_JS.relative_to(ROOT)}: sender ikke længere et 'buy-click'. Uden det er "
            "hvert købsklik på tværs af de 13 købssider usynligt."
        )
    if not CLICK_LISTENER_RE.search(track_text):
        problems.append(
            f"{TRACK_JS.relative_to(ROOT)}: har ingen click-lytter, så ingen købsknap "
            "kan melde fra — uanset hvilken begivenhed den ellers sender."
        )
    portal = catalog.get("billing_portal")
    for relative, text in source_pages() if pages is None else pages:
        _, anchors = parse_page(text)
        checkouts = {
            href for href, _ in anchors
            if CHECKOUT_LINK_RE.match(href) and href != portal
        }
        if not checkouts:
            continue
        if TRACKER_SRC_RE.search(text) or BUY_CLICK_RE.search(text):
            continue
        problems.append(
            f"{relative}: har {len(checkouts)} synligt kassalink, men indlæser ikke /track.js "
            "og sender ikke selv et 'buy-click' — klik på købsknappen kan ikke ses"
        )
    return problems


def check_free_tier(catalog: dict, pages: list[tuple[str, str]]) -> list[str]:
    """En side der sælger en licens, skal vise hvad den gratis udgave giver.

    Kun produkter med `kind: license`. En donation og et download-produkt har
    per definition ingen gratis udgave at vise, så de skal ikke fejle på en
    regel de ikke kan opfylde.

    Sætningen skal stå i læsbar tekst: hverken i `<head>`, i JSON-LD, i en
    attribut eller i en lukket `<details>`. En løsning på at skjule den
    gratis-fordelen i en collapsed FAQ er derfor umulig.
    """
    products = catalog["products"]
    offers = catalog.get("offers")
    if not isinstance(offers, list):
        return []
    by_path = dict(pages)
    problems: list[str] = []
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        product = products.get(offer.get("product"))
        if not isinstance(product, dict) or product.get("kind") != "license":
            continue
        relative = offer.get("path")
        text = by_path.get(relative)
        if text is None:
            continue  # check_offers melder en manglende fil.
        blocks = VisibleBlocks()
        blocks.feed(text)
        blocks.close()
        visible = blocks.text
        comparisons = [rows for rows, _ in free_pro_tables(text)]
        if FREE_TIER_PHRASES.search(visible) or comparisons:
            continue
        problems.append(
            f"{relative}: sælger {offer.get('product')} men siger aldrig, hvad den gratis "
            f"udgave giver — hverken i læsbar tekst eller i en synlig gratis/Pro-tabel"
        )
    return problems


LANG_ATTR_RE = re.compile(r"""<html[^>]*\blang\s*=\s*["']([A-Za-z-]+)["']""", re.I)


def page_lang(relative: str, text: str | None = None) -> str:
    """Sproget for en købsside, så et dansk krav ikke kan passes med engelsk.

    Kilden er sidens *erklærede* `lang`, fordi det er den eneste der ikke kan
    ligge. Stien var det eneste signal før, og målingen viser at den lyver for en
    tredjedel af de danske sider: 14 af dem hedder `<navn>-da.html` i stedet for at
    ligge under `/da/` (`scan-da`, `nis2-check-da`, `cookie-check-da`, …), så de
    blev talt som engelske. Det er ikke en tænkt fejl — `check_language_coverage`
    bygger både `spoken` og `sold` på denne funktion, så en dansk købsside uden
    `/da/` i stien passede som engelsk, og kravet om dansk dækning faldt bort.

    Stien er fallback for filer der ikke kan læses eller ikke erklærer et sprog
    porten kender, så en ny `/da/`-flade stadig gør kravet gælde med det samme.
    """
    if text is None:
        try:
            text = (ROOT / relative).read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
    match = LANG_ATTR_RE.search(text[:2000])
    if match:
        code = match.group(1).lower().split("-")[0]
        if code in LANG_NAMES:
            return code
    parts = relative.replace("\\", "/").split("/")
    return "da" if "da" in parts[1:-1] else "en"


LANG_NAMES = {"en": "engelsk", "da": "dansk"}


def lang_name(code: str) -> str:
    """Sprogkoden som læsevenlig tekst i en fejlmeddelelse.

    Kun *teksten* er navngivet — betingelsen i `check_language_coverage` er
    afledt af `page_lang()`, så et tredje sprog gør kravet gælde uden at denne
    tabel kender det. Ukendte koder vises som de er, aldrig som det engelske.
    """
    return LANG_NAMES.get(code, code)


def check_language_coverage(catalog: dict, pages: list[tuple[str, str]]) -> list[str]:
    """Et licensprodukt skal kunne købes på hvert sprog sitet udgiver.

    Fejlformen er målt, ikke antaget. Da `eucomply-pro` fik sin danske købsside,
    havde de tre øvrige licensprodukter en dansk side hver, og den nye side blev
    skrevet som en *fuld dansk købsside* — uden at nogen spiste, at det er
    betingelsen for at danske læsere kan købe. Sproget afledes af
    `page_lang()` over alle sider i `site/` (305 sider: 199 `en`, 106 `da`), så
    kravet er ikke en navneliste: en ny `/da/`-flade gør det gælde uden at
    porten ved det på forhånd, og en slettet dansk købsside får den ikke til at
    falde sammen til ét sprog.

    Kun produkter der faktisk sælges i dette repo gates. `transmute-desktop`
    erklærer ingen `pro_features` — katalogens egen note siger at købslinket
    ligger på transmute.run — så det ville være en fejl at kræve en side her.

    Beviset ligger i selftesten: katalogen *før* den danske side gav præcis én
    rød, `eucomply-pro`, og dagens katalog giver nul.
    """
    products = catalog["products"]
    offers = catalog.get("offers")
    if not isinstance(offers, list):
        return []
    spoken = {page_lang(str(relative)) for relative, _ in pages}
    for offer in offers:
        if isinstance(offer, dict):
            spoken.add(page_lang(str(offer.get("path"))))
    if len(spoken) < 2:
        return []  # Kun ét sprog: der er ingen anden, der mangler.
    sold: dict[str, set[str]] = {}
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        key = str(offer.get("product"))
        product = products.get(key)
        if not isinstance(product, dict) or product.get("kind") != "license":
            continue
        features = product.get("pro_features")
        if not isinstance(features, list) or not features:
            continue
        sold.setdefault(key, set()).add(page_lang(str(offer.get("path"))))
    problems: list[str] = []
    for key, langs in sorted(sold.items()):
        missing = sorted(spoken - langs)
        if not missing:
            continue
        first = lang_name(missing[0])
        problems.append(
            f"catalog: {key} sælges kun på "
            f"{', '.join(lang_name(code) for code in sorted(langs))}, men sitet udgiver også {first}. "
            f"Uden en {first} købsside kan en {first} læser hverken se hvad Pro giver eller hvor det "
            f"sælges, så hver {first} flade må sende folk videre til den anden sprogs side."
        )
    return problems


def check_pro_features(catalog: dict, pages: list[tuple[str, str]]) -> list[str]:
    """En side der sælger en licens, skal navngive den betalte udgaves funktioner.

    `check_free_tier` gater den *gratis* halvdel. Denne gater den *betalte*:
    hvis katalogen erklærer `pro_features` for et produkt, skal hver side der
    sælger det navngive dem alle i læsbar tekst.

    Fejlformen er målt, ikke antaget. `/clean-copy-tool` og `/activate/` sagde
    begge at en Pro-nøgle giver "batch conversion and custom cleanup rules",
    mens forsiden — katalogens egen "første skridt i købsrejsen" — kun nævnte
    batch og fyldte den anden halvdel med "supports development of the free
    version". Den eneste Pro-funktion i den udvidelse, siden selv beder folk
    installere, var altså aldrig nævnt der.

    Samme krav som `check_free_tier`: kun synlig tekst, aldrig `<head>`,
    JSON-LD, attributter eller en lukket `<details>`. Et produkt uden
    `pro_features` i katalogen gates ikke — kravet må kun gælde, hvor
    katalogen faktisk erklærer, hvad der sælges, ellers ville porten finde
    fejl på produkter, den ikke kan dømme.
    """
    products = catalog["products"]
    offers = catalog.get("offers")
    if not isinstance(offers, list):
        return []
    by_path = dict(pages)
    problems: list[str] = []
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        product = products.get(offer.get("product"))
        if not isinstance(product, dict) or product.get("kind") != "license":
            continue
        features = product.get("pro_features")
        if not isinstance(features, list) or not features:
            continue
        relative = offer.get("path")
        text = by_path.get(relative)
        if text is None:
            continue  # check_offers melder en manglende fil.
        blocks = VisibleBlocks()
        blocks.feed(text)
        blocks.close()
        haystack = normalize(blocks.text).casefold()
        lang = page_lang(str(relative), text)
        for feature in features:
            if not isinstance(feature, dict) or not isinstance(feature.get("id"), str):
                continue
            labels = feature.get("labels")
            labels = labels.get(lang) if isinstance(labels, dict) else None
            if not isinstance(labels, list) or not labels:
                problems.append(
                    f"{relative}: {offer.get('product')} erklærer pro_features "
                    f"{feature.get('id')!r} uden {lang}-labels i katalogen"
                )
                continue
            if any(normalize(str(label)).casefold() in haystack for label in labels):
                continue
            where = feature.get("where")
            suffix = f" ({where})" if isinstance(where, str) else ""
            problems.append(
                f"{relative}: sælger {offer.get('product')} men navngiver ikke Pro-funktionen "
                f"{feature.get('id')!r}{suffix} i læsbar tekst. Katalogen erklærer den som en del "
                f"af det købspris, så en kunde der læser denne side kan ikke se, hvad de får."
            )
    return problems


def pro_labels(feature: object, lang: str) -> list[str] | None:
    """Labels for én deklareret Pro-funktion i ét sprog, eller None.

    `None` betyder at katalogen ikke kan dømme siden: en manglende
    `labels`-nøgle må ikke give en grøn port, men en *tom* liste må heller
    ikke gøre den rød for en funktion, ingen side nogensinde nævner.
    """
    if not isinstance(feature, dict) or not isinstance(feature.get("id"), str):
        return None
    labels = feature.get("labels")
    labels = labels.get(lang) if isinstance(labels, dict) else None
    if not isinstance(labels, list) or not labels:
        return None
    return [str(label) for label in labels if str(label)]


class TierCards(HTMLParser):
    """Synlig tekst i hvert `tier-card`, med en dybde der gør det muligt at
    læse ét kort uden at få det næste med.

    Kortene er sidens *salgstavle*: en `<div class="tier-card pro">` der
    lister hvad en betalt kunde får. Det er derfra opgave 69s fejl kom —
    "Pro-versionen tilføjer sammenligning, batch og historik" lå i Pro-kortets
    `<li>`, selv om historik er gratis. Kortene er derfor den eneste flade hvor
    "dette er betalt" er en påstand, og de er målt på den rigtige markup
    (`.tier-card` + `.tier-card.pro`) frem for på en navneliste.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, list[str]]] = []
        self.cards: dict[str, list[str]] = {}
        self.active: tuple[str, list[str]] | None = None
        self.skip = 0

    def _tier(self, attrs: dict[str, str | None]) -> str | None:
        classes = (attrs.get("class") or "").split()
        if "tier-card" not in classes:
            return None
        return "pro" if "pro" in classes else "free"

    def handle_starttag(self, tag: str, attrs) -> None:
        values = {key: (value or "") for key, value in attrs}
        if tag in ("script", "style"):
            self.skip += 1
            return
        if self.skip:
            return
        tier = self._tier(values)
        if tier is not None:
            # Kortene ligger ikke i hinanden, så det seneste kort ejer al
            # tekst indtil det lukker. Uden den ejerskab fik hvert barn sin egen
            # tom liste, og porten ville have været grøn af en fejl grund.
            self.active = (tier, [])
        self.stack.append((tier or "", []))

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
            return
        if self.skip or not self.stack:
            return
        tier, _ = self.stack.pop()
        if tier and self.active and self.active[0] == tier:
            self.cards.setdefault(tier, []).append(
                " ".join(" ".join(self.active[1]).split())
            )
            self.active = None

    def handle_data(self, data: str) -> None:
        if self.skip or self.active is None or not data.strip():
            return
        self.active[1].append(data)

    def text(self, tier: str) -> str:
        return normalize(" ".join(self.cards.get(tier, [])))


class TierBlocks(HTMLParser):
    """Synlig tekst pr. blok, med to ting ved hver blok: ligger den i
    Pro-kortet, og er den en celle i en gratis/Pro-tabel.

    Blokke er de elementer en læser læser som ét afsnit: `<p>`, `<li>`, en
    overskrift, en tabelcelle. `<div>` og `<section>` er *beholdere*, ikke
    afsnit, så de åbner ingen blok — ellers ville en hel side være én blok,
    og "nævner den betalte udgave" ville blive sand for alt. En blok der
    ligger i en anden blok (`<li><p>`) får teksten begge steder, så den
    ydre afsnitstext ikke taber en indlejret sætning.
    """

    BLOCK_TAGS = frozenset(
        {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th",
         "caption", "blockquote", "dd", "dt", "figcaption"}
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden = HiddenStack()
        self.skip = 0
        self.in_json_ld = False
        self.open_tags: list[tuple[str, bool]] = []
        self.blocks: list[dict] = []
        self._open: list[dict] = []
        self.pro_depth = 0

    def _is_hidden(self) -> bool:
        return bool(self.hidden)

    def _tier(self, attrs: dict[str, str]) -> str | None:
        classes = (attrs.get("class") or "").split()
        if "tier-card" not in classes:
            return None
        return "pro" if "pro" in classes else "free"

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}
        style = attributes.get("style", "")
        hidden = (
            tag in HIDDEN_TAGS
            or "hidden" in attributes
            or attributes.get("aria-hidden", "").casefold() == "true"
            or re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", style, re.I) is not None
            or (tag == "details" and "open" not in attributes)
        )
        if tag == "script" and attributes.get("type", "").casefold() == "application/ld+json":
            self.in_json_ld = True
        if tag == "body":
            self.hidden.enter_body()
        if hidden and tag not in VOID_TAGS:
            self.hidden.open(tag)
        if self._is_hidden():
            self.open_tags.append((tag, False))
            return
        if tag in ("script", "style"):
            self.skip += 1
            self.open_tags.append((tag, False))
            return
        if self.skip:
            self.open_tags.append((tag, False))
            return
        entered_pro = self._tier(attributes) == "pro"
        if entered_pro:
            self.pro_depth += 1
        if tag in self.BLOCK_TAGS:
            self._open.append({
                "tag": tag,
                "parts": [],
                "pro": self.pro_depth > 0,
                "heading": tag.startswith("h") and len(tag) == 2 and tag[1].isdigit(),
            })
        self.open_tags.append((tag, entered_pro))

    def _unwind(self, tag: str) -> None:
        """Luk alle åbne elementer til og med `tag`, og tæl Pro-kort-dybden ned
        igen for hvert af dem. Uden denne fortryder en `</div>` der lukker et
        helt Pro-kort, dybden ikke, og resten af siden dømmes som betalt."""
        while self.open_tags:
            open_tag, entered_pro = self.open_tags.pop()
            if entered_pro and self.pro_depth:
                self.pro_depth -= 1
            if open_tag == tag:
                return

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_json_ld:
            # Uden denne nulstilling forblev `in_json_ld` sandt resten af
            # dokumentet, og hele `<body>` blev dømt som usynlig. Målt på
            # `site/clean-copy.html`: 51 blokke, alle tomme.
            self.in_json_ld = False
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        self.hidden.close(tag)
        if self.skip:
            self._unwind(tag)
            return
        # Kun en blok-slutning lukker blokke. En inline-slutning (`</strong>`,
        # `</code>`, `</a>`) må ikke lukke den `<p>` den står i — målt på
        # `site/activate/index.html`: `</strong>` i det nye gratis-afsnit
        # lukkede afsnittet efter den følende tekst, så porten så kun
        # "you do not have a license key?" og resten af sætningen forsvandt.
        # Det er samme fejl som opgave 69/70/71: et krav der ikke kan fejle,
        # fordi halvdelen af teksten aldrig blev læst.
        if tag in self.BLOCK_TAGS:
            while self._open and self._open[-1]["tag"] != tag:
                self.blocks.append(self._open.pop())
            if self._open:
                self.blocks.append(self._open.pop())
        self._unwind(tag)

    def _close(self, block: dict) -> None:
        self.blocks.append(block)

    def handle_data(self, data: str) -> None:
        if self.skip or self.in_json_ld or self._is_hidden() or not data.strip():
            return
        for block in self._open:
            block["parts"].append(data)

    def close(self) -> None:
        super().close()
        while self._open:
            self._close(self._open.pop())


def paid_contexts(text: str) -> tuple[str, str, bool]:
    """Sidens betalte og gratis side som læsbar tekst, målt på markupen.

    Målt først, skrevet bagefter. Opgave 72 efterlod at porten springer syv —
    i virkeligheden otte — købssider fra, fordi de kun har et
    `<div class="tier-card pro">`. De otte har hver sin form på at sige hvad
    der er gratis og hvad der koster, målt på de rigtige filer:

    | Side | Flade |
    |---|---|
    | `clean-copy.html` (EN/DA) | et afsnit i "Price"/"Pris" der siger *Free* … og et der siger hvad Pro *tilføjer* |
    | `activate/` (EN/DA) | to sætninger i brødteksten, resten et kassalink |
    | `clean-copy-tool` | tabel med `id="free-vs-pro"`, kolonnerne Free/Pro |
    | `deskuptime/` (EN/DA) | `id="compare"`, `h3` "Desktop Pro" + `h3` "CLI and desktop app" |
    | `blog/desktop-website-monitor-cli` | tabel med kolonnerne Free/Pro ($19) |
    | `compliance-report` (EN) | Pro-kort, men ingen gratis-kort og ingen tabel |

    Så en port der kun læser kortene kan ikke dømme otte af de ti købssider,
    og det er præcis de sider hvor opgave 69s fejlform lå. Derfor tre kilder,
    alle målt på markupen og ikke på en navneliste:

    1. **Pro-kortet** og **den betalte spalte** i en synlig gratis/Pro-tabel.
       Strukturelt: de to er den betalte side, uanset hvad teksten siger — en
       `<li>Gratis kerne … Pro-versionen tilføjer … historik</li>` i Pro-kortet
       nævner *gratis* og er stadig den betalte side.
    2. **Et afsnit, en punktumtekst eller en overskrift der nævner den
       betalte udgave og ikke den gratis.** Det er den rene tekstform: "Pro
       adds two things …" og `<h3>Desktop Pro</h3>`. Begge nævner den
       betalte side, ingen af dem siger *gratis*, og derfor er de betalt
       kontekst. Omvendt er en blok der nævner *begge* ("Free and Pro")
       en sammenligning, ikke en betalt side, og den dømmes ikke som sådan.

    Returnerer `(betalte, gratis, har_flade)`. Den tredje værdi er målet der
    forsvandt: før denne iteration læste porten kun sider med et Pro-kort og
    sprang de otte øvrige fra **uden at sige det**, så en gratis-funktion der
    flyttede til en betalt sætning på dem ville være usynlig. Med
    `har_flade=False` er det en melding i stedet for en tavshed.
    """
    blocks = TierBlocks()
    blocks.feed(text)
    blocks.close()
    paid_cells: set[str] = set()
    free_cells: set[str] = set()
    for rows, paid_column in free_pro_tables(text):
        free_column = next(
            (index for index, cell in enumerate(rows[0])
             if FREE_LABEL.search(cell) and not PAID_LABEL.search(cell)),
            None,
        )
        for row in rows[1:]:
            paid_cell = row[paid_column] if len(row) > paid_column else ""
            free_cell = (row[free_column] if free_column is not None
                         and len(row) > free_column else "")
            if paid_cell.strip():
                paid_cells.add(normalize(paid_cell).casefold())
            if free_cell.strip():
                free_cells.add(normalize(free_cell).casefold())
            # En kryds-tabel skriver funktionens *navn* i rækkens første
            # celle og svarer "✓"/"—" i spalterne, så cellerne alene forteller
            # intet om hvad det er. Rækkens navn hører derfor til den spalte
            # der svarer ja — og til ingen, når begge spalter svarer ja,
            # fordi en funktion begge udgaver har ikke er en *betalt* påstand
            # og heller ikke en *gratis* ene.
            if not row or not row[0].strip():
                continue
            label = normalize(row[0]).casefold()
            paid_yes = YES_CELL.match(paid_cell) is not None
            free_yes = YES_CELL.match(free_cell) is not None
            if paid_yes and not free_yes:
                paid_cells.add(label)
            elif free_yes and not paid_yes:
                free_cells.add(label)
    cards = TierCards()
    cards.feed(text)
    cards.close()
    pro_card = cards.text("pro")
    free_card = cards.text("free")

    # Casefold på begge sider: kort-teksten kommer med sin oprindelige
    # casing, blokkene kommer casefoldede, og de skal kunne sammenlignes.
    paid: list[str] = [pro_card.casefold()] if pro_card else []
    free: list[str] = [free_card.casefold()] if free_card else []
    paid.extend(sorted(paid_cells))
    free.extend(sorted(free_cells))
    for block in blocks.blocks:
        body = normalize(" ".join(block["parts"])).casefold()
        if not body:
            continue
        if block["pro"]:
            paid.append(body)
            continue
        says_paid = PAID_LABEL.search(body) is not None
        says_free = FREE_LABEL.search(body) is not None
        if says_paid and not says_free:
            paid.append(body)
        elif says_free and not says_paid:
            free.append(body)
    return " ".join(paid), " ".join(free), bool(paid or free or paid_cells or free_cells)


def free_features_by_product(catalog: dict) -> dict[str, list[dict]]:
    """`free_features` pr. produkt — det koden giver uden en nøgle.

    Modstående til `not_built_by_product`: den holder oversiden i tråd med
    koden, denne holder *undersiden* i tråd med koden. En `pro_features`-post
    uden kode bagved gør en kunde betale for ingenting; en `free_features`-post
    uden kode bagved får en funktion solgt som betalt, fordi ingen holdt øje.
    """
    products = catalog.get("products")
    if not isinstance(products, dict):
        return {}
    out: dict[str, list[dict]] = {}
    for key, product in products.items():
        if not isinstance(product, dict):
            continue
        entries = product.get("free_features")
        if isinstance(entries, list) and entries:
            out[key] = [entry for entry in entries if isinstance(entry, dict)]
    return out


def check_free_features(catalog: dict, pages: list[tuple[str, str]]) -> list[str]:
    """Pro-kortet må ikke sælge en funktion koden giver gratis.

    De tre andre checks dømmer hver én retning: `check_free_tier` kræver at
    siden siger noget om gratis, `check_pro_features` at den nævner det
    betalte, `check_pro_not_built` at den ikke lover det ubygde. Ingen af dem
    kan se en funktion *flyttet* fra gratis til betalt — fordi det kræver at
    porten ved hvilke funktioner der er gratis, og det stod ingen steder.

    Målt, ikke antaget. Opgave 69 fandt på den danske købsside: "Gratis kerne —
    web-tjekket er altid gratis. Pro-versionen tilføjer sammenligning, batch og
    historik." Historik er gratis i `page_profile.py` — `--history` er ikke
    gated, og `append_history()` (:1088) kører før det første `require_pro`
    (:1094). Sælgeren havde altså taget betaling for en funktion alle har, og
    ingen port så det, fordi ingen kendte den gratis side.

    Begge retninger dømmes nu, og kun for den side der sælger: Pro-kortet må
    ikke sælge den, og **Gratis-kortet skal nævne den**. Den anden retning er
    NEXT_TASK (1) fra opgave 70, og den var målt i mangel: med kun den første
    regel var porten grøn selv om Gratis-sætningen var slettet fra begge sider,
    så den eneste måde at rette en gratis-funktion der lå i Pro-kortet var
    "fjern påstanden" i stedet for "sig hvor den hører hjemme". En kunde der
    læser salgstavlen skal kunne se hvad der er gratis — ellers er
    `free_features` en påstand uden flade, og det er præcis den fejlklasse
    opgave 69 startede.

    Kravet er **én** sætning pr. sprog, så et katalogsignal der ligner to
    synonymer ikke giver to halve krav. Mere end én label er derfor en
    særskilt katalogfejl, ikke to krav på samme funktion.
    """
    products = catalog.get("products")
    offers = catalog.get("offers")
    if not isinstance(products, dict) or not isinstance(offers, list):
        return []
    declared = free_features_by_product(catalog)
    if not declared:
        return []
    by_path = dict(pages)
    problems: list[str] = []
    # Katalogfejl meldes én gang pr. produkt: de gælder alle sider, så at
    # gentage dem pr. tilbud ville fylde rapporten med den samme linje.
    for key, features in declared.items():
        for feature in features:
            where = feature.get("where")
            if not isinstance(where, str) or not where.strip():
                problems.append(
                    f"{key}: free_features {feature.get('id')!r} står i katalogen uden en "
                    f"`where` der peger på den kode der giver den gratis"
                )
            # Ét sprog, ét krav. Rækker katalogen to sætninger for den samme
            # funktion, kan porten ikke vide hvilken af dem der skal stå i
            # Gratis-kortet, så den melder katalogfejlen og bruger den første
            # sætning. Synonymer er en redaktørbeslutning, ikke et krav.
            labels_by_lang = feature.get("labels")
            if isinstance(labels_by_lang, dict):
                for lang, values in sorted(labels_by_lang.items()):
                    if isinstance(values, list) and len(values) != 1:
                        problems.append(
                            f"{key}: free_features {feature.get('id')!r} erklærer "
                            f"{len(values)} {lang}-labels, men porten dømmer én sætning "
                            f"pr. sprog. Skriv den ene sætning der står i Gratis-kortet."
                        )
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        key = offer.get("product")
        product = products.get(key)
        if not isinstance(product, dict) or product.get("kind") != "license":
            continue
        relative = offer.get("path")
        text = by_path.get(relative)
        if text is None:
            continue  # check_offers melder en manglende fil.
        paid_side, free_side, has_surface = paid_contexts(text)
        if not has_surface:
            # Før denne iteration sprang porten sådanne sider fra i tavshed, og
            # en gratis-funktion der flyttede til en betalt sætning på dem var
            # usynlig. Tavshed er den værste slags port: den ligner en der
            # passerer. Se `paid_contexts` for målingen af de otte flader.
            problems.append(
                f"{relative}: siden sælger {key}, men har ingen synlig gratis/Pro- "
                f"flade at vise de {len(declared.get(key, []))} erklærede gratis-"
                f"funktioner på. Skriv dem i en sammenligning, et kort eller en "
                f"sætning der siger gratis — ellers er påstanden uden flade."
            )
            continue
        lang = page_lang(str(relative), text)
        for feature in declared.get(key, []):
            where = feature.get("where")
            if not isinstance(where, str) or not where.strip():
                continue  # Allerede meldt ovenfor, én gang pr. produkt.
            labels = pro_labels(feature, lang)
            if labels is None:
                problems.append(
                    f"{relative}: {key} erklærer free_features {feature.get('id')!r} "
                    f"uden {lang}-labels i katalogen"
                )
                continue
            for label in labels:
                if normalize(label).casefold() in paid_side:
                    problems.append(
                        f"{relative}: Pro-kortet sælger {label!r}, men katalogen siger at "
                        f"{feature.get('id')!r} er gratis ({where}). En betalt kunde må "
                        f"ikke købe en funktion alle har."
                    )
            # Den anden retning: den skal *stå* i Gratis-kortet, fordi det er
            # den eneste flade hvor "dette er gratis" er en påstand. Sætningen
            # er den første, så et katalogsignal med flere sætninger (meldt
            # ovenfor) dømmes på én af dem i stedet for på ingen.
            said_free = labels[0]
            if normalize(said_free).casefold() not in free_side:
                problems.append(
                    f"{relative}: den gratis side af siden nævner ikke {said_free!r}, men katalogen "
                    f"siger at {feature.get('id')!r} er gratis ({where}). Kunden skal kunne "
                    f"se hvad de får gratis på den side der sælger — ellers er påstanden "
                    f"uden flade."
                )
    return problems


def not_built_by_product(catalog: dict) -> dict[str, list[dict]]:

    """`pro_not_built` pr. produkt — de løfter, koden modsiger.

    Målt i opgave 49, ikke formodet. `deskuptime-pro` lovede "email and
    webhook alerts" på fire live flader, og der er **ingen e-mail-kode**
    i hverken `deskuptime/` eller `deskuptime-desktop/`; produktets egen
    `src/features.js:145-153` markerer rækken `implemented: false`.
    `eucomply-pro` lovede "Continuous compliance monitoring", "Unlimited
    scans and history tracking", "Client-ready branded PDF reports" og
    "Priority support (email within 24h)" — de tre første findes ikke i
    nogen fil, og den fjerde er den supportlast, missionen forbyder.

    Katalogen er derfor ikke kun en prisliste: den siger nu, hvad hvert
    betalt produkt *faktisk* gater, og hvilke løfter der ikke findes.
    """
    products = catalog.get("products")
    if not isinstance(products, dict):
        return {}
    out: dict[str, list[dict]] = {}
    for key, product in products.items():
        if not isinstance(product, dict):
            continue
        entries = product.get("pro_not_built")
        if isinstance(entries, list) and entries:
            out[key] = [entry for entry in entries if isinstance(entry, dict)]
    return out


def check_pro_not_built(catalog: dict, pages: list[tuple[str, str]]) -> list[str]:
    """En købsside må ikke love en Pro-funktion, katalogen siger ikke findes.

    Modstående til `check_pro_features`: den gater at siden *nævner* det
    betalte, denne gater at den ikke *lover det ubygde*. Begge læser kun
    synlig tekst, aldrig `<head>`, JSON-LD, attributter eller en lukket
    `<details>` — en kunde skal kunne læse det samme som porten.

    Hver post skal have en `where`, der peger på koden der afviser løftet.
    Uden den er listen bare en måde at slå en fejl fra på, så en post
    uden bevis meldes i stedet for at troes.
    """
    products = catalog.get("products")
    offers = catalog.get("offers")
    if not isinstance(products, dict) or not isinstance(offers, list):
        return []
    not_built = not_built_by_product(catalog)
    by_path = dict(pages)
    problems: list[str] = []
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        key = offer.get("product")
        product = products.get(key)
        if not isinstance(product, dict) or product.get("kind") != "license":
            continue
        relative = offer.get("path")
        text = by_path.get(relative)
        if text is None:
            continue  # check_offers melder en manglende fil.
        blocks = VisibleBlocks()
        blocks.feed(text)
        blocks.close()
        haystack = normalize(blocks.text).casefold()
        lang = page_lang(str(relative), text)
        for entry in not_built.get(key, []):
            where = entry.get("where")
            if not isinstance(where, str) or not where.strip():
                problems.append(
                    f"{key}: pro_not_built {entry.get('id')!r} står i katalogen uden en "
                    f"`where` der peger på koden der modsiger løftet"
                )
                continue
            labels = pro_labels(entry, lang)
            if labels is None:
                problems.append(
                    f"{relative}: {key} erklærer pro_not_built {entry.get('id')!r} "
                    f"uden {lang}-labels i katalogen"
                )
                continue
            for label in labels:
                if normalize(label).casefold() in haystack:
                    problems.append(
                        f"{relative}: {key} lover {label!r}, men katalogen siger at "
                        f"{entry.get('id')!r} ikke er bygget ({where}). En betalt kunde "
                        f"må ikke købe et løfte koden ikke holder."
                    )
    return problems


def check_checkout_notes(catalog: dict, worker_text: str | None = None) -> list[str]:
    """Samme krav på `/checkout`-noten i workeren.

    Fundet fra opgave 45: en flade ingen port læste. `/api/stripe/checkout`
    bygger sin beskrivelse af hvert produkt i en `note`-streng i
    `site/_worker.js`, og den løvede "email & webhook alerts" for
    `deskuptime-pro` — den samme løgned som på fire HTML-sider, på en
    route ingen af dem så.
    """
    not_built = not_built_by_product(catalog)
    if not not_built:
        return []
    text = WORKER.read_text(encoding="utf-8") if worker_text is None else worker_text
    pairs = re.findall(r"product: '([a-z0-9-]+)'[\s\S]{0,400}?note: '([^']*)'", text)
    if not pairs:
        return ["site/_worker.js: ingen `product:`/`note:`-par fundet i /checkout"]
    problems: list[str] = []
    for key, note in pairs:
        haystack = normalize(note).casefold()
        for entry in not_built.get(key, []):
            for lang in ("en", "da"):
                labels = pro_labels(entry, lang)
                for label in labels or []:
                    if normalize(label).casefold() in haystack:
                        problems.append(
                            f"site/_worker.js: /checkout-noten for {key} lover {label!r}, "
                            f"men {entry.get('id')!r} ikke er bygget ({entry.get('where')})"
                        )
    return problems


def parse_page(text: str) -> tuple[str, list[tuple[str, str]]]:
    visible = Page()
    visible.feed(text)
    visible.close()
    anchors = AnchorCollector()
    anchors.feed(text)
    anchors.close()
    return visible.text, anchors.anchors


def load_catalog(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def catalog_links(catalog: dict) -> set[str]:
    links = {product["payment_link"] for product in catalog["products"].values()}
    portal = catalog.get("billing_portal")
    if isinstance(portal, str):
        links.add(portal)
    return links


def scan_files() -> list[Path]:
    files: list[Path] = []
    for name in SCAN_ROOTS:
        base = ROOT / name
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or SKIP_DIRS & set(path.parts):
                continue
            files.append(path)
    files.extend(ROOT / name for name in SCAN_FILES if (ROOT / name).is_file())
    return files


def check_catalog(catalog: dict) -> list[str]:
    problems: list[str] = []
    products = catalog.get("products")
    if not isinstance(products, dict) or not products:
        return ["tools/stripe_catalog.json: products skal være et ikke-tomt objekt"]
    links: dict[str, str] = {}
    for key, product in products.items():
        if not PRODUCT_KEY.match(key):
            problems.append(f"catalog: ugyldig product_key {key!r}")
        if not isinstance(product, dict):
            problems.append(f"catalog: {key} er ikke et objekt")
            continue
        for field in ("name", "kind", "price", "price_note", "payment_link"):
            if not isinstance(product.get(field), str) or not product[field]:
                problems.append(f"catalog: {key} mangler {field}")
        if not isinstance(product.get("payment_link"), str):
            continue
        if not product["payment_link"].startswith(("https://buy.stripe.com/", "https://donate.stripe.com/")):
            problems.append(f"catalog: {key} har et link uden for Stripe Payment Links")
        previous = links.setdefault(product["payment_link"], key)
        if previous != key:
            problems.append(f"catalog: link {product['payment_link']} bruges af både {previous} og {key}")
    for key in REQUIRED_PRODUCT_KEYS:
        if key not in products:
            problems.append(f"catalog: kontraktproduktet {key} mangler")
        elif products[key].get("kind") != REQUIRED_KINDS[key]:
            problems.append(f"catalog: {key} har kind {products[key].get('kind')!r}, forventet {REQUIRED_KINDS[key]!r}")
    return problems


def check_contract_doc(catalog: dict) -> list[str]:
    path = ROOT / catalog.get("contract", "docs/stripe-kontrakt.md")
    if not path.is_file():
        return [f"{catalog.get('contract')}: kontraktdokumentet mangler"]
    text = path.read_text(encoding="utf-8")
    problems: list[str] = []
    for key, product in catalog["products"].items():
        if f"`{key}`" not in text:
            problems.append(f"{path.name}: product_key {key} står ikke i tabellen")
        if product["payment_link"] not in text:
            problems.append(f"{path.name}: betalingslink for {key} står ikke i tabellen")
    for extra in LINK_PATTERN.findall(text):
        if extra not in catalog_links(catalog):
            problems.append(f"{path.name}: link {extra} er ikke i allowlisten")
    return problems


def check_worker(catalog: dict) -> list[str]:
    text = WORKER.read_text(encoding="utf-8")
    products = catalog["products"]
    problems: list[str] = []
    block = re.search(r"const STRIPE_PRODUCTS = \{(.*?)\n\};", text, re.S)
    if block is None:
        return ["site/_worker.js: STRIPE_PRODUCTS blev ikke fundet"]
    worker_keys = set(re.findall(r"^\s*'([a-z0-9-]+)':\s*\{", block.group(1), re.M))
    entries = dict(re.findall(r"^\s*'([a-z0-9-]+)':\s*\{([^\n]*)$", block.group(1), re.M))
    for key in sorted(worker_keys - set(products)):
        problems.append(f"site/_worker.js: produktet {key} mangler i allowlisten")
    for key, product in sorted(products.items()):
        if key not in worker_keys:
            problems.append(f"site/_worker.js: allowlisten har {key}, som workeren ikke kender")
            continue
        if key in REQUIRED_PRODUCT_KEYS and product["name"] not in text.split("const STRIPE_PRODUCTS")[1]:
            problems.append(f"site/_worker.js: navnet på {key} afviger fra allowlisten ({product['name']!r})")
    # Kun de årlige produkter må markeres som abonnement, ellers får et engangskøb
    # et kundeportalslink den aldrig kan bruge — eller et abonnement mangler det.
    worker_subscriptions = {key for key, entry in entries.items() if re.search(r"\bsubscription:\s*true\b", entry)}
    catalog_subscriptions = {key for key, product in products.items() if product.get("subscription") is True}
    for key in sorted(worker_subscriptions - catalog_subscriptions):
        problems.append(f"site/_worker.js: {key} er markeret som abonnement, men allowlisten siger engangskøb")
    for key in sorted(catalog_subscriptions - worker_subscriptions):
        problems.append(f"site/_worker.js: {key} er et årligt abonnement i allowlisten, men er ikke markeret som abonnement")
    if catalog_subscriptions and catalog.get("billing_portal") not in text:
        problems.append("site/_worker.js: kundeportalen mangler i workeren, så abonnenter ikke kan opsige selv")
    links_block = re.search(r"const STRIPE_LINKS = \{(.*?)\n  \};", text, re.S)
    if links_block is None:
        problems.append("site/_worker.js: STRIPE_LINKS blev ikke fundet")
        return problems
    for short, link in re.findall(r"(\w+):\s*'(https://buy\.stripe\.com/[A-Za-z0-9]+)'", links_block.group(1)):
        owner = next((key for key, product in products.items() if product["payment_link"] == link), None)
        if owner is None:
            problems.append(f"site/_worker.js: STRIPE_LINKS.{short} er ikke i allowlisten ({link})")
        if link not in text:
            problems.append(f"site/_worker.js: STRIPE_LINKS.{short} mangler i allowlisten")
    return problems


def check_links(catalog: dict) -> list[str]:
    allowed = catalog_links(catalog)
    problems: list[str] = []
    for path in scan_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for link in sorted(set(LINK_PATTERN.findall(text))):
            if link not in allowed:
                problems.append(f"{path.relative_to(ROOT)}: {link} er ikke i allowlisten")
    return problems


def price_tokens(text: str) -> set[str]:
    return {normalize(token) for token in PRICE_TOKEN.findall(text)}


ROUTE_PATTERN = re.compile(r"^/(?:[a-z0-9._~-]+/)*[a-z0-9._~-]*$")


def route_file(domain: str, route: str) -> Path | None:
    """Den byggede fil for en public route, hvis buildet ligger i dist/."""
    if (ROOT / "dist" / domain).is_dir():
        base = ROOT / "dist" / domain / route.strip("/")
        for candidate in (base.with_suffix(".html"), base / "index.html", base):
            if candidate.is_file():
                return candidate
    return None


def check_routes(offers: list[dict], core_pages: object) -> list[str]:
    """Hver købsside skal have sit domæne og sin public route, og de fire
    centrale produktsider skal findes med den CTA de erklærer."""
    problems: list[str] = []
    listed = {(offer.get("path"), offer.get("product")) for offer in offers if isinstance(offer, dict)}
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        domain, route = offer.get("domain"), offer.get("route")
        label = f"{offer.get('path')} ({offer.get('product')})"
        if domain not in KNOWN_DOMAINS:
            problems.append(f"{label}: ukendt domæne {domain!r}")
        if not isinstance(route, str) or not ROUTE_PATTERN.match(route):
            problems.append(f"{label}: ugyldig route {route!r}")
            continue
        if domain in KNOWN_DOMAINS and route_file(domain, route) is None:
            problems.append(f"{label}: {domain}{route} findes ikke i dist/")

    if not isinstance(core_pages, list) or len(core_pages) != 4:
        problems.append("catalog: core_pages skal være præcis fire centrale produktsider")
        return problems
    for page in core_pages:
        if not isinstance(page, dict):
            problems.append("catalog: en central produktside er ikke et objekt")
            continue
        label = f"core_page {page.get('product')!r}"
        if (page.get("path"), page.get("product")) not in listed:
            problems.append(f"{label}: {page.get('path')} sælger ikke {page.get('product')} i inventoriet")
        if not str(page.get("why", "")).strip():
            problems.append(f"{label}: mangler begrundelse")
    return problems


# --------------------------------------------------------------------------
# Indgang til en købsside. Målt i det *byggede* dist, fordi det er der
# domæneopløsningen er sket: cleancopy.tools, deskuptime.com, mahope.tools og
# bugbottle.dev deler alle `site/`, så `href="/"` i en mahope.tools-side er
# ikke en indgang til cleancopy.tools' `/`. Uden den opløsning ville reglen
# være grøn for de forkerte grunde — præcis fejlformen opgave 59 målte, da
# `scan-da.html` sendte danske læsere til den engelske købsside mens den
# danske lå i sitemap med nul indgange.
# --------------------------------------------------------------------------

# Kun disse tre attributter er en indgang. `<link rel=canonical>` og
# `hreflang` er maskinlæsbare henvisninger, og en URL i en inline
# JSON-Streng (søgeindekset) er slet ikke et link — tælles de med, bliver
# reglen grøn fordi en side nævner stien i et script.
ENTRY_ATTRS = {"a": "href", "area": "href", "form": "action"}
ENTRY_SKIP = ("script", "style", "template", "noscript")


class EntryLinks(HTMLParser):
    """Alle udgående links i et bygget dokument, i dokumentrækkefølge."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in ENTRY_SKIP:
            self.skip += 1
            return
        attribute = ENTRY_ATTRS.get(tag)
        if attribute is None or self.skip:
            return
        value = {key.lower(): item or "" for key, item in attrs}.get(attribute, "").strip()
        if value:
            self.links.append(value)

    def handle_startendtag(self, tag: str, attrs) -> None:
        if tag not in ENTRY_SKIP:  # `<script/>` er ikke en åbning
            self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag in ENTRY_SKIP and self.skip:
            self.skip -= 1


def entry_links(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    parser = EntryLinks()
    parser.feed(text)
    parser.close()
    return parser.links


def route_key(domain: str, route: str) -> tuple[str, str]:
    """`(domæne, route)` i én form, så `/da/x`, `/da/x/` og `/da/x.html` er samme.

    Katalogens `route` er den *public* route uden filendelse, fordi det er den
    der står i canonical, hreflang og sitemap. En fils dist-sti er derimod
    `da/x.html` eller `da/x/index.html`, så uden denne normalisering ville
    indgangen aldrig matche købssiden.
    """
    path = (route.split("#")[0].split("?")[0] or "/").replace("\\", "/")
    if not path.startswith("/"):
        path = "/" + path
    path = re.sub(r"/index\.html$", "/", path)
    if path.endswith(".html"):
        path = path[: -len(".html")]
    if len(path) > 1:
        path = path.rstrip("/")
    return (domain, path or "/")


def resolve_entry(domain: str, page: str, href: str) -> tuple[str, str] | None:
    """`(domæne, route)` et link peger på, eller None hvis det er et andet sted."""
    target = urlsplit(urljoin(f"https://{domain}/{page}", href))
    if target.scheme not in ("http", "https") or target.netloc not in KNOWN_DOMAINS:
        return None
    return route_key(target.netloc, target.path)


def entry_point_index(dist_root: Path | None = None) -> dict[tuple[str, str], set[str]]:
    """`(domæne, route)` -> de byggede sider der linker til den."""
    root = dist_root or (ROOT / "dist")
    index: dict[tuple[str, str], set[str]] = {}
    for domain in KNOWN_DOMAINS:
        base = root / domain
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.html")):
            relative = path.relative_to(base).as_posix()
            # En 404-side er ikke en indgang: ingen lærer følger den med vilje,
            # så en købsside der kun 404'en peger på, er stadig uopdaget.
            if relative == "404.html" or relative.endswith("/404.html"):
                continue
            here = route_key(domain, "/" + relative)
            targets = {key for key in
                       (resolve_entry(domain, relative, href) for href in entry_links(path))
                       if key is not None and key != here}
            for key in targets:
                index.setdefault(key, set()).add(f"{domain}/{relative}")
    return index


def check_buy_page_entry(offers: list[dict],
                         index: dict[tuple[str, str], set[str]],
                         dist_root: Path | None = None) -> list[str]:
    """En købsside skal kunne nås: mindst én indgang fra en anden bygget side.

    Fejlformen er målt, ikke antaget. `/da/compliance-report` lå i sitemap som
    det eneste danske købsside-hit, og **intet** i kodebasen linkede til den:
    `site/scan-da.html` nævnte EUComply Pro, men pegede på `/compliance-report`
    i den anden ende. Sitemap er ikke en indgang — det er en maskinlæsbar liste,
    ingen læser følger den — så siden var uopdaget for præcis den læser den
    findes for.

    Kun *købssider*. Resten af `dist/` har 8 sider uden indgang (to
    DeskUptime-værktøjer, Clean Copy's MCP-side, `/terms`, `/thanks` m.fl.), og
    en regel for hele sitemap ville være en sitemap-port, ikke en
    konverteringsregel. De otte er målt og skrevet som opgave i planen.

    Selve linket er fundet i det byggede `dist/`, fordi det er der domænet er
    opløst: de fire sites deler `site/`, så et rodrelativt link kun er en
    indgang på det domæne der faktisk udgiver målsiden. Et krydsdomæne-link
    tæller med — buildet skriver det som en absolut URL, så en læser kan følge
    det — mens hreflang og canonical gør ikke, fordi de ikke er en vej hen til
    siden. En købsside i et domæne der ikke er bygget springes over: så er det
    `check_routes` der melder den manglende build, med den præcise fejl.
    """
    root = dist_root or (ROOT / "dist")
    problems: list[str] = []
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        domain, route = offer.get("domain"), offer.get("route")
        if not isinstance(domain, str) or not isinstance(route, str):
            continue  # check_routes melder en manglende/ugyldig route.
        if not (root / domain).is_dir():
            continue
        key = route_key(domain, route)
        sources = index.get(key) or set()
        if sources:
            continue
        problems.append(
            f"{offer.get('path')} ({offer.get('product')}): {domain}{route} sælges, men ingen "
            f"af de byggede sider linker til den. Den ligger i sitemap, og en sitemap er ikke en "
            f"indgang en læser kan følge — så købssiden er uopdaget for alle der ikke gætter "
            f"URL'en. Link til den fra en side læseren faktisk lander på."
        )
    return problems


def check_offers(catalog: dict) -> tuple[list[str], list[dict]]:
    products = catalog["products"]
    offers = catalog.get("offers")
    if not isinstance(offers, list):
        return ["tools/stripe_catalog.json: offers skal være en liste"], []
    problems: list[str] = []
    seen: dict[tuple[str, str], int] = {}
    inventory: list[dict] = []

    for offer in offers:
        if not isinstance(offer, dict):
            problems.append("catalog: et offer er ikke et objekt")
            continue
        path = ROOT / offer.get("path", "")
        product = offer.get("product")
        if not path.is_file():
            problems.append(f"catalog: tilbuddet på {offer.get('path')!r} findes ikke")
            continue
        if product not in products:
            problems.append(f"catalog: {offer['path']} bruger ukendt product_key {product!r}")
            continue
        if (offer["path"], product) in seen:
            problems.append(f"catalog: {offer['path']} står to gange for {product}")
        seen[(offer["path"], product)] = seen.get((offer["path"], product), 0) + 1

        visible, anchors = parse_page(path.read_text(encoding="utf-8"))
        link = products[product]["payment_link"]
        ctas = [(href, text) for href, text in anchors if href == link]
        tokens = sorted(price_tokens(visible))
        inventory.append({
            "path": offer["path"],
            "domain": offer.get("domain"),
            "route": offer.get("route"),
            "product": product,
            "price": products[product]["price"],
            "prices_on_page": tokens,
            "cta": [text for _, text in ctas],
            "link": link,
        })
        if len(ctas) != 1:
            problems.append(f"{offer['path']}: {len(ctas)} synlige CTA'er for {product}, forventet præcis 1")
        allowed_tokens = set(offer.get("prices") or [])
        unknown = sorted(set(tokens) - allowed_tokens)
        if unknown:
            problems.append(f"{offer['path']}: udokumenterede priser {unknown} (tilladt: {sorted(allowed_tokens)})")
        for required in offer.get("requires_text", []):
            if normalize(required).casefold() not in visible.casefold():
                problems.append(f"{offer['path']}: mangler påkrævet tekst {required!r}")
        for forbidden in offer.get("forbids_text", []):
            if normalize(forbidden).casefold() in visible.casefold():
                problems.append(f"{offer['path']}: forbudt tekst {forbidden!r}")

    listed = {(offer.get("path"), offer.get("product")) for offer in offers if isinstance(offer, dict)}
    for path in scan_files():
        if path.suffix != ".html":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        relative = str(path.relative_to(ROOT))
        if relative.startswith("dist/"):
            continue
        _, anchors = parse_page(text)
        visible_links = {href for href, _ in anchors}
        for link in sorted(visible_links & set(LINK_PATTERN.findall(text))):
            if link == catalog.get("billing_portal"):
                # Kundeportalen er ikke en købsknap; den har sin egen sidekontrol.
                continue
            owner = next((key for key, product in products.items() if product["payment_link"] == link), None)
            if owner is None:
                problems.append(f"{relative}: synligt link {link} er ikke i allowlisten")
            elif (relative, owner) not in listed:
                problems.append(f"{relative}: synlig købsknap for {owner} mangler i inventoryet")
    return problems, inventory


def check_billing_portal(catalog: dict) -> list[str]:
    """Kundeportalen skal findes præcis de steder, en abonnent kan opsige fra.

    `/thanks` bygger linket ud fra leveringssvaret, så den skal referere
    `billing_portal`; `/support` og `/terms/` linker til den direkte.
    """
    problems: list[str] = []
    portal = catalog.get("billing_portal")
    if not isinstance(portal, str) or not portal.startswith("https://billing.stripe.com/p/login/"):
        return [f"tools/stripe_catalog.json: billing_portal skal være en billing.stripe.com-punktal, fik {portal!r}"]
    pages = catalog.get("portal_pages")
    if not isinstance(pages, list) or not pages:
        return ["tools/stripe_catalog.json: portal_pages skal være en ikke-tom liste"]
    for page in pages:
        path = ROOT / page
        if not path.is_file():
            problems.append(f"tools/stripe_catalog.json: portalsiden {page!r} findes ikke")
            continue
        text = path.read_text(encoding="utf-8")
        if portal not in text and "billing_portal" not in text:
            problems.append(f"{page}: mangler kundeportalen, så abonnenter kan ikke opsige selv")
    for path in scan_files():
        relative = str(path.relative_to(ROOT))
        # Kun sider: workerens brug af portalen er styret af check_worker.
        if path.suffix != ".html" or relative in pages or relative.startswith("dist/"):
            continue
        if portal in path.read_text(encoding="utf-8", errors="ignore"):
            problems.append(f"{relative}: bruger kundeportalen uden at være deklareret portalside")
    return problems


def check_forbidden_claims() -> list[str]:
    problems: list[str] = []
    for path in scan_files():
        if path.suffix != ".html":
            continue
        relative = str(path.relative_to(ROOT))
        if relative.startswith("dist/"):
            continue
        visible, _ = parse_page(path.read_text(encoding="utf-8"))
        lowered = visible.casefold()
        for claim in FORBIDDEN_CLAIMS:
            if claim in lowered:
                problems.append(f"{relative}: forbudt købs-påstand {claim!r}")
    return problems


def check_analysis_location(pages: list[tuple[str, str]]) -> list[str]:
    """Hvor rapporten beregnes, skal være sandt — og koden er dommeren.

    Målt i opgave 58, ikke formodet. `site/compliance-report.html` sagde to
    steder i synlig tekst at rapporten blev "analysed in your browser", efter at
    opgave 54 flyttede fund-beregningen til `/api/report` i workeren. Kunden
    betaler $79 for en GDPR-påstand om sine egne data, så det er den dyreste
    slags fejl på siden: en kunde, der troede på den, ville have bedt om en
    opbevaringsoverholdelse og fået en rapport der alligevel var beregnet
    server-side.

    Reglen er derfor **ikke** en ordliste over forbudte formuleringer. Den er
    strukturel i den ene ende: kun en side der faktisk henter en
    server-analyse-rute kan få en fejl. Det er derfor `/scan` og
    `/scan-da` går fri — de to analyserer stadig i browseren, så deres
    påstand er *sand*, og en global ordliste ville have tvunget en rettelse
    som gjorde siderne til løgnere. Samme fejlklasse som opgave 26 fund 1.

    I den anden ende må sætningen ikke være en ordliste heller: en kunde skal
    kunne skrive den samme påstand om en anden ting. Derfor kræves en
    *sætning* der både siger hvor (browseren) og at der analyseres i den.
    """
    problems: list[str] = []
    for relative, text in pages:
        if not any(route in text for route in SERVER_ANALYSIS_ROUTES):
            continue
        visible, _ = parse_page(text)
        for sentence in SENTENCE_SPLIT_RE.split(visible):
            if BROWSER_LOCATION_RE.search(sentence) and ANALYSIS_VERB_RE.search(sentence):
                problems.append(
                    f"{relative}: siden henter {'/'.join(SERVER_ANALYSIS_ROUTES)} "
                    f"(analysen sker på serveren) men siger i synlig tekst at browseren "
                    f"analyserer: {sentence.strip()[:120]!r}"
                )
                break
    return problems


def source_pages() -> list[tuple[str, str]]:
    """Alle sider i `site/`, som parret (relativ sti, tekst).

    Kun kilden, ikke `dist/`: bygget er gaten's første step og kopierer
    siderne uændret, så en kilde der er ren giver et rent dist.
    """
    pages: list[tuple[str, str]] = []
    for path in scan_files():
        if path.suffix != ".html":
            continue
        relative = str(path.relative_to(ROOT))
        if relative.startswith("dist/"):
            continue
        try:
            pages.append((relative, path.read_text(encoding="utf-8")))
        except (UnicodeDecodeError, OSError):
            continue
    return pages


def check_deliverable(catalog: dict, pages: list[tuple[str, str]], paid: dict | None = None) -> list[str]:
    """Et download-produkt må kun sælges, når filen kan leveres.

    Betalte filer ligger i Cloudflare KV, og `/api/download` svarer 503 når
    nøglen `paidfile:<fil>` mangker. `tools/paid_content.json` er den eneste
    kilde til om den findes. Så længe den ikke gør det, tager et køb penge
    ind og leverer intet — og fordi produkterne sælges gennem statiske Stripe
    Payment Links kan checkout ikke blokeres. Så må siden ikke tilbyde købet.

    Begge retninger er fejl. Uden den modsatte regel ville et produkt, der
    bliver leveringsklart, kunne forblive uden købsside og så aldrig sælges
    igen.
    """
    problems: list[str] = []
    relative_inventory = str(PAID_CONTENT.relative_to(ROOT))
    if paid is None:
        if not PAID_CONTENT.is_file():
            return [f"{relative_inventory}: betalt-indholds-inventaret mangler"]
        paid = json.loads(PAID_CONTENT.read_text(encoding="utf-8"))
    entries = paid.get("products")
    if not isinstance(entries, list):
        return [f"{relative_inventory}: products skal være en liste"]
    inventory = {entry.get("product_key"): entry for entry in entries if isinstance(entry, dict)}
    sold = {offer.get("product") for offer in catalog.get("offers") or [] if isinstance(offer, dict)}

    for key, product in sorted(catalog["products"].items()):
        if product.get("kind") != "download":
            continue
        entry = inventory.get(key)
        if entry is None:
            problems.append(f"catalog: {key} er et download-produkt uden post i {relative_inventory}")
            continue
        if entry.get("kv_verified") is True:
            if key not in sold:
                problems.append(f"catalog: {key} kan leveres, men ingen købsside sælger det")
            continue
        files = ", ".join(entry.get("delivery_files") or []) or "ingen filer"
        for label, text in pages:
            if product["payment_link"] in text:
                problems.append(
                    f"{label}: sælger {key}, men filerne er ikke i KV ({files}) — "
                    f"køberen betaler for et køb der svarer 503 i /api/download. "
                    f"Sæt kv_verified på true i {relative_inventory} når de er uploadet."
                )
    return problems


def run(catalog: dict) -> tuple[list[str], list[dict]]:
    problems = check_catalog(catalog)
    problems += check_contract_doc(catalog)
    problems += check_worker(catalog)
    problems += check_links(catalog)
    offer_problems, inventory = check_offers(catalog)
    problems += offer_problems
    problems += check_routes(catalog.get("offers") or [], catalog.get("core_pages"))
    problems += check_buy_page_entry(catalog.get("offers") or [], entry_point_index())
    problems += check_billing_portal(catalog)
    problems += check_forbidden_claims()
    problems += check_analysis_location(source_pages())
    problems += check_deliverable(catalog, source_pages())
    problems += check_free_tier(catalog, source_pages())
    problems += check_pro_features(catalog, source_pages())
    problems += check_free_features(catalog, source_pages())
    problems += check_pro_not_built(catalog, source_pages())
    problems += check_language_coverage(catalog, source_pages())
    problems += check_checkout_notes(catalog)
    problems += check_comparisons(catalog, source_pages())
    problems += check_unbuyable_prices(catalog, source_pages())
    problems += check_client_purchase_targets(catalog)
    problems += check_buy_click_tracking(catalog, source_pages())
    return problems, inventory


def discover_offers(catalog: dict) -> list[dict]:
    """Alle sider med en synlig købsknap, uanset inventaret."""
    products = catalog["products"]
    by_link = {product["payment_link"]: key for key, product in products.items()}
    found: list[dict] = []
    for path in scan_files():
        if path.suffix != ".html" or str(path.relative_to(ROOT)).startswith("dist/"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        visible, anchors = parse_page(text)
        ctas = [(href, label) for href, label in anchors if href in by_link]
        if not ctas:
            continue
        found.append({
            "path": str(path.relative_to(ROOT)),
            "prices_on_page": sorted(price_tokens(visible)),
            "ctas": [{"product": by_link[href], "text": label} for href, label in ctas],
        })
    return found


def self_test() -> int:
    """Beviser at gaten faktisk fanger de fem driftformer."""
    good = load_catalog(CATALOG)
    rogue_link = {**good, "products": {
        **good["products"],
        "clean-copy-pro": {**good["products"]["clean-copy-pro"],
                           "payment_link": "https://buy.stripe.com/ukjendtLink0"},
    }}
    missing_product = {**good, "products": {
        key: value for key, value in good["products"].items() if key != "deskuptime-pro"}}
    shared_link = {**good, "products": {
        **good["products"],
        "eucomply-nda-clauses": {**good["products"]["eucomply-nda-clauses"],
                                 "payment_link": good["products"]["eucomply-eaa-statement"]["payment_link"]},
    }}
    unsatisfiable_offer = {**good, "offers": [{
        "path": "site/books/compliance-bundle.html",
        "product": "eu-compliance-ebook-bundle",
        "prices": ["$29"],
        "requires_text": ["et krav der ikke kan stå på siden"],
    }]}
    uninventoried = {**good, "offers": []}
    # Muterer scenariet en side, der ikke lenger sælger noget, bliver det en
    # stum kontrol: den fejl, den skal fange, kan så ikke opstå. Derfor
    # verificeres her, at mutationen rent faktisk rammer en købsside.
    wrong_domain = {**good, "offers": [
        {**offer, "domain": "example.com"} if offer["path"] == "site/clean-copy.html" else offer
        for offer in good["offers"]]}
    if wrong_domain["offers"] == good["offers"]:
        print("SELFTEST FEJLER: domænescenariet muterer ingen købsside — det er en stum kontrol")
        return 1
    missing_core = {**good, "core_pages": good["core_pages"][:3]}
    rogue_portal = {**good, "billing_portal": "https://billing.stripe.com/p/login/ukjendtPortal0"}
    no_subscriptions = {**good, "products": {
        key: {field: value for field, value in product.items() if field != "subscription"}
        for key, product in good["products"].items()}}

    # 5: et download-produkt uden filer i KV må ikke sælges. Kilden scanneres
    # normalt, så scenarierne sender syntetiske sider ind i stedet for at
    # røre de rigtige filer — ellers ville selftesten selv skrive den fejl,
    # den skal fange.
    report_kit = good["products"]["eucomply-report-kit"]["payment_link"]
    synthetic_sale = [("site/eksempel.html", f'<a href="{report_kit}">Buy</a>')]
    undeliverable = check_deliverable(good, synthetic_sale)
    # Samme side med et produkt, der faktisk kan leveres: må ikke fejle.
    deliverable_page = [("site/eksempel.html", '<a href="https://buy.stripe.com/6oU4gy76PgvgdBIdAXbMQ00">Buy</a>')]
    should_pass = check_deliverable(good, deliverable_page)
    verified = json.loads(PAID_CONTENT.read_text(encoding="utf-8"))
    for entry in verified["products"]:
        if entry["product_key"] == "eucomply-report-kit":
            entry["kv_verified"] = True
    delisted = {**good, "offers": [
        offer for offer in good["offers"] if offer["product"] != "eucomply-report-kit"]}
    forgot_the_page = check_deliverable(delisted, [], verified)

    # 6: en Pro-side skal vise hvad den gratis udgave giver. Scenarierne er
    # syntetiske, så selftesten ikke skriver den fejl ind i de rigtige sider.
    clean_copy_link = good["products"]["clean-copy-pro"]["payment_link"]
    donate_link = good["products"]["support-mahope-oss"]["payment_link"]
    buys_only = f'<html><body><h1>Tool</h1><p>Convert text.</p><a href="{clean_copy_link}">Buy</a></body></html>'
    says_free = (f'<html><body><p>The free version is the complete tool, not a trial.</p>'
                 f'<a href="{clean_copy_link}">Buy</a></body></html>')
    says_free_but_buried = (f'<html><body><details><summary>FAQ</summary>'
                            f'<p>The free version is the complete tool, not a trial.</p></details>'
                            f'<a href="{clean_copy_link}">Buy</a></body></html>')
    empty_table = (f'<html><body><table><tr><th>Feature</th><th>Free</th><th>Pro</th></tr>'
                   f'<tr><td>Batch mode</td><td>—</td><td></td></tr>'
                   f'<tr><td>Price</td><td>free</td><td>$19/year</td></tr></table>'
                   f'<a href="{clean_copy_link}">Buy</a></body></html>')
    donation = f'<html><body><p>Thanks for using the free tools.</p><a href="{donate_link}">Donate</a></body></html>'
    # Pro-funktioner. Den danske variant skal med vilje kun nævne den EN funktion
    # på engelsk, så selftesten beviser at side-sproget vælger de danske labels —
    # ellers ville porten være grøn på en dansk side, der aldrig siger det danske.
    names_one_feature = (f'<html><body><p>Pro adds batch conversion in the web tool.</p>'
                         f'<a href="{clean_copy_link}">Buy</a></body></html>')
    names_one_feature_da = (f'<html><body><p>Pro giver batch-konvertering i webværktøjet.</p>'
                            f'<a href="{clean_copy_link}">Køb</a></body></html>')
    names_second_feature = '<p>Pro also gives you custom cleanup rules in the extension.</p>'
    second_feature_buried = (f'<html><body><p>Pro adds batch conversion.</p><details>'
                             f'<summary>Pro</summary><p>And custom cleanup rules.</p></details>'
                             f'<a href="{clean_copy_link}">Buy</a></body></html>')
    only_offer = [{**offer, "path": "site/eksempel.html"} for offer in good["offers"]
                  if offer["product"] == "clean-copy-pro"]
    free_tier_only = {**good, "offers": only_offer}
    no_free_tier = check_free_tier(free_tier_only, [("site/eksempel.html", buys_only)])
    buried_free_tier = check_free_tier(free_tier_only, [("site/eksempel.html", says_free_but_buried)])
    # Pro-værdien skal være *navngivet*, ikke kun prissat. Forsiden nævnte
    # batch men aldrig de regler, der er den eneste Pro-funktion i den
    # udvidelse siden selv beder folk installere.
    da_offer = [{**offer, "path": "site/da/eksempel.html"} for offer in only_offer]
    pro_only = {**good, "offers": only_offer}
    pro_missing = check_pro_features(pro_only, [("site/eksempel.html", names_one_feature)])
    pro_missing_da = check_pro_features({**good, "offers": da_offer},
                                        [("site/da/eksempel.html", names_one_feature_da)])
    # Samme krav som check_free_tier: kun synlig tekst. En funktion der kun
    # står i en lukket `<details>` er ikke noget en kunde læser før et køb.
    pro_buried = check_pro_features(pro_only, [("site/eksempel.html", second_feature_buried)])
    # Negativ kontrol: en side der navngiver begge funktioner skal være grøn,
    # ellers ville porten blot forbyde at sælge.
    pro_complete = check_pro_features(
        pro_only, [("site/eksempel.html", names_one_feature + names_second_feature)])
    # Og et produkt uden `pro_features` i katalogen gates ikke: porten må
    # ikke finde fejl på produkter den ikke kan dømme.
    no_features = {**good, "products": {
        **good["products"],
        "clean-copy-pro": {k: v for k, v in good["products"]["clean-copy-pro"].items()
                           if k != "pro_features"}}}
    pro_undeclared = check_pro_features(
        {**no_features, "offers": [{**offer, "product": "clean-copy-pro"} for offer in only_offer]},
        [("site/eksempel.html", buys_only)])
    if not pro_missing or not pro_missing_da or not pro_buried:
        print("SELFTEST FEJLER: pro_features-scenarierne fanger ikke den manglende funktion")
        return 1
    if pro_complete:
        print("SELFTEST FEJLER: en side der navngiver alle Pro-funktioner fejler alligevel — "
              "kravet er for stramt: " + "; ".join(pro_complete))
        return 1
    if pro_undeclared:
        print("SELFTEST FEJLER: et produkt uden pro_features i katalogen fejler alligevel — "
              "porten dømmer produkter den ikke kan se: " + "; ".join(pro_undeclared))
        return 1
    if "cleanup-rules" not in " ".join(pro_missing):
        print("SELFTEST FEJLER: pro_features-scenariet rammer den manglende funktion, "
              f"ikke den anden fejl: {pro_missing}")
        return 1
    # ── free_features: Pro-kortet må ikke sælge noget der er gratis ───────
    #
    # Beviset er de rigtige publicerede sætninger fra opgave 69, som lå i
    # Pro-kortet i produktion: den danske "Pro-versionen tilføjer sammenligning,
    # batch og historik" og den engelske "History tracking"-bullet. De læses
    # fra de rigtige filer, og kun sætningen muteres — en fejlform der kun
    # findes i en streng porten selv har fundet, er ingen fejlform.
    da_real = (ROOT / "site/da/page-profile.html").read_text(encoding="utf-8")
    en_real = (ROOT / "site/page-profile.html").read_text(encoding="utf-8")
    old_da_pro = ("<li>Gratis kerne — web-tjekket er altid gratis. Pro-versionen "
                  "tilføjer sammenligning, batch og historik.</li>")
    old_en_pro = "<li>History tracking across runs</li>"
    if old_da_pro in da_real or old_en_pro in en_real:
        print("SELFTEST FEJLER: de publicerede fejlformer fra opgave 69 står stadig i "
              "site/da/page-profile.html og site/page-profile.html")
        return 1
    da_sold_free = da_real.replace(
        "<li>Sammenligning — diff to URLs side om side",
        f"{old_da_pro}\n            <li>Sammenligning — diff to URLs side om side")
    en_sold_free = en_real.replace(
        "<li>Comparison mode — diff two URLs side by side",
        f"{old_en_pro}\n            <li>Comparison mode — diff two URLs side by side")
    da_in_free_card = da_real.replace(
        "<li>Historik — hver kørsel",
        f"{old_da_pro}\n            <li>Historik — hver kørsel")
    if old_da_pro not in da_sold_free or old_en_pro not in en_sold_free:
        print("SELFTEST FEJLER: kun påstanden muteres alene, men insertionsstedet "
              "findes ikke i de rigtige filer")
        return 1
    da_pairs = [("site/da/page-profile.html", da_real), ("site/page-profile.html", en_real)]
    sold_both = [x for x in check_free_features(
        good,
        [("site/da/page-profile.html", da_sold_free), ("site/page-profile.html", en_sold_free)],
    ) if "page-profile" in x]

    # Negativ kontrol 1: den samme sætning i GRATIS-kortet er ikke en fejl —
    # det er der funktionen hører hjemme, ellers ville porten forbyde at
    # fortælle kunderne hvad de får gratis.
    free_card_ok = [x for x in check_free_features(
        good,
        [("site/da/page-profile.html", da_in_free_card), ("site/page-profile.html", en_real)],
    ) if "page-profile" in x]
    # Negativ kontrol 2: dagens sider er grønne. Uden denne ville en port der
    # altid fejler se ud som om den virkede.
    untouched = [x for x in check_free_features(good, da_pairs) if "page-profile" in x]
    # En post uden `where` kan ikke dømmes: den siger ikke hvilken kode der
    # giver funktionen gratis, så den er en måde at slå porten fra på.
    no_where = {**good, "products": {**good["products"], "page-profile-pro": {
        **good["products"]["page-profile-pro"],
        "free_features": [{k: v for k, v in entry.items() if k != "where"}
                          for entry in good["products"]["page-profile-pro"]["free_features"]]}}}
    missing_where = check_free_features(no_where, da_pairs)
    if not sold_both:
        print("SELFTEST FEJLER: Pro-kortet der sælger historik fejler ikke — det er "
              "præcis den fejl opgave 69 rettede, og porten skal fange den igen")
        return 1
    if "historik" not in " ".join(sold_both) or "history tracking" not in " ".join(sold_both):
        print("SELFTEST FEJLER: free_features-scenarierne rammer ikke den gratis "
              f"funktion i begge sprog: {sold_both}")
        return 1
    if free_card_ok:
        print("SELFTEST FEJLER: en funktion der står i GRATIS-kortet fejler alligevel — "
              "kravet er for stramt: " + "; ".join(free_card_ok))
        return 1
    if untouched:
        print("SELFTEST FEJLER: de uændrede købssider fejler — porten kan ikke "
              f"finde fejlen: {untouched}")
        return 1
    free_features = good["products"]["page-profile-pro"]["free_features"]
    # Én linje pr. post, og kun én gruppe pr. produkt. Før denne iteration var
    # der én post, så "1" dækkede begge tal; med fem poster er det antallet af
    # poster der dømmes, og antallet af *sider* der ikke må blande sig ind —
    # produktet har to købssider, så en port der meldte pr. tilbud ville give 10.
    if (len(missing_where) != len(free_features)
            or any("where" not in x for x in missing_where)
            or len({x.split(":")[0] for x in missing_where}) != 1):
        print("SELFTEST FEJLER: en free_features-post uden `where` meldes ikke "
              f"én gang pr. post og kun én gang pr. produkt: {missing_where}")
        return 1

    # Hver erklæret gratis-funktion skal kunne *bide* — den rigtige Gratis-
    # sætning flyttet ind i Pro-kortet på den rigtige købsside er den fejlform
    # porten er skrevet for. Uden denne blok passede fire nye poster på at de
    # aldrig blev læst, fordi porten er grøn på en side der er i orden.
    def into_pro_card(real: str, li: str) -> str:
        start = real.index('class="tier-card pro"')
        at = real.index("<ul>", start) + len("<ul>")
        return real[:at] + li + real[at:]

    silent: list[str] = []
    for feature in free_features:
        for relative, real in (("site/da/page-profile.html", da_real),
                               ("site/page-profile.html", en_real)):
            labels = (feature.get("labels") or {}).get(page_lang(relative, real)) or []
            if not labels:
                continue
            moved = into_pro_card(real, f"<li>{labels[0]}</li>")
            if f"<li>{labels[0]}</li>" not in moved:
                silent.append(f"{feature.get('id')} på {relative}: Pro-kortet har ingen liste")
                continue
            pages = [(p, moved if p == relative else t) for p, t in da_pairs]
            if not [x for x in check_free_features(good, pages)
                    if f"'{feature.get('id')}'" in x]:
                silent.append(f"{feature.get('id')} på {relative}")
    if silent:
        print("SELFTEST FEJLER: disse gratis-funktioner kan flyttes ind i Pro-kortet "
              "uden at porten siger noget: " + "; ".join(silent))
        return 1

    # Den anden retning, som var målt i mangel: den erklærede gratis-funktion
    # skal *stå* i Gratis-kortet. Beviset er den rigtige sætning i de rigtige
    # filer, kun slettet — med kravet "må ikke stå i Pro-kortet" alene var
    # porten grøn på præcis denne mutation, så rettelsen af en gratis-funktion
    # der lå i Pro-kortet kunne have været "fjern påstanden" i stedet for
    # "sig hvor den hører hjemme". Samme fem poster, samme to sprog.
    LI_RE = re.compile(r"[ \t]*<li>(?:(?!</li>).)*?</li>\n", re.S)

    def out_of_free_card(real: str, label: str) -> str:
        """Slet den Gratis-sætning der nævner `label`, og kun den.

        Slicet er Gratis-kortets egen blok, ikke hele siden: samme ord står
        flere steder (navigation, sammenligningstabel), så en mutation der
        ramte en anden `<li>` ville slette det forkerte og lade porten grøn
        af en grund den ikke måtte være grøn af.
        """
        trimmed = real
        start = real.index('class="tier-card"')
        end = real.index('class="tier-card pro"', start)
        for match in LI_RE.finditer(real[start:end]):
            if label.casefold() in match.group(0).casefold():
                at = start + match.start()
                trimmed = real[:at] + real[start + match.end():]
                break
        # Gratis-siden er i dag to flader: kortet *og* den gratis spalte i
        # sammenligningstabellen. Mutationen skal fjerne sætningen fra begge,
        # ellers er den ikke en mutation af "kunden kan se at den er gratis"
        # men kun af "kortet er væk" — og porten ville være grøn af en grund
        # den ikke måtte være grøn af. Målt på `site/page-profile.html`: den
        # engelske historik-sætning findes i tabellen, så kun et kort-klip
        # slap alle otte mutationer igennem.
        for cell in re.finditer(r"<td[^>]*>((?:(?!</td>).)*?)</td>", trimmed, re.S):
            body = cell.group(1)
            if label.casefold() not in body.casefold():
                continue
            if PAID_LABEL.search(body) or not FREE_LABEL.search(body):
                continue  # Den betalte spalte er en anden fejlform.
            trimmed = (trimmed[:cell.start(1)] + "—" + trimmed[cell.end(1):])
        return trimmed

    unsaid: list[str] = []
    for feature in free_features:
        for relative, real in (("site/da/page-profile.html", da_real),
                               ("site/page-profile.html", en_real)):
            labels = (feature.get("labels") or {}).get(page_lang(relative, real)) or []
            if not labels:
                continue
            trimmed = out_of_free_card(real, labels[0])
            if trimmed == real:
                unsaid.append(f"{feature.get('id')} på {relative}: sætningen "
                              f"{labels[0]!r} findes ikke i Gratis-kortets liste")
                continue
            pages = [(p, trimmed if p == relative else t) for p, t in da_pairs]
            if not [x for x in check_free_features(good, pages)
                    if f"'{feature.get('id')}'" in x and "gratis side af siden" in x]:
                unsaid.append(f"{feature.get('id')} på {relative}")
    if unsaid:
        print("SELFTEST FEJLER: disse gratis-funktioner kan forsvinde fra Gratis-kortet "
              "uden at porten siger noget: " + "; ".join(unsaid))
        return 1

    # Ét sprog, ét krav: to sætninger for samme funktion er en katalogfejl, for
    # så kan porten ikke vide hvilken der skal stå i Gratis-kortet. Den må
    # meldes én gang pr. produkt — den gælder alle sider — og den må ikke
    # afføde et krav pr. sætning oveni.
    twin = {**good["products"]["page-profile-pro"]["free_features"][0],
            "labels": {"en": ["Redirect chain trace", "Redirect trail"],
                       "da": ["Redirect-kæde"]}}
    two_labels = {**good, "products": {**good["products"], "page-profile-pro": {
        **good["products"]["page-profile-pro"],
        "free_features": [twin] + good["products"]["page-profile-pro"]["free_features"][1:]}}}
    twin_problems = check_free_features(two_labels, da_pairs)
    twin_lines = [x for x in twin_problems if "2 en-labels" in x]
    if (len(twin_lines) != 1
            or any("gratis side af siden nævner ikke" in x for x in twin_problems)
            or len({x.split(":")[0] for x in twin_problems}) != 1):
        print("SELFTEST FEJLER: to labels for én funktion meldes ikke én gang pr. "
              f"produkt uden at dømme dem hver især: {twin_problems}")
        return 1
    # ── de otte flader: en erklæret gratis-funktion skal kunne bide på dem ──
    #
    # `paid_contexts` læser tre slags flader (målt i dens egen docstring):
    # Pro-kortet, den betalte spalte i en tabel, og brødteksten. Selftestens
    # øvrige mutationer læser alle **én** af dem — Gratis-kortet på de to
    # page-profile-sider — så de otte købssider der *kun* har en sætning
    # eller en tabel var ubevidnede. En gratis-funktion der flyttede til
    # "Pro adds history tracking" på `site/deskuptime/index.html` ville være
    # gået ubemærket.
    #
    # Derfor otte mutationer, én pr. flade, og hver kræver **præcis én** rød
    # der nævner netop den side. Mutationen er den rigtige fejlform: siden siger
    # ærligt at funktionen er gratis (det sætter testen op, som en kunde
    # ellers ikke ville se nogen steder), og mutationen sætter den *samme*
    # sætning ind i den betalte kontekst. Ét katalogsignal, ét krav, én fejl.
    #
    # Kun én `free_features`-post i katalogkopien, ikke alle fem: ellers ville
    # hver mutation også kræve de fire andres labels på alle otte sider, og
    # det er ikke den fejlform der testes her.
    prose_surfaces = [
        "site/clean-copy.html",
        "site/da/clean-copy.html",
        "site/activate/index.html",
        "site/da/activate/index.html",
        "site/clean-copy-tool.html",
        "site/deskuptime/index.html",
        "site/da/deskuptime/index.html",
        "site/blog/desktop-website-monitor-cli.html",
    ]
    # Sætningen skal være naturlig i begge sprog, og den skal ramme præcis det
    # porten dømmer: et gratis-afsnit med *gratis* og uden noget betalt ord, og
    # et betalt afsnit med *Pro* og uden noget gratis ord. `<strong>` før
    # sætningen er ikke kosmetik — den er der, fordi isolationen nedenfor
    # spørger om porten stadig ser den tekst der står *efter* et inline-element.
    free_sentence = {
        "en": "<p>{} is free for everyone.</p>",
        "da": "<p>{} er gratis for alle.</p>",
    }
    paid_sentence = {
        "en": "<p><strong>Pro</strong> also adds {} for every run.</p>",
        "da": "<p><strong>Pro</strong> tilføjer også {} for hver kørsel.</p>",
    }
    feature = good["products"]["page-profile-pro"]["free_features"][0]
    feature_id = str(feature.get("id"))
    unproven: list[str] = []
    for relative in prose_surfaces:
        real = (ROOT / relative).read_text(encoding="utf-8")
        lang = page_lang(relative, real)
        label = (feature.get("labels") or {}).get(lang) or []
        if not label:
            unproven.append(f"{relative}: {feature_id} har ingen {lang}-label at sætte ind")
            continue
        sentence = str(label[0])
        spoken = sentence[:1].upper() + sentence[1:]
        honest = real.replace("</main>", free_sentence[lang].format(spoken) + "\n</main>", 1)
        mutated = honest.replace("</main>", paid_sentence[lang].format(sentence) + "\n</main>", 1)
        if honest == real or mutated == honest:
            unproven.append(f"{relative}: sætningen blev ikke indsat — mutationen er en "
                            "stum kontrol, fordi den ikke rammer siden")
            continue
        one = {**good, "products": {**good["products"], "page-profile-pro": {
            **good["products"]["page-profile-pro"], "free_features": [feature]}},
            "offers": [{"path": relative, "product": "page-profile-pro"}]}
        # Negativ kontrol: den ærlige side — gratis-fladen siger den, den
        # betalte kontekst gør ikke — skal være grøn. Ellers ville mutationen
        # ramme en fejl der allerede var der.
        clean = check_free_features(one, [(relative, honest)])
        if clean:
            unproven.append(f"{relative}: den ærlige side fejler allerede: " + "; ".join(clean))
            continue
        sold = check_free_features(one, [(relative, mutated)])
        if len(sold) != 1 or relative not in sold[0] or f"'{feature_id}'" not in sold[0]:
            unproven.append(f"{relative}: den betalte kontekst giver "
                            f"{len(sold)} fejl i stedet for én om {feature_id}: " + "; ".join(sold))
    if unproven:
        print("SELFTEST FEJLER: en gratis-funktion kan flytte ind i den betalte kontekst "
              "på disse sider uden at porten siger præcis én ting om siden: "
              + "; ".join(unproven))
        return 1

    # Isolationen fra opgave 74, skrevet permanent. Inden parser-rettelsen lukkede
    # enhver slutning hele `<p>`-blokken, så alt der stod efter det første
    # inline-element forsvandt, og porten var grøn på otte sider den kun læste
    # halvdelen af. Det er skrevet som en måling i loggen to gange; her er det
    # en permanent blok, fordi "porten læser hele siden" er et krav der skal
    # kunne fejle. Vagten gøres blind — ethvert tag lukker blokke — og de otte
    # mutationer skal da **holde op med at fejle**, mens de rigtige sider
    # stadig er grønne. Blinde man vagten og mutationerne stadig fejler, er
    # de grønne af en anden grund end den, porten tror.
    class EveryTagClosesBlocks(frozenset):
        def __contains__(self, item: object) -> bool:
            return True

    class BlindedTierBlocks(TierBlocks):
        """`handle_endtag`s betingelse er blind, som den var før opgave 74.

        **Kun** slutningen blændes. `handle_starttag` skal stadig åbne blokke
        kun for de rigtige blok-tags, ellers genskaber vi en anden fejl: så
        åbner hvert inline-element også en blok, og mutationen overlever af
        den grund. Derfor blændes vagten kun for varigheden af ét
        `handle_endtag` — præcis den kode der blev rettet.
        """

        def handle_endtag(self, tag: str) -> None:
            self.BLOCK_TAGS = EveryTagClosesBlocks()
            try:
                super().handle_endtag(tag)
            finally:
                del self.BLOCK_TAGS

    def with_blinded_parser(work):
        """Kør `work` med den blinde parser i stedet for den rigtige."""
        saved = globals()["TierBlocks"]
        globals()["TierBlocks"] = BlindedTierBlocks
        try:
            return work()
        finally:
            globals()["TierBlocks"] = saved

    def mutation_for(relative: str) -> tuple[dict, list[tuple[str, str]]]:
        real = (ROOT / relative).read_text(encoding="utf-8")
        lang = page_lang(relative, real)
        sentence = str(((feature.get("labels") or {}).get(lang) or [""])[0])
        spoken = sentence[:1].upper() + sentence[1:]
        honest = real.replace("</main>", free_sentence[lang].format(spoken) + "\n</main>", 1)
        mutated = honest.replace("</main>", paid_sentence[lang].format(sentence) + "\n</main>", 1)
        one = {**good, "products": {**good["products"], "page-profile-pro": {
            **good["products"]["page-profile-pro"], "free_features": [feature]}},
            "offers": [{"path": relative, "product": "page-profile-pro"}]}
        return one, [(relative, mutated)]

    def sold_by_blind_parser(relative: str) -> list[str]:
        one, pages = mutation_for(relative)
        return [x for x in with_blinded_parser(
                    lambda: check_free_features(one, pages))
                if f"'{feature_id}'" in x and "Pro-kortet sælger" in x]

    blind = [relative for relative in prose_surfaces if sold_by_blind_parser(relative)]
    # Blindingen skal også kunne *måles*, ellers er den otte mutationers
    # grådige pause et tegn på en mutation der ingenting ændrede. Den rigtige
    # parser læser mere tekst end den blinde på de rigtige filer — målt, ikke
    # formodet: `site/clean-copy.html` læser 289/113 med den rigtige
    # (opgave 74, Fund 2) og taber alt efter første inline-element med den
    # blinde.
    real_text = (ROOT / "site/clean-copy.html").read_text(encoding="utf-8")
    read_right = paid_contexts(real_text)
    read_blind = with_blinded_parser(lambda: paid_contexts(real_text))
    if blind or not all(len(a) >= len(b) for a, b in zip(read_right[:2], read_blind[:2])):
        print("SELFTEST FEJLER: porten læser ikke hele siden. Med den blinde vagt i "
              "handle_endtag skulle de otte mutationer holde op med at fejle, og den "
              "blinde parser læse mindre end den rigtige — "
              f"fejlende mutationer: {blind}; læst med/uden blindning: {read_right} "
              f"mod {read_blind}")
        return 1

    # ── kryds-tabeller: rækkens navn *er* påstanden ───────────────────────
    #
    # En `✓`-tabel skriver funktionens navn i rækkens første celle og
    # svarer "✓"/"—" i spalterne, så de betalte celler alene forteller intet
    # om hvad det er. Målt før rettelsen: på `page-profile` gav
    # `Compare two URLs side by side | — | yes` en betalt spalte uden navnet,
    # så en erklæret gratis-funktion der lå i den række var usynlig for den
    # port der skal finde den. Derfor følger rækkens navn den spalte der
    # svarer ja — og ingen af dem, når begge svarer ja.
    #
    # Beviset går tre veje, fordi det er den *modsatte* retning rettelsen
    # styrker: (a) en erklæret gratis-funktion i rækkens navn giver præcis
    # én rød, (b) samme side med den betalte spalte sat til "nej" giver nul,
    # fordi funktionen så ikke længere sælges, og (c) en port der har
    # glemt reglen giver nul på (a) — ellers er der ingen forskel at bevise,
    # og en mutation der ikke biter er ingen bevis.
    real_catalog = load_catalog(CATALOG)
    tick_relative = "site/page-profile.html"
    tick_id = "compare two urls side by side"
    tick_key = "page-profile-pro"
    tick_text = (ROOT / tick_relative).read_text(encoding="utf-8")
    tick_lang = page_lang(tick_relative, tick_text)
    tick_entry = {"id": tick_id, "where": "selftest: mutation", "labels": {tick_lang: [tick_id]}}
    tick_one = {
        **real_catalog,
        "products": {tick_key: {**real_catalog["products"][tick_key],
                                "free_features": [tick_entry]}},
        "offers": [{"path": tick_relative, "product": tick_key}],
    }
    def tick_sold(blinded: bool) -> list[str]:
        """Gratis-funktionen i rækkens navn, dømt af porten med og uden reglen."""
        if not blinded:
            return check_free_features(tick_one, [(tick_relative, tick_text)])
        # Isolationen gør præcis den nye kode blind: `YES_CELL` læses kun
        # af rækkens navn, så en regex der aldrig rammer slår hele reglen
        # fra — og intet andet.
        saved = globals()["YES_CELL"]
        globals()["YES_CELL"] = re.compile(r"(?!x)x")
        try:
            return check_free_features(tick_one, [(tick_relative, tick_text)])
        finally:
            globals()["YES_CELL"] = saved

    # Kun den første retning tælles: "Pro-kortet sælger". Den anden — den
    # gratis side skal *nævne* funktionen — er rød for ethvert syntetisk
    # katalogsignal, fordi siderne ikke er skrevet til den, og den siger
    # intet om rækkenavnet. Beviset er derfor parret (1, 0): med reglen er
    # rækkens navn solgt, og uden reglen er det ikke. Den tredje arm —
    # "sæt den betalte spalte til nej og se det forsvinde" — er bevidst
    # ikke skrevet: målingen viser at "Compare two URLs side by side"
    # også står i brødteksten, så en celleflip alene fjerner navnet fra
    # to steder og beviser intet om reglen.
    def tick_sold_as_paid(problems: list[str]) -> list[str]:
        return [x for x in problems if "Pro-kortet sælger" in x and tick_id in x]

    if "Compare two URLs side by side" not in tick_text:
        print(f"SELFTEST FEJLER: mutationen for {tick_id!r} passer ikke længere på "
              f"{tick_relative} — rækken er flyttet eller slettet")
        return 1

    sold = tick_sold_as_paid(tick_sold(False))
    blind = tick_sold_as_paid(tick_sold(True))
    if len(sold) != 1 or blind:
        print(f"SELFTEST FEJLER: kryds-tabellen i {tick_relative} sælger rækkens navn "
              f"{len(sold)} gange (forventet 1) og {len(blind)} gange når rækkens navn "
              f"ikke følger spalten (forventet 0). En kryds-tabel skal give hver række en "
              f"placering, ellers sælger porten en funktion på en side der ikke læser den "
              f"som betalt")
        return 1

    # ── pro_not_built: et løfte koden ikke holder ─────────────────────────
    #
    # Beviset er de rigtige publicerede sætninger fra opgave 49, hentet fra
    # git og skrevet tilbage i de rigtige filer. En fejlform der kun findes
    # i en streng porten selv har fundet, er ingen fejlform — derfor læses
    # hver fil fra `site/`, og påstanden der testes muteres alene.
    superseded_promises = {
        "site/deskuptime/index.html": (
            "Email and webhook alerts",
            "Webhook alerts from the CLI",
        ),
        "site/deskuptime/index.html#prose": (
            "adds email and webhook alerts",
            "adds webhook alerts and a client-ready report",
        ),
        "site/da/deskuptime/index.html": (
            "E-mail- og webhook-alarmer",
            "Webhook-alarmer fra CLI'en",
        ),
        "site/da/deskuptime/index.html#prose": (
            "tilføjer e-mail- og webhook-alarmer",
            "tilføjer webhook-alarmer og en kunderapport",
        ),
        "site/blog/desktop-website-monitor-cli.html": (
            "Email &amp; webhook alerts",
            "Webhook alerts (CLI)",
        ),
    }
    promise_found: list[str] = []
    promise_offers = [{"path": path.split("#")[0], "product": key}
                      for key, path in (("deskuptime-pro", "site/deskuptime/index.html"),
                                        ("deskuptime-pro", "site/blog/desktop-website-monitor-cli.html"))]
    promise_catalog = {**good, "offers": promise_offers}
    for relative, (old, new) in superseded_promises.items():
        base = relative.split("#")[0]
        real = (ROOT / base).read_text(encoding="utf-8")
        if new not in real:
            raise AssertionError(f"{base}: den rettede tekst mangler i den rigtige fil: {new[:60]!r}")
        if old in real:
            raise AssertionError(f"{base}: den udgående løgned står stadig i den rigtige fil: {old[:60]!r}")
        path = base if base.endswith(".html") else base
        product = "deskuptime-pro"
        # Den danske side er sin egen købsside, så den får sin egen katalog.
        lang_catalog = (promise_catalog if "/da/" not in path
                        else {**promise_catalog, "offers": [{"path": path, "product": product}]})
        found = check_pro_not_built(lang_catalog, [(path, real.replace(new, old, 1))])
        if not found:
            raise AssertionError(
                f"{base}: pro_not_built fangt ikke den publicerede løgned {old[:60]!r} — "
                "reglen er grøn for præcis det den skal fange")
        promise_found.extend(found)
    # Det samme på den anden slags løfte: EUComply Pro lovede fire funktioner,
    # ingen af dem findes i koden.
    eucomply_real = (ROOT / "site/compliance-report.html").read_text(encoding="utf-8")
    eucomply_old = ("Continuous compliance monitoring for one website",
                    "Client-ready branded PDF reports",
                    "Priority support (email within 24h)")
    for old in eucomply_old:
        if old in eucomply_real:
            raise AssertionError(
                f"site/compliance-report.html: den udgående løgned står stadig i den "
                f"rigtige fil: {old[:60]!r}")
    for anchor in ("PDF download of the full report", "Licence covers 1 machine",
                   "24 automated checks, including 16 accessibility rules"):
        if anchor not in eucomply_real:
            raise AssertionError(
                f"site/compliance-report.html: mutationsankeret mangler i den rigtige "
                f"fil: {anchor[:60]!r}")
    eucomply_catalog = {**good, "offers": [{"path": "site/compliance-report.html",
                                            "product": "eucomply-pro"}]}
    eucomply_back = eucomply_real.replace(
        "PDF download of the full report", "Continuous compliance monitoring for one website", 1)
    eucomply_back = eucomply_back.replace(
        "Licence covers 1 machine", "Client-ready branded PDF reports", 1)
    eucomply_back = eucomply_back.replace(
        "24 automated checks, including 16 accessibility rules", "Priority support (email within 24h)", 1)
    eucomply_found = check_pro_not_built(eucomply_catalog, [("site/compliance-report.html", eucomply_back)])
    if not eucomply_found or "compliance monitoring" not in " ".join(eucomply_found):
        raise AssertionError(
            "site/compliance-report.html: pro_not_built fangt ikke de publicerede løfter "
            f"på EUComply Pro: {eucomply_found}")
    # 7: hvor analysen sker. Fejlformen er målt på den rigtige side fra før
    # opgave 58, så selftesten bruger netop den sætning.
    stale_claim = (
        f'<html><body><p>Public URLs only. The page is fetched server-side, '
        f'analysed in your browser, and discarded.</p>'
        f'<script>fetch("/api/report")</script></body></html>')
    stale_found = check_analysis_location([("site/compliance-report.html", stale_claim)])
    # Samme påstand uden server-kald: det er `/scan`, og der er den SAND.
    free_scanner = (
        f'<html><body><p>The page is fetched server-side through our proxy, '
        f'analysed in your browser, and immediately discarded.</p>'
        f'<script>fetch("/scan-proxy?url=")</script></body></html>')
    free_should_pass = check_analysis_location([("site/scan.html", free_scanner)])
    # Print-dialogen er sandt siden kalder window.print(): må ikke fejle.
    print_dialog = (
        f'<html><body><p>You save the PDF yourself from the browser print dialog.</p>'
        f'<script>fetch("/api/report")</script></body></html>')
    print_should_pass = check_analysis_location([("site/compliance-report.html", print_dialog)])
    # Dansk: samme krav, dansk sætning.
    stale_da = (
        f'<html><body><p>Siden hentes og analyseres i din browser, og kasseres bagefter.</p>'
        f'<script>fetch("/api/report")</script></body></html>')
    stale_da_found = check_analysis_location([("site/da/compliance-report.html", stale_da)])
    # Selv en synlig fejlsag må kun fange, fordi den *synlige tekst* er fundet:
    # samme sætning i en kommentar eller i en JSON-LD-streng er ikke en
    # påstand kunden læser.
    hidden_only = (
        f'<html><body><p>Public URLs only.</p>'
        f'<script>/* analysed in your browser */ fetch("/api/report")</script></body></html>')
    hidden_should_pass = check_analysis_location([("site/compliance-report.html", hidden_only)])
    # Og på den flade ingen HTML-port så: /checkout-noten i workeren.
    old_note = ("One-time license: desktop tray app, email & webhook alerts, unlimited URLs. "
                "Up to 3 machines, all v1.x updates.")
    new_note = ("One-time license: desktop tray app, unlimited sites, webhook alerts and a "
                "client-ready report. Up to 3 machines, all v1.x updates.")
    worker_text = WORKER.read_text(encoding="utf-8")
    if new_note not in worker_text or old_note in worker_text:
        raise AssertionError("site/_worker.js: /checkout-noten er ikke i den forventede stand")
    checkout_found = check_checkout_notes(good, worker_text.replace(new_note, old_note, 1))
    if not checkout_found:
        raise AssertionError(
            "site/_worker.js: check_checkout_notes fangt ikke den publicerede løgned i "
            "/checkout-noten")
    # Negativ kontrol: de rettede flader skal være grønne. Uden den kunne
    # reglen være for stram til at sælge nogen somhelst.
    honest_pages = [("site/deskuptime/index.html",
                     (ROOT / "site/deskuptime/index.html").read_text(encoding="utf-8")),
                    ("site/da/deskuptime/index.html",
                     (ROOT / "site/da/deskuptime/index.html").read_text(encoding="utf-8")),
                    ("site/blog/desktop-website-monitor-cli.html",
                     (ROOT / "site/blog/desktop-website-monitor-cli.html").read_text(encoding="utf-8")),
                    ("site/compliance-report.html", eucomply_real)]
    honest_offers = [{"path": path, "product": ("eucomply-pro" if "compliance-report" in path
                                                 else "deskuptime-pro")}
                     for path, _ in honest_pages]
    honest = check_pro_not_built({**good, "offers": honest_offers}, honest_pages)
    if honest:
        raise AssertionError(f"SELFTEST FEJLER (falsk alarm): de rettede købssider fejler: {honest[0]}")
    checkout_ok = check_checkout_notes(good, worker_text)
    if checkout_ok:
        raise AssertionError(
            f"SELFTEST FEJLER (falsk alarm): den rettede /checkout-note fejler: {checkout_ok[0]}")
    # En post uden `where` er ikke et løfte, koden modsiger — den er en måde
    # at slå fejlen fra på. Den skal derfor selv meldes.
    silent = {**good, "products": {**good["products"], "deskuptime-pro": {
        **good["products"]["deskuptime-pro"],
        "pro_not_built": [{"id": "email-alerts", "labels": {"en": ["email alerts"], "da": []}}]}}}
    silent_found = check_pro_not_built(
        {**silent, "offers": [{"path": "site/deskuptime/index.html", "product": "deskuptime-pro"}]},
        [("site/deskuptime/index.html", "<html><body><p>Email alerts</p></body></html>")])
    if not silent_found or "where" not in " ".join(silent_found):
        raise AssertionError(
            "SELFTEST FEJLER: en pro_not_best-post uden `where` bliver troet — "
            f"listen kan så slås fra på: {silent_found}")
    # Og et produkt uden `pro_not_built` gates ikke, samme hensigt som
    # `pro_features`: porten dømmer ikke produkter den ikke kan se.
    undeclared = {**good, "products": {
        **good["products"],
        "deskuptime-pro": {k: v for k, v in good["products"]["deskuptime-pro"].items()
                           if k != "pro_not_built"}}}
    undeclared_found = check_pro_not_built(
        {**undeclared, "offers": [{"path": "site/deskuptime/index.html", "product": "deskuptime-pro"}]},
        [("site/deskuptime/index.html",
          "<html><body><p>Email and webhook alerts, the works.</p></body></html>")])
    if undeclared_found:
        raise AssertionError(
            "SELFTEST FEJLER: et produkt uden pro_not_built fejler alligevel — "
            f"porten dømmer produkter den ikke kan se: {undeclared_found}")
    # Tomme celler hører nu til `check_comparisons`, som læser alle sider og
    # ikke kun katalogens købssider. Scenariet beholder sin købsknap, så det
    # isolerer den ene regel: her skal kun den tomme celle fanges.
    hollow_table = check_comparisons(good, [("site/eksempel.html", empty_table)])
    # Negativ kontrol: siden siger gratis-udgaven, og en donation skal ikke
    # fejle på en regel om gratis-udgaven — den har ikke en.
    should_also_pass = check_free_tier(free_tier_only, [("site/eksempel.html", says_free)])
    donation_only = {**good, "offers": [
        offer for offer in good["offers"] if offer["product"] == "support-mahope-oss"]}
    donation_no_free = check_free_tier(donation_only, [("site/support.html", donation)])
    # Uden denne kontrol er de tre scenarier ovenfor stumme: en syntese der
    # ikke rammer købssiden, ville stå som fanget uden at prøve noget, præcis
    # som fejlen i opgave 30.
    if not only_offer or only_offer == good["offers"]:
        print("SELFTEST FEJLER: gratis-udgave-scenarierne muterer ingen købsside — de er stumme")
        return 1
    if FREE_TIER_PHRASES.search("The free version is the complete tool, not a trial.") is None:
        print("SELFTEST FEJLER: frasen i det positive scenarie matcher ikke portens egen mønster")
        return 1

    # 7: en sammenligningstabel på en side der ikke sælger. Opgave 32 blev
    # meldt "kræver Mads", fordi porten kun læste katalogens købssider — så
    # en helt ukendt "EAA Scanner Pro — $19/år" kunne stå på en publiceret
    # side. Scenarierne er syntetiske, så selftesten ikke skriver fejlen ind i
    # de rigtige sider.
    def table(price: str, free_cell: str = "yes", pro_cell: str = "yes", link: str = "") -> str:
        return (f'<html><body><table><tr><th>Feature</th><th>Free</th>'
                f'<th>Pro (not released)</th></tr>'
                f'<tr><td>Batch scanning</td><td>{free_cell}</td><td>{pro_cell}</td></tr>'
                f'<tr><td>Price</td><td>Free (MIT)</td><td>{price}</td></tr></table>'
                f'{link}</body></html>')

    unbuyable_symbol = check_comparisons(good, [("site/eksempel.html", table("$19/year"))])
    unbuyable_words = check_comparisons(good, [("site/eksempel.html", table("19 USD per year"))])
    hollow_unsold = check_comparisons(
        good, [("site/eksempel.html", table("Not for sale yet", pro_cell=""))])
    # Negativ kontroller: det samme med en købsknap, og det samme uden pris.
    buyable = check_comparisons(
        good, [("site/eksempel.html", table("$19/year", link=f'<a href="{clean_copy_link}">Buy</a>'))])
    priceless = check_comparisons(good, [("site/eksempel.html", table("Not for sale yet"))])

    # 7: en *klient* må ikke sende brugeren ud for at købe noget uden et
    # købssted. Scenarierne er rigtige filer i en midlertidig mappe, fordi
    # porten læser filer — ikke strenge.
    with tempfile.TemporaryDirectory() as tmp:
        def client(name: str, body: str) -> Path:
            path = Path(tmp) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
            return path

        dead_buy = client("desktop/index.html", (
            '<p class="pro-note">Purchase a license at '
            '<a href="#" id="buyLicenseLink">hermes-passiv.pages.dev/clean-copy</a></p>\n'))
        danish_buy = client("desktop/om.js", (
            "// K\u00f8b en licens p\u00e5 https://example.invalid/licens\n"))
        # Uden en anden filnavn skriver denne linje sin egen tekst oven i
        # `dead_buy`, og scenarioen ville stå som fanget uden at have
        # prøvet noget: præcis det porten er skrevet til at fange.
        honest = client("desktop/honest.html", (
            '<p>There is no Pro licence for the EAA scanner today, and no price to pay for '
            'one \u2014 so there is nothing to buy yet.</p>\n'))
        with_link = client("page-profile/readme.md", (
            f'K\u00f8b licensen her: {clean_copy_link}\n'))
        dead_client_buy = check_client_purchase_targets(good, [dead_buy, danish_buy])
        honest_client = check_client_purchase_targets(good, [honest])
        linked_client = check_client_purchase_targets(good, [with_link])
    # Uden denne kontrol er `unbuyable_words` en stum scene: `$`-mønsteret
    # ville have fundet nul priser i "19 USD per year", så scenariet kunne
    # stå som fanget uden at have prøvet det valutaordene er der for.
    if PRICE_TOKEN.search("19 USD per year") is not None:
        print("SELFTEST FEJLER: valutaord-scenariet kan ikke skelnes fra PRICE_TOKEN — "
              "reglen om valutaord er uden betydning")
        return 1
    if CURRENCY_AMOUNT.search("19 USD per year") is None:
        print("SELFTEST FEJLER: CURRENCY_AMOUNT finder ikke sit eget positive eksempel")
        return 1

    # 8: en pris på en side, hvor den ikke kan betales. Opgave 41 rettede 15
    # filer uden port. Scenarierne er syntetiske, så selftesten ikke skriver
    # fejlen ind i de rigtige sider — beviset på de rigtige gamle filer står i
    # opgave 42 i planen.
    def page(body: str, link: str = "") -> str:
        return f"<html><body>{body}{link}</body></html>"

    jsonld = ('<script type="application/ld+json">{"@type":"WebApplication",'
              '"name":"E-book","offers":{"@type":"Offer","price":"%s",'
              '"availability":"%s"}}</script>')
    preorder_price = check_unbuyable_prices(
        good, [("site/eksempel.html", page(jsonld % ("9.99", "https://schema.org/PreOrder")))])
    label_price = check_unbuyable_prices(
        good, [("site/eksempel.html", page('<div class="price">$9.99</div>'))])
    promised_edition = check_unbuyable_prices(
        good, [("site/eksempel.html", page("<p>Paid edition: $9.99 (coming)</p>"))])
    foreign_venue = check_unbuyable_prices(
        good, [("site/eksempel.html",
                page('<p>Get the NIS2 e-book ($9.99 on Amazon).</p>'))])
    stale_structured = check_unbuyable_prices(
        good, [("site/eksempel.html", page(jsonld % ("29", ""), f'<a href="{report_kit}">Buy</a>'))])

    # ── Negative kontroller. Uden dem er hver regel ovenfor teater i sit
    # eget tilfælde — præcis fejlformen opgave 38 fund 4.
    #
    # (a) Den ærlige sætning fra opgave 41: "we do not sell a paid edition"
    #     må ikke fejle. Den har *ordene* "paid edition" men intet beløb, så
    #     reglen må kræve begge dele.
    honest_edition = check_unbuyable_prices(good, [("site/eksempel.html", page(
        "<p>This e-book is free, and it stays free — we do not sell a paid edition of it.</p>"))])
    # (b) Nul-priser er sande. `$0` under en gratis pakke og `price: "0"` +
    #     InStock i JSON-LD er to måder at sige "gratis" på — de er ikke et
    #     løfte om at betale. Uden denne kontrol ville porten være rød på
    #     `site/site-icons.html`.
    free_jsonld = check_unbuyable_prices(good, [("site/eksempel.html", page(
        jsonld % ("0", "https://schema.org/InStock")))])
    free_label = check_unbuyable_prices(good, [("site/eksempel.html", page(
        '<div class="price">$0</div>'))])
    # (c) Samme pris som katalogens produkt, med købsknappen ved siden:
    #     skal være grøn. Uden den ville reglen gøre hver købsside rød på
    #     sine egne priser — og det gjorde min første version netop.
    buyable_label = check_unbuyable_prices(good, [("site/eksempel.html", page(
        f'<div class="price">$19</div>', f'<a href="{clean_copy_link}">Buy</a>'))])
    # (d) En kommandolinje er ikke et pristilbud, og et eksempel i en
    #     dokumentationsside er ikke et løfte. `$` er shell-prompten, og
    #     `$1` i et regex er en gruppe-reference.
    shell_prompt = check_unbuyable_prices(good, [("site/eksempel.html", page(
        "<pre><code>$ pip install Pillow\n$ curl -O site-icons-1.0.0.tar.gz\n"
        "$ python3 site_icons.py logo.svg</code></pre>"
        "<p>That package is not for sale — it is free and MIT licensed.</p>"))])
    example_in_docs = check_unbuyable_prices(good, [("site/eksempel.html", page(
        "<p>Et betalingslink ser sådan ud:</p>"
        "<pre><code>&lt;a href=\"https://buy.stripe.com/ukjendt0\"&gt;"
        "Paid edition: $9.99 (coming)&lt;/a&gt;</code></pre>"))])
    # (e) En omtale af en tredjeparts-pris i prosa er ikke vores tilbud. En
    #     GDPR-bot står ikke ved siden af en købsknap, og det er korrekt.
    quoted_price = check_unbuyable_prices(good, [("site/eksempel.html", page(
        "<p>Irish authorities have fined companies up to €10 million under the GDPR.</p>"))])
    # (f) Samme beløb som det sælges til andre steder: det må gerne stå som
    #     en krydshenvisning, fordi købet sker på den side der sælger det.
    cross_reference = check_unbuyable_prices(good, [("site/eksempel.html", page(
        '<p>Clean Copy Pro costs $19 per year. <a href="/clean-copy-tool">See the tool</a></p>'))])

    # De negative kontroller skal bestå af *deres egen grund*. Hvis
    # (a) ikke rammer portens mønster, består den kun fordi reglen aldrig
    # var tændt — og så beviser den intet. Samme krav som opgave 17 fund 3:
    # siger porten intet om sin egen evne, skal den sige det med en fejl.
    if not UNFULFILLED_CLAIM.search(
            "This e-book is free, and it stays free — we do not sell a paid edition of it."):
        print("SELFTEST FEJLER: den negative kontrol (a) rammer ikke UNFULFILLED_CLAIM — "
              "den er grøn fordi reglen slet ikke er tændt, og beviser intet")
        return 1
    # Og (d) skal bevise at CODE_TAGS faktisk gør en forskel: samme
    # eksempelpris *uden* `<pre>`/`code` skal fejle. Ellers er undtagelsen
    # tom, og kommentaren ovenfor en påstand uden dækning.
    if not check_unbuyable_prices(good, [("site/eksempel.html", page(
            "<p>Paid edition: $9.99 (coming)</p>"))]):
        print("SELFTEST FEJLER: eksempelprisen fejler heller ikke uden <pre>/<code> — "
              "CODE_TAGS er uden betydning for den negative kontrol (d)")
        return 1

    # ── sprogdækning: en købsside kun på ét sprog ─────────────────────────
    #
    # Mutationen er den rigtige gamle katalog, ikke en konstrueret fejlform:
    # den danske købsside for `eucomply-pro` fjernes fra inventaret, så porten
    # genfinder præcis den fejl, opgave 59s danske side lukkede. Derfor
    # forventes her ÉN rød, og at den rammer det produkt og ikke et andet.
    without_da_offer = {**good, "offers": [offer for offer in good["offers"]
                                           if offer["path"] != "site/da/compliance-report.html"]}
    if len(good["offers"]) - len(without_da_offer["offers"]) != 1:
        print("SELFTEST FEJLER: mutationen fjerner ikke præcis én købsside — de andre "
              "scenarier ville så teste en tilfældighed i stedet for sprogdækningen")
        return 1
    coverage_missing = check_language_coverage(without_da_offer, source_pages())
    coverage_ok = check_language_coverage(good, source_pages())
    # Negativ kontrol: et produkt der ikke sælges fra dette repo kræver ingen
    # side her. `transmute-desktop` er uden `pro_features`, fordi købslinket
    # ligger på transmute.run. Uden den kontrol ville porten kræve en dansk
    # side for et produkt den ikke engang kan dømme.
    ungated = {**good, "products": {
        **good["products"],
        "clean-copy-pro": {k: v for k, v in good["products"]["clean-copy-pro"].items()
                           if k != "pro_features"}}}
    coverage_ungated = check_language_coverage(ungated, source_pages())
    if len(coverage_missing) != 1 or "eucomply-pro" not in coverage_missing[0]:
        print("SELFTEST FEJLER: sprogdækningen fanger ikke den manglende danske købsside, "
              "eller rammer et andet produkt: " + "; ".join(coverage_missing))
        return 1
    if coverage_ok:
        print("SELFTEST FEJLER: sprogdækningen fejler på den katalog, der er komplet — "
              "kravet er for stramt: " + "; ".join(coverage_ok))
        return 1
    if coverage_ungated != coverage_ok:
        print("SELFTEST FEJLER: et produkt uden pro_features i katalogen fejler alligevel — "
              "porten dømmer produkter den ikke sælger her: " + "; ".join(coverage_ungated))
        return 1

    # Sprog fra stien alene lyver for de danske sider der hedder `<navn>-da.html`:
    # 14 af dem ligger i `site/` uden `/da/`, så de gamle tællinger sagde `en`.
    # Beviset er derfor ikke et opdigtet par sider men en rigtig dansk side fra
    # repoet, sat som købsside for et produkt der mangler sin danske side. Den
    # gamle kode krævede så en danske side, der allerede var der; den nye ser
    # `lang="da"` og går grøn.
    da_suffix_page = next((relative for relative, text in source_pages()
                           if relative.endswith("-da.html")
                           and '<html lang="da"' in text[:400].replace("'", '"')
                           and relative not in {str(o.get("path")) for o in good["offers"]}), None)
    if not da_suffix_page:
        print("SELFTEST FEJLER: ingen dansk `-da.html`-side at bruge som mutation — "
              "sprogskellet er så ikke længere til stede i site/ og porten er uden dækning")
        return 1
    suffixed = {**good, "offers": [offer for offer in good["offers"]
                                  if offer["path"] != "site/da/compliance-report.html"]
                + [{"product": "eucomply-pro", "path": da_suffix_page}]}
    if check_language_coverage(suffixed, source_pages()):
        print(f"SELFTEST FEJLER: en dansk købsside med engelsk sti ({da_suffix_page}) "
              "tælles ikke som dansk — `page_lang()` læser stien og ikke `lang`")
        return 1
    parts = da_suffix_page.replace("\\", "/").split("/")
    if "da" in parts[1:-1]:
        print(f"SELFTEST FEJLER: mutationen er ikke længere en dansk side med engelsk sti "
              f"({da_suffix_page}) — scenariet ville teste intet")
        return 1

    # ── indgang til købssiden: en købsside ingen kan nå ───────────────────
    #
    # Scenarierne bygger en *syntetisk* dist, fordi indgangen afgøres i det
    # byggede output — og fordi den del af reglen der kan være grøn for de
    # forkerte grunde er link-indsamlingen, ikke katalogen. Derfor er her fire
    # sider der hver *nævner* købssiden uden at være en indgang: en 404-side, en
    # side med kun canonical/hreflang, en side med URL'en i en inline
    # JSON-Streng, og købssiden selv. Tælles nogen af dem, er regelen grøn for
    # en købsside ingen læser kan nå, og det er præcis fejlformen.
    with tempfile.TemporaryDirectory() as tmp:
        fake = Path(tmp)
        site = fake / "mahope.tools"
        site.mkdir(parents=True)
        buy_page = "<html><head><title>Pro</title></head><body><a href=\"/\">Hjem</a></body></html>"

        def page_file(name: str, body: str) -> None:
            (site / name).write_text(body, encoding="utf-8")

        page_file("koebsside.html", buy_page)
        page_file("404.html", '<html><body><a href="/koebsside">Køb</a></body></html>')
        page_file("head.html", (
            '<html><head><link rel="canonical" href="https://mahope.tools/head">'
            '<link rel="alternate" hreflang="da" href="https://mahope.tools/koebsside">'
            '</head><body><p>Ingen link.</p></body></html>'))
        page_file("script.html", (
            '<html><body><p>Søg.</p><script>const urls = ["/koebsside", "/andet"];'
            'fetch("/api/track", {body: JSON.stringify({path: "/koebsside"})});</script>'
            '</body></html>'))
        page_file("andet.html", '<html><body><p>En side uden links.</p></body></html>')
        only_mentions = entry_point_index(fake)
        entry_offers = [{"path": "site/koebsside.html", "product": "clean-copy-pro",
                         "domain": "mahope.tools", "route": "/koebsside"}]
        # Rød: de fire sider ovenfor er ikke indgange, så den syntetiske
        # købsside er uopdaget præcis som `/da/compliance-report` var det 1/9.
        unreachable = check_buy_page_entry(entry_offers, only_mentions, fake)
        # Grøn: den samme side, når en rigtig side faktisk linker til den.
        page_file("indgang.html", '<html><body><a href="/koebsside">Se Pro</a></body></html>')
        reachable_index = entry_point_index(fake)
        reachable = check_buy_page_entry(entry_offers, reachable_index, fake)
        # Diskriminerende: det er *domænet* der afgør, ikke stien. De fire sites
        # deler `site/`, så en indgang til samme sti på et andet domæne er en
        # anden side — ellers ville reglen være grøn for cleancopy.tools' `/`
        # når kun mahope.tools' `/`linkede.
        same_path_elsewhere = {key: sources for key, sources in reachable_index.items()
                               if key != ("mahope.tools", "/koebsside")}
        same_path_elsewhere[("cleancopy.tools", "/koebsside")] = {"cleancopy.tools/indgang.html"}
        cross_domain = check_buy_page_entry(entry_offers, same_path_elsewhere, fake)
        # Og en indgang fra en side på et *andet* domæne tæller med: buildet
        # skriver et krydsdomæne-link som en absolut URL, så en læser kan
        # følge det. Ellers ville porten være strammere end den virkelige
        # købsrejse, hvor Clean Copy-siden linker til EUComply Pro.
        cross = Path(tmp) / "krydsdomaene"
        (cross / "mahope.tools").mkdir(parents=True)
        (cross / "cleancopy.tools").mkdir(parents=True)
        (cross / "cleancopy.tools" / "værktøj.html").write_text(
            '<html><body><a href="https://mahope.tools/koebsside">Se EUComply Pro</a>'
            '</body></html>', encoding="utf-8")
        cross_real = check_buy_page_entry(
            entry_offers, entry_point_index(cross), cross)
        if unreachable and "site/koebsside.html" not in unreachable[0]:
            print("SELFTEST FEJLER: indgangsreglen rammer ikke den uopdagelige købsside: "
                  + "; ".join(unreachable))
            return 1
    if reachable:
        print("SELFTEST FEJLER: indgangsreglen fejler på en købsside der har en indgang — "
              "kravet er for stramt: " + "; ".join(reachable))
        return 1
    if not cross_domain:
        print("SELFTEST FEJLER: en indgang på et andet domæne med samme sti tæller som en "
              "indgang — reglen er grøn for den forkerte grund")
        return 1
    if cross_real:
        print("SELFTEST FEJLER: en bygget side der linker krydsdomæne til købssiden fejler "
              "alligevel: " + "; ".join(cross_real))
        return 1

    # ── købsklik der ikke måles ────────────────────────────────────────────
    #
    # De tre scenarier dækker de to målte fejlformer: en side med kassalink uden
    # tracker, og en tracker hvor kliklytteren er væk. Kundenportalen er med som
    # negativ kontrol, fordi den ligner en kassalink men ikke er et køb — ellers
    # ville porten være strammere end den virkelige købsrejse, hvor en abonnent
    # skal kunne nå sin portal uden at tælle som købsklik.
    portal_link = good["billing_portal"]
    untracked_page = [("site/eksempel.html", f'<html><body><a href="{clean_copy_link}">Buy</a></body></html>')]
    untracked_click = check_buy_click_tracking(good, untracked_page)
    tracked_page = [("site/eksempel.html", f'<html><head><script defer src="/track.js"></script>'
                     f'</head><body><a href="{clean_copy_link}">Buy</a></body></html>')]
    tracked_click = check_buy_click_tracking(good, tracked_page)
    portal_only = [("site/portal.html", f'<html><body><a href="{portal_link}">Manage billing</a></body></html>')]
    portal_click = check_buy_click_tracking(good, portal_only)
    real_track = TRACK_JS.read_text(encoding="utf-8")
    muted_track = re.sub(r"\n  // Every Stripe checkout link counts.*?\n  \}, true\);\n", "\n",
                         real_track, flags=re.S)
    if muted_track == real_track:
        print("SELFTEST FEJLER: kliklytteren i site/track.js blev ikke fundet — scenariet "
              "muterer intet, så intet beviser at porten fanger en fjernet lytter")
        return 1
    muted_click = check_buy_click_tracking(good, source_pages(), muted_track)
    renamed_track = real_track.replace("event: 'buy-click'", "event: 'buyclick'")
    if renamed_track == real_track:
        print("SELFTEST FEJLER: buy-begivenhedens navn blev ikke fundet i site/track.js — "
              "scenariet muterer intet")
        return 1
    renamed_click = check_buy_click_tracking(good, source_pages(), renamed_track)

    scenarios: list[tuple[str, list[str] | Any]] = [
        ("et link uden for allowlisten", check_links(rogue_link)),
        ("et kontraktprodukt mangler i allowlisten", check_catalog(missing_product)),
        ("ét link delt mellem to produkter", check_catalog(shared_link)),
        ("en opfundet påstand på en virkelig købsside", check_offers(unsatisfiable_offer)[0]),
        ("en dokumenteret købsside uden inventar", check_offers(uninventoried)[0]),
        ("en købsside med forkert domæne", check_routes(wrong_domain["offers"], good["core_pages"])),
        ("for få centrale produktsider", check_routes(good["offers"], missing_core["core_pages"])),
        ("en kundeportal-URL der ikke er allowlistet", check_links(rogue_portal)),
        ("en kundeportal der ikke findes på portalsiderne", check_billing_portal(rogue_portal)),
        ("en abonnement-markering der ikke er i allowlisten", check_worker(no_subscriptions)),
        ("et download-produkt der ikke kan leveres, men sælges", undeliverable),
        ("et leverbart download-produkt uden købsside", forgot_the_page),
        ("en Pro-side der aldrig siger hvad gratis-udgaven giver", no_free_tier),
        ("en gratis-udgave forklaret i en lukket FAQ", buried_free_tier),
        ("en gratis/Pro-tabel med tomme celler", hollow_table),
        ("en Pro-pris uden nogen købsknap", unbuyable_symbol),
        ("en Pro-pris i valutaord uden købsknap", unbuyable_words),
        ("en tom celle i en tabel på en side der ikke sælger", hollow_unsold),
        ("en klient der sender brugeren ud for at købe uden et købssted", dead_client_buy),
        ("en struktureret pris på et beløb siden ikke sælger til", preorder_price),
        ("en prislabel med et beløb siden ikke sælger til", label_price),
        ("en løftet betalt udgave med en pris", promised_edition),
        ("en pris ved siden af et købssted uden for katalogen", foreign_venue),
        ("en struktureret pris der ikke er produktets egen pris", stale_structured),
        ("en købsside der ikke navngiver en Pro-funktion", pro_missing),
        ("en dansk købsside der kun siger funktionen på engelsk", pro_missing_da),
        ("et licensprodukt uden købsside på dansk", coverage_missing),
        ("en Pro-funktion der kun står i en lukket FAQ", pro_buried),
        ("en publiceret løgned om en Pro-funktion koden ikke har bygget", promise_found),
        ("en købsside der lover overvågning, historik, branding og support", eucomply_found),
        ("en /checkout-note der lover en Pro-funktion koden ikke har bygget", checkout_found),
        ("en pro_not_built-post uden bevis i koden", silent_found),
        ("en side der henter /api/report men siger at browseren analyserer", stale_found),
        ("en dansk side der henter /api/report men siger at browseren analyserer", stale_da_found),
        ("en købsside ingen bygget side linker til", unreachable),
        ("en købsside der kun har en indgang på et andet domæne", cross_domain),
        ("en købsknap på en side uden tracker", untracked_click),
        ("en tracker uden kliklytter", muted_click),
        ("en tracker der sender en anden begivenhed end buy-click", renamed_click),
    ]
    missed = [label for label, problems in scenarios if not problems]
    for label in missed:
        print(f"SELFTEST FEJLER: {label} blev ikke fanget")
    for label, problems in (("et produkt uden pro_not_best i katalogen", undeclared_found),
                            ("en klient der siger at der intet er at købe", honest_client),
                            ("en klient med et katalogens betalingslink", linked_client),
                            ("en Pro-side der siger hvad gratis-udgaven giver", should_also_pass),
                            ("en donationsside uden gratis-udgave", donation_no_free),
                            ("en gratis/Pro-tabel med købsknap", buyable),
                            ("en gratis/Pro-tabel uden pris", priceless),
                            ("en side der ærligt siger at der ingen betalt udgave er", honest_edition),
                            ("en gratis vare med price 0 i JSON-LD", free_jsonld),
                            ("en gratis pakke med en $0-prislabel", free_label),
                            ("en prislabel i katalogens egen pris", buyable_label),
                            ("en kommandolinje der ligner et pristilbud", shell_prompt),
                            ("en eksempelpris i en dokumentationsside", example_in_docs),
                            ("en omtalt tredjeparts-pris i prosa", quoted_price),
                            ("en krydshenvisning til en pris der sælges andre steder",
                             cross_reference),
                            ("en browser-påstand på en side der analyserer i browseren",
                             free_should_pass),
                            ("en sand print-dialog-påstand på en /api/report-side",
                             print_should_pass),
                            ("en skjult browser-påstand i en kommentar", hidden_should_pass),
                            ("en købsside med en indgang fra en bygget side", reachable),
                            ("en købsside der linkes krydsdomæne fra en bygget side", cross_real),
                            ("en købsknap på en side med tracker", tracked_click),
                            ("en kundeportal som ikke er et køb", portal_click)):
        if problems:
            print(f"SELFTEST FEJLER (falsk alarm): {label}: {problems[0]}")
            missed.append(label)
    if should_pass:
        # En kontrol der aldrig må fejle. Uden den kunne den nye regel være
        # stram nok til at gøre hver købsside rød, uden at nogen ser det.
        print(f"SELFTEST FEJLER: et leverbart produkt blev meldt som ikke-leverbart: {should_pass[0]}")
        missed.append("et leverbart produkt på en syntetisk købsside")
    print(f"selftest: {len(scenarios) - len(missed)}/{len(scenarios)} fejlformer fanget")
    return 1 if missed else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true", help="printér inventaret uden at kræve grøn gate")
    parser.add_argument("--self-test", action="store_true", help="bevis at gaten fanger drift")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    catalog = load_catalog(CATALOG)
    if args.report:
        print(json.dumps({"discovered": discover_offers(catalog)}, ensure_ascii=False, indent=2))
        return 0
    problems, inventory = run(catalog)
    print(f"{len(catalog['products'])} produkter, {len(inventory)} dokumenterede købssider")
    print(f"problems: {len(problems)}")
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
