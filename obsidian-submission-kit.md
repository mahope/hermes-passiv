# Obsidian community-submission — klar til 5 minutter

**24. august 2026:** Obsidian har lanceret "Obsidian Community" (community.obsidian.md)
med developer dashboard. GitHub PR-vejen **findes ikke længere** for nye plugins.
Submissions går gennem web-dashboardet med automatisk review på få minutter.

## Det eneste Mads skal gøre (ca. 5 minutter)

1. **Gå til https://community.obsidian.md/account/profile** og log ind med sin
   Obsidian-konto (eller opret én: `mads@mahope.dk` — kræver kun email + adgangskode).
2. **Forbind GitHub-kontoen** (mahope). Dashboardet spørger om GitHub-login for
   at verificere ejerskab af repositoriet.
3. **Vælg repo** `mahope/clean-copy-obsidian` og klik **Submit**.
4. Automatisk review kører. Består det (forventet: ja), er plugin'et i
   community-listen inden for 24 timer.

## Hvad der ligger klar

- **Repo:** https://github.com/mahope/clean-copy-obsidian
  - main.js, manifest.json, styles.css på root
  - v1.0.7 release med alle 3 assets som individuelle filer (Obsidian kræver dette)
  - 14 tests passerer (`node test.js`)
- **Manifest:** id `clean-copy-obsidian`, version `1.0.7`, authorUrl sat til
  https://github.com/mahope, isDesktopOnly false
- **Licens:** MIT
- **Pro:** licensing-endpoints findes på /api/license/activate og /api/license/validate
  (Cloudflare Worker + KV). Kræver Lemon Squeezy-nøgle for at gå live.

## Efter godkendelse

Plugin'et dukker op i Obsidians community-liste. Så skal landingssiden
(hermes-passiv.pages.dev/clean-copy) have Obsidian-sektionen ændret fra
"manual install" til "install from community plugins" — det klarer jeg selv.