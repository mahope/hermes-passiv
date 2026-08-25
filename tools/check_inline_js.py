#!/usr/bin/env python3
"""JS-syntax-tjek af inline <script>-blokke (uden src=) i alle lokale site-HTML-filer.
Skriver hver blok til midlertidig .js og koerer node --check.
Kør: python3 tools/check_inline_js.py   (fra repo-roedden)"""
import re, sys, subprocess, tempfile, os, pathlib

SITE = pathlib.Path(__file__).resolve().parent.parent / 'site'

def check_file(path):
    html = path.read_text('utf-8', 'ignore')
    problems = []
    for m in re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S | re.I):
        body = m.group(1)
        if not body.strip():
            continue
        # spring JSON-LD og templates over
        if re.search(r'application/ld\+json', html[m.start():m.start()+120], re.I):
            continue
        if '<%' in body or '{{' in body:
            continue
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
            f.write(body)
            tmp = f.name
        try:
            r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
            if r.returncode != 0:
                first = [l for l in r.stderr.strip().splitlines() if 'SyntaxError' in l or 'Error' in l]
                problems.append((path.name, (first[0] if first else 'syntax error')[:100]))
        finally:
            os.unlink(tmp)
    return problems

def main():
    files = sorted(SITE.rglob('*.html'))
    bad = []
    for f in files:
        bad += check_file(f)
    print(len(files), 'html files checked')
    print('problems:', len(bad))
    for name, err in bad:
        print(f'{name}: {err}')
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
