# Build the Danish version of the scanner page from site/scan.html.
# Translates user-facing strings only; JS logic stays identical.
import re, json

src = open('site/scan.html').read()

T = [
 # head
 ('<html lang="en">\n<head>', '<html lang="da">\n<head>'),
 ('<title>Free EAA Compliance Scanner — Check Any Website | Hermes Compliance</title>',
  '<title>Gratis EAA-tilgængelighedsscanner — Tjek enhver hjemmeside | Hermes Compliance</title>'),
 ('<meta name="description" content="Paste a URL and get an instant automated EAA / WCAG 2.1 AA check. Works on any website — WordPress, Shopify, Webflow, Next.js, and hand-written HTML. No signup required.">',
  '<meta name="description" content="Indsæt en URL og få et øjeblikkeligt automatiseret EAA / WCAG 2.1 AA-tjek. Virker på enhver hjemmeside — WordPress, Shopify, Webflow, Next.js og håndskrevet HTML. Ingen tilmelding.">'),
 ('<meta property="og:title" content="Free EAA Compliance Scanner — Check Any Website">',
  '<meta property="og:title" content="Gratis EAA-tilgængelighedsscanner — Tjek enhver hjemmeside">'),
 ('<meta property="og:description" content="Paste a URL and get an instant automated EAA / WCAG 2.1 AA check. Works on any website. No signup required.">',
  '<meta property="og:description" content="Indsæt en URL og få et øjeblikkeligt automatiseret EAA / WCAG 2.1 AA-tjek. Virker på enhver hjemmeside. Ingen tilmelding.">'),
 ('<meta name="twitter:title" content="Free EAA Compliance Scanner — Check Any Website">',
  '<meta name="twitter:title" content="Gratis EAA-tilgængelighedsscanner — Tjek enhver hjemmeside">'),
 ('<meta name="twitter:description" content="Paste a URL and get an instant automated EAA / WCAG 2.1 AA check. Works on any website. No signup required.">',
  '<meta name="twitter:description" content="Indsæt en URL og få et øjeblikkeligt automatiseret EAA / WCAG 2.1 AA-tjek. Virker på enhver hjemmeside. Ingen tilmelding.">'),
 ('content="https://hermes-passiv.pages.dev/scan"', 'content="https://hermes-passiv.pages.dev/scan-da"'),
]
for a,b in T:
    assert a in src, 'missing: '+a[:60]
    src = src.replace(a,b)

# FAQ JSON-LD -> Danish
faq_da = {
"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
{"@type":"Question","name":"Hvad tjekker scanneren?","acceptedAnswer":{"@type":"Answer","text":"16 automatiserede WCAG 2.1 AA-regler: billed-alt-tekst, formularmærkater, link- og knaptekst, sidetitel, sprogattribut, viewport-meta, overskriftsstruktur, iframe-titler, tabelhoveder, duplikerede id'er, aria-hidden-elementer der stadig kan fokuseres, tekstkontrast og links der åbner i nyt vindue uden advarsel."}},
{"@type":"Question","name":"Er scanneren gratis?","acceptedAnswer":{"@type":"Answer","text":"Ja. Ingen tilmelding, ingen konto, ingen e-mail. Indsæt en offentlig URL og få straks en karakter med detaljerede fund."}},
{"@type":"Question","name":"Hvor præcist er det automatiske tjek?","acceptedAnswer":{"@type":"Answer","text":"Automatiserede tjek fanger cirka 30-40 % af tilgængelighedsproblemerne. De resterende 60-70 % kræver menneskelig vurdering: tastaturnavigation, skærmlæsertest og indholdsreview."}},
{"@type":"Question","name":"Gemmer scanneren de sider jeg tjekker?","acceptedAnswer":{"@type":"Answer","text":"Nej. Siden hentes server-side gennem vores Cloudflare-proxy, analyseres i din browser og kasseres straks. Ingen logs, ingen lagring, ingen cookies."}},
{"@type":"Question","name":"Virker den på alle platforme?","acceptedAnswer":{"@type":"Answer","text":"Ja \\u2014 WordPress, Shopify, Webflow, Wix, Squarespace, Drupal, Joomla, Next.js og håndskrevet HTML."}},
{"@type":"Question","name":"Kan jeg scanne en side med adgangskode eller en lokal side?","acceptedAnswer":{"@type":"Answer","text":"Nej \\u2014 scanneren henter sider over det offentlige internet. Til staging eller lokale sider: brug browserudvidelsen eller WordPress-pluginet."}}]}
src = re.sub(r'(<script type="application/ld\+json">\n).*?(\n</script>)',
             lambda m: m.group(1)+json.dumps(faq_da, ensure_ascii=False)+m.group(2),
             src, count=1, flags=re.S)

body = [
 ('<div class="badge">FREE TOOL</div>', '<div class="badge">GRATIS VÆRKTØJ</div>'),
 ('<h1>Free EAA Compliance Scanner</h1>', '<h1>Gratis EAA-tilgængelighedsscanner</h1>'),
 ('''Instant automated accessibility check — works on
    <strong>any website</strong>, any platform, no signup.''',
  '''Øjeblikkeligt automatiseret tilgængelighedstjek — virker på
    <strong>enhver hjemmeside</strong>, alle platforme, ingen tilmelding.'''),
 ('<h2 id="scan-heading">Scan your page</h2>', '<h2 id="scan-heading">Scan din side</h2>'),
 ('<label for="url" class="sr-only">Page URL</label>', '<label for="url" class="sr-only">Sidens URL</label>'),
 ('placeholder="https://your-site.com"', 'placeholder="https://din-hjemmeside.dk"'),
 ('<button type="submit">Scan now</button>', '<button type="submit">Scan nu</button>'),
 ('<h2 id="how-heading">What it checks</h2>', '<h2 id="how-heading">Hvad den tjekker</h2>'),
 ('<li>Images missing alt text · form fields without labels · links or buttons with no text</li>',
  '<li>Billeder uden alt-tekst · formularfelter uden mærkater · links eller knapper uden tekst</li>'),
 ('<li>Missing page title, language attribute or viewport meta</li>',
  '<li>Manglende sidetitel, sprogattribut eller viewport-meta</li>'),
 ('<li>Heading structure problems (no h1, skipped levels)</li>',
  '<li>Overskriftsproblemer (ingen h1, sprunget niveauer)</li>'),
 ('<li>Untitled iframes · tables without headers · duplicate id values</li>',
  '<li>Iframes uden titel · tabeller uden hoveder · duplikerede id-værdier</li>'),
 ('<li>aria-hidden elements that are still keyboard-focusable</li>',
  '<li>aria-hidden-elementer der stadig kan fokuseres med tastatur</li>'),
 ('<li>Low text contrast (WCAG 1.4.3 — inline colour styles)</li>',
  '<li>Lav tekstkontrast (WCAG 1.4.3 — inline farvestile)</li>'),
 ('<li>Links opening in a new window without warning the user</li>',
  '<li>Links der åbner i nyt vindue uden at advare brugeren</li>'),
 ('''<strong>Honest limitation:</strong> automated checks catch roughly
  30–40% of accessibility issues. The rest needs human judgement — the full
  manual process is in our
  <a href="/#products">EAA Compliance Checklist e-book</a>.''',
  '''<strong>Ærlig begrænsning:</strong> automatiserede tjek fanger cirka
  30–40 % af tilgængelighedsproblemerne. Resten kræver menneskelig vurdering —
  hele den manuelle proces ligger i vores
  <a href="/#products">EAA Compliance Checklist e-bog</a>.'''),
 ('<h2 id="pro-heading">Need a formal compliance report?</h2>',
  '<h2 id="pro-heading">Bruger du en formel compliance-rapport?</h2>'),
 ('''Get a professional PDF audit report with executive summary, detailed
  findings, prioritised recommendations, and methodology documentation.
  Perfect for client handovers and internal compliance files.''',
  '''Få en professionel PDF-revisionsrapport med executive summary, detaljerede
  fund, prioriterede anbefalinger og metodedokumentation. Velegnet til
  kundeoverdragelser og interne compliance-filer.'''),
 ('Pro Audit Report — $29', 'Pro-revisionsrapport — $29'),
 ('(available when store launches)', '(kommer når butikken åbner)'),
 ('<h2 id="ext-heading">Also available as a browser extension</h2>',
  '<h2 id="ext-heading">Fås også som browserudvidelse</h2>'),
 ('''Scan any page you're on with one click. The extension ships the same
  rule set — download the zip and load it unpacked in Chrome/Edge:''',
  '''Scan enhver side du er på med ét klik. Udvidelsen har samme regelsæt —
  hent zip-filen og load den upakket i Chrome/Edge:'''),
 ('Download extension (Chrome/Edge)', 'Hent udvidelse (Chrome/Edge)'),
 ('<h2 id="gen-heading">Accessibility Statement Generator</h2>',
  '<h2 id="gen-heading">Generator til tilgængelighedserklæringer</h2>'),
 ('''After you fix what the scanner finds, publish an
  <a href="/accessibility-statement-generator">EAA / WCAG accessibility statement</a> —
  answer 8 questions and get a ready-to-publish statement. Free, runs in your browser.''',
  '''Når du har rettet det scanneren finder, kan du udgive en
  <a href="/accessibility-statement-generator">EAA / WCAG-tilgængelighedserklæring</a> —
  svar på 8 spørgsmål og få en klar-til-udgivelse-erklæring. Gratis, kører i din browser.'''),
 ('<h2 id="cli-heading">Run it from the command line</h2>',
  '<h2 id="cli-heading">Kør den fra kommandolinjen</h2>'),
 ('''Prefer your terminal or CI? <a href="/downloads">Download eaa-scanner</a> —
  a free, zero-dependency Python CLI that runs this same scan on any number of
  URLs and fails the build when errors are found.''',
  '''Foretrækker du terminalen eller CI? <a href="/downloads">Hent eaa-scanner</a> —
  et gratis Python-CLI-værktøj uden afhængigheder, der kører samme scan på et vilkårligt
  antal URL'er og fejler buildet når der findes fejl.'''),
 ('<h2 id="wp-heading">WordPress plugin</h2>', '<h2 id="wp-heading">WordPress-plugin</h2>'),
 ('''Run the same 15-rule scan from your WordPress dashboard —
  <strong>Tools → EAA Scanner</strong>. Works with any theme, scans any URL,
  and everything runs on your own server: no data is sent to third parties.''',
  '''Kør samme scan fra dit WordPress-dashboard —
  <strong>Værktøjer → EAA Scanner</strong>. Virker med ethvert tema, scanner enhver URL,
  og alt kører på din egen server: ingen data sendes til tredjeparter.'''),
 ('Download WordPress plugin', 'Hent WordPress-plugin'),
 ('Install via\n  Plugins → Add New → Upload Plugin. Free, MIT licensed.',
  'Installér via\n  Plugins → Tilføj ny → Upload plugin. Gratis, MIT-licens.'),
 ('''After the automated check, the manual
  review steps are what make you actually compliant — they're all in our
  <a href="/#products">EAA Compliance e-books</a>.''',
  '''Efter det automatiske tjek er de manuelle
  trin det, der gør dig reelt compliant — de ligger alle i vores
  <a href="/#products">EAA Compliance e-bøger</a>.'''),
 ('<h2 id="guides-heading">Platform-specific fix guides</h2>',
  '<h2 id="guides-heading">Platformspecifikke fix-guides</h2>'),
 ('''Scan flagged something on your site? These free guides show exactly where
  to fix the most common issues in each platform's admin:''',
  '''Fandt scanneren noget på din side? Disse gratis guides viser præcis hvor du
  retter de mest almindelige problemer i hver platforms admin:'''),
 ('WordPress accessibility check', 'WordPress-tilgængelighedstjek'),
 ('Shopify accessibility check', 'Shopify-tilgængelighedstjek'),
 ('Webflow accessibility check', 'Webflow-tilgængelighedstjek'),
 ('Wix accessibility check', 'Wix-tilgængelighedstjek'),
 ('Squarespace accessibility check', 'Squarespace-tilgængelighedstjek'),
 ('Drupal accessibility check', 'Drupal-tilgængelighedstjek'),
 ('Joomla accessibility check', 'Joomla-tilgængelighedstjek'),
 ('PrestaShop accessibility check', 'PrestaShop-tilgængelighedstjek'),
 ('Weebly accessibility check', 'Weebly-tilgængelighedstjek'),
 ('Magento / Adobe Commerce accessibility check', 'Magento / Adobe Commerce-tilgængelighedstjek'),
 ('Ghost accessibility check', 'Ghost-tilgængelighedstjek'),
 ('TYPO3 accessibility check (BITV / EN 301 549)', 'TYPO3-tilgængelighedstjek (BITV / EN 301 549)'),
 ('Craft CMS accessibility check', 'Craft CMS-tilgængelighedstjek'),
 ('Umbraco accessibility check', 'Umbraco-tilgængelighedstjek'),
 ('Compare all platforms side by side →', 'Sammenlign alle platforme side om side →'),
 ('Platform deep-dives:', 'Platform-deep-dives:'),
 ('← Back to Compliance Guides', '← Tilbage til Compliance Guides'),
 ('''Automated EAA/WCAG screening tool. No data leaves your
  browser except fetching the page you scan.''',
  '''Automatiseret EAA/WCAG-screeningværktøj. Ingen data forlader din
  browser undtagen hentningen af siden du scanner.'''),
 # JS strings
 ("out.innerHTML = '<p>Scanning <code>'+url.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</code> …</p>';",
  "out.innerHTML = '<p>Scanner <code>'+url.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</code> …</p>';"),
 ("throw new Error(data.error || 'Proxy returned error');",
  "throw new Error(data.error || 'Proxy returnerede en fejl');"),
 ("out.innerHTML = '<p><strong>Scan failed.</strong></p>'",
  "out.innerHTML = '<p><strong>Scan fejlede.</strong></p>'"),
 ("+'Cannot scan this page. Possible reasons: the site blocks automated fetchers, '",
  "+'Kan ikke scanne siden. Mulige årsager: sitet blokerer automatiske hentninger, '"),
 ("+'the URL is invalid, or the page is too large. Try the '",
  "+'URL\\u2019en er ugyldig, eller siden er for stor. Prøv '"),
 ("+'<a href=\"eaa-scanner-extension.zip\" download>browser extension</a> '",
  "+'<a href=\"eaa-scanner-extension.zip\" download>browserudvidelsen</a> '"),
 ("+'which runs directly on the live page.</p>'",
  "+'som kører direkte på den live side.</p>'"),
 ("'{n} image(s) missing alt text'", "'{n} billede(r) mangler alt-tekst'"),
 ("'{n} form field(s) without a label'", "'{n} formularfelt(er) uden mærkat'"),
 ("'{n} link(s) with no accessible text'", "'{n} link(s) uden tilgængelig tekst'"),
 ("'{n} button(s) with no accessible text'", "'{n} knap(p(er)) uden tilgængelig tekst'"),
 ("'{n} duplicate id value(s) (breaks label/aria references)'",
  "'{n} duplikeret(e) id-værdi(er) (bryder label/aria-referencer)'"),
 ("'{n} link(s) opening in a new window without warning'",
  "'{n} link(s) der åbner i nyt vindue uden advarsel'"),
 ("findings.push({sev:'error',msg:'page has no <title>'});",
  "findings.push({sev:'error',msg:'siden har ingen <title>'});"),
 ("findings.push({sev:'error',msg:'<html> lacks a lang attribute'});",
  "findings.push({sev:'error',msg:'<html> mangler en lang-attribut'});"),
 ("findings.push({sev:'warning',msg:'missing viewport meta tag'});",
  "findings.push({sev:'warning',msg:'manglende viewport-meta-tag'});"),
 ("findings.push({sev:'warning',msg:'no <h1> found'});",
  "findings.push({sev:'warning',msg:'ingen <h1> fundet'});"),
 ("'{n} heading level skip(s)'", "'{n} sprunget(t) overskriftsniveau(er)'"),
 ("'{n} iframe(s) without a title'", "'{n} iframe(s) uden titel'"),
 ("'{n} table(s) without header cells'", "'{n} tabel(ler) uden hovedceller'"),
 ("'{n} aria-hidden element(s) still focusable'", "'{n} aria-hidden-element(er) kan stadig fokuseres'"),
 ("IMG_ALT:'Fix: add alt=\"description\" to every meaningful image; use alt=\"\" for purely decorative ones.',",
  "IMG_ALT:'Fix: tilføj alt=\"beskrivelse\" til alle meningsbærende billeder; brug alt=\"\" til rent dekorative.',"),
 ("FORM_LABEL:'Fix: give every field a <label for=\"field-id\">, or an aria-label attribute.',",
  "FORM_LABEL:'Fix: giv hvert felt en <label for=\"felt-id\">, eller en aria-label-attribut.',"),
 ("LINK_TEXT:'Fix: add descriptive text inside the link, or aria-label if it is icon-only.',",
  "LINK_TEXT:'Fix: tilføj beskrivende tekst i linket, eller aria-label hvis det kun er et ikon.',"),
 ("BUTTON_TEXT:'Fix: add visible text or an aria-label to every button.',",
  "BUTTON_TEXT:'Fix: tilføj synlig tekst eller aria-label til hver knap.',"),
 ("DUP_ID:'Fix: make every id value unique on the page.',",
  "DUP_ID:'Fix: gør hver id-værdi unik på siden.',"),
 ("TARGET_BLANK:'Fix: warn users the link opens in a new window (e.g. \"(opens in new tab)\") and add rel=\"noopener\".',",
  "TARGET_BLANK:'Fix: advertér brugerne om at linket åbner i nyt vindue (fx \"(åbner i nyt faneblad)\") og tilføj rel=\"noopener\".',"),
 ("DOC_TITLE:'Fix: add a descriptive <title> in the <head>.',",
  "DOC_TITLE:'Fix: tilføj en beskrivende <title> i <head>.',"),
 ("HTML_LANG:'Fix: add lang to <html>, e.g. <html lang=\"en\">.',",
  "HTML_LANG:'Fix: tilføj lang til <html>, fx <html lang=\"da\">.',"),
 ("VIEWPORT:'Fix: add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">.',",
  "VIEWPORT:'Fix: tilføj <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">.',"),
 ("HEADING_H1:'Fix: add one descriptive <h1> as the main page heading.',",
  "HEADING_H1:'Fix: tilføj én beskrivende <h1> som sidens hovedoverskrift.',"),
 ("HEADING_SKIP:'Fix: do not skip heading levels — nest h2 under h1, h3 under h2, etc.',",
  "HEADING_SKIP:'Fix: spring ikke overskriftsniveauer over — h2 under h1, h3 under h2 osv.',"),
 ("IFRAME_TITLE:'Fix: add a title attribute describing the iframe content.',",
  "IFRAME_TITLE:'Fix: tilføj en title-attribut der beskriver iframens indhold.',"),
 ("TABLE_HEADER:'Fix: use <th> for header cells in data tables.',",
  "TABLE_HEADER:'Fix: brug <th> til hovedceller i datatabeller.',"),
 ("ARIA_HIDDEN_FOCUS:'Fix: remove aria-hidden from focusable elements, or add tabindex=\"-1\".',",
  "ARIA_HIDDEN_FOCUS:'Fix: fjern aria-hidden fra fokusbare elementer, eller tilføj tabindex=\"-1\".',"),
 ("CONTRAST:'Fix: darken the text colour or lighten the background until the contrast ratio is at least 4.5:1 (3:1 for large text). Check it at webaim.org/resources/contrastchecker.'};",
  "CONTRAST:'Fix: gør teksten mørkere eller baggrunden lysere til kontrastforholdet er mindst 4,5:1 (3:1 for stor tekst). Tjek det på webaim.org/resources/contrastchecker.'};"),
 ("Detected platform: ", "Registreret platform: "),
 ("most fixes are done right in '", "de fleste rettelser foretages direkte i '"),
 ("'s admin. Step-by-step: <a href=\"'+PLATFORM_GUIDES[plat]+'\">the free '",
  "'s admin. Trin for trin: <a href=\"'+PLATFORM_GUIDES[plat]+'\">den gratis '"),
 (" accessibility fix guide</a>.</div>'", "-tilgængelighedsguide</a>.</div>'"),
 ("error(s), ", "fejl, "),
 ("No issues found by automated checks.", "Ingen problemer fundet af de automatiske tjek."),
 ("Print / save as PDF", "Udskriv / gem som PDF"),
 ("Copy shareable link", "Kopiér delelink"),
 ("Link copied: ", "Link kopieret: "),
 ("Note: automated checks catch 30–40% of accessibility issues. See our ",
  "Bemærk: automatiserede tjek fanger 30–40 % af tilgængelighedsproblemerne. Se vores "),
 (" for the full manual process.</p>", " for hele den manuelle proces.</p>"),
]

for a,b in body:
    assert a in src, 'MISSING BODY: '+repr(a[:70])
    src = src.replace(a,b)

# hreflang links both ways + canonical
hreflang = ('<link rel="alternate" hreflang="da" href="https://hermes-passiv.pages.dev/scan-da">\n'
            '<link rel="alternate" hreflang="en" href="https://hermes-passiv.pages.dev/scan">\n'
            '<link rel="canonical" href="https://hermes-passiv.pages.dev/scan-da">\n')
src = src.replace('<script defer src="/track.js"></script>',
                  hreflang + '<script defer src="/track.js"></script>')

open('site/scan-da.html','w').write(src)
print('written', len(src), 'bytes')

# verify JSON-LD parses
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, re.S)
for b_ in blocks:
    d = json.loads(b_)
    assert d['@context']=='https://schema.org'
    print('JSON-LD OK:', d.get('@type'))
