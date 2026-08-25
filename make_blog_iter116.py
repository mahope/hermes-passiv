#!/usr/bin/env python3
"""Iteration 116: two SEO articles from the proven blog pattern:
- EN 'meta tag checker' -> /blog/meta-tag-checker
- DA pendant of the Open Graph article -> /da/blog/open-graph-tjekker
Same guarantees as make_blog_og_en.py: JSON-LD validated with json.loads,
sitemap dup-check + extensionless URLs, internal cross-links, link check."""
import json, re, os
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

def check_links(*paths):
    broken = []
    for path in paths:
        h = open(path).read()
        for m in set(re.findall(r'href="(/[^"#]*?)"', h)):
            url = m.split('?')[0]
            t = ('site' + url).rstrip('/')
            if not (os.path.exists(t) or os.path.exists(t + '.html')
                    or url == '/' or os.path.exists(t + '/index.html')):
                broken.append((path, m))
    return broken

def add_to_sitemap(slug_path):
    p = f'{SITE}/sitemap.xml'
    c = open(p).read()
    if f'{slug_path}</loc>' in c:
        print(f'{slug_path} already in sitemap, skipping')
        return
    assert '</urlset>' in c
    c = c.replace('</urlset>',
        f'  <url><loc>{BASE}{slug_path}</loc><lastmod>{TODAY}</lastmod>'
        f'<changefreq>weekly</changefreq><priority>0.8</priority></url>\n</urlset>')
    open(p, 'w').write(c)

# ══════════════════════════════════════════════════════════════════
# Article 1 — EN meta tag checker
# ══════════════════════════════════════════════════════════════════
slug1 = 'meta-tag-checker'
desc1 = ('Free meta tag checker for any URL: title, meta description, robots, '
         'canonical, viewport and social tags. See exactly what search engines '
         'and social platforms read from your page — no signup.')
ld1 = json.dumps({
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'Meta Tag Checker — inspect any page\u2019s meta tags (free)',
    'description': desc1,
    'url': f'{BASE}/blog/{slug1}',
    'datePublished': TODAY, 'dateModified': TODAY,
    'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
})
html1 = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Meta Tag Checker — Inspect Any Page's Meta Tags (Free)</title>
<meta name="description" content="{desc1}">
<meta property="og:type" content="article">
<meta property="og:title" content="Meta Tag Checker — free, one URL in, full report out">
<meta property="og:description" content="Check title, description, robots, canonical, viewport and social meta tags on any URL. Free, no signup.">
<meta property="og:image" content="{BASE}/cover.jpg">
<meta property="og:url" content="{BASE}/blog/{slug1}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Meta Tag Checker — free, one URL in, full report out">
<meta name="twitter:description" content="Check title, description, robots, canonical and social meta tags on any URL.">
<link rel="canonical" href="{BASE}/blog/{slug1}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{ld1}
</script>
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">BLOG &middot; TECHNICAL SEO</div>
    <h1>Meta Tag Checker<br>See What Crawlers See</h1>
    <p class="subtitle">Your page's meta tags decide how it looks in Google results, social shares and browser tabs — and whether crawlers index it at all. Paste a URL and see every tag a crawler reads.</p>
    <div class="hero-cta">
      <a href="#what-to-check" class="btn-primary">Read the guide</a>
      <a href="/page-profile" class="btn-secondary">Check a URL now &rarr;</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; 5 minute read</p>
  </div>
</header>

<section class="problem" id="what-to-check">
  <div class="container">
    <h2>The meta tags that actually matter</h2>
    <p>Most pages carry a dozen meta tags; only a handful affect traffic. A good checker reads the raw HTML response — the same thing a search engine crawler sees on first fetch — and reports each one's presence and validity.</p>
    <div class="problem-cards">
      <div class="card"><h3>🔍 Title tag</h3><p>Not strictly a meta tag, but the single strongest on-page signal. Aim for unique, descriptive titles of roughly 50–60 characters per page.</p></div>
      <div class="card"><h3>📝 Meta description</h3><p>Does not rank directly, but Google often shows it as the snippet. Missing or duplicated descriptions mean Google writes your ad copy for you.</p></div>
      <div class="card"><h3>🤖 Robots meta</h3><p><code>noindex</code> or <code>nofollow</code> here silently removes pages from search. It is the most common accidental traffic killer we see.</p></div>
      <div class="card"><h3>🔗 Canonical link</h3><p>Tells search engines which URL is the real one. Wrong canonicals merge your pages' value into someone else's URL — or into nothing.</p></div>
      <div class="card"><h3>📱 Viewport</h3><p><code>&lt;meta name="viewport"&gt;</code> controls mobile rendering. Missing it means an unreadable zoomed-out page on phones.</p></div>
      <div class="card"><h3>💬 Social tags</h3><p>Open Graph and twitter:card tags control share previews on LinkedIn, Facebook and X. They are invisible until someone shares your link.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="how-to-check">How to check meta tags on any page</h2>
    <p><strong>Option A — automated (recommended).</strong> Paste the URL into the <a href="/page-profile" style="color:var(--color-accent);">free page profiler</a>. In seconds you get the complete meta tag picture — title length, description length, robots directives, canonical target, viewport and all Open Graph / Twitter Card tags — alongside a full technical SEO report.</p>
    <p><strong>Option B — view source.</strong> Open the page, right-click, "View Page Source" and read the <code>&lt;head&gt;</code>. This shows what the server sent — which matters, because tags injected by JavaScript at runtime are invisible to most crawlers.</p>
    <p><strong>Option C — curl for developers.</strong> <code>curl -s https://example.com | grep -i '&lt;meta'</code> gives you the raw list in the terminal, perfect for quick CI checks.</p>
    <div class="problem-cards">
      <div class="card"><h3>📏 Length limits that matter</h3><p>Title truncates around 55–65 characters, description around 150–160. Longer is not punished — it is simply cut off mid-sentence.</p></div>
      <div class="card"><h3>🧩 One set per page</h3><p>Template-wide defaults mean every article shares one description. Most CMSs fix this with one SEO plugin or one template partial per content type.</p></div>
      <div class="card"><h3>🔁 After fixing</h3><p>Crawlers re-fetch on their own schedule. Request re-indexing in Google Search Console after deploying fixes to see them reflected within days rather than weeks.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="mistakes">Five meta tag mistakes worth checking for</h2>
    <p><strong>1. Staging robots tags left in production.</strong> A <code>noindex</code> carried over from staging quietly removes the whole site from Google. Check it first when traffic drops mysteriously.</p>
    <p><strong>2. Duplicate titles across pages.</strong> When ten pages share one title, search engines pick which to show — and users cannot tell them apart in results.</p>
    <p><strong>3. Canonical pointing at the homepage.</strong> A copy-pasted <code>&lt;link rel="canonical"&gt;</code> tells Google every page is a copy of the front page.</p>
    <p><strong>4. Missing viewport tag.</strong> The page renders desktop-width on phones and fails mobile usability — a ranking factor on Google.</p>
    <p><strong>5. JS-only meta tags.</strong> Single-page apps that set title and description client-side serve empty metadata to crawlers. Render tags server-side.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Frequently asked questions</h2>
    <div class="problem-cards">
      <div class="card"><h3>Is this checker free?</h3><p>Yes. The <a href="/page-profile" style="color:var(--color-accent);">page profiler</a> runs in your browser, needs no account, and returns the meta tags together with headings, links, images and performance hints.</p></div>
      <div class="card"><h3>Do meta keywords still matter?</h3><p>No. Google has ignored the meta keywords tag since 2009. Its presence neither helps nor hurts — most modern sites omit it entirely.</p></div>
      <div class="card"><h3>Why does my page show a different title in Google?</h3><p>Google may rewrite titles it considers unhelpful — too long, keyword-stuffed, or boilerplate. A concise, accurate title usually gets shown as written.</p></div>
      <div class="card"><h3>Can I bulk-check a whole site?</h3><p>Yes — the companion Python CLI outputs JSON per URL, so you can loop it over a sitemap and fail a build on missing descriptions. See the <a href="/blog/technical-seo-check-website" style="color:var(--color-accent);">technical SEO check guide</a>.</p></div>
      <div class="card"><h3>Danish version?</h3><p>There is a <a href="/blog/teknisk-seo-tjek-hjemmeside" style="color:var(--color-accent);">Danish technical SEO guide</a> and a fully Danish profiler at /da/page-profile.</p></div>
      <div class="card"><h3>What about social previews?</h3><p>Open Graph and Twitter Card tags are covered in detail in the <a href="/blog/open-graph-checker" style="color:var(--color-accent);">Open Graph checker guide</a>.</p></div>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/page-profile" class="btn-primary">Check your meta tags free &rarr;</a>
      &nbsp;&nbsp;
      <a href="/blog/open-graph-checker" class="btn-secondary">Open Graph checker guide &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Related guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">SEO</span><h3><a href="/blog/technical-seo-check-website" style="color:var(--color-accent);text-decoration:none;">Technical SEO check for your website</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">SEO · SOCIAL</span><h3><a href="/blog/open-graph-checker" style="color:var(--color-accent);text-decoration:none;">Open Graph checker — test your share previews</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">A11Y</span><h3><a href="/blog/accessibility-scanner-cli" style="color:var(--color-accent);text-decoration:none;">Accessibility scanning from the command line</a></h3></div>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
  <p><a href="/">&larr; Home</a> &middot; <a href="/scan">Free scanner</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
</body>
</html>'''

with open(f'{SITE}/blog/{slug1}.html', 'w') as f:
    f.write(html1)
for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html1, re.DOTALL):
    d = json.loads(b)
    assert d['@context'] == 'https://schema.org' and d['@type'] == 'Article'
add_to_sitemap(f'/blog/{slug1}')
print(f'{slug1}.html written, JSON-LD OK, sitemap updated')

# ══════════════════════════════════════════════════════════════════
# Article 2 — DA Open Graph pendant
# ══════════════════════════════════════════════════════════════════
os.makedirs(f'{SITE}/da/blog', exist_ok=True)
slug2 = 'open-graph-tjekker'
desc2 = ('Tjek enhver URLs Open Graph- og Twitter Card-tags gratis: og:title, '
         'og:description, og:image og twitter:card. Se hvordan dit link ser ud '
         'når det deles på LinkedIn, Facebook og X — uden tilmelding.')
ld2 = json.dumps({
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'Open Graph-tjekker — se hvordan dine links ser ud når de deles (gratis)',
    'description': desc2,
    'url': f'{BASE}/da/blog/{slug2}',
    'datePublished': TODAY, 'dateModified': TODAY,
    'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
})
html2 = f'''<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Open Graph-tjekker — Sådan ser dit link ud når det deles (gratis)</title>
<meta name="description" content="{desc2}">
<meta property="og:type" content="article">
<meta property="og:title" content="Open Graph-tjekker — gratis, én URL ind, preview ud">
<meta property="og:description" content="Tjek og:title, og:description, og:image og twitter:card på enhver URL. Se dit LinkedIn/Facebook/X-preview inden du poster.">
<meta property="og:image" content="{BASE}/cover.jpg">
<meta property="og:url" content="{BASE}/da/blog/{slug2}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Open Graph-tjekker — gratis, én URL ind, preview ud">
<meta name="twitter:description" content="Tjek Open Graph- og Twitter Card-tags på enhver URL.">
<link rel="canonical" href="{BASE}/da/blog/{slug2}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{ld2}
</script>
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">BLOG &middot; SOCIALE MEDIER</div>
    <h1>Open Graph-tjekker<br>Se Dit Link Før Du Poster Det</h1>
    <p class="subtitle">Hver gang nogen deler din side på LinkedIn, Facebook, X, Slack eller Teams, bygger platformen et kort ud fra dine Open Graph-tags — i stilhed. Tjek hvad platformen ser, før du trykker del.</p>
    <div class="hero-cta">
      <a href="#hvordan" class="btn-primary">Læs guiden</a>
      <a href="/da/page-profile" class="btn-secondary">Tjek en URL nu &rarr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 5 minutters læsning</p>
  </div>
</header>

<section class="problem" id="hvad-er-open-graph">
  <div class="container">
    <h2>Hvad Open Graph-tags egentlig gør</h2>
    <p>Når en URL sættes ind i et socialt netværk eller en chat-app, henter platformens crawler din side og læser fire meta-tags fra <code>og:</code>-navnerummet: <strong>og:title</strong>, <strong>og:description</strong>, <strong>og:image</strong> og <strong>og:url</strong>. X (Twitter) bruger de parallelle <code>twitter:card</code>-tags og falder tilbage til Open Graph, hvis de mangler.</p>
    <p>Mangler tagsne, gætter platformen — normalt dårligt: intet billede, en afkortet titel eller en beskrivelse skrabet fra tilfældig sidetekst. Er tagsne forkerte, vises det forkerte kort — og platformene cacher aggressivt: retter du tagsne i dag, retter det ikke kort der allerede er cachet.</p>
    <div class="problem-cards">
      <div class="card"><h3>🖼️ Billede-problemet</h3><p>Den hyppigste fejl: manglende og:image, relativt i stedet for absolut URL, mindre end 200&times;200 px, eller et billede bag login. Alt sammen giver intet billede i previewet.</p></div>
      <div class="card"><h3>🗄️ Cache-problemet</h3><p>Facebook og LinkedIn cacher deledata i dage. Ret først tagsne, og tving derefter en ny scraping med platformens debugger — ellers tester du gamle data.</p></div>
      <div class="card"><h3>✅ Ét tjek, alle tags</h3><p>En god tjekker validerer alle tags på én gang: tilstedeværelse, størrelser, absolutte URL'er, billedimensioner og twitter:card-fallbacks.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="hvordan">Sådan tjekker du dine Open Graph-tags</h2>
    <p><strong>Mulighed A — automatisk (anbefalet).</strong> Indsæt din URL i den <a href="/da/page-profile" style="color:var(--color-accent);">gratis side-profiler</a>. Ud over den fulde tekniske SEO-rapport får du det komplette Open Graph- og Twitter Card-billede: hvilke tags findes, opfylder og:image størrelseskravene, og har twitter:card fornuftige fallbacks.</p>
    <p><strong>Mulighed B — view-source.</strong> Åbn siden, vis kildekode, og søg efter <code>og:</code>. Der skal være mindst titel, beskrivelse, billede og url i &lt;head&gt;. Husk: tags renderet af JavaScript er usynlige for de fleste platform-crawlere — de skal stå i det rå HTML-svar.</p>
    <p><strong>Mulighed C — platformenes debuggere.</strong> Efter rettelsen kører du Facebooks Sharing Debugger og LinkedIns Post Inspector for at tvinge deres cache opdateret og bekræfte det nye kort. Hver platform cacher uafhængigt.</p>
    <div class="problem-cards">
      <div class="card"><h3>📏 Tommelfingerregler for billeder</h3><p>1200&times;630 px, absolut URL, under ~8 MB, offentligt tilgængeligt, PNG eller JPEG. Det består alle store platformers krav med margen.</p></div>
      <div class="card"><h3>✍️ Længder på titel og beskrivelse</h3><p>Kort afkortes omkring 55–65 tegns titel og ~110–160 tegns beskrivelse afhængigt af platform. Sæt de vigtige ord først.</p></div>
      <div class="card"><h3>🧩 Tags pr. side</h3><p>Ét delt sæt OG-tags på hele sitet betyder at alle artikler viser forsides-kortet. Generér dem pr. skabelon — de fleste CMS'er kan det med ét plugin eller én meta-partiel.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Fem Open Graph-fejl der dræber klik</h2>
    <p><strong>1. Manglende og:image helt.</strong> Opslag uden billeder får markant mindre engagement på alle platforme. Det er den værdifuldeste rettelse på listen.</p>
    <p><strong>2. Relative billed-URL'er.</strong> <code>&lt;meta property="og:image" content="/img/cover.jpg"&gt;</code> virker i en browser men viser ingenting i et dele-preview. Altid absolut.</p>
    <p><strong>3. JavaScript-injicerede tags.</strong> Platform-crawlere kører mest ikke JS. Sætter din SPA tags ved runtime, viser delinger ingenting. Render tags server-side.</p>
    <p><strong>4. Identiske tags overalt.</strong> Skabelon-standarder der siver ud på artikler gør hver deling ens — og brugere holder op med at klikke.</p>
    <p><strong>5. Glemte twitter:card.</strong> Uden <code>twitter:card</code> (normalt <code>summary_large_image</code>) falder X tilbage til en lille, nøgen summary. Én linje fikser det.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
      <div class="card"><h3>Er tjekkeren gratis?</h3><p>Ja. <a href="/da/page-profile" style="color:var(--color-accent);">Side-profileren</a> kører i din browser, kræver ingen konto, og dækker Open Graph, Twitter Cards samt resten af sidens tekniske sundhed i samme rapport.</p></div>
      <div class="card"><h3>Hvorfor vises min rettelse ikke endnu?</h3><p>Platform-cache. Brug Facebooks Sharing Debugger og LinkedIns Post Inspector til at tvinge en ny scraping efter deploy. Indtil ser du på gamle cachede data.</p></div>
      <div class="card"><h3>Påvirker OG-tags SEO-placeringer?</h3><p>Ikke direkte — Google læser titel/meta-beskrivelse, ikke og:-tags, til placering. Men dele-previews driver klik og trafik, og et ødelagt preview dræber den kanal lydløst.</p></div>
      <div class="card"><h3>Hvad med WhatsApp, Slack, iMessage?</h3><p>Alle læser Open Graph-tags. Samme regler gælder: absolutte billed-URL'er, server-renderede tags, fornuftige dimensioner.</p></div>
      <div class="card"><h3>Engelsk version?</h3><p>Der er en <a href="/blog/open-graph-checker" style="color:var(--color-accent);">engelsk Open Graph-guide</a> og en engelsk profiler på /page-profile.</p></div>
      <div class="card"><h3>Kan jeg automatisere det i CI?</h3><p>Ja — Python CLI'en udskriver JSON for enhver URL, så en pipeline kan fejle et build når og:image forsvinder. Se den <a href="/blog/technical-seo-check-website" style="color:var(--color-accent);">engelske tekniske SEO-guide</a>.</p></div>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/da/page-profile" class="btn-primary">Tjek din URL gratis &rarr;</a>
      &nbsp;&nbsp;
      <a href="/blog/teknisk-seo-tjek-hjemmeside" class="btn-secondary">Teknisk SEO-guide &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Relaterede guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">SEO · DA</span><h3><a href="/blog/teknisk-seo-tjek-hjemmeside" style="color:var(--color-accent);text-decoration:none;">Teknisk SEO-tjek af din hjemmeside</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">SEO</span><h3><a href="/blog/open-graph-checker" style="color:var(--color-accent);text-decoration:none;">Open Graph checker (engelsk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">A11Y</span><h3><a href="/blog/eaa-accessibility-checklist" style="color:var(--color-accent);text-decoration:none;">EAA-accessibility checklist</a></h3></div>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
  <p><a href="/"> &larr; Forside</a> &middot; <a href="/da/page-profile">Side-profiler</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
</body>
</html>'''

with open(f'{SITE}/da/blog/{slug2}.html', 'w') as f:
    f.write(html2)
for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html2, re.DOTALL):
    d = json.loads(b)
    assert d['@context'] == 'https://schema.org' and d['@type'] == 'Article'
add_to_sitemap(f'/da/blog/{slug2}')
print(f'{slug2}.html written, JSON-LD OK, sitemap updated')

# ══════════════════════════════════════════════════════════════════
# Cross-links
# ══════════════════════════════════════════════════════════════════
pp = f'{SITE}/page-profile.html'
pc = open(pp).read()
if '/blog/meta-tag-checker' not in pc:
    anchor = '<a href="/blog/open-graph-checker">Open Graph checker</a>'
    assert anchor in pc, 'EN footer anchor missing'
    pc = pc.replace(anchor, anchor + ' · <a href="/blog/meta-tag-checker">Meta tag checker</a>')
    open(pp, 'w').write(pc)
    print('EN page-profile footer link added')
dpp = f'{SITE}/da/page-profile.html'
dc = open(dpp).read()
if '/da/blog/open-graph-tjekker' not in dc:
    # append a related-guides section before last closing section
    k = dc.rfind('</section>')
    xlink = ('\n<section class="products">\n  <div class="container">\n'
             '    <h2>Guides på dansk</h2>\n'
             '    <p>Læs guiden <a href="/da/blog/open-graph-tjekker" style="color:var(--color-accent);">Open Graph-tjekker</a> — se hvordan dine links ser ud når de deles.</p>\n'
             '  </div>\n</section>\n')
    dc = dc[:k] + xlink + dc[k:]
    open(dpp, 'w').write(dc)
    print('DA page-profile link added')
og_en = f'{SITE}/blog/open-graph-checker.html'
oc = open(og_en).read()
if '/blog/meta-tag-checker' not in oc:
    anchor = '<a href="/blog/technical-seo-check-website" style="color:var(--color-accent);text-decoration:none;">Technical SEO check for your website</a>'
    assert anchor in oc, 'OG related anchor missing'
    oc = oc.replace(anchor, anchor.replace('</a>', '') + ' → also see the <a href="/blog/meta-tag-checker" style="color:var(--color-accent);text-decoration:none;">meta tag checker</a></a>'.replace('</a></a>', '</a>'))
    open(og_en, 'w').write(oc)
    print('OG article cross-link added')

# ── Link check ──────────────────────────────────────────────────
broken = check_links(f'{SITE}/blog/{slug1}.html', f'{SITE}/da/blog/{slug2}.html', pp, dpp, og_en)
print('broken internal links:', broken if broken else 'none')
print('Done.')
