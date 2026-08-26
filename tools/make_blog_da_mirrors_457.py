#!/usr/bin/env python3
"""Iteration 457: Danish mirrors of the TYPO3 (BITV) and WordPress-vs-Wix guides.

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
    # -------------------------------------------------------------- TYPO3 ---
    dict(
        en_slug='typo3-accessibility-bitv-check',
        slug='typo3-tilgaengelighed-bitv',
        badge='TYPO3 &middot; TILGÆNGELIGHED &middot; BITV/EN 301 549',
        title_tag='TYPO3 og tilgængelighed: mød BITV 2.0 og EN 301 549 (guide 2026)',
        h1='TYPO3 og tilgængelighed:<br>mød BITV 2.0 og EN 301 549',
        desc=('Gør TYPO3-sites compliant med BITV 2.0, EN 301 549 og EAA: '
              'redaktørvaner, TypoScript- og Fluid-retter, extension-audit og en '
              'praktisk test-workflow — trin for trin på dansk.'),
        subtitle=('Redaktør-, template- og tekniske retter der bringer et TYPO3-site '
                  'op på WCAG 2.1 AA — til tyske offentlige kunder og '
                  'EAA-omfattede virksomheder.'),
        read='7 minutters læsning',
        intro=('TYPO3 er tungt udbredt i tysktalende offentlig forvaltning, og det '
               'ændrer hvad "tilgængelig" betyder for dig som bureau. Tyske '
               'offentlige organer skal opfylde BITV 2.0, som reelt er EN 301 549 — '
               'den europæiske ICT-tilgængelighedsstandard der indarbejder WCAG 2.1 '
               'niveau AA. Siden 28. juni 2025 udvider European Accessibility Act '
               'lignende krav til privat e-handel og banktjenester i hele EU. Et '
               'TYPO3-site bygget uden en bevidst tilgængelighedsindsats fejler '
               'typisk flere EN 301 549-krav på hver eneste side — og offentlige '
               'kunder forlanger i stigende grad en dokumenteret '
               'tilgængelighedserklæring før kontrakten underskrives.'),
        cards=[
            ('🏛️ Offentlige kunder', 'Tyske offentlige organer skal opfylde BITV 2.0. '
             'Bureauer der betjener dem skal kunne vise dokumenteret conformance — ikke '
             'gode intentioner.'),
            ('📜 BFSG for private', 'Private tjenester falder under BFSG — den tyske '
             'implementering af EAA. Samme tekniske standard, bare en anden juridisk vej.'),
            ('🧩 Tre fejlkilder', 'Størstedelen af defekterne kommer fra redaktørindhold, '
             'template-markup (Fluid/TypoScript) og extensions — hver skal håndteres '
             'for sig.'),
        ],
        sections=[
            ('Hvor TYPO3-sider fejler', [
                '<div class="problem-cards">'
                '<div class="card"><h3>📝 Redaktørindhold</h3><p>Manglende alt-tekst på '
                'uploadede billeder er den hyppigste defekt — TYPO3 gennemtvinger ikke '
                'alt-attributter på FAL-filreferencer, så redaktører springer dem rutinemæssigt '
                'over. Andenpladsen: overskriftsstruktur indsat fra Word som visuel formatering '
                'i stedet for rigtige h2/h3-elementer.</p></div>'
                '<div class="card"><h3>🧩 Templates &amp; TypoScript</h3><p>Custom Fluid-templates '
                'hardcoder ofte linktekster som "læs mere" gentaget på tværs af siden, dropper '
                'lang-attributten eller renderer ikonknapper uden aria-labels. Basistemplates '
                'skippet for år siden er ældre end gældende standarder.</p></div>'
                '<div class="card"><h3>🔌 Extensions</h3><p>Tredjeparts-plugins (formularer, '
                'sliders, lightboxes) injicerer ofte ikke-semantisk markup, keyboard-fælder eller '
                'manglende fokus-tilstande. Hver extension på sitet skal have sin egen '
                'tilgængelighedsgennemgang.</p></div>'
                '</div>',
            ]),
            ('Redaktørniveau — retter uden udvikler', [
                '<p>Disse retter kræver ingen udvikler og dækker det meste af fejlvolumenet:</p>',
                '<p><strong>1. Gør alt-tekst obligatorisk i praksis.</strong> Tilret workflowet omkring '
                'billedindholdselementet så redaktører skal udfylde alternativtekst-feltet. For rent '
                'dekorative billeder er eksplicit tom alt="" korrekt — træn forskellen på dekorative '
                'og informative billeder.</p>',
                '<p><strong>2. Gennemtving semantiske overskrifter.</strong> Begræns de header-layout-'
                'valg redaktører kan vælge, så de bruger rigtige h2/h3 frem for stylet tekst. Tjek at '
                'Fluid-templates renderer sektionsoverskrifter som ægte heading-elementer, ikke divs.</p>',
                '<p><strong>3. Skriv meningsfulde linktekster.</strong> "Mere", "her" og gentagne '
                'identiske links til forskellige mål fejler WCAG 2.4.4 og er fjendtlige overfor '
                'skærmlæserbrugere der navigerer via linkliste. Retningslinje: linkteksten skal '
                'beskrive målet, også læst uden kontekst.</p>',
                '<p><strong>4. Sprogattributter.</strong> Sæt sitesproget korrekt pr. sidetræ '
                '(TypoScript config.language / htmlTag_langKey eller site-konfiguration), og marker '
                'fremmedsprogede ord inline hvor det er praktisk. Det mapper direkte til EN 301 549 '
                'klausul 9.3.1.</p>',
                '<p><strong>5. Formularer.</strong> Hvert input behøver en programmatisk knyttet '
                'label — ikke placeholder-tekst. Bruger I en formularextension, så verificér dens '
                'output-markup; mange genererer felter uden labels som default.</p>',
            ]),
            ('Template- og tekniske retter', [
                '<p>Udviklersiden — arbejd listen igennem én gang pr. projekt og genbrug '
                'tjeklisten overalt:</p>',
                '<p><strong>Skip-links:</strong> et synligt "spring til indhold"-link som det første '
                'fokuserbare element.</p>',
                '<p><strong>Fokus-synlighed:</strong> fjern aldrig outline globalt; style '
                ':focus-visible i stedet.</p>',
                '<p><strong>Kontrast:</strong> verificér temafarver mod 4,5:1 for brødtekst og 3:1 '
                'for stor tekst og UI-komponenter.</p>',
                '<p><strong>Tastaturbetjening:</strong> tab igennem alle interaktive komponenter — '
                'menuer, accordions, sliders, lightboxes. Alt der kun kan betjenes med mus er en '
                'fejl.</p>',
                '<p><strong>ARIA-disciplin:</strong> foretræk native HTML-elementer frem for '
                'ARIA-patches. En ægte knap slår en div med role="button".</p>',
                '<p><strong>PDF-dokumenter:</strong> downloadbare PDF\'er tæller også under EN 301 549 '
                '— taggede, læsbare PDF\'er eller tilgængelige HTML-alternativer.</p>',
            ]),
            ('Test-workflow', [
                '<p>En realistisk verifikationsloop for et TYPO3-projekt tager en eftermiddag:</p>',
                '<p><strong>Trin 1 — automatisk scanning</strong> af nøglesidetyper (forside, artikel, '
                'formular, søgeresultater) med en statisk HTML-scanner. Den fanger kontrastfejl, '
                'manglende lang, brudt overskriftsorden, tomme knapper og duplikerede IDs — groft '
                'regnet 30-50 % af de typiske problemer på minutter.</p>',
                '<p><strong>Trin 2 — keyboard-gennemgang.</strong> Tag musen fra bordet og navigér alle '
                'flows en bruger ville. Notér alt der er utilgængeligt, fanget eller uden synligt '
                'fokus.</p>',
                '<p><strong>Trin 3 — skærmlæser-spotcheck</strong> af ét repræsentativt flow med NVDA '
                'eller VoiceOver. Du lytter efter unlabellede kontroller og forvirrende struktur — '
                'lav ikke en fuld audit.</p>',
                '<p><strong>Trin 4 — dokumentér.</strong> Publicér en tilgængelighedserklæring med '
                'conformance-status, kendte begrænsninger og feedbackkanal. Offentlige kunder i '
                'Tyskland forventer den; under EAA skal private tjenester i omfang også levere en.</p>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan dit TYPO3-site gratis'),
              ('/da/blog/eaa-tjekliste-2026', 'EAA-tjekliste')],
        related=[('/da/blog/joomla-tilgaengelighed-bitv', 'Joomla og tilgængelighed'),
                 ('/da/blog/wcag-22-aendringer', 'WCAG 2.2-ændringer'),
                 ('/da/blog/skriv-tilgaengelighedserklaering', 'Skriv en tilgængelighedserklæring')],
        da_link_text='TYPO3 og tilgængelighed: mød BITV 2.0 og EN 301 549',
        faqs=[
            ('Gælder BITV 2.0 min kommercielle kunde?',
             'BITV 2.0 binder tyske offentlige organer. Private virksomheder falder under '
             'Barrierefreiheitsstärkungsgesetz (BFSG), som implementerer EAA — men begge '
             'refererer EN 301 549 / WCAG-baserede krav, så det samme tekniske arbejde '
             'tilfredsstiller begge rammer.'),
            ('Er TYPO3 selv tilgængeligt?',
             'TYPO3-kernens backend har fået markante tilgængelhedsforbedringer i nyere '
             'versioner, og CMS\'et leverer værktøjerne (semantisk rendering, sproghåndtering, '
             'FAL-metadata). Reelt compliance afhænger næsten helt af templaten, '
             'extensionsættet og den redaktionelle praksis på det enkelte site.'),
            ('Hvilken WCAG-version bør vi sigte efter?',
             'EN 301 549 refererer i øjeblikket WCAG 2.1 niveau AA. At bygge mod WCAG 2.2 AA '
             'giver luft — tilføjelserne handler mest om fokus-udseende, alternativer til '
             'træk og konsekvent hjælp.'),
            ('Skal vi have en certificeret audit?',
             'Offentlige kunder kræver typisk en selvproduceret, dokumenteret vurdering plus '
             'tilgængelighedserklæring; nogle udbudsprocesser beder om uafhængige audits. En '
             'automatisk scanning plus manuel tastatur-/skærmlæsertest er accepteret minimum '
             'som intern standard.'),
            ('Hvor lang tid tager TYPO3-udbedring?',
             'For et typisk 20-50 siders site på en vedligeholdt template: 2-5 arbejdsdage til '
             'mekaniske retter plus redaktøruddannelse. Sider på gamle custom-templates eller '
             'med tunge tredjepartsextensions tager længere — template-refaktoreringen '
             'dominerer som regel.'),
        ],
    ),

    # ------------------------------------------------- WordPress vs Wix ----
    dict(
        en_slug='wordpress-vs-wix-accessibility',
        slug='wordpress-vs-wix-tilgaengelighed',
        badge='SAMMENLIGNING &middot; WORDPRESS VS WIX &middot; EAA',
        title_tag='WordPress vs Wix og tilgængelighed: hvor hver platform fejler (2026)',
        h1='WordPress vs Wix:<br>tilgængelighed sammenlignet',
        desc=('Begge platforme driver millioner af EU-sider under European Accessibility '
              'Act. Hvor WordPress og Wix fejler WCAG 2.1 AA — og hvordan udbedringen '
              'ser ud på hver — på dansk.'),
        subtitle=('Samme juridiske krav, to helt forskellige arkitekturer: hvor '
                  'WordPress- og Wix-sider fejler WCAG 2.1 AA, og hvilken '
                  'remediation-workflow der passer til hver.'),
        read='7 minutters læsning',
        intro=('WordPress driver cirka fire gange flere websites end Wix, og begge '
               'publikummer er nu underlagt European Accessibility Act, når de tilbyder '
               'tjenester til EU-forbrugere. Juridisk er de identiske: EN 301 549 / '
               'WCAG 2.1 AA-conformance, håndhævet nationalt siden midten af 2025. '
               'Arkitektonisk kunne de ikke være mere forskellige. WordPress er '
               'open source-software du hoster selv, temaet og udvidet fra et enormt '
               'plugin-økosystem. Wix er en hosted website builder hvor visuel '
               'redigering skriver markeringen for dig. De to modeller giver '
               'markant forskellige tilgængeligheds-fejlmønstre — og markant '
               'forskellige rette-workflows.'),
        cards=[
            ('⚖️ Samme pligt', 'EAA-omfattede tjenester på begge platforme skal møde '
             'WCAG 2.1 niveau AA. Håndhævelsesmyndigheder er ligeglade med hvilket CMS '
             'renderer dine sider.'),
            ('🔓 Åben vs hosted', 'WordPress giver fuld kontrol over hver byte HTML — '
             'inklusive magten til at ødelægge den. Wix begrænser hvad du kan ændre, '
             'til gavn og besvær.'),
            ('🧩 Extension-risiko', 'WordPress-plugins og Wix-apps injicerer begge '
             'widgets af ukendt kvalitet. Formularer, sliders og popups er de værste '
             'syndere på begge.'),
        ],
        sections=[
            ('Hvor WordPress fejler', [
                '<div class="problem-cards">'
                '<div class="card"><h3>📝 Redaktørindhold</h3><p>Manglende alt-tekst '
                '(media-uploaderen tillader tomt alt), overskrifter indsat som fed tekst og '
                'linktekster som "klik her" skrevet direkte i block-editoren.</p></div>'
                '<div class="card"><h3>🧩 Plugin-widgets</h3><p>Form-builders, page-builder-blokke '
                'og slider-plugins med placeholder-only felter, div-baserede "knapper" og '
                'keyboard-fælder.</p></div>'
                '<div class="card"><h3>🎨 tema-arv</h3><p>Custom themes og page-builder-layouts '
                'der springer landmarks over, fjerner fokus-outlines eller gentager identiske '
                '"læs mere"-links i arkiv-loops.</p></div>'
                '<div class="card"><h3>🔄 Opdaterings-regressioner</h3><p>Plugin- og temaopdateringer '
                'genintroducerer lydløst rettede fejl — tilgængelighed behøver en fast plads i '
                'opdateringsrutinen.</p></div>'
                '</div>',
            ]),
            ('Hvor Wix fejler', [
                '<div class="problem-cards">'
                '<div class="card"><h3>🎨 Visuelle defaults</h3><p>Truk-positionerede tekstbokse giver '
                'overskriftsniveauer valgt efter udseende, ikke struktur — flere manglende eller '
                'forkert ordnede overskrifter pr. side.</p></div>'
                '<div class="card"><h3>🖼️ Alt-tekst-huller</h3><p>Wix foreslår alt-tekst men kræver den '
                'ikke; gallerier importeret fra fotos skibes rutinemæssigt tomme.</p></div>'
                '<div class="card"><h3>📱 Mobil-layout-duplikering</h3><p>Den separate mobileditor lader '
                'rettelser fra desktop overse mobil-viewet helt — en klassisk kilde til "rettet men '
                'fejler stadig".</p></div>'
                '<div class="card"><h3>🔌 Tredjeparts-apps</h3><p>Formular-, chat- og booking-apps '
                'injicerer iframes og custom kontroller med inkonsistent tastaturstøtte.</p></div>'
                '</div>',
            ]),
            ('Ret-workflow sammenlignet', [
                '<p>Forskellen er igen kontrol:</p>',
                '<p><strong>WordPress:</strong> næsten alt kan rettes — redaktøruddannelse dækker '
                'indholdsproblemer, tema-/child-theme-arbejde dækker strukturelle, og ødelagte plugins '
                'kan udskiftes fra tusindvis af alternativer. Prisen er at intet gennemtvinger sig '
                'selv: hvert nyt plugin, temaopdatering og ny redaktør kan rulle fremskridtet tilbage, '
                'så scanning hører hjemme i vedligeholdelsesrutinen.</p>',
                '<p><strong>Wix:</strong> mange retter er konfiguration frem for kode — alt-tekst-felter, '
                'semantisk overskriftstildeling i SEO-/tilgængelighedsindstillingerne, kontrastjustering '
                'i site styles og aktivering af ren tekst-rendering på mobil. Strukturelle grænser (hvordan '
                'en given app renderer sin widget) kan slet ikke rettes; du vælger en anden app eller '
                'dokumenterer begrænsningen.</p>',
                '<p>Nettoeffekt: WordPress belønner investering med fuld retbarhed men kræver løbende '
                'årvågenhed; Wix når "rimeligt compliant" hurtigere for simple sider men rammer et loft '
                'sat af builderen og appsene.</p>',
            ]),
            ('Hvad skal du vælge', [
                '<p>Eksisterer siden allerede på en af platformene, bliv dér — migrationsomkostningerne '
                'overstiger udbedringen, og EAA-pligterne er identiske. Vælger du til et nyt EU-projekt:</p>',
                '<p>Vælg <strong>WordPress</strong> når du har (eller kan hyre) en der er tryg ved at '
                'vedligeholde themes og plugins — hver tilgængelighedsdefekt er i sidste ende retbar. '
                'Vælg <strong>Wix</strong> til simple brochure-agtige sider vedligeholdt af ikke-tekniske '
                'ejere, og acceptér at enkelte tredjeparts-widgets kan være uretbare og skal dokumenteres.</p>',
                '<p>Uanset hvad er workflowet det samme: automatisk scanning på tværs af nøgle-templates, '
                'ret mekaniske fejl (kontrast, alt-tekst, labels, overskriftsorden), auditér hver extension '
                'enkeltvis, publicér en tilgængelighedserklæring, og genscan ved hver meningsfuld ændring.</p>',
                '<div class="problem-cards">'
                '<div class="card"><h3>✅ Begge kan comply\'e</h3><p>Fuldt conformante sider findes på begge '
                'platforme. Proceskvalitet slår platformvalg.</p></div>'
                '<div class="card"><h3>🚀 Start med en scanning</h3><p>En automatisk scanning skiller '
                'rette-i-dag-problemer fra arkitektoniske på minutter — på ethvert CMS.</p></div>'
                '<div class="card"><h3>📄 Erklæring påkrævet</h3><p>EAA-omfattede virksomheder bør '
                'publicere en tilgængelighedserklæring med conformance-status og dokumenterede '
                'begrænsninger.</p></div>'
                '</div>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan din side gratis'),
              ('/da/blog/eaa-tjekliste-2026', 'EAA-tjekliste')],
        related=[('/da/blog/wix-tilgaengelighed-eaa', 'Wix og tilgængelighed'),
                 ('/da/blog/drupal-tilgaengelighed-eaa', 'Drupal og tilgængelighed'),
                 ('/da/blog/wcag-22-aendringer', 'WCAG 2.2-ændringer')],
        da_link_text='WordPress vs Wix: tilgængelighed sammenlignet',
        faqs=[
            ('Gælder EAA forskelligt for WordPress- og Wix-sider?',
             'Nej. Loven regulerer tjenesten der tilbydes forbrugeren, ikke '
             'publiceringsplatformen. En WordPress-side og en Wix-side der tilbyder samme '
             'tjeneste står overfor de samme WCAG 2.1 AA-krav.'),
            ('Er WordPress mere tilgængeligt end Wix ud af boksen?',
             'Ingen af dem er conformant som default når rigtigt indhold, temas og extensions '
             'kommer i bildet. WordPress-kernens defaults er solide, men plugin-økosystemet er '
             'jokeren; Wix begrænser dårlig markup men dens visuelle redigering skaber '
             'strukturelle overskriftsproblemer.'),
            ('Kan jeg rette tilgængelighedsproblemer i Wix uden udvikler?',
             'Meget af det, ja: alt-tekst-felter, overskriftstildeling, farvekontrast i site '
             'styles og linkbeskrivelser er ejerniveau-indstillinger. Problemer inde i '
             'tredjeparts-apps kræver som regel app-udskiftning eller dokumenterede '
             'begrænsninger.'),
            ('Hvad er den største enkeltstående WordPress-tilgængelighedsrisiko?',
             'Uadministrerede plugins. Hvert ekstra formular-, slider- eller page-builder-plugin '
             'øger defektfladen, og opdateringer kan lydløst genintroducere rettede fejl. Hold '
             'plugin-antallet lavt og scan efter hver opdateringsrunde.'),
            ('Hvor lang tid tager udbedring på hver platform?',
             'Et typisk 20-50 siders site: dage til mekaniske retter på begge. WordPress-sider '
             'tunge på page-builders og plugins kan tage uger; Wix-sider bliver normalt hurtigere '
             'færdige men kan bære dokumenterede begrænsninger for specifikke apps.'),
        ],
    ),
]


def main():
    m.PAGES = PAGES
    m.main()


if __name__ == '__main__':
    main()
