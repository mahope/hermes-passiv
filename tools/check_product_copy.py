#!/usr/bin/env python3
"""Gate produkttekster, der lover noget produkterne ikke kan holde.

To klasser:

* **DeskUptime** — de absolutte claims ("no phone-home", "no central server",
  "no telemetry"), opgave 2 trak tilbage fordi Pro-licensen er online.
* **Clean Copies Pro-flader** — de sider hvor licensnøglen *indtastes*, altså
  hvor et absolutt løfte om at intet forlader maskinen er en løgnest i samme
  dokument. Opgave 27 rettede FAQ'en på /clean-copy, men hero-noten og
  privatlivsnoten på /clean-copy-tool sagde videre det samme.

    python3 tools/check_product_copy.py
    python3 tools/check_product_copy.py --self-test
"""
from html.parser import HTMLParser
import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys

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
            "pro activates and revalidates your licence with mahope.tools",
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
            "pro aktiverer og revaliderer din licens mod mahope.tools",
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
            "pro activation and revalidation send the licence key, a stable device id and the product identifier deskuptime-pro to mahope.tools and receive the licence status",
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
            "pro-licensen aktiveres og revalideres online mod mahope.tools",
            "url-liste og tjekresultater bliver på din maskine og uploades ikke til en central monitoreringstjeneste",
            "ved aktivering og revalidering sender appen licensnøglen, et stabilt device-id og produktidentifieren deskuptime-pro til mahope.tools og modtager licensstatus",
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
    "pro-licensen aktiveres og revalideres online mod mahope.tools",
    "url-liste og tjekresultater bliver på din maskine og uploades ikke til en central monitoreringstjeneste",
    "ved aktivering og revalidering sender appen licensnøglen, et stabilt device-id og produktidentifieren deskuptime-pro til mahope.tools og modtager licensstatus",
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

# De præcise sætninger der var publiceret indtil denne iteration. Beviset på
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

    # Positiv kontrol: de rigtige filer skal være grønne, ellers er porten
    # grøn fordi den intet kan.
    positive = [f"{relative}: {problem}" for relative, (forbidden, required) in cases.items()
                for problem in check_text(relative, real[relative], forbidden, required)]

    # Negativ kontrol: en kvalificeret påstand er ikke en forbudt påstand.
    qualified = ('<p>Your text never leaves this page. If you activate a Pro key, that key and a '
                 'device id are sent to our license API on <code>mahope.tools</code> so the license '
                 'can be validated. A Pro license key is checked online against mahope.tools.</p>')
    negative = [problem for problem in check_text("qualified", qualified, *tool) if "forbidden" in problem]

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
        print(f"positiv kontrol: {len(cases)} rigtige filer er grønne")
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
    print(f"problems: {len(problems)}")
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
