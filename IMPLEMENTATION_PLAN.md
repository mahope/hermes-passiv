# STATUS

- **Scanningen tager nu flere URL'er, så Pro-løftet holder.** Rettet 1/10:
  `/compliance-site-check` (EN+DA) har et tekstfelt med én URL pr. linje, op til
  5 pr. kald, og serveren svarer én rapport pr. URL med et overblik først.
  Førhen tog feltet én URL, mens produktsiden lovede at Pro «crawls the site».
- **Fetch-budgettet er delt pr. kald, ikke pr. URL** — ét kald koster højst 12
  ude-kald uanset hvor mange URL'er der står i, ellers ville 5 URL'er være 60.
- **❓ Til Mads:** `OPENROUTER_API_KEY`, `STATS_TOKEN`, `bugbottle.dev`s domæne,
  banner-placering på 180 sider, de 2 desktop-apps der ringer til Lemon
  Squeezy, Search Console. Historie: `docs/plan-arkiv.md`.

## Verificér deploy

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

- `VERIFICÉR DEPLOY: compliance-scanneren tager flere URL'er pr. kald
  ceo/flere-urler-i-scanning 2026-10-01` — måles på **indhold**: live
  `GET /api/compliance-scan?url=scan.example%0Aexample.org` skal svare 200 med
  `multi:true` og to entries i `reports`, ét URL skal svare i den gamle form
  (intet `multi`), og `/compliance-site-check` + `/da/compliance-site-check`
  skal have `<textarea id="urlInput"` og `SCAN_MAX_SITES = 5`. Dommen er
  `tests/stripe-worker.test.mjs` (330/330) og `tests/scan-clients.test.mjs`
  (204/204) — begge kan fejle: mutationen på EN's genkaldskæde kører den gamle
  kode, og budget-dommen tæller ude-kald mod to tunge værter.


## Åbne opgaver

1. **Flere sider end forsiden pr. URL — det er stadig den store forskel.** Hvorfor:
   feltet tager nu 5 sites, men hvert site tjekkes kun på forsiden; Pro gør det
   samme for hver side den finder. Accept: et URL med en dyb sti (`/kontakt`)
   scannes på den side, og overblikket siger hvilken side der blev tjekket.
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
5. **DA-siden mangler download-knappen på rapporten.** Hvorfor:
   `downloadReport()` findes på `/da/compliance-site-check`, men ingen knap
   kalder den — kun EN har den. Målt 1/10 ved at læse begge filers markup.
   Accept: knappen er på DA også, eller funktionen er væk.
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
4. **En købsvej til Clean Copy Pro i værktøjet på cleancopy.tools.** Hvem: de 7
   besøgende i 28 dage, hvor `/clean-copy-tool` er indgangen. Tal: betalinger pr.
   uge (baseline 0 målt). Accept: efter et renset resultat ligger der én knap
   med pris **og** periode fra `stripe_catalog.json`, dømt af samme sektion 11b.
   Datagrund: 22 skriver `/year`, 10 `once`, 15 `lifetime` i katalogen, så
   `$19` alene afslører intet; de to ruter har hver sit eget købsflow i dag.
