# STATUS
- **3/10: rettelsen sagde hvad den havde rettet — næppe.** Efter «Fix it»
  skrev værktøjet «I put a 24 % dark layer behind the text and measured
  again» og viste **kun** det nye tal. Hvad rettelsen havde vundet, var væk:
  bruteren så 1,16:1 og så 4,72:1, og intet stod at de to hørte sammen. Der
  står nu **«Før dette målte den 1,16. Nu måler den 4,72.»** på begge veje —
  «Fix it» *og* «Find det bedste sted» — på alle fire sider, og den forsvinder
  i samme øjeblik bruteren selv rører farve, font, pladsering eller billede,
  samme nulstilling som sløret og `lastFix`.
  `check_contrast_sampling` **96 løfter** (var 72), `--self-test` **88/88**
  med tre mutationer af rigtige filer.
- **Målt 3/10 i browseren:** «1,16:1 → 4,72:1» i `#result` på
  `/text-on-image-checker` og på artiklen, 0 px vandret scroll ved 390 og
  1280 px, dansk side giver komma.
- **3/10: værktøjet sagde «målt på dine bogstaver» om et billede det selv havde
  tegnet.** Kontrasttjekkeren maler sit eget eksempelbillede ind ved sidevisning
  og måler på det med det samme, så en læser der ikke har uploadet noget fik
  «PASS — 5,42:1 … under *your* letters» uden at vide hvor tallet kom fra. Der
  står nu en note *før* PASS/FAIL-kappen på alle fire sider (EN+DA, værktøj og
  artikler), og den forsvinder i samme øjeblik bruteren vælger sit eget billede —
  samme nulstilling som sløret og `lastFix`. `check_contrast_sampling` **72
  løfter** (var 58), `--self-test` **70/70** med to mutationer af demo-noten.
- **3/10, øvrige leverancer:** tak-siden kan tale dansk (45 ens nøgler, 184/184
  med 45 røde mod koden fra før) og kan ikke læse prototypenøgler i `?lang=`
  (egen-ejendoms-prøve, 196/196 med 8 røde) — begge målt i Chromium ved 390 og
  1280 px. Scanneren siger hvad der er ændret siden sidste scanning af samme
  adresse (119/119, 13 røde). Kontrasttjekkerens «Find det bedste sted» måler 20
  steder med samme `sampleContrast()` som tallet kommer fra (58 løfter, 63/63).
- **Målt 3/10, så næste iteration ikke måler det igen:** (a) ingen vandret scroll
  på 390 px på `/`, `/text-on-image-checker`, `cleancopy.tools/` (CDP); (b)
  `cleancopy.tools/blog/` **404 er tænkt** (buildet omskriver nav-linket);
  (c) 21 ruter på de fire domæner svarer **200**; (d) alle 16 Stripe-links
  svarer **200** på HEAD.
- **Næste opgave: punkt 4** — 172 sider har stadig to-tre knapper over folden
  (kræver beslutning, se ❓). Egne opgaver: se `## Feature-kø`.
- PR-TJEK 3/10: 0 PR'er. BRANCH-TJEK 2/10. CI grøn på `main` (ét kald, 3/10).
- **❓ Til Mads:** uændret: `OPENROUTER_API_KEY`, `STATS_TOKEN`, `bugbottle.dev`s
  domæne, bogens betalte udgave mod 7 gratis-sider, 2 desktop-apps mod Lemon
  Squeezy, Search Console, IndexNow, livstidsprisen, `/blog/`s danske-tal.

## Verificér deploy

- `ceo/foer-til-nu` **VERIFICÉR DEPLOY: ceo/foer-til-nu 2026-10-03 15:0x.**
  Live `https://mahope.tools/text-on-image-checker`: upload et todelt billede,
  læg hvid tekst på den lyse halvdel, tryk «Fix it» → `#result` skal have præcis
  ét `data-ti-delta="…|…"` hvor **første** tal er det der stod *før* trykket og
  andet er det på skærmen nu, på **begge** sprog (dansk med komma). Efter at
  bruteren selv rører farvefeltet skal attributtet væk. Samme på
  `/text-on-image-checker-da` og de to artikler.

- `ceo/demo-billede-er-ikke-dit` **VERIFICÉR DEPLOY: ceo/demo-billede-er-ikke-dit
  2026-10-03 13:2x.** Live `https://mahope.tools/text-on-image-checker` skal
  vise **1** `data-ti-demo` og teksten «Example image, not yours — choose an
  image above to measure your own.» *før* `ti-badge` i DOM'en, og
  `/text-on-image-checker-da` + de to artikler skal have den på hvert sprog.
  Efter et upload skal `data-ti-demo` være væk — målt ved at sætte en fil i
  `#file` i browseren. `https://mahope.tools/build-info.json` skal bære merge-
  shas på alle tre domæner; `routes_sha256` flytter sig kun fordi
  `style.css` er rørt.

- `ceo/tak-side-sprognoegle` **VERIFICÉR DEPLOY: ceo/tak-side-sprognoegle 2026-10-03 12:55.**
  Tjek på live: `/thanks?session_id=…&lang=constructor` (eller `toString`,
  `__proto__`) skal give **engelsk** og 0 «undefined» i DOM'en — altså samme
  som URL'en uden `?lang=`. `?lang=da` skal stadig give dansk.

- ~~`ceo/scan-hvad-er-aendret`~~ **DEPLOY OK 3/10.** Hentet fra live:
  `mahope.tools/scan` har «Start here — the 3 findings that matter most» og
  «Since your last scan of this page», `mahope.tools/scan-da` har «Start her —
  de 3 fund der betyder mest» og «Siden din sidste scanning af denne side».
  *Ikke* kørt: den to-scaning-interaktion i en rigtig browser (localStorage).
  Indholdet i de to byggede sider er målt på live, og det er den kode der
  tegner begge strenge.

- ~~`ceo/scan-score-af-fundene`~~ **DEPLOY OK 3/10.** Live `/scan` med et link
  der siger `s=100`: **«71/100 — Grade C»** + «2 error(s), 1 warning(s)»,
  `/scan-da`: «2 fejl, 1 warning(s)», **0** `onerror`-noder i `#result` på begge.
  Porten `node tests/scan-share.test.mjs` siger **84/84**.
- ~~`ceo/find-bedste-sted`~~ **Delvis DEPLOY OK 3/10.** Siden er live med knappen
  og kernen (`text-on-image-core.js:328-367`) på EN + DA, og
  `check_contrast_sampling.py` er grøn med **58** løfter + `--self-test` **63/63**.
  Den *interaktive* prøve (upload → «find det bedste sted» → bedre tal) er ikke
  kørt i en rigtig browser i denne iteration — kun kildekoden og den byggede
  side er målt.

- Alle tidligere noter er `DEPLOY OK` eller dækket af en nyere og ligger i
  `docs/plan-arkiv.md`.

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
9. ~~**Et delt resultats score kommer fra linket, ikke fra fundene.**~~
   **Færdig 3/10.** `encode()` skriver ikke længere nogen score, og `decode()`
   regner den fra fundene med `scoreOf()` — den samme funktion begge sider nu
   bruger til en netop kørt scanning, så der er én formel og ikke tre.
   Gamle links med `s=` åbner stadig. Målt: `decode()` af et link med `s=100` og
   ét error-fund giver **88**, DOM-kortet siger **71/100 — Grade C** over «2
   error(s)», og porten er **11 rød** på koden fra før.
   `tests/scan-share.test.mjs` **84/84**. Flyttet til `docs/plan-arkiv.md`.
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
23. ~~**Værktøjet sagde «try en mørkere farve» og lod læseren regne det ud.**~~
    **Leveret 3/10.** Se punkt 1 i STATUS. Hvem: alle der lægger en hvid
    overskrift på et todelt billede — den største indgangsside på sitet.
    Tal: resultater der gik fra FAIL til PASS pr. klik (baseline **0**, fordi
    der ikke var nogen knap; målt i browseren **1,16:1 → 3,04:1**). Accept:
    `check_contrast_sampling` **38** løfter med 4 nye fix-domme, hvoraf dommen
    på «maks 1,5× kravet» fanger den mutation der regner i kanalværdi, og
    ratchet på at begge slør-retninger har hver sin tekst på alle fire sider;
    `--self-test` **24/24**. Datagrund: Plausible 28 d — artiklen er 8 af 18
    besøgende på mahope.tools med 100 % bounce, og dens egen `<h1>`-sætning
    omhandlede præcis den fejl værktøjet nu retter for læseren.
21. **Én rapport pr. kunde i stedet for én fil med alle kunder i.** Hvem: bureauer
    og webbureauer, der er målgruppen for `/compliance-site-check`’s egen
    teksthint («auditing several client sites»). Tal: rapporter pr. kørsel med
    flere sider (baseline **0** separate — kun samlet `.md`; målt på koden 3/10).
    Accept: én `.md` pr. side i ét klik, hver med sit eget filnavn på kundens
    domæne. Datagrund: feltet er bygget til fem sider og rapporten skriver alle
    fem i én fil, så det er en funktion der mangler, ikke en der skal opfindes.
    **Åbent:** se ❓ — pro-tabellen på samme side lover kundeklar rapport som
    den betalte vare, så jeg kan ikke bygge den gratis uden dit valg.
26. ~~**Stedet, ikke kun tallet.**~~ **Leveret 3/10** (`845808f`). Hvem: alle der lægger en overskrift på et
    foto med både en lys og en mørk flade — artiklen er 8 af 18 besøgende på
    mahope.tools. Tal: billeder der består efter «find det bedste sted» (baseline
    **0** — der var ingen vej; bruteren måtte trække teksten rundt for selv at
    finde ud af, om den kunne ligge andet sted). Accept: ét klik flytter
    teksten til det bedste af 20 målte steder, og porten dømmer pladseringen —
    knap, bedre tal, beskrivelsen, og at den forsvinder ved bruterens egen
    flytning. Datagrund: artiklens egen regel siger «mål det dårligste, ikke
    gennemsnittet», og det var netop dét værktøjet ikke kunne.
25. ~~**Den rettede grafik som en fil.**~~ **Leveret 3/10** (`65eef7f`). Hvem: designere der lægger tekst på et
    foto og har brugt værktøjet til at få den til at bestå. Tal: downloads pr.
    uge (baseline **0** — der var ingen vej; værktøjet endte ved et tal, og så
    måtte bruteren selv finde ud af hvordan han fik sit rettede billede ud igen,
    målt på koden 3/10). Accept: én klik giver et PNG af *billedet med
    rettelsen* på alle fire sider, og porten dømmer den hentede fil — knap,
    format, navn og pixels — ikke bare at knappen findes. Datagrund: artiklen
    `/blog/text-on-image-contrast-check` er 8 af 18 besøgende på mahope.tools
    (44 % af al trafik, 100 % bounce), og værktøjet er præcis der inde.
24. ~~**Et delt scanelink, der viste en tom formular.**~~ **Leveret 3/10.**
    Se punkt 1 i STATUS. Hvem: bureauer og webbureauer, der scanner en kundes
    side og vil sende fundene videre. Tal: fund delt pr. scanning med et helt
    resultat (baseline **0** — linket indeholdt kun URL'en, så modtageren så en
    tom formular og brugte sin egen kvote; målt i testen: `fetch` tælles, del-
    stien kalder nul gange). Accept: `tests/scan-share.test.mjs` **75/75** med
    polaritet på tre mutationer, og dommen læser *begge* rigtige sider, så den
    danske ikke kan få sin egen kopi og drive fra den engelske. Datagrund:
    målt på koden, ikke gættet — `shareResult()` kopierede
    `location.origin+'/scan#url='+…` og ingenting else.
29. **~~Rettelsen sagde hvad den rettede.~~** **Leveret 3/10.** Se punkt 2 i
    STATUS. Hvem: designere der lægger en overskrift på et todelt foto — den
    største indgangsside på sitet. Tal: resultater der får en målt forskel
    (baseline **0 af 4** sider; kernen skrev «…and measured again» uden at
    nævne hvad den målte førhen — målt på koden 3/10). Accept: ét
    `data-ti-delta` pr. rettelse på begge veje ind i kernen, hvis før-tal er det
    der stod på skærmen da knappen blev trykket, og linjen væk når bruteren selv
    griber ind. Datagrund: Plausible 28 d — artiklen er 8 af 18 besøgende med
    100 % bounce, og bruterens spørgsmål efter en rettelse er «virker det?», som
    et nyt tal uden en forskel ikke svarer på.
27. ~~**En fund-liste uden «start her» og uden forskel.**~~ **Leveret 3/10.**
    Se punkt 2 i STATUS. Hvem: bureauer og webbureauer der har rettet fundene
    siden sidste scanning — de vidste ikke, om det virkede, fordi et nyt tal
    uden en forskel ikke svarer på det. Tal: resultater der får en forskelslinje
    (baseline **0** — ingen vej, kun et nyt scorecard; målt på koden 3/10).
    Accept: `scan-share.test.mjs` **119/119** med **13 røde** mod koden fra før,
    dommen på at et *delt* resultat aldrig skriver «siden din sidste scanning»,
    og at forskelsen skrives med læserens sprog og ikke med fund-id'er. Datagrund:
    15 WCAG-regler giver typisk 8–14 fund pr. side, i den rækkefølge koden kører
    dem i — så en side med fire billeder uden alt-tekst viste ALT-kravet før den
    ene knap uden navn.
28. ~~**Tallet på skærmen handlede om et billede læseren aldrig havde set.**~~
    **Leveret 3/10.** Hvem: alle der lander på `/text-on-image-checker` eller på
    artiklen — den største indgangsside på sitet. Tal: resultater der siger hvad
    de måler (baseline **0 af 4** sider; kernen tegnede sit eget eksempelbillede
    og skrev «Measured against the lightest and darkest image pixels under your
    letters» om et billede brugeren ikke havde uploadet — målt på den byggede
    side 3/10). Accept: `data-ti-demo` står **før** PASS/FAIL-kappen på alle
    fire sider, forsvinder ved upload, og porten dømmer begge dele —
    `check_contrast_sampling` **72** løfter (var 58), `--self-test` **70/70**.
    Datagrund: bounce på `/blog/text-on-image-contrast-check` er 100 % (8 af 18
    besøgende); en læser der tror at have målt sit eget foto og så måler et
    andet, kommer tilbage med et forkert spørgsmål — eller kommer slet ikke.

