#!/usr/bin/env python3
"""Insert 'Related guide' block linking to the EN site-health hub into all
guides/*-accessibility-check.html pages (idempotent)."""
import glob, re, sys

HUB = "https://hermes-passiv.pages.dev/blog/site-health-github-actions"
BLOCK = (
    '<aside class="cta-scan" data-hub-link style="background:#f0fdf4;border:1px solid #bbf7d0;'
    'border-radius:10px;padding:18px 22px;margin:28px 0;">\n'
    '  <strong>Related guide: monitor your site for free</strong>\n'
    '  <p style="margin:8px 0 12px;font-size:14px;color:#374151;">Fixing accessibility once is not '
    'enough &mdash; regressions creep back with every theme update. Our free GitHub Actions stack '
    'watches uptime, SSL, security headers and compliance daily, runs smoke tests after every '
    'deploy, and validates visitor bug reports &mdash; no SaaS subscription.</p>\n'
    '  <a href="/blog/site-health-github-actions" style="color:#15803d;font-weight:600;'
    'text-decoration:none;">Read the site-health stack guide &rarr;</a>\n'
    '</aside>\n'
)

changed = skipped = already = 0
for f in sorted(glob.glob("guides/*-accessibility-check.html")):
    html = open(f, encoding="utf-8").read()
    if 'data-hub-link' in html:
        already += 1
        continue
    # insert right after the iter313 cta-scan aside if present, else before </body> scripts
    m = re.search(r'</aside>\s*\n(?=<h2>)', html)
    if m:
        html = html[:m.end()] + BLOCK + html[m.end():]
    else:
        m2 = re.search(r'<script>\n\(function\(\)\{try\{if\(navigator\.doNotTrack', html)
        if not m2:
            print(f"NO ANCHOR: {f}", file=sys.stderr); skipped += 1; continue
        html = html[:m2.start()] + BLOCK + html[m2.start():]
    open(f, "w", encoding="utf-8").write(html)
    changed += 1

print(f"changed={changed} already={already} skipped={skipped}")
