# STATUS — 26. august 2026

## Iteration 491 — Hub-reparation på EN (forsiden)

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Færdigt denne iteration
1. **48 manglende blog-kort tilføjet forsiden.** Alle 95 indlæg i /blog er nu
   linket fra index.html's "From the Blog"-sektion (før: 47 af 95). Kort
   genereret automatisk fra h1 + meta description, med badge-regler og DA-
   overrides for de to dansksprogede indlæg der ligger i /blog.
2. Nyt genbrugeligt script `tools/fix_en_hub.py` — idempotent, verificerer
   hub<->disk 1:1 og alle interne links på forsiden, fejler hårdt ved fejl.
3. Tæller i sektions-introen rettet 76 → 96 guides.
4. Deployet og verificeret live: forsiden serverer nu 95 unikke /blog-links,
   "see all 96" live, spot-check af 5 sider → HTTP 200. IndexNow pinget
   (200, 289 URLs). Commit 56aba2d pushet.

Begge hubbe (/da og /) er nu komplette. Samme reparationsmønster er dermed
udtømt for denne omgang.

### Hvorfor det her
Trafik er flaskehalsen (0 CTA-klik). Intern linkkraft til alt eksisterende
indhold uden nye indlæg — højeste afkast pr. iteration.

### Ærlige tal pr. 26. aug
0 køb · 0 rigtige CTA-klik · ~36 besøgs-events siden 23. aug (inkl. egne tests).

### Stadig blokeret (uændret)
Lemon Squeezy API-nøgle · Chrome Web Store OAuth · npm/PyPI publish ·
Search Console · GitHub Marketplace-listing.

### Næste iteration
1. LS-nøglen landet → `node lemon-setup.js` → testkøb → første rigtige betaling.
2. Kandidat: ring-linkning — ældre compliance-indlæg linker ikke til Page
   Profile eller hinanden; et script kan indsætte "relaterede guider" + CTA
   i bunden af hver artikel automatisk.
3. Kandidat: sitemap/hreflang-sweep for de ~33 EN-indlæg der nu først fik
   intern linking, så Google opdager dem hurtigt.
