#!/usr/bin/env python3
"""Iteration 114: English SEO blog pendant 'technical SEO check website'
as search entrance to /page-profile. Pattern from make_blog_da_trio2.py:
JSON-LD validated, sitemap dup-check, internal link check."""
import json, re, os
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

slug = 'technical-seo-check-website'
desc = ('How to run a technical SEO check on any website in 2 minutes: title tags, '
        'Open Graph, JSON-LD structured data, heading hierarchy, alt text, canonical '
        'URLs and security headers. Free tool, no signup.')
ld = json.dumps({
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'Technical SEO Check for Your Website — free guide with score',
    'description': desc,
    'url': f'{BASE}/blog/{slug}',
    'datePublished': TODAY, 'dateModified': TODAY,
    'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
})

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Technical SEO Check for Your Website — Free Guide with Score</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="Technical SEO Check for Your Website (free, in 2 minutes)">
<meta property="og:description" content="Title tags, Open Graph, JSON-LD, headings, alt text and security headers — one URL in, report out. Free and no signup.">
<meta property="og:image" content="{BASE}/cover.jpg">
<meta property="og:url" content="{BASE}/blog/{slug}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Technical SEO Check for Your Website (free, in 2 minutes)">
<meta name="twitter:description" content="Title tags, Open Graph, JSON-LD, headings, alt text and security headers — one URL in, report out.">
<link rel="canonical" href="{BASE}/blog/{slug}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{ld}
</script>
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">BLOG &middot; TECHNICAL SEO</div>
    <h1>Technical SEO Check<br>for Your Website</h1>
    <p class="subtitle">What Google and social platforms actually see when they visit your page &mdash; and how to check it for free in two minutes, without installing anything.</p>
    <div class="hero-cta">
      <a href="#the-check" class="btn-primary">Read the guide</a>
      <a href="/page-profile" class="btn-secondary">Run the health check now &rarr;</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; 6 minute read</p>
  </div>
</header>

<section class="problem" id="the-check">
  <div class="container">
    <h2 id="what-is-technical-seo">What is technical SEO &mdash; and why does it come first?</h2>
    <p>Technical SEO is everything a machine checks about your page before the content itself gets judged. It is the foundation: if it crumbles, the world's best copy cannot save your rankings. The most common failures are also the easiest to find &mdash; and fix.</p>
    <p>The seven things every page should pass:</p>
    <p>&bull; <strong>Title tag and meta description</strong> &mdash; what shows in Google's results. Missing them means Google guesses.<br>
    &bull; <strong>Open Graph tags</strong> &mdash; control how your link looks when shared on LinkedIn, Facebook and in chats.<br>
    &bull; <strong>JSON-LD structured data</strong> &mdash; tells machines what the page IS (article, product, organization).<br>
    &bull; <strong>Heading hierarchy</strong> &mdash; one h1, logical order. Both screen readers and crawlers navigate by it.<br>
    &bull; <strong>Alt text on images</strong> &mdash; accessibility AND image search in one.<br>
    &bull; <strong>Canonical URL</strong> &mdash; stops duplicate content from splitting your ranking signals.<br>
    &bull; <strong>Security headers</strong> (HTTPS, CSP and friends) &mdash; a trust signal that matters more every year.</p>
    <div class="problem-cards">
      <div class="card"><h3>⏱️ Two minutes</h3><p>You don't need to read source code. An automated check hands you the list of what's missing — sorted by weight.</p></div>
      <div class="card"><h3>🆓 Free</h3><p>No account, no scan quota, no email required. Paste a URL, read the report, fix what's red.</p></div>
      <div class="card"><h3>📱 Any platform</h3><p>WordPress, Shopify, Webflow, Wix, Squarespace or hand-written HTML — the tool sees your page the way Google does.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="how-to">How to run the check, step by step</h2>
    <p><strong>Step 1 — Run an automated profile.</strong> Open the <a href="/page-profile" style="color:var(--color-accent);">free page profiler</a>, paste your URL, and get a 21-point score covering metadata, social tags, structured data, headings, images, canonical/hreflang and security headers. No signup.</p>
    <p><strong>Step 2 — Read findings in priority order.</strong> The report groups issues into meta tags, social sharing (Open Graph/Twitter), structured data, headings, images, canonical/hreflang and security. Start with anything marked critical &mdash; typically a missing title, description or Open Graph image.</p>
    <p><strong>Step 3 — Fix in templates, not pages.</strong> Most technical SEO problems repeat across every page built from the same template. Fix the template once and hundreds of findings disappear together.</p>
    <p><strong>Step 4 &mdash; Re-run and keep the score.</strong> Re-profile after each release. A stable or rising score is the cheapest regression test you can run &mdash; and before/after numbers are a concrete deliverable you can show a client or your boss.</p>
    <div class="problem-cards">
      <div class="card"><h3>🔍 What "critical" really means</h3><p>A missing title tag affects every search impression. A missing og:image only affects shares. Both matter — but not equally. Fix in that order.</p></div>
      <div class="card"><h3>🧩 Structured data pitfalls</h3><p>JSON-LD must parse as valid JSON and use @context https://schema.org. Two blocks in one script tag is invalid — split them. Validate after every CMS update.</p></div>
      <div class="card"><h3>🔒 Headers are cheap wins</h3><p>HSTS, X-Content-Type-Options and a CSP are one-line changes on most hosts. They rarely move rankings directly, but they compound trust signals and protect against injection.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="mistakes">The five most common technical SEO mistakes</h2>
    <p><strong>1. Duplicate titles across templates.</strong> Every product or post inheriting the same title competes with itself. Unique titles are the single highest-leverage fix.</p>
    <p><strong>2. Broken Open Graph images.</strong> A relative og:image URL renders nothing on LinkedIn. Always use absolute URLs pointing at a real, crawlable image (&ge;1200&times;630 px).</p>
    <p><strong>3. Invalid or missing structured data.</strong> Copied JSON-LD snippets that no longer parse do nothing. Validate them &mdash; silently broken markup is extremely common after redesigns.</p>
    <p><strong>4. Multiple h1s or skipped heading levels.</strong> Themes and page builders love injecting extra h1s. One h1 per page, levels in order.</p>
    <p><strong>5. Canonical pointing at the wrong host.</strong> After migrations, canonicals often still point at staging URLs &mdash; telling Google to ignore the live site. Check yours today.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Frequently asked questions</h2>
    <div class="problem-cards">
      <div class="card"><h3>Is this tool really free?</h3><p>Yes. The web profiler runs on the page, no account needed, no scan limit. There is also a zero-dependency Python CLI you can download and run against any URL, with JSON output for CI pipelines.</p></div>
      <div class="card"><h3>Does technical SEO guarantee rankings?</h3><p>No. It removes the ceiling: content and links decide how high you climb, but unresolved technical failures cap what any of it can achieve. Treat it as table stakes.</p></div>
      <div class="card"><h3>How often should I re-check?</h3><p>After every significant release, plus a quarterly sweep. Automated checks take seconds — there is no reason to let regressions sit for months.</p></div>
      <div class="card"><h3>What can't an automated check find?</h3><p>Crawl budget issues, JavaScript rendering quirks, Core Web Vitals field data and content quality all need other tools. This covers the on-page fundamentals every site should pass first.</p></div>
      <div class="card"><h3>Does it work on sites behind a login?</h3><p>The web version profiles public URLs. For authenticated pages, fetch the HTML yourself and run it through the CLI's rule engine locally.</p></div>
      <div class="card"><h3>Danish version?</h3><p>Yes — there is a <a href="/blog/teknisk-seo-tjek-hjemmeside" style="color:var(--color-accent);">Danish guide to technical SEO checks</a> and a fully Danish interface at /da/page-profile.</p></div>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/page-profile" class="btn-primary">Profile your page free &rarr;</a>
      &nbsp;&nbsp;
      <a href="/blog/teknisk-seo-tjek-hjemmeside" class="btn-secondary">Dansk version &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Related guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">SEO · DA</span><h3><a href="/blog/teknisk-seo-tjek-hjemmeside" style="color:var(--color-accent);text-decoration:none;">Teknisk SEO-tjek af din hjemmeside (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">A11Y</span><h3><a href="/blog/accessibility-scanner-cli" style="color:var(--color-accent);text-decoration:none;">Accessibility scanning from the command line</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">WCAG</span><h3><a href="/blog/wcag-22-what-changes" style="color:var(--color-accent);text-decoration:none;">WCAG 2.2: what changes and why it matters</a></h3></div>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
  <p><a href="/">&larr; Home</a> &middot; <a href="/scan">Free scanner</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
</body>
</html>'''

# ── Write + validate ────────────────────────────────────────────────
with open(f'{SITE}/blog/{slug}.html', 'w') as f:
    f.write(html)
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
assert blocks, 'no JSON-LD'
for b in blocks:
    d = json.loads(b)
    assert d['@context'] == 'https://schema.org' and d['@type'] == 'Article'
print(f'{slug}.html written, JSON-LD OK')

# ── Sitemap ─────────────────────────────────────────────────────────
p = f'{SITE}/sitemap.xml'
c = open(p).read()
assert f'/blog/{slug}</loc>' not in c, 'already in sitemap'
c = c.replace('</urlset>',
    f'  <url><loc>{BASE}/blog/{slug}</loc><lastmod>{TODAY}</lastmod>'
    f'<changefreq>weekly</changefreq><priority>0.8</priority></url>\n</urlset>')
open(p, 'w').write(c)
print('sitemap updated')

# ── Internal links: EN page-profile footer + DA article cross-link ──
pp = f'{SITE}/page-profile.html'
pc = open(pp).read()
if '/blog/technical-seo-check-website' not in pc:
    anchor = '<a href="/da/page-profile">Dansk version</a>'
    assert anchor in pc, 'footer anchor not found'
    pc = pc.replace(anchor,
        anchor + ' · <a href="/blog/technical-seo-check-website">Technical SEO guide</a>')
    open(pp, 'w').write(pc)
    print('EN page-profile footer link added')
else:
    print('EN page-profile link already present')

da = f'{SITE}/blog/teknisk-seo-tjek-hjemmeside.html'
dc = open(da).read()
if f'/blog/{slug}' not in dc:
    k = dc.rfind('</section>')
    xlink = ('\n<section class="products">\n  <div class="container">\n    <h2>Læs den på engelsk</h2>\n'
             '    <p>Engelsk udgave af samme guide: '
             f'<a href="/blog/{slug}" style="color:var(--color-accent);">Technical SEO check for your website</a>.</p>\n'
             '  </div>\n</section>\n')
    dc = dc[:k] + xlink + dc[k:]
    open(da, 'w').write(dc)
    print('DA article cross-link added')
else:
    print('DA cross-link already present')

# ── Link check ──────────────────────────────────────────────────────
broken = []
for path in [f'{SITE}/blog/{slug}.html', pp, da]:
    h = open(path).read()
    for m in set(re.findall(r'href="(/[^"#]*?)"', h)):
        url = m.split('?')[0]
        t = ('site' + url).rstrip('/')
        if not (os.path.exists(t) or os.path.exists(t + '.html')
                or url == '/' or os.path.exists(t + '/index.html')):
            broken.append((path, m))
print('broken internal links:', broken if broken else 'none')
print('Done.')
