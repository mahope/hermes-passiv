# Iteration 433 — 26. august 2026

## Intern linking: alle 76 EN-blogindlæg linker nu til DeskUptime

**Søgninger:** 0 af 12 (intet skulle faktatjekkes)

**Budget:** 35/1000 DKK (uændret)

## Hvad blev bygget

STATUS.md's egen næste-gangs-liste fra iter 432 pegede på intern linking — gennemgangen
viste at kun **3 af 76** engelske blogindlæg linkede til /deskuptime/, selvom 43 havde
en "Related Guides"-sektion der var det naturlige sted.

1. **43 indlæg** fik et "UPTIME"-kort indsat som første kort i deres eksisterende
   Related Guides-sektion (`site/blog/*.html`).
2. **33 indlæg** uden Related Guides fik en lille inline-sektion ("Keeping websites
   online? …") lige før footeren.
3. **Idempotent script**: `link_deskuptime_433.py` (kan genkøres, gør intet hvis
   linket allerede findes).
4. **Deployet og verificeret live:** curl-tjek af samtlige 76 blogundersider på
   https://hermes-passiv.pages.dev — 76/76 indeholder nu /deskuptime/-linket,
   produktsiden svarer 200, sitemap er urørt og korrekt. Committed som `aa29808`.

## Bemærkning / fejl undervejs
Første kørsel af scriptet lavede 0 ændringer: `os.path.dirname(__file__)` opførte sig
uventet i dette miljø. Løst ved at bruge absolut sti fra cwd. To filer
(http-headers-reference, table-alignment) manglede både Related Guides og footer —
fik manuel indsættelse før </body>.

## Stadig blokeret
1. **Lemon Squeezy-nøgle** (Bitwarden) — licensflow kodet, venter på nøgle.
2. **npm publish** (bugbottle + deskuptime) — kræver npm token.
3. **Google Search Console** — skal Mads godkende.

## Næste iteration
- Dansk blog (/da/blog/) har sandsynligvis samme problem — gennemgå og tilføj
  tilsvarende links til /deskuptime/ der (55 DA-guides).
- Når LS-nøglen kommer: opret DeskUptime Pro på Lemon Squeezy + aktiveringstest.
- Homebrew-formel opdatering ved næste release.

---

# Iteration 434 — 26. august 2026

## Intern linking: alle 55 DA-blogindlæg linker nu til DeskUptime

**Søgninger:** 0 af 12 (intet skulle faktatjekkes)

**Budget:** 35/1000 DKK (uændret)

## Hvad blev bygget
STATUS.md's næste-gangs-punkt fra iter 433: den danske blog havde samme problem —
0 af 55 DA-indlæg linkede til /deskuptime/.

1. **21 indlæg** med "Relaterede guides" fik et UPTIME-kort indsat som første kort.
2. **34 indlæg** uden relaterede-guides sektion fik en inline-sektion ("Skal din
   hjemmeside holde sig online? …") lige før footeren.
3. Idempotent script: `link_deskuptime_da_434.py` (genkørsel bekræftet: 0 ændringer).
4. **Deployet og verificeret live:** curl-tjek af samtlige 55 DA-blogundersider —
   55/55 indeholder /deskuptime/-linket; produktsiden svarer 200. Committed `65caeed`.

## Stadig blokeret
1. **Lemon Squeezy-nøgle** (Bitwarden) — licensflow kodet, venter på nøgle.
2. **npm publish** (bugbottle + deskuptime) — kræver npm token.
3. **Google Search Console** — skal Mads godkende.

## Næste iteration
- Intern linking er nu dækket på både EN (76/76) og DA (55/55). Næste naturlige skridt:
  tjek at de andre produktsider (/clean-copy/, /page-profile/ osv.) får tilsvarende
  links i blogindlæg hvor det er relevant, eller forbedr konvertering på /deskuptime/
  selv (tydeligere CTA, screenshots).
- Når LS-nøglen kommer: opret DeskUptime Pro + aktiveringstest.
- Homebrew-formel opdatering ved næste release.
