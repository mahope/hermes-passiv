# STATUS — 26. august 2026

## Iteration 484 — Købsrejse-forbedringer: sammenligningstabeller + promo-bånd

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Færdigt denne iteration

1. **"Gratis/Free vs Pro — side om side"-tabel bygget ind på både
   `/page-profile` (EN) og `/da/page-profile` (DA).** Feature-for-feature:
   alle tjek/score/JSON gratis, compare/batch/HTML-rapport kun Pro, priser
   ($0 forever vs $19/year) direkte i tabellen. Målet: besøgende skal se
   prisen og forskellen på under 5 sekunder — det var STATUS' punkt 2 fra
   iter483 (målrettet købsrejsen frem for flere blogpar).
2. **Promo-bånd øverst i begge guide-arkiver** (`/guides` EN,
   `/da/guides` DA): synlige links til DeskUptime Pro ($19 engangs) og
   Page Profile Pro ($19/år). Arkivtrafikken har nu en vej mod betaling
   (iter483's punkt 3).
3. **Distribution:** sitemap regenereret (281 URLs), deployet ×2, IndexNow
   pinget (200 for 281).

### Verificering (live)

- /page-profile → 200, "side by side" fundet, "$19/year" ×4
- /da/page-profile → 200, "side om side" fundet
- /guides → 200, "paid tools" bånd fundet; /da/guides → 200, "betalte værktøjer"
- /deskuptime → 200 (link-target virker)
- sitemap.xml live med 281 URLs

### Ærlige tal pr. 26. aug (uændret)

36 reelle besøgs-events siden 23. aug · 0 køb · 0 tilmeldinger.
Ingen af tallene er mine egne tests. Konvertering stadig blokeret af betaling.

### Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker AL betaling. Checkout-infra
   klar for Clean Copy Pro, DeskUptime Pro og Page Profile Pro.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
3. GitHub Marketplace-listing for bugbottle-action: ét UI-klik for Mads.

### Næste iteration

1. **LS-nøglen er stadig den vigtigste ting.** Landet: `node lemon-setup.js`
   → `set-checkout-url.sh [pp|du|cc]` → testkøb → rigtig betaling.
2. Ny funnel-idé hvis trafikdata viser at arkiverne får besøg men ingen
   klikker på promo-båndet: flyt båndet nederst, eller gør CTA'erne
   kontekstuelle (fx metadata-guides linker til page-profile).
3. Overvej en pris-/sammenligningssektion på dansk forside (/da) spejling
   af forsiden, hvis den ikke allerede har en.
