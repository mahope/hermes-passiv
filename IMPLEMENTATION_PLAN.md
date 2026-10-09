# STATUS

- **9/10:** feature 49 leveret (`ceo/farveblindhed-artikel`): ny guide i EN+DA,
  `/blog/color-blindness-simulation-check` + `/da/blog/farveblindhed-tjek`, med
  en målende kontrasttabel pr. synstype — alle 24 tal beregnet med simulatorens
  egen Machado-model, ikke estimeret. Gate GRØN.
- **9/10:** feature 45 leveret (`ceo/bog-proeveside`): «Læs de første kapitler i
  browseren» for Build Your First Chrome Extension — ny side
  `/books/preview-build-your-first-chrome-extension` med bogens tre første
  afsnit (præcis teksten fra EPUB'en) og EPUB-download til slut. Bog-siden
  har nu en sekundær knap til forhåndsvisningen. Gate GRØN.
- **9/10:** to deploy-noter lukket på live-indhold (eaa-action, sitemap-scan,
  score-simulator).
- **9/10:** simulatoren (`ceo/farveblindhed-cta`) linker nu til farveblindhedsguiden,
  så de 5 besøgende på værktøjet kan nå guiden (9 besøgende).
- 0 åbne review-fund. Sentry: 0 uløste fejl (14 dage). 0 åbne PR'er.
- **PR-TJEK 8/10:** 0 åbne PR'er. **BRANCH-TJEK:** ikke kørt.
- **CEO-kø #0** er færdig og merged; 0 åbent.
## Åbne review-fund

Ingen.

## Verificér deploy

- **VERIFICÉR DEPLOY:** bog-prøveside + rød-port-fix `ceo/bogproeve-betalt-vej
  9/10-2026 03:30` — noten glemt i squash-commiten `fe9bdd51`, og siden kom
  aldrig ud: den commits egen gate var rød (tool-paid-path), så deploy-jobbet
  blev sprunget. Tjek at
  `https://mahope.tools/books/preview-build-your-first-chrome-extension` (200)
  viser «Preface: Why This Book Exists» og den nye sætning om Clean Copy, at
  knappen «Or read the first chapters in your browser» findes på
  `/books/build-your-first-chrome-extension`, og at
  `https://mahope.tools/color-blindness-simulator` (200) linker til
  `/blog/color-blindness-simulation-check` — begge commits (708d302e,
  fe9bdd51) lå ude af deploy indtil rettelsen landed.

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

50. **Forhåndsvisning af de øvrige fem EPUB'er.** Hvem: dem der lander på
    `/books/` uden en EPUB-læser. Tal: epub-downloads (9/uge på mahope.tools,
    feature 45s mønster). Accept: hver bog på `/books` har en «Læs de første
    kapitler»-knap. Datagrund: kun én bog kan læses i browseren endnu.
51. **`/page-profile`: sammenlign to URL'er i browseren.** Hvem: SEO-bureauer.
    Tal: konvertering til Page Profile Pro ($19/år). Accept: to URL-felter, én
    diff med score-forskel pr. kontrollpunkt, Pro-funktionen bag licenskontrol.
    Datagrund: CLI'en har allerede `--compare`; web-siden profilerer én URL.
52. **Skabelon-hub for de mest hentede filer.** Hvem: de 25 downloadbesøg/uge på
    mahope.tools. Tal: downloads og konvertering til EUComply Pro ($79/år).
    Accept: én side med hver gratis skabelon, hvad den dækker, og én købsknap.
    Datagrund: privacy-policy-template.md (5) og ropa-template.md (3) er de
    mest hentede filer, men hentes som rå .md uden en side der forklarer dem.
53. **cleancopy.tools: dansk udgave af web-værktøjet.** Hvem: de 3 besøgende/28
    dage på `/da/`-stierne. Tal: konvertering til Clean Copy Pro ($19/år).
    Accept: `/da/clean-copy-tool` med batch og licensaktivering på dansk.
    Datagrund: DA-forsiden lover batch-konvertering «i webværktøjet», men
    værktøjet findes kun på engelsk.

45. **e-bøger: læs kapitel 1 gratis i browseren.** Hvem: dem der laster de seks
    EPUB'er (top-downloads). Tal: downloads og konvertering til $29-bundlet.
    Accept: en prøveside der viser det første kapitel og linker til bundlet.
    Datagrund: `/books/` er top-download, men der er ingen vej fra læsning til køb.
    **LEVERET** `ceo/bog-proeveside` ( én bog; udvidelsen af de sidste fem er
    feature 50).
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
49. **Guide: farveblindhedssimulering.** Hvem: de 5 besøgende/28d på
    `/color-blindness-simulator` + 9 på kontrastartiklen. Tal: trafik til
    simulatoren og videre til `/scan`/EUComply Pro. Accept: EN+DA-guide med
    målte tal. **LEVERET** `ceo/farveblindhed-artikel`.
