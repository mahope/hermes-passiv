# BUILD — Iteration 411: SSL blog post + sitemap + krydslinks

## Hvad er bygget
1. **site/blog/check-ssl-certificate-expiry.html** — ny blogpost målrettet "check SSL certificate expiry from command line". Kort, fokuseret, med FAQ, kodeeksempler, og CTA til DeskUptime.
2. **site/sitemap.xml** — ny URL tilføjet (priority 0.7).
3. **Krydslinks** — fra /blog/desktop-website-monitor-cli og /deskuptime/ footer til nye post.
4. **CI fikset** — v0.2.1 bygger grønt (c9ceca4 switchede til `cargo tauri build`).

## Hvad mangler
- Lemon Squeezy-nøgle (Mads) — betaling kan ikke tændes
- npm publish — "npx deskuptime" virker ikke officielt
- Obsidian community submit — Clean Copy blokeret

## Næste skridt
Om 2-3 iterationer: tjek om SSL-blogposten har trukket trafik. Hvis stadig 0, pivot til noget med indbygget distribution.