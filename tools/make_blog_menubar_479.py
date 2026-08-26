#!/usr/bin/env python3
"""Iteration 479: EN+DA blogpar — "macOS menu bar website monitor".
Targets: "macos menu bar website monitor" / "overvaag hjemmeside fra mac menu bar".
Funnel: blog -> /deskuptime/. Samme moenster som make_blog_down_alert.py:
Article + FAQPage JSON-LD, hreflang-par (en<>da), idempotent sitemap.
"""
import json, os, re

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-26'
ROOT = '/Users/madsholstjensen/hermes-passiv'
URL_EN = f'{BASE}/blog/macos-menu-bar-website-monitor'
URL_DA = f'{BASE}/da/blog/overvaag-hjemmeside-mac-menu-bar'

FAQS_EN = [
    ('Is there a free macOS menu bar website monitor?',
     'Yes. DeskUptime is a lightweight macOS app that lives in your menu bar '
     'and checks any list of URLs on an interval you choose. You get a native '
     'macOS notification the moment a site goes down and again when it comes '
     'back \u2014 with no account and no monthly fee.'),
    ('Does a menu bar monitor work when my Mac is asleep?',
     'No local tool can. Checks only run while your Mac is awake and the app '
     'is running \u2014 which is exactly how you want it if you are watching '
     'your own sites during the workday. For 24/7 coverage you would need a '
     'server-side monitor.'),
    ('How often can it check my site?',
     'You pick per watchlist: every 1, 5, 10 or 30 minutes. A built-in floor of '
     '60 seconds between checks of the same URL keeps you polite to your own '
     'server.'),
    ('Will it tell me when the site is back up?',
     'Yes. DeskUptime compares each result with the previous status and sends a '
     'separate recovery notification, so you know both when something breaks '
     'and when it is fixed.'),
    ('Can I also check SSL certificates from the menu bar?',
     'The companion CLI can: <code>deskuptime check https://yoursite.com</code> '
     'reports HTTP status, response time and days until your TLS certificate '
     'expires. The app covers uptime; the CLI adds certificate and scripting '
     'workflows.'),
]
FAQS_DA = [
    ('Findes der en gratis macOS menu bar overvaagning af hjemmesider?',
     'Ja. DeskUptime er et let macOS-program der bor i din menu bar og tjekker '
     'en liste af URL\u2019er med et interval du selv vaelger. Du faar en '
     'native macOS-notifikation i det oeblik et site gaar ned \u2014 og igen '
     'naar det kommer tilbage. Uden konto og uden abonnement.'),
    ('Virker en menu bar-monitor naar min Mac soever?',
     'Nej, det kan ingen lokal vaerktoej. Tjek koerer kun mens Mac\u2019en er '
     'vaagen og programmet korer \u2014 hvilket netop er det, du vil ha, naar '
     'du overvaager egne sider i arbejdstiden. Doegningsdaekning kraever en '
     'serverbaseret loesning.'),
    ('Hvor ofte kan den tjekke mit site?',
     'Du vaelger pr. liste: hvert 1., 5., 10. eller 30. minut. En indbygget '
     'nedre graense paa 60 sekunder mellem tjek af samme URL holder dig venlig '
     'over for din egen server.'),
    ('Faar jeg besked naaret sitet er oppe igen?',
     'Ja. DeskUptime sammenligner hvert resultat med den forrige status og '
     'sender en separat opsvings-notifikation, sa du ved baade naaret noget '
     'gaar i stykker og naaret det er rettet.'),
    ('Kan jeg ogsaa tjekke SSL-certifikater fra menu bar\u2019en?',
     'Kommandolinje-vaerktoejet kan: <code>deskuptime check '
     'https://yoursite.com</code> viser HTTP-status, svartid og antal dage til '
     'dit TLS-certifikat udoeber. Appen doekker oppetid; CLI\u2019en laegger '
     'certifikat-tjek og script-arbejdsgange ovenpaa.'),
]

def head(url, lang, other_url, title, desc):
    return f"""  <link rel="canonical" href="{url}">
  <link rel="alternate" hreflang="{lang}" href="{url}">
  <link rel="alternate" hreflang="{'da' if lang=='en' else 'en'}" href="{other_url}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{url}">
"""

def build(lang):
    other = URL_DA if lang == 'en' else URL_EN
    if lang == 'en':
        url = URL_EN
        title = 'MacOS Menu Bar Website Monitor (Free, No Account)'
        desc = ('Watch your websites straight from the macOS menu bar. Native '
                'notifications when a site goes down \u2014 and when it comes '
                'back. Free desktop app, one-time upgrade, no monthly fee.')
        badge = 'MACOS &middot; MENU BAR &middot; UPTIME'
        h1 = 'Your websites,<br>watched from the menu bar'
        sub = ('DeskUptime sits quietly in your macOS menu bar, checks your '
               'sites every few minutes, and pings you natively the moment one '
               'goes down \u2014 or comes back.')
        cta = 'Download for macOS &rarr;'
        cards = """
      <div class="card"><h3>&#128268; Lives in the menu bar</h3><p>A tiny status icon shows overall health at a glance. Green means all sites up; click it to see every watchlist.</p></div>
      <div class="card"><h3>&#128276; Native notifications</h3><p>Downtime alerts and recovery alerts arrive as real macOS notifications. No email to miss.</p></div>
      <div class="card"><h3>&#127760; Your URLs stay private</h3><p>Checks run from your Mac. The URL list lives in a local file &mdash; nothing is uploaded anywhere.</p></div>"""
        steps_h2 = 'Set it up in two minutes'
        steps = """<li><strong>Download</strong> DeskUptime for macOS below.</li>
      <li><strong>Add your URLs</strong> to a watch list.</li>
      <li><strong>Pick an interval</strong> (1&ndash;30 min) and leave the app in the menu bar.</li>"""
        cli_note = ('Also available as a CLI: <code>deskuptime check</code> runs '
                    'a round right now and exits non-zero if anything is down '
                    '&mdash; perfect for scripts and CI.')
        faqs = FAQS_EN
        related_label = 'Related guides'
        related = [('/blog/get-notified-when-website-goes-down', 'Get notified when your website goes down'),
                   ('/blog/desktop-website-monitor-cli', 'Desktop website monitor vs. CLI checks'),
                   ('/blog/check-ssl-certificate-expiry', 'Check SSL certificate expiry')]
        footer_extra = '<a href="/blog/desktop-website-monitor-cli">Monitor guide</a>'
    else:
        url = URL_DA
        title = 'Overvaag hjemmesider fra Mac menu bar\u2019en (gratis)'
        desc = ('Hold oje med dine hjemmesider direkte fra macOS menu bar\u2019en. '
                'Native notifikationer naaret et site gaar ned \u2014 og naaret '
                'det kommer tilbage. Gratis skrivebordsprogram, ingen maanedsbetaling.')
        badge = 'MACOS &middot; MENU BAR &middot; OPPETID'
        h1 = 'Dine hjemmesider,<br>overvaaget fra menu bar\u2019en'
        sub = ('DeskUptime ligger stille i din macOS menu bar, tjekker dine '
               'sider hvert par minutter og giver dig en native notifikation i '
               'det oeblik en side gaar ned \u2014 eller kommer tilbage.')
        cta = 'Download til macOS &rarr;'
        cards = """
      <div class="card"><h3>&#128268; Bor i menu bar\u2019en</h3><p>Et lille status-ikon viser samlet sundhed ved et blik. Groent betyder alle sider oppe; klik for at se hver liste.</p></div>
      <div class="card"><h3>&#128276; Native notifikationer</h3><p>Nedbruds- og opsvingsalarmer kommer som rigtige macOS-notifikationer. Ingen mail at overse.</p></div>
      <div class="card"><h3>&#127760; Dine URL\u2019ers forbliver private</h3><p>Tjekene koerer fra din Mac. URL-listen ligger i en lokal fil &mdash; intet uploades nogetsted.</p></div>"""
        steps_h2 = 'Saet det op paa to minutter'
        steps = """<li><strong>Download</strong> DeskUptime til macOS nedenfor.</li>
      <li><strong>Tilfoej dine URL\u2019er</strong> til en overvaagningsliste.</li>
      <li><strong>Vaelg interval</strong> (1&ndash;30 min) og lad appen blive i menu bar\u2019en.</li>"""
        cli_note = ('Faas ogsaa som CLI: <code>deskuptime check</code> koerer en '
                    'runde med det samme og afslutter med fejlkode, hvis noget '
                    'er nede &mdash; perfekt til scripts og CI.')
        faqs = FAQS_DA
        related_label = 'Relaterede guider'
        related = [('/da/blog/faa-besked-naar-hjemmeside-er-nede', 'Faa besked naaret din hjemmeside gaar ned'),
                   ('/da/blog/overvaag-hjemmeside-fra-terminalen', 'Overvaag hjemmeside fra terminalen'),
                   ('/da/blog/tjek-ssl-certifikat-udloeb', 'Tjek SSL-certifikatets udoeb')]
        footer_extra = '<a href="/da/blog/overvaag-hjemmeside-fra-terminalen">Terminal-guide</a>'

    art = {'@context': 'https://schema.org', '@type': 'Article',
           'headline': title, 'description': desc, 'url': url,
           'datePublished': TODAY, 'dateModified': TODAY,
           'inLanguage': lang,
           'author': {'@type': 'Organization', 'name': 'Mahope Tools'},
           'publisher': {'@type': 'Organization', 'name': 'Mahope Tools'}}
    faq = {'@context': 'https://schema.org', '@type': 'FAQPage',
           'mainEntity': [{'@type': 'Question', 'name': re.sub('<[^>]+>', '', q),
                           'acceptedAnswer': {'@type': 'Answer',
                                              'text': re.sub('<[^>]+>', '', a)}}
                          for q, a in faqs]}

    faq_html = '\n'.join(
        f'    <details><summary>{q}</summary><p>{a}</p></details>'
        for q, a in faqs)
    rel_html = '\n'.join(
        f'<a href="{href}" style="color:var(--color-accent);">{label}</a>' +
        (' &middot; ' if i < len(related)-1 else '')
        for i, (href, label) in enumerate(related))

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
{head(url, lang, other, title, desc)}<script type="application/ld+json">{json.dumps(art)}</script>
<script type="application/ld+json">{json.dumps(faq)}</script>
<style>
:root{{--bg:#0f1220;--card:#181c2f;--text:#e8eaf2;--muted:#9aa1b5;--accent:#6ea8fe;--border:#2a2f4a}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);line-height:1.65}}
.container{{max-width:800px;margin:0 auto;padding:48px 24px 80px}}
.badge{{letter-spacing:.12em;font-size:.75em;color:var(--muted)}}
h1{{font-size:clamp(2rem,5vw,2.8rem);line-height:1.15;margin:.4em 0 .3em}}
.sub{{color:var(--muted);font-size:1.15em;margin-bottom:28px}}
.btn{{display:inline-block;background:var(--accent);color:#0f1220;font-weight:700;padding:13px 26px;border-radius:10px;text-decoration:none}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin:36px 0}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px}}
.card h3{{margin:0 0 8px;font-size:1.05em}}
.card p,.muted{{color:var(--muted)}}
ol li{{margin-bottom:10px}}
details{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 18px;margin-bottom:10px}}
summary{{cursor:pointer;font-weight:600}}
footer{{border-top:1px solid var(--border);margin-top:56px;padding-top:24px;color:var(--muted);text-align:center}}
code{{background:var(--card);padding:2px 6px;border-radius:6px;font-size:.92em}}
@media(max-width:520px){{.container{{padding:32px 16px 64px}}}}
</style>
</head>
<body>
<div class="container">
  <span class="badge">{badge}</span>
  <h1>{h1}</h1>
  <p class="sub">{sub}</p>
  <p><a class="btn" href="/deskuptime/">{cta}</a></p>

  <div class="cards">{cards}
  </div>

  <h2>{steps_h2}</h2>
  <ol>
    {steps}
  </ol>
  <p class="muted">{cli_note}</p>

  <h2>Frequently asked questions</h2>
{faq_html}

  <h2>{related_label}</h2>
  <p>{rel_html}</p>

  <footer>{footer_extra} &middot; <a href="/">Home</a></footer>
</div>
</body>
</html>"""


OUT_EN = os.path.join(ROOT, 'site', 'blog', 'macos-menu-bar-website-monitor.html')
OUT_DA = os.path.join(ROOT, 'site', 'da', 'blog', 'overvaag-hjemmeside-mac-menu-bar.html')
os.makedirs(os.path.dirname(OUT_DA), exist_ok=True)
with open(OUT_EN, 'w', encoding='utf-8') as f:
    f.write(build('en'))
with open(OUT_DA, 'w', encoding='utf-8') as f:
    f.write(build('da'))

# --- validate JSON-LD ---
for path in (OUT_EN, OUT_DA):
    html = open(path, encoding='utf-8').read()
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    assert len(blocks) == 2, path
    for b in blocks:
        d = json.loads(b)
        assert d['@context'] == 'https://schema.org'
    print('OK', path)

# --- idempotent sitemap update ---
SM = os.path.join(ROOT, 'site', 'sitemap.xml')
sm = open(SM, encoding='utf-8').read()
for url in (URL_EN, URL_DA):
    loc = f'<url><loc>{url}</loc>'
    if url not in sm:
        entry = (f'<url><loc>{url}</loc><lastmod>{TODAY}</lastmod>'
                 f'<xhtml:link rel="alternate" hreflang="en" href="{URL_EN}"/>'
                 f'<xhtml:link rel="alternate" hreflang="da" href="{URL_DA}"/>'
                 '</url>\n')
        sm = sm.replace('</urlset>', entry + '</urlset>')
open(SM, 'w', encoding='utf-8').write(sm)
import xml.dom.minidom
xml.dom.minidom.parse(SM)
print('sitemap OK,', sm.count('<loc>'), 'urls')

# --- internal link check against filesystem ---
missing = []
htmls = {p: open(p, encoding='utf-8').read() for p in (OUT_EN, OUT_DA)}
for p, html in htmls.items():
    for m in re.finditer(r'href="(/[^"#]*)(#[^"]*)?"', html):
        t = m.group(1)
        cand = os.path.join(ROOT, 'site', t.lstrip('/'))
        if not any(os.path.exists(c) for c in
                   (cand, cand + '.html', os.path.join(cand, 'index.html'))):
            missing.append((os.path.basename(p), t))
print('missing targets:', missing if missing else 'NONE')
