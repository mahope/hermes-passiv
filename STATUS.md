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
