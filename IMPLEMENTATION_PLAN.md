# STATUS

- **Bøgerne kan læses online, kapitel for kapitel.** Rettet 1/10: alle seks
  bogside-ruter har nu en læsevisning med kapitel 1 og 2 i fulde kapitler —
  bygget af `ebook/<slug>.epub`, altså af den fil kunden henter, så den ikke kan
  blive ældre end bogen. Rækkefølgen læses af OPF-spine'en. Baseline før: 6 af
  6 bogside-ruter viste 0 tegn bogtekst og en kapitel-liste, og den eneste måde
  at læse en bog på var at hente EPUB'en. Målt efter: `id="read-online"` 1 gang
  på hver af de seks, 0 på `index` og `compliance-bundle` (de er ikke en bog).
- **Gaten kørte 16 domme i CI uden at køre dem.** Rettet 1/10: `quality_gate.py`
  tog beslutningen om `dist/` *før* build-steppet, så en frisk checkout uden
  `dist/` sprang `sitemaps, seo, inline-js, links, design-tokens, jsonld-types,
  hreflang-pairs, built-css …` over og meldte grøn. Bevis fra den grønne
  kørsel af `c4fd730`: loggen siger «intet i dist/ — springer 16 dist-steps
  over», mens samme kode lokalt var **rød** i `built-css` med 35 fund. Derfor
  gaten lokalt: `python3 tools/quality_gate.py` → GRØN 123 steps, og de otte
  ovenfor kører alle med `--- grøn`.
- **Bogside-ruterne sendte død CSS.** Samme rodårsag: `book_reader.py` skrev
  regler for `pre`, `code`, `blockquote`, `table`, `th`, `td`, `hr` og `h4` til
  alle seks bøger, men kun nogle kapitler har sådanne afsnit. Nu skrives kun det
  kapitlerne faktisk bruger; `pre code` kræver begge dele. Målt: `cookie-consent`
  → `code, pre, table, td, th`; `eaa-checklist` → `blockquote, code, hr, table,
  td, th`; `eaa-shopify` og `build-your-first-chrome-extension` → ingen. Døde
  regler tilbage i skabelonen → `check_built_css` RØD 30 fund; uændret → GRØN.
- **Scannerens læsevisning er verificeret live.** `DEPLOY OK 2026-10-01` — alle
  seks domme fra sidste deploy-note er målt på live `8d8cdb5`, se nedenfor.
- **CEO-kø punkt 0 er leveret og efterprøvet 1/10.** Alle fem delpunkter er
  verificeret, ikke bare lukket: `handleUrlInspect(request, url, env)` kalder
  `rateLimitIp(request, env, …)` med `env` (`_worker.js:288/3367`), begge ruter
  svarer 200; `thanks.html` har egen `PENDING_OUT`-sætning til 202; 429 er
  endelig i `site/net.js:43` med `err.limited`, så ingen af de otte klienter
  genkalder den; 5xx er transient med højst ét ekstra kald; `targetIsPublic()`
  sidder på `/api/header-check` og `/api/url-inspect` **og på hvert
  redirect-hop** (`_worker.js:2659`, `3440`). Der findes ingen `ceo/net-js`
  længere — reglen ligger i `net.js` på `main`.
- **PR-TJEK 2026-10-01:** `gh pr list --state open` → ingen åbne PR'er.
- **❓ Til Mads:** `OPENROUTER_API_KEY`, `STATS_TOKEN`, `bugbottle.dev`s domæne,
  banner-placering på 180 sider, de 2 desktop-apps der ringer til Lemon
  Squeezy, Search Console, og **bogenes betalte udgave** (ny, se ❓). Historie:
  `docs/plan-arkiv.md`.

## Verificér deploy

- `VERIFICÉR DEPLOY: læsevisning på alle bogside-ruter
  ceo/boeger-laeses-online 2026-10-01 20:25` — måles på **indhold** på
  `https://mahope.tools/books/<slug>` for alle seks slugs.
  Baseline målt 1/10 på live `8d8cdb5` (før ændringen): `read-online` **0**
  gange i alle otte bogsider, og kapitel-1-teksten «The most common
  misconception among small agencies» **0** gange. Domden bliver derfor:
  1. `read-online` **1** gang i hver af `gdpr-for-agencies`,
     `nis2-for-agencies`, `cookie-consent-guide`, `eaa-checklist`, `eaa-shopify`,
     `build-your-first-chrome-extension` — og **0** i `books/index` og
     `books/compliance-bundle`.
  2. `reader-chapter-title` **2** gange i hver af de seks.
  3. Første `reader-chapter-title` skal være en rigtig kapitel — aldrig
     `Front Matter` eller `Foreword`.
  4. Bogen skal vise kapitel 2 også på `eaa-checklist`, hvor kapitel 2 er
     10-punkters-tjeklisten på 9,8 KB. Det var præcis den kapitel et loft på
     9000 tegn fjernede.
  5. `&lt;script` må forekomme i bogsektionen, og ingen `<script>`/`onerror`/
     `javascript:` må gå ud i den.
  6. Ingen vandret scroll ved 390 px; `<details>`+`<summary>` skal være der, så
     kapitlerne kan lukkes.
  Domden er `python3 tools/book_reader.py --self-test` (45/45) + gaten.
  Mutationer målt på den nye kode: escapen i `handle_data` fjernet → 43/45
  (script-tag og `javascript:`-href slipper igennem); `EXISTING.sub` fjernet →
  44/45 (anden injektion duplikerer sektionen); front-matter-filteret fjernet →
  43/45 (læsevisningen starter på omslagssiden); loftet tilbage på 9000 → 44/45
  (`eaa-checklist viser to kapitler — 1`); dommen «får læsevisning == har en
  EPUB» gjort til en ren existence-tjek → 43/45; EPUB-værnet i `build_sites.py`
  fjernet → 40/45 (alle seks EPUB'er forsvinder fra deres side). Grøn er kun
  den uændrede kode.

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
