#!/usr/bin/env python3
"""Byg en læsevisning af en e-bog ud fra den EPUB, kunden faktisk henter.

Baggrund (1/10): `site/books/*.html` er 132–153 linjer — en salgsside med en
liste over kapitler og en downloadknap. Den eneste måde at læse en bog på er at
hente EPUB'en og åbne den i en læser. Feature-kø punkt 2 sagde «bøgerne læses
online, kapitel for kapitel», og den er lavet her.

**Kilden er EPUB'en, ikke `ebook/*.md`.** EPUB'en er den fil kunden henter, så
den er den eneste sandhed: hvis vi læste markdown-kilden, kunne læsevisningen
vise en udgave der ikke findes i det, kunden får. Derfor bygges teksten ud af
`ebook/<slug>.epub` ved hvert build — den kan ikke blive ældre end bogen.

Rækkefølgen kommer fra OPF-spine'en, ikke fra filnavne, så en bog hvor kapitlerne
 hedder `ch10.xhtml` før `ch2.xhtml` stadig læses i rigtig rækkefølge.

Alt indhold går gennem `html.escape` på vej ud. EPUB'er er vores egne filer, men
konverteringen skriver tekst direkte i en side der også kører vores eget script,
 så uden escape ville én fejl i en bog gøre alle sider sårbare.
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from html import escape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EBOOK = ROOT / "ebook"

# Hvor mange kapitler der vises. To er nok til at se tonen og få et svar på
# «er det noget for mig», og holder siden under den størrelse hvor folk scroller
# videre uden at læse — hvilket er præcis det læsevisningen skal undgå.
PREVIEW_CHAPTERS = 2

# Sikkerhedsnet mod en udgave med 40 kapitler, ikke en daglig begrænsning. Den
# lå først på 9000, og det fik `eaa-checklist` til at vise 1 kapitel i stedet
# for 2: kapitel 2 er bogens 10-punkts-tjekliste på 9,8 KB, altså præcis den
# del en læser vil se. Resten af bogen er gratis, så at skjule dækningen er
# dyrere end at lade siden være lidt længere.
MAX_CHARS = 20000

# Tags der er indhold. Resten (head, title, link, meta) er EPUB-metadata.
BLOCK = {"h2", "h3", "h4", "p", "blockquote", "pre"}
INLINE = {"strong", "em", "code", "a", "b", "i"}
SKIP = {"head", "title", "link", "meta", "style", "script", "col", "colgroup"}
VOID = {"hr", "br"}


class _Body(HTMLParser):
    """Konverterer én EPUB-kapitel til ren, escaped HTML.

    HTMLParser bruges frem for regex, fordi en regex på XHTML-fejl giver enten
    rå markup i output (contract-punkt 2) eller taber indhold. Her er det kun
    én fejlvej, og den er håndteret: ukendte tags springes over, og tekst
    escapes altid.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.stack: list[str] = []
        self.skip_depth = 0
        self.title = ""

    # -- helpers -------------------------------------------------------
    def _open(self, tag: str) -> bool:
        if tag in SKIP:
            self.skip_depth += 1
            return False
        if self.skip_depth:
            return False
        if tag in BLOCK or tag in INLINE or tag in {"ul", "ol", "li", "table",
                                                   "thead", "tbody", "tr", "th", "td"}:
            self.out.append("<" + tag + ">")
            return True
        if tag in VOID:
            self.out.append("<hr>" if tag == "hr" else "<br>")
            return False
        return False

    def _close(self, tag: str) -> None:
        if tag in SKIP:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag in BLOCK or tag in INLINE or tag in {"ul", "ol", "li", "table",
                                                   "thead", "tbody", "tr", "th", "td"}:
            self.out.append("</" + tag + ">")

    # -- HTMLParser ---------------------------------------------------
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "title" and not self.skip_depth:
            return
        if tag == "a":
            href = dict(attrs).get("href", "")
            # Kun http(s) slipper igennem. `javascript:` i et link er den ene
            # måde EPUB-tekst kan blive til script på siden.
            if re.match(r"(?i)^https?://", href or ""):
                self.out.append('<a href="%s" rel="noopener">' % escape(href, quote=True))
                self.stack.append("a")
                return
            self.stack.append("")
            return
        if self._open(tag):
            self.stack.append(tag)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "a" and self.stack and self.stack[-1] == "a":
            self.out.append("</a>")
            self.stack.pop()
            return
        if tag in BLOCK or tag in INLINE or tag in {"ul", "ol", "li", "table",
                                                   "thead", "tbody", "tr", "th", "td"}:
            if self.stack and self.stack[-1] == tag:
                self.stack.pop()
                self._close(tag)
        elif tag in SKIP:
            self._close(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        if self.skip_depth or not data.strip():
            return
        self.out.append(escape(data))

    def text(self) -> str:
        return re.sub(r"\s+", " ", "".join(self.out)).strip()


def _spine(zf: zipfile.ZipFile) -> list[str]:
    """Kapitlerne i læse-rækkefølge, læst af OPF-spine'en."""
    opf_name = None
    for cand in ("content.opf", "OEBPS/content.opf"):
        if cand in zf.namelist():
            opf_name = cand
            break
    if not opf_name:
        raise ValueError("EPUB without content.opf")
    opf = zf.read(opf_name).decode("utf-8", "replace")

    hrefs = dict(re.findall(r'<item\b[^>]*\bid="([^"]+)"[^>]*\bhref="([^"]+)"', opf))
    if not hrefs:  # attributrækkefølgen kan være omvendt
        hrefs = {i: h for h, i in
                 ((h, i) for i, h in re.findall(r'<item\b[^>]*\bhref="([^"]+)"[^>]*\bid="([^"]+)"', opf))}
    order = []
    for idref in re.findall(r'<itemref\b[^>]*\bidref="([^"]+)"', opf):
        href = hrefs.get(idref)
        if href:
            name = href.split("/")[-1]
            if name in zf.namelist():
                order.append(name)
    if not order:
        raise ValueError("EPUB spine resolves to no chapters")
    return order


def _title_of(xhtml: str) -> str:
    m = re.search(r"<h2[^>]*>(.*?)</h2>", xhtml, re.S | re.I)
    if not m:
        m = re.search(r"<title[^>]*>(.*?)</title>", xhtml, re.S | re.I)
    if not m:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()


def _clean(html: str) -> str:
    """Tøm et kapitel for det der ikke er læsning.

    EPUB-skabelonen har `<h2>`-titlen både i `<title>` og som første element; det
    giver en dobbelt overskrift, fordi vi sætter titlen som `<summary>`.
    """
    html = re.sub(r"^\s*<h2[^>]*>.*?</h2>\s*", "", html, count=1, flags=re.S | re.I)
    return html.strip()


# Ren omslagsside-tekst. En læsevisning skal begynde med kapitel 1 — ellers
# læser man forside og forord og glemmer bogen. målt 1/10: alle seks EPUB'er
# starter med «Front Matter», og to har også en «Foreword» bagefter.
# «Preface» og «Introduction» er derimod rigtigt indhold og bliver stående —
# Chrome-extension-bogen har ingen «Chapter N»-titler, så der er forordet
# bogens egentlige første kapitel.
FRONT_MATTER = {"front matter", "foreword", "table of contents", "contents",
                "about the author", "acknowledgements", "acknowledgments",
                "copyright", "colophon", "title page"}


def _is_front_matter(title: str) -> bool:
    t = re.sub(r"\s+", " ", title).strip().strip(".:—–-").lower()
    return t in FRONT_MATTER


# Den frie værktøjsbane, der manglede i hver læsevisning. Målt 2/10: **0** af de
# seks bogsider linkede til et eneste af vores egne værktøjer, så en læser der
# lige har læst to kapitler om cookies eller NIS2 skulle selv finde ud af, at der
# står et gratis værktøj der gør det samme på sit eget site. Blokken sidder
# **sidst i kapitlerne** — efter folden, hvor læseren netop er færdig — så den
# ikke er endnu en knap i heroen oven på bogens egen download-CTA.
#
# Teksten er bogen emnet, ikke en påstand om værktøjet: hver linje er hentet fra
# den route den peger på, så den ikke kan rådne, hvis værktøjet ændrer sig. Den
# bruger `btc` med læsevisningens **egne** regler, fordi `.reader .reader-body p`
# og `a` er mere specifikke end sitets `blog-tool-cta`-komponent: målt i
# browseren 2/10, hvor komponenten renderede som brødtekst med et blåt
# understrevet link. Ingen ny farve og ingen ny afstand i sitets eget design.
TOOL_CTA = {
    "cookie-consent-guide": (
        "The same three checks, on your own site: the free cookie consent checker "
        "reads the banner, the script tags and the privacy link.",
        "/cookie-check", "Check my cookies"),
    "gdpr-for-agencies": (
        "The agreement from chapter 2, as a form: the free DPA generator asks for "
        "the roles and the annexes and gives you the document to send.",
        "/dpa-generator", "Write my DPA"),
    "nis2-for-agencies": (
        "Answer the chapter 1 questions about your own company: the free NIS2 "
        "self-assessment asks about your sector, your headcount and your services.",
        "/nis2-check", "Am I covered by NIS2?"),
    "eaa-checklist": (
        "Run the ten-point checklist on a real site: the free scanner checks "
        "contrast, alt text, headings and form labels, and hands you the findings.",
        "/scan", "Scan my site"),
    "eaa-shopify": (
        "The same checks on a real storefront — paste any Shopify URL into the free "
        "scanner, no plugin and no theme access needed.",
        "/scan", "Scan my store"),
    "build-your-first-chrome-extension": (
        "The icon sizes your manifest needs, generated from one SVG: favicons, "
        "PWA icons and the web app manifest, free and MIT-licensed.",
        "/site-icons", "Generate the icons"),
}


def tool_cta(slug: str) -> str:
    """Værktøjsbanneret til sidst i læsevisningen, eller tomt hvis bogen ingen har."""
    row = TOOL_CTA.get(slug)
    if not row:
        return ""
    label, href, button = row
    return ('\n<div class="btc"><p>%s</p>'
            '<a class="cta" href="%s">%s</a></div>' % (label, href, button))


def chapters(slug: str) -> list[dict]:
    """(titel, html) for de første kapitler i bogen med denne slug."""
    path = EBOOK / (slug + ".epub")
    if not path.exists():
        raise FileNotFoundError(path)
    out: list[dict] = []
    with zipfile.ZipFile(path) as zf:
        for name in _spine(zf):
            if len(out) >= PREVIEW_CHAPTERS:
                break
            raw = zf.read(name).decode("utf-8", "replace")
            body = re.search(r"<body[^>]*>(.*)</body>", raw, re.S | re.I)
            if not body:
                continue
            title = _title_of(raw)
            if _is_front_matter(title):
                continue
            p = _Body()
            p.feed(body.group(1))
            p.close()
            html = _clean(p.text())
            if len(html) < 400:
                continue
            out.append({"title": title, "html": html})
    return out


def section(slug: str, epub_note: str) -> str:
    """Hele `<section>`-blokken, som bygget skriver ind i bogsiden."""
    chs = chapters(slug)
    if not chs:
        raise ValueError("%s: no chapters extracted" % slug)

    body, used = [], 0
    for c in chs:
        if used and used + len(c["html"]) > MAX_CHARS:
            break
        used += len(c["html"])
        body.append('<h3 class="reader-chapter-title">%s</h3>\n%s' % (escape(c["title"]), c["html"]))

    # «1 chapter» og «2 chapters». En tidligere udgave skrev «2 chapter2», fordi
    # samme `{n}` blev brugt til både tallet og flertal — dansk og engelsk er
    # ikke sådan, og det så på en side vi sender til kunder.
    n = len(body)
    word = "chapter" if n == 1 else "chapters"
    joined = "\n".join(body) + tool_cta(slug)
    return READER_TEMPLATE.format(
        lede=("The opening of the book, straight from the EPUB you get below — not a "
              "summary written for this page. %d %s in full, then the rest is free to "
              "download." % (n, word)),
        summary="Read the first %s online" % (word if n == 1 else "%d %s" % (n, word)),
        chapters=joined,
        note=escape(epub_note),
        # Kun CSS for de elementer kapitlerne faktisk indeholder. Skabelonen
        # havde regler for `pre`, `blockquote`, `table`, `hr` og `h4` for alle
        # seks bøger, men kun nogle af dem har sådanne afsnit, så resten var død
        # CSS — og `check_built_css` dømmer et type-led i sidens egen `<style>`
        # som fejl, når siden ikke har elementet. Se `optional_css`.
        css=optional_css(joined),
        mørke=optional_dark_css(joined),
    )


# Hvilke elementer hvert kapitel faktisk bruger. Dødelisten er målt, ikke
# gættet: `check_built_css` fandt præcis `blockquote`, `code`, `h4`, `hr`,
# `pre`, `table`, `td` og `th` døde på de bogsider, hvis kapitler ikke har dem.
# `p`, `ul`, `ol`, `li` og `h3` er ikke på listen, fordi kapitlerne altid har
# mindst ét af hver — det er målt på alle seks.
OPTIONAL_TAGS = ("h4", "table", "th", "td", "blockquote", "pre", "code", "hr")

# Én regel pr. element. Rækkefølgen er CSS-kaskadens, så `pre` skal komme før
# `code` — ellers ville inline-kode arve `pre`'s baggrund.
OPTIONAL_RULES = (
    ("h4", "    .reader .reader-body h4 { font-size:14px; margin:16px 0 4px; color:#444; }"),
    ("table", "    .reader .reader-body table { border-collapse:collapse; width:100%; margin:0 0 14px; font-size:14px; display:block; overflow-x:auto; }"),
    ("th", "    .reader .reader-body th { background:#f4f6f8; }"),
    ("td", "    .reader .reader-body th, .reader .reader-body td { border:1px solid #e2e5ea; padding:7px 10px; text-align:left; vertical-align:top; }"),
    ("blockquote", "    .reader .reader-body blockquote { margin:0 0 12px; padding:2px 0 2px 14px; border-left:3px solid #d8dee6; color:#444; }"),
    ("pre", "    .reader .reader-body pre { background:#f6f8fa; padding:12px 14px; border-radius:6px; overflow-x:auto; font-size:13px; }"),
    ("code", "    .reader .reader-body code { background:#f1f3f5; padding:1px 5px; border-radius:4px; font-size:13px; }"),
    ("hr", "    .reader .reader-body hr { border:0; border-top:1px solid #e2e5ea; margin:20px 0; }"),
)

OPTIONAL_DARK = (
    ("h4", "      .reader .reader-body h4 { color:#b9bfc7; }"),
    ("th", "      .reader .reader-body th { background:#1f232a; }"),
    ("td", "      .reader .reader-body th, .reader .reader-body td { border-color:#2a2e35; }"),
    ("blockquote", "      .reader .reader-body blockquote { border-left-color:#3a3f47; color:#b9bfc7; }"),
    ("pre", "      .reader .reader-body pre { background:#1f232a; }"),
    ("code", "      .reader .reader-body code { background:#22262d; }"),
)


# Værktøjsbanneret i læsevisningen. Reglerne ligger i læsevisningens eget
# `<style>` og ikke i `style.css`, fordi `.reader .reader-body p` og
# `.reader .reader-body a` er mere specifikke end sitets egen `blog-tool-cta`:
# målt i browseren 2/10, hvor komponenten uden disse regler renderede som
# brødtekst med et blåt understreget link. Farverne er læsevisningens egne, så
# banneret ligner det, det står i — også i mørk tilstand.
CTA_RULES = (
    '    .reader .reader-body .btc { margin:22px 0 6px; padding:14px 16px;'
    ' border:1px solid #d8dee6; border-radius:10px; background:#f6f8fa;'
    ' display:flex; flex-wrap:wrap; gap:10px 14px; align-items:center; }',
    '    .reader .reader-body .btc p { margin:0; flex:1 1 16rem; font-size:14px;'
    ' line-height:1.5; color:#444; }',
    '    .reader .reader-body .btc a.cta { flex:0 0 auto; display:inline-block;'
    ' padding:9px 16px; border-radius:8px; background:#0b6e8f; color:#fff;'
    ' font-weight:600; font-size:14px; text-decoration:none; }',
)

CTA_DARK = (
    '      .reader .reader-body .btc { background:#16181d; border-color:#2a2e35; }',
    '      .reader .reader-body .btc p { color:#d7dbe0; }',
)


def optional_css(html: str) -> str:
    """CSS kun for de elementer `html` faktisk indeholder.

    Hvert element dømmes på sin egen tilstedeværelse, så porten kan ikke finde en
    regel uden sit element. Undtagelsen er `pre code`, som kræver begge dele:
    inline-kode inde i et kodeblok skal have blokkens baggrund, så reglen må
    kun skrives når der faktisk er et `<pre>` **og** et `<code>`.
    """
    brugte = {t for t in OPTIONAL_TAGS if re.search(r"<%s[\s>]" % t, html, re.I)}
    linjer = [rule for tag, rule in OPTIONAL_RULES if tag in brugte]
    if {"pre", "code"} <= brugte:
        linjer.append("    .reader .reader-body pre code { background:none; padding:0; }")
    if re.search(r'class="[^"]*\bbtc\b', html):
        linjer.extend(CTA_RULES)
    return "\n".join(linjer)


def optional_dark_css(html: str) -> str:
    """Mørke-mod af `optional_css`. Samme måde, samme grund."""
    brugte = {t for t in OPTIONAL_TAGS if re.search(r"<%s[\s>]" % t, html, re.I)}
    linjer = [rule for tag, rule in OPTIONAL_DARK if tag in brugte]
    if re.search(r'class="[^"]*\bbtc\b', html):
        linjer.extend(CTA_DARK)
    return "\n".join(linjer)


READER_TEMPLATE = """<section class="reader" id="read-online">
  <style>
    .reader {{ max-width:760px; margin:44px auto; padding:0 20px; }}
    .reader > h2 {{ font-size:22px; margin:0 0 8px; }}
    .reader-lede {{ color:#555; font-size:15px; line-height:1.6; margin:0 0 18px; }}
    .reader details {{ border:1px solid #e2e5ea; border-radius:8px; padding:14px 18px; background:#fbfcfd; }}
    .reader summary {{ font-weight:600; font-size:15px; cursor:pointer; color:#111; }}
    .reader-chapter-title {{ font-size:17px; margin:22px 0 8px; }}
    .reader .reader-body {{ font-size:15px; line-height:1.7; color:#222; margin-top:14px; }}
    .reader .reader-body h3 {{ font-size:15px; margin:20px 0 6px; }}
    .reader .reader-body p {{ margin:0 0 12px; }}
    .reader .reader-body ul, .reader .reader-body ol {{ margin:0 0 12px; padding-left:22px; }}
    .reader .reader-body li {{ margin:0 0 4px; }}
{css}
    .reader-foot {{ font-size:14px; color:#555; margin:16px 0 0; }}
    @media (prefers-color-scheme: dark) {{
      .reader summary {{ color:#e8eaed; }}
      .reader details {{ background:#16181d; border-color:#2a2e35; }}
      .reader .reader-body {{ color:#d7dbe0; }}
{mørke}
    }}
  </style>
  <h2>Read it before you download</h2>
  <p class="reader-lede">{lede}</p>
  <details open>
    <summary>{summary}</summary>
    <div class="reader-body">
{chapters}
    </div>
  </details>
  <p class="reader-foot">{note}</p>
</section>
"""


# Hvad der skal ske, når læsevisningen mangler på en bogside. Bygget kalder
# `inject` på hver bogside; en side uden EPUB er en fejl i repoet, ikke en grund
# til at publicere en bogside uden indhold.
INJECT_BEFORE = re.compile(
    r'(?=<div class="cta-section")|(?=<div class="related-books")|(?=</main>)', re.I)
# En side der allerede har læsevisningen. Bygget må kunne køre igen uden at
# læsevisningen kommer dobbelt (contract-punkt 3): en ekstra kopiering af to
# kapitler er både dobbelt indhold og en kilde til den slags copy-paste-fejl,
# der har overlevet review før.
EXISTING = re.compile(
    r'<section class="reader" id="read-online">.*?</section>', re.S | re.I)


def inject(html: str, slug: str, epub_note: str) -> str:
    """Skriv læsevisningen ind i en bogside, lige før købs-/download-CTA'en."""
    sec = section(slug, epub_note)
    html = EXISTING.sub("", html)  # idempotent: fjern først, skriv så
    m = INJECT_BEFORE.search(html)
    if not m:
        return html + "\n" + sec
    return html[: m.start()] + sec + "\n\n" + html[m.start():]


# ---------------------------------------------------------------- selftest
def self_test() -> int:
    passed = failed = 0

    def ok(name: str, cond: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print("FEJL: %s — %s" % (name, detail[:200]))

    epub = "gdpr-for-agencies"
    chs = chapters(epub)
    html = section(epub, "The full book is free as an EPUB.")

    ok("EPUB'en giver kapitler", len(chs) >= 1, str(len(chs)))
    ok("Titlen er kapitlets egen", bool(chs and chs[0]["title"]), str(chs[:1]))
    ok("Kapitlet har indhold", len(html) > 1500, str(len(html)))
    ok("Der er ingen rå markup-lækage", "&lt;" in html or "<script" not in html, "")

    # 0. Læsevisningen skal begynde med kapitel 1, ikke med omslagssiden, og
    #    fleral skal hedde «chapters». En tidligere udgave skrev «2 chapter2».
    ok("læsevisningen springer omslagssiden over",
       all(not _is_front_matter(c["title"]) for c in chs),
       str([c["title"] for c in chs]))
    ok("første kapitel er en rigtig kapitel",
       bool(chs) and not re.match(r"(?i)^(front matter|foreword)", chs[0]["title"]),
       str(chs[:1]))
    ok("flertal hedder chapters", "2 chapters in full" in html, html[:0] or "felt")
    ok("ingen 'chapter2'", "chapter2" not in html, "")
    ok("overskriften tæller korrekt", "Read the first 2 chapters online" in html, "")

    # 0b. CSS'en i læsevisningen skal nå browseren. Reglerne kommer fra
    # `OPTIONAL_RULES`/`CTA_RULES` som **værdier** til `READER_TEMPLATE.format`,
    # og `str.format` genbehandler ikke indsatte værdier — så de skal have
    # enkeltklammer. Målt 2/10 på den byggede side: skrevet med `{{ }}` kom
    # `{{` bogstaveligt ud i `<style>` på alle seks bogsider, browseren kassede
    # hver regel, og læsevisningens tabeller, kodeblokke, citater og overskrifter
    # har været uden styling lige siden den blev skrevet. Målt i browseren:
    # `.btc a.cta` havde `background: transparent` og `text-decoration: underline`.
    ok("CSS'en har ingen dobbeltklammer", "{{" not in html and "}}" not in html,
       repr([m for m in re.findall(r".{0,30}\{\{.{0,30}", html)][:2]))
    ok("værktøjsbannerets regel er med", ".reader .reader-body .btc a.cta {" in html, "")
    ok("banneret har knap og rute", 'class="cta" href="/dpa-generator"' in html
       or "btc" not in html, "gdpr-bogen skal pege på /dpa-generator")

    # 1. Markup i bogen må aldrig blive levende tags.
    p = _Body()
    p.feed("<body><p>Hej &amp; <script>alert(1)</script> "
           "<img src=x onerror=alert(1)>"
           "<a href=\"javascript:alert(1)\">klik</a> &lt;script&gt;x&lt;/script&gt;</p></body>")
    p.close()
    evil = p.text()
    ok("script-tags er væk", "<script" not in evil and "alert(1)" not in evil, evil)
    ok("onerror overlever ikke", "onerror" not in evil, evil)
    ok("javascript:-href overlever ikke", "javascript:" not in evil, evil)
    ok("tekst escape-stadig", "&lt;script&gt;" in evil, evil)

    # 2. Rækkefølgen kommer fra spine'en, ikke fra filnavne.
    ok("spine'en læses", bool(_spine(zipfile.ZipFile(EBOOK / (epub + ".epub")))), "")

    # 3. Alle otte bøger kan læses, og siden får præcis én sektion.
    for slug in sorted(p.stem for p in EBOOK.glob("*.epub")):
        try:
            h = section(slug, "note")
            ok("%s læses" % slug, "reader-body" in h and len(h) > 1200, str(len(h)))
            # Alle seks har mere end to rigtige kapitler, så de skal alle vise to.
            # En der viser én, har mistet dækning på loftet — det så
            # `eaa-checklist` gøre, og det er præcis den fejl der skjuler
            # bogens bedste kapitel. Tælles på den *renderede* sektion, ikke på
            # `chapters()`: loftet anvendes først i `section()`, så en dom på
            # `chapters()` er grøn uanset hvad der vises.
            shown = h.count('class="reader-chapter-title"')
            ok("%s viser to kapitler" % slug, shown == 2, str(shown))
            ok("%s er under loftet" % slug, len(h) < 40000, str(len(h)))
        except Exception as exc:  # noqa: BLE001
            ok("%s læses" % slug, False, repr(exc))

    # 4. Injektionen skriver præcis én gang, og før CTA'en.
    page = ('<html><body><div class="chapter-list">x</div>'
            '<div class="cta-section">download</div></body></html>')
    once = inject(page, epub, "note")
    ok("injektionen skriver én gang", once.count('id="read-online"') == 1, "")
    ok("læsevisningen kommer før CTA'en",
       once.index('id="read-online"') < once.index('cta-section'), "")
    ok("CTA'en er ikke væk", 'class="cta-section"' in once, "")

    twice = inject(once, epub, "note")
    ok("anden injektion duplikerer ikke", twice.count('id="read-online"') == 1,
       str(twice.count('id="read-online"')))

    # 5. Manglende EPUB skal vælte, ikke tie stille.
    try:
        section("findes-ikke", "note")
        ok("manglende EPUB vælter", False, "ingen fejl")
    except FileNotFoundError:
        ok("manglende EPUB vælter", True)

    # 6. `build_sites.py` springer kun sider over når der *ikke* findes en EPUB.
    #    Den springer altså ikke en rigtig bogside over ved en fejl, og de to
    #    bogside-ruter uden EPUB (`index`, `compliance-bundle`) får heller ikke
    #    en læsevisning. Uden denne dom kan en ny EPUB blive liggende i
    #    `ebook/` uden at nogen bogside nogensinde viser den.
    site_books = ROOT / "site" / "books"
    for page in sorted(site_books.glob("*.html")):
        slug = page.stem
        har_epub = (EBOOK / (slug + ".epub")).exists()
        dist_side = (ROOT / "dist" / "mahope.tools" / "books" / page.name)
        bygget = dist_side.exists() and 'id="read-online"' in dist_side.read_text(encoding="utf-8")
        ok("%s får læsevisning == den har en EPUB" % slug, har_epub == bygget,
           "epub=%s bygget=%s" % (har_epub, bygget))

    print("book_reader: %d/%d" % (passed, passed + failed))
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--slug", help="skriv læsevisningen for én bog til stdout")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.slug:
        sys.stdout.write(section(args.slug, ""))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
