# STATUS
- **Guideartiklerne har nu én købsvej til Clean Copy Pro.** 7/10: 17 artikler på
  cleancopy.tools (8 EN + 9 DA) har en linje med link til produktets egen
  købssektion, lige før bog-CTA'en. Feature-kø 17's acceptkriterium var dog
  allerede **43/46** opfyldt målt på det byggede site — de 17 var dem der
  nævner Clean Copy Pro **uden** nogen købsvej. Se feature-kø 17.
- **CI:** seneste kørsel på `main` (`f81cf612`) er **success**. Lokal gate
  grøn på **177 steps**; de fire mission-gates kørt enkeltvis og grønne.
- **Næste:** de åbne ❓. `PR-TJEK 6/10`: **0** åbne PR'er. `BRANCH-TJEK` ikke
  kørt (uge-tjek).



## Åbne review-fund

Ingen. Alle tre er lukket 6/10:

1. ~~**MIDDEL — Clean Copy-sidens `pro_limit` modsiger Obsidian-pluginens egen
   kode.**~~ **LUKKET 6/10.** Katalogteksten siger nu kun hvad der er målt:
   batch findes i webværktøjet, egne regler i browserudvidelsen **og**
   Obsidian-pluginet, og CLI/VS Code har ingen. `manifest.json` lovede «batch
   cleaning», som `batchConvert` ikke gør i pluginet — rettet, og Obsidian er
   bumpet til **1.0.11** fordi et arkiv med en ny beskrivelse under gammelt
   nummer er det samme som gammel kode til en kunde. Bloggen på begge sprog
   fortæller hvad 1.0.11 er.
2. ~~**MIDDEL — dom 4c blev rød på en korrekt `--apply` med `&`.~~ **LUKKET
   6/10.** Dommen sammenligner nu på `html.unescape`, altså det læseren ser.
   Selftest 28→30: en korrekt tegnet `pro_limit` med `&` er grøn, og en der
   siger noget andet er stadig rød — målt begge veje mod den gamle kode.
3. ~~**LAV — `krav 4` i `check_frontpage_pricing`.**~~ **LUKKET 6/10**,
   se opgave 34.

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
ceo/pro-vej-i-guides 7/10 02:0x`

`VERIFICÉR DEPLOY: hver danske række på /da/pricing skal pege på en dansk
købsside, så ingen læser lander i engelsk midt i betalingen — hent
mahope.tools/da/pricing og kræv på indhold: 2 href="https://cleancopy.tools/da/#priser", 1
href="https://deskuptime.com/da/#pro", 0 href="https://cleancopy.tools/#price", 0
href="https://deskuptime.com/#pro", og de øvrige 10 stadig relative /da/-ruter. Derefter
hent hvert mål og kræv at ankeret findes: cleancopy.tools/da/ har 1 id="priser",
deskuptime.com/da/ har 1 id="pro", og begge sider har <html lang="da">. Samme krav på
mahope.tools/pricing: de 12 rækker skal være uændrede på engelsk ceo/den-prisliste-koer-pa-engelsk 6/10 14:1x`
— *(HTTP 200 beviser intet: den gamle kode svarer 200 på præcis de tre rækker
dom 8 nu dømmer.)*

`DEPLOY OK 6/10 14:0x` for `ceo/pricing-stripe-ankere` og `ceo/one-buy-button-tools` —
målt på **indhold** med 15 `curl`, ikke på HTTP 200. Live `/pricing` og
`/da/pricing` har hver **12** `pc-buy`, **1** uden `#anker` (donationen til
`/support`) og **0** med den gamle rute `href="/paid-templates"`. Alle **7**
dokumentankere findes som `id` på live `/paid-templates`
(`eucomply-dpa`, `eucomply-nis2-clauses`, `eucomply-nda-clauses`,
`eucomply-eaa-statement`, `eucomply-report-kit`, `eucomply-template-bundle`,
`eu-compliance-ebook-bundle`), og på `/da/paid-templates` er de danske. Live
`cleancopy.tools/` har 1 `id="price"`, `cleancopy.tools/da/` 1 `id="priser"`,
`deskuptime.com/` 1 `id="pro"`, `deskuptime.com/da/` 1 `id="pro"`,
`/compliance-report` og `/da/compliance-report` hver 1 `id="buy"`,
`/page-profile` og `/da/page-profile` hver 1 `id="pp-buy-live"` — hver side
også med sit eget `<html lang>`. Live `deskuptime.com/tools/` har **1**
`buy.stripe.com/7sY9AS9eX3Iu418fJ5bMQ01` og **1** `Payment through Stripe`.
*(De to danske krydsdomæneankere var ikke i den gamle notes krav; de er målt her,
fordi dom 8s rettelse peger på dem.)*

- **VERIFICÉR DEPLOY:** https://mahope.tools/api/url-inspect?url=https://example.com skal returnere 200 med finalUrl (efter næste batch deploy)

`DEPLOY OK 6/10 20:2x` for `ceo/url-inspect-rettet` — målt på **indhold**, ikke
på HTTP 200: live `/api/url-inspect?url=https://example.com` svarer **200** med
`finalUrl: "https://example.com"` i kroppen. SSRF er målt begge veje: `127.0.0.1`
→ **400** på `/api/header-check` og `/api/url-inspect`, `[::ffff:127.0.0.1]` →
**400**, og `169.254.169.254` → **400**. *(HTTP 200 alene ville ikke have
beviset noget — endpointet svarede 200 med en tom krop før rettelsen.)*

`DEPLOY OK 6/10 22:0x` for `ceo/pro-pastand` — målt på **indhold** med tre
`curl`. Live `cleancopy.tools/` siger «Custom cleanup rules are in the browser
extension and the Obsidian plugin — the CLI and the VS Code plugin have
none», og live `cleancopy.tools/clean-copy-tool` har den samme linje i sit
`pro-limit`. Downloadlinket ligger på **`mahope.tools/downloads`**, der er den
ene rute der har arkiverne: **2** forekomster af
`clean-copy-obsidian-v1.0.11.zip`. *(Noten krævede `cleancopy.tools/downloads`
— den har **0** `.zip`-links. Samme 404-rute-fejl som opgave 35, og det er
derfor den er lukket her.)*

`DEPLOY OK 6/10 12:1x` for `ceo/pro-graense` — målt på **indhold** med fire
`curl`. Noten krævede live `mahope.tools/clean-copy`, og den ruten er **404**:
Clean Copy ligger på `cleancopy.tools` (`build_sites.py:95` — `site/clean-copy.
html` er cleancopy.tools' forside, `index_only`). Korrigeret rute: live
`cleancopy.tools/clean-copy`, `/clean-copy-tool` og `/da/clean-copy` har hver
**1** `class="pro-note pro-limit"` og **0** `No mobile app`. *(At noten pegede
på en 404-rute er en fejl i noten, ikke et deploy-problem — HTTP 200 blev ikke
brugt som bevis.)* **Indholdet på den grænselinje er dog en usand påstand:**
se review-fund 1.

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
      `ceo/pro-graense`.** Katalogens `pro_limit` for fire produkter tegnes som
      sin egen linje under tabellen på **21** sider, begge sprog. Ny **dom 4c** i
      `check_pro_table` dømmer tre ting (katalog har `pro_limit` på hvert sprog,
      teksten står i blokken, den står på grænselinjen), selftest **28/28** da, **30/30**
      tre mutationer i selve generatoren. To usande påstande blev rettet i
      kilden, og selftesten fandt en svækket port undervejs: dom 4 læste hele
      blokken, så grænsens egen tekst blev regnet som bevis på at en funktion
      stod i tabellen — den læser nu kun `<tbody>`-rækkerne. Se arkivet for de
      **25** `where`-intervaller, der rykket ét linjenummer.
34. ~~**`krav 4` så hverken `Page Profile` eller EUComply-bundlen rigtigt.**~~
      **LUKKET 6/10**, `ceo/frontpage-navn-normalisering`. Review-fund LAV:
      `katalognavne()` krævede et rent substring, så porten var blind for varer
      der skrives som sit slug i listerne over henvisningen
      (`<a href="/page-profile">`) — altså netop den fjerde af fire — og en
      sætning der nævner `EUComply Complete Template Bundle` blev regnet som
      også at nævne `EUComply`, som *ikke* står i listerne. Rettelse: begge
      sider normaliseres (bindestreg/hvidrum → ét, casefold) og der kræves en
      ordgrænse på begge sider, og de navne henvisningen nævner findes i **ét**
      alternativ med **længste match først**. Målt på den gamle kode: «Not listed
      above: Page Profile, …» → **fund: []** (skal være rød) og «… the EUComply
      Complete Template Bundle and Transmute Desktop.» → **1 fund** (falsk
      positiv); på den nye **RØD** / **GRØN**. Selftest **10/10** med to nye
      mutationer, der dømmer begge retninger. Fuld gate **GRØN — 177 steps**.
      *Ingen deploy-note:* kun `tools/` er rørt.
35. ~~**`UNMANAGED_DOMAINS` har en 404-rute i en verificeret note.**~~
      **LUKKET 6/10.** Der var to af slagsen, og begge er dømt og rettet:
      `ceo/pro-graense` krævede `mahope.tools/clean-copy` (**404** — Clean Copy
      er `cleancopy.tools`), og `ceo/pro-pastand` krævede
      `cleancopy.tools/downloads` (**0** `.zip`-links — arkiverne ligger på
      `mahope.tools/downloads`). Begge nævner nu den rute der findes, målt med
      `curl`. *Accept-kravet står ved magt:* en `VERIFICÉR`-note skal måles på
      en rute der svarer 200 **og** har den påstand den kræver.

36. ~~**CI var rød på `main` i to steps.**~~ **LUKKET 6/10.**
    `stripe-worker-ur`: `clock_jump.mjs` hopper én time pr. kald, og hver
    trafiksektion laver **11** kald, så de hopper **11** timer — og lander de hen
    over et døgnskifte, ser `isoDaysAgo(0)` og workerens `window[0]` to
    datoer, så `by_day`-dommen dømmer et vindue der aldrig blev sået. Rødt i
    CI-run `37340718217` 5/10 kl. 16:25 på `pr. dag: 2 i dag 0 og 1 to dage
    tilbage`. Samme mønster som `stopTimeUr2` længere nede i filen: tælleren
    skal måles, ikke klokken, så uret pinnes nu i begge sektioner med hver sin
    timebøtte (så kvoten på 30/time ikke deles). Målt: gammel kode med base
    16:00Z → **473/474** med CI's exacte by_day; ny kode med samme base →
    **474/474**; ny kode grøn i **alle 24** timebaser, gammel rød i 2 af 8
    målte. `weekly-history`: `check_shared_visits_namespace.py` sender med vilje
    3 sidevisninger på `/namespace-probe` (det står i portens egen docstring), så
    regel 5 dømte `reports/weekly/2026-41.json` for at tælle vores egen trafik.
    Undtagelsen er en **proveniens**, ikke en navneliste: ruten skal være en
    modul-konstant på kolonne 0 i en `tools/*.py`; portens egen fil er
    udelukket. Selftest **27/27**, mutation (kræver blot en bogstavelig streng i
    `tools/`) → **12 fejl**. Fuld gate **GRØN — 177 steps**. *Ingen
    deploy-note:* kun `tests/` og `tools/` er rørt.

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

18. **DeskUptime har otte ruter ingen læser nogensinde ser.** Hvem: alle nye.
    Tal: hvor mange af dem kommer i betragtning. Accept: hver bygget rute under
    `/tools/` har mindst ét link fra forsiden eller navigationen. Datagrund:
    målt 6/10 — 7 besøgende, **alle** på `/`, og `tools/` har ingen indgang.
    *(Dommen skal kræve **indgangen**, ikke at ruten findes — at siden svarer
    200 er allerede målet.)*

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
