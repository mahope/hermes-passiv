# PUBLISH_CHECKLIST — klar til at køre samme minut nøglerne ligger i Bitwarden

Alle artefakter er bygget OG testet lokalt (28. august 2026, iteration 85).
Ingenting her kræver forberedelse udover nøglerne.

## 1. npm — @mahope/eaa-scanner 1.2.0

Pakke: `scanner/npm/eaa-scanner/` (test.js: SELF-TEST OK, node --check OK)

```bash
cd scanner/npm/eaa-scanner
npm login                      # Mads' npm-konto (otp)
npm publish --access public
```

Efter: `npm view @mahope/eaa-scanner` → verificer version 1.2.0 live.
Opdatér derefter `/downloads` og README fra tarball-link til `npm install @mahope/eaa-scanner`.

## 2. PyPI — eaa-scanner 1.2.0

Pakke: `scanner/packaging/dist/eaa_scanner-1.2.0*` (twine check: PASSED begge;
installeret lokalt, `eaa-scan` CLI verificeret på defekt HTML → score/grade/exit=1 korrekt)

```bash
python3 -m twine upload scanner/packaging/dist/eaa_scanner-1.2.0*
```

Kræver PyPI API-token i `~/.pypirc` (Mads opretter konto + token).
Efter: `pip install eaa-scanner && eaa-scan <fil>` på en fransk maskine.

## 3. Lemon Squeezy (betaling)

- Opret produkt "EAA Scanner Pro" $29/år + ComplianceDocs-bundle $29.99
- Sæt licens-API-nøgle ind i desktop-appens validerings-endpoint (kode klar i `desktop/`)
- Testkøb med testkort før go-live

## 4. Chrome Web Store

- `$5` registreringsgebyr (under 150 kr-grænsen — afholdes af mig når konto er muligt)
- Upload `site/eaa-scanner-extension.zip` (bygget og klar)

## 5. KDP (manuel af Mads)

Kit komplet: `kdp-upload-kit.md` — 5 bøger, covers, beskrivelser klar til copy-paste.
