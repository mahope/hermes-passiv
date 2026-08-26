#!/usr/bin/env python3
"""Iteration 455: Danish mirrors of the Webflow / PrestaShop / Drupal guides.

Genbruger al mekanik fra tools/make_blog_da_mirrors_453.py (build(), hreflang,
sitemap, blog-indeks, krydslinks, validering) — kun PAGES-listen er ny.
Idempotent: anden kørsel laver ingen ændringer.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    'mirrors_453', os.path.join(HERE, 'make_blog_da_mirrors_453.py'))
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

PAGES = [
    # ------------------------------------------------------------ Webflow ---
    dict(
        en_slug='webflow-accessibility-audit',
        slug='webflow-tilgaengelighed-eaa',
        badge='WEBFLOW &middot; TILGÆNGELIGHED &middot; EAA',
        title_tag='Webflow og tilgængelighed: praktisk EAA-audit-guide (2026)',
        h1='Webflow og tilgængelighed:<br>den praktiske audit-guide',
        desc=('Sådan laver du en tilgængelighedsaudit af et Webflow-site og når '
              'i mål med EAA og WCAG 2.1 AA: Designer-indstillinger, typiske '
              'Webflow-fejl, interactions og en gratis scannings-workflow.'),
        subtitle=('Hvor Webflow-sider faktisk fejler WCAG-tjek — og hvordan bureauer '
                  'retter det inde i Designeren, før EAA bliver kundens problem.'),
        read='6 minutters læsning',
        intro=('Webflow er foretrukne værktøj til EU-marketingssider, SaaS-landingpages '
               'og bureaukunder — præcis den e-handels- og forbrugertjeneste-zone, '
               'European Accessibility Act dækker siden juni 2025. Bureauer der leverer '
               'Webflow-projekter, leverer altså også tilgængelighedstilstanden selv: '
               'der er mindre plugin-støj end i WordPress, men også intet plugin der '
               'redder dig. Den gode nyhed er, at Webflow giver usædvanlig direkte kontrol '
               'med semantikken — de fleste fejl skyldes designbeslutninger, ikke '
               'platformens grænser.'),
        cards=[
            ('🎯 Du ejer semantikken', 'Webflow lader dig sætte hvilket som helst '
             'element-tag (div → nav, section, h2...). De fleste '
             'tilgængelighedsfejl er simpelthen divs der udfører semantiske jobs.'),
            ('⚡ Hurtig udbedring', 'Fordi alt er visuelt og centraliseret, tager det '
             'minutter at rette 20 kontrastfejl i style-panelet — når først de er fundet.'),
            ('📜 Salgbart deliverable', 'En audit-rapport plus tilgængelighedserklæring '
             'er nu en fakturerbar linje — kunder i EAA-omfang skal have begge dele.'),
        ],
        sections=[
            ('Typiske Webflow-fejl', [
                '<div class="problem-cards">'
                '<div class="card"><h3>🧱 Div-suppe i stedet for overskrifter</h3><p>Tekst stylet '
                'til at ligne overskrifter men efterladt som rene divs. Skærmlæsere ser ingen '
                'dokumentstruktur. Fix: markér elementet → Indstillinger → skift tag til h1/h2/h3.</p></div>'
                '<div class="card"><h3>🎨 Kontrast på gradienter</h3><p>Hero-tekst oven på gradienter '
                'eller billeder fejler 4,5:1 et sted langs overgangen. Test det værste hjørne og læg '
                'et mørkt overlay (scrim) bag teksten.</p></div>'
                '<div class="card"><h3>⌨️ Interaction-fælder</h3><p>Hover-drevne dropdowns, tabs og '
                'slidere bygget med Interactions ignorerer ofte tastaturet helt — ingen fokus, ingen '
                'escape, intet touch-alternativ.</p></div>'
                '<div class="card"><h3>🖼️ Baggrundsbilleder som indhold</h3><p>Billeder uploadet som '
                'background-image har ingen alt-attribut. Indholdsbærende billeder skal være rigtige '
                'Image-elementer med alt-tekst.</p></div>'
                '<div class="card"><h3>🔗 Link Blocks</h3><p>En "Link Block" der omslutter hele kort '
                'giver gentagne nøgne links; indre tekst-spans læses ikke pålideligt som '
                'linkkontekst.</p></div>'
                '</div>',
            ]),
            ('Designer-retninger der dækker det meste', [
                '<p><strong>Tag-disciplin:</strong> gå sektion for sektion og sæt rigtige tags: nav omkring '
                'navigationen, header/footer-elementer, én h1 pr. side og logisk h2/h3-nesting under den.</p>',
                '<p><strong>Alt-tekst:</strong> hvert Image-element får beskrivende alt i sine indstillinger; '
                'dekorative får tomt alt. Erstat background-image-divs med informative billeder som rigtige '
                'billedelementer.</p>',
                '<p><strong>Fokus-synlighed:</strong> sæt aldrig outline: none uden en erstatning. Style '
                'Focus-tilstanden i selector-panelet — 2px solid currentColor med offset virker næsten altid.</p>',
                '<p><strong>Formularer:</strong> hvert input får et rigtigt label-element (ikke kun '
                'placeholder). Opsæt success-/fejlbeskeder som live regions så skærmlæsere annoncerer dem.</p>',
                '<p><strong>Farvetokens:</strong> ret kontrasten ét sted i dine globale variabler/swatches — '
                'mørkere brødtekst, mørkere gråtoner på badges — og tjek med et kontrastværktøj.</p>',
                '<p><strong>Sprog og metadata:</strong> sæt html lang i Project Settings og unikke titler/'
                'meta pr. side.</p>',
            ]),
            ('Interactions og tastatur', [
                '<p>Interactions er Webflows største strukturelle risiko, fordi funktionen opfordrer til '
                'mus-først-tænkning. Audit-reglerne: hver hover-interaktion skal have en fokus-ækvivalent '
                '(dropdowns åbner ved focus-in og lukker ved focus-out); tabs og slidere skal kunne betjenes '
                'med piletaster og eksponere aria-selected/roller; alt der udløses ved klik skal være en '
                'rigtig knap eller et link — ikke en div med click-trigger; modal-interaktioner skal flytte '
                'fokus ind ved åbning og tilbage ved lukning; og autospillede hero-animationer skal respektere '
                'prefers-reduced-motion. Er det for dyrt at genbygge en interaktion tilgængeligt, så giv en '
                'statisk fallback til samme indhold — WCAG kræver ikke identisk oplevelse, kun ækvivalent '
                'adgang.</p>',
            ]),
            ('Audit-workflow i fem skridt', [
                '<p><strong>Trin 1 — automatisk scanning</strong> af forsiden, en nøgleside, en formularside '
                'og evt. collection-/skabelonsider. Det fanger kontrast, alt, overskriftsorden, labels og '
                'duplikerede IDs på minutter — forvent 10-30 fund på et typisk build.</p>',
                '<p><strong>Trin 2 — ret i Designeren,</strong> publicér staging og genscan til de automatiske '
                'fund er væk.</p>',
                '<p><strong>Trin 3 — keyboard-gennemgang:</strong> tag musen fra bordet og gå hver interaktive '
                'sti igennem — menuer, accordions, tabs, modals og formularer.</p>',
                '<p><strong>Trin 4 — skærmlæser-spotcheck</strong> af én kernerejse med NVDA eller VoiceOver.</p>',
                '<p><strong>Trin 5 — levér:</strong> fundrapport (før/efter) plus tilgængelighedserklæring med '
                'conformance-status og kendte begrænsninger. Genscan efter hver større site-ændring.</p>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan dit Webflow-site gratis'),
              ('/da/blog/eaa-tjekliste-2026', 'EAA-tjekliste')],
        related=[('/da/blog/wix-tilgaengelighed-eaa', 'Wix og EAA'),
                 ('/da/blog/squarespace-tilgaengelighed-eaa', 'Squarespace og EAA'),
                 ('/da/blog/pris-tilgaengelighedsgennemgang', 'Pris på tilgængelighedsgennemgang')],
        da_link_text='Webflow og tilgængelighed: den praktiske audit-guide',
        faqs=[
            ('Er Webflow mere tilgængeligt end WordPress ud af boksen?',
             'Ingen af dem vinder automatisk. Webflow giver mere ren kontrol med markeringen, men '
             'outputtet er kun så tilgængeligt som designeren gør det. WordPress-temaer varierer '
             'vildere. I begge tilfælde afgør byggeren.'),
            ('Gælder EAA B2B-sider lavet i Webflow?',
             'EAA rammer forbrugervendte tjenester, så rene B2B-sider falder mest udenfor — men '
             'WCAG-baserede krav gælder stadig via EN 301 549-udbudskaeder, og offentlige kunder '
             'kræver conformance alligevel.'),
            ('Må jeg bruge et tilgængeligheds-overlay på Webflow?',
             'Overlays kan ikke skabe manglende semantik, reparere ubrugelige interactions eller rette '
             'indholdsproblemer, og markedsføring af dem som compliance har mødt regulatorisk kritik '
             'i EU. Ret årsagerne i Designeren i stedet.'),
            ('Hvordan tjekker jeg kontrast over gradienter og billeder?',
             'Prøvtag det lyseste og mørkeste punkt bag teksten og tjek begge mod tekstfarven i et '
             'kontrastværktøj. Læg et scrim-overlay på, hvis ét punkt fejler.'),
            ('Kan bureauer sælge Webflow-tilgængelighedsaudits?',
             'Ja — en automatiske scanning kombineret med manuel tastatur-/skærmlæsertestning og en '
             'leveret rapport er en standard, fakturerbar ydelse, og EAA-fristerne har gjort efterspørgslen '
             'voksende.'),
        ],
    ),

    # --------------------------------------------------------- PrestaShop ---
    dict(
        en_slug='prestashop-eaa-accessibility',
        slug='prestashop-tilgaengelighed-eaa',
        badge='PRESTASHOP &middot; TILGÆNGELIGHED &middot; EAA',
        title_tag='PrestaShop og tilgængelighed: bliv EAA-compliant (guide 2026)',
        h1='PrestaShop og tilgængelighed:<br>bliv EAA-compliant',
        desc=('Tilgængelighedsguide til PrestaShop-butikker: tema-retter, produkt-alt-tekst, '
              'module-audit, facetteret navigation og checkout — WCAG 2.1 AA og European '
              'Accessibility Act på dansk.'),
        subtitle=('Hvor PrestaShop-butikker fejler WCAG 2.1 AA — temaer, moduler, filtre og '
                  'checkout — og en praktisk udbedrings-workflow for EU-mercants.'),
        read='7 minutters læsning',
        intro=('PrestaShop driver hundredtusindvis af webshops med stor fodaftryk blandt europæiske '
               'små og mellemstore mercants — præcis e-handelskategorien European Accessibility Act '
               'regulerer. Siden juni 2025 er en utilgængelig butik juridisk risiko i hele EU, og '
               'betalingsudbydere og markedspladser spørger i stigende grad mercants til dokumenteret '
               'conformance. En typisk PrestaShop-butik stabler et købt tema, et dusin moduler og flere '
               'sprog oven på kernen — og hvert led kan bryde tilgængeligheden.'),
        cards=[
            ('🛒 E-handel er i omfang', 'Webshops har ingen mikrovirksomheds-befrielse under EAA. '
             'Sælger du til EU-forbrugere, gælder WCAG 2.1 AA dine produktsider, checkout og '
             'kontoområde.'),
            ('🎨 Marketplace-temaer varierer', 'Temaet styrer næsten al renderet HTML — '
             'overskriftshierarki, knap-markering, fokus-tilstande og kontrast. Kvaliteten svinger '
             'vildt mellem marketplace-temaer.'),
            ('🧩 Modul-risiko', 'Filter-widgets, sliders, reviews og newsletter-popups kommer typisk fra '
             'tredjeparts-moduludviklere med ukendt tilgængelighedskvalitet. Hvert modul skal gennemgås '
             'for sig.'),
        ],
        sections=[
            ('Typiske PrestaShop-fejl', [
                '<div class="problem-cards">'
                '<div class="card"><h3>🖼️ Produktbilleder uden Legend</h3><p>Bulk-import springer rutinemæssigt '
                'Legend-feltet over og efterlader kategorigitter fulde af billeder helt uden alt-tekst.</p></div>'
                '<div class="card"><h3>🧭 Facetterede filtre</h3><p>Filtrer renderet som klikbare divs uden '
                'tastaturstøtte eller aria-expanded — skærmlæserebrugere kan ikke indsnævre et produktgitter.</p></div>'
                '<div class="card"><h3>🔢 Antal- og variant-input</h3><p>Egne steppers i stedet for native '
                'number-inputs, farveprøver uden labels eller annoncering af valgt tilstand.</p></div>'
                '<div class="card"><h3>💳 Checkout-trin</h3><p>Ajax-udskiftede checkout-sektioner der hverken '
                'flytter fokus eller annoncerer fejl; betalingsfelter uden tilknyttede labels.</p></div>'
                '<div class="card"><h3>🔔 Popups &amp; toasts</h3><p>Newsletter-modals der fanger tastaturfokus, '
                '"lagt i kurven"-bekræftelser vist kun visuelt — ingen ARIA live region.</p></div>'
                '<div class="card"><h3>🎨 Kampagnekontrast</h3><p>Udsalgsbadges og banner-tekst i brandfarver '
                'under 4,5:1-minimummet — den hyppigste automatiske fundkategori på EU-butikker.</p></div>'
                '</div>',
            ]),
            ('Backoffice- og tema-retter', [
                '<p><strong>Backoffice først:</strong> produktbillede-alt bor i Katalog → Produkter → Fotos '
                '(Legend-feltet); butiks-sprog under International → Lokalisering; farver og typografi under '
                'Design → Theme &amp; Logo. Fyld det ordentligt ud, før du rører kode.</p>',
                '<p><strong>Tema-semantik:</strong> genskab rigtige landmarks (header, nav, main, footer), '
                'én h1 pr. side og produkttitler som rigtige overskrifter i gitterskabelonerne — mange '
                'marketplace-temaer renderer dem som stylede divs.</p>',
                '<p><strong>Native inputs:</strong> erstat egne antal-steppers og selects med native elementer '
                'stylet til at matche — de arver tastatur- og skærmlæseradfærd gratis.</p>',
                '<p><strong>Fokus &amp; ARIA-tilstande:</strong> style :focus-visible i stedet for at fjerne '
                'outlines; giv filter-toggles aria-expanded og resultatantal en aria-live region; hver '
                'Ajax-sektionsskift flytter fokus til sit nye indhold.</p>',
                '<p><strong>Kontrasttokens:</strong> ret grå-på-grå pris- og udsalgstekst ét sted i temaets '
                'farvevariabler, og verificér bagefter på tværs af bannere og knapper.</p>',
            ]),
            ('Module-audit', [
                '<p>Behandl hvert tredjepartsmodul som en tilgængeligheds-ubekendt indtil det modsatte er '
                'bevist. På staging: gå hvert mods komplette flow igennem kun med tastatur, derefter med en '
                'skærmlæser — installér, konfigurér, brug, fortryd. Facetteret søgning, carousels, '
                'cookie-bannere og newsletter-popups fortjener særlig opmærksomhed — det er kategorierne med '
                'de værste track records. Fejler et modul uden fix fra leverandøren, så beslut bevidst: '
                'erstat det, pak et korrigerende lag udenom, eller dokumentér det som begrænsning i din '
                'tilgængelighedserklæring med en workaround. Kør din scanning igen efter hver '
                'modul-installation og hver PrestaShop-opgradering — opdateringer genskaber lydløst gamle '
                'fejl, hvor leverandørfiler blev patchet direkte.</p>',
            ]),
            ('Audit-workflow i fem skridt', [
                '<p><strong>Trin 1 — automatisk crawl</strong> af forside, kategori-, produkt-, CMS- og '
                'checkout-skabeloner — forvent 20-50 distincte fund på en typisk butik.</p>',
                '<p><strong>Trin 2 — transaktionsrejser:</strong> gennemfør søg → filtrér → produkt → kurv → '
                'checkout ende-til-ende med tastatur, derefter med skærmlæser. Dér ligger EAA-risikoen.</p>',
                '<p><strong>Trin 3 — module-pass:</strong> auditér hvert installeret moduls widgets enkeltvis.</p>',
                '<p><strong>Trin 4 — ret</strong> i backoffice hvor muligt, ellers i et child theme — patch '
                'aldrig core- eller vendor-filer direkte.</p>',
                '<p><strong>Trin 5 — levér:</strong> fundrapport, re-scan-verifikation og en '
                'tilgængelighedserklæring med conformance-status og dokumenterede begrænsninger. Re-auditér '
                'efter hver opgradering og større modulændring.</p>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan din PrestaShop-butik gratis'),
              ('/da/blog/eaa-tjekliste-2026', 'EAA-tjekliste')],
        related=[('/da/blog/magento-tilgaengelighed-eaa', 'Magento og EAA'),
                 ('/da/blog/shopify-tilgaengelighed-eaa', 'Shopify og EAA'),
                 ('/da/blog/wcag-kontrast-checker', 'WCAG-kontrasttjek')],
        da_link_text='PrestaShop og tilgængelighed: bliv EAA-compliant',
        faqs=[
            ('Gælder EAA min lille PrestaShop-butik?',
             'Ja for e-handel: webshops har ingen mikrovirksomhedsbefrielse under EAA. En lille '
             'PrestaShop-butik der sælger til EU-forbrugere er i omfang uanset antal ansatte.'),
            ('Er PrestaShop tilgængeligt ud af boksen?',
             'Standard Classic-temaet leverer fornuftig semantik og responsiv markering, men de fleste '
             'butikker tilpasser temaer, tilføjer moduler og oversætter indhold — hvert trin kan '
             'introducere regressioner som manglende labels, generiske linktekster eller '
             'lavkontrast-bannere.'),
            ('Hvor retter jeg alt-tekst på produktbilleder?',
             'Katalog → Produkter → åbn produktet → Fotos-fanen → Legend-feltet. Bulk-importerede '
             'kataloger står ofte tomme på hundredvis af produkter; scanneren finder dem alle i ét '
             'træk.'),
            ('Er købte temaer tilgængelige?',
             'Nogle er bedre end andre, men marketingpåstande er upålidelige. Scan en hel side af dit '
             'live tema frem for at stole på demoen — overskriftsstruktur, fokus-tilstande og kontrast '
             'er hvor temaer oftest fejler.'),
            ('Hvor lang tid tager udbedring?',
             'En typisk mellemstor butik skal bruge 1-4 uger afhængigt af tematilpasningens dybde og '
             'modulantal. Backoffice-rettere (alt-tekst, sprog, indstillinger) kan klares på dage; '
             'temaskabelon-arbejde tager længere.'),
        ],
    ),

    # ------------------------------------------------------------ Drupal ---
    dict(
        en_slug='drupal-wcag-accessibility',
        slug='drupal-tilgaengelighed-eaa',
        badge='DRUPAL &middot; TILGÆNGELIGHED &middot; WCAG/EAA',
        title_tag='Drupal og tilgængelighed: WCAG 2.1 AA og EAA (guide 2026)',
        h1='Drupal og tilgængelighed:<br>WCAG 2.1 AA og EAA',
        desc=('Drupal-tilgængelighedsguide til EAA og WCAG 2.1 AA: Olivero-temaet, '
              'contributed-module-risici, Views- og formularretter, admin vs. front-end-'
              'ansvar og en verificerings-workflow — på dansk.'),
        subtitle=('Praktisk guide til bureauer der bygger Drupal-sider til EU-kunder — hvad core '
                  'allerede klarer, hvor contributed modules bryder compliance, og hvordan du '
                  'verificerer før EAA bider.'),
        read='6 minutters læsning',
        intro=('Drupal har et af de stærkeste tilgængelighedsfundamenter blandt CMS\'er. Siden Drupal 8 '
               'har core haft WCAG 2.1 og ATAG 2.0 som policy-mål: front-end-temaet Olivero skiber '
               'tilgængeligt som standard, formularelementer renderer labels programmatisk knyttet til '
               'inputs, og core-JavaScript bruger behaviours-systemet til at holde ARIA-tilstand konsistent '
               'efter AJAX-opdateringer. Admin-temaet Claro er bygget til samme standard. Kører dit site '
               'core-plus-Olivero uden tung tilpasning, starter du fra et solidt grundlag — arbejdet ligger '
               'i indhold, contributed modules og eventuelle custom-temaer.'),
        cards=[
            ('🏗️ Core-baseline', 'Semantisk markering, labellede formularer, fokusstyring og ARIA live '
             'regions håndteres på theme-system-niveau — ikke overlades til hver enkel sitebuilder.'),
            ('🎨 Olivero &amp; Claro', 'Både front-end- og admin-temaet målrettet WCAG 2.1 AA — inklusive '
             'mobil-navigation med rigtige disclosure-semantics og synlige fokus-tilstande.'),
            ('⚙️ ATAG 2.0', 'Drupal sigter højere end indholdsoutput: selve redigeringsoplevelsen er '
             'tilgængelig — det tæller ved offentlige udbud under EN 301 549.'),
        ],
        sections=[
            ('Hvor Drupal-sider fejler', [
                '<p>Reelle Drupal-tilgængelighedsfejl samler sig fire steder — næsten aldrig i core:</p>',
                '<div class="problem-cards">'
                '<div class="card"><h3>🧩 Contributed modules</h3><p>Moduler der renderer egen markering '
                '(sliders, kalendere, menuer, betalingswidgets) bypasser theme-systemet. Kvaliteten svinger '
                'enormt; nogle skiber ti år gamle jQuery-mønstre med unlabellede kontroller.</p></div>'
                '<div class="card"><h3>🖼️ Redaktørvaner</h3><p>Manglende alt-tekst på billeder uploadet via '
                'media library, overskrifter valgt efter visuel størrelse, links der bare siger "læs mere". '
                'Værktøjslinjen er tilgængelig; vanerne er ofte ikke.</p></div>'
                '<div class="card"><h3>🎛️ Views &amp; custom blocks</h3><p>Views-genererede lister kan give '
                'tomme overskrifter eller gentaget identisk linktekst på tværs af rækker. Custom block-typer '
                'springer ofte overskriftsniveauer over.</p></div>'
                '<div class="card"><h3>💻 Custom themes</h3><p>Håndbyggede eller kraftigt tilpassede temaer '
                'genintroducerer alle de klassiske fejl: placeholder-only inputs, divs som knapper, kontrast '
                'sat fra brandpaletten uden at tjekke forholdstal.</p></div>'
                '</div>',
            ]),
            ('Contrib module-audit', [
                '<p><strong>Inventar:</strong> list de moduler der outputter markering på offentlige sider '
                '(sliders, maps, videoplayere, booking-widgets, newsletter-formularer). Alt der kun bruges i '
                'admin kan vente.</p>',
                '<p><strong>Scan hver widget:</strong> tab dig igennem den på en rigtig side. Unlabellede '
                'ikonknapper, keyboard-fælder og manglende fokusindikatorer er disqualifying — find et '
                'alternativt modul eller patch sagen i upstream issue queue.</p>',
                '<p><strong>Tjek opdateringer:</strong> mange tilgængelighedspatches ligger allerede i nyere '
                'udgaver. At køre aktuelle stabile contrib-versioner er i sig selv en '
                'tilgængelighedsforanstaltning.</p>',
                '<p><strong>WYSIWYG-indstillinger:</strong> begræns CKEditor 5-knapperne så redaktører ikke kan '
                'indsætte inline-farver eller fonte der bryder kontrast og struktur. Færre værktøjer, mere '
                'compliant indhold.</p>',
            ]),
            ('Views, formularer og indhold', [
                '<p><strong>Views:</strong> giv hver display en rigtig, unik titel i stedet for auto-genererede '
                'tomme overskrifter; brug distinkt linktekst pr. række ("Læs casen" — ikke "Læs mere"); og '
                'tjek at pager-markeringen annoncerer aktuel side.</p>',
                '<p><strong>Formularer:</strong> webform og kontaktformularer labeler felter korrekt ud af boksen '
                '— fejlene kommer fra custom alterations. Verificér at required-indikation ikke kun er farve, '
                'og at fejlbeskeder er tekst, ikke bare røde kanter.</p>',
                '<p><strong>Indhold:</strong> håndhæv alt-tekst via media library (det er krævet som default — '
                'svæk det ikke), træn redaktører i overskriftsorden, og føj en "linktekst"-retningslinje til '
                'den redaktionelle tjekliste.</p>',
                '<p><strong>Flersproget:</strong> lang-attributter på oversatte sider skal skifte med '
                'grænsefladeoversættelsen — Drupal klarer det i core, men custom routes og indlejret indhold '
                'glemmer det ofte.</p>',
            ]),
            ('Verificerings-workflow', [
                '<p><strong>Trin 1 — automatisk scanning</strong> af forside, en liste-side, en node-side, en '
                'formularside og søgeresultater. Forvent 5-15 mekaniske fund på første kørsel, mest indhold '
                'og contrib.</p>',
                '<p><strong>Trin 2 — ret og genscan</strong> til de automatiske fund er væk: tema-CSS, '
                'Views-titler, alt-tekst-backfill.</p>',
                '<p><strong>Trin 3 — keyboard-gennemgang</strong> af søg → liste → node → formularafsending. Alt '
                'kun-mus fejler WCAG 2.1.2.</p>',
                '<p><strong>Trin 4 — skærmlæser-spotcheck</strong> af én hel rejse med NVDA eller VoiceOver — '
                'lyt efter unlabellede kontroller og lydløse AJAX-opdateringer.</p>',
                '<p><strong>Trin 5 — kør igen efter hver modulopdatering og ny block-type.</strong> Regressioner '
                'ankommer lydløst med contrib-opdateringer.</p>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan dit Drupal-site gratis'),
              ('/da/blog/eaa-tjekliste-2026', 'EAA-tjekliste')],
        related=[('/da/blog/tilgaengeligheds-overlays-eaa', 'Overlays og EAA'),
                 ('/da/blog/skriv-tilgaengelighedserklaering', 'Skriv en tilgængelighedserklæring'),
                 ('/da/blog/gratis-tilgaengelighedsvaerktoejer', 'Gratis tilgængelighedsværktøjer')],
        da_link_text='Drupal og tilgængelighed: WCAG 2.1 AA og EAA',
        faqs=[
            ('Er Drupal mere tilgængeligt end WordPress?',
             'Ud af boksen, ja — Drupal core målretter eksplicit WCAG 2.1 og ATAG 2.0, mens WordPress-'
             'kvalitet afhænger langt mere af valgt tema og plugins. Men et dårligt tilpasset Drupal-tema '
             'taber fordelen hurtigt; platformsbaseline hjælper, garanterer ingenting.'),
            ('Gælder EAA Drupal-sider?',
             'Ja, for de tjenester der leveres gennem dem, når de er forbrugervendte i EU — inklusive '
             'e-handel og medlems sites. Offentlige Drupal-byggerier har længe været bundet af EN 301 549-'
             'udbudregler uanset.'),
            ('Hvilke contributed modules skaber flest problemer?',
             'Tredjeparts-UI-widgets: sliders/carousels, maps, kalender-/booking-widgets og legacy-menu-'
             'moduler. De skiber egen markering uden for theme-systemet, så core-garantier stopper ved '
             'deres kant.'),
            ('Skal jeg bruge Bartik eller Olivero specifikt?',
             'Intet tema er obligatorisk, men at starte fra et vedligeholdt core-tema sparer uger. Skal du '
             'tilpasse, så subclass og override templates i stedet for at forke — så beholder du upstreams '
             'tilgængelighedsfixes ved opdatering.'),
            ('Hvor lang tid tager et Drupal-tilgængeligheds-pass?',
             'Et core-plus-contrib-build på Olivero: 1-3 dage inklusive test. Kraftigt tilpassede legacy-'
             'temaer (Bootstrap-forks er hyppige syndere) kræver et større udbedringsprojekt.'),
        ],
    ),
]


def main():
    m.PAGES = PAGES
    m.main()


if __name__ == '__main__':
    main()
