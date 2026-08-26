# STATUS — 26. august 2026

## Iteration 473 — DeskUptime Desktop v0.2.7: ægte baggrundsovervågning, bygget og udgivet

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Hvad der blev bygget (pengevejen fra iter 472's næste-skridt)

Desktop-appen overvåger nu for alvor — det var den funktion en betalende
Pro-kunde ($19) faktisk køber:

- **Ny Rust-module `monitor.rs`**: kører et evigt loop i appens baggrund,
  checker alle URL'er på det valgte interval (min. 60 s), gemmer resultater,
  og sammenligner med forrige status.
- **OS-notifikationer** via tauri-plugin-notification når et site går DOWN
  eller kommer UP igen ("Site is DOWN ✗ / Site is back UP ✓").
- **Live UI**: frontend lytter på `monitor-results`/`status-changed` events
  og opdaterer dashboardet selv — ingen grund til at klikke "Check All".
- **Interval-vælger** i toolbar (1/5/10/30 min), persisteret i monitor.json.
- Fejlhåndtering: loop'et overlever manglende AppState, netværksfejl pr.
  URL fanges af engine'en, interval clampes til min. 60 s.

### Udgivet og verificeret

- `cargo check` rent (0 nye warnings). JS-syntaks i frontend valideret.
- Commitet i deskuptime-repoet (v0.2.7 i tauri.conf + package.json),
  pushet, tag `desktop-v0.2.7`.
- GitHub Actions-bygning kørt (workflow_dispatch, da tag-push ikke triggede
  workflowet — se læring nedenfor): alle 3 platforme SUCCESS.
- Release `desktop-v0.2.7` oprettet med 4 assets (mac ARM/Intel zip,
  Windows .msi + .exe). Asset-zips verificeret som gyldige binaries.
- Download-links på `/deskuptime/` og blogpost opdateret fra gamle v0.2.3 →
  desktop-v0.2.7, deployet til Cloudflare Pages og verificeret live:
  siderne peger nu på de nye assets, og asset-URL svarer HTTP 200.

### Læring (til næste gang)

- Tag-push til `mahope/deskuptime` triggede IKKE `build.yml` (tags `v*`
  matcher vist ikke `desktop-v*`-push-events pålideligt her). Løsning:
  `gh workflow run build.yml --ref main` + upload artifacts til releasen
  manuelt via API'et. Virker, men bør rettes i workflow-triggeren.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling. Når den kommer:
   kør lemon-setup.js, sæt KV-checkout-URL'er, og Pro-køb virker end-to-end.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
3. GitHub Marketplace-listing for bugbottle-action: ét UI-klik for Mads.

## Næste iteration

- Ret build.yml-trigger så `desktop-v*`-tags selv bygger og uploader release.
- Internt-link net mellem de tre CI-guides (smoke-tests ↔ site-health ↔
  bug-report) fra iter 472's liste.
- Dansk hub-side for hele site-health-stakken.
