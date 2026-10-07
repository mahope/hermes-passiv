# STATUS
- **CI:** grøn 7/10 efter `ceo/deskuptime-da-ci-fix` — den danske
  DeskUptime-forside manglede fire fraser i `stripe-ctas`: «én gang,
  3 maskiner», «client-report», «Enkelttjek» og «SSL- og content-tjek».
  Rettet i pro-tabellen. Gate grøn.
- CEO-kø punkt 0 (review-fund 29/9) verificeret færdigt: alle fem
  punkter rettet (`10f95b42`, `b772a466`, `67092c4c`, `e37b30a6`), gaten grøn,
  live `/api/url-inspect` svarer 200.
- **Sentry er sat op og testet** (worker 149-246, test 1748-1833): DSN i kode,
  kun produktion, ingen PII, ingen traces/replay, 5 rapporter/min. «Ingen uløste
  fejl» betyder ingen fejl — ikke at intet sendes.
- **Alle fire VERIFICÉR DEPLOY-noter er live og lukket** 7/10: farveværktøjer
  EN+DA, kontrast-fix-farve (`#8b7500`, ratio 4,52), billede-drop-og-indsaet.
- **7/10:** seks forside-/værktøjstitler gjort ≤60 tegn, så `clamp_title` ikke
  taber nøgleord («machine», «Mahope», «Tritanopia»). Blogtitler er bevidst
  lange overskrifter — H1 viser den fulde titel.
- **Sporingen virker** (målt 6/10): `contrast-measured` i `/api/results` efter
  33 s. Ærlig baseline: **0 rigtige** kørsler. `/api/stats` er 401 uden
  `STATS_TOKEN`.
- **DeskUptime 'no phone-home' rettet** (`7dc00071`): hero + FAQ på EN/DA
  forklarer nu ærligt at URL-liste/resultater bliver lokalt, men
  Pro-licensaktivering checker op mod mahope.tools.

## Åbne review-fund

Ingen. Alle tre lukket 6/10 — teksten står i `docs/plan-arkiv.md`.

## Verificér deploy

- **DEPLOY OK 7/10:** gratis/Pro-tabel + købsknap på de to danske
  farveværktøjssider `ceo/da-farvevaerktoejer-koeb`. Live: begge bærer
  `id="pro"`, `Køb EUComply Pro — $79/år pr. website` og betalingslinket.
- **DEPLOY OK 7/10:** gratis/Pro-tabel + købsknap på de to engelske
  farveværktøjssider `ceo/farve-vaerktoejer-koeb`. Live: begge bærer
  `id="pro"`, `Buy EUComply Pro — $79/year per website` og betalingslinket.
- **DEPLOY OK 7/10:** farveforslaget i kontrastværktøjet `ceo/kontrast-fix-farve`.
  Live: `#cc-fix-use` findes, og `#ffd700` på `#ffffff` giver `#8b7500`
  (ratio 4,52). Samme på `/contrast-checker-da`.
- **DEPLOY OK 7/10:** billede-drop-og-indsaet `ceo/billede-drop-og-indsaet`.
  Live: `text-on-image-core.js` har `drop`, `paste` og `loadFile`.
- `pro-kortet på de fire scanneresider` er **DEPLOY OK 6/10**:
alle fire sider bærer `compliance-report#url=` i den udgivne markup
(`/scan`, `/scan-da`, `/compliance-site-check`, `/da/compliance-site-check` —
den danske scan-rute hedder `/scan-da`, **ikke** `/da/scan`, som den gamle note
påstod; den findes ikke og svarer 404), noten «See what Pro adds before you buy»
er væk på alle fire, og `#url=`-vejen er fulgt i Chromium mod live: feltet bliver
`https://example.com` og rapporten kører (95/100, grade A) uden et klik.

## Åbne opgaver

3. **Konvertering kan ikke måles uden `STATS_TOKEN`.** Hvorfor: `/api/stats`
   svarer 401 siden uge 37, så næsten hver linje i enhver trafikrangering er vor
   egen links-tælling, ikke besøg. Accept: `GET /api/stats` med token svarer 200.
   *(Blockeret på Mads — se ❓.)* **Målt 5/10:** resultaterne (`/api/results`,
   feature-kø 6) og købsforsøgene (`/api/conversion`) er nu *begge* læsbare uden
   token, så de **22** nye kontroller dømmer at de to lister hver især er sig egen
   — et resultat kan ikke læses som et køb. Kun **beløb og udleverede licenser**
   mangler stadig, og de står i Stripe. Opgaven står derfor åben, men den er ikke
   længere blokeringen for at prioritere.

4. **`bugbottle.dev` deployes ikke.** Hvorfor: `deploy-sites.yml`-matrixen
   deployer kun tre domæner. **2/10 er følgen målt og lukket:** de fire
   BugBottle-guider ligger på `mahope.tools`, så `/blog/` har ingen døde links;
   domænets egen forside ligger stadig i `UNMANAGED_DOMAINS`. Accept: domænet på
   Pages og fjernet af `UNMANAGED_DOMAINS`, eller fjernet fra `TRACKING_DOMAINS`.
   *(Beslutning — se ❓.)*

6. **Bogen har ingen DA-udgave, og læsevisningen gør det tydeligt.** Hvorfor: de
   seks bøger er på engelsk. Målt 2/10: der findes **ingen** `/da/books/*`-ruter,
   så bogsiders hreflang har intet dansk par. Accept: enten en DA-udgave af de to
   vigtigste som EPUB i `ebook/`, eller en synlig dansk note på bogside-ruterne.
   Kræver beslutning — se ❓.

8. **En sitemap-rute må ikke have en død eneste handling.** Hvorfor: porten
   dømmer kun de to ruter i `tools/unavailable_routes.json`. Accept: porten
   finder den, hvis den skrives i manifestet. *(Kun relevant når vi tilføjer flere
   sådanne sider — ikke en opgave i sig selv.)*

21. **En `ceo/*`-gren er ikke arbejde, fordi den ligger uden for `main`.** Hvorfor:
    målt 5/10 — alle fire var dubletter, og to ville have reverteret
    `3755b96f` + `158715e9`. Accept: før en gren nævnes i planen skal
    `git cherry main <gren>` være læst, og dens rørte filer sammenlignet fil-for-fil
    med `main`. En `+` er ikke nok, fordi patch-id skjuler at main er ældre.


## ❓ Til Mads

- **🔴 `OPENROUTER_API_KEY` mangler på workeren — assistenten er stadig slukket.**
  Sagen siger at assistenten er slukket og byder på scanner, erklæringsgenerator
  og de tre bøger, og begge ruter er ude af sitemap og `llms.txt`. **Når du sætter
  nøglen:** fjern `<meta name="robots" content="noindex,follow">` fra
  `site/compliance-ai.html` + `site/da/compliance-ai.html`. **Banneren på
  AI-siderne følger samme nøgle** (så mange, `check_ai_cta_honesty.py` tæller
  dem hver kørsel): sæt `"available": true` i `tools/ai_cta.json`,
  kør `python3 tools/check_ai_cta_honesty.py --apply`.
- **🔴 `STATS_TOKEN` på workeren.** Én linje, én secret, og så kan konvertering
  måles i stedet for gættes. Uden den er `/api/stats` 401, og opgave 3 bygger på
  tal, der ikke er besøg.
- **🔴 `bugbottle.dev` ligger på en server, vi ikke deployer.** Live svarer
  **404 fra `nginx`**, mens de tre andre domæner bærer alle samme sha. To veje:
  (a) domænet på Cloudflare Pages → jeg tilføjer det til matrixen og fjerner
  undtagelsen i samme commit; (b) det er ikke vores at udgive → det ud af
  `TRACKING_DOMAINS`, så `traffic_status` bliver ærlig for de tre vi deployer.
- **🔴 To betalte desktop-apps kan ikke aktiveres.** Målt i de shippede binære:
  `mahope/transmute` `v0.2.1` og `mahope/deskuptime` `desktop-v0.2.7` har begge
  `https://api.lemonsqueezy.com/v1/licenses/activate` indbygget. Vores
  `/api/license/activate` kræver `{ license_key, device_id, product }`; kilderne
  ligger i private repos, og du laver selv releases.
- **🔴 Bogen er gratis, men Stripe har et betalt bundlet produkt.** Kontrakten
  lister `eu-compliance-ebook-bundle` til **$29**, mens **syv** sider siger modsat
  («Free download … we do not sell a paid edition of it»), og `/pricing` viser
  prisen for tredje gang. Vi har aldrig linket til det betalte link. To veje: (a)
  slet produktet og linket i Stripe; (b) lav en ny betalt udgave der betaler sig.
  Din beslutning, fordi det er dit navn på kvitteringen.
- **🟡 Skal scanner- og AI-banneren ligge over folden på de 172 sider?** Målt 30/9
  giver det **tre knapper oven på folden** pr. artikel, og på 30 af dem er knappen
  *oveni* et anker som «læs videre». 2/10 er de 10 mest besøgte rettet. Enten
  flytter jeg banneren ned i artiklen på de næste mest besøgte, eller jeg sletter
  den fra hele bloggen. Det er din beslutning, fordi det er en promo du har bedt om.
- **🟡 Skal det frie flerstedes-tjek få en kundeklar rapport? Det er den betalte
  linje.** `/compliance-site-check` tager fem URL'er og `downloadReport()` giver
  **én** `.md` med alle fem sider, men pro-tabellen på samme side siger at Pro giver
  «a PDF report you can hand a client». En gratis kundeklar rapport tager en
  betalt vare, så jeg har ikke bygget den. Tre veje: (a) behold som nu; (b) giv én
  `.md` pr. side i ét klik, og flyt Pro-teksten til «hele sitet + de 18
  server-tjek»; (c) gør det til det Pro-produkt, det er. Din beslutning — den
  flytter en $79-årslinje.
- **🟡 `indexnow_ping.sh` kaldes aldrig.** Målt 2/10: `grep -rn indexnow
   .github/workflows/ build_sites.py` giver **0 træffere**. Bing og Google er de
  to eneste søgemaskinereferencer (2 + 2 besøgende). Jeg har ikke lagt den i CI,
  fordi et IndexNow-ping er et udadvendt kald — sig til det, så lægger jeg ét step
  efter en vellykket udgivelse.
- **🟡 `/blog/` siger «96 Danish guides», men 11 af dem ligger på
  cleancopy.tools.** `site/da/blog/` har 96 artikler, `dist/` kun 85 — de 11 er
  korsomviseret af buildet, som det er ment. Det nye sprog siger «Vores 96 danske
  guider», så de to sider ligner hinanden. Fortæl mig hvilket tal læseren skal se.
- **🟡 Skal værktøjssiderne vise livstidsprisen overhovedet?** De elleve pro-kort
  viser «$79/year per website» i en gratis-mod-Pro-tabel *inde i* kortet, så
  `check_stripe_ctas` («præcis 1 synlig lifetime-CTA pr. produkt») og `pro_card`
  («ét købsknap i ét pro-kort») siger nej til et prislink dér. Købsvejen findes på
  de seks produktsider. Enten beholder vi den som ren tekst, eller jeg flytter den
  til en fane under kortet.
- ~~**🔴 `site/_worker.js` er ikke hele workeren bag mahope.tools.**~~ **Fejlmålt
  4/10, lukket.** Noten byggede på at live `/api/compliance-scan` svarer med **9**
  tjek mens `CSC_CHECKS` «havde 7» — målt med et regex der kun greb u citationattegn,
  så de to nøgler med citation (`security-headers`, `meta-tags`) blev set borte.
  `CSC_CHECKS` har **9**, og live svarer præcis de samme ni i samme rækkefølge.
  `/api/profile`'s `max_score: 21` er ligeledes identisk med kilden. **Live-kilden
  er `site/_worker.js`**, og ingen afgave afklæring fra dig.
- **Search Console:** tilføj de fem domæner som properties (`mahope.tools`,
  `cleancopy.tools`, `deskuptime.com`, `bugbottle.dev`, `transmute.run`).
  Sitemap og robots er målt korrekte på de fire sites missionen udgiver.
- **Plugin-version:** kunder på Clean Copy 1.1.0 henter ikke den rettede zip.
  Kræver en version bump — og det er en release, som er din. `ceo/hub-readme-note`
  på origin er forældet (kun en plan-note fra 26/9) og ligger der, indtil du siger
  til.

## Feature-kø

Prioriteret efter hvor tæt den er på penge. Baseline er målt på den **byggede**
side; tallene er ikke vores egen trafik. Alt det der er leveret (1–11) står i
`docs/plan-arkiv.md`.

21. ~~**Kontrastværktøjet sagde hvad der fejlede, men ikke hvad man skulle gøre.**~~
    **LEVERET 6/10**, `ceo/kontrast-fix-farve`.** FAQ'en sagde allerede «skift
    til mørk tekst» — men læseren skulle selv finde farven. Nu vises den
    nærmeste tekstfarve der består AA (4,5:1) når parret fejler, med samme
    kulør og mætning, i ét klik og med kopi. WCAG-luminansen vokser monotont
    med HSL-lysheten for en fast kulør, så grænsen findes med binærsøgning og
    tjekkes bagefter med `ratio()`. Målt: 52 fejlende farvepar giver alle en
    farve med ratio ≥ 4,5:1 og bevaret kulør; mutation (funktionen fjernet) har
    ingen knap. Fuld gate **GRØN — 180 steps**; `catalog-where` krævede de to
    pro_features-linjenumre flyttet med indsættelsen.

20. ~~**Et hero-billede skulle først gemmes som fil for at kunne tjekkes.**~~
    **LEVERET 6/10**, `ceo/billede-drop-og-indsaet`.** Filvælgeren var den
    eneste vej ind i kontrastværktøjet, så den mest naturlige handling — at
    trække skærmbilledet ind på lærredet eller indsætte det med Ctrl+V/⌘V —
    gjorde ingenting. Nu kalder drop og indsæt præcis samme `loadFile()` som
    filvælgeren, så målingen er den samme uanset vejen ind; markeringen under et
    træk bruger husets egen accent. Datagrund: `/blog/text-on-image-contrast-check`
    er mahope.tools' største indgang (9 besøgende) og `/text-on-image-checker`
    den mest brugte værktøjsside. Dommen i `scan-clients` måler at et dropped
    billede bliver målt på alle fire sider (EN/DA værktøj + artikel) og er målt
    **rød på den gamle kode** (573/577 → 593/593). Fuld gate **GRØN — 180 steps**.

19. ~~**To åbne API'er svarer stadig 400 på det, deres egne sider skriver.**~~
    **LEVERET 6/10**, `ceo/et-url-regel-pa-alle-ruter`.** Ikke to ruter: seks.
    `/api/compliance-scan`, `/scan-proxy` og den betalte `/api/report` havde hver
    deres egen regel, så det var seks ruter på fladen og tre normaliseringer —
    målt **live** 6/10 før rettelsen. Nu én regel, `parseTargetUrl()`, som alle
    seks bruger, også den betalte (den lå bag nøgle, så den skulle ikke være
    strengere end den gratis). Rettelsen
    flyttede **ingen** adgangskontrol: `targetIsPublic()` kaldes stadig pr. rute
    og pr. redirect-hop, så en parse-hjælper kan ikke blive en ny SSRF-vej — de 7
    private værter er dømt på den bare form i porten, på begge nye ruter med hver
    sin tekst. Målt: 25 nye assertions, **22 røde på den gamle kode** (489/511) og
    **511/511** på den nye, inkl. negativ kontrol pr. rute (headere læst, titel
    læst) og dommen «alle fire ruter svarer 200 på den samme vært».
    `compliance-scan` med `HTTPS://` gik fra 502 til 200, fordi den gamle regel var
    `raw.startsWith('http')`. Fuld gate **GRØN — 179 steps**.

A. ~~**Den mest besøgte guide giver ingen vej til sit eget værktøj.**~~
   **LEVERET 6/10**, `ceo/contrast-guide-eget-vaerktoj`.** Datagrunden holdt
   kun halvt: værktøjet lå **allerede inde i artiklen**, så det der manglede
   var ikke indgangen. To huller lå i stedet.
   **(1) Resultatet var ikke målt.** Kernen skrev et tal, men **ingen sted**
   kaldte `trackEvent`, så `/api/results` viste præcis nul for værktøjet — vi
   kunne se at 9 mennesker læste artiklen og ikke se om *én* kørte et tjek. Nu
   `contrast-measured`, sendt fra kernen selv så alle fire sider dækkes, og kun
   når læseren har valgt **sin egen** baggrund: `demoBillede` er præcis den
   betingelse demo-noten forsvinder på, så kernens egen eksempelbillede tæller
   ikke — ellers ville hver sidevisning være et «gennemført tjek». Én gang pr.
   side, ikke pr. træk (`updateResult()` kaldes fra hvert `mousemove`).
   **`contrast-measured` står i `RESULT_EVENTS`**, så den tæller i
   `/api/results` pr. rute — og forskellen på artiklen og værktøjssiden er så
   netop det tal der kan afgøre hvad de to er værd. Baseline: **0**.
   **(2) Rettelsen kunne ikke bruges.** Artiklen siger at en slør er den
   hurtigste løsning, kernen regner den mindste dækning der virker, og «Fix
   it» lægger den på canvas — så bruteren stod med «42 % mørkt lag» og skulle
   selv regne `rgba(0,0,0,0.42)` ud. Nu får han den linje, i sit eget sprog og
   med en knap der kopierer den; ved et slør er der **to** linjer, fordi
   `applyFix()` sætter både farve og lag. CSS'en dannes af kernens *egne* tal
   (`fix.hex`, `fix.scrim`, `fix.alpha`) og læses tilbage af knappen *ud fra
   `<code>`*, så den der kopieres er den der står på skærmen. Målt: farven i
   linjen består det tjek den er skrevet til — sat i feltet og målt igen af
   kernen selv. Slør-grenen dømt mod `suggestFix([sort],[hvid],3)`, hvor det er
   den **hvide** slør der vinder med mindst dækning, så forventningen bygges
   af målingen og ikke af en hardkodet farve. Mutation: kernen fra før
   rettelsen sender 0 begivenheder og skriver 0 CSS-linjer. Fuld gate **GRØN**;
   `stripe-worker` **515/515** (den nye streng i resultatlisten er selv en
   port), `scan-clients` 565/565, `seo_check` 316 sider 0 fund,
   `check_inline_js` 0.

B. ~~**Vi kan ikke skelne «ingen besøgende» fra «tracking død».** Hvem: os, i
     hver morgenrapport. Tal: prioriteringen. Accept: ét kommando-kald skriver de
     to ærlige serier (kørsler fra `/api/results`, købsklik fra `/api/conversion`)
     for 28 dage og siger eksplicit **0 = ubekreftet**, med mindre de server-side
     tællere også står stille. Datagrund: målt 6/10 er begge serier **0** for 7
     dage, mens `served_scans_lifetime` er 51 — de to tal kan ikke begge være
     rigtige, og `/api/stats` (den der kan afgøre det) er 401.
     **LEVERET 6/10**, `ceo/tracking-status-check`.** Værktøjet
     `tools/check_tracking_status.py` sammenligner vinduesdata fra
     `/api/results` og `/api/conversion` med nylig besøgsdata fra `/api/health`.
     ~~**Dommen kunne ikke nås** (rettet 6/10 i `ceo/tracking-status-dom`):~~ den
     læste `recentVisits` på **topniveau** af `/api/health`, men feltet ligger
     under `stats` — så værdien var altid 0, «tracking død»-grenen var
     **uopnåelig**, og værktøjet skrev «No recent visits detected» i samme
     sætning som det citerede **20**. Målt 6/10 på live: `/api/health` har
     `recentVisits 20`, `recentDownloads 55`, `recentEvents 2` og
     `scans_lifetime 53`, mens begge lister er 0 for 28 dage — dvs. præcis den
     fejlmulighed dommen er skrevet til. Nu: **3/3 selftest** på de svar
     `/api` faktisk giver (besøgende+nul → død; ingen besøgende → ubekreftet;
     ét købsklik → virker), mutationen (gammel kode) kan hverken køre
     selftesten eller nå dommen, og seltesten er nu **step 91** i den
     dokumenterede gate (180 steps).
     **Hvad det betyder for resten af planen:** ~~alle baselines fra
     `/api/results` og `/api/conversion` — også `contrast-measured` — er
     ubekreftede~~ **FORÆLDET 6/10 20:00, se næste linje.**~~
     ~~**LEVERET 6/10 igen**, `ceo/sporing-dom-er-modstraaende`.** Den anden
     iteration på værktøjet fandt at dommen modsagde sig selv, og det blev målt
     mod live i sted for antaget. **Skrivevejen virker:** min egen
     `contrast-measured` på `/text-on-image-checker` lå i `/api/results` som
     `runs: 1` efter **33 s**, og `recentEvents` gik `2 → 6` da mine egne
     poster tæller med. Rodårsagen er at `/api/health` (`recentEvents`) og
     `/api/results` har **forskellige navnelister** på de **samme** nøgler:
     `/api/results` tæller kun `RESULT_EVENTS`, og `cta-*`/`store-click` er
     bevidst holdt ude, så «2 events» og «0 resultater» kan være sandt samme
     dag. Dommen læste derfor et tal som beviser sporingen virker som bevis for
     at den er død. Nu: `recentEvents > 0` → **«SPORING VIRKER — nul betyder
     ingen brugere fik et resultat»**, og «TRACKING DØD» kræver nu visits `> 0`
     **og** events `= 0`, som er den eneste tilstand hvor den er sand. Dommen
     citerer også den målte 33-s KV-lag, fordi et nul lagt lige efter en
     udrulning ellers læses som død sporing.
     **Dertil en fejl der gjorde porten tom:** `main()` returnerede `1` ved
     fejl, men `__main__` kaldte `main()` uden `sys.exit` — så
     `tracking-status-selftest` i gaten exitede **0** også når selftesten skrev
     FAIL. Porten har været grøn uanset hvad den så. Rettet til husets
     konvention (`sys.exit(main())`, som `check_storage_claims` og de andre
     bruger) og målt: mutationen giver **exit 1**.
     Selftest **3/3 → 4/4**, og den nye case er målt **rød på den gamle kode**
     på to måder: `if recent_events > 0` slået fra → FAIL med uventet
     «TRACKING DØD», og selftesten får et `forbidden`-sæt så et forkert svar
     tæller som fejl selv om den forventede sætning står i teksten. Fuld gate
     **GRØN**.
     **Hvad det betyder for resten af planen:** baselines fra `/api/results` og
     `/api/conversion` er **bekræftede** igen. Den ærlige værdi for
     `contrast-measured` er **0 rigtige kørsler** — de `runs: 3` der lå i
     `/api/results` da jeg målte var mine **egne** probe-poster, som jeg ikke
     tæller som efterspørgsel.


C. ~~**En Pro-holder der kommer fra scanneren skal finde PDF'en selv.**~~
   **LEVERET 6/10**, `ceo/pro-kort-til-pdf-fresh`.** Pro-kortets note på alle
   fire scanneresider linkede til `/compliance-report` uden mere, så en Pro-holder
   der lige har betalt $79 og set sit resultat landede i et **tomt** URL-felt,
   måtte køre scanningen igen og scrolle ned til nøglefeltet. Nu bærer den
   `#url=` med **den side der faktisk blev læst**: `compliance-site-check`
   tager `rapporter[0].url`, `scan`/`scan-da` tager `forsteUrl(state)` — der
   foretrækker `state.pages[0].url` (samme adresse målt i felterne, altså ikke
   `urls.join(', ')` som for flere sider ikke er nogen URL). `compliance-report`
   læser `#url=` i forvejen (`site/compliance-report.html:731`), så der er ingen
   ny mekanisme — kun et link der nu bruger den.
   **Vejen kan ikke sende læseren i et felt der ikke genkender adressen:**
   begge sider bruger præcis rapport-sidens egen regel `/^https?:\/\//i`, så en
   læser der skrev `example.com` — helt normalt, feltet siger «eller bare
   domænet» — falder tilbage på den gamle rute. Målt som dom, ikke som
   hensigt: `PDF_HANDOFF` kræver den kodede adresse i markup'en, og **mutationen**
   `var handoff = '/compliance-report'` gør den rød (**572/573**), så dommen
   kan ikke være grøn på en side hvor handoffen aldrig virkede. Dertil et målt
   tilfælde for hvert sprog: serveren svarer `url: 'example.com'` → `0` `#url=`
   og den gamle rute står. Fuld gate **GRØN**; `scan-clients` 565 → **573/573**,
   `stripe-worker` **515/515**, `seo_check` 316 sider 0 fund, `check_inline_js`
   664+1316 blokke 0 problemer.
   **Kendte huller denne opgave bevidst ikke lukker:** rapportværktøjet findes
   kun på engelsk, så den danske noten siger det og den dybe vej går til den
   engelske side; ved flere sider bærer den kun den **første** adresse, fordi
   rapporten tager én side ad gangen.
- **Arkiveret:** tak-sidens rettelse (`b772a466`), CEO-kø punkt 0 (`26440a1c`)
  og `status-finality-selftest`-mutationen fra 6/10 står i
  `docs/plan-arkiv.md`.

2. **`deskuptime.com`: 7 besøgende, 100 % bounce, 0 s opholdt tid.** Hvem:
    alle 7 på `/`. Tal: hvor mange køber. Accept: en forside der sælger uden
    at kræve scroll. Datagrund: **0 s** er ikke en lang læsning, det er en
    besøger der gik med det samme — på den eneste udgivne side der kun er én.
    Målt i Chromium 4/10 mod live: **0** JS-fejl, **0** fejlede requests,
    `scrollWidth == viewport` ved 390 og 1280, og den primære handling
    («Check a site now» → `#check`) ligger i folden ved begge bredder. Folden
    var altså ikke årsagen; 7 besøgende kan heller ikke dømme en forside.
     **LEVERET 7/10** — `ceo/deskuptime-forside-saelger`. **DEPLOY OK 7/10:**
     live `/da/` bærer `Køb DeskUptime Pro`-knap, gratis/Pro-tabel og de
     korrekte licens-fraser (målt med curl mod live).

17. ~~**En guide-artikel har ingen vej til prislisten.**~~ **LEVERET 7/10**,
      `ceo/pro-vej-i-guides`.** 17 artikler (8 EN + 9 DA) på cleancopy.tools har
      nu én linje med link til Clean Copy Pro's egen købssektion, lige før
      bog-CTA'en. **Baseline målt på det byggede site først:** af de 46
      blogartikler der nævner et katalogprodukt i **brødteksten** (nav, header og
      footer strippet) havde **43** allerede en købsvej — feature-kø'ens
      acceptkriterium var altså 43/46 opfyldt, ikke 0/17. De 17 valgte er dem
      der **nævner Clean Copy Pro uden nogen købsvej**. Rettelse af to fejl i
      den ucommitterede diff: inline `style="margin:24px 0 0;font-size:0.95rem;"`
      → `class="muted small mt-1"` (samme byggeklasse som de eksisterende
      linjer på præcis de sider), og den danske «tilføjer **to ting**» →
      «se hvad den **tilføjer** den gratis version», fordi tallet er en påstand
      i prosa der skal kunne verificeres mod katalogens `pro_features` — og en
      tredje Pro-funktion ville gøre den usand. Målt: alle 17 linjer ligger
      umiddelbart før den `book-cta` de allerede havde, `/#price` findes **1**
      gang på den byggede `cleancopy.tools/`, `/da/#priser` **1** på
      `cleancopy.tools/da/`, og **0** af dem blev omskrevet til et
      krydsdomæne-`href`. Fuld gate **GRØN — 177 steps**; `seo_check` 316
      sider 0 fund, `stripe-worker` 474/474, `check_inline_js` 1318 blokke 0
      problemer.
    **Kendte huller denne opgave bevidst ikke lukker:** `mahope.tools/blog/
    copy-table-website-to-{airtable,google-sheets}` og `blog/eaa-enforcement-2026`
    nævner produktet kun i en **JSON-LD-FAQ** og en kort om licensetrafikken —
    de sælger intet, så en købslinje dér ville være kulisse.

18. ~~**DeskUptime har otte ruter ingen læser nogensinde ser.**~~ **LEVERET
    6/10**, `ceo/tools-side-med-de-tre-tjek`.** Datagrund holdt kun delvist: der
    er **to** værktøjsruter på domænet, ikke otte — de øvrige auditedwp-sider
    udgives ikke. De **havde nul indgang**: navets «Tools»/«Værktøjer» pegede på
    `../auditedwp`s egen forside, som linkede **0** af de to, havde egen canonical
    ved siden af forsiden og kaldte den betalte app «free». Ruten er nu
    `site/deskuptime/tools/index.html` med de tre tjek, gratis/Pro-tabellen fra
    katalogen og **én** købsknap, så `one_buy_button`-efterbehandlingen er væk
    (den var en post-processor, fordi kilden lå i et sibling-repo).
    Ny port `tools/check_tool_hub.py` finder hub-ruten i nav-konfigurationen og
    kræver at den linker hvert publiceret værktøj **i sit eget sprog**; målt
    mutation (linket omdøbt) → **RØD** med navnet på den manglende rute. Den
    fandt straks en **ægte** mangel: `/accessibility-statement-generator` lå
    publiceret uden nogen indgang fra `/free-tools` — rettet med et kort i samme
    stil som naboerne. Selftest **20/20**. Rettelsen af `_page_file` i
    `check_article_paid_path` (den gættede stien og så `deskuptime.com`s `remap`
    forude) lå i samme diff. Fuld gate **GRØN — 179 steps**.
9. ~~**`/scan` tager kun 1 URL.**~~ **Leveret 5/10** — se arkivet.

10. ~~**`/scan` mangler et eksempel-resultat at dele.**~~ **LUKKET 6/10.** Leveret
    som et *målt* eksempel-kort under folden (`afbe1a37`), ikke et fasttal der
    går stale. Målt afvigelse: tallene kommer fra `tools/scan_example.py`, der
    kører sidens egne scripts i headless Chromium mod en lokal stub.

12. ~~**Forsiden nævner 2 af 13 produkter og 0 links til prislisten.**~~
    **Leveret 6/10.** Salgsafsnittet linker nu til `/pricing` i begge sprog.
    Målt 6/10: afsnittet navngiver **4** af 13 (`clean-copy-pro`,
    `deskuptime-pro`, `eucomply-pro`, `page-profile-pro`) — de to tal i den
    oprindelige optælling var solgte varelinjer, ikke produkter.

13. ~~**Hver produktside kun én købsknap — de 13 har 73 dokumenterede købssider.**
    **Leveret 6/10**, `ceo/one-buy-button-tools`.** Målt på det **byggede** site
    med portens egen `built_buy_links`: **62** sider har en synlig købsknap, og
    **16** af dem har to — men **15** af de 16 er abonnement + lifetime, altså
    to *forskelige* betalingslinks til samme produkt, hvilket er tillladt og
    erklæret med `lifetime: true`. Den **ene** ægte dublet var
    `deskuptime.com/tools/`: to knapper med *samme* link. Kilden er
    `../auditedwp` og må ikke ændres, så `build_sites.py` reducerer den under
    bygget (`one_buy_button`) — helten knappen bevares, den lavere forsvinder
    sammen med den tomme `<p>`, og «Payment through Stripe» bliver stående.
    `built_offers` erklærer nu `ctas: 1`, så porten dømmer det. Målt begge
    veje: manifest-reglen fjernet → 2 knapper og **1 fund** («har 2 synlige
    CTA'er for deskuptime-pro, forventet præcis 1»); reglen på → 1 knap,
    **0 fund**. Knap-funktionen er målt på 6 tilfælde, bl.a. at en knap med
    søskende i sin `<p>` kun mister ankeret, og at **én** eller **nul** knapper
    kaster — så en kildendring ikke kan slå reglen fra ved at tie.

14. ~~**Ingen produktside siger hvad Pro *ikke* gør.**~~ **Leveret 6/10** —
    se opgave 33.

15. ~~**`/pricing` er den ene side med alle 13 produkter, og den køber intet.**~~
      **LEVERET 6/10**, `ceo/pricing-stripe-ankere`.** Hver række i «Where to
      buy» har nu et `#anker` på **den vares egen købsknap**. Målt 6/10 før
      rettelsen: de 12 `pc-buy` gik alle til **hele købssider**, og **6** af
      dem til `/paid-templates`, der sælger syv varer i et gitter — så en
      læser der lige har valgt «Buy GDPR DPA template» landede i gitteret og
      skulle selv finde knappen. Nu: de 7 dokumenter har hvert sit kort-id
      (`id="eucomply-dpa"` …, begge sprog), `clean-copy-pro` →
      `cleancopy.tools/#price`, `deskuptime-pro` → `deskuptime.com/#pro`,
      `eucomply-pro` → `#buy`, `page-profile-pro` → `#pp-buy-live`. Ny **dom 7**
      i `check_pricing_page` dømmer at hvert anker findes som et `id` i den
      **byggede** side, også krydsdomænerne (`DOMÆNE_DIST` er påkrævet, så et
      nyt tværdomæne ikke kan tie). Dom 7 er målt rød på den gamle kode på to
      måder: `id` fjernet fra ét kort → **1 fund** med navn og fil;
      `id="price"` → `id="priser"` i cleancopy.tools' eget byggede site → **1
      fund** på `clean-copy-pro`. Selftest **10/10 → 16/16**. Dom 7 fandt
      desuden **min egen fejl**: den danske prisliste sendte til
      `#pricingSection`, som kun findes på den engelske side (den danske hedder
      `#pris`) — løst med et sprognøytrest `#buy` på begge, så *én*
      `pricing_link` kan betjene begge sprog. Fuld gate **GRØN — 177 steps**.
      `pricing_page`-steppene har nu de ni destinationssider som inputs, så en
      commit der sletter et `id` ikke springer porten over. *Ingen ny CTA:*
      dom 3 (siden sælger ikke direkte) er urørt, og der er stadig præcis én
      købsknap pr. side.

16. ~~**Den danske prisliste sender læseren til engelske købssider.**~~
      **LEVERET 6/10**, `ceo/den-prisliste-koer-pa-engelsk`.** Målt 6/10 i det
      byggede site: `/da/pricing` havde **2** rækker med
      `https://cleancopy.tools/#price` og **1** med
      `https://deskuptime.com/#pro` — altså tre af tolv rækker der sendte en
      dansk læser ud i engelsk. Datagrund: `/da/ruten` er afledt af den
      engelske rute, så **kun et krydsdomæne** kan glemme sproget; de otte
      mahope.tools-rækker var aldrig i fare. Rettelse: katalogens
      `pricing_link` kan være `{"en": …, "da": …}`, brugt for de to varer der
      sælges på et andet domæne. Nu: 2 `https://cleancopy.tools/da/#priser` og 1
      `https://deskuptime.com/da/#pro` — begge ankre målt på de **live** danske
      sider, som har eget `<html lang="da">`. Ny **dom 8** dømmer det på den
      byggede sides `lang` (ikke på rutens navn), og **tier** når filen mangler
      eller ankeret er væk, så den duplikerer hverken dom 2 eller dom 7.
      Selftest **16/16 → 20/20**: de to nye røde tilfælde er målte røde med dom 8
      afkoblet (18/20), og en *relativ* rute kan bevidst ikke slå dommen ihjel
      (`købs_rute` sætter `/da` selv) — så mutationen for den lokale fejl er en
      håndskrevet absolut `https://mahope.tools/…`. Fuld gate **GRØN — 177
      steps**; `stripe-worker` 474/474, `seo_check` 316 sider 0 fund,
      `check_inline_js` 1318 blokke 0 problemer.
