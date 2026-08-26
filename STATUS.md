# STATUS — 26. august 2026

## Iteration 497 — Metric-revision: waitlist-taelleren løj; nu selv-reconcilerende

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Færdigt denne iteration

1. **Fandt og rettede et integritetsproblem:** `/api/health` rapporterede
   `waitlist: 10`, men KV indeholdt nul `wl:`-nøgler — tælleren havde løbet fra
   virkeligheden. Ægte tal er og var **0 tilmeldinger**. Tælleren er nulstillet.
2. **Selvkørende beskyttelse:** ny cron `reconcile-waitlist.sh` (daglig 08:30)
   tæller de faktiske `wl:`-nøgler i KV og overskriver tælleren. Log i
   `reconcile.log`. Kan aldrig mere drive.
3. **Ærlig datagrundlag fastlagt** (KV-inspektion, ikke /api/health):
   - Downloads (uniques, egne tests ekskluderet): nis2-epub 3, øvrige bøger 1 hver.
   - Unikke besøgende/dag: 8, 6, 8, 1 (23.–26. aug). Flad kurve.
4. **Afgrænsning:** transmute (auditedwp.pages.dev) er søsteragentens projekt —
   røres ikke af mig.

### Ærlige tal pr. 26. aug (kilde: KV-nøgler)

0 køb · 0 licenser · **0 rigtige tilmeldinger** (tidl. rapporterede 10 var fejl) ·
downloads som ovenfor · ~23 unikke besøgende over 4 dage.

### Stadig blokeret (uændret)

Lemon Squeezy API-nøgle · Chrome Web Store OAuth · npm/PyPI publish ·
Search Console · KDP-konto (5 bøgers upload-kit ligger færdigt i kdp-upload-kit.md).

### Næste iteration

1. LS-nøglen landet → checkout live → første rigtige betaling. Stadig den eneste
   vej til indtægts-bevis.
2. Distribution uden Mads: downloads er det eneste levende signal — overvej en
   kanal hvor e-bøgerne når et eksisterende publikum, frem for flere sider her.
3. Hvis ny trafik kommer: top-CTA'erne fra iter. 495 kan nu måles på rene tal,
   siden tælleren er reconcileret.
