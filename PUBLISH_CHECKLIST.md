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

## 3. Betaling — Stripe (live 24/9-2026)

Lemon Squeezy afviste kontoen; alt salg kører via Stripe-kontoen Mahope.dk.
Kontrakten (betalingslinks, product_keys, licens-API) står i
`business/planer/2026-09-24-stripe-kontrakt.md` i workspace-repoet.

- Køb sker via Stripe Payment Links direkte fra siderne (ingen nøgler i
  klienter). Efter betaling lander køberen på `https://mahope.tools/thanks`,
  som viser licensnøgle eller downloadlinks; samme indhold mailes fra
  orders@mahoje.dk.
- Workeren (`site/_worker.js`) håndterer `/api/stripe-webhook`,
  `/api/stripe/fulfillment`, `/api/download/<token>/<fil>` og
  `/api/license/{activate,validate,deactivate}`. Test:
  `node tests/stripe-worker.test.mjs`.
- Mistet nøgle: hjælpesiden `https://mahope.tools/license-lookup`.
- Donationer: `https://mahope.tools/support` og `.github/FUNDING.yml`.

## 4. Chrome Web Store

- `$5` registreringsgebyr (under 150 kr-grænsen — afholdes af mig når konto er muligt)
- Upload `site/eaa-scanner-extension.zip` (bygget og klar)

## 5. KDP (manuel af Mads)

Kit komplet: `kdp-upload-kit.md` — 5 bøger, covers, beskrivelser klar til copy-paste.
