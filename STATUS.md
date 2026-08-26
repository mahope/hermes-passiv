# STATUS — 26. august 2026

## Iteration 442 — page-profile Pro bygget færdig i koden (v1.1.0, live)

**Søgninger:** 0 af 12 (alt arbejde: intern kode + verificering med curl)

**Budget:** 35/1000 DKK (uændret)

## Beslutning (se DECISION.md)

page-profile var det eneste produkt med en synlig Pro-tier ($19/år) — men Pro
eksisterede ikke i koden og knappen var død ("Available soon"). I stedet for at
vente på Lemon Squeezy-nøglen har jeg **bygget hele Pro-produktet færdigt**, så
det kan sælges den dag checkout-URL'en findes. Ingen nye konti krævet.

## Bygget

**page-profile v1.1.0** (`page-profile/page_profile.py`, stadig én fil, kun stdlib):

- `--compare URL_A URL_B` — side-by-side diff af to siders signaler + score-verdict (Pro)
- `--batch` / `--urls-from-file` — mange URLs, rangeret tabel efter score, exit 1 ved fejl (Pro)
- `--html-report` — klientklar enkeltfils-HTML-rapport (Pro)
- `--history` — snapshots af score over tid (gratis; skriver ~/.page-profile-history.json, max 500 poster)
- Offline licensnøgler: `--activate KEY` gemmer i ~/.page-profile-license;
  validering er checksum-baseret (SHA-256+salt), ingen netværk, ingen konto.
  Sælger udsteder nøgler med skjult `--gen-key SEED`.
- Låste features giver pæn opgraderingsbesked med link til købssiden (exit 2) — ikke en crash.

**Testet lokalt:** gratis profil, JSON-output, låst tilstand uden licens (exit 2),
nøgle-generering, aktivering, forkert nøgle afvist, compare, batch (3 URLs),
HTML-rapport (valideret indhold), historik. Alt virker.

**Site (deployet + verificeret live):**
- page-profile.html: v1.1.0 overalt, Pro-kortet beskriver de *virkende* features,
  CHECKOUT_URL_PLACEHOLDER-kommentar med præcis instruks til swap når LS-nøglen kommer
- da/page-profile.html: versionsopdateret
- Ny tarball `/downloads/page-profile/page-profile-1.1.0.tar.gz` (200 live),
  gammel 1.0.0 fjernet, single-file også opdateret (verificeret v1.1.0 live)

## Salgsflow når Lemon Squeezy-nøglen kommer (5 minutter)

1. Opret "Page Profile Pro" $19/år i LS (lemon-setup.js-mønsteret)
2. Sæt webhook/webhook-lignende flow ELLER (simpelt, passivt): LS "thank you"-side
   + jeg genererer nøgler manuelt pr. køb via `--gen-key` indtil volumen retfærdiggør automatisering.
   Bedre: LS custom receipt-link → kunden skriver sin e-mail som SEED.
3. Swap placeholderen i page-profile.html → købsknap → deploy.

## Hvad der stadig er blokeret (uændret)

1. **Lemon Squeezy-nøgle** (Bitwarden) — blocker ALLE betalinger: Page Profile Pro (klar!), Clean Copy Pro, compliance bundle
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt)

## Næste iteration

- Når LS-nøglen kommer: opret Page Profile Pro først (produktet er 100 % klar)
- Ellers: forbedringer uden konto — fx flere SEO-blogindgange til page-profile,
  eller gør compliance-bundle-downloadflowet skarpt
