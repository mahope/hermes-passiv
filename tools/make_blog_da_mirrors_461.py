#!/usr/bin/env python3
"""Iteration 461: Danish mirrors — de sidste 5 EN-only blogindlæg.

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
    # ------------------------------------------- Bug report form (Bugbottle) ---
    dict(
        en_slug='add-bug-report-form-to-any-website',
        slug='tilfoej-fejlrapport-formular-hjemmeside',
        badge='UDVIKLER-VÆRKTØJ &middot; OPEN SOURCE &middot; BUGS',
        title_tag='Tilføj en fejlrapport-formular til enhver hjemmeside — gratis',
        h1='Tilføj en fejlrapport-formular<br>til enhver hjemmeside',
        desc=('Bugbottle er et open source (MIT) JavaScript-bibliotek der '
              'samler console errors, browser-kontekst og skærmbillede med ét '
              'script-tag. Virker på WordPress, Shopify, statisk HTML og '
              'alt derimellem.'),
        subtitle='Ingen backend krævet. Drop ét script-tag, få detaljerede bugs '
                 'med console-log, viewport, user-agent og screenshot — '
                 'selv på en side uden server.',
        read='6 minutters læsning',
        intro=('Et typisk feedback-formular beder brugeren beskrive problemet i ord. '
               'De fleste gør det ikke. De kan ikke se console\'en, kender ikke deres '
               'viewport-størrelse, og det tager tid at skrive trin op. Resultatet: '
               'du hører om måske ét ud af halvtreds reelle problemer — hver med '
               'detaljer der er ubrugelige. Bugbottle løser præcis dét: '
               'det fanger console-fejlene automatisk, samler kontekst (user-agent, '
               'viewport, sprog, tidsstempel) og tager et skærmbillede — '
               'alt sammen med ét script-tag og ingen afhængigheder.'),
        cards=[
            ('🖥️ Console-fejl automatisk',
             'Det faktiske stack trace sidder allerede i brugerens browser. '
             'Bugbottle fanger det — fjerner den sværeste del af remote debugging.'),
            ('📱 Kontekstsamling',
             'User agent, viewport, sprog, tidsstempel, side-URL — indsamlet '
             'automatisk i stedet for gættet over mail.'),
            ('📸 Skærmbillede med ét kald',
             'Ét billede erstatter ti frem-og-tilbage-beskeder om "dan der ser underligt ud".'),
        ],
        sections=[
            ('Sådan virker det', [
                '<p>Biblioteket er dependency-frit og leveres som almindelig ESM — '
                'det virker direkte fra CDN uden bundler eller npm-installation. '
                'Du initialiserer <code>initConsoleBuffer()</code> før dine brugere '
                'overhovedet har tid til at lave en fejl, og når de klikker "Rapporter", '
                'samler du console-bufferen, konteksten og eventuelt et skærmbillede '
                'og sender det som JSON til et endpoint.</p>',
                '<p>Det medfølgende server-modul (<code>bugbottle/server</code>) '
                'validerer payloads i tre linjer — så du kan afvise ugyldige indsendelser '
                'før de overhovedet når din storage. Biblioteket er MIT-licenseret og '
                'ligger på GitHub: <a href="https://github.com/mahope/bugbottle" '
                'style="color:var(--color-accent)">github.com/mahope/bugbottle</a>.</p>',
            ]),
            ('"Men jeg har ikke en backend"', [
                '<p>Du har tre realistiske muligheder, alle gratis i hobby-skala:</p>'
                '<ol>'
                '<li><strong>Cloudflare Worker / Vercel-funktion / Netlify-funktion</strong> — '
                'accepter POST, gem i KV / R2 / database.</li>'
                '<li><strong>En form-tjeneste</strong> — Formspree, Web3Forms, '
                'FormKeep: ethvert endpoint der accepterer JSON POST kan modtage '
                'en rapport. Brugerens data sendes direkte til tjenesten — '
                'din server rører det aldrig.</li>'
                '<li><strong>GitHub Issues via Action</strong> — '
                '<a href="/da/blog/compliance-tjek-github-action" '
                'style="color:var(--color-accent)">Bugbottle Action</a> '
                'poster rapporten direkte som et GitHub Issue. '
                'Nul infrastruktur — kun en repository secret.</li>'
                '</ol>',
                '<p>Prøv en live-demo: <a href="/bugbottle-demo" '
                'style="color:var(--color-accent)">åbn Bugbottle-testen</a>.</p>',
            ]),
        ],
        ctas=[('/bugbottle-demo', 'Prøv live-demo'),
              ('/scan', 'Scan din side gratis →')],
        related=[('/da/blog/compliance-tjek-github-action', 'GitHub Action')],
        da_link_text='Tilføj en fejlrapport-formular til enhver hjemmeside',
        faqs=[
            ('Virker Bugbottle på alle hjemmesider?',
             'Ja. Biblioteket er rent JavaScript uden afhængigheder og virker '
             'på WordPress, Shopify, Squarespace, Wix, statisk HTML, Next.js, '
             'Vue, React — alt der kan køre et script-tag. Selve formen skal '
             'du selv tilføje, men biblioteket giver dig console-data, kontekst '
             'og screenshot i én funktion.'),
            ('Hvad med GDPR?',
             'Skærmbilleder indeholder potentielt personoplysninger — sørg for '
             'at din fortrolighedserklæring dækker det, og overvej at lade '
             'brugeren vælge fra i formularen. Biblioteket gemmer intet selv; '
             'det er kun din modtager-endpoint der gemmer data.'),
            ('Kan jeg bruge det uden en server?',
             'Ja. Brug GitHub Issues + Action-måden: rapporten postes direkte til '
             'et repository uden at du selv hoster noget. Eller brug en '
             'form-tjeneste som Formspree der modtager JSON.'),
            ('Er det gratis?',
             'Ja, MIT-licenseret. Biblioteket, server-validatoren og GitHub '
             'Action er alle open source og koster ingenting.'),
        ],
    ),
    # ------------------------------------------- Desktop Website Monitor CLI ---
    dict(
        en_slug='desktop-website-monitor-cli',
        slug='overvaag-hjemmeside-fra-terminalen',
        badge='OVERVAAGNING &middot; CLI &middot; DESKUPTIME',
        title_tag='Overvåg dine hjemmesider fra terminalen — drep dit SaaS-abonnement',
        h1='Overvåg dine hjemmesider<br>fra terminalen',
        desc=('Slip for UptimeRobot, Pingdom og Better Stack — DeskUptime er '
              'én engangsbetaling på 149 kr, kører lokalt, tjekker HTTP-status, '
              'SSL-udløb og indholdsændringer. Gratis CLI til op til 3 URL\'er.'),
        subtitle='Drep dit $144/år SaaS-abonnement. DeskUptime tjekker opetid, '
                 'SSL-certifikater og indholdsændringer — hele dit netværk '
                 'overvåges fra én terminal.',
        read='7 minutters læsning',
        intro=('Hvis du driver et lille webbureau, har du sikkert tre eller fire '
               'uptime-tjenester: UptimeRobot Pro, Pingdom Standard, Better Stack — '
               'måske en dedikeret SSL-monitor og en content-change-watcher oveni. '
               'Det er 500-900 kr om året for grønne prikker i et dashboard. '
               'DeskUptime er en engangsudgift på 149 kr, kører på din egen maskine, '
               'og tjekker alt hvad en SaaS-tjeneste gør — plus indholdsændringer.'),
        cards=[
            ('🟢 Uptime + respons',
             'HTTP-statuskode, responstid og redirect-tracking. Præcis hvad '
             'Pingdom måler — men uden abonnement.'),
            ('🔒 SSL-certifikat',
             'Udløbstælling, udsteder, cipher, protokol. Få besked når der '
             'er 14 dage tilbage.'),
            ('📄 Indholdsændringer',
             'SHA-256 hash-sammenligning mellem tjek. Opdag uventede ændringer '
             'og defacement uden at kigge selv.'),
        ],
        sections=[
            ('Gratis CLI vs. Pro', [
                '<p>Terminal-versionen er gratis og kræver ingen konto:</p>'
                '<pre>$ npx github:mahope/deskuptime check https://example.com<br>'
                '✅ https://example.com Status: 200 OK Response: 85ms<br>'
                '🔒 SSL: 63 days ✅ — Content: 559 bytes</pre>',
                '<p>Watch-mode kører i baggrunden, gemmer tilstand i '
                '<code>~/.deskuptime/state.json</code> og giver besked ved '
                'statusændringer: site går ned, SSL udløber inden 14 dage, '
                'eller indhold ændrer sig.</p>',
                '<p>Gratis-niveauet overvåger op til 3 URL\'er. Pro (149 kr) '
                'giver ubegrænset URL\'er, en desktop-app i system tray, plus '
                'email- og webhook-alarmer — én betaling, livsvarige opdateringer.</p>',
            ]),
            ('Universel — virker på alt', [
                '<p>DeskUptime er universelt. Det tjekker udefra — præcis som '
                'en rigtig besøgende ville. WordPress, Shopify, Netlify, '
                'håndskrevet HTML: det er ligegyldigt, fordi værktøjet ikke '
                'installeres på serveren, men kører på din egen maskine.</p>',
                '<p>Licensnøglen aktiveres offline med en checksum — ingen '
                'licensserver, ingen database, intet der går ned når du er '
                'væk i tre måneder.</p>',
            ]),
        ],
        ctas=[('/deskuptime/', 'Se DeskUptime'),
              ('/downloads', 'Download gratis CLI')],
        related=[('/da/blog/canonisk-url-guide', 'Canonisk URL-guide')],
        da_link_text='Overvåg dine hjemmesider fra terminalen',
        faqs=[
            ('Hvad er forskellen på gratis og Pro?',
             'Gratis overvåger op til 3 URL\'er fra terminalen med check, watch, '
             'SSL og content-change. Pro (149 kr engangsbetaling) giver '
             'ubegrænset URL\'er, en desktop-app i system tray med notifikationer, '
             'samt email- og webhook-alarmer.'),
            ('Kan jeg bruge det uden internet?',
             'Værktøjet kører lokalt og tjekker eksterne URL\'er — så det kræver '
             'internet til selve tjekkene. Men licensaktivering, state '
             'og konfiguration er helt offline.'),
            ('Erstatte det UptimeRobot / Pingdom?',
             'Ja. DeskUptime dækker HTTP-status, SSL-udløb, responstid, '
             'redirect-tracking og indholdsændringer — det samme som de '
             'betalte SaaS-tjenester. Forskellen er én betaling i stedet for '
             'løbende abonnement.'),
            ('Hvordan virker licensnøglen?',
             'Pro-nøglen er en checksum genereret fra din hardware. Du aktiverer '
             'den med <code>deskuptime activate NØGLE</code> — helt offline, '
             'ingen licensserver, intet der kan gå ned.'),
        ],
    ),
    # ------------------------------------------- Drupal vs TYPO3 ---
    dict(
        en_slug='drupal-vs-typo3-accessibility',
        slug='drupal-vs-typo3-tilgaengelighed',
        badge='TILGÆNGELIGHED &middot; CMS &middot; SAMMENLIGNING',
        title_tag='Drupal vs TYPO3: tilgængelighed sammenlignet (2026)',
        h1='Drupal vs TYPO3:<br>tilgængelighed sammenlignet',
        desc=('To open-source CMS\'er der bruges af den europæiske '
              'offentlige sektor. Hvordan deres WCAG 2.1 AA-baselines, '
              'extension-økosystemer og remedierings-workflows adskiller sig.'),
        subtitle='Drupal og TYPO3 er de to open source-CMS\'er der oftest bruges '
                 'af europæiske offentlige myndigheder — præcis de organisationer '
                 'med de strengeste tilgængelighedskrav.',
        read='7 minutters læsning',
        intro=('Drupal og TYPO3 er de to open source-CMS\'er der oftest bruges af '
               'europæiske offentlige myndigheder — præcis de organisationer med '
               'de strengeste tilgængelighedskrav. Offentlige myndigheder har været '
               'omfattet af EN 301 549 / WCAG 2.1 AA siden 2019 under '
               'Webtilgængelighedsdirektivet og siden juni 2025 også under '
               'European Accessibility Act. Begge CMS\'er er i stand til fuld '
               'compliance; de adskiller sig i hvor deres standardstyrker ligger, '
               'og hvordan deres extension-økosystemer introducerer risiko.'),
        cards=[
            ('🏛️ Directive Veterans',
             'Begge økosystemer har levet med Webtilgængelighedsdirektivet '
             'siden 2019 — tilgængelighedserklæringer, monitorering og '
             'feedback-mekanismer er velkendt territorium.'),
            ('⚙️ Stærke kerner',
             'Drupal leverer Olivero-fronter temaet bygget til AA; TYPO3 giver '
             'tilgængelig output via Fluid Styled Content og sine '
             'tilgængelighedsfokuserede extensions.'),
            ('🧩 Extension-risiko',
             'Drupal contrib-moduler og TYPO3-extensions injicerer formularer, '
             'views og widgets af ujævn kvalitet — den største kilde til '
             'defekter i praksis.'),
        ],
        sections=[
            ('Hvor Drupal fejler', [
                '<p>Typiske Drupal-defektmønstre:</p>'
                '<ul>'
                '<li><strong>🧩 Contrib-moduler</strong> — formularbyggere, '
                'sliders og kortmoduler overskriver core\'s tilgængelige '
                'defaults: placeholder-only felter, div-baserede kontroller, '
                'manglende aria-expanded.</li>'
                '<li><strong>🎨 Custom-temaer</strong> — sub-temaer dropper '
                'Oliveros fokus-styles, springer landmarks over eller hardcoder '
                'ikke-semantisk markup.</li>'
                '<li><strong>📝 Editor-indhold</strong> — rich-text-indhold '
                'omgår strukturerede felter: fed-tekst pseudo-overskrifter, '
                'tom alt på uploadede billeder, "klik her"-links.</li>'
                '<li><strong>🔄 Opdateringsregressioner</strong> — '
                'modulopdateringer genindfører stille og roligt fiksedee fejl.</li>'
                '</ul>',
            ]),
            ('Hvor TYPO3 fejler', [
                '<p>Typiske TYPO3-defektmønstre:</p>'
                '<ul>'
                '<li><strong>🖼️ Alt-disciplin</strong> — legacy-indhold og '
                'quick-uploads springer alt-metadata over.</li>'
                '<li><strong>🧱 Gamle templates</strong> — sider på '
                'Protostar-æra eller stærkt overridede Fluid-templates '
                'bærer strukturelle tilgængelighedsfejl.</li>'
                '<li><strong>🔌 Extension-overlap</strong> — flere extensions '
                'der håndterer samme funktion (fx kalender, kort) giver '
                'inkonsistent keyboard-adfærd.</li>'
                '<li><strong>📄 PDF-generering</strong> — TYPO3\'s indbyggede '
                'PDF-output mangler ofte tags og sprogmetadata.</li>'
                '</ul>',
                '<p>For en dybdegående guide til Drupal alene, se vores '
                '<a href="/da/blog/drupal-tilgaengelighed-eaa" '
                'style="color:var(--color-accent);">Drupal EAA-guide</a>. '
                'For TYPO3, se <a href="/da/blog/typo3-tilgaengelighed-bitv" '
                'style="color:var(--color-accent);">TYPO3 BITV-tjek</a>.</p>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan din side gratis'),
              ('/compliance-ai', 'Spørg Compliance AI')],
        related=[('/da/blog/drupal-tilgaengelighed-eaa', 'Drupal EAA-guide'),
                 ('/da/blog/typo3-tilgaengelighed-bitv', 'TYPO3 BITV-tjek')],
        da_link_text='Drupal vs TYPO3: tilgængelighed sammenlignet',
        faqs=[
            ('Hvilket CMS er mest tilgængeligt ud af boksen?',
             'Drupal med Olivero-temaet har en stærkere baseline — core\'en '
             'håndhæver semantisk markup og ARIA. TYPO3 kræver mere manuel '
             'opsætning af Fluid-templates for at opnå samme niveau. '
             'Men begge kan nå fuld AA-compliance — det afhænger af hvad '
             'du gør med dem.'),
            ('Er extensions/moduler et problem?',
             'Ja, det er den største kilde til defekter i praksis. '
             'Tredjeparts-moduler i begge CMS\'er har ujævn tilgængelighedskvalitet '
             '— test hvert modul individuelt før deployment.'),
            ('Hvad med opdateringer?',
             'Modul- og kernel-opdateringer kan genindføre tidligere fiksedee '
             'fejl. Tilgængelighedstest bør være en fast del af hver '
             'update-runde — ikke noget der gøres én gang om året.'),
            ('Bør jeg vælge Drupal eller TYPO3 for compliance?',
             'Begge er brugbare. Drupal kræver mindre manuel opsætning for '
             'at nå en AA-baseline; TYPO3 giver mere fleksibilitet i output '
             'men kræver strengere editor-disciplin. Vælg efter hvad dit team '
             'kender — et velbygget site i ethvert CMS er bedre end et '
             'dårligt bygget site i det "rigtige" CMS.'),
        ],
    ),
    # ------------------------------------------- EAA Compliance Scanner Desktop ---
    dict(
        en_slug='eaa-compliance-scanner-desktop',
        slug='eaa-compliance-scanner-desktop-download',
        badge='EAA &middot; SCANNER &middot; DESKTOP',
        title_tag='EAA Compliance Scanner Desktop — gratis offline WCAG-scanner',
        h1='EAA Compliance Scanner Desktop<br>gratis offline WCAG-scanner',
        desc=('Kør alle 22 WCAG 2.1 AA-regler lokalt på din maskine — '
              'ingen konto, ingen internethastighed, ingen grænser. '
              'macOS, Linux og Windows.'),
        subtitle='Den gratis desktop-scanner der kører lokalt: scan enkelt-URL\'er, '
                 'crawl hele sites, eksporter PDF-rapporter — helt offline, '
                 'uden API-grænser og uden abonnement.',
        read='4 minutters læsning',
        intro=('Tilgængeligheds-compliance behøver ikke betyde dyre SaaS-værktøjer '
               'eller langsomme cloud-baserede scannere. EAA Compliance Scanner '
               'Desktop er en gratis, native desktop-applikation der kører alle '
               '22 WCAG 2.1 AA-regler direkte på din maskine — ingen konti, '
               'intet internet, ingen grænser. Den er bygget til udviklere, QA-ingeniører '
               'og compliance-teams der skal tjekke sites før de går live, '
               'køre batch-audits eller integrere tilgængelighed i CI/CD-pipelines.'),
        cards=[
            ('📄 Enkelt-side scan',
             'Indsæt en URL, få resultater på sekunder med pass/fail pr. regel, '
             'issue-tællinger og en samlet score.'),
            ('🕸️ Crawl hele sites',
             'Scan op til 200 same-origin sider med live-progress og '
             'et per-side findings-brud.'),
            ('📑 PDF-rapporter',
             'Gem resultater som formaterede PDF-rapporter — klar til deling, '
             'arkivering eller compliance-dokumentation.'),
        ],
        sections=[
            ('Hvorfor en desktop-app?', [
                '<p>De fleste tilgængelighedsscannere er enten web-baserede '
                '(side-data sendes gennem deres servere) eller cloud-API\'er '
                'der kræver betaling pr. scanning. Desktop-appen er anderledes:</p>'
                '<ul>'
                '<li><strong>Fuldstændig offline</strong> — scanninger kører lokalt. '
                'Side-data forlader aldrig din maskine. Perfekt til interne sites, '
                'staging-miljøer og air-gapped netværk.</li>'
                '<li><strong>Ingen rate limits</strong> — scan så mange sider '
                'du vil, lige så hurtigt din maskine kan klare det.</li>'
                '<li><strong>Ingen konti</strong> — download og kør. '
                'Gratis-niveauet kræver ikke registrering.</li>'
                '<li><strong>Cross-platform</strong> — native builds til macOS '
                '(Apple Silicon + Intel), Linux (AppImage + .deb) og '
                'Windows (installer + portable).</li>'
                '</ul>',
            ]),
            ('Pro-funktioner (149 kr)', [
                '<p>Pro-niveauet låses op med én licensnøgle — betal én gang, '
                'aktiver på op til 3 maskiner:</p>'
                '<ul>'
                '<li><strong>Batch-scanning</strong> — scan en liste af URL\'er '
                'i sekvens med progress tracking og aggregerede statistikker.</li>'
                '<li><strong>CSV/JSON-eksport</strong> — eksporter individuelle '
                'eller batch-resultater til regneark eller programmatisk forbrug.</li>'
                '<li><strong>One-click PDF</strong> — gem scanninger som '
                'formaterede rapporter til compliance-dokumentation.</li>'
                '</ul>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan en side gratis i browseren'),
              ('/downloads', 'Download desktop-app')],
        related=[('/da/blog/tilgaengelighedsscanner-cli', 'CLI-scanner'),
                 ('/da/blog/compliance-tjek-github-action', 'Compliance Action')],
        da_link_text='EAA Compliance Scanner Desktop — download gratis',
        faqs=[
            ('Er desktop-scanneren virkelig gratis?',
             'Ja. Grundlæggende scanning (enkelt-URL, crawl op til 200 sider, '
             'PDF-rapport) er gratis og kræver ingen konto. Pro-niveauet '
             '(batch, CSV/JSON-eksport) koster 149 kr — én betaling.'),
            ('Kræver det internet?',
             'Nej — scanningerne kører lokalt. Du skal bruge internet til '
             'at hente siden du scanner (den er jo på nettet), men data '
             'forlader aldrig din maskine. Perfekt til interne/staging-sites.'),
            ('Hvilke operativsystemer?',
             'macOS (Apple Silicon + Intel), Linux (AppImage + .deb), '
             'Windows (installer + portable).'),
            ('Er den ligesom CLI-scanneren?',
             'Samme WCAG 2.1 AA-regelsæt (22 regler), men med en native GUI, '
             'crawl-funktion, PDF-rapporter og Pro-funktioner. CLI-scanneren '
             'er gratis og ubegrænset — desktop-appen tilføjer '
             'brugervenlighed og batch-workflows.'),
        ],
    ),
    # ------------------------------------------- Installer Clean Copy for Obsidian ---
    dict(
        en_slug='install-obsidian-plugin-clean-copy',
        slug='installer-clean-copy-obsidian',
        badge='OBSIDIAN &middot; PLUGIN &middot; CLEAN COPY',
        title_tag='Sådan installerer du Clean Copy til Obsidian (BRAT, manuelt & zip)',
        h1='Installer Clean Copy til Obsidian',
        desc=('Det gratis plugin der indsætter clipboard-HTML som korrekt Markdown '
              '— overskrifter, links, lister og tabeller. Tre måder at '
              'installere på, alle på under ét minut.'),
        subtitle='Det gratis plugin der indsætter clipboard-HTML som korrekt Markdown '
                 '— overskrifter, links, lister, tabeller og kode intakt. '
                 'Tre måder at installere på, alle på under ét minut.',
        read='5 minutters læsning',
        intro=('Clean Copy til Obsidian er det plugin du installerer én gang og '
               'glemmer — men mærker hver gang du kopierer fra nettet. '
               'I stedet for at indsætte forældet HTML der skal ryddes op i, '
               'får du ren Markdown med det samme: overskrifter som #, '
               'links som [tekst](url) og tabeller som pipe-tabeller. '
               'v1.0.9 tilføjer en CSV-tabel-tilføjelsestilstand ved siden af '
               'den eksisterende [[WikiLinks]]-tilstand.'),
        cards=[
            ('⚡ BRAT-metoden (hurtigst)',
             'Installer BRAT fra Obsidians community plugins, tilføj '
             'mahope/clean-copy-obsidian — auto-opdateringer fremover.'),
            ('📁 Manuel installation',
             'Download main.js, manifest.json og styles.css fra GitHub '
             'releases. Virker også på Obsidian mobile.'),
            ('📦 Zip-bundle',
             'Ét download med alle tre filer — pak ud i vaultets '
             'plugin-mappe og aktiver.'),
        ],
        sections=[
            ('Tre installationsmetoder', [
                '<p><strong>1) BRAT (hurtigst, auto-opdateringer)</strong></p>'
                '<ol>'
                '<li>Installer BRAT fra Obsidians community plugin-browser '
                '(Settings → Community plugins → Browse → søg "BRAT").</li>'
                '<li>Åbn kommandopaletten (Cmd/Ctrl+P) og kør '
                '"BRAT: Add a beta plugin for testing".</li>'
                '<li>Indtast <code>mahope/clean-copy-obsidian</code> og bekræft.</li>'
                '<li>Aktiver Clean Copy i Settings → Community plugins.</li>'
                '</ol>'
                '<p>BRAT overvåger repository\'ets releases — hver fremtidig '
                'version ankommer automatisk.</p>',
                '<p><strong>2) Manuel installation</strong></p>'
                '<ol>'
                '<li>Åbn den seneste release-side på GitHub.</li>'
                '<li>Download <code>main.js</code>, <code>manifest.json</code> '
                'og <code>styles.css</code>.</li>'
                '<li>Opret mappen <code>&lt;dit-vault&gt;/.obsidian/plugins/'
                'clean-copy-obsidian/</code> og læg alle tre filer derind.</li>'
                '<li>Genstart Obsidian og aktiver Clean Copy.</li>'
                '</ol>'
                '<p>Virker også på Obsidian mobile — brug en filhåndtering '
                'til at nå vault-mappen.</p>',
                '<p><strong>3) Zip-bundle (ét klik)</strong></p>'
                '<p><a href="/downloads/clean-copy-obsidian-v1.0.9.zip" '
                'style="color:var(--color-accent);">Download v1.0.9 zip</a>, '
                'pak ud i <code>&lt;vault&gt;/.obsidian/plugins/</code> og aktiver.</p>',
            ]),
            ('Første kørsel', [
                '<p>Kopiér formateret tekst fra nettet, tryk Ctrl/Cmd+Shift+V '
                '(eller kør "Paste as clean Markdown" fra kommandopaletten). '
                'Overskrifter ankommer som #, links som [tekst](url), '
                'tabeller som pipe-tabeller, entities afkodet.</p>',
                '<p>To ekstra kommandoer bor i paletten: "Paste as plain text" '
                'og "Clean selection" til at rense tekst der allerede er i en note.</p>',
                '<p>I Settings → Clean Copy vælger du din standard-tilstand: '
                'Markdown med [[WikiLinks]] (interne links) eller CSV-tabeltilstand. '
                'Se hvordan det virker i browseren: '
                '<a href="/clean-copy-tool" style="color:var(--color-accent);">'
                'prøv Clean Copy online</a>.</p>',
            ]),
        ],
        ctas=[('/clean-copy', 'Se Clean Copy'),
              ('/clean-copy-tool', 'Prøv i browseren')],
        related=[('/da/blog/indsæt-i-obsidian-ren-markdown', 'Indsæt ren Markdown i Obsidian'),
                 ('/da/blog/kopier-som-markdown-udvidelse', 'Kopiér som Markdown')],
        da_link_text='Installer Clean Copy til Obsidian',
        faqs=[
            ('Er det sikkert at installere plugins fra GitHub?',
             'Ja. Clean Copy er open source (MIT) — koden er synlig på GitHub. '
             'BRAT-installationen verificerer at filerne kommer fra den '
             'officielle release. Pluginnet har ingen netværksadgang og '
             'arbejder kun med din clipboard.'),
            ('Virker det på Obsidian mobile?',
             'Ja. Manuel installation virker fint — brug en filhåndtering '
             'til at placere de tre filer i vaultets plugin-mappe.'),
            ('Får jeg automatiske opdateringer?',
             'Kun med BRAT-metoden. Manuel/zip-installation kræver at du '
             'gentager processen når en ny version udkommer.'),
            ('Hvad er forskellen på v1.0.8 og v1.0.9?',
             'v1.0.9 tilføjer en CSV-tabeltilstand ved siden af '
             'WikiLinks-tilstanden — vælg din default i Settings.'),
        ],
    ),
]


def main():
    m.PAGES[:] = PAGES
    m.main()


if __name__ == '__main__':
    main()