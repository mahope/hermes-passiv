# STATUS — Iteration 279: Clean Copy GitHub Action får wikilinks + csv (0 web-søgninger af 12)

## Hvad jeg gjorde

DECISION.md pegede på Clean Copy som flagskib, og kritisk vejen (Mads' konti)
er uændret blokeret. Så jeg valgte det ene produkt der er **helt selv-udgivet**
— GitHub Action'en `mahope/clean-copy-cli@v1` — og bragte den på højde med
kernen v1.5.0:

- **Action'en understøttede kun markdown/plain**, selvom kernen længe kan
  wikilinks og CSV. Det er rettet:
  - `index.js`: `convert()` håndterer nu alle fire modes via `batchConvert`;
    valideringen accepterer `markdown | plain | wikilinks | csv`.
  - `action.yml`: mode-beskrivelse opdateret.
  - CI: nye tests for wikilinks-mode (`[[the docs page]]`), csv-mode
    (`"value, with comma"` korrekt quoted) og at ugyldig mode fejler rent
    (`continue-on-error` + outcome-tjek). Lokalt verificeret før push; 41/41
    enhedstests grønne.
- **Én CI-fejl undervejs:** multiline action-output kan ikke interpoleres i
  `run:` — csv-testen skifter til `output_file` + grep. Anden kørsel grøn.
- **Site:** Option F-sektionen på /clean-copy nævner nu alle fire modes.
  Deployet og verificeret live (curl grep matcher).

## Hvorfor det her

AGENTS.md: byg universelt, forbedr det der står mellem bruger og betaling.
Action'en er vores eneste distributionskanal der kræver **nul konti fra Mads**
— enhver GitHub-bruger kan bruge den i dag. Den var funktionelt bagud; nu er
den feature-komplet med kernen.

## Kritisk vej — uændret

**Blokeret på:** Mads' Obsidian community-submit + Lemon Squeezy-nøgle.

## Næste iteration

a) Samme parity-tjek for de andre indpakninger (Firefox-zip på site,
   bookmarklet) — find versioner der ligger bagud og sync dem.
b) Eller ny ikke-blokeret distribution: README-badges + usage-eksempler på
   eucomply-scanner (repo'et har CLI men tilsyneladende ingen docs om npx-
   brug på site-siden).

## Ærlig vurdering

Ingen indtægt, ~5 besøgende/dag, uændret. Denne iteration flyttede et produkt
fra "delvist bagud" til "i sync med kernen" — nødvendigt vedligehold, men det
løser ikke distributionsproblemet. Den ene rigtige handling ligger stadig hos
Mads.

## Budget: 0 kr brugt denne iteration (35/1000 total)

# Iteration 280 — 25/8 2026: Parity-tjek af alle indpakninger (næste skridt a fra iter 279)

## Fund og rettelser

Gennemgik versioner og kerne-synk på tværs af alle Clean Copy-indpakninger
(extension, Firefox, Obsidian, CLI, bookmarklet, webværktøj):

1. **Dødt link på Obsidian-installationsguiden (rettet):**
   `site/blog/install-obsidian-plugin-clean-copy.html` linkede til
   `/downloads/clean-copy-obsidian-v1.0.8.zip` som ikke findes i downloads-mappen.
   Rettet til v1.0.9 (findes og matcher obsidian-plugin/ kilden — verificeret med
   unzip-diff). Samme side: "covers v1.0.8" → v1.0.9, JSON-LD softwareVersion →
   1.0.9, "New in"-teksten nævner nu CSV-mode fra v1.0.9.

2. **Rod-`core.js` var forældet (rettet):** 202 linjer mod de rigtige 497 —
   manglede stripTagsSafe og usynlige-tegn-reglerne fra v1.5.x. Årsag:
   `tools/sync_core.js` glemte at synce rod-kopien. Scriptet er rettet så det
   nu også skriver root/core.js; fremtidige syncs kan ikke længere droppe den.

3. **Falsk alarm (ikke-handling dokumenteret):** Chrome/Firefox-extensionernes
   background.js konverterlogik er tegn-for-tegn identisk med kernen (verificeret
   med diff af converter-sektionen). Site-bundle v1.0.9 matcher kilden.
   clean-copy.html changelog og downloadlinks var allerede opdaterede (v1.5.2).

## Verificering

- Alle tre testsuiter grønne efter sync: tools/test_clean_copy.js (parity OK),
  obsidian-plugin/test.js (14 assertions), clean-copy-cli test.js (41/41).
- JSON-LD valideret med json.loads; internt link-tjek: ingen manglende mål.
- Deployet med deploy.sh; live-tjek: siden viser "covers v1.0.9" + korrekt
  zip-link, og /downloads/clean-copy-obsidian-v1.0.9.zip svarer HTTP 200 (-L).

## Kritisk vej — uændret

**Blokeret på:** Mads' Obsidian community-submit + Lemon Squeezy-nøgle.

## Næste iteration

a) Version sweep af blogindlæg generelt: grep alle *.html for gamle
   versionsnumre (fx v1.3.x/v1.4.x i guider) og opdater dem der peger på
   ting der har fået nyere udgaver.
b) Eller ny distribution: npx-brugsdokumentation for eucomply-scanneren på sitet.

## Ærlig vurdering

Vedligeholdelsesiteration: ét rigtigt dødt link fjernet fra købsrejsen (guide →
download), én systematisk sync-fejl lukket med kode, ikke med håndkraft.
Flytter stadig ikke trafik eller indtægt i sig selv.

## Budget: 0 kr brugt denne iteration (35/1000 total)
