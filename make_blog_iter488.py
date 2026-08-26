#!/usr/bin/env python3
"""Iteration 488: To nye blogpar (EN + DA) — funnel mod /page-profile (Pro $19/år).

1. broken-link-checker-free             -> da/blog/find-oedelaegge-links-hjemmeside

Moenster fra make_blog_iter487.py. Ingen eksterne soegninger.
"""
import json, re, os, sys
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

PAGES = [
    {
        'slug': 'find-oedelaegge-links-hjemmeside',
        'en_slug': 'broken-link-checker-free',
        'title': 'Find ødelagte links på din hjemmeside — gratis metoder (2026)',
        'h1': 'Find de ødelagte<br>links på sitet',
        'desc': ('Sådan finder du 404-fejl og døde links på en hel hjemmeside: gratis '
                 'online-tjek, browserudvidelser, terminalværktøjer og sitemap-crawl — '
                 'med fordele og ulemper ved hver metode.'),
        'og_desc': ('Broken link checker: find 404 errors and dead links on your website '
                    'with free methods — online checkers, browser extensions, CLI tools '
                    'and sitemap crawls compared.'),
        'badge': 'SEO &middot; GRATIS',
        'subtitle': ('Et enkelt dødt link koster tillid — og Google bemærker det også. '
                     'Her er fire måder at tjekke hele sitet på, fra nul-installation '
                     'til automatisering i CI.'),
        'cta1': '<a href="/page-profile" class="btn-primary">Analysér din side gratis &rarr;</a>',
        'cta2': '<a href="#metoder" class="btn-secondary">Se de 4 metoder</a>',
        'tool_url': '/page-profile',
        'tool_label': 'Tjek dit site nu',
        'hub_badge': 'SEO · VEDLIGEHOLD',
        'hub_title': 'Find ødelagte links på hjemmesiden',
        'hub_desc': 'Fire gratis metoder til at finde 404-fejl og døde links på et helt site.',
        'faq': [
            ("Hvorfor er ødelagte links et problem?",
             "De sender besøgende og søgemaskiner ind i 404-sider. Det koster tillid, "
             "spilder link-værdi (link equity) fra interne og eksterne links, og kan "
             "give dårligere placeringer over tid. Google Search Console rapporterer "
             "dem direkte under dækning."),
            ("Hvad er den hurtigste måde at tjekke ét site på?",
             "En online broken link checker eller et sitemap-crawl. Indsæt URL'en, vent "
             "et par minutter, og få en liste over alle links med deres HTTP-status. "
             "For større sites er et CLI-værktøj hurtigere og mere kontrollerbart."),
            ("Hvordan finder jeg dem automatisk fremover?",
             "Kør et link-tjek i din CI-pipeline ved hver udgivelse, eller planlæg et "
             "ugentligt crawl af sitemap.xml. GitHub Actions er gratis for offentlige "
             "reposer og kræver ingen server."),
            ("Skal alle 404'er fikses?",
             "Nej — nogle er bevidste (fjernede sider). Men de skal svare med en ordentlig "
             "404-side, og vigtige gamle URLs bør have en 301-redirect til det relevante "
             "indhold. Prioritér links fra sider med mest trafik og flest indgående links."),
        ],
        'body': '''
<section class="problem" id="metoder">
  <div class="container">
    <h2>Fire metoder — fra hurtigst til mest grundig</h2>
    <ol>
      <li><strong>Online checker:</strong> indsæt domænet i en gratis broken link
      checker. Færdig på minutter, men begrænset dybde på store sites.</li>
      <li><strong>Sitemap-crawl:</strong> hent sitemap.xml og test hver URL plus dens
      links. Dækker præcis de sider du selv anser for officielle.</li>
      <li><strong>Terminal:</strong> <code>wget --spider</code> eller et dedikeret
      CLI-værktøj giver fuld kontrol og output du kan scripte videre på.</li>
      <li><strong>CI-automatisering:</strong> kør tjekket ved hver deploy, så nye
      brudte links fanges inden publikum ser dem.</li>
    </ol>
<pre style="background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:0.9rem;"># Test én URL's statuskode
$ curl -s -o /dev/null -w "%{http_code}" https://ditside.dk/gammel-side

# Crawl hele sitet med wget (kun status, intet downloades)
$ wget --spider -r --no-parent https://ditside.dk 2&gt;&amp;1 | grep -B2 "404"</pre>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>Når du har fundet dem: sådan prioriterer du</h2>
    <p>Sortér efter hvor linket står, ikke kun efter fejlen. Et dødt link på din
    mest besøgte side koster mere end tyve på en arkivside. Tjek først:</p>
    <table style="width:100%;border-collapse:collapse;">
      <tr style="text-align:left;"><th>Placering</th><th>Hvorfor den tæller mest</th></tr>
      <tr><td>Forside og topnavigation</td><td>Første indtryk — alle ser dem</td></tr>
      <tr><td>Sider med mest organisk trafik</td><td>Direkte tab af besøgende</td></tr>
      <tr><td>Sider med mange indgående links</td><td>Spilder værdi andre har givet dig</td></tr>
      <tr><td>Konverteringsstien</td><td>Bryder købet midtvejs</td></tr>
    </table>
    <div style="text-align:center;margin-top:20px;">
      <a href="/page-profile" class="btn-primary">Få overblikket over dit site &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Læs videre</h2>
    <p>Læs også:
    <a href="/da/blog/find-alle-sider-paa-en-hjemmeside">find alle sider på et site</a>,
    <a href="/da/blog/tjek-url-redirect-kaede">tjek redirect-kæder</a> og
    <a href="/da/blog/teknisk-seo-tjek-hjemmeside">teknisk SEO-tjek</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/find-alle-sider-paa-en-hjemmeside" lang="da">Find alle sider</a> &middot; '
                    '<a href="/da/blog/tjek-url-redirect-kaede" lang="da">Redirect-kæder</a> &middot; '
                    '<a href="/da/blog/teknisk-seo-tjek-hjemmeside" lang="da">Teknisk SEO-tjek</a>'),
    },
]

EN = {
    'broken-link-checker-free': {
        'title': "Broken Link Checker — Find Dead Links on Any Site Free (2026)",
        'h1': 'Find the broken links<br>on your site',
        'desc': ('How to find 404 errors and dead links across a whole website: free '
                 'online checkers, browser extensions, CLI tools and sitemap crawls — '
                 'with the pros and cons of each method.'),
        'og_desc': ('Free broken link checking methods compared: online tools, sitemap '
                    'crawls, wget and CI automation. Find every 404 before your visitors do.'),
        'badge': 'SEO &middot; FREE',
        'subtitle': ("A single dead link costs trust — and search engines notice too. "
                     "Four ways to check your whole site, from zero-install to fully "
                     "automated in CI."),
        'body': '''
<section class="problem" id="guide">
  <div class="container">
    <h2>Four methods — from fastest to most thorough</h2>
    <ol>
      <li><strong>Online checker:</strong> paste your domain into a free broken link
      checker. Done in minutes, but depth is limited on large sites.</li>
      <li><strong>Sitemap crawl:</strong> fetch sitemap.xml and test every URL plus its
      links. Covers exactly the pages you consider official.</li>
      <li><strong>Terminal:</strong> <code>wget --spider</code> or a dedicated CLI tool
      gives full control and output you can pipe into scripts.</li>
      <li><strong>CI automation:</strong> run the check on every deploy so new broken
      links never reach visitors in the first place.</li>
    </ol>
<pre style="background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:0.9rem;"># Check one URL's status code
$ curl -s -o /dev/null -w "%{http_code}" https://yoursite.com/old-page

# Crawl an entire site with wget (status only, nothing downloaded)
$ wget --spider -r --no-parent https://yoursite.com 2&gt;&amp;1 | grep -B2 "404"</pre>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>Once you've found them: how to prioritize</h2>
    <p>Sort by where the link lives, not just by the error itself. One dead link on your
    most visited page costs more than twenty on an archive page. Check first:</p>
    <table style="width:100%;border-collapse:collapse;">
      <tr style="text-align:left;"><th>Location</th><th>Why it matters most</th></tr>
      <tr><td>Homepage and main navigation</td><td>First impression — everyone sees them</td></tr>
      <tr><td>Pages with the most organic traffic</td><td>Direct loss of visitors</td></tr>
      <tr><td>Pages with many backlinks</td><td>Wastes value others gave you</td></tr>
      <tr><td>The conversion path</td><td>Breaks the sale midway</td></tr>
    </table>
    <div style="text-align:center;margin-top:20px;">
      <a href="/page-profile" class="btn-primary">Get the full picture of your site &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Read next</h2>
    <p>Also read:
    <a href="/blog/find-all-pages-on-a-website">how to find all pages on a website</a>,
    <a href="/blog/check-url-redirect-chain">check redirect chains</a> and
    <a href="/blog/technical-seo-check-website">technical SEO checks</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/blog/find-all-pages-on-a-website">Find all pages</a> &middot; '
                    '<a href="/blog/check-url-redirect-chain">Redirect chains</a> &middot; '
                    '<a href="/blog/technical-seo-check-website">Technical SEO checks</a>'),
        'faq': [
            ("Why are broken links a problem?",
             "They send visitors and search engines into 404 pages. That costs trust, "
             "wastes link equity from internal and external links, and can hurt rankings "
             "over time. Google Search Console reports them directly under coverage."),
            ("What's the fastest way to check one site?",
             "An online broken link checker or a sitemap crawl. Paste the URL, wait a few "
             "minutes, get a list of every link with its HTTP status. For larger sites a "
             "CLI tool is faster and more controllable."),
            ("How do I catch them automatically going forward?",
             "Run a link check in your CI pipeline on every release, or schedule a weekly "
             "crawl of sitemap.xml. GitHub Actions is free for public repositories and "
             "needs no server."),
            ("Should every 404 be fixed?",
             "No — some are intentional (removed pages). But they should serve a proper "
             "404 page, and important old URLs deserve a 301 redirect to relevant content. "
             "Prioritize links from pages with the most traffic and backlinks."),
        ],
    },
}


def build_page(p):
    """DA page."""
    url = f'{BASE}/da/blog/{p["slug"]}'
    ld_article = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article',
        'headline': p['title'], 'description': p['desc'],
        'url': url,
        'datePublished': TODAY, 'dateModified': TODAY,
        'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
        'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    }, ensure_ascii=False)
    main_entity = [{"@type": "Question", "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p['faq']]
    ld_faq = json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage',
                         'mainEntity': main_entity}, ensure_ascii=False)
    faq_cards = '\n'.join(
        f'      <div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in p['faq'])
    return f'''<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{p['title']}</title>
<meta name="description" content="{p['desc']}">
<meta property="og:type" content="article">
<meta property="og:title" content="{p['title']}">
<meta property="og:description" content="{p['og_desc']}">
<meta property="og:image" content="{BASE}/deskuptime/og.png">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="en" href="{BASE}/blog/{p['en_slug']}">
<link rel="alternate" hreflang="da" href="{url}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{ld_article}</script>
<script type="application/ld+json">{ld_faq}</script>
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">{p['badge']}</div>
    <h1>{p['h1']}</h1>
    <p class="subtitle">{p['subtitle']}</p>
    <div class="hero-cta">
      {p['cta1']}
      {p['cta2']}
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 5 minutters læsning</p>
  </div>
</header>
{p['body']}
<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
{faq_cards}
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="{p['tool_url']}" class="btn-primary">{p['tool_label']} &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Relateret: {p['related']}</p></div>
<footer style="padding:32px 24px;">
  <p><a href="/da">Forside</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/page-profile">Page Profile</a> &middot; <a href="/da/#blog">Blog</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});document.addEventListener('click',function(ev){{var a=ev.target&&ev.target.closest?ev.target.closest('a[href]'):null;if(!a)return;var h=a.getAttribute('href')||'';var m=h.match(/^\\/(page-profile|deskuptime)(\\.html)?(#[^#]*)?$/);if(!m)return;try{{navigator.sendBeacon('/api/track',new Blob([JSON.stringify({{path:p,event:'cta-'+m[1]}})],{{type:'application/json'}}));}}catch(e){{}}}},true);}}catch(e){{}}}})();
</script>
</body>
</html>'''


def build_en(p):
    """EN mirror page, same structure, lang=en."""
    e = EN[p['en_slug']]
    url = f'{BASE}/blog/{p["en_slug"]}'
    ld_article = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article',
        'headline': e['title'], 'description': e['desc'],
        'url': url,
        'datePublished': TODAY, 'dateModified': TODAY,
        'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
        'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    }, ensure_ascii=False)
    main_entity = [{"@type": "Question", "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in e['faq']]
    ld_faq = json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage',
                         'mainEntity': main_entity}, ensure_ascii=False)
    faq_cards = '\n'.join(
        f'      <div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in e['faq'])
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e['title']}</title>
<meta name="description" content="{e['desc']}">
<meta property="og:type" content="article">
<meta property="og:title" content="{e['title']}">
<meta property="og:description" content="{e['og_desc']}">
<meta property="og:image" content="{BASE}/deskuptime/og.png">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="en" href="{url}">
<link rel="alternate" hreflang="da" href="{BASE}/da/blog/{p['slug']}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{ld_article}</script>
<script type="application/ld+json">{ld_faq}</script>
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">{e['badge']}</div>
    <h1>{e['h1']}</h1>
    <p class="subtitle">{e['subtitle']}</p>
    <div class="hero-cta">
      <a href="/page-profile" class="btn-primary">Analyse your site free &rarr;</a>
      <a href="#guide" class="btn-secondary">Jump to the guide</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; 5 min read</p>
  </div>
</header>
{e['body']}
<section class="products">
  <div class="container">
    <h2>Frequently asked questions</h2>
    <div class="problem-cards">
{faq_cards}
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/page-profile" class="btn-primary">Try the site analysis now &rarr;</a>
    </div>
  </div>
</section>

<p style="text-align:center;"><a href="/da/blog/{p['slug']}" lang="da">Danish version of this guide</a></p>
<div style="text-align:center;margin-top:16px;"><p>Related: {e['related']}</p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">Home</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/page-profile">Page Profile</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});document.addEventListener('click',function(ev){{var a=ev.target&&ev.target.closest?ev.target.closest('a[href]'):null;if(!a)return;var h=a.getAttribute('href')||'';var m=h.match(/^\\/(page-profile|deskuptime)(\\.html)?(#[^#]*)?$/);if(!m)return;try{{navigator.sendBeacon('/api/track',new Blob([JSON.stringify({{path:p,event:'cta-'+m[1]}})],{{type:'application/json'}}));}}catch(e){{}}}},true);}}catch(e){{}}}})();
</script>
</body>
</html>'''


def update_sitemap(slug_path):
    path = f'{SITE}/sitemap.xml'
    c = open(path).read()
    url = f'{BASE}/{slug_path}'
    if f'<loc>{url}</loc>' in c:
        print(f'sitemap: {slug_path} already present')
        return
    add = (f'  <url><loc>{url}</loc><lastmod>{TODAY}</lastmod>'
           f'<changefreq>weekly</changefreq><priority>0.8</priority></url>\n')
    c = c.replace('</urlset>', add + '</urlset>')
    open(path, 'w').write(c)
    print(f'sitemap: added {slug_path}')


def check_links(files):
    broken = []
    for path in files:
        html = open(path).read()
        for m in sorted(set(re.findall(r'href="(/[^"#]*?)"', html))):
            url = m.split('?')[0]
            t = ('site' + url).rstrip('/')
            if not (os.path.exists(t) or os.path.exists(t + '.html') or url == '/'
                    or os.path.exists(t + '/index.html')):
                broken.append((path, m))
    return broken


def verify_hub():
    files = {os.path.basename(f)[:-5] for f in glob_files()}
    hub = set(re.findall(r'href="/da/blog/([^"]+)"', open(f'{SITE}/da.html').read()))
    extra = hub - files
    missing = files - hub
    print(f'verify_hub: disk={len(files)} hub={len(hub)} missing_in_hub={sorted(missing)} dead_links={sorted(extra)}')
    assert not extra, f'hubbet linker til ikke-eksisterende sider: {extra}'


def glob_files():
    import glob as _g
    return _g.glob(f'{SITE}/da/blog/*.html')


def add_hub_card(p):
    path = f'{SITE}/da.html'
    c = open(path).read()
    card_url = f'/da/blog/{p["slug"]}'
    if card_url in c:
        print(f'hub: {p["slug"]} already present')
        return
    card = f'''
      <div class="product-card">
        <div class="product-badge product-badge-secondary">{p['hub_badge']}</div>
        <div class="product-body">
          <h3><a href="{card_url}" style="color:inherit;text-decoration:none;">{p['hub_title']}</a></h3>
          <p class="product-desc">{p['hub_desc']}</p>
          <div class="product-details"><span class="product-meta">📖 5 min</span><span class="product-meta">🇩🇰 Dansk guide</span></div>
          <a href="{card_url}" class="btn-secondary" style="margin-top:12px;">Læs guide →</a>
        </div>
      </div>
'''
    pos = c.rfind('<a href="/da/blog/')
    end = c.find('\n      </div>\n', pos)
    ins = end + len('\n      </div>\n')
    c = c[:ins] + card + c[ins:]
    open(path, 'w').write(c)
    print(f'hub: card added for {p["slug"]}')


def main():
    all_files = []
    for p in PAGES:
        da_out = f'{SITE}/da/blog/{p["slug"]}.html'
        en_out = f'{SITE}/blog/{p["en_slug"]}.html'
        assert not os.path.exists(da_out), f'{da_out} exists already'
        assert not os.path.exists(en_out), f'{en_out} exists already'
        for out, page in ((da_out, build_page(p)), (en_out, build_en(p))):
            with open(out, 'w') as f:
                f.write(page)
            blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL)
            for b in blocks:
                d = json.loads(b)
                assert d['@context'] == 'https://schema.org', d['@context']
            print(f'{out} written, JSON-LD OK ({len(blocks)} blocks)')
            if out.startswith(SITE + '/blog/'):
                update_sitemap('blog/' + os.path.basename(out)[:-5])
            else:
                update_sitemap('da/blog/' + p['slug'])
            all_files.append(out)
        add_hub_card(p)

    verify_hub()
    broken = check_links(all_files + [f'{SITE}/da.html'])
    if broken:
        print('BROKEN INTERNAL LINKS:')
        for path, link in broken:
            print(f'  {path} -> {link}')
        sys.exit(1)
    print('Internal link check: OK')


if __name__ == '__main__':
    main()
