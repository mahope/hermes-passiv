# STATUS
- **CI er grøn på `main`** siden `0016555` (3/10 15:1x) — de 3 commits porten
  holdt tilbage ligger nu live; `build-info.json` bærer `0016555` på domænet.
- **Alle 3 åbne deploy-noter er lukkede, målt i rigtig Chromium 1243 mod LIVE**
  (ikke `dist/`): `data-ti-demo` står før kappen på **alle 4** sider og forsvinder
  ved upload; `data-ti-delta` giver `1.10|3.07` på EN og `1,10|3,07` på DA, og på
  DA flytter «find det bedste sted» den til `3,07|19,64` med `data-ti-moved="1"`;
  `/thanks?lang=constructor` giver `lang="en"`, engelsk faneblad og **0**
  «undefined» i DOM'en (den ene forekomst er kernens egen forklaring i en
  kommentar). 0 px vandret scroll ved 390 og 1280.
- **Denne iteration: farvekoden.** `ceo/mal-tekstfarven` — resultatet viser den
  målte tekstfarve som `#rrggbb` i en knap der kopierer den. Baseline **0 af 4**
  sider: kernen skrev «I changed the text color to #1a1a1a» i en sætning, så
  bruteren skulle selv finde farvefeltet og skrive koden af i Figma.
  Målt i Chromium på den **byggede** side, EN + DA × værktøj + artikel:
  koden følger farvefeltet, udklipsholderen fik `#ffffff` → `#000000` efter «Fix
  it», knappen melder «Kopieret» på dansk, 44 px trykflade, 0 px vandret scroll.
  Gaten grøn: missionens 4 kommandoer + `check_contrast_sampling` **96** løfter +
  `check_owned_selectors` + `check_plan_status`.
- **Næste opgave: `## Feature-kø` punkt 1** (en port, der dømmer farvekoden).
  Egne opgaver: punkter 2–4. Alt i «Åbne opgaver» afventer Mads.
- PR-TJEK 3/10: **0** PR'er. BRANCH-TJEK 2/10. Sentry: ingen uløste fejl, og
  SDK'en er sat op (3/10), så det er ikke en tom rapport.
- **❓ Til Mads:** uændret: `OPENROUTER_API_KEY`, `STATS_TOKEN`, `bugbottle.dev`s
  domæne, bogens betalte udgave mod **7** gratis-sider, **2** desktop-apps mod
  Lemon Squeezy, Search Console, IndexNow, livstidsprisen, `/blog/`s danske-tal.

## Verificér deploy

- `ceo/mal-tekstfarven` **VERIFICÉR DEPLOY: ceo/mal-tekstfarven 2026-10-03
  16:2x.** Live `https://mahope.tools/text-on-image-checker`: upload et todelt
  billede → under tallet skal stå en pille med farveprøve og `#ffffff`; tryk på
  den → den skal sige `Copied`, og `#ffffff` skal ligge i udklipsholderen; tryk
  «Fix it» → koden skal blive `#000000` og følge farvefeltet. Samme på
  `/text-on-image-checker-da` (på dansk: «Kopiér den målte tekstfarve» /
  «Kopieret») og på de to artikler, hvor knappen ligger i `#art-result`.

- ~~`ceo/foer-til-nu`~~ **DEPLOY OK 3/10.** Målt på live: `#result` får præcis ét
  `data-ti-delta`, hvis **første** tal er det der stod da knappen blev trykket og
  andet er det på skærmen nu — `1.10|3.07` på EN, `1,10|3,07` på DA. Efter «find
  det bedste sted» forsvinder linjen på EN (målingen flyttede sig ikke) og skriver
  `3,07|19,64` med `data-ti-moved="1"` på DA.

- ~~`ceo/demo-billede-er-ikke-dit`~~ **DEPLOY OK 3/10.** Målt på live: præcis ét
  `data-ti-demo` med «Example image, not yours…» / «Eksempelbillede, ikke dit…»
  **før** badge'en på alle 4 sider, og det er væk efter upload. Live-kernen
  (`/text-on-image-core.js`) bærer de 4 nye nøgler.

- ~~`ceo/tak-side-sprognoegle`~~ **DEPLOY OK 3/10.** `?lang=constructor` giver
  `<html lang="en">` og «Thanks for your purchase | Mahope tools».

- Alle tidligere noter er `DEPLOY OK` eller dækket af en nyere og ligger i
  `docs/plan-arkiv.md`.

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
5. **172 sider har to-tre knapper over folden.** Hvorfor:
   `add_top_cta_495.py` og `add_ai_cta.py` har skudt scanner- og AI-banneren ind
   under `</header>`. **2/10 er de 10 mest besøgte rettet** (3 → 1 `btn-primary` i
   folden, ratchet 4 → 12 dømte sider), så 172 står tilbage. Accept: bannerne er
   flyttet ned i artiklen på de mest besøgte sider, eller slettet fra hele bloggen.
   Kræver beslutning — se ❓.
6. **Bogen har ingen DA-udgave, og læsevisningen gør det tydeligt.** Hvorfor: de
   seks bøger er på engelsk. Målt 2/10: der findes **ingen** `/da/books/*`-ruter,
   så bogsiders hreflang har intet dansk par. Accept: enten en DA-udgave af de to
   vigtigste som EPUB i `ebook/`, eller en synlig dansk note på bogside-ruterne.
   Kræver beslutning — se ❓.
7. **En sitemap-rute må ikke have en død eneste handling.** Hvorfor: porten
   dømmer kun de to ruter i `tools/unavailable_routes.json`. Accept: porten
   finder den, hvis den skrives i manifestet. *(Kun relevant når vi tilføjer flere
   sådanne sider — ikke en opgave i sig selv.)*

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
- **Search Console:** tilføj de fem domæner som properties (`mahope.tools`,
  `cleancopy.tools`, `deskuptime.com`, `bugbottle.dev`, `transmute.run`).
  Sitemap og robots er målt korrekte på de fire sites missionen udgiver.
- **Plugin-version:** kunder på Clean Copy 1.1.0 henter ikke den rettede zip.
  Kræver en version bump — og det er en release, som er din. `ceo/hub-readme-note`
  på origin er forældet (kun en plan-note fra 26/9) og ligger der, indtil du siger
  til.

## Feature-kø

Prioriteret efter hvor tæt den er på penge. Baseline for hvert tal er målt 3/10
på den **byggede** side; tallene er ikke vores egen trafik.

1. **En port, der dømmer farvekoden.** Hvem: alle der bruger værktøjet; artiklen
   `/blog/text-on-image-contrast-check` er 8 af 18 besøgende (44 %, 100 % bounce).
   Tal: resultater der viser den målte kode (baseline **4 af 4** sider målt i
   browseren, **0** dømt af porten). Accept: `check_contrast_sampling` får 3
   løfter — koden findes, den er farvefeltets værdi, og den følger «Fix it» — med
   polaritet målt ved at slette `data-ti-hex` fra den rigtige fil. Datagrund: 5 af
   de 6 seneste commits hang på dette ene værktøj, og intet i gaten vidste at
   koden findes.
2. **Mål bruterens egen tekst, ikke kun billedets.** Hvem: designere med to
   overlejrende tekstblokke på ét foto — det er det vanligste reelle tilfælde.
   Tal: målinger pr. session (baseline **1** pr. upload). Accept: bruteren kan
   lægge to tekster og få to tal, og nedlægningen skriver dem med i PNG'en.
   Datagrund: kernen kender `sampleContrast()` pr. tekstboks, men der er ingen
   vej til to; en designér med et billede og to overskrifter får i dag det
   sidste tal.
3. **Vis hvor på billedet fejlen sidder.** Hvem: bureauer der gennemgår en
   kundes fotos. Tal: downloads med markering (baseline **0**). Accept: den
   hentede PNG får et felt, der rammer det værste område under teksten, og det er
   et *andet* valg end den rettede grafik, så de to ikke blandes sammen.
   Datagrund: bruteren ser et tal på 1,10:1 og skal selv gætte hvorfor; kernen
   kender allerede de pixels den målte.
4. **Et gratis værktøj mere på en side der sælger.** Hvem: læsere af de 189
   guides, der ikke kan bruge en farvekontrast-måler. Tal: købsknapper pr. artikel
   (baseline **1** pr. artikel, porten dømmer det). Accept: ét værktøj der løser
   *tekst på mørk baggrund* (ikke kun tekst på billede) med samme kerne, så der
   er to ruter ind til den samme måling. Datagrund: porten `check_first_action`
   måler 172 sider med to-tre knapper i folden, så et nyt værktøj skal komme med
   ét klik og ikke to.
