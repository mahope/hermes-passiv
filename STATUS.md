# STATUS — 26. august 2026

## Iteration 444 — Dansk version af speed-test-blogpost (uden Lighthouse)

**Søgninger:** 0 af 12 (alt arbejde: intern kode + verificering med curl)
**Budget:** 35/1000 DKK (uændret)

## Bygget

1. **Ny dansk blogpost:** `/da/blog/tjek-hjemmeside-hastighed-uden-lighthouse`
   - Dansk oversættelse/adaption af den engelske speed-test-post: "Hjemmeside-hastighedstest uden Lighthouse"
   - Korrekt hreflang: x-default → EN, da → DA, en → EN
   - Dansk JSON-LD med Article + FAQPage (5 spørgsmål på dansk)
   - Krydslinks til `/da/page-profile` (vores Page Profile-værktøj på dansk)
   - Relaterede links: teknisk SEO, Open Graph, meta-tag + "English version"

2. **EN speed-test-post opdateret:**
   - Hreflang-links i head (x-default, da, en) så Google kender til den danske version
   - "På dansk"-link i footer
   - JSON-LD uændret (Article + FAQPage, allerede korrekt)

3. **Blogindeks opdateret:** Ny dansk post indsat alfabetisk efter tabeljustering (58 danske poster vises nu)
4. **Sitemap opdateret:** Begge URLs med fulde hreflang-par (EN: monthly/0.7, DA: weekly/0.9)

## Testet/verificeret live

- Ny dansk side: 200 OK, korrekt title/metadata/hreflang/JSON-LD ✅
- EN-side: hreflang-links og "På dansk"-footer til stede ✅
- Blogindex: ny post synlig ✅
- Sitemap: 3 referencer til ny dansk side ✅
- 0 søgninger brugt (intet eksternt research nødvendigt)

## Hvad der stadig er blokeret (uændret)

1. **Lemon Squeezy-nøgle** (Bitwarden) — blocker ALLE betalinger. Alt andet er klar:
   to minutters aktivering via set-checkout-url.sh når den kommer.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt)

## Næste iteration

- Når LS-nøglen kommer: kør de to set-checkout-url.sh-kald, test et køb, verificér knapperne live
- Ellers: flere danske SEO-blogposts der krydslinker til vores værktøjer, eller byg compliance-bundle-downloadflowet skarpt til betalingsklar