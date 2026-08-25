#!/usr/bin/env python3
"""Iteration 255: Tre danske spejle af EN-posts.

1. eaa-accessibility-checklist      -> da/blog/eaa-tjekliste-2026
2. nis2-readiness-guide             -> da/blog/nis2-beredskabstjek-2026
3. gdpr-website-compliance-checklist-> da/blog/gdpr-hjemmeside-tjekliste

Hver: ny DA-side (Article+FAQ JSON-LD), hreflang-par begge veje, synligt
krydslink fra EN-post til DA, sitemap-opdatering, intern linkcheck.
"""
import json, re, os, sys
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

PAGES = [
    {
        'slug': 'eaa-tjekliste-2026',
        'en_slug': 'eaa-accessibility-checklist',
        'title': 'EAA-tjekliste 2026: Er din hjemmeside klar til Europas tilgængelighedslov?',
        'h1': 'EAA-Tjekliste<br>2026',
        'desc': ('Komplet EAA-tjekliste for hjemmesider: hvem loven gælder for, '
                 'de 12 vigtigste krav, fristerne og hvordan du selv tester sitet '
                 'gratis — trin for trin.'),
        'og_desc': ('Europas tilgængelighedslov gælder allerede. Tjekliste med de 12 '
                    'vigtigste krav, frister og en gratis selvtest af din hjemmeside.'),
        'badge': 'EAA &middot; TJEKLISTE',
        'subtitle': ('Europas tilgængelighedslov (EAA) er i kraft. Her er tjeklisten '
                     'du kan gå igennem på 30 minutter for at vide, om din hjemmeside '
                     'er klar — eller hvad der mangler.'),
        'cta1': ('<a href="/scan-da" class="btn-primary">Test dit site gratis &rarr;</a>'),
        'cta2': '<a href="#krav" class="btn-secondary">Se de 12 krav</a>',
        'tool_url': '/scan-da',
        'tool_label': 'Scan din side nu',
        'faq': [
            ("Hvem gælder loven for?",
             "Alle virksomheder der sælger varer eller tjenester til forbrugere i EU — "
             "også udenlandske webshops og SaaS. Undtaget er mikrovirksomheder under "
             "10 ansatte og under 2 mio. euro i årlig omsætning."),
            ("Hvad er fristen?",
             "Loven trådte i kraft juni 2025, og myndighederne fører tilsyn fra da af. "
             "I praksis betyder det: jo senere du kommer i gang, desto større risiko "
             "for påbud og bøder."),
            ("Er WCAG 2.1 AA nok?",
             "WCAG 2.1 AA er den praktiske standard de fleste tilsyn arbejder ud fra. "
             "Men loven stiller også krav om dokumentation: en tilgængelighedserklæring "
             "og en feedback-mulighed for brugerne."),
            ("Hvad koster det at blive klar?",
             "En automatisk scanning er gratis. De fleste sider har 10–40 fejl der kan "
             "rettes på få timer: kontrast, alt-tekster, tastaturnavigation, labels. "
             "Manuel test af kritiske brugerflow anbefales ovenpå."),
        ],
        'body': '''
<section class="problem" id="krav">
  <div class="container">
    <h2>De 12 vigtigste krav</h2>
    <ol>
      <li><strong>Kontrast</strong> — tekst skal have mindst 4,5:1 kontrast mod baggrunden.</li>
      <li><strong>Alt-tekster</strong> — alle meningsfulde billeder har beskrivende alt-attribut.</li>
      <li><strong>Tastatur</strong> — alle funktioner kan nås uden mus; ingen keyboard-fælder.</li>
      <li><strong>Fokus-markering</strong> — man kan altid se hvor fokus er.</li>
      <li><strong>Overskriftshierarki</strong> — ét h1, logisk rækkefølge af h2/h3.</li>
      <li><strong>Formular-labels</strong> — alle felter har rigtige labels, ikke kun pladsholder.</li>
      <li><strong>Fejlbeskeder</strong> — formularfejl beskrives i tekst ved feltet.</li>
      <li><strong>Sprogangivelse</strong> — sidens sprog er korrekt sat (lang-attribut).</li>
      <li><strong>Zoom</strong> — siden virker ved 200 % zoom uden tab af indhold.</li>
      <li><strong>Ingen kun-farve-signaler</strong> — fejl vises ikke alene med farve.</li>
      <li><strong>Videoer</strong> — undertekster til indhold med tale.</li>
      <li><strong>Dokumentation</strong> — offentlig tilgængelighedserklæring med dato og feedbackvej.</li>
    </ol>
    <div style="text-align:center;margin-top:20px;">
      <a href="/scan-da" class="btn-primary">Tjek din side gratis nu &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Sådan tester du selv — 30 minutter</h2>
    <ol>
      <li>Kør en automatisk scan med et gratis værktøj
      (<a href="/scan-da" style="color:var(--color-accent);">Accessibility Scanner</a>).</li>
      <li>Gennemgå listen ovenfor punkt for punkt — automatiske værktøjer finder typisk
      kun halvdelen af fejlene.</li>
      <li>Ret de mekaniske fejl først: kontrast, alt-tekster, labels. Det er ofte 80 %
      af problemet.</li>
      <li>Test selv med tabulatoren: kan du bestille, kontakte os og finde kontaktinfo
      uden musen?</li>
      <li>Skriv tilgængelighedserklæringen — se vores guide til
      <a href="/da/blog/skriv-tilgaengelighedserklaering" style="color:var(--color-accent);">hvordan den skrives</a>.</li>
    </ol>
    <p>Læs også vores oversigt over
    <a href="/da/blog/gratis-tilgaengelighedsvaerktoejer">gratis tilgængelighedsværktøjer</a> og
    <a href="/da/blog/tilgaengeligheds-overlays-eaa">hvorfor overlays ikke løser problemet</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/skriv-tilgaengelighedserklaering" lang="da">Skriv tilgængelighedserklæring</a> &middot; '
                    '<a href="/da/blog/gratis-tilgaengelighedsvaerktoejer" lang="da">Gratis værktøjer</a> &middot; '
                    '<a href="/da/blog/wcag-kontrast-checker" lang="da">Kontrast-tjekker</a>'),
    },
    {
        'slug': 'nis2-beredskabstjek-2026',
        'en_slug': 'nis2-readiness-guide',
        'title': 'NIS2-beredskab 2026: Er din virksomhed dækket — og klar?',
        'h1': 'NIS2-Beredskab<br>2026',
        'desc': ('NIS2-readiness guide på dansk: hvem er dækket, hvilke krav gælder, '
                 'fristerne, sanktionerne og en trin-for-trin plan for at komme i mål.'),
        'og_desc': ('Hvem er dækket af NIS2? Hvilke 10 sikkerhedskrav gælder, og hvad '
                    'koster det at være for sent? Guide + gratis selvvurdering.'),
        'badge': 'NIS2 &middot; GUIDE',
        'subtitle': ('NIS2 udvider cybersikkerhedskravene markant i EU. Tjek på 15 minutter, '
                     'om din virksomhed er dækket — og hvad de ti krav konkret betyder for dig.'),
        'cta1': '<a href="/nis2-check-da" class="btn-primary">Tag selvvurderingen &rarr;</a>',
        'cta2': '<a href="#krav" class="btn-secondary">Se de 10 krav</a>',
        'tool_url': '/nis2-check-da',
        'tool_label': 'Tag NIS2-selvvurderingen',
        'faq': [
            ("Hvem er dækket af NIS2?",
             "Mellemstore og store virksomheder i 18 sektorer: energi, transport, bank, "
             "sundhed, digital infrastruktur, offentlig forvaltning m.fl. Mange "
             "leverandører bliver dækket via kundernes kontrakter, selv hvis de ikke selv "
             "rammer størrelsestærsklen."),
            ("Hvad er sanktionerne?",
             "For væsentlige enheder op til 10 mio. euro eller 2 % af den globale omsætning. "
             "Ledelsen kan holdes personligt ansvarlig — det er en af de skæreste dele af loven."),
            ("Skal vi rapportere hændelser?",
             "Ja. Alvorlige hændelser rapporteres tidligt (24/72 timers frister) til det "
             "nationale CSIRT. Har du ingen beredskabsplan, når hændelsen opstår, er det for sent."),
            ("Hvor starter vi?",
             "Med et gap-tjek: hvilke af de ti krav har vi allerede dækket, og hvor er hullerne? "
             "Vores gratis selvvurdering giver dig svaret og en prioriteret liste."),
        ],
        'body': '''
<section class="problem" id="krav">
  <div class="container">
    <h2>De 10 sikkerhedskrav (artikel 21)</h2>
    <ol>
      <li>Risikoanalyser og informations­sikkerhedspolitikker</li>
      <li>Hændelseshåndtering</li>
      <li>Forretningskontinuitet — backup, disaster recovery, krisestyring</li>
      <li>Leverandørkædens sikkerhed</li>
      <li>Sikkerhed i erhvervelse, udvikling og vedligehold — inkl. sårbarheds­håndtering</li>
      <li>Politikker og procedurer til at vurdere effektiviteten</li>
      <li>Grundlæggende cyberhygiejne og træning</li>
      <li>Kryptografi og kryptering hvor relevant</li>
      <li>Menneskelige ressourcer, adgangskontrol og asset management</li>
      <li>Brug af multi-faktor-autentisering og sikker kommunikation</li>
    </ol>
    <div style="text-align:center;margin-top:20px;">
      <a href="/nis2-check-da" class="btn-primary">Se jeres huller — gratis selvvurdering &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Jeres plan i fem trin</h2>
    <ol>
      <li>Afgør om I er dækket (selvvurderingen ovenfor giver svaret).</li>
      <li>Kør et gap-tjek mod de ti krav — dokumentér hvad der allerede er på plads.</li>
      <li>Prioritér hullerne: hændelsesplan og backup først, så leverandørkontrakter og MFA.</li>
      <li>Uddan ledelsen — personligt ansvar gør træningen ikke-frivillig.</li>
      <li>Genbesøg planen årligt, og efter hver væsentlig ændring i systemlandskabet.</li>
    </ol>
    <p>Læs også:
    <a href="/da/blog/nis2-guide-da">den danske NIS2-guide for små webbureauer</a>,
    <a href="/da/blog/nis2-leverandoerkaede-sikkerhed">sikkerhed i leverandørkæden</a> og
    <a href="/da/blog/gratis-nis2-vaerktoejer">gratis NIS2-værktøjer</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/nis2-guide-da" lang="da">NIS2-guide for bureauer</a> &middot; '
                    '<a href="/da/blog/gratis-nis2-vaerktoejer" lang="da">Gratis NIS2-værktøjer</a> &middot; '
                    '<a href="/da/blog/nis2-leverandoerkaede-sikkerhed" lang="da">Leverandørkæde-sikkerhed</a>'),
    },
    {
        'slug': 'gdpr-hjemmeside-tjekliste',
        'en_slug': 'gdpr-website-compliance-checklist',
        'title': 'GDPR-tjekliste for hjemmesider: 12 punkter du skal have styr på',
        'h1': 'GDPR-Tjekliste for<br>Hjemmesider',
        'desc': ('Praktisk GDPR-tjekliste for din hjemmeside: cookie-samtykke, '
                 'privatlivspolitik, databehandleraftaler, formularer og analytics — '
                 'med konkrete tjekpunkter.'),
        'og_desc': ('12 konkrete tjekpunkter: samtykke, privatlivspolitik, DBA\'er, '
                    'formularer og analytics. Gå listen igennem på 30 minutter.'),
        'badge': 'GDPR &middot; TJEKLISTE',
        'subtitle': ('De fleste GDPR-brud på hjemmesider skyldes ikke hackere — men '
                     'cookies uden gyldigt samtykke, manglende databehandleraftaler og '
                     'formularer der deler data forkert. Her er tjeklisten.'),
        'cta1': '<a href="/cookie-check-da" class="btn-primary">Generér cookie-politik &rarr;</a>',
        'cta2': '<a href="#liste" class="btn-secondary">Se de 12 punkter</a>',
        'tool_url': '/cookie-check-da',
        'tool_label': 'Generér din cookie-politik',
        'faq': [
            ("Skal jeg have samtykke før cookies lægges?",
             "Ja, for ikke-nødvendige cookies. Samtykke skal gives FØR cookien sættes, "
             "være lige nemt at sige nej til som ja til, og kunne trækkes tilbage. "
             "Google Analytics og reklamecookies må altså ikke fyre af ved indlæsning."),
            ("Hvad er en databehandleraftale (DBA)?",
             "En skriftlig aftale med hver tredjepart der behandler data på dine vegne: "
             "analytics, hosting, nyhedsbrev, chat. Mangler aftalen, er det en brud "
             "uafhængigt af om noget faktisk går galt."),
            ("Gælder det også for mit privatpersonssite?",
             "Reglerne gælder behandling af persondata. Et site med kun statistik-cookies "
             "og ingen formularer er ofte minimalt — men har du kontaktformular eller "
             "analytics, behandler du persondata."),
            ("Hvor store er bøderne?",
             "Op til 20 mio. euro eller 4 % af global omsætning for de tunge overtrædelser. "
             "De fleste påbud mod websites handler dog om mindre ting — manglende DBA, "
             "ugyldigt samtykke — med rettefrister og lavere gebyrer."),
        ],
        'body': '''
<section class="problem" id="liste">
  <div class="container">
    <h2>De 12 tjekpunkter</h2>
    <ol>
      <li><strong>Cookie-samtykke</strong> — intet ikke-nødvendigt script fyres af før ja.</li>
      <li><strong>Lige vilkår</strong> — "Afvis alle"-knap lige så synlig som "Acceptér".</li>
      <li><strong>Privatlivspolitik</strong> — aktuel, let at finde, nævner alle formål og modtagere.</li>
      <li><strong>DBA'er</strong> — skriftlig aftale med hver databehandler (hosting, analytics, mail).</li>
      <li><strong>Formularer</strong> — formål oplyst, kun nødvendige felter, samtykke ikke forudafkrydset.</li>
      <li><strong>Nyhedsbrev</strong> — dobbelt opt-in og tydeligt afmeldingslink i hver mail.</li>
      <li><strong>Data-minimering</strong> — slet ikke gamle leads, logs og kontakter du ikke bruger.</li>
      <li><strong>Logning</strong> — serverlogs anonymiseres eller begrænses i levetid.</li>
      <li><strong>Tredjeparts-embeds</strong> — YouTube, kort, chat: samme regler som cookies.</li>
      <li><strong>Borgerrettigheder</strong> — en kendt vej til indsigt, rettelse og sletning.</li>
      <li><strong>Databrud-plan</strong> — hvem gør hvad inden for 72 timer, hvis noget lækker.</li>
      <li><strong>Dokumentation</strong> — registrer over hvilke data I behandler, hvorfor og hvor længe.</li>
    </ol>
    <div style="text-align:center;margin-top:20px;">
      <a href="/cookie-check-da" class="btn-primary">Start med cookie-politikken &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Hvad tager længst tid?</h2>
    <p>Erfaringsmæssigt: DBA'erne. De fleste sites har 5–15 tredjeparter der behandler
    data, og halvdelen af dem mangler aftaler. Start med at lave listen — det tager en
    time og afgør resten af arbejdet.</p>
    <p>Læs videre:
    <a href="/da/blog/gdpr-boeder-2026">GDPR-bøder i 2026</a>,
    <a href="/da/blog/dbbaftale-webbureau">DBA-aftalen for webbureauer</a> og
    <a href="/da/blog/cookie-consent-gdpr-2026">cookie-samtykke og GDPR i 2026</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/gdpr-boeder-2026" lang="da">GDPR-bøder 2026</a> &middot; '
                    '<a href="/da/blog/dbbaftale-webbureau" lang="da">DBA-aftale</a> &middot; '
                    '<a href="/da/blog/cookie-consent-gdpr-2026" lang="da">Cookie-samtykke</a>'),
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
    <p class="hero-note">Opdateret august 2026 &middot; 7 minutters læsning</p>
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
  <p><a href="/da">Forside</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/scan-da">Scanner</a> &middot; <a href="/da/#blog">Blog</a></p>
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


def add_hreflang_pair(en_slug, da_path):
    en_f = f'{SITE}/blog/{en_slug}.html'
    da_f = f'{SITE}/{da_path}.html'
    en = open(en_f).read()
    da = open(da_f).read()
    da_url = f'{BASE}/{da_path}'
    if f'hreflang="da" href="{da_url}"' not in en:
        en = en.replace('</head>',
                        f'<link rel="alternate" hreflang="en" href="{BASE}/blog/{en_slug}">\n'
                        f'<link rel="alternate" hreflang="da" href="{da_url}">\n</head>')
        open(en_f, 'w').write(en)
        print(f'{en_slug}: hreflang pair added')
    else:
        print(f'{en_slug}: hreflang already present')
    if 'Dansk version af denne guide' not in en:
        done = False
        for anchor in ('<footer style="padding:32px 24px;">', '<footer class="site-footer">',
                       '<footer'):
            if anchor in en:
                en = open(en_f).read().replace(anchor,
                    f'<p><a href="/{da_path}" lang="da">Dansk version af denne guide</a></p>\n{anchor}', 1)
                open(en_f, 'w').write(en)
                print(f'{en_slug}: DA cross-link added')
                done = True
                break
        if not done:
            print(f'{en_slug}: WARNING no footer anchor found')
    # DA page already carries its own hreflang from build_page


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
    outs, en_files = [], []
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
        add_hreflang_pair(p['en_slug'], f'da/blog/{p["slug"]}')
        outs.append(out)
        en_files.append(f'{SITE}/blog/{p["en_slug"]}.html')

    broken = check_links(outs + en_files)
    if broken:
        print('BROKEN INTERNAL LINKS:')
        for path, link in broken:
            print(f'  {path} -> {link}')
        sys.exit(1)
    print('Internal link check: OK')


if __name__ == '__main__':
    main()
