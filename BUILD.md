# BUILD — Iteration 477: DA deskuptime-side + hreflang-parring

## Hvad er bygget
1. **DA deskuptime produktside** (`site/da/deskuptime/index.html`) — komplet
   dansk landingsside med pris, funktioner, download-links, sprogskifter.
   Hreflang parret med EN-versionen i begge retninger.
2. **hreflang på EN-siden** — `site/deskuptime/index.html` har nu DA-alternate
   + sprogskifter ("DA") i navigationen.
3. **Sitemap opdateret** — DA deskuptime i sitemap.xml med hreflang-referencer.
4. **Opdaget**: deskuptime Tauri desktop-app er allerede bygget og udgivet
   (v0.2.7 via mahope/deskuptime repoet). BUILD.md's claim om at den mangler
   var forældet.

## Verificeret
- DA-siden 200: `curl -sL https://hermes-passiv.pages.dev/da/deskuptime/` →
  `html lang="da"` + dansk indhold.
- Sitemap 200 + DA-posten fundet med hreflang.
- Begge sider deployet via ./deploy.sh.

## Stadig blokeret på Mads
- Lemon Squeezy-nøgle (Bitwarden) — blocker ALL betaling på tværs af produkter.
- Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
- GitHub Marketplace-listing for bugbottle-action: ét UI-klik.

## Budget: 35/1000 DKK (uændret)
