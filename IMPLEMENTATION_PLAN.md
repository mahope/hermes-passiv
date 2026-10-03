# STATUS
- **Denne iteration gav de fire frie API'er en adresse.** De svarer alle 4 med
  rigtigt JSON, men ingen side på mahope.tools nævnte dem, og MCP'en der kalder
  præcis de fire lå som `/mcp` på cleancopy.tools og 404'ede på mahope.tools.
  Ny side `/developers`, i footeren på alle 28 sprogvarianter, i sitemap og
  llms.txt. Datagrund: `passiv-mcp` er det mest klonede repo (14 d: 21 unikke
  kloninger, 2 visninger, 0 stjerner).
- **Siden løgnede om sig selv, og den farligste løgn var den jeg ikke troede.**
  3 påstande var forkerte mod `_worker.js`: den sendte `format:"text"` mens
  handleren læser `mode:'plain'`, og den skrev `passed/failed/notChecked` som
  tællere mens tællingerne hedder `passed`/`failed`/`not_checked`.
- **Den 4. viste sig at være sand 3 steder og falsk i det 4.** Mod kilden har
  `CSC_CHECKS` **7** nøgler, og det har den haft i *hvert* commit siden 25/8.
  Mod live er der **9**: `security-headers` og `meta-tags` findes i ingen
  commit, men live har også 2/10's `not_checked`/`pages_read`. Siden siger
  **9**, målt med curl 4/10 — fordi det er den læseren kalder. Se ❓.
- **Porten `check_developers_page` (5 domme, selftest 15/15) dømmer at hvert
  felt siden beder læseren sende, læses af den handler ruten peger på.** Målt
  rød på den gamle payload, grøn på den nye. Min egen krop-udtrækker brød
  undervejs; grænsen er nu næste topniveau-deklaration.
- **Review-fund 4/10 rettet (punkt 0):** noten i `first_action.json` sagde at
  `/clean-copy-tool` «ligger stadig i hovednavnen». Målt 4/10: 0 `<nav>` og 0
  forekomster i `<header>` på begge sprog — noteret de 4 rigtige steder.
- **Gaten grøn:** 84 steps. PR-TJEK 3/10: 0 PR'er. BRANCH-TJEK 2/10. Sentry:
  0 uløste fejl, SDK op. **Næste:** CEO-kø punkt 2 — DeskUptime lover «no
  phone-home», men licensen aktiveres online mod mahope.tools. ❓ uændret.

## Verificér deploy

`DEPLOY OK 4/10` for `ceo/cleancopy-koeb-handling` — hentet live: foldens
primære er `href="#check"` med teksten «Convert a page», CI grøn på `main`.

`VERIFICÉR DEPLOY: /developers + de tre løgnede påstande rettet ceo/developers-side 4/10 00:4x`
Graden deployer på push. Verificér på *indhold*: hent
`https://mahope.tools/developers` og tæl. Skal være **fire** endpoint-blokke,
og clean-copy-kommandoen skal sende `{"html":"…","mode":"markdown"}` — før
stod der `"format":"markdown"`. Siden skal sige **ni** compliance-tjek, fordi
det er dem live svarer (`checks` har 9 nøgler) — kilden siger syv, se ❓.
Linket skal også stå i mahope.tools' footer på en af de andre 27
sprogvarianter, `https://mahope.tools/llms.txt` skal have linjen, og
`https://mahope.tools/mcp` skal have **0** `npx github:mahope/passiv-mcp` og
**2** `npx @mahope/passiv-mcp` (den findes på npm: registry svarer 200,
`dist-tags.latest` 1.2.1, målt 4/10).



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
- **🔴 `site/_worker.js` er ikke hele workeren bag mahope.tools.** Målt 4/10 med
  curl: `/api/compliance-scan` svarer **9** tjek (`privacy, terms, cookie,
  imprint, accessibility, dpa, security-headers, meta-tags, hreflang`), men
  `CSC_CHECKS` i repoet har **7** nøgler — og har haft 7 siden 25/8. Live har
  også 2/10's `not_checked` og `pages_read`, så live er *nyere* end de 2 af
  de 9 vi aldrig har haft i noget commit. `/api/profile` svarer `max_score: 21`
  og de øvrige 3 felter er identiske med kilden. **Hvad jeg skal bruge fra
  dig:** en afklaring af hvad der svarer på `mahope.tools/api/*` — en Worker
  route der overskriver Pages, eller en udgivelse uden om repoet. Uden den kan
  jeg ikke vedligeholde dokumentation om API'et mod sandheden, og `_worker.js`
  i repoet er så ubrugt en kilde til at skrive om de ruter.
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
6. ~~**cleancopy.tools' forside er 7 af 9 besøgende, og de går igen.**~~ **Leveret
   4/10.** Hvem: de 7 på `/` (78 % bounce, 124 s). Tal: hvor mange har trykket
   værktøjet på forsiden. Accept: browseren viser én primær handling over folden på
   390 px, og `check_first_action`-porten får forsiden i ratchetfilen med den
   destination. Datagrund: 78 % af sitets besøg er på den ene side, og de er ikke
   dem der bruger værktøjet — de læser kun forsiden. **Målt:** foldens primære var
   `#install` **3 155 px** nede, `#check` lå **715 px** nede, og den sekundære
   «Try it in the browser» pegede *ud* på `/clean-copy-tool`. Nu peger primære på
   `#check`; ratchetet, og porten er rød på den gamle kode. Baseline: 9 besøgende,
   7 på forsiden, 78 % bounce — bounce på **én** side kan ikke bruges som dom,
   fordi én sidevisning også er en fuldført konvertering.

7. ~~**`passiv-mcp` klones 10 × mere end den ses.**~~ **Leveret 4/10.** Hvem:
   de 21 der klonaede den i 14 dage plus enhver agent der leder efter en gratis
   rute. Tal: om en kloning kan finde de fire API'er den kalder. Accept: en side
   på mahope.tools der finder alle fire med rute, metode og svarfelter — og som
   står i llms.txt, fordi det er den fil en agent faktisk læser. Datagrund: det
   er det mest klonede repo i familien (21 kloninger, 2 visninger, 0 stjerner).
   **Målt:** før stod `/mcp` kun på cleancopy.tools og 404'ede på mahope.tools;
   nu er `/developers` på mahope.tools med alle fire ruter, og porten
   `check_developers_page` er rød hvis nogen af dem forsvinder, ændrer metode
   eller får et sendt felt der ikke læses. Samtidig rettet de tre løgnede
   påstande siden startede med (se STATUS).
