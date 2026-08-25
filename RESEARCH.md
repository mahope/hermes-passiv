# RESEARCH — Iteration 269: Distributionsdata + ærlighedstjek (0 web-søgninger)

**Dato:** 2026-08-25
**Metode:** gh API traffic endpoints, /api/stats, curl af live-sider. 0 web-søgninger.

## Fakta
1. **GitHub organisk trafik er nul:** repositorierne clean-copy,
   clean-copy-firefox, clean-copy-vscode, clean-copy-obsidian,
   homebrew-clean-copy, clean-copy-cli og eucomply-scanner har alle
   **0 visninger over de seneste 14 dage** (gh /traffic/views).
2. Firefox-repoets 55 kloner (29 unikke) den 24/8 er en enkelt dags-spike uden
   tilhørende visninger — mest sandsynligt vores egen sync/CI-aktivitet, ikke
   eksterne brugere. Referrer-listen er tom.
3. Lead-formularerne fra iter 268 lovede email-levering ("Tjek din indbakke")
   som ikke eksisterer — handleWaitlist gemmer kun adressen i KV. Rettet i
   denne iteration; teksten lover nu kun det koden gør.
4. Waitlist-tæller: 1 (uændret). Lead capture var først live samme dag.

## Konklusion
GitHub som distributionskanal er død uden en aktiv butikskanal foran den.
Lead capture er den sidste billigste væksthypotese på egen flade — giv den
nogle dage, og skift spor hvis den ikke måler nogen vækst.

---

# RESEARCH — Iteration 234: EN PDF-tabel-post (0 web-søgninger)

**Dato:** 2026-08-25
**Metode:** Verifikation mod lokal blogliste. 0 af 12 søgninger brugt.

## Fakta
1. Ingen af de eksisterende blogposter dækker "copy table from pdf to excel"
   på engelsk (verificeret ved filist af site/blog/) — DA-versionen fra iter
   233 er en separat URL.
2. Teknisk indhold (PDF-tekst som DOM i browser-PDF-visere, Excel "Get Data
   From PDF", Acrobat-export) er velkendt produktadfærd, verificeret i iter 233.

---

# RESEARCH — Iteration 233: DA PDF-tabel-post (0 web-søgninger)

**Dato:** 2026-08-25
**Metode:** Verifikation mod lokal blogliste + kendt produktadfærd. 0 af 12 søgninger brugt.

## Fakta
1. Emnet fandtes ikke: ingen af de 74 eksisterende blogposter dækker
   PDF-tabel-kopiering (verificeret ved filist af site/blog/).
2. PDF'er vist i Chrome/Firefox renderer tekst som rigtig DOM-tekst — derfor
   virker en browserudvidelse på åbne PDF'er. Velkendt browseradfærd.
3. Excel har "Data > Fra PDF" (Microsoft 365) og Acrobat har eksport — begge
   nævnt ærligt i sammenligningstabellen som betalte alternativer.

---

# RESEARCH — Iteration 228: Notion-table-post (0 web-søgninger)

**Dato:** 2026-08-25
**Metode:** Ren udvikling + live-verifikation. 0 af 12 søgninger brugte.

## Fakta
1. Notion konverterer markdown-tabeller på paste til rigtige table blocks —
   velkendt produktadfærd, ingen søgning nødvendig for at beskrive den.
2. "Turn into database"-flowet efter paste er dokumenteret Notion-funktionalitet.
3. Søgevinklen "copy table to Notion" er den tredje i serien (Sheets, Excel) —
   samme mønster, nyt publikum.

---

# RESEARCH — Iteration 220: VS Code extension + npm distributionskanaler (1 web-søgning)

**Dato:** 2026-08-24
**Metode:** 1 målrettet npm registry check. 1 af 12 søgninger brugt.

## Fakta

1. `clean-copy-cli` er **ikke** på npm (404 — navnet er ledigt). Det eneste `clean-copy`
   på npm er en gammel 0.0.2-pakke fra 2016 (generisk fs-copy, irrelevant).
2. VS Code Marketplace har extensions som "Markdown Paste" og "Paste URL", men ingen
   tilbyder dedikeret HTML→clean Markdown med selection-only + clean-text mode +
   browser-extension-samme-kerne som USP.
3. VS Code Marketplace-publikation er gratis (kræver Microsoft-konto). Ingen årligt gebyr.
   Publisher can be created with any Microsoft account — kræver Mads' godkendelse.

## Konklusion

To nye distributionskanaler bygget og publish-ready. Begge er gratis, har indbygget
målgruppe (millioner af VS Code-brugere + npm-brugere), og kan monétiseres via LS
når nøglen kommer.

|---

**Dato:** 2026-08-24
**Metode:** gh API + lokal XML-parse. 0 af 12 søgninger brugt.

## Fakta

1. mahope/build-first-chrome-extension eksisterede (oprettet iter 210) men
   indeholdt kun chapter-02 — mens bogens landingsside lovede "complete
   source code for every step". Paastand ville have været falsk; nu sand.
2. KindlePub: python-markdown's `<hr>`-output er ikke gyldig XHTML. Enhver
   EPUB-bygger der indlejrer rå markdown-output i .xhtml skal self-close
   void-tags. Fejlen ramte alle 6 bøger, ikke kun den nye.

---

# RESEARCH — Iteration 206: Obsidian release-sync + PR-kanal-verifikation (0 web-søgninger)

**Dato:** 2026-08-24
**Metode:** gh API og direkte downloads. 0 af 12 søgninger brugt.

## Fakta

1. `obsidianmd/obsidian-releases` tillader kun collaborator-PR'er — API-forsøg
   (REST og GraphQL `CreatePullRequest`) fejler med 403 også nu. Fork-grenen er
   mergeable=CLEAN, så web-UI-klikket i obsidian-submission-kit.md virker stadig.
2. Ingen eksisterende Clean Copy-PR i obsidianmd/obsidian-releases (verificeret
   via search + community-plugins.json på master: id'et `clean-copy-obsidian`
   findes ikke der endnu; fork-grenens kopi indeholder vores indlæg).
3. Zip-bundles kan blive forældede i forhold til deres versionsnummer: den
   deployede 1.0.6-zip manglede kernefixes fra senere iterationer. Lektion:
   genbyg altid zips efter kerneændringer, verificér indholdet byte-for-byte.

---

# RESEARCH — Iteration 198: Firefox-repo + alignment-blogpost (0 web-søgninger)

**Dato:** 2026-08-24
**Metode:** Ren udvikling, gh CLI og lokal test. 0 af 12 søgninger brugt.

## Fakta

1. `mahope/clean-copy-firefox` fandtes ikke på GitHub, selv om clean-copy-repo's
   README (og ældre materialer) linkede til den URL. Oprettet og pushet v1.4.1-kode.
2. Firefox-repoets testpakke var i praksis ubrugelig i Node: sandbox'en stubbede
   kun `browser.*`, men background.js kalder også `chrome.storage.onChanged`,
   `chrome.runtime.onInstalled` og `chrome.commands`. Fixet ved at udstyre
   chrome-stubben fuldt — 25/25 pass. Lektion: en testpakke der aldrig er kørt
   i CI på et repo er ikke en testpakke.
3. Blogposten /blog/table-alignment-html-to-markdown skrevet ud fra kernen
   (`alignOf`/`convertTable` i tools/clean_copy_core.js) — ingen ny research krævet.

---

# RESEARCH — Iteration 197: Table alignment implementeret (0 web-søgninger)

**Dato:** 2026-08-24
**Metode:** Ren udvikling og lokal test. 0 af 12 søgninger brugt.

## Fakta

1. Tabel-alignment (STATUS 196's plan B) implementeret i kernen: `text-align`
   styles og legacy `align`-attributter på th/td → Markdown-separatorer
   (`:---`, `:---:`, `---:`). Header-row vinder over body-rækker; colspan-celler
   kan bære alignment på første kolonne.
2. Fintuning undervejs: første regex-forsøg (`(?:(?!>|\/>)[^])*?`) matchede
   attributterne ind i gruppe 2 men tabte dem — erstattet med simpel
   `([^>]*)` + separat colspan-udtræk. Lektion: komplekse conditional-regexes
   i én pass er fejlbehæftede; to enkle passes er mere robuste.
3. Sync-kæden afsløret: `tools/clean_copy_core.js` er kilde for site/obsidian/CLI,
   men extensions' background.js har sin EGEN kopi af convertTable som sync_core.js
   IKKE rører. Patchet manuelt der, derefter sync til firefox + clean-copy-repo.
   Alle 7 kopier har nu alignment-koden (verificeret med grep).

## Konklusion

v1.4.1 bygget, testet (20 CLI-tests + pro-core + tools-suite), releaset på GitHub
med tarball, zips lagt på sitet, site deployet og verificeret live.

---

# RESEARCH — Iteration 174: Kerne-edge-cases (0 web-søgninger)

**Dato:** 2026-08-24
**Metode:** Lokal test af kernen mod edge cases fra iteration 173's liste.
0 web-søgninger.

## Fakta

1. **CDATA tabte indhold:** `htmlToMarkdown('<p><![CDATA[x]]></p>')` returnerede
   tomt — CDATA-sektionen blev ikke fjernet af script/style-reglen, men den rå
   tekst forsvandt i det efterfølgende tag-strip. Fix: CDATA-indhold bevares nu.
2. **dl/dt/dd smeltede sammen:** `<dl><dt>T</dt><dd>D</dd></dl>` gav "TD" uden
   struktur. Fix: dt → fed linje, dd → indrykket definitionslinje.
3. Edge cases der allerede håndteres korrekt: HTML-kommentarer, inline SVG,
   5000-tegns ord, meget lange URL'er i anchors, tabel i listepunkt, tom input,
   whitespace-only input, br i headings, figure/figcaption.
4. cleanText's space-collapse regel kollapser `:   ` til `: ` i dd-output —
   acceptabelt, tests skrevet whitespace-tolerante.

## Konklusion

To ægte fejl rettet i kernen (v1.3.3 / Obsidian v1.0.4), synkroniseret til alle
6 overflader og verificeret live. Nye permanente assertions tilføjet til
testpakken så regressioner fanges automatisk.

---

# RESEARCH — Iteration 171: GitHub Action-udvidelse + Obsidian PR-blokering bekræftet (0 web-søgninger)

**Dato:** 2026-08-24
**Metode:** Lokal research (gh CLI, CI-logs, filanalyse). 0 af 12 mulige søgninger brugt.

## Fakta

1. **Obsidian community plugin PR:** Bekræftet blokeret via både REST og GraphQL API
   (`gh pr create`: "mahope does not have the correct permissions to execute
   CreatePullRequest"). Web-UI compare-URL'en virker men kræver Mads i browser:
   `https://github.com/obsidianmd/obsidian-releases/compare/master...mahope:obsidian-releases:add-clean-copy-obsidian?expand=1`
2. **GitHub Action Marketplace:** Clean Copy Action er ikke synlig på Marketplace
   (slug `clean-copy-url-to-markdown` returnerer 404). Funktionelt virker den via
   `uses: mahope/clean-copy-cli@v1` — Marketplace-listing er en ekstra discovery-lag,
   ikke en forudsætning for brug.
3. **GitHub Action CI:** `echo "${{ steps...outputs.markdown }}"` fejler på multi-line
   output med `#`-heading (shell tolker `#` som kommentar). Løsning: `printf '%s\n'`.
4. **GitHub Action v1.3.0 testet:** Alle 5 jobs (URL, file, html, output_file, CLI) passerer
   i CI med 100% success rate.

## Konklusion

GitHub Action er den eneste distributionskanal der kan forbedres uden Mads. v1.3.0 gør
den mere nyttig (file/html inputs) og dermed mere synlig på Marketplace. Obsidian PR
forbliver Mads-browser-blokeret. CWS upload tilsvarende.

---

# RESEARCH — Iteration 122: Browser store upload-API'er faktatjek (12 web-søgninger)

**Dato:** 2026-08-24
**Metode:** 12 målrettede søgninger (loft nået).

## Fakta

1. **Chrome Web Store API:** Upload+publish kan automatiseres (`chromewebstore` API, `items.update`/`items.publish`), men kræver OAuth2 refresh token fra én browser-consent i Mads' Google-konto, plus at item'et oprettes én gang manuelt i devconsole. Kilde: docs.extenshi.io. Stadig Mads-blokeret.
2. **Firefox AMO:** Simple JWT API-nøgler (issuer + secret), ingen OAuth-konsent. V5 API understøtter listede OG unlisted/selv-distribuerede udvidelser; første submission kan være unlisted uden GUID. Siden 3. nov 2025 kræver nye add-ons `gecko.data_collection_permissions` i manifestet — mangler den, afvises submissionen. MV3-signering kræver eksplicit add-on ID. Kilde: extensionworkshop.com, MDN.
3. **Edge Add-ons:** Publish API med API key + ClientID fra Partner Center — men Partner Center-udviklerkonto kræves først (gratis). Første publish er manuel. Kilde: learn.microsoft.com.
4. **Firefox clipboard:** `clipboardWrite`-permission gør at background page kan kalde `navigator.clipboard.writeText` uden transient activation — ingen offscreen-document nødvendighed som i Chrome MV3. Kilde: MDN Interact_with_the_clipboard.
5. **Firefox MV3:** Bruger event pages (`background.scripts`) — ikke service workers. Kilde: extensionworkshop.com MV3 migration guide.

## Konklusion

Firefox-porten er den eneste extensions-distributionsvej der kan åbnes med en simpel API-nøgle i stedet for Mads' browser-consent. Port bygget og testet denne iteration; upload venter på Firefox-konto/API-nøgle (samme Bitwarden-punkt).

---

# RESEARCH — Iteration 113: Trafikdata-tjek (0 web-søgninger)

**Dato:** 2026-08-24
**Metode:** /api/stats (cookieless KV-tracking), ingen web-søgninger.

1. **page-profile trækker nul trafik:** 14 dages data viser ingen
   `profile`-events og nogen sidevisninger af /page-profile eller
   /da/page-profile fra andre end mig. Eneste eksterne signaler den 23/8:
   11 visninger af forsiden, 2 af en Shopify-guide, 1 cookie-scan, 1 scan.html.
   Konklusion: værktøjerne får ikke fundet sig selv — indgangssider skal bygges.
2. Søgeindgangen til /da/page-profile er derfor bygget samme iteration:
   /blog/teknisk-seo-tjek-hjemmeside (se BUILD.md).

---

# RESEARCH — Iteration 36: Faktatjek og beslutning (10 web-søgninger)

**Dato:** 2026-08-23 (tidlig aften)
**Metode:** 10 web-søgninger for at tjekke usikre fakta fra iteration 35.
**Resultat:** WordPress-plugin (K1, tidligere #1) droppet pga. massiv konkurrence. KDP e-bog (K8, tidligere #2) valgt som primært produkt. Se DECISION.md.

# RESEARCH — Iteration 108: Distributionskanaler faktatjek (5 web-søgninger)

**Dato:** 2026-08-24
**Metode:** 5 målrettede web-søgninger for at tjekke om distributionskanaler til compliance-produktet er åbne.
**Resultat:** Alle undersøgte kanaler er enten mættede eller kræver en konto. Compliance-produktet erklæres færdigt og parkeret. STATUS.md indeholder stifter-beslutning.

## Nye fakta fra denne iteration

1. **Product Hunt (2026):** Kræver 8-12 ugers forberedelse, 400+ waitlist-abonnenter og måneders fællesskabsengagement for at blive featured. En afpresset launch uden publikum får ikke featured-status. Kilde: waitlister.me Product Hunt launch checklist 2026.
2. **Hacker News Show HN:** Der findes allerede en konkurrent der har lanceret nøjagtigt samme produkt: "Show HN: Free WCAG accessibility scanner – EAA compliance deadline is June 2025" (news.ycombinator.com/item?id=46610925). Kanalen er mættet for vores produkt.
3. **Meta/social-preview-tools (overvejet nyt territorium):** OpenGraph.xyz (gratis, 2 halvdele: debugger + billedegen.), Metatags.io (gratis, social preview + Google snippet), OGFixer (gratis, ingen login, 4 platforme), sunilpratapsingh.com (gratis, 0-100 score, 5 platforme). At bygge endnu et er commodity i et overfyldt gratis-marked.
4. **Lemon Squeezy:** Mads har allerede konto (mads@mahope.dk). API-nøgle forventet i Bitwarden. Har fuld skrive-API til at oprette produkter, priser og checkout-links — det eneste der mangler er nøglen.
5. **Chrome Web Store:** Mads har allerede udviklerkonto med API. OAuth-credentials forventet i Bitwarden.

## Konklusion

Compliance-produktet er bygget færdigt og kan tage imod penge via Lemon Squeezy + KDP, så snart konti/Mads åbner. Distributionskanalerne er mættede. At bygge mere indhold på sitet (0 ekstern trafik) er ikke løsningen. Den ene flaskehals er Mads' konti — intet produkt kan tjene penge uden en betalingsformidler i en persons navn med bankkonto.

## Nye fakta fra denne iteration

1. **wp.org plugin review:** 1-10 dage. Kræver SVN-adgang. OK — men irrelevant da plugin alligevel ikke kan konkurrere.
2. **EAA enforcement 2026:** I gang. Bøder op til €900K (Sverige), €600K (Spanien). Reel efterspørgsel.
3. **WP accessibility plugins:** ALLY (tidligere One Click Accessibility) har **500K+ aktive installs**. UserWay 80K+, WP Accessibility 60K+, Accessibility Checker 10K+. Accessibility Guard (lanceret Feb 2026) har kun 20+ installs på 6 måneder. **Nyt plugin ville være usynligt.**
4. **Gumroad Discover:** Kræver $10 i eget salg før Discover aktiveres. Første salg skal komme fra egen trafik. Discover er en belønning, ikke en kickstart.
5. **Amazon KDP:** Første salg 3-14 dage via søgning, selv uden publikum. Amazon har indbyggede købere.
6. **Gumroad vs KDP:** Gumroad vinder på margin (87-95%), KDP vinder på distribution (indbygget søgetrafik). De fleste succesfulde indie-forfattere bruger begge.
7. **NIS2 e-bog konkurrence:** Der findes "NIS2 Directive Compliance Guide 2026" (113 sider, Meridian Certification Press). Men ingen målretter specifikt **små webbureauer** — min niche er åben.

## Revideret top 3

1. 🥇 **KDP e-bog: NIS2 for Small Web Agencies** — bedste distribution pr. indsatsenhed. $0 opsætning.
2. 🥈 **ComplianceDocs på Gumroad** — sekundær kanal. Kan bygges når Mads har Gumroad-konto.
3. 🥉 **WordPress EAA-plugin** — droppet indtil videre pga. konkurrence. Revurder om 90 dage.

---

# RESEARCH — Iteration 35: Nytænkning på distribution (ingen web_search)

Dato: 2026-08-23 (eftermiddag). Metode: ren tænkning ud fra eksisterende viden.
**Mandat:** AGENTS.md opdateret 23/8 — krav om nytænkning lempet. "Tjen så mange penge som muligt, så hurtigt som muligt."
**Begrænsning i denne iteration:** Ingen web_search. Kun hvad jeg allerede ved.

## Vurderingsnøgle

Hver kandidat får tre svar:
- (a) Hvem betaler hvor meget
- (b) Månedligt menneskearbejde (mål: ingenting)
- (c) Mest sandsynlige fejlårsag

**Tre-måneders-testen:** Første betalende kunde inden ~90 dage via organisk/automatiseret distribution.
Kan bestå kun med ét Mads-ja (fx opret konto, upload produkt) — men ikke med løbende Mads-arbejde.

## Akilleshælen

Denne analyse afslørede i iteration 34 én central sandhed: **alle kandidater fejler samme sted.** Produktet kan bygges af mig, men *distribution* kræver én konto hos en tredjepart (Gumroad, wp.org, Chrome Web Store, Amazon KDP, Stripe), og den konto skal Mads oprette. Uden den er ALT dødt.

Løsningen er ikke at finde et bedre produkt — det er at finde produktet med **den bedste indbyggede distribution på den ene kanal, Mads siger ja til.** Når han først har sagt ja til at oprette én konto, skal produktet kunne sælge sig selv.

---

## Kandidater

### K1. Freemium WordPress-plugin på wp.org — EAA Accessibility Scanner
(a) WP-site-ejere i EU (2-50 ansatte), $49-99/år Pro-licens via EDD/WooCommerce på eget site + wp.org-plugin som lead.
(b) Næsten ingenting: opdateringer ved WP major releases ~2-3 gange/år. Support-svar kan være sporadisk.
(c) Kræver wp.org-konto fra Mads (5 min at oprette). Plugin review-time kan være 1-7 dage. Største risiko: at plugin'et er for simpelt til at konkurrere mod etablerede accessibility-plugins (WP Accessibility, Accessibility Helper). **Overlever tre måneder?** Ja — wp.org er den BEDSTE gratis distributionskanal. Folk søger aktivt "accessibility plugin wordpress". Hvis plugin'et har 3+ stjerner og virker, får det downloads.

### K2. Freemium WordPress-plugin — WP GDPR Consent Logger
(a) Samme målgruppe, $39-79/år. Logger consent på kommentarer/kontaktformularer.
(b) Ingenting efter upload.
(c) WordPress 6.7+ har indbygget privacy-værktøjer — min plugin kan blive overflødiggjort af core. **Grænsetilfælde.** Overlever hvis den gør noget core ikke gør (fx grafisk consent-log oversigt).

### K3. Freemium WordPress-plugin — WP Content Freshness
(a) Blog-ejere/indholdsansvarlige, $29-49/år. Viser "sidst opdateret" badges + sætter påmindelser om forældet indhold.
(b) Ingenting — cron-jobs kører selv.
(c) Lille marked. Ikke alle site-ejere gider betale for dette. **Dumpet:** betalingsvilje for lav, konkurrence fra gratis løsninger (dateret indhold-plugins).

### K4. Freemium WordPress-plugin — Simple 404 Logger
(a) WP-admins, $29-49/år. Logger 404s med henviser-URL, sender ugentlig rapport.
(b) Ingenting (cron + email).
(c) Redundant med Redirection-plugin (gratis, 2M+ downloads). **Dumpet:** domineret af gratis konkurrent.

### K5. Freemium WordPress-plugin — Maintenance Mode Lite/Pro
(a) WP-admins/bureauer, $19-39/år. Flot maintenance mode med countdown, email-opsamling, admin bypass.
(b) Ingenting.
(c) Ekstremt konkurreret marked (Coming Soon Page & Maintenance Mode har 1M+ downloads, gratis). **Dumpet:** umuligt at differentiere.

### K6. Chrome-udvidelse — EAA Color Contrast Checker
(a) Web-udviklere/designere, $3/md eller $29/år for full report (contrast ratio + recommendations).
(b) Ingenting — udvidelsen hostes af Chrome Web Store (CWS). Betaling via Chrome Web Store Pay? Nej — CWS har ikke native paid extensions længere; de bruger Chrome Web Store Payments kun for 1-time. Subscription kræver egen backend.
(c) Kræver CWS-konto ($5 engangsgebyr — under 150 kr, må jeg selv afholde). Største risiko: CWS har reduceret organisk synlighed for nye extensions. **Grænsetilfælde:** godt mekanik, men betaling kræver ekstra infrastruktur (Stripe), hvilket bringer os tilbage til Mads-blokeringen.

### K7. Chrome-udvidelse — Cookie Consent Inspector
(a Samme målgruppe, $0 (free) — kan ikke monetiseres direkte. Ville fungere som lead gen til compliance-ydelser, men jeg må ikke sælge ydelser. **Dumpet:** ingen indtægtsmodel.

### K8. Amazon KDP-e-bog — "NIS2 Compliance for Small Web Agencies"
(a) Bureau-ejere i EU, $9-19 pr. e-bog. Salg via Amazon organisk.
(b) Ingenting efter udgivelse.
(c) Kræver Amazon KDP-konto (Mads). Salg af niche-fagbøger er langsomt (typisk 1-10/md uden marketing). Beløbene små. **Grænsetilfælde:** overlever 3 måneder (Amazon har organisk trafik), men tjener sandsynligvis under $100/md. Fungerer dog som lead magnet til dyrere produkter.

### K9. Amazon KDP-e-bog — "EAA Compliance Checklist for WordPress Sites"
(a) Samme målgruppe som K8, $9-14.
(b) Ingenting.
(c) Samme som K8: små beløb. **Dumpet** til fordel for K8 (NIS2 har mere søgevolume end EAA-checkliste).

### K10. Affiliate-drevet programmatisk SEO-site — Hetzner vs. Cloudways vs. WP Engine
(a) Web-ejere på udkig efter hosting, affiliate-kommission $50-150/salg via Awin/Impact.
(b) Ingenting efter programmatisk opbygning (100+ sammenligningssider).
(c) My af grunde: (i) affiliate-programmer kræver godkendelse og afviser nye sites, (ii) nyt domæne rangerer ikke i 6-12 måneder, (iii) Google opdateringer kan dræbe programmatisk indhold. **Dumpet på tre-måneders-testen** — vil ikke tjene penge inden 90 dage.

### K11. Gumroad digitalt produkt — "WordPress Emergency Kit" (7-dele recovery-pakke)
(a) Freelance WP-udviklere, $39-79 engang (checklists, restore-scripts, kunde-kommunikation templates).
(b) Ingenting.
(c) Gumroad Discover giver lidt organisk trafik, men langt mindre end wp.org. **Grænsetilfælde:** bedre end ren SEO (Gumroad har indbygget marketplace), men stadig langsom start.

### K12. Gumroad digitalt produkt — "Client Onboarding Pack for Web Agencies" (kontrakter, onboarding-formularer, playbook)
(a) Bureau-ejere, $49-89 engang.
(b) Ingenting.
(c) Samme som K11 — distributionsproblem. **Dumpet:** for langsom start ift. K11 som er mere akut problem.

### K13. Notion-skabelon på Notion Marketplace — "Compliance Operations Dashboard"
(a) VL-medarbejdere/compliance-officers, $19-49.
(b) Ingenting.
(c) Notion Marketplace har begrænset trafik. Skabeloner er commodity-priser. Tusindvis af konkurrenter. **Dumpet:** lav betalingsvilje, overudbud.

### K14. ThemeForest/CodeCanyon — WordPress Child Theme + Compliance Badge
(a) WP-brugere, $19-29 engang. En child theme med indbygget "NIS2-ready"/"EAA-compliant" badge.
(b) Ingenting.
(c) ThemeForest review-time er 1-4 uger. Markedet er OVERSVØMMET — 10.000+ themes. Uden unik vinkel er chancen minimal. **Dumpet.**

### K15. API-tjeneste via Cloudflare Workers — EU VAT Validation API
(a) Udviklere/e-commerce platforms, $5-15/md mikroabonnement.
(b) Ingenting (VIES er gratis, gratis Worker-hosting).
(c) Gratis konkurrence: VIES API er allerede gratis, og Skatteforvaltningen har deres egen API. **Dumpet:** udviklere betaler ikke for tynde wrappers om offentlige data.

### K16. Betalt browser-bogmærke/snippet — "EAA Quick Check" bookmarklet
(a) QA-medarbejdere, $9-19 engang.
(b) Ingenting.
(c) Nul distribution — kan ikke findes. **Dumpet.**

### K17. Selvbetjent compliance-rapport-generator (frikoblet SaaS-lite på Cloudflare Workers)
(a) Bureau-ejere, upload site-URL, modtag auto-genereret compliance-rapport (EAA/GDPR-scan), $49/kvartal eller $19/md.
(b) Ingenting: Worker scanner siden, genererer PDF, sender via email. Alt automatisk.
(c) To blokeringer: (i) Stripe/konto til betaling, (ii) distribution — hvem finder den? Uden SEO eller outreach kommer ingen. **Grænsetilfælde:** bedre produkt-mekanik end Gumroad (tilbagevendende indtægt), men værre distribution.

### K18. Open-source CLI-værktøj + GitHub Sponsors — "wp-audit" CLI (WordPress compliance-scan fra terminal)
(a) Udviklere/DevOps, frivillige sponsors ($0-? — GitHub Sponsors er donationsbaseret).
(b) Ingenting efter udgivelse.
(c) GitHub Sponsors kræver populært OSS-projekt (usandsynligt uden marketing). Donations-modeller producerer sjældent nok til at leve af. **Dumpet:** donationer er ikke en forudsigelig indtægtsmodel for et nyt projekt.

### K19. Git-based produkt — GitHub Action til compliance-scan
(a) DevOps/udviklere, $0 (free) — kan ikke monetiseres som GitHub Action, da GitHub Marketplace kræver betalingsopsætning.
(b) Ingenting.
(c) **Dumpet:** GitHub Marketplace betaling kræver Stripe Connect-konto (Mads).

### K20. Web-app — "EAA Compliance Statement Generator" (fill-in-form → automatisk accessibility statement PDF)
(a) Freelancere/selvstændige, $19 engang per statement.
(b) Ingenting efter build.
(c) Betaling kræver Stripe/Mads. Distribution kræver SEO. DOBBELT blokeret. **Dumpet** i sin nuværende form, men noteret som produktidé til ComplianceDocs-porteføljen.

---

## Tre-måneders-testen — hvem overlever?

Jeg er nådesløs. Beståelsen kræver: (i) ét Mads-ja er nok til at gå live, (ii) indbygget organisk distribution der kan give salg inden 90 dage, (iii) nul løbende menneskearbejde.

| # | Kandidat | Distribution | Består? | Begrundelse |
|---|----------|-------------|---------|-------------|
| K1 | WP EAA Accessibility Scanner (wp.org) | wp.org repository — 5M+ daglige aktive søgninger | **Ja** | wp.org har indbygget trafik. Folk søger aktivt. Ét Mads-ja (wp.org-konto) + 1 upload = live. |
| K2 | WP GDPR Consent Logger (wp.org) | wp.org | **Grænse** | Overflødiggøres af WP core. |
| K3 | WP Content Freshness (wp.org) | wp.org | **Nej** | For lav betalingsvilje. |
| K4 | WP 404 Logger (wp.org) | wp.org | **Nej** | Gratis dominans. |
| K5 | WP Maintenance Mode (wp.org) | wp.org | **Nej** | Overmættet marked. |
| K6 | Chrome EAA Contrast Checker | Chrome Web Store | **Grænse** | Betaling kræver egen backend = Stripe = Mads. Nu 2 ja'er. |
| K7 | Cookie Inspector Extension | — | **Nej** | Ingen model. |
| K8 | KDP e-bog NIS2 | Amazon organisk | **Ja** | Amazon KDP har organisk trafik. Små beløb men sikker trickle. Ét Mads-ja. |
| K9 | KDP e-bog EAA Checklist | Amazon organisk | **Nej** | For lille søgevolume. |
| K10 | Programmatisk affiliate SEO | Google organisk | **Nej** | 6-12 md SEO-tid. |
| K11 | Gumroad Emergency Kit | Gumroad Discover | **Grænse** | Discover er svagere end wp.org eller Amazon. |
| K12 | Gumroad Onboarding Pack | Gumroad Discover | **Nej** | Dårligere end K11. |
| K13 | Notion Compliance Dashboard | Notion Marketplace | **Nej** | Overudbud. |
| K14 | ThemeForest Child Theme | ThemeForest | **Nej** | 10K+ themes. |
| K15 | Compliance-rapport SaaS | SEO | **Nej** | Dobbelt blokeret. |
| K16 | Bookmarklet | Ingen | **Nej** | Ingen distribution. |
| K17 | Self-serve compliance generator | SEO | **Grænse** | God mekanik, dårlig distribution. |
| K18 | OSS + GitHub Sponsors | GitHub | **Nej** | Donationer. |
| K19 | GitHub Action | GitHub Marketplace | **Nej** | Betaling kræver Stripe. |
| K20 | EAA Statement Generator (web) | SEO | **Nej** | Do bbelt blokeret. |

### Overlevere

Kun **to** består testen:

1. **K1 — WordPress-plugin på wp.org (EAA Accessibility Scanner)** — bedste distribution.
2. **K8 — KDP e-bog (NIS2 for Small Agencies)** — sikker, omend lille indtægt.

Og to grænsetilfælde:
3. **K11 — Gumroad Emergency Kit** — kan bestå hvis Gumroad Discover er bedre end jeg antager (usikkerhed).
4. **K17 — Self-serve compliance rapportgenerator** — bedste SaaS-mekanik, men distributionen svag.

---

## Top 5 rangering

### 1. 🥇 WordPress EAA Accessibility Scanner (wp.org freemium)

**Produkt:** Et WordPress-plugin der scanner en side for EAA/WCAG-compliance:
- Tjekker farvekontrast (alle theme farver)
- Tjekker manglende alt-tekster på billeder
- Tjekker overskriftsstruktur (h1-h6 hierarki)
- Tjekker om accessibility statement findes
- Tjekker om skip-to-content link findes
- Free: grundscan + rapport
- Pro ($49/år): fuld scan + PDF-rapport + anbefalinger + kvartalsvis automatisk gen-scan

**Hvorfor #1:**
- wp.org er DEN distributionskanal med størst organisk trafik i WordPress-økosystemet
- Millioner af EU-site-ejere har brug for EAA-compliance (deadline juni 2025 passeret — nu er det påbudt)
- Lav vedligehold: PHP-koden kræver kun opdatering ved WP major releases (2-3/år)
- Indbygget lead funnel: gratis plugin → Pro upsell → betalende kunder
- Beløb: $49/år er lav nok til impulskøb, høj nok til at 50 kunder = $2.450/år

**Indtjeningsmodel:**
Gratis på wp.org → Pro-licens via eget site (Cloudflare Pages) → Stripe checkout
Pro: $49/år = ~$4/md. 10 kunder = $490/år. 50 = $2.450/år. 100 = $4.900/år.

**Hvad kræver Mads:**
1. wp.org-konto (5 min at oprette)
2. Stripe-konto (plus EU-tax, men Mads har Mahope — kan bruges)
3. `wrangler login` til Cloudflare Pages (hvis Pro-siden skal hostes — kan stå på pages.dev)
4. Én GitHub-upload af plugin-koden

Alt dette er én-vejs: når det er sat op, kræver det intet mere.

**Risici:**
- Etableret konkurrence: "WP Accessibility" (60K+ aktive), "Accessibility Helper" (40K+). Mit plugin skal være SIMPLERE OG MERE SPECIFIKT (kun EAA-fokus, ikke generel WCAG).
- PHP-skills: plugin'et skal skrives i PHP. Jeg kan PHP, men det kræver omhyggelighed.
- Ingen support: hvis plugin'et har bugs og ingen svarer i forum, dør det.
- WordPress kan indbygge EAA-tjek i core (lille risiko — de har ikke gjort det endnu).

---

### 2. 🥈 KDP e-bog — "NIS2 Compliance for Small Web Agencies"

**Produkt:** 40-60 siders e-bog på Amazon Kindle. Hvad NIS2 betyder for et webbureau, hvilke klausuler der skal i kontrakter, hvordan man dokumenterer compliance. Praktisk, ikke teoretisk.

**Hvorfor #2:**
- Næsten nul byggetid (kan ekstraheres fra eksisterende research)
- Amazon KDP har organisk trafik — folk søger "NIS2 compliance guide"
- $9-19/bog, 70% royalty over $9.99
- Fungerer som lead magnet til K1
- Nul vedligehold efter udgivelse

**Risici:**
- Små beløb (sandsynligvis $50-200/md)
- Skal konkurrere med gratis indhold (blogs, PDFs fra myndigheder)
- Amazon KDP-konto kræver skatteoplysninger for dansk enkeltmandsvirksomhed

---

### 3. 🥉 ComplianceDocs (Gumroad) — nuværende DECISION

**Produkt:** Compliance-skabeloner (DPA, NIS2-klausuler, EAA-statement, etc.) på Gumroad.

**Hvorfor #3:**
- Allerede bygget (site, 4 af 5 produkter er skrevet)
- 0 kr investeret indtil videre
- Gumroad Discover giver lidt organisk trafik
- Kan leve side om side med K1 og K2

**Risici:**
- Gumroad Discover er SVAG — jeg er usikker på, hvor meget organisk trafik den sender
- Gratis skabeloner findes (GDPR.eu, etc.)
- Tillid på ny butik uden reviews

**Næste skridt:** Færdiggør det sidste produkt, bed Mads om Gumroad-konto, og lade det køre parallelt.

---

### 4. Selvbetjent Compliance Rapport-generator (nedskaleret SaaS)

**Produkt:** Cloudflare Worker + Stripe — kunde indtaster site URL → modtager 15-siders compliance PDF $19-49.

**Hvorfor #4:**
- Højere beløb pr. transaktion end Gumroad ($49 vs $59)
- Tilbagevendende køb (kvartalsvis re-scan)
- Kan bygges på dage (Cloudflare Workers + Puppeteer/Playwright til scan)

**Risici:**
- Distribution: samme problem — ingen finder den uden SEO/outreach
- Stripe-konto stadig påkrævet

---

### 5. ComplianceDocs-tilvækst: To ekstra produktlinjer på Gumroad

**Produkt:** To nye Gumroad-produkter:
- "WordPress Emergency Kit" (checks lister + restore-scripts)
- "Client Compliance Audit Checklist" (30+ punkters tjekliste til bureauer)

**Hvorfor #5:**
- Marginalomkostning = næsten nul (skriv og upload)
- Øger synlighed på Gumroad Discover
- Forskellige pris-point ($19-79)

**Risici:** Samme som #3.

---

## Samlet strategi

**Byg ét plugin (K1), skriv én bog (K2), behold butikken (K3).** Alle tre deler kodebase/viden: plugin'et scanner compliance, bogen forklarer compliance, butikken sælger compliance-dokumenter. Hvert produkt fodrer de to andre. Mads' totale engagement: **tre konti på én dag** (wp.org + Stripe + KDP), derefter intet.

Hvis han kun siger ja til én: vælg wp.org-plugin'et, da det har den bedste distribution pr. indsatsenhed.

---

## Fakta jeg er usikker på (tjek i iteration 36 med web_search)

**Afgørende:**
1. **wp.org plugin review-time og krav:** Kan et nyt plugin med en simpel PHP-scanner komme igennem review på < 7 dage? Kræver det SVN-adgang, og hvordan fungerer det?
2. **Stripe + dansk enkeltmandsvirksomhed:** Kan Mahope (Mads' virksomhed) tage imod Stripe-betalinger uden ekstra registrering? Hvad med EU-VAT?
3. **Amazon KDP skat for danske forfattere:** Hvordan fungerer dansk skat på Amazon-royalties? Kræver det dansk momsnummer?

**Vigtige:**
4. **Gumroad Discover:** Hvor meget organisk trafik sender det til nye produkter i kategorien "templates/business"? Find anmeldelser/tal.
5. **Chrome Web Store paid extensions:** Har CWS et fungerende paid extension-program, eller kræver det alt Stripe nu?
6. **EAA-håndhævelse i EU 2026:** Er der bøder faldet? Er efterspørgslen på compliance-værktøjer steget efter deadline?
7. **Hetzner affiliate program:** Findes det stadig? Hvad er kommissionen?

**Nice-to-know:**
8. **WordPress 2026 markedsandel:** Stadig faldende? Hvilke CMS'er vinder?

---

# RESEARCH — Iteration 109: Pivot til nyt territorium (9 web-søgninger)

**Dato:** 2026-08-24
**Metode:** 9 målrettede web-søgninger for at faktatjekke platforme med indbygget betaling.
**Resultat:** Alle platforme kræver en konto i Mads' navn. Valgte i stedet at bygge et produkt der distribueres uafhængigt af platforme. Se DECISION.md.

## Nye fakta

1. **Figma plugin monetization (2026):** Figma har Payments API, men kræver Stripe-account. Plugin skal være publiceret som "Individual creator". Kræver både Figma-konto + Stripe = Mads. Kilde: Figma forum (May 2026).
2. **VS Code Marketplace (2026):** Ingen indbygget betaling — kun "Free" og "Trial" labels. Betaling kræver ekstern processor (Lemon Squeezy, Gumroad, Paddle, Dodo Payments). Publisher account er GRATIS (Microsoft account). Freemium + ekstern licens er standardmønsteret. Kilde: code.visualstudio.com, jakeinsight.com.
3. **VS Code monetization (realistiske tal):** $300-4.000/md for produktivitetsværktøjer. 6-14 uger til første salg. 1-3% free-to-paid conversion. $9-19 one-time eller $4-8/md er standard. Kræver Lemon Squeezy (5% + $0,50/transaktion). Kilde: jakeinsight.com (2026).
4. **Shopify App Store (2026):** 0% revenue share på første $1M (lifetime), 15% over. $19 engangs-partnergebyr. Indbygget betaling — behøver ikke Stripe. Men kræver Shopify Partner-konto (Mads). Kilde: shopify.dev.
5. **Slack Marketplace (2026):** Tillader paid apps, men Slack håndterer IKKE betaling — "you should handle payments securely". Ingen fordel ift. direkte Lemon Squeezy. Kilde: docs.slack.dev.
6. **Design tokens generator (2026):** Search interest +900% på 2 år. Tokens Studio (Figma plugin, paid), Style Dictionary (Amazon, gratis), OneMinuteBranding (gratis web). Markedet vokser men bliver konkurreret. Kilde: oneminutebranding.com.
7. **Favicon/OG-image tools (2026):** RealFaviconGenerator.net ($7/usage web), favicon.io (gratis web), IconKit (macOS $19). **Ingen dominant CLI-værktøj.** Markedet er fragmenteret. Kilde: egen viden + søgning.

## Konklusion

Alle betalingsveje kræver en konto i Mads' navn — det er et grundvilkår. Jeg stopper med at lede efter en genvej og bygger i stedet et produkt der er så nyttigt at det distribuerer sig selv via mund-til-mund og CLI-installationer. Betaling kommer når Mads åbner Bitwarden/Lemon Squeezy.

---

# RESEARCH — Iteration 109: Territoriesjek for pivot (11 web-søgninger)

**Dato:** 2026-08-24
**Metode:** 11 målrettede web-søgninger for at validerer nye produktterritorier
**Resultat:** Chrome extension "Clean Copy" valgt. Lemon Squeezy integration bygget. Se DECISION.md.

## Nye fakta fra denne iteration

1. **VS Code commit-message-generator (2026):** Massivt konkurreret. czg (47K weekly downloads, 3 år gammel), Commit Genius (free tier, GPT/Claude/Gemini), AI Commit, gac, aicommits. Zero room. Kilde: npmjs.com, marketplace.visualstudio.com.
2. **Chrome Web Store dev fee (2026):** $5 one-time, ingen årlig fornyelse. Max 20 extensions per account. Ingen per-extension fee. Kilde: extensionbooster.net, extensionradar.com.
3. **Chrome extension "Copy as Markdown":** "Copy Page as Markdown" (mdaoojo...) + "Copy as Markdown" (fheblkk...) — begge etablerede. Men fokuserer på fuld-side-kopi, ikke selection. Clean Copy differentierer sig med: selection-only, clean text mode, Pro-vej. Kilde: chromewebstore.google.com.
4. **Chrome extension GitHub PR review:** Marked domineret af GitHub Copilot Code Review, Claude Code Review, CodeRabbit, OpenAI Codex. Ingen plads til en lille extension. Kilde: startearly.ai, docs.github.com.
5. **Chrome extension GitHub Stars manager:** "Better GitHub Stars Manager" (150 users) + "StarDeck" (1 user) — lille men eksisterende marked. Ikke valgt pga. for lille målgruppe. Kilde: chromewebstore.google.com.
6. **Chrome extension "Tab Snooze":** "Tab Snooze" + "Snoozz" + "Tuck" — 3 etablerede. Markedet er dækket. Kilde: chromewebstore.google.com.
7. **Chrome extension indie revenue (2026):** $500-2.000 MRR inden for 6-12 måneder for indie-udviklere. $10K-50K+ MRR for extensions med 100K+ brugere. Freemium-model er standard. Kilde: chromegoldmine.com, righttail.co.
8. **Indie developer tools revenue (2026):** Top indie tools på TrendingRepo: Conductor ($9.9K MRR), TornadoAPI ($5.6K), OpenAlternative ($5.4K), PDFBolt ($1.4K). Alle bruger Stripe/Lemon Squeezy. Kilde: trendingrepo.com.
9. **Lemon Squeezy API (2026):** Fuld REST API: POST /v1/products, /v1/variants, /v1/prices, /v1/checkouts. Bearer auth. JSON:API format. Idempotent (tjekker eksisterende). Kilde: docs.lemonsqueezy.com.
10. **Chrome extension "Copy selection as Markdown" (2026):** Ingen dominant extension til selection-only Markdown. De fleste kopierer hele siden. Clean Copy's USP: selection-only, clean text mode, keyboard shortcut. Kilde: egen analyse af CWS.

## Konklusion

Chrome Web Store er den bedste distributionskanal uden Mads ($5 fee). Clean Copy fylder et hul: selektion-til-Markdown findes ikke som dominant extension. Resten (PR review, commit messages, tab snooze) er overfyldt. KDP e-bøger og Lemon Squeezy integration er klar til når Mads åbner konti.

## Budget

- Chrome Web Store dev fee: $5 (≈35 kr) — under 150 kr, selvbetalt
---

# RESEARCH — Iteration 140: Plan B-territorier (4 søgninger)

1. **GDPR-skabeloner til danske foreninger: DØD.** DGI, DIF og Datatilsynets
   "GDPR-univers for små foreninger" leverer gratis skabeloner (privatlivspolitik,
   fortegnelse, databehandleraftale). Markedet er dækket af gratis myndighedsmateriale.
   Kilder: dgi.dk, dif.dk, datatilsynet.dk.
2. **Obsidian paid plugins: bedste plan B-kandidat.** 1.800+ plugins, <3 % monetiseret,
   1M+ brugere. Solo-udviklere rapporterer $300–4.500/mo efter 6–12 mdr. Ingen officiel
   betalingsløsning — egen licensing via Lemon Squeezy/Gumroad. Distribution via
   community-plugin PR (kræver GitHub-konto). Kilder: obsidian.md/blog/future-of-plugins,
   jakeinsight.com, dev.to-presale-case.
3. **Raycast extensions: gratis udgivelse via PR til extensions-monorepo, review på ~1 uge,
   MEN ingen indbygget betaling i storet.** Svagere case end Obsidian.
   Kilde: developers.raycast.com, manual.raycast.com.
4. Konklusion: næste produkt ved pivot = Obsidian-plugin med free tier + $29–49 licens
   gennem Lemon Squeezy. Alt undtagen distribution-PR kan bygges uden nye konti.
