#!/usr/bin/env python3
"""Iteration 159: Danish guide to pasting without formatting in Chrome.

- New: site/da/blog/indsæt-uden-formatering-i-chrome.html (DA mirror of EN paste-without-formatting-chrome)
- Cross-links: EN blog -> DA guide, DA relaterede cards
- JSON-LD validated with json.loads, sitemap dedupe check, internal link check
"""
import json, re, os
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

SLUG = 'indsæt-uden-formatering-i-chrome'


def build_page():
    desc = ('Når du indsætter tekst fra Chrome i Word, Gmail eller Notes, følger '
            'fonte, farver og skjult HTML med. Her er alle måder at indsætte uden '
            'formatering på — rangeret efter hvor lidt besvær de kræver.')
    ld_article = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article',
        'headline': 'Indsæt uden formatering i Chrome — alle metoderne',
        'description': desc,
        'url': f'{BASE}/da/blog/{SLUG}',
        'datePublished': TODAY, 'dateModified': TODAY,
        'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
        'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    }, ensure_ascii=False)
    faq = [
        ("Hvordan indsætter jeg uden formatering i Chrome?",
         "Tryk Ctrl+Shift+V (Windows) eller Cmd+Shift+V (Mac) for at indsætte "
         "som ren tekst. Til en permanent løsning kan du installere Clean Copy, "
         "som kopierer ren tekst automatisk."),
        ("Hvorfor indsætter Chrome formatering jeg ikke bad om?",
         "Chrome lægger hele HTML-fragmentet af din markering på udklipsholderen "
         "— inklusive fonte, farver og skjulte stilarter. Indsætningsmålet gengiver "
         "så HTML-versionen. En copy-udvidelse stripper det før udklipsholderen "
         "modtager det."),
        ("Kan man indstille Chrome til altid at indsætte som ren tekst?",
         "Nej — Chrome har ingen indbygget indstilling for det. Tætteste løsning "
         "er en copy-tids-udvidelse som Clean Copy, der fjerner formateringen før "
         "den når udklipsholderen, så hver almindelig indsætning giver ren tekst."),
        ("Virker Clean Copy også i Edge og Brave?",
         "Ja — Clean Copy virker i alle Chromium-browsere. Indlæs den udpakket fra "
         "samme zip: Edge bruger edge://extensions, Brave bruger brave://extensions. "
         "Samme proces."),
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
<title>Indsæt uden formatering i Chrome — alle metoder (2026)</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="Indsæt uden formatering i Chrome — komplet guide">
<meta property="og:description" content="Alt der virker: Ctrl+Shift+V, paste-as-plain-text-værktøjer, clipboard-managers og Clean Copy-udvidelsen der opfanger formateringen inden den når din udklipsholder.">
<meta property="og:image" content="{BASE}/clean-copy/og-preview.png">
<meta property="og:url" content="{BASE}/da/blog/{SLUG}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{BASE}/da/blog/{SLUG}">
<link rel="alternate" hreflang="en" href="{BASE}/blog/paste-without-formatting-chrome">
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
    <div class="badge">PRODUKTIVITET &middot; CHROME-TIPS</div>
    <h1>Indsæt Uden<br>Formatering i Chrome</h1>
    <p class="subtitle">Markér, kopiér, sæt ind — og formateringen følger med overalt. Her er alle metoderne der virker, rangeret efter hvor lidt besvær de kræver.</p>
    <div class="hero-cta">
      <a href="#metoder" class="btn-primary">Se alle metoder</a>
      <a href="/clean-copy" class="btn-secondary">Hent ét-klik-løsningen &rarr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 4 minutters læsning</p>
  </div>
</header>

<section class="problem" id="hvorfor">
  <div class="container">
    <h2>Hvorfor Chrome indsætter formatering du ikke bad om</h2>
    <p>Hver gang du kopierer i Chrome, lægger browseren <strong>to versioner</strong> af din markering på udklipsholderen: ren tekst og hele HTML-fragmentet. De fleste programmer læser HTML-versionen først — så du får sidens fonte, farver, linjeafstande, smarte anførselstegn og skjult tracking-markup med sammen med teksten.</p>
    <p>Løsningen er enten at bede indsætningsmålet om at ignorere formatering (et andet genvejstryk hver gang) — eller at ændre hvad der lægges på udklipsholderen, før indsætningen sker.</p>
  </div>
</section>

<section class="products" id="metoder">
  <div class="container">
    <h2>Seks metoder, rangeret efter bekvemmelighed</h2>
    <div class="problem-cards">
      <div class="card"><h3>1️⃣ Ctrl+Shift+V / Cmd+Shift+V</h3><p>Indsæt som ren tekst. Virker i de fleste programmer — men du skal <strong>huske</strong> det hver eneste gang. Godt som fallback, dårligt som vane (de fleste glemmer det og indsætter den formaterede version).</p><p>På Mac virker Cmd+Shift+Option+V også i nogle programmer som Word og Gmail.</p></div>
      <div class="card"><h3>2️⃣ Indsæt speciel-dialogen</h3><p>Ctrl+Alt+V åbner en dialog der spørger om du vil have ren tekst, HTML eller rich text. Nyttigt til dokumentarbejde, upraktisk ved hurtige indsætninger 50 gange om dagen.</p></div>
      <div class="card"><h3>3️⃣ Browserudvidelse: Clean Copy</h3><p><a href="/clean-copy" style="color:var(--color-accent);">Clean Copy</a> virker <strong>ved kopiering</strong>, ikke ved indsætning. Markér teksten, aktivér Clean Copy (højreklik eller Ctrl/Cmd+Shift+C), og udklipsholderen får ren tekst eller Markdown. Ingen særlig indsætningskommando nødvendig — i noget som helst program. Kører lokalt, ingen tracking, gratis og open source. Ikke i Chrome? <a href="/clean-copy-bookmarklet" style="color:var(--color-accent);">Bookmarklet'en</a> giver samme én-kliks rensning i enhver browser.</p></div>
      <div class="card"><h3>4️⃣ PureText (Windows) / PlainPaste (Mac)</h3><p>Systembakke-værktøjer der indsætter forrenset tekst. De tildeler en global genvej (fx Win+V) der overskriver udklipsholderens indhold med kun ren tekstversionen og derefter indsætter. Ét ekstra klik per indsætning.</p></div>
      <div class="card"><h3>5️⃣ Clipboard-managers</h3><p>Ditto (Windows), Maccy (Mac) eller Pastebot gemmer udklipsholderhistorik og kan strippe formatering. Tryk Ctrl+Shift+V for historik, eller klik på en genvej. Formateringsindstillingen er pr. program og pr. brug.</p></div>
      <div class="card"><h3>6️⃣ AutoHotkey / Keyboard Maestro-makroer</h3><p>Power users kan skrive et script der remapper Ctrl+V til "strip formatering, indsæt". Det virker systemdækkende men kræver opsætning, vedligeholdelse efter OS-opdateringer og et scriptingværktøj (AutoHotkey på Windows, Keyboard Maestro på Mac).</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="anbefalet">Den anbefalede tilgang: Clean Copy-udvidelsen</h2>
    <p>Genveje og clipboard-managers kræver at du <strong>ændrer din indsætningsadfærd</strong> — brug en anden genvej, åbn et panel, tænk over formatering ved hver indsætning. Clean Copy ændrer din <strong>kopieringsadfærd</strong> i stedet: markér teksten, aktivér én gang, og hver indsætning bagefter — hvor som helst — er ren.</p>
    <div style="background:var(--color-surface);border-radius:12px;padding:20px;margin:16px 0;">
      <p><strong>Sådan fungerer det i praksis:</strong></p>
      <ol style="margin:8px 0;">
        <li>Du finder en artikel på nettet med tekst du vil bruge.</li>
        <li>Markér teksten, højreklik → <strong>Clean Copy</strong> → Markdown (eller tryk Ctrl/Cmd+Shift+C).</li>
        <li>Skift til din mail, dit Notion-dokument, Obsidian-note eller AI-chat.</li>
        <li>Tryk Ctrl+V (eller Cmd+V). Almindelig indsætning. <strong>Teksten ankommer ren.</strong></li>
      </ol>
      <p>Nul genveje at huske, nul formatering at fjerne, nul programmer at konfigurere.</p>
    </div>
    <div style="text-align:center;margin-top:20px;">
      <a href="/clean-copy" class="btn-primary">Download Clean Copy gratis &rarr;</a>
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
      <a href="/clean-copy" class="btn-primary">Hent Clean Copy &rarr;</a>
      &nbsp;
      <a href="/da/blog/ren-tekst-fra-hjemmeside" class="btn-secondary">Se også: ren tekst fra hjemmeside &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="/da/blog/kopier-chatgpt-til-word" style="color:var(--color-accent);">Kopier fra ChatGPT til Word</a> &middot; <a href="/blog/html-to-markdown-converter" lang="en" style="color:var(--color-accent);">HTML til Markdown-konverter</a> &middot; <a href="/da/blog/indsæt-i-obsidian-ren-markdown" lang="da" style="color:var(--color-accent);">Indsæt i Obsidian uden rod</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">Forside</a> &middot; <a href="/clean-copy">Clean Copy</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/#blog">Blog</a></p>
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


def patch_file(path, old, new, must=True):
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
    patch_file(f'{SITE}/blog/paste-without-formatting-chrome.html',
               '<footer style="padding:32px 24px;">',
               '<p><a href="/da/blog/indsæt-uden-formatering-i-chrome" lang="da">Dansk version af denne guide</a></p>\n<footer style="padding:32px 24px;">')

    # 4. Internal link check on everything touched
    files = [out, f'{SITE}/blog/paste-without-formatting-chrome.html']
    broken = check_links(files)
    print('broken internal links:', broken if broken else 'none')

    # 5. Sitemap XML sanity + entry count
    sx = open(f'{SITE}/sitemap.xml').read()
    assert '</urlset>' in sx
    print('sitemap URLs:', sx.count('<loc>'))

    print(f'\nDone: /da/blog/{SLUG} created + sitemap + cross-links')


if __name__ == '__main__':
    main()
