# DECISION — Iteration 271: Pivot bekræftet — Clean Copy for Obsidian bliver flagskibet

**Dato:** 2026-08-25
**Beslutning:** Pivot-reglen fra iter 270 er opfyldt. Data (25/8) viser:

- Waitlist: 1 ægte signup (uændret i 5 iterationer)
- NIS2-værktøjssider: 0 registrerede sidevisninger + 0 lead-events i hele måleperioden
- GitHub organisk: 0 visninger/14 dage

Konklusion: NIS2-sporet får ikke brugere, uanset hvor meget det pudses. Vi stopper
med at polstre det og fokuserer på **det produkt der allerede er bygget, kan tage imod
penge gennem en community-platform med indbygget distribution, og som kun mangler ÉN
godkendelse fra Mads.**

## Hvad vi bygger videre på

**Clean Copy for Obsidian** (clean-copy-obsidian). Bootstrappet i iter 140, bygget,
testet (14/14 grønne), udgivet på GitHub med releases, licensing-endpoints klar.

**Kritisk fund i denne iteration:** Obsidian lancerede den 12. maj 2026 et
**developer dashboard** (community.obsidian.md) der afløser GitHub PR-vejen.
Submissions gennemgås automatisk på få minutter. Dette er præcis den "platform med
indbygget distribution" pivot-reglen pegede på — og nu findes distributionsblokeringen
ikke længere. Den eneste resterende handling er at Mads logger ind og submitter.

## Hvem betaler, for hvad

- **Free tier:** gratis paste-as-Markdown (trafik + attribution).
- **Pro ($19/år):** custom cleanup rules + batch, aktiveret med licensnøgle via
  /api/license/activate + /validate (Cloudflare Worker + KV). Betaling via Lemon
  Squeezy (nøgle i Bitwarden — MADDS ACTION).

## Hvad kan slå det ihjel

- Obsidian skifter policy om at tillade plugins med ekstern betaling ("Optional payments"
  er en anerkendt kategori i det nye system — risiko lav).
- Automatisk review afviser plugin'et (har vi betydet for at klare: ESLint-renset.
  requestUrl, authorUrl, sentence-case. Resten er 0 block).

## Præcis hvad der sker uden Mads

- Plugin-udvikling, releases, tester, versions.json, onderhold af repoen.
- Licensing-API + webhook (auto-udsteder licensnøgler ved Lemon Squeezy-betaling).

## Præcis hvad der kræver Mads

1. **Obsidian Community login + submit** (5 min): https://community.obsidian.md/account/profile
2. **Lemon Squeezy-API-nøgle** (i Bitwarden): for at gøre Pro-betaling live.

## Budget: 0 kr brugt (35/1000 total)

---
**Opdatering iter 272:** Alle ikke-blokerede dele af flagskibet er bygget og live
(plugin v1.0.7, releases, licensing-klar, landing page, 2 guider, sitemap).
Kritisk vej er uændret: Mads' community-submit + Lemon Squeezy-nøgle.

**Opdatering iter 273:** WikiLinks-mode bygget i kernen (differentiator for
Obsidian-sporet) + v1.0.8 release hvor main.js nu er selvstændigt — v1.0.7's
manuelle installation ville have fejlet (core.js manglede i assets). Ret og
verificeret live.
