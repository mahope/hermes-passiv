# STATUS

- **9/10:** rød CI rettet og de danske sider peger nu på det danske
  webværktøj (`ceo/da-vaerktoej-links`): `license-clients` kendte ikke den
  nye `/da/license-lookup`, og `catalog-where` lå skjult bag den (506 → 508).
  20 danske sider sendte læseren til det engelske `/clean-copy-tool`.
  Gaten grøn (187 steps).
- **9/10:** dansk udgave af licensøgningen leveret (`ceo/da-license-lookup`):
  `/da/license-lookup` med opslag af nøgle, frigørelse af maskiner,
  kopier-knap. Al tekst på dansk, hreflang begge veje.
- **9/10:** bog-prøvesider fik betalt vej (`ceo/bogproeve-betalt-vej`), og
  page-profiles to-URL-sammenligning er verificeret live (feature 51 LEVERET).
- **9/10:** Clean Copy-webværktøjet på dansk (`ceo/clean-copy-da-tool`) og
  prøvesider for de fem øvrige EPUB'er leveret; review-fonds to [LAV]
  gennemgået uden åbne fejl.
- **9/10:** rød CI rettet i tre runder (`ceo/kontrast-selvtage-hero`,
  `ceo/page-profile-cta`, `ceo/plan-status-laengde`): hero-montage,
  dobbelt-donation på page-profile, STATUS 35 linjer.
- **9/10:** page-profiles Pro-kort og fire guides siger nu at sammenligning i
  browseren er gratis (`ceo/page-profile-cta`, `ceo/forsider-pro-prajs`).
- 0 åbne review-fund. Sentry: 0 uløste fejl (14 dage). 0 åbne PR'er.
- **PR-TJEK 9/10:** 0 åbne PR'er. **BRANCH-TJEK 9/10:**
  `origin/ceo/hub-readme-note` kan slettes, men push --delete er spærret (❓).
- **CEO-kø #0** er færdig og merged; 0 åbent.
## Åbne review-fund

Ingen.

## Verificér deploy

- **VERIFICÉR DEPLOY:** danske lenker + rød CI `ceo/da-vaerktoej-links`
  9/10-2026 20:50 — tjek at `https://mahope.tools/da/license-lookup` (200)
  viser «Find din licensnøgle», at `/da/clean-copy-tool` (200) viser
  webværktøjet på dansk, og at f.eks. `/da/blog/kopier-tabel-til-excel`
  linker til `/da/clean-copy-tool` (ikke `/clean-copy-tool`).
- **VERIFICÉR DEPLOY:** dansk licensøgning `ceo/da-license-lookup` 9/10-2026
  15:00 — tjek at `https://mahope.tools/da/license-lookup` (200) viser
  «Find din licensnøgle» og at formularen virker. Filen er i `dist/` lokalt,
  men live-sitet gav 404 ved tjek — deploy endnu ikke gået igennem.
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
  9/10-2026 14:3x — tjek at `https://mahope.tools/books/preview-{nis2-for-agencies,
  gdpr-for-agencies, eaa-checklist, eaa-shopify, cookie-consent-guide}` (200)
  viser den nye sætning med «EUComply Pro» og $79 pr. website pr. år, og at
  `/compliance-report` stadig viser «Buy EUComply Pro — $79/year».

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
55. **EUComply: kundeklar rapport ud af det frie multi-site-tjek.** Hvem: bureauer
     med kunder. Tal: flytter en $79/årslinje. Accept: rapport-knappen på
     checket der fører til `/paid-templates` eller Pro. Datagrund: spørger Mads
     først (🟡 i ❓) — rapportkittet til $69 er den nærmeste eksisterende vej.
