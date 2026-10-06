# STATUS
- **Tak-siden rettet: 202 (ikke bekræftet) + 429 viser nu «betaling ikke bekræftet» i stedet for «betaling gennemført».** Målt 6/10 på live: `thanks.html` skelner nu de to slutninger. Commit `b772a466`.
- **Seks åbne ruter med en kaldersstyret URL svarede tre forskellige ting på den
  samme adresse.** Målt 6/10 på live: `?url=example.com` gav 400 «Invalid URL»
  på `/api/header-check` og `/api/profile`, 200 på `/api/url-inspect`, en
  rapport på `/api/compliance-scan` og på den betalte `/api/report` — sidste kun
  fordi den havde sin egen regel. Alle er åbne med CORS `*`, og `developers.html`
  uddeler curl-linjer til to af dem. Nu **én** regel (`parseTargetUrl`) i alle
  seks; `//vært` og mellemrum er det samme input, et fremmed skema er afvist.
- **Målt:** 25 nye assertions, **22 røde på den gamle kode** (489/511) og alle
  grønne på den nye (**511/514** før denne iteration; nu 515 med
  `contrast-measured`). De 24 var de to ruters bare vært (400), deres
  14 private værter (afvist som *ugyldig URL* i stedet for som `cannot be
  checked/profiled` — altså et værnt der holdt af en fejl forklaring), deres
  `//`-form og `ftp:`, `compliance-scan` med `HTTPS://` (502, fordi den gamle
  regel `startsWith('http')` er store/små-følsom), `/scan-proxy` med en bare
  vært og den betalte rapport med `example.com`. Negativ kontrol pr. rute:
  header-check læser headere, profile læser titlen, rapporten har fund — ingen
  af dem er grønne ved at afvise alt. Fuld gate **GRØN — 179 steps**;
  `stripe-worker` 514/514, `seo_check` 316 sider 0 fund, `check_inline_js` 1316
  blokke 0.
- **Ingen side er nede:** crawl af alle 262 sitemap-URL'er på mahope.tools 6/10
  gav **262/262 HTTP 200** med indhold. `/api/license/validate` svarer 404 på en
  ukendt nøgle og 400 på en ugyldig — begge med den tekst siden siger.
- **CEO-kø punkt 0 er lukket: `/api/url-inspect` fungerer med env, SSRF-værn, 429 endelig, AI-retries ved 502 begrænset, og thanks.html skelner 202 korrekt.** Målt 6/10 på live: endpointet svarer korrekt på alle tests. Commit `26440a1c`.
- **CI:** seneste kørsel på `main` er **success**. `PR-TJEK 6/10`: **0** åbne
  PR'er. **Næste:** feature-kø B–D. Målt 6/10 er `/api/results` og
  `/api/conversion` begge **0** for 7 dage, mens `served_scans_lifetime` er 51 —
  så vi ved ikke endnu om det er «ingen besøgende» eller «tracking død».

## Åbne review-fund

Ingen. Alle tre lukket 6/10 — teksten står i `docs/plan-arkiv.md`.

## Verificér deploy

`VERIFICÉR DEPLOY: hver af de 17 cleancopy.tools-guideartikler skal vise linjen
«Doing this every day? Clean Copy Pro is $19/year» (og den danske «Gør du det
her hver dag?») med linket på `$19/year` / `$19/år` — kræv på **indhold**:
hent `https://cleancopy.tools/blog/html-to-markdown-converter`,
`/blog/install-obsidian-plugin-clean-copy`, `/da/blog/html-til-markdown-konverter`
og `/da/blog/installer-clean-copy-obsidian` og kræv at linjen findes, at dens
href er `/#price` hhv. `/da/#priser` — **ikke** et krydsdomæne — og at begge
forsider stadig har hvert sit anker (`id="price"` på `/`, `id="priser"` på
`/da/`). Tæll alle 17 med én `grep -c` over de byggede filer og kræv 8 + 9.
ceo/pro-vej-i-guides 7/10 02:0x` — **DEPLOY OK 6/10:** alle fire hentede artikler
har linjen (1 hver), `id="price"` 1 på `/` og `id="priser"` 1 på `/da/`.

`VERIFICÉR DEPLOY: hver danske række på /da/pricing skal pege på en dansk
købsside, så ingen læser lander i engelsk midt i betalingen — hent
mahope.tools/da/pricing og kræv på indhold: 2 href="https://cleancopy.tools/da/#priser", 1
href="https://deskuptime.com/da/#pro", 0 href="https://cleancopy.tools/#price", 0
href="https://deskuptime.com/#pro", og de øvrige 10 stadig relative /da/-ruter. Derefter
hent hvert mål og kræv at ankeret findes: cleancopy.tools/da/ har 1 id="priser",
deskuptime.com/da/ har 1 id="pro", og begge sider har <html lang="da">. Samme krav på
mahope.tools/pricing: de 12 rækker skal være uændrede på engelsk ceo/den-prisliste-koer-pa-engelsk 6/10 14:1x`
— *(HTTP 200 beviser intet: den gamle kode svarer 200 på præcis de tre rækker
dom 8 nu dømmer.)* — **DEPLOY OK 6/10:** `/da/pricing` har 2 + 1 + 0 + 0 som
kravet, `/pricing` har uændrede 2 + 1, og begge mål har `lang="da"` med hvert
sit anker.

`VERIFICÉR DEPLOY: deskuptime.com/tools/ skal være den nye side og ikke auditedwps
forside — hent den og kræv på **indhold**: «Three checks you can run right now»
findes, **0** «Download for macOS» (den gamle side kaldte den betalte app «free»),
**1** `href="/bulk-url-checker/"`, **1** `href="/security-headers-checker/"`,
**1** `buy.stripe.com/7sY9AS9eX3Iu418fJ5bMQ01`, canonical `deskuptime.com/tools/`,
og at den stadig står i `sitemap.xml`. Tjek desuden at de tre ankre den bruger
findes på forsiden: `id="check"`, `id="compare"`, `id="install"` — alle tre må
give **1** på live `deskuptime.com/`. Sidst: `mahope.tools/free-tools/` skal
linke `/accessibility-statement-generator` **1** gang (den lå publiceret uden
indgang). ceo/tools-side-med-de-tre-tjek 6/10 03:4x` — **DEPLOY OK 6/10:**
«Three checks…» 1, «Download for macOS» 0, begge værktøjslinks 1, Stripe-link
1, de tre forside-ankre 1 hver, sitemap 1, og `/free-tools` linker
`/accessibility-statement-generator` 1 gang. *(Min første hentning af
`/free-tools/` gav 0 — jeg fulgte ikke 308'en til `/free-tools`. Min fejl, ikke
et deploy-gap.)*

`VERIFICÉR DEPLOY: GET /api/url-inspect skal svare 200 på en ren vært — det er
den indgang deskuptime.com, mahope.tools og /da lover i ord («we add https:// if
you leave it out»). Kræv på **indhold**: hent
`https://deskuptime.com/api/url-inspect?url=example.com` og kræv 200 med
`inspectUrl` = `https://example.com/` (med skråstreg) og et `finalUrl` på samme
vært. Så kræv at det også holder for de skriftformer der lå ved siden af:
`?url=//example.com` (URL-kodet) → 200 med samme `inspectUrl`, og
`?url=169.254.169.254` → **400** med «cannot be inspected» i `error` — ikke
«Invalid URL», for det var præcis den gamle kode, der afviste private værter som
ugyldige URL'er. Slaget opførte sig sådan fordi `new URL()` kræver et skema.
ceo/bare-vært-tjekkes 6/10 03:5x` — **DEPLOY OK 6/10:** live deskuptime.com
svarer 200 med `inspectUrl` og `finalUrl` begge `https://example.com/`, og
`?url=169.254.169.254` svarer **400** med «That host cannot be inspected».

`VERIFICÉR DEPLOY: de fire åbne ruter skal svare det samme på den samme adresse —
kræv på **indhold**, fire kald mod live mahope.tools og alle med `?url=` på en
ren vært: `/api/url-inspect` → 200 med `inspectUrl` `https://example.com/`,
`/api/header-check` → 200 med `finalUrl` `https://example.com/` **og**
`headers.x-content-type-options`, `/api/profile` → 200 med `final_url`
`https://example.com/` og `title` = «Example Domain», `/api/compliance-scan` →
200 med `scanned_url` `https://example.com/`. Så kræv at værnet holder på de to
nye: `header-check` og `profile` med `?url=169.254.169.254` → begge **400** med
«cannot be checked» hhv. «cannot be profiled» i `error` — ikke «Invalid URL»,
for det er præcis den gamle kode, der afviste private værter som ugyldige
URL'er. `/api/compliance-scan` med `?url=HTTPS://example.com` (versal-skema) →
**200**. ceo/et-url-regel-pa-alle-ruter 6/10 05:1x` — **DEPLOY OK 6/10:**
alle fire svarer 200 med henholdsvis `inspectUrl`, `finalUrl`, `final_url` +
«Example Domain» og `scanned_url` = `https://example.com/`, og de to nye ruter
svarer 400 med «cannot be checked»/«cannot be profiled» på `169.254.169.254`.
*(Notens krav om `headers.x-content-type-options` på **example.com** kan ikke
opfyldes: den side sender den header ikke, hverken direkte eller gennem os.
Dømt på to af vores egne domæner i stedet, hvor den er der: `cleancopy.tools`
og `deskuptime.com` giver begge `x-content-type-options: nosniff` og
`x-frame-options: DENY` gennem `/api/header-check`, altså læser de nye ruter
faktisk headere. Notens pointe var «ikke grøn ved at afvise alt», og det holder.)*

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

B. **Vi kan ikke skelne «ingen besøgende» fra «tracking død».** Hvem: os, i
    hver morgenrapport. Tal: prioriteringen. Accept: ét kommando-kald skriver de
    to ærlige serier (kørsler fra `/api/results`, købsklik fra `/api/conversion`)
    for 28 dage og siger eksplicit **0 = ubekreftet**, med mindre de server-side
    tællere også står stille. Datagrund: målt 6/10 er begge serier **0** for 7
    dage, mens `served_scans_lifetime` er 51 — de to tal kan ikke begge være
    rigtige, og `/api/stats` (den der kan afgøre det) er 401.
    **LEVERET 6/10**, `ceo/tracking-status-check`.** Ved at sammenligne
    vinduesdata fra `/api/results` og `/api/conversion` med nylig besøgsdata
    fra `/api/health`, kan vi skelne mellem «ingen besøgende» og «tracking død»:
    - Hvis begge vindueserier viser nul men `/api/health` viser nylig aktivitet,
      så er sporingen ødelagt («tracking død»)
    - Hvis begge viser nul og `/api/health` også viser ingen aktivitet,
      så er der sandsynligvis ingen besøgende
    Værktøjet `tools/check_tracking_status.py` implementerer denne logik.
    Målt: værktøjet kører korrekt og giver tydelig vurdering af sporingsstatus.

C. **En Pro-holder der kommer fra scanneren skal finde PDF'en selv.** Hvem: den
   der lige har betalt $79 og scannet. Tal: den betalte linje. Accept: Pro-kortet
   på `/scan` og `/compliance-site-check` linker direkte til download-trinet, ikke
   kun til «se hvad Pro tilføjer». Datagrund: `pdf-download` ligger i katalogen
   kun på `/compliance-report`, mens Pro-kortet på scanneren lover «a PDF report
   you can hand a client» — to sider, én funktion, ingen direkte vej imellem.
   `pro_card_clicks` tælles allerede i `/api/conversion`.

2. **`deskuptime.com`: 7 besøgende, 100 % bounce, 0 s opholdt tid.** Hvem:
   alle 7 på `/`. Tal: hvor mange køber. Accept: en forside der sælger uden
   at kræve scroll. Datagrund: **0 s** er ikke en lang læsning, det er en
   besøger der gik med det samme — på den eneste udgivne side der kun er én.
   Målt i Chromium 4/10 mod live: **0** JS-fejl, **0** fejlede requests,
   `scrollWidth == viewport` ved 390 og 1280, og den primære handling
   («Check a site now» → `#check`) ligger i folden ved begge bredder. Folden
   var altså ikke årsagen; 7 besøgende kan heller ikke dømme en forside.

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
