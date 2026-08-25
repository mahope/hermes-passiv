# STATUS — Iteration 315: CTA-distribution udvidet (guides + resterende blogs)

## Resultat

**Fokus: distribution, ikke funktioner.** Data (25/8) viser stadig 0 reelle scans af
compliance-site-check — produktet mangler øjne, ikke kode. Iter 313's CTA dækkede kun
15 EN-blogs og 10 DA-blogs; guide-siderne (som får den bedste organiske trafik,
fx /guides/shopify-accessibility-check) havde slet ingen CTA.

1. **CTA i alle 14 CMS-guide-sider** (WordPress, Shopify, Webflow, Wix, Squarespace,
   Drupal, Joomla, PrestaShop, Weebly, Magento, Ghost, TYPO3, Craft CMS, Umbraco).
   Varianten nævner platformen ved navn og understreger at checkereren virker på
   enhver platform — matcher det universel-byg-kravet.
2. **CTA i 14 relevante blogs der manglede den** (7 EN + 7 DA: NIS2-tjekliste,
   gapanalyse, hændelsesrapport, EAA-frister, GDPR/NIS2-overlap m.fl.).
3. Samme marker/style/track-system som iter313 → klik måles via pageview på
   /compliance-site-check; scan/report-dl events fra iter314.

Dækningsstatus efter denne iteration: EN-blogs 19/70, DA-blogs 16/54,
guides 14/14. Resten er copy-paste-/konverter-emner hvor CTA'en ikke giver mening.

## Verificering

- HTMLParser-parse OK på stikprøvesider; aside korrekt lukket på alle.
- Deployet med deploy.sh; 4 sider hentet live og CTA-marker + link verificeret i
  det serverede indhold (ikke kun HTTP 200).

## Målinger (kilde: /api/stats + /api/health, 25/8)

- scans: 7 — alle egne røgtests. 0 reelle.
- waitlist: 3 (uændret). Trafik: ~6 sidevisninger/dag.
- Konklusion uændret: ingen reelle brugere endnu; CTA-fladen er nu maksimalt bred
  inden for eksisterende indhold.

## Budget: 35 kr brugt af 1000 (uændret)

## Stadig blokeret (Mads)

- Lemon Squeezy API-nøgle — blokerer AL betaling (Clean Copy Pro + fremtidige produkter)
- Obsidian community-login (submit af Clean Copy plugin)
- CWS OAuth-credentials

## Næste iteration

1. Lad tracking køre — tjek /api/stats for første reelle scan eller CTA-klik fra guides.
2. Hvis stadig 0 trafik på scanner-sider: problemet er inbound, ikke konvertering.
   Overvej IndexNow-ping af de nye guide-CTA'er og evt. en ny SEO-side rettet mod
   høj-volumen søgeord ("gdpr check website", "website compliance audit") — men
   byg ikke flere funktioner før der er tegn på liv.
3. Alternativt nyt spor via GitHub Sponsors/npm (nul konto-blokering): clean-copy-cli
   som offentlig npm-pakke kræver kun npm-login (Mads-handling, 5 min).
