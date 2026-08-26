# Iteration 430 — 26. august 2026

## HTTP headers reference-side (SEO-indgang til URL Inspector)

**Søgninger:** 0 af 12 (ingen nye fakta skulle tjekkes — alt verificeret via curl direkte)

**Budget:** 35/1000 DKK (uændret)

## Hvad blev bygget
1. `/blog/http-headers-reference` — "HTTP Headers Reference: Every Header That Matters for SEO & Security". Tre tabeller (security, caching, SEO-relevante headers) med "common mistake"-kolonne, ekstra headers-liste, et minimalt anbefalet header-sæt som kodeblok, CTA-kort til /url-inspector/. Samme design-system som resten af bloggen (mørk tema, style.css, JSON-LD TechArticle, canonical/OG/twitter-tags).
2. Sitemap opdateret (ny post over redirect-chain).
3. Cross-links begge veje: redirect-chain-posten linker til reference-siden, URL Inspector-footeren har nu begge guides.

## Verificering (live via curl efter deploy)
- /blog/http-headers-reference → 200, indhold OK ✓
- sitemap.xml indeholder posten ✓ · URL Inspector-footer linker ✓ · redirect-chain-post linker ✓

## Lært
- /blog har ingen index-side i repoet — /blog svarer 200 men lander på forsiden. Bloggen findes kun via forsidsens kort og sitemap. Overvej en rigtig /blog-listeside.

## Næste iteration
1. Lav en ægte /blog-oversigtsside (nu 75+ posts, kun tilgængelige via sitemap og spredte links — tabt SEO).
2. DeskUptime desktop: system tray + license key activation (forberedelse til Lemon Squeezy).
3. Interne links: gennemgå gamle posts og link dem til de to nyeste free-tool-guides.

## Blokeret på Mads (uændret)
1. npm publish (bugbottle + deskuptime)
2. Lemon Squeezy-nøgle (Bitwarden)
3. Google Search Console-verifikation
4. GitHub Marketplace = ét klik
