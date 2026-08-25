# BUILD — hvad der er bygget, hvad der mangler

## Bygget (hele historien)

**NIS2-økosystemet:**
- /nis2-check (scope checker) — EN + DA
- /nis2-incident-generator (incident report) — EN + DA
- /nis2-gap-assessment (20-spørgsmåls analyse) — EN + DA
- E-bog: "NIS2 Compliance for Small Web Agencies" (KDP, venter på Mads)
- Blog: 5 NIS2-relaterede indlæg (checkliste, incident report, readiness guide, gap assessment guide, GDPR overlap)
- **Email lead capture på alle 6 NIS2-værktøjer** (iter 269: + /nis2-check EN/DA; iter 268's falske "vi sender PDF"-tekst rettet til ærlig beskrivelse — ingen email-afsendelse findes, e-mail gemmes kun til lanceringssvar)
- **Lead-konverteringssporing pr. side (iter 270):** hver formular sender `trackEvent('lead_<tool>')` ved succesfuld tilmelding — synligt i /api/stats?token=hp-stats-v1

**Clean Copy-økosystemet:**
- Chrome-udvidelse (bygget, CWS-upload blokeret)
- Firefox-udvidelse (bygget, AMO-upload blokeret)
- VS Code-udvidelse (bygget, publisher-blokeret)
- npm-pakke (bygget, publish-blokeret)
- Obsidian-plugin (bygget, PR-blokeret)
- GitHub Action (live og fungerer)
- CLI-værktøj (live på GitHub)
- 10+ blog-indlæg

## Mangler (blokeret)

- Betalingsintegration (Lemon Squeezy-nøgle i Bitwarden)
- Email levering til leads (kræver Mads' accept — udadvendt i hans navn)
- KDP-e-bog (kræver Mads' KDP-konto)
- CWS-upload (kræver OAuth-credentials i Bitwarden)
- Alle andre kanaler (kræver konti i Mads' navn)

## Plan for næste byg

**Pivot bekræftet (iter 271):** NIS2-sporet stoppes. Clean Copy for Obsidian bliver flagskibet.

**Bygget i iter 272:**
- Installationsguide /blog/install-obsidian-plugin-clean-copy (BRAT/manuelt/zip,
  FAQ, JSON-LD SoftwareApplication+FAQPage) — live og verificeret
- Krydslink + v1.0.7-note i paste-guiden; sitemap 196 URL'er; deploy verificeret

**Bygget i iter 271:**
- v1.0.7 release: fetch → requestUrl (Obsidian policy compliance), authorUrl i manifest,
  versions.json rettet til at inkludere alle versioner 1.0.0–1.0.6 (tidligere manglede 1.0.2–1.0.6)
- Release 1.0.7 live på GitHub med 3 assets (main.js, manifest.json, styles.css)
- Obsidian-submission-kit opdateret til nyt dashboard-flow (community.obsidian.md)
- FAQ: gentag ALDRIG en søgning — dette er iter 271's eneste jagt
- Nul kr brugt denne iteration

## Næste skridt (kræver Mads)

1. Log ind på https://community.obsidian.md/account/profile, connect GitHub, submit plugin
2. Giv Lemon Squeezy-API-nøgle fra Bitwarden

## Hvis Mads ikke gør noget

- Plugin'et fortsætter med at virke via BRAT/manual install
- Ingen nye brugere får det gennem community-listen
- Ingen Pro-indtægt før Lemon Squeezy