# STATUS

- **Donationslinjen nåede 9 værktøjssider mere (37 → 28).** Rund 1 af opgave
  29. Ranglisten er målt på **interne links** (hvor mange sider der peger på
  siden), ikke på trafik: Plausible har 15 besøgende på mahope.tools og 6 på
  cleancopy.tools i 28 dage, så den kan ikke adskille to sider. `clean-copy-tool`
  har 48 indgange, `compliance-site-check` 44, `word-counter` 15.
- **Valgt efter to regler, ikke efter plads.** (1) Siden skal have **ét**
  renderingspunkt, så linjen kun kan sidde ét sted. (2) Der må ikke stå en
  købsknap i samme resultat — `compliance-report` (30 links) blev sprunget over,
  fordi den har to `Buy EUComply Pro`-knapper i selve rapporten. `nis2-check`
  og `nis2-check-da` er tilsvarende sprunget over: de har en e-mail-leadform
  («Save my result») i resultatet, og der konkurrerer tre handlinger om pladsen.
- **Rettet under egen review-runde:** donationslinjen på `/page-profile` lå
  i den mørke `.cli-demo`-kasse med `var(--color-text-muted)`. I lyst tema er
  det `#5a5f64` på `#0f172a` = **2,68:1** — under WCAG AA. Nu `#94a3b8`
  (7,77:1), som er den tone kassen selv bruger. Samme fejl på DA.
  På `/cookie-check` stod linjen i `#667` som den naboende note; skiftet til
  tokenet, fordi `#667` er ulæselig i mørktema.
- **Baseline:** 37 sider uden linje → 28. `check_donation_paths.py` dømmer nu
  11 filer (var 2), alle målt i **dist**: præcis én donation pr. side, i et
  `<script>`, aldrig en knap.
- **Donationslinjen nåede otte generatorer mere (28 → 20).** Runde 2, del 1:
    `dpa-generator`, `ropa-generator`, `privacy-notice-generator`,
    `nis2-incident-generator` (alle EN+DA). Ratchetfilen dømmer nu 19 filer.
- **De otte er de fire generatorer med ét resultatfelt hver** — den billigste
    gruppe i runde 2, og de deler én renderingslinje pr. side. På NIS2 indsættes
    leadformen *under* `reportWrap`, så taklinjen kommer før den som aftalt.
- **`no-print` er ikke en død klasse her.** Alle seks generator-sider har deres
    egen `@media print` med `.no-print` (dpa/ropa/privacy linje 53-55,
    nis2 linje 51-54) — klassen findes *ikke* i `style.css`, så den ville været
    død markup, hvis jeg havde antaget den fælles. Taklinjen skal ikke ende i
    det dokument læseren udskriver eller gemmer som PDF.
- **Målt i en sand sandkasse, ikke ved læsning.** `/tmp/smoke.mjs` eval'er hver
    sides IIFE med DOM-shim og dyrker de rigtige listeners: 1× donation i
    resultatet, **også efter to submits** (dobbelt-Handling), ikke i
    `renderHTML()` (så den lækker ikke ind i dokumentet), ikke i den kopierede
    tekst, ikke i markup. Mutation A (fjernet `+ DONATION`) giver 2 røde domme.
    `node --check` grøn på alle 32 inline blokke.
- `GATE`: **GRØN — `python3 tools/quality_gate.py`, 107 steps.**
- `OPGRADERINGER`: ingen. Diffen rører ingen afhængighed.
- **Historie:** de afsluttede iterationsafsnit ligger i
  `docs/plan-arkiv.md` (append-only; grep i stedet for at læse hel).

## Verificér deploy

- Alle tre åbne noter fra 30/9 er lukket: **`DEPLOY OK 2026-09-30`**. Målt på
  de live sites: `build-info.json` = `e6137bf` på alle tre domæner (det er
  den commit der låst alle tre), CI's `gate`-job success, `/books/` har seks
  `<h2 class="sub"><a>` og den publicerede CSS har
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

- `VERIFICÉR DEPLOY: donationslinjen på otte generatorer, hvor den kun opstår
  når dokumentet er genereret
  ceo/donation-runde-2 2026-09-30` — ingen ændring i layout: den nye linje er
  13px i `var(--color-text-muted)` som de øvrige noter, og den har
  `class="no-print"`, så den ikke udskrives med dokumentet. Mål i dist på de otte
  ruter, og læg mærke til at CI's `donation-paths`-step er grøn.

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

30. ~~**Ni danske blogartikler har mistet deres sammenligningstabel.**~~
    **BEGRUNDELSEN ER FORKERT — målt 30/9.** Der er **23** danske artikler med
    `.compare`-CSS og uden `<table class="compare">`, ikke ni. Og ** nul af dem
    har tabt en tabel ved oversættelse**: for alle 23 er den engelske original
    også uden tabel (`EN tabel=0` på alle 23). Det er ikke en oversættelsesfejl
    — det er **død CSS i begge sprog**, fordi generatorerne
    (`make_blog_da_mirrors_453.py:404` m.fl.) indsætter `.compare`-blokken i
    enhver artikel uden at se, om artiklen har en tabel.
    Det rigtige spørgsmål er derfor ikke «skriv en tabel til» men «find ud af om
    artiklen *skal* have en». 15 engelske blogartikler har rigtige tabeller, så
    mønstret virker — de 23 er artikler hvor en tabel ville være lavet, hvis
    generatoren havde vidst at den skrev prosa.
    **Ny vinkel for en senere iteration:** tilføj til `check_built_css.py` en
    dømning på **klasser** (`.compare` med ingen `class="compare"` i markup).
    Det kan *ikke* gøres med et navnesøg — `.score-badge.A` bygges som
    `'score-badge ' + bogstav` og `.sh-grade-${g}` ligeså — men det kan gøres
    med præfiks: `.sh-grade-A` er død kun hvis heller ikke `sh-grade-` står
    bogstaveligt i siden. Uden den dømning kan porten ikke se denne fejlform,
    og det er præcis den revieweren efterlyste 30/9.
