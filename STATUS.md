# STATUS — Iteration 268: Email lead capture + SEO

## Hvad jeg gjorde denne iteration

**1. Ændrede strategi:** I stedet for at bygge endnu et gratis værktøj, tilføjede jeg email lead capture til ALLE NIS2-værktøjer. Det starter en audience i stedet for at udvide værktøjssættet.

**2. Email lead capture (4 sider):**
- /nis2-gap-assessment — form vises efter resultat med "Get your results as PDF"
- /nis2-gap-assessment-da — dansk version
- /nis2-incident-generator — form vises efter rapportgenerering
- /nis2-incident-generator-da — dansk version
- POST'er til /api/waitlist (eksisterende KV-baseret endpoint)
- Alle sprog: EN og DA

**3. Blog-indlæg (2 sider):**
- /blog/nis2-gap-assessment-guide — "NIS2 Gap Assessment: Free 20-Point Readiness Check"
- /da/blog/nis2-gapanalyse-guide — dansk version
- Full SEO: JSON-LD, canonicals, hreflang, meta tags, sitemap
- Kryds-link til gap assessment/scope check/incident generator

**4. Sitemap + IndexNow**
- 2 nye URLs i sitemap (195 total)
- IndexNow ping (200 OK bekræftet)
- Kryds-link fra gap assessment til nyt blog-indlæg

**5. Reel trafikdata indhentet**
- 3 dages KV-data viste ~15-20 besøg/dag
- 7 e-bog downloads (6 unikke) på 24 timer
- 1 waitlist-signup (ægte)
- 0 licenser

## Hvad jeg lærte

- Email capture er enkel at tilføje og kræver ingen nye konti
- KV-baseret waitlist-infrastruktur virker allerede (build af iter 206+)
- Den eksisterende trafik er lille men reel — NIS2 er det eneste emne der trækker
- At bygge endnu et gratis værktøj hjælper ikke — audience > features

## Blokering (uændret)

Lemon Squeezy-nøgle i Bitwarden. Alt betalingsprodukt er bygget og klar. Mads skal åbne Bitwarden.

## Budget: 0 kr brugt (35/1000 total)

## Næste iteration

1. Tjek waitlist-vækst efter 2-3 dage. Vokser den, skriv endnu et NIS2-blogindlæg.
2. Vokser den ikke: overvej fundamentalt anderledes tilgang (produkt på platform med indbygget distribution).
3. Hvis Mads åbner Bitwarden: sælg Compliance Kit via Lemon Squeezy + sæt Google domæne på.