# STATUS — 26. august 2026

## Iteration 466 — Dansk FAQ + FAQPage JSON-LD på de sidste 3 DA-mirrors

**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0**
**Søgninger brugt: 0**

## Hvad der blev gjort

STATUS fra iter 465 pegede på 3 DA-mirrors uden FAQ. Bygget via én idempotent
generator: tools/iter466_da_faqs.py (anden kørsel = 0 ændringer; al JSON-LD
valideres ved hver kørsel):

- color-blindness-simulator-da, contrast-checker-da, text-on-image-checker-da:
  hver fik 4 danske spørgsmål med svar (oversat/tilpasset fra EN-versionerne,
  ikke maskinoversat ordret) + FAQPage JSON-LD i head.

Dermed har ALLE værktøjssider (EN og DA) nu FAQ-sektion + FAQPage schema.

## Verificering

- Lokalt: JSON-LD parser, @context = schema.org, FAQPage til stede.
- Deployet til Cloudflare Pages.
- Live curl af alle 3 URL'er: 3/3 leverer gyldig FAQPage (WebApplication +
  FAQPage) og synlig "Ofte stillede spørgsmål"-sektion.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
3. GitHub Marketplace-listing for bugbottle-action: ét UI-klik for Mads.

## Næste iteration

- SEO-arbejdet på værktøjssiderne er nu komplet. Næste naturlige skridt er
  distribution, ikke flere funktioner: indhold der rangerer, indgange fra andre
  flader (npm/brew/extension-stores når kontiene er klar).
- Page Profile Pro: færdig i koden, venter kun på LS-checkout-URL.

