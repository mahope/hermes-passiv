"""Brand facts shared by make_icons.py, make_og.py and build_sites.py."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAND_DIR = ROOT / "site" / "_brand"

BRANDS: dict[str, dict] = {
    "cleancopy": {
        "name": "Clean Copy",
        "domain": "cleancopy.tools",
        "mark": "C",
        "accent": "#0f7b6c",
        "github": "https://github.com/mahope/clean-copy",
        "summary": "Clean Copy turns any web page, selection or HTML file into clean Markdown or plain text. "
                   "Browser extension (Chrome, Firefox), CLI, Obsidian plugin, VS Code extension and a web tool. "
                   "MIT-licensed, runs locally, no account.",
        "install": ["npx github:mahope/clean-copy-cli --url https://example.com",
                    "npm install -g github:mahope/clean-copy-cli",
                    "brew install mahope/tap/clean-copy"],
        "tagline": {"en": "Copy web pages as clean Markdown or plain text.",
                    "da": "Kopiér websider som ren Markdown eller ren tekst."},
    },
    "deskuptime": {
        "name": "DeskUptime",
        "domain": "deskuptime.com",
        "mark": "D",
        "accent": "#2456d6",
        "github": "https://github.com/mahope/deskuptime",
        "summary": "DeskUptime checks whether your websites are up, when their SSL certificates expire and whether "
                   "their content changed, from your own machine. Free CLI; desktop app for macOS and Windows. No monthly fee.",
        "install": ["npx github:mahope/deskuptime check https://example.com",
                    "brew install deskuptime"],
        "tagline": {"en": "Uptime, SSL and content checks from your own machine.",
                    "da": "Oppetid, SSL og indholdstjek fra din egen maskine."},
    },
    "bugbottle": {
        "name": "BugBottle",
        "domain": "bugbottle.dev",
        "mark": "B",
        "accent": "#b4520f",
        "github": "https://github.com/mahope/bugbottle",
        "summary": "BugBottle is a small MIT-licensed JavaScript library that collects page context, console errors, "
                   "the element a user points at and an optional screenshot, and POSTs the report to your own endpoint. "
                   "Zero dependencies, no vendor backend.",
        "install": ["npm install bugbottle"],
        "tagline": {"en": "In-app bug reports with the evidence attached.",
                    "da": "Fejlrapporter i appen, med beviserne vedhæftet."},
    },
    "mahope": {
        "name": "mahope.tools",
        "domain": "mahope.tools",
        "mark": "m",
        "accent": "#4a3fc4",
        "github": "https://github.com/mahope",
        "summary": "mahope.tools collects free browser-based tools for developers and small web agencies: GDPR document "
                   "generators, WCAG colour and contrast tools, NIS2 assessments, developer utilities, plus guides, "
                   "blog posts and e-books. Everything runs in the browser; no account, no tracking cookies.",
        "install": [],
        "tagline": {"en": "Free web tools, guides and e-books from mahoje.dk.",
                    "da": "Gratis webværktøjer, guides og e-bøger fra mahoje.dk."},
    },
}

BG = "#f7f7f5"
INK = "#1b1d1f"
MUTED = "#5a5f64"
