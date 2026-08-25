#!/usr/bin/env python3
"""Iteration 156: Danish guide to copying website tables into Excel.

- New: site/da/blog/kopier-tabel-til-excel.html (DA mirror of EN copy-table-from-website-to-excel)
- Cross-links: EN blog -> DA guide (lang=da), DA blog relaterede cards
- JSON-LD validated with json.loads, sitemap dedupe check, internal link check
"""
import json, re, os
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

SLUG = 'kopier-tabel-til-excel'


def build_page():
    desc = ('Sådan kopierer du en tabel fra en hjemmeside ind i Excel — uden at kolonnerne '
            'smelter sammen. Tre metoder rangeret efter pålidelighed, inkl. gratis konvertering '
            'til Markdown med Clean Copy. Virker også til Google Sheets.')
    ld_article = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article',
        'headline': 'Kopier tabel fra hjemmeside til Excel — uden rod',
        'description': desc,
        'url': f'{BASE}/da/blog/{SLUG}',
        'datePublished': TODAY, 'dateModified': TODAY,
        'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
        'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    }, ensure_ascii=False)
    faq = [
        ("Hvordan kopierer jeg en tabel fra en hjemmeside ind i Excel?",
         "Markér tabellen på siden, kopiér den, og sæt den ind i Excel. Fungerer det ikke pænt, "
         "kan du først konvertere tabellen til Markdown med et gratis værktøj som Clean Copy, og "
         "derefter splitte rækkerne ved tegnet | via Data > Tekst til kolonner."),
        ("Hvorfor ser min indsatte tabel forkert ud i Excel?",
         "Mange hjemmesider bygger deres tabeller af indlejrede div'er, CSS-grid og colspan-tricks "
         "i stedet for ægte <table>-markup. Når Excel modtager udklipsholderens HTML, forsøger det "
         "at genskabe kolonnerne — og ender ofte med alt i én kolonne eller skjult styling med i købet."),
        ("Virker det også i Google Sheets?",
         "Ja. Google Sheets følger samme regler: direkte indsætning virker for velformede tabeller; "
         "ellers skal du splitte ved pipe-tegnet med Rediger > Find og erstat, eller bruge Filer > Importer "
         "på en renset CSV."),
        ("Hvad med tabeller bag login eller JavaScript?",
         "Excels Data > Fra web kan ikke se sider der kræver login, og nogle JavaScript-genererede "
         "tabeller dukker aldrig op. Et kopiværktøj som Clean Copy virker på alt hvad du kan markere "
         "i din browser — også loggede dashboards."),
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
<title>Kopier tabel fra hjemmeside til Excel — sådan undgår du rodet</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="Kopier en tabel fra nettet ind i Excel — uden rod">
<meta property="og:description" content="Hvorfor tabeller sættes dårligt ind i Excel — og tre løsninger rangeret efter pålidelighed, inkl. konvertering til Markdown med gratis Clean Copy.">
<meta property="og:image" content="{BASE}/clean-copy/og-preview.png">
<meta property="og:url" content="{BASE}/da/blog/{SLUG}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{BASE}/da/blog/{SLUG}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{ld_article}</script>
<script type="application/ld+json">{ld_faq}</script>
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">PRODUKTIVITET &middot; REGNEARK</div>
    <h1>Kopier Tabel Fra Hjemmeside Til Excel<br>Uden At Kolonnerne Smelter Sammen</h1>
    <p class="subtitle">Du har fundet præcis den tabel du skal bruge. Du kopierer den. Du sætter den ind i Excel. Og så står alt i én kæmpe kolonne. Her er hvorfor det sker — og de tre løsninger der faktisk virker.</p>
    <div class="hero-cta">
      <a href="#loesninger" class="btn-primary">Se løsningerne</a>
      <a href="/clean-copy-tool" class="btn-secondary">Konvertér din tabel nu &rarr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 5 minutters læsning</p>
  </div>
</header>

<section class="problem" id="hvorfor">
  <div class="container">
    <h2>Hvorfor tabeller ryger under indsætningen</h2>
    <p>Excel forventer et gitter: rækker og celler. Moderne hjemmesider giver det sjældent. Tabeller bygges af <strong>indlejrede &lt;div&gt;'er, CSS-grid, flexbox-rækker og colspan-tricks</strong>. Når Excel får udklipsholderens HTML, forsøger det at genskabe kolonnerne så godt det kan — og fejler på forudsigelige måder:</p>
    <p>Alt lander i én kolonne. Skjulte sporingselementer bliver til ekstra tomme rækker. Cellebaggrunde og skrifttyper tages med. Links kommer som hele URL'er limet fast til teksten. Flettede overskriftsceller flytter hver række under dem.</p>
    <div class="problem-cards">
      <div class="card"><h3>🎯 Tre udgange</h3><p>Direkte indsætning når tabellen er ægte, Markdown-konvertering når den ikke er, eller Power Query til store tabeller.</p></div>
      <div class="card"><h3>⚡ Sekunder, ikke oprydning</h3><p>Konvertér tabellen til ren Markdown før den rammer regnearket — så splitter du kolonnerne på sekunder i stedet for at rette i minutter.</p></div>
      <div class="card"><h3>🔒 Kører lokalt</h3><p>Clean Copy kører i din egen browser. Din tabel sendes ikke til en server og gemmes ingen steder.</p></div>
    </div>
  </div>
</section>

<section class="products" id="loesninger">
  <div class="container">
    <h2>Tre løsninger, rangeret efter pålidelighed</h2>
    <div class="problem-cards">
      <div class="card"><h3>Løsning 1 — Indsæt direkte, og tjek resultatet</h3><p>Bruger siden ægte <strong>&lt;table&gt;</strong>-markup (Wikipedia, de fleste dokumentationssider), virker almindelig kopiering direkte ind i Excel eller Google Sheets. Indsæt, og scan for flettede rækker og løse kolonner. Tager ti sekunder når det virker — to minutters oprydning når det ikke gør.</p></div>
      <div class="card"><h3>Løsning 2 — Konvertér til Markdown først (Clean Copy)</h3><p><a href="/clean-copy" style="color:var(--color-accent);">Clean Copy</a> er en gratis browserudvidelse der konverterer markeret indhold — inklusive tabeller — til <strong>ren Markdown</strong> før noget rammer udklipsholderen. Markér tabellen, højreklik, vælg Clean Copy, og sæt resultatet ind hvor som helst. Markdown-tabeller er pipe-separeret tekst: alle konvertere, importeringsguides og AI-assistenter læser dem fejlfrit. Ingen sporing, kører lokalt — eller brug <a href="/clean-copy-bookmarklet" style="color:var(--color-accent);">bookmarklet'et</a>/<a href="/clean-copy-tool" style="color:var(--color-accent);">web-værktøjet</a> uden at installere noget.</p></div>
      <div class="card"><h3>Løsning 3 — Power Query / Data &gt; Fra web</h3><p>Excels indbyggede <strong>Data &gt; Fra web</strong> (Power Query) henter siden og lister dens tabeller til import. Det er den mest grundige løsning til store tabeller, men virker kun på offentlige sider, rammer nogle gange ikke JavaScript-genererede tabeller, og er overkill til en hurtig fem-rækkers tabel.</p></div>
    </div>
    <div style="text-align:center;margin-top:20px;">
      <a href="/clean-copy-tool" class="btn-primary">Prøv Clean Copy gratis &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Sådan deler du Markdown-tabellen op i kolonner i Excel</h2>
    <ol>
      <li>Konvertér tabellen til Markdown med <a href="/clean-copy-tool" style="color:var(--color-accent);">web-værktøjet</a> eller udvidelsen, og indsæt resultatet i et tomt ark (én celle pr. linje er fint — brug fx Notesblokken imellem).</li>
      <li>Fjern separatorlinjen (den med bindestreger), og markér resten.</li>
      <li>Vælg <strong>Data &gt; Tekst til kolonner &gt; Afgrænset</strong>, og angiv <strong>|</strong> (pipe) som adskillelsestegn.</li>
      <li>Færdig: hver kolonne lander på sin plads, klar til formler og sortering.</li>
    </ol>
    <p>I Google Sheets: brug <strong>Rediger &gt; Find og erstat</strong> til at udskifte | med tabulator, og indsæt derefter — eller gem som CSV og brug <strong>Filer &gt; Importer</strong>.</p>
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
      <a href="/clean-copy-tool" class="btn-primary">Konvertér din tabel nu &rarr;</a>
      &nbsp;&nbsp;
      <a href="/blog/copy-table-from-website-to-excel" class="btn-secondary">English version of this guide &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="/da/blog/ren-tekst-fra-hjemmeside" style="color:var(--color-accent);">Ren tekst fra hjemmeside</a> &middot; <a href="/da/blog/url-til-markdown-konverter" style="color:var(--color-accent);">URL til Markdown-konverter</a> &middot; <a href="/blog/html-to-markdown-converter" lang="en" style="color:var(--color-accent);">HTML to Markdown converter</a></p></div>
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
    patch(f'{SITE}/blog/copy-table-from-website-to-excel.html',
          '<footer style="padding:32px 24px;">\n  <p><a href="/">&larr; Home</a>',
          '<p><a href="/da/blog/kopier-tabel-til-excel" lang="da">Dansk version af denne guide</a></p>\n<footer style="padding:32px 24px;">\n  <p><a href="/">&larr; Home</a>',
          must=False)

    # 4. Card on the EN post's related line already exists; also add DA frontpage mention if anchor exists
    patch(f'{SITE}/da.html',
          '/da/blog/url-til-markdown-konverter',
          '/da/blog/kopier-tabel-til-excel',
          must=False)

    # 5. Internal link check on everything touched
    files = [out, f'{SITE}/blog/copy-table-from-website-to-excel.html']
    broken = check_links(files)
    print('broken internal links:', broken if broken else 'none')

    # 6. Sitemap XML sanity + entry count
    sx = open(f'{SITE}/sitemap.xml').read()
    assert '</urlset>' in sx
    print('sitemap URLs:', sx.count('<loc>'))

    print(f'\nDone: /da/blog/{SLUG} created + sitemap + cross-links')


if __name__ == '__main__':
    main()
