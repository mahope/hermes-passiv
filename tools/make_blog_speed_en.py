#!/usr/bin/env python3
"""Iteration 443: EN blogpost — Website Speed Test: Check Performance Without Lighthouse.

Ny post: site/blog/check-website-speed-without-lighthouse (EN).
- House-template som resten af serien (hero, steps, compare, FAQ)
- Article + FAQPage JSON-LD, valideret efter skrivning
- Sitemap opdateres kun hvis URL'en ikke allerede findes (idempotent)
- Krydslinks fra beslaegtede page-profile-posts + hubkort
"""
import json, os, re, xml.dom.minidom

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-26'
ROOT = '/Users/madsholstjensen/hermes-passiv'
URL = f'{BASE}/blog/check-website-speed-without-lighthouse'

desc = ('Run a fast website speed and health check from your terminal — no browser '
        'devtools, no Lighthouse install, no signup. A free CLI profiler scores '
        'metadata, structured data, security headers and more in seconds.')

FAQS = [
    ('Can I check website speed without running Lighthouse?',
     'Yes. The free page-profile CLI fetches the page server-side and reports response '
     'time, HTTP status, redirects and page weight signals in a few seconds — no Chrome, '
     'no npm install, no Lighthouse setup. It complements Lighthouse: use it for quick '
     'health checks and CI gates, and Lighthouse for deep rendering audits.'),
    ('Is this an alternative to Google PageSpeed Insights?',
     'It measures different things. PageSpeed Insights runs a full browser render and '
     'scores Core Web Vitals; page-profile checks what is actually served — metadata, '
     'Open Graph tags, canonical, hreflang, structured data, image alt text, HTTPS '
     'headers and redirect chains. Many teams run both: PSI monthly, page-profile on '
     'every deploy.'),
    ('Do I need to install anything?',
     'No. page-profile is a single Python file using only the standard library. Download '
     'it, run python3 page_profile.py https://example.com — works on macOS, Linux and '
     'Windows with Python 3.8+. There is also a browser version on the site that needs '
     'no download at all.'),
    ('Can I use it in CI to fail a build on a bad score?',
     'Yes. Add --json for machine-readable output and check the score field in your '
     'pipeline. The Pro tier adds batch mode over many URLs and client-ready HTML '
     'reports, but the single-URL check and JSON output are free.'),
    ('What counts as a good response time?',
     'Under about 200 ms server response (TTFB) for a static page is healthy; 200-800 ms '
     'is typical for dynamic sites; anything consistently above one second usually means '
     'caching is missing or the origin is slow. Run the check a few times — first hits '
     'include DNS and TLS setup.'),
]

ARTICLE = {
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'Website Speed Test: Check Performance Without Lighthouse',
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

faq_html = '\n    '.join(f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in FAQS)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Website Speed Test Without Lighthouse (Free CLI, 2026)</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="Website Speed Test: Check Performance Without Lighthouse">
<meta property="og:description" content="Score any URL's health and response time from the terminal in seconds — no Lighthouse, no browser, no signup.">
<meta property="og:url" content="{URL}">
<meta name="twitter:card" content="summary_large_image">
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
  pre.cmd {{
    background:#0f172a; color:#e2e8f0; padding:14px 16px; border-radius:8px;
    overflow-x:auto; font-size:0.85rem; line-height:1.6; margin:0.8rem 0;
  }}
  pre.cmd code {{ font-family:'SF Mono','Monaco','Fira Code',monospace; }}
</style>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">PERFORMANCE &middot; SEO &middot; CLI</div>
    <h1>Website speed test —<br>without Lighthouse</h1>
    <p class="subtitle">Lighthouse is great for deep audits, but it is heavy: a full browser render, dozens of seconds per run, and awkward in CI. For the everyday question — "is this page fast, valid and properly wired?" — a lightweight terminal profiler answers in seconds.</p>
    <div class="hero-cta">
      <a href="#how" class="btn-primary">Show me how &rarr;</a>
      <a href="/page-profile" class="btn-secondary">Try it in the browser</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; 4 minute read</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>When Lighthouse is the wrong tool</h2>
    <p>Full-render audits have their place. But three everyday jobs do not need them:</p>
    <div class="problem-cards">
      <div class="card"><h3>⏱️ Quick pre-deploy sanity check</h3><p>Did the new build ship a canonical tag? Is TTFB still sane? You want an answer now, not after a 40-second audit.</p></div>
      <div class="card"><h3>🤖 CI pipelines</h3><p>Installing headless Chrome in CI just to gate a deploy on a score is slow and fragile. A stdlib Python script has zero dependencies.</p></div>
      <div class="card"><h3>📊 Many URLs at once</h3><p>Lighthouse runs one page per invocation. Checking twenty landing pages means scripting around it — or one batch command.</p></div>
    </div>
  </div>
</section>

<section class="products" id="how">
  <div class="container">
    <h2>The method: one command, no install</h2>
    <p><a href="/page-profile" style="color:var(--color-accent);">page-profile</a> is a free, open CLI that fetches the page server-side and scores 21 signals: response time, redirects, title/description lengths, Open Graph tags, canonical, hreflang, JSON-LD, headings, alt text and security headers.</p>

    <h3 style="margin-top:24px;">Option A — run it in the browser (nothing to install)</h3>
    <pre class="cmd"><code>Open hermes-passiv.pages.dev/page-profile,
paste the URL, get the report instantly.</code></pre>

    <h3 style="margin-top:24px;">Option B — download the single-file CLI</h3>
    <pre class="cmd"><code>curl -O https://hermes-passiv.pages.dev/downloads/page-profile/page_profile.py
python3 page_profile.py https://example.com

# Machine-readable output for scripts and CI:
python3 page_profile.py --json https://example.com | jq .score</code></pre>

    <div class="problem-cards">
      <div class="card"><h3>⚡ Seconds, not minutes</h3><p>No headless browser. The check fetches once and parses — typical run time is under two seconds.</p></div>
      <div class="card"><h3>🔁 Track changes over time</h3><p><code>--history</code> stores past scores locally so you can see whether a release made things better or worse. Free for everyone.</p></div>
      <div class="card"><h3>🧰 Works anywhere</h3><p>Pure Python standard library — any machine with Python 3.8+, including CI containers and Raspberry Pis.</p></div>
    </div>
  </div>
</section>

<section class="products" id="options">
  <div class="container">
    <h2>How it compares</h2>
    <table class="compare">
      <thead>
        <tr><th>Tool</th><th>Setup</th><th>Run time</th><th>Best for</th></tr>
      </thead>
      <tbody>
        <tr><td>Lighthouse</td><td>Chrome / Node</td><td>30-60 s</td><td>Deep render audits, Core Web Vitals</td></tr>
        <tr><td>PageSpeed Insights</td><td>None (web)</td><td>~30 s</td><td>Field data, lab scores</td></tr>
        <tr><td>curl + manual inspection</td><td>None</td><td>Seconds</td><td>One header at a time, expert eyes</td></tr>
        <tr>
          <td><a href="/page-profile" style="color:var(--color-accent);">page-profile</a></td>
          <td>Single Python file</td>
          <td>&lt; 2 s</td>
          <td>Everyday health checks, CI gates, batch runs</td>
        </tr>
      </tbody>
    </table>
    <p>They answer different questions. Use Lighthouse when you need rendered diagnostics; use page-profile when you need a fast, repeatable verdict you can put in a pipeline.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Frequently asked questions</h2>
    <div class="problem-cards">
    {faq_html}
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/page-profile" class="btn-primary">Profile your page free &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Related: <a href="/blog/technical-seo-check-website" style="color:var(--color-accent);">Technical SEO check</a> &middot; <a href="/blog/meta-tag-checker" style="color:var(--color-accent);">Meta tag checker</a> &middot; <a href="/blog/http-headers-reference" style="color:var(--color-accent);">HTTP headers reference</a> &middot; <a href="/blog/accessibility-scanner-cli" style="color:var(--color-accent);">Accessibility scanner CLI</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/"> &larr; Home</a> &middot; <a href="/page-profile">page-profile</a> &middot; <a href="/free-tools">Free tools</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});document.addEventListener('click',function(ev){{var a=ev.target&&ev.target.closest?ev.target.closest('a[href]'):null;if(!a)return;var h=a.getAttribute('href')||'';var m=h.match(/^\\/(scan|clean-copy-tool|page-profile|site-icons|text-diff|url-to-markdown|free-tools|compliance-report)(\\.html)?(#[^#]*)?$/);if(!m)return;try{{navigator.sendBeacon('/api/track',new Blob([JSON.stringify({{path:p,event:'cta-'+m[1]}})],{{type:'application/json'}}));}}catch(e){{}}}},true);}}catch(e){{}}}})();
</script>
</body>
</html>
'''

out = os.path.join(ROOT, 'site/blog/check-website-speed-without-lighthouse.html')
with open(out, 'w') as f:
    f.write(html)

# --- validate JSON-LD ---
content = open(out).read()
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
assert len(blocks) == 2, f'expected 2 JSON-LD blocks, got {len(blocks)}'
for i, b in enumerate(blocks):
    parsed = json.loads(b)
    assert parsed['@context'] == 'https://schema.org', parsed['@context']
    print('JSON-LD block', i + 1, 'OK (@type=%s)' % parsed['@type'])

# --- validate internal link targets exist ---
for ref in [
    'site/page-profile.html',
    'site/blog/technical-seo-check-website.html',
    'site/blog/meta-tag-checker.html',
    'site/blog/http-headers-reference.html',
    'site/blog/accessibility-scanner-cli.html',
    'site/free-tools.html',
]:
    p = os.path.join(ROOT, ref)
    assert os.path.exists(p), p
print('All internal link targets exist')

# --- sitemap (idempotent) ---
sm = os.path.join(ROOT, 'site/sitemap.xml')
c = open(sm).read()
if URL + '</loc>' not in c:
    entry = f'<url><loc>{URL}</loc><lastmod>{TODAY}</lastmod></url>'
    c = c.replace('</urlset>', f'{entry}</urlset>')
else:
    print('URL already in sitemap, skipping')
c = c.replace('><url>', '>\\n<url>')
open(sm, 'w').write(c)
xml.dom.minidom.parse(sm)
print('sitemap parses as XML,', c.count('<loc'), 'urls')

# --- reciprocal cross-links from related posts ---
def add_related(path, slug, label):
    x = open(path).read()
    if slug in x:
        return False
    x = x.replace('</body>', '<div style="text-align:center;margin-top:16px;"><p>Related: <a href="' + URL + '" style="color:var(--color-accent);">' + label + '</a></p></div>\\n</body>', 1)
    open(path, 'w').write(x)
    return True

for path, label in [
    ('site/blog/technical-seo-check-website.html', 'Website speed test without Lighthouse'),
    ('site/blog/meta-tag-checker.html', 'Website speed test without Lighthouse'),
    ('site/blog/accessibility-scanner-cli.html', 'Website speed test without Lighthouse'),
]:
    full = os.path.join(ROOT, path)
    changed = add_related(full, 'check-website-speed-without-lighthouse', label)
    print(f'{path}: {"cross-linked" if changed else "already linked"}')

print('\\nDone:', out)