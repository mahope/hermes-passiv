# BUILD — hvad der er bygget, hvad der mangler

## Bygget (hele historien)

**EAA Compliance Scanner Desktop — CI multi-platform builds (v1.3.3)**

- **CI workflow** (build-desktop.yml) bygger nu automatisk på tag push:
  - macOS: ARM64 + x64 (DMG + ZIP)
  - Linux: AppImage + .deb
  - Windows: NSIS installer + portable .exe
  - Release job: opretter release + uploader alle assets
- **v1.3.1 release** — 7 assets live (macOS 4, Linux 2, Windows 1)
- **v1.3.2** — tilføjer Windows portable .exe (artifact naming fix)
- **v1.3.3** — version bump (1.3.0→1.3.3 i main.js), CI-trigger fix (tag-only flow), 8 assets live
- **SEO blog post** — ny guide: "EAA Compliance Scanner Desktop" (site/blog/eaa-compliance-scanner-desktop.html)
- **Downloads page** — alle 8 v1.3.3-links, Pro-badge, Pro-sektion, opdateret source zip

**EAA Compliance Scanner Desktop — v1.2.0 macOS ARM64 build + distribution**
[...]

**EAA Compliance Scanner Desktop — v1.3.0 Pro license + batch scan**
[...]

**NIS2-økosystemet:** [uændret]

**Compliance site check:** [uændret]

**Clean Copy-økosystemet:** [uændret]

**Checkout-infrastruktur:** [uændret]

**Iter 313: Compliance-site-check CTA + rapport-download + SEO-blogpost**

- **CTA i 21 compliance-blogs (EN+DA):** "Scan your site" aside-kort indsat i
  toppen af artikler om GDPR, EAA, NIS2, cookie-consent, accessibilitet m.fl.
  Linker til scanneren. Styling matcher eksisterende book-cta.
- **Rapport-download-knap (.md):** Klient-side Blob-download af scan-resultatet
  som Markdown-fil med score, grade, alle tjek og konkrete fixes. Ingen server,
  ingen email, ingen konto. Paa EN + DA scanner-sider.
- **Ny blogpost:** /blog/free-website-compliance-checker (EN) +
  /da/blog/gratis-compliance-tjek-hjemmeside (DA). SEO-optimeret med schema,
  canonical, hreflang. I sitemap.
- **Sitemap opdateret** med begge nye poster.
- **JS-validert:** node --check paa begge scanner-sider.

## Mangler (blokeret)

- Betalingsintegration (Lemon Squeezy-nøgle i Bitwarden)
- Email levering til leads (kræver Mads' accept)
- KDP-e-bog (kræver Mads' KDP-konto)
- CWS-upload (kræver OAuth-credentials i Bitwarden)
- Obsidian community submit (kræver Mads' login)
- Alle andre kanaler (kræver konti i Mads' navn)

## Plan for naeste byg

1. Overvaag om CTA i blogs tracker trafik — tjek /api/stats
2. Hvis scanneren faar >0 reelle scans: overvej email-indgang paa resultatet
   (lead capture) — kraever Mads' accept og email-infrastruktur
3. Alternativt: nyt produkt der kan tage imod penge via GitHub Sponsors eller
   lignende zero-account-kanal

**Iter 314: Maale- og synlighedshuller lukket for compliance-site-check**

- **scan/report-dl event-tracking** i scan() og downloadReport() paa EN + DA
  scanner-sider. Samme trackEvent()-system som cookie-check. Data synlig i
  /api/stats?token=hp-stats-v1&days=3.
- **Homepage-kort** i index.html free-tools-sektionen: "Compliance Checker" direkte
  link + CTA-tracker-regex opdateret til compliance-site-check.
- **llms.txt** tilfoejet compliance-site-check (EN + DA).
- **API-dokumentation** site/api-compliance-scan-readme.md: dokumenterer
  /api/compliance-scan endpoint med eksempler og felttabel.