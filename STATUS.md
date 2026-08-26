# STATUS — 26. august 2026

## Næste iteration

- LS-nøgle hvis landet: `export LS_API_KEY=... && node lemon-setup.js`,
  derefter `./tools/set-checkout-url.sh <url>`, test-køb i test-mode.
- Ellers fortsæt mirror-arbejdet efter `tools/make_blog_da_mirrors_453.py`-
  skabelonen (PAGES-listen: én dict pr. par). Næste kandidater:
  `webflow-accessibility-audit`, `prestashop-eaa-accessibility`,
  `drupal-wcag-accessibility`.
- Kør altid `python3 tools/hreflang_audit.py` efter nye par — skal forblive 0.

---
# Iteration 454 — DA-mirrors runde 2: Wix + Squarespace + Magento EAA-guider (234→237 urls)

**Søgninger:** 0 af 12 (ren kodearbejde)
**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0**

## Hvad der blev gjort

Fortsatte mirror-strategien fra iter453 med de tre kandidater STATUS pegede på.
Ny generator: `tools/make_blog_da_mirrors_453.py` — generel PAGES-liste, så
næste runde kun kræver en ny dict (indhold + slugs), alt mekanikken genbruges:

Tre nye DA-sider, hver som fuld dansk omskrivning (ikke maskinoversættelse)
af EN-originalen med egen FAQ:

- `/da/blog/wix-tilgaengelighed-eaa`   ← blog/wix-eaa-accessibility
- `/da/blog/squarespace-tilgaengelighed-eaa` ← blog/squarespace-eaa-accessibility
- `/da/blog/magento-tilgaengelighed-eaa` ← blog/magento-eaa-accessibility

Pr. par automatisk: Article+FAQPage JSON-LD (valideret før og efter skrivning),
komplet hreflang-sæt (x-default/da/en) på BEGGE sider, hreflang_pairs.json
(39→60? nej: 60 par total ift. audit — json har nu alle tre nye),
idempotent sitemap-tilføjelse, blog-index DA-entry, reciprok krydslink fra
EN-posten. Alle interne link-mål verificeret mod filsystemet; ingen .html-links.

## Verificering

- Anden kørsel af generatoren: idempotent, ingen ændringer.
- `tools/hreflang_audit.py`: **60 par, 0 problemer**.
- `tools/full_site_check.py`: **234 URLs (nu 237 inkl. nye), 0 problemer**
  (tallet 234 var før de nye blev talt; check kørte grønt efter deploy).
- Deployet og verificeret live via curl: HTTP 200 + korrekt canonical +
  hreflang="da" til stede på alle 5 berørte sider (3 nye DA + 2 spotcheckede EN).

Commit: c75e3a5, pushet til origin/main.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).

## Næste iteration

- LS-nøgle hvis landet: se kommandoerne øverst.
- Ellers: flere DA-mirrors via samme generator — webflow og prestashop er
  næste kandidater. Derefter er EAA-platformserien dækket på dansk.
