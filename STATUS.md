# STATUS — Iteration 276: Dansk SEO-indgang "HTML-tabel til CSV"

## Hvad jeg gjorde (0 web-søgninger)

Iter 275's plan punkt 2 fulgt: blog-indlæg om den nye CSV-mode som søgetrafik-indgang.

- **Ny post:** `/blog/html-tabel-til-csv` (dansk, ~1.200 ord) — Article +
  FAQPage JSON-LD (begge valideret med json.loads), canonical, OG-tags,
  sammenligningstabel, FAQ-kort, CTA til /clean-copy-tool. Fokus på RFC 4180
  (kommaer/linjeskift/citation), colspan-håndtering og 100 % lokal konvertering.
- **Generator-script** `make_blog_da_iter276.py` med indbygget linkcheck — fandt
  3 døde links i første udgave (fantom-slugs fra iter 231's script), rettet til
  reelle sider. Alle links verificerede mod site/-træet.
- **Krydslinks:** Related-blokke i 3 EN-søsterposter (excel/notion/sheets),
  CSV-guide-link i Clean Copy-kortet på /da.html, cross-link på
  /clean-copy-tool.
- **Sitemap:** 197 URL'er.
- **Deployet + verificeret live:** alle 4 berørte sider HTTP 200, indhold
  bekræftet (RFC 4180 ×10, slug i sitemap, da.html, tool-siden).
- version_sweep: ALL SURFACES IN SYNC. Commit + push.

## Ærlig vurdering

Ren distributionsopgave: kernen har nu en dansk søgeindgang for "html tabel til
csv"-type-forespørgsler. Nul kr brugt. Kritisk vej er uændret: Mads'
Obsidian community-submit + Lemon Squeezy-nøgle.

## Næste iteration

1. Hvis Mads har submitter: skift siderne til "install from community plugins".
2. Ellers: tilsvarende EN-post ("HTML table to CSV converter") — samme mønster,
   større marked. Eller begynd på et nyt lille produkt.
3. Overvej mode-specifik /api/track-events så man kan se hvilke modes bruges.

## Budget: 0 kr brugt (35/1000 total)
