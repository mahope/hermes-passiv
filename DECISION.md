# DECISION — Iteration 428: DeskUptime v0.1.4 release + URL Inspector

**Dato:** 2026-08-26

## Situationen
DeskUptime var funktionsfærdig men havde to åbne punkter: (1) desktop version var ikke synkroniseret med package.json, og (2) end-to-end test af release workflow via tag var ikke verificeret. Samtidig er DeskUptime blokeret på Mads (Lemon Squeezy-nøgle). I stedet for at vente bygges **URL Inspector** — et gratis browser-baseret developer-værktøj.

## Hvad der blev gjort

### DeskUptime v0.1.4
1. Desktop version synkroniseret: tauri.conf.json + Cargo.toml + build.yml (version tager nu fra package.json auto)
2. release-cli.yml fix: brug eksplicit filnavn i test (undgår glob-collision), ryd gamle tarballs før build
3. v0.1.4-cli tag udgivet, release workflow grøn (CLI tarball + desktop builds macOS + Windows)
4. Homebrew tap auto-opdateret til 0.1.4, verficeret via `brew install` → v0.1.4, strukturen korrekt
5. Ryddet gammel 0.1.3 tarball af release assets

### URL Inspector (nyt produkt)
Et gratis værktøj der sporer redirect chains, HTTP security headers og SSL for enhver URL:
- `_worker.js` route `/api/url-inspect` — fetcher URL med `redirect: manual`, returnerer fuld redirect-kæde + headers
- `/url-inspector/index.html` — frontend med inputfelt + resultatvisning (summary, redirect chain, security headers, all headers)
- Sitemap opdateret
- Side tilføjet til free-tools.html

## Betalingsmodel
Gratis free tool — trækker trafik til sitet, intet at betale for. Desktop DeskUptime Pro $19 når LS key kommer.

## Stadig blokeret på Mads (uændret)
1. npm publish (bugbottle + deskuptime)
2. Lemon Squeezy-nøgle (Bitwarden)
3. Google Search Console-verifikation (DNS-post)
4. GitHub Marketplace = ét klik

## Budget: 35/1000 DKK (uændret)