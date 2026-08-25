#!/usr/bin/env python3
"""Inject a click-tracking beacon: logs internal clicks to tool pages as events.
Idempotent: skips files already containing 'cta-click'.
Event names are slugs of the target path (e.g. /clean-copy-tool -> cta-clean-copy-tool).
Kør: python3 tools/add_cta_tracking.py   (fra repo-roedden)
"""
import re, sys, pathlib

SNIPPET = (
    "<script>\n"
    "(function(){try{"
    "if(navigator.doNotTrack==='1')return;"
    "var p=location.pathname.replace(/\\.html$/,'')||'/';"
    "document.addEventListener('click',function(ev){"
    "var a=ev.target&&ev.target.closest?ev.target.closest('a[href]'):null;"
    "if(!a)return;var h=a.getAttribute('href')||'';"
    "var m=h.match(/^\\/(scan|clean-copy-tool|page-profile|site-icons|text-diff|url-to-markdown|free-tools|compliance-report)(\\.html)?(#[^#]*)?$/);"
    "if(!m)return;"
    "try{navigator.sendBeacon('/api/track',new Blob([JSON.stringify({path:p,event:'cta-'+m[1]})],{type:'application/json'}));}catch(e){}"
    "},true);"
    "}catch(e){}})();\n"
    "</script>"
)

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'site')
changed = skipped = 0
for f in sorted(root.rglob('*.html')):
    html = f.read_text(encoding='utf-8')
    if 'cta-click' in html or ("event:'cta-" in html):
        skipped += 1; continue
    if '</body>' not in html:
        print('NO BODY TAG:', f); continue
    idx = html.rindex('</body>')
    html = html[:idx] + SNIPPET + '\n</body>' + html[idx+len('</body>'):]

    f.write_text(html, encoding='utf-8')
    changed += 1
print(f'cta tracking injected: {changed}, already present: {skipped}')
