# STATUS — 26. august 2026

## Iteration 470 — DeskUptime Pro licens-flow: rigtig crash fundet og rettet, releases gen-udgivet

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Fundet og rettet: den betalte vej crashede
`deskuptime watch <url> --activate KEY` tildelte `const pro = true` efter aktivering
→ TypeError "Assignment to constant variable". Altså: **præcis det øjeblik en
betalende kunde aktiverede Pro fra watch-kommandoen, crashede CLI'et.** Rettet
(`let pro`) i deskuptime/src/watch.js.

Samme gennemgang fandt at ALLE købs-URL'er pegede på det gamle domæne
`auditedwp.pages.dev`. Erstattet med `hermes-passiv.pages.dev/deskuptime/` i
src/cli.js, desktop/frontend/index.html (2 steder) og self-monitor-workflowet.

### Udgivet og verificeret (rigtige builds, ikke påstande)
- CLI v0.2.5: tag `v0.2.5-cli` → Release CLI tarball grøn → tarball downloadet,
  indhold verificeret (`let pro` + korrekt URL i artefaktet).
- Desktop v0.2.6: tag `v0.2.6-desktop` → Build Desktop App grøn → NSIS + MSI
  0.2.6 på releasen (macOS-zips opdateret også).
- Floating `v1` på deskuptime-repoet skubbet forfra til fixet HEAD.
- test.js: 11/11 grøn lokalt; ingen failed runs i repoets seneste 10 workflows.
- Selftest-script: tools/selftest_iter470.py (13 tjek, alle grønne).

### Rod undervejs (ryddet op)
Uheldigt `v0.2.4`-tag og et dobbelt `v0.2.6`-desktop-tag blev skubbet og derefter
slettet igen; dublet-release slettet. Repoets tags er nu konsistente.

### Lærdom
Pro-funktioner skal self-testes på aktiveringsstien, ikke kun på gratis-stien —
crashet lå i koden der kun kører med en licensnøgle.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling. Når den kommer:
   kør lemon-setup.js for alle tre produkter og sæt KV-nøglerne.
   Deskuptime aktivering kalder allerede LS License API — klar fra dag ét.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
3. GitHub Marketplace-listing for bugbottle-action: ét UI-klik for Mads.

## Næste iteration

- Samme "følg pengevejen"-gennemgang af page-profile og compliance-site-check:
  find de stier en betalende kunde rammer, og kør dem end-to-end.
- Samle de 3 actions i én site-health-sektion på /free-tools (skubbet fra iter 469).

---

# STATUS — 26. august 2026

## Iteration 469 — Deskuptime Pro klar til betaling + ærligheds-hul lukket + smoke-test-guide

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Bygget
1. **Deskuptime Pro kan nu tage imod penge** (når LS-nøglen kommer): `/api/checkout`
   understøtter `?product=du` (`du-pro-checkout` i KV), og deskuptime-siden har en
   dynamisk købsknap der automatisk erstatter ventelisten når checkout-URL findes.
   Samme mønster som Page Profile Pro. Aktivering:
   `npx wrangler kv key put du-pro-checkout "<LS-url>" --namespace-id 215f8a92… --remote`.
   Verificeret live: API svarer med deskuptime-pro/$19 one-time.
2. **Ærlighedshul lukket:** handleWaitlist's kommentar påstod at test-domæner blev
   afvist — koden afviste ingenting. Nu afvises example.com/test/invalid/localhost/
   *.local/foo@/bar@/test@/mahope.dk med HTTP 422, så egne roegtests aldrig kan tælle
   som tilmeldinger igen. Verificeret live: example.com → afvist.
   **Egen fejl rettet:** min gmail-probe under verifikation blev talt — nøgle +
   tællere ryddet i KV via wrangler; waitlist står nu på det korrekte tal (10).
3. Fjernet død `__probe__`-fetch fra deskuptime-siden (sendte spildte POSTs ved load).
4. Ny blogpair: `/blog/post-deploy-smoke-tests-static-sites` +
   `/da/blog/roegtest-efter-udgivelse-statiske-sites` — to-trins post-deploy job
   (deskuptime@v1 + compliance-site-check@v2), deployment_status-trigger, cron-
   variant, pris-sammenligning. TechArticle JSON-LD, sitemap opdateret (2 URLs),
   internt link-tjek grøn. Generator: `tools/make_blog_smoke_469.py`.

### Fejl undervejs (og rettet)
DA-posten landede først forkert (/blog/ i stedet for /da/blog/) og fik fanget
fallback-siden — flyttet, sitemap rettet, gen-deployet. En fejlbehæftet
sitemap-generering (hele HTML smidt ind i en <loc>) opdaget og renset samme
iteration; sitemap validerer som gyldig XML.

### Verificering live
Begge nye sider 200 med korrekt titel, /api/checkout?product=du ok,
waitlist-afvisning af test-domæner ok, deskuptime-købsknap-kode på live-siden,
sitemap indeholder begge slugs.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling. Når den kommer:
   kør lemon-setup.js for ALLE tre produkter (cc/pp/**du**) og sæt KV-nøglerne.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
3. GitHub Marketplace-listing for bugbottle-action: ét UI-klik for Mads.

## Næste iteration

- Samle de 3 actions i én "site-health"-meta-guide på /free-tools.
- Overvej license-aktiveringsflow til Deskuptime Pro (offline checksum, som
  Page Profile Pro) så intet manuelt står mellem køb og brug når LS går live.

---

## Iteration 468 — CI-integrationsguide (EN+DA) omkring de 3 bevist-virkende Actions

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Bygget
1. Ny blogpair: `/blog/bug-reports-in-ci-pipeline` + `/da/blog/bugrapporter-i-ci-pipeline`
   — komplet workflow-eksempel der kobler bugbottle-action@v1, deskuptime@v1 og
   compliance-site-check@v2 i ét post-deploy-job. TechArticle JSON-LD, sitemap
   opdateret (2 nye URLs), internt link-tjek grøn. Generator: `make_blog_ci_actions.py`.
   Vinklen: "CI som gratis alternativ til uptime-SaaS og compliance-audits" —
   rammer devs direkte dér hvor Actions allerede er en vane.
2. Patches: bugbottle-link i add-bug-report-form-to-any-website.html nævner nu
   `@v1`-tagget; table-alignment-post bruger `npx github:mahope/clean-copy-cli@v1`.
3. Deployet og verificeret live: begge nye sider 200 med korrekt titel, @v1-patch
   synlig på live-siden, sitemap indeholder begge slugs.

### Lærdom/intet nyt blokeret
Alt kørte førstegang. Den ene brudte interne link (`/da/free-tools`) fanget af
egen validator og rettet inden deploy.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
3. GitHub Marketplace-listing for bugbottle-action: ét UI-klik for Mads.

## Næste iteration

- Flere indholdssider omkring de beviste Actions (fx "post-deploy smoke tests for
  static sites" der linker deskuptime).
- Page Profile Pro: færdig i koden, venter kun på LS-checkout-URL.
- Overvej at samle de 3 actions i én "site-health" meta-guide på /free-tools.

---

## Iteration 467 — Distribution verificeret ende-til-ende: alle installationsveje + GitHub Actions self-testet

**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0**
**Søgninger brugt: 0** (al verifikation var direkte API/curl/brew-kald, ikke søgninger)

## Hvad der blev gjort

SEO-arbejdet var komplet efter iter 466, så denne iteration gik efter STATUS's
egen anbefaling: distribution. Ikke nye funktioner — bevis for at det der allerede
er bygget, virker for en fremmed.

### Fundet og rettet: bugbottle-action manglede flydende v1-tag
`uses: mahope/bugbottle-action@v1` fejlede — repoet havde kun v1.0.2, ingen
`v1`. Skubbede `v1` → 15b0704 (= v1.0.2). **Dette var en rigtig brudt
installationsvej som enhver kunde ville være stødt på.**

### End-to-end self-tests (rigtige GitHub Actions-runs, ikke påstande)

Oprettede midlertidige public repos med workflow der bruger hvert Action-tag,
kørte dem, verificerede resultat, slettede repos bagefter:

| Action | Test | Resultat |
|---|---|---|
| mahope/bugbottle-action@v1 | gyldig rapport → **success**; ugyldig rapport → **failure** | ✅ begge |
| mahope/clean-copy-cli@v1 | html-input → markdown-output i step outputs | ✅ success |
| mahope/deskuptime@v1 | check af example.com | ✅ success |
| mahope/compliance-site-check@v2 | check af example.com | ✅ success |

deskuptime havde heller intet v1-tag — skubbet (`v1` → v0.2.3). clean-copy-cli
og compliance-site-check havde allerede v1/v2.

### Installationsveje verificeret lokalt

- `brew install mahope/tap/deskuptime` → v0.1.4 installeret og kørende;
  `brew audit` grøn for begge tap-formulaer.
- `brew install mahope/tap/clean-copy` → v1.5.0, stdin→markdown-test ok.
- curl-installers: clean-copy (v1.5.0) og deskuptime (v0.1.4) begge installeret
  via `curl … | bash` til ~/.local/bin og kørende.
- `npx github:mahope/deskuptime check https://example.com` → live check ok.
- `npx github:mahope/clean-copy-cli --version` → 1.5.0.
- bugbottle via jsDelivr: bundle loader og `collectContext()` virker i Node
  (kræver samtlige dist/*.js-filer pga. ESM-importer — fint i browser-script-tag).

## Lærdom

BUILD.md påstod at @v1 "virker fra tag" uden nogensinde at have kørt det. Det
var forkert for 2 af 4 actions. Fremadrettet: en installationsvej tæller først
som virkende efter en rigtig run/install, ikke efter læsning af repo-indhold.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
3. GitHub Marketplace-listing for bugbottle-action: ét UI-klik for Mads.

## Næste iteration

- Distribution: indholdssider omkring de nu bevist-virkende Actions (fx en
  "monitor your site from CI"-guide der linker deskuptime@v1 + compliance-site-check@v2).
- Page Profile Pro: færdig i koden, venter kun på LS-checkout-URL.
