#!/usr/bin/env python3
"""Generate blog post: EAA Compliance Scanner Desktop — offline WCAG 2.1 AA scanning"""

import os, hashlib, json
from datetime import datetime

BLOG_DIR = 'site/blog'
SLUG = 'eaa-compliance-scanner-desktop'
TITLE = 'EAA Compliance Scanner Desktop — Free, Offline WCAG 2.1 AA Scanner for macOS, Linux & Windows'
DESC = 'A free, native desktop app for EAA / WCAG 2.1 AA accessibility scanning. Offline-capable with batch scanning and PDF reports. Available for macOS, Linux, and Windows.'

POST = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:image" content="https://hermes-passiv.pages.dev/desktop-icon.png">
<meta property="og:type" content="article">
<meta property="og:url" content="https://hermes-passiv.pages.dev/blog/{SLUG}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="https://hermes-passiv.pages.dev/blog/{SLUG}">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"TechArticle","headline":"{TITLE}","description":"{DESC}","datePublished":"{datetime.utcnow().strftime('%Y-%m-%d')}","author":{{"@type":"Organization","name":"Mahope"}}}}
</script>
</head>
<body>
<main class="container" style="max-width:720px">
  <nav style="margin-bottom:2rem"><a href="/">&larr; Home</a> · <a href="/blog">Blog</a></nav>
  <article>
    <h1>{TITLE}</h1>
    <p class="meta" style="color:var(--color-text-muted)">{datetime.utcnow().strftime('%B %d, %Y')} · 4 min read</p>

    <p>Accessibility compliance doesn't have to mean expensive SaaS tools or slow cloud-based scanners. The <strong>EAA Compliance Scanner Desktop</strong> is a free, native desktop application that runs every WCAG 2.1 AA rule right on your machine — no accounts, no internet, no limits.</p>

    <p>It's built for developers, QA engineers, and compliance teams who need to check sites <strong>before they go live</strong>, run batch audits, or integrate accessibility into CI/CD pipelines without hitting API rate limits.</p>

    <h2>What It Does</h2>
    <p>The desktop app applies the same 22 WCAG 2.1 AA rules as our CLI and web-based scanner, but in a native interface with features designed for daily use:</p>
    <ul>
      <li><strong>Single-page scan</strong> — paste a URL, get results in seconds with pass/fail per rule, issue counts (errors, warnings, notices), and an overall score.</li>
      <li><strong>Whole-site crawl</strong> — scan up to 200 same-origin pages with live progress and a per-page findings breakdown. Average score and most frequent issue types are summarized automatically.</li>
      <li><strong>One-click PDF reports</strong> — save scan results as formatted PDF reports for documentation, sharing, or compliance records.</li>
      <li><strong>Batch scanning (Pro)</strong> — scan a list of URLs in sequence with progress tracking plus aggregate stats (average score, total errors, failure rate per URL).</li>
      <li><strong>CSV / JSON export (Pro)</strong> — export individual or batch results for spreadsheet analysis, dashboards, or programmatic consumption.</li>
    </ul>

    <h2>Why a Desktop App?</h2>
    <p>Most accessibility scanners today are either web-based (meaning your page data passes through their servers) or cloud APIs that charge per scan. The desktop app is different:</p>
    <ul>
      <li><strong>Fully offline</strong> — scans run locally. Page data never leaves your machine. Great for internal sites, staging environments, and air-gapped networks.</li>
      <li><strong>No rate limits</strong> — scan as many pages as you like, as fast as your machine can handle.</li>
      <li><strong>No accounts</strong> — download and run. Free tier doesn't need signup. Pro only needs a license key when you're ready.</li>
      <li><strong>Cross-platform</strong> — native builds for macOS (Apple Silicon + Intel), Linux (AppImage + .deb), and Windows (installer + portable).</li>
    </ul>

    <h2>Platform Breakdown</h2>
    <h3>macOS</h3>
    <p>Native builds for both Apple Silicon (M1/M2/M3/M4) and Intel Macs. Comes as DMG and ZIP. Note: the app is not signed with an Apple Developer ID, so on first launch right-click and select <strong>Open</strong> to bypass the unidentified-developer gate.</p>

    <h3>Linux</h3>
    <p>AppImage (universal, works on any distro) and .deb (Debian/Ubuntu). The AppImage needs <code>chmod +x</code> on first use. No runtime dependencies beyond what Electron bundles.</p>

    <h3>Windows</h3>
    <p>NSIS installer for permanent install and a portable .exe that runs from any folder — USB sticks, build agents, CI runners. No admin rights needed for the portable version.</p>

    <h2>Free vs Pro</h2>
    <table style="width:100%;border-collapse:collapse;margin:1rem 0">
      <tr><th style="text-align:left;padding:8px;border-bottom:1px solid #333">Feature</th><th style="text-align:left;padding:8px;border-bottom:1px solid #333">Free</th><th style="text-align:left;padding:8px;border-bottom:1px solid #333">Pro</th></tr>
      <tr><td style="padding:8px;border-bottom:1px solid #222">Single-page scan</td><td style="padding:8px;border-bottom:1px solid #222">✓ Unlimited</td><td style="padding:8px;border-bottom:1px solid #222">✓ Unlimited</td></tr>
      <tr><td style="padding:8px;border-bottom:1px solid #222">Whole-site crawl</td><td style="padding:8px;border-bottom:1px solid #222">✓ Up to 200 pages</td><td style="padding:8px;border-bottom:1px solid #222">✓ Unlimited</td></tr>
      <tr><td style="padding:8px;border-bottom:1px solid #222">PDF reports</td><td style="padding:8px;border-bottom:1px solid #222">✓</td><td style="padding:8px;border-bottom:1px solid #222">✓</td></tr>
      <tr><td style="padding:8px;border-bottom:1px solid #222">Batch scanning</td><td style="padding:8px;border-bottom:1px solid #222">—</td><td style="padding:8px;border-bottom:1px solid #222">✓</td></tr>
      <tr><td style="padding:8px;border-bottom:1px solid #222">CSV / JSON export</td><td style="padding:8px;border-bottom:1px solid #222">—</td><td style="padding:8px;border-bottom:1px solid #222">✓</td></tr>
      <tr><td style="padding:8px;border-bottom:1px solid #222">Crawl depth</td><td style="padding:8px;border-bottom:1px solid #222">200 pages</td><td style="padding:8px;border-bottom:1px solid #222">Unlimited</td></tr>
      <tr><td style="padding:8px">Price</td><td style="padding:8px">Free (MIT)</td><td style="padding:8px">$19/year <span style="color:var(--color-text-muted);font-size:13px">(coming soon)</span></td></tr>
    </table>

    <h2>Download</h2>
    <p>All builds are available on the <a href="/downloads">downloads page</a>. Or build from source:</p>
    <code>git clone https://github.com/mahope/hermes-passiv<br>cd hermes-passiv/desktop<br>npm install<br>npm start</code>

    <p>CI/CD teams can also run the same engine via <a href="/downloads">CLI with pip</a> or <a href="/downloads">npm</a>, or through the <a href="/downloads">GitHub Actions workflow</a> template.</p>

    <h2>What the Scanner Checks</h2>
    <p>The engine covers all 22 WCAG 2.1 AA success criteria that can be automated including:</p>
    <ul>
      <li>Image alt text presence and emptiness</li>
      <li>Heading structure (h1-h6 hierarchy)</li>
      <li>Link text quality and redundancy</li>
      <li>Form input labels and aria-label usage</li>
      <li>Color contrast (WCAG 2.1 AA ratios for text and non-text)</li>
      <li>Language attribute on html element</li>
      <li>Viewport meta tag for responsive scaling</li>
      <li>Frame/iframe title attributes</li>
      <li>Video/audio element captions and transcripts</li>
      <li>Table headers and scope attributes</li>
      <li>ARIA landmark roles and duplicates</li>
      <li>Landmark nesting and complementary roles</li>
      <li>Tabindex values (positive values are flagged)</li>
      <li>Accesskey attribute usage (duplicates and conflicts)</li>
      <li>Empty buttons and links in navigation</li>
      <li>Abbreviation elements with title attributes</li>
      <li>Blockquote with correct cite attribute</li>
      <li>Description list (dl/dt/dd) structure</li>
      <li>Figure/figcaption pairing</li>
      <li>Cite element usage in blockquotes</li>
      <li>Label-for association with form controls</li>
      <li>Skip-navigation link presence</li>
    </ul>

    <p>Automated checks catch roughly 30–40% of accessibility issues. For full EAA conformance, pair with manual testing — see our <a href="/scan">free online scan tool</a> and <a href="/">compliance guides</a>.</p>

    <h2>Licensing</h2>
    <p>The free tier is MIT-licensed and open source. Pro requires an annual license key ($19/year). License keys will be issued through Lemon Squeezy once payment integration is live. <a href="/downloads">Check the downloads page</a> for current availability.</p>

    <p><a href="/downloads" class="btn-primary" style="display:inline-block;padding:12px 28px;margin:8px 0;text-decoration:none;border-radius:8px">⬇ Download the Desktop App →</a></p>

  </article>
</main>
<footer class="site-footer"><div class="container"><a href="/">&larr; hermes-passiv.pages.dev</a></div></footer>
<script defer src="/track.js"></script>
</body>
</html>
"""

if __name__ == '__main__':
    os.makedirs(BLOG_DIR, exist_ok=True)
    path = os.path.join(BLOG_DIR, f'{SLUG}.html')
    with open(path, 'w') as f:
        f.write(POST)
    print(f'Wrote {path}')