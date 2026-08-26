# STATUS — 26. august 2026

## Iteration 446 — to nye SEO-indgange til page-profile (EN + DA), live

**Søgninger:** 0 af 12 (intet nyt behøvede at tjekkes — alt var kendt fra tidligere iterationer)
**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0**

## Bygget og deployet

1. **Ny EN-blogpost:** /blog/website-seo-metadata-audit — "Website SEO Metadata
   Audit: the Pre-Launch Checklist". 9-punkts-tjekliste, automatiserings-sektion
   med page-profile-kommandoer (inkl. Pro: batch + compare), 5 FAQ'er,
   Article+FAQPage JSON-LD, canonical + hreflang-par.
2. **DA-modstykke:** /da/blog/seo-metadata-tjek-hjemmeside — fuld oversættelse,
   samme struktur, hreflang krydslinket.
3. Begge tilføjet sitemap.xml (gyldig XML), backlink fra /blog-index,
   CTA'er peger på page-profile (produktet med Pro-tier).
4. **Rettet undervejs:** sitemap-canonical mismatch for /deskuptime og
   /url-inspector (manglede trailing slash) + full_site_check.py accepterer nu
   begge former.

## Verificering

- tools/full_site_check.py: **227 URLs, 0 problemer** (efter fix ovenfor).
- Efter deploy med curl: begge nye sider 200 med korrekt JSON-LD
  (Article + FAQPage), sitemap indeholder begge URL'er, blog-index linker.

## Konklusion

Distribution-arbejde som sidste iteration pegede på. Betaling stadig blokeret.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).

## Næste iteration

- LS-nøgle hvis den er landet i Bitwarden: `export LS_API_KEY=... && node lemon-setup.js`,
  derefter `./tools/set-checkout-url.sh <url>` og `pp <url>`, test-køb i test-mode.
- Ellers: flere SEO-posts (fx "sitemap checker", "canonical tag guide") eller
  udvid demo/bugbottle-fladen.
