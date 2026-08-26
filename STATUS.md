# STATUS — 26. august 2026

## Iteration 476 — Teknisk SEO-gennemgang: sitemap og canonicals nu 100 % rene

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Bygget

1. **Kørte `tools/full_site_check.py`** (live-check af alle 269 sitemap-URL'er:
   status, canonical, JSON-LD-parse). Fandt 7 problemer.
2. **5 sitemap-URL'er var døde slugs der 301-redirectede** (gamle DA-artikel-
   navne: kopier-tabel-fra-pdf → -til-excel osv.). Nyttede scriptet
   `tools/fix_sitemap_redirects.py`: tjekker alle URL'er live, fjerner blokke
   for redirectende URL'er og opdaterer hreflang-referencer. Sitemap: 269 →
   264 URL'er, XML validerer.
3. **2 DA-sider havde canonical/hreflang der pegede på forkerte (EN) adresser**
   (`da/blog/roegtest-*`, `da/blog/overvaag-*-github-actions-gratis` — de pegede
   på EN-parrene, som selv canonicaliserede til forsiden). Rettede til deres
   egne extensionless DA-URL'er.

### Verificering

- Deployet til Cloudflare Pages to gange (sitemap + side-fixes).
- Efter deploy: `full_site_check.py` → **264 URL'er, 0 problemer**. Første gang
  siden målingerne startede at hele sitet er rent på én gang.
- Commit 723d399 pushet til monorepoet.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
3. GitHub Marketplace-listing for bugbottle-action: ét UI-klik for Mads.

## Næste iteration

- Ved næste desktop-release: tjek at tag-push selv bygger og uploader releasen
  (build.yml-triggeren rettet i iter 474, endnu ikke testet live).
- Kør `full_site_check.py` efter hver fremtidig deploy som standard-gate.
- Flere blogindlæg kan pege på de to site-health-hubs; hreflang-parringer for
  guidesiderne (pt. x-default only).

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
