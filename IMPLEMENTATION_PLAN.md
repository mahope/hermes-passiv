# STATUS
- **Hvert pro-kort siger nu hvad Pro *ikke* gør, leveret 6/10.** Katalogens
  `pro_limit` tegnes som sin egen linje under tabellen på **21** sider, og
  ny dom **4c** i `check_pro_table` dømmer den, selftest **28/28**. Se opgave 33.
- **Forsiden havde 0 links til `/pricing`, rettet 6/10.** Afsnittet navngiver
  **4** af katalogens **13** produkter (målt på begge sprog), og den eneste side
  med alle 13 var ubefærdet herfra. Baseline: **6** besøgende, bounce
  **100 %**. Nu linker begge forsider til hele listen.
- **Forsidens henvisning modsagde listerne over den, rettet 6/10.**
  Review-fund LAV: den sagde Clean Copy Pro og DeskUptime Pro «ikke står
  ovenfor», men de står der med prisen i teksten. Ny **dom 4** i
  `check_frontpage_pricing` dømmer det — målt rød (**2 fund**) med den gamle
  sætning genindsat, selftest **7/7**. Portens «2 i listen, 11 via den» var
  håndholdt og uklædte; den er væk.
- **`check_js_residue` tabte præcis den form den var bygget til at fange,
  rettet 6/10.** Rettelsen af `; ;` slettede de linjeskifter den matchede
  over, så den maskerede tekst fik færre linjer end den rå — og porten tabte
  et ægte fund og rapporterede linjetal **to for lave**. Se opgave 31.
- **Én åben `VERIFICÉR DEPLOY`-note** (se nedenfor), alle tidligere lukket på
  målt indhold, ikke på HTTP 200.
- **Næste:** mål de **2** `#url=`-delingskinder på `/scan`, så vi ved om
  deling er værd at gøre synlig. `PR-TJEK 6/10`: **0** åbne PR'er.
  `BRANCH-TJEK` ikke kørt (uge-tjek).

## Verificér deploy

`VERIFICÉR DEPLOY: hvert pro-kort har en ærlig grænse
ceo/pro-graense 6/10 09:3x` — krav på **indhold**: live `mahope.tools/` skal
have **1** `class="pro-note pro-limit"` på `/clean-copy` og **0**
`No mobile app` (den påstand var usand), og live `cleancopy.tools/` det
samme. HTTP 200 er ikke bevis.

`DEPLOY OK 6/10 08:5x` for `ceo/folsaetning-om-priser` — målt på **renderet
indhold** med to `curl`: live `mahope.tools/` og `mahope.tools/da/` har
hver **1** `Not listed above:` / `Ikke listet ovenfor:`. *(Noten krævede også
**0** `Clean Copy Pro, DeskUptime Pro` i `#products`, og den fandt **1** på den
engelske forside — men kun fordi målingen greb en **HTML-kommentar** i kilden
der forklarer rettelsen. Kommentaren er ikke læsbar tekst; det er den nye
sætning der dømmes. Den danske forside har **0**.)*

`DEPLOY OK 6/10 07:1x` for `ceo/pricing-fra-forsiden` — målt på **indhold** med
to `curl`: live `mahope.tools/` har **2** `href="/pricing"` og live
`mahope.tools/da/` **2** `href="/da/pricing"`. *(Noten krævede 1; den rigtige
måling er 2 pr. forside, fordi buildet skriver både `<head>`-canonical og
sidens synlige knap. Kravet var «mindst én», så begge er over linjen, og det er
indholdet der er dømt — ikke HTTP 200.)* CI `2ee5d77f` = **success**.

`DEPLOY OK 6/10 07:0x` for `ceo/js-rest-gate` — målt på **indhold**: live
`mahope.tools/da/free-tools` (34 991 bytes) har **0** `);;if` og **1**
`?$/);if(!m)return;`, altså dobbelt-semicolon-resteren er væk og klik-
målingen er intakt. Kildekaldet er stadig der: **1** `api/track` og **3**
`da/paid-templates`. CI `8bcd5e18` = **success**. HTTP 200 blev ikke brugt
som bevis.

`DEPLOY OK 6/10 07:0x` for `ceo/pro-kort-uden-krybning` — målt på **indhold**
på alle nitten ruter med `curl`. De ni pro-sider har **0** `crawls the whole
site` og **0** `gennemgår hele sitet`, og hver har sin egen sætning fundet 1–2
gange: «reads the page you name from the server» på compliance-site-check begge
sprog, «response headers as well» på cookie-check begge sprog, «reads the page
from the server too» på contrast- og text-on-image begge sprog, «reads the page
source as well» på security-headers-check. `/books`, `/compliance-ai`,
`/da/compliance-ai` og to bogsider: **0** «crawls the site»/«crawls it». Live
`/scan` har stadig **1** «whole-site crawl up to 200 pages» — den ægte
desktop-påstand er ikke ved et fejl gået. HTTP 200 blev ikke brugt som bevis.

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


31. ~~**`check_js_residue` dømmer kun `;;` uden mellemrum, så `; ;` glider
    igennem.**~~ **LUKKET 6/10.** Review-fund 5/10 (MIDDEL): begge regexer krævede
    at semikolonnerne stod i én ubrudt række, så den form `sed`/`perl` faktisk
    efterlader var grøn. Målt med portens egen `judge_js()` **før** rettelsen:
    `f(); ; g();`, `a=b; ; c=d;`, `f(); ;`, `}); … ;if (x) {…}` og `  ; ;` på
    egen linje gav **alle 0**. Nu `;[ \t]*;` og `^[ \t]*(?:;[ \t]*)+$`. Den
    ene legitime form er den tomme betingelsesliste, og den kan stå midt i en
    fyldt peger (`for (let i = 0; ; i++)`), så `RE_LOOP_HEADER` sletter parret på
    hele pegeren — ikke kun mellem parenteser som den gamle `RE_EMPTY_HEADER`.
**Selftest 0 fejl, porten 0 fund i 2087 enheder** (site + dist), og syv af
     de ti nye selftest-tilfælde er målt røde på den gamle kode (0 fund) mod
     korrekte på den nye; de tre øvrige er nye vagter, fordi den gamle regel
     slet ikke kendte `; ;`-formen. *(Et review-fund sagde «ni» — tallet er
     syv, og det er rettet her, så det ikke bliver brugt som grundlag for at
     droppe en port.)* Fuld gate **GRØN — 177 steps**. Der kom også en
     rå-bekræftelse på dobbelt-reglen: maskeren gør to template-literals på én
     linje til mellemrum, så `` `a` ; `b` ; `` lignede et fund; den er låst med
     et tilfælde. *Ingen deploy-note:* kun `tools/` er rørt, ingen fil i
     `site/` eller `dist/`, så intet på sitet ændrer sig.

32. ~~**Rettelsen i opgave 31 slettende de linjeskifter den matchede over.**~~
     **LUKKET 6/10.** Review-fund 6/10 (MIDDEL): `RE_EMPTY_CONDITION` er
     `;[ \t\r\n]*;`, så den matcher *også på tværs af et linjeskift*, og
     `out[i + k] = " "` skrev `" "` over hvert tegn i matchen —
     **linjeskiftene inklusive**. Den maskerede tekst fik derfor færre linjer
     end den rå, og `judge_js` tæller linjer i den maskerede tekst *og* slår
     den rå linje op på samme indeks, så både tal og opslag kom ud af trit.
     Docblocken sagde «positionerne bevares, så et fund stadig kan slås op på
     den rigtige linje» — længden blev bevaret, **linjetallet ikke**.
     *Målt* med portens egen `judge_js()` på samme input, `2ee5d77f` mod
     `887d1c0f`: `for (let i = 0;\n;\ni++) {}\n;\n` gav **2 fund** (linje 2 +
     4) på den gamle kode og **0** på den nye. Linje 3 (`;` alene) er den
     **legitime** tomme betingelsesliste, linje 4 (`;` alene) er en **ægte
     rest** efter pegeren — altså tabte den nye kode den sande. Og et fund på
     rå linje 9 blev rapporteret på linje 7. Rettelse: `if out[i + k] not in
     "\r\n"`. *Efter rettelsen* (målt i samme måling): **1 fund på linje 4**,
     og den anden række **linje 9**. Den falske positive på den legitime
     `;`-linje kommer ikke tilbage, fordi semikolonerne selv stadig blandes
     ud, så den maskerede linje er `   `. Selftest **0 fejl** mod **3 fejl**
     på den gamle kode — to nye rækker plus en ny `paa_linje`-kontrol der
     dømmer linjetallet, fordi det er læsbarheden og ikke en bivirkning.
     Porten **0 fund i 2087 enheder**, og kørt på de **35 egne `.js`-filer**
     uden for portens dækning (den dækker `site/` og `dist/`): **0 fund**, så
     den bredere regel har ikke lavet falske positive i `desktop/`- eller
     extension-overfladen. Fuld gate **GRØN — 177 steps**. *Ingen
     deploy-note:* kun `tools/` er rørt.

33. ~~**Ingen produktside siger hvad Pro *ikke* gør.**~~ **LEVERET 6/10,
     `ceo/pro-graense`.** Katalogen har nyt `pro_limit` på de **4** produkter
     der har en pro-tabel, og `pro_table.py` tegner det som **egen linje**
     under tabellen på **21** sider, begge sprog. Den ligger ikke i prisnoten:
     målt 6/10 læste den der som «Én licens dækker 3 maskiner. · Alarmer er …»,
     et punktum midt i en punktumliste. Ny **dom 4c** i `check_pro_table`
     dømmer tre ting: katalogen skal have en `pro_limit` på **hvert** sprog,
     teksten skal stå i blokken, og den skal stå på grænselinjen
     (`class="pro-note pro-limit"`) — så den hverken kan forsvinde eller glide
     op i prisnoten og læses som en pris. Selftest **28/28** med tre
     mutationer i selve generatoren, så dom 1 (byte mod `pro_table.blok()`)
     er grøn og kun dom 4c kan være rød.
     **To påstande var usande og er rettet, målt i kilden:** Clean Copy
     sagde «browser extension and desktop only» — der findes ingen Clean Copy
     desktop-app, kun udvidelse, CLI og to editor-pluginer; den siger nu at
     batch kun findes i webværktøjet og egne regler kun i udvidelsen
     (målt: `clean-copy-cli` har ingen `--batch` og ingen regelflag). Og
     DeskUptime sagde «webhook only», men `monitor.rs` sender
     desktop-notifikationer (`tauri_plugin_notification`) ved siden af de 36
     webhook-kald, så teksten siger nu at alarmer er
     skrivebordsnotifikationer og webhooks. De to øvrige er målt sande:
     `page_profile.py` har nul `alert`/`notify`/`schedule`, og DPA + NIS2 er
     egne Stripe-produkter.
     **Selftesten fandt en svækket port undervejs:** dom 4 læste katalogens
     funktionsnavne i hele blokken, så grænsens «Batch conversion is web-tool
     only» blev regnet som bevis på at funktionen stod i tabellen, og
     «manglende Pro-funktion» faldt rød. Dom 4 læser nu kun `<tbody>`-rækkerne.
     **En følge fandt porten `catalog-where`:** den nye linje forskyder
     linjenumrene i fem sider, og katalogens `where`-intervaller peger på
     linjer — så 6 fund blev røde på citater der lå **én linje** under deres
     interval. Alle **25** `where`-strenge er rykket ét linjenummer for de
     referencer der ligger efter indsættelsen (målt: `catalog-where` GRØN,
     selftest **11/11**). Det er samme fælde som opgave 31: en linje i en
     kildefil er en afhængighed, ikke en detalje.

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

10. ~~**`/scan` mangler et eksempel-resultat at dele.**~~ **LUKKET 6/10.** Leveret
    som et *målt* eksempel-kort under folden (`afbe1a37`), ikke et fasttal der
    går stale. Målt afvigelse: tallene kommer fra `tools/scan_example.py`, der
    kører sidens egne scripts i headless Chromium mod en lokal stub.

12. ~~**Forsiden nævner 2 af 13 produkter og 0 links til prislisten.**~~
    **Leveret 6/10.** Salgsafsnittet linker nu til `/pricing` i begge sprog.
    Målt 6/10: afsnittet navngiver **4** af 13 (`clean-copy-pro`,
    `deskuptime-pro`, `eucomply-pro`, `page-profile-pro`) — de to tal i den
    oprindelige optælling var solgte varelinjer, ikke produkter.

13. **Hver produktside kun én købsknap — de 13 har 73 dokumenterede købssider.**
    Hvem: købere på tværs af alle 13. Tal: køb pr. produktside. Accept: hver
    produktside har præcis én synlig CTA til sin egen payment link, så ingen
    læser skal vælge mellem to knapper. Datagrund: målt 5/10 —
    `check_stripe_ctas` tæller i 73 dokumenterede købssider, men kun pr. side,
    ikke pr. CTA. *Ikke påbegyndt.*

14. ~~**Ingen produktside siger hvad Pro *ikke* gør.**~~ **Leveret 6/10** —
    se opgave 33.
