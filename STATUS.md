# STATUS — 26. august 2026

## Iteration 493 — "Relaterede guides" i alle 95 DA-blogindlæg

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Færdigt denne iteration
1. **Relaterede guides-boks indsat i alle 95 DA-blogindlæg** (mønstret fra
   iter 492s EN-udgave). Nyt idempotent script `tools/crosslink_blog_da.py`:
   token-overlap på titel + description vælger de 3 mest relaterede indlæg.
2. Verificering indbygget: alle filer har boksen, ingen døde links,
   /da-forsiden linker stadig til alle 95 (regressionstjek). Kør igen = 0 ændringer.
3. `full_site_check.py`: 287 URLs, 0 problemer efter indsættelsen.
4. Deployet og verificeret live: boksen synlig på spot-checkede DA-sider, HTTP 200.

### Ærlige tal pr. 26. aug
0 køb · 0 rigtige CTA-klik · ~36 besøgs-events siden 23. aug (inkl. egne tests).

### Stadig blokeret (uændret)
Lemon Squeezy API-nøgle · Chrome Web Store OAuth · npm/PyPI publish ·
Search Console · GitHub Marketplace-listing.

### Næste iteration
1. LS-nøglen landet → `node lemon-setup.js` → testkøb → første rigtige betaling.
2. Kandidat: hreflang-sweep — audit viser stadig 23 problemer (manglende
   x-default på flere par, 5 DA- og 5 EN-indlæg helt uden hreflang).
   `tools/hreflang_audit.py` lister dem; ret systematisk og verificér med audit.
3. Kandidat: opfølgning på trafikken — hvis der stadig er 0 CTA-klik efter
   cross-linkingen, så test en tydeligere CTA-placering midt i de mest besøgte
   indlæg frem for kun i bunden.
