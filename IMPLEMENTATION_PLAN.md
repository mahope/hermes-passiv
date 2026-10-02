# STATUS
- **En farvesimulering kan nu videresendes som et link.** Simulatoren kører helt
  i browseren og intet blev sendt nogen steder, så det eneste en designer
  egentlig vil have — «se præcis den her simulering» — døde med fanebladet.
  Tilstanden ligger nu i fragmentet (`#pal=…;s=…;f=…;b=…`), læses før der tegnes,
  og `replaceState` skriver den i adresselinjen hele tiden, så knappen
  «Copy link to this simulation» bare kopierer den adresse brugeren allerede
  har. Ny fælles kernе `site/cb-share-core.js` (EN + DA deler den, så en dansk
  kopi ikke kan falde fra). Målt: 58/58 i ny `tests/cb-share.test.mjs`; porten
  er **RØD på den gamle kode — 8 fejl**, bl.a. fordi gridet stadig viser
  standardpaletten på `#pal=2563eb,e91e63;s=42`. Fund undervejs: `addColor()` og
  slette-knappen kaldte aldrig `renderExport()`, så en tilføjet farve stod i
  tabellen men ikke i CSS/JSON-eksporten — rettet i samme opgave.
- **`BRANCH-TJEK 2/10`:** to branches var fuldt landede og er slettet på origin
  (`lifetime-founding`, `ceo/porten-kan-skelne-vilkaar`). `ceo/hub-readme-note`
  har kun en gammel plan-note fra 26/9 og intet kode — se ❓. **`PR-TJEK 2/10`:**
  ingen åbne PR'er.
- **`/blog/` havde fire døde links, og porten vidste det.** De fire
  BugBottle-guider lå i `bugbottle.dev`s `include`, blev bygget hver kørsel og
  **lagt ingen steder** — domænet står ikke i deploy-matricen — så
  `build_sites.py` skrev deres `href` om til `https://bugbottle.dev/…`. Målt
  **404 på alle fire** 2/10, og **15** links døde i alt, fordi fire artikler
  mere peger på dem. De ligger nu på `mahope.tools`: 189 guides, 189 relative
  links, 0 mangler mod `site/blog/`.
- **Porten skrev «ikke udgivet: 4 artikler» med filnavnene og gaven GRØN**, fordi
  dom 4 spørger om *domænet* har en begrundelse — og `bugbottle.dev` har en.
  Det er ikke det spørgsmål, en læser stiller, når han trykker et link. Ny
  **dom 4b** `dark_link_problems()` dømmer linket. Polaritet på rigtige filer:
  genskabt gammel `include` → **RØD — 4 problem(er)**; tre nye selftestarme
  grønne (den tredje med en matrix på ét domæne → 21 døde links).
- **To kataloger var forældede på samme måde** — de fire ruter lå under
  `bugbottle.dev` i `route_inventory.json` og i `stripe_catalog.json`s `offers`.
  Flyttet dem røde `check_stripe_ctas` med 6 fund: igen et tal der beregnes og
  ikke siges. De to artikler har 9 målte besøg og ingen købsknap, så dom 5 blev
  rød; BugBottle har **ingen** betalt udgave i katalogen, så det står nu som
  linje med grund i `tools/article_click_no_button.json`.
- **Målt undervejs:** `--self-test` i `check_article_paid_path.py` var **allerede
  rød på HEAD** (`IndexError` i `andre[0]`, fordi de 4 rapporter er tomme
  uden `STATS_TOKEN`).
- **❓ Til Mads:** `STATS_TOKEN`, `OPENROUTER_API_KEY`, `bugbottle.dev`s domæne,
  bogens betalte udgave mod 7 sider der siger gratis, 2 desktop-apps der ringer
  til Lemon Squeezy, Search Console, IndexNow-ping, livstidsprisen. Resten: ❓.

## Verificér deploy

- `VERIFICÉR DEPLOY: del-link i farveblindhedssimulatoren 2026-10-02
   ceo/cb-simulator-del-link` — måles på **indhold** pr. side, ikke på HTTP 200:
   `/color-blindness-simulator` og `/color-blindness-simulator-da` skal hver
   have præcis **én** `<script src="/cb-share-core.js">`, `CBSHARE.decode(
   location.hash)` på den linje der læser fragmentet, **én** `id="copy-share"`
   og **én** `addEventListener('click', copyShare)`. `mahope.tools/cb-share-core.js`
   skal serveres **200** og have `CBSHARE.encode` + `CBSHARE.decode`. Dom 1:
   `cb-share.test.mjs` **58/58** + porten målt **RØD — 8 fejl** på de gamle
   sider. Dom 2: `stripe-worker.test.mjs` **354/354** (worker urørt). Dom 3:
   `build_sites.py` 335 filer 0 brudte, `seo_check.py` 314 sider 0 fund,
   `check_inline_js.py` 0 problemer. Dom 4: hele `quality_gate.py` grøn
   (**145** steps, fra 144). Dom 5: `tools/shots.py` **ingen vandret scroll**
   ved 360 + 768 + 1280 px på begge ruter.

- `VERIFICÉR DEPLOY: fire døde links fra /blog/ 2026-10-02
   ceo/blog-indeks-dode-links` — måles på **indhold**, ikke på HTTP 200:
   `mahope.tools/blog/` skal have **189** unikke `href` på guides (93 EN +
   96 DA, dvs. 0 mangler mod `site/blog/`), de fire BugBottle-guider skal være
   **relative** (`href="/blog/bug-reports-in-ci-pipeline"`) og **ikke**
   `https://bugbottle.dev/…`, og `dist/mahope.tools/blog/` skal have de fire
   filer. `build-info.json` på alle tre domæner skal stå i squash-sha'en. Dom 1:
   `check_article_paid_path.py` **GRØN** + de tre nye selftestarme grønne
   (polaritet målt ved at genskabe den gamle `include`: **RØD — 4 problem(er)**,
   «DØDTE LINK … 5 side(r) i site/ linker til den»). Dom 2:
   `stripe-worker.test.mjs` **354/354**. Dom 3: `build_sites.py` 334 + 33 filer 0
   brudte, `seo_check.py` 314 sider 0 fund, `check_inline_js.py` 0 problemer.
   Dom 4: hele `quality_gate.py` grøn.

- **DEPLOY OK 2/10 (kl. 21).** Alle fem åbne noter fra 2/10 er lukket her, målt på
  **indhold**: `build-info.json` står i `c2891ac` (= main HEAD) på alle tre
  deployede domæner, og CI er `success`. `ceo/hash-decode-urierror` (`c2891ac`):
  de **ni** sider der læser `#url=` serverer hver `try{…decodeURIComponent(…)}
  catch` på den linje der læser fragmentet — de to `url-to-markdown`-sider
  ligger på `cleancopy.tools`, ikke mahope.tools, så mit første tjek så 404 og
  var min egen fejlsøgning, ikke en død reference. `ceo/blog-indeks` (`caea80f`)
  og `ceo/url-med-til-udpakke` (`9f07a09`): `/blog/` serverer 189 unikke
  guide-links og heroens «93 English guides … plus 96 Danish guides»;
  `ceo/frontdoors-gate` og `ceo/blogindeks-citerede-lofter` (`df1cd60`) er dækket
  af de samme to målinger plus CI.

- ~~`VERIFICÉR DEPLOY: at et håndskrevet #url=% ikke dræber fragment-læseren~~
   2026-10-02 ceo/hash-decode-urierror` — syv sider ændret, så måles på **indhold**
   pr. side, ikke på HTTP 200: `mahope.tools/scan`, `/scan-da`, `/cookie-check`,
   `/cookie-check-da`, `/compliance-report`, `/compliance-site-check` og
   `/da/compliance-site-check` skal hver have `try{…decodeURIComponent(…)}catch`
   på den linje der læser `#url=`, og `url-to-markdown` +
   `da/url-til-markdown` skal fortsat være grønne. Dom 1: `check_url_handoff.py`
   **GRØN** (8 forsider dømt, 6 handoff, 9 sider dekoder fragmentet) +
   `--self-test` **18/18**. Dom 2: `stripe-worker.test.mjs` **354/354**. Dom 3:
   `build_sites.py` 330+35+73+37 filer 0 brudte, `seo_check.py` 314 sider 0 fund,
   `check_inline_js.py` 663 inline-blokke 0 problemer. Dom 4: hele
   `quality_gate.py` **144 steps** grønne.

- **DEPLOY OK 2/10 (kl. 09).** Noten om gratis-mod-Pro i kortet på de ni øvrige
  værktøjssider er målt på **indhold**: `pro-table:start` står 1 gang på alle ni
  live, og `build-info.json` på alle tre deployede domæner står i `ce438ba`.
- **DEPLOY OK 2/10 (kl. 11).** `ceo/livstid-scope` (`45b31df`) er ude — den lå
  og ventede, fordi den gik rødt i CI. Målt på indhold: `/compliance-report`
  serverer `$149 once per website — lifetime, first 100 purchases` og den danske
  `$149 én gang pr. website, for altid.`, og `build-info.json` står i `182af57`.
- **DEPLOY OK 2/10 (kl. 12:30).** `ceo/pris-side` (`b0da8ad`) er ute. Målt på
  **indhold**, ikke på HTTP 200: `/pricing` og `/da/pricing` serverer hver 14
  `data-product`-rækker, 3 `data-lifetime`-rækker, **0** `buy.stripe.com` og
  `pricing:start` 1 gang pr. fil; `build-info.json` står i `b0da8ad`.
- **DEPLOY OK 2/10 (kl. 11).** `ceo/donation-pris-fra-katalog` (`19e59b2`) er ude,
  målt på indhold: `build-info.json` står i `19e59b2`, `/pricing` har
  `From 10 kr.` i rækken `support-mahope-oss`, `/da/pricing` `fra 10 kr.`,
  `/support` «Any amount from 10 kr.» og `/da/support` «Valgfrit beløb fra 10 kr.».

- **DEPLOY OK 2/10 (kl. 16).** `ceo/tjek-paa-mahope-forside` (`d0e55bf`) er ude,
  målt på indhold: `mahope.tools/` og `/da/` har hver præcis 1 `#oc-check-form`,
  og `build-info.json` står i `d0e55bf` på alle tre deployede domæner. Dom 1:
  `GET /api/url-inspect?url=…` svarer 200 med `securityHeadersChecked` på 8 navne.
  Dom 2: `stripe-worker.test.mjs` 354/354. Dom 3: `build_sites.py` 330+35+70+37
  filer 0 brudte, `seo_check.py` 314 sider 0 fund, `check_inline_js.py` grøn.
  Dom 4: hele `quality_gate.py` 130 steps. Dom 5: `check_donation_paths` 43 sider,
  `check_first_action` 14 dømte 0 problemer, `check_form_labels`, `check_net_copies`
  og `check_built_css` grønne.

- **DEPLOY OK 2/10 (kl. 17).** `ceo/cleancopy-konverteringstjek` (`22a2753`) er
  ude alligevel — dens blokering var rød CI, som `db3c537` rettede 15:01. Målt på
  **indhold**: `cleancopy.tools/build-info.json` står i `db3c537` (main HEAD),
  forsiden har `cc-check-form` og 3 referencer til `/readable.js` +
  `/convert-check.js`.

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
   lægges ingen steder. Det er derfor `traffic_status` er `partial` hver time og
   `reports/weekly/` mangler et helt domæne. **2/10 er følgen målt og lukket:**
   de fire BugBottle-guider lå der og gav fire døde links fra `/blog/`, så de er
   flyttet til `mahope.tools`, og dom 4b i artikelporten dømmer det fra nu af.
   Domænets egen forside og demo ligger stadig i `UNMANAGED_DOMAINS`, fordi det
   er *domænet* der mangler, ikke artiklerne. Accept: enten domænet på Pages og
   fjernet af `UNMANAGED_DOMAINS`, eller fjernet fra `TRACKING_DOMAINS` så
   status bliver ærlig. *(Beslutning — se ❓.)*
4. **172 sider har to-tre knapper over folden.** Hvorfor:
   `add_top_cta_495.py` og `add_ai_cta.py` har skudt scanner- og AI-banneren
   ind under `</header>` på hele bloggen, så de lå over folden på 180 af 224
   sider med hero — og på mange er heroens egen primære et anker (`#content`,
   `#how`). Målt 30/9 af `check_first_action.py`; **2/10 er de 10 mest besøgte
   rettet** (kontrastartiklerne + otte artikler med 1–2 besøgende, EN+DA), så
   172 står tilbage. Accept: bannerne er enten flyttet ned i artiklen på de mest
   besøgte sider (dømt i `tools/first_action.json`), eller slettet fra hele
   bloggen så AI-CTA'en ligger ét sted pr. side. Kræver beslutning — se ❓.
   **Målt i denne iteration:** de otte nyrettede havde 3 → 1 `btn-primary` i
   folden; portens ratchet voksede 4 → 12 dømte sider.
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
- **🟡 Skal scanner- og AI-banneren ligge over folden på de 172 resterende
  sider?** Målt 30/9 giver det **tre knapper oven på folden** pr. artikel, og på
  30 af dem er knappen *oveni* et anker som «læs videre», så det værktøj artiklen
  handler om ikke er den primære handling. **2/10 er de 10 mest besøgte rettet**
  (kontrastartiklerne + otte med 1–2 besøgende, EN+DA), målt 3 → 1 knap i folden
  og dømt i `tools/first_action.json`. Enten flytter jeg banneren ned i artiklen
  på de næste mest besøgte, eller jeg sletter den fra hele bloggen, så AI-CTA'en
  ligger ét sted pr. side. Det er din beslutning, fordi det er en promo du har
  bedt om.
- **🟡 `indexnow_ping.sh` kaldes aldrig.** Målt 2/10: `grep -rn indexnow
  .github/workflows/ build_sites.py` giver **0 træffere** — skripten er skrevet,
  nøgle-filen serveres korrekt, men intet udløser den. Bing og Google er de to
  eneste søgemaskinereferencer (2 + 2 besøgende), så det er den billigste
  distribution vi ikke bruger. Jeg har ikke lagt den i CI, fordi et IndexNow-ping
  er et udadvendt kald til et eksternt API, og det er din beslutning. Sig til det,
  så lægger jeg ét step i `deploy-sites.yml` efter en vellykket udgivelse.
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
  **Haster lidt mere 2/10:** `/pricing` viser nu også `$29 once` for
  `eu-compliance-ebook-bundle`, så modsætningen med de syv bogside-ruter er synlig
  på **tre** sider i stedet for to. Den nye side tager dog ikke selv imod betaling
  — den sender læseren videre til `/paid-templates`, som gjorde det i forvejen.
- **🟡 Skal værktøjssiderne vise livstidsprisen overhovedet?** De elleve pro-kort
  på `/scan`, `/cookie-check`, `/contrast-checker` m.fl. har en gratis-mod-Pro-tabel
  med «$79/year per website». Jeg lagde livstidsprisen ind som et prislink dér, og
  to porte sagde nej: `check_stripe_ctas` dømmer «præcis 1 synlig lifetime-CTA pr.
  produkt», og `pro_card` dømmer «ét købsknap i ét pro-kort» — fordi tabellen ligger
  inde i kortet. Købsvejen findes allerede på de seks produktsider, så det er ikke
  en mistet indtægt, men det er en pris læseren ikke kan købe. Enten beholder vi
  den som ren tekst, eller jeg flytter den til en fane under kortet. Din beslutning.
- **🟡 `ceo/hub-readme-note` på origin er forældet.** Branchen har ingen kode —
  kun en plan-note fra 26/9 om en README der siden er blevet dømt af
  `check_repo_readme.py`. Jeg har ikke slettet den, fordi en note *er* unikt
  arbejde i den forstand. Siger du til, tager jeg den ned; ellers bliver den.
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
10. **Livstidsprisen lå på 17 sider uden købsvej — løsningen er fundet, og
    den er: ingen.** Hvem: alle der hellere betaler engang end pr. år; de tre
    livstidsudgaver er Stripe-varer med `limit: 100`. Tal: målt 2/10 — de 17
    sider viste beløbet, 0 af dem linkede til `lifetime.payment_link`, men de
    **seks produktsider** har den købsvej, og `check_stripe_ctas.py` dømmer
    «præcis 1 synlig lifetime-CTA pr. produkt». Accept: den er nået på den side
    hvor købet sker; de elleve værktøjssiders tabel skal fortsat vise prisen
    som tekst, fordi tabellen ligger **inde i** pro-kortet, og `pro_card.py`
    dømmer «ét købsknap i ét pro-kort». Datagrund: begge fund er målt i gaten
    efter en færdig implementering, ikke gættet. **Åbent:** om værktøjssiderne
   overhovedet skal vise livstidsprisen — se ❓.
11. ~~Én side med alle priser.~~ **Leveret 2/10** — `/pricing` (EN + DA) lister
    alle 12 katalogvarer med beløb, periode, omfang, gratis-mod-Pro og en
    købsvej, bygget af `tools/pricing_page.py` fra katalogen. Den **tager ikke
    imod betaling** — hver række linker til produktets egen købsside — så de tre
    porte bygget på «én købsvej pr. produkt» kan blive ved med at være strenge.
    Målt først: 0 af de 102 ruter nævnte to produkter i `<title>`/`<h1>`, så
    spørgsmålet «hvad koster hele pakken» krævede at gætte hvilken af otte
    sider der har svaret. Fund undervejs: `check_tool_paid_path.py`s ratchet dømte
    de to nye ruter som ubefalede, så `--write` skrev dem ind — 92 → 94 linjer.
12. ~~**Tjekket lå på mahope.tools, ikke på det site, der sælger det.**~~ **Leveret
    2/10** — `deskuptime.com` og `/da/` har nu ét tjek i `#check` lige under
    heroen, der kalder `/api/url-inspect` og svarer på de to første af de tre
    spørgsmål i sit eget h1. Hvem: alle der lander på forsiden (4 besøgende,
    100 % bounce, 0 s). Tal: checks pr. uge mod forsiden (baseline **0** — der var
    ingen kodevej til den). Accept: heroens primære handling er tjekket, formen er
    en rigtig GET så den virker uden JavaScript, og svaret siger ærligt at det
    *ikke* overvåger noget og ikke kan se indholdsændringer — det er CLI'ens og
    appens job. Datagrund: målt 2/10 på live — `/api/url-inspect` svarede 200
    med status, kæde, certifikat og headere, men blev aldrig kalt herfra; de to
    gratis webværktøjer lå 120 linjer prosa længere nede. Fund undervejs: listen
    af de otte headere lå i workeren og skulle hardkodes igen i klienten, så
    `securityHeadersChecked` kom i svaret, og `stripe-worker.test.mjs` fik to
    kontroller der fejler på den gamle kode (354/354). Fund undervejs, fundet af
    gaten: `check_donation_paths.py --self-test` blev rød, fordi den nye `#check`
    gør forsiden til en side der renderer et målt resultat — så den skal have
    donationslinjen, som `DU_DONATE` i siden nu sætter ind i resultatkortet.
13. ~~Samme tjek på de to andre forsider.~~ **Leveret — de tre er dækket nu.**
    `deskuptime.com` (12/9) og `mahope.tools` (2/10) fik et HTTP-tjek, fordi deres
    `<h1>` handler om *sitet*. `cleancopy.tools` fik i denne iteration et
    **konverteringstjek** i stedet, fordi dens `<h1>` er «Copy any web page as
    clean Markdown or plain text» — et HTTP-svar svarer ikke på det spørgsmål.
    Målt før: 7 af 9 besøgende på `/`, 71 % bounce. Efter: adresse ind, rigtig
    Markdown ud i browseren, samme motor som `/url-to-markdown`. Datagrund:
    Chromium 28/28 kontroller ved 390 + 1280 px.
14. ~~En gate for frontdørs-tjekkene.~~ **Leveret 2/10** — `front-door` og
    `front-door-selftest` kører i gaten. Dømmer **8** forsider fra
    build-manifestet: præcis ét tjek pr. `#check`, erklæret motor + `/net.js`
    indlæst, motoren leder præcis det form-id op, ingen rute uden `NET`, og formen
    virker uden JavaScript. Selvtest **16/16**, polaritet målt ved **5**
    mutationer af rigtige filer. Hvorfor: de 28 Chromium-kontroller lå i to
    midlertidige scripts, og motorernes `if (!form) return;` gør den stille
    fejlform umulig at se.
15. **Bundlen, der hedder gratis på syv sider og $29 på `/pricing`.** Hvem:
    læsere af `books/*` og købere på `/pricing`. Tal: katalogrækker pr. destination
    (baseline: 1 modsigelse, synlig på 3 sider). Accept: enten kontrakten og
    siderne er enige, eller den nye side har en købsvej der betaler sig. Kræver
    Mads' beslutning — se ❓. Datagrund: målt 2/10 i review-fundet, portene er
    grønne fordi ingen dommer den modsigende tekst.
16. ~~Forsidens tjek smed den adresse læseren lige havde indtastet.~~ **Leveret
    2/10.** Alle fire forsiders `next`-links bærer nu `#url=`, og de otte
    modtagelsessider læser den. Hvem: alle der trykker den dybeste handling på
    forsiden. Tal: felter der skal fyldes to gange pr. session (baseline: **2 →
    1** på både `mahope.tools` og `cleancopy.tools` — målt på kode, ikke på
    trafik). Accept: `check_url_handoff.py` grøn + **12** nye adfærdsdomme i
    `scan-clients.test.mjs`. Datagrund: bounce på mahope.tools' forside er 100 %
    (4 af 4 besøgende) og på cleancopy.tools' 71 % (7 af 9); de toforsider er de
    eneste steder, hvor vi *kan* fjerne et spørgsmål læseren netop har svaret på.
18. ~~**En simulering kunne ikke videresendes.**~~ **Leveret 2/10.** Se STATUS.
    Hvem: designere der skal have en kollega til at se præcis den samme
    simulering. Tal: delinger pr. uge mod simulatoren (baseline **0** — der var
    ingen vej, kun Copy code og Download, som begge kræver modtageren sidder
    med i samme værktøj). Accept: `cb-share.test.mjs` grøn og **RØD på den gamle
    kode**. Datagrund: 1 besøgende på `/color-blindness-simulator` og 100 %
    bounce; værktøjet er det eneste på sitet der producerer noget, en anden
    gerne vil se — og det døde i fanebladet. Fund undervejs: eksporten holdt
    ikke nye farver, så et link ville have løjet om indholdet.
17. ~~**Blogindekset holdt op at dække alle guides.**~~ **Leveret 2/10.** Alle
    189 guides (93 EN + 96 DA) har nu præcis ét link fra `/blog/`, de danske er
    grupperet i de samme fem emner med beskrivelser, og `check_blog_index.py`
    dømmer både dækningen og at siden er lig sin egen generator. Hvem: læsere
    der leder efter en guide, og de 20 artikler der lå uden indgående links fra
    en indeksside. Tal: guides uden link (baseline: **20** — 7 EN, 13 DA).
    Accept: `check_blog_index.py` grøn + 9/9 selvtest, polaritet målt ved to
    mutationer af den rigtige side. Datagrund: målt 2/10 på kildefilerne mod
    `site/blog/index.html`; bounce på mahope.tools er 94 % (18 besøgende), så
    her er tale om fund og interne links, ikke om besøg.
