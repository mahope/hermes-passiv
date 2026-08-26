#!/usr/bin/env python3
"""Iteration 481: To nye DeskUptime-blogpar (EN + DA) — funnel mod /deskuptime.

1. website-down-checker-free          -> da/blog/tjek-om-hjemmeside-er-nede-gratis
2. monitor-multiple-websites-desktop  -> da/blog/overvaag-flere-hjemmesider-paa-skrivebordet

Moenster fra make_blog_da_iter259.py. Ingen eksterne soegninger.
"""
import json, re, os, sys, glob
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

PAGES = [
    {
        'slug': 'tjek-om-hjemmeside-er-nede-gratis',
        'en_slug': 'website-down-checker-free',
        'title': 'Er hjemmesiden nede? Gratis tjek — og hvad du gør bagefter (2026)',
        'h1': 'Er hjemmesiden<br>nede? Tjek det gratis',
        'desc': ('Sådan tjekker du om en hjemmeside er nede for alle — eller kun for dig. '
                 'Gratis metoder, forskellen på nedbrud og lokale problemer, og hvordan '
                 'du får besked automatisk.'),
        'og_desc': ('Website down checker gratis: tjek om et site er nede, skeln mellem '
                    'rigtige nedbrud og lokale DNS-problemer, og opsæt automatisk overvågning '
                    'uden månedligt abonnement.'),
        'badge': 'OVERVÅGNING &middot; GRATIS',
        'subtitle': ('Sitet loader ikke. Er det nede for alle, eller er det din forbindelse, '
                     'din DNS eller dit netværk? Her er den hurtige tjekliste — og hvordan '
                     'du slipper for at opdage det fra kunderne næste gang.'),
        'cta1': '<a href="/deskuptime" class="btn-primary">Hent DeskUptime gratis &rarr;</a>',
        'cta2': '<a href="#tjeklisten" class="btn-secondary">Spring til tjeklisten</a>',
        'tool_url': '/deskuptime',
        'tool_label': 'Overvåg dine sites fra skrivebordet',
        'hub_badge': 'OVERVÅGNING · GRUNDLAG',
        'hub_title': 'Er hjemmesiden nede? Gratis tjek',
        'hub_desc': 'Tjek om et site er nede for alle eller kun for dig — og opsæt automatisk overvågning uden abonnement.',
        'faq': [
            ("Hvordan tjekker jeg om en hjemmeside er nede?",
             "Prøv siden i en anden browser eller på mobildata. Virker den der, er problemet "
             "lokaalt. Virker den ingen steder, så tjek status på hostens statusside eller brug "
             "et værktøj der pinger sitet udefra — fx DeskUptime, der kører på din maskine."),
            ("Hvorfor virker en side for andre men ikke for mig?",
             "Typiske årsager: lokal DNS-cache der har gemt en gammel IP, en udgået "
             "internetudbyder-rute, VPN eller firmanetværk der blokerer domænet, eller cached "
             "indhold i browseren. Ryd DNS-cachen og prøv privat browsing."),
            ("Kan jeg se om et site er nede uden at installere noget?",
             "Ja — curl -I https://domaene.dk i terminalen viser statuskoden (200 = OK, "
             "5xx = serverfejl). Det kræver dog at du selv husker at tjekke; automatiske "
             "notifikationer kræver et overvågningsværktøj."),
            ("Hvad er den billigste måde at få besked når mit site går ned?",
             "En desktop-app som DeskUptime kører på din egen maskine og giver besked via "
             "skrivebordet — engangsbetaling i stedet for de typiske 10-30 USD/mdr. hos "
             "cloud-tjenester. Til kritiske produktionssites anbefales stadig en ekstern tjeneste "
             "som sekundær sikkerhed."),
        ],
        'body': '''
<section class="problem" id="tjeklisten">
  <div class="container">
    <h2>Tjeklisten: nede for alle, eller kun for dig?</h2>
    <ol>
      <li><strong>Anden netværksvej:</strong> slå wifi fra og prøv mobildata. Virker siden
      nu, er problemet dit eget netværk.</li>
      <li><strong>Statuskode:</strong> kør <code>curl -I https://ditdomaene.dk</code>.
      200/301/302 = serveren lever. 500/502/503 = rigtigt nedbrud. Timeout = vært eller
      DNS-problem.</li>
      <li><strong>DNS:</strong> kør <code>nslookup ditdomaene.dk</code> og sammenlign med
      den IP din host angiver. Uoverensstemmelse = DNS-problem, ikke nedbrud.</li>
      <li><strong>Værtens statusside:</strong> de store hosts (Netlify, Cloudflare,
      Vercel, one.com m.fl.) offentliggør hændelser — tjek den før du fejlretter blindt.</li>
    </ol>
<pre style="background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:0.9rem;">$ curl -I https://ditdomaene.dk
HTTP/2 503     # nede for alle — kontakt værten
HTTP/2 200     # oppe herfra → problemet er lokalt</pre>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>Problemet med at tjekke manuelt</h2>
    <p>Et enkelt tjek svarer på "er det nede <em>nu</em>". Men det spørgsmål kunder og
    besøgende stiller er "hvornår var det nede, og hvor længe?". Et site der flakker
    et par minutter ad gangen kl. 3 om natten opdager du aldrig manuelt — det opdager
    de kunder der forsøgte at købe.</p>
    <p>Løsningen er overvågning der kører selv: et interval på 1-5 minutter, notifikation
    når svaret fejler, og en historik du kan se bagefter. DeskUptime gør netop det fra
    din menulinje — ingen cloud-konto, ingen månedlig betaling:</p>
    <div style="text-align:center;margin-top:20px;">
      <a href="/deskuptime" class="btn-primary">Se DeskUptime &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Læs videre</h2>
    <p>Læs også:
    <a href="/da/blog/faa-besked-naar-hjemmeside-er-nede">få besked når hjemmesiden er nede</a>,
    <a href="/da/blog/overvaag-hjemmeside-fra-terminalen">overvåg fra terminalen</a> og
    <a href="/da/blog/overvaag-hjemmeside-github-actions-gratis">gratis overvågning med GitHub Actions</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/faa-besked-naar-hjemmeside-er-nede" lang="da">Besked ved nedbrud</a> &middot; '
                    '<a href="/da/blog/overvaag-hjemmeside-fra-terminalen" lang="da">Terminal-overvågning</a> &middot; '
                    '<a href="/da/blog/overvaag-flere-hjemmesider-paa-skrivebordet" lang="da">Flere sites på én gang</a>'),
    },
    {
        'slug': 'overvaag-flere-hjemmesider-paa-skrivebordet',
        'en_slug': 'monitor-multiple-websites-desktop',
        'title': 'Overvåg flere hjemmesider fra skrivebordet — uden cloud-abonnement',
        'h1': 'Overvåg flere<br>sites fra skrivebordet',
        'desc': ('Sådan holder du øje med 5, 20 eller 100 websites fra din egen maskine: '
                 'intervaller, notifikationer, statushistorik — og hvad desktop-overvågning '
                 'kan som cloud-tjenester ikke.'),
        'og_desc': ('Monitor multiple websites from your desktop: intervals, notifications and '
                    'status history without a monthly cloud subscription. DeskUptime-guide.'),
        'badge': 'OVERVÅGNING &middot; DESKTOP',
        'subtitle': ('Én hjemmeside kan du huske at tjekke. Fem klienters sites, dit eget og '
                     'staging-miljøet — det kræver et system. Cloud-overvågning koster typisk '
                     '10-30 USD/mdr.; din egen maskine kan gøre jobbet gratis.'),
        'cta1': '<a href="/deskuptime" class="btn-primary">Hent DeskUptime gratis &rarr;</a>',
        'cta2': '<a href="#saadan" class="btn-secondary">Sådan sætter du det op</a>',
        'tool_url': '/deskuptime',
        'tool_label': 'Prøv skrivebords-overvågning nu',
        'hub_badge': 'OVERVÅGNING · DESKTOP',
        'hub_title': 'Overvåg flere sites fra skrivebordet',
        'hub_desc': 'Hold øje med mange websites samtidig fra din egen maskine — intervaller, notifikationer og historik uden abonnement.',
        'faq': [
            ("Kan min computer overvåge websites mens jeg sover?",
             "Ja, hvis den ikke går i fuld dvale. På macOS holdes netværket aktivt i "
             "standby; på Windows skal du deaktivere fuld dvale eller bruge 'væk-timer'. "
             "Til mission-kritisk overvågning døgnet rundt er en cloud-tjeneste stadig mere "
             "pålidelig end en bærbar der lukker ned."),
            ("Hvor ofte bør et website tjekkes?",
             "Hvert 1.-5. minut er normalt for produktions-sites. Hyppigere giver falske "
             "alarmer ved kortvarige netværksblips; sjældnere (15+ min) kan overse korte "
             "nedbrud. Kombinér gerne to tjek i træk før alarm udløses."),
            ("Hvad er fordelene frem for en cloud-overvågningstjeneste?",
             "Ingen månedlig betaling, ingen konto, og dataene forlader aldrig din maskine. "
             "Ulempen: overvågningen stopper når computeren er slukket. Mange bruger derfor "
             "desktop-værktøjet til arbejdsdagen og en cloud-tjeneste som nat-dækning."),
            ("Kan jeg overvåge specifikke sider og ikke bare forsidelen?",
             "Ja. Giv værktøjet en komplet URL — fx /checkout eller /login. En forside kan "
             "svare 200 mens betalingsflowet er nede; de sider der tjener penge, er dem der "
             "skal overvåges."),
        ],
        'body': '''
<section class="problem" id="saadan">
  <div class="container">
    <h2>Sådan sætter du det op på fem minutter</h2>
    <ol>
      <li><strong>Hent DeskUptime</strong> — en lille desktop-app til macOS. Ingen konto,
      ingen konfigurationsfil.</li>
      <li><strong>Tilføj dine URLs:</strong> forside, checkout, API-endpoint, staging.
      Én linje pr. site.</li>
      <li><strong>Vælg interval:</strong> 60 sekunder til produktion, 300 til staging.
      To fejl i træk = alarm.</li>
      <li><strong>Slå notifikationer til:</strong> du ser besked direkte på skrivebordet
      når et site svarer forkert.</li>
      <li><strong>Kig i historikken:</strong> hver statusændring logges, så du kan se
      mønstre — fx nedbrud hver nat kl. 03 under backup-vinduet.</li>
    </ol>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>Hvornår er desktop-overvågning det rigtige valg?</h2>
    <table style="width:100%;border-collapse:collapse;">
      <tr style="text-align:left;"><th>Situation</th><th>Anbefaling</th></tr>
      <tr><td>Egen maskine står tændt i arbejdstiden</td><td>Desktop-app rækker helt</td></tr>
      <tr><td>Frie konsulenter med 5-20 kundesites</td><td>Desktop-app + historik pr. site</td></tr>
      <tr><td>Mission-kritisk e-handel, døgndrift</td><td>Cloud som primær, desktop som sekundær</td></tr>
      <tr><td>Budget nær nul</td><td>Desktop-app: engangsbeløb, intet abonnement</td></tr>
    </table>
    <div style="text-align:center;margin-top:20px;">
      <a href="/deskuptime" class="btn-primary">Hent DeskUptime &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Læs videre</h2>
    <p>Læs også:
    <a href="/da/blog/overvaag-hjemmeside-mac-menu-bar">overvågning i Mac-menulinjen</a>,
    <a href="/da/blog/overvaag-hjemmeside-fra-terminalen">terminal-baseret overvågning</a> og
    <a href="/da/blog/tjek-om-hjemmeside-er-nede-gratis">gratis tjek af om et site er nede</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/overvaag-hjemmeside-mac-menu-bar" lang="da">Mac-menulinje</a> &middot; '
                    '<a href="/da/blog/overvaag-hjemmeside-fra-terminalen" lang="da">Terminal</a> &middot; '
                    '<a href="/da/blog/tjek-om-hjemmeside-er-nede-gratis" lang="da">Nedtjek gratis</a>'),
    },
]


def build_page(p):
    url = f'{BASE}/da/blog/{p["slug"]}'
    ld_article = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article',
        'headline': p['title'], 'description': p['desc'],
        'url': url,
        'datePublished': TODAY, 'dateModified': TODAY,
        'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
        'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    }, ensure_ascii=False)
    main_entity = [{"@type": "Question", "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p['faq']]
    ld_faq = json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage',
                         'mainEntity': main_entity}, ensure_ascii=False)
    faq_cards = '\n'.join(
        f'      <div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in p['faq'])
    return f'''<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{p['title']}</title>
<meta name="description" content="{p['desc']}">
<meta property="og:type" content="article">
<meta property="og:title" content="{p['title']}">
<meta property="og:description" content="{p['og_desc']}">
<meta property="og:image" content="{BASE}/deskuptime/og.png">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="en" href="{BASE}/blog/{p['en_slug']}">
<link rel="alternate" hreflang="da" href="{url}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{ld_article}</script>
<script type="application/ld+json">{ld_faq}</script>
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">{p['badge']}</div>
    <h1>{p['h1']}</h1>
    <p class="subtitle">{p['subtitle']}</p>
    <div class="hero-cta">
      {p['cta1']}
      {p['cta2']}
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 6 minutters læsning</p>
  </div>
</header>
{p['body']}
<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
{faq_cards}
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="{p['tool_url']}" class="btn-primary">{p['tool_label']} &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Relateret: {p['related']}</p></div>
<footer style="padding:32px 24px;">
  <p><a href="/da">Forside</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/deskuptime">DeskUptime</a> &middot; <a href="/da/#blog">Blog</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});document.addEventListener('click',function(ev){{var a=ev.target&&ev.target.closest?ev.target.closest('a[href]'):null;if(!a)return;var h=a.href;if(h&&h.indexOf('chromewebstore.google.com')>-1){{try{{navigator.sendBeacon('/api/track',new Blob([JSON.stringify({{path:p,event:'store-click'}})],{{type:'application/json'}}));}}catch(e){{}}}}}},true);}}catch(e){{}}}})();
</script>
</body>
</html>'''


def build_en(p):
    """EN mirror page, same structure, lang=en."""
    url = f'{BASE}/blog/{p["en_slug"]}'
    ld_article = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article',
        'headline': EN[p['en_slug']]['title'], 'description': EN[p['en_slug']]['desc'],
        'url': url,
        'datePublished': TODAY, 'dateModified': TODAY,
        'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
        'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    }, ensure_ascii=False)
    e = EN[p['en_slug']]
    main_entity = [{"@type": "Question", "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in e['faq']]
    ld_faq = json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage',
                         'mainEntity': main_entity}, ensure_ascii=False)
    faq_cards = '\n'.join(
        f'      <div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in e['faq'])
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e['title']}</title>
<meta name="description" content="{e['desc']}">
<meta property="og:type" content="article">
<meta property="og:title" content="{e['title']}">
<meta property="og:description" content="{e['og_desc']}">
<meta property="og:image" content="{BASE}/deskuptime/og.png">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="en" href="{url}">
<link rel="alternate" hreflang="da" href="{BASE}/da/blog/{p['slug']}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{ld_article}</script>
<script type="application/ld+json">{ld_faq}</script>
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">{e['badge']}</div>
    <h1>{e['h1']}</h1>
    <p class="subtitle">{e['subtitle']}</p>
    <div class="hero-cta">
      <a href="/deskuptime" class="btn-primary">Get DeskUptime free &rarr;</a>
      <a href="#guide" class="btn-secondary">Jump to the guide</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; 6 min read</p>
  </div>
</header>
{e['body']}
<section class="products">
  <div class="container">
    <h2>Frequently asked questions</h2>
    <div class="problem-cards">
{faq_cards}
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/deskuptime" class="btn-primary">Try desktop monitoring now &rarr;</a>
    </div>
  </div>
</section>

<p style="text-align:center;"><a href="/da/blog/{p['slug']}" lang="da">Dansk version af denne guide</a></p>
<div style="text-align:center;margin-top:16px;"><p>Related: {e['related']}</p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">Home</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/deskuptime">DeskUptime</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
</script>
</body>
</html>'''


EN = {
    'website-down-checker-free': {
        'title': 'Is the Website Down? Free Checks — and What to Do Next (2026)',
        'h1': 'Is the website<br>down? Check it free',
        'desc': ('How to check whether a website is down for everyone or just you. Free '
                 'methods, how to tell real outages from local problems, and how to get '
                 'alerted automatically.'),
        'og_desc': ('Free website down checker: tell real outages apart from local DNS or '
                    'network issues, and set up automatic monitoring without a subscription.'),
        'badge': 'MONITORING &middot; FREE',
        'subtitle': ('The site won\'t load. Is it down for everyone — or is it your connection, '
                     'your DNS, your network? Here\'s the quick checklist, and how to stop '
                     'finding out from your customers next time.'),
        'related': ('<a href="/blog/get-notified-when-website-goes-down">Get notified when a site goes down</a> &middot; '
                    '<a href="/blog/desktop-website-monitor-cli">CLI monitoring</a> &middot; '
                    '<a href="/blog/monitor-multiple-websites-desktop">Monitor many sites at once</a>'),
        'faq': [
            ("How do I check if a website is down?",
             "Try it on another network (mobile data). If it works there, the problem is "
             "local. If not, check your host's status page or use a tool that probes the "
             "site externally — such as DeskUptime, which runs on your own machine."),
            ("Why does a site work for others but not for me?",
             "Common causes: a stale local DNS cache, ISP routing problems, VPN/corporate "
             "firewalls blocking the domain, or cached content. Flush your DNS cache and try "
             "a private window first."),
            ("Can I check if a site is down without installing anything?",
             "Yes — run curl -I https://example.com in a terminal. A 200 means the server is "
             "up; 5xx means a real server error; a timeout suggests hosting or DNS trouble. "
             "But manual checks only answer 'is it down right now' — automatic alerts need "
             "monitoring software."),
            ("What's the cheapest way to get alerted when my site goes down?",
             "A desktop app like DeskUptime runs locally and notifies you on your machine — "
             "a one-time cost instead of the typical $10–30/month cloud services charge. For "
             "mission-critical production sites, keep an external service as backup coverage."),
        ],
        'body': '''
<section class="problem" id="guide">
  <div class="container">
    <h2>The checklist: down for everyone, or just you?</h2>
    <ol>
      <li><strong>Another network:</strong> switch to mobile data. If it loads now, the
      problem is your own connection.</li>
      <li><strong>Status code:</strong> run <code>curl -I https://yoursite.com</code>.
      200/301/302 = server alive. 500/502/503 = real outage. Timeout = host or DNS issue.</li>
      <li><strong>DNS:</strong> run <code>nslookup yoursite.com</code> and compare with the
      IP your host documents. A mismatch means DNS, not downtime.</li>
      <li><strong>Host status page:</strong> major hosts publish incidents publicly —
      check there before debugging blindly.</li>
    </ol>
<pre style="background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:0.9rem;">$ curl -I https://yoursite.com
HTTP/2 503     # down for everyone — call your host
HTTP/2 200     # up from here &rarr; the problem is local</pre>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>The problem with checking manually</h2>
    <p>A single check answers "is it down <em>now</em>". But customers ask a different
    question: "when was it down, and for how long?" A site that flickers for two minutes
    at 3 AM never gets noticed manually — except by the customers who tried to buy.</p>
    <p>The fix is monitoring that runs itself: a short interval, a notification when the
    response fails, and history you can inspect afterwards. DeskUptime does exactly that
    from your menu bar — no cloud account, no monthly fee:</p>
    <div style="text-align:center;margin-top:20px;">
      <a href="/deskuptime" class="btn-primary">See DeskUptime &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Read more</h2>
    <p>Also:
    <a href="/blog/get-notified-when-website-goes-down">get notified when your site goes down</a>,
    <a href="/blog/desktop-website-monitor-cli">monitor from the terminal</a> and
    <a href="/blog/monitor-website-github-actions-free">free monitoring with GitHub Actions</a>.</p>
  </div>
</section>
''',
    },
    'monitor-multiple-websites-desktop': {
        'title': 'Monitor Multiple Websites From Your Desktop — Without a Cloud Subscription',
        'h1': 'Monitor multiple<br>sites from your desktop',
        'desc': ('How to watch 5, 20 or 100 websites from your own machine: intervals, '
                 'notifications, status history — and what desktop monitoring does that '
                 'cloud services can\'t.'),
        'og_desc': ('Monitor multiple websites from your desktop: intervals, desktop '
                    'notifications and per-site status history with no monthly subscription.'),
        'badge': 'MONITORING &middot; DESKTOP',
        'subtitle': ('One website you can remember to check. Five client sites plus staging '
                     'requires a system. Cloud monitoring typically costs $10–30/month; '
                     'your own machine can do the job free.'),
        'related': ('<a href="/blog/macos-menu-bar-website-monitor">macOS menu bar monitor</a> &middot; '
                    '<a href="/blog/desktop-website-monitor-cli">CLI monitoring</a> &middot; '
                    '<a href="/blog/website-down-checker-free">Free down checks</a>'),
        'faq': [
            ("Can my computer monitor websites while I sleep?",
             "Yes, as long as it doesn't enter full sleep. On macOS the network stays active "
             "in standby; on Windows disable full sleep or schedule wake timers. For "
             "round-the-clock critical monitoring, a cloud service remains more reliable than "
             "a laptop that powers down."),
            ("How often should a website be checked?",
             "Every 1–5 minutes is typical for production sites. More frequent checks create "
             "false alarms from brief network blips; less frequent (15+ min) misses short "
             "outages. Consider requiring two consecutive failures before alerting."),
            ("What are the advantages over a cloud monitoring service?",
             "No monthly fee, no account, and data never leaves your machine. The trade-off: "
             "monitoring stops when your computer shuts down. Many people pair the desktop "
             "tool during work hours with a cloud service for night coverage."),
            ("Can I monitor specific pages instead of just the homepage?",
             "Yes. Give the tool full URLs — e.g. /checkout or /login. A homepage can return "
             "200 while the payment flow is broken; the pages that make money are the ones "
             "worth watching."),
        ],
        'body': '''
<section class="problem" id="guide">
  <div class="container">
    <h2>Set it up in five minutes</h2>
    <ol>
      <li><strong>Download DeskUptime</strong> — a small macOS desktop app. No account,
      no config file.</li>
      <li><strong>Add your URLs:</strong> homepage, checkout, API endpoint, staging.
      One line each.</li>
      <li><strong>Pick an interval:</strong> 60 seconds for production, 300 for staging.
      Two failures in a row = alert.</li>
      <li><strong>Enable notifications:</strong> you'll see a message on your desktop the
      moment a site responds wrongly.</li>
      <li><strong>Review history:</strong> every status change is logged, so patterns become
      visible — like an outage every night at 3 AM during the backup window.</li>
    </ol>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>When is desktop monitoring the right choice?</h2>
    <table style="width:100%;border-collapse:collapse;">
      <tr style="text-align:left;"><th>Situation</th><th>Recommendation</th></tr>
      <tr><td>Your machine stays on during work hours</td><td>A desktop app covers it fully</td></tr>
      <tr><td>Freelancers with 5–20 client sites</td><td>Desktop app + per-site history</td></tr>
      <tr><td>Mission-critical e-commerce, 24/7</td><td>Cloud primary, desktop secondary</td></tr>
      <tr><td>Near-zero budget</td><td>Desktop app: one-time cost, no subscription</td></tr>
    </table>
    <div style="text-align:center;margin-top:20px;">
      <a href="/deskuptime" class="btn-primary">Get DeskUptime &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Read more</h2>
    <p>Also:
    <a href="/blog/macos-menu-bar-website-monitor">menu bar monitoring on macOS</a>,
    <a href="/blog/desktop-website-monitor-cli">terminal-based monitoring</a> and
    <a href="/blog/website-down-checker-free">free checks for a down site</a>.</p>
  </div>
</section>
''',
    },
}


def update_sitemap(slug_path):
    path = f'{SITE}/sitemap.xml'
    c = open(path).read()
    url = f'{BASE}/{slug_path}'
    if f'<loc>{url}</loc>' in c:
        print(f'sitemap: {slug_path} already present')
        return
    add = (f'  <url><loc>{url}</loc><lastmod>{TODAY}</lastmod>'
           f'<changefreq>weekly</changefreq><priority>0.8</priority></url>\n')
    c = c.replace('</urlset>', add + '</urlset>')
    open(path, 'w').write(c)
    print(f'sitemap: added {slug_path}')


def check_links(files):
    broken = []
    for path in files:
        html = open(path).read()
        for m in sorted(set(re.findall(r'href="(/[^"#]*?)"', html))):
            url = m.split('?')[0]
            t = ('site' + url).rstrip('/')
            if not (os.path.exists(t) or os.path.exists(t + '.html') or url == '/'
                    or os.path.exists(t + '/index.html')):
                broken.append((path, m))
    return broken


def verify_hub():
    files = {os.path.basename(f)[:-5] for f in glob.glob(f'{SITE}/da/blog/*.html')}
    hub = set(re.findall(r'href="/da/blog/([^"]+)"', open(f'{SITE}/da.html').read()))
    extra = hub - files
    missing = files - hub
    print(f'verify_hub: disk={len(files)} hub={len(hub)} missing_in_hub={sorted(missing)} dead_links={sorted(extra)}')
    assert not extra, f'hubbet linker til ikke-eksisterende sider: {extra}'


def add_hub_card(p):
    path = f'{SITE}/da.html'
    c = open(path).read()
    card_url = f'/da/blog/{p["slug"]}'
    if card_url in c:
        print(f'hub: {p["slug"]} already present')
        return
    card = f'''
      <div class="product-card">
        <div class="product-badge product-badge-secondary">{p['hub_badge']}</div>
        <div class="product-body">
          <h3><a href="{card_url}" style="color:inherit;text-decoration:none;">{p['hub_title']}</a></h3>
          <p class="product-desc">{p['hub_desc']}</p>
          <div class="product-details"><span class="product-meta">📖 5 min</span><span class="product-meta">🇩🇰 Dansk guide</span></div>
          <a href="{card_url}" class="btn-secondary" style="margin-top:12px;">Læs guide →</a>
        </div>
      </div>
'''
    pos = c.rfind('<a href="/da/blog/')
    end = c.find('\n      </div>\n', pos)
    ins = end + len('\n      </div>\n')
    c = c[:ins] + card + c[ins:]
    open(path, 'w').write(c)
    print(f'hub: card added for {p["slug"]}')


def main():
    outs, all_files = [], []
    for p in PAGES:
        da_out = f'{SITE}/da/blog/{p["slug"]}.html'
        en_out = f'{SITE}/blog/{p["en_slug"]}.html'
        assert not os.path.exists(da_out), f'{da_out} exists already'
        assert not os.path.exists(en_out), f'{en_out} exists already'
        for out, page in ((da_out, build_page(p)), (en_out, build_en(p))):
            with open(out, 'w') as f:
                f.write(page)
            blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL)
            for b in blocks:
                d = json.loads(b)
                assert d['@context'] == 'https://schema.org', d['@context']
            print(f'{out} written, JSON-LD OK ({len(blocks)} blocks)')
            update_sitemap('blog/' + os.path.basename(out)[:-5] if '/blog/' in out else 'da/blog/' + p['slug'])
            all_files.append(out)
        add_hub_card(p)
        outs.append(da_out)

    verify_hub()
    broken = check_links(all_files + [f'{SITE}/da.html'])
    if broken:
        print('BROKEN INTERNAL LINKS:')
        for path, link in broken:
            print(f'  {path} -> {link}')
        sys.exit(1)
    print('Internal link check: OK')


if __name__ == '__main__':
    main()
