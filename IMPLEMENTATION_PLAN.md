# STATUS
- **Den indgang tre domæner sælger på, døde på det den lovede.** 6/10 målt på
  live `deskuptime.com`: `GET /api/url-inspect?url=example.com` svarer **400
  «Invalid URL»**. Formularen på deskuptime.com, mahope.tools og /da siger
  bogstaveligt «we add `https://` if you leave it out», men normaliseringen lå
  kun i `one-off-check.js` — så løftet holdt kun når JS indlæste, mens formen er
  `method="get"` og skal virke uden. Ruten er åben for enhver klient (CORS `*`),
  og `/api/compliance-site-check` gjorde allerede det samme med to linjer, så tre
  ruter på samme flade svarede på samme URL på tre måder. Nu normaliserer
  workeren (trim + `//`), protokol-checken er der stadig, kæden starter på den
  parsede adresse, og `inspectUrl` er den vi faktisk undersøgte.
- **Målt først:** 9 forskellige input gennem workeren (ren, `//`, `EXAMPLE.COM`,
  `example.com:8080` → 200 med samme `finalUrl`; `ftp:`, `javascript:`, `not a
  url` → 400). 12 nye assertions, målt røde på den gamle kode (**475/486**) og
  grønne på den nye (**486/486**). Fire mutationer hver for sig røde:
  normaliseringen væk → 11 fund, protokol-checken væk → 1, kæden på rå-strengen
  → 3, `inspectUrl` på rå-strengen → 1. SSRF-listen er **genbrugt** (ingen ny
  kode), så de 7 private værter dømmes også i den blotte form — de var fejl i
  *gamle* rækkefølge, fordi `127.0.0.1:8787` blev afvist som ugyldig URL
  *før* `targetIsPublic` nåede at dømme det. Fuld gate **GRØN — 179 steps**;
  `stripe-worker` 486/486, `seo_check` 316 sider 0 fund, `check_inline_js` 0.
- **CI:** seneste kørsel på `main` er **success**. `PR-TJEK 6/10`: **0** åbne
  PR'er. `BRANCH-TJEK` ikke kørt (uge-tjek).
- **Næste:** de åbne ❓. `/api/header-check` og `/api/profile` har samme
  skæve (ren vært → 400 målt live 6/10), men ingen af deres sider lover at skemaet
  sættes på, så de er ikke brud på et løfte. Se feature-kø 19.



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
ceo/bare-vært-tjekkes 6/10 03:5x`

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

19. **To åbne API'er svarer stadig 400 på det, deres egne sider skriver.** Hvem:
    enhver der kalder `mahope.tools/api/header-check` eller `/api/profile` — 6/10
    målt **live** til 400 «Invalid URL — must start with http:// or https://» på
    `url=example.com`. Tal: ikke køb direkte, men troværdighed på den åbne
    flade, `developers.html` dokumenterer begge med curl-linjer. Accept: samme
    normalisering som i `/api/url-inspect` på alle tre ruter, så ét kald på
    `example.com` giver ét svar. Datagrund: de to sider der bruger dem
    normaliserer i JS, så bruden er usynlig i browseren — præcis derfor er
    ingen opdaget den. **Ingen løftetekst på de to sider, så det er ikke et
    brud på et løfte**; det er inkonsistensen på API-fladen. Ikke gjort i samme
    iteration som rettelsen ovenfor: to ruter i én diff er to fejl at rulle til
bage, og `/api/url-inspect` var den der lå på tre domæners forside.
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
