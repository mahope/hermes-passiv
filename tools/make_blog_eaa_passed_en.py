#!/usr/bin/env python3
"""Iteration 286: EN search-entry page — EAA deadline has passed (enforcement angle).

site/blog/eaa-deadline-passed.html: targets English queries like
"eaa deadline passed", "eaa enforcement", "what now european accessibility act".
House template, Article + FAQPage JSON-LD, idempotent sitemap add,
internal-link check, cross-link from the existing eaa-enforcement-2026 post.
"""
import json, os, re, xml.dom.minidom

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-25'
ROOT = '/Users/madsholstjensen/hermes-passiv'
SITE = os.path.join(ROOT, 'site')
SLUG = 'eaa-deadline-passed'
URL = f'{BASE}/blog/{SLUG}'

desc = ('The European Accessibility Act deadline of 28 June 2026 has passed. Here is '
        'what that means in practice: who can complain, what fines look like across '
        'the EU, and how to check and fix your website for free in one afternoon.')

FAQS = [
    ('Has the European Accessibility Act deadline really passed?',
     'Yes. New services had to comply with the EAA by 28 June 2026. The requirements '
     'are now in force, and national market surveillance authorities across the EU can '
     'enforce them against businesses that fall short.'),
    ('Who can complain about my website?',
     'Any user can lodge a complaint with the national supervisory authority — free of '
     'charge. An inaccessible checkout flow or booking form is exactly the kind of '
     'service the law covers, so any visitor can realistically trigger a review.'),
    ('How big are the fines for missing accessibility?',
     'It depends on the member state. France can issue fines in the tens of thousands '
     'of euros; others start with formal notices and deadlines. The expensive part is '
     'rarely the fine itself — it is forced rework under time pressure.'),
    ('How long does it take to check my website?',
     'A first pass with a free scanner tool takes minutes. The typical problems — missing '
     'alt text, low contrast, form fields without labels — are often fixed in a single '
     'afternoon. A full audit takes longer, but automated tools catch around 80% of '
     'common complaint points.'),
    ('Does the EAA apply to my small online shop?',
     'Micro-enterprises with fewer than ten employees are only partially covered, but '
     'most shops sit above that line — and payment providers and marketplaces increasingly '
     'require accessibility regardless. Check before assuming you are exempt.'),
]

ARTICLE = {
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'EAA deadline passed — what does it mean for your website now?',
    'description': desc,
    'url': URL,
    'datePublished': TODAY, 'dateModified': TODAY,
    'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
}
FAQPAGE = {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    'mainEntity': [{'@type': 'Question', 'name': q,
                    'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQS],
}
for block in (ARTICLE, FAQPAGE):
    assert block['@context'] == 'https://schema.org', block['@context']
    json.loads(json.dumps(block))

faq_html = '\n'.join(f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in FAQS)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EAA Deadline Passed — What Now? (Guide 2026)</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="EAA Deadline Passed — What Now?">
<meta property="og:description" content="The European Accessibility Act deadline went by on 28 June 2026. See what the rules mean now, and how to check your website for free in an afternoon.">
<meta property="og:url" content="{URL}">
<link rel="canonical" href="{URL}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{json.dumps(ARTICLE, ensure_ascii=False)}
</script>
<script type="application/ld+json">
{json.dumps(FAQPAGE, ensure_ascii=False)}
</script>
<script defer src="/track.js"></script>
<style>
  .compare {{ width:100%; border-collapse:collapse; font-size:0.92rem; margin:1.5rem 0; }}
  .compare th, .compare td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--color-border); vertical-align:top; }}
  .compare th {{ border-bottom:2px solid var(--color-border); }}
</style>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">ACCESSIBILITY &middot; EAA &middot; EU</div>
    <h1>The deadline was 28 June 2026.<br>What does that mean now?</h1>
    <p class="subtitle">The European Accessibility Act is no longer a future rule. The requirements apply, the complaint channel is open, and authorities can enforce. Good news: most errors on ordinary websites can be found and fixed for free — in one afternoon.</p>
    <div class="hero-cta">
      <a href="/scan" class="btn-primary">Check your site free &rarr;</a>
      <a href="#now" class="btn-secondary">See what the rules mean</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; 5 minute read</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>The short version of life after the deadline</h2>
    <div class="problem-cards">
      <div class="card"><h3>&#9878;&#65039; The rules already apply</h3><p>New services had to comply from 28 June 2026. Existing services follow by 2030 — but the earlier you fix issues, the less risk you carry.</p></div>
      <div class="card"><h3>&#128226; Anyone can complain</h3><p>The complaint route to your national authority costs users nothing. An inaccessible checkout or booking step is exactly what the law covers.</p></div>
      <div class="card"><h3>&#128295; Fixes are cheap now</h3><p>Missing alt text, low contrast and unlabeled form fields are found automatically. Fixing them yourself beats receiving a formal notice.</p></div>
    </div>
  </div>
</section>

<section class="products" id="now">
  <div class="container">
    <h2>Three steps to get on top of it</h2>

    <h3 style="margin-top:24px;">1. Scan your site for free</h3>
    <p>The <a href="/scan" style="color:var(--color-accent);">free EAA scanner</a> reviews any URL for classic WCAG failures: contrast, alt text, labels, language declaration and more. You get a report with concrete findings — no account needed.</p>

    <h3 style="margin-top:24px;">2. Fix the most common errors</h3>
    <table class="compare">
      <thead><tr><th>Typical finding</th><th>How to fix it</th></tr></thead>
      <tbody>
        <tr><td>Image without alt text</td><td>Short descriptive text in the <code>alt</code> attribute; decorative images get empty alt</td></tr>
        <tr><td>Text contrast below 4.5:1</td><td>Darker text or lighter background — checked with the free <a href="/contrast-checker" style="color:var(--color-accent);">contrast checker</a></td></tr>
        <tr><td>Form field without label</td><td>Connect a <code>&lt;label for&gt;</code> to the field</td></tr>
        <tr><td>No language declaration</td><td><code>&lt;html lang="en"&gt;</code> on every page</td></tr>
      </tbody>
    </table>

    <h3 style="margin-top:24px;">3. Document it</h3>
    <p>Your site needs an <a href="/accessibility-statement-generator" style="color:var(--color-accent);">accessibility statement</a>. The generator produces a correctly structured statement in minutes — including the complaint-channel link.</p>

    <div class="problem-cards">
      <div class="card"><h3>&#9989; Free all the way</h3><p>Scanner, contrast checker and statement generator cost nothing and require no account.</p></div>
      <div class="card"><h3>&#127470;&#127475; WCAG-based</h3><p>The reports use the same WCAG criteria enforcement measures against.</p></div>
      <div class="card"><h3>&#128274; No data collected</h3><p>You scan your own site — results are not sent anywhere.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Frequently asked questions</h2>
    <div class="problem-cards">
      {faq_html}
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/scan" class="btn-primary">Start with a free scan &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Related: <a href="/blog/eaa-enforcement-2026" style="color:var(--color-accent);">EAA enforcement explained</a> &middot; <a href="/blog/eaa-accessibility-checklist" style="color:var(--color-accent);">EAA checklist</a> &middot; <a href="/blog/eaa-deadline-2026" style="color:var(--color-accent);">EAA deadlines</a> &middot; <a href="/da/blog/eaa-frist-hvad-nu" style="color:var(--color-accent);">Dansk version</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">Home</a> &middot; <a href="/scan">EAA scanner</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/blog/eaa-accessibility-checklist">EAA checklist</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
</script>
</body>
</html>
'''

out = os.path.join(SITE, f'blog/{SLUG}.html')
with open(out, 'w') as f:
    f.write(html)

content = open(out).read()
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
assert len(blocks) == 2, f'expected 2 JSON-LD blocks, got {len(blocks)}'
for i, b in enumerate(blocks):
    parsed = json.loads(b)
    assert parsed['@context'] == 'https://schema.org', parsed['@context']
    print('JSON-LD block', i + 1, 'OK (@type=%s)' % parsed['@type'])

refs = re.findall(r'href="(/[^"#]+)"', content)
missing = []
for ref in set(refs):
    if ref.startswith('/api') or ref in ('/sitemap.xml', '/style.css', '/track.js'):
        continue
    p = os.path.join(ROOT, 'site', ref.lstrip('/') + '.html')
    if not os.path.exists(p):
        missing.append(ref)
assert not missing, missing
print('All internal link targets exist:', len(set(refs)), 'checked')
bad = [r for r in refs if r.endswith('.html')]
assert not bad, bad
print('No .html links')

# --- sitemap (idempotent) ---
sm = os.path.join(ROOT, 'site/sitemap.xml')
c = open(sm).read()
if URL + '</loc>' not in c:
    entry = f'<url>\n    <loc>{URL}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <priority>0.8</priority>\n  </url>\n  '
    c = c.replace('</urlset>', entry + '</urlset>')
else:
    print('URL already in sitemap, skipping')
open(sm, 'w').write(c)
xml.dom.minidom.parse(sm)
print('sitemap parses as XML,', c.count('<loc'), 'urls')

# --- cross-link from existing EN enforcement post ---
src_path = os.path.join(SITE, 'blog/eaa-enforcement-2026.html')
x = open(src_path).read()
if SLUG not in x:
    x = x.replace('</body>', '<div style="text-align:center;margin-top:16px;"><p>Related: <a href="' + URL + '" style="color:var(--color-accent);">EAA deadline passed — what now?</a></p></div>\n</body>', 1)
    open(src_path, 'w').write(x)
    print('eaa-enforcement-2026: related line added')
else:
    print('eaa-enforcement-2026 already linked')

# --- llms.txt ---
ll = os.path.join(ROOT, 'site/llms.txt')
l = open(ll).read()
if '/blog/' + SLUG not in l:
    open(ll, 'a').write('- [EAA deadline passed — what now?](https://hermes-passiv.pages.dev/blog/eaa-deadline-passed): English guide on what the June 2026 accessibility deadline means in practice, with free checking tools.\n')
    print('llms.txt: entry added')
else:
    print('llms.txt already up to date')

print('\nDone:', out)
