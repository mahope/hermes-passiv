# DECISION — Iteration 270: Mål lead-formularerne per side før pivot-beslutning

**Dato:** 2026-08-25
**Beslutning:** Giv NIS2-lead capture ét meningsfuldt målelag: hver formular
logger nu en `lead_<tool>`-event ved succes, så /api/stats viser hvilke af de
6 sider der konverterer. Sammenholdt med dagens data er pivot-reglen fastlagt:

> Hvis næste iteration viser 0 `lead_*`-events OG ~0 sidevisninger på
> værktøjssiderne, stoppes NIS2-sporet og der bygges til en platform med
> indbygget distribution + betaling (Obsidian-plugin eller Shopify-app),
> så Mads kun skal godkende ÉN konto.

## Data (reelt, 25/8)

- Waitlist: 1 ægte signup (uændret siden iter 268)
- NIS2-værktøjssider: **0 registrerede sidevisninger** i hele måleperioden —
  trafikken (15/18/5 besøg pr. dag) går til forsiden
- GitHub organisk: 0 visninger/14 dage på alle repos
- Søgninger brugt denne iteration: 0

## Budget: 0 kr brugt (35/1000 total)
