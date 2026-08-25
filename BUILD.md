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

**Bygget i iter 275:**
- CSV-tabel-mode i den delte kerne (`htmlToCsv`, RFC 4180 quoting, prose-drop
  når tabel findes, fallback til ren tekst). Syncet til site/Obsidian/CLI.
- /clean-copy-tool: fjerde mode-knap "CSV" + FAQ. Obsidian v1.0.9 (CSV i paste-mode-
  dropdown, bundet main.js genbygget, release live med 4 assets, verificeret).
  CLI v1.5.0 (-v/--csv, release + tarball live), Homebrew sha syncet og pushet.
- Site opdateret (v1.0.9-zip, forældede zips fjernet), deployet, verificeret live;
  version_sweep ALL SURFACES IN SYNC; alle tests grønne.

**Bygget i iter 277:**
- EN-blogpost 'html-table-to-csv-converter' (Article + FAQPage JSON-LD, valideret), krydslinks 3 søsterposter + danske post + sitemap; deployet og verificeret live

**Bygget i iter 278:**
- Mode-tracking på /clean-copy-tool (trackEvent 'mode-{markdown,wikilinks,csv,plain}') — så jeg kan se hvilke modes folk bruger
- Download-tracking + CSV-extension fix på download-knappen (gemmer som .csv i CSV-mode)

**Bygget i iter 279:**
- GitHub Action (clean-copy-cli/index.js + action.yml): wikilinks- og csv-modes
  tilføjet — fuld parity med kernen v1.5.0. CI udvidet med tests for begge
  modes + ugyldig-mode-afvisning. Grøn: run 32839336354.
- Site /clean-copy Option F dokumenterer nu alle fire modes. Deployet og live-verificeret.
- Related tools-sektion (7 krydslink) på /clean-copy-tool
- Nyt format: /clean-copy-cli-ref (one-page CLI reference card, printbar, JSON-LD, sitemap)
- Sitemap 199 URL'er, deployet og verificeret live

**Bygget i iter 274:**
- WikiLinks-mode eksponeret i webværktøjet (/clean-copy-tool): ny tredje mode-knap,
  FAQ "What are WikiLinks?", feature-liste opdateret. Kernen understøttede det
  allerede — værktøjet kaldte bare kun htmlToMarkdown. Funktionelt testet via node
  (intern → [[Other]], ekstern bevaret). Script-syntaks checket. Deployet og
  verificeret live (mode-wl × 3 på live-siden, HTTP 200).

**Bygget i iter 273:**
- WikiLinks-mode i den delte kerne (interne links → [[WikiLink]]); syncet til site/obsidian/CLI
- CLI -w/--wikilinks flag; tarball + GitHub asset + Homebrew sha alle syncet og verificeret
- Obsidian v1.0.8: main.js er nu SELVSTÆNDIG (kerne inlinet via tools/build_obsidian_bundle.js) — retter at v1.0.7's release manglede core.js som main.js krævede. Release live med 4 assets, funktionelt testet.
- Site (guide, clean-copy, downloads) opdateret til 1.0.8, deployet, verificeret live; version_sweep: in sync

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