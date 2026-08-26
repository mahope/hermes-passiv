#!/usr/bin/env python3
"""Iteration 478: EN+DA blogpar — "Get notified when your website goes down".
Targets: "get notified when website goes down" / "faa beskod naar hjemmeside er nede".
Funnel: blog -> /deskuptime/ (product). Idempotent sitemap, hreflang pair,
JSON-LD Article + FAQPage, reciprocal cross-links from the CLI-monitor posts.
"""
import json, os, re, xml.dom.minidom

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-26'
ROOT = '/Users/madsholstjensen/hermes-passiv'
URL_EN = f'{BASE}/blog/get-notified-when-website-goes-down'
URL_DA = f'{BASE}/da/blog/faa-besked-naar-hjemmeside-er-nede'
REL_DL = 'https://github.com/mahope/deskuptime/releases/download/desktop-v0.2.7'

FAQS_EN = [
    ('How do I get notified when my website goes down?',
     'The simplest free way is a small script or app on your own machine that '
     'checks your URL every few minutes and sends an OS notification when the '
     'status changes. DeskUptime does exactly this: add your URLs, pick an '
     'interval from 1 minute, and you get a native notification the moment a '
     'site goes down and when it comes back.'),
    ('Is there a free alternative to uptime monitoring SaaS?',
     'Yes. Cloud SaaS monitors charge $10\u201315 per month per project for what '
     'is essentially a scheduled HTTP request plus an email. A desktop monitor '
     'like DeskUptime is a one-time purchase, keeps your URL list private on '
     'your machine, and never has a monthly fee.'),
    ('How often should my site be checked?',
     'For most sites every 5 minutes is plenty \u2014 it catches outages within '
     'minutes without hammering your server. DeskUptime enforces a minimum of '
     '60 seconds between checks of the same URL and supports 1, 5, 10 and '
     '30 minute intervals.'),
    ('Will I know when the site comes back up?',
     'Yes \u2014 recovery alerts matter as much as downtime alerts. DeskUptime '
     'compares each result to the previous status and notifies you both when a '
     'site goes DOWN and when it is back UP.'),
    ('Does anything run in the cloud?',
     'No. Checks run from your own computer, so your URL list and results stay '
     'private. The trade-off: notifications only arrive while the app is '
     'running, which for freelancers and small teams watching their own sites '
     'is exactly when they want them.'),
]
FAQS_DA = [
    ('Hvordan faar jeg besked naar min hjemmeside er nede?',
     'Den enkleste gratis metode er et lille program paa din egen maskine, der '
     'tjekker din URL med faa minutters interval og sender en '
     'operativsystem-notifikation naar status aendres. DeskUptime goer praecis '
     'det: tilfoej dine URL\'er, vaelg et interval fra 1 minut, og du faar en '
     'notifikation i det oeblik et site gaar ned \u2014 og naar det kommer tilbage.'),
    ('Findes der et gratis alternativ til overvaagnings-tjenester?',
     'Ja. Skybaserede tjenester koster typisk 70\u2013100 kr. om maaneden for i '
     'praksis en planlagt HTTP-forespargoergsel plus en mail. Et '
     'skrivebordsprogram som DeskUptime koebes een gang, holder din URL-liste '
     'privat paa din egen maskine og har aldrig en maanedsbetaling.'),
    ('Hvor ofte boer mit site tjekkes?',
     'For de fleste sider er hvert 5. minut rigeligt \u2014 det fanger nedbrud '
     'hurtigt uden at belaste serveren. DeskUptime haandhaever minimum 60 '
     'sekunder mellem tjek af samme URL og understoetter 1, 5, 10 og 30 minutter.'),
    ('Faar jeg ogsaa at vide naaret sitet kommer op igen?',
     'Ja \u2014 opsving er mindst lige sa vigtigt som nedbrud. DeskUptime '
     'sammenligner hvert resultat med den forrige status og giver besked baade '
     'naar et site gaar DOWN og naar det er UP igen.'),
    ('Koerer noget i skyen?',
     'Nej. Tjekkene koerer fra din egen computer, saa din URL-liste og dine '
     'resultater forbliver private. Bemoerkningen: notifikationer kommer kun, '
     'mens appen koerer \u2014 hvilket netop er naar du selv sidder ved maskinen.'),
]

def jsonld(url, lang, headline, desc, faqs):
    art = {'@context': 'https://schema.org', '@type': 'Article',
           'headline': headline, 'description': desc, 'url': url,
           'datePublished': TODAY, 'dateModified': TODAY,
           'inLanguage': lang,
           'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
           'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'}}
    faq = {'@context': 'https://schema.org', '@type': 'FAQPage',
           'mainEntity': [{'@type': 'Question', 'name': q,
                           'acceptedAnswer': {'@type': 'Answer', 'text': a}}
                          for q, a in faqs]}
    return art, faq

def build(lang):
    if lang == 'en':
        url, other = URL_EN, URL_DA
        title = 'Get Notified When Your Website Goes Down (Free Desktop Monitor)'
        desc = ('Stop finding out about downtime from customers. A lightweight '
                'desktop monitor checks your sites every few minutes and sends a '
                'native notification the moment one goes down \u2014 and when it '
                'recovers. One-time purchase, no monthly fee.')
        badge = 'UPTIME &middot; ALERTS &middot; DESKTOP'
        h1 = 'Get notified the moment<br>your website goes down'
        sub = ('Cloud monitors charge a subscription to send you an email. A tiny '
               'desktop app checks your sites itself and pings your operating '
               'system directly \u2014 downtime caught in minutes, not hours.')
        cta = 'Download Deskuptime &rarr;'
        how_h2 = 'Three ways to get downtime alerts'
        cards = """
      <div class="card"><h3>&#128276; Native OS notifications</h3><p>DeskUptime watches every URL you add and fires a real macOS/Windows notification when a site goes DOWN and again when it is back UP. No inbox, no missed emails.</p></div>
      <div class="card"><h3>&#9201;&#65039; Intervals from 1 minute</h3><p>Pick 1, 5, 10 or 30 minutes per watchlist. A built-in floor of 60 seconds keeps you polite to your own server.</p></div>
      <div class="card"><h3>&#128190; Your data stays yours</h3><p>The URL list and history live in a local file on your machine. Nothing is uploaded anywhere, ever.</p></div>"""
        cli = ('Prefer the terminal? The same engine ships as a CLI: '
               '<code>deskuptime check</code> runs a round right now and exits '
               'non-zero if anything is down \u2014 easy to wire into scripts.')
        steps_h2 = 'Set it up in two minutes'
        steps = """<li><strong>Download</strong> DeskUptime for macOS or Windows below.</li>
      <li><strong>Add URLs</strong> to your watch list.</li>
      <li><strong>Choose an interval</strong> and leave the app running in the menu bar / tray.</li>"""
        faqs = FAQS_EN
        related_label = 'Desktop website monitor vs. CLI uptime checks'
        footer_extra = '<a href="/blog/desktop-website-monitor-cli">Monitor guide</a>'
    else:
        url, other = URL_DA, URL_EN
        title = 'Faa besked naar din hjemmeside gaar ned (gratis skrivebordsovervaagning)'
        desc = ('Slut paa at hoere om nedbrud fra kunderne. Et let '
                'skrivebordsprogram tjekker dine sider hvert par minutter og '
                'sender en notifikation i det oeblik en side gaar ned \u2014 og '
                'naar den kommer tilbage. Eengangsbealing, ingen abonnement.')
        badge = 'OPPETID &middot; ALARMER &middot; DESKTOP'
        h1 = 'Faa besked i det oeblik<br>din hjemmeside gaar ned'
        sub = ('Skytjenester opkræver et abonnement for at sende dig en mail. Et '
               'lille skrivebordsprogram tjekker selv dine sider og raaber direkte '
               'i operativsystemet \u2014 nedbrud fanget paa minutter, ikke timer.')
        cta = 'Download Deskuptime &rarr;'
        how_h2 = 'Tre maader at faa nedbrudsalarmer paa'
        cards = """
      <div class="card"><h3>&#128276; Notifikationer i styresystemet</h3><p>DeskUptime overvaager alle URL'er paa din liste og uloeser en rigtig macOS/Windows-notifikation naaret et site gaar DOWN \u2014 og igen naaret det er UP igen. Ingen indbakke, ingen mistede mails.</p></div>
      <div class="card"><h3>&#9201;&#65039; Interval fra 1 minut</h3><p>Vaelg 1, 5, 10 eller 30 minutter pr. liste. En indbygget nedre graense paa 60 sekunder holder dig hoeflig mod din egen server.</p></div>
      <div class="card"><h3>&#128190; Dine data bliver dine</h3><p>URL-listen og historikken ligger i en lokal fil paa din maskine. Intet uploades nogensinde.</p></div>"""
        cli = ('Foretraekker du terminalen? Samme motor findes som CLI: '
               '<code>deskuptime check</code> koerer en runde nu og returnerer '
               'fejlkode, hvis noget er nede \u2014 let at bygge ind i scripts.')
        steps_h2 = 'Saet det op paa to minutter'
        steps = """<li><strong>Download</strong> DeskUptime til macOS eller Windows herunder.</li>
      <li><strong>Tilfoej URL'er</strong> til din overvaagningsliste.</li>
      <li><strong>Vaelg interval</strong> og lad appen koere i menulinjen / bakken.</li>"""
        faqs = FAQS_DA
        related_label = 'Skrivebords-overvaagning vs. CLI-tjek af oppetid'
        footer_extra = '<a href="/da/blog/overvaag-hjemmeside-fra-terminalen">Guide: overvaagning fra terminalen</a>'
    art, faq = jsonld(url, lang,
                      re.sub('<[^>]+>', '', title.replace('(Gratis', '(gratis')), desc, faqs)
    dl = ''
    if lang == 'en':
        dl = f"""<div style="text-align:center;margin-top:24px;">
      <a class="btn-primary" href="{REL_DL}/DeskUptime-macOS-aarch64-apple-darwin.zip">macOS (Apple Silicon)</a>
      &nbsp; <a class="btn-primary" href="{REL_DL}/DeskUptime_0.2.7_x64-setup.exe">Windows</a>
      &nbsp; <a class="btn-secondary" href="/deskuptime/">Product page</a>
    </div>"""
    else:
        dl = f"""<div style="text-align:center;margin-top:24px;">
      <a class="btn-primary" href="{REL_DL}/DeskUptime-macOS-aarch64-apple-darwin.zip">macOS (Apple Silicon)</a>
      &nbsp; <a class="btn-primary" href="{REL_DL}/DeskUptime_0.2.7_x64-setup.exe">Windows</a>
      &nbsp; <a class="btn-secondary" href="/da/deskuptime/">Produktside</a>
    </div>"""
    faq_html = '\n    '.join(f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in faqs)
    home = '/' if lang == 'en' else '/da/'
    html = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="{lang}" href="{url}">
<link rel="alternate" hreflang="{'da' if lang == 'en' else 'en'}" href="{other}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{json.dumps(art, ensure_ascii=False)}
</script>
<script type="application/ld+json">
{json.dumps(faq, ensure_ascii=False)}
</script>
<script defer src="/track.js"></script>
<style>
  .compare {{ width:100%; border-collapse:collapse; font-size:0.92rem; margin:1.5rem 0; }}
  .compare th, .compare td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--color-border); vertical-align:top; }}
  .compare th {{ border-bottom:2px solid var(--color-border); }}
</style>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">{badge}</div>
    <h1>{h1}</h1>
    <p class="subtitle">{sub}</p>
    <div class="hero-cta">
      <a href="/{'da/' if lang == 'da' else ''}deskuptime/" class="btn-primary">{cta}</a>
      <a href="#how" class="btn-secondary">{'How it works' if lang == 'en' else 'Sadan virker det'}</a>
    </div>
    <p class="hero-note">{TODAY} &middot; 4 minute read</p>
  </div>
</header>

<section class="products" id="how">
  <div class="container">
    <h2>{how_h2}</h2>
    <div class="problem-cards">{cards}
    </div>
    <p style="margin-top:16px;">{cli}</p>

    <h2 style="margin-top:32px;">{steps_h2}</h2>
    <ol>
      {steps}
    </ol>
    {dl}

    <h2 style="margin-top:40px;">{'What you pay' if lang == 'en' else 'Hvad koster det'}</h2>
    <table class="compare">
      <thead><tr><th>{'Option' if lang == 'en' else 'Mulighed'}</th><th>{'Cost' if lang == 'en' else 'Pris'}</th><th>{'Catch' if lang == 'en' else 'Bemaerkning'}</th></tr></thead>
      <tbody>
        <tr><td>{'Cloud SaaS monitor' if lang == 'en' else 'Skybaseret overvaagning'}</td><td>$10&ndash;15/{'month' if lang == 'en' else 'md.'}</td><td>{'Recurring forever, URL list leaves your machine' if lang == 'en' else 'Loebende for altid, URL-listen forlader din maskine'}</td></tr>
        <tr><td>cron + curl + mail</td><td>{'Free' if lang == 'en' else 'Gratis'}</td><td>{'You maintain the script and a mail relay' if lang == 'en' else 'Du vedligeholder scriptet og en mailrelay'}</td></tr>
        <tr><td><a href="/{'da/' if lang == 'da' else ''}deskuptime/" style="color:var(--color-accent);">DeskUptime</a></td><td>$19 {'once' if lang == 'en' else 'een gang'}</td><td>{'Notifications only while the app runs' if lang == 'en' else 'Notifikationer kun mens appen koerer'}</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>FAQ</h2>
    <div class="problem-cards">
    {faq_html}
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/{'da/' if lang == 'da' else ''}deskuptime/" class="btn-primary">{cta}</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>{'Related' if lang == 'en' else 'Relateret'}: <a href="{other}" style="color:var(--color-accent);">{'Dansk version' if lang == 'en' else 'English version'}</a> &middot; {footer_extra}</p></div>
<footer style="padding:32px 24px;">
  <p><a href="{home}">&larr; {'Home' if lang == 'en' else 'Forside'}</a> &middot; <a href="{home}blog/">{'Blog' if lang == 'en' else 'Blog'}</a> &middot; <a href="/{'da/' if lang == 'da' else ''}deskuptime/">DeskUptime</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
</script>
</body>
</html>
'''
    # validate JSON-LD
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    assert len(blocks) == 2
    for b in blocks:
        parsed = json.loads(b)
        assert parsed['@context'] == 'https://schema.org'
    print(f'{lang}: JSON-LD OK')
    return html

out_en = os.path.join(ROOT, 'site/blog/get-notified-when-website-goes-down.html')
out_da = os.path.join(ROOT, 'site/da/blog/faa-besked-naar-hjemmeside-er-nede.html')
open(out_en, 'w').write(build('en'))
open(out_da, 'w').write(build('da'))
print('wrote', out_en)
print('wrote', out_da)

# --- sitemap (idempotent) ---
sm = os.path.join(ROOT, 'site/sitemap.xml')
c = open(sm).read()
added = False
for u in (URL_EN, URL_DA):
    if u + '</loc>' not in c:
        c = c.replace('</urlset>', f'<url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url></urlset>')
        added = True
open(sm, 'w').write(c)
xml.dom.minidom.parse(sm)
print('sitemap parses,', c.count('<loc'), 'urls,', 'added 2' if added else 'already present')

# --- reciprocal cross-links from existing monitor posts ---
def add_related(path, label):
    x = open(path).read()
    if 'get-notified-when-website-goes-down' in x or 'faa-besked-naar-hjemmeside-er-nede' in x:
        print(path, ': already linked')
        return
    x = x.replace('</body>', f'<div style="text-align:center;margin-top:16px;"><p>Related: <a href="{URL_EN if "overvaag" in path or "terminalen" in path else URL_DA}" style="color:var(--color-accent);">{label}</a></p></div>\n</body>', 1)
    open(path, 'w').write(x)
    print(path, ': cross-linked')

add_related(os.path.join(ROOT, 'site/blog/desktop-website-monitor-cli.html'), 'Get notified when your website goes down')
add_related(os.path.join(ROOT, 'site/da/blog/overvaag-hjemmeside-fra-terminalen.html'), 'Faa besked naar din hjemmeside gaar ned')
