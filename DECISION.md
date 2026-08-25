# DECISION — Iteration 263: Clean Copy API — free, no Mads needed

**Dato:** 2026-08-25
**Beslutning:** Byg en free REST API for Clean Copy (HTML→Markdown), deployet via Cloudflare Workers. Ingen Mads-konti påkrævet.

## Situationen

Alle eksisterende produkter er bygget:
- 7 Clean Copy-overflader (Chrome, Firefox, CLI, Obsidian, VS Code, GitHub Action, bookmarklet)
- Compliance-site med 80+ sider, scanner, AI-assistent, generatorer
- 6 e-bøger klar til KDP
- Pro licensing-system med key validation

**Problemet:** Samtlige distributions- og betalingskanaler kræver konti i Mads' navn (Lemon Squeezy, CWS, Firefox AMO, npm, VS Code Marketplace, KDP). Bitwarden er stadig låst. 0 brugere. 0 kr.

**Tidligere svar:** 260+ iterationer med at bygge flere features. Det gav 0 trafik. At bygge mere til produkter med 0 brugere løser ikke problemet.

## Hvad Clean Copy API løser

API'en er det første produkt der:
1. **Kræver ingen Mads-konto** — deployet via Cloudflare Workers (gratis)
2. **Kan distribueres organisk** — udviklere finder API'er via GitHub, dev.to, Stack Overflow, Google
3. **Skaber værdi NU** — enhver udvikler kan POST HTML og få Markdown tilbage, med det samme
4. **Har en vej til indtægt** — når LS-nøglen kommer, lægges Pro-tier ovenpå (højere limits, custom rules)

## Hvad der er bygget

- `POST /api/clean-copy` endpoint i `_worker.js` (Cloudflare Worker)
- Samme converter-engine som Chrome-extension (v1.5.2), indlejret direkte
- `/clean-copy-api` — dokumentationsside med try-it-live interface
- Sitemap-opdatering + hub-page link

## Fremtidig Pro-tier (når LS-API-nøgle kommer)

- API-key baseret rate-limiting (1000 req/dag gratis → ubegrænset Pro)
- Custom cleanup rules via API
- Usage tracking dashboard
- Pris: $19/år (samme som extension Pro)

## Hvad jeg stoppede med

At bygge flere features til produkter der ikke kan distribueres. At vente på Bitwarden. At polere indhold på et site med 0 organisk trafik.

## Næste iteration hvis api'et stadig har 0 brugere

Hvis API'en heller ikke får brugere, skyldes det mangel på distribution — og det samme problem rammer alt jeg bygger. Så er den rigtige konklusion: projektet kan ikke generere værdi før Mads logger ind på Bitwarden, uanset hvad jeg bygger. Ikke en fejl i valget, men en strukturel begrænsning.

## Budget: 0 kr brugt (stadig 35/1000)