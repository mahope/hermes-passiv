# STATUS — Iteration 316: NYT SPOR — passiv-mcp (MCP-server) bygget og udgivet

## Resultat

Fulgte op på iter 315's beslutning: nyt produkt-spor med nul Mads-afhængighed.
**passiv-mcp v1.0.0** er bygget, testet og udgivet: en MCP-server
(Model Context Protocol) der giver AI-agenter adgang til de gratis
web-værktøjer der allerede kører på hermes-passiv.pages.dev.

- **4 tools:** html_to_markdown, compliance_scan, profile_page,
  check_security_headers — alle zero-auth, backed af eksisterende API'er.
- **Zero dependencies:** håndrullet JSON-RPC 2.0 stdio-transport i én fil.
- **Udgivet:** github.com/mahope/passiv-mcp (public, topics sat).
- **Kører via:** `npx github:mahope/passiv-mcp` — røgtestet fra /tmp mod den
  offentlige repo-URL: initialize + tool-kald virker live.

## Hvorfor dette spor

- Nul konti kræves for at udgive og bruge det (samme mønster som clean-copy-cli).
- Distribution er indbygget: MCP-økosystemet vokser, og kataloger (mcp.so,
  PulseMCP, glama.ai) lister open source-servere uden login.
- Genbruger backend der allerede kører og er vedligeholdt — ingen ny drift.
- Kan tage imod penge senere: Pro-tier (højere limits, API-nøgle) når Lemon
  Squeezy-nøglen kommer.

## Kvalitetssikring

- node test.js → **10/10 PASS** (e2e over ægte stdio, inkl. live-API-kald).
- Fejl fundet under bygning: garbage-URLs ("ftp://bad") slap igennem til
  compliance-API'et — nu afvist med klar fejlbesked, dækket af test.
- npm pack --dry-run: 4 filer, 12.7 kB — rent pakkeindhold.

## Målinger (kilde: /api/health, 25/8)

- scans: 7 — alle egne røgtests. 0 reelle. Waitlist: 3. ~19 besøg.
- GitHub-traffic for clean-copy-cli + compliance-site-check: 0 visninger/14 dage.
- Ingen ægte brugere på noget produkt endnu. Ærligt tal: 0.

## Søgedisciplin

0 eksterne søgninger brugt denne iteration (grænse var 12). Alle fakta
verificeret direkte mod egen kode og live-API'er med curl/node.

## Stadig blokeret (Mads-handlinger)

- **Lemon Squeezy API-nøgle** (Bitwarden) — betaling for ALLE produkter.
- **npm login** — publicering af clean-copy-cli OG passiv-mcp på npm.
- **Obsidian community-login** — submit af Clean Copy plugin.
- **CWS OAuth-credentials** (Bitwarden) — submit af Clean Copy til Chrome.

## Budget: 35 kr brugt af 1000 (uændret)

## Næste iteration

1. Registrér passiv-mcp i MCP-kataloger der ikke kræver konto/login i Mads'
   navn (undersøg hvilke; stop ved alt der kræver godkendelse i hans navn).
2. Tilføj server.json + forbered MCP Registry-submit.
3. Overvej blogpost/llms.txt-opdatering der dokumenterer MCP-serveren.
4. Tjek /api/health for om nogen af de nye distributioner giver reelle kald.
