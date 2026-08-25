# DECISION — Iteration 268: Email lead capture + SEO blog-indlæg

**Dato:** 2026-08-25
**Beslutning:** Skift fra at bygge flere gratis værktøjer til at bygge en audience. Email lead capture på alle NIS2-værktøjer. SEO-blogindlæg til gap assessment.

## Situationen

**Data (reelle, bekræftet 25/8):**
- Sitet får ~15-20 besøg/dag (3 dages data: 23-25 aug)
- 7 e-bog downloads på en dag (6 unikke) — NIS2-e-bogen topper med 4/3
- 1 ægte waitlist-signup
- 0 licenser solgt (forventet — betaling blokeret)

**Hvad der ikke virkede:** At bygge endnu et gratis værktøj (gap assessment, incident generator, scope checker) og håbe på at noget ændrer sig. Værktøjerne er gode, men de bygger ikke en audience og de tjener ikke penge.

**Hvad jeg gjorde anderledes denne iteration:**
1. Tilføjede email lead capture til gap assessment (EN + DA)
2. Tilføjede email lead capture til incident generator (EN + DA)
3. Skrev SEO-blogindlæg "NIS2 Gap Assessment: Free 20-Point Readiness Check" (EN + DA)
4. Kryds-linkede værktøjer + sitemap + IndexNow

**Hvorfor dette er rigtigt:**
- Email capture er INBOUND — brugeren vælger selv at give sin email. Ikke udadvendt handling i Mads' navn.
- Listevækst løser distributionsproblemet: når Mads åbner betaling, har vi folk at konvertere.
- Blogindlægget tilføjer søgbart indhold uden at bygge et nyt værktøj.
- PDF-export via `window.print()` + `window.open()` giver brugeren værdi med det samme.

## Hvad det stadig ikke løser

- 0 kr i indtægt — betalingsvej stadig blokeret (Bitwarden)
- Audience er lille — lead capture er en investering, ikke en indtægt
- Kan ikke sende mails til listen uden Mads' godkendelse

## Budget: 0 kr brugt (35/1000 total)

## Næste iteration

1. Tjek om email captures gav nye signups (via /api/stats — waitlist-tælleren)
2. Hvis waitlist vokser: skriv endnu et NIS2-blogindlæg (f.eks. "NIS2 documentation requirements for web agencies")
3. Hvis waitlist stadig 1: overvej fundamentalt anderledes tilgang — byg produkt med indbygget distribution (f.eks. AI-baseret værktøj på en markedsplads med egen trafik)
4. Hvis Mads har åbnet Bitwarden: aktiver Lemon Squeezy og sælg Compliance Kit