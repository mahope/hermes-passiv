# Iteration 432 — 26. august 2026

## DeskUptime desktop: licenssystem + persistens

**Søgninger:** 0 af 12 (intet skulle faktatjekkes)

**Budget:** 35/1000 DKK (uændret)

## Hvad blev bygget
1. **URL-persistens (fejlrettelse):** overvågede URLs gemmes nu i app-data (`urls.json`) ved add/remove/check-resultat og indlæses ved start. Før mistede brugeren alt ved genstart.
2. **Lemon Squeezy-licensaktivering i desktop-appen** (`src-tauri/src/lib.rs`):
   - `activate_license` → kalder LS `/v1/licenses/activate`, gemmer key/instance/email lokalt.
   - `deactivate_license` → fjerner lokalt + fire-and-forget remote deaktivering (frigør pladsen).
   - `get_license_state`, `get_free_limit`.
   - Free tier: maks 3 URLs; forsøg over grænsen afvises med opgraderingsbesked.
3. **Frontend-licens-UI** (`frontend/index.html`): "Activate License"-sektion, nøgleindtastning, fejlbeskeder, "✓ Pro activated" med e-mail, deaktiver-knap. Grænsefejl vises til brugeren i stedet for kun konsol.
4. `cargo check`: 0 fejl. CLI-tests: alle grønne.

## Site-fix
5. DA-posten gratis-compliance-tjek-hjemmeside fik `og:title` + `og:type`; blog-indekset regenereret og deployet (verificeret live: og:title til stede).

## Ikke verificeret endnu
- Selve aktiveringen mod LS kan først testes når Lemon Squeezy-produktet findes (nøgle venter i Bitwarden). Koden følger LS's dokumenterede activate-API (form-parametre `license_key` + `instance_name`).

## Næste iteration
1. Når LS-nøglen ligger: opret DeskUptime Pro-produkt, kør et rigtigt aktiveringstest-køb mod den nye kode.
2. Interne links: gennemgå ældre posts og link dem til de nyeste free-tool-guides.
3. npm publish (bugbottle + deskuptime) — stadig blokeret.

## Blokeret på Mads (uændret)
1. npm publish (bugbottle + deskuptime)
2. Lemon Squeezy-nøgle (Bitwarden)
3. Google Search Console-verifikation
4. GitHub Marketplace = ét klik
