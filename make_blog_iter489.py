#!/usr/bin/env python3
"""Iteration 489: To nye blogpar (EN + DA) — metadata checker, funnel mod /page-profile.

1. website-metadata-checker            -> da/blog/tjek-din-hjemmesides-meta-tags

Moenster fra make_blog_iter488.py. Ingen eksterne soegninger.
"""
import json, re, os, sys, glob as _g
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

PAGES = [
    {
        'slug': 'tjek-din-hjemmesides-meta-tags',
        'en_slug': 'website-metadata-checker',
        'title': 'Tjek din hjemmesides meta-tags — gratis metoder (2026)',
        'h1': 'Tjek din sides<br>meta-tags',
        'desc': ('Sådan tjekker du en hjemmesides meta-tags: title, description, Open Graph, '
                 'Twitter-kort og struktureret data — gratis online-tjek, browserfunktioner '
                 'og terminalkommandoer med fordele og ulemper.'),
        'og_desc': ('Free ways to check any page\'s meta tags: title, description, Open Graph, '
                    'Twitter cards and structured data — online checkers, view-source and '
                    'terminal commands compared.'),
        'badge': 'SEO &middot; GRATIS',
        'subtitle': ('Meta-tags er det første Google og de sociale medier ser af din side. '
                     'Her er fire måder at tjekke dem på, fra nul-installation til '
                     'automatisering i CI.'),
        'cta1': '<a href="/page-profile" class="btn-primary">Analysér din side gratis &rarr;</a>',
        'cta2': '<a href="#metoder" class="btn-secondary">Se de 4 metoder</a>',
        'tool_url': '/page-profile',
        'tool_label': 'Tjek dit site nu',
        'hub_badge': 'SEO · META-TAGS',
        'hub_title': 'Tjek din hjemmesides meta-tags',
        'hub_desc': 'Fire gratis metoder til at tjekke title, description, OG-tags og mere.',
        'faq': [
            ("Hvilke meta-tags betyder mest for SEO?",
             "Title-tag og meta description er de vigtigste: de er teksten i søgeresultatet. "
             "Canonical hreflang og robots-meta styrer indeksering, mens Open Graph- og "
             "Twitter-tags primært påvirker hvordan siden vises når den deles."),
            ("Hvorfor viser Facebook et forkert billede når jeg deler min side?",
             "Næsten altid et mangelfuldt eller cachet Open Graph-tag. Tjek at og:image, "
             "og:title og og:description findes og er mindst 1200x630 px, og tving en ny "
             "cachning i delings-debuggeren efter rettelser."),
            ("Kan jeg tjekke meta-tags uden et værktøj?",
             "Ja — højreklik og vælg Vis kilde, eller brug curl. Alle meta-tags står i "
             "head-sektionen. Det er hurtigt til én side, men upraktisk hvis du skal gennemgå "
             "et helt site."),
            ("Hvordan overvåger jeg meta-tags automatisk?",
             "Kør et script i CI der henter hver vigtige side og validerer at title, description "
             "og canonical findes og har rimelige længder. Så fanger du fejl inden udgivelsen "
             "i stedet for efter."),
        ],
        'body': '''
<section class="problem" id="metoder">
  <div class="container">
    <h2>Fire metoder — fra hurtigst til mest grundig</h2>
    <ol>
      <li><strong>Online checker:</strong> indsæt URL'en i en gratis metadata-checker.
      Færdig på sekunder og viser OG-preview — men kun én side ad gangen.</li>
      <li><strong>Vis kilde:</strong> højreklik &rarr; Vis kilde. Alle tags står i
      head-sektionen. Gratis, men manuelt.</li>
      <li><strong>Terminal:</strong> hent HTML'en med curl og filtrér meta-tags ud.
      Scriptbar og perfekt til hurtige tjek.</li>
      <li><strong>CI-automatisering:</strong> validér titel, description og canonical ved
      hver deploy, så fejl aldrig når publikum.</li>
    </ol>
<pre style="background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:0.9rem;"># Se alle meta-tags på én side
$ curl -s https://ditside.dk | grep -o '&lt;meta[^&gt;]*&gt;' | head -20

# Kun title og description
$ curl -s https://ditside.dk | grep -Eo '&lt;title&gt;.*&lt;/title&gt;|name="description" content="[^"]*"'</pre>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>Sådan skal et sundt sæt meta-tags se ud</h2>
    <table style="width:100%;border-collapse:collapse;">
      <tr style="text-align:left;"><th>Tag</th><th>Tommelfingerregel</th></tr>
      <tr><td>&lt;title&gt;</td><td>30–60 tegn, unik pr. side, vigtigste ord først</td></tr>
      <tr><td>meta description</td><td>120–158 tegn, konkret budskab + call-to-action</td></tr>
      <tr><td>canonical</td><td>Én pr. side, peger på sig selv (absolut URL)</td></tr>
      <tr><td>og:title / og:description / og:image</td><td>Spejler title/description; billede mindst 1200x630</td></tr>
      <tr><td>robots</td><td>Kun til stede når du vil fraråde indeksering</td></tr>
    </table>
    <div style="text-align:center;margin-top:20px;">
      <a href="/page-profile" class="btn-primary">Få metadata-tjekket automatisk &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Læs videre</h2>
    <p>Læs også:
    <a href="/da/blog/find-oedelaegge-links-hjemmeside">find ødelagte links</a>,
    <a href="/da/blog/tjek-url-redirect-kaede">tjek redirect-kæder</a> og
    <a href="/da/blog/teknisk-seo-tjek-hjemmeside">teknisk SEO-tjek</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/find-oedelaegge-links-hjemmeside" lang="da">Ødelagte links</a> &middot; '
                    '<a href="/da/blog/tjek-url-redirect-kaede" lang="da">Redirect-kæder</a> &middot; '
                    '<a href="/da/blog/teknisk-seo-tjek-hjemmeside" lang="da">Teknisk SEO-tjek</a>'),
    },
]

EN = {
    'website-metadata-checker': {
        'title': "Website Metadata Checker — Check Any Page's Meta Tags Free (2026)",
        'h1': "Check your page's<br>meta tags",
        'desc': ("How to check a webpage's meta tags: title, description, Open Graph, Twitter "
                 "cards and structured data — free online checkers, view-source tricks and "
                 "terminal commands, with the pros and cons of each method."),
        'og_desc': ("Free website metadata checking methods compared: online tools, view-source "
                    "and curl. Verify title, description, Open Graph and canonical before your "
                    "visitors do."),
        'badge': 'SEO &middot; FREE',
        'subtitle': ("Meta tags are the first thing Google and social networks read on your page. "
                     "Four ways to check them, from zero-install to fully automated in CI."),
        'body': '''
<section class="problem" id="guide">
  <div class="container">
    <h2>Four methods — from fastest to most thorough</h2>
    <ol>
      <li><strong>Online checker:</strong> paste the URL into a free metadata checker.
      Done in seconds and shows the social preview — but one page at a time.</li>
      <li><strong>View source:</strong> right-click &rarr; View Page Source. Every tag lives
      in the head section. Free, but manual.</li>
      <li><strong>Terminal:</strong> fetch the HTML with curl and filter out the meta tags.
      Scriptable and perfect for quick checks.</li>
      <li><strong>CI automation:</strong> validate title, description and canonical on every
      deploy so errors never reach visitors.</li>
    </ol>
<pre style="background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:0.9rem;"># See every meta tag on one page
$ curl -s https://yoursite.com | grep -o '&lt;meta[^&gt;]*&gt;' | head -20

# Just the title and description
$ curl -s https://yoursite.com | grep -Eo '&lt;title&gt;.*&lt;/title&gt;|name="description" content="[^"]*"'</pre>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>What a healthy set of meta tags looks like</h2>
    <table style="width:100%;border-collapse:collapse;">
      <tr style="text-align:left;"><th>Tag</th><th>Rule of thumb</th></tr>
      <tr><td>&lt;title&gt;</td><td>30–60 characters, unique per page, most important words first</td></tr>
      <tr><td>meta description</td><td>120–158 characters, concrete message plus a reason to click</td></tr>
      <tr><td>canonical</td><td>Exactly one per page, self-referencing (absolute URL)</td></tr>
      <tr><td>og:title / og:description / og:image</td><td>Mirror title/description; image at least 1200x630</td></tr>
      <tr><td>robots</td><td>Only present when you want to discourage indexing</td></tr>
    </table>
    <div style="text-align:center;margin-top:20px;">
      <a href="/page-profile" class="btn-primary">Get your metadata checked automatically &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Read next</h2>
    <p>Also read:
    <a href="/blog/broken-link-checker-free">broken link checkers</a>,
    <a href="/blog/check-url-redirect-chain">check redirect chains</a> and
    <a href="/blog/technical-seo-check-website">technical SEO checks</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/blog/broken-link-checker-free">Broken link checkers</a> &middot; '
                    '<a href="/blog/check-url-redirect-chain">Redirect chains</a> &middot; '
                    '<a href="/blog/technical-seo-check-website">Technical SEO checks</a>'),
        'faq': [
            ("Which meta tags matter most for SEO?",
             "The title tag and meta description are the big two: they form the text in the "
             "search result. Canonical, hreflang and robots meta control indexing, while Open "
             "Graph and Twitter tags mainly affect how the page looks when shared."),
            ("Why does Facebook show the wrong image when I share my page?",
             "Almost always missing or cached Open Graph data. Verify that og:image, og:title "
             "and og:description exist and that the image is at least 1200x630 px, then force a "
             "re-scrape in the sharing debugger after fixing."),
            ("Can I check meta tags without a tool?",
             "Yes — right-click and choose View Page Source, or use curl. All meta tags live in "
             "the head section. It's fast for one page but impractical when auditing a whole site."),
            ("How do I monitor meta tags automatically?",
             "Run a script in CI that fetches each important page and validates that title, "
             "description and canonical exist with sensible lengths. That catches mistakes "
             "before release instead of after."),
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
    <p class="hero-note">Opdateret august 2026 &middot; 5 minutters l&aelig;sning</p>
  </div>
</header>
{p['body']}
<section class="products">
  <div class="container">
    <h2>Ofte stillede sp&oslash;rgsm&aring;l</h2>
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
  <p><a href="/da">Forside</a> &middot; <a href="/free-tools">Gratis v&aelig;rkt&oslash;jer</a> &middot; <a href="/page-profile">Page Profile</a> &middot; <a href="/da/#blog">Blog</a></p>
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
    files = {os.path.basename(f)[:-5] for f in _g.glob(f'{SITE}/da/blog/*.html')}
    hub = set(re.findall(r'href="/da/blog/([^"]+)"', open(f'{SITE}/da.html').read()))
    extra = hub - files
    missing = files - hub
    print(f'verify_hub: disk={len(files)} hub={len(hub)} missing_in_hub={sorted(missing)} dead_links={sorted(extra)}')
    assert not extra, f'hubbet linker til ikke-eksisterende sider: {extra}'


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
          <a href="{card_url}" class="btn-secondary" style="margin-top:12px;">L&aelig;s guide →</a>
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
