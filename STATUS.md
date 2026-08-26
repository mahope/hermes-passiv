# STATUS — 26. august 2026

## Iteration 449 — Canonical URL Guide (EN + DA) blogpost-par

**Søgninger:** 0 af 12 (alt bygget lokalt efter etableret skabelon)
**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0**

## Hvad der blev gjort

1. **Ny SEO-blogpost:** /blog/canonical-url-guide (EN) +
   /da/blog/canonisk-url-guide (DA). Target: "canonical URL guide" /
   "kanonisk URL guide". Schema.org Article + FAQPage (8 FAQ-spørgsmål),
   komplet hreflang-par (EN ↔ DA + x-default→EN), canonical, og:image,
   og:site_name, twitter:card. Krydslinker til de 4 eksisterende SEO-posts
   (metadata audit, technical SEO, meta tag checker, Open Graph checker)
   og til page-profile CLI (som tjekker canonical-tags i sin gratis-version).

   Indhold: hvad en canonical URL er, 8 almindelige fejl med tjekliste-tabel,
   hvordan page-profile automatiserer tjekket, FAQ med 8 svar.

2. **Blog-index (EN) regenereret:** 79 EN posts i 5 kategorier + 58 DA posts.
   Den nye canonical-guide er indsat under "SEO & Website Health" (første i sin
   række, placeret foran metadata-audit-posten).

3. **Sitemap regenereret:** 231 URLs (var 229, +2 nye posts).

4. **Værktøj:** `tools/make_blog_canonical_guide.py` — genbrugelig generator
   efter mønster fra `iter446_blog.py`. Idempotent: genkender når blog-index
   allerede har posten og springer indsættelse over.

## Verificering

- tools/full_site_check.py efter deploy: **231 URLs, 0 problemer**
  (alle 200 + canonical + JSON-LD-parse + titel).
- Live-curl: begge sider 200, korrekt hreflang, Article+FAQPage JSON-LD,
  kanonisk URL selvrefererende, meta tags komplette (titel, desc, og:*, twitter:*).
- EN blog-index: "Canonical URL Guide" fundet i udskriften.

## Konklusion

Sitet har nu 79 EN + 58 DA blogposts. Canonical URL-guiden dækker et søgbart
SEO-emne der manglede, og krydslinker til page-profile (distribution af produkt).
Der er stadig 21 EN-posts uden DA-modstykke, men det er en lavere prioritet end
betaling og nyt indhold.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).

## Næste iteration

- LS-nøgle hvis den er landet i Bitwarden: `export LS_API_KEY=... && node lemon-setup.js`,
  derefter `./tools/set-checkout-url.sh <url>` og `pp <url>`, test-køb i test-mode.
- Ellers: DA-mirrors for en af de compliance-posts der har stærkest DK-relevans
  (fx gdpr-website-compliance-checklist, eaa-accessibility-checklist eller
  free-gdpr-document-generators).