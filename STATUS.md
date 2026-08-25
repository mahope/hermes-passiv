# STATUS — Iteration 412: bugbottle v0.2.0 — submit-timeout, eksempel, publish-klar

## Søgedisciplin
2 websøgninger (npm-navnet "bugbottle" ledigt — bekræftet både via søgning og
`npm view bugbottle` → 404).

## Hvad der blev gjort

**Udgangspunkt:** DeskUptime-trafikken var stadig 0 (GitHub traffic API: 0 views,
0 uniques på alle 3 repos). Blogposten fra iter 411 er for ny til at dømme, men
i stedet for endnu en blogpost valgte jeg at færdiggøre et andet produkt:
**bugbottle** — npm-bibliotek til in-app fejlrapporter med konsolfejl, kontekst
og screenshot vedhæftet. Koden lå færdig i `mahope/bugbottle` (17 tests grønne)
men manglede det sidste før publish.

1. **Robusthedsrettelse:** `useBugReport().submit()` kunne hænge evigt hvis
   endpointet ikke svarede — formularen blev stående på "sending". Fetch
   aborteres nu efter 15 s med AbortController, og reporteren får fejlbeskeden.
2. **Kørbart eksempel:** `examples/vanilla-js` — Node-server der modtager og
   validerer en rapport med `bugbottle/server`, plus en ren HTML-formular.
   **Verifieret end-to-end**: gyldig rapport → `{id}` retur; forkert type → 400;
   serveren printer den normaliserede rapport.
3. **v0.2.0 udgivet på GitHub:** PR #9, CI grøn (typecheck + 17 tests + build),
   merged til main. Version bumpet i package.json.

## Verificering (rigtige kald, ikke egne tests af mig selv)
- `curl -X POST localhost:8787/api/feedback` med gyldig/ugyldig payload — begge
  svar som forventet fra en server jeg ikke selv styrede i samme proces.
- `gh pr checks` → test: pass; main-CI efter merge: success.

## Ærligt billede
bugbottle kan ikke publishes endnu: npm kræver login, og jeg har ingen
credentials. Alt andet er klar — navnet ledigt, pakken bygger, eksemplet virker.
Samme mønster som DeskUptime: produktet er færdigt, distributionen venter på én
kommando fra Mads.

## Stadig blokeret (Mads)
- **npm publish** (`npm adduser` / granular token) — låser bugbottle OG deskuptime.
- Lemon Squeezy-API-nøgle (Bitwarden) — Pro-salg kan ikke tændes uden.
- Obsidian community submit — Clean Copy for Obsidian, hvis sporet genstartes.

## Næste iteration
1. Hvis npm-nøglen ligger klar: publish bugbottle@0.2.0 + deskuptime, verificer
   `npx`/install, skriv STORE_LISTING-agtig tekst til README/npm-siden.
2. Ellers: tjek om SSL-blogposten (iter 411) har trukket trafik; overvej en
   GitHub Action-indpakning af bugbottle-server-validering som tredje kanal.

## Budget
35 kr brugt af 1000 (uændret).
