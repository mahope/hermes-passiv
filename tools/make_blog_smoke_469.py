#!/usr/bin/env python3
"""Iteration 469: Post-deploy smoke tests guide (EN+DA).

Targets "post-deploy smoke test", "test website after deploy" long-tail and
links deskuptime@v1 + compliance-site-check@v2 (both self-test-proved in
iter 467). Same generator pattern as make_blog_ci_actions.py.
Validates: JSON-LD parse + schema check, sitemap update, internal-link check.
"""

import json
import re
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'


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


EN_BODY = '''
<body><header class="hero">
  <div class="container">
    <div class="badge">GUIDE · DEPLOYMENT</div>
    <h1>Post-Deploy Smoke Tests for Static Sites:<br>A 5-Minute CI Setup</h1>
    <p class="subtitle">Your deploy succeeded. Is the site actually up? Does the privacy policy still exist? A two-step GitHub Actions job answers both after every release — free, no monitoring SaaS, no account.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">Read the setup</a>
      <a href="/compliance-site-check" class="btn-secondary">Scan your site free →</a>
    </div>
    <p class="hero-note">Updated August 2026 · Reading time: 5 minutes</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="why">The gap between "deployed" and "works"</h2>
    <p>Static-site pipelines report success when files land on the CDN — not when the site serves correctly. A misconfigured redirect rule, an expired certificate nobody noticed, or a build that silently dropped a page all pass the deploy step green. For static sites especially, "the upload finished" and "the site works" are different questions.</p>
    <p>A post-deploy smoke test closes that gap: one job that hits your live URL right after every release and fails loudly if anything is wrong.</p>

    <h2 id="setup">The workflow</h2>
    <p>Two steps, no secrets, no third-party service. Save as <code>.github/workflows/post-deploy.yml</code>:</p>
    <pre style="background:#0d1117;color:#e6edf3;padding:20px;border-radius:10px;overflow-x:auto;font-size:0.85em;"><code>name: Post-deploy smoke test
on:
  deployment_status:            # runs on real deploys (Vercel/Cloudflare/etc.)
    states: [success]
  workflow_dispatch:            # also runnable manually

jobs:
  smoke:
    if: github.event_name == 'workflow_dispatch' || github.event.deployment_status.state == 'success'
    runs-on: ubuntu-latest
    steps:
      - name: Site responds
        uses: mahope/deskuptime@v1
        with:
          url: https://your-site.com

      - name: Compliance intact
        uses: mahope/compliance-site-check@v2
        with:
          url: https://your-site.com</code></pre>
    <p>Replace <code>your-site.com</code> with your domain. Both steps are pinned to floating major tags so fixes arrive automatically without breaking changes.</p>

    <h2 id="what">What each step checks</h2>
    <div class="problem-cards">
      <div class="card"><h3><code>deskuptime@v1</code></h3><p>A dependency-free uptime check: fetches the URL and fails the step if the page does not respond as expected. Zero npm installs, zero config files — the whole action is a single YAML step you can read in ten seconds.</p></div>
      <div class="card"><h3><code>compliance-site-check@v2</code></h3><p>Runs nine GDPR/EAA-oriented checks against the live page: security headers, privacy-policy reachability, cookie-consent signals, and more. If a redesign quietly dropped the consent banner, this step turns red before your lawyer does.</p></div>
    </div>

    <h2 id="schedule">Add a daily schedule (optional)</h2>
    <p>The same file doubles as a daily monitor — add a cron trigger:</p>
    <pre style="background:#0d1117;color:#e6edf3;padding:20px;border-radius:10px;overflow-x:auto;font-size:0.85em;"><code>on:
  deployment_status:
    states: [success]
  schedule:
    - cron: '0 6 * * *'   # daily at 06:00 UTC
  workflow_dispatch:</code></pre>
    <p>Now a certificate expiry or host outage surfaces in the same Actions tab your team already watches — instead of an email digest from yet another SaaS dashboard nobody logs into.</p>

    <h2 id="costs">What it replaces</h2>
    <p>Uptime-monitoring SaaS starts around $10–15/month per site, and compliance audits run $2,000–10,000 per engagement. Neither catches regressions between check-ins. This setup runs continuously on infrastructure you already have: free for public repositories, included minutes for private ones.</p>

    <div class="card" style="margin-top:32px;">
      <h3>Try the compliance half right now</h3>
      <p>No repo needed to see what the scanner finds on your live site — free, no signup, results in about a minute.</p>
      <a href="/compliance-site-check" class="btn-primary" style="margin-top:12px;">Scan your site free →</a>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
    <p><a href="/">← Home</a> · <a href="/deskuptime/">Deskuptime</a> · <a href="/free-tools">Free tools</a> · <a href="/#blog">Blog</a></p>
</footer>
</body>
</html>'''


def en_page():
    slug = 'post-deploy-smoke-tests-static-sites'
    desc = ('Your deploy succeeded — but does the site actually work? A two-step '
            'GitHub Actions smoke test checks uptime and EU-compliance after every '
            'release. Free, no secrets, no SaaS.')
    h = head(slug, 'en',
             'Post-Deploy Smoke Tests for Static Sites: 5-Minute GitHub Actions Setup',
             desc,
             'Post-Deploy Smoke Tests for Static Sites',
             'Two free GitHub Actions steps verify uptime and compliance after every deploy — no SaaS, no secrets.',
             'Post-Deploy Smoke Tests for Static Sites')
    body = EN_BODY.replace('<body>', '', 1)
    return slug, h + '\n' + body


def da_page():
    slug = 'roegtest-efter-udgivelse-statiske-sites'
    desc = ('Udgivelsen lykkedes — men virker sitet? Et to-trins GitHub Actions-job '
            'tjekker oppetid og EU-compliance efter hver udgivelse. Gratis, uden '
            'secrets, uden abonnement.')
    h = head(slug, 'da',
             'Roegtest efter udgivelse af statiske sites: 5-minutters GitHub Actions-setup',
             desc,
             'Roegtest efter udgivelse af statiske sites',
             'To gratis GitHub Actions-trin tjekker oppetid og compliance efter hver udgivelse — uden SaaS, uden secrets.',
             'Roegtest efter udgivelse af statiske sites')
    body = f'''{h}
<body><header class="hero">
  <div class="container">
    <div class="badge">GUIDE · DEPLOYMENT</div>
    <h1>R&oslash;gtest efter udgivelse af statiske sites:<br>Et 5-minutters CI-setup</h1>
    <p class="subtitle">Din udgivelse lykkedes. Virker sitet overhovedet? Eksisterer privatlivspolitikken stadig? Et to-trins GitHub Actions-job svarer p&aring; begge efter hver udgivelse &mdash; gratis, uden overv&aring;gnings-SaaS, uden konto.</p>
    <div class="hero-cta">
      <a href="#indhold" class="btn-primary">L&aelig;s setuppet</a>
      <a href="/da/compliance-site-check" class="btn-secondary">Scan dit site gratis &rarr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; L&aelig;setid: 5 minutter</p>
  </div>
</header>

<section class="problem" id="indhold">
  <div class="container">
    <h2 id="hvorfor">Afstanden mellem "udgivet" og "virker"</h2>
    <p>Pipelines til statiske sites rapporterer succes n&aring;r filerne lander p&aring; CDN'en &mdash; ikke n&aring;r sitet serveres korrekt. En fejlkonfigureret redirect-regel, et udl&oslash;bet certifikat ingen lagde m&aelig;rke til, eller et build der lydl&oslash;st mistede en side: det hele best&aring;r udgivelsestrinnet gr&oslash;nt. For statiske sites er "uploaden er f&aelig;rdig" og "sitet virker" to forskellige sp&oslash;rgsm&aring;l.</p>
    <p>En r&oslash;gtest lukker hullet: &eacute;t job der rammer din live-URL lige efter hver udgivelse og fejler h&oslash;jt, hvis noget er galt.</p>

    <h2 id="setup">Workflowet</h2>
    <p>To trin, ingen secrets, ingen tredjepartstjeneste. Gem som <code>.github/workflows/post-deploy.yml</code>:</p>
    <pre style="background:#0d1117;color:#e6edf3;padding:20px;border-radius:10px;overflow-x:auto;font-size:0.85em;"><code>name: Post-deploy roegtest
on:
  deployment_status:            # koerer ved rigtige udgivelser (Vercel/Cloudflare osv.)
    states: [success]
  workflow_dispatch:            # kan ogsaa koeres manuelt

jobs:
  smoke:
    if: github.event_name == 'workflow_dispatch' || github.event.deployment_status.state == 'success'
    runs-on: ubuntu-latest
    steps:
      - name: Sitet svarer
        uses: mahope/deskuptime@v1
        with:
          url: https://dit-site.dk

      - name: Compliance er intakt
        uses: mahope/compliance-site-check@v2
        with:
          url: https://dit-site.dk</code></pre>
    <p>Erstat <code>dit-site.dk</code> med dit dom&aelig;ne. Begge trin er fastgjort til flydende hovedversions-tags, s&aring; fejlretninger kommer automatisk uden breaking changes.</p>

    <h2 id="hvad">Hvad hvert trin tjekker</h2>
    <div class="problem-cards">
      <div class="card"><h3><code>deskuptime@v1</code></h3><p>En afh&aelig;ngighedsfri oppetidstjek: henter URL'en og fejler trinnet, hvis siden ikke svarer som forventet. Nul npm-installeringer, nul konfigurationsfiler &mdash; hele actionen er &eacute;t YAML-trin du kan l&aelig;se p&aring; ti sekunder.</p></div>
      <div class="card"><h3><code>compliance-site-check@v2</code></h3><p>K&oslash;rer ni GDPR/EAA-orienterede tjek mod den live side: sikkerhedsheaders, om privatlivspolitikken kan n&aring;s, cookie-samtykke-signaler med flere. Hvis en ny design stille dropper samtykke-banneret, bliver dette trin r&oslash;dt f&oslash;r din advokat g&oslash;r.</p></div>
    </div>

    <h2 id="skema">Tilf&oslash;j dagligt skema (valgfrit)</h2>
    <p Samme fil fungerer ogs&aring; som daglig overv&aring;gning &mdash; tilf&oslash;j en cron-trigger:</p>
    <pre style="background:#0d1117;color:#e6edf3;padding:20px;border-radius:10px;overflow-x:auto;font-size:0.85em;"><code>on:
  deployment_status:
    states: [success]
  schedule:
    - cron: '0 6 * * *'   # dagligt kl. 06:00 UTC
  workflow_dispatch:</code></pre>
    <p>S&aring; dukker et udl&oslash;bende certifikat eller et v&aelig;rtsudfald op i samme Actions-fane teamet alligevel kigger i &mdash; i stedet for en mail-digest fra endnu et SaaS-dashboard ingen logger ind p&aring;.</p>

    <h2 id="pris">Hvad det erstatter</h2>
    <p>Oppetidsoverv&aring;gnings-SaaS starter omkring 70&ndash;100 kr./md. pr. site, og compliance-audits koster 15.000&ndash;70.000 kr. pr. engagement. Ingen af delene fanger regressioner mellem tjek. Dette setup k&oslash;rer l&oslash;bende p&aring; infrastruktur du alligevel har: gratis for offentlige repositories, inkluderede minutter for private.</p>

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
    return slug, body


def update_sitemap(slugs):
    p = f'{SITE}/sitemap.xml'
    c = open(p).read()
    add = ''.join(f'  <url><loc>{BASE}/{lang_dir(s)}blog/{s}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'
                  for s in slugs)
    assert all(f'/{s}</loc>' not in c.replace(add,'') for s in slugs), 'slug already in sitemap'
    c = c.replace('</urlset>', add + '</urlset>')
    open(p, 'w').write(c)

def lang_dir(slug):
    return 'da/' if slug == 'roegtest-efter-udgivelse-statiske-sites' else ''


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
    pages = [en_page(), da_page()]
    for slug, html in pages:
        outdir = f'{SITE}/da/blog' if slug == 'roegtest-efter-udgivelse-statiske-sites' else f'{SITE}/blog'
        with open(f"{outdir}/{slug}.html", 'w') as f:
            f.write(html)
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        assert blocks, f'no JSON-LD in {slug}'
        for b in blocks:
            d = json.loads(b)
            assert d['@context'] == 'https://schema.org' and d['@type'] == 'TechArticle', slug
        print(f'{slug}.html written, JSON-LD OK')
    update_sitemap([s for s, _ in pages])
    print('sitemap updated')
    broken = check_links([('site/da/blog/' if s in ('roegtest-efter-udgivelse-statiske-sites',) else 'site/blog/') + s + '.html' for s, _ in pages])
    print('broken internal links:', broken if broken else 'none')


if __name__ == '__main__':
    main()
