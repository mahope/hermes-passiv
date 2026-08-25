#!/usr/bin/env python3
"""Fix malformed canonical link tags: missing closing '>' on
<link rel="canonical" href="..."> (line ends after the quote).
Also fix the identical malformation on og:url / hreflang / sitemap links if present.
Idempotent: only rewrites lines matching the broken pattern.
Kør: python3 tools/fix_canonical.py   (fra repo-roedden)
"""
import re, sys, pathlib

# <link rel="canonical" href="https://..."   (missing >)  -> add >
BROKEN = re.compile(r'(<link\s+(?:(?!>)\s)*href="[^"]*")\s*$')
VALID = re.compile(r'<link\s[^>]*>')


def fix_line(line: str) -> str:
    stripped = line.rstrip('\n')
    m = BROKEN.search(stripped)
    if m and '<link' in stripped:
        return line.replace(m.group(1), m.group(1) + '>', 1)
    return line


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'site')
    changed = files = 0
    for f in sorted(root.rglob('*.html')):
        html = f.read_text(encoding='utf-8')
        new = '\n'.join(fix_line(l) + ('\n' if l.endswith('\n') else '') for l in html.splitlines(keepends=False)) + ('\n' if html.endswith('\n') else '')
        # simpler: apply regex on whole text, per-line anchored
        new2 = re.sub(r'(<link\s+(?:(?!>)[^>])*?)\s*\n', lambda m: m.group(1).rstrip() + '>\n', html)
        if new2 != html:
            f.write_text(new2, encoding='utf-8')
            files += 1
            changed += sum(1 for a, b in zip(html.split('\n'), new2.split('\n')) if a != b)
    print(f'canonical fixed: {changed} lines in {files} files')


if __name__ == '__main__':
    main()
