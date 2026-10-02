# STATUS

- **Rødt CI 2/10 var uret, ikke licensserveren.** `rateLimitIp` tæller i hele
  time-bøtter, og «rapporten over grænsen»-sløjfen lå da grænsen krydsede (push
  04:59:41, dømt 05:00:00): 200 i stedet for 429. Sløjferne har nu et fast ur, og
  gatestrækket `stripe-worker-ur` kører suiten under et ur der hopper en time
  hvert 30. ms. Målt ved mutation: uden pinnet ur rød med CI's egen fejltekst.
- **Alle 19 sider har gratis mod Pro i samme tabel.** De ni øvrige værktøjssider
  (`/scan`, `/compliance-site-check`, `/cookie-check`, `/contrast-checker`,
  `/security-headers-check` i begge sprog) har katalogens tabel i stedet for en
  håndskrevet `.pro-list` der kun talte om Pro. Dom: `check_pro_table.py`
  (8 produktsider + 11 værktøjssider), `pro_table.py --check` på dist.
- **Ny port `check_catalog_where.py` kører i gaten.** Dom 6 og dom 4 i
  `check_pro_table` dømmer *hvad* tabellen siger mod katalogen, men ingen port
  læste de 112 `where` der skal sige *hvor* koden findes: målt 2/10 lå 13 af dem
  2–10 linjer væk fra den sætning de citerede. Alle 13 rettet i katalogen.
- **Ærligheden overlevede — målt 2/10.** Den genererede tabel skrev «Every page
  of the site, not just the one you pasted», altså præcis den sætning
  `scan-clients` holder i live («crawls the whole site … every page it finds»).
  Rettelsen ligger i katalogen, så alle ni sider får den ærlige formulering.
- **CEO-kø punkt 0 er færdigt** — `5693853`: `/api/url-inspect` → 200, 202 på
  `/thanks` siger «not confirmed yet», 429 er endelig, SSRF-værnet dækker hvert hop.
- **PR-tjek 1/10:** 0 åbne PR'er. **Branch-tjek:** ingen 14 dage gamle branches.
- **❓ Til Mads:** `OPENROUTER_API_KEY`, `STATS_TOKEN`, `bugbottle.dev`s domæne,
  banner-placering på 180 sider, de 2 desktop-apps der ringer til Lemon Squeezy,
  Search Console, og **bogenes betalte udgave** (se ❓).

## Verificér deploy

- Alle fem noter fra 1.–2. oktober er **målt på indhold** og lukket 2/10
  (`DEPLOY OK 2/10`): gratis-mod-Pro-tabellen, `/net.js`, det delte
  rapport-budget, kontrasttjekkeren i artiklerne og AI-banneren.
  Detaljerne står i `docs/plan-arkiv.md`.

- `VERIFICÉR DEPLOY: gratis mod Pro i kortet på de ni øvrige værktøjssider
  ceo/pro-kort-tabel-alle 2026-10-02` — måles på **indhold**. Målt 2/10 kl. 08:
  `build-info.json` på live står stadig i `543a734`, altså de 2 sidste commits
  blev **aldrig deployet** — CI var rød, så Actions rullede dem ikke ud. Derfor
  står `pro-table:start` 0 gange på alle ni live-sider. Den her rettelse gør CI
  grøn igen, så samme note gælder den næste deploy. Dom 1: `python3
  tools/quality_gate.py` er grøn med 134 steps. Dom 2: `python3
  tools/pro_table.py --check` på dist siger «19 sider». Dom 3:
  `check_catalog_where.py` er grøn på 112 funktioner og dømmer **belægget** i
  katalogens `where`; dens 11 mutationer ligger i `--self-test` i samme gate.
  Dom 4: `node tests/scan-clients.test.mjs` 417/417, altså den ærlige
  crawls-sætning står stadig i kortet. Dom 5: `check_pro_table.py --self-test`
  21/21 og `pro_card.py --self-test` 8/8. Dom 6: `node tests/clock_jump.mjs`
  352/352 — CI's røde fejl kan ikke komme tilbage.

## Åbne opgaver

1. ~~Flere sider end forsiden pr. URL.~~ **Færdig 1/10.** Kaldet læser den
   indsendte side og de juridiske sider forsiden *linker til* — kun på sitets
   eget domæne — før det gætter stier, og svaret lister dem i `pages_read`.
   Accept nået: `pages_checked` overstiger de gættede stier, og fundet peger på
   den linkede side. Flyttet til `docs/plan-arkiv.md`.
2. ~~Generatorerne lavede dokumentet, men ikke vejen videre.~~ **Færdig 2/10.**
    Alle otte generatorer (DPA, NIS2, RoPA, privacy notice, EAA-erklæring —
    EN + DA) har nu et kort på resultatet med den betalte vare der svarer til
   deres eget output, pris og periode læst fra `tools/stripe_catalog.json`.
   Flyttet til `docs/plan-arkiv.md`.
3. **Konvertering kan ikke måles uden `STATS_TOKEN`.** Hvorfor:
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
7. ~~`check_pro_table.py` kører ikke i gaten.~~ **Færdig, målt 2/10** med
   `quality_gate.py --list` — `pro-table` og `pro-table-selftest` står i
   `STEPS`, så opgavens egen beskrivelse var forældet. De to nye steps
   `catalog-where` og `catalog-where-selftest` er kablet på samme måde, og
   `tools/test_deploy_workflow.py` bekræfter at filerne er i CI's path-filter.
7. **Bogen har ingen DA-udgave, og læsevisningen gør det tydeligt.** Hvorfor:
   de seks boger er på engelsk, og hele `_worker.js`, scanneren og resten af
   mahope.tools findes på dansk. Læsevisningen gør bogen mere læsbar end før,
   og dermed mer synlig for en dansk læser der ellers ville havedownloadet den
   uden at læse. Accept: enten en DA-udgave af de to vigtigste bøger
   (`gdpr-for-agencies`, `nis2-for-agencies`) som EPUB i `ebook/`, eller en
   synlig dansk note på bogside-ruterne om at bogen findes på engelsk. Kræver
   beslutning — se ❓. Baseline 1/10: 0 danske EPUB'er, og 6 bogsider uden
   dansk sætning.

## ❓ Til Mads

- **🔴 `OPENROUTER_API_KEY` mangler på workeren — assistenten er stadig slukket.**
  Rettet 1/10, så ingen kunde længere skriver et spørgsmål og bliver bedt om at
  kontakte os: siden siger nu at assistenten er slukket og byder på scanner,
  erklæringsgenerator og de tre bøger, og begge ruter er ude af sitemap og
  `llms.txt`. **Når du sætter nøglen:** fjern `<meta name="robots"
  content="noindex,follow">` fra `site/compliance-ai.html` og
  `site/da/compliance-ai.html`, så slutter de i sitemap igen. Chatten tænder
  selv — kapabilitets-tjekket læser nøglen direkte, så der er ingen anden kode
  at rette.   `tools/check_unavailable_routes.py` fortæller dig hvis du glemmer
  den ene halv. **Banneren på de 187 artikler følger samme nøgle:** sæt
  `"available": true` i `tools/ai_cta.json`, kør
  `python3 tools/check_ai_cta_honesty.py --apply`, og de gamle
  «Ask the Compliance AI»-tekster kommer tilbage på alle 187 sider. Gaten er
  rød, indtil det er gjort.
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
- **🔴 Bogen er gratis, men Stripe har et betalt bundlet produkt.** Kontrakten
  lister `eu-compliance-ebook-bundle` til **$29**
  (`https://buy.stripe.com/fZu9AScr9a6SbtA68vbMQ0b`), mens **syv** publicerede
  sider siger modsatte: «Free download — no signup, no email. This e-book is
  free, and it stays free — we do not sell a paid edition of it» og på
  `/books/compliance-bundle` «nothing is left out, and nothing is reserved for
  a paid edition». Vi har aldrig linket til det betalte link, så det ligger og
  venter. Feature-kø sagde «én købsknap til sit bundle-link» — den har derfor
  **ikke** fået en knap, fordi den ville være en købsknap til noget syv sider
  siger er gratis. To veje: (a) vi sletter produktet og linket i Stripe, så
  kontrakten og siderne er enige; (b) vi laver en **ny** betalt udgave der rent
  faktisk betaler sig — fx de samme bøger i PDF + Word + de opdaterede
  revisioner, eller en 2027-udgave — og skriver dens ærlige beskrivelse. Det er
  din beslutning, fordi det er dit navn på kvitteringen.
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
   serveren svarer én rapport pr. URL, og Pro-boksen siger ærligt hvad den
   *ikke* ser. Næste skridt var punkt 1 under «Åbne opgaver»: det er gjort.
2. ~~E-bøgerne læses online, kapitel for kapitel.~~ **Leveret 1/10** — alle seks
   bogside-ruter viser kapitel 1 og 2 i fuld tekst, bygget af den EPUB kunden
   henter. Målt først: `read-online` 0 gange i alle otte bogsider, og den eneste
   vej til teksten var en download. Næste skridt er punkt 6: måle om nogen læser
   læsevisningen, hvilket kræver `STATS_TOKEN`.
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
5. ~~Scanneren siger hvilken side den læste, og følger de links siden har.~~
   **Leveret 1/10** — overblikket, det enkelte resultat og den downloadede
   rapport siger hvilken side og hvilke sider der blev læst, og et dybt URL
   scannes på den side det angiver. Målt først: «the score is the homepage»
   stod på siden uanset input, og kun de gættede stier blev læst.
6. ~~Det mest linkede værktøj solgte ikke.~~ **Leveret 1/10** — `/scan` og
   `/scan-da` renderer nu det samme pro-kort som de otte søskendeværktøjer,
   med katalogens betalingslink, pris og periode, og donationslinjen overlever.
   Målt først: 0 `buy.stripe.com` på begge sider. Dertil en fundet fejl: kortet
   blev trykt med i brugerens egen rapport, fordi `@media print` skjuler `.btn`
   men ikke `.pro-card` — så PDF'en havde salgstext uden den eneste handling.
   Nu skjuler print-listen begge, målt i browseren (`display: none`).
7. ~~Kontrast-tjekkeren indeni artiklen, der får hele trafikken.~~
   **Leveret 2/10** — begge artikler har selve værktøjet, og heroens primære
   handling er et anker ned til det i stedet for et hop ud af siden. Målt først:
   8 af 18 besøgende landede på artiklen, 100 % forlod den, og værktøjet fik 1.
   Dertil fundet undervejs: felterne var 192 px høje på telefon, fordi en delt
   `.ti-field > *`-regel gav kolonnebørnene en *højde* på 12 rem. WCAG-formlen
   lå i fire kopier; den ligger nu i `site/text-on-image-core.js`.
8. ~~Rettfærdigt budget pr. rapport, og et fund der siger fra.~~
   **Leveret 2/10** — se fundet fra review 30/9 i STATUS. Datagrund: målt på
   den levende rute, 3 sites i ét kald → rapport 3 med `pages_checked: 1`,
   `score: 22` og fem «Not found»-fund om sider wordpress.org har.
9. ~~Free mod Pro på ét sted.~~ **Leveret 2/10** — de otte produktsider har nu
   samme to-rækkers-tabel, tegnet af `tools/pro_table.py` fra
   `tools/stripe_catalog.json`, og `check_pro_table.py` dømmer hver blok mod
   samme kilde. Målt først: `page-profile` skrev «$0 forever / $19/year /
   $39 once» i hånden, `deskuptime` «19 USD once», de to andre havde ingen
   tabel — fire svar om det samme produkt, ingen port dømte dem. **Næste skridt
   er gjort 2/10:** de ni øvrige værktøjssiders pro-kort har nu samme tabel, så
   en besøgende på `/scan` ser «gratis gør dette, Pro gør hele sitet» i samme
   øjeblik han har set sit resultat. Ny port `check_catalog_where.py` dømmer
   belægget i katalogens `where`, så «hvor»-påstandene ikke kan rådne igen.
