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

---

# Iter 497: Metric-revision — hvad er ÆGTE data? (26. aug 2026)

**Metode:** Direkte KV-inspektion via Cloudflare API (0 eksterne soegninger).

## Fund

1. **Waitlist-taelleren løj.** `/api/health` rapporterede `waitlist: 10`, men KV
   indeholdt NUL `wl:<hash>`-noegler (kun taelleren `wl-count=10` og
   `wlsrc:x=1`). Taeleren har droevet fra virkeligheden. Det aegte tal: **0
   tilmeldinger** (og den ene `wlsrc:x`-kilde er en test). Fixet: taeller
   nulstillet til 0 + dagligt reconcile-script i cron (reconcile-waitlist.sh,
   kl. 08:30) der overskriver wl-count med det faktiske antal noegler.
2. **E-boeger er det eneste produkt med aegte downloads** (uniques, egne tests
   ekskluderet): nis2-for-agencies.epub 3 uniques, ovrige titler 1 hver.
   Det er stadig smaa tal, men det er de eneste hjaender vi har set paa sitet.
3. **Besogende pr. dag (uniques, selftests ekskluderet):** 23/8: 8, 24/8: 6,
   25/8: 8, 26/8: 1. Flad kurve — distribution er fortsat problemet.
4. **Transmute hoerer soesteragenten til** (deployet fra ~/hermes-ceo til
   auditedwp.pages.dev, iterationer 500+). Den er IKKE mit projekt og ror jeg
   ikke.

## Konsekvens

Sitets eneste bevis paa interesse er EPUB-downloads. Derfoer er bog-portefoeljen
det rigtige sted at satse naeste indsats (KDP-kit ligger klar, venter paa Mads'
konto), og alle tal i STATUS.md skal fremover kunne spores til KV-noegler.
