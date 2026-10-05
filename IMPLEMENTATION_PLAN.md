# STATUS
- **«It crawls the whole site» lå i 16 pro-kort på 9 sider + 11 prosa-steder,
  6/10.** Den rute en licens låser op (`/api/report`) kalder `cscFetch`
  **præcis én gang** — målt på koden. Rettet på alle ni sider, og hver fik sin
  **egen** ærlige sætning, fordi de frie værktøjer ikke er ens: `/scan`,
  `contrast-checker` og `text-on-image-checker` læser slet ingen side i
  browseren (0 kald efterfulgt af `rg -c 'scan-proxy|api/header-check'`), så
  Pro læser den fra serveren; `cookie-check` læser kilden (`/scan-proxy` giver
  html uden headers), så Pro læser **også** svarheaderne; `security-headers-check`
  læser kun headerne, så Pro læser kilden; `compliance-site-check` følger de
  juridiske links, så Pro gør **ikke** flere sider — den læser dybere.
- **`check_scan_page_claims` så kun 2 af de 16 kort, 6/10.** Dom 4 læste
  `proCard()` på `/scan` og `/scan-da`. De anden syv lå i
  `tools/stripe_catalog.json`, som er sandheden for alle 21 pro-blokke. Ny
  **dom 5** læser katalogen for `eucomply-pro`, låst til samme måling
  (`kald == 1`), så en ægte flersidet `handleReport` slår den fra. Selftest
  **12/12**.
- **`tests/scan-clients.test.mjs` krævede den løgnest, 6/10.** Dom 4 i testen
  ville have «crawls the whole site — the same check on every page it finds»
  stå i kortet — altså holdt testen løgnen i live. Dømmer nu intet krybende
  verb **i pro-kortet** plus den positive sætning om serverlæsningen.
  Målt begge veje: **532/534** med løgnest genindsat, **534/534** med teksten.
- **Seks `VERIFICÉR DEPLOY`-noter er verificeret og lukket, 6/10** (se nedenfor).
- **Næste:** feature-kø 10 — `/scan` mangler et eksempel-resultat at dele uden
  en kørsel. Deploy-noten for `ceo/js-rest-gate` skal måles på indhold.

## Verificér deploy

`VERIFICÉR DEPLOY: gaten dømmer `;;` og rettet `/da/free-tools` 6/10 06:0x
ceo/js-rest-gate` — måles på **indhold**: live `mahope.tools/da/free-tools` skal
være fri for `?$/);;if(!m)return;` og have `?$/);if(!m)return;` (klik-
målingen skal stadig virke: et klik på `/da/paid-templates` skal sende et
`/api/track`-kald). HTTP 200 beviser intet for denne note.

`VERIFICÉR DEPLOY: pro-kortene fortæller hvad /api/report gør 6/10 03:5x
ceo/pro-kort-uden-krybning` — måles på **indhold**, ikke bare 200. Live
`https://mahope.tools/compliance-site-check`, `/da/compliance-site-check`,
`/cookie-check`, `/cookie-check-da`, `/contrast-checker`, `/contrast-checker-da`,
`/security-headers-check`, `/text-on-image-checker` og
`/text-on-image-checker-da` skal **alle** være fri for `crawls the whole site` og
`gennemgår hele sitet`, og hver skal have sin egen sætning: «reads the page you
name from the server» på compliance-site-check begge sprog, «reads the response
headers as well — HSTS and CSP» på cookie-check begge sprog, «reads the page
from the server too» på contrast- og text-on-image begge sprog, «reads the page
source as well … which no response header shows» på security-headers-check. Live
`/books`, de fire bogsider, `/compliance-ai` og `/da/compliance-ai` skal være fri
for «crawls the site» / «crawls it». Live `/scan` og `/scan-da` skal stadig have
den **ægte** desktop-påstand «whole-site crawl up to 200 pages» / «crawl hele
sitet op til 200 sider» — den er et andet program med sin egen krybning.

`DEPLOY OK 4/10 23:3x` for `ceo/scan-form-i-folden` — målt på indhold med to `curl`:
live `/scan` har `<form id="scanForm" class="scanbox">` **inde i**
`<header class="hero">` (9956–11032, altså **1** form og **0** i `<main>`),
knappen er `<button type="submit" class="btn-primary">`, siden har **0**
`background` i `.scanbox button`, `#result` er **1** gang og **uden for** heroen,
og alle **3** skrivninger kalder `revealResult(out);`.

`DEPLOY OK 4/10 23:3x` for `ceo/verdict-i-folden` — målt på indhold: live
`/text-on-image-checker` har præcis **1** `id="verdict"` **før** `ti-canvas-wrap`
og før `#result`, og dens statiske tekst er «Measured on the example image.»
`.hero p.tagline` er under 120 tegn. *(Tallet «PASS 4,07:1» er JS-beregnet og kan
ikke læses med curl — det var et forkert kriterium i noten.)*

`DEPLOY OK 4/10 23:3x` for `ceo/resultat-koerende-taeller` og
`ceo/tokenfri-konvertering` — målt på indhold: live `/api/results?days=7` har
`served_scans_lifetime`, `note` med «NOT a count for this window» og
`totals {runs: 0, visitor_days: 0}`; live `/api/conversion?days=7` svarer
`status ok` med `totals {buy_clicks: 1, visitor_days: 1, pro_card_clicks: 0}`.
HTTP 200 blev ikke brugt som bevis.

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

25. ~~**Punkt 13 i ren kultur dømmer kun `$1`, ikke `;;`.**~~ **LUKKET 6/10.**
    Hvorfor: fundet 6/10 var et dobbelt `;;` i `site/_worker.js:119`, rester fra
    en scriptet indsættelse — og `;;` er *gyldig* JavaScript (en tom sætning),
    så hverken `node --check`, tsc, bygget eller `check_inline_js` kan se den.
    Ny port `tools/check_js_residue.py` dømmer hele JS-overfladen (`.js` +
    inline `<script>`, `site/` **og** `dist/`) for `;;` og for linjer der kun er
    `;`, med `for(;;)` undtaget. Den **maskerer strenge og kommentarer først**,
    fordi `site/clean-copy-bookmarklet.js` er én minificeret `javascript:`-streng
    med `});;var` som data — uden masking var porten rød på første kørsel.
    To steps i gaten (`js-residue`, `js-residue-selftest`), **175 steps grønne**.
    Første kørsel fandt én rigtig rester i `site/da/free-tools.html:353`
    (`?$/);;if(!m)return;`), rettet i samme commit. Selftest **0 fejl**, og den
    er målt rød på den gamle kode: med `_worker.js` plus mutationen er den
    **4 fund** mod **0** på den uændrede fil. Maskeringen er testet mod de to
    fejl den selv havde: en `/* … */` der lukker på samme linje slugt resten af
    workeren som kommentar, og en template-literal med `${ … }` indeni som lod
    maskeren tro den yderste streng stod åben ved EOF.


26. ~~**`/scan-proxy` kan svare 500 på `?url=https://`.**~~ **LUKKET 6/10.**
    Hvorfor: dedup'en i `handleScanProxy` droppede stille enhver linje hvis
    `cscNormalizeUrl` gav tom streng (`https://`, `http://`, `///`, `//` …), så
    `sider` blev tom og `sider[0].error` var en `TypeError` på en åben rute.
    Accept: `?url=https://` svarer **400** med hele linjen; to linjer hvor den
    ene er ugyldig svarer 400 med *den* linje; en test der kalder handleren
    direkte. **Målt:** 5 tegnsfejl (`https://`, `http://`, `///`, `//`,
    `https:///`) svarer alle 400 med hele linjen i `error`; en tegnsfejl ved
    siden af en gyldig side er 400 med *den* linje; to skrivelser af samme side
    er stadig én side; ingen fejl er tom eller `undefined`. `stripe-worker`
    **474/474** mod **462/474** (12 fejl, alle med `-> 500 {}`) på den gamle kode.
    Rettelsen: tom nøgle identificeres på sin egen rå tekst i stedet for at
    være en adgangsbetingelse, og `sider[0]?.error` kan ikke kaste mere.
27. ~~**Punkt 3 på «Scan now»:** knappen har ingen lås, og et dobbeltklik
    brænder **ti** kvoteslots~~ **LUKKET 6/10.** `scan()` blev en lås omkring
    `scanKør()`: et kald i luft får **samme** løfte tilbage, og knappen er
    `disabled` med teksten «Scanning…» / «Scanner …» mens den venter. Målt i
    `tests/scan-clients.test.mjs`: et dobbeltklik på submit giver **1** kald mod
    **2** på mutationen hvor låsen er fjernet — og den mutationen læser den
    rigtige fil, ikke en kopi. Knappen findes gennem `#scanForm`, fordi
    `scan-share`'s sandkasse kun har `querySelector: () => null` på *dokumentet*
    (den faldt rød på første kørsel).
28. ~~**«Fem er samme tal som `/api/compliance-scan` tager» er usandt.**~~
    **LUKKET 6/10.** Den tager `CSC_MAX_PAGES = 12` pr. kald. Kommentaren
    peger nu på begge tal, og pro-kortet på `/scan` + `/scan-da` siger sandheden
    om den rute licensen låser. Målt: `check_scan_page_claims` **6 fund** på
    `63b65842` (hele vejen fra kommentar til pro-kort) mod **GRØN** nu, og
    `--self-test` **9/9**. Se opgave 29 for den større del.
29. ~~**«It crawls the whole site» står i 16 pro-kort på 8 sider, og er usandt.**~~
     **LUKKET 6/10.** Målt: `handleReport` kalder `cscFetch` **én** gang, så
     den læser én side og ser dens svarheadere. Alle **16** kort + **11**
     prosa-steder på **9** sider rettet, hver med sin egen ærlige sætning —
     målt pr. side hvilken kilde det frie værktøj læser. Ny **dom 5** i
     `check_scan_page_claims` dømmer katalogen for `eucomply-pro`, låst til
     målingen `kald == 1`; selftest **12/12** (mutation 10/11 genindsætter
     løgnest på sider dom 4 aldrig så, mutation 12 beviser at porten **tie**,
     når `handleReport` faktisk henter to sider). `scan-clients.test.mjs`
     krævede den løgnest — nu **534/534**, målt rød (**532/534**) med løgnest
     genindsat. `pro_table.py --apply` kørt på 9 sider, `check_pro_table` +
     `check_catalog_where` grønne, katalogens 27 `where`-citater peger på den
     nye tekst. Fuld gate: **GRØN — 173 steps**. *Bemærk: `url-inspector`s
     «across a whole site» gælder Page Profile Pro, en anden rute i et privat
     repo, så den er ikke dømt her.*
30. ~~**Porten kunne tvinge en sand side til at lyve.**~~ **LUKKET 6/10.**
    Review-fund 29/9 (MIDDEL). `tools/check_storage_claims.py` læste *næste
    funktions signatur* som et kald, så 7 af 12 «hentende» ruter aldrig
    hentede noget. Hvorfor det betød noget: `check_fetch_claim` ville have dømt
    `clean-copy-api.html` for en **sand** afvisning. Rettelse: kroppen slutter
    nu ved næste `start()` og begynder ved sin egen `{`, og `RE_FUNCTION`
    tager `async` som valgfrit så `function guard(` bliver en grænse — ellers
    faldt hele rutedispatchen i `handleClientError`s krop. Accept:
    `fetching_routes()` giver **5** ruter (`/scan-proxy`,
    `/api/header-check`, `/api/profile`, `/api/url-inspect`,
    `/api/compliance-scan`), stabilt for `dybde` 1/2/3/5/10, og selvtestens
    **5d/5e** er røde på den gamle kode (**58** fejl hhv. **1** fund) mod **0**
    på den nye. `storing_routes` er uændret på **9**, porten **GRØN** med 0
    fund, `--self-test` **0 fejl**. Fuld gate: **GRØN — 173 steps**. *Ingen
    deploy-note:* kun `tools/` er rørt, ingen fil i `site/` eller `dist/`, så
    intet på sitet ændrer sig.


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

2. **`deskuptime.com`: 7 besøgende, 100 % bounce, 0 s opholdt tid.** Hvem:
   alle 7 på `/`. Tal: hvor mange køber. Accept: en forside der sælger uden
   at kræve scroll. Datagrund: **0 s** er ikke en lang læsning, det er en
   besøger der gik med det samme — på den eneste udgivne side der kun er én.
   Målt i Chromium 4/10 mod live: **0** JS-fejl, **0** fejlede requests,
   `scrollWidth == viewport` ved 390 og 1280, og den primære handling
   («Check a site now» → `#check`) ligger i folden ved begge bredder. Folden
   var altså ikke årsagen; 7 besøgende kan heller ikke dømme en forside.

9. ~~**`/scan` tager kun 1 URL.**~~ **Leveret 5/10** — se arkivet.
10. **`/scan` har ingen skærmbillede-resultat at dele uden et resultat.** Hvem:
    alle der scanner. Tal: hvor mange resultater der deles videre (og kommer
    tilbage som besøg). Accept: et statisk, ærligt eksempel-resultat i folden
    der ikke sender en hændelse, så læseren ser produktet uden at købe en
    kørsel. Datagrund: `#url=`-deling virker kun *efter* en kørsel, så en læser
    der kommer fra en guide kan ikke se, hvad et resultat overhovedet er. Målt
    afvigelse: et eksempel med et fast tal går stale, så det skal genereres
    eller mærkes som et eksempel — ikke skrives som et målt resultat.
