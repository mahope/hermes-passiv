# BUILD — Iteration 253: lemon-setup.js + projekt parkeret

## Hvad blev bygget

### 1. `lemon-setup.js`
Script der opretter Clean Copy Pro på Lemon Squeezy via deres REST API, når LS-nøglen kommer fra Bitwarden:
- Finder butik på LS-kontoen
- Opretter produkt ("Clean Copy Pro") + variant ("Yearly - $19")
- Genererer checkout-link
- Udskriver instruktioner til at sætte LS_WEBHOOK_SECRET

Kør: `export LS_API_KEY="..." && node lemon-setup.js`

Ingen Pages-secrets eller deploy nødvendigt — det er et standalone script.

### 2. DECISION.md opdateret
Ærlig beskrivelse af situationen: alt bygget, alt klar, mangler kun Mads' konti.

### 3. STATUS.md opdateret
Samme ærlige status. Blokeringen rapporteret som én linje.

## Budget: 0 kr brugt (stadig 35/1000)
