# STATUS

- **En køber der mistede sin licensnøgle skulle skrive til Mads.** Målt 1/10:
  `/api/license/lookup` er fuldt implementeret, ratelimited og testet (5 af 5
  opslag grønne i `stripe-worker.test.mjs`), og **ingen side kaldte den** —
  `/license-lookup`, sidens hele formål, var ren tekst med «write to
  support@mahope.tools … we send the key again, usually the same day».
  Det er menneskelig support i en indtægt der skal klare sig uden. Siden har nu
  en formular der kalder endpointen, og ny port `tests/license-lookup.test.mjs`
  (14 kontroller) dømmer at et licens-endpoint har en indgang — målt rød med 12
  mod den gamle kode. Se opgave 37.
- **Hvorfor ingen port så det:** `check_stripe_ctas` dømmer at *salg* har en
  knap, og `check_buyable` at et købsklart produkt sælges. Ingen dømmer at et
  *support*-endpoint har en klient — og support er præcis den udgift missionen
  forbyder. Samme fejlform som de fund, de lukker: en påstand uden dom.
- **Ryggraden er grøn:** `python3 tools/quality_gate.py` — 113 steps (nu 114
  med `license-lookup-page`). De fire kommandoer missionen navngiver er en
  delmængde; se opgave 36 for hvorfor kun de er for få. Mål: `gh run list -L 1`
  grønnest i starten af hver iteration.
- **Et køb kunne få tolv afvisninger og en kunde der stadig ikke har sin
  nøgle.** Tak-siden genkaldte `/api/stripe/fulfillment` på 429, og den rute
  tæller selv sine forsøg — så hvert genkald gjorde det værre. Rettet, og
  `check_status_finality.py` dømmer det fra nu af. Se opgave 35.
- **Otte generatorer var døde i live — inkl. hele den betalte DPA/ROPA/privacy-
  vej.** `build_sites` skrev shell- og BugBottle-tags ind foran det *første*
  `</body>`, men generatorerne bygger den fil de downloader som en JS-streng, så
  `</body>` står midt i et `<script>`. Browseren stoppede scriptet der, og
  «Generate» gav et tomt felt. Målt 30/9 på de otte live-ruter: alle otte med
  en blok browseren afviser. Samme fejlform i `pagepass.scrub_css`, som skrev sit
  eget linjeskift ind i strengene på 4 sider. Se opgave 34.
- **Den port, der skulle have set det, læste kun kilden.** `check_inline_js`
  sagde «problems: 0» — filerne i `site/` var i orden, det var *bygget* der brød.
  Den dømmer nu begge træer, og dens selvtest bygger repoet med de to mutationer
  der lå i live. Målt før/efter på de otte: 8 brudde → 0.
- **Samme fejlform i ny form: en regel skrevet ned, ingen dom.** CEO-kø punkt 0
  rettede *de syv klienter der stod i køen*. Den tiende lå ved siden af. Næste
  batch skal derfor spørge, om en opgave nævnte et **antal** uden at liste
  filerne — antallet er ikke listen.
- **`❓ Til Mads` nederst:** `STATS_TOKEN`, `bugbottle.dev`'s domæne,
  banner-placering på 180 sider, og de to desktop-apps der stadig ringer til
  Lemon Squeezy.
- **Historie:** `docs/plan-arkiv.md` (append-only; grep i stedet for at læse hel).



## Verificér deploy

- `DEPLOY OK 2026-10-01` — begge 429-rettelser (`ceo/429-er-sendeloeende-paa-tak-siden`
  + `ceo/429-gate-tak-siden`, `70ec8c4`). Målt på indhold: `build-info.json` bærer
  præcis `70ec8c49cd52dc27a020f752d33fa0e6708292ff`, og live `/thanks` har **én**
  `x.code === 429` på sin egen linje (ikke `429 || x.code >= 500`), som kalder
  `fail((x.d && x.d.error ? x.d.error : 'Too many attempts.') + LIMITED_OUT)`.

- `VERIFICÉR DEPLOY: ceo/konkurrent-pris-grundlag 2026-10-01` — mål på indhold:
  `/blog/desktop-website-monitor-cli` har «1 year, billed annually» i
  kolonneoverskriften, `$348` i Better Stack-cellen og **ikke** `$408` nogen
  steder på de seks sider, der linkede til artiklen.

- `VERIFICÉR DEPLOY: ceo/429-kommentar-siger-modsaet 2026-10-01` — kommentar
  i `site/thanks.html`, intet kørtid. Verificér at live `/thanks` svarer 200 og
  stadig kun har ét `x.code === 429`.

- `VERIFICÉR DEPLOY: ceo/selvbetjent-noegleopslag 2026-10-01` — mål på indhold:
  1. `https://mahope.tools/build-info.json` bærer præcis merge-sha'en.
  2. `/license-lookup` har præcis ét `fetch('/api/license/lookup'` med
     `{ order_id, email }`, to `<label for>`, og **ikke** sætningen «We send the
     key again, usually the same day».
  3. Et rigtigt 200-svar på endpointet med et kvittér mails `cs_`-reference
     og den betalte adresse gengiver nøglen i browseren.

- `DEPLOY OK 2026-10-01` — otte generatorer (`ceo/generator-script-kom-til-live`,
  `8c61191`). Målt 1/10 kl. 00:0x UTC: CI-kørsel `36793625580` grøn i alle jobs,
  `build-info.json` bærer præcis `8c61191`, og alle otte live-ruter
  (`dpa-generator`, `ropa-generator`, `privacy-notice-generator`,
  `nis2-incident-generator` + de fire `-da`) svarer 200 med en inline-blok
  `node --check` accepterer. Målt på indhold, ikke på HTTP-status.

- `DEPLOY OK 2026-09-30` — reglen for forbigående fejl (`ceo/et-forbigaaende-kal`,
  `250e604`) er live: CI-kørsel `36779886917` grøn i alle jobs, og
  `build-info.json` bærer præcis `250e6043…` på begge domæner med
  **uændret** `routes_sha256` (`8367db4b…` / `81ed162d…`) — kun `tools/` var
  rørt, så intet på sitet ændrede sig, som det skulle.

- `DEPLOY OK 2026-09-30` — donationslinjen på de 17 sidste værktøjssider er
  live på alle ni målte ruter, hver med **præcis ét** `donate.stripe.com`-link:
  `json-formatter`, `nis2-check`, `nis2-gap-assessment`, `word-counter`,
  `uuid-generator` og `security-headers-check` på mahope.tools, og
  `clean-copy-api`, `url-to-markdown` og `da/url-til-markdown` på
  cleancopy.tools. Målt på indhold, ikke på HTTP-status; live bærer `df3799f`.

- `DEPLOY OK 2026-09-30` — `ceo/live-check-flake` (`a97616f`): CI's kørsel
  `36769685936` er grøn i alle jobs, og `build-info.json` på mahope.tools bærer
  præcis `a97616fc06b4affe31a98600e5b731f19da3f533` med routes_sha256
  `8367db4b…`, så live er den commit der retter prøvningen. Målt på indhold:
  `/books/` har seks `<h2 class="sub"><a>` og den publicerede CSS har
  `.book-card :is(h3, h2.sub) a { color:#111; text-decoration:none }`.

- **CEO-kø punkt 0 (29/9) er lukket og målt 30/9.** Alle fem delpunkter er
    rettet og hver er dækket af en test: `handleUrlInspect(request, url, env)`
    får `env` (`_worker.js:138/2949`) og `tests/stripe-worker.test.mjs:813-924`
    kalder endpointet, inkl. en mutation der lægger den gamle kode ind og
    forventer rød. `thanks.html` har `PENDING_OUT` til 202, så den ikke ender i
    "your payment went through". 429 er endeligt alle syv steder — de fire
    uden `/net.js` har `err.transient = !data || r.status >= 500`, som holder
    429 ude, og de viser `data.error`. AI-retry er højst ét ekstra kald.
    SSRF: `targetIsPublic()` kører på mål og hvert redirect-hop, og
    værnet afviser IPv4-mapped IPv6 (`:1130-1175`).

- `DEPLOY OK 2026-09-30` — donationslinjen på de otte generatorer er live på
  alle otte, målt på indhold og ikke på HTTP-status: `dpa-generator`,
  `ropa-generator`, `privacy-notice-generator`, `nis2-incident-generator` og
  deres `-da`-varianter har hver præcis ét `donate.stripe.com`-link.
  (**Bemærk:** de danske sider ligger på samme sti som de engelske, ikke under
  `/da/` — min første måling læste `mahope.tools/da/dpa-generator-da` og fandt
  0, hvilket så ud som en manglende linje indtil ruten blev slået op.)

- `DEPLOY OK 2026-09-30` — død CSS på klasser (`ceo/port-kan-doe-klasser`,
  `567fb26`), målt på indhold live: `.empty-state` er væk fra
  `/url-inspector/`, de fire `.rating-*`/`.tag-blue` er væk fra
  `/guides/comparison`, `.scanbox` er væk fra `/nis2-check`. `.sev-*` er
  **beholdt** med vilje — de døde kun fordi bogstavel-læseren stoppede ved
  citationstegnet i `class="sev-`; de er levende, fordi `/scan` og
  `/compliance-report` skriver dem fra `f.sev`.

## Åbne opgaver

1. ~~**Samme næste-vej på de øvrige gratis tjek.**~~ **FÆRDIG 30/9, `ceo/vej-til-betalt-otte-tjek` (66172a0).**
2. ~~**Løgnen i JSON-LD'en: tre sider siger "intet gemmes", og tre API'er gemmer et IP-hash.**~~ **FÆRDIG 30/9, `ceo/aehlige-lagrings-loefter`.**
3. ~~**En port, der finder næste side selv.**~~ **FÆRDIG 30/9, `ceo/vaerktoj-betalt-vej`.**
4. ~~**De 5 blinde værktøjssider.**~~ **FÆRDIG 30/9, `ceo/porten-kan-skelne-vilkaar` (2b1fceb+).** Alle 94 dømte værktøjssider har nu en betalt vej; de 10 undtagne står med grund i hver kørsel.
5. **Konvertering kan ikke måles uden `STATS_TOKEN`.** Hvorfor: `/api/stats` svarer 401 siden uge 37, så næsten hver linje i enhver trafikrangering er vor egen links-tælling, ikke besøg. Den nye port har samme problem og siger det i hver kørsel. Accept: `GET /api/stats` med token svarer 200. *(Blokeret på Mads — se ❓.)*
6. **`bugbottle.dev` deployes ikke.** Hvorfor: `deploy-sites.yml`-matrixen deployer kun tre domæner, så `dist/bugbottle.dev/` bygges hver kørsel og lægges ingen steder; live er 61 ruter fra en anden udgivelse. Det er derfor `traffic_status` er `partial` hver time og `reports/weekly/` mangler et helt domæne. Den nye port måler `/bugbottle-demo` og dømmer den ikke, fordi samme grund gør dom 4/7 i artikelporten umulige at dømme. Accept: enten domænet på Pages og fjernet af `UNMANAGED_DOMAINS`, eller fjernet fra `TRACKING_DOMAINS` så status bliver ærlig. *(Beslutning — se ❓.)*
7. ~~**Falsk 0 i næste dødsvarsel.**~~ **FÆRDIG 30/9, `ceo/selvklik-kan-ikke-vaere-et-besog`.**
8. ~~**Ratcheten kan ikke se en tilbagefaldet side.**~~ **FÆRDIG 30/9, `ceo/ratchet-ser-vejens-destination` + `ceo/ratchet-per-anker`.** Den kan nu se både en forsvunden destination *og* en ombytning. Se STATE.
9. ~~**`RE_CLAIM` tæller tal den ikke dømmer.**~~ **FÆRDIG 30/9, `ceo/dom-pro-og-totaltal`.** 201 → 239 dømte løfter, intet mistet målt mod den gamle port.
10. ~~**En selvtest må ikke afhænge af, hvilken side der er nået.**~~ **FÆRDIG 30/9, `ceo/selvtest-ikke-navngiver-side`.**
11. ~~**To købssider sælger en crawl, der ikke findes.**~~ **LUKKET 30/9 ved måling — løftet er sandt.**
12. ~~**Porten beder `/privacy` og `/terms` om en købsknap.**~~ **FÆRDIG 30/9** — blindliste 5 → 0.
13. ~~**Bygget sletter CSS på 22 sider.**~~ **FÆRDIG 30/9.**
14. ~~**Kun (c) tilbage: `check_ui_constants.py`.**~~ **FÆRDIG 30/9, `ceo/ui-konstanter`.**
15. ~~**Ingen port dømmer, at en sides CSS overlever bygget.**~~ **FÆRDIG 30/9, `ceo/port-der-dommer-css`.**
16. ~~**Dublet `<h2>` på 63 sider.**~~ **FÆRDIG 30/9, `ceo/relaterede-guides-to-gange`.**
17. ~~**En port skal finde fejl i CI-layout den ikke kan reproducere lokalt.**~~ **FÆRDIG 30/9 (4a0fc12).**
18. ~~**En fejlform i denne familie er stadig ubemandet: en *generator* der skriver en løgn.**~~ **FÆRDIG 30/9, `ceo/generator-loefter`.** Se arkiv.
19. ~~**En port erklærer flere filer end den læser, så gaten er rød og to commits aldrig deployer.**~~ **FÆRDIG 30/9, `ceo/porten-demper-sin-egen-rute`.** Se STATE.
20. ~~**Sjakal (`ceo/check_area_ordinals.py`) tæller løfter den ikke dømmer.**~~ **FÆRDIG 30/9, `ceo/dom-de-syv-antalsloefter`.** 7 → 14 dømte løfter, 0 uden dom. Se STATE og arkiv.
21. ~~**Produkt på de to mest besøgte sider.**~~ **FÆRDIG 30/9, `ceo/vaerktojet-foerst-over-folden`.** Værktøjet er den primære handling over foldet på `/blog/text-on-image-contrast-check` (EN+DA), de to injicerede banneren er flyttet ned og demoteret, og `check_first_action.py` dømmer folden pr. rute med destination. Se STATE.
22. **180 sider har to-tre knapper over folden.** Hvorfor: `add_top_cta_495.py` og `add_ai_cta.py` har skudt scanner- og AI-banneren ind under `</header>` på hele bloggen, så de ligger over folden på 180 af 224 sider med hero — og på mange er heroens egen primære et anker (`#content`, `#how`). Målt 30/9 af `check_first_action.py`. Accept: bannerne er enten flyttet ned i artiklen på de mest besøgte sider (dømt i `tools/first_action.json`), eller slettet fra hele bloggen så AI-CTA'en ligger ét sted pr. side. Kræver beslutning — se ❓.

23. ~~**14 formularfelter uden navn.**~~ **FÆRDIG 30/9, `ceo/formularer-med-navn`.** 14 → 0, målt på de rigtige filer. Ny port `tools/check_form_labels.py` dømmer hvert felt og læser inline-`<script>` med. Se STATE.
24. ~~**Ingen port dømmer `h1`→`h3`-spring.**~~ **FÆRDIG 30/9, `ceo/overskrifts-spring`.** 12 sider → 0, ny port `tools/check_heading_levels.py` med 13 kontroller. Se STATE.

25. ~~**44 blogartikler lister deres værktøjer to gange.**~~ **FÆRDIG 30/9,
    `ceo/vaerktojer-en-gang`.** Målt rigtigt var det 62 (44 EN + 18 DA), og de
    to lister overlappede i 36 links. Se STATE.

26. ~~**Værktøjet `/text-on-image-checker` svarer ikke på sit eget billede.**~~
    **FÆRDIG 30/9, `ceo/tekst-paa-billed`.** Se STATE.

27. ~~**Porten kan ikke dømme at værktøjet svarer på den *bedste* baggrund.**~~
     **FÆRDIG 30/9, `ceo/gradient-dommer-baggrund`.** Ny gradientcase med sort
     tekst + en mutation der springer `minC` over, målt rød på begge sider.
     Se STATE.

31. ~~**Ét netværksreset kunne erklære en sund udgivelse for brudt.**~~
    **FÆRDIG 30/9, `ceo/live-check-flake`.** `main` var rød ved start:
    kørsel `36763842986` faldt i alle tre deploys på én linje
    (`[Errno 104] Connection reset by peer` for
    `/guides/prestashop-accessibility-check`, som svarer 200 tre gange i træk
    fra samme maskine). `check_live_sitemaps.py` så hver side **én** gang;
    kun `wait_for_artifacts` havde gentagelse. Nu `fetch_resilient` gentager kun
    ved netværksfejl eller 5xx — 404 og 429 forbliver røde på første forsøg, så
    porten kan hverken gøre en fejl grøn eller trække en 429. 26 tests (var 11),
    10 mutationer alle fanget. Se arkiv.

32. ~~**`_transient` findes to gange, og de er uenige om 429.**~~
    **FÆRDIG 30/9, `ceo/et-forbigaaende-kal`.** Reglen ligger i
    `tools/transient.py` og tager begge kaldsformer (status, undtagelse);
    `check_live_sitemaps.is_transient` *er* den funktion, så en lokal
    `def` igen ville være rød. 18 kontroller i `tools/test_transient.py`,
    hvoraf fire er røde mod den gamle kode (målt i klon). Se STATE.

- `❓ Til Mads`:
  - **🟡 Skal scanner- og AI-banneren ligge over folden på 180 sider?** De blev skudt ind under overskriften på hele bloggen i en tidligere iteration. Målt 30/9 giver det **tre knapper oven på folden** pr. artikel, og på 30 af dem er knappen *oveni* et anker som «læs videre», så det værktøj artiklen handler om ikke er den primære handling. Jeg har rettet de to mest besøgte artikler. Enten flytter jeg banneren ned i artiklen på de næste mest besøgte, eller jeg sletter den fra hele bloggen, så AI-CTA'en ligger ét sted pr. side. Det er din beslutning, fordi det er en promo du har bedt om — jeg gør ikke det ene frem for det andet i det større format.
  - **🔴 `STATS_TOKEN` på workeren.** Én linje, én secret, og så kan konvertering måles i stedet for gættes. Uden den er `/api/stats` 401, og opgave 5 og 8 bygger på tal, der ikke er besøg.
  - **🔴 `bugbottle.dev` ligger på en server, vi ikke deployer.** `https://bugbottle.dev/build-info.json` svarer **404 fra `nginx`**, ikke Cloudflare, mens de tre andre domæner bærer alle samme sha. To veje: (a) domænet skal på Cloudflare Pages → opsæt `bugbottle-dev`-projektet, så tilføjer jeg domænet til matrixen og fjerner undtagelsen i samme commit; (b) domænet er ikke vores at udgive → det skal ud af `TRACKING_DOMAINS`, så `traffic_status` bliver ærlig `ok` for de tre vi faktisk deployer.
  - **🔴 To betalte desktop-apps kan ikke aktiveres.** Målt i de shippede binære: `mahope/transmute` `v0.2.1` og `mahope/deskuptime` `desktop-v0.2.7` har begge `https://api.lemonsqueezy.com/v1/licenses/activate` indbygget, og binæren sender `license_key` + `instance_name` og læser `activated`, `id`, `product_name`, `customer_email` — mens vores `/api/license/activate` kræver `{ license_key, device_id, product }`. Serveren er tolerant over for `instance_id` som alias for `device_id`; `instance_name` giver jeg ikke. Kilden ligger i private repos, og du laver selv releases.
  - **Search Console:** tilføj de fem domæner som properties (`mahope.tools`, `cleancopy.tools`, `deskuptime.com`, `bugbottle.dev`, `transmute.run`). Sitemap og robots er målt korrekte på de fire sites missionen udgiver; kun property-tilføjelsen mangler.
  - **EUComply Pro-prisen** ($79/år pr. website) er sat i Stripe, men nogen sider nævner tallet. Skal det stå på en `/pro/`-side? **Bemærk: `/pro/` findes ikke** — live er den 404, og intet i `site/` linker til den, så spørgsmålet afgør om vi bygger siden eller dropper den.
  - **Er desktop-appen stadig en del af `deskuptime-pro`?** Et betalt produkt skal kunne det, det lover.
  - **Plugin-version:** kunder på Clean Copy 1.1.0 henter ikke den rettede zip. Kræver en version bump — og det er en release, som er din.
  - **7 betalte produkter** (DPA, NIS2/DORA, NDA, EAA, report kit, template bundle, e-bøg-bundle) sælger endnu ikke, fordi filerne ikke ligger i Cloudflare KV. Uploadskrivet ligger i `mahope/paid-products`.

28. ~~**Donationen nåede kun 4 af 161 sider.**~~ **FÆRDIG 30/9,
     `ceo/tak-efter-resultat`.** De to mest besøgte værktøjssider har linjen i
     resultatet, og `check_donation_paths.py` dømmer den og de 37 øvrige tæller.
     Se STATE.

29. ~~**37 værktøjssider mangler donationslinjen.**~~ **FÆRDIG 30/9.** Alle tre
    runder er gjort: `ceo/donation-runde-1` (9 sider, 37 → 28),
    `ceo/donation-runde-2` (8 generatorer, 28 → 20) og
    `ceo/donation-runde-2-del-2` (17 sider, 20 → 3). Ratchetfilen dømmer 36
    filer; de tre sidste er undtagelser med en skrevet grund, ikke en rest:
    `compliance-report` (to `Buy EUComply Pro`-knapper i selve rapporten),
    `clean-copy-tool` (eget købsflow) og `site-icons` (CLI-side med et
    **statisk** demo-output, så `class="output"` matcher portens `RESULT_RE`
    uden at der er noget resultat). Se arkiv.

30. ~~**Død CSS på *klasser* er stadig udømt.**~~ **FÆRDIG 30/9,
    `ceo/port-kan-doe-klasser`.** Fjerde dømning i `check_built_css.py`
    («død klasse») plus 17 fund ryddet, og **«tabt regel» døde stille i gaten**
    fordi `import build_sites` fandt intet. Se STATE.

33. ~~**Priserne på konkurrenterne er en påstand uden dom.**~~
     **FÆRDIG 30/9, `ceo/konkurrent-priser`.** Alle beløb ligger i
     `tools/competitor_prices.json` med kilde-URL og `checked`-dato, og
     `tools/check_competitor_prices.py` dømmer hvert beløb ved siden af en
     konkurrent i `<title>`, `og:description`, JSON-LD, tabeller og brødtekst på
     tværs af 303 sider — 9/9 kontroller, fem mutationer alle fanget. En
     konkurrent uden offentlig pris må ikke have et tal ved siden af sig, så
     Pingdom skrives nu navnet uden pris. Alders-tjekket er en **advarsel, ikke
     en dom**: en gammel `checked` må aldrig låse gaten for alle fremtidige
      udgivelser. Se arkiv.

    33b. ~~**«1 year»-kolonnen regnede de to konkurrenter på hver sit
      grundlag.**~~ **RETTET 1/10, `ceo/konkurrent-pris-grundlag`.**
      Review-fund 29/9 (LAV): UptimeRobot Solo stod til €108, som er *årlig*
      betaling (€9 × 12), mens Better Stack stod til $408, som er *månedlig*
      betaling ($34 × 12) — årlig betaling er $29, altså $348. Begge tal var
      sande, så `check_competitor_prices` dømte dem grønne; de overdriver
      konkurrenten med $60 i en tabel der skal være troværdig netop fordi den
      er kildeført. Fejlen lå i kilden selv (`"34 x 12 = 408"`), så den var
      læst igen fra fem relaterede artikler plus `og:description`. Nu er
      `per_year` $348 — samme grundlag som €108 — og hver celle siger hvilket
      («1 year, billed annually», €9/month, $29/month). Brødteksten siger
      udtrykkeligt at €10/$34 er månedspriserne, som begge firmaer rabatterer
      ved årlig binding. Kilden må nu kun give ét årstal pr. plan, så
      `$408` kan ikke genindsættes som et år uden en bevidst kildeændring:
      to nye domme i selvtesten + en ny mutation der lægger den gamle fejl
      tilbage i kolonnen (12/12 kontroller grøn). *Følge:* de samme beløb stod
      også i `tools/stripe_catalog.json` som tilladte pris-tokens pr. købsside,
      så de to porte var uenige om, hvad der måtte stå på siden — opdateret i
      samme commit, ellers går `stripe-ctas` rød på sit eget hvidestregede
      hvidlisteproblem.

34. ~~**Otte generatorer lå døde i live, og porten der så det læste kilden.**~~
     **FÆRDIG 30/9, `ceo/generator-script-kom-til-live`.** `insert_before_end_tag`
     sætter shell- og BugBottle-tags foran det **sidste** `</head>`/`</body>`
     uden for script-, style- og kommentarblokke, og `pagepass._skip_scripts`
     lader kun `scrub_css` springe scripts over — ikke `<pre>`, fordi 20 sider
     bygger markup med `innerHTML` og ellers fik `#667` hårdkodet i stedet for
     tokenet. `check_inline_js` dømmer nu `site/` **og** `dist/`, med en
     selvtest der bygger repoet to gange med de to mutationer der lå i live, og
     gaten fik et `inline-js-selftest`-step. Målt: 8/8 sider døde i live →
     0/8 i `dist`, og `diff` mod før-rettelsen viser præcis de 8 filer og ingen
     andre. Se STATE.

35. ~~**Tak-siden genkaldte et endeligt 429 tolv gange.**~~ **FÆRDIG 1/10,
     `ceo/429-er-sendeloeende-paa-tak-siden`.** CEO-kø punkt 0 (29/9) sagde at 429
     er endelig og skal vise serverens besked, og rettede de syv klienter der
     stod i køen — `site/thanks.html` stod ikke i den. Dens ene linje var
     `if (x.code === 429 || x.code >= 500) return again(…)`, og
     `/api/stripe/fulfillment` tæller selv sine forsøg (`hits >= 30`,
     `_worker.js:3933`): tolv genkald á fire sekunder, og hvert af dem tæller i
     den tæller der gav 429. Den der ventede længst fik *færrest* forsøg
     tilbage, og serverens "Too many attempts. Try again later." blev kastet
     bort for "trying again", der ikke siger hvornår man kommer tilbage.
     Ny port `tools/check_status_finality.py` måler de **11** 429-ruter i
     `_worker.js` (dispatch → handler → 429) og dømmer hver klient der
     sammenligner med 429 på tre ting: ingen nyt kald (også via en
     mellemligende reference som `setTimeout(poll, …)`, som kun `navn(` ville
     have set som grøn), et tidspunkt eller serverens egen sætning, og 5xx
     stadig forbigående — ellers kunne dom 1 og 2 opfyldes ved at gøre alt
     endeligt. 3/3 mutationer fanget. Bevis: gaten kørt mod `8c61191:site/thanks.html`
     er **rød med netop de to domme** tak-siden bryder.
     *Målt og bevidst ikke dømt:* dommen «kalder en 429-rute uden at nævne 429».
     **287** sider kalder `/api/track` som beacon (`fetch(…).catch(…)`, intet
     svar læst) og skal *ikke* nævne 429; de fire klienter der faktisk **venter**
     på et 429-svar (`/api/report`, `/api/profile` ×2, `/api/header-check`,
     `/api/url-inspect`, `/api/clean-copy`) gør alle `err.transient = !data ||
     status >= 500`, som holder 429 ude, og viser `data.error`. Det er altså et
     navneproblem, ikke et adfærdsproblem — målt i portens egen måling. Se arkiv.


36. ~~**To test dømte det modsatte af rettelsen, så CI var rød på `main`.~~
    **FÆRDIG 1/10, `ceo/429-gate-tak-siden`.** Kørsel `36796052854` faldt i
    `thanks-page` med to domme fra 29/9, der hævdede at et 429 *skal* gentages.
    Opgave 35 gjorde 429 endeligt i `site/thanks.html`, så de to lå i konflikt —
    og de to var de forkerte, fordi CEO-kø punkt 0 og regel 8 begge siger at 429
    er endelig, og opgave 35 målte at gentagelsen var skadelig (hvert genkald
    tæller i den tæller der gav 429). Erstattet af syv domme der dømmer den
    låste adfærd og har tænder: den gamle kode i en klon giver 5 røde af 7,
    blandt andet `fetches=13` skal være 1. `thanks-page` 109/109, hele porten
    grøn (113 steps). Accept opfyldt. Se arkiv.

37. ~~**En køber der mistede sin nøgle skulle skrive til Mads.**~~ **FÆRDIG
    1/10, `ceo/selvbetjent-noegleopslag`.** Hvorfor:
    `/api/license/lookup` (`_worker.js:1365`) er fuldt bygget, ratelimited
    (10/IP/time) og dækket af 5 opslag i `stripe-worker.test.mjs`, men **nogen
    klient kaldte den**. `/license-lookup` — hvis H1 er «Find your license key» —
    havde ingen formular, kun «write to support@mahope.tools … usually the same
    day». Det er præcis den menneskelige indsats missionen kasserer, placeret
    lige i den betalte indtægt. Accept: siden har en formular der POST'er de to
    felter serveren kræver, viser nøglen + udløb + aktiveringssted, og
    `tests/license-lookup.test.mjs` (17 kontroller) dømmer at et licens-endpoint
    har en indgang — målt **15 røde mod den gamle kode** (genmålt 1/10 efter
    review af egen diff), grøn mod den nye.
    Siden blev også dømt af to eksisterende porte undervejs, begge korrekt:
    `check_license_clients` krævede den opført (den kalder `/api/license`),
    `check_donation_paths` krævede donationslinjen i resultatet.
    Målt i Chromium ved 390 og 1280 px: overflow 0, ingen JS-fejl, og de seks
    svarsformer (200, lifetime, 404, 429, 503, `<img onerror>` som nøgle) er
    hver dømt visuelt; href afvises hvis den ikke er http/https. Egen-diff-review
    1/10 fandt to CSS-fejl i den nye side — `border: 1px solid --color-border`
    (var() var tabt, så ingen ramme) og `.lookup-form .btn`, en regel der aldrig
    kunne ramme de `btn-primary`/`btn-secondary` den skrev sig til, så knappen
    aldrig blev 44 px. Begge rettet før commit; 429-teksten «the limit resets
    when the hour changes» er ikke antaget — `_worker.js:3617` tømmer tælleren på
    `Math.floor(Date.now()/3600000)`, altså hver time.
