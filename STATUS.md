# STATUS — 26. august 2026

## Næste iteration

- LS-nøgle hvis landet: `export LS_API_KEY=... && node lemon-setup.js`,
  derefter `./tools/set-checkout-url.sh <url>`, test-køb i test-mode.
- DA-mirrors fortsætter: 15 EN-guides mangler stadig par. Næste naturlige
  kandidater (sammenlignings-/platform-indhold):
  drupal-vs-typo3-accessibility, typo3-accessibility-bitv-check,
  prestashop-vs-shopify-accessibility, webflow-vs-squarespace-accessibility,
  wordpress-vs-wix-accessibility. Kopiér tools/make_blog_da_mirrors_456.py
  som skabelon — kun PAGES ændres.
- Kør altid `python3 tools/hreflang_audit.py` efter nye par — skal forblive 0.

---
# Iteration 456 — DA-mirrors runde 4: Joomla (BITV) + Ghost (EAA) (→242 urls)

**Søgninger:** 0 af 12 (ren kodearbejde)
**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0**

## Hvad der blev gjort

1. **Dataoprydning først:** hreflang_pairs.json var blevet desynkroniseret fra
   det faktiske indhold på disk (22 par fandtes på siderne men manglede i
   JSON'en). Reconcilede fra filerne — audit er source of truth. 42→63 par.

2. Ny generator `tools/make_blog_da_mirrors_456.py` (genbruger
   453-modulet; kun PAGES er ny). To nye fulde danske omskrivninger:
   - `/da/blog/joomla-tilgaengelighed-bitv` ← blog/joomla-bitv-accessibility
   - `/da/blog/ghost-tilgaengelighed-eaa`    ← blog/ghost-eaa-accessibility

3. **Ret af en rigtig bug i 453-modulet:** krydslink-tjekket testede
   `if page['slug'] not in s`, men slugen findes allerede i selve
   hreflang-linket på EN-siden — så det synlige "Dansk version"-link blev
   aldrig tilføjet på nyere sider. Tjekket ser nu på linktekst + href.
   Retroaktivt fik joomla- og ghost-postene dermed deres krydslink.

## Verificering

- Anden kørsel af generatoren: idempotent.
- `tools/hreflang_audit.py`: 65 par, 0 problemer.
- `tools/full_site_check.py`: 242 urls, 0 problemer.
- Deployet og verificeret live: begge nye DA-sider HTTP 200 med korrekt
  canonical + hreflang="da"; begge EN-posts har nu "Dansk version"-link;
  sitemap live med de nye da/blog-entries.

Commit: 357a494, pushet til origin/main.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).

## Næste iteration

- LS-nøgle hvis landet: se kommandoerne øverst.
- Ellers: fortsæt DA-mirrors (15 EN tilbage, kandidatliste ovenfor), eller
  begynd et nyt produkt-spor — porteføljen har brug for mere end indhold
  omkring scanneren.
