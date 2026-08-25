#!/usr/bin/env python3
"""Iteration 276: dansk blogpost "HTML-tabel til CSV" — SEO-indgang der
udnytter den nye CSV-mode i kernen (iter 275). Article + FAQPage JSON-LD,
canonical, FAQ, sammenligningstabel, CTA til /clean-copy-tool.
Tilfoejer posten i sitemap.xml og krydslinks fra soesterposter + da-hub."""

import json, re

SLUG = "html-tabel-til-csv"
URL = f"https://hermes-passiv.pages.dev/blog/{SLUG}"

ARTICLE_LD = {
    "@context": "https://schema.org", "@type": "Article",
    "headline": "HTML-tabel til CSV: konvertér enhver webtabel online (gratis)",
    "description": "Indsæt HTML fra en webtabel og få ren RFC 4180-kompatibel CSV — klar til Excel og Google Sheets. Kører helt i din browser.",
    "url": URL, "datePublished": "2026-08-25", "dateModified": "2026-08-25",
    "author": {"@type": "Organization", "name": "Hermes Compliance"},
    "publisher": {"@type": "Organization", "name": "Hermes Compliance"},
}

FAQS = [
    ("Hvordan konverterer jeg en HTML-tabel til CSV?",
     "Åbn det gratis webværktøj på /clean-copy-tool, kopier tabel-HTML'en fra siden (højreklik → Undersøg → kopiér outerHTML, eller brug Ctrl+U og find <table>-blokken), indsæt den i feltet og vælg CSV som output-format. Du får straks RFC 4180-korrekt CSV du kan gemme som .csv-fil."),
    ("Hvad er RFC 4180?",
     "RFC 4180 er standarden for CSV-filer: rækker adskilt af linjeskift, celler adskilt af kommaer, og anførselstegn rundt om celler der selv indeholder kommaer, anførselstegn eller linjeskift. Clean Copy følger standarden, så filen åbner korrekt i Excel, Google Sheets, Numbers og alle programmeringsværktøjer."),
    ("Bevarer konverteringen celler med kommaer eller linjeskift?",
     "Ja. Celler der indeholder kommaer, anførselstegn eller linjeskift bliver automatisk pakket ind i anførselstegn, og indre anførselstegn escapes — præcis som standarden kræver. Ingen værdier bliver klippet over."),
    ("Hvad med colspan og indlejrede tabeller?",
     "Clean Copy håndterer colspan/rowspan ved at gentage værdien i de dækkede kolonner, flader indlejret markup ud til tekst og dropper prosa uden for tabellen når der findes en tabel — så du kun får rækker og kolonner."),
    ("Bliver dataene sendt til en server?",
     "Nej. Konverteringen kører 100 % i din browser med JavaScript. Intet af det du indsætter forlader din maskine."),
    ("Kan jeg også få Markdown eller WikiLinks i stedet?",
     "Ja. Samme værktøj kan levere Markdown-tabeller (til Notion, Obsidian, GitHub) og WikiLinks-format — skift bare output-mode."),
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
<title>HTML-tabel til CSV — gratis online konvertering (2026)</title>
<meta name="description" content="Konvertér en HTML-tabel til ren CSV direkte i browseren: RFC 4180-korrekt, klar til Excel og Google Sheets, intet sendes til en server.">
<meta property="og:type" content="article">
<meta property="og:title" content="HTML-tabel til CSV — gratis online konvertering">
<meta property="og:description" content="Indsæt HTML, få RFC 4180-korrekt CSV klar til Excel og Google Sheets. Kører 100 % i din browser.">
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
    <div class="badge">CSV &middot; TABELLER &middot; GRATIS VÆRKTØJ</div>
    <h1>HTML-tabel til CSV<br>på to klik</h1>
    <p class="subtitle">Skal tabellen fra en hjemmeside ind i Excel eller Google Sheets? Indsæt HTML'en, og få RFC 4180-korrekt CSV — hver celle på sin plads, intet sendt til nogen server.</p>
    <div class="hero-cta">
      <a href="/clean-copy-tool" class="btn-primary">Åbn konverteren gratis &rarr;</a>
      <a href="#how" class="btn-secondary">Sådan virker det</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; Læsetid: 4 minutter</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>Hvorfor HTML-til-CSV er svært i hånden</h2>
    <p>En HTML-tabel er ikke bare tekst — og CSV-tolererer heller ikke bare tekst. Tre ting går næsten altid galt, når man konverterer manuelt:</p>
    <div class="problem-cards">
      <div class="card"><h3>␣ Kommaer inde i celler</h3><p>Står der &bdquo;1.234,56&ldquo; eller &bdquo;København, Danmark&ldquo; i en celle, ødelægger kommaet kolonnestrukturen — medmindre cellen pakkes korrekt ind i anførselstegn.</p></div>
      <div class="card"><h3>↵ Linjeskift i celler</h3><p>Celler med linjeskift knækker rækkerne, hvis de ikke escapes efter RFC 4180. Resultatet ser fint ud i teksteditoren og er ødelagt i regnearket.</p></div>
      <div class="card"><h3>🧩 colspan og indlejret markup</h3><p>Overskrifter der spænder over flere kolonner, fed tekst, links og indlejrede elementer giver ekstra kolonner eller tomme felter, hvis de behandles som almindelig tekst.</p></div>
    </div>
  </div>
</section>

<section class="products" id="how">
  <div class="container">
    <h2>Sådan gør du</h2>
    <p>Det gratis <a href="/clean-copy-tool" style="color:var(--color-accent);">Clean Copy webværktøj</a> konverterer HTML-tabeller til korrekt CSV direkte i din browser.</p>

    <h3 style="margin-top:24px;">1. Find tabellens HTML</h3>
    <pre class="cmd"><code>Højreklik på tabellen → Undersøg
→ højreklik på &lt;table&gt;-elementet → Copy → Copy outerHTML.
(Alternativt: Ctrl+U og find &lt;table&gt;-blokken.)</code></pre>

    <h3 style="margin-top:24px;">2. Indsæt og vælg CSV</h3>
    <pre class="cmd"><code>Gå til /clean-copy-tool, indsæt HTML'en,
og klik "CSV" som output-format.</code></pre>

    <h3 style="margin-top:24px;">3. Gem som .csv</h3>
    <pre class="cmd"><code>Kopiér resultatet, sæt det ind i en teksteditor,
og gem som fx konkurrentpriser.csv.
Eller indsæt direkte i Excel / Google Sheets —
Data → Fra tekst/CSV læser formatet automatisk.</code></pre>

    <div class="problem-cards">
      <div class="card"><h3>✅ RFC 4180-korrekt</h3><p>Celler med kommaer, anførselstegn eller linjeskift citeres og escapes automatisk — filen åbner pænt i ethvert regneark.</p></div>
      <div class="card"><h3>🧹 Kun tabellen</h3><p>Prosa, menuer og reklamer uden for tabellen dropper vi, når der findes en tabel i det du indsætter.</p></div>
      <div class="card"><h3>🔐 100 % lokal</h3><p>Konverteringen kører i din browser. Dine data forlader aldrig din maskine.</p></div>
    </div>
  </div>
</section>

<section class="products" id="options">
  <div class="container">
    <h2>Dine muligheder sammenlignet</h2>
    <table class="compare">
      <thead>
        <tr><th>Metode</th><th>RFC 4180-sikker?</th><th>Hage</th></tr>
      </thead>
      <tbody>
        <tr><td>Manuel copy-paste</td><td>Nej</td><td>Kommaer og linjeskift ødelægger kolonnerne</td></tr>
        <tr><td>Sidens egen eksport-knap</td><td>Nogle gange</td><td>Findes sjældent; ofte bag betalt plan</td></tr>
        <tr><td>Python-script (BeautifulSoup)</td><td>Ja</td><td>Kræver kodning og miljø-setup</td></tr>
        <tr>
          <td><a href="/clean-copy-tool" style="color:var(--color-accent);">Clean Copy webværktøj — CSV-mode</a></td>
          <td>Ja</td>
          <td>Ingen — gratis, ingen installation, kører lokalt</td>
        </tr>
      </tbody>
    </table>
    <p>Bruger du det ofte? Der er også en <a href="/clean-copy" style="color:var(--color-accent);">browserudvidelse</a>, et CLI-værktøj og en Obsidian-plugin med samme CSV-motor.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
__FAQCARDS__
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/clean-copy-tool" class="btn-primary">Prøv konverteren nu — gratis &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="/blog/copy-table-from-website-to-excel" style="color:var(--color-accent);">Webtabel → Excel (EN)</a> &middot; <a href="/blog/copy-table-website-to-notion" style="color:var(--color-accent);">Webtabel → Notion (EN)</a> &middot; <a href="/blog/copy-table-website-to-google-sheets" style="color:var(--color-accent);">Table → Google Sheets (EN)</a> &middot; <a href="/blog/html-to-markdown-converter" style="color:var(--color-accent);">HTML → Markdown converter (EN)</a></p></div>
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
print(f"Wrote {out}")

# --- JSON-LD sanity check ---
content = open(out).read()
for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL):
    parsed = json.loads(block)
    assert parsed["@context"] == "https://schema.org", parsed["@context"]
print("JSON-LD valid")

# --- Sitemap ---
sm_path = "site/sitemap.xml"
sm = open(sm_path).read()
if SLUG not in sm:
    entry = f"  <url><loc>{URL}</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>\n"
    sm = sm.replace("</urlset>", entry + "</urlset>")
    open(sm_path, "w").write(sm)
count = sm.count("<loc>")
print(f"Sitemap updated: {count} URLs")

# --- Cross-links from sibling posts ---
SIBLINGS = [
    "site/blog/copy-table-from-website-to-excel.html",
    "site/blog/copy-table-website-to-notion.html",
    "site/blog/copy-table-website-to-google-sheets.html",
]
new_link = '<a href="/blog/html-tabel-til-csv" style="color:var(--color-accent);">HTML-tabel til CSV (DA)</a>'
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

# --- Link from the Danish hub page (Clean Copy tool card) ---
hub = "site/da.html"
t = open(hub).read()
if SLUG not in t:
    anchor = '<a href="/da/blog/kopier-tabel-til-excel" class="btn-secondary" style="margin-top:12px;">Guide: tabeller til Excel →</a>'
    if anchor in t:
        t = t.replace(anchor,
            anchor + f'\n          <a href="/blog/{SLUG}" class="btn-secondary" style="margin-top:12px;">Guide: HTML-tabel til CSV →</a>', 1)
        open(hub, "w").write(t)
        print("da.html: CSV guide link added to Clean Copy card")
    else:
        print("da.html: WARNING anchor not found")
else:
    print("da.html: already links")

# --- Cross-link from clean-copy-tool page ---
tool = "site/clean-copy-tool.html"
t = open(tool).read()
link_line = '<a href="/blog/html-tabel-til-csv">HTML-tabel til CSV — guide</a>'
if SLUG not in t and 'href="/blog/' in t:
    m = re.search(r'href="/blog/[a-z0-9\-]+"[^>]*>[^<]+</a>', t)
    if m:
        seg = m.group(0)
        t = t.replace(seg, f'{seg} &middot; <a href="/blog/{SLUG}" style="color:var(--color-accent);">HTML-tabel til CSV (guide)</a>', 1)
        open(tool, "w").write(t)
        print(f"{tool}: cross-link added")
    else:
        print(f"{tool}: WARNING no blog link found")
else:
    print(f"{tool}: slug present or no links")
