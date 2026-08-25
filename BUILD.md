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

## Mangler (blokeret)

- Betalingsintegration (Lemon Squeezy-nøgle i Bitwarden)
- Email levering til leads (kræver Mads' accept)
- KDP-e-bog (kræver Mads' KDP-konto)
- CWS-upload (kræver OAuth-credentials i Bitwarden)
- Obsidian community submit (kræver Mads' login)
- Alle andre kanaler (kræver konti i Mads' navn)

## Plan for næste byg

1. Næste desktop release: `git tag eaa-scanner-desktop-vX.Y.Z && git push origin --tags`
2. SEO: tilføj bloggen til sitemap, internt links til desktop app
3. Overvej npm/pip publish som næste distributionskanal