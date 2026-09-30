# STATUS

- **Portene er grønne, og de dømmer flere ting end de læser.** 107 steps i
  `tools/quality_gate.py`. Senest: `ceo/live-check-flake` lod ét netværksreset
  erklære en sund udgivelse for brudt. Se opgave 31.
- **Donationslinjen nåede 37 → 20 værktøjssider** i to runder. Ranglisten er
  målt på **interne links** (hvor mange sider der peger på siden), ikke på
  trafik: Plausible har 15 besøgende på mahope.tools og 6 på cleancopy.tools i
  28 dage, så den kan ikke adskille to sider. `clean-copy-tool` har 48
  indgange, `compliance-site-check` 44, `word-counter` 15. Undtaget er
  `compliance-report` (to `Buy EUComply Pro`-knapper i selve rapporten) og
  `nis2-check` (en leadform i resultatet, der konkurrerer om pladsen).
- **Målt i en sand sandkasse, ikke ved læsning.** `/tmp/smoke.mjs` eval'er hver
  sides IIFE med DOM-shim: 1× donation i resultatet, også efter to submits,
  ikke i `renderHTML()`, ikke i den kopierede tekst. `check_donation_paths.py`
  dømmer nu 19 filer målt i **dist**.
- **Egen fejlform fundet og rettet to gange i denne uge:** (a) donationslinjen
  lå i `#5a5f64` på `#0f172a` = 2,68:1 i lyst tema, under WCAG AA → `#94a3b8`
  (7,77:1); (b) `no-print` antaget fælles, men klassen findes kun i generatorernes
  egen `@media print` — den ville være død markup.
- **Åben note:** donationslinjen på otte generatorer (runde 2, del 1) er
  verificeret live og lukket nedenfor.
- `❓ Til Mads` nederst: `STATS_TOKEN`, `bugbottle.dev`'s domæne, banner-placering
  på 180 sider, og de to desktop-apps der stadig ringer til Lemon Squeezy.
- **Historie:** `docs/plan-arkiv.md` (append-only; grep i stedet for at læse hel).

## Verificér deploy

- **Deploy-status pr. 30/9 21:20.** `build-info.json` på mahope.tools =
  `5f9c678`, som er det seneste mergede. CI's `gate`-job success på alle
  committene siden `e6137bf`, men **de tre `deploy`-job står røde på `5f9c678`**
  pga. netværksreset'en i opgave 31. Indholdet er målt live og i orden:
  `/books/` har seks `<h2 class="sub"><a>` og den publicerede CSS har
  `.book-card :is(h3, h2.sub) a { color:#111; text-decoration:none }`,
  `/text-on-image-checker` har donationslinjen i sit script.

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

- `VERIFICÉR DEPLOY: forbigående netværksfejl i «Tjek produktion» får 3 forsøg
  i stedet for 1, så ét reset ikke erklærer en udgivelse brudt
  ceo/live-check-flake 2026-09-30` — **dette repo deployer ved push til `main`**,
  så der er ingen batch at vente på. Mål: de tre deploy-jobs er grønne, og
  `check_live_sitemaps.py --only mahope.tools` er grøn live. Bemærk at
  `5f9c678` selv står som **rød** i CI: ikke en fejl i den kode, men
  netværksreset'en ovenfor, som denne commit retter. Den bliver rød igen hvis
  den kører igen, så grøn herafgør den gamle kørsel ikke retroaktivt.

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

32. **`_transient` findes to gange, og de er uenige om 429.** Hvorfor:
    `weekly_report.py:188` løste samme problem 21/9 (uge 39 mistede et helt
    trafiksnapshot på ét timeout) med sin egen `_transient` + `http_json`.
    `ceo/live-check-flake` skrev en anden til `check_live_sitemaps.py`, fordi de
    to scripts ikke deler kode — og de to er **uenige**: `weekly_report` prøver
    429 igen, kontrakten siger 429 er endelig og skal vises. Kontraktens
    version anvendes nu, så uge-rapporten kan blive langsommere ved
    rate-limiting. Accept: én delt `is_transient` i `tools/`, begge scripts
    bruger den, og 429-afgørelsen er truffet ét sted med en begrundelse. Skal
    ikke gøres som en del af en anden opgave.

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

29. **37 værktøjssider mangler donationslinjen.** Hvorfor: missionen beder om
    tak *efter et resultat*, og kun `/scan` gjorde det. Målt 30/9 af den nye
    port, som skriver hele listen ud hver kørsel. Accept: linjen ligger i
    resultatet på de 37, de følger samme sætning som `/scan`, og ratchetfilen
    `tools/donation.json` vokser med dem. Tages i to omgange, fordi det er 37
    sider med hvert sit eget renderingspunkt — ikke én rettelse.
    **RUNDE 1 FÆRDIG 30/9, `ceo/donation-runde-1`.** Ni sider, valgt på interne
    links: `compliance-site-check` (EN+DA), `page-profile` (EN+DA),
    `cookie-check` (EN+DA), `text-diff`, `hash-generator`, `url-inspector`.
    37 → 28. Ratchetfilen dømmer nu 11 filer.
    **RUNDE 2, DEL 1 FÆRDIG 30/9, `ceo/donation-runde-2`.** Otte generatorer
    (dpa, ropa, privacy-notice, nis2-incident — EN+DA). 28 → 20.
    **RUNDE 2, DEL 2:** de 20 tilbage. `word-counter` (15 links) tæller løbende
    og har intet enkelt resultat-`innerHTML` — den kræver et tomt skjult element
    som på `hash-generator`. `nis2-check` (EN+DA) og `nis2-gap-assessment`
    (EN+DA) har en leadform i resultatet; de må have donationen **før**
    leadformen. `markdown-table-generator`, `uuid-generator`,
    `accessibility-statement-generator`, `base64-encoder-decoder`,
    `url-encoder-decoder`, `json-formatter`, `case-converter` er
    klientværktøjer med ét resultatfelt. `compliance-report` er fortsat
    undtaget (to `Buy EUComply Pro`-knapper i selve rapporten),
    `clean-copy-tool` har 48 interne links men sit eget købsflow.

30. **Død CSS på *klasser* er stadig udømt.** Hvorfor: opgave 30 viste 23 danske
    artikler med `.compare`-CSS men uden `<table class="compare">` — ikke en
    oversættelsesfejl, men død CSS i *begge* sprog, fordi
    `make_blog_da_mirrors_453.py:404` indsætter `.compare`-blokken i enhver
    artikel uden at se, om artiklen har en tabel (alle 23 har `EN tabel=0`).
    15 engelske artikler har rigtige tabeller, så mønstret virker. Kan **ikke**
    løses med et navnesøg — `.score-badge.A` bygges som `'score-badge ' +
    bogstav` og `.sh-grade-${g}` ligeså. Kan løses med **præfiks**: `.sh-grade-A`
    er død kun hvis heller ikke `sh-grade-` står bogstaveligt i siden. Samme
    tredje dømning som `check_built_css.py` fik 30/9 for døde regler. Accept:
    porten finder mindst de 23 `.compare` og 0 af de scripts, der bygger
    klasser ved kørsel.

