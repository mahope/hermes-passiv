#!/usr/bin/env python3
"""Iteration 105: Three Danish blog pendants + JSON-LD fix + sitemap + cards.

Henter EN-indhold → danske pendanter med same safety pattern:
- JSON-LD valideres med json.loads
- sitemap duplikattjek
- internt link-tjek
- forsids-kort indsat
"""
import json, re, os
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'


def head(slug, lang, title, meta_desc, og_title, og_desc, headline):
    ld = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article', 'headline': headline,
        'description': meta_desc, 'url': f'{BASE}/blog/{slug}',
        'datePublished': TODAY, 'dateModified': TODAY,
        'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
        'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    })
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{meta_desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_desc}">
<meta property="og:url" content="{BASE}/blog/{slug}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{og_desc}">
<link rel="canonical" href="{BASE}/blog/{slug}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{ld}
</script>
<script defer src="/track.js"></script>
</head>'''


def footer_da():
    return '''<footer style="padding:32px 24px;">
    <p><a href="/">← Forside</a> · <a href="/scan-da">Gratis scanner</a> · <a href="/free-tools">Gratis værktøjer</a> · <a href="/#blog">Blog</a></p>
</footer>
</body>
</html>'''


# ── Blog 1: Accessibility Overlays & EAA ──────────────────────────────

def page_overlays():
    slug = 'tilgaengeligheds-overlays-eaa'
    desc = ('Accessibility overlays (accessiBe, UserWay m.fl.) lover WCAG-compliance '
            'med én linje kode. Hvad de faktisk gør, FTC-sagen mod accessiBe, '
            'søgsmålsdata, og hvorfor EAA kræver reelle rettelser.')
    h = head(slug, 'da',
             'Accessibility Overlays & EAA: Hvorfor "én linje kode" ikke er compliance',
             desc,
             'Accessibility overlays: Hvorfor de ikke gør dit site EAA-kompatibelt',
             'FTC-sag, søgsmål, EAA-positionen — og hvad der faktisk virker for små webbureauer.',
             'Accessibility Overlays & EAA: Hvorfor overlays ikke duer til compliance')
    body = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">BLOG · EAA</div>
    <h1>Accessibility Overlays &amp; EAA:<br>Hvorfor &quot;&eacute;n linje kode&quot; ikke er compliance</h1>
    <p class="subtitle">Overlay-widgets som accessiBe, UserWay og AudioEye markedsf&oslash;rer &oslash;jeblikkelig tilg&aelig;ngelighed for 300-600 kr/m&aring;neden. Her er hvad FTC fandt, hvad s&oslash;gsm&aring;lsdata viser, hvad Europa-Kommissionen siger, og hvad der faktisk virker for klient-sites.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">L&aelig;s guiden</a>
      <a href="/scan-da" class="btn-secondary">Scan din side gratis &rarr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; L&aelig;setid: 8 minutter</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="hvad-lover-overlays">Hvad overlays lover</h2>
    <p>Et accessibility overlay er en tredjeparts JavaScript-widget, du tilf&oslash;jer et website med et enkelt script-tag. Det lover at g&oslash;re siden tilg&aelig;ngelig automatisk: forst&oslash;rre tekst, generere alt-tekster med AI, tvinge tastaturfokus, justere kontrast. S&aelig;lgerne markedsf&oslash;rer det som &oslash;jeblikkelig WCAG-compliance &mdash; ofte med et &quot;accessibility shield&quot;-badge i footeren.</p>
    <p>Argumentet rammer godt hos sm&aring; bureauer og deres klienter: ingen udviklingstid, intet redesign, 300-600 kr/m&aring;neden i stedet for en audit til femcifret bel&oslash;b. Problemet er ikke at overlays intet g&oslash;r. Det er, at hvad de g&oslash;r, ikke matcher hvad de p&aring;st&aring;r &mdash; og i 2026 har b&aring;de myndigheder og domstole sl&aring;et det fast.</p>
    <div class="problem-cards">
      <div class="card"><h3>🤖 AI-auto-fix</h3><p>Overlays p&aring;st&aring;r at opdage og rette tilg&aelig;ngelighedsproblemer ved sideindl&aelig;sning. Automatisk detektion fanger kun en brøkdel af WCAG-fejl, og mange &quot;rettelser&quot; (auto-genererede alt-tekster, DOM-omskrivninger) bryder sk&aelig;rml&aelig;seradf&aelig;rd.</p></div>
      <div class="card"><h3>🛡️ Compliance-badges</h3><p>S&aelig;lgerne lader sites vise et certificerings-lignende badge, der antyder juridisk beskyttelse. Intet badge g&oslash;r et site kompatibelt &mdash; kun faktisk overensstemmelse med EN 301 549 / WCAG 2.1 AA g&oslash;r det.</p></div>
      <div class="card"><h3>💸 Løbende omkostning</h3><p>Et typisk bureau betaler 300-900 kr/m&aring;neden pr. site. Over tre &aring;r er det mere end en engangs-professionel oprydning af de fleste sm&aring; virksomhedssites.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="ftc-sag">FTC-sagen mod accessiBe</h2>
    <p>I januar 2025 anlagde den amerikanske forbundsmyndighed FTC sag mod accessiBe &mdash; den st&oslash;rste overlay-udbyder &mdash; for vildledende markedsf&oslash;ring. FTC h&aelig;vdede, at accessiBe fejlagtigt p&aring;stod, at deres widget kunne g&oslash;re websites WCAG-kompatible. I april 2025 p&aring;lagde en endelig kendelse accessiBe at betale 1 million dollars og forb&oslash;d dem at p&aring;st&aring;, at deres automatiserede produkter g&oslash;r noget site WCAG-kompatibelt uden dokumentation.</p>
    <p>T&aelig;nk over hvad det betyder: virksomheden der s&aelig;lger &quot;garanteret compliance&quot; blev selv sanktioneret for vildledende reklame. Hvis dit pitch til klienter inkluderer et overlays compliance-p&aring;stande, gentager du markedsf&oslash;ringssprog en konkurrencemyndighed allerede har kendt vildledende.</p>
    <p>Selvom FTC er amerikansk, har sagen global betydning: den er f&oslash;rste gang en tilsynsmyndighed juridisk fastsl&aring;r, at overlays ikke leverer det de lover. Danske og europ&aelig;iske klienter googler &quot;accessiBe FTC&quot; og stiller sp&oslash;rgsm&aring;l.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="sogsmaal-data">Søgsmålsdata</h2>
    <p>USA er der hvor overlay-fejl er bedst dokumenteret, fordi ADA-websites&oslash;gsm&aring;l anl&aelig;gges i tusindvis hvert &aring;r. I 2025 blev der indgivet 3.948 ADA-s&oslash;gsm&aring;l om webtilg&aelig;ngelighed &mdash; en stigning p&aring; n&aelig;sten 24 % i forhold til 2024. Cirka 20-25 % af disse rettede sig mod websites, der havde et accessibility overlay installeret p&aring; tidspunktet.</p>
    <p>Sags&oslash;gernes advokatfirmaer scanner aktivt efter overlays: widget'en signalerer at en virksomhed kendte til tilg&aelig;ngelighed og valgte en genvej. At installere et overlay reducerer ikke s&oslash;gsm&aring;lsrisikoen &mdash; brancherapporter tyder p&aring;, at det kan markere et site som et bedre m&aring;l.</p>
    <p>Mere end 900 tilg&aelig;ngelighedsprofessionelle og handicappede brugere har skrevet under p&aring; Overlay Fact Sheet, der fastsl&aring;r at overlays ofte g&oslash;r sites sv&aelig;rere at bruge med hj&aelig;lpeteknologi &mdash; ikke lettere. De mennesker, der er afh&aelig;ngige af sk&aelig;rml&aelig;sere, betaler prisen for &oslashdelagte auto-fixes.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="eaa-position">EAA-positionen</h2>
    <p>For bureauer i EU er den relevante lovgivning siden 28. juni 2025 European Accessibility Act (EAA). Den kr&aelig;ver at e-handel, bank, transport og andre omfattede tjenester overholder EN 301 549 &mdash; som inkorporerer WCAG 2.1 AA &mdash; og offentligg&oslash;r en tilg&aelig;ngelighedserkl&aelig;ring. Markedsoverv&aring;gningsmyndigheder kan kr&aelig;ve korrigerende handling; b&oslash;derammerne n&aring;r op til 3 millioner euro i nogle lande.</p>
    <p>Europa-Kommissionen har udtalt, at overlays alene ikke opn&aring;r EAA-compliance, og forbrugerorganisationer inklusive European Disability Forum har udsendt erkl&aelig;ringer imod at markedsf&oslash;re dem som compliance-l&oslash;sninger. Et overlay kan ikke rette de strukturelle problemer, EAA rammer: manglende tastaturst&oslash;tte i checkout-flow, utilg&aelig;ngelige dokumenter, um&aelig;rkede formularfelter i bookingsystemer. Det kr&aelig;ver kode&aelig;ndringer.</p>
    <p>Den praktiske position for et lille bureau er enkel: et overlay installeret oven p&aring; et ikke-konformt site efterlader sitet ikke-konformt. Pengene er brugt, erkl&aelig;ringen kan ikke afgives &aelig;rligt, og den underliggende risiko best&aring;r.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="hvad-virker">Hvad virker</h2>
    <p>Intet af dette betyder at automatiserede v&aelig;rkt&oslash;j er ubrugelige. Det betyder at de h&oslash;rer til det rigtige sted: detektion, ikke remediering. K&oslash;r en scanner for at finde problemer, ret dem s&aring; i koden. Den arbejdsgang koster intet ekstra og producerer et site der faktisk er kompatibelt.</p>
    <p>En realistisk plan for et lille bureaus portef&oslash;lje:</p>
    <p>&bull; Scan hvert klient-site for almindelige automatisk-detekterbare fejl (manglende alt-tekster, um&aelig;rkede inputs, kontrast, overskriftsstruktur).<br>
&bull; Ret dem i skabeloner og komponenter &eacute;n gang &mdash; hver side p&aring; temaet drager fordel.<br>
&bull; Test tastaturnavigation og &eacute;n sk&aelig;rml&aelig;ser-gennemgang af kritiske flows (checkout, kontakt, tilmelding).<br>
&bull; Offentligg&oslash;r en &aelig;rlig tilg&aelig;ngelighedserkl&aelig;ring pr. site.<br>
&bull; Gen-scan efter indholdsopdateringer eller nye plugins.</p>
    <p>Dette tager timer pr. site, ikke m&aring;neder &mdash; og i mods&aelig;tning til en widget-abonnement stopper det. N&aring;r du kan vise en ren scanning og en dokumenteret proces, kan du ogs&aring; priss&aelig;tte det som en serviceydelse i stedet for at betale for et badge.</p>
    <div class="problem-cards">
      <div class="card"><h3>🔍 Scan f&oslash;rst</h3><p>Vores gratis scanner tjekker 16+ WCAG-regler p&aring; enhver URL &mdash; WordPress, Shopify, Webflow eller h&aring;ndskrevet HTML. Ingen installation, ingen konto.</p></div>
      <div class="card"><h3>🧩 Ret p&aring; skabelonniveau</h3><p>De fleste fejl gentager sig p&aring; tv&aelig;rs af sider fordi de sidder i temaet. &Eacute;n komponentrettelse fjerner hundredvis af fund.</p></div>
      <div class="card"><h3>📝 Dokument&eacute;r &aelig;rligt</h3><p>En tilg&aelig;ngelighedserkl&aelig;ring baseret p&aring; reelle scanningsresultater beskytter dig langt mere end et overlay-badge nogensinde gjorde.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede sp&oslash;rgsm&aring;l</h2>
    <div class="problem-cards">
      <div class="card"><h3>Virker accessibility overlays overhovedet?</h3><p>De &aelig;ndrer nogle overfladeegenskaber (tekstst&oslash;rrelse, kontrast, noget fokusadf&aelig;rd) men kan ikke p&aring;lideligt rette de problemer der betyder mest: semantisk HTML, tastaturf&aelig;lder, sk&aelig;rml&aelig;serkompatibilitet og tilg&aelig;ngelige arbejdsgange. Automatiserede v&aelig;rkt&oslash;jer opdager langt mindre end manuel test, og overlays bryder nogle gange hj&aelig;lpeteknologi yderligere. Konsensus blandt praktikere, handicappede brugere og nu FTC er at de ikke leverer compliance.</p></div>
      <div class="card"><h3>Er det ulovligt at installere et overlay?</h3><p>Nej. At k&oslash;be og installere et overlay er lovligt. Problemet er at stole p&aring; det til compliance: under EAA skal selve sitet overholde EN 301 549 uanset hvilke scripts der k&oslash;rer, og s&aelig;lgerne m&aring; ikke l&aelig;ngere lovligt p&aring;st&aring; at deres produkt garanterer WCAG-compliance uden dokumentation.</p></div>
      <div class="card"><h3>Hvad skete der med accessiBe og FTC?</h3><p>I januar 2025 anlagde FTC sag mod accessiBe for vildledende markedsf&oslash;ring. April 2025-kendelsen indebar en b&oslash;de p&aring; 1 million dollars og forb&oslash;d accessiBe at p&aring;st&aring;, at deres produkter g&oslash;r websites WCAG-kompatible uden dokumentation.</p></div>
      <div class="card"><h3>B&oslash;r jeg fjerne et overlay en klient allerede har?</h3><p>Evalu&eacute;r det som enhver afh&aelig;ngighed: scan siden med og uden overlay aktiveret. Hvis overlayet introducerer fejl eller blokerer reelle rettelser, anbefal fjernelse og l&aelig;g budgettet i skabelon-niveau remediering &mdash; hvilket normalt er billigere over tre &aring;r alligevel. Fjern aldrig noget under aktiv h&aring;ndh&aelig;velseskorrespondance uden at dokumentere beslutningen.</p></div>
      <div class="card"><h3>Forbyder EAA overlays?</h3><p>Nej, men Europa-Kommissionen har gjort klart at overlays alene ikke opfylder EAA-kravene, og forbruger- og handikaporganisationer har formelt modsat sig, at de markedsf&oslash;res som compliance-l&oslash;sninger. Overensstemmelse m&aring;les mod EN 301 549 / WCAG 2.1 AA, ikke mod om en widget er til stede.</p></div>
      <div class="card"><h3>Hvad er den billigste vej til reel EAA-compliance for et lille site?</h3><p>Automatisk scanning (gratis), skabelon-niveau rettelser af de fejl den finder, en tastatur- og sk&aelig;rml&aelig;ser-test af kritiske flows, og en &aelig;rlig tilg&aelig;ngelighedserkl&aelig;ring. For de fleste sm&aring; virksomhedssites er det dages arbejde, ikke m&aring;neder &mdash; og det producerer noget et overlay aldrig kan: et site der rent faktisk virker med hj&aelig;lpeteknologi.</p></div>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/scan-da" class="btn-primary">Scan din side gratis &rarr;</a>
      &nbsp;&nbsp;
      <a href="/blog/eaa-accessibility-checklist" class="btn-secondary">EAA-tjeklisten &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Relaterede guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">EAA</span><h3><a href="/blog/eaa-accessibility-checklist" style="color:var(--color-accent);text-decoration:none;">EAA-tjekliste: 10 trin for WordPress</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">WCAG</span><h3><a href="/blog/wcag-22-aendringer" style="color:var(--color-accent);text-decoration:none;">WCAG 2.2: Hvad er &aelig;ndret (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">EAA</span><h3><a href="/blog/eaa-haandhaevelse-2026" style="color:var(--color-accent);text-decoration:none;">EAA-h&aring;ndh&aelig;velse 2026 (dansk)</a></h3></div>
    </div>
  </div>
</section>
''' + footer_da()
    return slug, h + body


# ── Blog 2: WCAG 2.2 Changes ──────────────────────────────────────────

def page_wcag22():
    slug = 'wcag-22-aendringer'
    desc = ('WCAG 2.2 i 2026: de 9 nye successkriterier for tilg&aelig;ngelighed, '
            'hvad der blev fjernet, og hvordan sm&aring; webbureauer opdaterer '
            'klient-sites til EAA-standard uden et compliance-team.')
    h = head(slug, 'da',
             'WCAG 2.2: Hvad er ændret og hvad det betyder for dine klienter',
             desc,
             'WCAG 2.2: De 9 nye kriterier & hvad du skal gøre',
             'Fokusstørrelse, målstørrelse, tilgængelig autentifikation — de 9 nye krav og en praktisk plan for at opdatere klient-sites.',
             'WCAG 2.2: Hvad er ændret — guide til små webbureauer')
    body = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">BLOG · EAA &amp; WCAG</div>
    <h1>WCAG 2.2:<br>Hvad er &aelig;ndret &amp; hvad det betyder for dine klienter</h1>
    <p class="subtitle">De 9 nye successkriterier, dem der blev fjernet, og en praktisk plan for at bringe klient-sites up to date &mdash; intet compliance-team kr&aelig;ves.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">L&aelig;s guiden</a>
      <a href="#nye-kriterier" class="btn-secondary">Se de 9 nye kriterier &darr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; L&aelig;setid: 7 minutter</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="hvorfor-nu">Hvorfor WCAG 2.2 betyder noget nu</h2>
    <p>WCAG 2.2 blev en W3C-anbefaling i oktober 2023 og er nu referencesstandarden for European Accessibility Act (EAA), der tr&aring;dte i kraft juni 2025. Hvis dine klienter s&aelig;lger produkter eller tjenester online i EU, forventes deres sites at overholde mindst WCAG 2.1 AA &mdash; og WCAG 2.2 er der hvor standarden er p&aring; vej hen.</p>
    <p>WCAG 2.2 erstatter ikke 2.1 &mdash; det udvider den. Et site der overholder 2.2 AA overholder automatisk 2.1 AA. Det g&oslash;r opgradering til det sikreste langsigtede m&aring;l for ethvert bureau, der vedligeholder klient-sites i EU.</p>
    <div class="problem-cards">
      <div class="card"><h3>⚖️ EAA-h&aring;ndh&aelig;velse</h3><p>Siden juni 2025 skal e-handel, bank, transport og teleservices i EU v&aelig;re tilg&aelig;ngelige. Nationale markedsoverv&aring;gningsmyndigheder kan b&oslash;de- l&aelig;gge ikke-konforme virksomheder.</p></div>
      <div class="card"><h3>🎯 9 nye kriterier</h3><p>WCAG 2.2 tilf&oslash;jer ni nye successkriterier med fokus p&aring; kognitiv tilg&aelig;ngelighed, mobilinteraktion og formularer &mdash; omr&aring;der hvor de fleste sites fejler i dag.</p></div>
      <div class="card"><h3>🗑️ 4 fjernede</h3><p>Fire gamle kriterier blev fjernet fordi de overlappede med andre. Sites bygget til 2.0 kan opleve at nogle krav er forsvundet &mdash; men ingen er blevet sv&aelig;rere uden erstatning.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="nye-kriterier">De 9 nye successkriterier</h2>
    <p>Her er hvert nyt kriterium p&aring; niveau A og AA, med hvad det betyder i praksis for de sites du bygger:</p>
    <p><strong>2.4.11 Focus Not Obscured (Minimum) &mdash; AA.</strong> N&aring;r et element modtager tastaturfokus, m&aring; det ikke skjules af forfatterskabt indhold som sticky headers, cookie-bannere eller chat-widgets. Test: tabuler gennem siden og tjek at intet d&aelig;kker det fokuserede element.</p>
    <p><strong>2.5.7 Dragging Movements &mdash; AA.</strong> Enhver handling der udf&oslash;res ved at tr&aelig;kke (sliders, drag-to-reorder, kort) skal ogs&aring; kunne udf&oslash;res med et enkelt klik eller tryk. S&oslash;rg for knapper som alternativ.</p>
    <p><strong>2.5.8 Target Size (Minimum) &mdash; AA.</strong> Interaktive m&aring;l skal v&aelig;re mindst 24&times;24 CSS-pixels, eller have tilstr&aelig;kkelig afstand omkring sig. Dette dr&aelig;ber sm&aring; icon-only-knapper og trang mobilnavigation.</p>
    <p><strong>3.2.6 Consistent Help &mdash; A.</strong> Hvis et site tilbyder hj&aelig;lp (supportlink, chat), skal det vises samme sted p&aring; alle sider. At flytte hj&aelig;lpelinks mellem sider fejler.</p>
    <p><strong>3.3.7 Redundant Entry &mdash; A.</strong> Brugere m&aring; ikke skulle indtaste samme information to gange i &eacute;n proces. Autoudfyld tidligere indtastede data i flertrins-checkouts og formularer.</p>
    <p><strong>3.3.8 Accessible Authentication (Minimum) &mdash; AA.</strong> Login m&aring; ikke kr&aelig;ve kognitive funktionstests &mdash; det er tilladt at huske adgangskoder, men puslespil, genindtastning af koder fra billeder eller transkriptionstests er ikke. Tillad inds&aelig;tning i adgangskodefelter og underst&oslash;t password managers.</p>
    <div class="problem-cards">
      <div class="card"><h3>⌨️ Fokussynlighed</h3><p>2.4.11 + 2.4.13 betyder tilsammen at sticky headers ikke m&aring; sluge tastaturfokus. Rettelsen er typisk scroll-padding-top i CSS &mdash; billigt at implementere, let at demonstrere for klienter.</p></div>
      <div class="card"><h3>📱 Mobil m&aring;lst&oslash;rrelse</h3><p>2.5.8 fanger de tommelfinger-tr&aelig;thedsproblemer som rigtige brugere klager over. F&aring; tilg&aelig;ngelighedsopgraderinger til at ligne UX-forbedringer n&aring;r du taler med klienter.</p></div>
      <div class="card"><h3>🔐 Login-flow</h3><p>3.3.8 p&aring;virker enhver klient med et login. CAPTCHA'er der kr&aelig;ver transkription er en direkte fejl &mdash; skift til usynlige risikobaserede checks.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="hvad-fjernet">Hvad blev fjernet</h2>
    <p>Fire kriterier fra tidligere versioner blev fjernet i 2.2 fordi de duplikerede andre eller viste sig ikke-testbare:</p>
    <p><strong>4.1.1 Parsing</strong> &mdash; fjernet; duplikerede ID'er og misdannet markup bryder stadig hj&aelig;lpeteknologi, men kravet er d&aelig;kket af andre kriterier og browsers parsing-adf&aelig;rd. Ret duplikerede ID'er alligevel (vores scanner tjekker for dem).</p>
    <p>Andre krav blev reorganiseret: 2.4.10 Section Headings og dele af farvekontrast-vejledningen blev konsolideret frem for strammet.</p>
    <p>Praktisk konsekvens: en audit mod 2.0 vil liste fejl der ikke l&aelig;ngere eksisterer, og overse fejl der g&oslash;r. Genbas&eacute;r dine audits mod 2.2.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="opdatering">Sådan opdaterer du klient-sites</h2>
    <p>De fleste sites fejler de nye kriterier i de samme h&aring;ndfulde steder. Arbejd gennem denne prioritetsorden:</p>
    <p><strong>1. Sticky headers og overlays.</strong> Tilf&oslash;j scroll-padding-top svarende til header-h&oslash;jde, og s&oslash;rg for at cookie-bannere lukker helt s&aring; de aldrig f&aelig;lder fokus.</p>
    <p><strong>2. Touch-m&aring;l.</strong> Gennemg&aring; ikonknapper, sociale ikoner og paginering. &Oslash;g padding til minimum 24&times;24 px. P&aring; de fleste sites er dette ren CSS.</p>
    <p><strong>3. Tr&aelig;k-alternativer.</strong> Enhver sorterbar liste eller slider har brug for synlige klik-/tryk-kontroller. Mange komponentbiblioteker leverer dette bag et flag &mdash; sl&aring; det til.</p>
    <p><strong>4. Formularer og checkouts.</strong> Autoudfyld gentagne felter, tillad inds&aelig;tning overalt, fjern puzzle-CAPTCHA'er.</p>
    <p><strong>5. Gen-audit.</strong> K&oslash;r en scanning (vores er gratis, ovenfor), ret hvad den finder, og spot-tjek de nye kriterier manuelt. Dokumenter overensstemmelsesp&aring;stande mod 2.2 AA fremadrettet.</p>
    <div class="problem-cards">
      <div class="card"><h3>🆓 Gratis scanner</h3><p>Vores scanner tjekker alt-tekster, labels, kontrast, target sizes, duplikerede ID'er og mere &mdash; inds&aelig;t en URL, f&aring; en score p&aring; sekunder. Ingen tilmelding.</p></div>
      <div class="card"><h3>📚 Platform-guides</h3><p>Vi har trinvise fix-guides til WordPress, Shopify, Webflow, Wix, Squarespace, Drupal, Joomla og flere &mdash; se guides-sektionen p&aring; forsiden.</p></div>
      <div class="card"><h3>📄 Erkl&aelig;ringsgenerator</h3><p>Efter rettelse kan du generere en tilg&aelig;ngelighedserkl&aelig;ring til din klient p&aring; minutter med vores gratis v&aelig;rkt&oslash;j.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede sp&oslash;rgsm&aring;l</h2>
    <div class="problem-cards">
      <div class="card"><h3>Er WCAG 2.2 lovpligtigt i EU?</h3><p>EAA refererer til harmoniserede standarder baseret p&aring; WCAG 2.1 AA i dag, men EN 301 549 opdateres mod 2.2. At overholde 2.2 AA nu betyder at du er foran kravet i stedet for at jagte det.</p></div>
      <div class="card"><h3>G&aelig;lder WCAG 2.2 for mine klienter uden for EU?</h3><p>Tilsvarende tendenser findes globalt &mdash; Section 508 i USA, EN 301 549-procurement-regler og nationale love der refererer til WCAG. At bygge til 2.2 AA opfylder n&aelig;sten alle.</p></div>
      <div class="card"><h3>Vi bestod lige en 2.1-audit. Er vi kompatible med 2.2?</h3><p>Ikke automatisk. Fokus-skjulning, m&aring;lst&oslash;rrelse og tilg&aelig;ngelig autentifikation er almindelige nye fejl p&aring; sites der best&aring;r 2.1. Budget&aelig;r en lille re-audit-runde.</p></div>
      <div class="card"><h3>Hvilket nyt kriterium knuser flest sites?</h3><p>Target Size (2.5.8). Icon-only-knapper under 24px er overalt &mdash; sociale delingsr&aelig;kker, carousel-pile, mobilmenuer. Det er ogs&aring; den billigste klasse af rettelser.</p></div>
      <div class="card"><h3>Tjekker jeres gratis scanner WCAG 2.2?</h3><p>Den automatiserer det maskintjekbare delm&aelig;ngde (alt-tekster, labels, kontrast, duplikerede ID'er, viewport, overskrifter og mere). Nogle 2.2-kriterier &mdash; tr&aelig;kbev&aelig;gelser, redundant indtastning &mdash; kr&aelig;ver manuel test, og vores guider f&oslash;rer dig gennem disse tjek.</p></div>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/scan-da" class="btn-primary">Test ethvert site gratis &rarr;</a>
      &nbsp;&nbsp;
      <a href="/blog/eaa-accessibility-checklist" class="btn-secondary">EAA-tjeklisten &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Relaterede guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">EAA</span><h3><a href="/blog/eaa-accessibility-checklist" style="color:var(--color-accent);text-decoration:none;">EAA-tjekliste: 10 trin for WordPress</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">OVERLAYS</span><h3><a href="/blog/tilgaengeligheds-overlays-eaa" style="color:var(--color-accent);text-decoration:none;">Accessibility overlays & EAA (dansk)</a></h3></div>
    </div>
  </div>
</section>
''' + footer_da()
    return slug, h + body


# ── Blog 3: NIS2 Supply Chain Security ────────────────────────────────

def page_nis2_supply():
    slug = 'nis2-leverandoerkaede-sikkerhed'
    desc = ('NIS2 artikel 21 g&oslash;r leverand&oslash;rsikkerhed til en juridisk pligt. '
            'Hvad sm&aring; danske webbureauer skal g&oslash;re ved leverand&oslash;rrisici, '
            'underdatabehandlere og klientkontrakter i 2026.')
    h = head(slug, 'da',
             'NIS2 leverandørkædesikkerhed for webbureauer — gratis guide',
             desc,
             'NIS2: Leverandørkædesikkerhed for dit webbureau',
             'Artikel 21(2)(d) gør hosting, plugins og freelancere til et compliancespørgsmål. Praktisk vendor assessment, kontraktklausuler og 5-trins plan.',
             'NIS2 leverandørkædesikkerhed: praktisk guide til små webbureauer')
    body = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">BLOG · NIS2</div>
    <h1>NIS2 Leverand&oslash;rk&aelig;desikkerhed<br>for Webbureauer</h1>
    <p class="subtitle">Artikel 21 g&oslash;r dine hosting-udbydere, plugins og freelancere til et compliance-sp&oslash;rgsm&aring;l. Her er hvad et lille bureau faktisk skal g&oslash;re &mdash; uden et enterprise GRC-system.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">L&aelig;s guiden</a>
      <a href="#hvorfor" class="btn-secondary">Hvorfor leverand&oslash;rk&aelig;den? &darr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; L&aelig;setid: 8 minutter</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="hvorfor">Hvorfor leverandørkæden er dit problem</h2>
    <p>De fleste sm&aring; webbureauer t&aelig;nker p&aring; NIS2 som en regel om deres egen sikkerhed: patch dine servere, aktiv&eacute;r MFA, hav en incidentplan. Det er halvdelen. Den anden halvdel &mdash; og den del regulatorerne i stigende grad fokuserer p&aring; &mdash; er artikel 21(2)(d), som g&oslash;r <strong>leverand&oslash;rsikkerhed</strong> til et eksplicit juridisk krav for enhver omfattet enhed.</p>
    <p>For et webbureau er leverand&oslash;rk&aelig;den ikke et abstrakt begreb. Det er din hosting-udbyder, dit CDN, dine plugin-leverand&oslash;rer, den freelance-udvikler der havde admin-adgang sidste for&aring;r, e-mail-platformen du konfigurerer for klienter, og backup-tjenesten ingen har tjekket i to &aring;r. Under NIS2 er sikkerheden hos disse leverand&oslash;rer dit problem &mdash; og du skal kunne dokumentere hvordan du styrer den risiko.</p>
    <div class="problem-cards">
      <div class="card"><h3>📜 Artikel 21(2)(d)</h3><p>Enheder skal h&aring;ndtere sikkerhedsrisici relateret til &quot;forholdet mellem enheden og dens direkte leverand&oslash;rer eller tjenesteudbydere.&quot; Det er en direkte juridisk pligt, ikke best practice.</p></div>
      <div class="card"><h3>🔗 Du sidder i to kæder</h3><p>Som bureau sidder du i midten: dine klienter er afh&aelig;ngige af dig, og du er afh&aelig;ngig af snesevis af leverand&oslash;rer. NIS2-forpligtelser g&aelig;lder i begge retninger.</p></div>
      <div class="card"><h3>🧾 Bevis tæller</h3><p>Tilsynsmyndigheder forventer dokumenterede leverand&oslash;rvurderinger, kontraktklausuler og exit-planer &mdash; ikke et politikdokument der siger &quot;vi v&aelig;lger anerkendte leverand&oslash;rer.&quot;</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="omfattet">Er dit bureau omfattet?</h2>
    <p>NIS2 klassificerer omfattede organisationer som &quot;vigtige&quot; eller &quot;andre vigtige&quot; baseret p&aring; sektor og st&oslash;rrelse. Mange sm&aring; bureauer falder uden for direkte omfattelse &mdash; et 5-personers studie der bygger marketingsites er normalt ikke selv en omfattet enhed.</p>
    <p>Men at v&aelig;re uden for omfattelse betyder ikke at leverand&oslash;rk&aelig;dens regler ikke r&oslash;rer dig. Tre praktiske grunde til at omfattede klienter alligevel skubber NIS2-krav ned til deres bureauer:</p>
    <p><strong>1. Indk&oslash;bssp&oslash;rgeskemaer.</strong> Ethvert bureau der betjener mellemstore eller store klienter, offentlige myndigheder eller virksomheder i energi, sundhed, finans, transport eller digital infrastruktur ser allerede sikkerhedssp&oslash;rgeskemaer der refererer til NIS2. &quot;Beskriv jeres leverand&oslash;rstyringsproces&quot; er nu et standardfelt.</p>
    <p><strong>2. Kontraktklausuler.</strong> Omfattede klienter skal styre sikkerheden hos deres egne leverand&oslash;rer &mdash; og deres webbureau er en leverand&oslash;r. Forvent kontraktlige sikkerhedskrav, revisionsrettigheder og incident-meldepligter i nye og fornyede aftaler.</p>
    <p><strong>3. K&aelig;deansvar ved h&aelig;ndelser.</strong> N&aring;r et brud hos et bureau uds&aelig;tter en omfattet klient, b&aelig;rer klienten stadig sine egne NIS2-pligter &mdash; 24-timers tidlig advarsel, 72-timers notifikation. Bureauer der ikke kan underst&oslash;tte den tidslinje mister disse klienter.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="din-kæde">Din faktiske leverandørkæde</h2>
    <p>F&oslash;r du kan styre leverand&oslash;rrisiko, skal du vide hvad din leverand&oslash;rk&aelig;de faktisk er. De fleste bureauer har aldrig skrevet den ned. Kortl&aelig;g den p&aring; &eacute;n eftermiddag:</p>
    <div class="problem-cards">
      <div class="card"><h3>🖥️ Infrastruktur</h3><p>Hosting (shared, VPS, managed WP), DNS, CDN, e-mail-levering. Disse r&oslash;rer hvert klient-site &mdash; &eacute;t kompromis spreder sig overalt.</p></div>
      <div class="card"><h3>🧩 Software</h3><p>CMS-kernel, plugins, temaer, biblioteker. Tredjepartskode er den mest almindelige brudvektor for sm&aring; sites &mdash; et enkelt forladt plugin kan v&aelig;re indgangen.</p></div>
      <div class="card"><h3>👥 Personer</h3><p>Freelancere, underleverand&oslash;rer, tidligere medarbejdere med levende adgange. Adgang uden kontrakt og offboarding-proces er ustyret risiko.</p></div>
      <div class="card"><h3>☁️ Tjenester</h3><p>Analyse, formularbehandlere, betalingsgateways, backup-lagring, CRM-v&aelig;rkt&oslash;jer du konfigurerer for klienter. Hver enkelt behandler klientdata p&aring; din konfiguration.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="vendor-vurdering">Vendor assessment</h2>
    <p>Du beh&oslash;ver ikke et enterprise GRC-system. Et regneark med &eacute;n r&aelig;kke pr. leverand&oslash;r og fem kolonner d&aelig;kker artikel 21 for et lille bureau:</p>
    <p><strong>1. Hvilke data og adgang har denne leverand&oslash;r?</strong> Klienters persondata? Admin-legitimationsoplysninger? Produktionsservere? Klassific&eacute;r: kritisk, vigtig, mindre.</p>
    <p><strong>2. Hvad er deres sikkerhedsniveau?</strong> Har de en trust-page, ISO 27001- eller SOC 2-certificering, en DBA, en brudhistorik? For store udbydere (Cloudflare, AWS, Google) er det et tjek p&aring; ti minutter. For en plugin-leverand&oslash;r til 200 kr/&aring;r kan det &aelig;rlige svar v&aelig;re &quot;ukendt&quot; &mdash; hvilket i sig selv er en risikovurdering.</p>
    <p><strong>3. Hvad siger kontrakten?</strong> Er der en databehandleraftale (GDPR art. 28), sikkerhedsforpligtelser, brudnotifikationsvilk&aring;r og en opsigelsesret? For kritiske leverand&oslash;rer er ingen kontrakt lig med intet styret forhold.</p>
    <p><strong>4. Hvad sker der hvis de svigter?</strong> Har du en exit-vej &mdash; eksporter, alternative udbydere, DNS du kontrollerer? En leverand&oslash;r du ikke kan forlade, er en leverand&oslash;r du ikke kan styre.</p>
    <p><strong>5. Hvorn&aring;r blev dette sidst tjekket?</strong> S&aelig;t en &aring;rlig gennemgangsdato. Et risikoregister der aldrig genbes&oslash;ges, er teater.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="kontraktklausuler">Kontraktklausuler</h2>
    <p>Vurderingen siger dig hvor du st&aring;r; kontrakter er hvad der g&oslash;r risikoen styrbar. Fire klausuler at standardisere i dine egne klient- og leverand&oslash;raftaler:</p>
    <p><strong>Med dine leverand&oslash;rer (n&aring;r du har forhandlingsstyrke):</strong> brudnotifikation inden for 24-48 timer, dokumenterede sikkerhedsforanstaltninger, underdatabehandler-transparens og sletning af data ved exit. Hos hyperscalere tager du deres standardvilk&aring;r &mdash; hvilket er fint, og i sig selv v&aelig;rd at dokumentere som en accepteret risiko.</p>
    <p><strong>Med dine klienter:</strong> defin&eacute;r pr&aelig;cis hvilke systemer du er ansvarlig for at sikre (og hvilke der forbliver klientens), en sikkerhedskontakt- og incident-samarbejdsklausul s&aring; du kan underst&oslash;tte deres 24/72-timers NIS2-tidslinjer, en change management-klausul for overdragelse af legitimationsoplysninger, og en ansvarsbegr&aelig;nsning der er proportional med et lille bureau &mdash; ikke ubegr&aelig;nset.</p>
    <p>Hvis du betjener omfattede klienter, afstem din incident-meldepligt med deres regulatoriske ur. &quot;Vi vil fort&aelig;lle dig inden for 24 timer efter bekr&aelig;ftet brud&quot; er en klausul der vinder enterprise-arbejde.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="angrebsflade">Reducer angrebsfladen</h2>
    <p>Den billigste leverand&oslash;rrisikobehandling er at have mindre leverand&oslash;rk&aelig;de. Fire tr&aelig;k der kapper reel risiko for et typisk bureau p&aring; under en uge:</p>
    <p><strong>1. Dr&aelig;b ubrugt adgang.</strong> Gennemg&aring; admin-konti p&aring; tv&aelig;rs af hosting, DNS, klient-sites og koderepositorier. Fjern enhver konto der tilh&oslash;rer personer der ikke l&aelig;ngere arbejder med dig. Dette er den enkelt h&oslash;jeste timel&oslash;nsinvestering i bureausikkerhed.</p>
    <p><strong>2. Standardis&eacute;r din stak.</strong> Hvert unikt plugin, tema og tjeneste multiplicerer din vurderingsbyrde. En kort tilladelsesliste &mdash; &quot;disse er de plugins og udbydere vi bruger&quot; &mdash; g&oslash;r leverand&oslash;rstyring overskuelig og klient-sikkerhedsgennemgange hurtigere.</p>
    <p><strong>3. Hold &oslash;je med forladt software.</strong> S&aelig;t en regel: ethvert plugin eller dependency uden en release i 12+ m&aring;neder udskiftes eller isoleres. Forladte komponenter er den klassiske sm&aring;-site-brudvektor.</p>
    <p><strong>4. Adskil n&oslash;glerne.</strong> Brug en password manager med per-klient-vaults og MFA overalt det underst&oslash;ttes. &Eacute;t f&aelig;lles regneark med klient-legitimationsoplysninger er en leverand&oslash;rh&aelig;ndelse der venter p&aring; at ske.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="regulator-forventning">Hvad regulatorer forventer</h2>
    <p>Hvis en tilsynsmyndighed nogensinde sp&oslash;rger &mdash; eller en omfattet klient reviderer dig &mdash; er forventningen proportional, dokumenteret praksis, ikke perfektion. Dit bevis-mappe b&oslash;r indeholde:</p>
    <p>&bull; Et aktuelt leverand&oslash;rregister med kritikalitetsvurderinger og gennemgangsdatoer<br>
&bull; Underskrevne DBA'er med enhver leverand&oslash;r der behandler persondata<br>
&bull; Standardkontraktklausuler (dine og accepterede tredjepartsvilk&aring;r)<br>
&bull; En adgangskontrolpolitik: hvem har admin-adgang, hvordan gives og tilbagekaldes det<br>
&bull; En incident-responsplan der inkluderer leverand&oslash;r-originerede h&aelig;ndelser og underst&oslash;tter klienters notifikationstidslinjer</p>
    <p>Det er seks dokumenter, hvoraf de fleste et lille bureau burde have alligevel for GDPR. NIS2 leverand&oslash;rk&aelig;de-compliance, gjort pragmatisk, er i vid udstr&aelig;kning det papirarbejde du allerede skyldte under databeskyttelsesreglerne &mdash; udvidet til sikkerhed, og faktisk vedligeholdt.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede sp&oslash;rgsm&aring;l</h2>
    <div class="problem-cards">
      <div class="card"><h3>Mit bureau er for lille til at v&aelig;re NIS2-omfattet. Hvorfor skal jeg bekymre mig?</h3><p>Tre grunde: omfattede klienter skubber NIS2-afledte sikkerhedskrav ned til deres leverand&oslash;rer gennem kontrakter og indk&oslash;bssp&oslash;rgeskemaer; incident-response-forventninger (24/72-timers tidslinjer) kaskaderer gennem k&aelig;den; og sikkerhedspraksissen i sig selv &mdash; leverand&oslash;rregistre, adgangsaudits, kontraktklausuler &mdash; beskytter dig mod de brud der faktisk dr&aelig;ber sm&aring; bureauer.</p></div>
      <div class="card"><h3>Hvad kr&aelig;ver artikel 21 pr&aelig;cist for leverand&oslash;rk&aelig;den?</h3><p>Artikel 21(2)(d) kr&aelig;ver at omfattede enheder h&aring;ndterer sikkerhedsrisici i forhold til direkte leverand&oslash;rer og tjenesteudbydere. I praksis forventer regulatorer: identifikation af kritiske leverand&oslash;rer, vurdering af deres sikkerhed, indlejring af sikkerhedskrav i kontrakter og en dokumenteret proces der gennemg&aring;s regelm&aelig;ssigt. Proportionalitet g&aelig;lder &mdash; en 10-personers virksomhed m&aring;les ikke mod en bank.</p></div>
      <div class="card"><h3>Skal jeg vurdere hvert eneste plugin og SaaS-v&aelig;rkt&oslash;j?</h3><p>Vurder efter kritikalitet, ikke udt&oslash;mmende. Leverand&oslash;rer med adgang til klientdata, produktionssystemer eller admin-rettigheder f&aring;r en fuld gennemgang; et farvev&aelig;lger-plugin g&oslash;r ikke. Et tretrins-rating (kritisk / vigtig / mindre) holder registeret p&aring; en h&aring;ndterbar st&oslash;rrelse &mdash; typisk 10-25 r&aelig;kker for et lille bureau.</p></div>
      <div class="card"><h3>Hvad er den st&oslash;rste leverand&oslash;rrisiko for et lille webbureau?</h3><p>Tredjepartskode og dv&aelig;lende adgang. Forladte plugins og afh&aelig;ngigheder er den mest almindelige brudvektor p&aring; sm&aring; sites, og glemte admin-konti tilh&oslash;rende tidligere freelancere er det mest almindelige audit-fund. Begge dele kan rettes p&aring; en dag.</p></div>
      <div class="card"><h3>Kan jeg genbruge mit GDPR-leverand&oslash;rregister til NIS2?</h3><p>Stort set ja. Dine art. 30-registreringer og DBA-inventar lister allerede de fleste databehandlere. Udvid hver entry med en sikkerhedskritikalitetsvurdering, kontraktlige sikkerhedsklausuler og en exit-plan. GDPR-registeret d&aelig;kker data; NIS2-registeret d&aelig;kker data og systemer.</p></div>
      <div class="card"><h3>Hvor ofte b&oslash;r vi gennemg&aring; leverand&oslash;rer?</h3><p>&Aring;rligt for kritiske leverand&oslash;rer, og straks ved enhver trigger-h&aelig;ndelse: en leverand&oslash;rs brudmeddelelse, en kontraktfornyelse, et ejerskifte eller en st&oslash;rre arkitekturl&aelig;ndring p&aring; din side. S&aelig;t gennemgangsdatoen i registeret s&aring; den er synlig, ikke i nogens hukommelse.</p></div>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/#products" class="btn-primary">Se NIS2-e-bogen &rarr;</a>
      &nbsp;&nbsp;
      <a href="/blog/nis2-guide-da" class="btn-secondary">NIS2-guiden (dansk) &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Relaterede guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">NIS2</span><h3><a href="/blog/nis2-guide-da" style="color:var(--color-accent);text-decoration:none;">NIS2-guiden (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">INCIDENT</span><h3><a href="/blog/nis2-incident-report-checklist" style="color:var(--color-accent);text-decoration:none;">NIS2 Incident Report Checklist & Template</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">GDPR</span><h3><a href="/blog/gdpr-webbureau-da" style="color:var(--color-accent);text-decoration:none;">GDPR-guiden: webbureauets rolle (dansk)</a></h3></div>
    </div>
  </div>
</section>
''' + footer_da()
    return slug, h + body


# ── Sitemap ──────────────────────────────────────────────────────────

def update_sitemap(slugs):
    p = f'{SITE}/sitemap.xml'
    c = open(p).read()
    add = ''.join(f'  <url><loc>{BASE}/blog/{s}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'
                  for s in slugs)
    assert all(f'/blog/{s}</loc>' not in c for s in slugs), 'slug already in sitemap'
    c = c.replace('</urlset>', add + '</urlset>')
    open(p, 'w').write(c)


# ── Frontpage cards ─────────────────────────────────────────────────

CARDS = {
    'tilgaengeligheds-overlays-eaa':
'''      <div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">
        <h3><a href="/blog/tilgaengeligheds-overlays-eaa" style="color:inherit;text-decoration:none;">Accessibility overlays & EAA (dansk)</a></h3>
        <p>FTC-sag, søgsmålsdata, EAA-positionen — og hvad der faktisk virker for små webbureauer i stedet for overlay-widgets.</p>
        <a href="/blog/tilgaengeligheds-overlays-eaa" class="btn-secondary" style="margin-top:12px;">Læs guiden →</a>
      </div>
''',
    'wcag-22-aendringer':
'''      <div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">
        <h3><a href="/blog/wcag-22-aendringer" style="color:inherit;text-decoration:none;">WCAG 2.2: hvad er ændret (dansk)</a></h3>
        <p>De 9 nye successkriterier, hvad der blev fjernet, og hvordan små webbureauer opdaterer klient-sites til den nye standard.</p>
        <a href="/blog/wcag-22-aendringer" class="btn-secondary" style="margin-top:12px;">Læs guiden →</a>
      </div>
''',
    'nis2-leverandoerkaede-sikkerhed':
'''      <div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">
        <h3><a href="/blog/nis2-leverandoerkaede-sikkerhed" style="color:inherit;text-decoration:none;">NIS2 leverandørkædesikkerhed (dansk)</a></h3>
        <p>Artikel 21(2)(d), vendor assessment, kontraktklausuler og en 5-trins plan til at reducere leverandørrisiko — skrevet til små bureauer.</p>
        <a href="/blog/nis2-leverandoerkaede-sikkerhed" class="btn-secondary" style="margin-top:12px;">Læs guiden →</a>
      </div>
''',
}


def add_frontpage_cards(slugs):
    p = f'{SITE}/index.html'
    c = open(p).read()
    for s in slugs:
        if f'/blog/{s}' in c:
            print(f'card for {s} already present')
            continue
        anchor = '<div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">\n        <h3><a href="/blog/free-gdpr-document-generators"'
        i = c.find(anchor)
        assert i > 0, f'anchor for {s} not found'
        c = c[:i] + CARDS[s] + c[i:]
        print(f'card for {s} added')
    open(p, 'w').write(c)


# ── Link check ──────────────────────────────────────────────────────

def check_links(files):
    broken = []
    for path in files:
        html = open(path).read()
        for m in set(re.findall(r'href="(/[^"#]*?)"', html)):
            url = m.split('?')[0]
            target = ('site' + url).rstrip('/')
            if not (os.path.exists(target) or os.path.exists(target + '.html')
                    or url == '/' or os.path.exists(target + '/index.html')):
                broken.append((path, m))
    return broken


# ── Main ────────────────────────────────────────────────────────────

def main():
    pages = [page_overlays(), page_wcag22(), page_nis2_supply()]
    slugs = []
    for slug, html in pages:
        with open(f'{SITE}/blog/{slug}.html', 'w') as f:
            f.write(html)
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        assert blocks, f'no JSON-LD in {slug}'
        for b in blocks:
            d = json.loads(b)
            assert d['@context'] == 'https://schema.org' and d['@type'] == 'Article', slug
        print(f'{slug}.html written, JSON-LD OK')
        slugs.append(slug)

    update_sitemap(slugs)
    print('sitemap updated')

    add_frontpage_cards(slugs)

    all_files = [f'{SITE}/blog/{s}.html' for s in slugs] + [f'{SITE}/index.html']
    broken = check_links(all_files)
    print('broken internal links:', broken if broken else 'none')

    print(f'\nDone. 3 Danish blog posts created: {", ".join(slugs)}')


if __name__ == '__main__':
    main()