# STATUS — 26. august 2026

## Iteration 465 — FAQ + FAQPage JSON-LD på de sidste 7 værktøjssider

**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0**
**Søgninger brugt: 0**

## Hvad der blev gjort

STATUS fra iter 464 pegede på 4 sider der "sandsynligvis manglede FAQPage".
Fuld audit viste at det faktisk var **7 EN-sider uden FAQPage** (og 4 DA-mirrors
uden FAQ overhovedet):

- **7 nye FAQ-sektioner + FAQPage JSON-LD (EN):** color-blindness-simulator,
  security-headers-check, site-icons, text-on-image-checker, url-to-markdown,
  contrast-checker. (cookie-check havde allerede FAQPage — springet over.)
- **1 DA-mirror:** palette-generator-da fik dansk FAQ + FAQPage (dansk tekst).
  De øvrige DA-mirrors (color-blindness/text-on-image/contrast -da) har stadig
  ingen FAQ — næste kandidat.

Alt via én idempotent generator: tools/iter465_tool_faqs.py (anden kørsel =
0 ændringer; al JSON-LD valideres ved hver kørsel).

## Verificering

- Lokalt: alle JSON-LD-blokke parser, @context = schema.org, FAQPage til stede.
- Deployet til Cloudflare Pages.
- Live curl + parse af alle 7 URL'er: 7/7 leverer gyldig FAQPage schema
  (2 ld+json-blokke pr. side: WebApplication + FAQPage) og synlig FAQ-sektion.
- full_site_check: 261 URL'er, kun de 5 kendte Worker-301-canonical-aliaser —
  ingen nye problemer.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).

## Næste iteration

- DA-mirrors af contrast-checker, color-blindness-simulator og
  text-on-image-checker mangler stadig FAQ — samme generator kan udvides med
  danske tekster.
- GitHub Marketplace-listing for bugbottle-action er stadig ét UI-klik væk.
- Page Profile Pro: færdig i koden, venter kun på LS-checkout-URL.
