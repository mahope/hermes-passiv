#!/usr/bin/env python3
"""Iteration 97: dansk pendant til /blog/eaa-deadline-2026 -> /blog/eaa-frister-2026
plus forsids-kort til begge danske blogsider (STATUS iter.96 punkt 2).
Selvstændigt script; JSON-LD valideres med json.loads."""

import json
import re
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'


def head(slug, lang, title, meta_desc, og_title, og_desc, headline):
    ld = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article', 'headline': headline,
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


def da_deadline_page():
    slug = 'eaa-frister-2026'
    desc = ('Den Europæiske Accessibilitetslovs frist er overskredet. Her er hvad der håndhæves '
            'i 2026, hvem der er undtaget, hvilke bøder landene uddeler — og den hurtigste vej til '
            'dokumenteret overensstemmelse.')
    h = head(slug, 'da',
             'EAA-fristen er overskredet: Sådan håndhæves loven i 2026 (dansk guide)',
             desc,
             'EAA-fristen 2026: Hvad håndhæves nu?',
             'Bøder, undtagelser og den hurtigste vej til overensstemmelse med Den Europæiske Accessibilitetslov.',
             'EAA-fristen 2026: Hvad håndhæves nu?')
    body = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">BLOG · EAA-FRISTER</div>
    <h1>EAA-fristen er<br>overskredet — hvad nu?</h1>
    <p class="subtitle">Fristen 28. juni 2025 er passeret. Her er hvad Den Europæiske Accessibilitetslov kræver i dag, hvem der er undtaget, hvordan bøderne ser ud fra land til land — og den hurtigste vej til dokumenteret overensstemmelse.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">Læs guiden</a>
      <a href="/scan-da" class="btn-secondary">Scan dit site gratis →</a>
    </div>
    <p class="hero-note">Opdateret august 2026 · Læsetid: 6 minutter</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="status">Status på fristen</h2>
    <p>Den Europæiske Accessibilitetslov (direktiv (EU) 2019/882) skulle anvendes af medlemslandene fra <strong>28. juni 2025</strong>. Den dato er passeret: Håndhævelsen kører i alle medlemslande, markedsovervågningsmyndighederne er i gang, og de første bøder er uddelt — herunder bøder rapporteret i Sverige (ca. 900.000 €) og Spanien (ca. 600.000 €). I 2026 er spørgsmålet ikke længere "hvornår skal jeg overholde loven?", men "hvor hurtigt kan jeg dokumentere overensstemmelse?".</p>
    <div class="problem-cards">
      <div class="card"><h3>📅 Allerede overskredet</h3><p>28. juni 2025 — forpligtelserne gælder. Tjenester kontraheret efter datoen skal leve op til WCAG 2.1 AA / EN 301 549.</p></div>
      <div class="card"><h3>⏳ Fortsættelsesfrist</h3><p>Eksisterende tjenester må fortsætte, indtil de gennemgår en "væsentlig ændring" — men redesigns, platforms-skift eller større opdateringer nulstiller uret til fuld overensstemmelse.</p></div>
      <div class="card"><h3>🏗️ Undtagelse for byggeri</h3><p>Nogle fysiske undtagelser løber til 2030 i visse lande. Digitale tjenester får ingen sådan forlængelse.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Hvem er omfattet?</h2>
    <p>EAA omfatter produkter og tjenester sat på EU-markedet efter fristen: webshops, banktjenester, e-bøger, billetteringsautomater, smartphones, TV-udstyr og teletjenester. For webbureauer er nøgleudløseren e-handel: enhver webshop du bygger, hoster eller vedligeholder for en EU-sælger er i scope. Mikrovirksomheder (færre end 10 ansatte OG under 2 mio. € i årlig omsætning), der udbyder <strong>tjenester</strong>, er undtaget — men undtagelsen dækker ikke de produkter de sælger eller videresælger.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Sådan ser håndhævelsen ud</h2>
    <p>Hvert medlemsland har udpeget markedsovervågningsmyndigheder. Mønsteret indtil videre: klager fra brugere udløser undersøgelse, myndighederne udsteder påbud med frister, og bøder følger ved fortsat manglende overensstemmelse. Flere lande tillader også forbrugerorganisationer at føre sag. Den praktiske konsekvens for bureauer: kundens klagebrev lander hos <strong>dig</strong> først, fordi rettelsen ligger i din kodebase.</p>
    <div class="problem-cards">
      <div class="card"><h3>🇸🇪 Sverige</h3><p>Bøder op mod ca. 900.000 € rapporteret for tjenester uden overensstemmelse efter fristen.</p></div>
      <div class="card"><h3>🇪🇸 Spanien</h3><p>Bøder på ca. 600.000 € uddelt; forbrugergrupper tester aktivt detailhandelssider.</p></div>
      <div class="card"><h3>🇩🇪 Tyskland</h3><p>BFSD-håndhævelse via Marktüberwachungsstellen; BITV-lignende testmetoder anvendt på privat sektor for første gang.</p></div>
      <div class="card"><h3>🇫🇷 Frankrig</h3><p>Eksisterende RGAA-håndhævelse skærpet; EAA-forpligtelser foldet ind i samme overvågningscyklus.</p></div>
    </div>
  </div>
</section>

<section class="cta-section">
  <div class="container">
    <h2>Hvis du ikke er compliant nu</h2>
    <p class="section-intro">Panik-redesign ikke. Myndighederne reagerer langt bedre på dokumenterede, godtroende rettelser end på tavshed. Rækkefølgen der virker: (1) kør en automatiseret scanning og find de mekaniske fejl — kontrast, alt-tekster, overskrifter, etiketter; (2) ret dem, det er typisk dages arbejde; (3) udgiv en ærlig tilgængelighedserklæring med delvis overensstemmelse, kendte begrænsninger og en feedbackkanal — det alene opfylder dokumentationskravet mens det dybere arbejde fortsætter; (4) planlæg manuel skærmlæsertest af komplekse flows som checkout. Vores gratis scanner klarer trin 1 på ca. to minutter for de fleste sider.</p>
    <p>Vores EAA-e-bog omsætter lovens tekst til en 14-dages handlingsplan med værktøjsanbefalinger og en udfyldningsklar tilgængelighedserklæring.</p>
    <div style="text-align:center;margin-top:24px;">
      <a href="/scan-da" class="btn-primary">Scan dit site gratis →</a>
      &nbsp;&nbsp;
      <a href="/#products" class="btn-secondary">Se EAA-e-bogen →</a>
      &nbsp;&nbsp;
      <a href="/blog/eaa-deadline-2026" class="btn-secondary">English version →</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
      <div class="card"><h3>Kommer en ny EAA-frist efter juni 2025?</h3><p>Nej. 28. juni 2025 var den endelige anvendelsdato. Der findes ingen anden overgangsperiode for digitale tjenester. De eneste resterende overgange vedrører eksisterende tjenesters fortsættelse og specifikke bygningsværker i enkelte lande.</p></div>
      <div class="card"><h3>Mit site blev lanceret før fristen — er jeg sikker?</h3><pIkke permanent. Eksisterende aftaler nyder fortsættelse indtil en væsentlig ændring, men myndighederne tolker "væsentlig ændring" bredt: et redesign, nyt checkout-flow eller platformsskift afslutter fristen. Og brugsklager udløser kontrol uanset lanceringsdato.</p></div>
      <div class="card"><h3>Er mikrovirksomheder undtaget?</h3><p>Tjeneste-undtagelsen gælder ved færre end 10 ansatte og under 2 mio. € i omsætning. Den dækker IKKE produkter du sælger, og den forhindrer ikke enterprise-kunder i at kræve WCAG-overensstemmelse kontraktuelt.</p></div>
      <div class="card"><h3>Hvilken standard skal vi opfylde?</h3><p>Formodningen om overensstemmelse knytter sig til EN 301 549, som indarbejder WCAG 2.1 niveau AA for webindhold. WCAG 2.1 AA plus erklæringen og feedbackkanalen dækker langt størstedelen af EAA-forpligtelserne for websites.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Relaterede guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">TJEKLISTE</span><h3><a href="/blog/eaa-accessibility-checklist" style="color:var(--color-accent);text-decoration:none;">EAA-tjekliste</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">HÅNDHÆVELSE</span><h3><a href="/blog/eaa-enforcement-2026" style="color:var(--color-accent);text-decoration:none;">EAA-håndhævelse 2026: bøder og sager</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">ERKLÆRINGEN</span><h3><a href="/blog/gratis-eaa-saetninger" style="color:var(--color-accent);text-decoration:none;">Gratis værktøjer til erklæringen</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">OVERLAYS</span><h3><a href="/blog/accessibility-overlays-eaa" style="color:var(--color-accent);text-decoration:none;">Hvorfor overlays ikke løser EAA</a></h3></div>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
    <p><a href="/">← Forside</a> · <a href="/scan-da">Gratis scanner</a> · <a href="/free-tools">Gratis værktøjer</a> · <a href="/#blog">Blog</a></p>
</footer>
</body>
</html>'''
    return slug, h + body


def update_sitemap(slugs):
    p = f'{SITE}/sitemap.xml'
    c = open(p).read()
    add = ''.join(f'  <url><loc>{BASE}/blog/{s}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'
                  for s in slugs)
    assert all(f'/blog/{s}</loc>' not in c for s in slugs), 'slug already in sitemap'
    c = c.replace('</urlset>', add + '</urlset>')
    open(p, 'w').write(c)


DA_CARDS = '''      <div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">
        <h3><a href="/blog/gratis-eaa-saetninger" style="color:inherit;text-decoration:none;">Gratis værktøjer til tilgængelighedserklæringen (dansk)</a></h3>
        <p>Generator, scanner og kontrasttjek til den erklæring, Den Europæiske Accessibilitetslov kræver — hvad dækker de, og hvad gør du med resultatet?</p>
        <a href="/blog/gratis-eaa-saetninger" class="btn-secondary" style="margin-top:12px;">Læs guiden →</a>
      </div>
      <div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">
        <h3><a href="/blog/eaa-frister-2026" style="color:inherit;text-decoration:none;">EAA-fristen er overskredet (dansk)</a></h3>
        <p>Hvad håndhæves der i 2026, hvem er undtaget, hvor store er bøderne — og den hurtigste vej til dokumenteret overensstemmelse.</p>
        <a href="/blog/eaa-frister-2026" class="btn-secondary" style="margin-top:12px;">Læs guiden →</a>
      </div>
'''


def add_frontpage_cards():
    p = f'{SITE}/index.html'
    c = open(p).read()
    if '/blog/eaa-frister-2026' in c:
        print('frontpage cards already present')
        return
    anchor = '<div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">\n        <h3><a href="/blog/free-gdpr-document-generators"'
    i = c.find(anchor)
    assert i > 0, 'anchor not found in index.html'
    c = c[:i] + DA_CARDS + c[i:]
    open(p, 'w').write(c)
    print('frontpage cards added')


def check_links(files):
    import os
    broken = []
    for path in files:
        html = open(path).read()
        for m in set(re.findall(r'href="(/[^"#]*?)"', html)):
            url = m.split('?')[0]
            if url.startswith(('http://', 'https://')):
                continue
            target = ('site' + url).rstrip('/')
            if not (os.path.exists(target) or os.path.exists(target + '.html')
                    or url == '/' or os.path.isdir(target)
                    or (target + '/index.html')):
                # index.html fallback
                if os.path.exists(target + '/index.html') if target != 'site' else False:
                    continue
                broken.append((path, m))
    return broken


def main():
    slug, html = da_deadline_page()
    with open(f'{SITE}/blog/{slug}.html', 'w') as f:
        f.write(html)
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    assert blocks, 'no JSON-LD'
    for b in blocks:
        d = json.loads(b)
        assert d['@context'] == 'https://schema.org' and d['@type'] == 'Article', slug
        assert '&#64;' not in b and '@context' in d
    print(f'{slug}.html written, JSON-LD OK')
    update_sitemap([slug])
    print('sitemap updated')
    add_frontpage_cards()
    broken = check_links([f'{SITE}/blog/{slug}.html', f'{SITE}/index.html'])
    print('broken internal links:', broken if broken else 'none')


if __name__ == '__main__':
    main()
