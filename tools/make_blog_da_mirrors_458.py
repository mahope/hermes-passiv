#!/usr/bin/env python3
"""Iteration 458: Danish mirrors of PrestaShop-vs-Shopify and Webflow-vs-Squarespace.

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
    # ------------------------------------------- PrestaShop vs Shopify ---
    dict(
        en_slug='prestashop-vs-shopify-accessibility',
        slug='prestashop-vs-shopify-tilgaengelighed',
        badge='PRESTASHOP VS SHOPIFY &middot; SAMMENLIGNING &middot; EAA',
        title_tag='PrestaShop vs Shopify: tilgængelighed sammenlignet (EAA-guide 2026)',
        h1='PrestaShop vs Shopify:<br>tilgængelighed sammenlignet',
        desc=('Begge platforme skal opfylde European Accessibility Act. Hvor hver af '
              'dem fejler WCAG 2.1 AA, hvordan fix-workflowsne adskiller sig, og hvad '
              'det betyder for din webshop — på dansk.'),
        subtitle=('Sammenligning for EU-handlere og bureauer: samme lov, to '
                  'arkitekturer. Se hvor defekterne kommer fra på hver platform, '
                  'hvem der kan rette dem, og hvilken proces der holder shoppens '
                  'compliance i hævd efter hver opdatering.'),
        read='7 minutters læsning',
        intro=('Shopify og PrestaShop ligger under præcis samme juridiske forpligtelse: '
               'siden juni 2025 kræver European Accessibility Act, at e-handel opfylder '
               'EN 301 549 / WCAG 2.1 AA — uden undtagelse for mikrovirksomheder der '
               'sælger online. Det der adskiller dem, er hvor defekterne kommer fra, '
               'og hvem der kan rette dem. Shopify samler kontrollen i et hosted '
               'theme-lag med Liquid-skabeloner og et app-økosystem; PrestaShop giver '
               'dig selvhostede kernetemplates, et back office og et marked af moduler. '
               'Compliance-arbejdet følger arkitekturen — ikke loven.'),
        cards=[
            ('⚖️ Samme standard', 'EN 301 549 med WCAG 2.1 niveau AA gælder begge. '
             'Betalingsudbydere og markedspladser forlanger i stigende grad '
             'dokumenteret conformance fra handlere på begge platforme.'),
            ('🎨 Theme dominerer', 'På begge platforme styrer det aktive theme næsten al '
             'renderet HTML — overskriftshierarki, fokus-tilstande, kontrast og '
             'formularlabels er theme-beslutninger, ikke platformbeslutninger.'),
            ('🔌 Tredjepartsrisiko', 'Shopify-apps og PrestaShop-moduler injicerer begge '
             'widgets (filtre, reviews, popups) med svingende tilgængelighedskvalitet. '
             'Hver skal auditers for sig.'),
        ],
        sections=[
            ('Hvor Shopify fejltypisk ses', [
                '<p>Typiske Shopify-defektmønstre:</p>',
                '<p><strong>App-widgets:</strong> review-sliders, quick-view-modals og '
                'upsell-popups fra apps fanger ofte tastaturfokus eller renderer knapper '
                'uden labels.</p>',
                '<p><strong>Theme-kontrast:</strong> Dawn-baserede custom-themes sejler '
                'grå-på-grå udsalgsbadges og footer-tekst under 4.5:1.</p>',
                '<p><strong>Ajax-sektioner:</strong> cart-drawer og filtrering som hverken '
                'flytter fokus eller annoncerer ændringer via ARIA live regions.</p>',
                '<p><strong>Separate mobil-beslutninger:</strong> theme-indstillinger lader '
                'handleren style mobil uafhængigt — retter lavet til desktop når i '
                'tavshed aldrig mobil-breakpointet.</p>',
            ]),
            ('Hvor PrestaShop fejltypisk ses', [
                '<p>Typiske PrestaShop-defektmønstre:</p>',
                '<p><strong>Tomme produkt-legender:</strong> bulk-import springer '
                'Legend-feltet over, så kategorigitter fyldes med billeder helt uden '
                'alt-tekst.</p>',
                '<p><strong>Facetterede filtermoduler:</strong> tredjepartsfilter facetter '
                'renderer som klikbare divs uden tastaturunderstøttelse eller '
                'aria-expanded.</p>',
                '<p><strong>Checkout-flow:</strong> ajax-udskiftede checkout-trin uden '
                'focus management, betalingsfelter uten tilknyttede labels.</p>',
                '<p><strong>Patchede vendor-filer:</strong> direkte rettelser i kerne- eller '
                'modulfiler bliver lydløst rullet tilbage ved hver opgradering og '
                'genindfører gamle fejl.</p>',
            ]),
            ('Fix-workflow sammenlignet', [
                '<p>Remedieringslooppene adskiller sig i én vigtig ting: hvem ejer koden.</p>',
                '<p><strong>Shopify:</strong> retter lander i theme Liquid/CSS via '
                'theme-editoren eller en udviklingskopi af themet. App-forårsagede defekter '
                'kan slet ikke rettes — du erstatter appen eller dokumenterer den som en '
                'begrænsning i din tilgængelighedserklæring. Opgraderinger håndteres af '
                'Shopify og rammer sjældent dit theme-arbejde.</p>',
                '<p><strong>PrestaShop:</strong> back office-content-retter (alt-tekst via '
                'Katalog &rarr; Produkter &rarr; Photos Legend, shoppens sprogindstillinger) '
                'plus template-overrides i et child theme. Du ejer selv hostingen, så du ejer '
                'også opgraderingsdisciplinen: scan igen efter hver kerne-, theme- og '
                'modulopdatering, for patchede vendorfiler ruller tilbage.</p>',
                '<p>Nettoeffekt: Shopify bytter mindre kontrol til færre '
                'regressionsoverraskelser; PrestaShop giver fuld kontrol men kræver en '
                'gentagelig re-verifikationsvane.</p>',
            ]),
            ('Hvad er nemmest at comply?', [
                '<p>For en typisk lille EU-handler allerede på én af platformene er det '
                'næsten aldrig værd at skifte platform for at opnå tilgængelighed — '
                'defektvolumenet ligger i theme- og tredjepartslagene, som findes på begge.</p>',
                '<p>Den praktiske indsats-rækkefølge: mekaniske retter (kontrast-tokens, '
                'alt-tekst, labels) tager dage på begge; widget-niveau app/modul-remediation '
                'tager uger på begge; differentiatoren er processdisciplin.</p>',
                '<p>Kør et automatisk scan hen over forside, kategori, produkt, kurv og '
                'checkout på begge stacks, ret i theme eller child theme, auditér hver '
                'app/modul individuelt, og publicér en tilgængelighedserklæring med '
                'dokumenterede begrænsninger. Scan igen efter hver theme-ændring og '
                'platformopgradering.</p>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan din shop gratis'),
              ('/da/blog/eaa-tjekliste-2026', 'EAA-tjekliste')],
        related=[('/da/blog/shopify-tilgaengelighed-eaa', 'Shopify og tilgængelighed'),
                 ('/da/blog/prestashop-tilgaengelighed-eaa', 'PrestaShop og tilgængelighed'),
                 ('/da/blog/skriv-tilgaengelighedserklaering', 'Skriv en tilgængelighedserklæring')],
        da_link_text='PrestaShop vs Shopify: tilgængelighed sammenlignet',
        faqs=[
            ('Skal min webshop overholde EAA?',
             'Ja. Siden 28. juni 2025 omfatter European Accessibility Act e-handelstjenester '
             'i hele EU — også mikrovirksomheder der sælger online. Teknisk standard er EN '
             '301 549 / WCAG 2.1 niveau AA.'),
            ('Kan jeg bare skifte platform for at blive compliant?',
             'Næsten aldrig. Defekterne kommer fra theme, apps/moduler og redaktionelt '
             'indhold — lag der findes på begge platforme. En migrering koster mere end '
             'remediation og flytter ikke ansvaret.'),
            ('Hvad med apps og moduler fra tredjepart?',
             'De skal auditers ét ad gangen: test tastaturnavigation, fokus-håndtering, '
             'labels og kontrast i hver widget. Er en app utilgængelig og uundværlig, så '
             'dokumentér den som kendt begrænsning i din tilgængelighedserklæring.'),
        ],
    ),
    # --------------------------------------- Webflow vs Squarespace ---
    dict(
        en_slug='webflow-vs-squarespace-accessibility',
        slug='webflow-vs-squarespace-tilgaengelighed',
        badge='WEBFLOW VS SQUARESPACE &middot; SAMMENLIGNING &middot; EAA',
        title_tag='Webflow vs Squarespace: tilgængelighed sammenlignet (EAA-guide 2026)',
        h1='Webflow vs Squarespace:<br>tilgængelighed sammenlignet',
        desc=('To visuelle byggere, én juridisk forpligtelse under European Accessibility '
              'Act. Hvor hver af dem fejler WCAG 2.1 AA, og hvordan et fix ser ud på '
              'henholdsvis Webflow og Squarespace — på dansk.'),
        subtitle=('Sammenligning for designere og bureauer: Webflow giver element-niveau '
                  'kontrol, Squarespace abstraherer markup bag skabeloner. Se hvor '
                  'defekterne kommer fra, hvem der kan rette dem, og hvad det koster i '
                  'proces.'),
        read='7 minutters læsning',
        intro=('Webflow og Squarespace er begge visuelle website-byggere, og sider på '
               'begge der betjener EU-forbrugere falder under European Accessibility Act: '
               'EN 301 549 / WCAG 2.1 AA conformance, håndhævet nationalt siden midten '
               'af 2025. Loven skelner ikke mellem dem — men byggeoplevelsen gør. Webflow '
               'giver designere lavniveau-kontrol over hvert elements HTML-tag, '
               'ARIA-attributter og custom code. Squarespace abstraherer markuppen bag '
               'skabeloner og sektionsblokke og eksponerer kun kuraterede indstillinger. '
               'Den forskel former både hvor defekterne kommer fra, og hvem der kan rette '
               'dem.'),
        cards=[
            ('⚖️ Samme standard', 'EAA-omfattede tjenester på begge byggere skal opfylde '
             'WCAG 2.1 niveau AA. Regulatorer spørger ikke, hvilket værktøj der lavede '
             'siden.'),
            ('🎛️ Kontinuum af kontrol', 'Webflow eksponerer tags, ARIA og custom code pr. '
             'element; Squarespace eksponerer kuraterede indstillinger. Mere kontrol er '
             'flere måder at rette på — og flere måder at ødelægge på.'),
            ('🔌 Widget-risiko', 'Webflow-interactions/custom embeds og Squarespace '
             'tredjepartsblokke injicerer begge kontroller af varierende '
             'tastaturkvalitet.'),
        ],
        sections=[
            ('Hvor Webflow fejltypisk ses', [
                '<p>Typiske Webflow-defektmønstre:</p>',
                '<p><strong>Div-suppe-struktur:</strong> designerbyggede layouts bruger ofte '
                'div-elementer stylet som overskrifter og knapper — ingen ægte '
                'h1-h6-hierarki, ingen native button-semantik.</p>',
                '<p><strong>Interaction-overload:</strong> hover-only reveals, '
                'scroll-triggerede animationer og klik-triggerede dropdowns, der aldrig '
                'dukker op for tastaturbrugere.</p>',
                '<p><strong>Custom code embeds:</strong> tredjepartsembeds sat ind i '
                'custom-code-felter har deres egne kontrast-, label- og focus-problemer '
                'uden for Webflows tjeks.</p>',
                '<p><strong>Fokus-håndtering:</strong> custom nav-komponenter og modaler '
                'uden fokus-fælder eller synlige fokus-tilstande — typisk i '
                'håndbyggede Designer-projekter.</p>',
            ]),
            ('Hvor Squarespace fejltypisk ses', [
                '<p>Typiske Squarespace-defektmønstre:</p>',
                '<p><strong>Galleri-alt-huller:</strong> billedblokke og gallerier accepterer '
                'tom alt-tekst i tavshed; billedtunge marketingsider sejler rutinemæssigt '
                'uden.</p>',
                '<p><strong>Template-kontrast:</strong> site-style overrides (grå tekst på '
                'tonet baggrund) falder under 4.5:1 mens det ser bevidst ud i '
                'editor-preview.</p>',
                '<p><strong>Sektion-semantik:</strong> drag-genbestilte sektioner giver '
                'overskriftsrækker valgt visuelt; nogle blokker renderer klikbare kort som '
                'divs med JS-handlers.</p>',
                '<p><strong>Mobil-overrides:</strong> styleændringer kun på mobile '
                'breakpoints efterlader desktop-retter ufuldstændige — eller omvendt.</p>',
            ]),
            ('Fix-workflow sammenlignet', [
                '<p>Remedieringsloopet adskiller sig mest i hvem der rører markuppen.</p>',
                '<p><strong>Webflow:</strong> næsten alt kan rettes af designeren — giv rigtige '
                'overskrift-tags, konvertér div-knapper til native buttons, tilføj '
                'ARIA-attributter, omskriv interactions til at være tastatur-triggerede, '
                'justér fokus-tilstande. Intet håndhæves dog automatisk: hver ny interaction '
                'eller embed kræver manuelt tjek.</p>',
                '<p><strong>Squarespace:</strong> retterne er konfiguration — alt-tekstfelter, '
                'overskrift-tildeling hvor blokken tillader det, farve-tokens i site styles, '
                'fjernelse af dekorative autoplay-sektioner. Strukturelle problemer inde i en '
                'specifik blok eller tredjepartsudvidelse kan slet ikke rettes; du bytter '
                'blokken eller dokumenterer begrænsningen i din tilgængelighedserklæring.</p>',
                '<p>Nettoeffekt: Webflow belønner kunnen med fuld remediability men kræver '
                'disciplin; Squarespace når \"rimeligt compliant\" hurtigere men rammer et loft '
                'sat af dens blokke.</p>',
            ]),
            ('Hvad skal du vælge?', [
                '<p>Har du allerede et site: bliv where du er — migrering koster mere end '
                'remediation, og EAA-forpligtelsen er identisk.</p>',
                '<p>Nyt EU-projekt: vælg Webflow når en professionel designer vedligeholder '
                'siden, og du kan håndhæve en tilgængelighedscheckliste i designprocessen — '
                'hver defekt er i sidste ende retbar på elementniveau. Vælg Squarespace til '
                'simple sider vedligeholdt af ikke-designere, og acceptér dokumenterede '
                'begrænsninger hvor blokkene ikke kan rettes.</p>',
                '<p>Uanset hvad er workflowet det samme: automatisk scan hen over nøgle-'
                'templates, ret mekaniske fejl (kontrast, alt-tekst, labels, '
                'overskriftsorden), auditér hver embed eller blok individuelt, publicér en '
                'tilgængelighedserklæring, og scan igen efter meningsfulde ændringer.</p>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan din side gratis'),
              ('/da/blog/eaa-tjekliste-2026', 'EAA-tjekliste')],
        related=[('/da/blog/webflow-tilgaengelighed-eaa', 'Webflow og tilgængelighed'),
                 ('/da/blog/squarespace-tilgaengelighed-eaa', 'Squarespace og tilgængelighed'),
                 ('/da/blog/wcag-kontrast-checker', 'WCAG-kontrast-checker')],
        da_link_text='Webflow vs Squarespace: tilgængelighed sammenlignet',
        faqs=[
            ('Gælder EAA mit Webflow- eller Squarespace-site?',
             'Ja, hvis sitet tilbyder tjenester til EU-forbrugere — fx markedsføring, '
             'booking eller e-handel. Siden juni 2025 håndhæves EN 301 549 / WCAG 2.1 AA '
             'nationalt i hele EU.'),
            ('Hvilken builder er nemmest at gøre compliant?',
             'Afhænger af teamet. Webflow giver fuld mulighed for at rette alt, men kræver '
             'designerkompetence og disciplin. Squarespace når basisniveau hurtigst via '
             'indstillinger, men strukturelle blok-fejl kan ikke rettes — kun dokumenteres.'),
            ('Kan jeg få en Squarespace-blok rettet, som platformen ikke tillader?',
             'Nej, ikke inde i blokken. Dine muligheder er at bytte til en anden blok, løse '
             'problemet udenfor (fx en custom embed du selv kontrollerer) eller dokumentere '
             'det som kendt begrænsning i tilgængelighedserklæringen.'),
        ],
    ),
]


def main():
    m.PAGES[:] = PAGES
    m.main()


if __name__ == '__main__':
    main()
