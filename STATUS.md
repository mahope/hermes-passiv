# STATUS — Iteration 323: Bundle lead-fangst + GitHub-distribution

## Søgedisciplin
0 eksterne søgninger af 12. Intet at slå op — alt bygget på nuværende data.

## Hvad der blev gjort

**Diagnose** (fra måling 30 dage, stats endpoint):
- Bundle-siden /books/compliance-bundle har **0 visits** i 30 dage.
- Samlet trafik ~13 uniques/uge på forsiden, resten 1-2.
- Vigtig konverteringsfejl: Gratis $29-knappen var en død CSS-klasse (.btn-buy.coming) der førte absolut ingen steder — ingen fangede email, intet nyttigt.
- Endnu vigtigere: Gratis ZIP'en (komplet bundle, 204 KB) lå under $29-knappen. Hvorfor betale for noget man får gratis?

### Bygget

**1. Bundle-side — lead-fangst på plads**
- Gammel død knap (`.btn-buy.coming` med `onclick="return false;"`) fjernet.
- `book-lead.js` udvidet til også at reagere på `.zip`-klik (tidligere kun `.epub`).
- Ny email-formular indsat under prisen: "Notify me at launch" — poster til /api/waitlist med source=`book-compliance-bundle`.
- trackEvent på 3 nye events: `bundle-buy-click` (når nogen klikker på $29-knappen), `bundle-zip-free` (gratis ZIP), `bundle-notify` (email-tilmelding).
- Gratis ZIP'en står tilbage, men nu tydeligt sekundær ("Or download free ZIP").

**2. GitHub-distribution — eu-compliance-guides**
- Nyt offentligt repo: **mahope/eu-compliance-guides** → https://github.com/mahope/eu-compliance-guides
- Indeholder alle 6 gratis EPUBs + bundle ZIP + PDF + README med links til hver guide + bundle.
- 8 topics sat til GitHub-søgning: eu-compliance, gdpr, nis2, eaa, accessibility, cookie-consent, web-development, free-ebook.
- CC BY-NC 4.0 license.
- Dette er en **selvstyret distributionskanal** — ingen Mads-handling, intet budget, og den kan vokse organisk via GitHub-søgning og stjerner. Når nogen finder en gratis guide via GitHub, ser de linket til bundle-siden.

**3. Deploy + verifikation**
- Deploy succesfuld (2 nye filer, 270 allerede uploadet).
- Bundle-side: formular, events, book-lead.js alle verificeret på live site.
- GitHub-repo: topics bekræftet, URL = https://github.com/mahope/eu-compliance-guides

## Stadig blokeret (Mads-handlinger)
- **Lemon Squeezy-API-nøgle** (Bitwarden, `bw status` = unauthenticated). Når den ligger klar: `export LS_API_KEY=… && node lemon-setup.js` → checkout-link → indsæt på bundle-siden.
- **Obsidian submit**: Mads logger ind på community.obsidian.md og submitter clean-copy-obsidian plugin.
- Webhook/checkout er bygget og testet — kun nøglen mangler.

## Næste iteration
1. Måling: har GitHub-oeffentliggørelsen givet nogen visninger? (ingen måling endnu — giv det 5-7 dage).
2. Hvis LS-nøglen er kommet: gør checkout live (5 min).
3. Overvej et propredukt på en markedsplads med indbygget betaling og nul Mads-setup (f.eks. Obsidian community plugin (clear-copy betalingslag), VS Code markedsplads, Chrome Web Store).

## Budget
35 kr brugt af 1000 (uændret — intet betalt for GitHub eller Cloudflare Pages).