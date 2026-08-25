#!/usr/bin/env python3
"""Iteration 230: dansk blogpost "Kopiér en tabel fra en hjemmeside ind i Notion".
Samme mønster som den engelske Notion-post (make_blog_da-variant af table-copy-serien):
Article + FAQPage JSON-LD, canonical, FAQ, sammenligningstabel, CTA til /clean-copy.
Tilføjer posten i sitemap.xml og gensidige krydslinks fra 3 søsterposter."""

import json, re

SLUG = "kopier-tabel-hjemmeside-til-notion"
URL = f"https://hermes-passiv.pages.dev/blog/{SLUG}"

ARTICLE_LD = {
    "@context": "https://schema.org", "@type": "Article",
    "headline": "Kopiér en tabel fra en hjemmeside ind i Notion (rækker og kolonner intakte)",
    "description": "Få en vilkårlig webtabel ind i Notion som rigtig database — hver række en side, hver kolonne en egenskab. Ingen CSV-omveje, ingen OCR, ingen manuel rettelse.",
    "url": URL, "datePublished": "2026-08-25", "dateModified": "2026-08-25",
    "author": {"@type": "Organization", "name": "Hermes Compliance"},
    "publisher": {"@type": "Organization", "name": "Hermes Compliance"},
}

FAQS = [
    ("Hvordan kopierer jeg en tabel fra en hjemmeside ind i Notion?",
     "Installér den gratis Clean Copy-udvidelse til Chrome eller Firefox, klik på ikonen mens tabellen er på skærmen, vælg Kopiér som Markdown — og sæt derefter ind i Notion med Ctrl+V (Cmd+V på Mac) i et database-view. Notion omdanner markdownen til rækker og kolonner, og første række bruges som egenskabsnavne."),
    ("Hvorfor ender indsatte tabeller i én kolonne i Notion?",
     "Hvis udklipsholderen kun indeholder almindelig tekst uden ensartede skilletegn, kan Notion ikke se hvor én celle slutter og den næste begynder — så værdierne stables i én kolonne. Når du kopierer selve tabel-elementet som markdown (som Clean Copy gør), bevares række- og kolonnegrænserne, som Notion skal bruge."),
    ("Kan jeg indsætte direkte i en eksisterende Notion-database?",
     "Ja. Åbn det view du vil fylde, marker den første celle hvor dataene skal lande, og sæt ind. Udfylder Notion eksisterende egenskaber fra venstre mod højre — så tjek at kolonnerækkefølgen matcher egenskabernes, før du indsætter."),
    ("Virker det på tabeller bag et login?",
     "Ja. Clean Copy kører i din egen browser-session, så enhver tabel du kan se, mens du er logget ind, kan kopieres — dashboards, adminpaneler, SaaS-rapporter. Serverbaserede scrapere fejler typisk her."),
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
FAQS[1] = (FAQS[1][0], FAQS[1][1].replace("where", "hvor"))

def ld(obj):
    return json.dumps(obj, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kopiér en tabel fra en hjemmeside ind i Notion (2026-guide)</title>
<meta name="description" content="Indsæt enhver webtabel i Notion som rigtig database — rækker bliver sider, kolonner bliver egenskaber. Ingen CSV-omveje, ingen OCR, ingen manuel rettelse.">
<meta property="og:type" content="article">
<meta property="og:title" content="Kopiér en tabel fra en hjemmeside ind i Notion">
<meta property="og:description" content="Indsæt enhver webtabel i Notion med alle celler på plads — ingen OCR, ingen manuel rettelse.">
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
    <div class="badge">NOTION &middot; TABELLER &middot; NO-CODE</div>
    <h1>Kopiér en tabel fra en hjemmeside<br>ind i Notion</h1>
    <p class="subtitle">Konkurrentpriser, leadlister, researchedata — at få en levende webtabel ind i Notion betyder normalt en skrøbelig CSV-eksport eller en times cellerettelse i hånden. Her er to-klik-måden der lander som en rigtig database.</p>
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
    <p>Notion vil have strukturerede rækker og kolonner. Det svære er at få dem hel ned fra en live webside.</p>
    <div class="problem-cards">
      <div class="card"><h3>📋 Markér og kopiér giver tekst</h3><p>Trækker du markøren hen over en tabel, fanger du ofte omgivende afsnit, reklamer og billedtekster. Indsat i Notion er strukturen væk — værdierne kollapser eller lander i de forkerte egenskaber.</p></div>
      <div class="card"><h3>📸 Skærmbilleder kræver OCR</h3><p>Et skærmbillede er bare pixels for Notion. Du ender med at køre OCR og rette cifrene den rammer forkert — værre end at taste igen.</p></div>
      <div class="card"><h3>⌨️ CSV-omveje er skrøbelige</h3><p>Nogle sider tilbyder CSV-download, men så skal du igennem Notions import-flow — og sammenflettede overskrifter, fodnoter og formatering forsvinder alligevel.</p></div>
    </div>
  </div>
</section>

<section class="products" id="how">
  <div class="container">
    <h2>Løsningen: to klik</h2>
    <p>Den gratis <a href="/clean-copy" style="color:var(--color-accent);">Clean Copy</a>-udvidelse til Chrome og Firefox omdanner præcis den tabel din markør står i, til ren markdown — som Notion parser til rækker og kolonner ved indsættelse.</p>

    <h3 style="margin-top:24px;">1. Installér</h3>
    <pre class="cmd"><code>Chrome Web Store eller Firefox Add-ons — søg på "Clean Copy",
installér, færdig.</code></pre>

    <h3 style="margin-top:24px;">2. Kopiér tabellen som markdown</h3>
    <pre class="cmd"><code>Åbn siden, klik et vilkårligt sted i tabellen,
klik på Clean Copy-ikonet, vælg "Copy as Markdown".</code></pre>

    <h3 style="margin-top:24px;">3. Indsæt i Notion</h3>
    <pre class="cmd"><code>Opret en ny database (eller åbn et eksisterende view),
markér den første målcelle, tryk Ctrl+V (Cmd+V på Mac).
Hver række bliver en side, hver kolonne en egenskab —
første række bliver egenskabsnavnene.

Indsætter du i en eksisterende database? Tjek at
kolonnerækkefølgen matcher egenskaberne først.</code></pre>

    <div class="problem-cards">
      <div class="card"><h3>✅ Rækker forbliver sider</h3><p>Clean Copy læser det rigtige HTML <code>&lt;table&gt;</code>-element, så hver <code>&lt;td&gt;</code> lander i sin egen egenskab i Notion automatisk.</p></div>
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
        <tr><td>Browser-table-scrapere</td><td>Ofte</td><td>Opsætning pr. side; strutter bag logins</td></tr>
        <tr>
          <td><a href="/clean-copy" style="color:var(--color-accent);">Clean Copy — Copy as Markdown</a></td>
          <td>Ja</td>
          <td>Kræver gratis browserudvidelse</td>
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

<div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="/blog/copy-table-website-to-notion" style="color:var(--color-accent);">Copy a Table From a Website Into Notion (EN)</a> &middot; <a href="/blog/copy-table-website-to-airtable" style="color:var(--color-accent);">Kopiér en tabel ind i Airtable (EN)</a> &middot; <a href="/blog/copy-table-website-to-google-sheets" style="color:var(--color-accent);">Kopiér en tabel ind i Google Sheets (EN)</a></p></div>
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
SIBLINGS = {
    "site/blog/copy-table-website-to-notion.html":
        '<a href="/blog/copy-table-website-to-notion" style="color:var(--color-accent);">Copy a Table From a Website Into Notion</a>',
    "site/blog/copy-table-website-to-airtable.html":
        '<a href="/blog/copy-table-website-to-airtable" style="color:var(--color-accent);">Copy a Table From a Website Into Airtable</a>',
    "site/blog/copy-table-website-to-google-sheets.html":
        '<a href="/blog/copy-table-website-to-google-sheets" style="color:var(--color-accent);">Copy a Table From a Website Into Google Sheets</a>',
}
new_link = '<a href="/blog/kopier-tabel-hjemmeside-til-notion" style="color:var(--color-accent);">Kopiér en tabel ind i Notion (DA)</a>'
for path, old_link in SIBLINGS.items():
    t = open(path).read()
    if SLUG in t:
        print(f"{path}: already links")
        continue
    if old_link in t:
        t = t.replace(old_link, old_link + " &middot; " + new_link, 1)
        open(path, "w").write(t)
        print(f"{path}: link added")
    else:
        m = re.search(r'(Related:[^<]*<p>.*?</p>|Related:.*?</p>)', t, re.DOTALL)
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
    anchor = 'href="/blog/nis2-guide-da"'
    if anchor in t:
        # add next to an existing blog list item if the structure allows; else append near first blog link
        print("da.html: manual check needed — no auto-insert")
