# BUILD — Iteration 495: top-CTA på alle blogindlæg

## Bygget
1. **Top-CTA på alle 191 blogindlæg (EN+DA).** Før iterationen manglede ~74
   indlæg CTA over artiklen; nu har alle to CTA-blokke øverst:
   - "Run the Free Scanner" → /scan (EN) / /scan-da (DA)
   - "Ask the Compliance AI" → /compliance-ai (EN) / /da/compliance-ai (DA)
2. Værktøj: `tools/add_top_cta_495.py` indsætter standard-parret efter
   `</header>` i filer uden `blog-tool-cta`. 5 filer med afvigende layout
   (macos-menu-bar-parret, redirect-chain, eaa-desktop, http-headers) fik
   CTA indsat manuelt efter hero/meta.

## Verificeret live
- Deploy via deploy.sh (74 filer uploadet).
- Spot-check live: canonical-url-guide, hreflang-guide-da og
  macos-menu-bar-website-monitor returnerer 200 med begge CTA-blokke.
- full_site_check.py: 286 URLs, 0 problemer.

## Budget: 35/1000 DKK (uændret)
