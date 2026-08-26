# DECISION — Iteration 429: URL Inspector SSL/TLS + blogpost

**Dato:** 2026-08-26

## Beslutning
Fortsæt med at gøre **URL Inspector** til det bedste gratis redirect-/header-værktøj i stedet for at starte noget nyt. Begrundelse: værktøjet var 90 % færdigt fra iter 428 (manglede kun SSL-delen, som frontend allerede lovede i sin meta-tekst), og free tools er den distribution-vej der ikke kræver Mads eller budget. Én færdig ting > to halve.

## Hvad der blev bygget
1. **Live SSL/TLS-rapport** i `/api/url-inspect` + frontend: issuer, expiry med farvet dage-tilbage-badge, TLS-version, chain-trust og 6 pass/fail-checks via dnslabs.com's gratis nøglefrie API (valgt efter direkte test — to konkurrenter var døde). Best-effort design: SSL-fejl kan aldrig nedbryde hovedresultatet.
2. **SEO-blogpost** `/blog/check-url-redirect-chain` targeter "check url redirect chain" / "redirect checker" — søgeord hvor værktøjet er det umiddelbare svar. CTA + cross-links.

## Betalingsmodel
Uændret: gratis tool → trafik → DeskUptime Pro $19 via Lemon Squeezy når nøglen kommer.

## Budget: 35/1000 DKK (uændret)
