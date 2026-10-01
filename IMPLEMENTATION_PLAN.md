# STATUS

- **Scanneren siger ikke længere «Not found» om sider den aldrig læste.**
  Fund fra review 30/9 var målt på den levende rute: ét kald med tre sites gav
  to fulde rapporter og en tredje bygget på forsiden alene — wordpress.org, som
  både har og linker sin privatlivspolitik, fik «Not found. Add a Privacy
  Policy page and link it from your footer» og score 22. Rettelsen er tre ting:
  budgettet er **delt retfærdigt** pr. URL (12 pr. kald, delt 4+4+4 ved tre
  sites), det bruges **tur for tur** så hvert tjek får mindst to kandidater,
  og et tjek der ikke nåede igennem sin liste **siger fra hvor**: «We checked 3
  of the 7 pages we expected here» — eller `status: "unknown"` og
  `not_checked`, hvis det ikke fik læst en eneste side. Bevis: 6 af portens
  domme fejler på den gamle kode (dokumenteret i commit-body), 352/352 på den
  nye. Dertil et fund undervejs: URL-feltet havde `content-box` og stod 12 px
  ud over kanten på 390 px — altså vandret scroll på indsendelsessiden, målt
  før/efter i browseren på begge sprog.
- **Kontrasttjekkeren kører nu inde i den artikel der får hele trafikken.**
  `/blog/text-on-image-contrast-check` var mahope.tools' største indgangsside
  med 8 af 18 besøgende (28 d) og **100 % bounce** — alle otte forlod den igen,
  og værktøjet de blev sendt videre til fik 1. Begge artikler (EN + DA) har nu
  `#try-it` / `#prov-dit-billede` med selve værktøjet, og heroens primære
  handling er det anker i stedet for et hop ud af siden. Baseline før: **0**
  `ti-card` på artiklerne. Målt i browseren på 390 og 1280 px × 5 sider:
  `overflowX=0`, resultatet skriver 3,86:1 på EN og 4,20:1 på DA, ingen
  `pageerror`. WCAG-formlen lå før som **fire** kopier; den ligger nu i
  `site/text-on-image-core.js`, og dommen «kernen definerer `sampleContrast`
  præcis én gang» er grøn.
- **En rigtig fejl faldt ud af designkontrollen:** `.ti-field` er en kolonne,
  så den delte regel `.ti-field > * { flex: 1 1 12rem }` blev til en **højde**
  på 12 rem — alle fire felter stod 192 px høje på en telefon, og
  farvevælgeren blev et 30 px bredt højt bjerg. Det lå på værktøjssiderne
  længe før denne iteration. Målt før/efter i browseren: 192 px → 44–48 px.
- **Deploy-noterne er lukket på indhold 2/10.** `ceo/generator-kobsvej-2` er målt
  på live `0adc322`: alle fire domme grønne på seks sider. `ceo/ai-cta-uden-loefte`
  afventer sit deploy-vindue.
- **PR-TJEK 2026-10-01:** ingen åbne PR'er. **BRANCH-TJEK:** 3 remote-branches,
  ingen 14 dage gamle.
- **❓ Til Mads:** `OPENROUTER_API_KEY`, `STATS_TOKEN`, `bugbottle.dev`s domæne,
  banner-placering på 180 sider, de 2 desktop-apps der ringer til Lemon
  Squeezy, Search Console, og **bogenes betalte udgave** (se ❓).

## Verificér deploy

- `VERIFICÉR DEPLOY: ret budgettet på de rapporter, kunden sender videre
  ceo/deling-pr-url 2026-10-02` — måles på **indhold** på den levende rute, ikke
  på HTTP 200. Dom 1: `GET /api/compliance-scan?url=` med `mahope.dk\n` +
  `www.cookiebot.com\n` + `wordpress.org\n` (tre linjer, ét kald) → 200 og
  `scanned: 3`, og **alle tre** rapporter har `pages_checked` ≥ 2 — den tredje
  havde `pages_checked: 1` før. Dom 2: wordpress.org's privatlivstjek er `pass`
  med `https://wordpress.org/about/privacy/` i `details` — før var det
  `Not found. Add a Privacy Policy page and link it from your footer`. Dom 3:
  summen af `pages_checked` for de tre rapporter er ≤ 12, og hver rapport har
  højst sin andel (4). Dom 4: hvert tjek med `status: "unknown"` ligger i
  `results.notChecked` og **ikke** i `results.failed`, og `passed + failed +
  not_checked === total` for alle tre. Dom 5: `not_checked` findes i svaret,
  og ingen `details` med «Not found» mangler «We checked N of the M pages we
  expected here», når listen ikke gennemgik alle kandidater. Dom 6: UI'en på
  `/compliance-site-check` og `/da/compliance-site-check` viser «N not checked»
  / «N ikke tjeket» i scoren, og et `unknown`-punkt er **gult** (–), ikke rødt
  (✗). Dom 7: `getStatusIcon` og `statusOrder` er på plads i begge filer, og
  `pageerror` er 0. Dommen er `node tests/stripe-worker.test.mjs` (352/352,
  heraf 6 domme der fejler på `main`s worker) + `node
  tests/scan-clients.test.mjs` (392/392) + `python3 tools/quality_gate.py` +
  missionens gate.
- `VERIFICÉR DEPLOY: kontrasttjekkeren indeni de to artikler
  ceo/kontrast-tjekker-i-artiklen 2026-10-02` — måles på **indhold**, ikke på
  HTTP 200. Dom 1: `/blog/text-on-image-contrast-check` og
  `/da/blog/tekst-paa-billede-kontrasttjek` har `ti-card` 1 gang, `ti-canvas-wrap`
  1 gang, `art-cv` 1 gang og `TiContrast.mount` 1 gang hver — altså er værktøjet
  faktisk der, ikke kun en omtale af det. Dom 2: heroens `btn-primary` er
  `href="#try-it"` (EN) og `href="#prov-dit-billede"` (DA), og begge anker findes
  som `id` i markup'en — læseren bliver på siden. Dom 3:
  `/text-on-image-core.js` svarer **200** og `text-on-image-core.js` ligger i
  `dist/mahope.tools/`, og **alle fire** sider indlæser den (0 kopier af
  `function sampleContrast` i nogen af dem). Dom 4: resultatet renderes i live —
  `/text-on-image-checker` måler 3,86:1 på EN og 4,20:1 på DA (dansk komma),
  og artiklens `#try-it`-kort har samme mål. Dom 5: `art-result` har
  `role="status"` + `aria-live="polite"`, `art-err` har `role="alert"`, og alle
  fire felter har `<label for>` (dommen er `tools/check_form_labels.py`).
  Dommen er `node tests/scan-clients.test.mjs` (392/392) +
  `python3 tools/check_contrast_sampling.py` (22/22) + gaten.

- `VERIFICÉR DEPLOY: AI-banneren uden et løfte den ikke kan holde
  ceo/ai-cta-uden-loefte 2026-10-02` — måles på **indhold**, ikke på HTTP 200.
  Dom 1: `See what we publish free` 91 gange og `Se hvad vi udgiver gratis` 96
  gange i live EN/DA, og **0** gange `practical answer in seconds`,
  `få et praktisk svar på få sekunder`, `Ask the Compliance AI` eller
  `Spørg Compliance-AI` i noget publiceret HTML. Dom 2: hver AI-banners `href`
  er `/compliance-ai` (EN) eller `/da/compliance-ai`, altså den side der
  fortænger sandheden — ikke en død `/books`-rute. Dom 3: bannerens knapstørrelse
  (`btn-secondary`/`btn-primary`) er uændret, så intet rykker sig på folden.
  Dom 4: `ai-cta-link` ligger stadig 1 gang pr. artikel, så `data-track` og
  `/api/track`-tællingen virker uændret. Dom 5: `GET /api/compliance-ai` svarer
  stadig `{"ok":true,"available":false}` — banneren siger det samme, og det er
  hele pointen. Dommen er `python3 tools/check_ai_cta_honesty.py` + gaten.
- `DEPLOY OK 2026-10-02` — købsvej på RoPA, privacy notice og EAA-erklæring.
  Note lukket på **indhold** på live `0adc322` (`build-info.json` →
  `0adc3224ef8756e5…`), alle fire domme målt på de seks sider: `upsell-card`
  **1** gang i hver, `renderHTML(current) + UPSELL + DONATION` **1** gang i
  hver, katalogens betalingslink **1** gang i hver (`bJe7sK8aT4My7dk7czbMQ05`
  på de to RoPA-sider, `eVqaEW0Iren855c68vbMQ0a` på de to privacy-sider,
  `3cI7sK2Qz3IugNUgN9bMQ08` på de to EAA-sider), beløbet fra katalogen pr. side
  (`$59` / `$149` / `$39`) og perioden som sit egot ord — `once` i EN,
  `engang` i DA. `no-print` findes på alle seks, e-book-bundlet **0** gange i
  alle seks, og «behøver aldrig at betale for noget» **0** gange.

- `DEPLOY OK 2026-10-02` — pro-kortet på `/scan` og `/scan-da`. Note lukket på
  **indhold** på live `919280b`. Alle fem domme målt: `class="result-card
  pro-card"` 1 gang i hver, katalogens betalingslink `eVq00i4YH6UG69g0ObbMQ03`
  1 gang i hver, knappen siger `$79/year per website` (EN) og `$79/år pr.
  website` (DA), `donate.stripe.com` stadig 1 gang pr. side, og `style.css`
  skjuler `.pro-card` i den **samme** `@media print`-regel som `.btn`. Punkt 5
  målt på det udskrevne pro-kort: EN siger «It read the one page you pasted. A
  site is every page.», DA siger «Den læste den ene side, du indsatte. Et
  website er alle sider.» — hvert sit sprog, ingen af dem påstår kun én side
  blev læst. **Ruten hedder `/scan-da`, ikke `/da/scan`** — den gamle note
  havde den forkerte adresse, som gav 404. Den er rettet her.

- `DEPLOY OK 2026-10-01` — bogen læses online på alle seks bogside-ruter. Note
  lukket på **indhold** på live `c4fd730`. Alle seks domme målt 1/10:
  `read-online` **1** gang i hver af `gdpr-for-agencies` (`Chapter 1 — Why This
  Applies to You (Yes, You)`), `nis2-for-agencies` (`Chapter 1: Does NIS2 Apply
  to Your Agency?`), `cookie-consent-guide` (`Chapter 1: What the Law Actually
  Requires`), `eaa-checklist` (`Chapter 1: Is Your Site in Scope?`),
  `eaa-shopify` (`Chapter 1: What the EAA Means for Your Shopify Store`) og
  `build-your-first-chrome-extension` (`Preface: Why This Book Exists` er
  indhold, filteret dropper kun `Front Matter`/`Foreword`) — **0** i `books/index`
  og `books/compliance-bundle`; `reader-chapter-title` **2** gange i hver;
  `eaa-checklist` viser kapitel 2 som `Chapter 2: The 10-Point EAA Compliance
  Checklist`; `<details>`+`<summary>` 1 og 1 i hver bogsektion.

  Punkt 5 målt på den afgrænsede bogsektion (fra `id="read-online"` til første
  `</section>` efter den), fordi et 40 000-tegns vindue løber ind i sidens
  footer og ville tælle sidernes egne scripts: **0** rå `<script>`, **0**
  `onerror`, **0** `javascript:` på `gdpr-for-agencies` (8 705 tegn) og
  `eaa-checklist` (14 213 tegn). Bogen har heller ingen `<script>` at vise, så
  kravet om at `&lt;script` skal forekomme kan ikke måles live: det escapede
  markup ligger i `build-your-first-chrome-extension` kapitel 6, og læsevisningen
  viser kun kapitel 1 og 2. Escapen er derfor dømt på koden i stedet —
  `book_reader.py:133` (`self.out.append(escape(data))`), og
  `--self-test` 45/45. Mutation: escapen fjernet → **43/45** med «script-tags
  er væk» og «tekst escape-stadig». Det er altså ikke en from regel, men den
  konkrete linje der gør den.

- `DEPLOY OK 2026-10-01` — bogen læses online på alle seks bogside-ruter. Note
  lukket på **indhold** på live `c4fd730`, alle seks domme målt: `read-online`
  1 gang i hver af `gdpr-for-agencies`, `nis2-for-agencies`,
  `cookie-consent-guide`, `eaa-checklist`, `eaa-shopify`,
  `build-your-first-chrome-extension` og 0 i `books/index` +
  `books/compliance-bundle`; `class="reader-chapter-title"` 2 gange i hver;
  første kapitel er et rigtigt kapitel på alle seks (`Preface: Why This Book
  Exists` er indhold, filteret dropper kun `Front Matter`/`Foreword`); `eaa-checklist`
  viser kapitel 2 som 10-punkters-tjeklisten; 0 `script`/`onerror`/`javascript:`
  lækker ud af læsevisningen; `scrollWidth == clientWidth == 390` ved 390 px på
  tre sider med `<details>`+`<summary>`.

- `DEPLOY OK 2026-10-01` — scanneren siger hvilken side den læste, og den hvide
  knap fik sin farve. Målt på **indhold** på live `8d8cdb5`: `pages_read`
  **5** gange i live EN (variablen bruges flere steder), `class="pages-read"`
  **1** gang i hvert af EN og DA, `<summary>` **1** gang i hvert,
  `Pages read (` **2** gange i EN og **0** i DA, `Sider læst (` **2** gange i
  DA og **0** i EN. Punkt 6 i den gamle note var **umuligt** at måle sådan den
  var skrevet: de fire forbudte formuleringer findes stadig i filen, men som
  ting der ikke er i pro-kortet — «One page per site» er indledningen til den
  *nye* ærlige sætning «One page per site, plus the legal pages it links to» i
  flersteds-kortet, og «checked one page» står i en dansk kildekommentar. Domden
  skal derfor læse det *renderede* pro-kort, hvilket er hvad
  `tests/scan-clients.test.mjs` gør (233/233). Punkterne 1–3 er målt på den
  levende rute: `GET /api/compliance-scan?url=forbrug.dk` → 200,
  `pages_read` 2 entries, ingen dubletter, ingen anden vært, og fundet for vilkår
  peger på `https://forbrug.dk/emner/aftaler-og-abonnementer/abonnementsvilkaar`
  — en sti scanneren aldrig ville gætte, hvilket er hele pointen. Samme for
  `mahope.tools`: privatliv på `/privacy-notice-generator`, vilkår på `/terms/`.


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
9. **Free mod Pro på ét sted.** Hvem: alle der køber. Tal: købsknapper pr.
   Pro-side (baseline: målt af `check_tool_sections.py`). Accept: hver Pro-side
   har den samme to-rækkers-tabel, og beløbet er læst fra
   `tools/stripe_catalog.json` som på `/scan`. Datagrund: 19 af 84 købsknapper
   sagde ingen periode før 1/10; samme fejlform kan ligge i sammenligningerne.
