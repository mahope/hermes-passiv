#!/usr/bin/env python3
from html.parser import HTMLParser
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


def main() -> None:
    problems = []
    for relative, forbidden, required in PUBLIC_CHECKS:
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
    print(f"{len(PUBLIC_CHECKS) + 1} DeskUptime copy sources checked")
    print(f"problems: {len(problems)}")
    for problem in problems:
        print(problem)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
