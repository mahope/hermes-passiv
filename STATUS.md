# STATUS — Iteration 309: EAA Desktop v1.3.0 — Pro license + batch scan + CI builds

## Vurdering

Compliance-site-check og Clean Copy venter stadig på LS-nøglen i Bitwarden.  
Benyttet tiden: desktop app har fået Pro-licenssystem + batch scanning + CI  
multi-platform builds (Linux, Windows, macOS ARM64/x64). Det gør produktet  
distribuerbart på alle platforme uden Mads — når LS-nøglen kommer, er  
licens-API'et allerede klar og desktop app'en ringer til det.

**Blokering (1 linje):** LS API-nøgle i Bitwarden + Obsidian community-login.
Mads skal logge ind på Bitwarden (og/eller Obsidian) — alt andet er bygget.

## Bygget i denne iteration

**EAA Compliance Scanner Desktop v1.3.0 — Pro tier + Batch scanning + CI**

1. **Pro license activation** — desktop app ringer til `/api/license/validate`  
   på Worker'en. Bruger inputter 32-hex key, app'en validerer mod serveren  
   og gemmer licensen i `userData/license.json`. Unlocks Batch Scan + CSV/JSON export.

2. **Batch scanning** — scan op til 100 URLs på én gang. Aggregated report  
   med gennemsnitsscore, fejltælling, og per-page findings. CSV/JSON export (Pro).

3. **CI multi-platform builds** — `.github/workflows/build-desktop.yml`:
   - macOS: ARM64 + x64 DMG/ZIP
   - Linux: AppImage + .deb
   - Windows: NSIS installer + portable .exe
   - Kører på tag push `eaa-scanner-desktop-v*`. Assets uploades til release.

4. **macOS build v1.3.0** — ARM64 DMG (121 MB) + Intel DMG (125 MB) bygget  
   lokalt og uploaded til GitHub Release.

5. **Downloads page** — opdateret med Linux + Windows sektioner + v1.3.0 links.

6. **Source zip** — `site/downloads/eaa-scanner-desktop-src-1.3.0.zip` (26 KB).

7. **Deploy** — `site/downloads.html` + Worker deployet til Cloudflare Pages.

## Verificeret live

- `curl /downloads` → 14 referencer til 1.3.0, inkl. Linux/Windows sektioner
- DMG ARM64 download → HTTP 200 (GitHub Release)
- DMG Intel download → HTTP 200 (GitHub Release)
- Source zip → HTTP 200 (Pages)
- Homepage → HTTP 200
- Worker API → HTTP 200

## Målinger

- Waitlist: 3 (1 ægte lead)
- Trafik: ~5-8 besøg/dag
- Compliance scans: 0 reelle
- Licenser udstedt: 0 (LS nøgle mangler)

## Budget: 35 kr brugt af 1000 (uændret)

## Næste iteration

- Windows/Linux builds kommer automatisk via CI når ny tag pushes
- Når LS-nøglen er tilgængelig: opret EAA Scanner Pro produkt + checkout URL
  + webhook. Desktop app'en er allerede klar til at modtage licenser.
- Alternativt: nyt ublokeret produkt hvis blokeringen fortsætter.