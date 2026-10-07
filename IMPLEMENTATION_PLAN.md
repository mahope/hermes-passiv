# STATUS
- **Kontrast pr. synstype og billed-simulering i farveblindhedssimulatoren
  leveret 7/10** (`ceo/cvd-kontrast`, `ceo/cb-billede-simulering`):
  `site/cb-contrast.js` regner WCAG-forholdet for hver synstype med samme
  `CB_SIM.simulate` som tabellen, og et billede kan trækkes ind, indsættes eller
  vælges og tegnes af samme Machado-model. Målt i Chromium 390/1280 px: 0
  overflow, 0 JS-fejl. Gate **GRØN — 182 steps**. Baseline: **3** besøgende/28 dage.
- **Farver ud af et billede i paletgeneratoren leveret 7/10**
  (`ceo/palette-billede`): et logo eller skærmbillede kan trækkes ind, indsættes
  eller vælges, og de dominerende farver bliver klikbare prøver der sætter
  basisfarven. Målt i Chromium 390/1280 px: 0 overflow, 0 JS-fejl, gate
  **GRØN — 183 steps**. Baseline: **0** besøgende/28 dage på `/palette-generator`.
- CEO-kø punkt 0 (review-fund 29/9) verificeret færdigt: alle fem punkter
  rettet (`10f95b42`, `b772a466`, `67092c4c`, `e37b30a6`), gaten grøn.
- **Sentry er sat op og testet** (worker 149-246, test 1748-1833): DSN i kode,
  kun produktion, ingen PII, ingen traces/replay. «Ingen uløste fejl» betyder
  ingen fejl — ikke at intet sendes.
- **Alle fire VERIFICÉR DEPLOY-noter er live og lukket** 7/10.
- **Sporingen virker** (målt 6/10): `contrast-measured` i `/api/results` efter
  33 s. Ærlig baseline: **0 rigtige** kørsler.
- **DeskUptime 'no phone-home' rettet** (`7dc00071`): hero + FAQ på EN/DA
  forklarer nu ærligt at Pro-licensaktivering checker op.
- **Batch-kontrasttjek leveret 7/10** (`ceo/kontrast-batch`): indsæt en liste
  af farvepar (ét pr. linje) og få ratio + AA/AAA-dom for hvert i én tabel.
  Verificeret i Chromium 390/1280 px: ingen overflow, gate **GRØN**. Baseline:
  **0** batch-kørsler.
- **Donation-linje tilføjet til kontrast-checkerne** (`ceo/donation-kontrast-checker`):
  `contrast-checker.html` og `-da.html` manglede linjen, så `donation-paths-selftest`
  var rød i CI. Gate **GRØN**.

## Åbne review-fund

Ingen. Review-fund 7/10 (deskuptime-kopi) er rettet og merged (`7e101213`):
hero/FAQ og Pro-kortet siger nu alle «previous licence provider», og porten
kræver den formulering.

## Verificér deploy

- **VERIFICÉR DEPLOY:** batch-kontrasttjek `ceo/kontrast-batch` 7/10 — tjek at
  live `/contrast-checker` og `/contrast-checker-da` bærer `id="batch-input"`,
  `id="batch-run"` og `id="batch-tbody"`, og at indsætning af par viser tabel.
- **VERIFICÉR DEPLOY:** billed-farver i paletgeneratoren `ceo/palette-billede`
  7/10 — tjek at live `/palette-generator` og `-da` bærer
  `<script src="/palette-image.js">` og `id="pg-img-swatches"`.
- **VERIFICÉR DEPLOY:** kontrast pr. synstype `ceo/cvd-kontrast` 7/10 — tjek at
  live `/color-blindness-simulator` og `-da` bærer `id="cvd-contrast"` og
  `<script src="/cb-contrast.js">`, og at tabellen tegner fire rækker.
- **VERIFICÉR DEPLOY:** billed-simulering `ceo/cb-billede-simulering` 7/10 — tjek
  at live `/color-blindness-simulator` og `-da` bærer `id="cbi-cv"`,
  `id="cbi-file"` og `<script src="/cb-image.js">`.
- **VERIFICÉR DEPLOY:** dansk DeskUptime-pris/pro-tabel
  `ceo/da-deskuptime-gate` 7/10 — tjek at live `/da/` bærer «Køb DeskUptime
  Pro — 19 USD én gang» og «én gang, 3 maskiner».
- **VERIFICÉR DEPLOY:** DeskUptime licens-kopi `ceo/deskuptime-kopi-ensartet`
  7/10 — tjek at live `/` og `/da/` ikke længere siger «mahope.tools» i
  hero/FAQ, men «previous licence provider» / «tidligere licensudbyder».
- **DEPLOY OK 7/10:** gratis/Pro-tabel + købsknap på de to danske
  farveværktøjssider `ceo/da-farvevaerktoejer-koeb`. Live: begge bærer
  `id="pro"`, `Køb EUComply Pro — $79/år pr. website` og betalingslinket.
- **DEPLOY OK 7/10:** gratis/Pro-tabel + købsknap på de to engelske
  farveværktøjssider `ceo/farve-vaerktoejer-koeb`. Live: begge bærer
  `id="pro"`, `Buy EUComply Pro — $79/year per website` og betalingslinket.
- **DEPLOY OK 7/10:** farveforslaget i kontrastværktøjet `ceo/kontrast-fix-farve`.
  Live: `#cc-fix-use` findes, og `#ffd700` på `#ffffff` giver `#8b7500`
  (ratio 4,52). Samme på `/contrast-checker-da`.
- **DEPLOY OK 7/10:** billede-drop-og-indsaet `ceo/billede-drop-og-indsaet`.
  Live: `text-on-image-core.js` har `drop`, `paste` og `loadFile`.
- `pro-kortet på de fire scanneresider` er **DEPLOY OK 6/10**:
alle fire sider bærer `compliance-report#url=` i den udgivne markup
(`/scan`, `/scan-da`, `/compliance-site-check`, `/da/compliance-site-check` —
den danske scan-rute hedder `/scan-da`, **ikke** `/da/scan`, som den gamle note
påstod; den findes ikke og svarer 404), noten «See what Pro adds before you buy»
er væk på alle fire, og `#url=`-vejen er fulgt i Chromium mod live: feltet bliver
`https://example.com` og rapporten kører (95/100, grade A) uden et klik.

## Åbne opgaver

3. **Konvertering kan ikke måles uden `STATS_TOKEN`.** Hvorfor: `/api/stats`
   svarer 401 siden uge 37, så næsten hver linje i enhver trafikrangering er vor
   egen links-tælling, ikke besøg. Accept: `GET /api/stats` med token svarer 200.
   *(Blockeret på Mads — se ❓.)* **Målt 5/10:** resultaterne (`/api/results`,
   feature-kø 6) og købsforsøgene (`/api/conversion`) er nu *begge* læsbare uden
   token, så de **22** nye kontroller dømmer at de to lister hver især er sig egen
   — et resultat kan ikke læses som et køb. Kun **beløb og udleverede licenser**
   mangler stadig, og de står i Stripe. Opgaven står derfor åben, men den er ikke
   længere blokeringen for at prioritere.

4. **`bugbottle.dev` deployes ikke.** Hvorfor: `deploy-sites.yml`-matrixen
   deployer kun tre domæner. **2/10 er følgen målt og lukket:** de fire
   BugBottle-guider ligger på `mahope.tools`, så `/blog/` har ingen døde links;
   domænets egen forside ligger stadig i `UNMANAGED_DOMAINS`. Accept: domænet på
   Pages og fjernet af `UNMANAGED_DOMAINS`, eller fjernet fra `TRACKING_DOMAINS`.
   *(Beslutning — se ❓.)*

6. **Bogen har ingen DA-udgave, og læsevisningen gør det tydeligt.** Hvorfor: de
   seks bøger er på engelsk. Målt 2/10: der findes **ingen** `/da/books/*`-ruter,
   så bogsiders hreflang har intet dansk par. Accept: enten en DA-udgave af de to
   vigtigste som EPUB i `ebook/`, eller en synlig dansk note på bogside-ruterne.
   Kræver beslutning — se ❓.

8. **En sitemap-rute må ikke have en død eneste handling.** Hvorfor: porten
   dømmer kun de to ruter i `tools/unavailable_routes.json`. Accept: porten
   finder den, hvis den skrives i manifestet. *(Kun relevant når vi tilføjer flere
   sådanne sider — ikke en opgave i sig selv.)*

21. **En `ceo/*`-gren er ikke arbejde, fordi den ligger uden for `main`.** Hvorfor:
    målt 5/10 — alle fire var dubletter, og to ville have reverteret
    `3755b96f` + `158715e9`. Accept: før en gren nævnes i planen skal
    `git cherry main <gren>` være læst, og dens rørte filer sammenlignet fil-for-fil
    med `main`. En `+` er ikke nok, fordi patch-id skjuler at main er ældre.


## ❓ Til Mads

- **🔴 `OPENROUTER_API_KEY` mangler på workeren — assistenten er stadig slukket.**
  Sagen siger at assistenten er slukket og byder på scanner, erklæringsgenerator
  og de tre bøger, og begge ruter er ude af sitemap og `llms.txt`. **Når du sætter
  nøglen:** fjern `<meta name="robots" content="noindex,follow">` fra
  `site/compliance-ai.html` + `site/da/compliance-ai.html`. **Banneren på
  AI-siderne følger samme nøgle** (så mange, `check_ai_cta_honesty.py` tæller
  dem hver kørsel): sæt `"available": true` i `tools/ai_cta.json`,
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
- ~~**🔴 `site/_worker.js` er ikke hele workeren bag mahope.tools.**~~ **Fejlmålt
  4/10, lukket.** Noten byggede på at live `/api/compliance-scan` svarer med **9**
  tjek mens `CSC_CHECKS` «havde 7» — målt med et regex der kun greb u citationattegn,
  så de to nøgler med citation (`security-headers`, `meta-tags`) blev set borte.
  `CSC_CHECKS` har **9**, og live svarer præcis de samme ni i samme rækkefølge.
  `/api/profile`'s `max_score: 21` er ligeledes identisk med kilden. **Live-kilden
  er `site/_worker.js`**, og ingen afgave afklæring fra dig.
- **Search Console:** tilføj de fem domæner som properties (`mahope.tools`,
  `cleancopy.tools`, `deskuptime.com`, `bugbottle.dev`, `transmute.run`).
  Sitemap og robots er målt korrekte på de fire sites missionen udgiver.
- **Plugin-version:** kunder på Clean Copy 1.1.0 henter ikke den rettede zip.
  Kræver en version bump — og det er en release, som er din. `ceo/hub-readme-note`
  på origin er forældet (kun en plan-note fra 26/9) og ligger der, indtil du siger
  til.

## Feature-kø

Prioriteret efter hvor tæt den er på penge. Baseline er målt på den **byggede**
side; tallene er ikke vores egen trafik. Alt det leverede (1–22) står i
`docs/plan-arkiv.md`.

23. **Del din palet med et link.** Hvem: en designer der vil sende den palet hun
    lige byggede til en kollega. Tal: besøgende på `/palette-generator` (0/28
    dage, Plausible 7/10). Accept: et `#`-link gendanner basisfarve og baggrund,
    og begge sprog læser det. Datagrund: simulatoren har allerede
    `cb-share-core.js`, og en palet er det ene man videresender.

25. **Farvenavn ved siden af hex.** Hvem: en ikke-designer der fik en farve ud af
    et billede. Tal: besøgende på `/palette-generator` (0/28 dage). Accept: hver
    prøve viser nærmeste CSS-navn (`crimson`, `slateblue`), så man kan tale om
    farven. Datagrund: `PALETTE_IMAGE` giver hex; navnet er den næste sætning en
    ikke-designer bruger.

26. **Paletten under farveblindhed.** Hvem: en designer der netop har bygget en
    palet. Tal: besøgende på `/color-blindness-simulator` (3/28 dage). Accept:
    hvert farvepar vises simuleret for protan/deutan/tritan med samme pr.
    synstype-kontrast som simulatoren. Datagrund: WCAG-kontrast fanger ikke at
    rød og grøn kollapser; modellen findes allerede i `CB_SIM`.
