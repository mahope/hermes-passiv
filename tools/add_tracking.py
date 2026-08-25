#!/usr/bin/env python3
"""Inject a privacy-friendly pageview beacon into every HTML page that lacks it.
Idempotent: skips files already containing /api/track."""
import re, sys, pathlib

SNIPPET = """<script>
(function(){try{if(navigator.doNotTrack==='1')return;
var p=location.pathname.replace(/\\.html$/,'')||'/';
fetch('/api/track',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({path:p}),keepalive:true}).catch(function(){});});}catch(e){}
</script>"""
# fix: snippet above has a stray ");" — build cleanly below
SNIPPET = ("<script>\n"
"(function(){try{"
"if(navigator.doNotTrack==='1')return;"
"var p=location.pathname.replace(/\\.html$/,'')||'/';"
"fetch('/api/track',{method:'POST',headers:{'Content-Type':'application/json'},"
"body:JSON.stringify({path:p}),keepalive:true}).catch(function(){});"
"}catch(e){}})();\n"
"</script>")

root = pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'site')
changed = skipped = 0
for f in sorted(root.rglob('*.html')):
    if '/da/' in str(f) and False: pass
    html = f.read_text(encoding='utf-8')
    if 'api/track' in html:
        skipped += 1; continue
    if '</body>' not in html:
        print('NO BODY TAG:', f); continue
    html = html.replace('</body>', SNIPPET + '\n</body>', 1)
    f.write_text(html, encoding='utf-8')
    changed += 1
print(f'injected: {changed}, already tracked: {skipped}')
