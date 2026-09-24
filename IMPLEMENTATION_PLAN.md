# IMPLEMENTATION_PLAN

## Status

- `ITERATION_ID`: `research-2026-09-25`
- `STATE`: `FÆRDIG`
- `ACTIVE_TASK`: `INGEN`
- `NEXT_TASK`: `1 — Fjern Lemon Squeezy-ruten helt`
- `TASK_ATTEMPTS`: `1: 0/2`
- `LAST_BRANCH`: `ceo/initial-research-plan`
- `PLAN_COMMIT`: `10c5908`
- `BASELINE`: `main@b3a42cf`
- `RESULT`: Research og prioritering er færdig; produktkode er ikke ændret.
- `GATE`: `GRØN — 41/41 Stripe-tests, 0 inline-JS-problemer; build/SEO grøn`
- **Reelle, dokumenterede salg i repoet:** 0. Det er ikke bevis for 0 salg; kun dokumentation, der kan tælles.
- **Blokerede opgaver:** ingen.
- `dist/` må regenereres af `build_sites.py`, men må ikke redigeres manuelt eller committes.
- `../auditedwp` er en ekstern buildkilde og må ikke ændres.
- Secrets, `.env*`, produktionsdatabaser og udadvendte writes er forbudte. Eneste eksplicitte undtagelse er den kontraktstyrede merge/push til `main` i dette repo, som må deploye de fire sites; ingen anden extern handling må udføres.

### Kanonisk state-protokol

Før en ny iteration ændrer kode skal den sætte `ACTIVE_TASK` til opgavenummeret og opgavens status til `I GANG`, tælle én `TASK_ATTEMPTS`-entry, opdatere `STATE`, `ITERATION_ID` og `LAST_BRANCH` og oprette den nye `ceo/*`-branch. Hvis en opgave står `I GANG`, skal næste iteration fortsætte den og aldrig starte en anden. Når ingen er `I GANG`, vælges altid den øverste `UFÆRDIG`-opgave. Efter grøn gate, commit og merge markeres netop den opgave `FÆRDIG`, og dens resultat, gate, commit-SHA og eventuelt `DEPLOY OK` skrives konkret heri. Efter to mislykkede forsøg markeres opgaven `BLOCKED: <årsag>`, hvorefter den næste `UFÆRDIG`-opgave vælges. De øvrige filer `STATUS.md`, `BUILD.md`, `DECISION.md`, `RESEARCH.md` og `BUDGET.md` er arkiv- og factualdokumenter i denne loop; kun denne plan styrer næste iteration.

## Kvalitetsgate

Denne gate er den obligatoriske minimum før merge til `main`:

```bash
python3 build_sites.py && python3 tools/seo_check.py && node tests/stripe-worker.test.mjs && python3 tools/check_inline_js.py
```

Den dækker kun siteproduktionen. Hver opgave skal have én konkret `**Gate:**`-linje med arbejdsmappe og kommandoer. Hvis en viste opgave endnu mangler en eksakt produktkommando, skal den researches og skrives ind, før opgaven markeres `I GANG`; usikre placeholder-gates er ikke gyldige. `site/_worker.js` kræver altid Stripe-worker-testen. Helt nye worker-ruter skal have en test, der beviser både success og failure. En eksisterende testtælle må ikke reduceres for at få gaten grøn.

## Mission og autoritative kilder

- Missionen er fire statiske sites bygget fra `site/` af `build_sites.py`: `cleancopy.tools`, `deskuptime.com`, `bugbottle.dev` og `mahope.tools`.
- Stripe og licensserveren er den aktuelle betalingsvej. Lemon Squeezy og Gumroad er døde og må ikke genoplives.
- Betalte og offentlige værktøjer skal være fuldt funktionelle. Betalt værdi skal være dokumenteret og må ikke hænge på Mads' løbende indsats.
- Betalt indhold må ikke ligge i det offentlige repo. Private file skal bygges reproducerbart og leveres fra Cloudflare KV efter Stripe-verifikation.
- `build_sites.py` fordeler først matchede filer til hvert site og giver resten til `mahope.tools`: `build_sites.py:46-140`.
- Den fælles runtime er `site/_worker.js`: `build_sites.py:142-158`.
- SEO, robots og sitemap genereres af `build_sites.py`: `build_sites.py:959-1057`.
- Den eksterne DeskUptime-kode ligger i `../deskuptime`; den er read-only for denne plan og skal have sin egen ændringsiteration.

## Researchfund

### Betaling og købsrejse

- `/api/lemon-webhook` og `handleLemonWebhook` findes stadig i `site/_worker.js` og kopieres til alle fire genererede Worker-output: `site/_worker.js:64-65`, `site/_worker.js:900-1031`, `build_sites.py:142-158`.
- `tools/test_license_flow.js` er en blandet legacy-test: Lemon-webhook-cases skal fjernes, mens dækning af fortsat understøttede licensruter skal bevares eller flyttes til den separate Stripe-worker-test.
- Page Profile Stripe-udsteder 32 hex-tegn, men CLI'en kræver `PPRO-` + 32 tegn: `site/_worker.js:2861-2875`, `page-profile/page_profile.py:33-58`.
- Clean Copy-webværktøjet sender korrekt `product: clean-copy-pro`, men root/Obsidian-pluginterne og mindst én browserudvidelseslicensklient mangler produktfeltet: `site/clean-copy-tool.html:427-432`, `obsidian-plugin/main.js:718-729`, `main.js:204-218`, `extension-clean-copy/options.js:46-92`.
- Licensklienter skal cache Pro-status i rimelig tid, eksempelvis syv dage, ved `503`/5xx, så betalende brugere ikke låses ude.
- Betalte downloads forventes i KV som `paidfile:*`: `site/_worker.js:2717-2725`, `site/_worker.js:3024-3040`. Repoet har ingen reproducerbar producer/uploader, og betalte kilder som `products/compliance-bundle.pdf`, `products/compliance-bundle.zip`, `products/dpa-template.md` og `products/nis2-contract-clauses.md` ligger allerede i det offentlige repo.
- Stripe-salg skriver `t:all:sales:<product>`, mens `/api/stats` og ugerapporten stadig læser den gamle Lemon-tæller: `site/_worker.js:1235-1246`, `site/_worker.js:2888-2893`, `tools/weekly_report.py:148-180`. Den nuværende salgstæller er desuden en read-modify-write-operation og må ikke alene være ground truth ved parallelle fulfillments.

### sider, claims og konvertering

- DeskUptime EN/DA lover “no phone-home”, “no central server” og “no telemetry”, selv om Pro aktiverer og revaliderer mod `mahope.tools`: `site/deskuptime/index.html:130-150`, `site/da/deskuptime/index.html:127-147`, `../deskuptime/src/license.js:70-152`.
- Den danske DeskUptime-blogartikel siger også, at licensen er offline: `site/da/blog/overvaag-hjemmeside-fra-terminalen.html:25-86`.
- Clean Copy, Page Profile og DeskUptime har allerede tydelig gratis/Pro-sammenligning og én direkte Stripe-CTA på deres centrale EN/DA-sider.
- Flere ældre Pro-/premium-sider viser fortsat priser eller “coming soon” uden købsmulighed: `site/site-icons.html:126-155`, `site/downloads.html:91-115`, `site/blog/eaa-compliance-scanner-desktop.html:67-119`, `site/compliance-report.html:127-157`, `site/scan-da.html:89-97`.
- `site/index.html:159-162` og `site/da/index.html:156-159` siger stadig, at betalt checkout ikke er koblet på.
- Ugerapport 2026-37 og 2026-38 har kun samlede top-8 paths uden domæne. Ugerapport 2026-39 har tom trafik efter timeout: `reports/weekly/2026-39.json:12`, `reports/weekly/2026-39.json:210-216`.
- Alle fire sites deler KV-namespace, og tracking gemmer path uden hostname. Derfor kan de nuværende rapporter ikke rangere Pro-sider pr. domæne: `site/track.js:1-18`, `site/_worker.js:1147-1173`, `build_sites.py:1148-1152`.
- Flere sider har både `track.js` og inline tracking og kan derfor tælle samme besøg to gange.

### SEO, links og drift

- Robots og sitemap genereres korrekt domænespecifikt for Clean Copy og DeskUptime.
- `mahope.tools/sitemap.xml` indeholder `https://mahope.tools/` to gange, fordi både `index.html` og `free-tools.html` bliver canonical root: `build_sites.py:126-139`, `dist/mahope.tools/sitemap.xml:3-4`.
- Live `bugbottle.dev/sitemap.xml` afviger fra det nuværende lokale buildoutput. Dette skal diagnosticeres som deployment-drift, ikke ved at redigere `dist/`.
- Kilde-scripts som `tools/gen_sitemap.py`, `tools/fix_sitemap_redirects.py`, `tools/full_site_check.py`, `health_check.py` og `verify_live.sh` er hardcoded til det gamle `hermes-passiv.pages.dev`.
- Den seneste build registrerer 18 unresolved references: Clean Copy 1, DeskUptime 6, BugBottle 2, mahope.tools 9. `build_sites.py` tæller dem men returnerer alligevel succes: `build_sites.py:1181-1195`.
- Deploy-CI kører build og SEO-check, men ikke Stripe-worker-test, inline-JS-test eller broken-reference-gate: `.github/workflows/deploy-sites.yml:49-83`.
- Deploy-triggeren mangler `tools/brand.py`, `tools/pagepass.py` og `tools/seo_check.py`, selv om de påvirker build eller gate: `.github/workflows/deploy-sites.yml:10-14`.
- `auditedwp` checkes ud uden fast commit-SHA: `.github/workflows/deploy-sites.yml:40-43`.

### Afhængigheder og runtime

- Den centrale oversigt `~/.local/oxloop/AFHAENGIGHEDER.md` er fra 2026-08-23 og indeholder ikke dette repo. Den er derfor ikke tilstrækkelig aktuel.
- En read-only OSV-scanning den 24. september fandt 15 advisory-fund i `desktop/package-lock.json`, blandt andet i `app-builder-lib 25.1.8`, `builder-util-runtime 9.2.10`, `js-yaml 4.3.1` og `tar 6.2.1`.
- Den samhængende patched linje var `electron-builder 26.15.3`; Electron 44.x kunne samtidig opgraderes til 44.4.5.
- `desktop/package.json` mangler `engines` trods Electron 44's krav om Node `>=22.12.0`; repoet mangler også `.nvmrc`: `desktop/package.json:83-86`, `desktop/package-lock.json:2148-2150`.
- `site-icons/pyproject.toml` har projektmetadata under `[tool]` i stedet for `[project]` og kan derfor ikke installeres korrekt: `site-icons/pyproject.toml:1-23`.
- Python-buildafhængigheder er hverken samlet eller låst. Det gælder Markdown, Pillow, ReportLab, fpdf2 og Playwright.
- Flere produktversioner og lockfile-versioner afviger, blandt andet desktop 1.3.3 mod lock-root 1.3.0 og Page Profile 1.1.0 mod `pyproject.toml` 1.0.0.

## Prioriteret kø

Opgave 1-4 er missionens eksplicitte åbne opgaver og kommer derfor før nyopdagede security-, purchase- og CI-opgaver. Opgraderingsreglen “sikkerhed først” gælder blandt alle øvrige backlogitems efter denne åbne missionsekvens.

### 1. UFÆRDIG — Fjern Lemon Squeezy-ruten helt

**Begrundelse:** Den gamle webhook er stadig i den fælles Worker og kopieres til alle fire sites, selv om Lemon Squeezy ikke længere er en gyldig betalingsvej.

**Omfang:**

- Fjern `/api/lemon-webhook` og `handleLemonWebhook` samt relaterede LS-kommentarer fra `site/_worker.js`.
- Fjern kun Lemon-webhook-cases fra `tools/test_license_flow.js`. Bevar eller portér dens fortsat relevante dækning af activation, validation, expiry, lookup og rate limiting, så opgaven ikke sletter dækning af andre ruter.
- Undgå ændringer i `/api/stripe-webhook`, `/api/stripe/fulfillment` og `/api/download`.

**Acceptkriterier:**

- `site/_worker.js` indeholder hverken `lemon-webhook`, `handleLemonWebhook` eller `LS_WEBHOOK_SECRET`.
- Stripe-worker-testen har en assertion for, at den fjernede route returnerer 404 på både GET og POST.
- Den eksisterende Stripe-testkæde fortsætter grøn, uden at antallet af assertions reduceres.
- Legacy-testen indeholder ingen Lemon-webhook-fixture, men bevarer dækning af de øvrige understøttede licensruter.

**Gate:** `node --check site/_worker.js && node tools/test_license_flow.js && node tests/stripe-worker.test.mjs` plus hele kvalitetsgaten ovenfor.

### 2. UFÆRDIG — Gør DeskUptime-teksten sand

**Begrundelse:** Pro-licensen kontakter licensserveren, så absolutte påstande om “no phone-home”, “no central server” og “no telemetry” er fejl.

**Omfang:**

- Ret EN- og DA-landingssiderne til at skelne mellem lokal gratis URL-monitorering og online Pro-licensaktivering/revalidering.
- Ret den danske blogartikel og dens generative kilde `tools/make_blog_da_mirrors_461.py`, der kalder licensen offline.
- Beskriv kun den konkrete dataoverførsel: licensnøgle, device-id, produkt og licensstatus; påstå ikke produkttelemetri uden dokumentation.
- Tilføj `tools/check_product_copy.py`, som fejler ved de gamle absolutte claims i både de fire public sider og den generative blogkilde.

**Acceptkriterier:**

- Ingen af de fire sider indeholder de gamle absolutte claims.
- EN og DA siger eksplicit, at Pro aktiverer og revaliderer mod `mahope.tools`.
- EN og DA siger, at URL-liste og check-resultater ikke uploades til en central monitoreringstjeneste.
- Hele kvalitetsgaten er grøn.

**Gate:** `python3 tools/check_product_copy.py` plus hele kvalitetsgaten.

### 3. UFÆRDIG — Gør robots, sitemap og domænedrift korrekt

**Begrundelse:** Fire domæner skal have én kanonisk, komplet og live-matchende SEO-overflade. Den nuværende mahope.tools-dublet og BugBottle-driften kan skade indeksering.

**Omfang:**

- Ret den dublede `https://mahope.tools/` i `build_sites.py` uden at slette en reel side.
- Gør robots/sitemap-kontrollen domæne-aware og automatisér den i kvalitetsgaten med `tools/check_sitemaps.py`.
- Tilføj `tools/check_live_sitemaps.py`, som verificerer de fire live domæners robots, sitemap, canonicale URL'er og commit-version read-only efter deploy.
- Definer routeinventaret eksplicit: hver indexerbar, self-referenced canonical-HTML-rute skal forekomme én gang; `404.html`, generated search-ruter, redirect-only sider og dokumenterede aliaser skal udelukkes. Et alias skal enten have en reel canonical/redirect-strategi eller eksplicit noindex.
- Opdatér gamle hardcoded sitemap/health-check-scripts, så de ikke peger på `hermes-passiv.pages.dev`.
- Diagnosticér hvorfor live BugBottle-output afviger fra source-buildet; ret source/CI, ikke `dist/`.

**Acceptkriterier:**

- Hvert af de fire builds har gyldig `robots.txt` med eget sitemap og `sitemap.xml` med kun sit eget domæne.
- Ingen sitemap har duplikerede `<loc>`-værdier.
- Hver indexerbar canonical-HTML-rute findes præcis én gang i det pågældende sitemap; eksklusionsreglerne er dokumenterede og stabile.
- `python3 tools/check_sitemaps.py` returnerer non-zero ved forkert domæne, duplikat eller manglende canonical-rute.
- Efter deploy er live robots, sitemap og sidesantal identiske med det seneste `main`-build.
- Search Console-punktet står under `❓ Til Mads`.

**Gate:** `python3 build_sites.py && python3 tools/check_sitemaps.py && python3 tools/seo_check.py` plus resten af kvalitetsgaten.

**Deploy-gate:** `python3 tools/check_live_sitemaps.py --commit <merge-sha>` efter GitHub Actions er grøn.

### 4A. UFÆRDIG — Gør trafikdata domæneopdelt og troværdige

**Begrundelse:** Ugerapport 2026-39 er tom, og de gamle rapporter kan ikke adskille fire domæner eller skelne duplikattracking. Uden troværdige data kan opgave 4B ikke vælge sider fra data.

**Omfang:**

- Lad Workeren aflede domæne og tid fra `request.url`; ignorer spoofede clientfelter og allowlist de fire domæner.
- Gem path og domæne uden at gemme rå IP som identitet.
- Fjern dobbelt pageview fra sider, der både indlæser `track.js` og har inline tracking.
- Undtag kendte bots, CI og interne health checks; tilføj tests, at sådanne besøg ikke øger tælleren.
- Gør `/api/stats` og `tools/weekly_report.py` domæneopdelt.
- Brug den eksisterende unikke `ful:<checkout-session>`-post som eneste idempotente salgsledger og tæl unikke session/product-poster; fjern den separate `t:all:sales:*`-tæller som ground truth.

**Acceptkriterier:**

- En syntetisk test skaber præcis én talt pageview pr. domæne/path og ingen talt bot-/CI-pageview; et spoofet domænefelt ignoreres.
- Parallelle fulfillments og replay af samme checkout-session tæller præcis ét salg pr. product.
- Ugerapporten viser top paths for hvert af de fire domæner og separate, dokumenterede Stripe-salg pr. produkt.
- Manglende/timeout-data rapporteres eksplicit som ukendt, aldrig som 0.
- `node tests/tracking-worker.test.mjs` og `python3 tools/test_weekly_report.py` er grønne.

**Gate:** `node tests/tracking-worker.test.mjs && python3 tools/test_weekly_report.py` plus hele kvalitetsgaten.

### 4B. UFÆRDIG — Prioritér konvertering uden nye Stripe-produkter

**Begrundelse:** De fire centrale produktsider er stærke, men gamle Pro-tilbud uden købsmulighed og modstridende checkout-claims skader købsrejsen.

**Omfang:**

- Definer konsekvent rankingperioden som de seneste syv fulde dage. En ny rapport skal have `ranking_basis: traffic` med domæne/path og uden test-/bottrafik.
- Kræv mindst 30 verificerede pageviews i perioden og mindst 5 i hvert domæne, der skal rangeres. Hvis et krav ikke er opfyldt, skal rapporten eksplicit have `ranking_basis: unknown`; gå derefter deterministisk tilbage til de fire centrale produktsider og inventaret af alle synlige Pro-tilbud uden at påstå, at de er mest besøgte.
- Opret `docs/stripe-kontrakt.md` fra missionens eksisterende offentlige Stripe-tabel og `tools/stripe_catalog.json` som maskinlæsbar allowlist; check-scriptet skal fejle ved drift mellem dem.
- Inventér alle synlige Pro/premium-tilbud med side, produkt, pris og CTA.
- Brug kun Payment Links og product keys fra missionen. Findes intet tilladt tilbud, skal den gamle købs-påstand fjernes eller flyttes til `❓ Til Mads`; opret ikke et nyt Stripe-produkt.
- Fjern de forældede globale claims om manglende checkout.

**Acceptkriterier:**

- Hver central Pro-side viser gratis og betalt uden overlapende eller modstridende claims.
- Hver købsbar side har præcis én tydelig CTA med et tilladt Stripe-link.
- Alle fundne Stripe-links giver HTTP 200 ved read-only GET, og produkttestdata matcher kun den tilladte mapping.
- Ingen side viser “coming soon”, placeholder-link eller “Pro is coming” oven på et allerede betalt produkt.
- Hvis perioden mangler data, har færre end 30 totale verificerede pageviews eller færre end 5 i et domæne, der rangeres, står `ranking_basis: unknown` sammen med den dokumenterede fallback; ingen egen trafik indgår.
- `python3 tools/check_stripe_ctas.py` er grøn og beviser, at `tools/stripe_catalog.json` matcher den tilladte kontrakt og alle brugte CTA'er.

**Gate:** `python3 tools/check_stripe_ctas.py` plus hele kvalitetsgaten.

### 5. UFÆRDIG — Stop offentlig eksponering af betalt indhold

**Begrundelse:** Betalte kilder og artefakter ligger allerede i det offentlige repo, selv om missionen kræver private filer og kun offentlig open-core-kode.

**Omfang:**

- Inventér hvert betalt produkt, kilde, builder, public downloadsti, filstørrelse, checksum, product key og forventet `paidfile:*`-nøgle.
- Tilføj `tools/check_private_content.py`, som fejler ved betalte kilder/artefakter i den offentlige git-tracked tree eller i offentligt buildoutput.
- Stop offentlig build/copy af betalte kilder og artefakter, men bevar open-core Pro-kode i repoet.
- Flyt kun betalt indhold til den private destination, Mads godkender, og erstat først de offentlige downloadstier når private leveringsfiler er dokumenteret.
- En eventuel git-historik-rewrite eller produktions-KV-upload er en separat handling og må ikke ske uden Mads' go.

**Blokeret delhandling:** Betalt indhold findes allerede i tidligere public commits. En fuld historik-remediering kræver en koordineret historik-rewrite, som er forbudt af denne kontrakt og desuden kræver Mads' go. Opgaven må derfor kun markeres `FÆRDIG` for stop af ny eksponering; historikken skal stå som eksplicit `BLOCKED: kræver Mads-godkendelse`, indtil der tages en beslutning.

**Acceptkriterier:**

- Der findes ingen betalte PDF/ZIP/Markdown-kilder ellerArtefakter i den offentlige git-tracked tree ved opgavens afslutning.
- Hvert betalt produkt har en reproducerbar buildkommando, checksum og sikker destination i et privat repo.
- Den offentlige Worker har kun licensadgang til private KV-filer; ingen downloadroute peger på offentlige filer.
- Read-only produktionsinventering eller en godkendt Mads-handling bekræfter hver forventet `paidfile:*`-nøgle.
- Hver commit beskriver præcist, hvilke filer der flyttes, og ingen historik-rewrite sker i samme commit.
- Historikken rapporteres fortsat som `BLOCKED: kræver Mads-godkendelse`; opgaven påstår ikke fuld sletning fra tidligere commits.

**Gate:** `python3 tools/check_private_content.py && python3 build_sites.py && python3 tools/seo_check.py` plus resten af kvalitetsgaten.

**Ekstern read-only-gate:** En Cloudflare-KV-inventering af forventede `paidfile:*`-nøgler skal gemmes read-only i planen af Mads eller en godkendt driftsti; ingen upload/sletning må ske i denne iteration.

### 6. UFÆRDIG — Reparer Page Profile-købsflowet

**Begrundelse:** En kunde kan betale og få en gyldig 32-hex Stripe-nøgle, som den solgte CLI afviser.

**Omfang:**

- Skriv først mockbaserede fejltests for en 32-hex Stripe-nøgle.
- Ret den kanoniske kode i `page-profile/` og den publicerede kopi i `site/downloads/page-profile/`; tilføj `tools/check_page_profile_distribution.py`, så builden ikke kan publicere en divergerende kopi.
- Aktivér og valider nøglen online via `https://mahope.tools/api/license/activate` og `/validate` med `product: page-profile-pro` og et stabilt device-id.
- Accepter aldrig en 32-hex nøgle alene på format/checksum; kun et gyldigt serversvar må aktivere Pro.
- Cache kun en tidligere gyldig positiv status i højst syv dage ved netværksfejl eller `503`/5xx. Hård fejl ved `403`, `404` eller `409` må ikke bruge cachen.
- Ret offline-claims i `site/page-profile.html` og `site/da/page-profile.html`, så de beskriver den online Pro-aktivering korrekt.
- Test canonicalisering, enheds-ID, replay og stabil lokal status.

**Acceptkriterier:**

- En mocket gyldig 32-hex `page-profile-pro`-nøgle aktiverer Pro via API'et.
- Ukendt nøgle, forkert produkt, udløbet/tilbagekaldt nøgle og nået enhedsgrænse giver korrekt hard failure.
- En cached gyldig status overlever ét 5xx-svar, men hverken `403`, `404` eller `409`.
- Formatnøgler uden gyldigt serversvar giver ikke Pro-status.
- Den publicerede CLI-kopi er byte-for-byte/parity-kontrolleret mod den kanoniske kode, og EN/DA-siderne har ingen offline-Pro-claims.
- `python3 page-profile/test_page_profile.py` og `python3 tools/check_page_profile_distribution.py` er grønne.

**Gate:** `python3 page-profile/test_page_profile.py && python3 tools/check_page_profile_distribution.py` plus hele kvalitetsgaten.


### 7. UFÆRDIG — Gør Clean Copy-pluginklienterne Stripe-kompatible

**Begrundelse:** Root- og Obsidian-plugin sender ikke `product`, selv om workeren afviser payloaden.

**Omfang:**

- Find alle shipped klienter, der kalder `/api/license`, herunder root/Obsidian-pluginterne og Clean Copy Chrome/Firefox-udvidelserne; send `product: clean-copy-pro` i hver klient.
- Implementér syvdages cachet Pro-status ved `503`/5xx i hver klient, så en licensserverfejl ikke låser kunden ude.
- Tilføj `tools/check_license_clients.py`, som fejler ved manglende product payload eller divergerende generated/publicerede klientkode.
- Skriv tests for success, `403`, `409` og `503` før implementeringen.

**Acceptkriterier:**

- Hver shipped licensklient sender valid product payload.
- Hver klient bevarer en cached gyldig status i højst syv dage over serverfejl.
- En udløbt eller tilbagekaldt licens giver en synlig, deterministisk fejl.
- `tools/check_license_clients.py` dækker alle fundne callers og offentlige dist-kopier.
- Hele kvalitetsgaten er grøn.

**Gate:** `node obsidian-plugin/test.js && node test.js && node extension-clean-copy/tools/test_clean_copy.js && python3 tools/check_license_clients.py` plus hele kvalitetsgaten.

### 8. UFÆRDIG — Opgrader electron-builder og fjern advisory-fund

**Begrundelse:** En aktuel OSV-scanning fandt 15 kendte advisory-fund i desktop-buildværktøjet. Sikkerhedshallere skal eftergives de fire prioriterede missionstasks.

**Omfang:**

- Opgradér kun `electron-builder` 25.x til den testede 26.15.x-linje i denne commit.
- Lad den patchede builder trække patched `app-builder-lib`, `builder-util-runtime`, `js-yaml` og `tar`.
- Læs migrationsnoter og opdatér buildkonfiguration kun hvis de kræver det.

**Acceptkriterier:**

- `npm ci` virker fra den nye lockfil.
- `npm audit --audit-level=high` har ingen high/critical advisory-fund.
- Lokal macOS build og CI-b builds for macOS, Linux og Windows producerer alle forventede artefakter.
- Hele kvalitetsgaten er grøn.
- Opgraderingen og eventuelle kodeændringer står i denne plan.

**Gate:** `npm ci && npm audit --audit-level=high && npm run build:mac` i `desktop/`, derefter platform-CI, plus hele kvalitetsgaten.

**Post-merge-gate:** `gh run watch <run-id> --exit-status` skal være grøn for macOS x64/arm64, Linux og Windows; en rød post-merge-gate reverteres straks i en ny commit.

### 9. UFÆRDIG — Gør alle 18 broken references til en hard gate

**Begrundelse:** Nuværende build tæller 18 fejl men deployer, og missionen forbyder døde links, downloads og formularer.

**Omfang:**

- Ret kun reelle interne links og manglende assets i source.
- Erstat regex-baseret referencekontrol med en parser, der ignorerer kodeeksempler i `pre/code`.
- Lad build og CI fejle ved reelle uopklarede references.

**Acceptkriterier:**

- `dist/build-summary.json` har `broken: 0` for alle fire sites.
- `python3 tools/check_links.py` og build/CI returnerer non-zero ved en syntetisk broken reference.
- Hvert downloadlink og hver kritisk formular har mindst én repræsentativ smoke test.
- Hele kvalitetsgaten er grøn.

**Gate:** `python3 build_sites.py && python3 tools/check_links.py` plus resten af kvalitetsgaten.

### 10. UFÆRDIG — Få CI til at køre den faktiske kvalitetsgate

**Begrundelse:** Workflowen kører kun build og SEO-check; den betalingskritiske Worker-test og inline-JS-test mangler.

**Omfang:**

- Kør præcis den dokumenterede kvalitetsgate før deploy.
- Medtag alle buildinputs i path-filteret, især `tools/brand.py`, `tools/pagepass.py` og `tools/seo_check.py`.
- Pin `auditedwp` til en godkendt commit-SHA.
- Lad ikke de fire matrixjobs fortsætte efter en fælles gatefejl.

**Acceptkriterier:**

- CI fejler, hvis Stripe-worker-testen eller inline-JS-testen fejler.
- En ændring i et buildinput udløser workflowen.
- Den pinnede `auditedwp`-revision står i planen.
- `python3 tools/test_deploy_workflow.py` beviser gatekommandoer, path-triggere og fail-fast-adfærd.
- Hele kvalitetsgaten er grøn.

**Gate:** `python3 tools/test_deploy_workflow.py` plus hele kvalitetsgaten.

### 11. UFÆRDIG — Deklarér runtime og opgradér Electron-patchlinjen

**Begrundelse:** Desktop kræver Node `>=22.12.0`, men manifestet og repoet erklærer det ikke.

**Omfang:**

- Opgradér Electron 44.0.0 til den aktuelle patched 44.x-version i en separat commit.
- Tilføj `engines.node` og `.nvmrc` i samme commit.
- Ret stale lock-root-version, hvis den følger produktmanifestet.

**Acceptkriterier:**

- `engines.node` og `.nvmrc` peger på en understøttet Node-version.
- `npm ci`, audit og alle desktop-builds er grønne.
- Hele kvalitetsgaten er grøn.
- Versionsændringen står i planen.

**Gate:** `npm ci && npm audit --audit-level=high && npm run build:mac` i `desktop/`, derefter platform-CI, plus hele kvalitetsgaten.

**Post-merge-gate:** `gh run watch <run-id> --exit-status` skal være grøn for macOS x64/arm64, Linux og Windows; en rød post-merge-gate reverteres straks i en ny commit.

### 12. UFÆRDIG — Lå Python-buildmiljøet og reparer site-icons

**Begrundelse:** Fire siteværktøjer bruger tredjepartspakker uden samlet lock, og Site Icons har ugyldig PEP 621-metadata.

**Omfang:**

- Opret et låst, auditérbart Python-miljø til site-, ebook-, bundle-, cover- og screenshotværktøjer.
- Ret `site-icons/pyproject.toml` til gyldig `[project]`-metadata.
- Byg og test Site Icons fra en ren installation.

**Acceptkriterier:**

- En ren installation installerer de deklarerede buildafhængigheder.
- `pip-audit` har ingen kendte high/critical-fund eller har en dokumenteret, begrundet undtagelse.
- `pip install` fra Site Icons-sdist installerer Pillow og `site-icons --help` virker.
- Hele kvalitetsgaten er grøn.

**Gate:** `python3 -m pip install --require-hashes -r requirements-build.txt && pip-audit -r requirements-build.txt && python3 -m build site-icons && python3 -m pip install --force-reinstall site-icons/dist/*.whl && site-icons --help` plus hele kvalitetsgaten.

### 13. UFÆRDIG — Ret dokumentation, privacy og versiondrift

**Begrundelse:** `STATUS.md`, `DECISION.md`, `BUILD.md`, `BUDGET.md`, root-README og privacy beskriver delvist Lemon Squeezy, gamle produkter eller urigtige data claims.

**Omfang:**

- Opdatér `STATUS.md`, `BUILD.md`, `DECISION.md`, `RESEARCH.md`, `BUDGET.md` og root-README som historiske/factuelle dokumenter; fjern deres operative “næste iteration”-state.
- Ret privacyteksten, så den beskriver faktisk KV-, waitlist- og BugBottle-behandling uden at godkende nye datagrundlag.
- Etablér én versionskilde pr. produkt og fang afvigelser i `tools/check_versions.py`.

**Acceptkriterier:**

- Ingen aktuel status- eller public-facing-kontrakt dokumenterer Lemon Squeezy eller Gumroad som aktiv betaling.
- De seks dokumenter indeholder ingen konfliktende `ACTIVE_TASK`, `NEXT_TASK` eller blocker-state; kun denne plan har det.
- Privacy matcher de faktiske behandlinger.
- `python3 tools/check_versions.py` fejler på den nuværende drift mellem manifests, locks, source og publicerede artefakter.
- Hele kvalitetsgaten er grøn.

**Gate:** `python3 tools/check_versions.py` plus hele kvalitetsgaten.


## ❓ Til Mads

1. **Tilføj property i Google Search Console** for `mahope.tools`, `cleancopy.tools`, `deskuptime.com`, `bugbottle.dev` og `mahoje.dk`. Verificér sitemap og robots efter tilføjelse. Denne handling må ikke udføres af repoet.
2. **Beslut om historik-remediering:** Betalt indhold findes i tidligere public commits. En fuld sletning kræver en koordineret historik-rewrite, som loop-kontrakten forbyder og som ikke må ske uden dit go. Indtil beslutningen står som `BLOCKED: kræver Mads-godkendelse`.
3. **Bekræft private paid-file-kilder:** hvilket privat repo eller hvilken godkendt buildkilde skal producere de filer, der forventes i Cloudflare KV? Ingen produktionsupload må køre automatisk fra dette repo uden separat godkendelse.
4. **Udfør én lavendt Stripe-testkøb**, når de lokale mock-tests er grønne, hvis licensaktivering, kvittering og download skal verificeres mod rigtige Stripe/CF-tjenester. Brug kun et allerede oprettet produkt; opret ikke et nyt.

## Deploylog

- 2026-09-25: Researchiterationen ændrer kun `IMPLEMENTATION_PLAN.md`. Deploy-workflowens path-filter forventes derfor ikke at udløse en site-deploy. Efter merge/push kontrolleres GitHub Actions read-only, og der tilføjes en `VERIFICÉR DEPLOY`-note kun hvis workflowen alligevel kører.

## Commitlog

- Research og initial plan: `10c5908` — `Lav en prioriteret plan for næste Hermes-iterationer`.
