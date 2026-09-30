# STATUS

- **`/text-on-image-checker` målte teksten mod sig selv.** Rettet og målt.
  Årsagen var strukturel, ikke et regnestykke: `sampleContrast()` malede
  billedet **og** teksten på samme canvas og læste så `getImageData` i tekstens
  bounding box, idet den kasserede alt hvad der lå inden for
  `dr+dg+db < 120` af tekstfarven. Men en anti-aliaset glyfkant med 16 %
  dækning scorer allerede **126** — kantpixelerne overlevede filteret, og
  værktøjet målte hvid tekst mod sin egen grå frimængse. Målt i Chromium mod
  den **live** side 30/9: hvid tekst på rent hvidt billede svarede **1.47:1**,
  og tallet fulgte fontstørrelsen (1.42 / 1.46 / 1.47) i stedet for billedet
  eller tekstfarven. Hvid på hvid gav desuden *intet resultat*, fordi så blev
  alle pixels filtreret væk. `lum()` og `ratio()` var korrekte hele vejen.
- **Rettelsen maler i to lag:** ét pass med kun fotografiet, læst som
  baggrund, og ét pass med kun bogstaverne, hvor **alpha er dækningen pr.
  pixel** — den eneste måde at skelne en bogstav fra et billedpixel på, fordi
  kanten *er* en blanding. Tekstkassen **klippes** nu til canvas i stedet for
  at flyttes opad, fordi `getImageData` uden for canvas'en giver gennemsigtigt
  sort, som ville blive læst som sort baggrund. Samme rettelse i EN og DA.
  Målt efter rettelsen i Chromium: 1.00 / 21.00 / 21.00 / 4.54 / 3.03 — de
  korrekte WCAG-værdier, mod 1.46 / 1.44 / 1.70 før.
- **Ny port `tools/check_contrast_sampling.py`:** 22 løfter dømt på de to
  sider, kørt på **sidens egen kode** i en Node-canvas-stub (source-over,
  nearest-neighbour, gennemsigtigt sort uden for canvas) mod billeder med
  kendte farver. Ingen browser, så den kører i CI. Tre mutationer er målt til
  at gøre den rød: måler i hjørnet i stedet for hvor teksten står, læser
  farverne fra det lag der indeholder teksten (den gamle kode), og flytter
  kassen opad i stedet for at klippe den. `--self-test` 11/11.
  **Fund undervejs:** to af de første mutationer viste sig **ækvivalente** —
  de kunne ikke gøre en forskel, fordi dækningskortet alligevel springer de
  pixels over som de tilføjede. De blev byttet ud med mutationer der er fejl,
  ikke skrivemåder. Samme fejl som de tre fund fra reviewen: et løfte uden dom.
- **Porten dømmer ikke:** at `worst` springer den mørkeste baggrund over. Det
  er umærkeligt på de billeder porten bruger, fordi de er ensfarvede eller
  todelte — der er ingen farvevariation *inde i* tekstkassen at vælge imellem.
  Det kræver et gradientbillede. Skrevet op nedenfor, ikke som en løftet
  kontrol.
- **Opgave 25 deployet og verificeret.** `DEPLOY OK 2026-09-30` — live
  `build-info.json` bærer `commit 9b82111`, `routes_sha256 8367db4b…` og
  `sitemap_count 256`, som er byte-identiske med det lokale byg. Indholdskrav
  (a)–(e) er alle målt opfyldt; (c) målt mod `dist/bugbottle.dev/` fordi den
  route er bugbottle.dev's, ikke mahope.tools', og bugbottle.dev deployes
  stadig ikke (❓).
- **Live-måling af de ti mest besøgte sider: rent.** Alle 10 svarer 200 med
  **nul console-errors, nul page-errors og nul fejlede requests** i Chromium
  på 390 px. Døde ankre i hele `dist/`: **0** (de 7 fund er `/scan#url=…`,
  som er en klient-rute, ikke et anker). Alle 16 Stripe-betalingslinks svarer
  200. `/api/license/validate` giver 404/400 korrekt. `/api/url-inspect` er
  bekræftet live med CEO-fiksen. `/pro/` er 404, men **intet** linker til den.
- **Opgave 25 færdig.** 62 sider — 44 EN, 18 DA — havde to afsnit med samme job
  side om side: «Tools and guides» med et kortgitter og «Related Guides» med en
  liste. 36 af de relaterede links pegede på en destination siden *allerede*
  viste i sit eget gitter, så `/blog/text-on-image-contrast-check` (8 af 15
  besøgende, bounce 100 %) nåede læseren med `/blog/wcag-contrast-checker` to
  gange under to overskrifter og to navne.
- **Rettelsen er i generatoren, ikke i filerne.** Ny delt
  `tools/crosslink_merge.py` fletter de relaterede artikler *ind* i det afsnit
  siden allerede har: et nyt kort pr. artikel, og findes destinationen i
  forvejen, bærer *det* kort beskrivelsen. Begge generatorer
  (`crosslink_blog.py` + `_da`) bruger den, så de ikke kan glide fra hinanden.
  Målt: 91 EN + 93 DA filer, to kørsler efter hinanden → 0 ændringer (idempotent).
- **Tre fund undervejs, alle rettet samme sted:**
  (a) `da/blog/bugrapporter-i-ci-pipeline` havde **den engelske** kasse med
  `/blog/…`-links på en dansk side — en dansk oversættelse der fik den med i
  kopien. DA-generatoren fjerner den nu og siger hvis den kommer igen.
  (b) Begge generatorers `if new != c` sammenlignede med den *allerede*
  ændrede tekst, så et greb uden ny tekst aldrig blev skrevet — det fjernede
  lå på disken. Sammenligner nu mod filen.
  (c) Et krydslink-uddrag lækkede «Kør alle 22 WCAG 2.1 AA-regler lokalt» fra
  desktop-scannerens beskrivelse ind på siden om den *online* tjekker.
  `check_rule_claims` blev rød, og den havde ret. Et uddrag med et tal i er nu
  tomt: **et tal skal stå på den side der kan måle det.**
- Ny port `tools/check_tool_sections.py`: dømmer to afsnit med samme job på én
  side (EN og DA som én familie) og én destination to gange i ét afsnit.
  **GRØN på 190 afsnit i 303 sider**, `--self-test` OK 11/11. Bevis at den
  dømmer: de 62 sider var røde *før* rettelsen, målt i en klon.
  Vinduet i porten var først kun «næste `<h2>`», hvilket gav 8 røde
  `/free-tools`-fund fra **footeren** — en rød uden en fejl. Nu slutter den også
  ved `<footer>`, `</main>`, `</article>`, `</body>`.
- `stripe-ctas` blev rød på `$144`/`$7` i en krydslink-titel om
  *konkurrenternes* SaaS-priser. Dokumenteret i `stripe_catalog.json` for det
  tilbud, som er portens egen måde at godkende et tal.
- **Opgave 26 er live og verificeret 30/9.** Hvid tekst på et rent hvidt
  billede svarede **1.00:1** på den **live** side ved 390 px og 1280 px,
  nul console-errors og nul page-errors, ingen vandret scroll.
  `build-info.json` bærer `commit f36fb6b`, og `check_live_sitemaps.py` mod
  fuld SHA siger «live sitemap OK» på alle tre deployede domæner.
- **Porten dømmer nu, om værktøjet svarer på den *dårligste* baggrund.**
  `sampleContrast()` tager `min` og `max` af baggrunden under bogstaverne
  og svarer på det værste par — det er hele pointen med «worst-case». Men
  porten havde intet billede, hvor den kunne se forskel på de to: på de
  ensfarvede og todelte har **alle** dommene hvid tekst, og med hvid tekst
  er den *lyseste* baggrund altid den dårligste. Springer `worst` den
  mørkeste over, ændrer tallet sig derfor **ikke** — mutationen var målt
  grøn, altså uden dom.
- **Rettelsen er et gradientbillede med sort tekst**, hvor rollerne bytter
  om: her er den mørkeste baggrund den dårligste. Ny femte mutation
  `[minC, maxC]` → `[maxC]` er målt til at gøre porten rød med præcis den
  linje («viser 21.00:1, men billedet og tekstfarven giver 1.00:1») —
  værktøjet siger PASS oveni en baggrund der indeholder rent sort. Målt på
  **begge** sider. Selvtesten får tre nye kontroller, hvoraf den ene kræver
  at casen kan svare 21:1 når kun den bedste baggrund tælles, så den ikke
  kan blive grøn af tilfældighed. `--self-test` **24/24**.
- **Fund undervejs: porten dømte 22 løfter og kørte 20.**
  `antal += len(FARVEPAR) + 2 + len(TODELT)` sagde 11 pr. side mens
  harnessen faktisk returnerede 10 — målt i en klon af `main` 30/9. To
  løfter uden dom, i porten der skal dømme netop «et løfte uden dom».
  Tallet kommer nu fra de rigtige resultater i stedet for en hårdkodet
  formel. Samme slags hårdkodet `11/11` i selvtestens overskrift er nu en
  rigtig optælling.
- `GATE`: **GRØN — `python3 tools/quality_gate.py`, 105 steps** (103 → 105).
- `OPGRADERINGER`: ingen. Diffen rører ingen afhængighed.
## Verificér deploy

- ~~`VERIFICÉR DEPLOY: /text-on-image-checker måler teksten mod sig selv`~~
  **DEPLOY OK 2026-09-30** — målt på den live side: 1.00:1 ved 390 og
  1280 px, nul console-errors, `build-info.json` = f36fb6b, sitemaps OK.

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
