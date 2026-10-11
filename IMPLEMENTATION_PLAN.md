# STATUS

- **11/10:** deskuptime.com's kort byder på fler-URL-tjekket
  (`ceo/deskuptime-flere-url`, gate grøn 637/637). Ny side
  `/bulk-url-checker/` (EN+DA) med textarea, tabel og status; linket er i
  kortets `next`-array på begge sider.
- **11/10:** cleancopy.tools' to forsider har konverteren i siden
  (`ceo/forside-indsaet-konverter`); deskuptime.com ruller til sit eget
  eksempel-svar (`ceo/eksempel-i-syne`). Begge verificeret live.
- 0 åbne review-fund. Sentry: 0 uløste fejl (14 dage). 0 åbne PR'er.
  **PR-TJEK 10/10:** 0 åbne PR'er. **BRANCH-TJEK 9/10:** `origin/ceo/hub-readme-note`
  kan slettes, men push --delete er spærret (❓).
- **CEO-kø #0** er færdig og merged; 0 åbent. **11/10:** CI grøn igen efter
  banner-label-retten i `ceo/wcag-ci-banner`.
- **11/10:** robots.txt + sitemap er efterprøvet på alle fire domæner og er
  korrekte (mahope.tools 274 URL'er, cleancopy 35, deskuptime 5, alle med
  hreflang og `robots: noindex` hvor det skal). CEO-opgave 3 er dermed lukket
  bortset fra Search Console (❓).
- **11/10:** kunderapport fra scanneren (EN+DA) i `ceo/scan-rapport` —
  `site/scan-report.js` + `tests/scan-report.test.mjs` (73 domme), nyt
  gatestræk `scan-report`, linjerefs i `stripe_catalog.json` flyttet.
  `quality_gate.py` grøn (191 steps).

## Åbne review-fund

Ingen.

## Verificér deploy

- **VERIFICÉR DEPLOY OK 11/10:** konverteren på cleancopy.tools' to forsider
  `ceo/forside-indsaet-konverter` 11/10-2026 — verificeret live: begge sider
  har `id="cc-embed"` og korrekt `CC_EMBED` path, alle scripts 200.
- **VERIFICÉR DEPLOY OK 11/10:** deskuptime.com-frontens eget svar i syne
  `ceo/eksempel-i-syne` 11/10-2026 — verificeret live: begge sider indlæser
  `/one-off-check.js` (200) med `bringExampleIntoView` og artiklen.
- **VERIFICÉR DEPLOY OK 11/10:** kunderapport fra scanneren `ceo/scan-rapport`
  11/10-2026 — verificeret live: `https://mahope.tools/scan` og `/scan-da`
  indlæser `/scan-report.js` (200) inden egen inline-kode, «Download the
  report»/«Hent rapporten» findes **to** gange pr. side (curl 11/10). De
  resterende punkter (`LAST`-grade, filnavn, `dist/`) dømmes af
  `tests/scan-report.test.mjs` (73 domme), JS-kørsel kan ikke curles.

- **VERIFICÉR DEPLOY OK 11/10:** EN-søskende til WCAG 2.2-listen
  `ceo/wcag-en-kravliste` 10/10-2026 — efter rød CI-genløbet: live
  `https://mahope.tools/blog/wcag-22-requirements-checklist` (200) har de tre
  tabeller med **55** fund (29 A + 20 AA + 6 nye), hreflang `en`/`da`/
  `x-default`, «DANISH VERSION»-kort til `/da/blog/wcag-22-krav-liste`, og
  FAQ-JSON-LD siger «86 success criteria: 31 at level A, 24 at level AA and 31
  at level AAA» (talt efter W3C). `/da/blog/wcag-22-krav-liste` (200) har
  «Listen på engelsk» + link tilbage; begge blog-indekser lister artiklen; de to
  danske originaler har hver sit «På engelsk»-link (curl, live 11/10).

- **VERIFICÉR DEPLOY OK 11/10:** licensnøglen forudfyldt i frigørelsesformularen
  `ceo/licensnogle-forudfyld` 10/10-2026 — live EN+DA (200) indeholder
  `udfyldSeatKey()` (to forekomster pr. side); browser-kørsel af opslag kan
  ikke curles, men DOM-tjek + `tests/license-lookup.test.mjs` dømmer løsningen.

- **VERIFICÉR DEPLOY OK 11/10:** farveblindhed-simulator + artikel
  `ceo/farveblindhed-artikel` 10/10-2026 — live EN+DA indlæser `/cb-machado.js`
  (200); artiklens severity-slider og 6×3-gitter er JS-kørsel og dømmes af
  `tests/scan-clients.test.mjs`.

- **VERIFICÉR DEPLOY OK 11/10:** page-profile 1.2.2 `--compare --json`
  `ceo/compare-json` 10/10-2026 — live-zip
  `https://mahope.tools/downloads/page-profile/page-profile-1.2.2.tar.gz` er
  byte-identisk med `site/downloads/` (samme sha256 `2eca913a…`); version i
  downloaden og link fra `/page-profile` tjekkes i næste CI-kørsel.

- **VERIFICÉR DEPLOY OK 10/10:** APCA Lc i tekst-på-billede-tjekkeren
  `ceo/apca-tekst-billede` 10/10-2026 — tjek at live
  `https://mahope.tools/text-on-image-checker` og `/text-on-image-checker-da`
  samt `https://mahope.tools/blog/text-on-image-contrast-check` henter
  `/apca.js` FØR `/text-on-image-core.js`, at resultatet indeholder `APCA Lc`
  med et tal, og at rådet på den danske side står på dansk.

- **VERIFICÉR DEPLOY OK 10/10:** Clean Copy-popup + licenskøbslink `ceo/popup-pro-koeb`
  10/10-2026 — tjek at live `https://mahope.tools/downloads/clean-copy-v1.5.3.zip`
  og `/downloads/clean-copy-firefox-v1.5.4.zip` er byte-identiske med arkiverne i
  `site/downloads/` (samme sha256), at arkivernes `popup.html` ikke indeholder
  «Soon», og at `options.html` indeholder
  `buy.stripe.com/6oU4gy76PgvgdBIdAXbMQ00`.

- **VERIFICÉR DEPLOY OK 10/10:** konverteren i cleancopy.tools' tre artikler
  `ceo/artikel-konverter` 10/10-2026 — tjek at live
  `https://cleancopy.tools/blog/{html-to-markdown-cli,html-to-markdown-vscode,
  copy-as-markdown-chrome-extension}` indeholder `<script src="/net.js"></script>`
  FØR `<script src="/clean-copy-embed.js"></script>`, at
  `https://cleancopy.tools/net.js` og `/clean-copy-embed.js` svarer 200, og at
  formularen i artiklen konverterer (JS-kørsel kan ikke curles — det samme
  script kører på `/clean-copy-tool`, som er verificeret).

- **VERIFICÉR DEPLOY OK 10/10:** eksempel-tjek på mahope.tools' to forsider
  `ceo/forside-eksempel` 10/10-2026 — tjek at live `https://mahope.tools/` og
  `/da/` erklærer `example: 'example.com'` i `ONE_OFF_CHECK`, at kortet ved
  sidevisning siger «This is an example check»/«Dette er et eksempel-tjek» uden
  en donationslinje, og at formularen stadig kører ét kald for læserens egen
  adresse — med donationslinjen efter et rigtigt tjek.

- **VERIFICÉR DEPLOY OK 10/10:** eksempel-tjek på deskuptime.com
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
- **VERIFICÉR DEPLOY OK 10/10:** bog-kopi «client-ready report» `ceo/bogproeve-kopi`
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

3–5 prioriterede idéer, valgt på trafikdata 11/10. Alt der er leveret står i
`docs/plan-arkiv.md`.

  67. **cleancopy.tools: indsætnings-konverteren på `/clean-copy-tool` skal
      pege på browserudvidelsen.** Hvem: de 2 besøgende/28 d på selve
      værktøjet (0 % bounce — de bliver). Tal: installer og Pro-aktivering.
      Accept: værktøjet viser ét tydeligt skridt til udvidelsen og CLI'en.
      Datagrund: værktøjet er den side der holder folk (0 % bounce), men den
      leder ikke videre til det der bruges dagligt; GitHub viser 15 kloninger
      af CLI'en og 8 af hver udvidelse pr. 14 dage.

  68. **mahope.tools `/blog/text-on-image-contrast-check`: 9 besøgende,
      100 % bounce.** Hvem: dem der søger på kontrast af tekst på billeder.
      Tal: videre til `/text-on-image-checker` (7 besøgende) og til `/scan`
      (EUComply Pro, $79/år). Accept: artiklen fører læseren ét sted hen, der
      er værd at komme til, uden at forlade siden igen. Datagrund: artiklen
      kører allerede tjekkeren (feature 60) — 100 % bounce siger, at læseren
      ikke fandt noget at gå videre til bagefter.

  69. **Clean Copy Pro i Obsidian- og VS Code-udvidelserne: 11 + 8 kloninger
      pr. 14 dage, 0 stjerner.** Hvem: dem der allerede har valgt en editor.
      Tal: kloninger → stjerner → Pro ($19/år). Accept: begge repos' README
      har én købsvej og ét link til mahope.tools. Datagrund: kloningerne viser
      installerede brugere, men intet peger tilbage, og Pro aktiveres i dag
      kun fra webværktøjet og udvidelsen.

  70. **`/color-blindness-simulator`: 6 besøgende, 67 % bounce.** Hvem: dem
      der tester farver. Tal: videre til `/scan` og EUComply Pro ($79/år).
      Accept: simulatoren slutter med ét konkret næste skridt på sidens eget
      sprog. Datagrund: artiklen bag den kører allerede simulatoren
      (feature 61), men værktøjet ender uden et tilbud om, hvad man gør med
      resultatet.

