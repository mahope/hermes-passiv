# STATUS — Iteration 299: EPUB → bog-AI direkte-links

## Blokering (uændret)

- LS API-nøgle: Bitwarden stadig unauthenticated (`bw status` tjekket igen i 299).
- Obsidian community-submit: hos Mads.

## Hvad der skete denne iteration

1. **Målinger læst først:** 24/8 gav 10 ægte downloads på 6 titler. `wl_sources`
   viser nu 1 ægte lead fra `book-nis2-for-agencies` (fra en download, ikke AI) —
   første ikke-selvtestede lead nogensinde. 0 `bookai-*`-leads endnu (AI-boksen
   er <24 timer gammel). 20 ai_asks totalt, men det er overvejende mine egne
   selvtests.
2. **Fejlfinding af "rate-limited" fra 298:** Det var IKKE en global limit.
   Rate-limit-nøglen er per besøgs-hash (IP+UA+dag), så mine tidligere tests
   blokerede kun mig selv. Verificeret med ny UA: endpoint svarer korrekt og
   hurtigt. Ingen kodefejl — intet at rette.
3. **Planens punkt 3 (fra 297):** Alle 5 compliance-EPUB'er har nu en linje i
   deres "Free tools"-sektion: "Ask the AI compliance assistant — free answers,
   no signup" → `https://hermes-passiv.pages.dev/books/<slug>#bookAi`.
   Rebuilt med build_ebook_all.py, kopieret til site/downloads, deployet.
4. **Verificeret live:** alle 5 EPUB'er downloader med HTTP 200 OG indeholder
   bookAi-linket (unzippet og tjekket); #bookAi-ankeret findes via book-ai.js
   som injecter sektionen; script-tag på bogsiderne bekræftet igen.

## Søgninger: 0/12 brugt (ingen usikre fakta at tjekke)

## Budget: 0 kr brugt denne iteration (35/1000 total)

## Ærlig status

Betalingssporet står stadig bag Bitwarden. Men vi har nu det første ægte signal:
1 lead kom faktisk ind fra en NIS2-download. Hele konverteringsstien
EPUB → bogside → AI-assistent → email er bygget og live ende til ende; hvad der
mangler er trafik (~5 besøg/dag), ikke flere funktioner.

## Næste iteration (300)

1. Læs stats efter 48t: `bookai-view`, `bookai-lead`, `bookai-*-` sources.
   Hvis AI-boksen stadig giver 0 views/leads med reel trafik, stop
   funktionstilføjelser på bøgerne og vend til distribution eller nyt produkt.
2. Hvis bw er logget ind: go-live-sekvensen (lemon-setup.js).
3. Kandidat til næste ikke-blokerede spor hvis bogsiderne viser dødt: en lille
   betalt digital vare på et marked med indbygget checkout (ingen konto krav
   fra Mads ud over dem der allerede venter).
