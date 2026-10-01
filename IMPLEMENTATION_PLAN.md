# STATUS

- **AI-siden er død for alle besøgende.** Målt 1/10: `POST /api/compliance-ai`
  svarer **503** «AI service not configured», fordi `OPENROUTER_API_KEY` mangler
  på workeren (`_worker.js:733`). Klienten håndterer 503 pænt, så intet fejler
  hårdt — men funktionen er publiceret og gør intet. Én secret, se ❓.
- **Købsvejen havde 2 huller, begge rettet 1/10:** en tabt licensnøgle krævede
  en mail til Mads (nu `ceo/selvbetjent-noegleopslag`), og `/api/checkout`
  svarede med Clean Copy Pro's link for ethvert produkt den ikke genkendte
  (`ceo/checkout-ruten-kan-vaere-forskrevet`).
- **Det der lå i live, var *bygget*, ikke skrevet** — 3 gange samme uge: 8
  generatorer døde i browseren, 37 sider uden donationslinje, 44 artikler med
  dobbelt værktøjsliste. `check_inline_js` sagde «problems: 0» fordi den kun
  læste `site/`; den dømmer nu begge træer.
- **En regel skrevet ned uden en dom der kan fejle, er den dyre fejlform:** CEO-kø
  punkt 0 rettede *sisyv* klienter og den tiende lå ved siden af, og opgave 42s
  eget acceptkriterium gav 0 linjer for enhver plan (arkivet). Næste batch skal
  spørge, om en opgave nævner et **antal** uden at liste filerne.
- **Rygraden er grøn:** `python3 tools/quality_gate.py` — 120 steps, hvoraf
  `check_plan_status` er ny. Vores egne priser er målt rene 1/10: alle 15
  `buy.stripe.com`-links matcher kontrakten, alle 84 købsknapper er dømt mod
  `tools/stripe_catalog.json`, nul afviger (`ceo/egen-pris-port`).
- **❓ Til Mads:** `OPENROUTER_API_KEY`, `STATS_TOKEN`, `bugbottle.dev`s domæne,
  banner-placering på 180 sider, de 2 desktop-apps der ringer til Lemon
  Squeezy, Search Console. **Historie:** `docs/plan-arkiv.md` (append-only —
  grep i stedet for at læse hel).

## Verificér deploy

- `DEPLOY OK 2026-10-01` — `ceo/perioden-ved-prisen` (`00817f5`), målt på
  **indhold** mod live der bærer præcis `00817f5` på alle 3 deployede domæner
  (`mahope.tools` `8367db4b`, `cleancopy.tools` `81ed162d`, `deskuptime.com`
  `db653dcb`): `/paid-templates` og `/da/paid-templates` har hver **7**
  `<p class="pt-price">` med «once»/«én gang» ($59, $49, $29, $39, $69, $149,
  $29 — alle 7 betalte produkter), `/` og `/da/` på deskuptime.com siger «Buy
  DeskUptime Pro — 19 USD once»/«Køb DeskUptime Pro — 19 USD én gang», og
  `/blog/desktop-website-monitor-cli` siger «Buy DeskUptime Pro — 19 USD once».
  *Ikke* efterprøvet: punkt om 14 `pt-price` i noten var talt på den rå
  greptælling, som også rammer CSS-vælgeren og JS-skabelonen på hver side;
  de 14 *viste* pristag er der 7 pr. side, hvilket er de 7 produkter.

- `VERIFICÉR DEPLOY: planen som arbejdskø (ny port + path-filter) ceo/plan-status-port 2026-10-01`
  — kun `tools/`, `.github/` og planen, intet på sitet. Live `build-info.json`
  skal bære merge-sha'en på de 3 deployede domæner med **uændret**
  `routes_sha256` (`8367db4b` / `81ed162d` / `db653dcb`), og
  `tools/quality_gate.py` skal have 120 steps.

- `DEPLOY OK 2026-10-01` — `ceo/egen-pris-port` (kun `tools/`, intet på sitet):
  live `build-info.json` bærer præcis `fb8b7b5` med uændret `routes_sha256`
  (`8367db4b…`), altså den udgivelse der indeholder porten, og ingen rute ændrede sig.

- `DEPLOY OK 2026-10-01` — fem ventende noter målt på indhold mod live `04288fc`
  (`build-info.json` bærer præcis merge-sha'en, så *alle* fem er på én gang):
  1. **`ceo/ai-svaret-kan-koere-script` (`04288fc`)** — live `/compliance-ai` og
     `/da/compliance-ai` har begge `.replace(/&/g, '&amp;')` som **første** kæde
     i `formatAnswer` (tegn 458 i den udskrevne streng, og der er ingen bold-
     udskiftning før den). Skærmbilleder bevidst ikke taget: ingen markup eller
     CSS ændrer sig, så et billede ville dømme layout og ikke escaping.
  2. **`ceo/checkout-ruten-kan-vaere-forskrevet` (`22a6d02`)** —
     `GET /api/checkout?product=deskuptime-pro` svarer 200 med
     `"product":"deskuptime-pro"`, `price_usd: 19`, `billing: "once"` og
     DeskUptimes link `https://buy.stripe.com/7sY9AS9eX3Iu418fJ5bMQ01`.
     `?product=eucomply-pro` og `?product=` svarer begge **400** med
     «Unknown or missing product. Use one of: clean-copy-pro, deskuptime-pro,
     page-profile-pro.» — ingen af dem har et købslink i kroppen.
  3. **`ceo/konkurrent-pris-grundlag` (`a4985b0`)** — live
     `/blog/desktop-website-monitor-cli` har «1 year, billed annually» to gange,
     `$348` syv gange og **`$408` nul gange**. Begge tal står i
     `tools/competitor_prices.json` med kilde-URL og `checked`-dato.
  4. **`ceo/429-kommentar-siger-modsaet` (`3ed3b1e`)** — live `/thanks` svarer
     200 og har **én** `x.code === 429` i *kode*, på sin egen linje og uden for
     `again()`. De to øvrige forekomster er kommentarer: linje 90 **citerer**
     den gamle linje ordret, som dokumentation af rettelsen, og linje 251 er
     forklaringen til begrænsningen. Den gamle form
     `429 || x.code >= 500` findes kun i den citerende kommentar.
  5. **`ceo/selvbetjent-noegleopslag`** — live `/license-lookup` har præcis ét
     `fetch('/api/license/lookup` med `{ order_id, email }`, to `<label for>`
     og **ikke** sætningen «We send the key again, usually the same day».
     *Ikke efterprøvet:* punkt 3 i noten kræver et rigtigt 200-svar med en
     kvitters `cs_`-reference, og det kan ikke fremstilles uden et køb.

- `DEPLOY OK 2026-10-01` — begge 429-rettelser (`ceo/429-er-sendeloeende-paa-tak-siden`
  + `ceo/429-gate-tak-siden`, `70ec8c4`). Målt på indhold: `build-info.json` bærer
  præcis `70ec8c49cd52dc27a020f752d33fa0e6708292ff`, og live `/thanks` har **én**
  `x.code === 429` på sin egen linje (ikke `429 || x.code >= 500`), som kalder
  `fail((x.d && x.d.error ? x.d.error : 'Too many attempts.') + LIMITED_OUT)`.

- `DEPLOY OK 2026-10-01` — `ceo/konkurrent-pris-grundlag` og
  `ceo/429-kommentar-siger-modsaet` er begge dømt ovenfor i samme måling mod
  live `04288fc`.

- `DEPLOY OK 2026-10-01` — `ceo/selvbetjent-noegleopslag` er dømt ovenfor i
  samme måling mod live `04288fc` (indhold: ét `fetch`, to labels, ingen
  support-sætning; ikke efterprøvet: et rigtigt købs-svar).

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
  - **🔴 `OPENROUTER_API_KEY` mangler på workeren — AI-siden er død for alle.**
    Målt 1/10: `POST /api/compliance-ai` svarer **503** «AI service not
    configured» (`_worker.js:733` læser `env.OPENROUTER_API_KEY`). Klienten
    håndterer det pænt, så intet er brudt — men `/compliance-ai` er en
    publiceret funktion, som artikler på både EN og DA linker til, og den gør
    intet. En secret på workeren. **Alternativ:** hvis AI'en ikke skal være
    permanent, skal siden sige at funktionen er i beta og ikke lover et svar.
  - **🟡 Skal scanner- og AI-banneren ligge over folden på 180 sider?** De blev skudt ind under overskriften på hele bloggen i en tidligere iteration. Målt 30/9 giver det **tre knapper oven på folden** pr. artikel, og på 30 af dem er knappen *oveni* et anker som «læs videre», så det værktøj artiklen handler om ikke er den primære handling. Jeg har rettet de to mest besøgte artikler. Enten flytter jeg banneren ned i artiklen på de næste mest besøgte, eller jeg sletter den fra hele bloggen, så AI-CTA'en ligger ét sted pr. side. Det er din beslutning, fordi det er en promo du har bedt om — jeg gør ikke det ene frem for det andet i det større format.
  - **🔴 `STATS_TOKEN` på workeren.** Én linje, én secret, og så kan konvertering måles i stedet for gættes. Uden den er `/api/stats` 401, og opgave 5 og 8 bygger på tal, der ikke er besøg.
  - **🔴 `bugbottle.dev` ligger på en server, vi ikke deployer.** `https://bugbottle.dev/build-info.json` svarer **404 fra `nginx`**, ikke Cloudflare, mens de tre andre domæner bærer alle samme sha. To veje: (a) domænet skal på Cloudflare Pages → opsæt `bugbottle-dev`-projektet, så tilføjer jeg domænet til matrixen og fjerner undtagelsen i samme commit; (b) domænet er ikke vores at udgive → det skal ud af `TRACKING_DOMAINS`, så `traffic_status` bliver ærlig `ok` for de tre vi faktisk deployer.
  - **🔴 To betalte desktop-apps kan ikke aktiveres.** Målt i de shippede binære: `mahope/transmute` `v0.2.1` og `mahope/deskuptime` `desktop-v0.2.7` har begge `https://api.lemonsqueezy.com/v1/licenses/activate` indbygget, og binæren sender `license_key` + `instance_name` og læser `activated`, `id`, `product_name`, `customer_email` — mens vores `/api/license/activate` kræver `{ license_key, device_id, product }`. Serveren er tolerant over for `instance_id` som alias for `device_id`; `instance_name` giver jeg ikke. Kilden ligger i private repos, og du laver selv releases.
  - **Search Console:** tilføj de fem domæner som properties (`mahope.tools`, `cleancopy.tools`, `deskuptime.com`, `bugbottle.dev`, `transmute.run`). Sitemap og robots er målt korrekte på de fire sites missionen udgiver; kun property-tilføjelsen mangler.
  - ~~**EUComply Pro-prisen** ($79/år pr. website) er sat i Stripe, men nogen
    sider nævner tallet.~~ **FORÆLDET 1/10 ved måling.** Den er nævnt 35+ steder:
    forside-knappen siger «Buy EUComply Pro — $79/year per website» (EN + DA),
    `/compliance-report` har pris-tagg, købsknap **og** en «Free vs Pro»-tabel med
    «$79/year per website» (EN + DA), og 38 sider skriver det i brødteksten eller
    i en knap (55 forekomster i alt). Alle **84** købsknapper i `site/` er dømt
    mod `tools/stripe_catalog.json`: 70 af dem har prisen i knippeteksten og
    **nul** har et andet tal end katalogens. De 14 der ikke har den i teksten, er
    alle på `/paid-templates` (EN + DA), og de har `<p class="pt-price">` lige
    ovenfor knappen i samme `.pt-foot` — så salgssiden viser alle syv priser uden
    at man skal åbne Stripe.
  - **Er desktop-appen stadig en del af `deskuptime-pro`?** Et betalt produkt skal kunne det, det lover.
  - **Plugin-version:** kunder på Clean Copy 1.1.0 henter ikke den rettede zip. Kræver en version bump — og det er en release, som er din.
  - ~~**7 betalte produkter** (DPA, NIS2/DORA, NDA, EAA, report kit, template bundle, e-bøg-bundle) lå som «sælger ikke, filerne mangler i KV».~~ **FORÆLDET 1/10.** Målt på live: `GET /api/paid-files` svarer `kv_ok: true` og **alle svy** produkter med `ready: files`, `missing: 0`, `available: true` og deres betalingslink. `site/paid-templates.html` (EN + DA) har knapperne i HTML'en og `/api/paid-files` fjerner dem kun når serveren kan *bevise* at leveringen ikke kan ske — så de sælger i live. Denne note skal ikke læses som «endnu ikke lagt ind».

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

34. ~~**Otte generatorer lå døde i live.**~~ **FÆRDIG 30/9, `ceo/generator-script-kom-til-live`.**
35. ~~**Tak-siden genkaldte et endeligt 429 tolv gange.**~~ **FÆRDIG 1/10, `ceo/429-er-sendeloeende-paa-tak-siden`.**
36. ~~**To test dømte det modsatte af rettelsen.**~~ **FÆRDIG 1/10, `ceo/429-gate-tak-siden`.**
37. ~~**En køber der mistede sin nøgle skulle skrive til Mads.**~~ **FÆRDIG 1/10, `ceo/selvbetjent-noegleopslag`.**
38. ~~**Købsruten svarede med et andet produkt end det spurgte på.**~~ **FÆRDIG 1/10, `ceo/checkout-ruten-kan-vaere-forskrevet`.**
39. ~~**AI-svaret kunne køre script på mahope.tools.**~~ **FÆRDIG 1/10, `ceo/ai-svaret-kan-koere-script`.**
40. ~~**Ingen port dømmer vores egne priser, kun konkurrenternes.**~~ **FÆRDIG 1/10, `ceo/egen-pris-port`.**

41. ~~**Perioden ved siden af prisen er en påstand uden dom.**~~ **FÆRDIG 1/10,
    `ceo/perioden-ved-prisen`.** Ordlisten blev målt på alle 84 købsknapper *før*
    porten blev skrevet: 22 skriver `/year`, 15 `pr. år`, 8 `/år` på de tre
    årssubskriptioner, 10 `once`/`én gang` på engangskøb, 15 `lifetime` på de
    lifetime-varianter. **Ingen knap skrev en forkert periode** — men 19 skrev
    *ingen*: `Buy DeskUptime Pro — 19 USD` og `Køb GDPR-DPA-skabelon — 59 $` er
    grønne fordi de tier stilt, og `$19` står både for Clean Copy Pro
    *tilbage* i dag og for et engangskøb, så beløbet alene afslører intet.
    Rettet på alle 19 (5 knapper + 14 pristag på `/paid-templates` EN+DA).
    Ordlisten ligger i `tools/stripe_catalog.json` (`billing_periods`) og porten
    bygger sin detektor af den, så et nyt ord i katalogen kan ikke give en stille
    grøn — selvtesten dømmer at hvert af de 17 ord kan findes igen. Se arkiv.

42. ~~**STATUS er 63 linjer, ikke 25.**~~ **FÆRDIG 1/10, `ceo/plan-status-port`.**
    Koget til 24 linjer i 6 punkter med et tal hver, og hele den gamle tekst
    ligger i `docs/plan-arkiv.md`. *Men opgavens eget acceptkriterium var en
    falsk grøn* — det var `awk '/^## STATUS/{f=1;next}/^## /{f=0}f'`, mens
    overskriften hedder `# STATUS`, så mønsteret matcher aldrig og awk skriver
    0 linjer ud for enhver plan. Kriteriet var grønt før rettelsen og efter.
    Den anden awk-form er også død: `^# ` matcher ikke `##`, så den læser
    resten af filen med (343 linjer). Ny port `tools/check_plan_status.py`
    dømmer 4 ting, hvoraf dom 1 er «afsnittet skal findes» — uden den er de 3
    ande lige så døde som awk'en. Målt **rød mod den gamle plan** (63 linjer,
    2 punkter uden tal) og grøn mod den nye (24 af 25). 11 kontroller i
    selvtesten, alle syntetiske mutationer. Gaten 118 → 120 steps, og
    `IMPLEMENTATION_PLAN.md` kom i path-filteret — `test_deploy_workflow`
    fangede præcis den udeladelse, før den blev rettet. Se arkiv.
