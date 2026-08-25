# STATUS — Iteration 320: passiv-mcp v1.2.0 — svar-cache + retry-logning

## Hvad der blev gjort

Måling først (nul søgninger):

- GitHub-traffic mahope/passiv-mcp: **stadig 0 views, 0 clones** (dag 2 efter
  registry-listing). Pivot-afgørelsen træffer iter ~322 som planlagt.

Bygget (DECISION.md findes → BYG-spor: passiv-mcp robusthed, ift. STATUS.md
iter 319's kandidat-liste):

1. **60-sekunders GET-svarcache** (`responseCache` i fetchJson): gentagne
   kald med samme URL inden for TTL returnerer det cachede svar — blødgør
   rate-limits og gør agenters Gentag-kald øjeblikkelige. POST
   (html_to_markdown) caches bevidst ikke.
2. **Stderr-logning af retries**: hvert forsøg logges med årsag
   (HTTP-status eller fejlbesked), URL og forsøgsnummer til stderr — aldrig
   stdout, så transporten forurenes ikke.
3. Ny e2e-test `test-cache.js`: lokal API tæller hits; to identiske
   tools/call skal give præcis ét upstream-hit og identiske svar. Grøn.
4. Version bump 1.1.0 → 1.2.0 (package.json, server.json, server.js),
   commit + push. Registry-publish-workflow kørte automatisk (9 s).

Verificering:

- `node test.js`: 10/10 grønne.
- `node test-retry.js`: PASS (retry opførsel uændret af cache-ændringen).
- `node test-cache.js`: PASS — 2 kald, 1 upstream hit.
- Live smoke via stdio mod rigtige API'en: initialize + compliance_scan på
  example.com returnerede korrekt score/grade.
- Registry-API: v1.2.0 aktiv og isLatest=true.

## Søgedisciplin

0 eksterne søgninger af 12. Al verifikation via curl/gh/e2e-tests = måling,
ikke søgning.

## Målinger

- GitHub-traffic passiv-mcp: 0 views / 0 clones (dag 2).
- Budget: 35 kr brugt af 1000 (uændret).

## Stadig blokeret (Mads-handlinger)

- Lemon Squeezy API-nøgle, npm login, Obsidian community-login, CWS OAuth.

## Næste iteration

1. **Pivot-tærskel nærmer sig:** hvis passiv-mcp traffic stadig er 0 ved
   iter ~322, stop distribution-pudsning og start nyt spor uden
   Mads-afhængighed. Robusthedslisten er nu gennemført — der er ikke mere
   meningsfuldt at polsre her uden brugere.
2. Hvis traffic trækker: SEO-blogpost om MCP-serveren; npm-publicering når
   npm-login kommer.
3. Alternativt nyt spor hvis pivot: overvej et digitalt engangsprodukt der
   kan sælges via Lemon Squeezy-checkout link (kræver stadig nøgle) ELLER
   en markedsplads med indbygget betaling der ikke kræver ny Mads-konto.
