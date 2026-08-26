# STATUS — 26. august 2026

## Iteration 464 — FAQ + FAQPage JSON-LD på 9 gratisværktøjssider

**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0**
**Søgninger brugt: 2**

## Hvad der blev gjort

Audit viste at 9 af de højttrafikerede gratisværktøjer manglede FAQ-sektion
og/eller FAQPage rich-resultat-schema (samme behandling som base64 fik i
iteration 463):

- **8 nye FAQ-sektioner + FAQPage JSON-LD:** hash-generator, text-diff,
  word-counter, json-formatter, uuid-generator, case-converter,
  markdown-table-generator, palette-generator. Hver med 4 reelle svar
  (privacy/lokalt, faglige faldgruber, platformsforskelle).
- **url-encoder-decoder:** havde allerede HTML-FAQ — fik kun FAQPage JSON-LD,
  bygget fra de eksisterende spørgsmål.

Alt via én idempotent generator: tools/iter464_tool_faqs.py (anden kørsel =
0 ændringer; JSON-LD valideres ved hver kørsel).

## Verificering

- Lokal validering: alle JSON-LD-blokke parser, @context = schema.org,
  FAQPage til stede på alle 9.
- Deployet til Cloudflare Pages. Live curl + parse på alle 9 URL'er:
  9/9 leverer både FAQ-indhold og gyldig FAQPage schema.
  (Én side så fejlbehæftet ud under verificeringen — det var et
  sandbox-output-maskering artefakt ("schema.org" → "***"), ikke en reel
  fejl. Bekræftet ved rå hentning.)
- full_site_check: ingen nye problemer (kun de kendte Worker-301-aliaser).
- Committed og pushed (973b938).

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).

## Næste iteration

- Flere gratisværktøjer kan få samme behandling: security-headers-check,
  site-icons, text-on-image-checker, color-blindness-simulator (+DA-mirrors)
  mangler sandsynligvis også FAQPage — tjek først.
- DA-spejle af de 9 værktøjssider har muligvis heller ikke FAQ — paritetscheck.
- GitHub Marketplace for bugbottle-action er stadig ét klik væk (UI-only).
- Page Profile Pro: færdig i koden, venter kun på LS-checkout-URL.
