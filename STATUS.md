# STATUS — Iteration 324: Metrics-hærdning — alle selftest-tal slettet, nulstillingen er nu ærlig

## Søgedisciplin
0 eksterne søgninger af 12. Hele iterationen var lokal verifikation + KV-rydning.

## Hvad der blev gjort

**Problemet:** Efter søsteragentens 23/8-hændelse (falske waitlist-tal) var vores egne
tællere stadig forurenede. Denne iteration gjorde tallene verificerbare:

**Fund ved direkte KV-inspektion** (wrangler kv key list/get mod VISITS-namespace):
- `wl-count` = 3, men begge to `wl:`-poster var egne roegtests:
  `selftest-297@example.com|book-nis2-for-agencies` og `__selftest@example.com`.
- `scans` (csc-count) = 21 — ALLE fra egne smoke-tests.
- 7 `lic:`-nøgler i KV — alle med order_id/devices som "selftest-*"/"verify-*".
  `licenses_issued`-tælleren fandtes slet ikke (404) men viste alligevel tal via health.
- `ai-ask-count` = 22 — egne tests.

**Rettet:**
1. Alle selftest-nøgler slettet permanent fra produktion-KV:
   2× wl:-emails, wlsrc:-kilde, csc-count, ai-ask-count, 7× lic:, 5× t:*selftest*.
2. `wl-count` nulstillet til 0.
3. Live-verificeret efter rydning: `/api/stats?token=…` → **waitlist=0, sources={},
   licenses=0, ai_asks=0, scans=0**. `/api/health` → scans=0. Tallene er nu ægte.
4. Rengjorde git: fjernede det indlejrede eu-compliance-guides-repo fra index
   (det har sit eget repo på GitHub), tilføjet til .gitignore.

## Ærligt billede efter oprydning (kilde: /api/stats, egen trafik ekskluderet)
- **Waitlist: 0. Licenser: 0. Scans: 0. AI-spørgsmål: 0.**
- Trafik 7 dage: forsiden ~13 uniques; største enkelt-download nis2-for-agencies.epub
  (3 uniques). Ingen konvertering til leads overhovedet.

## Konklusion til Mads
Alt hvad der er bygget indtil videre har **nul rigtige brugere og nul kroner i indtægt**.
Distributionen virker ikke. Nøgleflaskehalse er uændrede: Lemon Squeezy-nøglen
(Bitwarden, `bw status` = unauthenticated) og Obsidian-submission kræver Mads.

## Stadig blokeret (Mads-handlinger)
- **Lemon Squeezy-API-nøgle**: `export LS_API_KEY=… && node lemon-setup.js`.
- **Obsidian submit**: login på community.obsidian.md og submit plugin'et.

## Næste iteration
1. Ny distribution, der ikke afhænger af Mads eller af at folk finder os organisk:
   passiv-mcp er i det officielle MCP-registry — overvej npm-publicering når
   npm-credentials ligger i Bitwarden, samt GitHub-topics/README-SEO på
   mahope/passiv-mcp og mahope/eu-compliance-guides (0 visninger endnu).
2. Hvis LS-nøglen er kommet: gør checkout live (5 min).
3. Mål igen om GitHub-kanalen giver visninger før der bygges mere indhold.

## Budget
35 kr brugt af 1000 (uændret).
