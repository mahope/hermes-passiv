#!/usr/bin/env python3
"""Generate site/blog/index.html — the real blog overview page.
Run from repo root: python3 tools/make_blog_index.py
Deterministic: reads every post's <title> + <meta description>, groups by topic."""
import glob, html, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
BASE = 'https://hermes-passiv.pages.dev'

CATS = [
    ('Accessibility & EAA',
     ['accessib', 'eaa', 'wcag', 'bitv', 'joomla', 'drupal', 'typo3', 'ghost-',
      'magento', 'prestashop', 'shopify', 'squarespace', 'webflow', 'wix',
      'wordpress-vs', 'contrast-checker', 'text-on-image']),
    ('GDPR, NIS2 & Cookie Compliance',
     ['gdpr', 'nis2', 'cookie', 'cmp-', 'compliance', 'dpa-web']),
    ('Copy, Tables & Markdown Tools',
     ['copy-', 'copy_', 'table', 'html-to-markdown', 'html-tabel', 'markdown',
      'paste-', 'url-to-markdown', 'building-html']),
    ('SEO & Website Health',
     ['redirect', 'ssl', 'http-headers', 'meta-tag', 'open-graph',
      'technical-seo', 'seo', 'zip-before-release', 'release-integrity']),
    ('Dev Tools & Guides',
     ['bug-report', 'desktop-website-monitor', 'developer-text-tools',
      'cli', 'vscode', 'obsidian', 'chrome', 'github-action']),
]

def categorize(slug):
    for name, keys in CATS:
        if any(k in slug for k in keys):
            return name
    return 'Dev Tools & Guides'

def extract(path):
    s = open(path, encoding='utf-8', errors='ignore').read()
    t = re.search(r'<title>(.*?)</title>', s, re.S)
    og = re.search(r'<meta property="og:title" content="(.*?)"\s*/?>', s)
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S | re.I)
    d = re.search(r'<meta name="description" content="(.*?)"\s*/?>', s)
    # prefer og:title: full titles, no <br> truncation issues; fall back to h1
    src = og or h1 or t
    title = html.unescape(re.sub(r'<[^>]+>|<br\s*/?>', ' ', src.group(1))).strip() if src else ''
    title = re.sub(r'\s+', ' ', title)
    # strip trailing " | ..." suffixes some titles carry
    title = re.split(r'\s*[|—]\s*(?:Mahope|Hermes|Clean Copy)', title)[0].strip()
    desc = html.unescape(d.group(1).strip()) if d else ''
    return title, desc

def main():
    posts = []
    for f in sorted(glob.glob(os.path.join(SITE, 'blog', '*.html'))):
        slug = os.path.basename(f)[:-5]
        if slug == 'index':
            continue
        title, desc = extract(f)
        if not title:
            print(f'WARN no title: {slug}', file=sys.stderr)
            continue
        posts.append((slug, title, desc, categorize(slug)))

    da_posts = []
    for f in sorted(glob.glob(os.path.join(SITE, 'da', 'blog', '*.html'))):
        slug = os.path.basename(f)[:-5]
        title, _ = extract(f)
        if title:
            da_posts.append((slug, title))

    grouped = {}
    for p in posts:
        grouped.setdefault(p[3], []).append(p)

    out = ["""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blog — All Guides &amp; Free Tool Tutorials</title>
<meta name="description" content="Every guide on this site: EU compliance (EAA, GDPR, NIS2), accessibility audits, copy-paste tools, SEO checks and developer tooling. All free, no signup.">
<meta property="og:type" content="website">
<meta property="og:title" content="Blog — All Guides &amp; Free Tool Tutorials">
<meta property="og:description" content="EU compliance, accessibility, copy-paste tools, SEO checks and developer tooling — every guide in one place. All free.">
<meta property="og:url" content="{base}/blog">
<meta property="og:image" content="{base}/cover.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{base}/blog">
<link rel="alternate" type="text/plain" href="/llms.txt" title="Machine-readable tool catalog">
<link rel="stylesheet" href="/style.css">
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">BLOG</div>
    <h1>All Guides &amp;<br>Tutorials</h1>
    <p class="subtitle">{n} English guides on EU compliance, accessibility, copy-paste workflows, SEO checks and free developer tools — plus {nda} Danish guides.</p>
  </div>
</header>
<main class="container" style="max-width:900px;padding-top:32px">
""".format(base=BASE, n=len(posts), nda=len(da_posts))]

    for name, _keys in CATS:
        items = grouped.get(name, [])
        if not items:
            continue
        anchor = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        out.append(f'<section id="{anchor}">\n<h2>{name}</h2>\n<ul style="list-style:none">\n')
        for slug, title, desc, _c in items:
            out.append(
                f'<li style="margin-bottom:20px">'
                f'<a href="/blog/{slug}" style="color:var(--color-accent);font-weight:600;text-decoration:none;font-size:1.02rem">{html.escape(title)}</a>'
                + (f'<br><span style="color:var(--color-text-muted);font-size:0.88rem">{html.escape(desc[:180])}</span>' if desc else '')
                + '</li>\n')
        out.append('</ul>\n</section>\n')

    if da_posts:
        out.append('<section id="dansk">\n<h2>Danske guides</h2>\n<ul style="list-style:none">\n')
        for slug, title in da_posts:
            out.append(f'<li style="margin-bottom:14px"><a href="/da/blog/{slug}" style="color:var(--color-accent);text-decoration:none">{html.escape(title)}</a></li>\n')
        out.append('</ul>\n</section>\n')

    out.append("""<p style="margin:48px 0;text-align:center"><a href="/" class="btn-secondary">&larr; Home</a> &nbsp; <a href="/free-tools" class="btn-primary">Browse all free tools &rarr;</a></p>
</main>
<footer style="padding:32px 24px;text-align:center;color:var(--color-text-muted)">
  <p>&copy; 2026 Mahope &middot; <a href="/">Hermes Passiv</a></p>
</footer>
</body>
</html>
""")

    dest = os.path.join(SITE, 'blog', 'index.html')
    open(dest, 'w', encoding='utf-8').write(''.join(out))
    total = sum(len(v) for v in grouped.values())
    print(f'Wrote {dest}: {total} EN posts in {len([k for k,_ in CATS if grouped.get(k)])} sections + {len(da_posts)} DA posts')
    # coverage check
    missing = [name for name, _k in CATS if not grouped.get(name)]
    if missing:
        print('Empty categories:', missing)

if __name__ == '__main__':
    main()
