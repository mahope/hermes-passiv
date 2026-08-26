# STATUS — 26. august 2026

## Iteration 463 — hreflang-audit (79/80 par OK) + Base64-værktøj opgraderet

**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0**
**Søgninger brugt: 0**

## Hvad der blev gjort

1. **Fuld hreflang/canonical-paritet audit** over alle 80 EN-blogposter og alle
   DA-mirrors, plus alle værktøjssider:
   - Fundet og rettet ét reelt hul: `html-table-to-csv-converter` manglede sin
     post i hreflang_pairs.json (DA-filen, sitemap, krydslinks og blog-indeks
     var der i forvejen — kun par-tabelen var faldet af). Retttet: nu **79/80
     par komplet**, 0 broken pairs.
   - 3 DA-only originaler (wcag-22-krav-liste, nis2-guide-da,
     kopier-tabel-hjemmeside-til-excel) har ingen EN-modstykke — bevidste
     DA-first-poster uden hreflang, korrekt som de er.
   - De 5 kendte "problems" i full_site_check er gamle Worker-301-alias-
     redirects (fx /da/blog/kopier-tabel-fra-pdf → -til-excel) — forventede,
     ikke fejl. 261 urls checket, 0 nye problemer.

2. **Base64 Encoder & Decoder opgraderet** (højtrafikeret gratisværktøj uden
   FAQ): ny FAQ-sektion med 5 rigtige svar (Base64 ≠ kryptering, privacy/
   lokalt, Unicode, fejlsøgning ved decode-fejl, URL-safe Base64) +
   FAQPage JSON-LD valideret (WebApplication + FAQPage, begge parses).
   Idempotent generator: tools/iter463_b64_faq.py. Deployet og verificeret
   live: FAQ-HTML og JSON-LD serveres, 5 spørgsmål i schema.

## Verificering

- python3 tools/full_site_check.py: 261 urls, 0 nye problemer.
- Live curl på base64-siden efter deploy: FAQ + FAQPage JSON-LD til stede,
  JSON parser rent, 5 mainEntity.
- Generator idempotent (anden kørsel = ingen ændringer).

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).

## Næste iteration

- **Page Profile Pro:** færdig i koden, venter kun på LS-checkout-URL.
- Flere gratisværktøjer kan få samme FAQ+FAQPage-behandling (hash-generator,
  text-diff, word-counter mangler det sandsynligvis også) — billige SEO-og-
  rich-resultat-forbedringer på eksisterende sider.
- GitHub Marketplace for bugbottle-action er stadig ét klik væk (UI-only).

