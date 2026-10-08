# STATUS

- **8/10:** CI på `main` var rød i fem gate-steps, alle rettet på
  `ceo/eaa-github-action`: `storage-claims`-selftesten ramte det forkerte
  `rateLimitIp`-kald efter sitemap-featuren; `first-action` fandt to
  primærknapper i DeskUptime-folden (købslinket er nu sekundært mod `#pro`);
  `contrast-sampling` dømte artikel-demoens `mount()` som værktøj;
  `catalog-where` havde forældede linjenumre; `scan-events` talte ét scan som
  to. Gate grøn (alle steps).
- **8/10:** feature 47 (GitHub Action for eaa-scanner) leveret: `action.yml`
  scanner og uploader SARIF; CLI'en skriver nu rapporten før fail-on-dommen, og
  `--fail-on never` afvises ikke længere. Testen dømmer action, workflow-skabelon
  og salgsside og kører CLI'en for rigtigt.
- **8/10:** `bugbottle.dev` er bevidst ude af deploy-matrixen igen — vores
  7 ruter ville overskrive den rigtige produktside. Afventer Mads' ja (❓).
- **8/10:** planens STATUS skåret til ≤25 linjer; historik i `docs/plan-arkiv.md`.
- 0 åbne review-fund. Sentry: 0 uløste fejl (14 dage). 0 åbne PR'er.
- **PR-TJEK 8/10:** 0 åbne PR'er. **BRANCH-TJEK:** ikke kørt.
- **CEO-kø #0** er færdig og merged; 0 åbent.
- **VERIFICÉR DEPLOY:** eaa-action `ceo/eaa-github-action` — tjek at
  `https://mahope.tools/downloads` viser GitHub Action-skabelonen med
  `--sarif` og `--fail-on`, og at siden stadig svarer 200.
## Åbne review-fund

Ingen.

## Verificér deploy

- **VERIFICÉR DEPLOY:** compliance-score-simulator `ceo/compliance-score-simulator`
  — tjek at `https://mahope.tools/compliance-report` viser score-simulatoren
  (score-bar med «Nu» vs «Fixed» og point-værdier per fix).
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
- **VERIFICÉR DEPLOY OK 8/10:** gate-rettelsen `ceo/first-action-form-hero` —
  påvirker intet i markup; CI grøn på `main`.
- **VERIFICÉR DEPLOY OK 8/10:** free-tools-katalog `ceo/free-tools-hero-catalog` —
  live `https://mahope.tools/free-tools` og `/da/free-tools` viser kataloget med
  7 kategorier i folden (EN: `#catalog-heading` "Tools by category", DA:
  "Værktøjer efter kategori"), og «Alle værktøjer» / «All tools» ruller til den.
  Gate grøn.
- **VERIFICÉR DEPLOY OK 8/10:** free-tools-katalog `ceo/free-tools-hero-catalog` —
  live `https://mahope.tools/free-tools` og `/da/free-tools` viser kataloget med
  7 kategorier i folden (EN: `#catalog-heading` "Tools by category", DA:
  "Værktøjer efter kategori"), og «Alle værktøjer» / «All tools» ruller til den.
  Gate grøn.
- **VERIFICÉR DEPLOY OK 8/10:** compliance-report-folden `ceo/compliance-hero-buy`
  — live `https://mahope.tools/compliance-report` (200) viser «See pricing —
  EUComply Pro» i heroen, og `id="pricingSection"` findes med den ene «Buy
  EUComply Pro — $79/year»-knap.
- **VERIFICÉR DEPLOY OK 8/10:** compliance-report-prissektionen
  `ceo/compliance-report-pricing-visible` — live `https://mahope.tools/compliance-report`
  (200) viser `#pricingSection` med «See pricing — EUComply Pro», «No licence
  yet?»-kortet og «Buy EUComply Pro — $79/year per website»-knappen.
- **VERIFICÉR DEPLOY OK 8/10:** text-on-image-eksport `ceo/text-on-image-export` —
  live `https://mahope.tools/text-on-image-checker` viser «Download the marked
  check» og `/text-on-image-checker-da` viser «Hent det markerede tjek».
- **VERIFICÉR DEPLOY OK 8/10:** DeskUptime-frontside `ceo/deskuptime-bounce` — live
  `deskuptime.com` og `deskuptime.com/da` viser klar værdi og én købsknap i
  heroen, konvertering er tydelig.
- **VERIFICÉR DEPLOY:** sitemap-scanning `ceo/sitemap-scan` — tjek at
  `https://mahope.tools/scan` og `/da/scan` viser Pages/Sitemap-skifteren i
  heroen, og at en sitemap-URL giver et multi-resultat med alle sider.

## Åbne opgaver

3. **Konvertering kan ikke måles uden `STATS_TOKEN`.** Hvorfor: `/api/stats`
   svarer 401, så trafikrangeringer er vor egen links-tælling, ikke besøg.
   Accept: `GET /api/stats` med token svarer 200. *BLOCKED: Venter på Mads til
   STATS_TOKEN — uden token returnerer endpointet 401.*

4. **`bugbottle.dev` er ude af deploy-matrixen igen.** Hvorfor: vores 7 ruter
   ville overskrive den rigtige produktside (61 ruter) og gav tre røde porte.
   Accept: Mads siger ja til at udgive vores landing. *(❓ Til Mads.)*

6. **Bogen har ingen DA-udgave.** Hvorfor: de seks bøger er på engelsk, og der
   findes ingen `/da/books/*`-ruter, så bogsiders hreflang har intet dansk par.
   Accept: en DA-udgave af de to vigtigste som EPUB, eller en synlig dansk note.
   *(Beslutning — ❓.)*

8. **En sitemap-rute må ikke have en død eneste handling.** Hvorfor: porten
   dømmer kun de to ruter i `tools/unavailable_routes.json`. Accept: porten
   finder den, hvis den skrives i manifestet. *(Kun relevant ved nye sådanne
   sider — ikke en opgave i sig selv.)*

21. **En `ceo/*`-gren er ikke arbejde, fordi den ligger uden for `main`.** Hvorfor:
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

45. **e-bøger: læs kapitel 1 gratis i browseren.** Hvem: dem der laster de seks
    EPUB'er (top-downloads). Tal: downloads og konvertering til $29-bundlet.
    Accept: en prøveside der viser det første kapitel og linker til bundlet.
    Datagrund: `/books/` er top-download, men der er ingen vej fra læsning til køb.
46. **cleancopy.tools: batch-konverter i web-værktøjet.** Hvem: de 18 besøgende/28d
    (bounce 81%). Tal: konvertering til Clean Copy Pro ($19/år). Accept: indsæt
    flere HTML-bidder, få flere Markdown-bagter. Datagrund: Pro-funktion bag
    licenskontrol (open-core), web-værktøjet er den gratis indgang.
47. **GitHub Action for eaa-scanner.** Hvem: de 91 npm-downloads/uge. Tal:
    adoption. Accept: `action.yml` der scanner og uploader SARIF. Datagrund:
    SARIF-outputet (feature 38) findes; kræver Marketplace-publicering (❓).
48. **/page-profile: sammenlign to URL'er.** Hvem: SEO-bureauer. Tal: konvertering
    til Page Profile Pro ($19/år). Accept: `page-profile --compare A B` giver
    en diff. Datagrund: Pro-funktionen findes ikke endnu; CLI'en har allerede
    score og grade.

33. **`/compliance-report`: virkende vej fra den frie rapport til Pro.** Hvem: de
    besøgende der kører det gratis tjek. Tal: `checkout.pages` i
    `reports/weekly/2026-41.json` — kun `/compliance-report` har et købstal (1).
    Accept: efter en scanning er `#pricingSection` synlig, og rapporten slutter
    med et opgraderingskort med pris og købsknap. Datagrund: `renderReport()`
    skjulte prissektionen, så hero- og rapportlinket var døde.
    **LEVERET** `ceo/compliance-report-upgrade-path`; JS-skjulningen fuldført
    `ceo/compliance-report-pricing-visible`.

34. **`/scan`: kør et helt sitemap i én scanning.** Hvem: bureauer der tjekker en
    kundes sider. Tal: scans (`health.scans=51`/uge) og konvertering til EUComply
    Pro ($79). Accept: indsæt en sitemap-URL, få ét samlet scorekort og én delt
    rapport. Datagrund: flerside-tjekket findes kun bag Pro.
    **LEVERET** `ceo/sitemap-scan`.

36. **`/text-on-image-checker`: eksportér det markerede tjek som billede.** Hvem:
    de 6 besøgende på værktøjet (top-værktøjsside i ugerapporten). Tal:
    besøgende/brug. Accept: en «Download the marked check»-fil med dommen
    indbrændt. Datagrund: del-linket findes, men billedet gør ikke.
    **LEVERET** `ceo/text-on-image-export`.

37. **`/deskuptime`: vis Pro-forskellen i selve tjekresultatet.** Hvem: de 8
     besøgende/28 dage, der alle forlader forsiden (bounce 100%). Tal: bounce på
     `/` og konvertering til DeskUptime Pro ($19). Accept: resultatet viser hvad
     online-overvågning tilføjer. Datagrund: Plausible 7/10. **LEVERET** JavaScript-iend
     `site/one-off-check.js` og note i `site/deskuptime/index.html`.

38. **eaa-scanner: SARIF-output til GitHub code scanning.** Hvem: de 91
     npm-downloads/uge — stærkeste adoption. Tal: downloads og CI-integration.
     Accept: `--sarif` giver et gyldigt SARIF 2.1.0-dokument med regler og fund.
     Datagrund: udviklere bruger allerede CLI'en, men resultatet kunne ikke vises
     i GitHubs Security-tab. **LEVERET** `ceo/eaa-sarif`.

39. **Privatlivspolitik-generator.** Hvem: de 9 downloads/uge af
     privatlivsskabeloner på mahope.tools. Tal: downloads og konvertering til
     EUComply Pro ($79). Accept: en guide der stiller spørgsmål og genererer en
     tilpasset politik. Datagrund: skabelonerne er top-downloads, men er statiske.
     **LEVERED** *Privacy notice generator* kører client-side i begge sprog
     (`/privacy-notice-generator` og `/privacy-notice-generator-da`), er linket
     fra forsiden og `free-tools`, og matcher acceptkriteriet om at stille spørgsmål
     og generere en tilpasset politik.

40. **GitHub Action for eaa-scanner.** Hvem: udviklere der vil scanne i CI. Tal:
     adoption. Accept: en `action.yml` der kører scanneren og uploader SARIF.
     Datagrund: SARIF-outputet (feature 38) gør det muligt. *(Kræver publicering
     på GitHub Marketplace — ❓ Til Mads.)*

41. **DeskUptime forside: 100 % bounce.** Hvem: de 11 besøgende/28 dage. Tal:
     bounce og konvertering til Pro ($19). Accept: forsiden får en klar værdi og
     én købsknap. Datagrund: Plausible 8/10 — alle forlader uden at handle.
