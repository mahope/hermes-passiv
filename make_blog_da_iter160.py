#!/usr/bin/env python3
"""Iteration 160: Two Danish guide pendants for Clean Copy blog posts.

- site/da/blog/html-til-markdown-konverter.html  (mirror of EN html-to-markdown-converter)
- site/da/blog/kopier-som-markdown-udvidelse.html (mirror of EN copy-as-markdown-chrome-extension)
- Cross-links both ways, JSON-LD validated, sitemap updated, internal link check
"""
import json, re, os
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

PAGES = [
    {
        'slug': 'html-til-markdown-konverter',
        'en_slug': 'html-to-markdown-converter',
        'title': 'HTML til Markdown-konverter — gratis og online',
        'h1': 'HTML til Markdown<br>Konverter',
        'desc': ('Indsæt rå HTML og få ren Markdown med det samme — gratis online '
                 'konverter der kører 100 % i din egen browser. Overskrifter, links, '
                 'lister, kodeblokke og tabeller håndteres korrekt. Intet uploades.'),
        'og_desc': ('Konvertér HTML til ren Markdown online gratis. Alt sker i din '
                    'egen browserfane — intet sendes til en server.'),
        'badge': 'GRATIS VÆRKTJ &middot; KONVERTERE',
        'subtitle': ('Indsæt rodet rich text eller rå HTML → få ren Markdown med ét '
                     'klik. Gratis, øjeblikkeligt, og intet forlader nogensinde din browser.'),
        'cta1': ('<a href="/clean-copy-tool" class="btn-primary">Åbn konverteren &rarr;</a>'),
        'cta2': '<a href="#saadan" class="btn-secondary">Sådan virker det</a>',
        'faq': [
            ("Hvad er den bedste gratis HTML til Markdown-konverter?",
             "Clean Copy Web er en gratis konverter der kører i browseren: indsæt HTML "
             "eller rodet tekst og få ren Markdown eller ren tekst med det samme. Den "
             "kører 100 % klient-side — intet uploades til en server."),
            ("Er det sikkert at indsætte HTML i en online-konverter?",
             "Kun hvis konverteren kører klient-side. Server-baserede konvertere modtager "
             "alt hvad du indsætter. Clean Copy Web udfører konverteringen inde i din egen "
             "browserfane, så indholdet forlader aldrig din maskine."),
            ("Hvilke HTML-elementer kan konverteres til Markdown?",
             "Overskrifter (h1-h6), afsnit, links, billeder, ordnede og uordnede lister "
             "inklusive indlejrede, fed/kursiv/inline-kode, kodeblokke, citater og tabeller "
             "har alle standard-Markdown-modstykker. Script-tags, styles og skjulte elementer "
             "strippes."),
        ],
        'body': '''
<section class="products" id="saadan">
  <div class="container">
    <h2>Sådan foregår konverteringen</h2>
    <p>Clean Copy Web parser din indsatte markup med browserens egen HTML-parser, går
    dokumenttræet igennem og udsender standard-Markdown:</p>
    <ol>
      <li><strong>Overskrifter</strong> h1-h6 bliver til <code>#</code>-<code>######</code></li>
      <li><strong>Links og billeder</strong> bliver til <code>[tekst](url)</code> og <code>![alt](src)</code></li>
      <li><strong>Lister</strong> — også indlejrede — beholder korrekt indrykning og mærker</li>
      <li><strong>Fed, kursiv, inline-kode</strong> bliver til <code>**…**</code>, <code>_…_</code>, backticks</li>
      <li><strong>Kodeblokke og citater</strong> bliver til fenced blocks og <code>&gt;</code>-citater</li>
      <li><strong>Tabeller</strong> bliver til GitHub-flavoured pipe-tabeller</li>
      <li><strong>Rod fjernes</strong>: scripts, styles, skjulte spans, tracking-pixels, smarte anførselstegn renses</li>
    </ol>
    <p>Samme motor driver <a href="/clean-copy" style="color:var(--color-accent);">Clean Copy-browserudvidelsen</a>,
    så webside og udvidelse giver identisk output. Har du en hel URL i stedet for rå HTML?
    Brug den gratis <a href="/da/url-til-markdown" style="color:var(--color-accent);">URL-til-Markdown-konverter</a>
    (<a href="/blog/url-to-markdown-converter" lang="en" style="color:var(--color-accent);">engelsk guide</a>) —
    den henter siden og finder hovedindholdet for dig.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Hvorfor klient-side betyder noget</h2>
    <div class="problem-cards">
      <div class="card"><h3>🔒 Privatliv fra starten</h3><p>Server-baserede konvertere ser alt hvad du indsætter — kontrakter, interne dokumenter, personlige noter. Clean Copy Web har slet intet upload-trin: konverteringen kører i din fane og virker offline, når siden først er loadet.</p></div>
      <div class="card"><h3>⚡ Øjeblikkelige resultater</h3><p>Ingen rundtur til en server. Indsæt, konvertér, kopier tilbage — på under et sekund selv for store dokumenter.</p></div>
      <div class="card"><h3>🆓 Gratis, ingen konto</h3><p>Ubegrænsede konverteringer, ingen tilmelding, ingen vandmærker, ingen daglige grænser.</p></div>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/clean-copy-tool" class="btn-primary">Prøv nu — indsæt lidt HTML &rarr;</a>
      &nbsp;
      <a href="/da/blog/ren-tekst-fra-hjemmeside" class="btn-secondary">Se også: ren tekst fra hjemmeside &rarr;</a>
    </div>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/indsæt-i-obsidian-ren-markdown" lang="da">Indsæt i Obsidian uden rod</a> &middot; '
                    '<a href="/da/blog/url-til-markdown-konverter" lang="da">URL-til-Markdown-konverter</a> &middot; '
                    '<a href="/da/blog/kopier-chatgpt-til-word" lang="da">Kopier fra ChatGPT til Word</a>'),
    },
    {
        'slug': 'kopier-som-markdown-udvidelse',
        'en_slug': 'copy-as-markdown-chrome-extension',
        'title': 'Copy as Markdown i Chrome — sådan gør du (2026)',
        'h1': 'Copy as Markdown<br>i Chrome',
        'desc': ('Markér tekst på enhver hjemmeside og kopiér den som ren Markdown med ét '
                 'klik. Guide til de bedste metoder: browserudvidelsen Clean Copy, '
                 'bookmarklet og CLI — plus hvad du skal tjekke før du vælger.'),
        'og_desc': ('Sådan kopierer du markeret tekst som Markdown direkte i Chrome — '
                    'med udvidelse, bookmarklet eller kommandolinje.'),
        'badge': 'PRODUKTIVITET &middot; MARKDOWN',
        'subtitle': ('Markér, klik, indsæt: overskrifter, lister, links og kodeblokke '
                     'ankommer som gyldig Markdown — hvor som helst du indsætter.'),
        'cta1': '<a href="#metoder" class="btn-primary">Se metoderne</a>',
        'cta2': '<a href="/clean-copy" class="btn-secondary">Hent Clean Copy gratis &rarr;</a>',
        'faq': [
            ("Hvordan kopierer jeg tekst som Markdown i Chrome?",
             "Den hurtigste vej er en copy-tids-udvidelse som Clean Copy: markér teksten, "
             "højreklik → Clean Copy → Markdown (eller Ctrl/Cmd+Shift+C). Udklipsholderen "
             "modtager gyldig Markdown, som du kan indsætte hvor som helst."),
            ("Er Copy-as-Markdown gratis?",
             "Ja. Clean Copy er gratis og open source, kører lokalt i din browser uden "
             "tracking og kræver ingen konto. Der findes en valgfri Pro-udgave med licens­nøgler, "
             "men kernefunktionen — kopier som Markdown eller ren tekst — er gratis."),
            ("Virker det også med tabeller og kodeblokke?",
             "Ja. Tabeller bliver til GitHub-flavoured pipe-tabeller, kodeblokke til fenced "
             "blocks med korrekt indrykning, og indlejrede lister bevarer deres struktur. "
             "Samme konvertermotor bruges af web-værktøjet, udvidelsen og CLI'en."),
            ("Kan jeg bruge det i Edge, Brave eller Firefox?",
             "Clean Copy virker i alle Chromium-browsere (Edge, Brave, Opera). I Firefox "
             "kan bookmarklet'en give samme én-kliks rensning, og CLI'en dækker scripting "
             "på tværs af browsere."),
        ],
        'body': '''
<section class="problem" id="hvorfor">
  <div class="container">
    <h2>Problemet: Markdown går tabt undervejs</h2>
    <p>Kopierer du tekst fra en hjemmeside, lægger Chrome hele HTML-fragmentet på
    udklipsholderen — ikke Markdown. Når du indsætter i Obsidian, Notion, en AI-chat
    eller en README-fil, skal du enten rydde op manuelt eller miste strukturen:
    overskrifter bliver til almindelige linjer, lister til punkter uden hierarki,
    tabeller til uigennemtrængelig tekst.</p>
    <p>Løsningen er at konvertere <strong>ved kopiering</strong>, ikke ved indsætning.</p>
  </div>
</section>

<section class="products" id="metoder">
  <div class="container">
    <h2>Tre metoder, rangeret efter bekvemmelighed</h2>
    <div class="problem-cards">
      <div class="card"><h3>1️⃣ Browserudvidelsen: Clean Copy</h3>
      <p><a href="/clean-copy" style="color:var(--color-accent);">Clean Copy</a> sidder i højreklik-menuen og på Ctrl/Cmd+Shift+C. Markér tekst → aktivér → udklipsholderen får ren Markdown (eller plain text, dit valg). Kører 100 % lokalt, ingen tracking, open source. Ét værktøj, alle sider.</p></div>
      <div class="card"><h3>2️⃣ Bookmarklet</h3><p><a href="/clean-copy-bookmarklet" style="color:var(--color-accent);">Bookmarklet'en</a> trækkes til bogmærkelinjen og giver samme én-kliks konvertering i enhver browser — også Firefox og Safari. Kræver ingen installation, men et klik pr. gang.</p></div>
      <div class="card"><h3>3️⃣ Kommandolinjen</h3><p>Til scripting og batch-arbejde: <code>brew install mahope/clean-copy/clean-copy</code>, derefter <code>clean-copy --url https://eksempel.dk/artikel</code>. Samme motor, identisk output — velegnet til pipelines og automatisering.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Sådan fungerer det i praksis</h2>
    <ol>
      <li>Du finder en artikel eller docs-side med tekst du vil gemme.</li>
      <li>Markér afsnittet, højreklik → <strong>Clean Copy</strong> → Markdown.</li>
      <li>Skift til Obsidian, Notion, VS Code eller din AI-chat.</li>
      <li>Tryk Ctrl/Cmd+V. Overskrifter, lister, links og kodeblokke ankommer som gyldig Markdown.</li>
    </ol>
    <div style="text-align:center;margin-top:20px;">
      <a href="/clean-copy" class="btn-primary">Download Clean Copy gratis &rarr;</a>
    </div>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/indsæt-i-obsidian-ren-markdown" lang="da">Indsæt i Obsidian uden rod</a> &middot; '
                    '<a href="/da/blog/html-til-markdown-konverter" lang="da">HTML-til-Markdown-konverter</a> &middot; '
                    '<a href="/da/blog/ren-tekst-fra-hjemmeside" lang="da">Ren tekst fra hjemmeside</a>'),
    },
]


def build_page(p):
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
<meta property="og:image" content="{BASE}/clean-copy/og-preview.png">
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
    <p class="hero-note">Opdateret august 2026 &middot; 4 minutters læsning</p>
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
      <a href="/clean-copy-tool" class="btn-primary">Prøv web-værktøjet gratis &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Relateret: {p['related']}</p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">Forside</a> &middot; <a href="/clean-copy">Clean Copy</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});document.addEventListener('click',function(ev){{var a=ev.target&&ev.target.closest?ev.target.closest('a[href]'):null;if(!a)return;var h=a.href;if(h&&h.indexOf('chromewebstore.google.com')>-1){{try{{navigator.sendBeacon('/api/track',new Blob([JSON.stringify({{path:p,event:'store-click'}})],{{type:'application/json'}}));}}catch(e){{}}}}}},true);}}catch(e){{}}}})();
</script>
</body>
</html>'''


def update_sitemap(slug):
    path = f'{SITE}/sitemap.xml'
    c = open(path).read()
    url = f'{BASE}/da/blog/{slug}'
    if f'<loc>{url}</loc>' in c:
        print(f'sitemap: {slug} already present')
        return
    add = (f'  <url><loc>{url}</loc><lastmod>{TODAY}</lastmod>'
           f'<changefreq>weekly</changefreq><priority>0.8</priority></url>\n')
    c = c.replace('</urlset>', add + '</urlset>')
    open(path, 'w').write(c)
    print(f'sitemap: added {slug}')


def patch_file(path, old, new):
    c = open(path).read()
    if new in c:
        print(f'{path}: already patched')
        return
    assert old in c, f'anchor not found in {path}: {old[:70]!r}'
    open(path, 'w').write(c.replace(old, new))
    print(f'{path}: patched')


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
    outs = []
    for p in PAGES:
        out = f'{SITE}/da/blog/{p["slug"]}.html'
        page = build_page(p)
        with open(out, 'w') as f:
            f.write(page)
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL)
        for b in blocks:
            d = json.loads(b)
            assert d['@context'] == 'https://schema.org', d['@context']
        print(f'{out} written, JSON-LD OK ({len(blocks)} blocks)')
        update_sitemap(p['slug'])
        # Cross-link from the EN post down to this DA guide
        patch_file(f'{SITE}/blog/{p["en_slug"]}.html',
                   '<footer style="padding:32px 24px;">',
                   f'<p><a href="/da/blog/{p["slug"]}" lang="da">Dansk version af denne guide</a></p>\n<footer style="padding:32px 24px;">')
        outs.append(out)

    # Cross-link between the two new DA pages is already inside body/related.
    files = outs + [f'{SITE}/blog/{p["en_slug"]}.html' for p in PAGES]
    broken = check_links(files)
    print('broken internal links:', broken if broken else 'none')
    sx = open(f'{SITE}/sitemap.xml').read()
    assert '</urlset>' in sx
    print('sitemap URLs:', sx.count('<loc>'))
    print('\nDone: 2 DA guides created + sitemap + cross-links')


if __name__ == '__main__':
    main()
