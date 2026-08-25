#!/usr/bin/env python3
"""add_ai_cta.py — add a compact Compliance-AI CTA strip to blog pages.

Idempotent: pages already containing 'ai-cta' are skipped. Inserts the strip
right after the existing .blog-tool-cta (if present) or right after
</header>. The link points at /compliance-ai and is tracked automatically by
the existing cta-click listener? No — that listener only matches tool paths,
so we also inject a tiny inline beacon for clicks on this link.

Usage: python3 tools/add_ai_cta.py            # EN + DA blog dirs
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EN = ('Ask any EU compliance question — EAA, NIS2 or GDPR — '
      'and get a practical answer in seconds:')
DA = ('Stil et spørgsmål om EU-compliance — EAA, NIS2 eller GDPR — og få et '
      'praktisk svar på få sekunder:')

CTA_EN = (
    '<div class="blog-tool-cta ai-cta">'
    '<span class="btc-label">{label}</span> '
    '<a href="/compliance-ai" class="btn-primary ai-cta-link" data-track="ai-cta">🤖 Ask the Compliance AI →</a>'
    '</div>'
)
CTA_DA = (
    '<div class="blog-tool-cta ai-cta">'
    '<span class="btc-label">{label}</span> '
    '<a href="/da/compliance-ai" class="btn-primary ai-cta-link" data-track="ai-cta">🤖 Spørg Compliance-AI’en →</a>'
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
        if process(path, CTA_EN.format(label=EN)):
            n += 1
    for path in sorted(glob.glob(os.path.join(ROOT, 'site/da/blog/*.html'))):
        if process(path, CTA_DA.format(label=DA)):
            n += 1
    print(f'Updated {n} pages.')


if __name__ == '__main__':
    main()
