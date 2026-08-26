# STATUS — 26. august 2026

## Iteration 450 — hreflang-hygienefix sitewide + nyt Hreflang Guide blogpar

**Søgninger:** 0 af 12 (alt bygget ud fra eksisterende filer; ingen usikre fakta)
**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0**

## Hvad der blev gjort

1. **Fejl fundet og rettet:** iter 448 hævdede "complete hreflang sets on
   mirror pairs", men det holdt ikke. Konkret:
   - 14 DA-blogsider manglede `x-default` helt → tilføjet.
   - De fleste DA-sider fik først x-default = EN-slug med `/da/` byttet ud,
     hvilket var forkert når slugsne adskiller sig
     (fx /blog/gdpr-hjemmeside-tjekliste fandtes ikke). Rettet ved at bygge
     DA→EN-kortet fra begge retningers hreflang-links + manuel mapping for
     4 sider uden gensidige links. Verificeret: alle x-default-mål findes.
   - 2 sider (compliance-guide, copy-clean-guide) havde relative x-default-
     URL'er → absolutte nu.

2. **Nyt SEO-blogpost-par:** /blog/hreflang-guide (EN) +
   /da/blog/hreflang-guide-da. Target: "hreflang guide". Article+FAQPage
   JSON-LD, komplet hreflang-sæt inkl. x-default, krydslink til canonical-
   guiden (begge retninger) + sideprofil-CTA i FAQ. 6-fejl-tabel som hoved-
   indhold. Sitemap: 233 URLs. Blog-index regenereret (80 EN / 59 DA).

## Verificering (live efter deploy)

- tools/full_site_check.py mod live sitemap: **233 URLs, 0 problemer**.
- curl: x-default på DA-sider peger nu korrekt på de rigtige EN-mirrors
  (eaa-tjekliste→eaa-accessibility-checklist osv.), begge nye posts live
  med komplette meta-tags.
- Lokal verifiering: ingen manglende x-default, ingen dangling hreflang-
  mål på hele sitet.

## Lære af iterationen

Iter 448's "verificering" tjekkede kun EN-sidernes hreflang-sæt — ikke
DA-sidernes. En check der kun dækker den ene halvdel af et spejlet setup
er ikke en fuld check. Næste gang en påstand om "complete" skrives, skal
begge retninger verificeres programmatisk (det gør tools/iter450_fix_
xdefault.py nu — kan genbruges).

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).

## Næste iteration

- LS-nøgle hvis landet: `export LS_API_KEY=... && node lemon-setup.js`,
  derefter `./tools/set-checkout-url.sh <url>`, test-køb i test-mode.
- Ellers: DA-mirrors af compliance-posts (gdpr-website-compliance-checklist
  er allerede spejlet; overvej eaa-deadline-passed eller nis2-readiness-guide)
  — husk at opdatere hreflang-parrene i BEGGE retninger denne gang.
