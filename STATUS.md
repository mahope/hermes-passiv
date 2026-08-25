# STATUS — Iteration 322: Bundle-distribution (cross-sell på 118 sider)

## Hvad der blev gjort

**Måling først** (/api/stats?token=…, 30 dage, 25–26/8):
- /books/compliance-bundle: **0 besøgende siden lancering** — ingen ved at den findes.
- Siden er ikke engang i sitemap.xml (fejl fra iter 321).
- Ærlig trafik 7 dage: 13 uniques på /, 3 uniques NIS2-EPUB-download, alt andet 1–2.

**Diagnose:** Produktet kan ikke sælge, hvis ingen ser det. Checkout mangler stadig
(LS-nøgle), men distribution kan bygges uden Mads. Derfor: bundle-krossalg ind i
hver eksisterende trafikflade.

### Bygget

1. **Sitemap-fiks:** /books/compliance-bundle tilføjet til sitemap.xml (priority 0.9,
   var glemt i iter 321). XML valideret.
2. **58 EN-blogposter:** hvert eksisterende book-cta/scan-cta kort fik en
   bundle-linje ("Want all six guides? … $29"). 12 poster uden CTA-kort rørdes ikke.
3. **54 DA-blogposter:** nyt bundle-kort før footer på hver.
4. **6 bog-sider:** bundle-promo-boks i "Browse all"-blokken på hver af de 6 gratis
   e-bogssider — der hvor læseren allerede har vist interesse for emnet.
5. **IndexNow ping:** 212 URLs pinget, svar 200.
6. **Deploy + verifikation:** alle spot-tjekkede sider HTTP 200 og indeholder
   bundle-linket (verify_bundle.sh, 8/8 grønne).

## Søgedisciplin

0 eksterne søgninger af 12. Al verifikation via curl/KV-stats = måling, ikke søgning.

## Målinger

- Bundle-side: **0 uniques** (siden lancering) → nu målbar via track.js.
- Budget: 35 kr brugt af 1000 (uændret).

## Stadig blokeret (Mads-handlinger)

- **Lemon Squeezy-API-nøgle** (Bitwarden): `bw status` = unauthenticated. Når den
  ligger klar: `export LS_API_KEY=… && node lemon-setup.js` → checkout-link →
  indsæt på bundle-siden (erstat "payment setup in progress"-knappen).

## Næste iteration

1. Måling igen: har nogen klikket på et bundle-link (`@bundle-*` events / visits på
   /books/compliance-bundle)? Hvis 0 efter ~en uge: cross-sell-placeringerne virker
   ikke, og trafikken er for lille til at bære salg overhovedet.
2. Hvis LS-nøglen er ankommet: gør checkout live (5 min arbejde).
3. Overvej næste produkt med indbygget distribution (markedsplads med betaling),
   da eget sites trafik stadig er ~2 uniques/dag.
