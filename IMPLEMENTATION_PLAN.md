# STATUS

- **Scanneren følger nu de links, siden selv peger på.** Rettet 1/10: den læser
  den indsendte side og derefter de juridiske sider forsiden *linker til* — kun
  på sitets eget domæne — før den gætter stier. Før dette gættede den kun, så et
  site med privatlivspolitikken på `/da/juridisk/privatlivspolitik` fik «Privacy
  Policy: Not found» om en side, footeren peger på lige dér. Samme fejl ramte
  vilkår på dansk: hintlisten kendte `vilkar`, dansk skriver «Vilkår og
  betingelser». Baseline 1/10 før rettelsen: 341 domme, hvoraf 3 nye var røde
  på den gamle kode (336/341 ved gæt-først, 337/341 uden same-host-værnet).
- **Rapporterne lister hvilke sider der blev læst.** Ny `pages_read` i svaret,
  vist i resultatkortet som en fold-liste og skrevet i den downloadede `.md`, så
  et fund kan efterprøves. «9 pages read» kunne ingen kontrollere. Pro-kortet er
  samtidig rettet: det sagde «checked one page» om et kald der læser mere, og
  det er præcis den løgn kortet sælger på at undgå.
- **PR-TJEK 2026-10-01:** `gh pr list --state open` → ingen åbne PR'er.
- **❓ Til Mads:** `OPENROUTER_API_KEY`, `STATS_TOKEN`, `bugbottle.dev`s domæne,
  banner-placering på 180 sider, de 2 desktop-apps der ringer til Lemon
  Squeezy, Search Console. Historie: `docs/plan-arkiv.md`.

## Verificér deploy

- `VERIFICÉR DEPLOY: scanneren følger links fra forsiden
  ceo/scanneren-foelger-links 2026-10-01 19:55` — måles på **indhold** på
  `https://mahope.tools/compliance-site-check` og `/da/compliance-site-check`.
  Baseline målt 1/10 på live `bfd4a9e`: `pages_read` **0** gange i begge scripts,
  `pages-read` **0** gange, `Pages read (` **0** gange, `cscExtractLinks` **0**
  gange i den publicerede worker. Domden bliver derfor:
  1. `GET /api/compliance-scan?url=<host>` hvor sitets privatlivs- og
     vilkårsside kun findes via footeren: begge fund skal være `pass`, og
     `details` skal pege på den linkede sti — ikke på `/privacy`.
  2. `pages_read` skal kun indeholde URLs på **samme vært** som `scanned_url`.
  3. `pages_read` skal være et sæt: ingen sti to gange.
  4. Begge sider har `class="pages-read"` og `<summary>` i hvert script.
  5. Begge sider har `Pages read (` hhv. `Sider læst (` i rapport-generatoren.
  6. Pro-kortet skal **ikke** sige `checked one page` / `One page per site` /
     `tjekkede én side` / `Én side pr. website`.
  Dommen er `tests/stripe-worker.test.mjs` (341/341) + `tests/scan-clients.test.mjs`
  (233/233). Mutationer på den nye kode, målt: gæt-stier før links → 336/341;
  `pages_read` fjernet fra svaret → 338/341; same-host-værnet fjernet →
  337/341 (og `andet.example` får 1 kald); `laesteSider()` fjernet fra EN-
     markup'en → 227/229; gammel DA-pro-h3 tilbage → 231/233. Grøn er kun den
  uændrede kode.

- `DEPLOY OK 2026-10-01` — scanneren siger hvilken side den læste, og den hvide
  knap fik sin farve. Målt på **indhold** på live `bfd4a9e` (alle syv domme er
  grønne, se tallene nedenfor — de afviger fra opskriften, der var skrevet uden
  at være målt). `class="site-page"` **1** gang i hvert script, `scannetSide`
  **3** gange i hvert script (variablen bruges tre steder — opskriftens «1 gang»
  var for stram), `pages_checked` **3** gange, `scanned_url` **3** gange. Den
  publicerede `/style.css` har `.input-group button` **6** gange: regel plus
  `:hover`, `:active`, `:disabled`, `@media (max-width: 480px)` og portens
  kommentar. Punkt 5 er ikke «0 gange» men «0 gange i det viste output»: EN
  har «the score is the homepage» **1** gang i en dansk kildekommentar
  (`site/compliance-site-check.html:450`), DA har den tilsvarende **1** gang,
  begge steder uden for DOM. Punkt 7 var en **umulig** opskrift:
  `example.dk` findes ikke i DNS, så kaldet svarer 502. Målt i stedet med et
  domæne der findes: `GET /api/compliance-scan?url=example.com/some/deep/path`
  → 200 med `scanned_url` `https://example.com/some/deep/path` og
  `pages_checked` 12.

## Åbne opgaver

1. ~~Flere sider end forsiden pr. URL.~~ **Færdig 1/10.** Kaldet læser den
   indsendte side og de juridiske sider forsiden *linker til* — kun på sitets
   eget domæne — før det gætter stier, og svaret lister dem i `pages_read`.
   Accept nået: `pages_checked` overstiger de gættede stier, og fundet peger på
   den linkede side. Flyttet til `docs/plan-arkiv.md`.
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
   serveren svarer én rapport pr. URL, og Pro-boksen siger ærligt hvad den
   *ikke* ser. Næste skridt var punkt 1 under «Åbne opgaver»: det er gjort.
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
5. ~~Scanneren siger hvilken side den læste, og følger de links siden har.~~
   **Leveret 1/10** — overblikket, det enkelte resultat og den downloadede
   rapport siger hvilken side og hvilke sider der blev læst, og et dybt URL
   scannes på den side det angiver. Målt først: «the score is the homepage»
   stod på siden uanset input, og kun de gættede stier blev læst.
