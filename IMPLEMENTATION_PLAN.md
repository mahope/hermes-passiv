# STATUS

- **Scannen siger nu hvilken side den læste.** Rettet 1/10: indsender du
  `example.dk/kontakt`, står der `Checked: /kontakt`, og et resultat med dyb
  sti tæller de sider kaldet hentede. Før stod «the score is the homepage»
  overalt, også når netop ikke forsiden var tjekket — rapporten løgnede, og den
  samme tekst lå i den rapport, kunden sender videre. Baseline 1/10: 4 kald til
  `/api/compliance-scan` i testene på 213/213, klienten sagde «the score is the
  homepage» på EN og «scoren er forsiden» på DA.
- **«Check Site»-knappen var hvid i den publicerede scanner.** Fund fra samme
  iteration: `pagepass.OWNED_SELECTORS` påstod at designsystemet ejer
  `.input-group button`, `style.css` erklærede den aldrig, så bygget strippede
  sidens regel og knappen faldt tilbage på `button:not([class])` — hvid med
  mørk tekst, 2,52:1 mod blå baggrund ved hover. Målt på live `e69baa6` 1/10
  (`.input-group button {` 0 gange i den publicerede CSS). Rettet i
  `style.css`; ny dom i `check_design_tokens.py` fanger påstanden fremover.
- **❓ Til Mads:** `OPENROUTER_API_KEY`, `STATS_TOKEN`, `bugbottle.dev`s domæne,
  banner-placering på 180 sider, de 2 desktop-apps der ringer til Lemon
  Squeezy, Search Console. Historie: `docs/plan-arkiv.md`.

## Verificér deploy

- `VERIFICÉR DEPLOY: scanneren siger hvilken side den læste
  ceo/scanner-siger-hvilken-side 2026-10-01 19:40` — måles på **indhold** på
  `https://mahope.tools/compliance-site-check` og `/da/compliance-site-check`.
  Baseline målt 1/10 på live `e69baa6` (endnu ikke deployet):
  `scanned_url` **0** gange i begge scripts, `site-page` **0** gange,
  og den publicerede `/style.css` har `.input-group button` **0** gange.
  Dommen bliver derfor:
  1. `scanned_url` står **1** gang i hvert script,
  2. `class="site-page"` står **1** gang i hvert script,
  3. `scannetSide` **1** gang i hvert script,
  4. `pages_checked` **1** gang i hvert script,
  5. `the score is the homepage` og `scoren er forsiden` **0** gange,
  6. `https://mahope.tools/style.css` har `.input-group button` **1** gang,
  7. `GET /api/compliance-scan?url=example.dk/kontakt` svarer 200 med
     `scanned_url` der indeholder `/kontakt` og `pages_checked` > 1.
  Dommen er `tests/scan-clients.test.mjs` (221/221) + `tests/stripe-worker.test.mjs`
  (333/333): begge røde på den gamle kode (215/221 hhv. 330/333), grønne på den
  nye. `check_design_tokens.py --self-test` fanger fejlen i punkt 6.

- `DEPLOY OK 2026-10-01` — Pro-kort i resultatet af Clean Copy-webværktøjet.
  Målt på **indhold** på live `e69baa6` (`build-info.json` → `e69baa688c73`):
  `id="pro-nudge"` **1** gang, `function proCard` **1** gang,
  `6oU4gy76PgvgdBIdAXbMQ00` **2** gange (1 i den statiske HTML fra det
  eksisterende Pro-afsnit, 1 i scriptet fra det nye kort) — altså præcis de tre
  domme noten krævede.

- `DEPLOY OK 2026-10-01` — compliance-scanneren tager flere URL'er pr. kald.
  Målt på live `209baa0`: `GET /api/compliance-scan?url=scan.example%0Aexample.org`
  → 200 med `multi: true` og to entries i `reports`; ét URL svarer i den gamle
  form uden `multi`; `/compliance-site-check` + `/da/compliance-site-check` har
  `<textarea id="urlInput"` og `SCAN_MAX_SITES = 5`.

- `DEPLOY OK 2026-10-01` for de tre noter under «Verificér deploy» 1/10 (købsknap
  i scannerens resultat, workerens Sentry-guard, samme købsvej i de fem øvrige
  skannere). Målt på live `21acd2f`: `/compliance-site-check` +
  `/da/compliance-site-check` har `pro-card` og `eVq00i4YH6UG69g0ObbMQ03` i
  scriptet (DA linker til `/da/compliance-report`); `/cookie-check`,
  `/contrast-checker`, `/text-on-image-checker`, `/security-headers-check`
  (med `getElementById('shc-pro').hidden = false`) og `/url-inspector/`
  (med `9B6eVcgHp7YK69ggN9bMQ04`) har hver sit `*-pro`-element i scriptet, og
  **0** sider har `.pro-card`-regler i egen `<style>` længere; workeren svarer
  200 på `/api/url-inspect`, 400 på `validate` med `ZZZ`, 404 på
  `/api/ukendt-rute` og på en ukendt `/downloads/`-sti, og
  `{"ok":true,"kv_ok":true}` på `/api/paid-files`. *To noter havde forkerte
  URL'er:* de danske skannere ligger på `/cookie-check-da` og
  `/contrast-checker-da`, ikke under `/da/` — `/da/cookie-check` er 404.

- `DEPLOY OK 2026-10-01` — UptimeRobot Team-prisen er €420, ikke €492.
  Målt på **indhold** i live `0f64110`: `/blog/desktop-website-monitor-cli` har
  `&euro;420` 1 gang i samme celle som `&euro;35/month`, og `492` er **0**
  gange i hele siden. `build-info.json` bærer `0f64110a09a9`.

- `DEPLOY OK 2026-10-01` — `/compliance-ai` siger at assistenten er slukket, og
  de to ruter er ude af sitemap + llms.txt. Målt på live `bda70e2`: `GET
  /api/compliance-ai` → 200 `{"ok":true,"available":false}`, begge sider har
  `aiUnavailable` ×2 og `noindex,follow`, og `compliance-ai` er **0** gange i
  `sitemap.xml` og `llms.txt`.


## Åbne opgaver

1. ~~Flere sider end forsiden pr. URL.~~ **Halvdelen leveret 1/10.** Et URL med
   en dyb sti scannes på *den* side, og overblikket, det enkelte resultat og den
   downloadede rapport siger hvilken side og hvor mange sider der blev læst —
   det var planens acceptkriterium, og det er grønt. **Resten:** kaldet læser
   stadig kun den indsendte side plus de juridiske stier den gætter på
   (`/privacy`, `/terms`, …), ikke hele sitet; det er det Pro gør. Accept:
   scanneren følger links fra forsiden og tjekker de sider den finder, med det
   delte `CSC_MAX_PAGES`-budget uændret.
2. **Konvertering kan ikke måles uden `STATS_TOKEN`.** Hvorfor:
   `/api/stats` svarer 401 siden uge 37, så næsten hver linje i enhver
   trafikrangering er vor egen links-tælling, ikke besøg. Den nye port har samme
   problem og siger det i hver kørsel. Accept: `GET /api/stats` med token
   svarer 200. *(Blokeret på Mads — se ❓.)*
3. **`bugbottle.dev` deployes ikke.** Hvorfor: `deploy-sites.yml`-matrixen
   deployer kun tre domæner, så `dist/bugbottle.dev/` bygges hver kørsel og
   lægges ingen steder; live er 61 ruter fra en anden udgivelse. Det er derfor
   `traffic_status` er `partial` hver time og `reports/weekly/` mangler et helt
   domæne. Den nye port måler `/bugbottle-demo` og dømmer den ikke, fordi samme
   grund gør dom 4/7 i artikelporten umulige at dømme. Accept: enten domænet på
   Pages og fjernet af `UNMANAGED_DOMAINS`, eller fjernet fra `TRACKING_DOMAINS`
   så status bliver ærlig. *(Beslutning — se ❓.)*
4. **180 sider har to-tre knapper over folden.** Hvorfor:
   `add_top_cta_495.py` og `add_ai_cta.py` har skudt scanner- og AI-banneren
   ind under `</header>` på hele bloggen, så de ligger over folden på 180 af 224
   sider med hero — og på mange er heroens egen primære et anker (`#content`,
   `#how`). Målt 30/9 af `check_first_action.py`. Accept: bannerne er enten
   flyttet ned i artiklen på de mest besøgte sider (dømt i
   `tools/first_action.json`), eller slettet fra hele bloggen så AI-CTA'en
   ligger ét sted pr. side. Kræver beslutning — se ❓.
5. ~~DA-siden mangler download-knappen på rapporten.~~ **Ikke et problem.**
   Optaget på en måling af kildefilerne 1/10, men målt på live: både EN og DA
   har `dlReport` to gange og `function downloadReport` én gang. Flyttet til
   `docs/plan-arkiv.md`.
6. **En sitemap-rute må ikke have en død eneste handling.** Hvorfor:
   Fund fra review 1/10 blev rettet for `/compliance-ai`, men porten dømmer kun
   de to ruter, der er skrevet i `tools/unavailable_routes.json` — en ny AI-
   eller beta-side kan stadig publiceres med en handling, der altid fejler.
   Accept: porten finder den, hvis den skrives i manifestet. *(Kun relevant når
   vi tilføjer flere sådanne sider — ikke en opgave i sig selv.)*

## ❓ Til Mads

- **🔴 `OPENROUTER_API_KEY` mangler på workeren — assistenten er stadig slukket.**
  Rettet 1/10, så ingen kunde længere skriver et spørgsmål og bliver bedt om at
  kontakte os: siden siger nu at assistenten er slukket og byder på scanner,
  erklæringsgenerator og de tre bøger, og begge ruter er ude af sitemap og
  `llms.txt`. **Når du sætter nøglen:** fjern `<meta name="robots"
  content="noindex,follow">` fra `site/compliance-ai.html` og
  `site/da/compliance-ai.html`, så slutter de i sitemap igen. Chatten tænder
  selv — kapabilitets-tjekket læser nøglen direkte, så der er ingen anden kode
  at rette. `tools/check_unavailable_routes.py` fortæller dig hvis du glemmer
  den ene halv.
- **🟡 Skal scanner- og AI-banneren ligge over folden på 180 sider?** Målt 30/9
  giver det **tre knapper oven på folden** pr. artikel, og på 30 af dem er
  knappen *oveni* et anker som «læs videre», så det værktøj artiklen handler om
  ikke er den primære handling. Jeg har rettet de to mest besøgte artikler. Enten
  flytter jeg banneren ned i artiklen på de næste mest besøgte, eller jeg sletter
  den fra hele bloggen, så AI-CTA'en ligger ét sted pr. side. Det er din beslutning,
  fordi det er en promo du har bedt om.
- **🔴 `STATS_TOKEN` på workeren.** Én linje, én secret, og så kan konvertering
  måles i stedet for gættes. Uden den er `/api/stats` 401, og opgave 2 bygger på
  tal, der ikke er besøg.
- **🔴 `bugbottle.dev` ligger på en server, vi ikke deployer.**
  `https://bugbottle.dev/build-info.json` svarer **404 fra `nginx`**, ikke
  Cloudflare, mens de tre andre domæner bærer alle samme sha. To veje: (a)
  domænet skal på Cloudflare Pages → opsæt `bugbottle-dev`-projektet, så
  tilføjer jeg domænet til matrixen og fjerner undtagelsen i samme commit;
  (b) domænet er ikke vores at udgive → det skal ud af `TRACKING_DOMAINS`, så
  `traffic_status` bliver ærlig `ok` for de tre vi faktisk deployer.
- **🔴 To betalte desktop-apps kan ikke aktiveres.** Målt i de shippede binære:
  `mahope/transmute` `v0.2.1` og `mahope/deskuptime` `desktop-v0.2.7` har begge
  `https://api.lemonsqueezy.com/v1/licenses/activate` indbygget, og binæren
  sender `license_key` + `instance_name` og læser `activated`, `id`,
  `product_name`, `customer_email` — mens vores `/api/license/activate` kræver
  `{ license_key, device_id, product }`. Serveren er tolerant over for
  `instance_id` som alias for `device_id`; `instance_name` giver jeg ikke.
  Kilden ligger i private repos, og du laver selv releases.
- **Search Console:** tilføj de fem domæner som properties (`mahope.tools`,
  `cleancopy.tools`, `deskuptime.com`, `bugbottle.dev`, `transmute.run`).
  Sitemap og robots er målt korrekte på de fire sites missionen udgiver; kun
  property-tilføjelsen mangler.
- **Er desktop-appen stadig en del af `deskuptime-pro`?** Et betalt produkt skal
  kunne det, det lover.
- **Plugin-version:** kunder på Clean Copy 1.1.0 henter ikke den rettede zip.
  Kræver en version bump — og det er en release, som er din.

## Feature-kø

Prioriteret efter hvor tæt den er på penge, ikke efter hvor let den er at kode.
Baseline for hvert tal er målt 1/10; tallene er ikke vores egen trafik.

1. ~~Flere URL'er pr. scanning.~~ **Leveret 1/10** — feltet tager linjeskift,
   serveren svarer én rapport pr. URL, og Pro-boksen siger ærligt at Pro gør
   det samme for hver side den finder. Næste skridt er punkt 1 under «Åbne
   opgaver»: flere sider end forsiden pr. URL.
2. **E-bøgerne læses online, kapitel for kapitel.** Hvem: den der læser en
   GDPR- eller NIS2-bog før han køber bundlet. Tal: køb fra `/books`
   (baseline 0). Accept: hver bogside har en læsevisning med de første kapitler
   og én købsknap til sit bundle-link. Datagrund: Cloudflare tæller 90011
   sidevisninger på mahope.tools i 28 dage mod Plausibles 17, så bøgerne er det
   største indhold vi har og ligger uden for målingen.
3. **`/compliance-ai` som ikke gør ingenting.** Hvem: alle der lander på siden
   fra artiklerne. Tal: kald pr. uge (baseline: **0**, siden secret'en mangler).
   **Delvis leveret 1/10:** siden siger det ærligt og ruterne er ude af de
   genererede lister, så den ikke længere skader nogen. Resten kræver
   `OPENROUTER_API_KEY` — se ❓. Datagrund: målt 1/10 — 503 «AI service not
   configured», `cf-cache-status: DYNAMIC`.
4. ~~En købsvej til Clean Copy Pro i værktøjet på cleancopy.tools.~~
   **Leveret 1/10** — efter en konvertering ligger der ét Pro-kort med batch,
   egne rense regler og knappen «Buy Clean Copy Pro — $19/year», skjult for
   aktiverede Pro-kunder. Målt først: 0 købsknapper i resultatet. Næste skridt
   er punkt 2 — bøgerne læses online.
5. ~~Scanneren siger hvilken side den læste.~~ **Leveret 1/10** — overblikket,
   det enkelte resultat og den downloadede rapport siger det, og et dybt URL
   scannes på den side det angiver. Målt først: «the score is the homepage»
   stod på siden uanset input. Ny accept for resten af opgaven: scanneren
   følger links fra forsiden, så `pages_checked` kan overstige de gættede stier.
