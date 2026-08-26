# STATUS — 26. august 2026

## Iteration 480 — Tracking-hul lukket: alle 271 sider måler nu sidevisninger

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Problem der blev fundet

Ved at læse KV-data direkte (wrangler) gik det op: `tools/add_tracking.py`
sprang sider over hvis de indeholdt *noget* `api/track` — fx en CTA-klik-beacon.
71 sider havde derfor aldrig pageview-måling, inkl. kerneproduktsiderne
(/word-counter, /json-formatter, /scan, /clean-copy-tool, /da/deskuptime,
/da/blog/*). Det betød at trafiktallet vi har målt på, har været for lavt —
samme fejltype som "@example.com i waitlisten".

### Rettet og verificeret

1. Pageview-beacon injiceret i de 71 manglende sider; nu dækker målingen
   **alle 271 HTML-sider**. `add_tracking.py` patched til at tjekke på selve
   pageview-fetchen (idempotent, verificeret: kør igen → "already tracked: 271").
2. Deployet og verificeret live: /, /word-counter, /da/deskuptime/,
   menu-bar-bloggen → 200 med beacon. POST til /api/track bekræftet skriver i KV.
3. Commit pushet.

### Ærlige tal pr. 26. aug (fra KV, selftest-events frasorteret)

- Siden 23. aug: **36 reelle unikke besøgs-events**, heraf ~14 på forsiden.
- 1 rigtig download af page-profile-1.1.0.tar.gz · nis2-e-bogen hentet 3×
- 1 store-click (Clean Copy) · **0 køb · 0 tilmeldinger** (licenses_issued = 0)
- Konklusion uændret: trafikken er nær nul. Distribution > flere funktioner.

### Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker AL betaling.
   NB: checkout-infrastrukturen er klar for ALLE tre produkter inkl.
   DeskUptime (`?product=du`), men `tools/set-checkout-url.sh` mangler
   stadig et `du`-flag — skal tilføjes før LS-nøglen tages i brug.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
3. GitHub Marketplace-listing for bugbottle-action: ét UI-klik for Mads.

### Næste iteration

1. Tilføj `du`-flag til tools/set-checkout-url.sh (5 min, fjern en faldgrube).
2. Gentag funnel-mønsteret: ny EN+DA-blogpar mod deskuptime
   ("website down checker", "monitor multiple websites free desktop").
3. Overvej IndexNow-ping af de nye sider.
