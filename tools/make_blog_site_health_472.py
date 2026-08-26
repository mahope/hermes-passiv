#!/usr/bin/env python3
"""Iteration 472: "Monitor your website from GitHub Actions for free" guide (EN+DA).

Hub post that collects the whole proven site-health stack (deskuptime@v1,
compliance-site-check@v2, clean-copy-cli@v1, bugbottle-action@v1) around one
cron-based workflow — the SEO entry point STATUS.md asked for. Same generator
pattern as make_blog_smoke_469.py.
Validates: JSON-LD parse + schema check, sitemap update, internal-link check.
"""

import json
import re
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

EN_SLUG = 'monitor-website-github-actions-free'
DA_SLUG = 'overvaag-hjemmeside-github-actions-gratis'


def head(slug, lang, title, meta_desc, og_title, og_desc, headline):
    ld = json.dumps({
        '@context': 'https://schema.org', '@type': 'TechArticle', 'headline': headline,
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


PRE_STYLE = 'background:#0d1117;color:#e6edf3;padding:20px;border-radius:10px;overflow-x:auto;font-size:0.85em;'

EN_BODY = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">GUIDE · SITE HEALTH</div>
    <h1>Monitor Your Website from GitHub Actions:<br>Free Uptime, SSL &amp; Compliance in One Cron Job</h1>
    <p class="subtitle">Skip the $10–15/month monitoring SaaS. One scheduled workflow checks that your site is up, the SSL certificate is valid, security headers are intact and your privacy policy still exists — using four free, open-source GitHub Actions.</p>
    <div class="hero-cta">
      <a href="#workflow" class="btn-primary">Copy the workflow</a>
      <a href="/free-tools" class="btn-secondary">See all free tools →</a>
    </div>
    <p class="hero-note">Updated August 2026 · Reading time: 6 minutes</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="why">Why a cron job beats a monitoring dashboard</h2>
    <p>Most uptime monitors want a monthly subscription, an account, and another inbox of alert emails. If you already ship your site through GitHub, you have a scheduler, a runner and a notification channel (failed workflow runs email the repo owner by default) sitting there unused.</p>
    <p>This setup runs on public repositories for free, needs no secrets, and every check is a plain YAML step you can read in seconds. It catches the failures that actually happen to small sites: expired certificates, a redesign that dropped the cookie banner, a redirect rule that broke after a deploy.</p>

    <h2 id="workflow">The complete workflow</h2>
    <p>Save as <code>.github/workflows/site-health.yml</code>:</p>
    <pre style="{PRE_STYLE}"><code>name: Site health
on:
  schedule:
    - cron: '0 6 * * *'   # daily at 06:00 UTC
  workflow_dispatch:      # also runnable manually from the Actions tab

jobs:
  health:
    runs-on: ubuntu-latest
    steps:
      - name: Uptime + SSL certificate expiry
        uses: mahope/deskuptime@v1
        with:
          url: https://your-site.com

      - name: EU compliance intact (privacy policy, headers, meta)
        uses: mahope/compliance-site-check@v2
        with:
          url: https://your-site.com</code></pre>
    <p>Replace <code>your-site.com</code> with your domain. Both actions pin floating major tags, so bug fixes arrive automatically without breaking changes.</p>

    <h2 id="actions">What each action checks</h2>
    <div class="problem-cards">
      <div class="card"><h3><code>deskuptime@v1</code></h3><p>Fetches the URL and fails if the page does not respond correctly, warns when the SSL certificate is close to expiry, and can detect unwanted content changes. Zero dependencies — no npm install, no config files.</p></div>
      <div class="card"><h3><code>compliance-site-check@v2</code></h3><p>Nine GDPR/EAA-oriented checks against the live page: privacy-policy reachability, cookie-consent signals, security headers (CSP, HSTS, XFO), SEO meta tags and language declaration. A silent regression turns red before your users or a regulator notice.</p></div>
    </div>

    <h2 id="extras">Two more steps for teams that publish content</h2>
    <p>The same workflow can carry two optional jobs:</p>
    <ul>
      <li><strong>Content integrity:</strong> <code>mahope/clean-copy-cli@v1</code> converts a live page to Markdown inside the workflow and exposes it as step outputs — useful to snapshot documentation or diff a changelog between runs.</li>
      <li><strong>Bug-report quality:</strong> if you collect in-app reports with <a href="https://github.com/mahope/bugbottle">bugbottle</a>, <code>mahope/bugbottle-action@v1</code> validates collected reports in CI so low-quality submissions never reach your issue tracker.</li>
    </ul>

    <h2 id="schedule-tips">Scheduling tips</h2>
    <ul>
      <li>Cron times on GitHub Actions are in UTC. <code>'0 6 * * *'</code> is 08:00 in Copenhagen (CEST).</li>
      <li>Scheduled workflows only run on the default branch, and can be delayed a few minutes during peak hours — fine for daily monitoring, not for sub-minute alerting.</li>
      <li>GitHub disables schedules on repos with no activity for 60 days; any commit re-enables them. Pinning a comment or bumping a date keeps an idle repo alive.</li>
    </ul>

    <h2 id="costs">What it replaces</h2>
    <p>Uptime-monitoring SaaS typically starts around $10–15/month per site ($120–180/year per site), and a manual compliance review starts in the thousands. This stack costs nothing on public repos and fits in one file you own. For sub-minute paging during incidents, dedicated monitoring still has a place — but for "did my site silently break?", a daily cron job catches it within 24 hours at zero cost.</p>

    <div class="card" style="margin-top:32px;">
      <h3>Try the compliance half right now</h3>
      <p>No repo needed to see what the scanner finds on your live site — free, no signup, results in about a minute.</p>
      <a href="/compliance-site-check" class="btn-primary" style="margin-top:12px;">Scan your site free →</a>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
    <p><a href="/">← Home</a> · <a href="/deskuptime/">Deskuptime</a> · <a href="/free-tools">Free tools</a> · <a href="/blog/post-deploy-smoke-tests-static-sites">Post-deploy smoke tests</a></p>
</footer>
</body>
</html>'''

DA_BODY = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">GUIDE · SITE HEALTH</div>
    <h1>Overv&aring;g din hjemmeside fra GitHub Actions:<br>Gratis oppetid, SSL &amp; compliance i &eacute;t cron-job</h1>
    <p class="subtitle">Drop overv&aring;gnings-SaaS til 70&ndash;100 kr./md. &Eacute;t planlagt workflow tjekker at dit site er oppe, SSL-certifikatet er gyldigt, sikkerhedsheaders er intakte og privatlivspolitikken stadig findes &mdash; med fire gratis open-source GitHub Actions.</p>
    <div class="hero-cta">
      <a href="#workflow" class="btn-primary">Kopier workflowet</a>
      <a href="/da/compliance-site-check" class="btn-secondary">Scan dit site gratis &rarr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; L&aelig;setid: 6 minutter</p>
  </div>
</header>

<section class="problem" id="indhold">
  <div class="container">
    <h2 id="hvorfor">Hvorfor et cron-job sl&aring;r et overv&aring;gnings-dashboard</h2>
    <p>De fleste oppetidsoverv&aring;gninger vil have et m&aring;nedsabonnement, en konto og endnu en indbakke af alarm-mails. Hvis du allerede udgiver dit site via GitHub, har du en skemal&aelig;gger, en runner og en notifikationskanal (fejlende workflow-k&oslash;rsler sender som udgangspunkt mail til repo-ejeren) st&aring;ende ubrugt.</p>
    <p>Dette setup k&oslash;rer gratis p&aring; offentlige repositories, kr&aelig;ver ingen secrets, og hvert tjek er et almindeligt YAML-trin du kan l&aelig;se p&aring; sekunder. Det fanger de fejl der faktisk rammer sm&aring; sites: udl&oslash;bne certifikater, et redesign der droppede samtykke-banneret, en redirect-regel der br&oslash;d efter en udgivelse.</p>

    <h2 id="workflow">Det komplette workflow</h2>
    <p>Gem som <code>.github/workflows/site-health.yml</code>:</p>
    <pre style="{PRE_STYLE}"><code>name: Site health
on:
  schedule:
    - cron: '0 6 * * *'   # dagligt kl. 06:00 UTC (08:00 dansk tid)
  workflow_dispatch:      # kan ogsaa koeres manuelt fra Actions-fanen

jobs:
  health:
    runs-on: ubuntu-latest
    steps:
      - name: Oppetid + SSL-certifikatets udl&oslash;b
        uses: mahope/deskuptime@v1
        with:
          url: https://dit-site.dk

      - name: EU-compliance intakt (privatliv, headers, meta)
        uses: mahope/compliance-site-check@v2
        with:
          url: https://dit-site.dk</code></pre>
    <p>Erstat <code>dit-site.dk</code> med dit dom&aelig;ne. Begge actions bruger flydende hovedversions-tags, s&aring; fejlretninger kommer automatisk uden breaking changes.</p>

    <h2 id="actions">Hvad hver action tjekker</h2>
    <div class="problem-cards">
      <div class="card"><h3><code>deskuptime@v1</code></h3><p>Henter URL'en og fejler, hvis siden ikke svarer korrekt, advarer n&aring;r SSL-certifikatet snart udl&oslash;ber, og kan opdage u&oslash;nskede indholds&aelig;ndringer. Nul afh&aelig;ngigheder &mdash; ingen npm-installering, ingen konfigurationsfiler.</p></div>
      <div class="card"><h3><code>compliance-site-check@v2</code></h3><p>Ni GDPR/EAA-orienterede tjek mod den live side: om privatlivspolitikken kan n&aring;s, cookie-samtykke-signaler, sikkerhedsheaders (CSP, HSTS, XFO), SEO-metatags og sprogdeklaration. En lydl&oslash;s regression bliver r&oslash;d f&oslash;r dine brugere eller myndighederne opdager det.</p></div>
    </div>

    <h2 id="ekstra">To ekstra trin til teams der udgiver indhold</h2>
    <ul>
      <li><strong>Indholdsintegritet:</strong> <code>mahope/clean-copy-cli@v1</code> konverterer en live side til Markdown inde i workflowet og eksponerer resultatet som step outputs &mdash; praktisk til snapshots af dokumentation eller diffs af en changelog mellem k&oslash;rsler.</li>
      <li><strong>Fejlrapport-kvalitet:</strong> samler du rapporter i appen med <a href="https://github.com/mahope/bugbottle">bugbottle</a>, validerer <code>mahope/bugbottle-action@v1</code> de indsamlede rapporter i CI, s&aring; d&aring;rlige rapporter aldrig n&aring;r dit issue tracker.</li>
    </ul>

    <h2 id="skema-tips">Tips til skemal&aelig;gning</h2>
    <ul>
      <li>Cron-tider i GitHub Actions er i UTC. <code>'0 6 * * *'</code> er kl. 08:00 dansk tid (CEST).</li>
      <li>Planlagte workflows k&oslash;rer kun p&aring; default-branchen og kan blive forsinket et par minutter i travle perioder &mdash; fint til daglig overv&aring;gning, ikke til under-minut-alarming.</li>
      <li>GitHub deaktiverer skemaer p&aring; repos uden aktivitet i 60 dage; enhver commit genaktiverer dem.</li>
    </ul>

    <h2 id="pris">Hvad det erstatter</h2>
    <p>Oppetids-SaaS starter typisk omkring 70&ndash;100 kr./md. pr. site (840&ndash;1.200 kr./&aring;r pr. site), og en manuel compliance-gennemgang starter i tusindvis af kroner. Denne stak koster ingenting p&aring; offentlige repos og fylder &eacute;t fil du selv ejer. Til under-minut-alarming ved driftsstop har dedikeret overv&aring;gning stadig sin plads &mdash; men til &quot;har mit site g&aring;et i stykker uden at jeg opdagede det?&quot; fanger et dagligt cron-job det inden for 24 timer til nul pris.</p>

    <div class="card" style="margin-top:32px;">
      <h3>Pr&oslash;v compliance-delen lige nu</h3>
      <p>Ingen repository n&oslash;dvendig for at se hvad scanneren finder p&aring; dit live-site &mdash; gratis, uden tilmelding, resultat p&aring; cirka &eacute;t minut.</p>
      <a href="/da/compliance-site-check" class="btn-primary" style="margin-top:12px;">Scan dit site gratis &rarr;</a>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
    <p><a href="/da/">← Forside</a> &middot; <a href="/da/blog">Blog</a></p>
</footer>
</body>
</html>'''


def update_sitemap(slugs):
    p = f'{SITE}/sitemap.xml'
    c = open(p).read()
    add = ''.join(f'  <url><loc>{BASE}/{lang_dir(s)}blog/{s}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'
                  for s in slugs)
    assert all(f'/{s}</loc>' not in c for s in slugs), 'slug already in sitemap'
    c = c.replace('</urlset>', add + '</urlset>')
    open(p, 'w').write(c)


def lang_dir(slug):
    return 'da/' if slug == DA_SLUG else ''


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
    pages = [
        (EN_SLUG, head(EN_SLUG, 'en',
                       'Monitor Your Website from GitHub Actions: Free Uptime, SSL & Compliance Checks',
                       'A daily GitHub Actions cron job checks uptime, SSL certificate expiry, security headers and GDPR basics with four free open-source actions. No SaaS, no secrets.',
                       'Monitor Your Website from GitHub Actions',
                       'Free uptime, SSL and compliance checks in one scheduled workflow — four open-source actions, no SaaS.',
                       'Monitor Your Website from GitHub Actions: Free Uptime, SSL & Compliance Checks'),
         EN_BODY, f'{SITE}/blog'),
        (DA_SLUG, head(DA_SLUG, 'da',
                       'Overvåg hjemmeside fra GitHub Actions: gratis oppetid, SSL og compliance',
                       'Et dagligt GitHub Actions cron-job tjekker oppetid, SSL-udløb, sikkerhedsheaders og GDPR-basics med fire gratis open-source actions. Uden SaaS, uden secrets.',
                       'Overvåg hjemmeside fra GitHub Actions',
                       'Gratis oppetid-, SSL- og compliance-tjek i ét planlagt workflow — fire open-source actions, uden SaaS.',
                       'Overvåg hjemmeside fra GitHub Actions: gratis oppetid, SSL og compliance'),
         DA_BODY, f'{SITE}/da/blog'),
    ]
    written = []
    for slug, h, body, outdir in pages:
        html_out = h + '\n' + body
        path = f'{outdir}/{slug}.html'
        with open(path, 'w') as f:
            f.write(html_out)
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html_out, re.DOTALL)
        assert blocks, f'no JSON-LD in {slug}'
        for b in blocks:
            d = json.loads(b)
            assert d['@context'] == 'https://schema.org' and d['@type'] == 'TechArticle', slug
        print(f'{slug}.html written, JSON-LD OK')
        written.append(path)
    update_sitemap([EN_SLUG, DA_SLUG])
    print('sitemap updated')
    broken = check_links(written)
    print('broken internal links:', broken if broken else 'none')

    # llms.txt entries
    ll_path = f'{SITE}/llms.txt'
    ll = open(ll_path).read()
    adds = []
    en_url = f'/blog/{EN_SLUG}'
    da_url = f'/da/blog/{DA_SLUG}'
    if en_url not in ll:
        adds.append('- [Monitor Your Website from GitHub Actions](https://hermes-passiv.pages.dev/blog/monitor-website-github-actions-free): free daily uptime, SSL and compliance checks with four open-source Actions.')
    if da_url not in ll:
        adds.append('- [Overvåg hjemmeside fra GitHub Actions](https://hermes-passiv.pages.dev/da/blog/overvaag-hjemmeside-github-actions-gratis): gratis daglig overvågning af oppetid, SSL og compliance.')
    if adds:
        open(ll_path, 'a').write('\n'.join(adds) + '\n')
    print('llms.txt:', len(adds), 'entries added')


if __name__ == '__main__':
    main()
