# STATUS
- **Denne iteration: en finger kan trække teksten.** Målt i Chromium 153 ved
  390 px: `touchstart` flyttede teksten ét sted, seks `touchmove` ændrede
  *intet* — så «(or drag)» / «(eller træk)» på alle fire sider var sand på en
  mus og falsk på en telefon. Samme måling: `touchstart`s `preventDefault()`
  låste scrolling med fingeren oven på billedet, så man kunne heller ikke bare
  læse videre som man plejer.
- **Nu:** tryk flytter teksten som før · **vandret** fingerstræk flytter den med
  fingeren (og må så gå hvor som helst bagefter) · **lodret** stræk lader siden
  scroll(e), fordi det er præcis den bevægelse en læser gør for at komme videre.
  Tre lyttere i kernen; intet markup, ingen ny knap, ingen JS-hængsel.
- **Verificeret i browseren** på artiklen *og* `/text-on-image-checker` ved
  390 px: tryk JA, træk JA, scroll fra billedet 0 → 301 px (før låst).
  `scan-clients` **517/517** med fire nye domme; polaritetsdommen kører kernen
  fra `HEAD` og bliver rød på den. Gaten grøn: build 315 sider/0 fund, seo 0,
  stripe 377/377, inline-js 0. Skærmbilleder 390 + 1280 i `/tmp/ui-touch/`.
- **Deploy fra sidste iteration er verificeret:** CI grøn på `main` 3/10, og den
  live artikel har gradientruten (`art-bgmode` × 2) → `DEPLOY OK 3/10`.
- PR-TJEK 3/10: 0 PR'er. BRANCH-TJEK 2/10. Sentry: ingen uløste fejl, SDK op.
- **Næste opgave: Feature-kø 6** — mål folden på cleancopy.tools i browseren.
- **❓ Til Mads:** uændret — alle 12 spørgsmål står i afsnittet nedenfor, 0 nye.

## Verificér deploy

`VERIFICÉR DEPLOY: finger-træk i kontrastkernen ceo/finger-traek 3/10 23:0x`
Graden deployer på push. Verificér på *indhold*, ikke på HTTP: hent
`https://mahope.tools/text-on-image-core.js` og tæl `touchmove`. Skal være 2
(én definition + ét `addEventListener`) — før var der 0. `DEPLOY OK 3/10` for
`ceo/artikel-gradient`: CI grøn, live artiklen har `art-bgmode` × 2.

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

Prioriteret efter hvor tæt den er på penge. Baseline for hvert tal er målt på den
**byggede** side; tallene er ikke vores egen trafik. Punkt 1–4 er leveret og står
i `docs/plan-arkiv.md`.

1. ~~**En port, der dømmer farvekoden.**~~ Leveret 3/10 — `d051da8`.
2. ~~**Mål bruterens egen tekst, ikke kun billedets.**~~ Leveret 3/10 — `d4d0266`.
3. ~~**Vis hvor på billedet fejlen sidder.**~~ Leveret 3/10 — `0f9dd27`.
4. ~~**Et gratis værktøj mere på en side der sælger.**~~ Leveret 3/10 i to
   commits: `b8ca1ba` lagde gradientruten på de to værktøjssider, denne
   iteration lagde den i **artiklerne**. Ikke en ny side: `/contrast-checker`
   tager allerede to flade farver, så en «mørk baggrund»-side ville været en tynd
   dublet. Den reelle revne lå mellem flade farver og foto — en `linear-gradient`,
   som man ikke kan uploade.
5. ~~**Artiklen der 44 % af besøgene lander på, sender ingen hjem.**~~ **Leveret
   3/10, men en anden fejl end den antaget.** Premissen holdt ikke: foldens
   primære handling har været `#try-it` siden 2/10, kernen måler sit
   eksempelbillede ved sidevisning (`b96b6bc`), og `#report` har købsknappen.
   Den **målebare** fejl var en anden: på en telefon kunne læseren ikke flytte
   teksten, kun trykke. Baseline: 0 af 6 `touchmove` flyttede noget. Nu: træk på
   vandret finger flytter den med fingeren — målt i Chromium 153 ved 390 px på
   begge sider. Bounce 100 % på én side kan ikke bruges som dom: én sidevisning
   er også en *fuldført* tekstplacering, og det kan vi ikke måle.
6. **cleancopy.tools' forside er 7 af 9 besøgende, og de går igen.** Hvem: de 7
   på `/` (78 % bounce, 124 s). Tal: hvor mange har trykket værktøjet på forsiden.
   Accept: browseren viser én primær handling over folden på 390 px, og
   `check_first_action`-porten får forsiden i ratchetfilen med den destination.
   Datagrund: 78 % af sitets besøg er på den ene side, og de er ikke dem der
   bruger værktøjet — de læser kun forsiden.
7. **`passiv-mcp` klones 10 × mere end den ses.** 14 dage: 21 unikke kloninger,
   2 visninger, 0 stjerner. Tal: om en kloning fører til et kald på
   `mahope.tools`. Accept: repoet har en README der siger hvad MCP'en gør, og
   en side på mahope.tools der linker til den — så en kloning kan finde vej
   hjem. Datagrund: det er det mest klonede repo i familien.
