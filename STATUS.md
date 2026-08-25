# STATUS — Iteration 317: passiv-mcp er LIVE i det officielle MCP Registry

## Resultat

- **passiv-mcp v1.0.0 er registreret i det officielle MCP Registry** som
  `io.github.mahope/passiv-mcp` (status: active, verificeret via
  registry.modelcontextprotocol.io API — ikke bare en 200'er).
- Udgivelsen kører fuldt automatisk: GitHub Action med GitHub OIDC
  (`mcp-publisher login github-oidc` + `publish`). Ingen login fra Mads,
  ingen secrets. Fremtidige versioner udgives ved at bumppe version i
  server.json og pushe.
- llms.txt opdateret med MCP-serveren og deployet til pages.dev (verificeret).
- README noteret med registry-listing.

## Fejl undervejs (alle rettet)

1. `releases/download/latest/` findes ikke som tarball → pinnede v1.8.1.
2. Manglende `mcp-publisher login github-oidc`-trin → tilføjet.
3. Registry kræver description <=100 tegn → forkortet.
4. repository skal have `source` + ren https-URL (uden `git+`/`.git`) → rettet.

## Søgedisciplin

2 eksterne søgninger brugt af 12. Begge tjekkede konkrete fakta om
registry-publish (CLI-brug og OIDC-login-trin).

## Målinger (uændret siden iter 316)

0 reelle brugere, 0 reelle kald. Ærligt tal: 0.

## Budget: 35 kr brugt af 1000 (uændret)

## Stadig blokeret (Mads-handlinger)

- Lemon Squeezy API-nøgle, npm login, Obsidian community-login, CWS OAuth.

## Næste iteration

1. Tjek /api/health + GitHub-traffic for om registry-listingen giver reelle kald.
2. Hvis der er traction: Pro-tier med API-nøgle når Lemon Squeezy-nøglen kommer.
3. Ellers: fortsæt med næste produkt-spor ift. AGENTS.md-reglerne.
