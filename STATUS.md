# STATUS — Iteration 310: CI FIXET + Desktop v1.3.2 (8 assets, alle platforme)

## Resultat

**CI workflow virker.** Efter 7 fix-forsøg bygger workflow'et nu automatisk alle 3 platforme
på tag push `eaa-scanner-desktop-v*`. Første vellykkede build: v1.3.2 med 8 assets:

- macOS: ARM64 DMG + ZIP, Intel DMG + ZIP (4)
- Linux: AppImage + .deb (2)
- Windows: NSIS installer + portable .exe (2)

**Downloads page opdateret.** Alle 8 links peger på v1.3.2 release. Site deployet.

## Hvad der blev rettet i CI

1. Node 20→22 (electron@44 kræver >=22.12)
2. Tag trigger (eaa-scanner-desktop-v*) til workflow
3. package-lock regenereret (var ude af sync)
4. repository + author.email i package.json
5. permissions: contents: write
6. --publish never (electron-builders auto-publish gav 403)
7. Windows artifact naming (NSIS vs portable separate filnavne)
8. gh release create forenklet (ingen --clobber, ingen 2>/dev/null)

## Fremtidig release-proces

`git tag eaa-scanner-desktop-vX.Y.Z && git push origin --tags`
→ CI bygger alle 3 platforme, opretter release, uploader assets.

## Stadig blokeret

- LS API-nøgle i Bitwarden — Mads skal logge ind
- Obsidian community-login — Mads skal submitte
- CWS OAuth-credentials — Mads

## Målinger

- Waitlist: 3 (1 ægte lead)
- Trafik: ~5-8 besøg/dag
- Compliance scans: 0 reelle
- Licenser udstedt: 0 (LS nøgle mangler)

## Budget: 35 kr brugt af 1000 (uændret)

## Næste iteration

- Overvej næste distributionskanal: npm publish? pip publish?
- Eller forbedr SEO/content på sitet for at drive download-trafik til desktop app'en