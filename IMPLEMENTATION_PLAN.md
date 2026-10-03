# STATUS
- **Denne iteration: gradientruten er også i artiklen.** Feature-kø punkt 4 lagde
  den på de to *værktøjssider* 3/10; `/blog/text-on-image-contrast-check` er 8 af
  18 besøgende (**44 %**, bounce 100 %) og indlejrer samme kerne — så læseren måtte
  ud af døren for at få den. Begge artikler (EN/DA) har nu **An image / A
  gradient** + to stopfarver + vinkel, samme id'er og værdier som værktøjssiderne.
- **Porten dømmer nu alle fire sider, ikke kun to** (176 løfter fra 132). Felterne
  læses i **sidens egen markup** og præfikset i **sidens eget `mount()`-kald** —
  før la porten nogle felter op selv, så et `id` med en tastefejl fik en grøn dom.
  Tre mutationer i markup'en gør den rød: gradientfeltet forsvinder,
  `<option value="gradient">` forsvinder, `<label for>` forsvinder.
- **Målt:** `check_contrast_sampling` GRØN 176/4 sider; `--self-test` OK
  (161/161) på 3m52s. Gaten grøn (`build_sites` 315 sider/0 fund,
  `stripe-worker.test.mjs` 377/377, `check_inline_js` 0). **Ikke kørt:** ingen
  browser ved 390/1280 — de fire felter er samme markup som på værktøjssiderne.
- **Deploy fra sidste iteration er verificeret:** live `text-on-image-core.js` har
  **4** forekomster af `bgmode`, så `40654c3` er ude. CI grøn på `main` 3/10.
- PR-TJEK 3/10: **0** PR'er. BRANCH-TJEK 2/10. Sentry: ingen uløste fejl, SDK op.
- **Næste opgave: Feature-kø punkt 5** — artiklen har stadig ingen købsknap over
  folden. Baslinen måles i browseren, før der røres ved den.
- **❓ Til Mads:** uændret — alle 12 spørgsmål står i afsnittet nedenfor, 0 nye.

## Verificér deploy

`VERIFICÉR DEPLOY: gradientruten i artiklen og porten på alle fire sider ceo/artikel-gradient 3/10 21:3x`
Graden deployer på push, så næste iteration tjekker med ét `gh run list -L 1` og
ét kald på live `/blog/text-on-image-contrast-check/` efter `art-bgmode`.

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
5. **Artiklen der 44 % af besågene lander på, sender ingen hjem.** Hvem: de 8 af 18
   besøgende på `/blog/text-on-image-contrast-check` — de kommer fra søgning efter
   præcis det problem og går alle med 100 % bounce, mens selve værktøjet
   `/text-on-image-checker` kun har 2. Tal: købs- og værktøjsknapper i artiklen
   (baseline måles i browseren først). Accept: artiklen har **én** primær handling
   over folden, der åbner tjekkeren med læserens eget eksempel, og porten
   `check_first_action` dømmer pr. artikel (den dømmer i dag 172 sider for to-tre
   knapper i folden). Datagrund: største enkelt indgang på sitet, højeste bounce,
   og 44 % af alle besøg på én URL.
