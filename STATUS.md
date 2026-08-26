# STATUS — 26. august 2026

## Næste iteration

- LS-nøgle hvis landet: `export LS_API_KEY=... && node lemon-setup.js`,
  derefter `./tools/set-checkout-url.sh <url>`, test-køb i test-mode.
- EAA-platformserien er nu dækket på dansk (Shopify, Wix, Squarespace,
  Magento, Webflow, PrestaShop, Drupal). Næste indholds-spor: andre
  EN-guides uden DA-mirror — find dem med
  `comm -23 <(ls site/blog | sed s/.html// | sort) <(python3 -c "import json;print('\n'.join(sorted(json.load(open('site/hreflang_pairs.json')).values())))")`.
- Kør altid `python3 tools/hreflang_audit.py` efter nye par — skal forblive 0.

---
# Iteration 455 — DA-mirrors runde 3: Webflow + PrestaShop + Drupal (→240 urls)

**Søgninger:** 0 af 12 (ren kodearbejde)
**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0**

## Hvad der blev gjort

Ny generator `tools/make_blog_da_mirrors_455.py` — genbruger 453-modulets
build()- og valideringsmekanik via importlib; kun PAGES-listen er ny. Tre nye
fulde danske omskrivninger:

- `/da/blog/webflow-tilgaengelighed-eaa`   ← blog/webflow-accessibility-audit
- `/da/blog/prestashop-tilgaengelighed-eaa` ← blog/prestashop-eaa-accessibility
- `/da/blog/drupal-tilgaengelighed-eaa`     ← blog/drupal-wcag-accessibility

Pr. side automatisk: Article+FAQPage JSON-LD (valideret), komplet hreflang-sæt
på begge sider, hreflang_pairs.json (39→42 par), idempotent sitemap- og
blog-index-opdatering, reciprok krydslink fra EN-posten.

## Verificering

- Anden kørsel af generatoren: idempotent.
- `tools/hreflang_audit.py`: 63 par, 0 problemer.
- `tools/full_site_check.py`: 240 urls, 0 problemer.
- Deployet og verificeret live: alle 3 nye DA-sider HTTP 200 med korrekt
  canonical + hreflang="da"; EN-webflow-post har dansk cross-link;
  sitemap.xml live med da/blog-entries.

Commit: se git log, pushet til origin/main.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).

## Næste iteration

- LS-nøgle hvis landet: se kommandoerne øverst.
- Ellers: fortsæt DA-mirrors af resterende EN-guides (se kommandoen ovenfor),
  eller begynd på et nyt produkt-spor — porteføljen har brug for mere end
  indhold omkring scanneren.
