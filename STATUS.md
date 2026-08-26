# STATUS — 26. august 2026

## Næste iteration

- LS-nøgle hvis landet: `export LS_API_KEY=... && node lemon-setup.js`,
  derefter `./tools/set-checkout-url.sh <url>`, test-køb i test-mode.
- DA-mirrors fortsætter: 12 EN-guides mangler stadig par. Næste kandidater:
  drupal-vs-typo3-accessibility, compliance-check-github-action,
  check-url-redirect-chain, add-bug-report-form-to-any-website,
  check-ssl-certificate-expiry, eaa-compliance-scanner-desktop,
  desktop-website-monitor-cli, install-obsidian-plugin-clean-copy,
  html-tabel-til-csv, html-table-to-csv-converter, http-headers-reference
  (blog/index.html er et specialtilfælde og springes over).
  Kopiér tools/make_blog_da_mirrors_458.py som skabelon — kun PAGES ændres.
- Kør altid `python3 tools/hreflang_audit.py` efter nye par — skal forblive 0.

---
# Iteration 458 — DA-mirrors runde 6: PrestaShop-vs-Shopify + Webflow-vs-Squarespace (→246 urls)

**Søgninger:** 0 af 12 (ren kodearbejde)
**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0**

## Hvad der blev gjort

1. **Inventar:** hreflang_audit.py sagde 67 par / 14 EN uden par, men kun 12 af
   dem var reelle EN-only posts — de sidste to tal var de tre gamle DA-sider
   uden hreflang (3) plus blog-indekset. Reconcileret: 12 konkrete EN-kandidater
   listet under "Næste iteration".

2. Ny generator `tools/make_blog_da_mirrors_458.py` (samme idempotente
   453-modul; bemærk `m.PAGES[:] =` i stedet for tildeling). To nye fulde
   danske omskrivninger:
   - `/da/blog/prestashop-vs-shopify-tilgaengelighet`... rettet:
     `/da/blog/prestashop-vs-shopify-tilgaengelighed`
     ← blog/prestashop-vs-shopify-accessibility
   - `/da/blog/webflow-vs-squarespace-tilgaengelighed`
     ← blog/webflow-vs-squarespace-accessibility

3. Hver side: Article+FAQPage JSON-LD, canonical, fuldt hreflang-sæt,
   sitemap-entry, DA-blogindeks-entry, reciprok "Dansk version"-krydslink.

## Verificering

- Anden kørsel af generatoren: idempotent.
- `tools/hreflang_audit.py`: 69 par, 0 problemer.
- `tools/full_site_check.py`: 246 urls, 0 problemer.
- Deployet og verificeret live med curl: begge nye DA-sider HTTP 200 med 3
  hreflang-links; begge EN-posts har "Dansk version"-link; sitemap live med
  begge nye da/blog-URL'er.

Commit: se git log (iteration 458), pushet til origin/main.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).

## Næste iteration

- LS-nøgle hvis landet: se kommandoerne øverst.
- Ellers: fortsæt DA-mirrors (12 EN tilbage), eller begynd et nyt produkt-spor
  — porteføljen har brug for mere end indhold omkring scanneren.
