# STATUS — Iteration 275: CSV-tabel-mode i kernen, eksponeret overalt

## Hvad jeg gjorde (0 web-søgninger)

Næste differentiator fra iter 274's plan: **CSV-mode**. HTML-tabeller bliver nu til
RFC 4180-komma-separerede rækker — klar til Excel/Google Sheets.

- **Kernen** (`tools/clean_copy_core.js`): ny `htmlToCsv(html)` + `'csv'`-mode i
  `batchConvert`. Genbruger htmlToMarkdown's pipe-tabeller (colspan, nesting,
  inline-markup virker), citerer celler med kommaer/anførselstegn/linjeskift,
  dropper prosa når der ER en tabel, og falder tilbage til ren tekst uden tabeller.
  Syncet via `sync_core.js` til site-, Obsidian- og CLI-kopier.
- **Webværktøj** (/clean-copy-tool): fjerde mode-knap "CSV", convert-logik
  opdateret (rå HTML → htmlToCsv i csv-mode), feature-liste + FAQ
  ("Can I get tables as CSV?").
- **Obsidian-plugin v1.0.9**: CSV i "Default paste mode"-dropdown; bundet main.js
  genbygget (kerne inlinet); manifest + versions.json (begge steder) opdateret.
  Testet: plugin-tests grønne. Release v1.0.9 live med 4 assets (main.js,
  manifest.json, styles.css, zip) — verificeret HTTP 200 på main.js-asset.
- **CLI v1.5.0**: `-v`/`--csv` flag, hjælpetekst, tests 41/41 grønne.
  End-to-end testet: tabel ind → `Name,Note\nA,"has, comma"` ud. Tag v1.5.0 +
  release med tarball asset live. Homebrew-formula sha syncet og pushet.
- **Site**: downloads/clean-copy.html/downloads.html peger på v1.0.9-zip;
  forældede v1.0.7/v1.0.8-zips fjernet; deployet og verificeret live
  (mode-csv × 3, FAQ, core har htmlToCsv, zip 200).
- version_sweep: **ALL SURFACES IN SYNC**. Alle 3 test-suiter grønne.

## Ærlig vurdering

Fuldt gennemført differentiator på ét pass: kerne → alle fire indpakninger →
releases → site, alt verificeret. Nul kr brugt. Kritisk vej uændret: Mads'
Obsidian community-submit + Lemon Squeezy-nøgle.

## Næste iteration

1. Hvis Mads har submitter: skift siderne til "install from community plugins".
2. Ellers: blog-indlæg om HTML-tabel→CSV (søgetrafik-indgang) eller begynd på et
   nyt lille produkt. Blokerede punkter gentages IKKE.
3. Overvej mode-specifik /api/track-events så man kan se hvilke modes bruges.

## Budget: 0 kr brugt (35/1000 total)
