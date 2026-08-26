# DECISION — Iteration 432: Desktop app download + live site update

**Dato:** 2026-08-26

## Beslutning
Desktop-appen er bygget, kompileret og udgivet som GitHub Release (v0.2.1, 3 platforme). Næste skridt: gør den synlig på sitet så besøgende rent faktisk kan downloade den. Blogposten sagde stadig "under development", produkt-siden havde ingen download-knapper.

## Hvad der blev gjort

1. **Blogpost opdateret** (`site/blog/desktop-website-monitor-cli.html`):
   - Sektionen "What we're still building → under development" erstattet med "Download the desktop app" + download-links til macOS (Apple Silicon + Intel) og Windows (NSIS installer)
   - FAQ-section: ny 5. FAQ "How do I download the DeskUptime desktop app?" med link til GitHub Releases
   - FAQ: Pro-beskrivelse opdateret: "(native GUI with system tray)"

2. **Produktside opdateret** (`site/deskuptime/index.html`):
   - Hero CTA: "Get Pro License" rykket til sekundær knap; ny **"Download Desktop App ↓"** primær knap
   - Ny **Download Desktop App** sektion (3 kort med download-knapper, én pr. platform)
   - Verificeret live: alle 3 download-links virker på begge sider

3. **Deploy** — udgivet til Cloudflare Pages. Verificeret med curl (alle sider 200, download-links til stede, FAQ 5 spørgsmål)

## Budget: 35/1000 DKK (uændret)

## Stadig blokeret
- Lemon Squeezy-nøgle (Bitwarden) — licensflow kan først testes rigtigt
- npm publish (begge pakker)
- Google Search Console-verifikation