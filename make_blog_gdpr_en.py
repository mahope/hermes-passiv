#!/usr/bin/env python3
"""Iteration 102: English counterpart of the Danish GDPR agency guide ->
/blog/gdpr-agency-role plus frontpage card.
Same safety pattern as iter.97-101: JSON-LD validated with json.loads,
sitemap duplicate check, internal link check."""

import json
import re
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'


def head(slug, lang, title, meta_desc, og_title, og_desc, headline):
    ld = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article', 'headline': headline,
        'description': meta_desc, 'url': f'{BASE}/blog/{slug}',
        'datePublished': TODAY, 'dateModified': TODAY,
        'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
        'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    })
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{meta_desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_desc}">
<meta property="og:url" content="{BASE}/blog/{slug}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{og_desc}">
<link rel="canonical" href="{BASE}/blog/{slug}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{ld}
</script>
<script defer src="/track.js"></script>
</head>'''


def page():
    slug = 'gdpr-agency-role'
    desc = ('GDPR for web agencies in 2026: which role does the agency play '
            '(controller or processor), cookies and consent, data processing '
            'agreements, hosting choices, the 72-hour breach rule — and a '
            '5-step checklist.')
    h = head(slug, 'en',
             'GDPR Guide 2026: The Web Agency\u2019s Role Explained',
             desc,
             'GDPR: What is a web agency responsible for?',
             'Controller or processor? Cookies, DPAs, hosting, the 72-hour rule and a 5-step checklist.',
             'GDPR Guide: The Web Agency\u2019s Role and Responsibilities in 2026')
    body = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">BLOG · GDPR</div>
    <h1>GDPR:<br>What is a web agency responsible for?</h1>
    <p class="subtitle">Agencies touch personal data every day — contact forms, analytics, newsletters, client site backups. Yet there is constant confusion over who carries the responsibility: the agency or the client? The answer depends on your role. Here are the roles explained, the five classic mistakes, and a 5-step checklist.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">Read the guide</a>
      <a href="/scan" class="btn-secondary">Scan your site free →</a>
    </div>
    <p class="hero-note">Updated August 2026 · Reading time: 7 minutes</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="roles">Two roles: controller and processor</h2>
    <p>The GDPR (Regulation 2016/679) defines two main roles, and understanding them decides who answers to the supervisory authority:</p>
    <div class="problem-cards">
      <div class="card"><h3>🎯 Controller</h3><p>The party that determines <em>why</em> and <em>in broad terms how</em> data is processed. Your client is typically the controller for their website's data: they decide the purposes (marketing, sales) and the means (CMS, newsletter tools).</p></div>
      <div class="card"><h3>🔧 Processor</h3><p>The party that processes data on the controller's instructions. An agency maintaining a client site with access to user data via admin logins, backups or staging environments is typically a processor.</p></div>
      <div class="card"><h3>⚖️ Both at once</h3><p>Many agencies are both: processor for client website data — but an independent controller for their own data (employees, own leads, analytics on their own domain).</p></div>
    </div>
    <p><strong>Why it matters:</strong> as a processor you cannot simply "follow the client's instructions" if those instructions breach the GDPR — you are jointly exposed. And without a written data processing agreement (DPA), the processing is unlawful from day one (Art. 28).</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>The five classic agency mistakes</h2>
    <p><strong>1. No data processing agreement.</strong> Art. 28 requires a written DPA BEFORE processing starts — not "we'll get to it later". This also applies to your sub-processors (hosting, e-mail).</p>
    <p><strong>2. Cookies before consent.</strong> Non-essential cookies (analytics, marketing, social plugins) may only be set after active, informed consent — and refusing must be as easy as accepting. A banner with "Accept all" and a buried reject button does not comply.</p>
    <p><strong>3. Analytics without a legal basis.</strong> A default Google Analytics setup transfers data to the US. European data protection authorities have ruled this requires extra safeguards (IP truncation, DPA, possibly proxy solutions) — otherwise traffic data is effectively personal data without a lawful basis.</p>
    <p><strong>4. Form data in email chains.</strong> Contact forms forwarded as email scatter personal data across mailboxes with no retention limit or access control. Better: deliver form submissions directly to the CMS/database with logged access.</p>
    <p><strong>5. Forgotten staging and backup environments.</strong> Copies of production sites with real user data often sit unprotected on staging domains. Either anonymise the data or lock the environments behind login — and set a deletion deadline.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>The 72-hour rule — it applies to agencies too</h2>
    <p>In case of a personal data breach, the controller must notify the supervisory authority <strong>within 72 hours</strong> where the risk is real (Art. 33). As a processor your duty is tighter: <strong>you must notify the client without undue delay</strong> after becoming aware of the breach (Art. 33(2)).</p>
    <p>In practice: if you discover a client site has been compromised, the client's 72-hour clock starts immediately — and your notification duty makes your reaction time a contractual matter. Have a written incident process ready: who detects, who assesses, who notifies, within how many hours.</p>
    <div class="problem-cards">
      <div class="card"><h3>📝 What must a DPA contain?</h3><p>Art. 28(3) lists the minimum: subject matter and duration, nature and purpose, data categories, the controller's rights and obligations, confidentiality, security measures, sub-processors, assistance with notifications, deletion/return of data and audit rights. Our e-book includes a ready-to-use template.</p></div>
      <div class="card"><h3>🌍 Hosting and third countries</h3><p>Clients increasingly ask where their site is hosted. EU/EEA hosting removes a whole chapter of transfer questions. If you use sub-processors in third countries, they must be listed in the DPA and covered by Standard Contractual Clauses.</p></div>
    </div>
  </div>
</section>

<section class="cta-section">
  <div class="container">
    <h2>A 5-step checklist for your agency</h2>
    <p class="section-intro">How to get the basics in place — without turning it into a months-long project:</p>
    <p><strong>1. Map your data processes.</strong> Which client sites do you have access to? Where do form submissions land? Which tools do you set up yourself (analytics, newsletters)? One overview goes a long way.<br>
    <strong>2. Get DPAs on every client relationship.</strong> One standard template + a short process: send at contract start, archive the signed version.<br>
    <strong>3. Clean up cookies and tracking.</strong> Consent banner with equal terms for yes/no, strictly necessary cookies only before consent, documented cookie policy.<br>
    <strong>4. Write the incident process.</strong> One page: detection → assessment → client notification (hours, not days) → help with the authority report.<br>
    <strong>5. Review annually.</strong> New clients, new tools, new sub-processors? Update the list and the agreements. A documented review counts at audits.</p>
    <div style="text-align:center;margin-top:24px;">
      <a href="/scan" class="btn-primary">Scan your site free →</a>
      &nbsp;&nbsp;
      <a href="/#products" class="btn-secondary">See the GDPR e-book →</a>
      &nbsp;&nbsp;
      <a href="/blog/nis2-readiness-guide" class="btn-secondary">NIS2 readiness guide →</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Frequently asked questions</h2>
    <div class="problem-cards">
      <div class="card"><h3>Is the agency responsible for the client's website cookies?</h3><p>As a rule, no — the client determines the purpose of tracking. BUT: if you set up the cookie, you chose the technical solution and delivered the configuration. Make sure the client actively approved the setup and that the consent solution actually works. Responsibility can be shared (Art. 26, joint controllership).</p></div>
      <div class="card"><h3>Do we need a DPA with the hosting provider too?</h3><p>Yes — hosting a website containing personal data is processing on behalf of the controller. Either the client is the direct party (typical when the client owns the hosting account), or you are the intermediary and must have your own agreement with the host, passing on the same requirements.</p></div>
      <div class="card"><h3>How big are the fines?</h3><p>Up to €20 million or 4% of global turnover for serious violations of principles; €10 million / 2% for e.g. missing DPAs or inadequate security. For small businesses, the realistic risk is usually orders, supervisory proceedings and lost trust.</p></div>
      <div class="card"><h3>Does GDPR even apply to small sites?</h3><p>Yes. GDPR has no size threshold — only exemptions for purely personal/household use. A business contact page with names and emails is personal data, whether the company has three employees or three hundred.</p></div>
      <div class="card"><h3>How does this relate to NIS2 and the EAA?</h3><p>Three tracks: GDPR protects personal data, NIS2 requires operational cybersecurity, the EAA demands accessibility. A single incident can hit several tracks at once. See our NIS2 and EAA guides for the other pillars.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Related guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">COOKIES</span><h3><a href="/blog/cookie-consent-gdpr-2026" style="color:var(--color-accent);text-decoration:none;">Cookie consent &amp; GDPR 2026</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">NIS2</span><h3><a href="/blog/nis2-guide-da" style="color:var(--color-accent);text-decoration:none;">NIS2-guiden (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">EAA</span><h3><a href="/blog/eaa-deadline-2026" style="color:var(--color-accent);text-decoration:none;">EAA deadline 2026</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">TOOLS</span><h3><a href="/free-tools" style="color:var(--color-accent);text-decoration:none;">Free compliance tools</a></h3></div>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
    <p><a href="/">← Home</a> · <a href="/scan">Free scanner</a> · <a href="/free-tools">Free tools</a> · <a href="/#blog">Blog</a></p>
</footer>
</body>
</html>'''
    return slug, h + body


def update_sitemap(slugs):
    p = f'{SITE}/sitemap.xml'
    c = open(p).read()
    add = ''.join(f'  <url><loc>{BASE}/blog/{s}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'
                  for s in slugs)
    assert all(f'/blog/{s}</loc>' not in c for s in slugs), 'slug already in sitemap'
    c = c.replace('</urlset>', add + '</urlset>')
    open(p, 'w').write(c)


CARD = '''      <div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">
        <h3><a href="/blog/gdpr-agency-role" style="color:inherit;text-decoration:none;">GDPR guide: the web agency&#8217;s role (English)</a></h3>
        <p>Controller or processor? DPA obligations, cookies, hosting, the 72-hour rule — plus a 5-step checklist for agencies.</p>
        <a href="/blog/gdpr-agency-role" class="btn-secondary" style="margin-top:12px;">Read the guide →</a>
      </div>
'''


def add_frontpage_card():
    p = f'{SITE}/index.html'
    c = open(p).read()
    if '/blog/gdpr-agency-role' in c:
        print('frontpage card already present')
        return
    anchor = '<div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">\n        <h3><a href="/blog/gdpr-webbureau-da"'
    i = c.find(anchor)
    assert i > 0, 'anchor not found in index.html'
    c = c[:i] + CARD + c[i:]
    open(p, 'w').write(c)
    print('frontpage card added')


def check_links(files):
    import os
    broken = []
    for path in files:
        html = open(path).read()
        for m in set(re.findall(r'href="(/[^"#]*?)"', html)):
            url = m.split('?')[0]
            target = ('site' + url).rstrip('/')
            if not (os.path.exists(target) or os.path.exists(target + '.html')
                    or url == '/' or os.path.exists(target + '/index.html')):
                broken.append((path, m))
    return broken


def main():
    slug, html = page()
    with open(f'{SITE}/blog/{slug}.html', 'w') as f:
        f.write(html)
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    assert blocks, 'no JSON-LD'
    for b in blocks:
        d = json.loads(b)
        assert d['@context'] == 'https://schema.org' and d['@type'] == 'Article', slug
    print(f'{slug}.html written, JSON-LD OK')
    update_sitemap([slug])
    print('sitemap updated')
    add_frontpage_card()
    broken = check_links([f'{SITE}/blog/{slug}.html', f'{SITE}/index.html'])
    print('broken internal links:', broken if broken else 'none')


if __name__ == '__main__':
    main()
