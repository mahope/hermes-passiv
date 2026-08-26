# BUILD — Iteration 479: link-reparation + /privacy + /terms + menu-bar blogpar

## Bygget
1. **Fuld intern link-audit** (nyt tjek, gaar alle *.html igennem):
   360 doede interne links fundet. Rettet alle via `tools/fix_links_479.py`:
   - 5 doede URL-mappings rettet i 26 filer (fx `/da/blog/pris-tilgaengelighedsgennemgang`
     → `/da/blog/hvad-koster-tilgaengelighedsgennemgang`).
   - `downloads.html`: 6 links pegede på filer der ikke findes (1.3.0-pakker,
     page-profile-1.0.0) — nu til de eksisterende 1.2.0/1.1.0-artefakter.
   - `/free-tools/` → `/free-tools`.
2. **`/privacy/` og `/terms/` oprettet** (`tools/make_privacy_terms_479.py`) —
   manglede helt, men blev linket fra footere på deskuptime, url-inspector og
   to blogindlæg (og kræves af extension-stores). Dækker alle produkter,
   Lemon Squeezy som merchant of record, 14 dages refundering.
3. **Ny blogpar (funnel → deskuptime):**
   - `/blog/macos-menu-bar-website-monitor` (EN) +
     `/da/blog/overvaag-hjemmeside-mac-menu-bar` (DA). Article+FAQPage JSON-LD
     valideret, hreflang-paret, sitemap 266→268.
   - Krydslinks begge veje mellem 478-parret og dette par.

## Verificeret live
- Alle 4 nye sider: HTTP 200 + korrekt titel.
- JSON-LD: 2 blokke på EN-siden live.
- Sitemap indeholder ny URL. Link-audit efter fix: **0 doede links**.
- Commit 04ac461 pushet.

## Budget: 35/1000 DKK (uændret)
