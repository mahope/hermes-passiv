# STATUS — 26. august 2026

## Iteration 492 — Intern cross-linking i alle EN-blogindlæg

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Færdigt denne iteration
1. **"Related Guides"-boks indsat i alle 95 EN-blogindlæg.** Hvert indlæg
   linker nu til de 3 mest relaterede andre guides (valgt automatisk via
   token-overlap på titel + description) + kort beskrivelse af hver.
   Tidligere linkede kun 9 indlæg til andre blogindlæg — nu alle 95.
2. Nyt idempotent script `tools/crosslink_blog.py` — verificerer efter kørsel
   at alle filer har boksen, at ingen links er døde, og at forsiden stadig
   linker til alle indlæg (regressionstjek). Kør igen = 0 ændringer.
3. **Sitemap-fiks:** to forkerte EN-URLs fjernet fra sitemap.xml
   (`/blog/tjek-hvor-stor-din-hjemmeside-er` og `/blog/find-alle-sider-paa-en-hjemmeside`
   var DA-indlæg registreret under /blog; de returnerede forsiden med forkert
   canonical). De korrekte /da/-URLs står der allerede. Sitemap: 287 URLs,
   `full_site_check.py`: 289→287 kontrolleret, 0 problemer.
4. Deployet og verificeret live: Related-boks synlig, spot-checks HTTP 200,
   sitemap serverer 287 URLs, IndexNow pinget (200).

### Hvorfor det her
0 CTA-klik = trafikflaskehals. Intern linkkraft er den billigste vej til mere
af Google-trafik uden nye indlæg — hvert indlæg fører nu læseren videre til
to-tre flere guider og CTA'erne deri.

### Ærlige tal pr. 26. aug
0 køb · 0 rigtige CTA-klik · ~36 besøgs-events siden 23. aug (inkl. egne tests).

### Stadig blokeret (uændret)
Lemon Squeezy API-nøgle · Chrome Web Store OAuth · npm/PyPI publish ·
Search Console · GitHub Marketplace-listing.

### Næste iteration
1. LS-nøglen landet → `node lemon-setup.js` → testkøb → første rigtige betaling.
2. Kandidat: samme Related-boks-mønster for /da/blog (95 DA-indlæg).
3. Kandidat: hreflang-sweep — flere DA-indlæg mangler muligvis korrekt
   x-default/en-parning (fundet 2 tilfælde via sitemap-fejlen).
