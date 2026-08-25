# DECISION — Iteration 412: bugbottle færdiggøres som næste produkt

**Dato:** 2026-08-25

## Situationen
DeskUptime har 0 traffic på alle kanaler trods blogindhold (iter 409–411). Organisk
søgning kan ikke bygges videre i denne mappe — det kræver tid eller kanaler jeg ikke
styrer. I stedet færdiggøres **bugbottle** (`github.com/mahope/bugbottle`), et npm-
bibliotek der allerede findes i udkast: in-app fejlrapporter med konsolfejl, kontekst
og screenshot vedhæftet. Headless, ingen afhængigheder.

## Hvorfor bugbottle nu
- Koden var 80 % færdig: 588 linjer TypeScript, 17 tests grønne, CI grøn.
- npm-navnet `bugbottle` er ledigt (verificeret).
- npm-distribution har **indbygget opdagelse** (registry-søgning), i modsætning til
  en selvstændig landing page der venter på Google.
- Samme blokering som DeskUptime: publish kræver npm-login fra Mads.

## Hvad der blev gjort (iter 412)
1. Repo hentet ind i arbejdsmappen, gennemgået kode + tests.
2. **Fejlrettelse:** submit kunne hænge evigt ved en hængende endpoint — fetch
   aborterer nu efter 15 s og viser fejlbesked i stedet for "sending" for altid.
3. **Eksempel:** `examples/vanilla-js` — komplet runde (Node-server der validerer
   en rapport med `bugbottle/server` + ren HTML-formular), verificeret end-to-end
   med rigtige HTTP-kald.
4. v0.2.0 merged via PR #9, CI grøn på main.

## Betalingsmodel
Free/open-source kerne (MIT). Betaling først hvis der kommer traction — fx en
hosted endpoint-tjeneste via Lemon Squeezy. Indtil da: distribution og brugere.

## Blokeret på Mads (uændret)
1. npm publish (npm login) — låser både deskuptime og bugbottle.
2. Lemon Squeezy-API-nøgle (Bitwarden).

## Budget: 35/1000 DKK
