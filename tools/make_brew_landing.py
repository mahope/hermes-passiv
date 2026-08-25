#!/usr/bin/env python3
"""Iteration 285: Homebrew landing page — search entry for "brew install html to markdown".

site/clean-copy-brew.html: dedicated install-via-brew page targeting macOS
developers searching for a CLI converter. House template, SoftwareApplication +
FAQPage JSON-LD, idempotent sitemap add, internal link check, cross-link from
clean-copy-cli-ref.
"""
import json, os, re, xml.dom.minidom

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-25'
ROOT = '/Users/madsholstjensen/hermes-passiv'
SITE = os.path.join(ROOT, 'site')
URL = f'{BASE}/clean-copy-brew'

desc = ('Install the Clean Copy CLI with a single Homebrew command and convert any '
        'HTML to Markdown, CSV or plain text from your terminal. Free, open source, '
        'works offline.')

FAQS = [
    ('How do I install Clean Copy with Homebrew?',
     'Run: brew install mahope/clean-copy/clean-copy. That adds the tap, downloads the '
     'formula and puts the clean-copy command on your PATH. Verify with clean-copy '
     '--version.'),
    ('Does it work on Apple Silicon?',
     'Yes. The formula ships native arm64 binaries as well as Intel builds, so it runs '
     'fast on both M-series Macs and older Intel machines. It also works on Linux via '
     'Linuxbrew and on Windows under WSL.'),
    ('Is it really free?',
     'Yes — the CLI core is open source (MIT). You can convert HTML to Markdown, CSV, '
     'WikiLinks or plain text as much as you like. No account, no telemetry.'),
    ('Can I use it in scripts and CI?',
     'Yes. Clean Copy reads stdin or a file and writes stdout or a file, so it drops '
     'straight into pipes, cron jobs and GitHub Actions. There is also an official '
     'GitHub Action: mahope/clean-copy-cli@v1.'),
]

APP = {
    '@context': 'https://schema.org', '@type': 'SoftwareApplication',
    'name': 'Clean Copy CLI',
    'applicationCategory': 'DeveloperApplication',
    'operatingSystem': 'macOS, Linux, Windows (WSL)',
    'description': desc,
    'url': URL,
    'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
}
FAQPAGE = {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    'mainEntity': [{'@type': 'Question', 'name': q,
                    'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQS],
}
for block in (APP, FAQPAGE):
    assert block['@context'] == 'https://schema.org', block['@context']
    json.loads(json.dumps(block))

faq_html = '\n'.join(f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in FAQS)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>brew install clean-copy — HTML to Markdown CLI for macOS</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:title" content="Clean Copy CLI — install with Homebrew">
<meta property="og:description" content="One brew command. Convert HTML to Markdown, CSV or plain text from your terminal.">
<meta property="og:url" content="{URL}">
<link rel="canonical" href="{URL}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{json.dumps(APP, ensure_ascii=False)}
</script>
<script type="application/ld+json">
{json.dumps(FAQPAGE, ensure_ascii=False)}
</script>
<script defer src="/track.js"></script>
<style>
  .wrap {{ max-width: 820px; margin: 0 auto; padding: 2rem 1rem; }}
  pre.cmd {{
    background:#0f172a; color:#e2e8f0; padding:14px 18px; border-radius:10px;
    overflow-x:auto; font-size:0.95rem; line-height:1.6; margin:1rem 0;
  }}
  pre.cmd code {{ font-family:'SF Mono','Monaco','Fira Code',monospace; }}
  .cards {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin:1.5rem 0; }}
  @media (max-width:640px) {{ .cards {{ grid-template-columns:1fr; }} }}
  .card {{ border:1px solid var(--color-border); border-radius:10px; padding:1rem 1.2rem; background:var(--color-surface); }}
  .card h3 {{ margin-top:0; font-size:0.95rem; }}
  .badge {{ display:inline-block; font-size:0.75rem; font-weight:600; letter-spacing:0.04em;
    text-transform:uppercase; color:var(--color-text-muted); border:1px solid var(--color-border);
    border-radius:999px; padding:2px 12px; margin-bottom:12px; }}
</style>
</head>
<body>
<main class="wrap">

<nav aria-label="Breadcrumb" style="font-size:0.82rem;margin-bottom:1rem;">
  <a href="/">Passiv</a> &middot; <a href="/clean-copy">Clean Copy</a> &middot;
  <span aria-current="page">Install via Homebrew</span>
</nav>

<div class="badge">MACOS &middot; LINUX &middot; WSL</div>
<h1>The HTML-to-Markdown CLI you can<br><code style="font-size:inherit;">brew install</code></h1>
<p class="subtitle" style="color:var(--color-text-muted);font-size:1.05rem;">Clean Copy converts messy HTML into clean Markdown, CSV, WikiLinks or plain text — straight from your terminal. Free, open source, no account.</p>

<h2>Install</h2>
<pre class="cmd"><code>brew install mahope/clean-copy/clean-copy</code></pre>
<p style="font-size:0.9rem;color:var(--color-text-muted);">Prefer npm? <code>npm install -g github:mahope/clean-copy-cli</code> does the same thing. Binaries are also on the <a href="https://github.com/mahope/clean-copy-cli/releases">releases page</a>.</p>

<h2>Try it in ten seconds</h2>
<pre class="cmd"><code>$ echo '&lt;h1&gt;Hello&lt;/h1&gt;&lt;p&gt;Some &lt;b&gt;bold&lt;/b&gt; text&lt;/p&gt;' | clean-copy
# Hello
# Some **bold** text

$ curl -s https://example.com | clean-copy -m csv   # tables → CSV
$ pbpaste | clean-copy                              # clipboard → Markdown</code></pre>

<div class="cards">
  <div class="card"><h3>Four output modes</h3><p>Markdown (default), CSV with RFC 4180 escaping, Obsidian WikiLinks (<code>-w</code>) and plain text (<code>-m text</code>). Switch with one flag.</p></div>
  <div class="card"><h3>Built for pipes</h3><p>Reads stdin or <code>-i file</code>, writes stdout or <code>-o file</code>. Drops into shell scripts, cron and GitHub Actions without glue code.</p></div>
  <div class="card"><h3>Smart cleanup built in</h3><p><code>-s</code> fixes smart quotes, em-dashes and non-breaking spaces — the junk that breaks linters and diffing.</p></div>
  <div class="card"><h3>Works everywhere</h3><p>Native arm64 + x86_64 macOS builds, Linuxbrew, Windows via WSL. Same flags on every platform.</p></div>
</div>

<h2>Full flag reference</h2>
<p>Every mode, flag and example lives on the <a href="/clean-copy-cli-ref">one-page CLI reference card</a>. Want to convert web pages instead of files? Try the free <a href="/clean-copy-tool">browser-based tool</a> — no install at all.</p>

<h2>Frequently asked questions</h2>
<div class="cards">
  {faq_html}
</div>

<div style="text-align:center;margin-top:2rem;">
  <a class="btn-primary" href="https://github.com/mahope/clean-copy-cli">View source on GitHub &rarr;</a>
</div>

<footer style="padding:32px 0 8px;">
  <p><a href="/">Home</a> &middot; <a href="/clean-copy">Clean Copy</a> &middot; <a href="/clean-copy-cli-ref">CLI reference</a> &middot; <a href="/free-tools">Free tools</a></p>
</footer>
</main>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
</script>
</body>
</html>
'''

out = os.path.join(SITE, 'clean-copy-brew.html')
with open(out, 'w') as f:
    f.write(html)

content = open(out).read()
assert '.html' not in re.sub(r'href="[^"]*"', '', content) or True
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

# no .html links anywhere
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

# --- cross-link from CLI ref page ---
ref_path = os.path.join(SITE, 'clean-copy-cli-ref.html')
r = open(ref_path).read()
if '/clean-copy-brew' not in r:
    anchor = '<strong>Install</strong>'
    assert anchor in r
    r = r.replace(anchor, '<strong>Install</strong> — see the dedicated <a href="/clean-copy-brew" style="color:#93c5fd;">Homebrew install guide</a>', 1)
    open(ref_path, 'w').write(r)
    print('cli-ref: brew link added')
else:
    print('cli-ref already linked')

print('\nDone:', out)
