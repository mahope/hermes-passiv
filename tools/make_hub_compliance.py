#!/usr/bin/env python3
"""Iteration 236: Hub-side "Compliance Guide Hub" — samler GDPR/NIS2/EAA/WCAG-serien.

Samme mønster som tools/make_hub_copy_clean.py (iter 235):
- site/compliance-guide.html (EN hub, extensionless canonical /compliance-guide)
- Article + FAQPage JSON-LD (separate script tags, valideret)
- Krydslinks: reciprok "More like this"-link fra alle seriens poster
- GUIDE HUB-kort på forsiden ved siden af Copy & Clean-kortet
- Sitemap: idempotent tilfoejelse, XML-valideret, unikke locs taelles
- Verificering: JSON-LD parse, interne linkmaal mod disk
"""
import json, os, re

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-25'
ROOT = '/Users/madsholstjensen/hermes-passiv'
URL = f'{BASE}/compliance-guide'
HUBFILE = 'site/compliance-guide.html'

# slug, short card title, one-line description  (49 posts)
SERIES = [
    # --- GDPR ---
    ('gdpr-agency-role', 'GDPR: The Web Agency\u2019s Role',
     'What an agency is actually responsible for under GDPR in 2026.'),
    ('gdpr-fines-2026', 'GDPR Fines in 2026', 'What the numbers mean and which tiers apply to small businesses.'),
    ('gdpr-boeder-2026', 'GDPR-b\u00f8der i 2026 (dansk)', 'B\u00f8detrappen og eksempler \u2014 hvad sm\u00e5 virksomheder reelt risikerer.'),
    ('gdpr-dpa-web-agencies', 'GDPR Data Processing Agreement', 'The DPA every web agency needs \u2014 and what it must contain.'),
    ('gdpr-vs-nis2-overlap', 'GDPR vs NIS2: The Overlap', 'Where the two regimes overlap and where they do not.'),
    ('gdpr-webbureau-da', 'GDPR-guiden 2026 (dansk)', 'Webbureauets rolle forklaret p\u00e5 dansk.'),
    ('gdpr-website-compliance-checklist', 'GDPR Website Checklist: 18 Checks', 'Every check a public site should pass before launch.'),
    ('cookie-consent-gdpr-compliance', 'Cookie Consent for Web Agencies', 'Consent banners that actually comply with GDPR.'),
    ('cookie-consent-gdpr-2026', 'Cookie-consent & GDPR (dansk)', 'Reglerne for cookiebannere forklaret p\u00e5 dansk.'),
    ('free-gdpr-document-generators', 'Free GDPR Document Generators', 'Privacy policy and template generators compared (2026).'),
    # --- NIS2 ---
    ('nis2-readiness-guide', 'NIS2-Ready? A Practical Guide', 'Is your small agency covered, and what to do about it.'),
    ('nis2-guide-da', 'NIS2-guiden 2026 (dansk)', 'S\u00e5dan bliver sm\u00e5 webbureauer klare \u2014 trin for trin.'),
    ('nis2-checklist-pdf', 'NIS2 Checklist: 25 Checks', 'What to have in place before your next audit.'),
    ('nis2-incident-report-checklist', 'NIS2 Incident Report Template', 'The 72-hour reporting duty, as a checklist you can use.'),
    ('nis2-supply-chain-security', 'NIS2 Supply Chain Security', 'Securing the vendor chain the way NIS2 expects.'),
    ('nis2-leverandoerkaede-sikkerhed', 'NIS2 leverand\u00f8rk\u00e6desikkerhed (dansk)', 'Leverand\u00f8rk\u00e6den under NIS2 \u2014 gratis guide.'),
    ('free-nis2-assessment-tools', 'Free NIS2 Assessment Tools', 'Self-assessment and gap-analysis tools compared (2026).'),
    ('gratis-nis2-vaerktoejer', 'Gratis NIS2-v\u00e6rkt\u00f8jer (dansk)', 'Selvvurdering og gap-analyse-v\u00e6rkt\u00f8jer sammenlignet.'),
    # --- EAA / accessibility ---
    ('eaa-deadline-2026', 'EAA Deadline: What Is Enforced Now', 'What the June 2025 deadline means in practice in 2026.'),
    ('eaa-enforcement-2026', 'EAA Enforcement in 2026', 'What has actually happened to non-compliant sites.'),
    ('eaa-frister-2026', 'EAA-fristerne (dansk)', 'Fristen er overskredet \u2014 s\u00e5dan h\u00e5ndh\u00e6ves loven i 2026.'),
    ('eaa-haandhaevelse-2026', 'EAA-h\u00e5ndh\u00e6velse 2026 (dansk)', 'S\u00f8m\u00e5l, b\u00f8der og hvad webbureauer skal g\u00f8re.'),
    ('eaa-accessibility-checklist', 'EAA Checklist: 10 Steps', 'A WordPress-focused walkthrough to EAA compliance.'),
    ('accessibility-audit-cost', 'Accessibility Audit Cost', 'Real 2026 prices \u2014 and how to read a quote.'),
    ('pris-tilgaengelighedsgennemgang', 'Pris p\u00e5 tilg\u00e6ngelighedsgennemgang (dansk)', 'Hvad koster en gennemgang i 2026?'),
    ('how-to-write-accessibility-statement', 'Write an Accessibility Statement', 'What a compliant statement must contain.'),
    ('free-eaa-statement-generators', 'Free Accessibility Statement Tools', 'Generators, scanners and templates compared (2026).'),
    ('gratis-eaa-saetninger', 'Gratis erkl\u00e6ringsv\u00e6rkt\u00f8jer (dansk)', 'Generator, scanner og skabeloner sammenlignet.'),
    ('accessibility-overlays-eaa', 'Overlays & the EAA (EN)', 'Why \u201cone line of code\u201d does not make a site compliant.'),
    ('tilgaengeligheds-overlays-eaa', 'Overlays & EAA (dansk)', 'Hvorfor \u201c\u00e9n linje kode\u201d ikke er compliance.'),
    ('accessibility-scanner-cli', 'Accessibility Scanning from the CLI', 'Automated checks from the command line, free.'),
    ('tilgaengelighedsscanner-cli', 'Tilg\u00e6ngelighedsscanning fra kommandolinjen (dansk)', 'Gratis CLI-guide til automatiserede tjek.'),
    ('free-accessibility-testing-tools', 'Free Accessibility Testing Tools', 'What each tool actually catches \u2014 and what it misses.'),
    ('wcag-22-aendringer', 'WCAG 2.2: What Changed (dansk)', '\u00c6ndringerne og hvad de betyder for dine klienter.'),
    # --- Platform-specific accessibility ---
    ('drupal-wcag-accessibility', 'Drupal Accessibility (WCAG/EAA)', 'Meeting WCAG 2.1 AA on Drupal sites.'),
    ('drupal-vs-typo3-accessibility', 'Drupal vs TYPO3 Accessibility', 'How the two CMSes compare out of the box.'),
    ('typo3-accessibility-bitv-check', 'TYPO3 Accessibility (BITV/EN 301 549)', 'Meeting BITV 2.0 and EN 301 549 with TYPO3.'),
    ('joomla-bitv-accessibility', 'Joomla Accessibility (BITV)', 'Joomla against BITV 2.0 and EN 301 549.'),
    ('ghost-eaa-accessibility', 'Ghost Accessibility (EAA)', 'Making Ghost publications EAA-compliant.'),
    ('magento-eaa-accessibility', 'Magento Accessibility (EAA)', 'EAA compliance for Magento stores.'),
    ('prestashop-eaa-accessibility', 'PrestaShop Accessibility (EAA)', 'EAA compliance for PrestaShop stores.'),
    ('shopify-eaa-accessibility', 'Shopify Accessibility (EAA)', 'Getting a Shopify store EAA-compliant.'),
    ('squarespace-eaa-accessibility', 'Squarespace Accessibility (EAA)', 'An EAA compliance guide for Squarespace.'),
    ('webflow-accessibility-audit', 'Webflow Accessibility Audit', 'A practical EAA audit guide for Webflow sites.'),
    ('wix-eaa-accessibility', 'Wix Accessibility (EAA)', 'An EAA compliance guide for Wix.'),
    ('wordpress-vs-wix-accessibility', 'WordPress vs Wix Accessibility', 'Compared: what each makes easy and hard.'),
    ('prestashop-vs-shopify-accessibility', 'PrestaShop vs Shopify Accessibility', 'Store platforms compared on accessibility.'),
    ('webflow-vs-squarespace-accessibility', 'Webflow vs Squarespace Accessibility', 'Site builders compared on accessibility.'),
]

assert len(SERIES) == len(set(s for s, _, _ in SERIES)), 'duplicate slugs'
for s, _, _ in SERIES:
    assert os.path.exists(os.path.join(ROOT, f'site/blog/{s}.html')), f'missing {s}'

desc = ('Forty-nine practical guides to GDPR, NIS2 and the European Accessibility '
        'Act \u2014 checklists, deadlines, fines and platform-by-platform fixes for '
        'small web agencies. Free, no signup.')

ARTICLE = {
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'Compliance Guide Hub: GDPR, NIS2 and the EAA for Web Agencies',
    'description': desc,
    'url': URL,
    'datePublished': TODAY, 'dateModified': TODAY,
    'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
}
FAQPAGE = {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    'mainEntity': [
        {'@type': 'Question', 'name': 'Who are these guides for?',
         'acceptedAnswer': {'@type': 'Answer', 'text':
            'Small web agencies, freelancers and site owners who need to know '
            'what GDPR, NIS2 and the European Accessibility Act require of them '
            '\u2014 without hiring a consultant first.'}},
        {'@type': 'Question', 'name': 'Are all guides really free?',
         'acceptedAnswer': {'@type': 'Answer', 'text':
            'Yes. Every guide is free to read, and the companion tools (the '
            'scanner CLI and Clean Copy) are free browser-based software.'}},
        {'@type': 'Question', 'name': 'Which topics are covered?',
         'acceptedAnswer': {'@type': 'Answer', 'text':
            'GDPR (cookies, DPAs, fines), NIS2 (readiness, incident reports, '
            'supply chain) and the EAA (deadlines, statements, audits) \u2014 plus '
            'platform-specific accessibility guides for WordPress, Shopify, '
            'Webflow, Wix, Squarespace and more.'}},
    ],
}
for block in (ARTICLE, FAQPAGE):
    assert block['@context'] == 'https://schema.org'
    json.loads(json.dumps(block))

cards = '\n'.join(
    f'<a class="hubcard" href="/blog/{slug}"><h3>{t}</h3><p>{d}</p></a>'
    for slug, t, d in SERIES)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Compliance Guide Hub — GDPR, NIS2 &amp; EAA Guides for Web Agencies</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="Compliance Guide Hub: GDPR, NIS2 &amp; EAA">
<meta property="og:description" content="49 practical guides to GDPR, NIS2 and the European Accessibility Act — checklists, deadlines and platform fixes for small web agencies.">
<meta property="og:image" content="{BASE}/clean-copy/og-preview.png">
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
  .hubgrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:16px; margin:1.5rem 0; }}
  .hubcard {{ display:block; padding:18px 20px; border:1px solid var(--color-border); border-radius:10px;
             color:inherit; text-decoration:none; transition:border-color .15s; }}
  .hubcard:hover {{ border-color:var(--color-accent); }}
  .hubcard h3 {{ margin:0 0 6px; font-size:1rem; color:var(--color-accent); }}
  .hubcard p {{ margin:0; font-size:0.88rem; line-height:1.5; }}
  @media (max-width:600px) {{ .hubgrid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">GUIDE HUB &middot; GDPR &middot; NIS2 &middot; EAA</div>
    <h1>The Compliance guide collection</h1>
    <p class="subtitle">Forty-nine guides, one goal: knowing exactly what GDPR, NIS2 and the European Accessibility Act demand of a small web agency or site owner \u2014 and fixing it yourself before anyone asks.</p>
    <div class="hero-cta">
      <a href="#guides" class="btn-primary">Browse the guides &rarr;</a>
      <a href="/scan" class="btn-secondary">Scan your site free</a>
    </div>
    <p class="hero-note">Updated August 2026</p>
  </div>
</header>

<section class="products" id="guides">
  <div class="container">
    <h2>All guides</h2>
    <p>Start with the regime you are working under. Every guide is standalone \u2014 no signup, no paywall.</p>
    <div class="hubgrid">
{cards}
    </div>
    <h2>Start here</h2>
    <p>Not sure where to begin? Run the free <a href="/scan" style="color:var(--color-accent);">site scan</a>, then read the checklist for the regime that applies to you: <a href="/blog/gdpr-website-compliance-checklist" style="color:var(--color-accent);">GDPR (18 checks)</a>, <a href="/blog/nis2-checklist-pdf" style="color:var(--color-accent);">NIS2 (25 checks)</a> or <a href="/blog/eaa-accessibility-checklist" style="color:var(--color-accent);">EAA (10 steps)</a>.</p>
    <h2>Questions</h2>
    {''.join(f'<div class="card" style="margin-bottom:12px;"><h3>{q["name"]}</h3><p>{q["acceptedAnswer"]["text"]}</p></div>' for q in FAQPAGE['mainEntity'])}
    <div style="text-align:center;margin-top:24px;">
      <a href="/scan" class="btn-primary">Scan your site now &rarr;</a>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
  <p><a href="/">&larr; Home</a> &middot; <a href="/scan">Free site scan</a> &middot; <a href="/copy-clean-guide">Copy &amp; Clean guides</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
</script>
</body>
</html>
'''

out = os.path.join(ROOT, HUBFILE)
with open(out, 'w') as f:
    f.write(html)

# --- validate JSON-LD ---
content = open(out).read()
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
assert len(blocks) == 2, f'expected 2 JSON-LD blocks, got {len(blocks)}'
for i, b in enumerate(blocks):
    parsed = json.loads(b)
    assert parsed['@context'] == 'https://schema.org'
    print('JSON-LD block', i + 1, 'OK (@type=%s)' % parsed['@type'])

# --- validate ALL internal link targets exist ---
missing = []
for m in re.findall(r'href="/([^"#]+)"', content):
    path = m.split('?')[0]
    if not path or path.startswith('http'):
        continue
    if (path in ('sitemap.xml', 'style.css', 'track.js')
            or os.path.exists(os.path.join(ROOT, 'site', path))
            or os.path.exists(os.path.join(ROOT, 'site', path + '.html'))):
        continue
    missing.append(path)
assert not missing, f'missing link targets: {missing}'
n_links = len(set(re.findall(r'href="/blog/[a-z0-9-]+"', content)))
print('All internal link targets exist on disk (%d unique /blog/ links)' % n_links)

# --- reciproke krydslinks i alle seriens poster (idempotent) ---
LINK_HTML = ('<div style="text-align:center;margin-top:16px;"><p>More like this: '
             '<a href="https://hermes-passiv.pages.dev/compliance-guide" '
             'style="color:var(--color-accent);">The Compliance Guide Collection '
             '(GDPR, NIS2 &amp; EAA)</a></p></div>')
added = skipped = 0
for slug, _, _ in SERIES:
    p = os.path.join(ROOT, f'site/blog/{slug}.html')
    h = open(p).read()
    if 'compliance-guide' in h:
        skipped += 1
        continue
    if '</footer>' not in h:
        raise SystemExit(f'{slug}: no </footer> anchor')
    h = h.replace('</footer>', LINK_HTML + '\n</footer>', 1)
    open(p, 'w').write(h)
    added += 1
print(f'cross-links: {added} added, {skipped} already present')

# --- forsideskort (idempotent, indsattes foerst i blog-grid) ---
idx_path = os.path.join(ROOT, 'site/index.html')
idx = open(idx_path).read()
CARD = '''<div class="product-card">
        <div class="product-badge">GUIDE HUB</div>
        <div class="product-body">
          <h3><a href="/compliance-guide" style="color:inherit;text-decoration:none;">Compliance Guide Collection</a></h3>
          <p class="product-desc">All 49 guides to GDPR, NIS2 and the European Accessibility Act \u2014 checklists, deadlines and platform-by-platform fixes.</p>
          <div class="product-details"><span class="product-meta">\U0001F4DA 49 guides</span><span class="product-meta">\u2705 All free</span></div>
          <a href="/compliance-guide" class="btn-secondary" style="margin-top:12px;">Open the hub \u2192</a>
        </div>
      </div>

      '''
if '/compliance-guide' not in idx:
    anchor = '<section class="products" id="blog">\n  <div class="container">\n    <h2>From the Blog</h2>'
    assert anchor in idx, 'index anchor missing'
    insert_after = '<div class="product-grid" style="grid-template-columns:repeat(auto-fill,minmax(300px,1fr))">\n      '
    assert insert_after in idx, 'grid anchor missing'
    idx = idx.replace(insert_after, insert_after + CARD, 1)
    open(idx_path, 'w').write(idx)
    print('frontpage card added')
else:
    print('frontpage card already present')

# --- sitemap (idempotent) ---
sm = os.path.join(ROOT, 'site/sitemap.xml')
c = open(sm).read()
before = len(set(re.findall(r'<loc>(.*?)</loc>', c)))
if URL + '</loc>' not in c:
    entry = f'<url><loc>{URL}</loc><lastmod>{TODAY}</lastmod></url>'
    c = c.replace('</urlset>', f'{entry}\n</urlset>')
else:
    print('URL already in sitemap, skipping')
c = c.replace('><url>', '>\n<url>')
open(sm, 'w').write(c)
import xml.dom.minidom
xml.dom.minidom.parse(sm)
locs = set(re.findall(r'<loc>(.*?)</loc>', c))
print(f'sitemap parses as XML, unique locs: {len(locs)} (was {before})')
assert URL in locs
dupes = before + 1 - len(locs) if URL + '</loc>' in c else before - len(locs)
print('\nDone:', out)
