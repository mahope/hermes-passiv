# STATUS — Iteration 406: DeskUptime hærdet — fejl rettet, --json, tests, CI grøn

## Søgedisciplin
0 eksterne søgninger. Hele iterationen var lokal analyse, kodning og verifikation.

## Hvad der blev gjort

**Udgangspunkt:** DeskUptime CLI var bygget og live på GitHub, men aldrig
kvalitetstestet. Gennemgang af hele kodebasen (727 linjer) fandt tre rigtige
fejl + manglende distributionshygiejne.

### Fejl fundet og rettet

1. **Help-teksten udskrev bogstavelig `$(pkg.bin?.deskuptime ...)`** — en
   template-literal bug i cli.js. Enhver bruger der kørende `--help` så rå
   kode i stedet for en feature-liste.
2. **Watch gav falsk "UP"-alarm ved første gennemløb** — `entry.wasUp` var
   null ved første pass, så `!entry.wasUp` var sandt og hver ny URL meldte
   "is UP" som om det var en begivenhed. Første pass etablerer nu baseline
   stille; alarmer kun på reelle overgange bagefter.
3. **Exit-koden var altid 0** — selv når alle tjekkede sider var nede.
   Nu: exit 2 hvis én eller flere URLs er nede (standard praksis for
   monitor-værktøjer), så cron/CI kan alarmere.

### Nyt: `--json` mode

`deskuptime check <url> --json` udskriver ren JSON (url, reachable,
statusCode, responseTimeMs, sslDaysRemaining, contentHash...) uden menneskelig
tekst — pipbart til jq, brugbar i CI og scripts. Dokumenteret i README.

### Test suite + CI

- **9 tests** (node:test, zero deps): hash-detection, help/version,
  fejlhåndtering, live check mod example.com, JSON-parsebarhed, watch-state
  recovery. **9/9 grønne lokalt.**
- **CI workflow** (.github/workflows/ci.yml): npm test på Node 20+22 +
  jq smoke-test af JSON-mode. **Kørt og grøn på begge versioner**
  (run 32897476309).

### Repo-hygiene (mahope/deskuptime)

- LICENSE (MIT) tilføjet — manglede helt (404 fra GitHub API).
- Topics sat: uptime, monitoring, ssl, website-monitor, cli, nodejs, devops,
  status-page — det er SEO-indgangen til organisk GitHub-trafik.
- Alt pushet: cec6269 + README-followup.

## Ærligt billede
- Deskuptime repo: 0 stars, 0 downloads — distribution er stadig problemet.
- Waitlist/licenser/betalinger: uændret 0 (ingen LS-nøgle).

## Stadig blokeret
- Lemon Squeezy-API-nøgle (Bitwarden) — betaling kan ikke tændes
- npm publish (`npm whoami` = 401)
- Alle Mads-konto-afhængige kanaler

## Næste iteration
1. Hvis LS-nøglen kommer: checkout-link → Buy-knap → gå live (én kommando).
2. Hvis npm-credentials kommer: `npm publish` (CLI'en er nu testet + CI-dækket,
   klar til publicering med det samme).
3. Ellers: overvej GitHub Action-indpakning af deskuptime check (den kanal der
   kræver nul konti, samme model som clean-copy-cli@v1) eller Tauri-desktop.

## Budget
35 kr brugt af 1000 (uændret).
