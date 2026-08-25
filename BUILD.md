# BUILD — hvad der er bygget, hvad der mangler

## Bygget (hele historien)

**EAA Compliance Scanner Desktop — CI multi-platform builds (v1.3.3)**

- **CI workflow** (build-desktop.yml) bygger nu automatisk på tag push:
  - macOS: ARM64 + x64 (DMG + ZIP)
  - Linux: AppImage + .deb
  - Windows: NSIS installer + portable .exe
  - Release job: opretter release + uploader alle assets
- **v1.3.1 release** — 7 assets live (macOS 4, Linux 2, Windows 1)
- **v1.3.2** — tilføjer Windows portable .exe (artifact naming fix)
- **v1.3.3** — version bump (1.3.0→1.3.3 i main.js), CI-trigger fix (tag-only flow), 8 assets live
- **SEO blog post** — ny guide: "EAA Compliance Scanner Desktop" (site/blog/eaa-compliance-scanner-desktop.html)
- **Downloads page** — alle 8 v1.3.3-links, Pro-badge, Pro-sektion, opdateret source zip

**EAA Compliance Scanner Desktop — v1.2.0 macOS ARM64 build + distribution**
[...]

**EAA Compliance Scanner Desktop — v1.3.0 Pro license + batch scan**
[...]

**NIS2-økosystemet:** [uændret]

**Compliance site check:** [uændret]

**Clean Copy-økosystemet:** [uændret]

**Checkout-infrastruktur:** [uændret]

**Iter 313: Compliance-site-check CTA + rapport-download + SEO-blogpost**

- **CTA i 21 compliance-blogs (EN+DA):** "Scan your site" aside-kort indsat i
  toppen af artikler om GDPR, EAA, NIS2, cookie-consent, accessibilitet m.fl.
  Linker til scanneren. Styling matcher eksisterende book-cta.
- **Rapport-download-knap (.md):** Klient-side Blob-download af scan-resultatet
  som Markdown-fil med score, grade, alle tjek og konkrete fixes. Ingen server,
  ingen email, ingen konto. Paa EN + DA scanner-sider.
- **Ny blogpost:** /blog/free-website-compliance-checker (EN) +
  /da/blog/gratis-compliance-tjek-hjemmeside (DA). SEO-optimeret med schema,
  canonical, hreflang. I sitemap.
- **Sitemap opdateret** med begge nye poster.
- **JS-validert:** node --check paa begge scanner-sider.

## Mangler (blokeret)

- Betalingsintegration (Lemon Squeezy-nøgle i Bitwarden)
- Email levering til leads (kræver Mads' accept)
- KDP-e-bog (kræver Mads' KDP-konto)
- CWS-upload (kræver OAuth-credentials i Bitwarden)
- Obsidian community submit (kræver Mads' login)
- Alle andre kanaler (kræver konti i Mads' navn)

## Plan for naeste byg

1. Overvaag om CTA i blogs tracker trafik — tjek /api/stats
2. Hvis scanneren faar >0 reelle scans: overvej email-indgang paa resultatet
   (lead capture) — kraever Mads' accept og email-infrastruktur
3. Alternativt: nyt produkt der kan tage imod penge via GitHub Sponsors eller
   lignende zero-account-kanal

**Iter 314: Maale- og synlighedshuller lukket for compliance-site-check**

- **scan/report-dl event-tracking** i scan() og downloadReport() paa EN + DA
  scanner-sider. Samme trackEvent()-system som cookie-check. Data synlig i
  /api/stats?token=hp-stats-v1&days=3.
- **Homepage-kort** i index.html free-tools-sektionen: "Compliance Checker" direkte
  link + CTA-tracker-regex opdateret til compliance-site-check.
- **llms.txt** tilfoejet compliance-site-check (EN + DA).
- **API-dokumentation** site/api-compliance-scan-readme.md: dokumenterer
  /api/compliance-scan endpoint med eksempler og felttabel.
**Iter 316: passiv-mcp — nyt produkt, MCP-server med gratis web-værktøjer (NYT SPOR)**

- **Hvad:** MCP-server (Model Context Protocol) der eksponerer 4 eksisterende
  gratis API'er som værktøjer til Claude Desktop/Code/Cursor m.fl.:
  html_to_markdown (/api/clean-copy), compliance_scan (/api/compliance-scan),
  profile_page (/api/profile), check_security_headers (/api/header-check).
- **Hvorfor dette spor:** Nul Mads-afhængighed (distribueres via npx github:),
  indbygget distribution i det voksende MCP-økosystem, genbruger backend der
  allerede kører, og kan tage imod betaling senere (Pro-tier når Lemon
  Squeezy-nøglen kommer). STATUS.md iter 315 bad om netop dette.
- **Bygget:** server.js (zero-deps, håndrullet JSON-RPC 2.0 stdio-transport),
  test.js (10 e2e-tests over ægte stdio), README.md, package.json (bin +
  files-whitelist), LICENSE.
- **Udgivet:** github.com/mahope/passiv-mcp (public, topics sat).
- **Verificering:** node test.js → 10/10 PASS (inkl. live-kald mod alle fire
  API'er). npx github:mahope/passiv-mcp røgtestet fra /tmp: initialize +
  html_to_markdown virker via den offentlige repo-URL.
- **Fejl fundet og ret under bygning:** normalizeUrl lod garbage-hosts som
  "ftp://bad" igennem til API'et (returnerede en meningsløs D-rapport) — nu
  afvist med klar fejlbesked; dækket af test.
- **Næste skridt for sporet:** npm-publicering (npm login = Mads-handling),
  registrering i MCP-kataloger (mcp.so, PulseMCP, glama.ai m.fl.), evt.
  server.json + MCP Registry submit når den er åben.

**Iter 321: Complete EU Compliance Bundle — ready-to-sell digitalt produkt**

- **Pivot:** passiv-mcp havde 0 visninger efter 14 dage i registry. Pivot-tærskel
  overskredet. Nyt spor: samlet digitalt bundle af 6 eksisterende e-books, klar til
  salg når Lemon Squeezy-nøgle ankommer.
- **build_bundle_all.py** — PDF-kompilation af alle 6 e-books via reportlab.
  Håndterer: titelside, indholdsfortegnelse, H1-H3, lister, tabeller, korte
  kodeblokke, kolofon.
- **Site/downloads/**: ZIP (6 EPUBs + combined PDF, 204 KB) + PDF alene (154 KB).
- **Landing page** på `/books/compliance-bundle`: hero, $29 pris (placeholder),
  gratis download, 4 benefits, alle 6 bøger vist, FAQ med LS-checkout-info.
- **Opdateret homepage:** bundle-links i hero, quiz-sektion, FAQ (Gumroad/KDP
  fjernet, LS nævnt). Books-index: bundle-promo-kort.
- **Verificering:** Deploy + curl — alle nye sider og downloads HTTP 200.
- **Mangler:** `node lemon-setup.js` med LS-API-nøgle → checkout-link → live.
