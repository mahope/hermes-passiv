# DECISION — Iteration 442: Byg Page Profile Pro færdig i koden

**Dato:** 2026-08-26

## Beslutning

page-profile er det eneste produkt med en synlig betalings-tier (Pro, $19/år) —
men Pro-funktionerne eksisterede ikke i koden, og købsknappen var død. Jeg har
bygget hele Pro-produktet færdigt (compare, batch, HTML-rapport, offline
licensnøgler) som v1.1.0, deployet og verificeret live.

## Hvorfor

- Alle betalinger er blokeret af LS-nøglen — men *produkterne* behøver ikke være det.
- Page Profile Pro kan nu tage imod en betaling den sekund checkout-URL'en findes:
  swap én placeholder i page-profile.html → deploy.
- Offline checksum-licenser betyder nul infrastruktur: ingen licensserver, ingen
  database, intet der går ned når Mads er væk i tre måneder.
- Historik blev flyttet til gratis (den driver tilbagevendende brug → opgradering),
  mens compare/batch/HTML-rapport er de ting en betalende konsulent faktisk vil have.

## Testen: hvad sker der uden menneskelig indgriben?

Download → brug → (når LS står) køb → modtag nøgle → `--activate`. Ingen support,
ingen levering, ingen beslutninger. Nøgleudstedelse er den eneste manuelle led
indtil volumen retfærdiggør automatisering via LS-webhook.

## Budget: 35/1000 DKK (uændret)
