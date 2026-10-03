# STATUS
- **CI er grøn på `main`** siden `9a1c7f7` (3/10 13:4x) — de seneste rettelser
  ligger live, og `build-info.json` bærer `9a1c7f7` på domænet.
- **Alle deploy-noter er lukkede.** Den sidste, `ceo/mal-tekstfarven`, er
  efterprøvet i rigtig Chromium mod **LIVE** (ikke `dist/`): EN giver
  `#ffffff` → «Copied» → `#000000`, DA siger «Kopieret», farveprøve og kode
  følger farvefeltet begge veje, 44 px trykflade, 0 px vandret scroll ved 1280.
- **Denne iteration: en port, der dømmer farvekoden.** `ceo/port-farvekode` —
  `check_contrast_sampling` **96 → 112** løfter: fire på de to værktøjssider
  (koden findes som en knap, den er farvefeltets værdi, den følger «Fix it»,
  prøven i knappen er den samme kode) og to pr. artikel (knappens to tekster).
  **Porten kan fejle, målt på den rigtige fil:** `hexNu` frosset → **6 røde** på
  begge sprog i begge tilstande; farveprøven i en anden farve → **4 røde**;
  farveprøven fjernet → **4 røde**. Selftest **109/109**.
  Ved gennemsyn af egen diff fandt jeg i porten selv den fejl porten jager:
  prøven blev læst i knappens *egne åbningstag* men er en `<span>` *inde i*
  knappen, så `praem` var altid `null` og det fjerde løfte blev talt uden dom
  (112 i meldingen, 108 reelt dømt). Rettet, to nye selftest-tjek sikrer det.
- **Næste opgave: `## Feature-kø` punkt 1** — mål bruterens *egen* tekst, så
  to tekstblokke på ét foto får to tal. Egne opgaver: punkter 2–3.
  Alt i «Åbne opgaver» afventer Mads.
- PR-TJEK 3/10: **0** PR'er. BRANCH-TJEK 2/10. Sentry: ingen uløste fejl, og
  SDK'en er sat op (3/10), så det er ikke en tom rapport.
- **❓ Til Mads:** uændret: `OPENROUTER_API_KEY`, `STATS_TOKEN`, `bugbottle.dev`s
  domæne, bogens betalte udgave mod **7** gratis-sider, **2** desktop-apps mod
  Lemon Squeezy, Search Console, IndexNow, livstidsprisen, `/blog/`s danske-tal.

## Verificér deploy

Ingen åbne noter. Alle tidligere er `DEPLOY OK` eller dækket af en nyere og
ligger i `docs/plan-arkiv.md`.

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

1. ~~**En port, der dømmer farvekoden.**~~ **Leveret 3/10.** Se punkt 3 i
   STATUS. Hvem: alle der bruger værktøjet; artiklen
   `/blog/text-on-image-contrast-check` er 8 af 18 besøgende (44 %, 100 % bounce).
   Tal: resultater der viser den målte kode (baseline **4 af 4** sider målt i
   browseren, **0** dømt af porten → **16** løfter). Accept: `check_contrast_sampling`
   får 4 løfter pr. værktøjsside + 2 pr. artikel med polaritet målt ved at slette
   `data-ti-hex` fra den rigtige fil og ved at føse `hexNu` — 6 røde. Datagrund: 5 af
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
