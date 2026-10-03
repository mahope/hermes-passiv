# STATUS
- **Rød CI på `main` rettet 3/10 (rød siden 02:44).** `rule-claims-selftest`
  døde med «`da/blog/index.html` står ikke i PRODUCT_ENGINE». Ikke sidens fejl: to
  selftest-arme muterer en artikels `meta description` og rettede kun `/blog/`, så
  den danske hub stod med et **forældet** citat — og et forældet citat er
  indeksets *eget* løfte, præcis den fejl porten findes for. Nu retter begge arme
  alle indekser, og polaritets-armen køres på `/blog/` **og** `/da/blog/`. Målt:
  selftest grøn, `check_rule_claims` 240 løfter 0 fejl. Den danske guides-indeks
  (`cd48b18`) er færdig i historikken, men kunne ikke deployes fordi gaten var rød.
- **Tre review-fund fra 29/9 lukket 3/10.** (1) `/license-lookup` sagde «two
  websites on EUComply Pro, five elsewhere» — modsagt af tre andre sider. Nu
  **5/3/3/3/1** som tal, hvert bundet til sin `product_key`, dømt mod
  `tools/stripe_catalog.json` (25/25 selvtest, rød på tre mutationer). (2)
  Tak-sidens `<title>` fulgte ikke `<h1>` på en fejl: `titel()` sætter begge
  steder (128/128; 18 røde på den gamle kode). (3) `POST /api/license/devices`
  havde ingen tæller — nu 30/time pr. IP på eget scope, målt 429 på det 31. kald,
  `validate` svarer stadig 200 (375/375; rød på den gamle worker).
- **Deploy:** `build-info.json` står på **`2f91b61`** på alle tre domæner, så
  `ceo/license-selvbetjening` og `ceo/support-koen-er-donation` er målt
  `DEPLOY OK`. `ceo/da-guides-indeks` (`cd48b18`) er **ikke** live: CI var rød, og
  denne commit retter årsagen. PR-TJEK 3/10: 0 PR'er. BRANCH-TJEK 2/10: 2 fuldt
  landede slettet; `ceo/hub-readme-note` har kun 1 plan-note, intet kode — se ❓.
- **❓ Til Mads:** uændret: `OPENROUTER_API_KEY`, `STATS_TOKEN`, `bugbottle.dev`s
  domæne, bogens betalte udgave mod 7 sider der siger gratis, 2 desktop-apps der
  ringer til Lemon Squeezy, Search Console, IndexNow-ping, livstidsprisen,
  `/blog/`s danske-guider-tal. Resten: ❓.

## Verificér deploy

- `VERIFICÉR DEPLOY: antal fra katalogen + faneblad på tak-siden + tæller på
  /api/license/devices ceo/license-tal-og-tæller 2026-10-03 03:20`

- **`DEPLOY OK 2026-10-03` — `ceo/license-selvbetjening` er live, målt på
  indhold.** `build-info.json` står på **`2f91b61`** på alle tre domæner.
  Live `/license-lookup` har præcis **én** «Free up a machine», to
  `/api/license/devices` og ét `/api/license/deactivate`, `seatForm` 6 gange.
  Samme commit-slug dækker den forrige note: `/thanks` har 1
  `href="/license-lookup"` + «Lost your key?» og 2 `href="/support"`.

- **`DEPLOY-MISSING 2026-10-03` — `ceo/da-guides-indeks` (`cd48b18`) er ikke
  live.** Kørslen 02:44 døde i `rule-claims-selftest` (se STATUS), så
  deploy-jobbet aldrig kørte. Årsagen er rettet i `ceo/license-tal-og-tæller`;
  næste iteration verificerer indholdet på `/da/blog/`, ikke bare HTTP 200.

- **`DEPLOY OK 2026-10-03` — `ceo/scan-sider-laest-tal` er live, målt på indhold.**
  `build-info.json` står på **`55ea279`** på alle tre domæner. `/compliance-site-check`
  (EN og DA) har **4** forekomster af «pages read» / «sider læst» og **0** af
  «pages checked» / «kald udført». `/thanks` har stadig den gamle linje her,
  fordi den først deployes med noten ovenfor.

- **`DEPLOY OK 2026-10-03` — begge forrige noter er live, målt på indhold.**
  `build-info.json` står på **`34e9c2d`** på alle tre domæner.
  - Bogbanneret (34e9c2d): `/books/gdpr-for-agencies/` har **0** forekomster af
    «annex», og banneret siger nu præcis «the free DPA generator asks who is
    controller and who is processor». Siden er byte-identisk med `dist/`.
  - Byggetagen (158715e): live `style.css` er **byte-identisk** med
    `dist/mahope.tools/style.css`, og `details.faq summary { cursor: pointer }`,
    `.gen legend { font-weight: 700 }`, `.gen label`, `.book-card-body
    { min-width: 0 }` og `.book-header .tagline` står der. `.plat-links a` er en
    grupperet regel (linje 511), ikke en egen — pillen er der.
  - Målt undervejs, ikke et fund: 6 af 7 bogsider er byte-identiske med
    `dist/`; `nis2-for-agencies` afviger kun fordi **Cloudflare** har
    obfuskeret en mailadresse til `data-cfemail`. Ikke en gammel udgivelse.

- **`DEPLOY OK 2026-10-02` — `ceo/site-icons-h1` er live, målt på indhold.**
  `build-info.json` står på **`692d7b2`** (squash-sha'en). De tre sider der ligger
  på mahope.tools har den nye overskrift i markupken: `/site-icons` «Every icon
  your site needs, from one SVG», `/page-profile` «Profile any web page from
  your terminal», `/da/page-profile` «Tjek enhver websides tekniske sundhed».
  Den fjerde, `/bugbottle-demo`, svarer 404 fordi siden kun findes i
  `dist/bugbottle.dev/`, som ikke deployes — det er ❓ om domænet, ikke en fejl.

- **`DEPLOY OK 2026-10-02` — alle tre næster er live, målt på indhold.**
  `build-info.json` står på **`4c41d9e`** (squash-sha'en) på **mahope.tools**,
  **cleancopy.tools** og **deskuptime.com**. Domænernes sider er
  **byte-identiske med `dist/`** (`diff` på simulatoren og `/blog/`), så det er
  *denne* kode der er live og ikke en senere.
  - `ceo/plan-gate-og-502-kvote` (4c41d9e): begge simulatorer har præcis **én**
    `(globalThis.CBSHARE || {}).decode(location.hash)`-læser, **én**
    `id="copy-share"`, **én** `addEventListener('click', copyShare)` og **én**
    `<script src="/cb-share-core.js">`; `/cb-share-core.js` svarer **200** med
    `encode`+`decode`. `colors[colors.length-1]` findes kun i de to forklarende
    kommentarer, der fortæller hvorfor den gamle kode lå sort på sort.
  - `ceo/cb-simulator-del-link` (b55e036): samme to sider, samme greb.
  - `ceo/blog-indeks-dode-links` (27f8aa2): `mahope.tools/blog/` svarer 200,
    de fire BugBottle-guider står **relative**
    (`/blog/bug-reports-in-ci-pipeline`) og **0** `https://bugbottle.dev/…`
    på siden. Dom 1: `check_blog_index.py` **93 EN + 96 DA, 0 problemer**,
    `stripe-worker.test.mjs` **354/354**, `seo_check.py` **314 sider, 0 fund**,
    `check_inline_js.py` **0**, hele `quality_gate.py` **146 steps GRØN**.

## Åbne opgaver

1. ~~**En nøgle der ikke aktiverer, har ingen selvbetjening.**~~ **Færdig 3/10.**
   Kunden lister sine maskiner på `/license-lookup` og frigør selv, via den
   testede `/api/license/deactivate`. `docs/plan-arkiv.md`.
2. ~~Flere sider end forsiden pr. URL.~~ **Færdig 1/10.** Kaldet læser den
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
   dansk sætning. Målt 2/10: der findes **ingen** `/da/books/*`-ruter overhovedet
   (hverken i `dist/` eller i sitemap), så de 6 bogsiders hreflang har intet
   dansk par — det er derfor værktøjsbanneret fra i dag kun findes på de
   engelske sider.
8. ~~**Byggetagen sletter sidelinje for 28 selectors designsystemet ikke ejer.**~~
    **Færdig 3/10.** Alle 154 `OWNED_SELECTORS` er nu erklæret i `style.css`, så
    påstanden er sand og målbar. De 14 manglende fik skallens egne værdier, ikke
    sidens: `.plat-links a` (1 side) fik pillen tilbage i tokens, `details.faq
    summary` (4) fik `cursor: pointer`, `.book-card-body` (2) fik `min-width: 0`,
    `.book-header .tagline` (6) fik 18px + 12px luft, `.gen label`/`.gen legend`
    (10 generator-sider) fik 600/700 og luften. Ny port `check_owned_selectors`
    + `--self-test` **11/11**, to gatestræk. Polaritet: **14 røde** på
    style.css fra før rettelsen mod **0** på den nye. Flyttet til
    `docs/plan-arkiv.md`.
    **Rettet i samme opgave:** planens påstand om 230 px vandret scroll på
    `/page-profile` holdt ikke — Chromium giver **0 px** ved 390 og 1280 px, på
    både gammel og ny kode.

## ❓ Til Mads

- **🟡 `/blog/` siger «96 Danish guides», men 11 af dem ligger på
  cleancopy.tools.** Målt 3/10: `site/da/blog/` har 96 artikler, `dist/` kun
  85 — de 11 `html-til-markdown`/`clean-copy`-artikler er korsomviseret til
  cleancopy.tools af buildet, som det er ment. Tallet i heroen er bundet til
  *kilden* af `check_blog_index.py`, så det er samme opgave at rette begge
  steder, og det er en beslutning om hvilket tal læseren skal se: 96 på tværs
  af familien eller 85 her. Jeg har ændret det nye sprog til «Vores 96 danske
  guider» og ladt `/blog/` være, så de to sider ligner hinanden.
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
- **🟡 Skal det frie flerstedes-tjek få en kundeklar rapport? Det er den
  betalte linje.** Målt 3/10 på `/compliance-site-check`: feltet tager fem
  URL'er («handy when you are auditing several client sites»), og
  `downloadReport()` giver **én** `.md` med alle fem sider i. Et bureau kan
  altså ikke sende hver kunde sin side — kun samlet. Men pro-tabellen på
  samme side siger at Pro giver «The findings as a PDF report you can hand a
  client», og `/compliance-report` sælger præcis det. En gratis
  kundeklar rapport ville derfor tage en betalt vare, så jeg har **ikke** bygget
  den. Tre veje: (a) behold som nu — gratis er de ni tjek, betalt er leverancen;
  (b) giv gratisværktøjet én `.md` pr. side i ét klik, og flyt Pro-teksten til
  «hele sitet + de 18 server-tjek»; (c) gør det til det Pro-produkt, det er.
  Din beslutning — den flytter en $79-årslinje.
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
19. ~~**Tak-siden lovede hjælp på en donationsside.**~~ **Leveret 3/10.** Se
    STATUS. Hvem: kunder der lige har betalt og så møder en nøgle der ikke
    virker. Tal: links til `/support` der lover hjælp (baseline **1 af 274** i
    den byggede side — kun `/thanks`; de 273 øvrige er fodnote, «say thanks» og
    fire `hreflang`). Accept: ny port `support-link-text` grøn med **21/21**
    selvtest, **1 rød** mod den gamle `thanks.html` i `dist/`, og browseren
    målt ved 390 og 1280 px (0 px vandret scroll, `<h1>` skifter kun på den
    bekræftede vej). Datagrund: `/support` er målt live — donationsside, ingen
    licensindhold. Næste skridt er punkt 1 under «Åbne opgaver».
20. ~~**Læsevisningen sluttede i et tomrum.**~~ **Leveret 2/10.** Hvem: en
   læser der lige har læst to kapitler om cookies, DPA, NIS2 eller EAA — den
   højeste vilje til at gøre noget på sit eget site. Tal: bogsider der linker
   til et af vores egne værktøjer (baseline: **0 af 6**; målt på kildefilerne
   mod `dist/`, hvor `/free-tools` og `/compliance-report` var de eneste interne
   nævn). Accept: **6 af 6** bogsider har præcis ét `blog-tool-cta` **sidst i
   `reader-body`**, hver med ét `btn-primary` på en route der findes
   (`/cookie-check`, `/dpa-generator`, `/nis2-check`, `/scan`, `/site-icons`) —
   målt på den byggede side, ikke på kildekoden. **Fund undervejs, målt i
   browseren:** banneret renderede som **brødtekst med et blåt understrevet
   link** — læsevisningens egen CSS var **død** på alle seks bogsider, fordi
   `OPTIONAL_RULES`/`CTA_RULES` er *værdier* til `str.format`, der ikke
   genbehandles, så `{{ }}` kom bogstaveligt ud i `<style>`: browseren kassede
   hver regel, og læsevisningens tabeller, kodeblokke, citater og `h4` har
   været uden styling lige siden den blev skrevet. Nu: `.btc a.cta` har
   `background: rgb(11,110,143)`, `text-decoration: none`, i lys **og** mørk;
   **0 px** vandret scroll ved **390** og **1280**. `book_reader --self-test`
   **48/48** med to nye domme, polaritet målt ved at genskabe `{{` → **RØD**.
   Datagrund: bogen er fri, så
   læsevisningen er hele værdien; en læser der læser videre og så rammer en
   mur har mistet hele familien af gratis værktøjer. Fund undervejs:
   `/site-icons`' egen `<h1>` er «site-icons» — ny opgave 8. Bevidst valgt **ikke**
   at lægge banneret i heroen: bogsiden har allerede bogens download-CTA, og
   bannerets plads i kapitlerne er der, hvor læseren lige er færdig.
22. ~~**En dansk læser blev sendt på den engelske indeks.**~~ **Leveret 3/10.**
    `/da/blog/` findes nu, på dansk, med alle 96 danske guider, de fem danske
    emner og dansk chrome; dansk nav, footer og brødkrumme peger derhen.
    Hvem: de danske læsere — hele familien er dansk, og `/da/` er den rute
    Mads' egne kunder kommer ind ad. Tal: danske sider der linker til den
    engelske indeks i chrome (baseline **97 sider / 282 links**, målt på
    `dist/`; nu **0**). Accept: `check_blog_index.py` dømmer den danske sides
    dækning, generatorens ejerskab og de to tal, **og** at ingen dansk side
    peger på `/blog/` i nav/footer — 15/15 selvtest med polaritet målt ved at
    slette siden. Datagrund: målt 3/10 på `dist/`, ikke gættet; de 96 danske
    artikler lå uden for enhver dansk indeks.
21. **Én rapport pr. kunde i stedet for én fil med alle kunder i.** Hvem: bureauer
    og webbureauer, der er målgruppen for `/compliance-site-check`’s egen
    teksthint («auditing several client sites»). Tal: rapporter pr. kørsel med
    flere sider (baseline **0** separate — kun samlet `.md`; målt på koden 3/10).
    Accept: én `.md` pr. side i ét klik, hver med sit eget filnavn på kundens
    domæne. Datagrund: feltet er bygget til fem sider og rapporten skriver alle
    fem i én fil, så det er en funktion der mangler, ikke en der skal opfindes.
    **Åbent:** se ❓ — pro-tabellen på samme side lover kundeklar rapport som
    den betalte vare, så jeg kan ikke bygge den gratis uden dit valg.
