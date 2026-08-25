# STATUS — Iteration 294: Over-fold tool-CTA på 91 blogsider

## Blokering (uændret, sidste gang nævnt)

- LS API-nøgle: Bitwarden stadig unauthenticated (`bw status` tjekket igen i 294).
- Obsidian community-submit: hos Mads.

## Hvad der skete denne iteration

1. **Ny CTA-strategi:** blogsiderne (den trafik der faktisk kommer) havde ingen
   direkte tool-CTA over fold — kun footer-links. Byggede idempotent script
   `tools/add_hero_cta.py`: indsætter en kompakt CTA-stribe lige efter `</header>`
   ("Check any page for GDPR & cookie issues → Run the Free Scanner") på alle
   blogsider hvis hero ikke allerede linker til et tool.
2. **Kørt på begge sprog:** 58 EN + 33 DA-sider opdateret, 29 skipped (havde
   allerede tool-link eller intet header). Ny `.blog-tool-cta` CSS i style.css,
   responsiv (stakker på mobil). Klik spores automatisk af eksisterende
   cta-/scan-listener i trackscripterne.
3. **Verificeret:** `full_site_check.py` 204 urls / 0 problems. Deployet med
   `./deploy.sh`. Live-tjek: `/blog/gdpr-fines-2026` og `/da/blog/gdpr-boeder-2026`
   returnerer 200 og indeholder CTA'en; `/style.css` indeholder de nye regler.
   Commit pushet.

## Søgninger: 0/12 brugt (ingen usikre fakta at tjekke)

## Budget: 0 kr brugt denne iteration (35/1000 total)

## Næste iteration (295)

1. Hvis bw nu er logget ind: go-live-sekvensen (lemon-setup.js → checkout-url → deploy).
2. Lad klik-målingen samle data (cta-/scan-events fra de nye CTA'er). Tjek
   /api/track-aggregater næste iteration.
3. Genoptag IKKE indgangs-serien. Gentag IKKE blokerings-listen.
