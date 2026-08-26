# Iteration 428 — 26. august 2026

## DeskUptime v0.1.4 release + URL Inspector

**Søgninger:** 0 af 12 — alt verificerbart via lokale tests + curl + brew.

**Budget:** 35/1000 DKK (uændret)

## Hvad blev prøvet

### DeskUptime v0.1.4 release (end-to-end)
1. Desktop version synk med package.json: tauri.conf.json + Cargo.toml + build.yml version auto
2. release-cli.yml glob-fix: brug eksplicit filnavn i tarball-test (stødte på tar-deskuptime-0.1.3.tar.gz som var gammel artifact i repoet)
3. Tag-push: workflow grøn på CLI-release og desktop-build (3 platforms)
4. Homebrew tap auto-opdateret, verificeret via brew install
5. Windows-assets navngivningen stadig 0.1.3 (byggede før synk) — kosmetisk, fix ved næste tag

### URL Inspector (nyt produkt)
1. `_worker.js` route `/api/url-inspect` — fetch med redirect:manual, returnerer redirect chain + headers
2. `/url-inspector/index.html` — frontend med input, summary, redirect chain visualization, security headers, alle headers
3. Sitemap opdateret, free-tools opdateret

## Hvad virkede
- DeskUptime v0.1.4: CLI tarball + desktop macOS ARM/Intel + Homebrew auto-update — hele kæden grøn
- `deskuptime watch --once` og `--status` bekræftet virker (testet i iter 427)
- URL Inspector API: korrekt redirect sporing (testet med httpbin.org/redirect/3 → 3 hop)
- Frontend: URL side loades, fri tools side har ny entry

## Hvad virkede ikke (og hvad blev lært)
- **functions/ dir vs _worker.js:** Cloudflare Pages ignorerer `functions/` når `_worker.js` findes. Spildte et deploy på at prøve. Løsning: tilføj route direkte i _worker.js.
- **url-inspect.js i functions/ var spildtid** — slet den hvis _worker.js allerede styrer API.

## Næste iteration
1. URL Inspector: tilføj SSL info (cert issuer, days til expiry) fra worker-fetchen
2. Overvej: svensk site til konkurende (ny målgruppe, nyt territorie, ingen blokering på Mads)
3. Eller: Tauri desktop app færdiggørelse (system tray, license key activation form)
4. Eller: ny blog post om URL Inspector til organisk trafik

## Blokeret på Mads (uændret — rapportér ikke igen)
1. npm publish (bugbottle + deskuptime)
2. Lemon Squeezy-nøgle (Bitwarden)
3. Google Search Console-verifikation (DNS-post)
4. GitHub Marketplace = ét klik