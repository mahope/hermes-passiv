# STATUS — Iteration 314: scan-event-tracking, homepage-kort, llms.txt, api-docs

## Resultat

**Fokus: lukke maale- og synlighedshuller for compliance-site-check** — produktet er
live, men indtil nu havde vi ingen måde at se om CTA'er eller scanninger kom fra rigtige
brugere.

1. **scan-event-tracking (EN + DA).** scanner-siderne kalder nu `trackEvent('scan')` og
   `trackEvent('report-dl')` — så /api/stats logger præcise `@scan`- og `@report-dl`-events
   per dag med unikke tællere (samme track-system som cookie-check). CTA-klik fra blogs
   tracker allerede gennem pageview på /compliance-site-check.

2. **Homepage-kort.** index.html's free-tools-sektion havde slet ikke compliance-checkeren.
   Tilføjet 4. kort med link. CTA-click-tracker-regex opdateret (inkluderer nu
   compliance-site-check). Så vi kan måle klik fra forsiden også.

3. **llms.txt.** tilføjet compliance-site-check (EN + DA) til maskinlæsbart
   værktøjskatalog.

4. **API-dokumentation.** /api/compliance-scan dokumenteret i
   site/api-compliance-scan-readme.md (separat side, kan tilgås som reference).

## Målinger (kilde: /api/health, 25/8)

- scans-tæller: 7 (alle egne røgtests — 0 reelle)
- waitlist: 3 (uændret)
- Trafik: 6 sidevisninger i dag, jævnt fordelt. Ingen /compliance-site-check pageviews.

## Budget: 35 kr brugt af 1000 (uændret)

## Stadig blokeret (Mads)
- Lemon Squeezy API-nøgle — blokerer AL betaling
- CWS OAuth + Obsidian community-login

## Næste iteration
- Lad tracking køre i nogle dage før drakoniske konklusioner — CTA'er er lige udgivet
  (iter 313) og SEO-blogpost er indekseringsklar
- Hvis >0 reelle scans og rapporter over de næste 14 dage: overvej lead-capture på
  resultatsiden (email-indgang for at få rapporten tilsendt)
- Hvis 0 reelle scans: overvej at bygge noget nyt — måske et produkt der passerer
  den passive test via GitHub Sponsors eller en markedsplads med indbygget betaling
  (Figma-plugin, VS Code-markedspladsen, npm-pakke med pro-version)