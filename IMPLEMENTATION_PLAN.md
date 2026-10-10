# STATUS

- **10/10:** cleancopy.tools' tre HTML-to-Markdown-guider kører konverteren i
  artiklen (`ceo/artikel-konverter`). Licensvalideringen går gennem
  `net.js`, så en 429 forbliver endelig; uden kernen holder syvdagesreglen.
- **10/10:** deskuptime.coms to sider og mahope.tools' to forsider kører ét
  eksempel-tjek ved sidevisning (`ceo/deskuptime-auto-tjek`,
  `ceo/forside-eksempel`); baselineer: deskuptime.com 17 besøgende/28 d,
  100 % bounce, 0 s; `/`+`/da/` 10 besøgende, 89 % bounce. Donationen skal
  nu ventes ind, til læseren selv har skrevet en adresse.
- **10/10:** dependabot-PR #3 (undici 7.29.0 → 7.30.0 i `desktop/`) landet og
  lukket: 2 høje + 8 moderate advisories væk fra lockfilen.
- **10/10:** desktop-lockfilens sidste HØJE sårbarhed (`http-cache-semantics`
  4.2.0 → 4.3.0 via `overrides`) er lukket; `npm audit` 9 → 8 fund, alle
  moderate og kun i electron-build-kæden (`sprintf-js` har ingen rettet udgivelse).
- 0 åbne review-fund. Sentry: 0 uløste fejl (14 dage). 0 åbne PR'er.
- **PR-TJEK 10/10:** 0 åbne PR'er (undici-PR landet, se næste punkt).
  **BRANCH-TJEK 9/10:** `origin/ceo/hub-readme-note` kan slettes, men
  push --delete er spærret (❓).
- **CEO-kø #0** er færdig og merged; 0 åbent.
- **10/10:** `/contrast-checker` (EN+DA) viser nu også APCA Lc ved siden af
  WCAG-forholdet — polariteten 2.x-tallet smider ud (`ceo/apca-kontrasttjekker`).
  `site/apca.js` er en citatport af APCA 0.1.9 (W3, G-4g); de otte
  reference-værdier i `tests/apca.test.mjs` er regnet om med
  `Myndex/apca-w3@master` og stemmer tegn for tegn.
## Åbne review-fund

Ingen.

## Verificér deploy

- **VERIFICÉR DEPLOY:** konverteren i cleancopy.tools' tre artikler
  `ceo/artikel-konverter` 10/10-2026 — tjek at live
  `https://cleancopy.tools/blog/{html-to-markdown-cli,html-to-markdown-vscode,
  copy-as-markdown-chrome-extension}` indeholder `<script src="/net.js"></script>`
  FØR `<script src="/clean-copy-embed.js"></script>`, at
  `https://cleancopy.tools/net.js` og `/clean-copy-embed.js` svarer 200, og at
  formularen i artiklen konverterer (JS-kørsel kan ikke curles — det samme
  script kører på `/clean-copy-tool`, som er verificeret).

- **VERIFICÉR DEPLOY:** eksempel-tjek på mahope.tools' to forsider
  `ceo/forside-eksempel` 10/10-2026 — tjek at live `https://mahope.tools/` og
  `/da/` erklærer `example: 'example.com'` i `ONE_OFF_CHECK`, at kortet ved
  sidevisning siger «This is an example check»/«Dette er et eksempel-tjek» uden
  en donationslinje, og at formularen stadig kører ét kald for læserens egen
  adresse — med donationslinjen efter et rigtigt tjek.

- **VERIFICÉR DEPLOY:** eksempel-tjek på deskuptime.com
  `ceo/deskuptime-auto-tjek` 10/10-2026 — tjek at live
  `https://deskuptime.com/` og `/da/` erklærer `example: 'example.com'` i
  `ONE_OFF_CHECK`, at `/one-off-check.js` (200) indeholder `autoNote`, og at
  formularen stadig kører for læserens egen adresse.

- **VERIFICÉR DEPLOY OK 10/10:** APCA Lc på kontrasttjekkeren
  `ceo/apca-kontrasttjekker` 10/10-2026 — live EN+DA henter `/apca.js` (200),
  har `#apca-out` og batch-tabellens kolonne «APCA Lc» + forklaringen i
  hero-sektionen (set i live-HTML; JS-kørsel kan ikke curles).

- **VERIFICÉR DEPLOY OK 10/10:** `http-cache-semantics` 4.3.0 i desktop-lockfil +
  download-zip `ceo/desktop-http-cache` 10/10-2026 — live-zip'en er
  byte-identisk med `desktop/package.json`+`package-lock.json`; lockfilen
  resolver `http-cache-semantics` 4.3.0.
- **VERIFICÉR DEPLOY OK 10/10:** undici 7.30.0 i `desktop/package-lock.json` +
  download-zip `ceo/undici-sikkerhedsopdatering` 10/10-2026 — samme zip, lockfilen
  resolver `node_modules/undici` 7.30.0.
- **VERIFICÉR DEPLOY:** købsanker på gratis-downloads
  `ceo/free-downloads-paid-path` 9/10-2026 22:50 — **DEPLOY OK 10/10:** live
  `https://mahope.tools/free-downloads` viser sektionen «When the free files are
  not enough» med knappen «Buy EUComply Pro — $79/year per website», og både
  `/paid-templates` og `/compliance-report` svarer 200.
- **VERIFICÉR DEPLOY:** bog-kopi «client-ready report» `ceo/bogproeve-kopi`
  10/10-2026 — tjek at `https://mahope.tools/books/preview-{nis2-for-agencies,
  gdpr-for-agencies, eaa-checklist, eaa-shopify, cookie-consent-guide}` ikke
  længere skriver «client-ready report», men en PDF-man-udlevere-formulering
  («PDF report you can hand to a client») med prisen `$79/year per website`.
- **VERIFICÉR DEPLOY:** danske lenker + rød CI `ceo/da-vaerktoej-links`
  9/10-2026 20:50 — **DEPLOY OK 10/10:** `https://cleancopy.tools/da/clean-copy-tool`
  (200) viser konverteren på dansk, `https://mahope.tools/da/license-lookup`
  (200) viser «Find din licensnøgle» og er koblet til `/api/license/lookup` +
  `/api/license/deactivate`, og `/da/blog/kopier-tabel-til-excel` linker til
  `https://cleancopy.tools/da/clean-copy-tool`.
- **VERIFICÉR DEPLOY:** dansk licensøgning `ceo/da-license-lookup` 9/10-2026
  15:00 — **DEPLOY OK 10/10:** `https://mahope.tools/da/license-lookup` (200)
  viser «Find din licensnøgle» og formularens to API-kald findes i live-HTML.
- **VERIFICÉR DEPLOY OK 9/10:** scan-proxy POST + scanFejl fix `ceo/scan-fejl-post` — live `https://mahope.tools/scan-proxy` svarer 400 på POST med ugyldig URL (ruten er live og fungerer).
- **VERIFICÉR DEPLOY OK 9/10:** fire pushes `ceo/page-profile-compare`,
  `ceo/kontrast-selvtage-hero`, `ceo/page-profile-cta`, `ceo/plan-status-laengde`
  9/10-2026 — tjekket live: `/page-profile` har to URL-felter
  (`compare-url-a`/`compare-url-b`) og «Compare», bog-prøvesiden viser
  «Preface: Why This Book Exists», knappen «Or read the first chapters in your
  browser» findes på `/books/build-your-first-chrome-extension`, og
  `/color-blindness-simulator` linker til `/blog/color-blindness-simulation-check`.
  Fire ude-blivere pushes er nu live.

- **VERIFICÉR DEPLOY:** bog-prøvesider med betalt vej `ceo/bogproeve-betalt-vej`
  9/10-2026 14:3x — **DEPLOY OK 10/10:** live
  `https://mahope.tools/books/preview-{nis2-for-agencies,gdpr-for-agencies,
  eaa-checklist,eaa-shopify,cookie-consent-guide}` (200) viser
  EUComply Pro-sætningen med $79 pr. website pr. år, og `/compliance-report`
  viser «Buy EUComply Pro — $79/year».

- **VERIFICÉR DEPLOY OK 9/10:** eaa-action `ceo/eaa-github-action` — live
  `https://mahope.tools/downloads` (200) viser GitHub Action-skabelonen med
  `action.yml`, `--sarif` og `--fail-on`.
- **VERIFICÉR DEPLOY OK 9/10:** sitemap-scanning `ceo/sitemap-scan` — live
  `https://mahope.tools/scan` og `/da/scan` (200) viser Pages/Sitemap-skifteren
  i heroen («Sider» på dansk).
- **VERIFICÉR DEPLOY OK 9/10:** compliance-score-simulator `ceo/compliance-score-simulator`
  — live `https://mahope.tools/compliance-report` viser score-barer med «Nu» vs
  «Fixed» og point-værdier pr. fix («Fix all N error(s) → +N points»).
- **VERIFICÉR DEPLOY OK 8/10:** GDPR-brudsgenerator `ceo/gdpr-breach-report-generator` —
  live EN/DA svarer 200, 72-timers-fristen vises, «Generate report»/«Lav rapport»
  viser rapporten med link til `/paid-templates`.
- **VERIFICÉR DEPLOY OK 8/10:** url-inspector-folden `ceo/url-inspector-fold-pro-link` —
  live `https://mahope.tools/url-inspector/` viser URL-feltet og «Inspect» i heroen
  (200), og `id="ui-pro-heading"` findes to steder i markup.
- **VERIFICÉR DEPLOY OK 8/10:** DeskUptime-tjekket i heroen `ae08878a` — live
  `deskuptime.com` og `deskuptime.com/da/` viser URL-feltet i heroen, tjek virker.
- **VERIFICÉR DEPLOY OK 8/10:** Clean Copy-konverteren i heroen `2085f465` — live
  `cleancopy.tools` og `cleancopy.tools/da/` viser konverteringsformularen i
  heroen, konvertering virker.
- **VERIFICÉR DEPLOY OK 8/10:** text-on-image-checker del-link `2613639a` — live
  `https://mahope.tools/text-on-image-checker` og `-da` svarer 200 og viser
  «Share this check»-knappen i resultatet (delt-linket gendanner tilstanden).
- **VERIFICÉR DEPLOY OK 8/10:** compliance-report-folden `ceo/compliance-hero-buy`
  — live `https://mahope.tools/compliance-report` (200) viser «See pricing —
  EUComply Pro» i heroen, og `id="pricingSection"` findes med den ene «Buy
  EUComply Pro — $79/year»-knap.
- **VERIFICÉR DEPLOY OK 8/10:** text-on-image-eksport `ceo/text-on-image-export` —
  live `https://mahope.tools/text-on-image-checker` viser «Download the marked
  check» og `/text-on-image-checker-da` viser «Hent det markerede tjek».
- **VERIFICÉR DEPLOY OK 8/10:** DeskUptime-frontside `ceo/deskuptime-bounce` — live
  `deskuptime.com` og `deskuptime.com/da` viser klar værdi og én købsknap i
  heroen, konvertering er tydelig.

## Åbne opgaver

1. ✅ **Tjek CI-kørsel for `bfd9889` og live-deployet** — AFKRYSET 10/10
   (`gh run list`: success på `7154b50a`; alle 11 commits siden `74963e5c`
   verificeret live — se STATUS).

3. ✅ **Desktop-lockfilens sårbarheder** — den HØJE (`http-cache-semantics`)
   løftet 4.2.0 → 4.3.0 via `overrides` 10/10. De 8 moderate sidder alle i
   electron-build-kæden og stammer fra `sprintf-js` (≤ 1.1.3, ingen rettet
   udgivelse findes) samt `http-cache-semantics`-forgreningen under
   `@electron/get`. `electron-builder` er allerede nyeste (26.15.3); nærmeste
   «fix» er et nedgradér til 26.5.0. Kun build-tid, ikke i den udgivne app.

4. **Konvertering kan ikke måles uden `STATS_TOKEN`.** Hvorfor: `/api/stats`
   svarer 401, så trafikrangeringer er vor egen links-tælling, ikke besøg.
   Accept: `GET /api/stats` med token svarer 200. *BLOCKED: Venter på Mads til
   STATS_TOKEN — uden token returnerer endpointet 401.*

5. **`bugbottle.dev` er ude af deploy-matrixen igen.** Hvorfor: vores 7 ruter
   ville overskrive den rigtige produktside (61 ruter) og gav tre røde porte.
   Accept: Mads siger ja til at udgive vores landing. *(❓ Til Mads.)*

7. **Bogen har ingen DA-udgave.** Hvorfor: de seks bøger er på engelsk, og der
   findes ingen `/da/books/*`-ruter, så bogsiders hreflang har intet dansk par.
   Accept: en DA-udgave af de to vigtigste som EPUB, eller en synlig dansk note.
   *(Beslutning — ❓.)*

9. **En sitemap-rute må ikke have en død eneste handling.** Hvorfor: porten
   dømmer kun de to ruter i `tools/unavailable_routes.json`. Accept: porten
   finder den, hvis den skrives i manifestet. *(Kun relevant ved nye sådanne
   sider — ikke en opgave i sig selv.)*

22. **En `ceo/*`-gren er ikke arbejde, fordi den ligger uden for `main`.** Hvorfor:
   alle fire målte 5/10 var dubletter. Accept: før en gren nævnes i planen skal
   `git cherry main <gren>` være læst, og dens rørte filer sammenlignet
   fil-for-fil med `main`.

## ❓ Til Mads

- **🔴 `OPENROUTER_API_KEY` mangler på workeren — assistenten er stadig slukket.**
  Når du sætter nøglen: fjern `noindex` fra `site/compliance-ai.html` +
  `site/da/compliance-ai.html`, og sæt `"available": true` i `tools/ai_cta.json`
  og kør `python3 tools/check_ai_cta_honesty.py --apply`.
- **🔴 `STATS_TOKEN` på workeren.** Én secret, og så kan konvertering måles i
  stedet for gættes. Uden den er `/api/stats` 401.
- **🟡 `bugbottle.dev` er ikke med i deploy-matrixen.** Domænet serveres af den
  rigtige produktside; vores 7-ruters landing ville overskrive den. Sig til,
  hvis den skal med i stedet.
- **🔴 To betalte desktop-apps kan ikke aktiveres.** De shippede binære
  (`transmute` v0.2.1, `deskuptime` desktop-v0.2.7) har Lemon Squeezy indbygget,
  og kilderne ligger i private repos, hvor du selv laver releases.
- **🔴 Bogen er gratis, men Stripe har et betalt bundlet produkt.** Kontrakten
  lister `eu-compliance-ebook-bundle` til $29, mens syv sider siger «Free».
  Din beslutning, fordi det er dit navn på kvitteringen.
- **🟡 Skal scanner- og AI-banneren ligge over folden på de 172 sider?**
- **🟡 Skal det frie flerstedes-tjek få en kundeklar rapport?** Den flytter en
  $79-årslinje.
- **🟡 `indexnow_ping.sh` kaldes aldrig** — et ping er et udadvendt kald; sig til.
- **🟡 `/blog/` siger «96 Danish guides», men 11 ligger på cleancopy.tools.**
- **🟡 Skal værktøjssiderne vise livstidsprisen?** Portene siger nej til et
  prislink i pro-kortet.
- **Search Console:** tilføj de fem domæner som properties.
- **Plugin-version:** kunder på Clean Copy 1.1.0 henter ikke den rettede zip —
  kræver en release, som er din.
## Feature-kø

Prioriteret efter hvor tæt den er på penge. Baseline er målt på den **byggede**
side; tallene er ikke vores egen trafik. Alt det leverede (1–44) står i
`docs/plan-arkiv.md`.

51. **`/page-profile`: sammenlign to URL'er i browseren.** Hvem: SEO-bureauer.
      Tal: konvertering til Page Profile Pro ($19/år). Accept: to URL-felter, én
      diff med score-forskel pr. kontrollpunkt, Pro-funktionen bag licenskontrol.
      Datagrund: CLI'en har allerede `--compare`; web-siden profilerte én URL.
      **LEVERET** `ceo/page-profile-compare` — live verificeret 9/10 (to felter
      + «Compare»).
52. **`/free-downloads`: én købsknap til de betalte skabelonsæt.** Hvem: de 25
      downloadbesøg/uge på mahope.tools. Tal: konvertering til de betalte
      skabeloner ($29–$149) og EUComply Pro ($79/år). Accept: hubben viser pr.
      gratis fil hvad den dækker og har én købsknap der virker. Datagrund:
      privacy-policy-template.md (5) og ropa-template.md (3) er de mest hentede
      filer, og hubben har i dag intet købsanker.
      **LEVERET** `ceo/free-downloads-paid-path` — kortet «When the free files
      are not enough» med én EUComply Pro-knap og vej til `/paid-templates`.

53. **cleancopy.tools: dansk udgave af web-værktøjet.** Hvem: de 3 besøgende/28
     dage på `/da/`-stierne. Tal: konvertering til Clean Copy Pro ($19/år).
     Accept: `/da/clean-copy-tool` med batch og licensaktivering på dansk.
     Datagrund: DA-forsiden lover batch-konvertering «i webværktøjet», men
     værktøjet findes kun på engelsk. **LEVERET** `ceo/clean-copy-da-tool`.

45. **e-bøger: læs kapitel 1 gratis i browseren.** Hvem: dem der laster de seks
     EPUB'er (top-downloads). Tal: downloads og konvertering til $29-bundlet.
     Accept: en prøveside der viser det første kapitel og linker til bundlet.
     Datagrund: `/books/` er top-download, men der er ingen vej fra læsning til køb.
     **LEVERET** `ceo/bog-proeveside` + `ceo/bog-forhaandsvisning` (seks prøvesider);
     den betalte vej (EUComply Pro på `/compliance-report`) kom i
     `ceo/bogproeve-betalt-vej` 9/10.
46. **cleancopy.tools: batch-konverter i web-værktøjet.** Hvem: de 18 besøgende/28d
     (bounce 81%). Tal: konvertering til Clean Copy Pro ($19/år). Accept: indsæt
     flere HTML-bidder, få flere Markdown-bagter. Datagrund: Pro-funktion bag
     licenskontrol (open-core), web-værktøjet er den gratis indgang.
     **LEVERET** — batch-sektionen kører i EN og DA bag licenskontrollen.
47. **GitHub Action for eaa-scanner.** Hvem: de 91 npm-downloads/uge. Tal:
     adoption. Accept: `action.yml` der scanner og uploader SARIF. Datagrund:
     SARIF-outputet (feature 38) findes; kræver Marketplace-publicering (❓).
     **LEVERET** `ceo/eaa-github-action` — live på `/downloads` verificeret.
48. **/page-profile: sammenlign to URL'er.** Hvem: SEO-bureauer. Tal: konvertering
     til Page Profile Pro ($19/år). Accept: `page-profile --compare A B` giver
     en diff. Datagrund: Pro-funktionen findes ikke endnu; CLI'en har allerede
     score og grade.
49. **Guide: farveblindhedssimulering.** Hvem: de 5 besøgende/28d på
     `/color-blindness-simulator` + 9 på kontrastartiklen. Tal: trafik til
     simulatoren og videre til `/scan`/EUComply Pro. Accept: EN+DA-guide med
     målte tal. **LEVERET** `ceo/farveblindhed-artikel`.
54. **`deskuptime.com`: 11 besøg, 100 % bounce, 0 s besøgstid.** Hvem: alle der
      lander på forsideen. Tal: fra 0 s til en reel læsning, og CTR til CLI/Pro.
      Accept: fundet og rettet hvad der får besøgende til at forlade siden med det
      samme (0 s tyder på fejl før indholdet vises). Datagrund: Plausible
      28 dage: besøgstid 0 s og bounce 100 % — den eneste af de tre måldomæner.
      **LEVERET** `ceo/deskuptime-auto-tjek` (kunne ikke bevise en fejl: alle
      aktiver 200, `/api/url-inspect` svarer). Rettet på den tætteste grund:
      h1'en spurgte tre ting, og svaret ventede på et tastetryk ingen kom med.
      EN+DA kører nu ét selvvalgt eksempel ved sidevisning (gennem
      `example:` i `ONE_OFF_CHECK`), kortet siger at det er et eksempel, og
      `#url=`-håndflek og et allerede afsendt submit annullerer det.
      Dommerne i `tests/scan-clients.test.mjs` §22 (A–E) dømmer rødt på den gamle
      kode: 608/608 kører grønt.
55. **EUComply: kundeklar rapport ud af det frie multi-site-tjek.** Hvem: bureauer
      med kunder. Tal: flytter en $79/årslinje. Accept: rapport-knappen på
      checket der fører til `/paid-templates` eller Pro. Datagrund: spørger Mads
      først (🟡 i ❓) — rapportkittet til $69 er den nærmeste eksisterende vej.
56. **`/contrast-checker`: APCA Lc ved siden af WCAG-forholdet.** Hvem: alle der
      tjekker kontrast — kontrasttjekkeren er den mest brugte gratis indgang til
      EUComply Pro. Tal: PRO-tjek på siden er en $79/årslinje, og Lc er det
      WCAG-3-tal kunder spørger efter. Accept: både EN og DA viser Lc pr. par i
      både enkelt- og batch-tjekket. **LEVERET** `ceo/apca-kontrasttjekker`.
      Baseline: siden står ikke i Plausibles top-sider (ikke målelig fra
      promptens data), så effekten måles via PRO-tjek på `/api/stats` (❓).

57. **mahope.tools `/`: fordsiden skal også svare sig selv.** Hvem: de 10
      besøgende/28 d på `/` (89 % bounce — målt 10/10). Tal: fra bounce til et
      set eksempel-svar, og videre til `/scan` og EUComply Pro ($79/år).
      Accept: `/` erklærer `example:` så eksemplet kører ved sidevisning, på
      sidens eget sprog. Datagrund: deskuptime.com sad i samme mønster (17
      besøgende, 100 % bounce, 0 s) og er rettet i `ceo/deskuptime-auto-tjek` —
      det er én linje i `ONE_OFF_CHECK`, ikke ny kode.
      **LEVERET** `ceo/forside-eksempel`: EN+DA kører ét eksempel-tjek ved
      sidevisning. Samme ændring flyttede donationslinjen: den kommer ikke mere
      på et svar, siden kørte af sig selv — den kommer først, når læseren selv
      har skrevet en adresse. Dommerne i `tests/scan-clients.test.mjs` §23
      (A/B/C/D) dømmer rødt på den gamle kode: 618/618 kører grønt.

 58. **cleancopy.tools: konverteren indeni artiklerne.** Hvem: de 3+2+2 besøgende
       på de tre html-to-markdownartikler (bounce 50–67 %). Tal: brug af
       konverteren og Clean Copy Pro ($19/år). Accept: artiklen kører den samme
       kerne som `/clean-copy-tool` i browseren, med licenskontrol foran batch.
       Datagrund: artiklerne linker til værktøjet, men indeholder det ikke —
       mahope.tools' kontrastartikel har vist, at værktøj i teksten er hvad der
       flytter læseren fra læsning til brug.
       **LEVERET** `ceo/artikel-konverter` — de tre guides indeholder
       konverteren; licensvalideringen går gennem `net.js` (guiderne indlæser
       det foran embed-scriptet), og `tests/clean-copy-embed.test.mjs` dømmer
       64 kontroller på den shippede kode med den rigtige kerne indlæst.

