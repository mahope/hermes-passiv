# RESEARCH — Iteration 311: v1.3.3 desktop release + SEO blog post

**Dato:** 2026-08-25
**Metode:** 2 eksterne søgninger (github release view, curl verify). 0 af 12 brugt.

## Fakta

### Desktop CI workflow

1. **Tag dedup problem:** GitHub Actions deduplicerer SHA's. Når en tag push har samme SHA som main push, køres workflow'et kun én gang (for main). Løsning: fjern `branches: [main]` fra tag-triggeren, så CI kun kører på tag pushes.
2. **v1.3.3 release:** Alle 8 assets bygget og uploadet (macOS DMG+ZIP x2, Linux AppImage+.deb, Windows installer+portable). Download-link virker: https://github.com/mahope/hermes-passiv/releases/tag/eaa-scanner-desktop-v1.3.3
3. **Versions mismatch fundet i iter 310:** package.json sagde v1.3.1, men main.js og index.html havde hårdkodet v1.3.0. Dette rettes i v1.3.3.

### SEO

- Ny blog post "EAA Compliance Scanner Desktop — Free, Offline WCAG 2.1 AA Scanner" live på https://hermes-passiv.pages.dev/blog/eaa-compliance-scanner-desktop
- Schema.org TechArticle + alternat hreflang + canonical + OG tags på plads
- Siden beskriver alle 3 platformsbygg, Free vs Pro feature-table, og 22 WCAG 2.1 AA regler

## Konklusion

Desktop app'en har nu en korrekt version gennem hele stack'en (package.json, main.js, index.html), et stabilt CI-workflow, og en SEO-blogpost. Næste distributionsskridt: npm/pip publish eller sitemap-opdatering.