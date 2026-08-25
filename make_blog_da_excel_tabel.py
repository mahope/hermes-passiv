#!/usr/bin/env python3
"""Iteration 231: dansk blogpost "Kopiér en tabel fra en hjemmeside ind i Excel".
Samme mønster som iter 230 (Notion DA-posten). Article + FAQPage JSON-LD,
canonical, FAQ, sammenligningstabel, CTA til /clean-copy.
Tilføjer posten i sitemap.xml og gensidige krydslinks fra søsterposter."""

import json, re

SLUG = "kopier-tabel-hjemmeside-til-excel"
URL = f"https://hermes-passiv.pages.dev/blog/{SLUG}"

ARTICLE_LD = {
    "@context": "https://schema.org", "@type": "Article",
    "headline": "Kopiér en tabel fra en hjemmeside ind i Excel (rækker og kolonner intakte)",
    "description": "Få en vilkårlig webtabel ind i Excel med hver værdi i sin egen celle — ingen CSV-omveje, ingen OCR, ingen manuel rettelse.",
    "url": URL, "datePublished": "2026-08-25", "dateModified": "2026-08-25",
    "author": {"@type": "Organization", "name": "Hermes Compliance"},
    "publisher": {"@type": "Organization", "name": "Hermes Compliance"},
}

FAQS = [
    ("Hvordan kopierer jeg en tabel fra en hjemmeside ind i Excel?",
     "Installér den gratis Clean Copy-udvidelse til Chrome eller Firefox, klik på ikonen mens tabellen er på skærmen, vælg Kopiér som Markdown — sæt ind i Excel med Ctrl+V (Cmd+V på Mac), og brug derefter Data → Tekst til kolonner med | som skilletegn. Hver værdi lander i sin egen celle."),
    ("Hvorfor ender indsatte tabeller i én kolonne i Excel?",
     "Hvis udklipsholderen kun indeholder almindelig tekst uden ensartede skilletegn, kan Excel ikke se hvor én celle slutter og den næste begynder — så stables alle værdierne i én kolonne. Når du kopierer selve tabel-elementet som markdown (som Clean Copy gør), er række- og kolonnegrænserne bevaret, og Tekst til kolonner kan adskille dem på sekunder."),
    ("Kan jeg springe Tekst til kolonner over?",
     "Ja. Clean Copy kan også kopiere som ren tekst fra HTML-tabeller, og hvis du markerer tabellen direkte i browseren og bruger Kopiér som Markdown, kan du i stedet indsætte via Data → Fra web eller gemme markdown-tabellen som .csv og åbne den i Excel. Men Tekst til kolonner er hurtigst for engangsjob."),
    ("Virker det på tabeller bag et login?",
     "Ja. Clean Copy kører i din egen browser-session, så enhver tabel du kan se, mens du er logget ind, kan kopieres — dashboards, adminpaneler, bankoversigter, SaaS-rapporter. Serverbaserede scrapere fejler typisk her."),
    ("Bliver noget sendt til en server?",
     "Nej. Clean Copy arbejder helt inde i din browser. Tabellen forlader ikke din maskine, før du selv indsætter den der, hvor den skal bruges."),
]

FAQPAGE_LD = {
    "@context": "https://schema.org", "@type": "FAQPage",
    "mainEntity": [
        {"@type": "Question", "name": q,
         "acceptedAnswer": {"@type": "Answer", "text": a}}
        for q, a in FAQS
    ],
}

def ld(obj):
    return json.dumps(obj, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kopiér en tabel fra en hjemmeside ind i Excel (2026-guide)</title>
<meta name="description" content="Få enhver webtabel ind i Excel med hver værdi i sin egen celle — ingen CSV-omveje, ingen OCR, ingen manuel rettelse.">
<meta property="og:type" content="article">
<meta property="og:title" content="Kopiér en tabel fra en hjemmeside ind i Excel">
<meta property="og:description" content="Få enhver webtabel ind i Excel med alle celler på plads — ingen OCR, ingen manuel rettelse.">
<meta property="og:image" content="https://hermes-passiv.pages.dev/clean-copy/og-preview.png">
<meta property="og:url" content="__URL__">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="__URL__">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
__ARTICLE__
</script>
<script type="application/ld+json">
__FAQ__
</script>
<script defer src="/track.js"></script>
<style>
  .compare { width:100%; border-collapse:collapse; font-size:0.92rem; margin:1.5rem 0; }
  .compare th, .compare td { text-align:left; padding:10px 12px; border-bottom:1px solid var(--color-border); vertical-align:top; }
  .compare th { border-bottom:2px solid var(--color-border); }
  pre.cmd {
    background:#0f172a; color:#e2e8f0; padding:14px 16px; border-radius:8px;
    overflow-x:auto; font-size:0.85rem; line-height:1.6; margin:0.8rem 0;
  }
  pre.cmd code { font-family:'SF Mono','Monaco','Fira Code',monospace; }
</style>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">EXCEL &middot; TABELLER &middot; NO-CODE</div>
    <h1>Kopiér en tabel fra en hjemmeside<br>ind i Excel</h1>
    <p class="subtitle">Konkurrentpriser, leadlister, researchedata — at få en levende webtabel ind i Excel betyder normalt CSV-eksport der ikke findes, eller en times cellerettelse i hånden. Her er to-klik-måden der lander med hver værdi i sin egen celle.</p>
    <div class="hero-cta">
      <a href="#how" class="btn-primary">Vis mig 2-klik-måden &rarr;</a>
      <a href="/clean-copy" class="btn-secondary">Om Clean Copy</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; Læsetid: 4 minutter</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>Hvorfor de sædvanlige metoder fejler</h2>
    <p>Excel vil have hver værdi i sin egen celle. Det svære er at få strukturen hel ned fra en live webside.</p>
    <div class="problem-cards">
      <div class="card"><h3>📋 Markér og kopiér giver rod</h3><p>Trækker du markøren hen over en tabel, fanger du ofte omgivende afsnit, reklamer og billedtekster — og cellerne kollapser, når du indsætter.</p></div>
      <div class="card"><h3>📸 Skærmbilleder kræver OCR</h3><p>Et skærmbillede er bare pixels for Excel. Du ender med at køre OCR og rette cifrene den rammer forkert — værre end at taste igen.</p></div>
      <div class="card"><h3>⌨️ CSV-omveje findes sjældent</h3><p>De fleste sider tilbyder slet ikke CSV-download, og hvor de gør, mister du formatering og skal igennem et import-flow alligevel.</p></div>
    </div>
  </div>
</section>

<section class="products" id="how">
  <div class="container">
    <h2>Løsningen: to klik</h2>
    <p>Den gratis <a href="/clean-copy" style="color:var(--color-accent);">Clean Copy</a>-udvidelse til Chrome og Firefox omdanner præcis den tabel din markør står i, til ren markdown — som Excel let deler op i celler.</p>

    <h3 style="margin-top:24px;">1. Installér</h3>
    <pre class="cmd"><code>Chrome Web Store eller Firefox Add-ons — søg på "Clean Copy",
installér, færdig.</code></pre>

    <h3 style="margin-top:24px;">2. Kopiér tabellen som markdown</h3>
    <pre class="cmd"><code>Åbn siden, klik et vilkårligt sted i tabellen,
klik på Clean Copy-ikonet, vælg "Copy as Markdown".</code></pre>

    <h3 style="margin-top:24px;">3. Indsæt i Excel</h3>
    <pre class="cmd"><code>Sæt ind i A1 med Ctrl+V (Cmd+V på Mac).
Markér kolonne A → Data → Tekst til kolonner
→ Adskilt → skriv | som skilletegn → Udfør.

Nu står hver værdi i sin egen celle, og hver
række på sin egen linje. Gem som .xlsx.</code></pre>

    <div class="problem-cards">
      <div class="card"><h3>✅ Hver værdi i sin egen celle</h3><p>Clean Copy læser det rigtige HTML <code>&lt;table&gt;</code>-element, så hver <code>&lt;td&gt;</code> bliver sin egen kolonne efter Tekst til kolonner.</p></div>
      <div class="card"><h3>🧹 Ingen junk-rækker</h3><p>Ingen reklamefragmenter, cookiebannere eller billedtekster — kun den tabel du pegede på.</p></div>
      <div class="card"><h3>🔐 Virker bag logins</h3><p>Dashboards, adminpaneler og SaaS-rapporter virker alle, fordi konverteringen sker i din egen loggede browser-session.</p></div>
    </div>
  </div>
</section>

<section class="products" id="options">
  <div class="container">
    <h2>Dine muligheder sammenlignet</h2>
    <table class="compare">
      <thead>
        <tr><th>Metode</th><th>Bevarer struktur?</th><th>Hage</th></tr>
      </thead>
      <tbody>
        <tr><td>Markér + kopiér tekst</td><td>Nej</td><td>Fanger ekstra indhold, celler kollapser til én kolonne</td></tr>
        <tr><td>Skærmbillede + OCR</td><td>Efter oprydning</td><td>Cifrefejl er svære at spotte</td></tr>
        <tr><td>CSV-download + import</td><td>Nogle gange</td><td>Kun hvor siden tilbyder eksport; mister formatering</td></tr>
        <tr><td>Excel Data → Fra web</td><td>Ofte</td><td>Fejler bag logins og på dynamiske sider</td></tr>
        <tr>
          <td><a href="/clean-copy" style="color:var(--color-accent);">Clean Copy — Copy as Markdown</a></td>
          <td>Ja</td>
          <td>Kræver gratis browserudvidelse + ét ekstra trin (Tekst til kolonner)</td>
        </tr>
      </tbody>
    </table>
    <p>Ligger tabellen bag et login eller renderer dynamisk, fejler serverbaserede scrapere og import-flows — et lokalt kopieringsværktøj der virker i din session er den pålidelige mulighed.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
__FAQCARDS__
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/clean-copy" class="btn-primary">Hent Clean Copy gratis &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="/blog/copy-table-website-to-google-sheets" style="color:var(--color-accent);">Copy a Table From a Website Into Google Sheets (EN)</a> &middot; <a href="/blog/kopier-tabel-hjemmeside-til-notion" style="color:var(--color-accent);">Kopiér en tabel ind i Notion (DA)</a> &middot; <a href="/blog/copy-table-website-to-notion" style="color:var(--color-accent);">Copy a Table Into Notion (EN)</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/"> &larr; Forside</a> &middot; <a href="/clean-copy">Clean Copy</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/da">Dansk oversigt</a></p>
</footer>
<script>
(function(){try{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:p}),keepalive:true}).catch(function(){});}catch(e){}})();
</script>
</body>
</html>
"""

faqcards = "\n".join(
    f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in FAQS
)
html = (html.replace("__ARTICLE__", ld(ARTICLE_LD))
            .replace("__FAQ__", ld(FAQPAGE_LD))
            .replace("__FAQCARDS__", faqcards)
            .replace("__URL__", URL))

out = f"site/blog/{SLUG}.html"
with open(out, "w") as f:
    f.write(html)

# --- Verify JSON-LD blocks parse and @context is correct ---
raw = open(out).read()
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.DOTALL)
for b in blocks:
    parsed = json.loads(b)
    assert parsed["@context"] == "https://schema.org", parsed["@context"]
print(f"Wrote {out} ({len(raw)} bytes), {len(blocks)} JSON-LD blocks OK")

# --- Sitemap ---
sm_path = "site/sitemap.xml"
sm = open(sm_path).read()
if SLUG not in sm:
    entry = f"  <url><loc>{URL}</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>\n"
    sm = sm.replace("</urlset>", entry + "</urlset>")
    open(sm_path, "w").write(sm)
count = sm.count("<loc>")
print(f"Sitemap updated: {count} URLs")

# --- Cross-links from sibling posts (bidirectional) ---
SIBLINGS = [
    "site/blog/kopier-tabel-hjemmeside-til-notion.html",
]
new_link = '<a href="/blog/kopier-tabel-hjemmeside-til-excel" style="color:var(--color-accent);">Kopiér en tabel ind i Excel (DA)</a>'
for path in SIBLINGS:
    t = open(path).read()
    if SLUG in t:
        print(f"{path}: already links")
        continue
    m = re.search(r'Related:[\s\S]*?</p>', t)
    if m:
        seg = m.group(0)
        t = t.replace(seg, seg.replace("</p>", f" &middot; {new_link}</p>", 1), 1)
        open(path, "w").write(t)
        print(f"{path}: link appended to Related")
    else:
        print(f"{path}: WARNING no Related block found")

# --- Link from the Danish hub page ---
hub = "site/da.html"
t = open(hub).read()
if SLUG not in t:
    notion_card = '''          <h3><a href="/blog/kopier-tabel-hjemmeside-til-notion" style="color:inherit;text-decoration:none;">Kopiér en tabel fra en hjemmeside ind i Notion</a></h3>
          <p class="product-desc">Få enhver webtabel ind i Notion som rigtig database — to klik, ingen CSV-omveje, ingen cellerettelse i hånden.</p>
          <div class="product-details"><span class="product-meta">📖 4 min</span><span class="product-meta">✅ Gratis guide</span></div>
          <a href="/blog/kopier-tabel-hjemmeside-til-notion" class="btn-secondary" style="margin-top:12px;">Læs guide →</a>
        </div>
      </div>'''
    excel_card = '''          <h3><a href="/blog/kopier-tabel-hjemmeside-til-excel" style="color:inherit;text-decoration:none;">Kopiér en tabel fra en hjemmeside ind i Excel</a></h3>
          <p class="product-desc">Få enhver webtabel ind i Excel med hver værdi i sin egen celle — to klik, ingen OCR, ingen cellerettelse i hånden.</p>
          <div class="product-details"><span class="product-meta">📖 4 min</span><span class="product-meta">✅ Gratis guide</span></div>
          <a href="/blog/kopier-tabel-hjemmeside-til-excel" class="btn-secondary" style="margin-top:12px;">Læs guide →</a>
        </div>
      </div>'''
    # insert a new card after the Notion card's closing div
    idx = t.find(notion_card)
    if idx >= 0:
        end = idx + len(notion_card)
        insert_at = t.find("\n", end)
        card_html = '''
      <div class="product-card">
        <div class="product-badge product-badge-secondary">EXCEL · TABELLER</div>
        <div class="product-body">
''' + excel_card
        t = t[:end] + card_html + t[end:]
        open(hub, "w").write(t)
        print("da.html: Excel card added")
    else:
        print("da.html: WARNING Notion card not found")
else:
    print("da.html: already links")
