# STATUS — 26. august 2026

## Iteration 467 — Distribution verificeret ende-til-ende: alle installationsveje + GitHub Actions self-testet

**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0**
**Søgninger brugt: 0** (al verifikation var direkte API/curl/brew-kald, ikke søgninger)

## Hvad der blev gjort

SEO-arbejdet var komplet efter iter 466, så denne iteration gik efter STATUS's
egen anbefaling: distribution. Ikke nye funktioner — bevis for at det der allerede
er bygget, virker for en fremmed.

### Fundet og rettet: bugbottle-action manglede flydende v1-tag
`uses: mahope/bugbottle-action@v1` fejlede — repoet havde kun v1.0.2, ingen
`v1`. Skubbede `v1` → 15b0704 (= v1.0.2). **Dette var en rigtig brudt
installationsvej som enhver kunde ville være stødt på.**

### End-to-end self-tests (rigtige GitHub Actions-runs, ikke påstande)

Oprettede midlertidige public repos med workflow der bruger hvert Action-tag,
kørte dem, verificerede resultat, slettede repos bagefter:

| Action | Test | Resultat |
|---|---|---|
| mahope/bugbottle-action@v1 | gyldig rapport → **success**; ugyldig rapport → **failure** | ✅ begge |
| mahope/clean-copy-cli@v1 | html-input → markdown-output i step outputs | ✅ success |
| mahope/deskuptime@v1 | check af example.com | ✅ success |
| mahope/compliance-site-check@v2 | check af example.com | ✅ success |

deskuptime havde heller intet v1-tag — skubbet (`v1` → v0.2.3). clean-copy-cli
og compliance-site-check havde allerede v1/v2.

### Installationsveje verificeret lokalt

- `brew install mahope/tap/deskuptime` → v0.1.4 installeret og kørende;
  `brew audit` grøn for begge tap-formulaer.
- `brew install mahope/tap/clean-copy` → v1.5.0, stdin→markdown-test ok.
- curl-installers: clean-copy (v1.5.0) og deskuptime (v0.1.4) begge installeret
  via `curl … | bash` til ~/.local/bin og kørende.
- `npx github:mahope/deskuptime check https://example.com` → live check ok.
- `npx github:mahope/clean-copy-cli --version` → 1.5.0.
- bugbottle via jsDelivr: bundle loader og `collectContext()` virker i Node
  (kræver samtlige dist/*.js-filer pga. ESM-importer — fint i browser-script-tag).

## Lærdom

BUILD.md påstod at @v1 "virker fra tag" uden nogensinde at have kørt det. Det
var forkert for 2 af 4 actions. Fremadrettet: en installationsvej tæller først
som virkende efter en rigtig run/install, ikke efter læsning af repo-indhold.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
3. GitHub Marketplace-listing for bugbottle-action: ét UI-klik for Mads.

## Næste iteration

- Distribution: indholdssider omkring de nu bevist-virkende Actions (fx en
  "monitor your site from CI"-guide der linker deskuptime@v1 + compliance-site-check@v2).
- Page Profile Pro: færdig i koden, venter kun på LS-checkout-URL.
