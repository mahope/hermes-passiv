# STATUS
- **Scannerens eget felt ligger nu i folden.** 5/10: `/scan` er mål for **559**
  interne links på **228** sider (optalt med `html.parser`, altså uden de 4 fund
  i `dist/`), og den er toppen af den dyreste linje — EUComply Pro, **$79/år**.
  Folden var badge + `<h1>` + tagline og så et tomt `required`-felt i `<main>`.
  Formularen ligger nu i `<header class="hero">`, og knappen bruger husets
  `btn-primary`: den egne regel `.scanbox button` (0,1,1) lå oven i
  `.btn-primary` (0,1,0) og lagde sin egen `#0b6e8f` oven i accentfarven.
- **Målt afvigelse i opgavens egen begrundelse:** `#result` kom under folden med
  formularen, så et klik i folden intet gjorde synligt. Alle **3** skrivninger
  kalder derfor `revealResult(out)`, som kun ruller når resultatet ikke allerede
  kan ses — ellers ville et læst resultat hoppe op ved hvert skærmbillede.
- **Rigtige tal fra `/api/results` og `/api/conversion` (28 dage):** **0**
  resultater, **0** `pro-card-clicks`, **2** `buy-clicks**. Nul er det rigtige
  svar på «er nogen ved at bruge scanneren lige nu», ikke en fejl.
- **Tragten kan læses uden `STATS_TOKEN`** i **2** ruter — resultater (`/api/results`) og
  købsforsøg (`/api/conversion`) er hver en udlæsning af de nøgler `/api/track`
  allerede skriver, med egen navneliste. Salg og licenser ligger *kun* i
  `/api/stats`.
- **Scannerens købsvej er målt hel i 5 events, og kun én gang:** `scan()` →
  `scan-findings`/`scan-clean` → `pro-card-click`, plus `scan-failed`.
- **Næste:** feature-kø 2 (`deskuptime.com` — 7 besøgende, 100 % bounce, 0 s) er
  målt og kan ikke dømmes på 7 besøgende. `/scan` er nu rettet, så næste måling
  er dens `scan`-events og `pro-card-clicks` — ikke dens markup.

## Verificér deploy

`VERIFICÉR DEPLOY: scannerens felt i folden 5/10 23:1x
ceo/scan-form-i-folden` — måles på **indhold**: live
`https://mahope.tools/scan` skal have præcis **1** `<form id="scanForm">`
**inden i** `<header class="hero">` (altså før `</header>`) og **0** i `<main>`,
knappen skal være `<button type="submit" class="btn-primary">`, og siden skal
**ikke** definere `background` for `.scanbox button`. `#result` skal være **1**
gang og **uden for** heroen, og alle **3** skrivninger til den skal kalde
`revealResult(out);`. Samme dømning på `/scan-da`. HTTP 200 bruges ikke.

`VERIFICÉR DEPLOY: dommen i folden 5/10 21:5x
ceo/verdict-i-folden` — måles på **indhold**: live
`https://mahope.tools/text-on-image-checker` skal have præcis **1**
`#verdict[data-ti-verdict]` som **første** element efter `<h2 id="tool-heading">`
— altså før `.ti-canvas-wrap` og før `#result` — og dens tekst skal være
«PASS 4.07:1» + «Measured on the example image.». Den danske side skal have
«BESTÅET 4,43:1» + «Målt på eksempelbilledet.». `.hero p.tagline` skal være
**under 120 tegn** på begge. HTTP 200 bruges ikke som bevis.

`VERIFICÉR DEPLOY: resultat-koerende-taeller 5/10 21:0x
ceo/resultat-koerende-taeller` — måles på **indhold**: live
`https://mahope.tools/api/results?days=7` skal have feltet
`served_scans_lifetime` (ikke `served_scans`), `note` skal indeholde
`NOT a count for this window`, og svaret må stadig have `totals.runs`.

`DEPLOY OK 5/10 21:0x` for `ceo/tokenfri-konvertering` — målt på **indhold**:
live `/api/conversion?days=7` svarer **200** med `"status":"ok"` og `totals` med
`buy_clicks`, `visitor_days` og `pro_card_clicks`; svaret rummer **0** `@`, **0**
32-hex-t og **0** `$`+tal, `POST` svarer **405**, og `/api/results` svarer **200**
uden at tælle `buy-click`. Rigtige tal fra den: **1** købsklik på
`/compliance-report` 29/9 og **0** resultater i 7 dage.

`DEPLOY OK 5/10` for `ceo/clean-copy-tool-fold` — målt på **indhold**:
`https://cleancopy.tools/clean-copy-tool` har **1** `<header class="hero">` med
**1** `.hero-cta a[href="#input-box"]` («Paste your text») og **1** `.hero-note
a[href="#free-vs-pro"]`, og begge id'er **1** gang. Hero-noten er målt i rigtig
Chromium ved **390 og 1280**: **13,6 px** (0,85 rem) på `cleancopy.tools/`,
`/da/` og en `/da/blog/`-side — ikke 20,8/18,4. HTTP 200 blev ikke brugt.

`DEPLOY OK 5/10` for `ceo/klientfejl-til-sentry` — målt på **indhold**: live
`https://mahope.tools/track.js` (200) har præcis **1** `addEventListener('error'`,
**1** på `'unhandledrejection'`, **2** `'/api/client-error'` (beacon + fallback) og
**0** felter med brugerens URL. **Målt afvigelse:** noten krævede **0**
`location.href` og **0** `page:`; live står hver **1** gang, men begge er i
*kommentarer* (linje 250 og 46), ikke i payload'en — de sådan fund er
meningsløse, så dommen er præciseret til at dømme payload-felterne.

`DEPLOY OK 5/10` for `ceo/scan-events` — målt på **indhold**: `/scan` og `/scan-da`
(308 → `/scan`, `/scan-da`, 200) har hver præcis **1** `trackEvent('scan')`, **0**
`event:'scan'`-fetch, **1** `scan-findings`, **1** `scan-clean`, **1**
`scan-failed`, **1** `pro-card-click` på **samme linje** som
`buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03`, og **1** `!opts.shared`. Runtime-kravet
(klik på den renders knap → **én** `trackEvent('pro-card-click')`) var målt i
Chromium mod den byggede `dist/` i opgavens iteration; den udgivne fil er
tegn for tegn lig den.

`DEPLOY OK 5/10 19:5x` for `ceo/tekstartens-egen-handling` — målt på **indhold**:
live `/blog/text-on-image-contrast-check` (200) har præcis **1** `p` med «check
it free in the browser» i **første** `<section class="problem" id="why">` før
`problem-cards`, med `href="/text-on-image-checker"`; live
`/da/blog/tekst-paa-billede-kontrasttjek` (200) har **1** «tjek det gratis i
browseren» med `href="/text-on-image-checker-da"` på samme plads. Begge sider har
**1** `hero-cta` med `btn-primary` (`#try-it` / `#prov-dit-billede`) og **0**
`btn-primary` i `.blog-tool-cta`. **Målt afvigelse:** noten skrev
`<section class="problem">` uden `id`; live er den `id="why"`. Dommen er rettet
til at læse `problem-cards` som ankerpunkt, så den ikke igen er så stram at den
måler sin egen fejl.

`VERIFICÉR DEPLOY: konvertering læses uden STATS_TOKEN 5/10 20:5x
ceo/tokenfri-konvertering` — måles på **indhold**: live
`https://mahope.tools/api/conversion?days=7` skal svare **200** med
`"status":"ok"` og `totals` med `buy_clicks`, `visitor_days` og `pro_card_clicks`,
svaret skal **ikke** indeholde `@`, 32 hex-tegn eller `$` + tal, og `POST` skal
svare **405**. `/api/results` skal stadig svare **200** og må **ikke** tælle
`buy-click` — de to lister er hver sin. Nul købsklik er det rigtige svar på «er
nogen ved at købe noget lige nu», ikke en fejl.

`DEPLOY OK 4/10 13:1x` for `ceo/fold-pris` — målt på **indhold**:
`https://cleancopy.tools/` har **1** `.hero-note a[href="#price"]`, `id="price"`
**1** gang. `https://deskuptime.com/` og `/da/` har **1** `.hero-note
a[href="#pro"]` hver, `id="pro"` **1** gang hver. Den danske forside peger på
`#priser`, **1** gang. HTTP 200 bruges ikke som bevis.

`DEPLOY OK 4/10 13:1x` for `ceo/bogsfold-handling` — målt på **indhold**:
`https://mahope.tools/books/` har præcis **1** `<a href="#books" class="btn-primary">`,
og `/books/compliance-bundle` **1** `href="#download"` med `id="download"`
**1** gang. **Målt afvigelse:** `/books/compliance-bundle/` med slutstreg svarer
**308** til den uden streg — den nævnte adresse i noten var derfor den forkerte
af de to; indholdet er det samme, og begge varianter er dømt ovenfor.

`DEPLOY OK 4/10 11:2x` for `ceo/downloads-fold` — målt på **indhold**:
`https://mahope.tools/downloads` har præcis **1** `btn-primary` i
`<header class="hero">` med etiketten «Get the desktop app», og
`href="#desktop-app"` + `id="desktop-app"` forekommer **1** gang hver. HTTP 200
blev ikke brugt som bevis.

Ingen deploy-note for `ceo/taal-i-tekst`: den rører **0** filer i `site/`, kun
`tools/*.py`, `tools/*.json` og planen, så intet serverside eller i klienten
ændrer sig. Portene er målt lokalt i stedet.

`DEPLOY OK 4/10 11:2x` for `ceo/review-fund-oktober` — målt på **indhold**:
`https://mahope.tools/da/blog/` har **0** «Browse efter emne» og **1** «Se efter
emne», og `href="#tilg-ngelighed-eaa"` står uændret **1** gang.

`DEPLOY OK 4/10` for `ceo/banner-secondary` — målt på **indhold** 10:1x, ikke
HTTP 200: de fem artikler har **1** `btn-primary` i `<header class="hero">`
(`Start Reading` ×3, `Læs guiden` ×2), **0** i hvert
`<div class="blog-tool-cta">`, og ankeret `#content`/`#indhold` forekommer
**præcis 1** gang pr. side. Deploy sker ved push til `main`.

`DEPLOY OK 4/10` for `ceo/hub-fold-handling` — målt på **indhold** 10:1x:
`/free-tools`, `/da/free-tools`, `/blog/`, `/da/blog/` og `/free-downloads`
har hver **1** `btn-primary` i folden, og ankerne er `#gdpr-heading` ×2,
`#accessibility-eaa`, `#tilg-ngelighed-eaa` og `#tpl-heading` — hvert med
**præcis 1** matchende `id`. `/da/blog/` leverede dog «Browse efter emne»,
altså den halvoversatte etikette der er rettet i dette loop; den er derfor
**stadig ikke live**, og kun den etikette mangler.

`DEPLOY OK 4/10` for `ceo/pricing-i-footer` — målt på **indhold** 09:2x:
`https://mahope.tools/` har **23** links i `<footer class="site-footer">` og
præcis **1** `/pricing`; `https://mahope.tools/da/` har **23** og præcis **1**
`/da/pricing`. Det er dom 6 i `tools/check_pricing_page.py`, som allerede læste
samme adresse i den byggede footer. HTTP 200 blev ikke brugt som bevis.

`DEPLOY OK 4/10` for `ceo/vaerktoj-fold` — målt på indhold 07:0x: alle **otte**
svarer 200 og har præcis **1** `btn-primary` i `<header class="hero">`, hver med
sit eget anker (`#checker-heading` ×2, `#sim-heading` ×2, `#gen-heading` ×2,
`#tool-heading` ×2), og hvert anker findes **præcis 1** gang på sin egen side.
`contrast-checker-da` har **0** `FREE TOOL`. HTTP 200 blev ikke brugt som bevis.

`DEPLOY OK 4/10` for `ceo/net-ruter` — ikke en note, men en måling fra samme
kørsel: ændringen ligger i `tools/check_net_copies.py` og rører **0** filer i
`site/`, så der er intet nyt at hente. Porten måles i næste iteration.

`DEPLOY OK 4/10` for `ceo/developers-side` — hentet på indhold: `/developers`
200 med fire endpoint-blokke, clean-copy-kommandoen sender `{"mode":"markdown"}`,
siden siger *nine* compliance-tjek, footeren på `mahope.tools/da/free-tools`
har linket, `llms.txt` har linjen, og `cleancopy.tools/mcp` har 2 `npx
@mahope/passiv-mcp` og 0 `npx github:`. **Målt afvigelse:** planen havde
skrevet `mahope.tools/mcp`, som 404'er — `/mcp` er kun på cleancopy.tools,
fordi den side ligger i det domænes kilde. Noten er rettet her.

`DEPLOY OK 4/10` for `ceo/deskuptime-en-kob` — målt på indhold 05:2x, efter at
gaten blev grøn: EN 200 med **1** `buy.stripe.com/7sY9AS9eX3Iu418fJ5bMQ01`,
**0** «uploaded anywhere, ever», og afsnittet «The notification only arrives
while the app runs» har `webhook` + `unlimited sites` + `client-ready report`.
DA-siden giver 1 købslink, 0 «uploaded anywhere, ever» og 0 «Intet uploades
nogensinde». Deployen var forsinket, fordi `deploy` har `needs: gate`, og begge
røde kørsler lå på gatens egen selftest.

`DEPLOY OK 4/10` for `ceo/waitlist-egen-fejl` — målt på indhold 05:2x: alle
**seks** bogsider der indlæser `book-lead.js` har præcis **1** `src="/net.js"`
**før** `src="/book-lead.js"` i markup-rækkefølge, inklusive
`/books/build-your-first-chrome-extension` der før manglede `/net.js` helt. Live
`/net.js` har **1** `function ask(`, `book-lead.js` har **0** `fetch('/api/waitlist'`
og **0** `Network error`. **Målt afvigelse:** noten lovede «2 defer-tags» på den
side; live har **5** linjer med `defer`, fordi siden også indlæser `track.js`.
Kriteriet der betød noget — `/net.js` før `book-lead.js` — holder.

`DEPLOY OK 4/10` for `ceo/developers-kvoter` — målt på indhold 06:2x:
`https://mahope.tools/developers` har **1** `512 000 characters per page` og **0**
`500 000`. Kriteriet var rigtigt; resten af rækkerne er dømt af
`tools/check_developers_page.py`, som læser dem fra `_worker.js`.


## Åbne opgaver

1. ~~**En nøgle der ikke aktiverer, har ingen selvbetjening.**~~ **Færdig 3/10.**
2. ~~Flere sider end forsiden pr. URL.~~ **Færdig 1/10.**  Flyttet til
   `docs/plan-arkiv.md` sammen med de 8 øvrige afkrydsede opgaver.
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
5. ~~**171 sider har to-tre knapper over folden.**~~ **Færdig 4/10**,
   `ceo/banner-secondary`. `add_top_cta_495.py`, `add_ai_cta.py` og
   `add_hero_cta.py` skrev hver især en `btn-primary` ind i bannerne —
   **330** knapper på de **179** banner-sider dengang. Nu er de
   `btn-secondary`, alle tre generatorer er rettet i samme diff, og
   `check_first_action.py` dømmer bannerreglen på alle sider med banner.
   Målt **171 → 0**. Fem artikler der kun *havde* banneren som handling har
   fået deres egen. ❓ om bannerens placering står uændret — reglen er
   skrevet, så den er forenlig med alle tre svar.
6. **Bogen har ingen DA-udgave, og læsevisningen gør det tydeligt.** Hvorfor: de
   seks bøger er på engelsk. Målt 2/10: der findes **ingen** `/da/books/*`-ruter,
   så bogsiders hreflang har intet dansk par. Accept: enten en DA-udgave af de to
   vigtigste som EPUB i `ebook/`, eller en synlig dansk note på bogside-ruterne.
   Kræver beslutning — se ❓.
7. ~~**CEO-kø punkt 2 og 4 — DeskUptimes løgnede privatlivstext og den
   artikel uden købsvej.**~~ **Færdig 4/10**, `ceo/deskuptime-en-kob`.
   CEO-kø punkt 1 (Lemon Squeezy-ruten) lå allerede væk: `grep -rn lemon
   site/_worker.js` giver 0. Punkt 3 (sitemap/robots) er målt grøn af
   `check_sitemaps.py` + `check_live_sitemaps.py`, og ❓ har
   Search Console-linjen. Punkt 4 er målt af `check_stripe_ctas.py` (13
   produkter, 73 købssider, 0 problemer) og nu af `check_deskuptime_claims.py`.
8. **En sitemap-rute må ikke have en død eneste handling.** Hvorfor: porten
   dømmer kun de to ruter i `tools/unavailable_routes.json`. Accept: porten
   finder den, hvis den skrives i manifestet. *(Kun relevant når vi tilføjer flere
   sådanne sider — ikke en opgave i sig selv.)*
9. ~~**Porten dømmer kopier af reglen, ikke klienter der mangler den.**~~
   **Færdig 4/10**, `ceo/net-kaldere`. Dom 3 læser ruterne i `_worker.js`s egen
   dispatch og dømmer rå `fetch` på dem. `<pre>` er fjernet før søgningen.
   ~~de 6 `nis2-*`~~ og ~~`compliance-ai` 486/487~~ er begge flyttet 4/10,
   `ceo/net-waitlist-klienter` — portens liste er **7 filer**, og alle syv har en
   grund der *ikke* er «ikke flyttet endnu».
10. ~~**Review-fund 4/10: porten dømmer 22 af 23 ruter, og den 23. er usynlig af
     konstruktion.**~~ **Færdig 5/10**, `ceo/net-ruter`. `_worker.js:286`
     dispatcher `/api/download/` med `startsWith`, som et `path ===`-mønster ikke
     kan se — så fundets egen mutation var grøn. Målt: **23** ruter, selvtest
     **30/30**, fire mutationer røde (fundets egen `/api/download/`-indsats i
     `stats.html`, `fetch('/api/ukendte-rute')`, en død undtagelsesrute, og en
     præfiks-rute læst med kun den gamle liste). Ny liste med **1** grund:
     `clean-copy-tool.html`s dynamiske `'/api/license/' + endpoint`.
11. ~~**Prislisten kunne ikke findes.**~~ **Færdig 4/10**, `ceo/pricing-i-footer`.
     Hvorfor: `/pricing` er den eneste side med alle **12** varers priser, og den
     hang i **1** af **224** kildesider og **0** af **270** footere — altså i
     sitemap, målbar for Google og usynlig for mennesker. Accept: linket i hver
     bygget footer på sit eget sprog, ratchetede af dom 6. **Målt:** grøn på ny
     kode, **270** fund på gammel, selftest **13/13**, ingen vandret scroll ved
     **360/390/1280**.
12. ~~**Review-fund 4/10: to fund om noter der afregner for lidt.**~~
     **Færdig 4/10**, `ceo/review-fund-oktober`. Den danske foldknap sagde
     «Browse efter emne» på den ellers danske `/da/blog/` — **målt live** — og
     `_4oktober_hubs` afregnede **9 af 11** sider. Rettet til «Se efter emne» i
     generatoren og i den genererede side, og de **6** der blev ladt ligge er
     nu navngivet med grund, så noten afregner **11 af 11**. Selftestens
     mutation greber på **ankeret** i stedet for på etiketten, så en
     sprogretning ikke kan låse porten: **23/23** med den nye sætning (var
     **22/23** med den gamle regex), og et dødt foldanker giver stadig **RØD**.
13. ~~**`/downloads` stod uden handling i folden.**~~ **Færdig 4/10**,
     `ceo/downloads-fold`. Søster-siden til `/free-downloads`, der fik en
     fold-CTA samme dag, havde badge, `<h1>` og tagline men intet at trykke på.
     Nu `#desktop-app`, sektionen med de tre rigtige downloads, og ratcheted.
     Målt: sider med nul primær **6 → 5**, porten **RØD** når `hero-cta` fjernes.
14. ~~**Banner-teksten skrev fire forkerte optællinger.**~~ **Færdig 4/10**,
    `ceo/taal-i-tekst`. Målt på `b1a1b77~1` med portens egne regex'er: de
    **330** knapper lå på **179** sider (ikke 187 over tre steder), **189** sider
    bar et banner (ikke 187), og **186** havde AI-banner (ikke 188 i to
    steder). Rettelsen er ikke et nyt tal men en regel: et *dateret* målingstal
    er en kendsgerning og bliver stående, et *løbende* side-tal er skrevet ud
    og peger på portens egen afregning. Rørt 6 filer, heraf `_4oktober_hubs` der
    stadig skrev at `downloads` var «ikke dømt endnu» — samme fejlform, samme
    diff. Efter egen gennemgang af de nye tekster grebet de to påstande de selv
    skabte: «eller kør `--list`» (porten returnerer *før* afregningen der) og
    «banneren ligger på hver side» (M i portens linje er alle sider i `site/`,
    ikke dem med banner).
15. ~~**De 3 af de 5 sider med nul handling over folden, der ikke var undtaget
    med en grund.**~~ **Færdig 5/10**, `ceo/bogsfold-handling`. `books/index`
    fik `#books` og `books/compliance-bundle` `#download`; `url-inspector` er
    skrevet ind som *begrundelse* (handling = `<input>` + knap, ikke et link),
    ikke som udsættelse. Sider med nul primær **5 → 3**. Målt: porten **RØD**
    når `hero-cta` fjernes fra `books/index`, og **RØD** «ankeret er dødt» når
    `id="download"` fjernes; selftest **20/20**; fuld gate **159 steps** grøn.
    Chromium ved **390/1280**: begge knapper i folden, `scrollWidth == viewport`,
    blå #1a73e8 med hvid tekst (**4.51:1**, AA), og `#books`/`#download` findes
    begge **1** gang. `books/index`' knap er **37 px** høj — sidens egen
`.btn-primary`-token, som de seks downloadknapper under den også bruger, så
     den er gjort større forskel uden at skille sig fra dem.
16. ~~**Fire lokale grene har 7 uafgivne commits** de skal landes fra.~~
    **Færdig 5/10**, `ceo/stale-grene` — de skulle **ikke** landes. Se
    målingen i STATUS: to var allerede på `main` (`git cherry` giver `-`), og de
    to andenordens filer var **ældre** end main, så en landing ville have
    reverteret to rettelser. Alle fire slettet, intet tabt.
17. ~~**Katalogens `where` har linjenumre, der ikke peger på det de siger.**~~
    **Færdig 5/10**, målt i samme kørsel: `check_catalog_where.py:176-180` dømmer
    `y > len(linjer)`, så en vilkårlig `:900`-henvisning giver **RØD** — accepten
    holdt uden ny kode. De otte pro-teksters egne linjesnit er rettet i samme
    diff som målingen fandt dem forkerte.
18. ~~**`/clean-copy-tool` er Pro-salgssiden, og dens fold kan ikke dømmes.**~~
    **Færdig 5/10**, `ceo/clean-copy-tool-fold`. Målt 4/10: **2** besøgende,
    **0 % bounce** — de eneste to af 19 der læste videre. Nu `<header
    class="hero">` med `#input-box` som primær (siden *er* værktøjet) og
    Pro-tilbuddet i `.hero-note` til `#free-vs-pro`. `pristabel()` læser nu det
    nærmeste overskrifts-id på sider **uden** `<section>`, så tabellen dømmes i
    stedet for at blive overset. Accept holdt: **38** ratchetede sider, selftest
    **28/28**, porten **RØD** når `hero-cta` fjernes, **GRØN** når ankerets
    *etikette* ændres. Chromium 390/1280: CTA i folden, ingen vandret scroll,
    `.hero-note` **13,6 px**, `#0f7b6c`/hvid = **5,16:1**, 0 JS-fejl.
19. ~~**Review-fund 5/10 (MIDDEL): hero-noten på de to cleancopy-sider var
     20,8 px.**~~ **Færdig 5/10**, `ceo/clean-copy-tool-fold` — samme squash som
     opgave 17, fordi de to rettelser deler portene. Fundet var rigtigt,
     men **årsagen var bredere end de to filer**: `.hero p` (0,1,1) vandt over
     `.hero-note` (0,1,0), så enhver `.hero-note` der var et `<p>` blev stor som
     brødteksten. Målt i Chromium 390/1280 mod den byggede `dist/`: **20,8 px**
     på `cleancopy.tools/` og `/da/` (mod **13,6**) og **18,4 px** på de **179**
     blog- og guidesider med `<p class="hero-note">`. Rettet i årsagen med
     `:not(.hero-note)` på begge `.hero p`-regler; efter: **13,6 / 13,6 / 13,6**
     på cleancopy og **13,6** på bloggen ved begge bredder, `scrollWidth ==
     innerWidth` overalt. Ny port `check_hero_note_scale.py` (10/10 selftest)
     dømmer at ingen `.hero p`-regel må overrule noten; **GRØN** på den nye
kode, **2 fund** på den gamle med præcis de to regler, og mutationsmodulet
      giver **RØD** når `:not()` fjernes fra enten den ene eller den anden.
20. ~~**Pro-kortet på `/scan` kan ikke måles, så dets effekt er ukendt.**~~
    **Færdig 5/10**, `ceo/scan-events`. Målt i koden: `scan()` sendte `scan`
    ved starten *og* igen med en rå fetch efter svaret — **én scanning = to
    begivenheder** — og der kom intet ved resultatet eller ved pro-kortets knap,
    så 290 indgående links (1/10) ikke kunne skelnes fra køb. Nu hele tragten:
    `scan` → `scan-findings`/`scan-clean` → `pro-card-click`, plus
    `scan-failed` så en fejl ikke ser ud som et resultat. Delt rapport tæller
    ikke (`!opts.shared`) — den er afsenderens resultat. `pro-card-click` er et
    målepunkt *ved siden af* `buy-click`, ikke en erstatning. Ny port
    `check_scan_events.py`: grøn på ny kode, **5 fund pr. sprog** på den gamle,
    selftest **18/18** (6 mutationer + 4 polariteter), og katalogens otte
    `where`-henvisninger på de to sider er flyttet med koden. Runtime målt i
    Chromium mod den byggede `dist/`: 0 sidefejl, og et klik på den renders
    knap kalder `trackEvent('pro-card-click')` **én** gang.
21. **En `ceo/*`-gren er ikke arbejde, fordi den ligger uden for `main`.** Hvorfor:
    målt 5/10 — alle fire var dubletter, og to ville have reverteret
    `3755b96f` + `158715e9`. Accept: før en gren nævnes i planen skal
    `git cherry main <gren>` være læst, og dens rørte filer sammenlignet fil-for-fil
    med `main`. En `+` er ikke nok, fordi patch-id skjuler at main er ældre.
22. ~~**Ingen JS-fejl fra en besøgendes browser nåede Sentry.**~~ **Færdig
    5/10**, `ceo/klientfejl-til-sentry`. Se STATUS. Ruten er ny og har derfor
    **26** nye kontroller i `tests/stripe-worker.test.mjs` — bl.a. at den URL
    brugeren indtaster i `/compliance-site-check` ikke kan komme med, at et
    syvende felt giver 400, at GET giver 405, at localhost tier, og at både
    løkkedæmpning (3/min pr. fejl) og timekvoten (20/t pr. besøgende) svarer
    429. `check_net_copies.py` krævede en grund for ruten, og den har fået
    en: en fejlrapport må ikke vise en fejlmeddelelse i et værktøj.
    **Målt fund i samme opgave:** de to nye tællertests var grønne på uren
    kode og **røde i `clock_jump.mjs`**, som hopper én time pr. kald — de
    målte klokken, ikke tælleren (6 rapporter i stedet for 1, 26 i stedet for
    20), fordi `browserSentryRateLimited` er et 20-sekunders glidende vindue,
    timekvoten er `Math.floor(Date.now() / 3600000)`, og `visitorHash` salter
    med dagens dato. Rettet som i den ældre worker-test: uret pinnes til
    minut/timets begyndelse i selve løkken, så det aldrig springer baglænes.
    Samme fælde som den 2/10, der gav to røde CI-kørsler.
23. ~~**Rød CI på `main`, og konverteringen var ulæselig.**~~ **Færdig 5/10**,
   `ceo/tokenfri-konvertering`. 5/10 17:36 faldt `deploy-sites` på `plan-status`
   (STATUS **28** mod **25** linjer), så sidste deploys kørsel aldrig nåede
   `/api/results`. Samme diff gør STATUS **23** og tilføjer `GET /api/conversion`:
   kun købsintents-klik (`buy-click` + `pro-card-click`) pr. side og pr. dag, med
   egen navneliste, egen `CONVERSION_KEY_LIMIT` og egen 30/t-tæller, så den ikke
   kan gøre `/api/results` rød og ikke låner dennes nøglegrænse. Bevidst **ikke**
   med `licenses_issued`, `waitlist`, `cta-*`, `ai-cta` eller `store-click`, og
   svaret er dømt på at det hverken rummer `@`, 32 hex-tegn eller `$`+tal — en
   offentlig rute må ikke afsløre hvem, hvor meget eller med hvilken nøgle.
   **22** nye kontroller, **453/453**; mutation mod `97ef0b68` giver 404.
24. ~~**`/api/results` læser en kumulativ tæller som et vinduestal.**~~ **Færdig
    5/10**, `ceo/resultat-koerende-taeller`. `csc-count` skrives med
    `expirationTtl: 365 * 86400` (`_worker.js:3899`), så `served_scans` var
    scanninger *siden tælleren blev nulstillet* — mens `totals.runs` kun dækker
    `days`. Kommentaren på linjen sagde at et større tal end `runs` betyder at
    «klienten ikke skriver alle sine resultater». Målt live 5/10 21:0x:
    `served_scans: 50` mod `runs: 0` i 7 dage, og det er **ikke** et spor af en
    fejl — `/scan` har nul besøgende, og `/api/conversion` beviser at
    `/api/track` stadig skriver (`buy_clicks: 1` 29/9). Feltet hedder nu
    `served_scans_lifetime`, `note` siger at det ikke må sammenlignes med
    `runs`, og **2** nye kontroller (**454/454**) dømmer præcis det: røde mod
    gammel kode (**452/454**). Målt i samme kørsel: `POST /api/track` svarer
    **200** på alle **tre** domæner, så tragten er ikke død noget sted.


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

1. ~~**`/clean-copy-tool` er Pro-salgssiden, og dens fold kan ikke dømmes.**~~
   **Færdig 5/10**, `ceo/clean-copy-tool-fold`. Se opgave 18.
2. **`deskuptime.com`: 7 besøgende, 100 % bounce, 0 s opholdt tid.** Hvem:
   alle 7 på `/`. Tal: hvor mange køber. Accept: en forside der sælger uden
   at kræve scroll. Datagrund: **0 s** er ikke en lang læsning, det er en
   besøger der gik med det samme — på den eneste udgivne side der kun er én.
   Målt i Chromium 4/10 mod live: **0** JS-fejl, **0** fejlede requests,
   `scrollWidth == viewport` ved 390 og 1280, og den primære handling
   («Check a site now» → `#check`) ligger i folden ved begge bredder. Folden
   var altså ikke årsagen; 7 besøgende kan heller ikke dømme en forside.
3. ~~**Sentry for workeren.**~~ **Færdig 1/10**, `ceo/sentry-ogensynlig`.
   `site/_worker.js` sender hændelser med den offentlige envelope-protokol
   (ikke `@sentry/cloudflare`, fordi en `_worker.js` i Pages *advanced mode*
   ikke bundles), og `tools/check_sentry_setup.py` dømmer de otte regler:
   kun produktion, ingen persondata (`url`+`method` kun), ingen traces, ingen
   replay, intet auth-token, ingen source maps, rapporteringen kan ikke kaste,
   og løkker er dæmpet. Begge steps hængt i portene.
4. ~~**Ingen JS-fejl fra en besøgendes browser når Sentry.**~~ **Færdig 5/10**,
   `ceo/klientfejl-til-sentry`. Se opgave 22. Replay er stadig slået fra, så
   fejlene kommer uden skærmbillede — det er ikke længere en afvejning til dig,
   men en permanent regel.
5. ~~**`/blog/text-on-image-contrast-check` er 8 af 21 besøgende på mahope.tools,
   og alle 8 bouncede.**~~ **Færdig 5/10**, `ceo/tekstartens-egen-handling`.
   Hvem: de der lander på artiklen. Tal: hvor mange af dem kører selve
   tjekket. Accept: artiklen sender læseren ind i `/text-on-image-checker` med
   det samme problem de lige har læst om — egen handling i teksten, ikke
   banner. Datagrund: Plausible 4/10 viser **8** besøgende på bloggen mod **2**
   på værktøjet, og **100 %** mod **50 %** bounce. Baseline: `text-on-image-checker`
   har **2** besøgende. Målt i koden: artiklens **første** afsnit (grunden til at
   teksten fejler) havde **0** links til værktøjet — den eneste in-text sti lå i
   `#try-it`, altså *efter* at læseren var nået halve vejen. Nu én handling i
   begge sprog, i **første** `<section>`, på **hele ruten** (ikke `#try-it`),
   fordi den `cta-`-beacon nederst i filen kun måler klik på hele ruter.
   **Målt fejl i opgavens egen begrundelse:** «alle 8 bouncede» er ikke
   bevis for at handlingen manglede. Siden har tjekkeren *indlejret*, så en
   læser der bruger den bliver på ét sidevisning — Plausible tæller det som
   bounce, præcis som en læser der lukkede fanen. Bounce 100 % kan her altså
   ikke skelne brug fra flugt; det erfarede den næste opgave.
6. ~~**Ingen måling kan skelne «brugte værktøjet» fra «lukkede fanen».**~~
   **Færdig 5/10**, `ceo/resultat-uden-hemmelighed`. Hvem: alle brugere af de
   gratis værktøjer. Tal: hvor mange rent faktisk får et resultat. Accept: ét
   resultat pr. kørsel tælles ét sted, der kan læses *uden* `STATS_TOKEN` —
   holdt: `GET /api/results` er en udlæsning af de nøgler `/api/track` allerede
   skriver, så der er **én** tæller og ingen der kan komme i strid. Datagrund:
   `/api/stats` svarer 401 siden uge 37, så hele tragten fra opgave 20 var
   skrevet men ulæselig. Målt: **31** nye kontroller, **431/431** grøn, tre
   mutationer røde (navnelisten, stidommen, nøglegrænsen), mutation mod den
   gamle kode giver 404. Bevidst *uden* salg, købsforsøg og sidevisninger — de
   er ikke resultater, og opgave 3 (konvertering) står derfor stadig åben.
7. ~~**`/text-on-image-checker` beder om upload, før den viser noget.**~~
   **Færdig 5/10**, `ceo/verdict-i-folden`. Se STATUS. Kernen skriver nu
   `#verdict` — badge og forholdstal — fra den **samme** `sample` som `#result`,
   som første element efter overskriften; målt i Chromium 390/1280 mod den
   byggede `dist/`: `.ti-badge` **1739 → 601 px** (EN) og **1690 → 579** (DA) i
   en 664 px fold, `scrollWidth == viewport` begge steder, 0 JS-fejl. Taglinen
   gik fra 330 tegn/8 linjer til 109/3, fordi `.ti-verdict` (83 px) ikke kan
   være i en 664 px fold ovenpå en hero på 378. Ny port
   `check_verdict_first.py` dømmer rækkefølgen i markup'en og at kernen *ikke*
   måler selv; **GRØN** på ny kode, **4 fund** på den gamle, selftest **7/7** med
   fem mutationer. **Målt afvigelse:** de 6 nummererede felter ligger stadig
   *under* dommen — de er ikke flyttet, kun kommet ud af det første
   skærmbillede, så pro-kortet `$79/år` stadig ikke står over selve værktøjet.
   Baseline: `/text-on-image-checker` **2** besøgende mod artiklens **8**.
8. ~~**`/scan` beder om en URL i et felt under folden.**~~ **Færdig 5/10**,
   `ceo/scan-form-i-folden`. Hvem: de 559 interne links' læsere. Tal: hvor mange
   trykker Scan. Accept: feltet i heroen i husets knap, og et klik der fører til
   et synligt resultat. Datagrund: `/api/results` læser **0** resultater i 28
   dage på den side der fører 559 links. Målt: ny port `check_scan_fold.py` er
   GRØN på ny kode og **RØD** med **8** fund på den gamle, selftest **5/5**
   mutationer, fuld gate **169 steps** grøn.
9. **`/scan` tager kun én URL, så en virksomed med 40 sider kan ikke se sin
   egen tilstand.** Hvem: bureauer og webbureauer der leverer EAA-rapporter.
   Tal: hvor mange af dem går fra én scanning til betalt helsitet. Accept: et
   krav på flere URL'er der svarer på den samme rute, med den samme kvote-per-tid
   og den samme 5xx/429-semantik. Datagrund: pro-kortet på `/scan` lover «It
   crawls the whole site» for $79/år, men siden tager **1** side pr. kørsel, og
   `/compliance-site-check` tager **5**. Forskellen mellem gratis og betalt er
   altså lige nu to tal i en tekst, ikke i produktet.
10. **`/scan` har ingen skærmbillede-resultat at dele uden et resultat.** Hvem:
    alle der scanner. Tal: hvor mange resultater der deles videre (og kommer
    tilbage som besøg). Accept: et statisk, ærligt eksempel-resultat i folden
    der ikke sender en hændelse, så læseren ser produktet uden at købe en
    kørsel. Datagrund: `#url=`-deling virker kun *efter* en kørsel, så en læser
    der kommer fra en guide kan ikke se, hvad et resultat overhovedet er. Målt
    afvigelse: et eksempel med et fast tal går stale, så det skal genereres
    eller mærkes som et eksempel — ikke skrives som et målt resultat.

