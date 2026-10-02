# STATUS

- **deskuptime.com svarer nu på sit eget h1.** Tjekket i `#check` lige under heroen
  kalder `/api/url-inspect` og svarer på «er sitet oppe» og «er certifikatet
  gyldigt» i browseren (`ceo/deskuptime-live-check`). Målt 2/10 før: 4 besøgende i
  28 dage, 100 % bounce, 0 s besøgstid — og de to gratis webværktøjer lå 120
  linjer prosa længere nede. Tredje spørgsmål (indholdsændring) kan svaret ikke,
  og det siger det.
- **Én handling over folden på de otte næst mest besøgte artikler** (EN+DA).
  Målt 2/10: alle otte havde **3** `btn-primary` i folden (heroens anker +
  `/scan` + `/compliance-ai` under `</header>`). Nu **1** pr. side. 12 sider dømt.
- **To værktøjssiders gratis-mod-Pro-tabel kommer fra katalogen** (`ceo/pro-tabel-webtool`).
  `/clean-copy-tool` havde den eneste **håndskrevne** tabel i familien («19 USD per
  year», uden port), `/url-inspector` havde ingen. Målt 2/10: 11 → 13 sider.
- **Donationsprisen læses af katalogen på alle fire sider** (`19e59b2`) — «fra 10 kr.»
- **Alle 21 sider har gratis mod Pro i samme tabel.** `check_pro_table.py`
  (8 produktsider + 13 værktøjssider) + `check_catalog_where.py` (112 belæg).
- **CEO-kø punkt 0 er færdigt** — `5693853`: `/api/url-inspect` → 200, 202 på
  `/thanks` siger «not confirmed yet», 429 er endelig, SSRF-værnet dækker hvert hop.
- **PR-tjek 2/10:** 0 åbne PR'er. **Branch-tjek 2/10:** ingen 14 dage gamle.
- **❓ Til Mads:** `OPENROUTER_API_KEY`, `STATS_TOKEN`, `bugbottle.dev`s domæne,
  banner-placering på de 172 øvrige sider, de 2 desktop-apps der ringer til Lemon
  Squeezy, Search Console, **IndexNow pinges aldrig** (skripten kaldes ikke), og
  **bogenes betalte udgave** (se ❓).

## Verificér deploy

- **DEPLOY OK 2/10 (kl. 09).** Noten om gratis-mod-Pro i kortet på de ni øvrige
  værktøjssider er målt på **indhold**: `pro-table:start` står 1 gang på alle ni
  live, og `build-info.json` på alle tre deployede domæner står i `ce438ba`.
- **DEPLOY OK 2/10 (kl. 11).** `ceo/livstid-scope` (`45b31df`) er ude — den lå
  og ventede, fordi den gik rødt i CI. Målt på indhold: `/compliance-report`
  serverer `$149 once per website — lifetime, first 100 purchases` og den danske
  `$149 én gang pr. website, for altid.`, og `build-info.json` står i `182af57`.
- **DEPLOY OK 2/10 (kl. 12:30).** `ceo/pris-side` (`b0da8ad`) er ute. Målt på
  **indhold**, ikke på HTTP 200: `/pricing` og `/da/pricing` serverer hver 14
  `data-product`-rækker, 3 `data-lifetime`-rækker, **0** `buy.stripe.com` og
  `pricing:start` 1 gang pr. fil; `build-info.json` står i `b0da8ad`.
- **DEPLOY OK 2/10 (kl. 11).** `ceo/donation-pris-fra-katalog` (`19e59b2`) er ude,
  målt på indhold: `build-info.json` står i `19e59b2`, `/pricing` har
  `From 10 kr.` i rækken `support-mahope-oss`, `/da/pricing` `fra 10 kr.`,
  `/support` «Any amount from 10 kr.» og `/da/support` «Valgfrit beløb fra 10 kr.».

- **DEPLOY OK 2/10 (kl. 11).** `ceo/donation-pris-fra-katalog` (`19e59b2`) er ude,
  målt på indhold: `build-info.json` står i `19e59b2`, `/pricing` har
  `From 10 kr.` i rækken `support-mahope-oss`, `/da/pricing` `fra 10 kr.`,
  `/support` «Any amount from 10 kr.» og `/da/support` «Valgfrit beløb fra 10 kr.».

- `VERIFICÉR DEPLOY: gratis-mod-Pro-tabellen på /clean-copy-tool og /url-inspector
   2026-10-02 ceo/pro-tabel-webtool` — måler på **indhold**:
   `build-info.json` står i `7e74d3b` på `mahope.tools` og `cleancopy.tools`;
   `cleancopy.tools/clean-copy-tool` har `pro-table:start` 1 gang og **0**
   «19 USD per year» og `$19/year` i prisrækken; `mahope.tools/url-inspector/`
   har `pro-table:start` 1 gang, `$19/year` og `Three machines per licence` i noten.
   Dom 1: `check_pro_table.py` grøn (8 produktsider + 13 værktøjssider). Dom 2:
   `--self-test` 24/24. Dom 3: `build_sites.py` (329 filer, 264 html, 0 brudte),
   `seo_check.py`, `stripe-worker.test.mjs` (352/352) og `check_inline_js.py` grønne.
   Dom 4: hele `quality_gate.py` 136 steps grøn (målt i den iteration der lavede
   ændringen). Dom 5: `check_catalog_where` grøn.

- `VERIFICÉR DEPLOY: én handling over folden på de otte næst mest besøgte
   artikler 2026-10-02 ceo/fold-fire-besogte-artikler` — måles på **indhold**:
   hver af de otte artikler (4 EN + 4 DA) har **1** `btn-primary` i foldregionen
   i stedet for 3, og **0** `btn-primary` i `blog-tool-cta`-bannerne. Dom 1:
   `check_first_action.py` grøn (12 sider dømt). Dom 2: `--self-test` 12/12.
   Dom 3: `build_sites.py`, `seo_check.py`, `stripe-worker.test.mjs`,
   `check_inline_js.py` grønne. Dom 4: hele `quality_gate.py` grøn (målt i den
   iteration der lavede ændringen). Dom 5: `ai-cta-honesty` grøn.

- `VERIFICÉR DEPLOY: tjekket på deskuptime.com's forside 2026-10-02
   ceo/deskuptime-live-check` — måles på **indhold**, ikke på HTTP 200:
   `https://deskuptime.com/` og `https://deskuptime.com/da/` har hver præcis
   **1** `.du-form` med `id="du-check-form"`, `action="/api/url-inspect"`,
   `<label for="du-check-url">`, `#du-check-status` med `role="status"` og
   `#du-check-result`, `DU_DONATE`, og indlæser `/net.js` **og** `/one-off-check.js`;
   `build-info.json` står i squash-sha'en for denne note. Dom 1: `GET
   /api/url-inspect?url=https://example.com` på deskuptime.com svarer **200**
   med `securityHeadersChecked` på **8** navne (nyt felt i `_worker.js`, så
   widgetten ikke hardkoder listen). Dom 2: `stripe-worker.test.mjs` **354/354**,
   og de to nye kontroller fejler på koden før ændringen. Dom 3: `build_sites.py`
   (329 + 35 filer, 0 brudte), `seo_check.py`, `check_inline_js.py` grønne.
   Dom 4: hele `quality_gate.py` grøn. Dom 5: `check_first_action.py` dømer nu
   begge forsider mod `#check` (14 ratchetede sider), `check_form_labels.py`
   grøn på det nye felt, `check_net_copies.py` grøn (genkaldsreglen kun i
   `net.js`), `check_donation_paths.py` **GRØN på 41 sider** + `--self-test`
   grøn (de to forsider kom i ratchetfilen, fordi de nu renderer et resultat).

## Åbne opgaver

1. ~~Flere sider end forsiden pr. URL.~~ **Færdig 1/10.** Kaldet læser den
   indsendte side og de juridiske sider forsiden *linker til* — kun på sitets
   eget domæne — før det gætter stier, og svaret lister dem i `pages_read`.
   Accept nået: `pages_checked` overstiger de gættede stier, og fundet peger på
   den linkede side. Flyttet til `docs/plan-arkiv.md`.
2. ~~Generatorerne lavede dokumentet, men ikke vejen videre.~~ **Færdig 2/10.**
    Alle otte generatorer (DPA, NIS2, RoPA, privacy notice, EAA-erklæring —
    EN + DA) har nu et kort på resultatet med den betalte vare der svarer til
   deres eget output, pris og periode læst fra `tools/stripe_catalog.json`.
   Flyttet til `docs/plan-arkiv.md`.
3. **Konvertering kan ikke måles uden `STATS_TOKEN`.** Hvorfor:
    `/api/stats` svarer 401 siden uge 37, så næsten hver linje i enhver
    trafikrangering er vor egen links-tælling, ikke besøg. Den nye port har samme
    problem og siger det i hver kørsel. Accept: `GET /api/stats` med token
    svarer 200. *(Blokeret på Mads — se ❓.)*
3. **`bugbottle.dev` deployes ikke.** Hvorfor: `deploy-sites.yml`-matrixen
   deployer kun tre domæner, så `dist/bugbottle.dev/` bygges hver kørsel og
   lægges ingen steder; live er 61 ruter fra en anden udgivelse. Det er derfor
   `traffic_status` er `partial` hver time og `reports/weekly/` mangler et helt
   domæne. Den nye port måler `/bugbottle-demo` og dømmer den ikke, fordi samme
   grund gør dom 4/7 i artikelporten umulige at dømme. Accept: enten domænet på
   Pages og fjernet af `UNMANAGED_DOMAINS`, eller fjernet fra `TRACKING_DOMAINS`
   så status bliver ærlig. *(Beslutning — se ❓.)*
4. **172 sider har to-tre knapper over folden.** Hvorfor:
   `add_top_cta_495.py` og `add_ai_cta.py` har skudt scanner- og AI-banneren
   ind under `</header>` på hele bloggen, så de lå over folden på 180 af 224
   sider med hero — og på mange er heroens egen primære et anker (`#content`,
   `#how`). Målt 30/9 af `check_first_action.py`; **2/10 er de 10 mest besøgte
   rettet** (kontrastartiklerne + otte artikler med 1–2 besøgende, EN+DA), så
   172 står tilbage. Accept: bannerne er enten flyttet ned i artiklen på de mest
   besøgte sider (dømt i `tools/first_action.json`), eller slettet fra hele
   bloggen så AI-CTA'en ligger ét sted pr. side. Kræver beslutning — se ❓.
   **Målt i denne iteration:** de otte nyrettede havde 3 → 1 `btn-primary` i
   folden; portens ratchet voksede 4 → 12 dømte sider.
5. ~~DA-siden mangler download-knappen på rapporten.~~ **Ikke et problem.**
   Optaget på en måling af kildefilerne 1/10, men målt på live: både EN og DA
   har `dlReport` to gange og `function downloadReport` én gang. Flyttet til
   `docs/plan-arkiv.md`.
6. **En sitemap-rute må ikke have en død eneste handling.** Hvorfor:
   Fund fra review 1/10 blev rettet for `/compliance-ai`, men porten dømmer kun
   de to ruter, der er skrevet i `tools/unavailable_routes.json` — en ny AI-
   eller beta-side kan stadig publiceres med en handling, der altid fejler.
   Accept: porten finder den, hvis den skrives i manifestet. *(Kun relevant når
   vi tilføjer flere sådanne sider — ikke en opgave i sig selv.)*
7. ~~`check_pro_table.py` kører ikke i gaten.~~ **Færdig, målt 2/10** med
   `quality_gate.py --list` — `pro-table` og `pro-table-selftest` står i
   `STEPS`, så opgavens egen beskrivelse var forældet. De to nye steps
   `catalog-where` og `catalog-where-selftest` er kablet på samme måde, og
   `tools/test_deploy_workflow.py` bekræfter at filerne er i CI's path-filter.
7. **Bogen har ingen DA-udgave, og læsevisningen gør det tydeligt.** Hvorfor:
   de seks boger er på engelsk, og hele `_worker.js`, scanneren og resten af
   mahope.tools findes på dansk. Læsevisningen gør bogen mere læsbar end før,
   og dermed mer synlig for en dansk læser der ellers ville havedownloadet den
   uden at læse. Accept: enten en DA-udgave af de to vigtigste bøger
   (`gdpr-for-agencies`, `nis2-for-agencies`) som EPUB i `ebook/`, eller en
   synlig dansk note på bogside-ruterne om at bogen findes på engelsk. Kræver
   beslutning — se ❓. Baseline 1/10: 0 danske EPUB'er, og 6 bogsider uden
   dansk sætning.

## ❓ Til Mads

- **🔴 `OPENROUTER_API_KEY` mangler på workeren — assistenten er stadig slukket.**
  Rettet 1/10, så ingen kunde længere skriver et spørgsmål og bliver bedt om at
  kontakte os: siden siger nu at assistenten er slukket og byder på scanner,
  erklæringsgenerator og de tre bøger, og begge ruter er ude af sitemap og
  `llms.txt`. **Når du sætter nøglen:** fjern `<meta name="robots"
  content="noindex,follow">` fra `site/compliance-ai.html` og
  `site/da/compliance-ai.html`, så slutter de i sitemap igen. Chatten tænder
  selv — kapabilitets-tjekket læser nøglen direkte, så der er ingen anden kode
  at rette.   `tools/check_unavailable_routes.py` fortæller dig hvis du glemmer
  den ene halv. **Banneren på de 187 artikler følger samme nøgle:** sæt
  `"available": true` i `tools/ai_cta.json`, kør
  `python3 tools/check_ai_cta_honesty.py --apply`, og de gamle
  «Ask the Compliance AI»-tekster kommer tilbage på alle 187 sider. Gaten er
  rød, indtil det er gjort.
- **🟡 Skal scanner- og AI-banneren ligge over folden på de 172 resterende
  sider?** Målt 30/9 giver det **tre knapper oven på folden** pr. artikel, og på
  30 af dem er knappen *oveni* et anker som «læs videre», så det værktøj artiklen
  handler om ikke er den primære handling. **2/10 er de 10 mest besøgte rettet**
  (kontrastartiklerne + otte med 1–2 besøgende, EN+DA), målt 3 → 1 knap i folden
  og dømt i `tools/first_action.json`. Enten flytter jeg banneren ned i artiklen
  på de næste mest besøgte, eller jeg sletter den fra hele bloggen, så AI-CTA'en
  ligger ét sted pr. side. Det er din beslutning, fordi det er en promo du har
  bedt om.
- **🟡 `indexnow_ping.sh` kaldes aldrig.** Målt 2/10: `grep -rn indexnow
  .github/workflows/ build_sites.py` giver **0 træffere** — skripten er skrevet,
  nøgle-filen serveres korrekt, men intet udløser den. Bing og Google er de to
  eneste søgemaskinereferencer (2 + 2 besøgende), så det er den billigste
  distribution vi ikke bruger. Jeg har ikke lagt den i CI, fordi et IndexNow-ping
  er et udadvendt kald til et eksternt API, og det er din beslutning. Sig til det,
  så lægger jeg ét step i `deploy-sites.yml` efter en vellykket udgivelse.
- **🔴 `STATS_TOKEN` på workeren.** Én linje, én secret, og så kan konvertering
  måles i stedet for gættes. Uden den er `/api/stats` 401, og opgave 2 bygger på
  tal, der ikke er besøg.
- **🔴 `bugbottle.dev` ligger på en server, vi ikke deployer.**
  `https://bugbottle.dev/build-info.json` svarer **404 fra `nginx`**, ikke
  Cloudflare, mens de tre andre domæner bærer alle samme sha. To veje: (a)
  domænet skal på Cloudflare Pages → opsæt `bugbottle-dev`-projektet, så
  tilføjer jeg domænet til matrixen og fjerner undtagelsen i samme commit;
  (b) domænet er ikke vores at udgive → det skal ud af `TRACKING_DOMAINS`, så
  `traffic_status` bliver ærlig `ok` for de tre vi faktisk deployer.
- **🔴 To betalte desktop-apps kan ikke aktiveres.** Målt i de shippede binære:
  `mahope/transmute` `v0.2.1` og `mahope/deskuptime` `desktop-v0.2.7` har begge
  `https://api.lemonsqueezy.com/v1/licenses/activate` indbygget, og binæren
  sender `license_key` + `instance_name` og læser `activated`, `id`,
  `product_name`, `customer_email` — mens vores `/api/license/activate` kræver
  `{ license_key, device_id, product }`. Serveren er tolerant over for
  `instance_id` som alias for `device_id`; `instance_name` giver jeg ikke.
  Kilden ligger i private repos, og du laver selv releases.
- **🔴 Bogen er gratis, men Stripe har et betalt bundlet produkt.** Kontrakten
  lister `eu-compliance-ebook-bundle` til **$29**
  (`https://buy.stripe.com/fZu9AScr9a6SbtA68vbMQ0b`), mens **syv** publicerede
  sider siger modsatte: «Free download — no signup, no email. This e-book is
  free, and it stays free — we do not sell a paid edition of it» og på
  `/books/compliance-bundle` «nothing is left out, and nothing is reserved for
  a paid edition». Vi har aldrig linket til det betalte link, så det ligger og
  venter. Feature-kø sagde «én købsknap til sit bundle-link» — den har derfor
  **ikke** fået en knap, fordi den ville være en købsknap til noget syv sider
  siger er gratis. To veje: (a) vi sletter produktet og linket i Stripe, så
  kontrakten og siderne er enige; (b) vi laver en **ny** betalt udgave der rent
  faktisk betaler sig — fx de samme bøger i PDF + Word + de opdaterede
  revisioner, eller en 2027-udgave — og skriver dens ærlige beskrivelse. Det er
  din beslutning, fordi det er dit navn på kvitteringen.
  **Haster lidt mere 2/10:** `/pricing` viser nu også `$29 once` for
  `eu-compliance-ebook-bundle`, så modsætningen med de syv bogside-ruter er synlig
  på **tre** sider i stedet for to. Den nye side tager dog ikke selv imod betaling
  — den sender læseren videre til `/paid-templates`, som gjorde det i forvejen.
- **🟡 Skal værktøjssiderne vise livstidsprisen overhovedet?** De elleve pro-kort
  på `/scan`, `/cookie-check`, `/contrast-checker` m.fl. har en gratis-mod-Pro-tabel
  med «$79/year per website». Jeg lagde livstidsprisen ind som et prislink dér, og
  to porte sagde nej: `check_stripe_ctas` dømmer «præcis 1 synlig lifetime-CTA pr.
  produkt», og `pro_card` dømmer «ét købsknap i ét pro-kort» — fordi tabellen ligger
  inde i kortet. Købsvejen findes allerede på de seks produktsider, så det er ikke
  en mistet indtægt, men det er en pris læseren ikke kan købe. Enten beholder vi
  den som ren tekst, eller jeg flytter den til en fane under kortet. Din beslutning.
- **Search Console:** tilføj de fem domæner som properties (`mahope.tools`,
  `cleancopy.tools`, `deskuptime.com`, `bugbottle.dev`, `transmute.run`).
  Sitemap og robots er målt korrekte på de fire sites missionen udgiver; kun
  property-tilføjelsen mangler.
- **Er desktop-appen stadig en del af `deskuptime-pro`?** Et betalt produkt skal
  kunne det, det lover.
- **Plugin-version:** kunder på Clean Copy 1.1.0 henter ikke den rettede zip.
  Kræver en version bump — og det er en release, som er din.

## Feature-kø

Prioriteret efter hvor tæt den er på penge, ikke efter hvor let den er at kode.
Baseline for hvert tal er målt 1/10; tallene er ikke vores egen trafik.

1. ~~Flere URL'er pr. scanning.~~ **Leveret 1/10** — feltet tager linjeskift,
   serveren svarer én rapport pr. URL, og Pro-boksen siger ærligt hvad den
   *ikke* ser. Næste skridt var punkt 1 under «Åbne opgaver»: det er gjort.
2. ~~E-bøgerne læses online, kapitel for kapitel.~~ **Leveret 1/10** — alle seks
   bogside-ruter viser kapitel 1 og 2 i fuld tekst, bygget af den EPUB kunden
   henter. Målt først: `read-online` 0 gange i alle otte bogsider, og den eneste
   vej til teksten var en download. Næste skridt er punkt 6: måle om nogen læser
   læsevisningen, hvilket kræver `STATS_TOKEN`.
3. **`/compliance-ai` som ikke gør ingenting.** Hvem: alle der lander på siden
   fra artiklerne. Tal: kald pr. uge (baseline: **0**, siden secret'en mangler).
   **Delvis leveret 1/10:** siden siger det ærligt og ruterne er ude af de
   genererede lister, så den ikke længere skader nogen. Resten kræver
   `OPENROUTER_API_KEY` — se ❓. Datagrund: målt 1/10 — 503 «AI service not
   configured», `cf-cache-status: DYNAMIC`.
4. ~~En købsvej til Clean Copy Pro i værktøjet på cleancopy.tools.~~
   **Leveret 1/10** — efter en konvertering ligger der ét Pro-kort med batch,
   egne rense regler og knappen «Buy Clean Copy Pro — $19/year», skjult for
   aktiverede Pro-kunder. Målt først: 0 købsknapper i resultatet. Næste skridt
   er punkt 2 — bøgerne læses online.
5. ~~Scanneren siger hvilken side den læste, og følger de links siden har.~~
   **Leveret 1/10** — overblikket, det enkelte resultat og den downloadede
   rapport siger hvilken side og hvilke sider der blev læst, og et dybt URL
   scannes på den side det angiver. Målt først: «the score is the homepage»
   stod på siden uanset input, og kun de gættede stier blev læst.
6. ~~Det mest linkede værktøj solgte ikke.~~ **Leveret 1/10** — `/scan` og
   `/scan-da` renderer nu det samme pro-kort som de otte søskendeværktøjer,
   med katalogens betalingslink, pris og periode, og donationslinjen overlever.
   Målt først: 0 `buy.stripe.com` på begge sider. Dertil en fundet fejl: kortet
   blev trykt med i brugerens egen rapport, fordi `@media print` skjuler `.btn`
   men ikke `.pro-card` — så PDF'en havde salgstext uden den eneste handling.
   Nu skjuler print-listen begge, målt i browseren (`display: none`).
7. ~~Kontrast-tjekkeren indeni artiklen, der får hele trafikken.~~
   **Leveret 2/10** — begge artikler har selve værktøjet, og heroens primære
   handling er et anker ned til det i stedet for et hop ud af siden. Målt først:
   8 af 18 besøgende landede på artiklen, 100 % forlod den, og værktøjet fik 1.
   Dertil fundet undervejs: felterne var 192 px høje på telefon, fordi en delt
   `.ti-field > *`-regel gav kolonnebørnene en *højde* på 12 rem. WCAG-formlen
   lå i fire kopier; den ligger nu i `site/text-on-image-core.js`.
8. ~~Rettfærdigt budget pr. rapport, og et fund der siger fra.~~
   **Leveret 2/10** — se fundet fra review 30/9 i STATUS. Datagrund: målt på
   den levende rute, 3 sites i ét kald → rapport 3 med `pages_checked: 1`,
   `score: 22` og fem «Not found»-fund om sider wordpress.org har.
9. ~~Free mod Pro på ét sted.~~ **Leveret 2/10** — de otte produktsider har nu
   samme to-rækkers-tabel, tegnet af `tools/pro_table.py` fra
   `tools/stripe_catalog.json`, og `check_pro_table.py` dømmer hver blok mod
   samme kilde. Målt først: `page-profile` skrev «$0 forever / $19/year /
   $39 once» i hånden, `deskuptime` «19 USD once», de to andre havde ingen
   tabel — fire svar om det samme produkt, ingen port dømte dem. **Næste skridt
   er gjort 2/10:** de ni øvrige værktøjssiders pro-kort har nu samme tabel, så
   en besøgende på `/scan` ser «gratis gør dette, Pro gør hele sitet» i samme
   øjeblik han har set sit resultat. Ny port `check_catalog_where.py` dømmer
   belægget i katalogens `where`, så «hvor»-påstandene ikke kan rådne igen.
10. **Livstidsprisen lå på 17 sider uden købsvej — løsningen er fundet, og
    den er: ingen.** Hvem: alle der hellere betaler engang end pr. år; de tre
    livstidsudgaver er Stripe-varer med `limit: 100`. Tal: målt 2/10 — de 17
    sider viste beløbet, 0 af dem linkede til `lifetime.payment_link`, men de
    **seks produktsider** har den købsvej, og `check_stripe_ctas.py` dømmer
    «præcis 1 synlig lifetime-CTA pr. produkt». Accept: den er nået på den side
    hvor købet sker; de elleve værktøjssiders tabel skal fortsat vise prisen
    som tekst, fordi tabellen ligger **inde i** pro-kortet, og `pro_card.py`
    dømmer «ét købsknap i ét pro-kort». Datagrund: begge fund er målt i gaten
    efter en færdig implementering, ikke gættet. **Åbent:** om værktøjssiderne
   overhovedet skal vise livstidsprisen — se ❓.
11. ~~Én side med alle priser.~~ **Leveret 2/10** — `/pricing` (EN + DA) lister
    alle 12 katalogvarer med beløb, periode, omfang, gratis-mod-Pro og en
    købsvej, bygget af `tools/pricing_page.py` fra katalogen. Den **tager ikke
    imod betaling** — hver række linker til produktets egen købsside — så de tre
    porte bygget på «én købsvej pr. produkt» kan blive ved med at være strenge.
    Målt først: 0 af de 102 ruter nævnte to produkter i `<title>`/`<h1>`, så
    spørgsmålet «hvad koster hele pakken» krævede at gætte hvilken af otte
    sider der har svaret. Fund undervejs: `check_tool_paid_path.py`s ratchet dømte
    de to nye ruter som ubefalede, så `--write` skrev dem ind — 92 → 94 linjer.
12. ~~**Tjekket lå på mahope.tools, ikke på det site, der sælger det.**~~ **Leveret
    2/10** — `deskuptime.com` og `/da/` har nu ét tjek i `#check` lige under
    heroen, der kalder `/api/url-inspect` og svarer på de to første af de tre
    spørgsmål i sit eget h1. Hvem: alle der lander på forsiden (4 besøgende,
    100 % bounce, 0 s). Tal: checks pr. uge mod forsiden (baseline **0** — der var
    ingen kodevej til den). Accept: heroens primære handling er tjekket, formen er
    en rigtig GET så den virker uden JavaScript, og svaret siger ærligt at det
    *ikke* overvåger noget og ikke kan se indholdsændringer — det er CLI'ens og
    appens job. Datagrund: målt 2/10 på live — `/api/url-inspect` svarede 200
    med status, kæde, certifikat og headere, men blev aldrig kalt herfra; de to
    gratis webværktøjer lå 120 linjer prosa længere nede. Fund undervejs: listen
    af de otte headere lå i workeren og skulle hardkodes igen i klienten, så
    `securityHeadersChecked` kom i svaret, og `stripe-worker.test.mjs` fik to
    kontroller der fejler på den gamle kode (354/354). Fund undervejs, fundet af
    gaten: `check_donation_paths.py --self-test` blev rød, fordi den nye `#check`
    gør forsiden til en side der renderer et målt resultat — så den skal have
    donationslinjen, som `DU_DONATE` i siden nu sætter ind i resultatkortet.
13. **Samme tjek på de tre andre forsider.** Hvem: alle der lander på `mahope.tools`
    (4 besøgende, 100 % bounce), `cleancopy.tools` (7, 71 %) og `deskuptime.com/da/`.
    Tal: brug pr. uge pr. forside. Accept: hver forside har ét tjek der svarer på
    spørgsmålet i sin egen `<h1>`, og ingen har to primære handlinger over folden.
    Datagrund: målt 2/10 — alle tre forsider er kataloger, ikke værktøjer.
