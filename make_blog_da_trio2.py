#!/usr/bin/env python3
"""Iteration 106: Three new Danish blog pendants.

- dbbaftale-webbureau        (pendant til EN gdpr-dpa-web-agencies)
- gdpr-boeder-2026           (pendant til EN gdpr-fines-2026)
- tilgaengelighedsscanner-cli(pendant til EN accessibility-scanner-cli)

Same safety pattern: JSON-LD valideret, sitemap duplikattjek,
internt link-tjek, forsids-kort indsat.
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


# ── Blog 1: Databehandleraftaler for webbureauer ─────────────────────

def page_dba():
    slug = 'dbbaftale-webbureau'
    desc = ('Databehandleraftalen (DBA) er den mest oversete del af et webbureaus '
            'GDPR-arbejde. Hvornår du er databehandler, hvad aftalen skal indeholde '
            'efter artikel 28, og en skabelon-struktur du kan bruge i dag.')
    h = head(slug, 'da',
             'Databehandleraftale for webbureauer: hvad artikel 28 kræver',
             desc,
             'DBA til webbureauet: hvad artikel 28 kræver',
             'Hvornår er du databehandler? Hvad skal aftalen indeholde? Skabelon-struktur og svar på de spørgsmål klienter stiller.',
             'Databehandleraftale for webbureauer — praktisk guide')
    body = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">BLOG · GDPR</div>
    <h1>Databehandleraftalen<br>for Webbureauer</h1>
    <p class="subtitle">Artikel 28 g&oslash;r databehandleraftalen (DBA) til en juridisk pligt &mdash; i begge retninger. Her er hvorn&aring;r du er databehandler, hvad aftalen minimum skal indeholde, og hvordan et lille bureau f&aring;r det p&aring; plads uden advokat.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">L&aelig;s guiden</a>
      <a href="/blog/gdpr-rolle-webbureau" class="btn-secondary">F&oslash;rst: din GDPR-rolle &rarr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; L&aelig;setid: 7 minutter</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="hvornaar">Hvornår er webbureauet databehandler?</h2>
    <p>Reglen er enkel i teorien: <strong>dataansvarlig</strong> bestemmer form&aring;l og midler; <strong>databehandleren</strong> behandler data p&aring; den ansvarliges vegne. I praksis sidder et webbureau typisk i tre roller samtidig:</p>
    <p><strong>1. Databehandler for klientens site-brugere.</strong> Kontaktformularer, nyhedsbreve, analytics og bookings p&aring; det site du driver behandler bes&oslash;gendes persondata p&aring; klientens vegne. Det kr&aelig;ver en skriftlig DBA mellem jer &mdash; mundtligt t&aeli;ller ikke.</p>
    <p><strong>2. Dataansvarlig for egne form&aring;l.</strong> Din egen hjemmeside, dine leads, din fakturering og dit CV-lager er dit eget ansvar.</p>
    <p><strong>3. Dataansvarlig ved "egne" beslutninger.</strong> V&aelig;lger du selv at sende markedsf&oslash;ring til klientens kunder, eller bruger du produktionsdata til test uden aftale om det, er du ikke l&aelig;ngere behandler &mdash; du er blevet ansvarlig, og det er en kontraktbrud og en overtr&aelig;delse p&aring; &eacute;n gang.</p>
    <div class="problem-cards">
      <div class="card"><h3>📄 Skriftlig pligt</h3><p>Artikel 28(9): behandlingen skal reguleres af en EU-/EØS-retlig kontrakt eller andre juridiske bindende handlinger. En mail kan nogle gange v&aelig;re nok, men et underskrevet dokument er det eneste der holder ved revision.</p></div>
      <div class="card"><h3>🔁 Begge veje</h3><p>Du skal HAVE en DBA fra hver leverand&oslash;r der behandler klientdata for dig (hosting, e-mail, backup) &mdash; og LEVERE en til hver klient hvis du behandler deres data.</p></div>
      <div class="card"><h3>⚖️ Underbehandlere</h3><p>Dine underbehandlere (fx din hostingudbyder) skal godkendes af klienten, og du videregiver samme forpligtelser ned ad kæden via artikel 28(4).</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="indhold">Hvad aftalen minimum skal indeholde</h2>
    <p>Artikel 28(3) lister ni obligatoriske elementer. De fleste standardaftaler d&aelig;kker dem &mdash; tjek at din g&oslash;r:</p>
    <p><strong>1. Genstand og varighed.</strong> Hvilke behandlinger, hvilke datakategorier, hvor l&aelig;nge.<br>
    <strong>2. Formål og art.</strong> Drift og vedligehold af website, hosting, support osv.<br>
    <strong>3. Datakategorier.</strong> Kontaktoplysninger, ordredata, logdata &mdash; v&aelig;r konkret.<br>
    <strong>4. Registerpligt.</strong> Beholderen skal f&oslash;re dokumentation af behandlingskategorierne (art. 30(2)).<br>
    <strong>5. Transfers.</strong> Ingen overf&oslash;rsel til lande uden for EU/E&Oslash;S uden gyldigt overf&oslash;rselsgrundlag.<br>
    <strong>6. Sikkerhed.</strong> Henvisning til artikel 32-foranstaltninger.<br>
    <strong>7. Underbehandlere.</strong> Forudg&aring;ende generel eller specifik godkendelse + underretningspligt ved &aelig;ndringer.<br>
    <strong>8. Hjælp til den ansvarlige.</strong> Assistance ved dataminejer, DPIA'er og tilsyn fra Datatilsynet.<br>
    <strong>9. Sletning/returnering.</strong> Ved aftalens ophør slettes eller udleveres alle persondata &mdash; efter den ansvarliges valg.</p>
    <p>Til det kommer to punkter bureauer ofte glemmer: <strong>fortrolighedspligt</strong> for alt personale der f&aring;r adgang, og <strong>revisionssamarbejde</strong> &mdash; klienten har ret til at f&aring; dokumentation for overholdelse.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="praksis">Sådan gør et lille bureau det praktisk</h2>
    <p><strong>Skabelon én gang.</strong> Lav &eacute;n standard-DBA som bilag til dine serviceaftaler. Datatilsynets vejledning og brancheskabeloner (Dansk Erhverv, IT-Branchen) giver et godt udgangspunkt.</p>
    <p><strong>Leverandørsiden.</strong> Gennemg&aring; din egen stak: har hver hosting-, CDN-, e-mail- og backup-udbyder en DBA du reelt har? Hyperscalere leverer DPA'er online &mdash; gem dem sammen med acceptdatoer. Sm&aring; plugins og SaaS-v&aelig;rkt&oslash;jer uden DPA er et r&oslash;d flag.</p>
    <p><strong>Underbehandlerliste.</strong> Før en liste du kan give klienten: navn, form&aring;l, land. Opdater den ved &aelig;ndringer og underret klienter inden nye tilf&oslash;jes.</p>
    <p><strong>Ved ophør.</strong> Defin&eacute;r i skabelonen hvad der sker med produktiondata ved opsigelse: slettes inden for X dage, eksporteres til klienten, backups ruller ud inden for backup-cyklussen.</p>
    <div class="problem-cards">
      <div class="card"><h3>🧾 Bevis-mappen</h3><p>Underskrevne DBA'er ind og ud, underbehandlerliste, sletterutiner. Seks dokumenter der dækker både GDPR og NIS2-leverandørkrav.</p></div>
      <div class="card"><h3>🚫 Test-data</h3><p>Produktionsdata i staging er behandling uden formålsdækning. Anonymisér eller fikser det i din DBA som tilladt formål med særlige krav.</p></div>
      <div class="card"><h3>📋 Spørgsmål fra klienter</h3><p>"Har I en DBA?" er nu et standard indkøbspørgsmål. Et klart ja med dokument på minutter vinder hænder mod et bureau der skal "returnere senere".</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede sp&oslash;rgsm&aring;l</h2>
    <div class="problem-cards">
      <div class="card"><h3>Kan vi bruge hostingudbyderens standard-DPA?</h3><p>Ja &mdash; for den relation. Store leverand&oslash;rers DPA'er er artikel 28-korrekte og dækker normalt underbehandlere. Dit arbejde er at have dem, kende scope'et og kunne fremvise dem ved anmodning.</p></div>
      <div class="card"><h3>Er vi databehandler eller dataansvarlige for klientens analytics?</h3><p>Som udgangspunkt behandler: klienten beslutter værktøj og formål, du konfigurerer. Men vælger du selv analytics-værktøjet og dets formål, kan du blive fælles eller selvstændig ansvarlig. Læg beslutningen hos klienten og dokumentér den.</p></div>
      <div class="card"><h3>Hvad hvis klienten nægter at skrive under?</h3><p>Du må ikke starte behandlingen uden aftale, hvis den omfatter persondata. I praksis: brug din standard-DBA som bilag til tilbuddet, så accept af tilbuddet er accept af DBA'en.</p></div>
      <div class="card"><h3>Skal en DBA registreres hos Datatilsynet?</h3><p>Nej. Der findes ingen notifikationspligt. Pligten er at have aftalen og kunne dokumentere overholdelsen ved tilsyn.</p></div>
      <div class="card"><h3>Bøder for manglende DBA?</h3><p>Ja &mdash; artikel 83(4)(a) sætter rammen op til 10 millioner euro eller 2 % af den globale årsomsætning for brud på artikel 28. Sanktionerne i praksis er sjældent maksimale for små virksomheder, men ordrer om at bringe behandlingen i orden er almindelige.</p></div>
      <div class="card"><h3>Dækker vores DBA også AI-værktøjer vi bruger?</h3><p>Kun hvis de behandler klientdata og du har aftalt det. Indsæt AI-værktøjer i underbehandlerlisten eller udelad dem eksplicit &mdash; "vi bruger ChatGPT til alt" er ikke et overførselsgrundlag.</p></div>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/blog/gdpr-rolle-webbureau" class="btn-primary">GDPR-guiden: bureauets rolle &rarr;</a>
      &nbsp;&nbsp;
      <a href="/blog/nis2-guide-da" class="btn-secondary">NIS2-guiden (dansk) &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Relaterede guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">GDPR</span><h3><a href="/blog/gdpr-rolle-webbureau" style="color:var(--color-accent);text-decoration:none;">GDPR-guiden: webbureauets rolle (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">GDPR</span><h3><a href="/blog/gdpr-boeder-2026" style="color:var(--color-accent);text-decoration:none;">GDPR-bøder i 2026 (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">NIS2</span><h3><a href="/blog/nis2-leverandoerkaede-sikkerhed" style="color:var(--color-accent);text-decoration:none;">NIS2 leverandørkædesikkerhed (dansk)</a></h3></div>
    </div>
  </div>
</section>
''' + footer_da()
    return slug, h + body


# ── Blog 2: GDPR-bøder 2026 ──────────────────────────────────────────

def page_boeder():
    slug = 'gdpr-boeder-2026'
    desc = ('Hvor store er GDPR-bøderne i 2026? Reelle eksempler, bøde-trappen '
            '(artikel 83), hvad der udløser de største sanktioner, og hvad små '
            'webbureauer og deres klienter konkret skal frygte.')
    h = head(slug, 'da',
             'GDPR-bøder i 2026: trappen, eksemplerne og hvad små virksomheder risikerer',
             desc,
             'GDPR-bøder i 2026: hvad risikerer du reelt?',
             'Bøde-trappen i artikel 83, reelle eksempler fra Datatilsynet og EU, og de fejl der faktisk udløser sanktioner.',
             'GDPR-bøder i 2026 — guide til små virksomheder og bureauer')
    body = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">BLOG · GDPR</div>
    <h1>GDPR-B&Oslash;DER I 2026:<br>Trappen, eksemplerne og realiteterne</h1>
    <p class="subtitle">Hvad risikerer en dansk virksomhed reelt? B&oslash;detrappen i artikel 83, de st&oslash;rste kendte sager, de fejl der faktisk udl&oslash;ser b&oslash;der &mdash; og hvad et lille bureau skal have styr p&aring; for sine klienter.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">L&aelig;s guiden</a>
      <a href="/blog/gdpr-rolle-webbureau" class="btn-secondary">Bureauets GDPR-rolle &rarr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; L&aelig;setid: 6 minutter</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="trappen">Bøde-trappen i artikel 83</h2>
    <p>GDPR har to niveauer af maksimumsbøder:</p>
    <p><strong>Niveau 1</strong> (op til 10 millioner euro eller 2 % af global &aring;rsoms&aelig;tning): overtr&aelig;delser af de grundl&aelig;ggende pligter &mdash; dokumentation, sikkerhed (art. 32), databehandleraftaler (art. 28), dataregistrering, brudnotifikation (art. 33-34).</p>
    <p><strong>Niveau 2</strong> (op til 20 millioner euro eller 4 %): overtr&aelig;delser af selve behandlingsprincipperne, rettigheder og lovlig grundlag &mdash; behandling uden samtykke eller anden hjemmel, manglende information, overtr&aelig;delse af sletteretten.</p>
    <p>Maksima er sj&aelig;lde. Myndighederne skal afpasse efter grovhed, varighed, antal ber&oslash;rte, om det var fors&aelig;tligt, og samarbejdet under sagen. For sm&aring; virksomheder ender de fleste sager med en b&oslash;de i tusind-kroners-klassen plus en ordre om at rette det &mdash; men det er ikke gratis, og offentligg&oslash;relsen koster ry.</p>
    <div class="problem-cards">
      <div class="card"><h3>💶 Største kendte</h3><p>De historiske topbøder (Meta, Amazon) ligger i hundredmillioner-euro klassen. De rammer platform-modellen — ikke småsites. Men principperne bag dem gælder alle.</p></div>
      <div class="card"><h3>🇩🇰 Danske sager</h3><p>Datatilsynet udstedte kritik og bøder typisk i intervallet 10.000–500.000 kr til private virksomheder — oftest for utilstrækkelig sikkerhed, manglende adgangsstyring og forkert grundlag.</p></div>
      <div class="card"><h3>📣 Tilsynskampagner</h3><p>Koordinerede EU-tilsyn rammer temaer årligt: cloud-tjenester, cookies, brug af AI, dataminejer. Næste kampagne er offentlig i forvejen — følg med og vær foran.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="fejl">De fejl der faktisk udløser bøder</h2>
    <p>Gennemgang af kendte sager viser at samme h&aring;ndfuld fejl g&aring;r igen &mdash; is&aelig;r for mindre virksomheder:</p>
    <p><strong>1. Manglende adgangsstyring.</strong> Fælles login, tidligere medarbejdere med adgang, ukrypterede mapper. Den hyppigste danske b&oslash;de-&aring;rsag.</p>
    <p><strong>2. Behandling uden grundlag.</strong> Markedsf&oslash;ring til kundelistes uden samtykke eller relevans, tracking f&oslash;r samtykke, data brugt til nye form&aring;l uden vurdering.</p>
    <p><strong>3. Brud ikke anmeldt.</strong> 72-timers-reglen (art. 33). At opdage et brud og tie er en separat overtr&aelig;delse oven i selve bruddet.</p>
    <p><strong>4. Utilstrækkelige DBA'er.</strong> Behandling hos leverand&oslash;rer uden artikel 28-aftale.</p>
    <p><strong>5. Overoverv&aring;gning af medarbejdere.</strong> Logning og video uden hjemmel &mdash; fast tema i nordiske sager.</p>
    <div class="problem-cards">
      <div class="card"><h3>🍪 Cookies</h3><p>Ikke-bøde men aktivt håndhævet: myndigheder i hele EU sender påbud om tracking før samtykke. Cookie-banneret er det mest synlige compliance-element på ethvert site.</p></div>
      <div class="card"><h3>🔒 Sikkerhed først</h3><p>Artikel 32 er proportionalt: MFA, opdateringer, backups og adgangsliste. Et lille site kan dokumentere dette på en dag — og undgå den mest almindelige bødekategori.</p></div>
      <div class="card"><h3>📝 Dokumentér</h3><p>En kort behandlingsoversigt (art. 30) og en incidentplan er billig forsikring. Myndigheder møder dokumenteret proportionalitet med lempelige udfald.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="bureau">Hvad betyder det for webbureauet?</h2>
    <p>To roller igen: du kan selv blive p&aring;banket for dine egne behandlinger, og du kan tr&aelig;kkes ind i klient-sager som den der byggede og driftede systemet.</p>
    <p>Den realistiske plan for et lille bureau:</p>
    <p>&bull; Standard-DBA ind og ud, underbehandlerliste, gemte leverand&oslash;r-DPA'er.<br>
    &bull; Adgangsstyringsrutine: per-person konti, MFA, offboarding samme dag.<br>
    &bull; Cookie-samtykke korrekt konfigureret p&aring; alle klient-sites du driver.<br>
    &bull; En side incidentplan der matcher 72-timers-reglen &mdash; ogs&aring; for klienters sites.<br>
    &bull; Kort art. 30-oversigt over dine egne behandlinger.</p>
    <p>Det er en uges arbejde f&oslash;rste gang, og derefter vedligeholdelse. Til geng&aelig;ld kan du svare "ja, dokumenteret" p&aring; de sikkerhedssp&oslash;rgsm&aring;l st&oslash;rre klienter nu stiller &mdash; hvilket i sig selv vinder arbejde.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede sp&oslash;rgsm&aring;l</h2>
    <div class="problem-cards">
      <div class="card"><h3>Kan en lille virksomhed virkelig få millionbøde?</h3><p>Teoretisk ja — loftet gælder alle. Praktisk nej i de fleste tilfælde: myndigheder afpasser efter virksomhedens størrelse og grovhed. Realistiske udfald for småvirksomheder er kritik, påbud og bøder i tusind-kroners-til lav-sekscifret kroners klasse.</p></div>
      <div class="card"><h3>Hvem betaler — bureauet eller klienten?</h3><p>Afhængigt af rolle og kontrakt. Den dataansvarlige (typisk klienten) bærer hovedansvaret for grundlag og rettigheder; behandleren (bureauet) for sikkerheden i leverancen. Ansvarsfordelingen skal stå i kontrakten — ellers ender diskussionen i tvisten.</p></div>
      <div class="card"><h3>Udløser et cookie-banner-fejl en bøde?</h3><p>I Danmark typisk påbud og frist først; gentagelse eller grov overskridelse eskalerer. Flere EU-lande bødelægger direkte. Ret banneret — det er timeworks, ikke ugersarbejde.</p></div>
      <div class="card"><h3>Hvad er fristen for at anmelde et databrud?</h3><p>72 timer fra den ansvarlige bliver bekendt med bruddet, til Datatilsynet — medmindre bruddet sandsynligvis ikke medfører risiko for fysiske personer. Berørte skal informeres, hvis risikoen er høj.</p></div>
      <div class="card"><h3>Får man varsel før tilsyn?</h3><p>Ingen garanti. Datatilsynet arbejder både med klager, tilsynskampagner og utilmeldte kontroller. Dokumentationen skal derfor være klar på forhånd — ikke produceres i panik.</p></div>
      <div class="card"><h3>Hvor finder jeg officielle tal?</h3><p>Datatilsynets afgørelsesdatabase og EDPB's sagsdatabase offentliggør kendte bøder. Brug dem som kilde — ikke pressens afrundede tal.</p></div>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/blog/gdpr-rolle-webbureau" class="btn-primary">Læs bureau-rollen &rarr;</a>
      &nbsp;&nbsp;
      <a href="/free-tools" class="btn-secondary">Gratis GDPR-værktøjer &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Relaterede guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">GDPR</span><h3><a href="/blog/gdpr-rolle-webbureau" style="color:var(--color-accent);text-decoration:none;">GDPR-guiden: webbureauets rolle (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">COOKIES</span><h3><a href="/blog/cookie-consent-gdpr-2026" style="color:var(--color-accent);text-decoration:none;">Cookie-banners &amp; GDPR (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">DBA</span><h3><a href="/blog/dbbaftale-webbureau" style="color:var(--color-accent);text-decoration:none;">Databehandleraftale for webbureauer (dansk)</a></h3></div>
    </div>
  </div>
</section>
''' + footer_da()
    return slug, h + body


# ── Blog 3: Accessibility Scanner CLI (dansk) ─────────────────────────

def page_cli():
    slug = 'tilgaengelighedsscanner-cli'
    desc = ('Gratis kommandolinje-scanner til WCAG 2.2 / EAA-problemer: 16+ regler, '
            'kontrastberegning, JSON-output og --fail-on til CI. Python og Node.js, '
            'nul afhængigheder — guide på dansk.')
    h = head(slug, 'da',
             'Tilgængelighedsscanning fra kommandolinjen — gratis CLI-guide',
             desc,
             'Gratis CLI-scanner til WCAG 2.2 / EAA',
             '16+ regler, JSON-output, --fail-on til CI. Sådan scanner du klient-sites fra terminalen — Python og Node.js, nul afhængigheder.',
             'Tilgængelighedsscanning fra kommandolinjen (dansk)')
    body = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">BLOG &middot; V&AElig;RKT&Oslash;J</div>
    <h1>Tilg&aelig;ngelighedsscanning<br>fra Kommandolinjen</h1>
    <p class="subtitle">En gratis CLI-scanner der tjekker 16+ WCAG 2.2 / EAA-regler p&aring; enhver URL &mdash; med JSON-output og CI-integration. S&aring;dan f&aring;r du automatiske tilg&aelig;ngelighedstjek ind i din arbejdsgang, uden abonnement.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">L&aelig;s guiden</a>
      <a href="/scan-da" class="btn-secondary">Pr&oslash;v scanneren i browseren &rarr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; L&aelig;setid: 8 minutter</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="hvorfor-cli">Hvorfor kommandolinjen?</h2>
    <p>Browser-baserede scannere er gode til enkeltkontroller. Men hvis du vedligeholder ti, tyve eller hundrede klient-sites, har du brug for noget der kan k&oslash;res i batch, gemmes i git og fejle automatisk n&aring;r en release introducerer problemer. Det er CLI'ens rolle.</p>
    <p>Vores scanner er skrevet til netop det: ingen installation ud over Python eller Node.js, ingen konto, ingen gr&aelig;nser. Du giver den en URL, den returnerer fundene struktureret &mdash; i terminalen eller som JSON til videre behandling.</p>
    <div class="problem-cards">
      <div class="card"><h3>🆓 Gratis og ubegrænset</h3><p>Ingen freemium-væg, ingen scan-grænser. Kør den på alle dine klient-sites hver nat hvis du vil.</p></div>
      <div class="card"><h3>🔌 Platform-uafhængig</h3><p>WordPress, Shopify, Webflow, Umbraco eller håndskrevet HTML — scanneren ser bare DOM. Kravet om universalitet er designet ind, ikke boltret på.</p></div>
      <div class="card"><h3>⚙️ CI-klar</h3><p>--fail-on flaget gør den til en gate i GitHub Actions: ny kode med kritiske fund stopper pipelinen.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="regler">Hvad scanneren tjekker</h2>
    <p>Automatiserede v&aelig;rkt&oslash;jer kan kun finde det maskintjekbare &mdash; men det er stadig flertallet af de fejl der ses i praksis. Scanneren d&aelig;kker blandt andet:</p>
    <p>&bull; Manglende eller tomme alt-tekster p&aring; billeder<br>
    &bull; Formularfelter uden label eller associeret tekst<br>
    &bull; Kontrastforhold under WCAG-kravene (4.5:1 / 3:1 beregnet, ikke g&aelig;ttet)<br>
    &bull; Duplikerede ID'er der bryder sk&aelig;rml&aelig;ser<br>
    &bull; Overskriftshierarki (spring over niveauer, manglende h1)<br>
    &bull; Manglende lang-attribut og viewport-meta<br>
    &bull; Links uden genkendelig tekst ("l&aelig;s mere her"-m&oslash;nstre)<br>
    &bull; HTML-lang mismatch og andre strukturelle fundamentfejl</p>
    <p>Det automatiserbare dels&aelig;t svarer typisk til 30-50 % af de fund en fuld manuel audit laver &mdash; men 100 % af dem er fund du kan rette med det samme, uden konsulent.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="kom-i-gang">Kom i gang</h2>
    <p><strong>Browser-versionen f&oslash;rst.</strong> Vil du se resultat-formatet f&oslash;r du installerer noget: inds&aelig;t en URL i <a href="/scan-da" style="color:var(--color-accent);">scanneren her p&aring; sitet</a>. Samme regels&aelig;t, samme score.</p>
    <p><strong>CLI'en.</strong> Scannerens kerne er et lille script uden tredjepartsafh&aelig;ngigheder. Grundprincippet:</p>
    <p>1. Hent siden (urllib / fetch).<br>
    2. Parse DOM'en og k&oslash;r regels&aelig;ttet.<br>
    3. Beregn kontraster fra de reelle farvev&aelig;rdier.<br>
    4. Udskriv fundene sorteret efter alvor &mdash; eller emit JSON med --json.</p>
    <p><strong>CI-eksempel.</strong> I GitHub Actions k&oslash;rer du scanneren mod staging-URL'en efter deploy og s&aelig;tter <code>--fail-on critical</code>: kritiske fund fejler buildet, advarsler logger blot. S&aring;dan holder du gulvet under det niveau der allerede er opn&aring;et &mdash; uden at blokere hverdagen.</p>
    <div class="problem-cards">
      <div class="card"><h3>🌙 Natlig portefølje-runde</h3><p>Et cron-job der scanner alle klient-sites én gang i døgnet og mailler diffen. Du ser regressioner dagen efter de lander — ikke ved næste audit.</p></div>
      <div class="card"><h3>📊 Score som salgsargument</h3><p>Før/efter-scores er det letteste bevis over for klienter: "dit site gik fra 62 til 91 — dokumenteret."</p></div>
      <div class="card"><h3>⚠️ Grænser</h3><p>Automatik fanger ikke tastaturfælder, skærmlæser-flow eller kognitive krav. Brug CLI'en som filter, og brug manual test på checkout/login-flows.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede sp&oslash;rgsm&aring;l</h2>
    <div class="problem-cards">
      <div class="card"><h3>Koster scanneren noget?</h3><p>Nej. Både browser-versionen og CLI-tilgangen er gratis og uden begrænsninger. Ingen konto, ingen scan-kvote.</p></div>
      <div class="card"><h3>Kan den erstatte en manuel audit?</h3><p>Nej — og ingen scanner kan det. Automatiserede regler fanger en delmængde af WCAG. Men den delmængde er stor nok til at fjerne hovedparten af de fejl småsites fejler på, og den holder niveauet mellem audits.</p></div>
      <div class="card"><h3>Hvilken WCAG-version tjekker den mod?</h3><p>Regelsættet følger det maskintjekbare i WCAG 2.2 AA — samme referenceramme EAA bygger på via EN 301 549.</p></div>
      <div class="card"><h3>Virker den på sider bag login?</h3><p>Browser-versionen scanner offentlige URL'er. Bag-login-scenarier klares i CLI-tilgangen ved at hente siden autentificeret først og sende HTML'en gennem regelmotoren.</p></div>
      <div class="card"><h3>Hvorfor ikke bare bruge Lighthouse?</h3><p>Lighthouse er fint og inkluderer axe-core. Fordelen ved en dedikeret scanner er kontrol: egne regler, stabil output-format til scripting, og mulighed for at køre den hvor du vil — uden Chrome-instans.</p></div>
      <div class="card"><h3>Hvad gør jeg med resultaterne?</h3><p>Prioritér efter alvor og synlighed: kritiske fejl på checkout og kontaktformularer først. Ret i skabeloner/komponenter, ikke side for side — så forsvinder hundredvis af fund på én gang.</p></div>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/scan-da" class="btn-primary">Scan din side gratis &rarr;</a>
      &nbsp;&nbsp;
      <a href="/blog/pris-tilgaengelighedsgennemgang" class="btn-secondary">Hvad koster en fuld audit? &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Relaterede guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">WCAG</span><h3><a href="/blog/wcag-22-aendringer" style="color:var(--color-accent);text-decoration:none;">WCAG 2.2: hvad er ændret (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">PRIS</span><h3><a href="/blog/pris-tilgaengelighedsgennemgang" style="color:var(--color-accent);text-decoration:none;">Prisen på en tilgængelighedsgennemgang (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">EAA</span><h3><a href="/blog/eaa-frister-2026" style="color:var(--color-accent);text-decoration:none;">EAA-frister og håndhævelse (dansk)</a></h3></div>
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
    'dbbaftale-webbureau':
'''      <div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">
        <h3><a href="/blog/dbbaftale-webbureau" style="color:inherit;text-decoration:none;">Databehandleraftale for webbureauer (dansk)</a></h3>
        <p>Hvornår er du databehandler? Artikel 28's ni obligatoriske elementer, underbehandlere, test-data og en skabelon-struktur du kan bruge i dag.</p>
        <a href="/blog/dbbaftale-webbureau" class="btn-secondary" style="margin-top:12px;">Læs guiden →</a>
      </div>
''',
    'gdpr-boeder-2026':
'''      <div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">
        <h3><a href="/blog/gdpr-boeder-2026" style="color:inherit;text-decoration:none;">GDPR-bøder i 2026 (dansk)</a></h3>
        <p>Bøde-trappen i artikel 83, reelle eksempler fra Danmark og EU, og de fem fejl der faktisk udløser sanktioner for små virksomheder.</p>
        <a href="/blog/gdpr-boeder-2026" class="btn-secondary" style="margin-top:12px;">Læs guiden →</a>
      </div>
''',
    'tilgaengelighedsscanner-cli':
'''      <div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">
        <h3><a href="/blog/tilgaengelighedsscanner-cli" style="color:inherit;text-decoration:none;">Tilgængelighedsscanning fra kommandolinjen (dansk)</a></h3>
        <p>Gratis CLI-scanner til WCAG 2.2 / EAA: 16+ regler, kontrastberegning, JSON-output og CI-integration — guide på dansk.</p>
        <a href="/blog/tilgaengelighedsscanner-cli" class="btn-secondary" style="margin-top:12px;">Læs guiden →</a>
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
    pages = [page_dba(), page_boeder(), page_cli()]
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
