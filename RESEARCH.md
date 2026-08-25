# RESEARCH — Iteration 310: CI workflow fixes (0 eksterne søgninger)

**Dato:** 2026-08-25
**Metode:** In-repo CI debugging. 0 af 12 søgninger brugt.

## Fakta

1. **electron-builder 25.1.8 + electron@44.0.0** kræver node >= 22.12.0. CI brugte node 20.
2. **package-lock.json** skal være synkroniseret med package.json — `npm ci` fejler ellers med "Invalid: lock file's electron@35.7.5 does not satisfy electron@44.0.0".
3. **electron-builder auto-publish** når den detekterer et tag. Den prøver at oprette en GitHub Release via API'en, men GITHUB_TOKEN har ikke `contents: write` som standard på tag push. Løsning: `permissions: contents: write` + `--publish never`.
4. **electron-builder** kræver `repository` felt i package.json for at bygge (ellers "Cannot detect repository by .git/config").
5. **electron-builder** kræver `author.email` for Linux .deb builds (ellers "Please specify author 'email'").
6. **Windows artifact naming** — NSIS og portable producerer begge `.exe` med samme artifactName-mønster, så den ene overskriver den anden. Løsning: specifik `artifactName` per target (`*-setup.exe` / `*-portable.exe`).
7. **gh release create** — `--clobber` er til upload, ikke create. Forenklet til `gh release create <tag> <files> --repo --title --notes`.
8. **GitHub Releases** har 2 GB per-file limit. Cloudflare Pages har 25 MB. Desktop binaries (90-125 MB) går via GitHub Releases.

## Konklusion

CI workflow'et er nu stabilt. Fremtidige desktop releases kræver kun `git tag eaa-scanner-desktop-vX.Y.Z && git push origin --tags`. CI bygger alle 3 platforme, opretter release og uploader assets automatisk.