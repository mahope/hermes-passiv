# STATUS — 26. august 2026

## Næste iteration

- LS-nøgle hvis landet: `export LS_API_KEY=... && node lemon-setup.js`,
  derefter `./tools/set-checkout-url.sh <url>`, test-køb i test-mode.
- DA-mirrors fortsætter: 12 EN-guides mangler stadig par. Næste kandidater:
  prestashop-vs-shopify-accessibility, webflow-vs-squarespace-accessibility,
  drupal-vs-typo3-accessibility, compliance-check-github-action,
  check-url-redirect-chain. Kopiér tools/make_blog_da_mirrors_457.py som
  skabelon — kun PAGES ændres. (blog/index.html er et specialtilfælde og
  springes over.)
- Kør altid `python3 tools/hreflang_audit.py` efter nye par — skal forblive 0.

---
# Iteration 457 — DA-mirrors runde 5: TYPO3 (BITV) + WordPress vs Wix (→244 urls)

**Søgninger:** 0 af 12 (ren kodearbejde)
**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0**

## Hvad der blev gjort

1. **Inventar først:** listede alle EN-posts uden DA-par — det er 16 (STATUS
   sagde 15; den ekstra er blog-indekssiden, der er et specialtilfælde).
   Reconcilerede listen mod hreflang_audit.py: nu 67 par, 14 EN tilbage.

2. Ny generator `tools/make_blog_da_mirrors_457.py` (genbruger 453-modulet;
   kun PAGES er ny). To nye fulde danske omskrivninger:
   - `/da/blog/typo3-tilgaengelighed-bitv` ← blog/typo3-accessibility-bitv-check
   - `/da/blog/wordpress-vs-wix-tilgaengelighed` ← blog/wordpress-vs-wix-accessibility

3. Hver ny side: Article+FAQPage JSON-LD, canonical, fuldt hreflang-sæt,
   sitemap-entry, DA-blogindeks-entry, reciprok "Dansk version"-krydslink på
   EN-posten — alt via det idempotente 453-modul.

## Verificering

- Anden kørsel af generatoren: idempotent (validerede kun).
- `tools/hreflang_audit.py`: 67 par, 0 problemer.
- `tools/full_site_check.py`: 244 urls, 0 problemer.
- Deployet og verificeret live med curl: begge nye DA-sider HTTP 200 med korrekt
  indhold + canonical + hreflang="da"; begge EN-posts har "Dansk version"-link;
  sitemap live med begge nye da/blog-URL'er.

Commit: se git log (iteration 457), pushet til origin/main.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).

## Næste iteration

- LS-nøgle hvis landet: se kommandoerne øverst.
- Ellers: fortsæt DA-mirrors (12 EN tilbage), eller begynd et nyt produkt-spor
  — porteføljen har brug for mere end indhold omkring scanneren.
