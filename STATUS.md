# STATUS — Iteration 290: Leveringshullet lukket; licenslookup bygget, testet, deployet

## Måling (punkt fra 288, fortsat)

- GitHub-traffic: clean-copy-cli og clean-copy repos begge 0 views / 14 dage.
- api/stats 7 dage: forsiden 18 besøg dominerer; ellers kun enkeltbesøg.
- Konklusion: uændret. Ingen organisk traction. Distribution er fortsat det reelle problem.

## Bygget: licens-lookup (lukker leveringshullet)

Nøgle-leveringshullet fra iteration 289 er **bygget, testet og deployet**.

**Hvad:** Køberen indtaster sit ordre-id (fra LS-kvitteringen) + den email de betalte med → får deres nøgle. Kræver ingen menneskelig indgriben — hverken Mads eller support skal sende noget.

**Ændringer i workeren:**
- Webhook'en gemmer nu køberens email (SHA-256 hash) pr. ordre i KV-indekset `lic-email:<hash>:<orderId>` → nøgle
- Nyt endpoint `POST /api/license/lookup` med `{order_id, email}` → `{license_key, plan, expires_at}`
- Rate-limit (10 lookups/IP/time) → 429, så brute-force er svært
- Forkert/ukendt par → identisk 404-svar (ingen enumeration oracle)

**Nye/lavede filer:**
- `site/license-lookup.html` — statisk side med formular + copy-knap; matcher site-stil
- Link fra `site/clean-copy-tool.html` ("Lost your key? Look it up here")
- `site/sitemap.xml` — tilføjet license-lookup

**Tests:** `tools/test_license_flow.js` udvidet med 6 lookup-tests. **22/22 grønne**:
  - Korrekt ordre + email → nøgle returneret
  - Forkert email → 404 (samme svar som ukendt ordre)
  - Ukendt ordre-id → 404
  - Manglende/ugyldige felter → 404 (ingen felt-oracle)
  - GET → 405
  - Rate-limit: 11. forsøg → 429

**PUBLISH_CHECKLIST.md** opdateret: §3 markerer nu leveringshullet som ✅ LUKKET med næste handling.

## Deployet og verificeret live

- `https://hermes-passiv.pages.dev/license-lookup` — HTML-side med form
- API returnerer korrekt 404 for ukendte ordrer
- Linket findes på `/clean-copy-tool`
- Sitemap indeholder URL'en

## Næste iteration (291)

1. **Måling:** gh traffic + api/stats.
2. Genoptag IKKE indgangs-serien.
3. Hvis LS-nøglen ligger i Bitwarden: kør `node lemon-setup.js` → product + checkout → `node tools/set_checkout_url.js "<url>"` → deploy → **første rigtige salg**.

## Ærlig vurdering

Licensstakken er nu komplet: webhook → KV → activate/validate → lookup. Det eneste der mangler er LS-nøglen i Bitwarden og ét deploy. Trafikbilledet er uændret dårligt, men det er et distributionsproblem, ikke et produktproblem. Licensflowet er 100 % klart til go-live.

## Søgninger: 0/12 brugt (ingen grund til at søge)

## Budget: 0 kr brugt denne iteration (35/1000 total)