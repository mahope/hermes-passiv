#!/usr/bin/env python3
"""Iteration 459: Danish mirrors runde 7 (5 sider).

Genbruger al mekanik fra tools/make_blog_da_mirrors_453.py via importlib —
kun PAGES-listen er ny. Idempotent: anden kørsel laver ingen ændringer.
"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    'mirrors_453', os.path.join(HERE, 'make_blog_da_mirrors_453.py'))
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

PAGES = [
    # ------------------------------- Compliance-check GitHub Action ---
    dict(
        en_slug='compliance-check-github-action',
        slug='compliance-tjek-github-action',
        badge='GITHUB ACTION &middot; AUTOMATISERING &middot; EU-COMPLIANCE',
        title_tag='Automatisér dine EU-compliance-tjek med en GitHub Action (2026)',
        h1='Automatisér dine EU-compliance-tjek<br>i CI',
        desc='Gratis GitHub Action der tjekker et website for 9 ting: privatliv, '
             'vilkår, cookie-samtykke, imprint, tilgængelighed, DPA, '
             'sikkerhedsheadere, meta-tags og hreflang. Kører i CI efter hver '
             'deploy. Nul afhængigheder.',
        subtitle='Til webbureauer og devops-team i EU: de samme ni tjek efter hver '
                 'eneste deploy — uden at nogen åbner siden og klikker sig igennem '
                 'tre sider for at konstatere at "det er vist der".',
        read='6 minutters læsning',
        intro='Driver du kundersider i EU, har du haft samtalen: "Har sitet en '
              'privatlivspolitik? Vilkår? Cookie-samtykke?" Svaret er typisk "tror '
              'jeg" — og så klikker nogen sig igennem sitet for at bekræfte det. '
              'Netop det manuelle tjek bør ligge i CI: efter hver deploy, før '
              'kunden ser det, automatisk. Action\'en mahope/compliance-site-check '
              'gør præcis det — gratis, open source og helt uden npm-'
              'afhængigheder.',
        cards=[
            ('\u2705 Ni tjek i \u00e9n action', 'Seks EU-compliance-sider (privatliv, vilk\u00e5r, '
             'cookie-banner, imprint, tilg\u00e6ngelighedserkl\u00e6ring, DPA), fem '
             'sikkerhedsheadere, meta-tags og hreflang \u2014 alt i \u00e9n rapport.'),
            ('\u23f1 To minutters setup', '\u00c9n YAML-fil under .github/workflows/. Ingen '
             'API-n\u00f8gle, ingen konto, ingen installation \u2014 Node 20\'s indbyggede '
             'fetch klarer alt.'),
            ('\U0001f6a6 Fail kun n\u00e5r du vil', 'Som standard rapporterer den kun. S\u00e6t '
             'fail-on-missing til fx "privacy, imprint, security-headers" hvis '
             'pipelinen skal fejle p\u00e5 konkrete mangler.'),
        ],
        sections=[
            ('Hvad den tjekker \u2014 ni punkter', [
                '<p>EU-compliance (6):</p>',
                '<ul><li><strong>Privatlivspolitik</strong> \u2014 pr\u00f8ver /privacy, '
                '/privacy-policy, /datenschutz m.fl.</li>'
                '<li><strong>Vilk\u00e5r</strong> \u2014 /terms, /tos, /conditions, /agb</li>'
                '<li><strong>Cookie-samtykke</strong> \u2014 genkender 15+ platforme '
                '(Cookiebot, OneTrust, Complianz, Osano, Termly m.fl.)</li>'
                '<li><strong>Imprint</strong> \u2014 /impressum, /imprint, /legal (krav i '
                'Tyskland og \u00d8strig)</li>'
                '<li><strong>Tilg\u00e6ngelighedserkl\u00e6ring</strong> \u2014 krav under EAA</li>'
                '<li><strong>DPA</strong> \u2014 /dpa, krav under GDPR art. 28</li></ul>',
                '<p>Sikkerhedsheadere (5): CSP, HSTS, X-Frame-Options, '
                'X-Content-Type-Options og Referrer-Policy.</p>',
                '<p>Meta og sprog: titell\u00e6ngde, description, viewport, canonical, '
                'robots, OG-tags samt lang-attribut og hreflang-alternatives.</p>',
            ]),
            ('Ops\u00e6tningen p\u00e5 to minutter', [
                '<p>L\u00e6g denne fil i dit repository som '
                '.github/workflows/compliance-check.yml:</p>',
                '<pre>name: Ugentligt compliance-tjek\n'
                'on:\n'
                '  schedule:\n'
                '    - cron: \'0 8 * * 1\'   # hver mandag\n'
                '  workflow_dispatch:\n'
                'jobs:\n'
                '  check:\n'
                '    runs-on: ubuntu-latest\n'
                '    steps:\n'
                '      - uses: actions/checkout@v4\n'
                '      - uses: mahope/compliance-site-check@v2\n'
                '        with:\n'
                '          url: \'https://kundesite.dk\'\n'
                '          fail-on-missing: \'privacy, imprint, accessibility, '
                'security-headers\'</pre>',
            ]),
            ('Hvorfor det betyder noget for bureauer', [
                '<p>EU-h\u00e5ndh\u00e6velsen accelererer: GDPR-b\u00f8der passerede 1,9 mia. i '
                '2025, og EAA-h\u00e5ndh\u00e6velsen startede juni 2025. Kravene er ikke '
                'valgfrie \u2014 men de skal heller ikke kr\u00e6ve at et menneske manuelt '
                'tjekker sidens footer p\u00e5 hvert kundewebsted.',
                '</p>',
                '<p>Action\'en giver et objektivt, automatiseret fundament. Den '
                'erstatter ikke juridisk genneml\u00e6sning \u2014 men den fanger de mest '
                'almindelige huller inden de n\u00e5r en kunde, en revisor eller en '
                'tilsynsmyndighed.</p>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan din side gratis'),
              ('/free-tools', 'Gratis v\u00e6rkt\u00f8jer')],
        related=[('/da/blog/eaa-tjekliste-2026', 'EAA-tjekliste'),
                 ('/da/blog/eaa-frist-hvad-nu', 'EAA-fristen: hvad nu?'),
                 ('/da/blog/gratis-eaa-saetninger', 'Gratis EAA-s\u00e6tninger')],
        da_link_text='Automatis\u00e9r dine EU-compliance-tjek med en GitHub Action',
        faqs=[
            ('Hvad tjekker action\'en pr\u00e6cist?',
             'Ni ting: privatlivspolitik, vilk\u00e5r, cookie-samtykke-banner, imprint, '
             'tilg\u00e6ngelighedserkl\u00e6ring, DPA, fem sikkerhedsheadere, SEO-meta-tags og '
             'hreflang/sprogerkl\u00e6ring. Sidetjek pr\u00f8ver g\u00e6ngse URL-stier og validerer '
             'indholdet; headere og meta l\u00e6ses direkte fra forsidens respons.'),
            ('Kan pipelinen fejle hvis sider mangler?',
             'Ja. Angiv fail-on-missing: \'privacy, imprint, accessibility, '
             'security-headers\' for kun at fejle p\u00e5 bestemte tjek, eller \'any\' '
             'for alle. Som standard rapporteres der kun.'),
            ('Hvad koster det?',
             'Intet. Action\'en er free and open source (MIT), har nul '
             'npm-afh\u00e6ngigheder, kr\u00e6ver ingen API-n\u00f8gle og k\u00f8rer p\u00e5 GitHubs '
             'standard-runners.'),
        ],
    ),
    # ------------------------------------------- URL redirect chain ---
    dict(
        en_slug='check-url-redirect-chain',
        slug='tjek-url-redirect-kaede',
        badge='URL &middot; REDIRECTS &middot; GRATIS V\u00c6RKT\u00d8J',
        title_tag='S\u00e5dan tjekker du en URL\'s redirect-k\u00e6de (gratis v\u00e6rkt\u00f8j, 2026)',
        h1='S\u00e5dan tjekker du en<br>URL\'s redirect-k\u00e6de',
        desc='Spor den fulde redirect-k\u00e6de for enhver URL, inspic\u00e9r sikkerhedsheadere '
             'og tjek SSL-certifikatet. Gratis browserv\u00e6rkt\u00f8j, ingen tilmelding \u2014 '
             'plus hvorfor 301 vs 302 betyder noget for SEO.',
        subtitle='Hver hop koster en rundtur og udvander link-signaler. Se hele '
                 'k\u00e6den, alle statuskoder og certifikatet ved endestationen \u2014 p\u00e5 '
                 'f\u00e5 sekunder.',
        read='4 minutters l\u00e6sning',
        intro='N\u00e5r du taster en URL, lander du ofte et helt andet sted. Serveren '
              'sender browseren gennem to, tre eller flere hop inden den rigtige '
              'side dukker op. Hvert hop er en HTTP-redirect \u2014 og n\u00e5r \u00e9t af dem er '
              'forkert, f\u00e5r du langsomme loads, tabt SEO-v\u00e6rdi eller en \u00f8delagt '
              'side. Denne guide viser hvordan du sporer k\u00e6den p\u00e5 sekunder med det '
              'gratis URL Inspector-v\u00e6rkt\u00f8j, og hvad du g\u00f8r ved problemerne.',
        cards=[
            ('\U0001f517 Hele k\u00e6den', 'Se hvert hop, hver statuskode og alle response-headere '
             'for den endelige destination \u2014 inklusive SSL-certifikatets udl\u00f8b.'),
            ('\U0001f4c9 Hvert hop koster', 'Google f\u00f8lger op til 10 hop, men un\u00f8dvendige hop '
             'udvander link-signaler og tilf\u00f8jer latenstid \u2014 is\u00e6r p\u00e5 mobil.'),
            ('\U0001f512 Certifikatet til sidst', 'En redirect kan skjule et SSL-problem: '
             'f\u00f8rste hop virker, men slutv\u00e6rten har udl\u00f8bet certifikat.'),
        ],
        sections=[
            ('Statuskoderne der t\u00e6ller', [
                '<p><strong>301:</strong> Permanent redirect \u2014 dom\u00e6nemigreringer, '
                'HTTPS-opgraderinger, omd\u00f8bte sider. Videref\u00f8rer fuld SEO-v\u00e6rdi.</p>',
                '<p><strong>302/307:</strong> Midlertidig \u2014 vedligeholdelse, A/B-tests. '
                'S\u00f8gemaskiner beholder den gamle URL indekseret.</p>',
                '<p><strong>308:</strong> Permanent og metodebevarende \u2014 POST forbliver '
                'POST. Bruges bl.a. af Cloudflare Pages.</p>',
                '<p>Den mest almindelige fejl er 302 hvor 301 var meningen: Google '
                'beholder den gamle URL \u2014 eller behandler redirecten som bl\u00f8d '
                'sletning.</p>',
            ]),
           ('Typiske problemer \u2014 og rettelser', [
                '<ul><li><strong>K\u00e6der over 3 hop:</strong> peg den f\u00f8rste redirect '
                'direkte p\u00e5 slut-URL\'en.</li>'
                '<li><strong>Redirect-loops</strong> \u2014 ERR_TOO_MANY_REDIRECTS, typisk '
                'to systemer der hver h\u00e5ndh\u00e6ver www og HTTPS og oph\u00e6ver hinanden.'
                '</li>'
                '<li><strong>HTTP \u2192 mellemstation \u2192 slut:</strong> redirect HTTP '
                'direkte til den endelige HTTPS-URL i \u00e9t hop.</li>'
                '<li><strong>Redirects p\u00e5 interne links:</strong> opdat\u00e9r egne links '
                'til slut-URL\'erne.</li>'
                '<li><strong>Bl\u00f8d 404:</strong> en redirect der serverer forsiden i '
                'stedet for den \u00f8nskede side \u2014 kontroll\u00e9r at slut-URL\'en matcher.'
                '</li></ul>',
            ]),
            ('SSL og headere mens du alligevel er der', [
                '<p>Et certifikat kan v\u00e6re udl\u00f8bet, have en utrov\u00e6rdig k\u00e6de eller kun '
                'underst\u00f8tte TLS 1.0 \u2014 bes\u00f8gende ser fejlen f\u00f8rst efter alle hop. URL '
                'Inspector laver et live TLS-h\u00e5ndtryk mod slutv\u00e6rten og viser '
                'issuer, udl\u00f8bsdato med dage tilbage, TLS-version og om k\u00e6den er '
                'trov\u00e6rdig. Under 30 dage markeres som advarsel; udl\u00f8bet fejler.',
                '</p>',
                '<p>Samme visning viser sikkerhedsheaderne p\u00e5 svaret: HSTS, CSP, '
                'nosniff, frame-beskyttelse og Referrer-Policy \u2014 med '
                'pass/warn/fail-bed\u00f8mmelse.</p>',
            ]),
        ],
        ctas=[('/url-inspector/', '\u00c5bn URL Inspector'),
              ('/scan-da', 'Scan din side gratis')],
        related=[('/da/blog/canonisk-url-guide', 'Kanoniske URLs'),
                 ('/scan-da', 'Scan din side gratis')],
        da_link_text='S\u00e5dan tjekker du en URL\'s redirect-k\u00e6de',
        faqs=[
            ('Hvordan ser jeg en URL\'s redirect-k\u00e6de?',
             'Inds\u00e6t URL\'en i det gratis URL Inspector p\u00e5 /url-inspector/. Du f\u00e5r '
             'hele k\u00e6den med statuskoder, alle response-headere, analyse af '
             'sikkerhedsheadere og SSL-rapport for destinationen \u2014 intet gemmes.'),
            ('Hvilken statuskode skal jeg bruge?',
             '301 til permanente flytninger (dom\u00e6neskift, HTTPS-opgradering) \u2014 den '
             'viderer\u00f8rer SEO-v\u00e6rdien. 302/307 kun til midlertidige \u00e6ndringer. 308 '
             'n\u00e5r POST-data skal bevares gennem redirecten.'),
            ('Hvor mange hop er for mange?',
             '\u00c9t hop er ideelt, to er okay. Over tre hop b\u00f8r du korte af ved at pege '
             'de tidlige redirects direkte p\u00e5 slut-URL\'en \u2014 hvert ekstra hop koster '
             'latenstid og udvander signaler.'),
        ],
    ),
    # --------------------------------------- HTML table to CSV converter ---
    dict(
        en_slug='html-table-to-csv-converter',
        slug='html-tabel-til-csv-konverter',
        badge='CSV &middot; TABELLER &middot; GRATIS V\u00c6RKT\u00d8J',
        title_tag='HTML-tabel til CSV \u2014 gratis, lokalt og RFC 4180-korrekt (2026)',
        h1='HTML-tabel til CSV<br>p\u00e5 to klik',
        desc='Konvert\u00e9r enhver HTML-tabel til ren CSV direkte i browseren: '
             'RFC 4180-overholder, klar til Excel og Google Sheets, intet sendes '
             'til en server.',
        subtitle='Skal tabellen fra en hjemmeside ind i Excel eller Google Sheets? '
                 'Inds\u00e6t HTML\'en og f\u00e5 RFC 4180-korrekt CSV \u2014 hver celle p\u00e5 sin '
                 'plads, intet sendes nogen steder hen.',
        read='4 minutters l\u00e6sning',
        intro='En HTML-tabel er ikke bare tekst \u2014 og CSV tolererer ikke slurvet '
              'tekst. Tre ting g\u00e5r n\u00e6sten altid galt ved manuel konvertering: '
              'kommaer i celler deler kolonnen, linjeskift i celler kn\u00e6kker r\u00e6kke-'
              'strukturen, og colspan/nested markup giver ekstra kolonner eller '
              'tomme felter. Det gratis Clean Copy-webv\u00e6rkt\u00f8j h\u00e5ndterer alle tre '
              '\u2014 100 % lokalt i din browser.',
        cards=[
            ('\u2705 RFC 4180-korrekt', 'Celler med komma, anf\u00f8rselstegn eller linjeskift '
             'omsluttes og escapes automatisk \u2014 filen \u00e5bner rent i ethvert regneark.'),
            ('\U0001f3af Kun tabellen', 'Prosa, menuer og reklamer uden for tabellen droppes, '
             'n\u00e5r der er en tabel i det du inds\u00e6tter.'),
            ('\U0001f512 100 % lokalt', 'Konverteringen k\u00f8rer i din browser. Dine data '
             'forlader aldrig din maskine.'),
        ],
        sections=[
            ('S\u00e5dan g\u00f8r du', [
                '<p><strong>1. Hent tabellens HTML:</strong> H\u00f8jreklik p\u00e5 tabellen '
                '\u2192 Unders\u00f8g \u2192 h\u00f8jreklik p\u00e5 &lt;table&gt;-elementet \u2192 '
                'Copy \u2192 Copy outerHTML. (Alternativt Ctrl+U og find tabelblokken.)</p>',
                '<p><strong>2. Inds\u00e6t og v\u00e6lg CSV:</strong> G\u00e5 til /clean-copy-tool, '
                'inds\u00e6t HTML\'en og v\u00e6lg CSV som outputformat.</p>',
                '<p><strong>3. Gem som .csv:</strong> Kopi\u00e9r resultatet ind i en '
                ' teksteditor og gem som fx konkurrent-priser.csv \u2014 eller s\u00e6t det '
                'lige ind i Excel / Google Sheets via Data \u2192 Fra tekst/CSV.</p>',
            ]),
            ('Dine muligheder sammenlignet', [
                '<table class="compare" style="width:100%;border-collapse:collapse;">'
                '<tr><th style="text-align:left;padding:8px;border-bottom:2px solid #ccc">Metode</th>'
                '<th style="text-align:left;padding:8px;border-bottom:2px solid #ccc">RFC 4180?</th>'
                '<th style="text-align:left;padding:8px;border-bottom:2px solid #ccc">Hage</th></tr>'
                '<tr><td style="padding:8px;border-bottom:1px solid #ddd">Manuel kopiering</td>'
                '<td style="padding:8px;border-bottom:1px solid #ddd">Nej</td>'
                '<td style="padding:8px;border-bottom:1px solid #ddd">Kommaer og '
                'linjeskift \u00f8del\u00e6gger kolonnerne</td></tr>'
                '<tr><td style="padding:8px;border-bottom:1px solid #ddd">Sitens egen eksportknap</td>'
                '<td style="padding:8px;border-bottom:1px solid #ddd">Sommetiden</td>'
                '<td style="padding:8px;border-bottom:1px solid #ddd">Findes sj\u00e6ldent; '
                'ofte bag en betalt plan</td></tr>'
                '<tr><td style="padding:8px;border-bottom:1px solid #ddd">Python-script (BeautifulSoup)</td>'
                '<td style="padding:8px;border-bottom:1px solid #ddd">Ja</td>'
                '<td style="padding:8px;border-bottom:1px solid #ddd">Kr\u00e6ver kode og '
                'milj\u00f8ops\u00e6tning</td></tr>'
                '<tr><td style="padding:8px"><a href="/clean-copy-tool" '
                'style="color:var(--color-accent);">Clean Copy webv\u00e6rkt\u00f8j \u2014 CSV-tilstand</a></td>'
                '<td style="padding:8px">Ja</td>'
                '<td style="padding:8px">Ingen \u2014 gratis, ingen installation, k\u00f8rer lokalt</td></tr>'
                '</table>',
                '<p>Bruger du det ofte? Samme CSV-motor driver ogs\u00e5 en '
                '<a href="/clean-copy" style="color:var(--color-accent);">'
                'browserudvidelse</a>, et CLI-v\u00e6rkt\u00f8j og en Obsidian-plugin.</p>',
            ]),
            ('Colspan, nestede tabeller og Markdown', [
                '<p>Clean Copy h\u00e5ndterer colspan/rowspan ved at gentage v\u00e6rdien hen '
                'over de d\u00e6kkede kolonner, flader nested markup ud til ren tekst og '
                'dropper prosa uden for tabellen \u2014 s\u00e5 du kun f\u00e5r r\u00e6kker og kolonner.',
                '</p>',
                '<p>Skal du have Markdown i stedet? Samme v\u00e6rkt\u00f8j udskriver ogs\u00e5 '
                'Markdown-tabeller (til Notion, Obsidian, GitHub) og WikiLinks-format '
                '\u2014 bare skift outputtilstand.</p>',
            ]),
        ],
        ctas=[('/clean-copy-tool', '\u00c5bn konverteren'),
              ('/clean-copy', 'Om Clean Copy')],
        related=[('/clean-copy', 'Clean Copy-udvidelsen'),
                 ('/scan-da', 'Scan din side gratis')],
        da_link_text='HTML-tabel til CSV \u2014 gratis og RFC 4180-korrekt',
        faqs=[
            ('Hvordan konverterer jeg en HTML-tabel til CSV?',
             '\u00c5bn det gratis webv\u00e6rkt\u00f8j p\u00e5 /clean-copy-tool, kopi\u00e9r tabellens HTML '
             '(h\u00f8jreklik \u2192 Unders\u00f8g \u2192 Copy outerHTML), inds\u00e6t den i '
             'inputfeltet og v\u00e6lg CSV som outputformat. Du f\u00e5r straks '
             'RFC 4180-overholdende CSV.'),
            ('Bevares celler med kommaer eller linjeskift?',
             'Ja. Celler der indeholder kommaer, anf\u00f8rselstegn eller linjeskift '
             'ombrydes automatisk i dobbelte anf\u00f8rselstegn, og indre tegn escapes \u2014 '
             'pr\u00e6cis som standarden kr\u00e6ver. Ingen v\u00e6rdier klippes af.'),
            ('Bliver mine data sendt til en server?',
             'Nej. Konverteringen k\u00f8rer 100 % lokalt i din browser med JavaScript. '
             'Intet du inds\u00e6tter forlader nogensinde din maskine.'),
        ],
    ),
    # ------------------------------------------- HTTP headers reference ---
    dict(
        en_slug='http-headers-reference',
        slug='http-headere-reference',
        badge='HTTP &middot; HEADERE &middot; REFERENCE',
        title_tag='HTTP-headere reference: alle headerne der t\u00e6ller for SEO og sikkerhed',
        h1='HTTP-headere:<br>alle der t\u00e6ller',
        desc='Komplet reference til HTTP-response-headere: caching, sikkerhedsheadere '
             '(CSP, HSTS), SEO-relevante headere \u2014 og hvad hver enkelt g\u00f8r. Gratis '
             'v\u00e6rkt\u00f8j til at tjekke enhver URL.',
        subtitle='F\u00f8r HTML\'en n\u00e5r frem, sender serveren en bunke response-headere '
                 'der styrer caching, sikkerhed, redirects og hvordan s\u00f8gemaskiner '
                 'behandler siden. De fleste sider f\u00e5r flere af dem forkert.',
        read='7 minutters l\u00e6sning',
        intro='Hver gang en browser loader en side, sender serveren et s\u00e6t '
              'HTTP-response-headere f\u00f8r noget HTML ankommer. De styrer caching, '
              'sikkerhed, redirects og hvordan s\u00f8gemaskiner behandler din side \u2014 '
              'og alligevel f\u00e5r de fleste sider flere af dem forkert. Dette er en '
              'praktisk reference: hvad hver header g\u00f8r, hvorn\u00e5r den t\u00e6ller, og en '
              'typisk fejl du skal undg\u00e5. Til sidst kan du tjekke enhver URL med '
              'det gratis URL Inspector-v\u00e6rkt\u00f8j.',
        cards=[
            ('\U0001f510 Sikkerhed', 'CSP, HSTS, nosniff, frame-beskyttelse og '
             'Referrer-Policy er de fem headere enhver side b\u00f8r have.'),
            ('\u26a1 Cache rigtigt', 'Lang cache p\u00e5 hashede statiske filer, no-cache p\u00e5 '
             'HTML. Lang cache p\u00e5 HTML betyder at bes\u00f8gende ser gamle sider efter '
             'din deploy.'),
            ('\U0001f50e SEO-relevante', 'Link: rel=canonical, X-Robots-Tag og Location '
             '(3xx) styrer hvordan s\u00f8gemaskiner behandler dine URLs.'),
        ],
        sections=[
            ('Sikkerhedsheadere', [
                '<table style="width:100%;border-collapse:collapse;margin:1rem 0;">'
                '<tr><th style="text-align:left;padding:8px;border-bottom:2px solid #ccc">Header</th>'
                '<th style="text-align:left;padding:8px;border-bottom:2px solid #ccc">Hvad den g\u00f8r</th>'
                '<th style="text-align:left;padding:8px;border-bottom:2px solid #ccc">Typisk fejl</th></tr>'
                '<tr><td style="padding:8px;vertical-align:top"><code>Strict-Transport-Security</code></td>'
                '<td style="padding:8px;vertical-align:top">Browseren m\u00e5 kun n\u00e5 sitet '
                'via HTTPS. max-age mindst 31536000 (\u00e9t \u00e5r).</td>'
                '<td style="padding:8px;vertical-align:top">Glemt includeSubDomains \u2014 '
                'subdom\u00e6ner forbliver ubeskyttet.</td></tr>'
                '<tr><td style="padding:8px;vertical-align:top"><code>Content-Security-Policy</code></td>'
                '<td style="padding:8px;vertical-align:top">Hvidlister hvor scripts, '
                'styles og frames m\u00e5 loades fra. Den mest effektive XSS-forsvar.</td>'
                '<td style="padding:8px;vertical-align:top">unsafe-inline overalt "for '
                'at det bare virker" \u2014 fjerner det meste af beskyttelsen.</td></tr>'
                '<tr><td style="padding:8px;vertical-align:top"><code>X-Content-Type-Options</code></td>'
                '<td style="padding:8px;vertical-align:top">nosniff: stopper browserens '
                'g\u00e6tteri p\u00e5 filtyper.</td>'
                '<td style="padding:8px;vertical-align:top">Kun sat p\u00e5 HTML \u2014 den t\u00e6ller '
                'mest p\u00e5 uploads og API\'er.</td></tr>'
                '<tr><td style="padding:8px;vertical-align:top"><code>X-Frame-Options</code></td>'
                '<td style="padding:8px;vertical-align:top">DENY/SAMEORIGIN stopper '
                'clickjacking via iframes.</td>'
                '<td style="padding:8px;vertical-align:top">Alene om den: CSP\'s '
                'frame-ancestors er st\u00e6rkere og erstatter den.</td></tr>'
                '<tr><td style="padding:8px;vertical-align:top"><code>Referrer-Policy</code></td>'
                '<td style="padding:8px;vertical-align:top">Styrer hvor meget '
                'referrer-data der l\u00e6kker ved udg\u00e5ende klik. '
                'strict-origin-when-cross-origin er dagens fornuftige standard.</td>'
                '<td style="padding:8px;vertical-align:top">Udeladt: fulde URLs (inkl. '
                'query-strenge med persondata) l\u00e6kker til alle linkede sites.</td></tr>'
                '</table>',
            ]),
            ('Caching og SEO', [
                '<p><strong>Cache-Control:</strong> statiske filer: public, '
                'max-age=31536000, immutable. HTML: no-cache s\u00e5 opdateringer ses '
                'med det samme. <strong>ETag:</strong> fingeraftryk der giver en lille '
                '304 i stedet for hele siden. <strong>Expires:</strong> \u00e6ldre '
                'forg\u00e6nger \u2014 ignoreres n\u00e5r Cache-Control findes. <strong>Vary:'
                'User-Agent</strong> er en klassisk fejl der fragmenterer cachen i '
                'hundredvis af n\u00e6sten-tomme entries.</p>',
                '<p><strong>Link: rel=canonical</strong> er kanon-tagget som HTTP-'
                'header \u2014 nyttigt n\u00e5r samme fil serveres p\u00e5 flere URLs. Pas p\u00e5 '
                'modstridende kanoniske: header siger A, meta-tag siger B \u2014 Google '
                'v\u00e6lger selv. <strong>X-Robots-Tag: noindex</strong> holder fx en PDF '
                'ude af s\u00f8geresultater. Ved vedligeholdelse: 503 med Retry-After, '
                'ellers begynder Google at droppe siderne.</p>',
            ]),
            ('Et sundt minimum', [
                '<pre>Strict-Transport-Security: max-age=31536000; includeSubDomains\n'
                'X-Content-Type-Options: nosniff\n'
                'Referrer-Policy: strict-origin-when-cross-origin\n'
                'Content-Security-Policy: frame-ancestors \'self\'\n'
                '# HTML:\nCache-Control: no-cache\n'
                '# hashede statiske filer:\n'
                'Cache-Control: public, max-age=31536000, immutable</pre>',
                '<p>Tjek enhver URL p\u00e5 sekunder: det gratis URL Inspector henter '
                'siden, f\u00f8lger alle redirects, lister alle response-headere, bed\u00f8mmer '
                'sikkerhedsheaderne pass/warn/fail og viser SSL-certifikatet \u2014 uden '
                'konto og uden at noget gemmes.</p>',
            ]),
        ],
        ctas=[('/url-inspector/', 'Tjek dine headere'),
              ('/scan-da', 'Scan din side gratis')],
        related=[('/da/blog/canonisk-url-guide', 'Kanoniske URLs'),
                 ('/scan-da', 'Scan din side gratis')],
        da_link_text='HTTP-headere: referencen for SEO og sikkerhed',
        faqs=[
            ('Hvilke HTTP-headere b\u00f8r ethvert site have?',
             'Minimum: Strict-Transport-Security (max-age mindst \u00e9t \u00e5r, '
             'includeSubDomains), X-Content-Type-Options: nosniff, Referrer-Policy: '
             'strict-origin-when-cross-origin og en Content-Security-Policy \u2014 selv en '
             'beskeden en med frame-ancestors er bedre end ingen.'),
            ('Hvad er forskellen p\u00e5 Expires og Cache-Control?',
             'Cache-Control er den moderne header og vinder altid n\u00e5r begge er sat. '
             'Expires er en \u00e6ldre forg\u00e6nger du kun beh\u00f8ver for meget gamle '
             'klienter \u2014 s\u00e6t ikke Expires og tro at den tilsides\u00e6tter Cache-Control.'),
            ('Hvordan tjekker jeg en sides headere?',
             'Inds\u00e6t URL\'en i det gratis URL Inspector p\u00e5 /url-inspector/. Du ser '
             'alle response-headere, en pass/warn/fail-bed\u00f8mmelse af '
             'sikkerhedsheaderne, hele redirect-k\u00e6den og SSL-certifikatet.'),
        ],
    ),
    # ------------------------------------- Check SSL certificate expiry ---
    dict(
        en_slug='check-ssl-certificate-expiry',
        slug='tjek-ssl-certifikat-udloeb',
        badge='SSL &middot; CLI &middot; DESKUPTIME',
        title_tag='Tjek SSL-certifikatets udl\u00f8b fra kommandolinjen (uden SaaS)',
        h1='Tjek SSL-certifikatets udl\u00f8b<br>fra terminalen',
        desc='Tjek SSL-certifikatets udl\u00f8b fra terminalen med et gratis CLI-v\u00e6rkt\u00f8j. '
             '\u00c9n kommando, ingen konto, intet abonnement. Virker p\u00e5 ethvert dom\u00e6ne.',
        subtitle='Dit certifikat udl\u00f8ber om N dage \u2014 og du har et dusin dom\u00e6ner at '
                 'tjekke. En SaaS-monitor koster $10/m\u00e5ned. Her er et gratis CLI '
                 'der tjekker SSL-udl\u00f8b, HTTP-status og indholds\u00e6ndringer i \u00e9n '
                 'kommando.',
        read='5 minutters l\u00e6sning',
        intro='Alle certifikater udl\u00f8ber. N\u00e5r dit g\u00f8r det, viser browseren en '
              'advarsel, API-kaldene fejler, og kunderne forsvinder. De store '
              'monitorservices s\u00e6lger dig et abonnement for at fort\u00e6lle dig hvorn\u00e5r '
              'det er ved at ske \u2014 men selve tjekket er trivielt: \u00e5bn en '
              'forbindelse, l\u00e6s certifikatet, beregn dage tilbage. Det beh\u00f8ver du '
              'ikke et SaaS-abonnement til.',
        cards=[
            ('\U0001f4bb \u00c9n kommando', 'npx github:mahope/deskuptime check https://dit-site.dk '
             '\u2014 issuer, dage til udl\u00f8b og HTTP-status med det samme.'),
            ('\U0001f193 Gratis uden gr\u00e6nser', 'CLI\'ens SSL-tjek er gratis og uden begr\u00e6nsninger. '
             'Pro ($19 engang) tilf\u00f8rer skrivebordsapp og e-mail-advarsler.'),
            ('\U0001f6a8 Exit-kode 3', 'Udl\u00f8ber et certifikat inden for 14 dage returnerer '
             'CLI\'en exit-kode 3 \u2014 perfekt som gate i CI/CD.'),
        ],
        sections=[
            ('One-lineren', [
                '<pre>$ npx github:mahope/deskuptime check https://example.com\\n\\n'
                '\u2705 https://example.com\\n   Status:   200 OK\\n   Response: 85ms\\n'
                '   \U0001f512 SSL:     63 days \u2705\\n   \u2014 Content: 559 bytes</pre>',
                '<p>\U0001f512-linjen viser pr\u00e6cis hvor mange dage til udl\u00f8b: gr\u00f8n over 30 '
                'dage, gul 14\u201330, r\u00f8d under 14.</p>',
            ]),
            ('Sammenlignet med openssl', [
                '<p>Den traditionelle vej kr\u00e6ver mere arbejde:</p>',
                '<pre>$ openssl s_client -connect example.com:443 \\\n'
                '  -servername example.com &lt; /dev/null 2&gt;/dev/null \\\n'
                '  | openssl x509 -noout -enddate\n\n'
                'notAfter=Oct 27 12:00:00 2026 GMT</pre>',
                '<p>Derefter skal datan parseses, dage beregnes og et wrapper-script '
                'skrives. DeskUptime g\u00f8r det hele og tilf\u00f8jer HTTP-status og '
                'indholds\u00e6ndringsdetektion i samme output.</p>',
            ]),
            ('Mange dom\u00e6ner og CI/CD', [
                '<p>Tjek en hel liste p\u00e5 \u00e9n gang:</p>',
                '<pre>$ npx github:mahope/deskuptime check \\\n'
                '  https://example.com https://shop.example.com\n\n'
                '\u2705 https://example.com       SSL: 63 days \u2705\n'
                '\U0001f6a8 https://shop.example.com  SSL: 3 days \U0001f525</pre>',
                '<p>I GitHub Actions kan samme engine bruges som step: '
                'mahope/deskuptime@v1 med urls-input. Exit-kode 3 (SSL-advarsel) '
                'fungerer som gate \u2014 lad pipelinen fejle, alarm\u00e9r teamet, og forny '
                'certifikatet inden det er for sent.</p>',
                '<p>Til l\u00f8bende overv\u00e5gning k\u00f8rer watch mode med j\u00e6vne mellemrum og '
                'alarmerer ved \u00e6ndringer \u2014 op til 3 URLs gratis.</p>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan din side gratis'),
              ('/free-tools', 'Gratis v\u00e6rkt\u00f8jer')],
        related=[('/scan-da', 'Scan din side gratis'),
                 ('/free-tools', 'Gratis v\u00e6rkt\u00f8jer')],
        da_link_text='Tjek SSL-certifikatets udl\u00f8b fra kommandolinjen',
        faqs=[
            ('Hvordan tjekker jeg SSL-udl\u00f8b fra kommandolinjen?',
             'K\u00f8r npx github:mahope/deskuptime check https://dit-site.dk. Du f\u00e5r '
             'HTTPS-status, SSL-issuer og dage til udl\u00f8b. Ingen installation, ingen '
             'konto, k\u00f8rer helt lokalt.'),
            ('Hvad er openssl-kommandoen?',
             'openssl s_client -connect example.com:443 -servername example.com '
             '&lt; /dev/null 2&gt;/dev/null | openssl x509 -noout -enddate. Den viser '
             'udl\u00f8bsdatoen, men kr\u00e6ver b\u00f8vlet parsing \u2014 DeskUptime formaterer det '
             'som et rent antal dage tilbage.'),
            ('Kan jeg tjekke flere dom\u00e6ner p\u00e5 \u00e9n gang?',
             'Ja. DeskUptime tager flere URLs: npx github:mahope/deskuptime check '
             'https://site1.dk https://site2.dk. Hver f\u00e5r sit eget SSL-tjek, og '
             'exit-koden er 3 hvis noget udl\u00f8ber inden for 14 dage.'),
        ],
    ),
]


def main():
    m.PAGES[:] = PAGES
    m.main()


if __name__ == '__main__':
    main()