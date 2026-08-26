#!/usr/bin/env python3
"""Iteration 456: Danish mirrors of the Joomla (BITV 2.0) and Ghost (EAA) guides.

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
    # ------------------------------------------------------------- Joomla ---
    dict(
        en_slug='joomla-bitv-accessibility',
        slug='joomla-tilgaengelighed-bitv',
        badge='JOOMLA &middot; TILGÆNGELIGHED &middot; BITV/EN 301 549',
        title_tag='Joomla og tilgængelighed: mød BITV 2.0 og EN 301 549 (guide 2026)',
        h1='Joomla og tilgængelighed:<br>mød BITV 2.0 og EN 301 549',
        desc=('Gør Joomla-sites compliant med BITV 2.0, EN 301 549 og EAA: '
              'template-overrides, redaktørvaner, extension-audit og en praktisk '
              'test-workflow — trin for trin på dansk.'),
        subtitle=('Template-overrides, redaktørvaner og extension-tjek der bringer et '
                  'Joomla-site op på WCAG 2.1 AA — til tyske offentlige kunder og '
                  'EAA-omfattede virksomheder.'),
        read='7 minutters læsning',
        intro=('Joomla er stadig udbredt i tysk offentlig forvaltning, foreninger og '
               'Mittelstand — målgrupper der er styret af BITV 2.0 i Tyskland og, siden '
               'juni 2025, af European Accessibility Act i hele EU. BITV 2.0 er i praksis '
               'EN 301 549, den europæiske ICT-tilgængelighedsstandard som indarbejder '
               'WCAG 2.1 niveau AA. Et Joomla-site bygget uden en bevidst '
               'tilgængelighedsindsats fejler typisk flere EN 301 549-krav på hver eneste '
               'side — og tyske offentlige kunder kræver i stigende grad en dokumenteret '
               'tilgængelighedserklæring før kontrakten underskrives.'),
        cards=[
            ('🏛️ Offentlige kunder', 'Tyske offentlige organer skal opfylde BITV 2.0. '
             'Bureauer der betjener dem skal kunne vise dokumenteret conformance — ikke '
             'blive gode intentioner.'),
            ('📜 BFSG for private', 'Private tjenester falder under BFSG — den tyske '
             'implementering af EAA. Samme tekniske standard, bare en anden juridisk vej.'),
            ('🧱 Template-arv', 'De fleste Joomla-sider kører tungt tilpassede efterkommere '
             'af gamle Protostar-baserede templates — ti år gamle markup-mønstre replikeres '
             'på tværs af hele sitet.'),
        ],
        sections=[
            ('Hvor Joomla-sider fejler', [
                '<div class="problem-cards">'
                '<div class="card"><h3>📝 Redaktørindhold</h3><p>Manglende alt-tekst er den '
                'hyppigste defekt — Joomla gennemtvinger ikke alt-feltet på medier. Andet: '
                'overskrifter indsat fra Word som visuel formatering i stedet for rigtige '
                'h2/h3-elementer.</p></div>'
                '<div class="card"><h3>🧩 Templates &amp; overrides</h3><p>Gamle templates '
                'springer landmark-elementer over, renderer ikonknapper uden aria-labels og '
                'gentager identiske "læs mere"-linktekster på alle artikelteasers.</p></div>'
                '<div class="card"><h3>🔌 Extensions</h3><p>Formularer, gallerier, sliders og '
                'forum-extensions renderer egen markup med varierende kvalitet — hver skal '
                'auditeres enkeltvis.</p></div>'
                '</div>',
            ]),
            ('Redaktør- og konfigurationsretter', [
                '<p>Disse retter kræver ingen udvikler og dækker meget af fejlvolume:</p>',
                '<p><strong>1. Alt-tekst-disciplin.</strong> Træn redaktører: informative billeder '
                'får beskrivende alt-tekst, dekorative får eksplicit tom alt="". Joomlas '
                'mediehåndtering tillader begge — den kræver dem bare ikke.</p>',
                '<p><strong>2. Semantiske overskrifter.</strong> Begræns editorens tilladte formater '
                'så artikler bruger rigtige Overskrift 2/3-typografier, ikke fed paragraph-tekst. '
                'Tjek at artikelvisningens template override renderer titler som ægte '
                'heading-elementer.</p>',
                '<p><strong>3. Meningsfulde "Læs mere"-links.</strong> Konfigurér den globale '
                'Read More-tekst til at inkludere artikeltitlen ("Læs mere: {titel}") — gentagne '
                'identiske links fejler WCAG 2.4.4 og ødelægger skærmlæserens linkliste.</p>',
                '<p><strong>4. Sprogattributter.</strong> Sæt contentsproget korrekt pr. site/'
                'flersproget association så html lang matcher siden. Det mapper direkte til '
                'EN 301 549 klausul 9.3.1.</p>',
                '<p><strong>5. Formularer.</strong> Hvert felt skal have et programmatisk knyttet '
                'label — verificér at din formularextension renderer rigtige label-elementer, '
                'ikke kun placeholder-felter.</p>',
            ]),
            ('Template- og extension-retter', [
                '<p>Udviklerarbejde, én gang pr. projekt og genbrugt overalt:</p>',
                '<p><strong>Modernisér basen:</strong> ligger templaten stadig på Protostar-era-markup, '
                'så migrér til en aktuel bootstrap-baseret eller custom template med rigtige '
                'landmarks (header, nav, main, footer).</p>',
                '<p><strong>Skip-link og fokus:</strong> et synligt "spring til indhold"-link som det '
                'første fokuserbare element; fjern aldrig outlines globalt — style :focus-visible '
                'i stedet.</p>',
                '<p><strong>Tastaturbetjening:</strong> tab dig igennem menuer, accordions, sliders '
                'og lightboxes. Alt der kun kan betjenes med mus er en fejl under EN 301 549.</p>',
                '<p><strong>Extension-audit:</strong> test hver tredjepartsextensions widgets '
                'enkeltvis; udskift eller pakk dem der fejler, i stedet for at skibe kendt '
                'defekte komponenter.</p>',
                '<p><strong>Kontrast og dokumenter:</strong> verificér temafarver mod 4,5:1 minimum '
                'for brødtekst, og behandl downloadbare PDF\'er som omfang — taggede, læsbare '
                'PDF\'er eller tilgængelige HTML-alternativer.</p>',
            ]),
            ('Test og dokumentation', [
                '<p>En realistisk verifikationsloop for et Joomla-projekt tager en eftermiddag:</p>',
                '<p><strong>Trin 1 — automatisk scanning</strong> af centrale sidetyper (forside, '
                'artikel, kontaktformular, kategoriliste). Den fanger kontrastfejl, manglende '
                'lang, brudt overskriftsorden, tomme knapper og duplikerede IDs på minutter.</p>',
                '<p><strong>Trin 2 — keyboard-gennemgang.</strong> Tag musen fra bordet og navigér '
                'alle flows en bruger ville. Notér alt der er utilgængeligt, fanget eller uden '
                'synligt fokus.</p>',
                '<p><strong>Trin 3 — skærmlæser-spotcheck</strong> af én repræsentativ rejse med '
                'NVDA — lyt efter unlabellede kontroller og forvirrende struktur, lav ikke en fuld '
                'audit.</p>',
                '<p><strong>Trin 4 — dokumentér.</strong> Publicér en tilgængelighedserklæring med '
                'conformance-status, kendte begrænsninger og feedbackkanal. BITV-offentlige kunder '
                'forventer den; BFSG kræver den for private tjenester i omfang.</p>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan dit Joomla-site gratis'),
              ('/da/blog/eaa-tjekliste-2026', 'EAA-tjekliste')],
        related=[('/da/blog/drupal-tilgaengelighed-eaa', 'Drupal og tilgængelighed'),
                 ('/da/blog/wcag-22-aendringer', 'WCAG 2.2-ændringer'),
                 ('/da/blog/skriv-tilgaengelighedserklaering', 'Skriv en tilgængelighedserklæring')],
        da_link_text='Joomla og tilgængelighed: mød BITV 2.0 og EN 301 549',
        faqs=[
            ('Gælder BITV 2.0 min kommercielle kunde?',
             'BITV 2.0 binder tyske offentlige organer. Private virksomheder falder under '
             'Barrierefreiheitsstärkungsgesetz (BFSG), som implementerer EAA — men begge '
             'refererer EN 301 549 / WCAG-baserede krav, så det samme tekniske arbejde '
             'tilfredsstiller begge rammer.'),
            ('Er Joomla selv tilgængeligt?',
             'Joomla-kernen er markant forbedret, og CMS\'et leverer værktøjerne (semantisk '
             'rendering, flersprogede associationer, mediemetadata). Faktisk compliance afhænger '
             'næsten helt af den enkelte template, extensionsættet og den redaktionelle praksis.'),
            ('Hvilken WCAG-version bør vi sigte efter?',
             'EN 301 549 refererer i øjeblikket WCAG 2.1 niveau AA. At bygge mod WCAG 2.2 AA giver '
             'luft — tilføjelserne handler mest om fokus-udseende, alternativer til træk og '
             'konsekvent hjælp.'),
            ('Vi bruger en populær forms-extension — er vi fine?',
             'Ikke automatisk. Flere udbredte formular-extensions renderer felter med kun '
             'placeholder eller custom selects uden tastaturstøtte. Auditér den præcise installerede '
             'versions renderede markup på staging.'),
            ('Hvor lang tid tager Joomla-udbedring?',
             'For et typisk 20-50 siders site på en vedligeholdt template: 2-5 arbejdsdage til '
             'mekaniske retter plus redaktørtræning. Sites stadig på Protostar-era-templates tager '
             'længere — templatemigreringen dominerer.'),
        ],
    ),

    # -------------------------------------------------------------- Ghost ---
    dict(
        en_slug='ghost-eaa-accessibility',
        slug='ghost-tilgaengelighed-eaa',
        badge='GHOST &middot; TILGÆNGELIGHED &middot; EAA/WCAG 2.2',
        title_tag='Ghost og tilgængelighed: gør publikationer EAA-compliant (2026)',
        h1='Ghost og tilgængelighed:<br>gør publikationer EAA-compliant',
        desc=('Gør Ghost-publikationer compliant med European Accessibility Act og '
              'WCAG 2.2 AA: tema-retter, Koenig-indholdsvaner, medlemsflows og en '
              'gratis scannings-workflow — på dansk.'),
        subtitle=('Tema-retter, indholdsvaner og tjek af medlemsflows der bringer et '
                  'Ghost-site op på WCAG 2.2 AA — uden at bygge det forfra.'),
        read='6 minutters læsning',
        intro=('Ghost driver nyhedsbreve, betalte publikationer og medlemskabsbaserede sites — '
               'netop de kommersielle forbrugertjenester European Accessibility Act dækker. '
               'Siden 28 juni 2025 skal e-handelslignende tjenester og forbrugervendte digitale '
               'tjenester være opfattelige, betjenelige, forståelige og robuste — de fire '
               'WCAG-principper. For en Ghost-udgiver betyder det at temaet, artikelindholdet '
               'og især tilmeldings- og checkout-flowene alle har brug for opmærksomhed. Den '
               'gode nyhed: et moderne Ghost-setup har færre bevægelige dele end de fleste '
               'platforme, så WCAG 2.2 AA er reelt opnåeligt.'),
        cards=[
            ('🎨 Temaet først', 'De fleste Ghost-problemer bor i temaet, ikke kernen: kontrast, '
             'fokus-tilstande og baggrundsbilleder uden alt-tekst.'),
            ('✍️ Koenig er ren — men ikke sikker', 'Editoren producerer pæn HTML som default, men '
             'den gennemtvinger ikke alt-tekst eller overskriftsdisciplin. Redaktionelle regler '
             'fylder hullet.'),
            ('💳 Medlemsflowene tæller', 'Under EAA er en betalingsflow som assistive technology-'
             'brugere ikke kan gennemføre et compliance-svigt — ikke bare et WCAG-nitpick.'),
        ],
        sections=[
            ('Tema-niveau tjek', [
                '<div class="problem-cards">'
                '<div class="card"><h3>🎨 Farvekontrast</h3><p>Mange magasin-temaer bruger lysegrå '
                'tekst på hvid eller tekst oven på gradient-hero-billeder. Brødtekst kræver 4,5:1; '
                'store overskrifter 3:1; input og ikoner 3:1. Ret én gang i temaets CSS eller '
                'custom-indstillinger — gavn alle steder.</p></div>'
                '<div class="card"><h3>⌨️ Tastatur &amp; fokus</h3><p>Tab dig igennem header-navigation, '
                'post-kort og member-portalen. Dropdowns og kort-overlays er de sædvanlige fælder. '
                'Sørg for synlige :focus-visible-styles.</p></div>'
                '<div class="card"><h3>🖼️ Billeder &amp; kort</h3><p>Post-thumbnails renderet som '
                'background-image-divs bærer ingen alt-tekst. Foretræk img-elementer fødet fra postens '
                'feature-billede med meningsfuld alt-tekst arvet fra indlægget.</p></div>'
                '<div class="card"><h3>🔤 Typografi &amp; zoom</h3><p>Verificér at layoutet overlever '
                '200 % browser-zoom og 320 px bredde uden vandret scrolling (WCAG 1.4.10). Fluid '
                'type-systemer klarer det; gamle bryder sammen.</p></div>'
                '<div class="card"><h3>🧭 Struktur</h3><p>Én h1 pr. side (post-titlen), rigtig '
                'overskriftsorden i artikler, landmarks i temaets default-layout.</p></div>'
                '</div>',
            ]),
            ('Koenig-indholdsvaner', [
                '<p>Ghost\'s Koenig-editor producerer ren HTML som standard — bedre end de fleste '
                'rich-text-editorer — men forfattere kan stadig lave utilgængeligt indhold:</p>',
                '<p><strong>Alt-tekst:</strong> billedkortet foreslår alt-tekst men ingen bliver tvunget '
                'til at udfylde det. Gør det til en redaktionel regel: ethvert informativt billede får '
                'beskrivende alt; dekorative markeres eksplicit som sådan.</p>',
                '<p><strong>Embeds:</strong> YouTube-, Twitter/X- og andre embed-korte injicerer iframes '
                'du ikke styrer. Giv hvert embed en forudgående sætning der beskriver hvad læseren '
                'vil se/høre, da iframe-indhold er uigennemsigtigt for din egen markup.</p>',
                '<p><strong>Overskriftsdisciplin:</strong> forfattere fra Word bruger fed tekst i stedet '
                'for overskrifter. Skærmlæserebrugere navigerer via overskriftslister — en artikel uden '
                'rigtige h2\'er er unavigérbar.</p>',
                '<p><strong>Linktekst:</strong> undgå nøgne "her" og "denne artikel". Linktekst skal '
                'holde til at blive læst uden kontekst.</p>',
                '<p><strong>Gallerier:</strong> sørg for at hvert galleribillede har egen alt-tekst — '
                'ikke bare en samlet caption.</p>',
            ]),
            ('Medlemsflows', [
                '<p>Dette er delen der er unik for Ghost, og let at gå glip af. Tilmelding, login, '
                'checkout og kontostyring er brugerrejser, og under EAA er en betalingsrejse som '
                'assistive technology-brugere ikke kan gennemføre et compliance-svigt. Tjek at:</p>',
                '<p>e-mail-input og fejlbeskeder er korrekt labelde og annonceret (fejltekst knyttet '
                'til feltet via aria-describedby); Stripe-checkout\'en Ghost sender videre til er '
                'konfigureret med tilgængelige branding-indstillinger; magic-link-mails har '
                'meningsfuld linktekst ("Åbn dit login-link" — ikke "Klik her"); og member-portalen '
                'er brugbar med tastatur alene. Test hele rejsen selv med en skærmlæser én gang — det '
                'tager tyve minutter og afslører mere end noget automatisk værktøj.</p>',
            ]),
            ('Verifikationsloop', [
                '<p>En gentagelig QA-loop for et Ghost-site:</p>',
                '<p><strong>1. Automatisk scanning</strong> af forside, en tag-side, en komplet artikel, '
                '/#/portal og tilmelingssiderne. Statiska scannere fanger det mekaniske lag hurtigt — '
                'forvent kontrast-, alt-tekst- og overskriftsfund ved første kørsel.</p>',
                '<p><strong>2. Keyboard-pass</strong> gennem navigation, post-liste, artikel, kommentarer '
                '(hvis slået til) og hele tilmelding-til-checkout-rejsen.</p>',
                '<p><strong>3. Skærmlæser-sample:</strong> én artikel start-til-slut med VoiceOver eller '
                'NVDA, plus tilmeldingsflowet.</p>',
                '<p><strong>4. Erklæring:</strong> publicér en tilgængelighedserklæring med '
                'conformance-status, kendte begrænsninger og kontaktkanal. Kommercielle udgivere i '
                'EAA-omfang bør have den synlig fra footeren.</p>',
                '<p><strong>5. Regressionsvane:</strong> kør den automatiske scanning igen efter hver '
                'tema-opdatering eller ny udgivelse — temaer ændres oftere end folk tror, og '
                'regressioner er lydløse.</p>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan dit Ghost-site gratis'),
              ('/da/blog/eaa-tjekliste-2026', 'EAA-tjekliste')],
        related=[('/da/blog/wcag-22-aendringer', 'WCAG 2.2-ændringer'),
                 ('/da/blog/tilgaengeligheds-overlays-eaa', 'Overlays og EAA'),
                 ('/da/blog/eaa-haandhaevelse-2026', 'EAA-håndhævelse i 2026')],
        da_link_text='Ghost og tilgængelighed: gør publikationer EAA-compliant',
        faqs=[
            ('Gælder EAA virkelig nyhedsbreve og blogs?',
             'Hvis tjenesten er forbrugervendt og kommerciel — betalte abonnementer, e-handel med '
             'digitale produkter — ja. Gratis personlige blogs falder som regel uden for EAA, men '
             'WCAG-compliant publicering koster lidt og beskytter rækkevidde; der er sjældent en '
             'grund til ikke at rette basen.'),
            ('Er Ghost selv tilgængeligt ud af boksen?',
             'Ghost-kernen er rimeligt solid: ren HTML-output, labelde portal-komponenter, fornuftige '
             'defaults. De dominerende defektkilder er tredjepartstemаer og forfatteres indholdsvaner — '
             'derfor betyder tema-gennemgang og redaktionelle regler mere end platformvalget.'),
            ('Mit tema har ingen fokus-styles. Quick fix?',
             'Ja — tilføj :focus-visible { outline: 2px solid currentColor; outline-offset: 3px; } '
             'under Code Injection. Det respekterer temapaletten og genskaber synligt tastaturfokus '
             'hele sitet i én linje.'),
            ('Kan jeg automatisere Ghost-tilgængelighedstjek?',
             'Delvist. Automatiske værktøjer fanger cirka 30-50 % af problemerne — kontrast, manglende '
             'alt, struktur, labels. Tastaturbetjening, meningsfulde alt-beskrivelser og embed-'
             'tilgængelighed kræver menneskelig gennemgang. Kombinér: scan automatisk efter hver '
             'temaændring, gennemgå manuelt pr. udgivelse.'),
            ('Hjælper tilgængelighed SEO?',
             'Flere tilgængelighedssignaler overlapper SEO: rigtig overskriftshierarki, beskrivende '
             'linktekst, alt-tekst, hurtig semantisk HTML, mobilvenlige layouts. Tilgængelighedsarbejde '
             'forbedrer typisk crawlbarhed og placering som sideeffekt — men det bør gøres for '
             'brugerne først.'),
        ],
    ),
]


def main():
    m.PAGES = PAGES
    m.main()


if __name__ == '__main__':
    main()
