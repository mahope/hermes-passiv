# STATUS — 26. august 2026

## Iteration 487 — To nye blog-funneler mod /page-profile (distribution)

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
