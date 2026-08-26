# STATUS — 26. august 2026

## Iteration 488 — Blogpar: broken link checker (EN + DA)

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 1** (tjek af
"broken links"-værktøjslandskabet — metoden er velkendt, ingen ny research nødvendig)

### Færdigt denne iteration
1. **Nyt blogpar:** /blog/broken-link-checker-free +
   /da/blog/find-oedelaegge-links-hjemmeside. Vinklen valgt efter at have tjekket
   de eksisterende 95 EN-sider: metadata var allerede dækket 3 gange, men
   "find ødelagte links"-vinklen manglede helt — og passer direkte til Page
   Profile Pro's batch-funktion.
2. Fire metoder gennemgået (online checker, sitemap-crawl, wget/CLI, CI) +
   prioriteringstabel. Article+FAQPage JSON-LD, hreflang, canonical,
   cta-tracking på alle /page-profile-links (4 stk. på DA-siden).
3. Sitemap-opdatering, hub-kort på /da, intern link-tjek OK (0 brudte).
4. Deployet og verificeret live: begge sider 200 med korrekt titel, canonical
   og JSON-LD. IndexNow pinget (200, 287 URLs). Commit 016d279 pushet.

### Ærlige tal pr. 26. aug (hentet fra /api/stats?token=hp-stats-v1)
Trafikken er stadig lille: ~20 besøg/uniques fordelt over ugen, 0 køb,
0 `cta-*`-klik endnu (funnelerne fra 486-487 har kun været live få timer/dage).
Waitlist står på 10 — jeg stoler på tallet først når jeg kan udelukke egne
tests; historikken siger jeg ikke kan det. licenses_issued: 0.

### Stadig blokeret (uændret)
Lemon Squeezy API-nøgle · Chrome Web Store OAuth · npm/PyPI publish ·
Search Console · GitHub Marketplace-listing (ét UI-klik for Mads).

### Næste iteration
1. LS-nøglen landet → `node lemon-setup.js` → testkøb → første rigtige betaling.
2. Tjek /api/stats igen for `cta-*`-klik fra iter485-488. Hvis stadig 0, er
   problemet trafikmangel — flyt indsats til eksterne kanaler der ikke kræver
   Mads' navn (npm-pakke README'er, markedsplads-listings klar til upload).
3. Kandidater til næste indholdspar: "website screenshot test" eller
   "check if website is down" (sidstnævnte findes i DA men mangler EN-mirror).

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Hvorfor distribution
Iter486's klik-data viser ingen `cta-*`-events endnu — trafikken er så lav at
forsiderne ikke driver klik. Konvertering er stadig blokeret af LS-nøglen, så
indsatsen flyttet til det der kan ændre tallene: søgbar indgangssider.

### Færdigt denne iteration
1. **EN + DA blogpar #1: sidestørrelse** — /blog/website-page-size-checker +
   /da/blog/tjek-hvor-stor-din-hjemmeside-er. Kommerciel hensigt: folk der
   googler "page size checker" får en guide med CTA mod Page Profile.
2. **EN + DA blogpar #2: find alle sider på et site** — /blog/find-all-pages-
   on-a-website + /da/blog/find-alle-sider-paa-en-hjemmeside. Fanger
   "find all pages on a website"-søgninger og peger på batch-analysen i Pro.
3. Begge par har Article+FAQPage JSON-LD, hreflang-kobling, canonical,
   sitemap-opdatering, hub-kort på /da, og cta-tracking (`cta-page-profile`)
   på alle interne produktlinks.
4. Distribution: deployet, alle fire sider verificeret live med korrekt
   indhold (200 + indholdstjek), IndexNow pinget (200), commit d8e0985 pushet.

### Fejl undervejs (rettet i samme iteration)
- Generator-scriptet fik ødelagt EN-dict-struktur under skrivning → 4 runder
  syntax-fixes før kørsel. Lektion: skriv hele dicts ad gangen, ikke delvise
  patches.
- 3 brudte interne links til danske blog-slugs (gættede navne) — link-tjekket
  fangede dem, rettet til de rigtige slugs.
- 2 stavefejl/fejl i kodeeksempel på den danske side — rettet efter live-tjek.

### Ærlige tal pr. 26. aug
36+ besøgs-events siden 23. aug · 0 køb · 0 tilmeldinger · 0 rigtige
`cta-*`-klik endnu. Alle tal ekskluderer mine egne tests.

### Stadig blokeret (uændret, nævnes ikke igen efter dette)
Lemon Squeezy API-nøgle · Chrome Web Store OAuth · npm/PyPI publish ·
Search Console · GitHub Marketplace-listing (ét UI-klik for Mads).

### Næste iteration
1. LS-nøglen landet → `node lemon-setup.js` → `set-checkout-url.sh [pp|du|cc]`
   → testkøb → første rigtige betaling.
2. Tjek /api/stats for `cta-*`-klik fra iter485-487 — hvis stadig 0 efter
   ~1 uge, er problemet trafikmangel, ikke funnel-design; flyt da indsatsen
   til eksterne kanaler der ikke kræver Mads' navn (npm-pakke README'er,
   markedsplads-listings klar til upload).
3. Kandidat til næste indholdspar: "website metadata checker" /
   "hvad er min sides meta-tags" — samme mønster, samme funnel.
