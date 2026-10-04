# STATUS
- **Eksempel-resultat på `/scan` (EN + DA), 5/10.** wordpress.org målt
  **66/100**, 2 fejl, 2 advarsler med `tools/scan_example.py` — sidens egne
  scripts i headless Chromium mod lokal stub, så tallene er scannerens og
  målingen ikke tæller i `/api/results` (**0** runs, **2** buy-clicks,
  **0** pro-card-clicks). Datoen står på kortet, «scan det selv» er en
  `#url=`-link.
- **Rød CI fundet 5/10 og rettet i samme commit:** `488728f1` fejlede i
  `plan-status` — STATUS var **26** linjer mod højst 25 — så
  livslang-tæller-rettelsen er **ikke** live (live `/api/health` har stadig
  `scans: 50`). Deploy-forsøg #1 efter denne commit.
- **Ingen livslang tæller kan læses som et vinduestal.** `csc-count`,
  `wl-count` og `ai-ask-count` har `expirationTtl: 365 * 86400` og genoplades
  ved hvert skriv, så de kan kun stige. De hed `scans`/`waitlist` i
  **`/api/health`, som er offentlig**, ved siden af `recentVisits: 12`
  (to dage). Målt: samme **50** i `/api/health` og `served_scans_lifetime`.
  Alle **3** hedder nu `*_lifetime` i **7** ruter, og `weekly_report.py`
  læser præfikset uden reserve.
- **Målt fejl i porten, samme opgave:** en løs `/\*.*?\*/`-strip startede ved
  `'/*', ` i `_worker.js:750` og slugte **3.200** linjer kode, så
  `csc-count`s skrivning forsvandt. Kommentar-strippingen er forankret i
  linjens start.
- **Næste:** feature-kø 9 (`/scan` tager kun 1 URL mod pro-kortets «crawls the
  whole site») er den næste pengeopgave; feature-kø 2 (`deskuptime.com` —
  **7** besøgende, 100 % bounce, **0** s) kan ikke dømmes på 7 besøgende.

## Verificér deploy

`VERIFICÉR DEPLOY: eksempel-resultat paa /scan 5/10 00:3x
ceo/scan-eksempel-resultat` — måles på **indhold**: live `https://mahope.tools/scan`
skal have `<h2 id="example-heading">Example result</h2>` **og** `<div
class="scorecard">` med `66/100 — Grade C` **før** `<h2 id="scan-heading">`, og
`/scan-da` skal have `Eksempel på et resultat` + `66/100 — Klasse C`. Begge sider
skal have linken `href="#url=https%3A%2F%2Fwordpress.org%2F"`. HTTP 200 bruges
ikke som bevis.

`VERIFICÉR DEPLOY: kumulative taellere praefikses 4/10 23:3x
ceo/livslangt-tal-navn` — måles på **indhold**: live `https://mahope.tools/api/health`
(uden nøgle) skal have `stats.scans_lifetime` og `stats.waitlist_lifetime` og
**ikke** `stats.scans` / `stats.waitlist`, og `stats.recentVisits` skal stadig
findes ved siden af dem. Live `https://mahope.tools/api/results?days=7` skal
stadig have `served_scans_lifetime` og `totals.runs`. Live
`https://mahope.tools/`'s `track.js` skal være uændret. HTTP 200 bruges ikke.

**Sådan måles det rigtigt, efter at den har fejlet én gang:** dommen skal finde
`<header class="hero">` og *dets* `</header>`, ikke sideens første `</header>`.
`/scan` har to headere (en skip-link foran heroen), så et `split('</header>')[0]`
på hele siden erklærer en korrekt flyttet form for « stadig i `<main>` ». Samme
fælde i det andet kriterium: `#verdict`s tal («PASS 4,07:1») **beregnes i
browseren**, så et `curl` kan ikke se det — dom på `#verdict`s *plads* og på den
statiske note-tekst.

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

25. **Punkt 13 i ren kultur dømmer kun `$1`, ikke `;;`.** Hvorfor: fundet 6/10 var
   et dobbelt `;;` i `site/_worker.js:119`, rester fra en scriptet indsættelse —
   og `;;` er *gyldig* JavaScript (en tom sætning), så ingen tsc, build eller
   port kan se den. Den er rettet, men grebet `git diff | grep -nE '^\+.*\$[0-9]'`
   fanger kun `$1`, `$2`, `$0`. Accept: et script (eller en port) der dømmer
   tilføjede JS-linjer for `;;` og `^\+\s*;` kører efter hver regex-indsættelse.
   *(Målt: `;;` var på linje 119 alene, `git log -S` peger på `97ef0b68`; ingen
   port dækker `site/_worker.js` — `grep -rn "_worker.js" .github/workflows/*.yml
   tools/quality_gate.py | grep -i lint` er tom.)*


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
