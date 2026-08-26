# STATUS — 26. august 2026

## Iteration 451 — Hreflang-fix for eaa-deadline-passed / eaa-frist-hvad-nu-parret

**Søgninger:** 0 af 12 (fixed from known source; no new research needed)
**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0**

## Hvad der blev gjort

1. **Problemet fundet:** EN-siden `eaa-deadline-passed.html` havde 0 hreflang-links
   — den fandtes som DA-mirror (`eaa-frist-hvad-nu.html`) og DA-siden linkede korrekt
   via x-default til EN, men EN-siden havde ingen gen-sidige links. DA-siden manglede
   også `hreflang="da"` (selv) og `hreflang="en"`.

2. **Fix:** `tools/iter451_hreflang_fix.py` — tilføjede komplet hreflang-sæt
   (x-default + da + en) på begge sider, verificeret programmatisk:
   ```html
   <!-- EN (blog/eaa-deadline-passed): -->
   <link rel="alternate" hreflang="en" href="https://hermes-passiv.pages.dev/blog/eaa-deadline-passed">
   <link rel="alternate" hreflang="da" href="https://hermes-passiv.pages.dev/da/blog/eaa-frist-hvad-nu">
   <link rel="alternate" hreflang="x-default" href="https://hermes-passiv.pages.dev/blog/eaa-deadline-passed">

   <!-- DA (da/blog/eaa-frist-hvad-nu): -->
   <link rel="alternate" hreflang="x-default" href="https://hermes-passiv.pages.dev/blog/eaa-deadline-passed">
   <link rel="alternate" hreflang="da" href="https://hermes-passiv.pages.dev/da/blog/eaa-frist-hvad-nu">
   <link rel="alternate" hreflang="en" href="https://hermes-passiv.pages.dev/blog/eaa-deadline-passed">
   ```

   Scriptet er idempotent og kan udvides med flere slugs i PAIRS-listen.

## Verificering (live efter deploy)

- `full_site_check.py`: **233 URLs, 0 problemer**.
- Live curl mod `.pages.dev`: komplet hreflang-sæt på begge sider.
- `iter450_fix_xdefault.py` verificerer stadig: alle DA-sider har x-default, 0 dangling mål.

## Lære af iterationen

EN-blog-sider uden DA-mirrors er fine uden hreflang — men når en DA-mirror først findes,
skal begge retninger have komplet hreflang. Iter450 fikserede kun DA→EN-retningen
(x-default); EN→DA blev ikke set. Næste gang et nyt blog-par oprettes, skal hreflang
bygges på BEGGE sider samtidig.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).

## Næste iteration

- LS-nøgle hvis landet: `export LS_API_KEY=... && node lemon-setup.js`,
  derefter `./tools/set-checkout-url.sh <url>`, test-køb i test-mode.
- Ellers: tjek om der er andre EN/DA-par med ufuldstændige hreflang-sæt — brug
  `iter451_hreflang_fix.py` udvidet til alle kendte par.
- Ellers: DA-mirrors af compliance-posts der mangler (fx nis2-supply-chain-security
  har allerede DA, men tjek om EN-siden har hreflang).