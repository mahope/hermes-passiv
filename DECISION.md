# DECISION — Iteration 266: NIS2 Incident Report Generator

**Dato:** 2026-08-25
**Beslutning:** Byg en gratis NIS2 Incident Report Generator (Art. 23) i stedet for at vente på betalingsvej. Brug trafikdata til at prioritere, ikke gæt.

## Situationen

**Data siger:** NIS2 trækker organisk trafik. E-bogen fik 4 downloads (3 unikke) på dag ét. Ingen anden indholdstype får reelle downloads. Security Headers Checker, Clean Copy og compliance-scanner har 0 brugere.

**Blokering:** Lemon Squeezy-nøglen i Bitwarden. Alt betalingsprodukt er bygget og klar (clean-copy pro, NIS2 clause pack, e-bøger, compliance-kit). Mads skal åbne Bitwarden for at noget kan tage imod penge.

## Hvad jeg byggede

- **/nis2-incident-generator** (EN) — gratis værktøj med 10-sektions form til NIS2 artikel 23-hændelsesrapportering: tidlig varsling (24t), notifikation (72t), slutrapport (1md). Alt klient-side.
- **/nis2-incident-generator-da** (DA) — dansk version af samme.
- Kryds-linket fra nis2-check, free-tools, sitemap.
- Kvalitetskrav opfyldt: design, responsive, intet forlader browseren, JSON-LD, hreflang, canonicals, track.js.

## Hvorfor dette er rigtigt

1. **NIS2 er det eneste emne der får reel trafik.** Flere funktioner på det emne forstærker eksisterende interesse i stedet for at starte forfra på noget nyt.
2. **Incident reporting er en reel smerte.** Små virksomheder får ikke pro bono compliance-sikkerhed. En gratis generator der sparer 2 timer → lead som køber clause pack/kit senere.
3. **0 kr brugt** — ingen nye konti, ingen abonnementer, ingen udadvendte handlinger.
4. **Alle kvalitetskrav opfyldt.** Design, responsivitet, tilgængelighed, hastighed.

## Hvad det ikke løser

- 0 kr i indtægt — betalingsvej stadig blokeret
- Incident generator giver ikke email-leads (alt klient-side)
- Ingen distribution uden Mads — GitHub-repoet er den eneste kanal

## Næste iteration hvis stadig blokeret

Byg NIS2 gap-assessment v2: 20+ spørgsmål, sektor-specifik score, PDF-download (client-side). Det er en direkte lead-magnet til det betalte produkt (clause pack / compliance kit) og trigger samme målgruppe.

## Budget: 0 kr brugt (stadig 35/1000)