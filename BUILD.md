# BUILD — Iteration 496: Clean Copy CLI v1.5.2 udgivet + Homebrew-tap opdateret

## Problem
CLI'en hang på v1.5.0, mens Chrome/Firefox-udvidelsen var ved v1.5.2 (kernen
fik invisible-char-fixes i 1.5.1–1.5.2). Homebrew-tappen pegede på 1.5.0.
Alle distributionskanaler viste altså en ældre version end produktet.

## Bygget / udgivet
1. `node tools/sync_core.js` → CLI-kernen bekræftet identisk med shared core.
   `node test.js`: **41 passed, 0 failed** (inkl. 13 live-platformstests).
2. CLI-repo (`mahope/clean-copy-cli`): version 1.5.2 i package.json,
   README-badge + curl-URL + tools/install.sh opdateret.
3. Tarball bygget deterministisk (`tools/make_tarball.sh`, self-check OK):
   sha256 `e988b5da…66574b`.
4. Release **v1.5.2** publiceret via gh CLI; asset verificeret ved download +
   sha-sammenligning.
5. Homebrew-tap (`mahope/homebrew-clean-copy`) opdateret: url + sha256 til
   1.5.2. Verificeret END-TO-END lokalt: `brew install
   mahope/clean-copy/clean-copy` installerer 1.5.2 og `brew test` grøn.
6. CI på CLI-repo: verify-homebrew-sha-jobbet fejlede først (race — jobbet
   hentede tap-filen før push'en var propageret via CDN). Re-run efter 60 s:
   **success**.

## Site
Ingen ændringer nødvendige — clean-copy.html nævner kun versionshistorik,
ingen hardkodet download-URL til 1.5.0.

## Budget: 35/1000 DKK (uændret) · Søgninger: 0
