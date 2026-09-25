# Stripe-kontrakt for alle Hermes-produkter

Kilde: missionen af 24./25. september 2026. Denne fil er den menneskelæselige
modstykke til `tools/stripe_catalog.json`; `tools/check_stripe_ctas.py` fejler,
når de to kommer ud af trit. Lemon Squeezy er lukket, og Gumroad er droppet —
begge må aldrig genoplives.

## Køb (Payment Links)

Ingen side, klient eller CI-job må have Stripe-nøgler. Sider linker direkte til
Payment Links; nøglerne ligger kun i Bitwarden og som secrets på workeren.

| Produkt | product_key | Pris | Betalingslink |
|---|---|---|---|
| Clean Copy Pro | `clean-copy-pro` | $19/år | https://buy.stripe.com/6oU4gy76PgvgdBIdAXbMQ00 |
| DeskUptime Pro | `deskuptime-pro` | $19 engang, 3 maskiner | https://buy.stripe.com/7sY9AS9eX3Iu418fJ5bMQ01 |
| Transmute Desktop | `transmute-desktop` | $19 engang, 3 maskiner | https://buy.stripe.com/eVqbJ0dvdbaW55cgN9bMQ02 |
| EUComply Pro | `eucomply-pro` | $79/år pr. website | https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03 |
| Page Profile Pro | `page-profile-pro` | $19/år | https://buy.stripe.com/9B6eVcgHp7YK69ggN9bMQ04 |
| GDPR DPA template | `eucomply-dpa` | $59 | https://buy.stripe.com/bJe7sK8aT4My7dk7czbMQ05 |
| NIS2 / DORA Vendor Clause Set | `eucomply-nis2-clauses` | $49 | https://buy.stripe.com/4gM4gydvd92OapwgN9bMQ06 |
| Mutual NDA Clause Set | `eucomply-nda-clauses` | $29 | https://buy.stripe.com/aFafZg1Mv92OdBI8gDbMQ07 |
| EAA Accessibility Statement | `eucomply-eaa-statement` | $39 | https://buy.stripe.com/3cI7sK2Qz3IugNUgN9bMQ08 |
| Client Compliance Report Kit | `eucomply-report-kit` | $69 | https://buy.stripe.com/00wdR8bn5a6S0OWeF1bMQ09 |
| EUComply Complete Template Bundle | `eucomply-template-bundle` | $149 | https://buy.stripe.com/eVqaEW0Iren855c68vbMQ0a |
| EU Compliance E-book Bundle | `eu-compliance-ebook-bundle` | $29 | https://buy.stripe.com/fZu9AScr9a6SbtA68vbMQ0b |
| Support for Mahope open source (donation, valgfrit beløb) | `support-mahope-oss` | fra 10 kr. | https://donate.stripe.com/7sYeVcbn50wieFM8gDbMQ0c |

Stripe vælger valuta efter kundens land; priserne vises også i EUR og DKK.
Efter betaling lander køberen på `https://mahope.tools/thanks?session_id=…`,
som viser licensnøgle eller downloadlinks. Det samme sendes pr. mail fra
orders@mahoje.dk.

## Kundeportal (opsigelse og fakturaer)

Årsabonnenter — `clean-copy-pro`, `eucomply-pro` og `page-profile-pro` — skal
kunne opsige, hente fakturaer og rette kort, adresse og momsnummer selv. Det sker
i Stripe-kundeportalen:

https://billing.stripe.com/p/login/6oU4gy76PgvgdBIdAXbMQ00

Linket vises på `/thanks`, på `/support` og under opsigelse i `site/terms/`, og
i leveringsmailen for de tre årlige produkter. Engangskøb (DeskUptime Pro,
Transmute Desktop, alle downloads og donationen) får **ikke** linket, fordi
deres betaling ikke fornyes. Kun denne ene portal-URL må bruges offentligt.

## Licens-API

Base: `https://mahope.tools/api/license/`. Alle kald er `POST` med JSON og
CORS `*`.

| Endpoint | Body | Svar ved succes |
|---|---|---|
| `activate` | `{ license_key, device_id, product }` | `200 { ok: true, activated: true, plan, expires_at, devices_in_use }` |
| `validate` | `{ license_key, device_id, product }` | `200 { ok: true, valid: true\|false, plan, expires_at, reason? }` |
| `deactivate` | `{ license_key, device_id }` | `200 { ok: true, deactivated, devices_in_use }` |

- `license_key` er 32 hex-tegn (`/^[a-f0-9]{32}$/`). Trim og brug små bogstaver
  før afsendelse.
- `device_id` er stabilt pr. maskine eller installation, højst 128 tegn.
  WordPress bruger sitets hostname.
- `product` er product_key fra tabellen. En nøgle til et andet produkt giver
  `403`.

Fejlkoder: `400` forkert format, `404` ukendt nøgle, `403` udløbet/tilbagekaldt/
forkert produkt, `409` enhedsgrænsen nået, `503` midlertidig fejl. Klienter skal
fejle blødt og beholde en cachet Pro-status i højst syv dage, så en nede
licensserver ikke låser betalende kunder ude.

## Hvad der ikke er tilladt

- Nye Stripe-produkter, priser eller links oprettes ikke fra repoet. Mangler et
  produkt, skrives det i `IMPLEMENTATION_PLAN.md` under `❓ Til Mads`.
- En synlig pris eller en "coming soon"-knap på et produkt uden tilladt link er
  en fejl, ikke en købsrejse. Sådanne tilbud skal have prisen fjernet og
  spørgsmålet flyttet til `❓ Til Mads`.
- Hver købsbar side har præcis én synlig CTA med et link fra tabellen. Den
  fulde inventering ligger i `tools/stripe_catalog.json` under `offers`, og
  `tools/check_stripe_ctas.py` beviser den.
