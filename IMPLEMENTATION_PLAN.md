# STATUS

- **Page Profile Pro kunne ikke aktiveres overhovedet.** `page-profile --activate`
  fik **403 Cloudflare Error 1010** på alle fire felter, fordi `urllib` sender
  `Python-urllib/3.x` som User-Agent. Rettet 1/10: vi udgiver `1.2.1`.
- **AI-siden er død for alle besøgende.** Målt 1/10: `POST /api/compliance-ai`
  svarer **503** «AI service not configured» (`OPENROUTER_API_KEY` mangler). Den
  er publiceret og gør intet. Se ❓.
- **Ingen fejl blev nogensinde meldt.** Målt 1/10: 0 forekomster af «sentry»
  i hele repoet. Workerens fetch er nu pakket, så en uventet fejl er en ren 500
  *og* en rapport — 316/316 worker-tests, 5 mutationer røde mod ældre kode.
- **Artiklen om Desktop-website-monitoren solgte €492 for et UptimeRobot-team.**
  Fund fra review 1/10: €492 er €41 × 12, altså månedsprisen *uden* rabat,
  mens Solo i samme kolonne var €9 × 12 = €108, altså *med* rabat — to
  betalingsgrundlag i én «1 year»-kolonne. Målt 1/10 på deres egen prisside:
  «Team € 420 /y» (og «Scale € 780 /y» = €65 × 12). Rettet 1/10, og porten
  dømmer nu at et årstal er den årlige månedspris × 12 (17/17 kontroller).
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

- `VERIFICÉR DEPLOY: UptimeRobot Team-prisen er €420, ikke €492
  ceo/uptimerobot-team-pris 2026-10-01` — måles på **indhold**: live
  `/blog/desktop-website-monitor-cli` skal have `&euro;420` i samme celle som
  `&euro;35/month`, og `492` skal være **0** gange i hele siden. Dommen er
  `tools/check_competitor_prices.py` (grøn på 303 sider) med den nye regel at
  `per_year` er `per_month_annual` × 12 — målt **rød** mod de gamle tal, både
  som `KILDEFEJL` i kilden og som `forkert pris` i cellen, mens porten fra
  `origin/main` var grøn med dem.

## Åbne opgaver

Køen er udtømt for ufærdigt arbejde: **opgave 1 er den eneste der ikke
blokerer på Mads**, så den er næste iteration. 2–5 ligger fast på en
beslutning eller en secret (❓ nedenfor) og skal ikke genoptages, før de
er besvaret.

1. **Pro-løftet «crawls the site» er ikke indholdet i scanningen.** Hvorfor:
   `/compliance-site-check` tager én URL og scanner den, mens produktsiden for
   EUComply Pro lover at Pro «crawls the site» — så det betalte ikke er noget,
   kunden kan se forskel på. Feature-kø #1. Accept: feltet tager linjeskift,
   serveren svarer én rapport pr. URL, og knappen i resultatet siger ærligt at
   Pro gør det samme for hele sitet. Dømt af `tests/scan-clients.test.mjs`
   (mutation på den nye klientdel skal være rød). Baseline: betalinger pr.
   uge 0 målt 1/10. **Dette er den næste opgave.**
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
5. **Review-fund: `/api/compliance-ai` er publiceret og dør med 503.** Fund fra
   review 1/10: `POST /api/compliance-ai` svarer **503** «AI service not
   configured. Contact the site owner.», fordi `OPENROUTER_API_KEY` mangler —
   og `/compliance-ai` + `/da/compliance-ai` står begge i `sitemap.xml`. Den nye
   Sentry-guard fanger den ikke, fordi 503 er en håndteret tilstand. Rettelse:
   enten sæt nøglen, eller tag de to sider ud af sitemap og `build_sites.py` til
   den er sat. Accept: ingen sitemap-rute uden en funktion der svarer. *(Se
   ❓.)*

## ❓ Til Mads

- **🔴 `OPENROUTER_API_KEY` mangler på workeren — AI-siden er død for alle.**
  Målt 1/10: `POST /api/compliance-ai` svarer **503** «AI service not
  configured» (`_worker.js:733` læser `env.OPENROUTER_API_KEY`). Klienten
  håndterer det pænt, så intet er brudt — men `/compliance-ai` er en publiceret
  funktion, som artikler på både EN og DA linker til, og den gør intet. En
  secret på workeren. **Alternativ:** hvis AI'en ikke skal være permanent, skal
  siden sige at funktionen er i beta og ikke lover et svar, og de to ruter skal
  ud af sitemap (opgave 6).
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

1. **Flere URL'er pr. scanning.** Hvem: bureauet der scanner fem kunders sites
   og så må købe fem gange. Tal: betalinger pr. uge (baseline 0 målt).
   Accept: feltet tager linjeskift, serveren svarer én rapport pr. URL, og
   knappen siger ærligt at Pro gør det samme for hele sitet. Datagrund:
   scanningen kan i dag kun tage én URL, selv om produktsiden siger at Pro
   «crawls the site».
2. **E-bøgerne læses online, kapitel for kapitel.** Hvem: den der læser en
   GDPR- eller NIS2-bog før han køber bundlet. Tal: køb fra `/books`
   (baseline 0). Accept: hver bogside har en læsevisning med de første kapitler
   og én købsknap til sit bundle-link. Datagrund: Cloudflare tæller 90011
   sidevisninger på mahope.tools i 28 dage mod Plausibles 17, så bøgerne er det
   største indhold vi har og ligger uden for målingen.
3. **`/compliance-ai` som ikke gør ingenting.** Hvem: alle der lander på siden
   fra artiklerne. Tal: kald pr. uge (baseline: **0**, siden secret'en mangler).
   Accept: enten secret på workeren, eller siden siger at funktionen er i beta
   og ikke lover et svar — og begge ruter tages ud af sitemap. Datagrund: målt
   1/10 — 503 «AI service not configured» (`_worker.js:733`). Se ❓.
4. **En købsvej til Clean Copy Pro i værktøjet på cleancopy.tools.** Hvem: de 7
   besøgende i 28 dage, hvor `/clean-copy-tool` er indgangen. Tal: betalinger pr.
   uge (baseline 0 målt). Accept: efter et renset resultat ligger der én knap
   med pris **og** periode fra `stripe_catalog.json`, dømt af samme sektion 11b.
   Datagrund: 22 skriver `/year`, 10 `once`, 15 `lifetime` i katalogen, så
   `$19` alene afslører intet; de to ruter har hver sit eget købsflow i dag.
