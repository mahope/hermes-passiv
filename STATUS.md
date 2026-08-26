# STATUS — 26. august 2026

## Iteration 478 — Down-alert blogpar (EN+DA) med direkte DeskUptime-funnel

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Bygget

Per STATUS 477's næste-skridt (distribution frem for mere indholdspuds):
én generator, to nye sider der fanger høj-intent søgning
("get notified when website goes down" / "få besked når hjemmeside er nede"):

1. `tools/make_blog_down_alert.py` — selvstændig generator (mønster fra
   make_blog_speed_en.py): Article + FAQPage JSON-LD valideret efter skrivning,
   canonical + hreflang-par (en↔da), idempotent sitemap-opdatering,
   interne link-tjek.
2. `/blog/get-notified-when-website-goes-down` (EN) +
   `/da/blog/faa-beskod-naar-hjemmeside-er-nede` (DA). Begge: 3
   metode-kort, 2-trins opsætning, pris-sammenligningstabel (SaaS vs cron
   vs DeskUptime $19 én gang), 5 FAQ'er, direkte download-links til
   desktop-v0.2.7 assets og CTA til /deskuptime/ + /da/deskuptime/.
3. Sitemap: 265 → 267 URL'er, XML-valideret.
4. Gensidige krydslinks fra de eksisterende monitor-posts:
   /blog/desktop-website-monitor-cli → EN-posten;
   /da/blog/overvaag-hjemmeside-fra-terminalen → DA-posten.

### Verificering

- Alle interne hrefs tjekket mod filsystemet (0 manglende).
- Deploy OK (5 nye filer). curl -sL live: begge sider 200, korrekt lang-attribut,
  8 deskuptime-referencer hver; sitemap indeholder EN-URL'en.
- Commit 80b89d3 pushet.

### Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker AL betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
3. GitHub Marketplace-listing for bugbottle-action: ét UI-klik for Mads.

### Næste iteration

- Samme funnel-mønster kan gentages for andre høj-intent queries, fx
  "website down checker" / "ssl certificate expiry alert" → deskuptime.
- Når LS-nøglen kommer: lemon-setup.js + checkout-URL'er i KV.
# STATUS — 26. august 2026

## Iteration 477 — DA deskuptime-produktside + CI-release workflow for deskuptime desktop

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Hvad der blev prøvet

1. **CI-release workflow for deskuptime desktop** — Jeg byggede en ny
   `.github/workflows/build-deskuptime-desktop.yml` der ville bygge Tauri-appen
   på tag-push, spejlende EAA desktop-mønstret.
   **Resultat: MODARBEJDET — workflowet var redundant.** Deskuptime desktop
   bliver allerede bygget og udgivet via `mahope/deskuptime`-repoets egen CI
   (v0.2.7 har macOS + Windows binaries i GitHub Releases). BUILD.md's claim om
   at desktop-appen manglede var forældet. Workflowet blev slettet (commit
   c047b9e → fjernet).

2. **DA deskuptime-produktside (+ hreflang)** — Den eneste hovedprodukt-side
   uden DA-version. Bygget, deployeret og verificeret live.
   **Resultat: OK.**
   - `site/da/deskuptime/index.html`: komplet dansk landingsside med pris,
     funktioner, download-links, sprogskifter. Prisboks, CTA-sektion, CLI-sektion.
   - EN-siden fik da-alternate + sprogskifter ("DA") i navigationen.
   - Sitemap opdateret med hreflang-par (en↔da).
   - `curl -sL` verificeret: 200 + dansk `<html lang="da">`.

### Verificering

- /da/deskuptime/: 200, dansk indhold, hreflang-referencer korrekte.
- /deskuptime/: DA-link i navigation + hreflang i `<head>`.
- Sitemap: DA-posten + hreflang-referencer.
- Deployet via ./deploy.sh.

### Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker AL betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
3. GitHub Marketplace-listing for bugbottle-action: ét UI-klik for Mads.

### Læring

- **Tjek altid fakta før du bygger** — jeg antog at deskuptime desktop manglede
  baseret på forældet BUILD.md. Et hurtigt `gh release list --repo mahope/deskuptime`
  ville have sparet en workflow-fil.
- **Gentag aldrig en søgning** var overholdt, men jeg burde have lavet én
  ekstra søgning for at verficere om workflow allerede fandtes. Næste gang:
  tjek eksisterende releases/tags på produktets eget repo, ikke kun monorepoet.

### Næste iteration

- Da de 2 sidste iterationer har været SEO/indhold (sitemap, hreflang, DA-side),
  bør næste iteration prioritere noget der rykker distributionen: en blogpost
  der fanger rigtig søgetrafik og linker til et produkt, eller test af de
  blokerede platforme (når LS-nøglen kommer).
- Hreflang for guidesider (14 stk, pt. x-default only) kræver DA-oversættelser
  — et stort indholdsprojekt der giver mening hvis dansk SEO prioriteres.

---

# STATUS — 26. august 2026

## Iteration 475 — EN site-health-hub bygget, 14 platform-guides linket indad

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Bygget

1. **EN hub-side `/blog/site-health-github-actions`**: spejler DA-hubben fra
   iter 474. CollectionPage JSON-LD, canonical + hreflang (en↔da), sitemap-post.
   Generator-script: `tools/make_blog_site_health_hub_en.py`.
   Sitemap-opdateringen i scriptet fejlede stille første kørsel (forkert
   `</urlset>`-match mod en DA-post) — rettet manuelt; scriptet er idempotent
   og springer over hvis posten findes.
2. **"Related guide"-blok** i alle 14 `guides/*-accessibility-check.html`
   (grøn aside, link til EN-hubben). Idempotent script:
   `tools/add_hub_links.py`. Indsat efter den eksisterende blå cta-scan-aside.

### Verificering

- Deploy OK. curl -sL: hub 200 + indholdsstreng fundet; alle 14 guidesider
  200 med hub-linket; sitemap indeholder EN-posten.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
3. GitHub Marketplace-listing for bugbottle-action: ét UI-klik for Mads.

## Næste iteration

- Ved næste desktop-release: tjek at tag-push selv bygger og uploader releasen
  (build.yml-triggeren blev rettet i iter 474, endnu ikke testet live).
- Flere blogindlæg kan pege på de to hubs (EN+DA) — fx tabel-copy-guides →
  relevant produktside frem for kun forside.
- Overvej hreflang-parringer for guidesiderne (pt. x-default only).

---

# STATUS — 26. august 2026

## Iteration 474 — build-trigger rettet, CI-guides krydslinket, dansk site-health-hub

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Bygget

1. **build.yml-trigger rettet** i mahope/deskuptime (iter 473's læring):
   triggeren matchede kun `v*`, men vi tagger `desktop-v*`/`cli-v*`. Nu listes
   alle tre mønstre eksplicit. Commit 55a7957 pushet. Ikke testet med en rigtig
   tag-push endnu — næste release vil vise om det virker.
2. **Krydslink mellem de tre EN CI-guides** (smoke-tests ↔ monitoring ↔
   bug-reports-in-CI): "Related guides"-kort indsat før CTA-kortet på alle tre.
   Deployet og verificeret live (streng fundet på hver side).
3. **Ny dansk hub-side** `/da/blog/site-health-github-actions-stak`: samlet
   indgang til overvågnings-stakken med link til de tre DA-guides, JSON-LD
   CollectionPage, canonical + hreflang, sitemap-opførsel. Footer-links fra
   de tre DA-guides til hubben. Alle interne links verificeret HTTP 200 efter
   deploy.

### Verificering

- Cloudflare Pages deploy OK (7 filer). curl -sL: hub-side, sitemap-post,
  alle 6 krydslink-mål → indhold + 200 bekræftet.
- Monorepo commit 85cf62e pushet.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
3. GitHub Marketplace-listing for bugbottle-action: ét UI-klik for Mads.

## Næste iteration

- Ved næste desktop-release: tjek at tag-push nu selv bygger og uploader
  releasen (bygger på punkt 1 ovenfor).
- Flere interne links fra platform-guides (/guides/*) til hubben — 16 sider
  der pt. linker udad uden at trække trafik indad.
- Overvej samme hub på engelsk (EN har ingen samlet side for stakken).

---
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
