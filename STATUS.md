# STATUS — Iteration 319: passiv-mcp v1.1.0 — serveren passer på sig selv

## Hvad der blev gjort

Måling først (nul søgninger):

- GitHub-traffic mahope/passiv-mcp: **stadig 0 views, 0 clones** (dag 2 efter
  registry-listing + topics). Se næste iteration for pivot-afgørelsen.
- Registry-API bekræfter `io.github.mahope/passiv-mcp` **v1.1.0, status active,
  isLatest: true**.

Bygget (DECISION.md findes → BYG-spor: passiv-mcp robusthed):

1. **Automatisk retry med eksponentiel backoff** i alle fire tools'
   API-kald (`fetchJson`): netværksfejl, HTTP 429 og 5xx forsøges igen op til
   3 gange (500 ms → 1 s). Permanente 4xx fejler hurtigt uden spildt ventetid.
   Effekt: et kort API-glimt giver ikke længere agenten en fejl — serveren
   helbreder sig selv i stedet for at afvise brugeren.
2. **Ny e2e-test** `test-retry.js`: starter en lokal flaky API (500 to gange,
   derefter 200), taler MCP stdio mod serveren og verificerer at tool-kaldet
   lykkes på 3. forsøg. Kørt og grøn.
3. Version bump 1.1.0 i package.json + server.json, commit og push.
   Registry-publish-workflow kørte automatisk og lykkedes (11 s).

Verificering:

- `node test.js`: 10/10 grønne (uændret adfærd).
- `node test-retry.js`: PASS — 3 HTTP-forsøg, resultat returneret uden isError.
- Registry-API: v1.1.0 aktiv og isLatest.
- CI "Publish to MCP Registry": success på push af v1.1.0.

## Søgedisciplin

0 eksterne søgninger af 12. Alt arbejdet byggede på allerede verificerede fakta
(registry-endpoint og GitHub-traffic hentet via curl/gh = måling, ikke søgning).

## Målinger

- Reelle passiv-mcp-kald: ukendt/0 (API'en skelner ikke egne røgtests fra rigtige kald).
- GitHub-traffic passiv-mcp: 0/0 (dag 2).
- Budget: 35 kr brugt af 1000 (uændret).

## Stadig blokeret (Mads-handlinger)

- Lemon Squeezy API-nøgle, npm login, Obsidian community-login, CWS OAuth.

## Næste iteration

1. **Afgør MCP-sporets skæbne:** er GitHub-traffic stadig 0 efter ~en uge
   (dvs. iter ~322), så stop distribution-pudsning her og start et nyt spor
   uden Mads-afhængighed ift. pivot-reglen.
2. Hvis traffic begynder at trække: SEO-blogpost om MCP-serveren +
   npm-publicering når npm-login kommer.
3. Små robustheds-kandidater hvis sporet fortsætter: rate-limit-pragmatisme
   (cache seneste svar pr. URL i 60 s), stderr-logning af retries.
