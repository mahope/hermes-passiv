#!/usr/bin/env python3
"""Iteration 115: English SEO blog 'open graph checker' as search entrance
to /page-profile. Same pattern as make_blog_seo_en.py: JSON-LD validated,
sitemap dup-check, internal link check."""
import json, re, os
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

slug = 'open-graph-checker'
desc = ('Check any URL\'s Open Graph and Twitter Card tags free: og:title, '
        'og:description, og:image and twitter:card. See how your link looks '
        'when shared on LinkedIn, Facebook and X — no signup.')
ld = json.dumps({
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'Open Graph Checker — see how your links look when shared (free)',
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
<title>Open Graph Checker — Test How Your Links Look When Shared (Free)</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="Open Graph Checker — free, one URL in, preview out">
<meta property="og:description" content="Check og:title, og:description, og:image and twitter:card on any URL. See your LinkedIn/Facebook/X share preview before you post.">
<meta property="og:image" content="{BASE}/cover.jpg">
<meta property="og:url" content="{BASE}/blog/{slug}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Open Graph Checker — free, one URL in, preview out">
<meta name="twitter:description" content="Check og:title, og:description, og:image and twitter:card on any URL.">
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
    <div class="badge">BLOG &middot; SOCIAL SHARING</div>
    <h1>Open Graph Checker<br>See Your Link Before You Post It</h1>
    <p class="subtitle">Every time someone shares your page on LinkedIn, Facebook, X, Slack or Teams, the platform builds a card from your Open Graph tags &mdash; silently. Check what it sees before you hit publish.</p>
    <div class="hero-cta">
      <a href="#why-it-breaks" class="btn-primary">Read the guide</a>
      <a href="/page-profile" class="btn-secondary">Check a URL now &rarr;</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; 5 minute read</p>
  </div>
</header>

<section class="problem" id="why-it-breaks">
  <div class="container">
    <h2 id="what-open-graph-is">What Open Graph tags actually do</h2>
    <p>When a URL is pasted into a social network or chat app, that platform's crawler fetches your page and reads four meta tags from the <code>og:</code> namespace: <strong>og:title</strong>, <strong>og:description</strong>, <strong>og:image</strong> and <strong>og:url</strong>. X (Twitter) uses its parallel <code>twitter:card</code> tags, falling back to Open Graph when they are missing.</p>
    <p>If the tags are absent, the platform guesses &mdash; usually badly: no image, a truncated title, or a description scraped from random page text. If the tags are wrong, the wrong card shows, and the platforms cache aggressively: fixing the tags today does not fix cards already cached.</p>
    <div class="problem-cards">
      <div class="card"><h3>🖼️ The image problem</h3><p>The single most common failure: og:image missing, relative instead of absolute, smaller than 200&times;200 px, or pointing at a URL behind auth. Any of these renders no image at all.</p></div>
      <div class="card"><h3>🗄️ The cache problem</h3><p>Facebook and LinkedIn cache share data for days. Fix tags first, then use each platform's debugger to force a re-scrape — otherwise you're testing stale data.</p></div>
      <div class="card"><h3>✅ One check, all tags</h3><p>A good checker validates every tag at once: presence, sizes, absolute URLs, image dimensions and twitter:card fallbacks.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="how-to-check">How to check your Open Graph tags</h2>
    <p><strong>Option A — automated (recommended).</strong> Paste your URL into the <a href="/page-profile" style="color:var(--color-accent);">free page profiler</a>. Alongside the full technical SEO report you get the complete Open Graph and Twitter Card picture: which tags exist, whether og:image resolves and meets size minimums, and whether twitter:card has sane fallbacks.</p>
    <p><strong>Option B — view-source.</strong> Open your page, view source, and search for <code>og:</code>. You should find at least title, description, image and url inside the &lt;head&gt;. Remember: tags rendered client-side by JavaScript are invisible to most platform crawlers — they must be in the raw HTML response.</p>
    <p><strong>Option C — platform debuggers.</strong> After fixing, run Facebook's Sharing Debugger and LinkedIn's Post Inspector to refresh their caches and confirm the new card. Each platform caches independently; clearing one does not clear the others.</p>
    <div class="problem-cards">
      <div class="card"><h3>📏 Image rules of thumb</h3><p>1200&times;630 px, absolute URL, under ~8 MB, publicly reachable, PNG or JPEG. That passes every major platform's requirements with margin.</p></div>
      <div class="card"><h3>✍️ Title and description lengths</h3><p>Cards truncate around 55–65 characters of title and ~110–160 of description depending on platform. Put the important words first.</p></div>
      <div class="card"><h3>🧩 Per-page tags</h3><p>One shared set of OG tags across a whole site means every shared article shows the homepage card. Generate them per template — most CMSs do this with one plugin or one meta partial.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="mistakes">Five Open Graph mistakes that kill click-through</h2>
    <p><strong>1. Missing og:image entirely.</strong> Posts without images get dramatically less engagement on every platform. This is the highest-value fix on this list.</p>
    <p><strong>2. Relative image URLs.</strong> <code>&lt;meta property="og:image" content="/img/cover.jpg"&gt;</code> works in a browser but renders nothing in a share preview. Always absolute.</p>
    <p><strong>3. JavaScript-injected tags.</strong> Platform crawlers mostly do not execute JS. If your SPA sets OG tags at runtime, shares show nothing. Render tags server-side.</p>
    <p><strong>4. Identical tags everywhere.</strong> Template-level defaults leaking onto articles make every share look identical — and users stop clicking.</p>
    <p><strong>5. Forgetting twitter:card.</strong> Without <code>twitter:card</code> (usually <code>summary_large_image</code>), X falls back to a small plain summary. One line fixes it.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Frequently asked questions</h2>
    <div class="problem-cards">
      <div class="card"><h3>Is this checker free?</h3><p>Yes. The <a href="/page-profile" style="color:var(--color-accent);">page profiler</a> runs in your browser, needs no account, and covers Open Graph, Twitter Cards plus the rest of your page's technical health in the same report.</p></div>
      <div class="card"><h3>Why does my fix not show up yet?</h3><p>Platform caches. Use Facebook's Sharing Debugger and LinkedIn's Post Inspector to force a re-scrape after deploying changes. Until then you are looking at old cached data.</p></div>
      <div class="card"><h3>Do OG tags affect SEO rankings?</h3><p>Not directly — Google reads title/meta description, not og: tags, for ranking. But share previews drive clicks and traffic, and a broken preview quietly kills that channel.</p></div>
      <div class="card"><h3>What about WhatsApp, Slack, iMessage?</h3><p>All read Open Graph tags. The same rules apply: absolute image URLs, server-rendered tags, sensible dimensions.</p></div>
      <div class="card"><h3>Danish version?</h3><p>There is a <a href="/blog/teknisk-seo-tjek-hjemmeside" style="color:var(--color-accent);">Danish technical SEO guide</a> and a fully Danish profiler at /da/page-profile.</p></div>
      <div class="card"><h3>Can I automate this in CI?</h3><p>Yes — the companion Python CLI outputs JSON for any URL, so a pipeline can fail a build when og:image goes missing. See the <a href="/blog/technical-seo-check-website" style="color:var(--color-accent);">technical SEO check guide</a>.</p></div>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/page-profile" class="btn-primary">Check your URL free &rarr;</a>
      &nbsp;&nbsp;
      <a href="/blog/technical-seo-check-website" class="btn-secondary">Full technical SEO guide &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Related guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">SEO</span><h3><a href="/blog/technical-seo-check-website" style="color:var(--color-accent);text-decoration:none;">Technical SEO check for your website</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">SEO · DA</span><h3><a href="/blog/teknisk-seo-tjek-hjemmeside" style="color:var(--color-accent);text-decoration:none;">Teknisk SEO-tjek af din hjemmeside (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">A11Y</span><h3><a href="/blog/accessibility-scanner-cli" style="color:var(--color-accent);text-decoration:none;">Accessibility scanning from the command line</a></h3></div>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
  <p><a href="/">&larr; Home</a> &middot; <a href="/scan">Free scanner</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
</body>
</html>'''

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

# ── Internal links: EN page-profile footer + cross-link from SEO article ──
pp = f'{SITE}/page-profile.html'
pc = open(pp).read()
if '/blog/open-graph-checker' not in pc:
    anchor = '<a href="/blog/technical-seo-check-website">Technical SEO guide</a>'
    assert anchor in pc, 'footer anchor not found'
    pc = pc.replace(anchor,
        anchor + ' · <a href="/blog/open-graph-checker">Open Graph checker</a>')
    open(pp, 'w').write(pc)
    print('EN page-profile footer link added')
else:
    print('EN page-profile link already present')

seo = f'{SITE}/blog/technical-seo-check-website.html'
sc = open(seo).read()
if '/blog/open-graph-checker' not in sc:
    k = sc.rfind('</section>')
    xlink = ('\n<section class="products">\n  <div class="container">\n'
             '    <h2>Sharing links on social media?</h2>\n'
             '    <p>Check how your links render when shared: '
             '<a href="/blog/open-graph-checker" style="color:var(--color-accent);">Open Graph checker guide</a>.</p>\n'
             '  </div>\n</section>\n')
    sc = sc[:k] + xlink + sc[k:]
    open(seo, 'w').write(sc)
    print('SEO article cross-link added')
else:
    print('cross-link already present')

# ── Link check ──────────────────────────────────────────────────────
broken = []
for path in [f'{SITE}/blog/{slug}.html', pp, seo]:
    h = open(path).read()
    for m in set(re.findall(r'href="(/[^"#]*?)"', h)):
        url = m.split('?')[0]
        t = ('site' + url).rstrip('/')
        if not (os.path.exists(t) or os.path.exists(t + '.html')
                or url == '/' or os.path.exists(t + '/index.html')):
            broken.append((path, m))
print('broken internal links:', broken if broken else 'none')
print('Done.')
