#!/usr/bin/env python3
"""Iteration 224: add reciprocal hreflang links to EN/DA blog pairs + fix wrong DA canonical."""
import re, os, sys

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site")
DOMAIN = "https://hermes-passiv.pages.dev"

# (en_relpath, da_relpath) — paths relative to site/, extensionless URLs derived
PAIRS = [
    ("blog/wcag-22-what-changes.html", "blog/wcag-22-aendringer.html"),
    ("blog/gdpr-agency-role.html", "blog/gdpr-webbureau-da.html"),
    ("blog/eaa-deadline-2026.html", "blog/eaa-frister-2026.html"),
    ("blog/free-accessibility-testing-tools.html", "da/blog/gratis-tilgaengelighedsvaerktoejer.html"),
    ("blog/html-to-markdown-converter.html", "da/blog/html-til-markdown-konverter.html"),
    ("blog/url-to-markdown-converter.html", "da/blog/url-til-markdown-konverter.html"),
    ("blog/meta-tag-checker.html", "da/blog/meta-tjekker.html"),
    ("blog/open-graph-checker.html", "da/blog/open-graph-tjekker.html"),
    ("blog/copy-table-from-website-to-excel.html", "da/blog/kopier-tabel-til-excel.html"),
    ("blog/paste-without-formatting-chrome.html", "da/blog/indsæt-uden-formatering-i-chrome.html"),
    ("blog/paste-into-obsidian-clean-markdown.html", "da/blog/indsæt-i-obsidian-ren-markdown.html"),
    ("blog/copy-from-chatgpt-into-word.html", "da/blog/kopier-chatgpt-til-word.html"),
    ("blog/copy-as-markdown-chrome-extension.html", "da/blog/kopier-som-markdown-udvidelse.html"),
    ("blog/copy-clean-text-from-website.html", "da/blog/ren-tekst-fra-hjemmeside.html"),
    ("blog/how-to-write-accessibility-statement.html", "da/blog/skriv-tilgaengelighedserklaering.html"),
]

def url_for(rel):
    return f"{DOMAIN}/{rel[:-5]}"  # strip .html

def add_hreflang(path, en_url, da_url, self_lang):
    with open(path, encoding="utf-8") as f:
        html = f.read()
    if 'rel="alternate" hreflang=' in html:
        return "skip-already-has"
    block = (
        f'<link rel="alternate" hreflang="da" href="{da_url}">\n'
        f'<link rel="alternate" hreflang="en" href="{en_url}">\n'
        f'<link rel="alternate" hreflang="x-default" href="{en_url}">\n'
    )
    m = re.search(r'[ \t]*<link rel="canonical"[^>]*>\n', html)
    if not m:
        return "no-canonical-found"
    html = html[:m.start()] + block + html[m.start():]
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return "ok"

changed = []
for en_rel, da_rel in PAIRS:
    en_path = os.path.join(BASE, en_rel)
    da_path = os.path.join(BASE, da_rel)
    for p in (en_path, da_path):
        if not os.path.exists(p):
            print(f"MISSING: {p}")
            sys.exit(1)
    r1 = add_hreflang(en_path, url_for(en_rel), url_for(da_rel), "en")
    r2 = add_hreflang(da_path, url_for(en_rel), url_for(da_rel), "da")
    print(f"{en_rel} <-en:{r1} da:{r2}-> {da_rel}")
    changed += [(en_path, r1), (da_path, r2)]

# --- fix wrong canonical on DA url-til-markdown post ---
fix_path = os.path.join(BASE, "da/blog/url-til-markdown-konverter.html")
with open(fix_path, encoding="utf-8") as f:
    html = f.read()
wrong = 'href="https://hermes-passiv.pages.dev/blog/url-til-markdown-konverter"'
right = 'href="https://hermes-passiv.pages.dev/da/blog/url-til-markdown-konverter"'
if wrong in html:
    # only fix inside rel="canonical"
    html = html.replace(f'rel="canonical" {wrong}', f'rel="canonical" {right}')
    with open(fix_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("canonical fixed:", fix_path)

# --- validate every touched file: hreflangs parse, canonicals correct ---
ok = True
for en_rel, da_rel in PAIRS:
    en_url, da_url = url_for(en_rel), url_for(da_rel)
    for p, self_canon in ((os.path.join(BASE, en_rel), en_url), (os.path.join(BASE, da_rel), da_url)):
        h = open(p, encoding="utf-8").read()
        if h.count('rel="alternate" hreflang="da"') != 1 or h.count('rel="alternate" hreflang="en"') != 1:
            print("VALIDATION FAIL (hreflang count):", p); ok = False
        can = re.search(r'<link rel="canonical" href="([^"]+)"', h)
        if not can or can.group(1) != self_canon:
            print("VALIDATION FAIL (canonical):", p, "->", can and can.group(1)); ok = False
print("ALL VALID" if ok else "ERRORS FOUND")
sys.exit(0 if ok else 1)
