# STATUS — Iteration 310: CI FIXED + Desktop v1.3.1 (6 platform builds)

## Resultat

**CI workflow virker.** Efter 7 fix-forsøg (node 22, permissions, package-lock, author,
repository, --publish never, gh release create syntax) bygger workflow'et nu automatisk
alle 3 platforme på tag push `eaa-scanner-desktop-v*`.

- v1.3.1: 7 assets (macOS ARM64/Intel DMG+ZIP, Linux AppImage+.deb, Windows NSIS) — **live**
- v1.3.2: kører nu — tilføjer Windows portable .exe (artifact naming fix)

## Bygget i denne iteration

1. **CI workflow fixet** — 7 commits, alle fejl rettet:
   - Node 20→22 (electron@44 kræver >=22.12)
   - Tag trigger (eaa-scanner-desktop-v*) tilføjet
   - package-lock.json regenereret (var ude af sync)
   - repository + author felt i package.json
   - permissions: contents: write
   - --publish never (forhindrer electron-builders auto-publish 403)
   - gh release create forenklet

2. **Downloads page opdateret** — Linux/Windows sektioner med v1.3.1 links, site deployet

3. **v1.3.2 tag** — pushet med Windows artifact naming fix (portable + NSIS får separate filnavne)

## CI status

- ✅ **v1.3.1 tag** — 7/7 assets bygget, alle downloads virker (302 redirect)
- ⏳ **v1.3.2 tag** — kører nu, tilføjer Windows portable .exe

## Næste iteration

- Når v1.3.2 CI er færdig: opdater downloads page med portable .exe link
- Hvis CI fortsat virker: overvej automatisk at bygge på hver ny tag
- Overvej at tilføje `npm publish` eller `pip publish` som næste distributionskanal

## Budget: 35 kr brugt af 1000 (uændret)