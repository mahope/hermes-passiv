#!/usr/bin/env python3
"""add_ai_cta.py — add a compact Compliance-AI CTA strip to blog pages.

Idempotent: pages already containing 'ai-cta' are skipped. Inserts the strip
right after the existing .blog-tool-cta (if present) or right after
</header>. The link points at /compliance-ai and is tracked automatically by
the existing cta-click listener? No — that listener only matches tool paths,
so we also inject a tiny inline beacon for clicks on this link.

The strip is `btn-secondary`, never `btn-primary`: it is a promo, and
`tools/check_first_action.py` judges every one of the 189 banner pages on it
(measured 4/10: this script and `add_top_cta_495.py` together made 330 banner
buttons outrank the article's own action). Label and button come from
`tools/ai_cta.json` so the generator cannot promise a working assistant while
`available` is false — the strings below used to hardcode "practical answer in
seconds" and 🤖, which `check_ai_cta_honesty.py` forbids on all 188 pages.

Usage: python3 tools/add_ai_cta.py            # EN + DA blog dirs
"""
import glob
import json
import os
import re
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SANDHED = json.loads(
    (Path(ROOT) / "tools" / "ai_cta.json").read_text(encoding="utf-8"))
_VARIANT = "on" if SANDHED["available"] else "off"
EN = SANDHED[_VARIANT]["en"]["label"]
DA = SANDHED[_VARIANT]["da"]["label"]
KNAP_EN = SANDHED[_VARIANT]["en"]["button"]
KNAP_DA = SANDHED[_VARIANT]["da"]["button"]

CTA_EN = (
    '<div class="blog-tool-cta ai-cta">'
    '<span class="btc-label">{label}</span> '
    '<a href="/compliance-ai" class="btn-secondary ai-cta-link" data-track="ai-cta">{knap}</a>'
    '</div>'
)
CTA_DA = (
    '<div class="blog-tool-cta ai-cta">'
    '<span class="btc-label">{label}</span> '
    '<a href="/da/compliance-ai" class="btn-secondary ai-cta-link" data-track="ai-cta">{knap}</a>'
    '</div>'
)

BEACON = (
    "<script>(function(){try{document.addEventListener('click',function(ev){"
    "var a=ev.target&&ev.target.closest?ev.target.closest('.ai-cta-link'):null;"
    "if(!a)return;var p=location.pathname.replace(/\\.html$/,'')||'/';"
    "try{navigator.sendBeacon('/api/track',new Blob([JSON.stringify({path:p,event:'ai-cta'})],"
    "{type:'application/json'}));}catch(e){}},true);}catch(e){}})();</script>"
)


def page_done(html):
    return 'class="blog-tool-cta ai-cta"' in html


def has_beacon(html):
    return "event:'ai-cta'" in html or 'event:"ai-cta"' in html


def process(path, cta_html):
    with open(path, encoding='utf-8') as f:
        html = f.read()
    changed = False
    if not page_done(html):
        m = re.search(r'<div class="blog-tool-cta(?! ai-cta)".*?</div>', html)
        if m:
            html = html[:m.end()] + '\n' + cta_html + html[m.end():]
        else:
            # fall back: after </header>
            if '</header>' not in html:
                print(f'  SKIP (no header/tool-cta): {path}')
                return False
            html = html.replace('</header>', '</header>\n' + cta_html, 1)
        changed = True
    if not has_beacon(html):
        if '</body>' not in html:
            print(f'  SKIP (no </body>): {path}')
            return False
        html = html.replace('</body>', BEACON + '\n</body>', 1)
        changed = True
    if changed:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        return True
    return False


def main():
    n = 0
    for path in sorted(glob.glob(os.path.join(ROOT, 'site/blog/*.html'))):
        if process(path, CTA_EN.format(label=EN, knap=KNAP_EN)):
            n += 1
    for path in sorted(glob.glob(os.path.join(ROOT, 'site/da/blog/*.html'))):
        if process(path, CTA_DA.format(label=DA, knap=KNAP_DA)):
            n += 1
    print(f'Updated {n} pages.')


if __name__ == '__main__':
    main()
