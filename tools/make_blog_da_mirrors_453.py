#!/usr/bin/env python3
"""Iteration 453: Danish mirrors of the Wix / Squarespace / Magento EAA guides.

Samme skabelon og samme sikkerhedstjek som tools/make_blog_shopify_da.py:
Article + FAQPage JSON-LD, valideret før og efter skrivning, hreflang-sæt på
BEGGE sider, hreflang_pairs.json opdateret, idempotent sitemap-tilføjelse,
blog-indeks (DA-liste) entry, reciprok krydslink fra EN-posten.
Idempotent: anden kørsel laver ingen ændringer.
"""
import json, os, re, xml.dom.minidom

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-26'
ROOT = '/Users/madsholstjensen/hermes-passiv'
SITE = os.path.join(ROOT, 'site')

# ---------------------------------------------------------------- indhold ---
PAGES = [
    dict(
        en_slug='wix-eaa-accessibility',
        slug='wix-tilgaengelighed-eaa',
        badge='WIX &middot; TILGÆNGELIGHED &middot; EAA',
        title_tag='Wix og tilgængelighed: bliv EAA-compliant (guide 2026)',
        h1='Wix og tilgængelighed:<br>bliv EAA-compliant',
        desc=('Gør din Wix-side compliant med European Accessibility Act og '
              'WCAG 2.1 AA: editor-retter, app-risici, mobil-layout-fælder og '
              'en gratis scannings-workflow — trin for trin på dansk.'),
        subtitle=('Praktisk compliance-guide for Wix-ejere og bureauer: hvad du '
                  'kan rette i editoren, hvad platformen bestemmer for dig, og '
                  'hvordan du får en Wix-side op på WCAG 2.1 AA.'),
        read='6 minutters læsning',
        intro=('Wix driver millioner af små virksomhedssider i EU — restauranter, '
               'klinikker, lokale butikker og selvstændige. Siden juni 2025 er mange '
               'af de virksomheder omfattet af European Accessibility Act som '
               'leverandører af forbrugertjenester og e-handel, og spørgsmålet fra '
               'kunden lyder: kan denne side bestå et WCAG 2.1 AA-tjek? Wix har '
               'investeret kraftigt i tilgængelighedsværktøjer de seneste år, men '
               'resultatet er kun så compliant som den person der bygger siden.'),
        cards=[
            ('🧩 Platform vs. bygger', 'Wix-skabeloner lever med fornuftig semantik, '
             'men hver trukket sektion, strip og tekstboks kan bryde dem. De fleste '
             'audits fejler på byggerens valg, ikke platformens grænser.'),
            ('⚙️ Rigtige indstillinger findes', 'Wix eksponerer alt-tekst på billeder, '
             'overskrift-tags pr. tekstelement, fokus-tilstande på knapper og en '
             'tilgængelighedscheckliste i editoren — brug det hele.'),
            ('📜 Salgbart deliverable', 'En fundrapport plus tilgængelighedserklæring '
             'er en fakturerbar linje for de små virksomheder, der skal comply.'),
        ],
        sections=[
            ('Hvor Wix-sider typisk fejler', [
                '<p>Fejlbilledet på Wix-audits er bemærkelsesværdigt ensformigt:</p>',
                '<p><strong>Tekst over foto-strips:</strong> hvid tekst oven på billeder '
                'fejler kontrasten et sted på næsten alle enheder. Læg et farveoverlay '
                'bag teksten eller flyt den ned på en solid baggrundsblok.</p>',
                '<p><strong>Dekorative "overskrifter":</strong> tekstbokse gjort større '
                'og federe for at ligne overskrifter, men stadig med paragraph-tags. Sæt '
                'den rigtige overskriftstype i hvert tekstelements indstillinger.</p>',
                '<p><strong>Manglende alt-tekst:</strong> gallerielementer, logoer uploadet '
                'som almindelige billeder, dekorative strips brugt som bannere. Hvert '
                'indholdsbillede skal have alt; rent dekorative skal have eksplicit tom alt.</p>',
                '<p><strong>Kun-hover-menuer:</strong> fler-niveau-menuer der kun åbner ved '
                'hover strander tastaturbrugere. Slå klik-for-at-åbne til i menuindstillingerne.</p>',
                '<p><strong>Knap-lignende tekst:</strong> tekst stylet som en knap men ikke '
                'bygget som én — ingen fokusring, ingen knaprolle. Brug rigtige '
                'knap-elementer til alle handlinger.</p>',
                '<p><strong>Anker-kaos:</strong> lange one-page-sider bygget udelukkende af '
                'ankre giver linktekster som "klik her" ti gange i træk. Giv ankre '
                'beskrivende navne.</p>',
            ]),
            ('Editor-retter — uden kode', [
                '<p>Gå disse igennem inde i Wix-editoren — de rydder de fleste automatiske fund:</p>',
                '<p><strong>Overskriftsstruktur:</strong> vælg hvert tekstelement → Indstillinger '
                '→ sæt rigtige h1/h2/h3-tags. Én h1 pr. side; nest resten logisk.</p>',
                '<p><strong>Alt-tekst:</strong> hvert billede får sit alt-felt udfyldt — '
                'beskrivende for indholdsbilleder, tomt for dekoration. Gallerier skal '
                'gennemgås element for element; kedeligt og ikke-forhandleligt.</p>',
                '<p><strong>Kontrast:</strong> mørk gør kropstekstens gråtoner globalt under '
                'Sitedesign → Farver. Tjek hero-overlays og footer-links separat — dér fejer '
                'det oftest.</p>',
                '<p><strong>Fokus-synlighed:</strong> behold standardens fokusring i knap- og '
                'linkdesign, eller definér en synlig erstatning. Fjern aldrig outlines uden '
                'alternativ.</p>',
                '<p><strong>Sprog:</strong> sæt sidens sprog i Indstillinger så <code>html lang</code> '
                'bliver korrekt — skærmlæsere vælger udtale ud fra den.</p>',
                '<p><strong>Formularer:</strong> label hvert felt tydeligt, slå fejlbeskeder til '
                'der beskriver hvad der skal rettes, og bekræft afsendelse både visuelt og i tekst.</p>',
            ]),
            ('Apps og platformgrænser', [
                '<p>Tredjeparts Wix-apps (booking-widgets, chat-popups, review-slidere) er den '
                'største compliance-risiko du ikke fuldt styrer: mange injicerer iframes med egen '
                'markering, små tap-mål og keyboard-fælder. Gennemgangsmetoden er at tabbe dig '
                'gennem hver apps widget på en live side — er appen utilgængelig, så udskift den '
                'eller giv samme funktion via et tilgængeligt alternativ (fx en simpel '
                'bookingsformular ved siden af en utilgængelig widget).</p>',
                '<p>Kend også de ægte platformgrænser: enkelte legacy-funktioner og visse dynamiske '
                'sider giver mindre semantisk kontrol end moderne editor-sektioner. Dokumentér '
                'resterende huller ærligt i sitens tilgængelighedserklæring frem for at påstå en '
                'full conformance du ikke kan bevise.</p>',
            ]),
            ('Audit-workflow i fem skridt', [
                '<p><strong>Trin 1 — automatisk scanning</strong> af forsiden, én nøgleservice-/'
                'produktside og kontaktsiden. Forvent 10-25 fund på en typisk '
                'småvirksomhedsside.</p>',
                '<p><strong>Trin 2 — ret i editoren, publicér, genscan</strong> til de automatiske '
                'fund er væk.</p>',
                '<p><strong>Trin 3 — keyboard-gennemgang:</strong> tag musen fra bordet — menuer, '
                'gallerier, lightboxes, formularer og cookie-banneret skal alle kunne betjenes.</p>',
                '<p><strong>Trin 4 — mobil-tjek:</strong> Wix renderer et separat mobil-layout; '
                'gen-tjek tap-mål og tekstskalering dér specifikt.</p>',
                '<p><strong>Trin 5 — levér:</strong> fundrapport plus tilgængelighedserklæring med '
                'conformance-status og kendte begrænsninger (fx en booking-widget). Genscan efter '
                'større redigeringer.</p>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan din Wix-side gratis'),
              ('/da/blog/eaa-tjekliste-2026', 'EAA-tjekliste')],
        related=[('/da/blog/tilgaengeligheds-overlays-eaa', 'Overlays og EAA'),
                 ('/da/blog/pris-tilgaengelighedsgennemgang', 'Pris på tilgængelighedsgennemgang'),
                 ('/da/blog/gratis-tilgaengelighedsvaerktoejer', 'Gratis tilgængelighedsværktøjer')],
        da_link_text='Wix og tilgængelighed: bliv EAA-compliant',
        faqs=[
            ('Er Wix tilgængeligt ud af boksen?',
             'Moderne Wix-skabeloner klarer sig fornuftigt på automatiske tjek, og Wix leverer '
             'rigtige tilgængelighedsindstillinger. Men byggerens valg — tekst oven på fotos, '
             'manglende alt, falske overskrifter — skaber fejl på stort set hver rigtig side. '
             'Ud af boksen hjælper; det comply\'er ikke for dig.'),
            ('Gælder EAA min kundes lille Wix-butik?',
             'EAA dækker forbruger-e-handel og -tjenester med begrænsede undtagelser for '
             'mikrovirksomheder der yder tjenester (under 10 ansatte og 2 mio. euro omsætning). '
             'E-handel har som regel ingen størrelsesbefrielse — antag at en webshop er i omfang.'),
            ('Må jeg bruge et tilgængeligheds-overlay på Wix?',
             'Overlays kan ikke skabe manglende semantik, rette ubrugelige apps eller reparere '
             'kontrast inde i dine egne billeder, og at markedsføre dem som automatisk compliance '
             'har mødt regulatorisk kritik i EU. Ret årsagerne i editoren i stedet.'),
            ('Hvordan tester jeg Wix\' separate mobil-layout?',
             'Publicér og åbn den live side på en telefon eller i browserens mobilemulator. Wix '
             'vedligeholder et distinkt mobil-view, så desktop-rettelser skal verificeres dér '
             'også — især tekststørrelse og knapafstande.'),
            ('Kan bureauer sælge Wix-tilgængelighedsaudits?',
             'Ja. Millioner af EU-småvirksomheder ligger på Wix og står nu med EAA-spørgsmål de '
             'ikke kan svare på. En fastpris scan-ret-rapport-pakke er let at sælge og parres '
             'naturligt med den leverede tilgængelighedserklæring.'),
        ],
    ),
    dict(
        en_slug='squarespace-eaa-accessibility',
        slug='squarespace-tilgaengelighed-eaa',
        badge='SQUARESPACE &middot; TILGÆNGELIGHED &middot; EAA',
        title_tag='Squarespace og tilgængelighed: bliv EAA-compliant (guide 2026)',
        h1='Squarespace og tilgængelighed:<br>bliv EAA-compliant',
        desc=('Gør din Squarespace-side compliant med European Accessibility Act og '
              'WCAG 2.1 AA: farvepar, alt-tekst, overskriftsstruktur, code injection '
              'og en verificerings-workflow — trin for trin på dansk.'),
        subtitle=('Praktisk compliance-guide for Squarespace-ejere og bureauer: hvad du '
                  'kan og ikke kan rette i Squarespace, og workflowet der bringer en '
                  'skabelonbaseret side op på WCAG 2.1 AA.'),
        read='6 minutters læsning',
        intro=('Enhver Squarespace-side der sælger til eller informerer EU-forbrugere er '
               'omfattet af European Accessibility Act, hvor tjenesten er forbrugervendt — '
               'webshops allerførst. Det tekniske benchmark er EN 301 549 / WCAG 2.1 niveau AA. '
               'Squarespace lever rimeligt compliant skabeloner og infrastruktur, men '
               'sidens ejer ansvar for sit konfigurerede tema, sit indhold og sine '
               'tredjeparts-indlejringer. Den praktiske udfordring adskiller sig fra '
               'open source-CMS\'er: du styrer ikke markeringen, så compliance-arbejdet '
               'består i at arbejde indstillingerne, indholdet og et kort liste over '
               'code injection-punkter.'),
        cards=[
            ('⚖️ Juridisk omfang', 'E-handel og forbrugertjenester er nævnt direkte i EAA; '
             'salg til EU udløser reglerne uanset hvor ejeren er baseret.'),
            ('🧱 Skabelon-realiteten', 'Du kan ikke redigere den underliggende HTML på '
             'almindelige abonnementer. De fleste mekaniske retter ligger i site styles, '
             'sektionsindstillinger og billedfelter.'),
            ('🛡️ Ejers ansvar', 'Platformen giver dig værktøjerne; conformance opnås (eller '
             'tabes) af hvordan du konfigurerer og fylder dem.'),
        ],
        sections=[
            ('Hvor Squarespace-sider typisk fejler', [
                '<div class="problem-cards">'
                '<div class="card"><h3>🎨 Farvevalg</h3><p>Lysgrå brødtekst, lavkontrast-knapper '
                'oven på bannerbilleder, transparente headers oven på hero-sektioner. Squarespace '
                'lad dig vælge vilkårlige farvepar — det advarer dig ikke om kontrast.</p></div>'
                '<div class="card"><h3>🖼️ Manglende alt-tekst</h3><p>Den største enkeltkategori. '
                'Galleribilleder, baggrundsbilleder og inline-billeder skal alle have alt udfyldt '
                'pr. element; mange ejere rører aldrig feltet.</p></div>'
                '<div class="card"><h3>📐 Overskriftsmisbrug</h3><p>I Fluid Engine vælger tekstblokke '
                '"Overskrift 2" pga. størrelsen snarere end struktur — resultatet er sprunget niveauer '
                'og sider uden sammenhængende outline.</p></div>'
                '<div class="card"><h3>🔌 Indlejringer og kodeblokke</h3><p>Booking-widgets, formularer '
                'og video-embeds injicerer deres egen markering — unlabelled kontroller og '
                'keyboard-fælder kommer med ind.</p></div>'
                '</div>',
            ]),
            ('Indstillinger du kan rette i dag — uden kode', [
                '<p><strong>Farvepar:</strong> mørk gør brødtekst- og knapfarver i site styles til '
                'hver kombination klarer 4,5:1 (3:1 for stor tekst). Tjek announcement bars, footers '
                'og formularetiketter separat — de bærer egne par.</p>',
                '<p><strong>Alt-tekst overalt:</strong> udfyld alt pr. billede på sider, i gallerier '
                'og produktkort. Dekorative baggrunde håndterer temaet med tom alt; indholdsbilleder '
                'må beskrive sig selv.</p>',
                '<p><strong>Overskriftsstruktur:</strong> én h1 pr. side (typisk sidetitlen). '
                'Om-mærk sektionstitler så outline går ned uden spring — brug stiloverrides for '
                'udseendet i stedet for at vælge "større" overskrifter.</p>',
                '<p><strong>Linktekster:</strong> udskift gentagne "læs mere" med beskrivende tekst. '
                'Knapper der er billeder, skal have alt-tekst der navngiver handlingen.</p>',
                '<p><strong>Bevægelse og fokus:</strong> slå autospillende bannere fra eller hold dem '
                'subtile; verificér at fokusindikatorer stadig er synlige efter eventuel custom CSS.</p>',
            ]),
            ('Code injection-punkter', [
                '<p>Når indstillingerne slipper op, giver Squarespace tre kontrollerede '
                'nødudgange:</p>',
                '<p><strong>Kode-/embed-blokke:</strong> brug dem sparsomt, og kun med widgets du '
                'har tab-testet. Fælder en bookings- eller formular-widget tastaturet, så udskift '
                'den — ingen mængde styling retter det.</p>',
                '<p><strong>Code injection (footer):</strong> små CSS-patches er legitime her — at '
                'genskabe synlige <code>:focus-visible</code>-outlines en skabelon fjernede, er en '
                'én-linjes ret med reel effekt.</p>',
                '<p><strong>Custom CSS-panelet:</strong> ret kontrast ved at override specifikke '
                'klasser frem for at re-theme. Hold ændringerne dokumenteret; '
                'skabelonopdateringer kan flytte klassenavne.</p>',
                '<p><strong>Undgå overlay-scripts:</strong> "accessibility widgets" gør ikke en '
                'Squarespace-side conformant og har mødt europæisk regulatorisk kritik. Ret '
                'årsagerne i stedet.</p>',
            ]),
            ('Verificering i fem skridt', [
                '<p>En realistisk verificeringsloop tager to til fire timer:</p>',
                '<p><strong>Trin 1 — automatisk scanning</strong> af forsiden, én index-/kollektionsside, '
                'en detaljeside og kontaktsiden. Forvent 5-15 fund første gang, mest alt-tekst og '
                'kontrast.</p>',
                '<p><strong>Trin 2 — ret og genscan</strong> via site styles og billedfelter til de '
                'mekaniske fund er væk.</p>',
                '<p><strong>Trin 3 — keyboard-gennemgang</strong> af navigation → side → '
                'kurv/kontakt-afsendelse. Alt der kræver mus fejler WCAG 2.1.2; indlejrede widgets er '
                'de sædvanlige synder.</p>',
                '<p><strong>Trin 4 — mobil-tjek:</strong> Squarespace renderer et andet '
                'navigationsmønster på mobil — test at burger-menuen åbner, lukker og kan nås med '
                'tastatur.</p>',
                '<p><strong>Trin 5 — dokumentér:</strong> publicér en tilgængelighedserklæring med '
                'conformance-status og kendte begrænsninger (fx en specifik indlejring). Under EAA er '
                'det forventet, ikke valgfrit.</p>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan din Squarespace-side gratis'),
              ('/da/blog/wcag-22-aendringer', 'WCAG 2.2-ændringer')],
        related=[('/da/blog/tilgaengeligheds-overlays-eaa', 'Overlays og EAA'),
                 ('/da/blog/skriv-tilgaengelighedserklaering', 'Skriv en tilgængelighedserklæring'),
                 ('/da/blog/eaa-haandhaevelse-2026', 'EAA-håndhævelse i 2026')],
        da_link_text='Squarespace og tilgængelighed: bliv EAA-compliant',
        faqs=[
            ('Gælder EAA min Squarespace-side?',
             'Tilbyder den forbrugertjenester eller e-handel til EU, ja — også for små '
             'virksomheder, da online shops ikke har nogen generel mikrovirksomhedsbefrielse. '
             'Rent indholdsbaserede hobbiesider falder stort set udenfor, men WCAG tæller stadig '
             'for rækkevidde og kvalitet.'),
            ('Er Squarespace selv tilgængeligt?',
             'Squarespace oplyser at platformen sigter mod WCAG 2.1 AA, og aktuelle skabeloner er '
             'fornemme udgangspunkter. Men ejeren ejer sin konfiguration og sit indhold — en '
             'compliant platform gør ikke hver side bygget på den compliant.'),
            ('Kan jeg redigere HTML i Squarespace for at rette fejl?',
             'Ikke den underliggende skabelonmarkering på standardabonnementer. Du arbejder via '
             'site styles, sektionsindstillinger, alt-tekstfelter, CSS-panelet og code '
             'injection-punkter — tilsammen dækker de næsten alt en audit finder.'),
            ('Virker de der accessibility-widget-scripts på Squarespace?',
             'De kan injiceres, men de giver ikke conformance: overlays kan ikke rette kontrast i '
             'billeder, ødelagte embeds eller manglende alt-tekst, og EU-myndigheder har kritiseret '
             'at markedsføre dem som compliance.'),
            ('Hvor lang tid tager det typisk?',
             'En velholdt skabelonside: 2-4 timer til indstillinger, alt-tekst-backfill og test. '
             'Sider på gamle legacy-skabeloner eller med tunge embed-stakke kræver mere — som regel '
             'udskiftning af de værste embeds først.'),
        ],
    ),
    dict(
        en_slug='magento-eaa-accessibility',
        slug='magento-tilgaengelighed-eaa',
        badge='MAGENTO &middot; TILGÆNGELIGHED &middot; EAA',
        title_tag='Magento og tilgængelighed: bliv EAA-compliant (guide 2026)',
        h1='Magento og tilgængelighed:<br>bliv EAA-compliant',
        desc=('Gør din Magento- eller Adobe Commerce-butik compliant med European '
              'Accessibility Act og WCAG 2.1 AA: temaer, extensions, checkout og '
              'remediation-workflowet — trin for trin på dansk.'),
        subtitle=('Praktisk compliance-guide for Magento-butikker og bureauer: hvor '
                  'butikker fejler WCAG 2.1 AA — temaer, extensions, checkout — og '
                  'remediation-workflowet der gør EU-butikker EAA-klar.'),
        read='7 minutters læsning',
        intro=('Magento (nu Adobe Commerce) driver en stor del af Europas mellemstore og '
               'enterprise-webshops — netop den e-handelskategori European Accessibility Act '
               'regulerer uden mikrovirksomhedsbefrielse. Siden juni 2025 er en utilgængelig '
               'Magento-butik en juridisk eksponering i ethvert EU-marked, og B2B-indkøbere '
               'kaskader i stigende grad EN 301 549-krav ned i leverandørkontrakter. Skalaen '
               'adskiller sig fra WordPress og Wix: Magento-butikker har mere custom theming, '
               'flere extensions og mere komplekse transaktionsflows — hvilket betyder mere '
               'fejlflade, men også større budget til at rette det ordentligt.'),
        cards=[
            ('🛒 Ingen størrelsesbefrielse', 'I modsætning til tjenesteydere har e-handel '
             'ingen mikrovirksomhedsbefrielse under EAA. Selv en to-mands Magento-butik '
             'skal comply.'),
            ('🧱 Tema-arvsrisiko', 'De fleste butikker kører tungt tilpassede efterkommere '
             'af Luma — tilgængelighedsfejl bagt ind i forældretemaet replikerer på hver '
             'enkel side.'),
            ('🔌 Extension-vildvest', 'Checkout-opgraderinger, søgning, reviews og wishlists '
             'kommer ofte fra tredjepartsleverandører med ukendt tilgængelighedskvalitet. '
             'Hver enkelt skal auditeres.'),
        ],
        sections=[
            ('Typiske Magento-fejl', [
                '<div class="problem-cards">'
                '<div class="card"><h3>🧭 Lagernavigation</h3><p>Filter-facets renderet som '
                'div-baserede toggles uden aria-expanded eller tastaturstøtte. Skærmlæserbrugere '
                'kan slet ikke indsnævre et produktrude.</p></div>'
                '<div class="card"><h3>🔢 Antals- og variantinput</h3><p>Custom steppers der '
                'erstatter native number-inputs, swatches uden labels eller annoncering af '
                'valgt tilstand — de klassiske kurv-ødelæggende fejl.</p></div>'
                '<div class="card"><h3>💳 One-page checkout</h3><p>Ajax-swappede checkout-sektioner '
                'hverken flytter fokus eller annoncerer fejl. Betalingsfelter uden programmatisk '
                'koblede labels.</p></div>'
                '<div class="card"><h3>🖼️ Produktmedier</h3><p>Zoom-gallerier uden tastaturbetjening '
                'eller alt-tekst; farvevarianter formidlet kun visuelt via swatches.</p></div>'
                '<div class="card"><h3>🔔 Toasts og mini-cart</h3><p>"Lagt i kurv"-bekræftelser vist '
                'kun visuelt — ingen ARIA live region, så ikke-synende shoppere lægger varer i igen '
                'og igen.</p></div>'
                '<div class="card"><h3>🔍 Søgeautofuldførelse</h3><p>Type-ahead-forslag i '
                'utilgængelige popups der ignorerer piletaster og Escape.</p></div>'
                '</div>',
            ]),
            ('Tema- og skabelonretter', [
                '<p>Remediation sker mest i dit custom tema:</p>',
                '<p><strong>Start med semantikken:</strong> genskab rigtige landmarks (header, nav, '
                'main, footer), én h1 pr. side, og produktopslag som rigtige overskrifter i lister '
                'og grids.</p>',
                '<p><strong>Native inputs først:</strong> udskift custom antals-steppers og selects '
                'med native elementer stylet til at matche — de arver tastatur- og '
                'skærmlæseradfærd gratis.</p>',
                '<p><strong>ARIA-tilstande:</strong> facetnavigation behøver aria-expanded på '
                'toggles, aria-pressed på filter-chips, og resultatantal annonceret via aria-live.</p>',
                '<p><strong>Fokusstyring:</strong> hver Ajax-section-swap (kurv-opdateringer, '
                'checkout-trin) flytter fokus til sit nye indhold; fejlopsummeringer modtager fokus '
                'og linker til de enkelte feltfejl.</p>',
                '<p><strong>Formlabels:</strong> auditér hver skabelon der renderer formfelter for '
                'eksplicitte label-koblinger — Magentos knockout-skabeloner udelader dem ofte.</p>',
                '<p><strong>Kontrast-tokens:</strong> ret grå-på-grå pris/metatekst ét sted i '
                'temavariablerne, og verificér derefter på sale badges og knapper.</p>',
            ]),
            ('Extensions og opgraderinger', [
                '<p>Behandl hver tredjeparts-extension som en tilgængeligheds-ukendt indtil det '
                'modsatte er bevist. Metoden: på staging, gå extensionens komplette flow igennem '
                'kun med tastatur, derefter med en skærmlæser — installér, konfigurér, brug, '
                'fortryd. Leverandører varierer vildt; nogle store checkout- og søgemoduler har '
                'kendte offentlige tilgængelhedsproblemer.</p>',
                '<p>Når en extension fejler og leverandøren ikke vil rette, så beslut '
                'bevidst: udskift den, wrap den med et korrigerende lag, eller dokumentér den som '
                'begrænsning i tilgængelighedserklæringen med en workaround-vej.</p>',
                '<p>Bemærk desuden at opgraderinger mellem Magento-versioner lydløst '
                'genintroducerer gamle fejl dér hvor du patchede vendor-filer — kør din scanning '
                'igen efter hver opgradering som standardpraksis.</p>',
            ]),
            ('Audit-workflow i fem skridt', [
                '<p><strong>Trin 1 — automatisk crawl</strong> af home-, kategori-, produkt-, cart-, '
                'checkout- og konto-skabeloner — forvent 20-50 distinkte fund på en typisk '
                'butik.</p>',
                '<p><strong>Trin 2 — transaktionsforløb:</strong> gennemfør søgning → filtrering → '
                'produkt → kurv → checkout ende-til-ende med tastatur, derefter med skærmlæser. '
                'Det er her EAA-risikoen sidder.</p>',
                '<p><strong>Trin 3 — extension-pass:</strong> auditér hvert installeret moduls '
                'widgets individuelt.</p>',
                '<p><strong>Trin 4 — ret i temaet</strong> (ikke vendor-patcher hvor det kan undgås), '
                'deploy til staging, genscan til ren.</p>',
                '<p><strong>Trin 5 — levér:</strong> fundrapport, verificeret butik og en '
                'tilgængelighedserklæring med conformance-status og dokumenterede begrænsninger. '
                'Re-audit efter hver versionsopgradering og større extension-ændring.</p>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan din Magento-butik gratis'),
              ('/da/blog/shopify-tilgaengelighed-eaa', 'Shopify-guiden')],
        related=[('/da/blog/eaa-frister-2026', 'EAA-frister i 2026'),
                 ('/da/blog/tjekliste' if False else '/da/blog/eaa-tjekliste-2026', 'EAA-tjekliste'),
                 ('/da/blog/pris-tilgaengelighedsgennemgang', 'Pris på tilgængelighedsgennemgang')],
        da_link_text='Magento og tilgængelighed: bliv EAA-compliant',
        faqs=[
            ('Gælder EAA små Magento-butikker?',
             'Ja for e-handel: i modsætning til tjenesteydere har online shops ingen '
             'mikrovirksomhedsbefrielse under EAA. En lille Magento-butik der sælger til '
             'EU-forbrugere er i omfang uanset antal ansatte.'),
            ('Er Adobe Commerce mere tilgængeligt end open source-Magento?',
             'Adobe har forbedret kerne-tilgængeligheden, men næsten enhver butik lægger et custom '
             'tema og extensions ovenpå, og det afgør den reelle conformance. Platformudgaven '
             'betyder langt mindre end tema- og extensionkvalitet.'),
            ('Vi bruger en stor kommerciel checkout-extension — er vi så dækket?',
             'Ikke automatisk. Store checkout-moduler har været leveret med alvorlige tastatur- og '
             'skærmlæserproblemer. Auditér jeres præcise installerede version på staging; stol ikke '
             'på markedsføring.'),
            ('Hvor lang tid tager en Magento-tilgængelighedsoprydning?',
             'En typisk mellemstor butik behøver 2-6 ugers fokuseret tema- og skabelonarbejde afhængig '
             'af tilpasningsdybde. Automatisk scanning skærer det ned betydeligt ved at give '
             'udviklerne en præcis arbejdsliste.'),
            ('Skal vi have VPAT/EN 301 549-dokumentation?',
             'Sælger I til offentlige kunder eller store B2B-kunder, ja — de beder om en EN 301 '
             '549-conformitetsrapport. En audit plus jeres tilgængelighedserklæring føder direkte ind '
             'i det dokument.'),
        ],
    ),
]

CSS = '''
  .compare { width:100%; border-collapse:collapse; font-size:0.92rem; margin:1.5rem 0; }
  .compare th, .compare td { text-align:left; padding:10px 12px; border-bottom:1px solid var(--color-border); vertical-align:top; }
  .compare th { border-bottom:2px solid var(--color-border); }
'''

TRACK_JS = ("(function(){{try{{if(navigator.doNotTrack==='1')return;"
            "var p=location.pathname.replace(/\\.html$/,'')||'/';"
            "fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},"
            "body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}"
            "catch(e){{}}}})();")


def build(page):
    url = f'{BASE}/da/blog/{page["slug"]}'
    en_url = f'{BASE}/blog/{page["en_slug"]}'
    faqs = page['faqs']
    article_json = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article',
        'headline': re.sub(r'<[^>]+>', '', page['da_link_text']),
        'description': page['desc'],
        'url': url,
        'datePublished': TODAY, 'dateModified': TODAY,
        'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
        'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    }, ensure_ascii=False)
    faq_json = json.dumps({
        '@context': 'https://schema.org', '@type': 'FAQPage',
        'mainEntity': [{'@type': 'Question', 'name': q,
                        'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs],
    }, ensure_ascii=False)
    faq_html = '\n      '.join(f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in faqs)
    rel_html = ' &middot; '.join(
        f'<a href="{h}" style="color:var(--color-accent);">{t}</a>' for h, t in page['related'])
    cta_a, cta_b = page['ctas']
    body_sections = []
    for head, parts in page['sections']:
        body_sections.append(
            '<section class="products">\n  <div class="container">\n'
            f'    <h2>{head}</h2>\n    ' + '\n    '.join(parts) +
            '\n  </div>\n</section>')
    sections_html = '\n\n'.join(body_sections)
    card_html = '\n      '.join(
        f'<div class="card"><h3>{h}</h3><p>{p}</p></div>' for h, p in page['cards'])

    return f'''<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page["title_tag"]}</title>
<meta name="description" content="{page["desc"]}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Hermes Passiv">
<meta property="og:title" content="{page["da_link_text"]}">
<meta property="og:description" content="{page["desc"]}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/cover.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="x-default" href="{en_url}">
<link rel="alternate" hreflang="da" href="{url}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{article_json}
</script>
<script type="application/ld+json">
{faq_json}
</script>
<script defer src="/track.js"></script>
<style>{CSS}</style>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">{page["badge"]}</div>
    <h1>{page["h1"]}</h1>
    <p class="subtitle">{page["subtitle"]}</p>
    <div class="hero-cta">
      <a href="#indhold" class="btn-primary">Læs guiden</a>
      <a href="/scan-da" class="btn-secondary">Scan din side gratis &rarr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; {page["read"]}</p>
  </div>
</header>

<section class="problem" id="indhold">
  <div class="container">
    <h2>Hvorfor dette gælder dig</h2>
    <p>{page["intro"]}</p>
    <div class="problem-cards">
      {card_html}
    </div>
  </div>
</section>

{sections_html}

<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
      {faq_html}
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/scan-da" class="btn-primary">Start med en gratis scanning &rarr;</a>
    </div>
    <div style="text-align:center;margin-top:16px;"><p>Relateret: {rel_html}</p></div>
  </div>
</section>

<footer style="padding:32px 24px;">
  <p><a href="/">Forside</a> &middot; <a href="/scan-da">EAA-scanner</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/blog">Blog (EN)</a> &middot; <a href="{en_url}">Engelsk version</a></p>
  <p>Mahope © 2026 · Praktisk EU-compliance for små webbureauer</p>
</footer>
<script>
{TRACK_JS}
</script>
</body>
</html>
'''


def main():
    pf_path = os.path.join(SITE, 'hreflang_pairs.json')
    pairs = json.load(open(pf_path))

    for page in PAGES:
        print('=== ', page['slug'])
        html = build(page)

        out = os.path.join(SITE, f'da/blog/{page["slug"]}.html')
        new = not os.path.exists(out)
        if new:
            with open(out, 'w') as f:
                f.write(html)

        content = open(out).read()
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
        assert len(blocks) == 2, f'{page["slug"]}: expected 2 JSON-LD blocks, got {len(blocks)}'
        for i, b in enumerate(blocks):
            parsed = json.loads(b)
            assert parsed['@context'] == 'https://schema.org', parsed['@context']
        refs = re.findall(r'href="(/[^"#]+)"', content)
        missing = [r for r in set(refs)
                   if not r.startswith('/api')
                   and r not in ('/sitemap.xml', '/style.css', '/track.js', '/blog', '/free-tools')
                   and not os.path.exists(os.path.join(ROOT, 'site', r.lstrip('/') + '.html'))]
        assert not missing, missing
        assert not [r for r in refs if r.endswith('.html')], 'raw .html link found'
        print('  JSON-LD OK, %d internal links OK, no .html links' % len(set(refs)))

        # hreflang on the EN mirror (idempotent)
        en_url = f'{BASE}/blog/{page["en_slug"]}'
        en_path = os.path.join(SITE, f'blog/{page["en_slug"]}.html')
        e = open(en_path).read()
        hl_set = ('<link rel="alternate" hreflang="x-default" href="%s">\n'
                  '<link rel="alternate" hreflang="da" href="%s">\n'
                  '<link rel="alternate" hreflang="en" href="%s">' % (
                      en_url, f'{BASE}/da/blog/{page["slug"]}', en_url))
        if 'hreflang="da"' not in e:
            anchor = f'<link rel="canonical" href="{en_url}">'
            assert anchor in e, 'no canonical anchor in ' + page['en_slug']
            e = e.replace(anchor, anchor + '\n' + hl_set, 1)
            open(en_path, 'w').write(e)
            print('  EN mirror: hreflang added')
        else:
            print('  EN mirror: hreflang present')

        # hreflang_pairs.json
        if page['en_slug'] not in pairs:
            pairs[page['en_slug']] = page['slug']

        # sitemap (idempotent)
        sm = os.path.join(SITE, 'sitemap.xml')
        c = open(sm).read()
        da_url = f'{BASE}/da/blog/{page["slug"]}'
        if da_url + '</loc>' not in c:
            entry = ('<url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n'
                     '    <priority>0.8</priority>\n  </url>\n  ' % (da_url, TODAY))
            c = c.replace('</urlset>', entry + '</urlset>')
            open(sm, 'w').write(c)
            print('  sitemap entry added')
        else:
            print('  sitemap already has URL')

        # blog index DA entry (idempotent)
        idx = os.path.join(SITE, 'blog/index.html')
        x = open(idx).read()
        if page['slug'] not in x:
            li = ('<li style="margin-bottom:14px"><a href="/da/blog/%s" '
                  'style="color:var(--color-accent);text-decoration:none">%s</a></li>'
                  % (page['slug'], page['da_link_text']))
            lines = x.split('\n')
            last = max(i for i, ln in enumerate(lines) if '/da/blog/' in ln and '<li' in ln)
            lines.insert(last + 1, li)
            open(idx, 'w').write('\n'.join(lines))
            print('  blog index: DA entry added')
        else:
            print('  blog index: present')

        # reciprocal cross-link from EN post
        src = os.path.join(SITE, f'blog/{page["en_slug"]}.html')
        s = open(src).read()
        if ('Dansk version: <a href="%s"' % (f'{BASE}/da/blog/{page["slug"]}')) not in s:
            add = ('<div style="text-align:center;margin-top:16px;"><p>Dansk version: '
                   '<a href="%s" style="color:var(--color-accent);">%s</a></p></div>\n'
                   % (f'{BASE}/da/blog/{page["slug"]}', page['da_link_text']))
            if '<footer class="site-footer">' in s:
                s = s.replace('<footer class="site-footer">', add + '<footer class="site-footer">', 1)
            else:
                anchor = '<footer style="padding:32px 24px;">'
                assert anchor in s, 'no footer anchor in ' + page['en_slug']
                s = s.replace(anchor, add + anchor, 1)
            open(src, 'w').write(s)
            print('  EN post: Danish cross-link added')
        else:
            print('  EN post: cross-link present')

        if new:
            print('  wrote:', out)
        else:
            print('  file existed; validated only')

    open(pf_path, 'w').write(json.dumps(pairs, indent=1, ensure_ascii=False) + '\n')
    print('\nhreflang_pairs.json: %d pairs' % len(pairs))
    xml.dom.minidom.parse(os.path.join(SITE, 'sitemap.xml'))
    print('sitemap parses as XML')


if __name__ == '__main__':
    main()
