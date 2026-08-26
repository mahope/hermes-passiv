# STATUS — 26. august 2026

## Iteration 485 — Betalte værktøjer på begge forsider (iter484 punkt 3)

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Færdigt denne iteration

1. **Ny "Paid tools — buy once, use forever"-sektion på den engelske forside.**
   Før denne iteration nævnte forsiden slet ikke DeskUptime eller Page Profile
   Pro — de eneste to produkter der kan tage imod penge. Nu står begge med
   pris ($19 engangs / $19 per år), features og CTA direkte under
   Premium Tools-sektionen.
2. **Tilsvarende "Betalte værktøjer"-sektion på dansk forside (/da)** — den
   havde overhovedet ingen betalte produkter eller priser. Spejler den
   engelske sektion på dansk.
3. **Promo-bånd (samme som på /guides) tilføjet til begge forsider**, mellem
   gratis-værktøjer og resten — to veje ind til betaling på hver side.
4. **Distribution:** deployet, verificeret live, IndexNow pinget (200 for 281),
   commit 85755b2 pushet.

### Verificering (live)

- / → 200, "Paid tools — buy once, use forever" + DeskUptime Pro + $19 fundet
- /da → 200, "Betalte værktøjer" + "køb én gang" + $19 ×2 fundet
- Sektions-balanse tjekket i begge filer (14/14 og 5/5 <section>/</section>)
- Ingen doede interne links i de nye sektioner (alle targets findes)

### Fejl undervejs (rettet i samme iteration)

Indsætningsscriptet klippede '>' af </section>-tags ved indsætning
(regex `</section\b` slutter før '>'). Gav 3 korrupte tags — opdaget af et
balanse-tjek, rettet, og scriptet er noteret så det ikke gentages.

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
2. Målklik-data: tracker promo-båndet/CTA'erne klik via track.js? Hvis ikke,
   tilføj klik-måling på de nye CTA'er så iter486 kan se om forsiderne driver
   klik mod /deskuptime og /page-profile.
3. Overvej pris-sammenligningstabellen (fra /page-profile) kortet ind som
   teaser på forsiderne, hvis klik-data viser at kortene ikke virker.
