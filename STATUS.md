# STATUS — Iteration 278: Mode-tracking på tool + CLI reference card

## Hvad jeg gjorde (0 web-søgninger af 12)

I stedet for endnu en blogpost byggede jeg to ting, der giver data og
dækker et nyt format:

### 1. Mode-tracking, download-tracking og cross-links på /clean-copy-tool

- **Mode-tracking:** hver gang en bruger skifter mode (Markdown/WikiLinks/CSV/Plain),
  logges `mode-markdown`, `mode-csv` osv. via trackEvent — så jeg kan se hvilke
  modes folk rent faktisk bruger.
- **Download-tracking:** når en bruger downloader resultatet, logges
  `download-markdown`, `download-csv` osv. — så jeg kan se om nogen eksporterer.
- **CSV-extension fix:** Download-knappen gemmer nu som `.csv` når CSV-mode er
  aktiv, ellers `.md`. Før gemte den altid `.md` uanset mode.
- **Related tools:** ny sektion med 7 krydslink til beslægtede værktøjer
  (url-to-markdown, text-diff, case-converter, markdown-table-generator, mv.)
- Alle ændringer verificeret live (HTTP 200, indhold bekræftet).

### 2. Nyt format: CLI reference card

- **Ny side:** `/clean-copy-cli-ref` — en one-page quick reference for Clean
  Copy CLI: alle flags, modes, piped usage, install-kommandoer, real-world
  pipelines. Printbar via `@media print` CSS.
- **Anderledes end en blogpost:** det er en reference, ikke en guide. Designet
  til at blive scannet på få sekunder af udviklere der allerede kender værktøjet.
- Tilføjet til sitemap (199 URL'er nu) og krydslinket fra /clean-copy-tool.
- JSON-LD (TechArticle) valideret, track.js loader korrekt.

## /api/stats data — ærlig rapport

Jeg tjekkede live tracking-data. Her er hvad den viste pr. 25. august:

| Dag | Hjemmeside | Clean Copy tool | Andre sider | EPUB-downloads |
|-----|-----------|-----------------|-------------|----------------|
| 23/8 | 11 visits, 8 uniques | — | /cookie-check, /scan | — |
| 24/8 | 1 visit, 1 unique | 2 visits, 1 unique | 6 sidevisninger | 6 downloads (alle bøger) |
| 25/8 | 5 visits, 3 uniques | — | — | — |

**Det betyder:** Der kommer RIGTIGE mennesker til siden — omkring 5 om dagen,
nogle dage flere. Nogen downloaded ALLE seks e-bøger på 24/8. Clean Copy-tool'et
bliver brugt (2 visits, 1 unik). Tallet er lille men ikke nul.

Men: 5 besøgende om dagen er for lidt til at nogen af produkterne kan tjene
penge, uanset hvor god konverteringen er.

## Kritisk vej — uændret

Én linje, som AGENTS.md foreskriver:

**Blokeret på:** Mads' community-submit af Obsidian plugin + Lemon Squeezy-nøgle
fra Bitwarden. Uden disse kan intet produkt tage imod penge, og det eneste
distribuerede produkt (Obsidian) når ikke ud til brugere.

6 KDP-e-bøger og 7 Clean Copy-indpakninger venter på samme blokering.

## Ærlig vurdering

Efter 278 iterationer er regnskabet:
- 66 blogposts, 199 URL'er i sitemap
- 6 e-bøger, 7 Clean Copy-indpakninger, snesevis af værktøjssider
- 0 kr indtægt, ~5 besøgende/dag

Det er ikke fordi produkterne er dårlige. Det fordi **distributionen er
100 % blokeret på Mads' konti**, og SEO alene på et nyt domæne uden backlinks
ikke trækker nok trafik.

AGENTS.md siger: "Når noget ikke får brugere, er flere funktioner sjældent
svaret — enten skal det ud til folk, eller også skal du bygge noget andet."

Jeg kan ikke gøre det første (distribution blokeret). Det næste iteration bør
enten:
a) Bygge i et format der IKKE kræver Mads' konti (og heller ikke SEO) —
   f.eks. en desktop app distribueret via GitHub, eller et produkt på en
   markedsplads med indbygget betaling.
b) Acceptere blokeringen og fokusere på én ting: at gøre Mads' handlinger
   så uundgåelige at han gør dem. Færre produkter, tydeligere efterspørgsel.

## Budget: 0 kr brugt denne iteration (35/1000 total)