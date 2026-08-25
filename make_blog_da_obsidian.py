#!/usr/bin/env python3
"""Iteration 158: Danish guide to pasting into Obsidian cleanly.

- New: site/da/blog/indsæt-i-obsidian-ren-markdown.html (DA mirror of EN paste-into-obsidian-clean-markdown)
- Cross-links: EN blog -> DA guide (lang=da), DA relaterede cards
- JSON-LD validated with json.loads, sitemap dedupe check, internal link check
"""
import json, re, os
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

SLUG = 'indsæt-i-obsidian-ren-markdown'


def build_page():
    desc = ('Når du kopierer tekst fra en hjemmeside og sætter ind i Obsidian, '
            'følger usynlig HTML-rodd, smarte anførselstegn og zero-width-tegn med. '
            'Sådan får du ren Markdown hver gang — gratis.')
    ld_article = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article',
        'headline': 'Indsæt i Obsidian uden format-rod — ren Markdown hver gang',
        'description': desc,
        'url': f'{BASE}/da/blog/{SLUG}',
        'datePublished': TODAY, 'dateModified': TODAY,
        'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
        'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    }, ensure_ascii=False)
    faq = [
        ("Er der et gratis plugin der indsætter som ren Markdown?",
         "Clean Copy til Obsidian er gratis: download main.js og manifest.json "
         "fra udgivelsen, læg dem i <vault>/.obsidian/plugins/clean-copy-obsidian/, "
         "aktivér plugin'et, og brug Ctrl/Cmd+Shift+V — så får du ren Markdown "
         "i stedet for HTML-rodd."),
        ("Fikser Ctrl+Shift+V allerede ikke det her?",
         "Nej — Obsidians indbyggede 'Indsæt uden formatering' fjerner al "
         "formatering. Hvis du vil have overskrifter, links og lister bevaret "
         "som ægte Markdown, skal du konvertere – ikke bare strippe."),
        ("Håndterer det tabeller og kodeblokke?",
         "Ja. HTML-tabeller bliver til pipe-tabeller (med colspan-udfyldning), "
         "<pre>-blokke bliver til fenced kode, og navngivne + numeriske entiteter "
         "som &mdash; og &#8212; bliver afkodet."),
        ("Bliver mine data sendt nogen steder hen?",
         "Nej. Konverteringen kører lokalt inde i Obsidian. Intet forlader din maskine."),
    ]
    main_entity = [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                   for q, a in faq]
    ld_faq = json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': main_entity},
                        ensure_ascii=False)

    head_html = f'''<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Indsæt i Obsidian uden formateringsrod — Markdown-guide (2026)</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="Indsæt i Obsidian uden formateringsrod — ren Markdown">
<meta property="og:description" content="Obsidian er Markdown. Din udklipsholder er HTML. Hver indsætning fra nettet er et tabsgivende oversættelsesarbejde — medmindre du konverterer først. Tre løsninger, én gratis og på ét tastetryk.">
<meta property="og:image" content="{BASE}/clean-copy/og-preview.png">
<meta property="og:url" content="{BASE}/da/blog/{SLUG}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{BASE}/da/blog/{SLUG}">
<link rel="alternate" hreflang="en" href="{BASE}/blog/paste-into-obsidian-clean-markdown">
<link rel="alternate" hreflang="da" href="{BASE}/da/blog/{SLUG}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{ld_article}</script>
<script type="application/ld+json">{ld_faq}</script>
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">PRODUKTIVITET &middot; OBSIDIAN</div>
    <h1>Indsæt I Obsidian<br>Uden Formateringsrod</h1>
    <p class="subtitle">Dit Obsidian-vault er bygget på Markdown. Din udklipsholder indeholder HTML. Hver gang du kopierer fra en hjemmeside og sætter ind, er det en tabsgivende oversættelse — medmindre du konverterer først. Her er tre måder at gøre det på, én af dem gratis og på ét tastetryk.</p>
    <div class="hero-cta">
      <a href="#loesninger" class="btn-primary">Se løsningerne</a>
      <a href="/clean-copy" class="btn-secondary">Hent Clean Copy gratis &rarr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 4 minutters læsning</p>
  </div>
</header>

<section class="problem" id="hvorfor">
  <div class="container">
    <h2>Hvad der faktisk lander i dit Obsidian-vault</h2>
    <p>Når du kopierer et afsnit fra en hjemmeside, lægger browseren hele HTML-fragmentet på udklipsholderen — <strong>&lt;span&gt;-indpakninger, inline CSS, tracking-spans, smarte anførselstegn og zero-width-tegn</strong>. Når du så indsætter i Obsidian, sker der tre ting:</p>
    <div class="problem-cards">
      <div class="card"><h3>🧩 Struktur bliver mast</h3><p>Indlejrede div'er bliver til tomme linjer. Knapper bliver til løse links midt i en sætning. Tabeller kollapser til en lang ubrudt tekstlinje.</p></div>
      <div class="card"><h3>👻 Usynligt skrammel overlever</h3><p>Smarte anførselstegn, non-breaking spaces og zero-width-tegn bliver i din note evigt — usynlige, indtil en søgning eller et link ikke matcher på grund af dem.</p></div>
      <div class="card"><h3>🔗 Entiteter siver igennem</h3><p>Sideindhold gemt som <code>&amp;copy;</code>-lignende entiteter lander nogle gange som rå tegn i stedet for at blive til © eller —.</p></div>
    </div>
  </div>
</section>

<section class="products" id="loesninger">
  <div class="container">
    <h2>Tre måder at indsætte rent i Obsidian</h2>
    <div class="problem-cards">
      <div class="card"><h3>Løsning 1 — Indsæt uden formatering (indbygget)</h3><p>Obsidians egen <strong>Indsæt uden formatering</strong> (Ctrl/Cmd+Shift+V) fjerner alt — inklusive strukturen. Overskrifter bliver til almindelig tekst, lister mister deres bullettegn. Fint når du kun vil have rå tekst; ubrugeligt når du vil bevare artiklens opbygning.</p></div>
      <div class="card"><h3>Løsning 2 — Konvertér manuelt efter indsætning</h3><p>Indsæt, og ret så i hånden: genopbyg overskrifter, gensæt links, slet tomme linjer, jag usynlige tegn. Virker, men koster minutter per klip og fanger aldrig zero-width-tegn med det blotte øje.</p></div>
      <div class="card"><h3>Løsning 3 — Konvertér før det lander: Clean Copy (anbefalet)</h3><p><a href="/clean-copy" style="color:var(--color-accent);">Clean Copy til Obsidian</a> konverterer udklipsholderens HTML til ægte Markdown <em>før</em> indsætning — overskrifter til <code>#</code>, links til <code>[tekst](url)</code>, tabeller til pipe-tabeller, entiteter afkodet. Ét tastetryk: Ctrl/Cmd+Shift+V. Den samme motor findes også som <a href="/clean-copy" style="color:var(--color-accent);">Chrome- og Firefox-udvidelse</a>, så det du kopierer på nettet matcher det der lander i dit vault.</p></div>
    </div>
    <div style="text-align:center;margin-top:20px;">
      <a href="/clean-copy" class="btn-primary">Hent Clean Copy gratis &rarr;</a>
      <a href="/clean-copy-tool" class="btn-secondary">Prøv web-værktøjet &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
'''
    for q, a in faq:
        head_html += f'      <div class="card"><h3>{q}</h3><p>{a}</p></div>\n'
    head_html += '''    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/clean-copy" class="btn-primary">Hent Clean Copy gratis &rarr;</a>
      &nbsp;&nbsp;
      <a href="/blog/paste-into-obsidian-clean-markdown" class="btn-secondary">English version of this guide &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="/da/blog/kopier-chatgpt-til-word" style="color:var(--color-accent);">Kopier fra ChatGPT til Word</a> &middot; <a href="/da/blog/ren-tekst-fra-hjemmeside" style="color:var(--color-accent);">Ren tekst fra hjemmeside</a> &middot; <a href="/blog/html-to-markdown-converter" lang="en" style="color:var(--color-accent);">HTML til Markdown-konverter</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">Forside</a> &middot; <a href="/clean-copy-tool">Oprydningsværktøjet</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
<script>
(function(){try{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:p}),keepalive:true}).catch(function(){});document.addEventListener('click',function(ev){var a=ev.target&&ev.target.closest?ev.target.closest('a[href]'):null;if(!a)return;var h=a.href;if(h&&h.indexOf('chromewebstore.google.com')>-1){try{navigator.sendBeacon('/api/track',new Blob([JSON.stringify({path:p,event:'store-click'})],{type:'application/json'}));}catch(e){}}},true);}catch(e){}})();
</script>
</body>
</html>'''
    return head_html


def update_sitemap():
    p = f'{SITE}/sitemap.xml'
    c = open(p).read()
    url = f'{BASE}/da/blog/{SLUG}'
    if f'<loc>{url}</loc>' in c:
        print('sitemap: already present')
        return
    add = (f'  <url><loc>{url}</loc><lastmod>{TODAY}</lastmod>'
           f'<changefreq>weekly</changefreq><priority>0.8</priority></url>\n')
    c = c.replace('</urlset>', add + '</urlset>')
    open(p, 'w').write(c)
    print('sitemap updated')


def patch(path, old, new, must=True):
    c = open(path).read()
    if new in c:
        print(f'{path}: already patched')
        return True
    if old not in c:
        if must:
            raise SystemExit(f'anchor NOT found in {path}: {old[:70]!r}')
        return False
    open(path, 'w').write(c.replace(old, new))
    print(f'{path}: patched')
    return True


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


def main():
    out = f'{SITE}/da/blog/{SLUG}.html'

    # 1. New Danish blog page
    page = build_page()
    with open(out, 'w') as f:
        f.write(page)
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL)
    for b in blocks:
        d = json.loads(b)
        assert d['@context'] == 'https://schema.org', d['@context']
    print(f'{out} written, JSON-LD OK ({len(blocks)} blocks)')

    # 2. Sitemap
    update_sitemap()

    # 3. Cross-link from the EN blog post to this DA guide
    patch(f'{SITE}/blog/paste-into-obsidian-clean-markdown.html',
          '<footer style="padding:32px 24px;">',
          '<p><a href="/da/blog/indsæt-i-obsidian-ren-markdown" lang="da">Dansk version af denne guide</a></p>\n<footer style="padding:32px 24px;">')

    # 4. Internal link check on everything touched
    files = [out, f'{SITE}/blog/paste-into-obsidian-clean-markdown.html']
    broken = check_links(files)
    print('broken internal links:', broken if broken else 'none')

    # 5. Sitemap XML sanity + entry count
    sx = open(f'{SITE}/sitemap.xml').read()
    assert '</urlset>' in sx
    print('sitemap URLs:', sx.count('<loc>'))

    print(f'\nDone: /da/blog/{SLUG} created + sitemap + cross-links')


if __name__ == '__main__':
    main()
