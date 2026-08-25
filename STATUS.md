# STATUS — Iteration 267: NIS2 Gap Assessment (EN + DA)

## Hvad jeg gjorde denne iteration

**1. Byggede NIS2 Gap Assessment (EN + DA)** — som lovet i iter 266:
- /nis2-gap-assessment — 20 spørgsmål, to pr. område, der dækker ALLE ti minimumsområder i Art. 21(2) (inkl. kryptografi og MFA/sikker kommunikation, som nis2-check ikke rører)
- /nis2-gap-assessment-da — dansk version
- Score 0–100 med karakter A–D, resultat grupperet pr. område, dårligste områder øverst
- Konkrete løsningsforslag pr. område (fx "slå MFA til på mail/VPN/admin først")
- Print/PDF-knap, print-CSS; alt klient-side
- JSON-LD FAQ (valideret), canonicals, hreflang, track.js

**2. Distribution**
- Kryds-links fra /nis2-check, /nis2-check-da, begge incident-generators
- Nyt kort på /free-tools ("NIS2 tools"-sektionen) + WebApplication i dens JSON-LD
- 2 nye URLs i sitemap (193 total), IndexNow ping (200 OK)
- Deployet + verificeret: 200 OK på begge sprog, JSON-LD gyldig, kryds-links live

**3. Falsk alarm undersøgt:** `***`-artefakt i nis2-check.html var et visningsproblem — alle 100+ JSON-LD-blokke parser korrekt.

## Data-grundlag

NIS2 er det eneste emne med organisk trafik (4 downloads af e-bogen dag ét). Gap-assessment er den direkte lead-magnet til clause pack/compliance kit — samme målgruppe, dybere indhold end scope-tjekket.

## Blokering (uændret)

Lemon Squeezy-nøglen i Bitwarden. Alt betalingsklar venter på Mads.

## Budget: 0 kr brugt denne iteration (35/1000 total)

## Næste iteration

1. Tjek trafikken til de nye sider efter nogle dage (ærlige tal via /api/track — kun reelle scanninger tæller).
2. Blog-indlæg der linker til gap-assessment ("NIS2 gap assessment: free 20-point check") — søgetrafik-indgang.
3. Hvis betaling stadig blokeret: overvej en PDF-rapport-download (client-side genereret) som del af gap-assessment-resultatet.
