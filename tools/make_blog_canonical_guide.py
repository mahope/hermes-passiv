#!/usr/bin/env python3
"""Iteration 449: Canonical URL Checker & Guide (EN + DA).

- site/blog/canonical-url-guide.html (EN)
- site/da/blog/canonisk-url-guide.html (DA)
- House template, Article+FAQPage JSON-LD, canonical/hreflang pair,
  CTA to /page-profile (checks canonical URLs), cross-links to existing
  SEO posts, sitemap entries, backlinks from blog index.
"""
import json, re, os

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-26'
SLUG_EN = 'canonical-url-guide'
SLUG_DA = 'canonisk-url-guide'
URL_EN = f'{BASE}/blog/{SLUG_EN}'
URL_DA = f'{BASE}/da/blog/{SLUG_DA}'
ROOT = '/Users/madsholstjensen/hermes-passiv/site'

FAQS_EN = [
    ('What is a canonical URL?',
     'A canonical URL is a <link rel="canonical"> tag in the <head> of a page that tells '
     'search engines which version of a page is the authoritative one. When you have '
     'duplicate or near-duplicate pages (same content at different URLs), the canonical '
     'tag prevents search engines from splitting ranking signals between them.'),
    ('How do canonical URLs affect SEO?',
     'They consolidate ranking signals — links, content, and authority — to one preferred '
     'URL. Without them, Google may pick the "wrong" URL as canonical, split PageRank '
     'across duplicates, or index dozens of near-identical pages instead of one. A single '
     'misconfigured canonical is rarely fatal, but systematic errors across a site silently '
     'cap your organic performance.'),
    ('What is a self-referencing canonical?',
     'A canonical URL that points to the page itself. Every indexable page should have a '
     'self-referencing canonical. Even if nothing is duplicated, it is the strongest signal '
     'that this page is the version you want ranked. Many CMS platforms (WordPress, Shopify, '
     'Webflow) set these automatically, but static generators, legacy sites and hand-coded '
     'pages often omit them.'),
    ('Canonical vs. noindex — which should I use?',
     'Use canonical when you have multiple URLs showing the same content and you want one '
     'of them to rank. Use noindex when you want a page out of search results entirely. '
     'They solve different problems: canonical consolidates, noindex excludes. Combining '
     'them (canonical + noindex) is treated by Google as a noindex — the canonical is ignored.'),
    ('How do I check if my canonical URLs are correct?',
     'The simplest way is to inspect the <head> of each page: look for '
     '<code>&lt;link rel="canonical" href="..."&gt;</code>. For more than a handful of pages, '
     'use a CLI tool like <a href="/page-profile">page-profile</a> which checks canonical '
     'presence, validity and conflicts across a list of URLs automatically.'),
    ('Can a canonical URL point to a different domain?',
     'Yes, Google supports cross-domain canonicals — often used when syndicating content or '
     'when the same article appears on two domains you own. Most other search engines ignore '
     'cross-domain canonicals, so use this only when absolutely necessary.'),
    ('What happens when two pages canonical to each other?',
     'A canonical conflict (A canonicals to B, B canonicals to A) is one of the worst SEO '
     'mistakes. Search engines see a loop and may pick neither, leaving all duplicate '
     'versions in the index without consolidated ranking. Always ensure canonical chains '
     'are acyclic and point to the definitive URL.'),
    ('Does page-profile check canonical URLs?',
     'Yes. <a href="/page-profile">page-profile</a> reports whether a canonical tag is present, '
     'whether it is self-referencing, and flags potential issues. The free version checks one '
     'URL at a time; Pro adds batch mode for scanning your whole sitemap.'),
]

ARTICLE_EN = {
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'Canonical URL Guide: How to Set, Check, and Fix Them',
    'description': 'Learn what canonical URLs are, why they matter for SEO, and how to check every page of your site for missing, conflicting, or broken canonicals — automatically with a CLI tool.',
    'url': URL_EN, 'datePublished': TODAY, 'dateModified': TODAY,
    'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
}
FAQPAGE_EN = {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    'mainEntity': [{'@type': 'Question', 'name': q,
                    'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQS_EN],
}

FAQS_DA = [
    ('Hvad er en kanonisk URL?',
     'En kanonisk URL er et <link rel="canonical">-tag i sidens <head>, der fortæller '
     'søgemaskinerne, hvilken version af en side der er den autoritative. Når du har '
     'duplikat- eller næsten-duplikatsider (samme indhold på forskellige URL\'er), '
     'forhindrer det kanoniske tag, at søgemaskinerne deler rangsignaler imellem dem.'),
    ('Hvordan påvirker kanoniske URL\'er SEO?',
     'De samler rangsignaler — links, indhold og autoritet — til én foretrukken URL. '
     'Uden dem kan Google vælge den "forkerte" URL som kanonisk, splitte PageRank på '
     'tværs af dubletter eller indeksere snesevis af næsten-identiske sider i stedet for én.'),
    ('Hvad er en selvrefererende kanonisk URL?',
     'En kanonisk URL der peger på siden selv. Hver side der skal indekseres, bør have '
     'en selvrefererende canonical. Selv hvis intet er duplikeret, er det det stærkeste '
     'signal om, at denne side er den version du ønsker rangeret.'),
    ('Kanonisk URL vs. noindex — hvornår bruger jeg hvad?',
     'Brug canonical når flere URL\'er viser samme indhold og du vil have én af dem til '
     'at ranke. Brug noindex når du vil have en side helt ud af søgeresultaterne. '
     'Kombinerer du dem (canonical + noindex), behandler Google det som noindex — '
     'canonical ignoreres.'),
    ('Hvordan tjekker jeg om mine kanoniske URL\'er er korrekte?',
     'Den enkleste metode er at inspicere <head> på hver side og lede efter '
     '<code>&lt;link rel="canonical" href="..."&gt;</code>. Har du mere end en håndfuld sider, '
     'kan du bruge et CLI-værktøj som <a href="/da/page-profile">page-profile</a>, '
     'der automatisk tjekker canonical-tags på tværs af en liste af URL\'er.'),
    ('Kan en kanonisk URL pege på et andet domæne?',
     'Ja, Google understøtter tværdomæne-canonicals — ofte brugt ved syndikering af '
     'indhold eller når samme artikel optræder på to domæner du ejer. De fleste andre '
     'søgemaskiner ignorerer tværdomæne-canonicals, så brug det kun når det er strengt nødvendigt.'),
    ('Hvad sker der når to sider canonical til hinanden?',
     'En canonical-konflikt (A canonical til B, B canonical til A) er en af de værste '
     'SEO-fejl. Søgemaskinerne ser en løkke og vælger måske ingen af dem, hvilket efterlader '
     'alle dubletversioner i indekset uden samlet rangering.'),
    ('Tjekker page-profile kanoniske URL\'er?',
     'Ja. <a href="/da/page-profile">page-profile</a> rapporterer om et canonical-tag findes, '
     'om det er selvrefererende, og markerer potentielle problemer. Gratis-versionen tjekker '
     'én URL ad gangen; Pro tilføjer batch-tilstand til scanning af hele dit sitemap.'),
]

ARTICLE_DA = dict(ARTICLE_EN,
    headline='Guide til kanoniske URL\'er: Sådan sætter, tjekker og retter du dem',
    description='Lær hvad kanoniske URL\'er er, hvorfor de betyder noget for SEO, og hvordan du automatisk tjekker hver side på dit site for manglende, konfliktskabende eller ødelagte canonicals.',
    url=URL_DA)
FAQPAGE_DA = {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    'mainEntity': [{'@type': 'Question', 'name': q,
                    'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQS_DA],
}
for b in (ARTICLE_EN, FAQPAGE_EN, ARTICLE_DA, FAQPAGE_DA):
    assert b['@context'] == 'https://schema.org'
    json.loads(json.dumps(b, ensure_ascii=False))

STYLE = '''
  .compare {{ width:100%; border-collapse:collapse; font-size:0.92rem; margin:1.5rem 0; }}
  .compare th, .compare td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--color-border); vertical-align:top; }}
  .compare th {{ border-bottom:2px solid var(--color-border); }}
  pre.cmd {{
    background:#0f172a; color:#e2e8f0; padding:14px 16px; border-radius:8px;
    overflow-x:auto; font-size:0.85rem; line-height:1.6; margin:0.8rem 0;
  }}
  pre.cmd code {{ font-family:'SF Mono','Monaco','Fira Code',monospace; }}
'''

TRACK = '''<script>
(function(){try{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:p}),keepalive:true}).catch(function(){});}catch(e){}});
</script>'''


def head(lang, title, desc, url, alt_url, alt_lang, article, faqpage):
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/cover.jpg">
<meta property="og:site_name" content="Hermes Passiv">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="{alt_lang}" href="{alt_url}">
<link rel="alternate" hreflang="x-default" href="{url}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{json.dumps(article, ensure_ascii=False)}
</script>
<script type="application/ld+json">
{json.dumps(faqpage, ensure_ascii=False)}
</script>
<script defer src="/track.js"></script>
<style>{STYLE}</style>
</head>'''


def faq_cards(faqs):
    return '\\n'.join(f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in faqs)


# ---------------- EN ----------------
en_body = f'''
<body>
<header class="hero">
  <div class="container">
    <div class="badge">SEO &middot; CANONICAL &middot; GUIDE</div>
    <h1>Canonical URL Guide:<br>How to Set, Check, and Fix Them</h1>
    <p class="subtitle">Canonical tags are one of the most misunderstood SEO signals — and one of the most impactful to get right. A single broken canonical can split your traffic between duplicate URLs for months. Here is how to check every page in minutes.</p>
    <div class="hero-cta">
      <a href="#checklist" class="btn-primary">How to check your canonicals &rarr;</a>
      <a href="/page-profile" class="btn-secondary">Check them automatically with page-profile</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; 5 minute read</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>Why canonical URLs matter</h2>
    <p>A canonical URL (<code>&lt;link rel="canonical" href="..."&gt;</code>) tells search engines which version of a page is the definitive one. Without it, Google has to guess — and it often guesses wrong, especially on sites with URL parameters, multiple paths to the same content, or syndicated articles. The result is diluted ranking signals and lower organic performance.</p>
    <div class="problem-cards">
      <div class="card"><h3>🔗 Consolidates link equity</h3><p>All backlinks, shares and engagement on duplicate URLs should flow to one canonical page. Without a canonical, each duplicate competes rather than contributes.</p></div>
      <div class="card"><h3>📋 Prevents duplicate content</h3><p>Google penalises nothing for duplicate content — but it does split the index across duplicates, so none ranks as strongly as a single consolidated page would.</p></div>
      <div class="card"><h3>🔍 You control which URL ranks</h3><p>Canonical tags let you choose whether <code>/blog/post</code> or <code>/blog/post?ref=share</code> or <code>/2024/blog/post</code> appears in results. Without one, Google picks for you.</p></div>
    </div>
  </div>
</section>

<section class="products" id="checklist">
  <div class="container">
    <h2>Common canonical mistakes (and how to spot them)</h2>
    <table class="compare">
      <thead><tr><th>#</th><th>Issue</th><th>What to check</th><th>Fix</th></tr></thead>
      <tbody>
        <tr><td>1</td><td>Missing canonical tag</td><td>Does the page have <code>&lt;link rel="canonical"&gt;</code> at all?</td><td>Add a self-referencing canonical to the <code>&lt;head&gt;</code> of every indexable page.</td></tr>
        <tr><td>2</td><td>Non-self-referencing canonical</td><td>Does the canonical point to <em>this</em> page or to a different page?</td><td>If this is the canonical version, it should reference itself.</td></tr>
        <tr><td>3</td><td>Relative canonical URL</td><td>Is the href an absolute URL or relative path?</td><td>Always use absolute URLs — <code>https://example.com/page</code>, not <code>/page</code>.</td></tr>
        <tr><td>4</td><td>Canonical chain loop</td><td>A canonicals to B, B canonicals to A.</td><td>Break the loop. Trace the chain to a single final destination.</td></tr>
        <tr><td>5</td><td>Canonical + noindex together</td><td>Does the page have both a canonical tag and <code>noindex</code>?</td><td>Remove one: Google treats the pair as noindex and ignores the canonical.</td></tr>
        <tr><td>6</td><td>Cross-domain canonical to wrong domain</td><td>Does the canonical point to a domain you don't control?</td><td>Unless you are deliberately syndicating, keep canonicals on your own domain.</td></tr>
        <tr><td>7</td><td>HTTP→HTTPS mismatch</td><td>Canonical points to <code>http://</code> on an HTTPS site.</td><td>Update to the HTTPS version. Mixing protocols confuses the signal.</td></tr>
        <tr><td>8</td><td>Trailing slash mismatch</td><td>Canonical includes <code>/page/</code> but the page URL is <code>/page</code> (or vice versa).</td><td>Be consistent. Pick one convention and stick to it site-wide.</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section class="products" id="automate">
  <div class="container">
    <h2>Check every page automatically</h2>
    <p>Inspecting the canonical tag on each page by hand is feasible for five pages — not for fifty or five hundred. The free, open-source <a href="/page-profile" style="color:var(--color-accent);">page-profile</a> CLI checks canonical presence, self-reference status, absolute URL format and more against any URL:</p>
    <pre class="cmd"><code>npx page-profile https://example.com          # single page report\nnpx page-profile --urls-from-file urls.txt   # batch check all pages (Pro)\nnpx page-profile --compare prod.html staging.html  # diff canonicals (Pro)</code></pre>
    <div class="problem-cards">
      <div class="card"><h3>✅ Graded checks</h3><p>Canonical presence, absolute vs relative, self-referencing — each gets a pass/warn/fail so you triage instead of reading raw HTML.</p></div>
      <div class="card"><h3>📦 Batch mode</h3><p>Feed it your sitemap URLs or a text file and check every page in one pass. Pro feature with HTML report output.</p></div>
      <div class="card"><h3>🔒 Runs locally</h3><p>Your client URLs never leave your machine. No account, no upload, no data stored on a server.</p></div>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/page-profile" class="btn-primary">Get page-profile free &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>How canonical URLs work with page-profile</h2>
    <p>When you run page-profile against a URL, it extracts the canonical tag from the page <code>&lt;head&gt;</code> and checks:</p>
    <ul style="line-height:1.8;margin:16px 0;">
      <li><strong>Present:</strong> Does the page have a <code>&lt;link rel="canonical"&gt;</code> tag?</li>
      <li><strong>Absolute:</strong> Is the href an absolute URL (required for consistent interpretation)?</li>
      <li><strong>Self-referencing:</strong> Does it point back to this page or to a different URL?</li>
    </ul>
    <p>Each check scores pass, warn or fail so you know what to fix and in what order. The free version handles single pages; Pro adds batch scanning across your entire sitemap and produces a shareable HTML report.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Frequently asked questions</h2>
    <div class="problem-cards">
      {faq_cards(FAQS_EN)}
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Related: <a href="/blog/website-seo-metadata-audit" style="color:var(--color-accent);">SEO Metadata Audit Checklist</a> &middot; <a href="/blog/technical-seo-check-website" style="color:var(--color-accent);">Technical SEO Check</a> &middot; <a href="/blog/open-graph-checker" style="color:var(--color-accent);">Open Graph Checker</a> &middot; <a href="/blog/meta-tag-checker" style="color:var(--color-accent);">Meta Tag Checker</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">&larr; Home</a> &middot; <a href="/page-profile">page-profile</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
{TRACK}
</body>
</html>'''

en_html = head('en',
    'Canonical URL Guide: How to Set, Check, and Fix Them',
    ARTICLE_EN['description'], URL_EN, URL_DA, 'da', ARTICLE_EN, FAQPAGE_EN) + en_body

# ---------------- DA ----------------
da_body = f'''
<body>
<header class="hero">
  <div class="container">
    <div class="badge">SEO &middot; KANONISK &middot; GUIDE</div>
    <h1>Guide til kanoniske URL\'er:<br>Sådan sætter, tjekker og retter du dem</h1>
    <p class="subtitle">Kanoniske tags er et af de mest misforståede SEO-signaler — og et af de mest betydningsfulde at få rigtigt. Én ødelagt canonical kan splitte din trafik mellem dublet-URL\'er i måneder. Her er hvordan du tjekker hver side på få minutter.</p>
    <div class="hero-cta">
      <a href="#tjekliste" class="btn-primary">Sådan tjekker du dine canonicals &rarr;</a>
      <a href="/da/page-profile" class="btn-secondary">Tjek dem automatisk med page-profile</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 5 minutters læsning</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>Hvorfor kanoniske URL\'er betyder noget</h2>
    <p>En kanonisk URL (<code>&lt;link rel="canonical" href="..."&gt;</code>) fortæller søgemaskinerne, hvilken version af en side der er den endegyldige. Uden den må Google gætte — og ofte gætter den forkert, især på sider med URL-parametre, flere stier til samme indhold eller syndikerede artikler. Resultatet er fortyndede rangsignaler og lavere organisk performance.</p>
    <div class="problem-cards">
      <div class="card"><h3>🔗 Samler link-ekuitet</h3><p>Alle backlinks, delinger og engagement på dublet-URL\'er bør flyde til én kanonisk side. Uden en canonical konkurrerer dubletterne i stedet for at bidrage.</p></div>
      <div class="card"><h3>📋 Forhindrer dubletindhold</h3><p>Google straffer intet for dubletindhold — men det splitter indekset på tværs af dubletter, så ingen rangerer så stærkt som én samlet side ville.</p></div>
      <div class="card"><h3>🔍 Du bestemmer hvilken URL der rangerer</h3><p>Kanoniske tags lader dig vælge, om <code>/blog/post</code> eller <code>/blog/post?ref=share</code> vises i resultaterne. Uden én vælger Google for dig.</p></div>
    </div>
  </div>
</section>

<section class="products" id="tjekliste">
  <div class="container">
    <h2>Almindelige canonical-fejl (og hvordan du spotter dem)</h2>
    <table class="compare">
      <thead><tr><th>#</th><th>Problem</th><th>Hvad skal du tjekke</th><th>Løsning</th></tr></thead>
      <tbody>
        <tr><td>1</td><td>Manglende canonical-tag</td><td>Har siden overhovedet <code>&lt;link rel="canonical"&gt;</code>?</td><td>Tilføj en selvrefererende canonical i <code>&lt;head&gt;</code> på alle indekserbare sider.</td></tr>
        <tr><td>2</td><td>Ikke-selvrefererende canonical</td><td>Peger canonical på <em>denne</em> side eller på en anden side?</td><td>Hvis dette er den kanoniske version, bør den referere til sig selv.</td></tr>
        <tr><td>3</td><td>Relativ canonical-URL</td><td>Er href en absolut URL eller en relativ sti?</td><td>Brug altid absolutte URL'er — <code>https://eksempel.dk/side</code>, ikke <code>/side</code>.</td></tr>
        <tr><td>4</td><td>Canonical-kædeløkke</td><td>A canonical til B, B canonical til A.</td><td>Bryd løkken. Følg kæden til én endelig destination.</td></tr>
        <tr><td>5</td><td>Canonical + noindex sammen</td><td>Har siden både et canonical-tag og <code>noindex</code>?</td><td>Fjern det ene: Google behandler parret som noindex og ignorerer canonical.</td></tr>
        <tr><td>6</td><td>Tværdomæne-canonical til forkert domæne</td><td>Peger canonical på et domæne du ikke kontrollerer?</td><td>Medmindre du bevidst syndikerer, hold canonicals på dit eget domæne.</td></tr>
        <tr><td>7</td><td>HTTP→HTTPS-uoverensstemmelse</td><td>Canonical peger på <code>http://</code> på et HTTPS-site.</td><td>Opdater til HTTPS-versionen. Blanding af protokoller forvirrer signalet.</td></tr>
        <tr><td>8</td><td>Trailing slash-uoverensstemmelse</td><td>Canonical har <code>/side/</code> men sidens URL er <code>/side</code> (eller omvendt).</td><td>Vær konsekvent. Vælg én konvention og hold den på hele sitet.</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section class="products" id="automatiser">
  <div class="container">
    <h2>Tjek hver side automatisk</h2>
    <p>At inspicere canonical-tagget på hver side i hånden er muligt for fem sider — men ikke for halvtreds eller fem hundrede. Det gratis open source-værktøj <a href="/da/page-profile" style="color:var(--color-accent);">page-profile</a> tjekker canonical-tags, selvreferencer, absolutte URL-formater og mere på enhver URL:</p>
    <pre class="cmd"><code>npx page-profile https://eksempel.dk             # rapport for én side\nnpx page-profile --urls-from-file urls.txt      # batch (Pro)\nnpx page-profile --compare prod.html staging.html  # sammenlign canonicals (Pro)</code></pre>
    <div class="problem-cards">
      <div class="card"><h3>✅ Karaktergivende tjek</h3><p>Canonical findes, absolut vs. relativ, selvrefererende — hver får bestået/advar/dump, så du kan prioritere i stedet for at læse rå HTML.</p></div>
      <div class="card"><h3>📦 Batch-tilstand</h3><p>Giv den dit sitemaps URL'er eller en tekstfil, og tjek alle sider i ét gennemløb. Pro-funktion med HTML-rapport.</p></div>
      <div class="card"><h3>🔒 Kører lokalt</h3><p>Dine kunders URL'er forlader aldrig din maskine. Ingen konto, intet uploades, ingen data gemmes på en server.</p></div>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/da/page-profile" class="btn-primary">Hent page-profile gratis &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Sådan virker canonical-tjek med page-profile</h2>
    <p>Når du kører page-profile mod en URL, udtrækker den canonical-tagget fra sidens <code>&lt;head&gt;</code> og tjekker:</p>
    <ul style="line-height:1.8;margin:16px 0;">
      <li><strong>Findes:</strong> Har siden et <code>&lt;link rel="canonical"&gt;</code>-tag?</li>
      <li><strong>Absolut:</strong> Er href en absolut URL (krævet for ensartet fortolkning)?</li>
      <li><strong>Selvrefererende:</strong> Peger den tilbage til denne side eller til en anden URL?</li>
    </ul>
    <p>Hvert tjek scorer bestået, advar eller dump, så du ved hvad du skal rette og i hvilken rækkefølge. Gratis-versionen håndterer enkeltsider; Pro tilføjer batch-scanning af hele dit sitemap og laver en delbar HTML-rapport.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
      {faq_cards(FAQS_DA)}
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="/da/blog/seo-metadata-tjek-hjemmeside" style="color:var(--color-accent);">SEO- og metadata-tjek</a> &middot; <a href="/da/blog/teknisk-seo-tjek-hjemmeside" style="color:var(--color-accent);">Teknisk SEO-tjek</a> &middot; <a href="/da/blog/meta-tjekker" style="color:var(--color-accent);">Meta-tjekker</a> &middot; <a href="/da/blog/open-graph-tjekker" style="color:var(--color-accent);">Open Graph-tjekker</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/da/">&larr; Forside</a> &middot; <a href="/da/page-profile">page-profile</a> &middot; <a href="/">Blog</a></p>
</footer>
{TRACK}
</body>
</html>'''

da_html = head('da',
    'Guide til kanoniske URL\'er: Sådan sætter, tjekker og retter du dem',
    ARTICLE_DA['description'], URL_DA, URL_EN, 'en', ARTICLE_DA, FAQPAGE_DA) + da_body


def validate(path, expect=2):
    c = open(path).read()
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', c, re.DOTALL)
    assert len(blocks) == expect, f'{path}: {len(blocks)} JSON-LD blocks'
    for b in blocks:
        p = json.loads(b)
        assert p['@context'] == 'https://schema.org'
    print(f'OK {path} ({len(c)} bytes, {expect} JSON-LD blocks)')


def write(path, html):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(html)


write(f'{ROOT}/blog/{SLUG_EN}.html', en_html)
write(f'{ROOT}/da/blog/{SLUG_DA}.html', da_html)
validate(f'{ROOT}/blog/{SLUG_EN}.html')
validate(f'{ROOT}/da/blog/{SLUG_DA}.html')

# --- internal link targets must exist ---
targets = ['blog/website-seo-metadata-audit.html', 'blog/technical-seo-check-website.html',
           'blog/meta-tag-checker.html', 'blog/open-graph-checker.html',
           'page-profile.html', 'free-tools.html',
           'da/blog/seo-metadata-tjek-hjemmeside.html', 'da/blog/teknisk-seo-tjek-hjemmeside.html',
           'da/blog/meta-tjekker.html', 'da/blog/open-graph-tjekker.html',
           'da/page-profile.html']
for t in targets:
    assert os.path.exists(f'{ROOT}/{t}'), f'MANGLER link-target: {t}'
print('Alle interne link-targets findes')

# --- sitemap ---
sm = f'{ROOT}/sitemap.xml'
c = open(sm).read()
entries = ''.join(
    f'<url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>'
    for u in (URL_EN, URL_DA))
for u in (URL_EN, URL_DA):
    assert u + '</loc>' not in c, f'allerede i sitemap: {u}'
c = c.replace('</urlset>', f'{entries}</urlset>')
open(sm, 'w').write(c)
import xml.dom.minidom
xml.dom.minidom.parseString(c)
print('Sitemap opdateret + gyldig XML')

# --- backlink fra blog-index (EN) ---
bi = f'{ROOT}/blog/index.html'
b = open(bi).read()
assert SLUG_EN not in b
new_li = ('<li style="margin-bottom:20px"><a href="/blog/%s" style="color:var(--color-accent);'
          'font-weight:600;text-decoration:none;font-size:1.02rem">Canonical URL Guide: '
          'How to Set, Check, and Fix Them</a><br><span style="color:var(--color-text-muted);font-size:0.88rem">'
          'Everything about canonical URLs: what they are, why they matter for SEO, and how to check '
          'every page on your site for missing, conflicting or broken canonicals automatically '
          'with the free page-profile CLI.</span></li>\\n') % SLUG_EN
marker = '<li style="margin-bottom:20px"><a href="/blog/canonical-url-guide" style='
if marker in b:
    # already added, skip re-insert
    pass
else:
    marker = '<li style="margin-bottom:20px"><a href="/blog/website-seo-metadata-audit"'
    idx = b.find(marker)
    assert idx > 0, 'marker ikke fundet i blog-index'
    b = b[:idx] + new_li + b[idx:]
    open(bi, 'w').write(b)
    print('Blog-index opdateret')

# --- backlink fra DA blog-index ---
di = f'{ROOT}/da/blog/index.html'
if os.path.exists(di):
    d = open(di).read()
    if SLUG_DA not in d:
        new_da_li = ('<li style="margin-bottom:14px"><a href=\"/da/blog/%s\" style="color:var(--color-accent);text-decoration:none">'
                     'Guide til kanoniske URL\'er: Sådan sætter, tjekker og retter du dem</a></li>\\n') % SLUG_DA
        da_marker = '<li style="margin-bottom:20px"><a href=\"/da/blog/canonisk-url-guide\"'
        if da_marker not in d:
            marker2 = '</ul>\\n</section>\\n<section'
            idx2 = d.find(marker2)
            if idx2 > 0:
                d = d[:idx2] + new_da_li + d[idx2:]
                open(di, 'w').write(d)
                print('DA blog-index opdateret')
            else:
                # fallback: insert after last EN section
                d = d.replace('</ul>\\n</section>\\n<footer', f'</ul>\\n</section>\\n<section id="nyeste">\\n<h2>Nyeste guides</h2>\\n<ul style="list-style:none">\\n{new_da_li}</ul>\\n</section>\\n<footer')
                open(di, 'w').write(d)
                print('DA blog-index opdateret (append)')

print('FAERDIG')