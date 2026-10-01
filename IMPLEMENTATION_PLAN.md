# STATUS

- **Bøgerne læses online.** Alle seks bogside-ruter viser kapitel 1 og 2 i fuld
  tekst. Baseline før: 0 tegn bogtekst på alle otte ruter. Målt efter:
  `read-online` 1 gang på hver af de seks, 0 på `books/index` og
  `books/compliance-bundle`. De sender heller ikke længere død CSS (mutation:
  alle regler igen → RØD 30 fund).
- **Gaten kørte 16 domme i CI uden at køre dem.** `quality_gate.py` tog
  beslutningen om `dist/` *før* build-steppet, så en frisk checkout sprang dem
  over og meldte grøn, mens samme kode lokalt var rød i `built-css`. Bevis: den
  grønne kørsel af `c4fd730` siger «springer 16 dist-steps over». Målt efter:
  GRØN 123 steps fra en `dist/` der ikke fandtes. Scannerens læsevisning er
  `DEPLOY OK 2026-10-01` — seks domme målt på live `8d8cdb5`.
- **`/scan` og `/scan-da` sælger nu, og deres trykte rapport gør ikke.**
  Begge renderer det samme pro-kort som de otte søskendeværktøjer. Fundet under
  vejen: `@media print` skjulte `.btn` men ikke `.pro-card`, så «Udskriv / gem
  som PDF» gav en lilla salgstext uden knap. Nu skjuler print-listen begge.
  Målt: `$79`→`$19`-mutation rød (248/249), `.pro-card` fjernet fra print-
  listen rød (249/252), uændret 252/252; browseren viser `display: none`.
- **CEO-kø punkt 0 er leveret og efterprøvet 1/10** — alle fem delpunkter
  verificeret på koden, ikke bare lukket; detaljerne i `docs/plan-arkiv.md`.
- **PR-TJEK 2026-10-01:** ingen åbne PR'er. **BRANCH-TJEK:** 3 remote-branches,
  ingen 14 dage gamle.
- **❓ Til Mads:** `OPENROUTER_API_KEY`, `STATS_TOKEN`, `bugbottle.dev`s domæne,
  banner-placering på 180 sider, de 2 desktop-apps der ringer til Lemon
  Squeezy, Search Console, og **bogenes betalte udgave** (ny, se ❓).

## Verificér deploy

- `VERIFICÉR DEPLOY: pro-kort på /scan og /scan-da
  ceo/scan-saelger 2026-10-01 19:55` — måles på **indhold** på
  `https://mahope.tools/scan` og `https://mahope.tools/da/scan`.
  Baseline målt 1/10 på `site/`: 0 `buy.stripe.com` på begge sider. Domden:
  1. Begge sider har `class="result-card pro-card"` 1 gang.
  2. Katalogens betalingslink `buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03` står i
     `proCard()` på begge, og knappen siger `$79` + en periode (`/year`, `/år`).
  3. Donationslinjen overlever: `donate.stripe.com` stadig 1 gang pr. side.
  4. `https://mahope.tools/style.css` har `.pro-card` i den `@media print`
     regel der også skjuler `.btn` — ellers trykkes salgstexten uden knap.
  5. Pro-kortet på EN og DA skal være hvert sit sprog, og ingen af dem må
     påstå at kun én side blev læst (det gør `/compliance-site-check`'s).
  Domden er `node tests/scan-clients.test.mjs` (252/252) + gaten. Mutationer
  målt: `$79`→`$19` i knappen → 248/249 med «knappen viser prisen fra
  katalogen ($79)»; `.pro-card` fjernet fra print-listen → 249/252 med «print:
  pro-kortet skjuler sig i den trykte rapport». Grøn er kun den uændrede kode.

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
