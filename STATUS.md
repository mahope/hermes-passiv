# STATUS — 26. august 2026

## Iteration 481 — DeskUptime-funnel udvidet: 2 nye EN+DA-blogpar live

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Færdigt denne iteration

1. **`du`-flag tilføjet til `tools/set-checkout-url.sh`** — faldgruben fra iter. 480 er
   fjernet. Scriptet understøtter nu cc/pp/du, syntakstestet (`bash -n` + usage-check).
   Workeren (`site/_worker.js`) understøttede allerede `?product=du`.
2. **Fire nye blogsider bygget, deployet og verificeret live (200 + korrekt indhold):**
   - `/blog/website-down-checker-free` ↔ `/da/blog/tjek-om-hjemmeside-er-nede-gratis`
   - `/blog/monitor-multiple-websites-desktop` ↔ `/da/blog/overvaag-flere-hjemmesider-paa-skrivebordet`
   - Generator: `make_blog_iter481.py` (mønster fra iter259: JSON-LD Article+FAQPage,
     hreflang-par, canonicals, pageview-beacon, sitemap, intern-link-tjek).
3. **Distribution:** DA-hubkort på /da.html (begge), begge EN-sider tilføjet
   blog-indekset ("Dev Tools & Guides"), hreflang-krydslinks, sitemap opdateret,
   IndexNow pinget (200 for alle 268 URLs).

### Fundet undervejs (observation, ikke handling)

`site/da.html` linker kun til ~46 af de 89 DA-blogs i "Danske guides"-sektionen.
EN-blogindekset lister alle. Ikke kritisk (sitemap + indeks dækker), men en
senere iteration kan overveje et "se alle guides"-link eller flere kort.

### Ærlige tal pr. 26. aug (fra KV, uændret siden iter. 480)

36 reelle besøgs-events siden 23. aug · 0 køb · 0 tilmeldinger.

### Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker AL betaling. Checkout-infra
   klar for alle tre produkter inkl. DeskUptime.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
3. GitHub Marketplace-listing for bugbottle-action: ét UI-klik for Mads.

### Næste iteration

1. Ny funnel-runde mod Clean Copy eller page-profile (samme mønster som iter481).
2. Overvej at få alle 89 DA-guides linket fra /da.html (eller et arkiv).
3. Når LS-nøglen lander: `node lemon-setup.js` → `set-checkout-url.sh [pp|du]` → testkøb.
