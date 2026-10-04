# STATUS
- **171 sider med to-tre knapper over folden er nu 0.** `check_first_action.py`
  målte dem sig selv, og de tre generatorer — `add_top_cta_495.py`,
  `add_ai_cta.py`, `add_hero_cta.py` — skrev hver især en `btn-primary` ind i
  CTA-bannerne: **330** knapper på **187** artikler. Porten har nu et dom for
  **alle 189** sider med et banner, ikke kun de 29 ratchetede, så en ny artikel
  arver reglen uden at nogen skal huske den ind. Porten var **RØD med 330 fund**
  på den uændrede kode.
- **Bannerne ligger stadig.** De taler bare kun en gang, som det sekundære de
  er — forenligt med alle tre svar i ❓, så Mads' beslutning er ikke brugt op.
  Bygget `dist/`: `btn-primary` i banner **315 → 0**.
- **Fem artikler havde ingen egen handling** — banneren var deres eneste
  primære. De har nu `#content`/`#indhold` som `hero-cta` (185 søskendesiders
  mønster, `id` på artiklens første sektion) og er ratchetede. Sider med nul
  primær: **6 → 11 → 6**. Playwright 390 + 1280 på de fem: **0 px** scroll.
  Selftest **20/20**, fuld gate **159 steps grøn**.
- **De 6 tilbage er målt, ikke gættet:** `compliance-ai` ×2 (noindex,
  assistanten er slukket — se ❓), `books/compliance-bundle` (`btn-free` lige
  under folden), `downloads` (`pip install` er første `<section>` lige under),
  `books/index` (bundle-kortet under folden), `url-inspector` (`#url-input`
  ligger 2 px under folden). **PR-TJEK 4/10:** 0 PR'er. **BRANCH-TJEK 4/10:**
  ingen remote-grene over 14 dage.

## Verificér deploy

`DEPLOY OK 4/10` for `ceo/pricing-i-footer` — målt på **indhold** 09:2x:
`https://mahope.tools/` har **23** links i `<footer class="site-footer">` og
præcis **1** `/pricing`; `https://mahope.tools/da/` har **23** og præcis **1**
`/da/pricing`. Det er dom 6 i `tools/check_pricing_page.py`, som allerede læste
samme adresse i den byggede footer. HTTP 200 blev ikke brugt som bevis.

`VERIFICÉR DEPLOY: bannerne på alle 189 artikler er sekundære, og de fem
artikler uden egen handling har fået en ceo/banner-secondary 4/10 09:5x` — mål
på **indhold**, ikke HTTP 200: hent `https://mahope.tools/blog/developer-text-tools`,
`/blog/free-website-compliance-checker`, `/blog/site-health-github-actions`,
`/da/blog/gratis-compliance-tjek-hjemmeside` og
`/da/blog/site-health-github-actions-stak`. Kriteriet er: **1** `btn-primary` i
`<header class="hero">` pr. side (`Start Reading` ×3, `Læs guiden` ×2), **0**
`btn-primary` i hvert `<div class="blog-tool-cta">`, og **1** matchende `id`
(`content`/`indhold`) på hver side. Tæll også `dist/mahope.tools/blog/*.html`:
summen af `btn-primary` i bannerne skal være **0**. Deploy sker ved push til
`main`.

`VERIFICÉR DEPLOY: /free-tools, /blog/ og /da/blog/ får én handling over folden
ceo/hub-fold-handling 4/10 08:40` — mål på **indhold**: hent `/free-tools`,
`/da/free-tools`, `/blog/`, `/da/blog/` og `/free-downloads` og tæl
`btn-primary` i `<header class="hero">`. Kriteriet er **1** pr. side, og `href`
skal være `#gdpr-heading` ×2, `#accessibility-eaa`, `#tilg-ngelighed-eaa` og
`#tpl-heading`. Deploy sker ved push til `main`.

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
   *(Blokeret på Mads — se ❓.)*
4. **`bugbottle.dev` deployes ikke.** Hvorfor: `deploy-sites.yml`-matrixen
   deployer kun tre domæner. **2/10 er følgen målt og lukket:** de fire
   BugBottle-guider ligger på `mahope.tools`, så `/blog/` har ingen døde links;
   domænets egen forside ligger stadig i `UNMANAGED_DOMAINS`. Accept: domænet på
   Pages og fjernet af `UNMANAGED_DOMAINS`, eller fjernet fra `TRACKING_DOMAINS`.
   *(Beslutning — se ❓.)*
5. ~~**171 sider har to-tre knapper over folden.**~~ **Færdig 4/10**,
    `ceo/banner-secondary`. `add_top_cta_495.py`, `add_ai_cta.py` og
    `add_hero_cta.py` skrev hver især en `btn-primary` ind i CTA-bannerne —
    **330** knapper på **187** artikler. Nu er de `btn-secondary`, alle tre
    generatorer er rettet i samme diff, og `check_first_action.py` dømmer
    bannerreglen på **alle 189** sider med banner. Målt **171 → 0**. Fem
    artikler der kun *havde* banneren som handling har fået deres egen. ❓ om
    bannerens placering står uændret — reglen er skrevet, så den er forenlig
    med alle tre svar.
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

## ❓ Til Mads

- **🔴 `OPENROUTER_API_KEY` mangler på workeren — assistenten er stadig slukket.**
  Sagen siger at assistenten er slukket og byder på scanner, erklæringsgenerator
  og de tre bøger, og begge ruter er ude af sitemap og `llms.txt`. **Når du sætter
  nøglen:** fjern `<meta name="robots" content="noindex,follow">` fra
  `site/compliance-ai.html` + `site/da/compliance-ai.html`. **Banneren på de 187
  artikler følger samme nøgle:** sæt `"available": true` i `tools/ai_cta.json`,
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

1. **De 6 sider med nul handling over folden.** Hvem: læseren på
   `books/index`, `books/compliance-bundle`, `downloads` og `url-inspector` —
   de fire er målt enkeltvis i STATUS, og deres primære ligger 2 px under
   folden eller i et kort. Tal: hvor mange læser folden og går videre.
   Accept: ratchetede `hero-cta` på de fire + selftest rød på den gamle kode.
   Datagrund: `/downloads` og `/books/*` er de eneste sider i familien hvor
   læseren skal *finde* filen i stedet for at trykke på den.
2. **Artiklen der 8 af 21 besøgende lander på har ingen købsknap i artiklen.**
   Hvem: de 8 på `/blog/text-on-image-contrast-check` (100 % bounce, 28 d).
   Tal: hvor mange går fra artiklen til `/text-on-image-checker` og videre til
   et køb. Accept: ét købslink i artiklen derhen, dømt af `check_stripe_ctas`.
   Datagrund: den er destinationen for 8 af 21 besøgende på mahope.tools, og
   `/pricing` ligger nu i footeren på alle 270 sider — vejen findes, men der er
   ingen grund til at gå den.
3. **`cleancopy.tools` er 11 af 13 besøgende på én side.** Hvem: de 11 på `/`
   (73 % bounce, 86 s). Tal: hvor mange bruger selve værktøjet i stedet for at
   læse om det. Accept: en ærlig forskel gratis/Pro i folden på 390 px.
   Datagrund: 85 % af sitets besøg er på forsiden, og `/clean-copy-tool` får
   2. Baseline efter `ceo/forsidens-handling`: forsideens primære peger på
   `#check`. Bounce på én side kan ikke bruges som dom.
4. **`deskuptime.com`: 7 besøgende, 100 % bounce, 0 s opholdt tid.** Hvem:
   alle 7 på `/`. Tal: hvor mange køber. Accept: en forside der sælger uden
   at kræve scroll. Datagrund: **0 s** er ikke en lang læsning, det er en
   besøger der gik med det samme — på den eneste udgivne side der kun er én.
   Skal måles i browseren før der skrives kode.
5. **Sentry.** Hvem: alle brugere. Tal: hvor mange fejl rammer en købsvej.
   Accept: SDK kun i produktion, `sendDefaultPii: false`,
   `tracesSampleRate` 0.1, ingen Replay, ingen auth-token, porten rød hvis
   nogen af det mangler. Datagrund: snapshottet siger «ingen uløste fejl», og
   det kan også betyde at intet sendes — det er målt ved at søge efter
   `Sentry.init`.
