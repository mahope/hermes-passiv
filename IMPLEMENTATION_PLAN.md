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
- **Det der lå i live, var *bygget*, ikke skrevet** — 3 gange samme uge: 8
  generatorer døde i browseren, 37 sider uden donationslinje, 44 artikler med
  dobbelt værktøjsliste. Målt 1/10 i rigtig browser: 0 konsolfejl på 14 sider,
  197 anker-referencer dømt.
- **En regel skrevet ned uden en dom der kan fejle, er den dyre fejlform:** CEO-kø
  punkt 0 rettede *sisyv* klienter og den tiende lå ved siden af. En opgave skal
  nævne et **antal** *og* liste filerne.
- **Seks gratisværktøjer sluttede med en donation på 10 kr.** Målt 1/10 på live:
  **0** `buy.stripe.com` i resultatet på `/cookie-check`,
  `/security-headers-check`, `/contrast-checker`, `/text-on-image-checker` og
  `/url-inspector`. Rettet 1/10: alle **6** skannere har nu købsknappen i den
  markup et gennemført tjek renderer (baseline 1 → 6). `/url-inspector` sælger
  Page Profile Pro ($19/år), de andre EUComply Pro ($79/år pr. website).
- **❓ Til Mads:** `OPENROUTER_API_KEY`, `STATS_TOKEN`, `bugbottle.dev`s domæne,
  banner-placering på 180 sider, de 2 desktop-apps der ringer til Lemon
  Squeezy, Search Console. Historie: `docs/plan-arkiv.md`.

## Verificér deploy

- `VERIFICÉR DEPLOY: købsknappen på $79/år pr. website i resultatet af
  /compliance-site-check (EN + DA) ceo/pro-handoff-efter-scan 2026-10-01` —
  skal måles på **indhold**, ikke på HTTP 200: live `/compliance-site-check`
  skal have `pro-card` og `eVq00i4YH6UG69g0ObbMQ03` i sit inline-script, og det
  samme på `/da/compliance-site-check` med `/da/compliance-report`. Kun en
  statisk knap er ikke nok: dommen i `tests/scan-clients.test.mjs` sektion 11
  kræver, at linket *kun* findes i scriptet. Kan ikke efterprøves: et rigtigt
  køb kræver en gyldig Stripe-nøgle.

- `VERIFICÉR DEPLOY: workeren melder sine egne fejl ceo/workeren-melder-sentry 2026-10-01`
  — live `build-info.json` skal bære merge-sha'en på de 3 deployede domæner,
  og **indhold**: `GET /api/url-inspect?url=https://example.com` skal svare
  **200** (ikke 500/1101 — guarden pakkede hele rutedispatcheren, så ruten er
  den vigtigste at efterprøve), `GET /api/license/validate` med `ZZZ` skal
  svare **400**, `GET /api/ukendt-rute` skal svare **404**, en ukendt
  `/downloads/`-sti skal svare **404**, og `GET /api/paid-files` skal svare
  med `kv_ok: true`. *Efterprøves ikke:* en rigtig rapport i Sentry — den
  kræver at en fejl faktisk sker i prod, og man slår ikke fejl til for at lave
  en rapport. Beviset ligger i stedet i `tests/stripe-worker.test.mjs`:
  12 kontroller hvoraf 5 er målt røde mod `54fcc7e`-koden.

- `VERIFICÉR DEPLOY: samme købsvej i resultatet på de fem øvrige skannere
  ceo/pro-handoff-fem-skantere 2026-10-01` — måles på **indhold**: live
  `/cookie-check` og `/da/cookie-check` skal have `eVq00i4YH6UG69g0ObbMQ03`
  inde i deres inline-script (den lå slet ikke i filen før), live
  `/security-headers-check` skal have `<div id="shc-pro"` **og**
  `getElementById('shc-pro').hidden = false`, live `/contrast-checker` +
  `/da/contrast-checker` skal have `<div id="cc-pro"` med samme afsløring,
  live `/text-on-image-checker` + `-da` skal have `var PRO_CARD`, og live
  `/url-inspector/` skal have `<div id="ui-pro"` med `9B6eVcgHp7YK69ggN9bMQ04`
  (Page Profile Pro). Sidstnævnte må ikke have `.pro-card`-regler i sin egen
  `<style>` mere — de ligger i `site/style.css`. *Efterprøves ikke:* et rigtigt
  køb kræver en gyldig Stripe-nøgle. Dommen er `tests/scan-clients.test.mjs`
  sektion 11b, som kører hvert værktøj rigtigt igennem i sandkassen.

## Åbne opgaver

1. ~~**Samme købsvej på de øvrige gratis tjek.**~~ **FÆRDIG 30/9,
   `ceo/vej-til-betalt-otte-tjek` (66172a0).**
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
5. **UptimeRobots Team-pris er et regnestykke, der ikke holder.** Fund fra
   review 1/10: `tools/competitor_prices.json` siger `per_year: €492` med en
   `source_note` der regner €35 × 12 = 420, altså €492 er **u**rabatteret
   listepris × 12, mens Solo (`€108` = €9 × 12) er rabatteret — altså er den
   ene række i samme kolonne rabatteret og den anden er det ikke. Målt 1/10 på
   UptimeRobots egen prisside: **«Team € 420 /y»**. Rettelse: `per_year` → €420
   med opdateret `checked`, cellen på
   `/blog/desktop-website-monitor-cli` skal sige €420, og `plans_allowed()` skal
   få en dom på at `per_year == per_month_annual × 12`, ellers forsvarer porten
   det forkerte tal fordi den kun *tillader* beløb. Accept: `python3
   tools/check_competitor_prices.py` grøn, €492 nul gange i `dist/`, og en
   mutation der lægger €492 tilbage er rød.
6. **Review-fund: `/api/compliance-ai` er publiceret og dør med 503.** Fund fra
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
