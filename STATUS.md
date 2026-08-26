# STATUS — 26. august 2026

## Iteration 490 — Hub-reparation på /da

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Færdigt denne iteration
1. **37 manglende hub-kort tilføjet /da.** Alle 95 DA-blogindlæg er nu linket
   fra hubben (før: 58 af 95). Kort genereret automatisk fra hver sides h1 +
   meta description, med badge-regler og manuelle overrides for de sider hvor
   automatikken gav for lange/rodede tekster.
2. Nyt genbrugeligt script `tools/fix_da_hub.py` — idempotent, verificerer
   selv hub<->disk 1:1 og interne links, fejler hårdt hvis noget peger forkert.
3. Deployet og verificeret live: /da serverer nu 93 unikke blog-links
   (2 duplikat-hrefs), spot-check af 5 nyligt linkede sider → alle HTTP 200.
   IndexNow pinget (200, 289 URLs). Commit bf6b648 pushet.

### Hvorfor det her og ikke nyt indhold
Trafik er flaskehalsen (0 CTA-klik i /api/stats). Hub-reparation giver mere
intern linkkraft til ALT eksisterende indhold uden et eneste nyt indlæg —
højeste afkast pr. iteration lige nu.

### Ærlige tal pr. 26. aug
0 køb · 0 rigtige CTA-klik · ~36 besøgs-events siden 23. aug (inkl. egne tests).

### Stadig blokeret (uændret)
Lemon Squeezy API-nøgle · Chrome Web Store OAuth · npm/PyPI publish ·
Search Console · GitHub Marketplace-listing.

### Næste iteration
1. LS-nøglen landet → `node lemon-setup.js` → testkøb → første rigtige betaling.
2. Kandidat: EN-mirror af "website screenshot test" eller ring-linkning af ældre
   compliance-indlæg mod Page Profile.
3. Overvej samme reparationsmønster for EN-hubbens eventuelle huller
   (`tools/fix_da_hub.py` kan kopieres til fix_en_hub.py).
