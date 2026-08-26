#!/usr/bin/env python3
"""Iteration 460: Danish mirrors runde 8 (5 sider).

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
    # ------------------------------------------- Tilgængelighedsgennemgang-pris ---
    dict(
        en_slug='accessibility-audit-cost',
        slug='hvad-koster-tilgaengelighedsgennemgang',
        badge='TILGÆNGELIGHED &middot; PRISER &middot; EAA',
        title_tag='Hvad koster en tilgængelighedsgennemgang i 2026? Rigtige tal',
        h1='Hvad koster en tilgængelighedsgennemgang<br>i 2026?',
        desc=('Tilbud spænder fra 0 til 200.000 kr — og begge ender kan være '
              'seriøse. Her er hvad hvert prisleje faktisk køber, hvad der '
              'driver prisen, og hvad du kan fakturere dine kunder under EAA.'),
        subtitle='For små webbureauer i EU: de reelle markedspriser for automatiske '
                 'scanninger, hybrid-gennemgange og manuelle audits — og hvordan du '
                 'afgrænser selv, så du ikke betaler for det forkerte niveau.',
        read='8 minutters læsning',
        intro='Spørg tre leverandører hvad en tilgængelighedsgennemgang koster, og du '
              'får tre svar der adskiller sig med en faktor ti. Det er ikke '
              'prisafskalleri — "gennemgang" dækker alt fra en to minutters automatisk '
              'crawler-rapport til en manuel evaluering over flere uger med brugere af '
              'hjælpeteknologi. Leverancerne, grundigheden og den juridiske vægt er '
              'helt forskellige. Denne guide giver dig de reelle 2026-markedspriser, '
              'forklarer hvad der driver dem, og viser hvordan du afgrænser et opdrag '
              'så tilbuddene bliver sammenlignelige.',
        cards=[
            ('🆓 Automatisk scanning: 0-3.500 kr', 'Værktøjer som axe DevTools, Lighthouse, '
             'WAVE og vores egen gratis scanner fanger cirka 30-40 % af WCAG-problemerne '
             '— kontrast, alt-tekst, formularlabels, overskriftsstruktur. Et udgangspunkt, '
             'aldrig et forsvarligt dokument på sig selv.'),
            ('🔍 Hybrid-gennemgang: ~10.000-25.000 kr', 'Automatisk scan plus 6-12 timers '
             'erfaren manuel test (tastaturnavigation, skærmlæser på nøgleflows). Det '
             'bedste værdileje for en typisk småvirksomhedsside.'),
            ('🎓 Fuld manuel audit: 35.000-100.000+ kr', 'Specialister tester hver unikt '
             'skabelonforløb og interaktive komponent mod WCAG 2.2 AA med alvorsgraderede '
             'fund. Nødvendigt når juridisk forsvarlighed tæller.'),
        ],
        sections=[
            ('Hvorfor priserne varierer så meget', [
                '<p>Den største prismæssige driver er ikke antallet af sider — auditorer '
                'tester efter repræsentativt udvalg. Det er antallet af unikke '
                'sidetemplates og interaktive komponenter. En B2B-side på 45 sider bygget '
                'på én skabelon auditères for en brøkdel af en side på 20 sider med '
                'skræddersyet checkout, bookingflow og medlemsområde.</p>',
                '<p>Andre drivere: om du skal opfylder WCAG 2.1 AA eller 2.2 AA; om test '
                'med rigtige brugere af hjælpeteknologi er medtaget; om der kræves '
                'formel dokumentation (en VPAT-rapport alene lægger 70.000+ kr oveni); '
                'og selve rettelserne, som leverandører typisk tilbyder separat — regn '
                'med én til tre gange audit-honoraret for at fikse det der findes.</p>',
                '<p>Til kalibrering, nyligt rapporterede rigtige opdrag: hybrid-gennemgang '
                'af en advokatside på 8 sider landede omkring 12.000 kr; fuld manuel audit '
                'af en SaaS-marketingsside på 45 sider omkring 60.000 kr; webshop på 200 '
                'sider med brugertesting omkring 125.000 kr.</p>',
            ]),
            ('EAA-vinklen: hvad må du fakturere?', [
                '<p>European Accessibility Act har gjort tilgængelighed til et salgsargument '
                '— og til et ansvar. Millioner af EU-småvirksomheder står nu med krav de '
                'ikke selv kan vurdere. For et bureau betyder det en ny, veldefineret '
                'ydelsepakke: scanning, rettelser, rapport og tilgængelighedserklæring.</p>',
                '<p>Prissæt den som fastpris-pakke snarere end timebetaling. Kunden forstår '
                'fastpris, og du undgår at konkurrere på timetal. En realistisk pakke for '
                'en typisk småvirksomhedsside: automatisk scanning (gratis værktøj), 6-12 '
                'timers manuel gennemgang, rettelse af fundene og en korrekt '
                'tilgængelighedserklæring med kendte begrænsninger — samlet ofte inden for '
                'hybrid-lejet ovenfor.</p>',
                '<p>Vær ærlig i salget om hvad automatiske scanninger kan: de fanger '
                'cirka en tredjedel. Resten kræver mennesker. Det er netop derfor '
                'kunden køber din gennemgang frem for kun at køre en gratis scanner.</p>',
            ]),
        ],
        ctas=[('/scan-da', 'Scan din side gratis'),
              ('/da/blog/pris-tilgaengelighedsgennemgang', 'Prisguide for bureauer')],
        related=[('/da/blog/eaa-tjekliste-2026', 'EAA-tjekliste'),
                 ('/da/blog/gratis-tilgaengelighedsvaerktoejer', 'Gratis værktøjer'),
                 ('/da/blog/skriv-tilgaengelighedserklaering', 'Skriv erklæringen')],
        da_link_text='Hvad koster en tilgængelighedsgennemgang i 2026?',
        faqs=[
            ('Hvor meget koster en tilgængelighedsgennemgang?',
             'Markedet i 2026 spænder bredt: automatiske scanninger koster 0-3.500 kr, '
             'hybrid-gennemgange (automatisk plus manuel test) cirka 10.000-25.000 kr for '
             'en lille side, og fulde manuelle audits fra specialister 35.000-100.000+ '
             'kr afhængigt af kompleksitet. Prisen styres mest af antallet af unikke '
             'skabeloner og interaktive komponenter — ikke af sidens sidetal.'),
            ('Kan en gratis scanner erstatte en gennemgang?',
             'Nej. Automatiske værktøjer fanger typisk 30-40 % af WCAG-problemerne: '
             'kontrast, manglende alt-tekst, labels og overskriftsstruktur. Ting som '
             'tastaturfælder, ubrugelige fokusordener og meningsløs skærmlæser-output '
             'kræver manuel test. Brug scanningen som udgangspunkt og bevis for fremdrift '
             '— ikke som dokumentation for compliance.'),
            ('Hvad driver prisen op?',
             'Antal unikke sidetemplates og interaktive komponenter, om der kræves WCAG '
             '2.2 AA frem for 2.1 AA, om brugertesting med hjælpeteknologi er medtaget, '
             'og om der skal leveres formel dokumentation som en VPAT. Rettelser tilbydes '
             'typisk separat — regn med yderligere én til tre gange audit-honoraret.'),
            ('Hvad skal jeg fakturere som bureau under EAA?',
             'Sælg en fastpris-pakke: scanning, manuel gennemgang, rettelser og '
             'tilgængelighedserklæring. En typisk pakke for en småvirksomhedsside ligger '
             'i hybrid-lejet (ca. 10.000-25.000 kr). Vær tydelig med at automatiske tjek '
             'kun dækker omkring en tredjedel af kravene — resten er dit manuelt arbejde, '
             'og dét er værdien kunden køber.'),
            ('Er en dyb manuel audit nogensinde nødvendig?',
             'Ja, når juridisk forsvarlighed tæller: offentlige myndigheder, banker, '
             'store e-handelsplatforme og alle der står over for en klage eller '
             'tilsyn. Der kræves fuld test mod WCAG 2.2 AA af hver unik skabelon med '
             'alvorsgraderede fund. For de fleste små virksomheder rækker '
             'hybrid-niveauet — forudsigt at fundene faktisk blive rettet.'),
        ],
    ),
    # --------------------------------------------------- Ren tekst fra hjemmeside ---
    dict(
        en_slug='copy-clean-text-from-website',
        slug='kopier-ren-tekst-fra-hjemmeside',
        badge='PRODUKTIVITET &middot; BROWSER-TIPS',
        title_tag='Kopiér ren tekst fra enhver hjemmeside (uden formateringsrod)',
        h1='Kopiér ren tekst<br>fra enhver hjemmeside',
        desc=('Du markerer, kopierer, indsætter — og formateringen er pludselig forkert. '
              'Her er præcis hvorfor det sker, og fem måder at fikse det på — inklusive '
              'én hvor du ikke skal huske nogen genvej.'),
        subtitle='Hvorfor Ctrl+C kopierer HTML frem for tekst, hvad der ødelægger dine '
                 'indsættelser i Word, Notion, Gmail og AI-prompts — og hvilken metode '
                 'der passer til din arbejdsgang.',
        read='5 minutters læsning',
        intro='Browseren kopierer ikke ren tekst når du trykker Ctrl/Cmd+C. Den kopierer '
              'HTML-fragmentet af din markering — hver span, inline-stil, fontface-'
              'erklæring og tracking-pixel der bruges til at vise afsnittet på siden. '
              'Indsæt det i noget der accepterer rig formatering (mail, Word, Notion, '
              'Google Docs, en CMS-editor), så følger markeringen med: et rodet mix af '
              'kildesidens design og dit dokuments tema. Indsætter du i en Markdown-editor '
              'eller en AI-prompt, kan usynlige tegn i stilheden ødelægge teksten.',
        cards=[
            ('📋 Indsæt som ren tekst', 'Ctrl+Shift+V (Windows/Linux) eller Cmd+Shift+V '
             '(Mac) indsætter uformatteret i mange apps. Virker — men kun hvis appen '
             'understøtter det, og du skal huske det hver gang.'),
            ('🧹 Udklipsholder-administratorer', 'Ditto, Maccy eller Paste kan strippe '
             'formatering som regel. Giver historik og bekvemmelighed, men ligger uden '
             'for browseren og din workflow.'),
            ('🛠 Browser-udvidelse', 'En copy-as-clean-text-udvidelse som Clean Copy fikser '
             'problemet ved kilden: markeringen konverteres før den rammer '
             'udklipsholderen. Hver indsættelse — hvor som helst — er ren som standard.'),
        ],
        sections=[
            ('Fem måder at kopiere ren tekst på', [
                '<p><strong>1️⃣ Genvejen indsæt-som-ren-tekst (indbygget).</strong> Windows: '
                'Ctrl+Shift+V — virker i Chrome, Word, Gmail, Teams, Slack, VS Code, '
                'Obsidian og de fleste moderne apps. Mac: Cmd+Shift+V eller '
                'Cmd+Shift+Option+V afhængigt af appen. Begrænsning: kræver manuel '
                'aktivering ved hver indsættelse. Indsætter du 50 gange om dagen, skal du '
                'tænke på formatering 50 gange.</p>',
                '<p><strong>2️⃣ Standardindstilling i appen.</strong> Nogle apps kan sættes '
                'til paste-to-match-style som standard. Obsidian har en kontakt, VS Code '
                'har en indstilling. Gmail har ikke. Resultatet: virker kun i de apps du '
                'konfigurerer, én ad gangen.</p>',
                '<p><strong>3️⃣ Udklipsholder-manager med formatstripping.</strong> Ditto '
                '(Windows) eller Maccy (Mac) gemmer historik og kan fjerne rig formatering '
                'ved indsættelse. Nyttigt for power users — men endnu et program at '
                'installere og holde styr på.</p>',
                '<p><strong>4️⃣ Clean Copy-udvidelsen (anbefalet).</strong> Højrekliksmenu '
                'og genvej (Ctrl/Cmd+Shift+C). Markér tekst hvor som helst, kald Clean '
                'Copy, og udklipsholderen får ren tekst eller Markdown — uanset hvor du '
                'indsætter næste gang. Kører helt i browseren, sender intet data nogen '
                'steder, MIT-licenseret og gratis.</p>',
                '<p><strong>5️⃣ Clean Copy Web — helt uden installation.</strong> Ikke ved '
                'din egen computer? Så kører Clean Copy Web i enhver browser: indsæt det '
                'rodede tekst eller HTML, kopiér ren Markdown eller ren tekst tilbage.</p>',
            ]),
            ('Hvilken metode skal jeg vælge?', [
                '<div class="compare"><table>'
                '<tr><th>Metode</th><th>Renser altid?</th><th>Fangst</th></tr>'
                '<tr><td>Genvej Ctrl/Cmd+Shift+V</td><td>Kun i understøttende apps</td>'
                '<td>Husk den hver gang</td></tr>'
                '<tr><td>App-standardindstilling</td><td>Kun i den app</td><td>Sættes op '
                'app for app</td></tr>'
                '<tr><td>Udklipsholder-manager</td><td>Jævnligt</td><td>Ekstra program</td></tr>'
                '<tr><td>Clean Copy-udvidelse</td><td>Ja</td><td>Én installation i browseren</td></tr>'
                '</table></div>',
                '<p>Skal du flytte citater, tabeldata eller research ud af browsere flere '
                'gange dagligt, vinder udvidelsen på bekvemmelighed: én vane i stedet for '
                'én genvej pr. app. Skal du bare engangs imelle, er genvejen fint.</p>',
            ]),
        ],
        ctas=[('/clean-copy', 'Hent Clean Copy gratis'),
              ('/da/blog/indsaet-som-markdown-i-vscode', 'Clean Copy i VS Code')],
        related=[('/da/blog/kopier-tabel-til-excel', 'Tabeller til Excel'),
                 ('/da/blog/kopier-chatgpt-til-word', 'Fra ChatGPT til Word'),
                 ('/da/blog/ren-tekst-fra-hjemmeside', 'Ren tekst-workflow')],
        da_link_text='Kopiér ren tekst fra enhver hjemmeside',
        faqs=[
            ('Hvorfor indsætter min kopierede tekst med mærkelig formatering?',
             'Browseren kopierer HTML-fragmentet af din markering — ikke ren tekst. Alle '
             'inline-stile, spans og skrifttypeerklæringer fra kildesiden følger med, og '
             'apps der accepterer rig formatering (Word, Gmail, Notion) beholder dem. '
             'Resultatet er et mix af kildesidens design og dit dokuments tema.'),
            ('Virker Ctrl+Shift+V overalt?',
             'I mange, men ikke alle apps — og kombinationen varierer: Mac bruger ofte '
             'Cmd+Shift+V eller fire-tast-comboen Cmd+Shift+Option+V i Gmail og Word. '
             'Ulempen er at du skal huske genvejen ved hver enkelt indsættelse, og at '
             'den ikke virker i apps der ikke understøtter den.'),
            ('Er en browser-udvidelse sikker til dette?',
             'En ordentlig udvidelse kører lokalt i browseren og sender ingenting til en '
             'server. Clean Copy er open source under MIT-licensen — koden kan læses, og '
             'den kræver hverken konto eller netværksadgang for at konvertere din '
             'markering.'),
            ('Kan jeg få ren tekst på en computer jeg ikke må installere på?',
             'Ja. Clean Copy Web kører i browseren: indsæt det rodede tekst eller HTML, '
             'og kopiér ren Markdown eller ren tekst tilbage. Ingen installation, ingen '
             'konto — praktisk på arbejdscomputere med låste udvidelser.'),
            ('Hvad med Markdown i stedet for ren tekst?',
             'Clean Copy kan levere begge dele. Markdown bevarer struktur — overskrifter, '
             'listestruktur, links og tabeller bliver til gyldig Markdown — mens ren tekst '
             'fjerner al struktur. Vælg Markdown når resultatet skal redigeres videre i '
             'Obsidian, VS Code eller et CMS, ren tekst til mail og formularer.'),
        ],
    ),
    # ------------------------------- Tjek hastighed uden Lighthouse (findes alligevel) ---
    dict(
        en_slug='check-website-speed-without-lighthouse',
        slug='tjek-hastighed-uden-lighthouse',
        badge='PERFORMANCE &middot; SEO &middot; CLI',
        title_tag='Tjek din hjemmesides hastighed uden Lighthouse (gratis CLI, 2026)',
        h1='Tjek hastigheden —<br>uden Lighthouse',
        desc=('Lighthouse er tungt: fuld browser-render, snart minutter pr. kørsel, '
              'besværligt i CI. Til hverdagsspørgsmålet "er denne side hurtig, gyldig og '
              'korrekt koblet sammen?" svarer en letvægts-terminalprofiler på sekunder.'),
        subtitle='page-profile henter siden server-side og scorer 21 signaler på under to '
                 'sekunder — i browseren, som single-file CLI eller i batch. Gratis og '
                 'open source.',
        read='4 minutters læsning',
        intro='Fuld-render-audits har deres plads. Men tre daglige opgaver behøver dem '
              'ikke: et hurtigt pre-deploy sanity check (kom canonical-tagget med? Er '
              'TTFB stadig fornuftig?), CI-pipelines (headless Chrome i CI bare for at '
              'gate en deploy på en score er langsomt og skrøbeligt) og mange URLs på én '
              'gang (Lighthouse kører én side pr. invocation). Til det bruger man en let '
              'profiler der henter én gang, parser og svare.',
        cards=[
            ('⚡ Sekunder, ikke minutter', 'Ingen headless browser. Tjekket henter én gang '
             'og parser — typisk køretid under to sekunder.'),
            ('🔁 Følg udviklingen', '--history gemmer tidligere scores lokalt, så du kan se '
             'om en release gjorde det bedre eller værre. Gratis for alle.'),
            ('🧰 Virker overalt', 'Ren Python-standardbibliotek — enhver maskine med Python '
             '3.8+, herunder CI-containere og Raspberry Pi.'),
        ],
        sections=[
            ('Metoden: én kommando, ingen installation', [
                '<p><strong>Mulighed A — i browseren (intet at installere).</strong> Åbn '
                '/page-profile, indsæt URL\'en, få rapporten med det samme.</p>',
                '<pre>curl -O https://hermes-passiv.pages.dev/downloads/page-profile/page_profile.py\n'
                'python3 page_profile.py https://example.com\n'
                '\n'
                '# Maskinlæsbart output til scripts og CI:\n'
                'python3 page_profile.py --json https://example.com | jq .score</pre>',
            ]),
            ('Hvordan det klarer sig mod de tunge værktøjer', [
                '<div class="compare"><table>'
                '<tr><th>Værktøj</th><th>Opsætning</th><th>Køretid</th><th>Bedst til</th></tr>'
                '<tr><td>Lighthouse</td><td>Chrome / Node</td><td>30-60 s</td>'
                '<td>Dybe render-audits, Core Web Vitals</td></tr>'
                '<tr><td>PageSpeed Insights</td><td>Ingen (web)</td><td>~30 s</td>'
                '<td>Feltdata, lab-scores</td></tr>'
                '<tr><td>curl + manuel inspektion</td><td>Ingen</td><td>Sekunder</td>'
                '<td>Én header ad gangen, ekspertøjne</td></tr>'
                '<tr><td><strong>page-profile</strong></td><td>Én Python-fil</td>'
                '<td>&lt; 2 s</td><td>Daglige helbredstjek, CI-gates, batch</td></tr>'
                '</table></div>',
                '<p>De svarer på forskellige spørgsmål. Brug Lighthouse når du skal have '
                'renderede diagnostikker; brug page-profile når du skal have et hurtigt, '
                'gentageligt svar du kan lægge i en pipeline.</p>',
            ]),
            ('Hvad de 21 signaler dækker', [
                '<p>Svartid og redirects, titel- og description-længder, Open Graph-tags, '
                'canonical, hreflang, JSON-LD-struktureret data, overskriftsstruktur, '
                'alt-tekster og sikkerhedsheadere. Alt hvad der afgør om en side er '
                'teknisk sund — uden at rendere den.</p>',
                '<p>I Pro-versionen kommer compare (to URLs side om side), batch (hele '
                'listefiler) og en HTML-rapport du kan vedhæfte en ticket — med offline '
                'licensnøgler så intet afhænger af en server.</p>',
            ]),
        ],
        ctas=[('/page-profile', 'Prøv i browseren'),
              ('/downloads/page-profile/page_profile.py', 'Download CLI\'en')],
        related=[('/da/blog/teknisk-seo-tjek-hjemmeside', 'Teknisk SEO-tjek'),
                 ('/da/blog/meta-tjekker', 'Meta-tag-tjekker'),
                 ('/da/blog/canonisk-url-guide', 'Canonical-guide')],
        da_link_text='Tjek hjemmesidehastighed uden Lighthouse',
        faqs=[
            ('Kan jeg teste hastighed uden at køre Lighthouse?',
             'Ja. Den gratis page-profile CLI henter siden server-side og rapporterer '
             'svartid, HTTP-status, redirects og sidevægt-signaler på få sekunder — uden '
             'Chrome, uden npm-installation, uden Lighthouse-setup. Den supplerer '
             'Lighthouse: brug den til hurtige helbredstjek og CI-gates, Lighthouse til '
             'dybe render-audits.'),
            ('Er dette en alternativ til Google PageSpeed Insights?',
             'Den måler noget andet. PageSpeed Insights giver feltdata og lab-scores fra '
             'en fuld render — nyttigt til Core Web Vitals-arbejde, men langsomt pr. '
             'kørsel. page-profile svarer på det tekniske helbred: status, svartid, '
             'meta-tags, struktureret data, headere. Hurtigt og gentageligt.'),
            ('Kræver det installation?',
             'Nej. Enten kører du den direkte i browseren på /page-profile, eller også '
             'downloader du én enkelt Python-fil og kører den med python3. Ingen pip, '
             'ingen npm, ingen afhængigheder — standardbiblioteket klarer alt.'),
            ('Kan jeg bruge det i CI?',
             'Ja, det er et af hovedformålene. Outputtet findes som maskinlæsbar JSON '
             '(--json), scriptet afslutter med exit-koder, og fordi det er ren '
             'standardbiblioteks-Python kører det i enhver container med Python 3.8+ — '
             'inklusive GitHub Actions uden ekstra steps.'),
            ('Hvad koster Pro-versionen?',
             'Pro ($19/år) tilføjer compare, batch-kørsler og eksportérbar HTML-rapport '
             'med offline licensnøgler. Historik-funktionen — scores gemt lokalt over '
             'tid — er gratis for alle.'),
        ],
    ),
    # --------------------------------------------- Kopiér tabel fra PDF til Excel ---
    dict(
        en_slug='copy-table-from-pdf-to-excel',
        slug='kopier-tabel-fra-pdf-til-excel',
        badge='PDF &middot; EXCEL &middot; TABELLER',
        title_tag='Kopiér en tabel fra PDF til Excel (guide 2026)',
        h1='Fra PDF-tabel<br>til pæne Excel-celler',
        desc=('Årsrapporter, kvartalsregnskaber, offentlig statistik — tabellerne sidder '
              'fanget i PDF-filer. Markér-og-kopiér giver næsten altid én lang klump '
              'tekst. Sådan kommer du rundt om det, med hver kolonne der hvor den skal.'),
        subtitle='Hvorfor PDF-vieweren ødelægger strukturen, hvad OCR koster af tal — og '
                 'metoden hvor tabellen lander i rigtige celler via browseren og Markdown.',
        read='4 minutters læsning',
        intro='Problemet er ikke Excel — det er udklipsholderen. En PDF har ingen reel '
              'tabelstruktur at give videre. Direkte kopiering fra viewer-en giver typisk '
              'alle værdier stablet kolonnevis, én pr. linje. Skærmbillede plus OCR læser '
              'pixels — og cifre er præcis det OCR tager fejl af oftest. Ét forkert ciffer '
              'i et regnskab er værre end ingen data. Og manuel genindtasting skalerer '
              'ikke: fint til tre rækker, ej til en årsrapport på 40 sider.',
        cards=[
            ('✅ Celler forbliver celler', 'Udklipsholderen bærer reel tabelstruktur, så '
             'Excel mapper hver værdi til den rigtige celle — headers inkluderet.'),
            ('🧹 Intet rod med', 'Ingen sidehoveder, fodnotenumre eller løbende tekst — '
             'kun tabellen du pegede på.'),
            ('🔁 Virker andre steder også', 'Samme indsættelse virker i Google Sheets, '
             'Numbers og LibreOffice Calc.'),
        ],
        sections=[
            ('Metoden: åbn PDF\'en i browseren', [
                '<p>Når en PDF åbnes i Chrome eller Firefox, er teksten rigtig tekst på '
                'siden — og det er præcis hvad Clean Copy-udvidelsen arbejder med. Markér '
                'tabellen (eller klik inde i den) og kopiér som Markdown: konverteren '
                'gør tabellen til struktureret Markdown, som Excel, Sheets og Notion '
                'indsætter som rigtige rækker og kolonner.</p>',
                '<p><strong>1. Installér</strong> Clean Copy til Chrome eller Firefox — '
                'se installationsguiden på /clean-copy#install.</p>',
                '<p><strong>2. Åbn PDF\'en i browseren.</strong> Træk PDF-filen ind i et '
                'Chrome- eller Firefox-vindue og scroll hen til tabellen.</p>',
                '<p><strong>3. Kopiér tabellen.</strong> Markér tabellen, klik '
                'Clean Copy-ikonet og vælg kopiér som Markdown.</p>',
                '<p><strong>4. Indsæt i Excel.</strong> Klik celle A1 og tryk Ctrl+V '
                '(Cmd+V på Mac). Hver værdi lander i sin egen celle.</p>',
            ]),
            ('Mulighederne side om side', [
                '<div class="compare"><table>'
                '<tr><th>Metode</th><th>Bevarer struktur?</th><th>Hage</th></tr>'
                '<tr><td>Markér + kopiér i PDF-vieweren</td><td>Sjældent</td>'
                '<td>Tekst kommer i læserækkefølge, kollapser kolonner</td></tr>'
                '<tr><td>Skærmbillede + OCR</td><td>Efter oprydning</td>'
                '<td>Talfejl er svære at spotte</td></tr>'
                '<tr><td>Acrobat "Eksportér til regneark"</td><td>Ja</td>'
                '<td>Betales abonnement; langsom ved mange tabeller</td></tr>'
                '<tr><td>Excel Data → Hent data fra PDF</td><td>Ja</td>'
                '<td>Kræver Microsoft 365; halter ved komplekse layouts</td></tr>'
                '<tr><td><strong>Clean Copy — Markdown-tabel</strong></td><td>Ja</td>'
                '<td>Gratis browserudvidelse; PDF åbnet i browseren</td></tr>'
                '</table></div>',
                '<p>Har du allerede Microsoft 365 eller Acrobat, kan deres indbyggede '
                'eksporter sagtens bruges til enkelte store tabeller. Til hurtige kopier '
                '— og gratis — er browser-vejen den enkleste.</p>',
            ]),
        ],
        ctas=[('/clean-copy', 'Hent Clean Copy gratis'),
              ('/da/blog/kopier-tabel-til-excel', 'Tabeller fra hjemmesider')],
        related=[('/da/blog/html-tabel-til-csv-konverter', 'HTML-tabel til CSV'),
                 ('/da/blog/kopier-som-markdown-udvidelse', 'Kopiér som Markdown'),
                 ('/da/blog/tabeljustering-html-til-markdown', 'Tabeljustering')],
        da_link_text='Kopiér en tabel fra PDF til Excel',
        faqs=[
            ('Hvorfor bliver direkte kopiering fra PDF til rod?',
             'En PDF gemmer tekst som positionerede blokke uden reel tabelstruktur. '
             'Viewer-en renderer tekst i læserækkefølge — ikke tabelrækkefølge — så '
             'kolonner kollapser, og hver værdi lander typisk på sin egen linje. '
             'Udklipsholderen har simpelthen ingen struktur at give Excel.'),
            ('Er OCR en sikker vej?',
             'Nej, til tal aldrig. OCR læser pixels, og cifre er den hyppigste kilde til '
             'fejl. Et forkert digit i et regnskab er svært at opdage og værre end ingen '
             'data. Brug kun OCR på rent prosatekst, og verificér altid tallene imod '
             'originalen.'),
            ('Kræver metoden betalt software?',
             'Nej. Browser-vejen bruger Chromes eller Firefox\' indbyggede PDF-viewer '
             'plus den gratis Clean Copy-udvidelse. Acrobat-eksport og Excels '
             '"Hent data fra PDF" fungerer godt men kræver betalte abonnementer '
             '(Acrobat / Microsoft 365).'),
            ('Virker indsættelsen i Google Sheets også?',
             'Ja. Samme princip: Markdown-tabellen indsættes som rigtige rækker og '
             'kolonner i Google Sheets, Numbers og LibreOffice Calc — ikke kun Excel.'),
            ('Hvad med scannede PDF\'er uden rigtig tekst?',
             'Hvis PDF\'en er et billedscannet dokument, findes der ingen tekst at '
             'kopiere — browser-metoden kræver at teksten er rigtig tekst. Scannede '
             'dokumenter skal gennem OCR først, med de risici for talfejl det indebærer. '
             'Tjek om du kan markere tekst i viewer-en — kan du ikke, er det en scan.'),
        ],
    ),
    # ------------------------------------------------------------ Open Graph-tjekker ---
    dict(
        en_slug='open-graph-checker',
        slug='open-graph-tjekker-guide',
        badge='BLOG &middot; SOCIAL DELING',
        title_tag='Open Graph-tjekker — sådan ser dine links ud når de deles (gratis)',
        h1='Open Graph-tjekker:<br>se dit link før du deler det',
        desc=('Hver gang nogen deler din side på LinkedIn, Facebook, X, Slack eller Teams, '
              'bygger platformen et kort ud fra dine Open Graph-tags — i stilhed. Tjek '
              'hvad den ser, før du trykker publicér.'),
        subtitle='Hvad og-taggene gør, de fem fejl der dræber klik — og tre måder at '
                 'tjekke dem på, inklusive en automatiseret der også fanger twitter:card.',
        read='5 minutters læsning',
        intro='Når en URL indsættes i et socialt netværk eller chat-app, henter platformens '
              'crawler din side og læser fire meta-tags fra og-navnerummet: og:title, '
              'og:description, og:image og og:url. Mangler taggene, gætter platformen — '
              'normalt dårligt: intet billede, en afkortet titel eller en beskrivelse '
              'skrabt fra tilfældig sidetekst. Er taggene forkerte, vises det forkerte '
              'kort — og platformene cachér aggressivt: at rette taggene i dag retter '
              'ikke kort der allerede er cachet.',
        cards=[
            ('🖼️ Billede-problemet', 'Den hyppigste fejl: og:image mangler, er relativ i '
             'stedet for absolut, mindre end 200×200 px eller bag login. Enhver af dem '
             'renderer slet intet billede.'),
            ('🗄️ Cache-problemet', 'Facebook og LinkedIn cacher delingsdata i dage. Ret '
             'taggene først, tving derefter en re-scrape via platformens debugger — ellers '
             'tester du på gamle data.'),
            ('✅ Ét tjek, alle tags', 'En god tjekker validerer alle tags på én gang: '
             'tilstedeværelse, størrelser, absolutte URLs, billeddimensioner og '
             'twitter:card-fallbacks.'),
        ],
        sections=[
            ('Sådan tjekker du dine Open Graph-tags', [
                '<p><strong>Mulighed A — automatiseret (anbefalet).</strong> Indsæt din URL '
                'i den gratis page-profiler. Udover den fulde tekniske SEO-rapport får du '
                'hele Open Graph- og Twitter Card-billedet: hvilke tags findes, om '
                'og:image resolves og opfylder minimumsstørrelsen, og om twitter:card har '
                'fornuftige fallbacks.</p>',
                '<p><strong>Mulighed B — view-source.</strong> Åbn din side, vis kilde og '
                'søg efter "og:". Du bør finde mindst title, description, image og url i '
                '&lt;head&gt;. Husk: tags renderet client-side af JavaScript er usynlige '
                'for de fleste platform-crawlere — de skal ligge i det rå HTML-svar.</p>',
                '<p><strong>Mulighed C — platform-debuggere.</strong> Efter rettelsen: kør '
                'Facebooks Sharing Debugger og LinkedIns Post Inspector for at friske '
                'cacherne op og bekræfte det nye kort. Hver platform cacher uafhængigt; '
                'at rydde én rydder ikke de andre.</p>',
                '<p><strong>📏 Billed-regler:</strong> 1200×630 px, absolut URL, under '
                '~8 MB, offentligt tilgængelig, PNG eller JPEG. Det består alle store '
                'platformers krav med margen.</p>',
                '<p><strong>✍️ Titler og beskrivelser:</strong> Kort afkortes omkring '
                '55-65 tegn titel og ~110-160 tegn beskrivelse afhængigt af platform. '
                'De vigtige ord først.</p>',
                '<p><strong>🧩 Tags pr. side:</strong> Ét fælles sæt OG-tags på hele sitet '
                'betyder at hver delt artikel viser forsidekortet. Generér dem pr. '
                'skabelon — de fleste CMS\'er gør det med ét plugin eller én meta-partial.</p>',
            ]),
            ('Fem Open Graph-fejl der dræber klik', [
                '<p><strong>1. Manglende og:image.</strong> Opslag uden billeder får '
                'markant færre klik — og platformen finder sjældent et passende alternativ '
                'selv.</p>',
                '<p><strong>2. Relativ billede-URL.</strong> og:image skal være absolut. '
                'Crawleren resolver ikke relative stier pålideligt.</p>',
                '<p><strong>3. Billede bag auth eller for lille.</strong> Under 200×200 px '
                'eller bag login = intet kortbillede, uden advarsel.</p>',
                '<p><strong>4. Samme tags overalt.</strong> Ét globalt sæt betyder at '
                'artikler deles med forsidekortet — og click-through lider.</p>',
                '<p><strong>5. Ingen re-scrape efter rettelse.</strong> Rettede tags vises '
                'ikke før cachet tvinges frisk. Test altid via debuggeren efter ændring.</p>',
            ]),
        ],
        ctas=[('/page-profile', 'Tjek en URL nu'),
              ('/da/blog/meta-tjekker', 'Alle meta-tags på én gang')],
        related=[('/da/blog/teknisk-seo-tjek-hjemmeside', 'Teknisk SEO-tjek'),
                 ('/da/blog/hreflang-guide-da', 'Hreflang-guiden'),
                 ('/da/blog/seo-metadata-tjek-hjemmeside', 'Metadata-audit')],
        da_link_text='Open Graph-tjekker: se dit link før du deler det',
        faqs=[
            ('Hvad laver Open Graph-tags egentlig?',
             'De fortæller sociale platforme og chat-apps hvordan et link skal kort-lægges: '
             'titel, beskrivelse, billede og kanonisk URL. Udem dem gætter crawleren — '
             'typisk med afkortet titel, tilfældig tekst som beskrivelse eller slet intet '
             'billede.'),
            ('Hvorfor viser mit link stadig det gamle billede efter jeg rettede det?',
             'Platformene cacher delingsdata aggressivt — Facebook og LinkedIn i flere '
             'dage. Kør URL\'en igennem platformens debugger (Facebook Sharing Debugger, '
             'LinkedIn Post Inspector) for at tvinge en re-scrape. Hver platform cacher '
             'uafhængigt.'),
            ('Hvor stort skal og:image være?',
             '1200×630 px er den sikre standard: mindst 200×200 px kræves af de fleste, '
             'men små billeder renders lav opløsning eller slet ikke. Absolut URL, under '
             '~8 MB, PNG eller JPEG, offentligt tilgængelig.'),
            ('Kan JavaScript-genererede OG-tags bruges?',
             'Usikkert. Mange platform-crawlere eksekverer ikke JavaScript, så tags der '
             'først dukker op efter render ses ikke. De skal stå i det rå HTML-svar — '
             'generér dem server-side eller statisk i build.'),
            ('Hvordan tjekker jeg hurtigst muligt?',
             'Indsæt URL\'en i den gratis page-profiler på /page-profile. Ud over hele '
             'SEO-rapporten får du status på hvert og:-tag og twitter:card — inklusive '
             'om billedet resolver og opfylder størrelseskravene. Sekunder, ingen konto.'),
        ],
    ),
]


def main():
    m.PAGES[:] = PAGES
    m.main()


if __name__ == '__main__':
    main()
