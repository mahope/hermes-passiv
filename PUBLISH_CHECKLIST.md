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

## 3. Lemon Squeezy (betaling) — Clean Copy Pro

**Automatiseret:** kør `node lemon-setup.js` med `LS_API_KEY` fra Bitwarden.
Scriptet opretter produkt + variant ($19/år), genererer checkout-linket og
printer de sidste manuelle trin (webhook-secret som Pages secret + webhook-URL
`https://hermes-passiv.pages.dev/api/lemon-webhook`). Indsæt derefter
checkout-linket med `node tools/set_checkout_url.js "<url>"` og deploy.

**Hele licensflowet er testet end-to-end lokalt** (iteration 289,
`node tools/test_license_flow.js`, 16/16 grønne): webhook-signaturverificering
(bad sig = 403, manglende secret = 503 så LS retry'er), nøgleudstedelse ved
`order_created`, idempotens pr. ordre (retries mintes ikke dobbelt),
activate/validate med device-binding, device-grænse (409), udløb og revoked.

**Kendt hul (kræver beslutning før go-live):** køberen modtager ikke selv sin
licensnøgle — nøglen mintes kun i KV, og webhook-svaret når ikke køberen. LS'
kvittering kan ikke indeholde den via API. Løsning skal bygges (fx lookup-side)
eller nøglen sendes manuelt i starten. Ikke blokerende for at tænde betalingen,
men skal besluttes inden første rigtige salg.

**✅ Levering lukket (iteration 290):** lookup-siden er bygget. Webhook'en gemmer
nu køberens email (hash'et) pr. ordre, og `POST /api/license/lookup` med
ordrenummer + email returnerer nøglen. Siden ligger på
`https://hermes-passiv.pages.dev/license-lookup` og er linket fra aktiveringen i
`/clean-copy-tool`. Testet lokalt (22/22 i `tools/test_license_flow.js`):
forkert/ukendt par → identisk 404, rate-limit 429. Under go-live: webhook-secret
sættes som Pages secret, checkout-link injectes med `set_checkout_url.js`.
Buyer's ordre-id står i LS-kvitteringen.

Efter go-live: testkøb med LS testkort → verificér at /api/license/activate
udsteder en nøgle → indsæt den i Clean Copy extension → Pro aktiveret.

## 4. Chrome Web Store

- `$5` registreringsgebyr (under 150 kr-grænsen — afholdes af mig når konto er muligt)
- Upload `site/eaa-scanner-extension.zip` (bygget og klar)

## 5. KDP (manuel af Mads)

Kit komplet: `kdp-upload-kit.md` — 5 bøger, covers, beskrivelser klar til copy-paste.
