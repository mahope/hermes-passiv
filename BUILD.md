# BUILD — hvad der er bygget, hvad der mangler

## Bygget (hele historien)

**EAA Compliance Scanner Desktop — CI multi-platform builds (v1.3.1)**

- **CI workflow** (build-desktop.yml) bygger nu automatisk på tag push:
  - macOS: ARM64 + x64 (DMG + ZIP)
  - Linux: AppImage + .deb
  - Windows: NSIS installer + portable .exe
  - Release job: opretter release + uploader alle assets
- **v1.3.1 release** — 7 assets live (macOS 4, Linux 2, Windows 1)
- **v1.3.2** — tilføjer Windows portable .exe (artifact naming fix)

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

1. Verificer v1.3.2 CI-resultat (Windows portable)
2. Opdater downloads page med portable .exe link
3. Overvej npm/pip publish som næste distributionskanal