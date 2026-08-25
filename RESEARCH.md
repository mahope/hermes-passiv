# Iter 313: CTA + rapport-download + SEO-blogpost for compliance-site-check

**Metode:** 0 eksterne soegninger (data: /api/stats via curl). Alt arbejde er bygge-arbejde.

## Data der styrede valget (kilde: /api/health + /api/stats, 25/8)

- scans-taeller: **5** — ALLE egne roegtests. 0 reelle brugere af compliance-scanneren.
- Organisk trafik 7 dage: ~10 besigelser fordelt paa faa sider; stoerste organisk
  hit: /blog/nis2-for-agencies downloads (4/3 uniques) og cmp-comparison-2026.
- Konklusion: produktet mangler distribution, ikke funktioner. Derfor: CTA'er i
  eksisterende blogindhold + ny SEO-indgang + rapport-download som delings-/lead-mekanisme.

## Bygget

1. **"Scan your site"-CTA** indsat foerst i artikelindholdet paa 12 relevante
   blogs (EN+DA): gdpr-website-compliance-checklist, cookie-consent-gdpr-compliance,
   eaa-accessibility-checklist, free-nis2-assessment-tools, nis2-readiness-guide,
   gdpr-fines-2026 + DA-modstykker. Styling matcher eksisterende book-cta-kort.
   Hver CTA tracker `__selftest@cta-scan`-moensteret via /api/track? Nej — bruger
   eksisterende track.js side-tracking; CTA-link gaar til /compliance-site-check
   (EN) hhv. /da/compliance-site-check (DA).

2. **Download-rapport-knap** paa scannerens resultatvisning (EN+DA): klient-side
   genereret .md-fil med score, grade, alle tjek + fixes. Ingen server, ingen email,
   ingen konto — filen genereres lokalt i browseren (Blob + download-attribut).
   Formaal: goere resultatet delbart (attach i tickets/til kunder) → organisk spredning.

3. **Ny SEO-blogpost:** /blog/free-website-compliance-checker (EN) +
   /da/blog/gratis-compliance-tjek-hjemmeside (DA). Target: "free website compliance
   checker" / "compliance scan tool". Schema.org TechArticle, canonical, hreflang-par,
   cross-links til scanneren og GitHub Action.

4. **Sitemap:** begge nye poster tilfoejet til sitemap.xml.

## Verificering

- Alle aendrede sider hentet med curl efter deploy (200 + CTA-streng fundet).
- Rapport-download testet ved at inspicere genereret JS-logik (deterministisk,
  klient-side; ingen netvaerkafhængighed).
