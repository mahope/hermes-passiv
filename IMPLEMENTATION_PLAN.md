# STATUS

- **Donationen nåede 4 af 161 sider.** Missionen siger «tak, hvor en glad
  bruger siger tak, fx efter et vellykket resultat» — målt 30/9 var det kun
  `/scan`, `/scan-da` og de to `/support`. Katalogen, `FUNDING.yml` og
  kontrakten har haft linket længe; ingen port målte om det nåede nogen.
- **Linjen er lagt i resultatet på de to mest besøgte værktøjssider**
  (`/text-on-image-checker` EN + DA), i samme 13px-grå linje som `/scan`s
  øvrige noter: ikke en knap, fordi en knap deler opmærksomhed med
  værktøjets egen primære handling. Sætningen siger *kun* at kørslen er
  gratis og sker i browseren — ingen påstand om hvor den er, kun hvor den
  ikke er.
- **Ny port `tools/check_donation_paths.py`:** dømmer de to sider — katalogens
  URL, aldrig en knap (`class="btn…"` er rødt), præcis én, og **inde i
  `<script>`** så den først opstår når værktøjet renderer sit svar. Uden det
  sidste krav kan porten ikke se forskel på «donationen vises, når læseren
  har spørgsmålet» og «donationen ligger i markup'en og siger tak til en
  besøgende, der ingenting har bedt om». `--self-test` 13 kontroller,
  mutationer målt i en klon.
- **Porten tæller de øvrige 37 værktøjssider** og skriver dem ud i hver
  kørsel, men dømmer dem ikke: «hvor mange sider» er en samlet beslutning, og
  en port der lovede at dømme dem, ville være løgnen over det den kan se.
  `/thanks` er ikke i opgøret — købet er lige sket. Blogartikler heller ikke:
  en læser der er færdig med en artikel er ikke et *resultat*.
- **Baseline:** `site/` 161 sider, 4 med donation (2,5 %). Efter denne
  iteration 6 (3,7 %). De 37 tællede står som den næste batch.
- `GATE`: **GRØN — `python3 tools/quality_gate.py`, 107 steps** (105 → 107).
- `OPGRADERINGER`: ingen. Diffen rører ingen afhængighed.
- **Historie:** de afsluttede iterationsafsnit ligger i
  `docs/plan-arkiv.md` (append-only; grep i stedet for at læse hel).

## Verificér deploy

- ~~`VERIFICÉR DEPLOY: /text-on-image-checker måler teksten mod sig selv`~~
  **DEPLOY OK 2026-09-30** — målt på den live side: 1.00:1 ved 390 og
  1280 px, nul console-errors, `build-info.json` = f36fb6b, sitemaps OK.
- `VERIFICÉR DEPLOY: porten kan se bedste og dårligste baggrund i samme
  tekstkasse ceo/gradient-dommer-baggrund <TIDSPUNK>` — ingen UI-ændring,
  så det er bygget uændret. Sammenlign `build-info.json` mod lokalt byg
  og læg mærke til at CI's `contrast-sampling`-step er grøn.

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
