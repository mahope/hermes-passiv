#!/usr/bin/env python3
"""Iteration 468: CI-integration guides for the three self-test-proved Actions.

New EN+DA blog pair: "Run bug reports in your CI pipeline" — targets
"github actions validate json", "bug report workflow" long-tail, and links all
three proved actions (bugbottle-action@v1, deskuptime@v1,
compliance-site-check@v2). Also patches existing posts to use @v1 floating tags
(instead of bare repo links / untagged refs) now that every action is proven.
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
    <div class="badge">GUIDE · GITHUB ACTIONS</div>
    <h1>Run Bug Reports in Your CI Pipeline:<br>A Complete Setup</h1>
    <p class="subtitle">Three GitHub Actions that turn CI into more than a test runner: collect bug reports from your live site, keep your site up, and catch EU-compliance regressions — all as versioned, pinned actions you can drop into any workflow today.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">Read the guide</a>
      <a href="/deskuptime/" class="btn-secondary">See Deskuptime →</a>
    </div>
    <p class="hero-note">Updated August 2026 · Reading time: 6 minutes</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="why">Why put reporting in CI?</h2>
    <p>Your CI pipeline runs on every push whether anyone is watching or not. That makes it the cheapest place to answer questions that otherwise need a person: <em>did a new deploy break accessibility?</em> <em>Is the site even up?</em> <em>Are bug reports coming in valid?</em> A step that fails loudly in CI costs seconds; the same problem discovered by a user costs trust.</p>
    <p>All three actions below are plain YAML steps with no account signup, no API key, and no SaaS subscription. Each one is pinned to a floating major tag (<code>@v1</code> / <code>@v2</code>) so you get fixes automatically without surprise breaking changes.</p>

    <h2 id="actions">The three actions</h2>
    <div class="problem-cards">
      <div class="card"><h3>1. Validate bug reports: <code>bugbottle-action@v1</code></h3><p>If you collect bug reports as JSON files (from a feedback widget, a form export, or a script), this action validates them against the schema inside your workflow. A malformed report fails the build instead of silently rotting in a folder. It exits non-zero on invalid input, so it works as a gate before release.</p></div>
      <div class="card"><h3>2. Keep the site up: <code>deskuptime@v1</code></h3><p>A dependency-free uptime check that runs wherever your CI runs. Point it at any URL and it fails the step if the page does not respond as expected. Useful as a post-deploy smoke test — especially for static sites where "the deploy succeeded" and "the site works" are different questions.</p></div>
      <div class="card"><h3>3. Catch compliance regressions: <code>compliance-site-check@v2</code></h3><p>Runs a GDPR/EAA-oriented compliance scan against a URL and surfaces failures in the job log. Add it after each deploy so a removed privacy policy link or broken consent mechanism shows up in the same place your tests do.</p></div>
    </div>

    <h2 id="workflow">A complete example workflow</h2>
    <p>This workflow runs after deployment: it checks the site is up, scans compliance, and validates any collected bug reports:</p>
    <pre style="background:#0d1117;color:#e6edf3;padding:20px;border-radius:10px;overflow-x:auto;font-size:0.85em;"><code>name: Post-deploy checks
on:
  schedule:
    - cron: '0 6 * * *'   # daily at 06:00 UTC
  workflow_dispatch:

jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Site is up
        uses: mahope/deskuptime@v1
        with:
          url: https://example.com

      - name: Compliance scan
        uses: mahope/compliance-site-check@v2
        with:
          url: https://example.com

      - name: Validate bug reports
        uses: mahope/bugbottle-action@v1
        with:
          path: ./reports</code></pre>
    <p>Every step either passes or fails visibly. No dashboard to log into, no email digest to ignore — red is red, in the same place your team already looks.</p>

    <h2 id="setup">Setup, step by step</h2>
    <ol>
      <li><strong>Create the workflow file.</strong> Save it as <code>.github/workflows/post-deploy.yml</code> in your repository.</li>
      <li><strong>Point the URLs at your own site.</strong> Replace <code>example.com</code> everywhere. For staging environments, duplicate the job with your staging URL.</li>
      <li><strong>For bugbottle:</strong> point <code>path</code> at the directory where report files land. If you don't collect reports yet, remove that step — the other two stand alone.</li>
      <li><strong>Commit and run once manually</strong> via <em>workflow_dispatch</em> to confirm everything is green before trusting the schedule.</li>
    </ol>
    <p>No secrets are required for any of the three actions, since none of them call external services. They read your inputs and act on them locally in the runner.</p>

    <h2 id="costs">What this replaces</h2>
    <p>A typical uptime-monitoring SaaS starts around $10–15/month per site. Compliance audits run $2,000–10,000 per engagement. Neither catches regressions between check-ins. A daily CI job does both continuously, for free, on infrastructure (GitHub-hosted runners) you already pay for — free for public repositories, and included minutes for private ones.</p>

    <div class="card" style="margin-top:32px;">
      <h3>Try it on your site first</h3>
      <p>Before wiring CI, see what the compliance scanner finds on your live site — free, no signup, results in about a minute.</p>
      <a href="/compliance-site-check" class="btn-primary" style="margin-top:12px;">Scan your site free →</a>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
    <p><a href="/">← Home</a> · <a href="/compliance-site-check">Free scanner</a> · <a href="/free-tools">Free tools</a> · <a href="/#blog">Blog</a></p>
</footer>
</body>
</html>'''

DA_BODY = EN_BODY  # replaced below with Danish


def da_page():
    slug = 'bugrapporter-i-ci-pipeline'
    desc = ('Tre GitHub Actions der goer CI til mere end en testloebere: saml og '
            'valider bugrapporter, hold oeje paa sitet, og faang EU-compliance-'
            'regressioner — gratis, uden konto.')
    h = head(slug, 'da',
             'Bugrapporter i din CI-pipeline: Komplet opsætning med 3 GitHub Actions',
             desc,
             'Bugrapporter i CI: 3 gratis GitHub Actions',
             'Valider rapporter, overvaag sitet og tjek compliance direkte i workflowet — ingen konto, ingen API-noegle.',
             'Bugrapporter i CI: 3 gratis GitHub Actions')
    body = f'''{head.__doc__ or ""}'''
    # Build the Danish body directly (full translation)
    body = f'''{h}
<body><header class="hero">
  <div class="container">
    <div class="badge">GUIDE · GITHUB ACTIONS</div>
    <h1>Bugrapporter i din CI-pipeline:<br>Komplet opsætning</h1>
    <p class="subtitle">Tre GitHub Actions der gør CI til mere end en testløber: saml bugrapporter fra dit live-site, hold øje med at sitet virker, og fang EU-compliance-regressioner — alt sammen som versionerede actions du kan droppe ind i ethvert workflow i dag.</p>
    <div class="hero-cta">
      <a href="#indhold" class="btn-primary">Læs guiden</a>
      <a href="/da/" class="btn-secondary">Gratis scanner →</a>
    </div>
    <p class="hero-note">Opdateret august 2026 · Læsetid: 6 minutter</p>
  </div>
</header>

<section class="problem" id="indhold">
  <div class="container">
    <h2 id="hvorfor">Hvorfor lægge rapportering i CI?</h2>
    <p>Din CI-pipeline kører ved hvert push, uanset om nogen ser på det. Det gør den til det billigste sted at besvare spørgsmål der ellers kræver et menneske: <em>Knækkede en ny udgivelse tilgængeligheden?</em> <em>Virker sitet overhovedet?</em> <em>Er de bugrapporter der kommer ind, gyldige?</em> Et trin der fejler højt i CI koster sekunder. Det samme problem opdaget af en bruger koster tillid.</p>
    <p>Alle tre actions nedenfor er almindelige YAML-trin uden kontooprettelse, uden API-nøgle og uden SaaS-abonnement. Hver er fastgjort til et flydende hovedversions-tag (<code>@v1</code> / <code>@v2</code>), så du får fejlretninger automatisk uden pludselige breaking changes.</p>

    <h2 id="actions">De tre actions</h2>
    <div class="problem-cards">
      <div class="card"><h3>1. Valider bugrapporter: <code>bugbottle-action@v1</code></h3><p>Hvis du samler bugrapporter som JSON-filer (fra en feedback-widget, et formular-export eller et script), validerer denne action dem mod skemaet inde i dit workflow. En misdannet rapport fejler buildet i stedet for at rådne lydløst i en mappe. Den afslutter med fejlkode ved ugyldigt input, så den kan bruges som port før release.</p></div>
      <div class="card"><h3>2. Hold sitet i live: <code>deskuptime@v1</code></h3><p>En afhængighedsfri oppetidstjek der kører hvor end din CI kører. Peg den på en URL, og fejler trinnet hvis siden ikke svarer som forventet. Nyttig som post-deploy smoke test — især på statiske sites hvor "deployet lykkedes" og "sitet virker" er to forskellige spørgsmål.</p></div>
      <div class="card"><h3>3. Fang compliance-regressioner: <code>compliance-site-check@v2</code></h3><p>Kører en GDPR/EAA-orienteret compliancescanning mod en URL og viser fejl i jobloggen. Tilføj den efter hver udgivelse, så et fjernet privatlivspolitik-link eller en ødelagt samtyckemekanisme dukker op samme sted som dine tests.</p></div>
    </div>

    <h2 id="workflow">Et komplet eksempel-workflow</h2>
    <p>Dette workflow kører efter udgivelse: det tjekker at sitet er oppe, scanner compliance og validerer indsamlede bugrapporter:</p>
    <pre style="background:#0d1117;color:#e6edf3;padding:20px;border-radius:10px;overflow-x:auto;font-size:0.85em;"><code>name: Post-deploy checks
on:
  schedule:
    - cron: '0 6 * * *'   # dagligt kl. 06:00 UTC
  workflow_dispatch:

jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Sitet er oppe
        uses: mahope/deskuptime@v1
        with:
          url: https://example.com

      - name: Compliance-scan
        uses: mahope/compliance-site-check@v2
        with:
          url: https://example.com

      - name: Valider bugrapporter
        uses: mahope/bugbottle-action@v1
        with:
          path: ./reports</code></pre>
    <p>Hvert trin består eller fejler synligt. Ingen dashboard at logge ind på, ingen mail-digest at ignorere — rødt er rødt, samme sted som teamet alligevel kigger.</p>

    <h2 id="opsaetning">Opsætning, trin for trin</h2>
    <ol>
      <li><strong>Opret workflowfilen.</strong> Gem den som <code>.github/workflows/post-deploy.yml</code> i dit repository.</li>
      <li><strong>Peg URL'erne på dit eget site.</strong> Erstat <code>example.com</code> overalt. Duplikér jobbet med din staging-URL, hvis du også vil tjekke staging.</li>
      <li><strong>Til bugbottle:</strong> peg <code>path</code> på mappen hvor rapportfilerne lander. Samler du ikke rapporter endnu, så fjern trinnet — de to andre står alene.</li>
      <li><strong>Commit og kør én gang manuelt</strong> via <em>workflow_dispatch</em>, så du har bekræftet alt er grønt før du stoler på skemaet.</li>
    </ol>
    <p>Ingen af de tre actions kræver secrets, da ingen kalder eksterne tjenester. De læser dine inputs og arbejder lokalt på runneren.</p>

    <h2 id="pris">Hvad dette erstatter</h2>
    <p>En typisk oppetidsovervågnings-SaaS starter omkring 70–100 kr./md. pr. site. Compliance-audits koster 15.000–70.000 kr. pr. engagement. Ingen af delene fanger regressioner mellem tjek. Et dagligt CI-job gør begge dele løbende — gratis — på infrastruktur (GitHub-hostede runners) du allerede betaler for: gratis for offentlige repositories og inkluderede minutter for private.</p>

    <div class="card" style="margin-top:32px;">
      <h3>Prøv det på dit site først</h3>
      <p>Før du sætter CI op: se hvad compliance-scanneren finder på dit live-site — gratis, uden tilmelding, resultat på cirka ét minut.</p>
      <a href="/da/compliance-site-check" class="btn-primary" style="margin-top:12px;">Scan dit site gratis →</a>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
    <p><a href="/da/">← Forside</a> · <a href="/da/compliance-site-check">Gratis scanner</a> · <a href="/da/free-tools">Gratis værktøjer</a> · <a href="/da/#blog">Blog</a></p>
</footer>
</body>
</html>'''
    return slug, body


def en_page():
    slug = 'bug-reports-in-ci-pipeline'
    desc = ('Three GitHub Actions that turn CI into more than a test runner: '
            'validate bug reports, monitor uptime, and catch EU-compliance '
            'regressions — free, no account required.')
    h = head(slug, 'en',
             'Run Bug Reports in Your CI Pipeline: Complete Setup with 3 GitHub Actions',
             desc,
             'Bug Reports in CI: 3 Free GitHub Actions',
             'Validate reports, monitor uptime and check compliance directly in your workflow — no account, no API key.',
             'Bug Reports in CI: 3 Free GitHub Actions')
    # splice EN head onto EN body
    body = EN_BODY.replace('<body>', '', 1)
    return slug, h + '\n' + body


def update_sitemap(slugs):
    p = f'{SITE}/sitemap.xml'
    c = open(p).read()
    add = ''.join(f'  <url><loc>{BASE}/blog/{s}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'
                  for s in slugs)
    assert all(f'/blog/{s}</loc>' not in c for s in slugs), 'slug already in sitemap'
    c = c.replace('</urlset>', add + '</urlset>')
    open(p, 'w').write(c)


def patch_existing():
    """Patch existing posts to pin floating tags where they reference repos bare."""
    changed = []
    p = f'{SITE}/blog/add-bug-report-form-to-any-website.html'
    c = open(p).read()
    new = c.replace(
        '<a href="https://github.com/mahope/bugbottle-action" style="color:var(--color-accent);">bugbottle-action</a>',
        '<a href="https://github.com/mahope/bugbottle-action" style="color:var(--color-accent);">bugbottle-action</a> (<code>mahope/bugbottle-action@v1</code>)')
    if new != c:
        open(p, 'w').write(new)
        changed.append(p)
    p2 = f'{SITE}/blog/table-alignment-html-to-markdown.html'
    c = open(p2).read()
    new = c.replace('npx github:mahope/clean-copy-cli',
                    'npx github:mahope/clean-copy-cli@v1')
    if new != c:
        open(p2, 'w').write(new)
        changed.append(p2)
    return changed


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
    slug_en, html_en = en_page()
    slug_da, html_da = da_page()
    with open(f'{SITE}/blog/{slug_en}.html', 'w') as f:
        f.write(html_en)
    with open(f'{SITE}/blog/{slug_da}.html', 'w') as f:
        f.write(html_da)
    for slug, html in [(slug_en, html_en), (slug_da, html_da)]:
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        assert blocks, f'no JSON-LD in {slug}'
        for b in blocks:
            d = json.loads(b)
            assert d['@context'] == 'https://schema.org' and d['@type'] == 'TechArticle', slug
    print(f'{slug_en}.html + {slug_da}.html written, JSON-LD OK')
    update_sitemap([slug_en, slug_da])
    print('sitemap updated')
    changed = patch_existing()
    print('patched:', changed if changed else 'nothing (already tagged)')
    broken = check_links([f'{SITE}/blog/{slug_en}.html', f'{SITE}/blog/{slug_da}.html'])
    print('broken internal links:', broken if broken else 'none')


if __name__ == '__main__':
    main()
