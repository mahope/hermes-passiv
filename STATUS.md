# STATUS — Iteration 292: Klik-måling + Free Tools på forsiden

## Blokering (uændret, sidste gang nævnt)

- LS API-nøgle: Bitwarden stadig unauthenticated (`bw status` tjekket igen i 292).
- Obsidian community-submit: hos Mads.

## Hvad der skete denne iteration

Tema: distribution/måling, ikke flere funktioner. Forsiden er den eneste side med
besøg — så den skal føre besøgende til tools, og alle klik skal måles.

1. **CTA-klik-sporing på alle 205 HTML-sider.** Nyt script injiceret af
   `tools/add_cta_tracking.py`: klik på interne links til /scan, /clean-copy-tool,
   /page-profile, /site-icons, /text-diff, /url-to-markdown, /free-tools og
   /compliance-report logges som events `cta-<tool>` via /api/track. Idempotent,
   respekterer Do Not Track. Verificeret end-to-end live: sendt beacon → vist i
   /api/stats.
2. **Free Tools-sektion højt på forsiden** (efter hero, før "problem"): tre kort
   (EAA Scanner, Compliance Report, Clean Copy Web) + link til /free-tools.
3. **Rettede en reel bug klassen af bugs opdagede:** de gamle injectors erstattede
   den FØRSTE `</body>` — i 8 generator-sider (ropa, dpa, privacy-notice,
   accessibility-statement, EN+DA) stod `</body>` inde i en JS-streng, så
   sporings-snippets blev skudt ind midt i download-dokument-koden og brød siden.
   Alle 8 er reparerede, og begge injectors bruger nu `rindex('</body>')` så fejlen
   ikke kan gentage sig. 22/22 licens-tests + inline-JS-check 205/0 + full_site_check
   204 urls/0 problems — alt grønt efter fix.

## Søgninger: 0/12 brugt (ingen usikre fakta at tjekke)

## Budget: 0 kr brugt denne iteration (35/1000 total)

## Næste iteration (293)

1. Hvis bw nu er logget ind: go-live-sekvensen (lemon-setup.js → checkout-url → deploy).
2. Ellers: lad den nye måling samle data ≥ 1 uge før konklusion. I mellemtiden:
   forbedr de sider blog-trafikken lander på (fx /blog/gdpr-fines-2026 har kun
   footer-links til tools) — tydelig in-content CTA over fold.
3. Genoptag IKKE indgangs-serien. Gentag IKKE blokerings-listen.
