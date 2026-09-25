# IMPLEMENTATION_PLAN

## Status

- `ITERATION_ID`: `page-profile-stripe-license-2026-09-25`
- `STATE`: `FÆRDIG`
- `ACTIVE_TASK`: `INGEN`
- `NEXT_TASK`: `4F — Luk tre huller i licens-workeren`
- `TASK_ATTEMPTS`: `4E: 1/2`
- `LAST_BRANCH`: `ceo/page-profile-license`
- `PLAN_COMMIT`: `ea4e6c3`
- `BASELINE`: `main@cb725e9`
- `RESULT`: Opgave 4E er færdig. Stripe-udstedte 32-hex-nøgler aktiveres og valideres online med produktet `page-profile-pro` og et stabilt, lokalt gemt device-id. Kun netværksfejl og 5xx kan bruge en tidligere positiv status i højst syv dage; 403/404/409, ugyldige svar og inaktiv licens fejler hårdt. Legacy-PPRO, salt og `--gen-key` er fjernet. Version 1.2.0 er publiceret som kanonisk script, download-kopi og sdist, og offline-claims er rettet.
- `GATE`: `GRØN — Page Profile 11/11, sdist-build, build/sitemap 4/4, SEO 307/0, Stripe 52/52, inline JS 296/0, canonical/published/tar parity, live-validering 404 og frisk review med alle P1 rettet`
- **Reelle, dokumenterede salg i repoet:** 0. Det er ikke bevis for 0 salg; kun dokumentation, der kan tælles.
- **Blokerede opgaver:** ingen.
- `dist/` må regenereres af `build_sites.py`, men må ikke redigeres manuelt eller committes.
- `../auditedwp` er en ekstern buildkilde og må ikke ændres.
- Secrets, `.env*`, produktionsdatabaser og udadvendte writes er forbudte. Eneste eksplicitte undtagelse er den kontraktstyrede merge/push til `main` i dette repo, som må deploye de tre Cloudflare-Pages-domæner; `bugbottle.dev` er read-only og ejes af `mahope/bugbottle`.

### Kanonisk state-protokol

Før en ny iteration ændrer kode skal den sætte `ACTIVE_TASK` til opgavenummeret og opgavens status til `I GANG`, tælle én `TASK_ATTEMPTS`-entry, opdatere `STATE`, `ITERATION_ID` og `LAST_BRANCH` og oprette den nye `ceo/*`-branch. Hvis en opgave står `I GANG`, skal næste iteration fortsætte den og aldrig starte en anden. Når ingen er `I GANG`, vælges altid den øverste `UFÆRDIG`-opgave. Efter grøn gate, commit og merge markeres netop den opgave `FÆRDIG`, og dens resultat, gate, commit-SHA og eventuelt `DEPLOY OK` skrives konkret heri. Efter to mislykkede forsøg markeres opgaven `BLOCKED: <årsag>`, hvorefter den næste `UFÆRDIG`-opgave vælges. De øvrige filer `STATUS.md`, `BUILD.md`, `DECISION.md`, `RESEARCH.md` og `BUDGET.md` er arkiv- og factualdokumenter i denne loop; kun denne plan styrer næste iteration.

## Kvalitetsgate

Denne gate er den obligatoriske minimum før merge til `main`:

```bash
python3 build_sites.py && python3 tools/check_sitemaps.py && python3 tools/seo_check.py && node tests/stripe-worker.test.mjs && python3 tools/check_inline_js.py
```

Den dækker kun siteproduktionen. Hver opgave skal have én konkret `**Gate:**`-linje med arbejdsmappe og kommandoer. Hvis en viste opgave endnu mangler en eksakt produktkommando, skal den researches og skrives ind, før opgaven markeres `I GANG`; usikre placeholder-gates er ikke gyldige. `site/_worker.js` kræver altid Stripe-worker-testen. Helt nye worker-ruter skal have en test, der beviser både success og failure. En eksisterende testtælle må ikke reduceres for at få gaten grøn.

Efter et mergecommit skal livekontrollen køre som `python3 build_sites.py && python3 tools/check_live_sitemaps.py --commit "$(git rev-parse HEAD)"`. Først efter commitet må buildet regenereres, og live-scriptet kræver fuld 40-tegns SHA; en short SHA eller `dist/` fra et tidligere commit afvises.

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
- Live `bugbottle.dev/sitemap.xml` afviger fra det nuværende lokale buildoutput. Dette er diagnosticeret som deployment-ejerskabsdrift, ikke ved at redigere `dist/`.
- `bugbottle.dev` serverer 40 routes fra `mahope/bugbottle` via Dokploy på commit `07828a1d605383c58cf44416447e0497e91fdac3` og viser BugBottle 1.0.1. Denne repo bygger 7 routes fra v0.4.0-landingmateriale; `bugbottle-dev.pages.dev` matcher den lokale shadow-build. Deploy-workflowen udgiver derfor ikke denne forældede shadow; den separate `--all` livekontrol matcher den autoritative kilde read-only.
- Den nye lokale gate finder kun selv-referencede, indexerede HTML-ruter; noindex, de fire erklærede 404/search-ruter, Clean Copy-aliaserne og Workerens deklarerede redirectkilder er ekskluderet og dækket af negative tests.
- Hver build publicerer `build-info.json` med domæne, commit, routeantal og SHA-256 af sitemap/routes. Live-gaten kræver byte-identiske robots/sitemap/build-info og derefter 200 + self-canonical + indexerbar status for hver sitemap-URL.
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

### 1. FÆRDIG — Fjern Lemon Squeezy-ruten helt

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

### 2. FÆRDIG — Gør DeskUptime-teksten sand

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

### 3. FÆRDIG — Gør robots, sitemap og domænedrift korrekt

**Begrundelse:** Fire domæner skal have én kanonisk, komplet og live-matchende SEO-overflade. Den nuværende mahope.tools-dublet og BugBottle-driften kan skade indeksering.

**Omfang:**

- Ret den dublede `https://mahope.tools/` i `build_sites.py` uden at slette en reel side.
- Gør robots/sitemap-kontrollen domæne-aware og automatisér den i kvalitetsgaten med `tools/check_sitemaps.py`.
- Tilføj `tools/check_live_sitemaps.py`, som som standard verificerer de tre Pages-ejede live domæner og med `--all` også den separate BugBottle-kilde read-only: robots, sitemap, canonicale URL'er, sider og commit-version.
- Definer routeinventaret eksplicit: hver indexerbar, self-referenced canonical-HTML-rute skal forekomme én gang; `404.html`, generated search-ruter, redirect-only sider og dokumenterede aliaser skal udelukkes. Et alias skal enten have en reel canonical/redirect-strategi eller eksplicit noindex.
- Opdatér gamle hardcoded sitemap/health-check-scripts, så de ikke peger på `hermes-passiv.pages.dev`.
- Diagnosticér hvorfor live BugBottle-output afviger fra source-buildet; ret source/CI, ikke `dist/`.

**Implementeret denne iteration:**

- `free-tools.html` er en reel, self-canonical `/free-tools`-side; mahope.tools-hjemmesiden kommer ikke længere fra en alias-kopi. Sitemap, llms og search-index filtrerer noindex og ikke-self-canonical sider.
- `tools/route_inventory.json` er den uafhængige, eksplicitte inventory med 32 Clean Copy-, 5 DeskUptime-, 7 lokale BugBottle- og 251 mahope.tools-ruter. `build_sites.py` og `tools/check_sitemaps.py` afviser nye, manglende eller slash-ekvivalente ruter; 11 negative/positive tests dækker domæne, duplikater, inventory, noindex, redirects og commit.
- `tools/check_live_sitemaps.py` verificerer de tre Pages-ejede domæner mod lokale bytes, commit, title, JSON-LD, HTTP `X-Robots-Tag` og alle sitemap-sider. `--all` kræver en disposable, read-only BugBottle-kilde med genererede robots/sitemap og verificerer dens Git-commit.
- Den separate `mahope/bugbottle`-kilde er diagnosticeret read-only på commit `07828a1d605383c58cf44416447e0497e91fdac3`: dens `build-docs.mjs` genererer 33 docs-sider, fire selvstændige sider og changelog, i alt 40 sitemap-routes. Live `bugbottle.dev` matcher dens robots/sitemap og alle sider.
- Deploy-CI bruger den nye lokale og live-gate for de tre Pages-ejede domæner, kører Stripe-worker- og inline-JS-tests før deploy, dækker alle buildinputs i path-filteret, pinner `mahope/auditedwp` til `5e244dcff242352cd5be31a55ca5f7d260f7e520` og deployer kun fra `main`.
- Den røde første live-gate gav permanent harness-dækning: Wrangler installeres i repo-roden og deployer en eksplicit `dist/<domæne>`-sti; `pagepass.py` indpakker ikke `<table>` i scripts/pre/textarea; `seo_check.py` afviser ugyldig JSON-LD før deploy.

**Resultat:** Implementeringen blev merged i `fb4189d`; den korrigerende deploy-gate blev merged i `b7c8a64`. GitHub Actions-run `36099316657` og en uafhængig live-kontrol bekræfter robots, sitemap, build-info, JSON-LD, canonicale og alle 288 Pages-ruter.

**Acceptkriterier:**

- Hvert af de fire builds har gyldig `robots.txt` med eget sitemap og `sitemap.xml` med kun sit eget domæne.
- Ingen sitemap har duplikerede `<loc>`-værdier.
- Hver indexerbar canonical-HTML-rute findes præcis én gang i det pågældende sitemap; eksklusionsreglerne er dokumenterede og stabile.
- `python3 tools/check_sitemaps.py` returnerer non-zero ved forkert domæne, duplikat eller manglende canonical-rute.
- Efter deploy er live robots, sitemap og sidesantal identiske med det seneste `main`-build.
- Search Console-punktet står under `❓ Til Mads`.

**Gate:** `python3 tools/test_check_sitemaps.py && python3 tools/test_check_live_sitemaps.py && python3 build_sites.py && python3 tools/check_sitemaps.py && python3 tools/seo_check.py` plus resten af kvalitetsgaten.

**Deploy-gate:** `python3 tools/check_live_sitemaps.py --commit <merge-sha>` for de tre Pages-domæner efter GitHub Actions er grøn. Den separate read-only driftkontrol er `python3 tools/check_live_sitemaps.py --all --commit <merge-sha> --bugbottle-source <disposable-checkout> --bugbottle-source-commit 07828a1d605383c58cf44416447e0497e91fdac3 --attempts 1`; kontrollen arkiverer og bygger den pinned commit i en midlertidig mappe og matcher derefter den autoritative BugBottle-kilde.

### 4E. FÆRDIG — Page Profile Pro skal acceptere Stripe-nøgler

**Begrundelse:** Licens-audit 2026-09-25: `page-profile/page_profile.py:54-59` accepterer kun `PPRO-`+32 base32, men Stripe-leveringen udsteder 32 hex-tegn, så **enhver købt nøgle afvises**. Samtidig kan `--gen-key` (linje ~912-920) med det offentlige salt (linje ~37) lave gyldige nøgler, så Pro kan låses op gratis. Købslinket i CLI'en (linje ~79) peger på det forældede `hermes-passiv.pages.dev`.

**Omfang:**

- Erstat den offline validering med `activate`/`validate` mod `https://mahope.tools/api/license/` med `product: "page-profile-pro"` efter `C:\Projects\business\planer\2026-09-24-stripe-kontrakt.md` (32 hex, trim + små bogstaver; stabilt `device_id` gemt i `~/.page-profile-license`; 7 dages cache ved 503/netværksfejl; tydelige beskeder for 403/404/409).
- Fjern `--gen-key` og saltet.
- Købslink: `https://buy.stripe.com/9B6eVcgHp7YK69ggN9bMQ04`.
- Udgiv som 1.2.0 i `site/downloads/page-profile/` og opdatér versionsreferencer.

**Implementeret denne iteration:**

- `~/.page-profile-license` er en 0600 JSON-state med normaliseret 32-hex-nøgle, stabilt device-id og tidspunkt for seneste positive svar. Aktivering og validate bruger henholdsvis `/activate` og `/validate` med `product: page-profile-pro`.
- Netværksfejl og HTTP 5xx kan bruge højst syv dages positive cache. HTTP 403/404/409, `valid: false`, formatfejl og malformed HTTP 200-svar bruger aldrig cachen. 11 offline tests dækker payload, hard/soft fejl, cache-grænse, legacy-fjernelse og public copy.
- Kanonisk og publiceret script er byte-identiske; `page-profile-1.2.0.tar.gz` er bygget fra samme kilde og indeholder den kanoniske kode. EN/DA landingssider, README og dansk blogkilde fortæller nu korrekt om online licensstjek og syvdages outage-cache.
- Frisk review fandt to P1-fejl: malformed 200-svar kunne bruge cache, og tarball-vejledningen pegede på bindestreg. Begge er rettet og dækket af de grønne gates. Den planlagte separate distributions-CI-forsvar er bevaret som opgave 6.

**Acceptkriterier:**

- Test uden netværk (mocket HTTP): gyldig hex-nøgle aktiveres, `PPRO-`-nøgler og `--gen-key` findes ikke længere, 503 giver Pro i højst 7 dage fra seneste validering, 403/404/409 giver korrekt besked.
- Live read-only: `validate` med en tilfældig 32-hex-nøgle giver 404.

**Gate:** `python3 page-profile/test_page_profile.py` plus hele kvalitetsgaten.

### 4F. UFÆRDIG — Luk tre huller i licens-workeren

**Begrundelse:** Licens-audit 2026-09-25 af `site/_worker.js`.

**Omfang:**

- Refundering af abonnementer: ved checkout i abonnementstilstand er `s.payment_intent` null, så der skrives ingen `lic-pi:`, og `revokeForCharge` (~linje 2818) falder tilbage på `charge.invoice`, som ikke findes i nyere Stripe-API-versioner. Gem koblingen payment_intent → licens i `invoice.paid` (første faktura) eller slå op via `invoice_payments`, så en refunderet årslicens (`clean-copy-pro`, `eucomply-pro`, `page-profile-pro`) tilbagekaldes.
- Uventede fejl i licens-API'et skal svare 503 (kontrakten), ikke 500 (~linje 889).
- `activate_url` for `clean-copy-pro` skal pege på en side, der forklarer hvor nøglen indtastes i hver klient (Chrome, Firefox, Obsidian), fx `https://cleancopy.tools/activate/`; opret siden i `site/`.

**Acceptkriterier:**

- Worker-test: `charge.refunded` for et abonnement (uden `payment_intent` på sessionen) tilbagekalder licensen; engangskøb virker som før.
- Worker-test: en kastet fejl i licens-handleren giver 503.
- Aktiveringssiden findes i sitemap og består SEO-checket.
- Stripe-worker-testens antal tests falder ikke.

**Gate:** `node tests/stripe-worker.test.mjs` plus hele kvalitetsgaten.

### 4A. FÆRDIG — Gør trafikdata domæneopdelt og troværdige

**Begrundelse:** Ugerapport 2026-39 er tom, og de gamle rapporter kan ikke adskille fire domæner eller skelne duplikattracking. Uden troværdige data kan opgave 4B ikke vælge sider fra data.

**Omfang:**

- Lad Workeren aflede domæne og tid fra `request.url`; ignorer spoofede clientfelter og allowlist de fire domæner.
- Gem path og domæne uden at gemme rå IP som identitet.
- Fjern dobbelt pageview fra sider, der både indlæser `track.js` og har inline tracking.
- Undtag kendte bots, CI og interne health checks; tilføj tests, at sådanne besøg ikke øger tælleren.
- Gør `/api/stats` og `tools/weekly_report.py` domæneopdelt.
- Brug den eksisterende unikke `ful:<checkout-session>`-post som eneste idempotente salgsledger og tæl unikke session/product-poster; fjern den separate `t:all:sales:*`-tæller som ground truth.

**Implementeret i `df25c8b` og `9569979`:**

- Hver pageview/download er en egen KV-event med domæne, dato, path og daily hash af IP+UA; rå IP gemmes ikke. Path kommer fra et påkrævet same-origin `Referer`, og domæne/dato kan ikke spoofes via JSON.
- Kendte bots, CI, Lighthouse, health/sitemap-checks og den ugentlige rapport filtreres. Dobbelt pageviews fjernes ved at fjerne inline pageview-kald fra sider, der allerede indlæser `track.js`.
- `/api/stats` kræver et afledt bearer-token fra den eksisterende server-secret, og dashboardet hverken logger tokenet i URL'en eller i sessionStorage. Tredjeparts-BugBottle-scriptet er fjernet fra admin-siden.
- Salgsledgeren er `ful:<checkout-session>`, og både replay og parallel fulfillment giver én dokumenteret post. En pending-markør uden fuldført `ful:`-post gør status `unknown`; fejlet pending-skrivning afbryder leveringen, så der ikke opstås usynlig delvis salgsdata.
- Manglende eller ugyldige KV-counters, unikke, traffic- og fulfillmentdata er `unknown`; den ugentlige rapport parser kun dokumenterede heltal og bevarer kendte domæner adskilt.
- Frisk pre-land review fandt fire konkrete huller og en CI-regression; alle er rettet og dækket af de grønne gates ovenfor.

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

### 4C. UFÆRDIG — Send support og købersvar til de nye support-adresser

**Begrundelse:** Siden 2026-09-25 modtager alle produktdomæner mail (MX → Stalwart, catch-all → den fælles indbakke `support@mahope.tools`), som automations-serverens produktpuls læser og poster i #produkter. Sidernes kontaktlinks og leveringsmailens svar-adresse peger stadig på Mads' private indbakker, så kundehenvendelser bliver ikke sporet som produktfeedback.

**Omfang:**

- Erstat synlige `mailto:mads@mahope.dk`/`mailto:mads@mahoje.dk` på produktsiderne (bl.a. `site/privacy/`, `site/terms/`) med `support@<sidens domæne>` for cleancopy.tools, deskuptime.com og bugbottle.dev og `support@mahope.tools` for mahope.tools.
- Sæt `reply_to` i leveringsmailen (`site/_worker.js`, `Your ${r.product_name}`) til `support@<produktets domæne>` ud fra produktets `home` i produktkataloget, med `support@mahope.tools` som fallback. `from` forbliver `orders@mahoje.dk`, og salgsnotitsen til Mads ændres ikke.
- Ingen DNS-, Stalwart- eller Stripe-ændringer; adresserne findes allerede.

**Acceptkriterier:**

- `grep -rn "mailto:mads@" site/` giver ingen fund.
- En worker-test beviser, at leveringsmailen for `clean-copy-pro` har `reply_to: support@cleancopy.tools`, og at et produkt uden `home` falder tilbage til `support@mahope.tools`.
- Stripe-worker-testens antal tests falder ikke.

**Gate:** `! grep -rn "mailto:mads@" site/ && node tests/stripe-worker.test.mjs` plus hele kvalitetsgaten.

### 4D. UFÆRDIG — Link til Stripe-kundeportalen for årsabonnenter

**Begrundelse:** Stripe-kundeportalen blev oprettet 2026-09-25 (standardkonfiguration: opsigelse ved periodens udløb, fakturahistorik, opdatering af betalingskort, adresse og momsnummer). Årsabonnenter på `clean-copy-pro`, `eucomply-pro` og `page-profile-pro` har i dag ingen vej til at opsige eller hente fakturaer selv. EU-forbrugerregler kræver et let opsigelsesflow.

**Omfang:**

- Vis linket `https://billing.stripe.com/p/login/6oU4gy76PgvgdBIdAXbMQ00` ("Manage subscription, invoices and VAT ID") på `/thanks` og i leveringsmailen, når produktet i kataloget er et abonnement (årligt). Engangskøb får ikke linket.
- Tilføj samme link på `/support` og i `site/terms/` under opsigelse.
- Ingen ændring i Stripe-konfigurationen.

**Acceptkriterier:**

- En worker-test beviser, at leveringsmailen for `clean-copy-pro` indeholder portal-linket, og at mailen for `deskuptime-pro` (engangskøb) ikke gør.
- `/thanks` viser linket for et abonnementsprodukt i den eksisterende mock-test.
- Stripe-worker-testens antal tests falder ikke.

**Gate:** `node tests/stripe-worker.test.mjs` plus hele kvalitetsgaten.

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

### 14. UFÆRDIG — Fjern døde sitemap-generator- og deploystier

**Begrundelse:** Flere historiske bloggeneratorer skriver stadig til `site/sitemap.xml`, selv om builden nu kun bruger `dist/<domain>/sitemap.xml`; gamle instruktioner refererer desuden til den deaktiverede manuelle `deploy.sh`.

**Omfang:**

- Opdatér alle shippede generatorer, så de ikke kan mutere en ubrugt source-sitemap eller den gamle `hermes-passiv.pages.dev`-origin.
- Ret `indexnow_ping.sh` og relaterede health-/deploy-dokumentation til de aktive domæner og CI-deploystien.
- Behold kun read-only/public discovery-pings; ingen nye udadvendte writes uden Mads-godkendelse.

**Acceptkriterier:**

- Ingen generator eller aktivt helbredsscript peger på `hermes-passiv.pages.dev` eller skriver i `site/sitemap.xml`.
- `deploy.sh` har én dokumenteret, idempotent adgang; ingen aktiv instruktion beder om manuel Pages-upload.
- Hele kvalitetsgaten er grøn.

**Gate:** `python3 tools/check_legacy_seo_paths.py` plus hele kvalitetsgaten.


## ❓ Til Mads

1. **Tilføj property i Google Search Console** for `mahope.tools`, `cleancopy.tools`, `deskuptime.com`, `bugbottle.dev` og `mahoje.dk`. Verificér sitemap og robots efter tilføjelse. Denne handling må ikke udføres af repoet.
2. **Beslut om den lokale BugBottle-shadow:** live `bugbottle.dev` er dokumenteret som den separate `mahope/bugbottle`/Dokploy-kilde med 40 routes på commit `07828a1d605383c58cf44416447e0497e91fdac3`; dette repo har en ubrugt 7-routes shadow. Vælg om shadowen skal fjernes helt eller holdes som et lokalt kildesnapshot. Det er ikke længre en blocker for den nuværende deploy.
3. **Beslut om historik-remediering:** Betalt indhold findes i tidligere public commits. En fuld sletning kræver en koordineret historik-rewrite, som loop-kontrakten forbyder og som ikke må ske uden dit go. Indtil beslutningen står som `BLOCKED: kræver Mads-godkendelse`.
4. **Bekræft private paid-file-kilder:** hvilket privat repo eller hvilken godkendt buildkilde skal producere de filer, der forventes i Cloudflare KV? Ingen produktionsupload må køre automatisk fra dette repo uden separat godkendelse.
5. **Udfør én lavendt Stripe-testkøb**, når de lokale mock-tests er grønne, hvis licensaktivering, kvittering og download skal verificeres mod rigtige Stripe/CF-tjenester. Brug kun et allerede oprettet produkt; opret ikke et nyt.

## Deploylog

- 2026-09-25: `DEPLOY OK ea4e6c3` — GitHub Actions-run `36142200546` byggede, deployede og live-verificerede cleancopy.tools, deskuptime.com og mahope.tools grønt. Uafhængig sitemap-kontrol bekræftede alle tre domæner; live 1.2.0-script, tarball, EN/DA-licenstekst og 404 på det gamle 1.1.0-arkiv blev verificeret. CI meldte kun kendte Node 20-/Ubuntu 26-advarsler.
- 2026-09-25: `DEPLOY OK 9569979` — GitHub Actions-run `36133997658` byggede, deployede og live-verificerede cleancopy.tools, deskuptime.com og mahope.tools grønt. Uafhængig `check_live_sitemaps.py --commit 956997979390f5b0b28e3c8359350e581937e7fb` bekræftede alle tre domæner; live `/stats` viste den nye token-prompt uden tredjepartsscript, og det gamle URL-token gav 401. CI meldte kun kendte Node 20-/Ubuntu 26-advarsler.
- 2026-09-25: `DEPLOY OK b7c8a64` — GitHub Actions-run `36099316657` byggede, deployede og live-verificerede cleancopy.tools, deskuptime.com og mahope.tools grønt. Uafhængig `check_live_sitemaps.py --commit b7c8a64` bekræftede byte-identiske robots/sitemap/build-info og alle 288 sitemap-sider; CI meldte kun eksisterende Node 20-/Ubuntu 26-advarsler.
- 2026-09-25T07:37:10+02:00: `VERIFICÉR DEPLOY: korrigeret Wrangler-sti og JSON-LD-gate b7c8a64 2026-09-25T07:37:10+02:00`
- 2026-09-25T07:27:55+02:00: `VERIFICÉR DEPLOY: domænekorrekt robots/sitemap og tre Pages-domæner fb4189d 2026-09-25T07:27:55+02:00`
- 2026-09-25T05:28:41Z: `DEPLOY FEJL 36098659762` — alle tre Pages-deploysteps lykkedes, men post-deploy-gaten fejlede lokalt, fordi `wrangler-action` installerede `node_modules` i hver `dist/<domæne>`. En uafhængig live-kontrol bekræftede de nye robots/sitemap/build-info, men fandt ugyldig JSON-LD på `/blog/html-table-to-csv-converter`; korrigerende commit `b7c8a64` blev efterfølgende grøn live.
- 2026-09-25: Researchiterationen ændrer kun `IMPLEMENTATION_PLAN.md`. Deploy-workflowens path-filter forventes derfor ikke at udløse en site-deploy. Efter merge/push kontrolleres GitHub Actions read-only, og der tilføjes en `VERIFICÉR DEPLOY`-note kun hvis workflowen alligevel kører.
- 2026-09-25: `DEPLOY OK 28c7f64` — GitHub Actions-run `36076793409` deployede alle fire sites grønt. Live GET og POST på `/api/lemon-webhook` gav `404` på `cleancopy.tools`, `deskuptime.com`, `bugbottle.dev` og `mahope.tools`; de tre Worker-domaener returnerede `Not found`, mens BugBottle returnerede sit nginx-404-svar. CI meldte kun eksisterende Node 20-/Ubuntu-26-advarsler.
- 2026-09-25: `DEPLOY OK 41758af` — GitHub Actions-run `36082138701` deployede alle fire sites grønt. Live-contentcheck af de fire EN/DA-sider fandt de nye licens- og lokalitetsoplysninger, mens de gamle claims var fraværende. CI meldte kun eksisterende Node 20-/Ubuntu-26-advarsler.

## Commitlog

- Stripe-kompatibel Page Profile-licens: `ea4e6c3` — `Ret Page Profile Stripe-licensen`.
- Domæneopdelt trafik- og salgsledger: `df25c8b` — `Gør trafikdata domæneopdelt og troværdige`.
- Fail-closed review-rettelser: `9569979` — `Gør trafikledgeren fail-closed`.
- Research og initial plan: `10c5908` — `Lav en prioriteret plan for næste Hermes-iterationer`.
- Fjern død Lemon-webhook: `28c7f64` — `Fjern den døde Lemon-webhook`.
- Gør DeskUptime-teksten sand: `41758af` — `Gør DeskUptime-teksten sand`.
- Gør robots, sitemap og domænedrift korrekt: `fb4189d` — `Gør robots, sitemap og domænedrift korrekt`.
- Ret deploy-gaten efter Wrangler-forurening: `b7c8a64` — `Ret deploy-gaten efter Wrangler-forurening`.
