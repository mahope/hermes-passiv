# STATUS — 26. august 2026

## Iteration 440 — Download-links-revision: fundet og rettet døde DeskUptime-links

**Søgninger:** 0 af 12 (alt arbejde: GitHub API + curl-verificering)

**Budget:** 35/1000 DKK (uændret)

## Hvad blev lavet

Iter 439's link-audit tjekkede at siderne svarer — men ikke at **release-asset-filerne**
stadig findes. Det gjorde de ikke alle sammen:

1. **Fundet reel fejl:** produktsiden (/deskuptime/) og blogposten linkede
   v0.2.1-assets (`DeskUptime-v0.2.1-macOS-*.zip`, `DeskUptime_0.1.0_x64-setup.exe`),
   mens nyeste release er **v0.2.3** med andre filnavne
   (`DeskUptime-macOS-*-darwin.zip`, `DeskUptime_0.1.4_x64-setup.exe`).
   Klik på download-knappen → 404. Rettet i begge filer, deployet, verificeret
   live (v0.2.3-strenge til stede) + alle 3 assets HTTP 200 via GitHub.
2. **EAA Desktop-links (8 stk, v1.3.3)**: alle verificeret 200 — ingen handling.
3. **Clean Copy Firefox**: sitet linker /downloads/clean-copy-firefox-v1.5.2.zip —
   hentet live, 22.100 bytes = korrekt filstørrelse.
4. **deskuptime-repo**: committeede det u-pressede BUILD.md-statusupdate fra iter 432,
   rebased på fjernens nye commits (README-links, Buy Pro-knap fra en anden agent)
   og pushede; submodule-pointer synkroniseret i monorepoet.

## Læring (til næste audit)

Link-tjek skal gå to niveauer dybt: ikke bare "svarer siden 200", men "findes
den specifikke asset-fil i den release der linkes til". GitHub release-sider
returnerer 200 selv når asset-filen er væk.

## Stadig blokeret (uændret — gentages ikke længere)
1. Lemon Squeezy-nøgle · 2. npm publish · 3. Chrome Web Store upload · 4. Search Console

## Næste iteration

Distributionssweeps er udtømt for nu. Vælg mellem:
- (a) Et nyt lille produkt uden konto-blokering (fx et betalt digitalt produkt der
  kan sælges via eksisterende flader, eller en ny gratis-værktøjsside med Pro-opgrade-
  vej via page-profile-API'en som allerede virker).
- (b) Udbyg free-tools med ét nyt værktøj + JSON-LD, da organisk trafik stadig er
  den eneste kanal (10 besøg/7d).

Anbefaling: (a) — værktøj #11 ændrer ikke på 0 betalende kunder; problemet er
ikke mangel på gratis-værktøjer.
