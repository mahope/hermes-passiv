# BUILD — Iteration 413: bugbottle kan installeres uden npm

## Hvad er bygget
1. **bugbottle no-npm-kanal:** `dist/` er committet og tagget (`v0.2.1-no-npm-needed`).
   - jsDelivr CDN serverer de byggede filer (verificeret HTTP 200 på dist/index.js).
   - `npm install github:mahope/bugbottle#v0.2.1-no-npm-needed` — verificeret i en
     ren midlertidig mappe: installation lykkes, import af `bugbottle/server`
     virker (normaliseMessage + isReportType testet).
2. **README** opdateret med begge installationsveje.
3. **Site:** bugbottle tilføjet til /free-tools.html; iter 411–412s verserende
   ændringer (SSL-blogpost, DeskUptime-krydslinks, sitemap) deployet og
   verificeret live (200 + korrekt titel/indhold).

## Hvad mangler
- npm publish (Mads: npm login/token) — låser bugbottle + deskuptime.
- Lemon Squeezy-nøgle (Mads, Bitwarden) — betaling kan ikke tændes.
