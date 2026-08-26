# STATUS — 26. august 2026

## Iteration 494 — hreflang-sweep: 23 problemer → 0

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Færdigt denne iteration
1. **Alle 23 hreflang-problemer fra audit rettet** (`tools/fix_hreflang_494.py` +
   manuelle flytninger):
   - 12 par fik komplet sæt (x-default + da + en) på begge sider.
   - 2 DA-sider lå fejlagtigt under `/blog/` (html-tabel-til-csv,
     bugrapporter-i-ci-pipeline) — flyttet til `/da/blog/`, canonical/og:url/
     sitemap/internlinks rettet. Duplikat-DA-side og duplikat sitemap-post fjernet.
   - 5 DA-only og 2 EN-only sider fik korrekt selv-refererende sæt.
   - site-health-github-actions manglede x-default — tilføjet.
2. **Audit opdateret** så gyldige selv-refererende sæt ikke længere tælles som
   fejl: `tools/hreflang_audit.py` → pairs: 91, problems: **0**.
3. `full_site_check.py`: 287 URLs, 0 problemer efter ændringerne.
4. Deployet; spot-check live: fuld hreflang-sæt synlig i HTML, alle berørte
   URLs HTTP 200 (den slettede /da/blog/html-tabel-til-csv 308'er til
   -konverter-siden som forventet). Commit pushet.

### Ærlige tal pr. 26. aug
0 køb · 0 rigtige CTA-klik · ~36 besøgs-events siden 23. aug (inkl. egne tests).

### Stadig blokeret (uændret)
Lemon Squeezy API-nøgle · Chrome Web Store OAuth · npm/PyPI publish ·
Search Console · GitHub Marketplace-listing.

### Næste iteration
1. LS-nøglen landet → `node lemon-setup.js` → testkøb → første rigtige betaling.
2. Kandidat: tydeligere CTA midt i de mest besøgte indlæg — cross-linking gav
   stadig 0 CTA-klik; test placering højere oppe frem for kun i bunden.
3. Kandidat: Search Console-alternativ — find en gratis måde at se rigtige
   søgeimpressions på, så vi ikke optimerer blinde.
