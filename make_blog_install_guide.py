#!/usr/bin/env python3
"""Iteration 272: Obsidian plugin install guide (EN) + BRAT deep-link.

- New: site/blog/install-obsidian-plugin-clean-copy.html — step-by-step install
  (BRAT one-liner, manual release download, zip bundle), FAQ with SoftwareApplication
  JSON-LD. Targets searches like "how to install an obsidian plugin from github".
- Updates the existing paste-guide to link the new guide and mention v1.0.7.
- Sitemap updated, JSON-LD validated, internal link check.
"""
import json, re, os
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

SLUG = 'install-obsidian-plugin-clean-copy'


def build_page():
    title = 'How to Install Clean Copy for Obsidian (BRAT, Manual & Zip)'
    desc = ('Three ways to install the free Clean Copy paste-as-Markdown plugin in '
            'Obsidian: via BRAT in one line, manually from a GitHub release, or as a '
            'zip bundle. Works on desktop and mobile.')
    ld_app = json.dumps({
        '@context': 'https://schema.org', '@type': 'SoftwareApplication',
        'name': 'Clean Copy for Obsidian',
        'applicationCategory': 'UtilitiesApplication',
        'operatingSystem': 'Obsidian 1.4+',
        'description': desc,
        'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
        'softwareVersion': '1.0.7',
        'url': f'{BASE}/clean-copy',
        'author': {'@type': 'Organization', 'name': 'Mahope'},
    }, ensure_ascii=False)
    faq = [
        ("Is it safe to install plugins from GitHub?",
         "Yes, when the release is built from a public repository you can inspect. "
         "Clean Copy's source is public at github.com/mahope/clean-copy-obsidian, "
         "each release ships exactly three files (main.js, manifest.json, styles.css), "
         "and the plugin makes no network requests — conversion runs locally."),
        ("Does this work on Obsidian mobile?",
         "The manual and zip methods do: copy the three files into your vault's "
         ".obsidian/plugins folder from any file manager, then reload the plugin list. "
         "BRAT is desktop-only, so mobile users should use the manual method."),
        ("Why isn't it in the community plugin directory yet?",
         "Submission through Obsidian's developer dashboard is pending. The build is "
         "identical either way — installing via BRAT or manually gives you the same "
         "version today, and you can switch to the directory listing once approved."),
        ("Is Pro required for basic use?",
         "No. Paste as clean Markdown, plain-text paste and clean-selection are free "
         "forever. Pro ($19/yr) only adds custom find/replace cleanup rules."),
    ]
    main_entity = [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                   for q, a in faq]
    ld_faq = json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': main_entity},
                        ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="Install the free paste-as-Markdown plugin in under a minute — BRAT, manual or zip.">
<meta property="og:image" content="{BASE}/clean-copy/og-preview.png">
<meta property="og:url" content="{BASE}/blog/{SLUG}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{BASE}/blog/{SLUG}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{ld_app}</script>
<script type="application/ld+json">{ld_faq}</script>
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">GUIDE &middot; OBSIDIAN PLUGIN</div>
    <h1>Install Clean Copy<br>for Obsidian</h1>
    <p class="subtitle">The free plugin that pastes clipboard HTML as proper Markdown — headings, links, lists, tables and code intact. Three ways to install it, all under a minute.</p>
    <div class="hero-cta">
      <a href="#brat" class="btn-primary">Fastest way (BRAT)</a>
      <a href="/blog/paste-into-obsidian-clean-markdown" class="btn-secondary">Why clean pasting matters &rarr;</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; covers v1.0.7</p>
  </div>
</header>

<section class="products" id="brat">
  <div class="container">
    <h2>Way 1 — Install with BRAT (fastest, auto-updates)</h2>
    <ol style="line-height:2;max-width:680px;">
      <li>Install <a href="https://github.com/TfTHacker/obsidian42-brat" rel="noopener">BRAT</a> from Obsidian's community plugin browser (Settings → Community plugins → Browse → search "BRAT").</li>
      <li>Open the command palette (Ctrl/Cmd+P) and run <strong>BRAT: Add a beta plugin for testing</strong>.</li>
      <li>Enter <code>mahope/clean-copy-obsidian</code> and confirm.</li>
      <li>Enable <strong>Clean Copy</strong> in Settings → Community plugins.</li>
    </ol>
    <p>BRAT watches the repository's releases, so every future version arrives automatically.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Way 2 — Manual install from the GitHub release</h2>
    <ol style="line-height:2;max-width:680px;">
      <li>Open the <a href="https://github.com/mahope/clean-copy-obsidian/releases/latest" rel="noopener">latest release page</a>.</li>
      <li>Download <code>main.js</code>, <code>manifest.json</code> and <code>styles.css</code>.</li>
      <li>Create the folder <code>&lt;your-vault&gt;/.obsidian/plugins/clean-copy-obsidian/</code> and put all three files inside it.</li>
      <li>Restart Obsidian or reload community plugins, then enable <strong>Clean Copy</strong>.</li>
    </ol>
    <p>This method also works on Obsidian mobile — use any file manager to reach the vault folder.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Way 3 — One-click zip bundle</h2>
    <p>The same three files are bundled as a single download:</p>
    <p style="text-align:center;"><a href="/downloads/clean-copy-obsidian-v1.0.7.zip" class="btn-primary">Download v1.0.7 zip</a></p>
    <p>Unzip it into <code>&lt;vault&gt;/.obsidian/plugins/</code> so you end up with a <code>clean-copy-obsidian</code> folder containing the three files, then enable the plugin as above.</p>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>First run</h2>
    <p>Copy any formatted text from the web, then in Obsidian press <strong>Ctrl/Cmd+Shift+V</strong> (or run "Paste as clean Markdown" from the command palette). Headings arrive as <code>#</code>, links as <code>[text](url)</code>, tables as pipe tables, entities decoded. Two more commands live in the palette: <em>Paste as plain text</em> and <em>Clean selection</em> for tidying text already in a note.</p>
    <div style="text-align:center;margin-top:20px;">
      <a href="/clean-copy" class="btn-primary">About Clean Copy &rarr;</a>
      &nbsp;&nbsp;
      <a href="/clean-copy-tool" class="btn-secondary">Try it in the browser first &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Frequently asked questions</h2>
    <div class="problem-cards">
'''
    for q, a in faq:
        html += f'      <div class="card"><h3>{q}</h3><p>{a}</p></div>\n'
    html += '''    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/blog/paste-into-obsidian-clean-markdown" class="btn-secondary">&larr; Paste Into Obsidian Without the Formatting Mess</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Related: <a href="/blog/html-to-markdown-converter" style="color:var(--color-accent);">HTML to Markdown converter</a> &middot; <a href="/blog/html-to-markdown-cli" style="color:var(--color-accent);">HTML to Markdown from the terminal</a> &middot; <a href="/da/blog/indsæt-i-obsidian-ren-markdown" lang="da">Dansk guide</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">&larr; Home</a> &middot; <a href="/clean-copy">Clean Copy</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
<script defer src="/track.js"></script>
</body>
</html>'''
    return html


def update_sitemap():
    p = f'{SITE}/sitemap.xml'
    c = open(p).read()
    url = f'{BASE}/blog/{SLUG}'
    if f'<loc>{url}</loc>' in c:
        print('sitemap: already present')
        return
    add = (f'  <url><loc>{url}</loc><lastmod>{TODAY}</lastmod>'
           f'<changefreq>weekly</changefreq><priority>0.8</priority></url>\n')
    c = c.replace('</urlset>', add + '</urlset>')
    open(p, 'w').write(c)
    print('sitemap updated')


def patch(path, old, new):
    c = open(path).read()
    if new in c:
        print(f'{path}: already patched')
        return
    assert old in c, f'anchor NOT found in {path}: {old[:70]!r}'
    open(path, 'w').write(c.replace(old, new))
    print(f'{path}: patched')


def check_links(files):
    broken = []
    for path in files:
        html = open(path).read()
        for m in sorted(set(re.findall(r'href="(/[^"#:]*?)"', html))):
            url = m.split('?')[0]
            t = ('site' + url).rstrip('/')
            if not (os.path.exists(t) or os.path.exists(t + '.html') or url == '/'
                    or os.path.exists(t + '/index.html')):
                broken.append((path, m))
    return broken


def main():
    out = f'{SITE}/blog/{SLUG}.html'
    page = build_page()
    with open(out, 'w') as f:
        f.write(page)
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL)
    for b in blocks:
        d = json.loads(b)
        assert d['@context'] == 'https://schema.org', d['@context']
    print(f'{out} written, JSON-LD OK ({len(blocks)} blocks)')

    update_sitemap()

    # Cross-link from the existing paste guide
    patch(f'{SITE}/blog/paste-into-obsidian-clean-markdown.html',
          '<footer style="padding:32px 24px;">',
          '<p><a href="/blog/install-obsidian-plugin-clean-copy">How to install the plugin: BRAT, manual &amp; zip &rarr;</a></p>\n<footer style="padding:32px 24px;">')
    # Mention v1.0.7 explicitly in the paste-guide FAQ answer
    cpath = f'{SITE}/blog/paste-into-obsidian-clean-markdown.html'
    c = open(cpath).read()
    old = 'download <code>main.js</code> and <code>manifest.json</code> from the release'
    new = ('download <code>main.js</code>, <code>manifest.json</code> and <code>styles.css</code> '
           'from the latest release (v1.0.7) — see the full <a href="/blog/install-obsidian-plugin-clean-copy" '
           'style="color:var(--color-accent);">install guide</a>')
    if new not in c:
        assert old in c, 'v1.0.7 anchor missing'
        open(cpath, 'w').write(c.replace(old, new))
        print('paste-guide: v1.0.7 note added')

    files = [out, cpath]
    broken = check_links(files)
    print('broken internal links:', broken if broken else 'none')

    sx = open(f'{SITE}/sitemap.xml').read()
    assert '</urlset>' in sx
    print('sitemap URLs:', sx.count('<loc>'))
    print('\nDone.')


if __name__ == '__main__':
    main()
