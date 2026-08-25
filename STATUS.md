# STATUS — Iteration 270: Måling af lead-formularer (hvilken side konverterer?)

## Hvad jeg gjorde denne iteration

**1. Data-tjek først (0 web-søgninger):**
- Waitlist: stadig **1 ægte** signup. Lead capture har været live ~1 dag.
- Sitetrafik: 15 besøg (23/8), 18 (24/8), 5 indtil formiddag (25/8). Stort set
  alt på forsiden — NIS2-værktøjssiderne fik **nul registrerede sidevisninger**
  i hele perioden. Det er hovedproblemet: ingen kommer til siderne.
- GitHub: 0 visninger/14 dage på alle repos (uændret).

**2. Fundet og lukket et målehul (byggearbejdet denne iteration):**
Lead-formularerne på alle 6 NIS2-sider gemte e-mails, men loggede ikke *hvad
der blev sendt fra hvilket værktøj*. Nu sender hver formular en `trackEvent`
ved succesfuld tilmelding (`lead_nis2-check`, `lead_nis2-gap-assessment-da` osv.),
så /api/stats viser præcis hvilke sider der konverterer — uden at vente på at
Mads skal læse KV manuelt. Verificeret live med curl på alle 6 sider.

**3. Deployet + verificeret:** alle 6 sider serverer den nye tracking-kode,
/api/waitlist og /api/track svarer korrekt, commit pushet.

## Ærlig vurdering

Waitlist = 1 efter to dage med lead capture. Trafikken til selve værktøjerne
er nul — formularen kan ikke konvertere besøgende der ikke findes. Iterationens
konklusion: **distribution er fortsat flaskehalsen**, og de kanaler vi kan nå
selv (GitHub, blog) giver målbart 0.

## Blokering (uændret — gentages ikke længere)

Lemon Squeezy-nøgle, CWS-credentials, KDP-konto, email-afsender. Alt ligger som
én liste i BUILD.md.

## Budget: 0 kr brugt (35/1000 total)

## Næste iteration

1. Tjek `lead_*`-events i /api/stats — første gang vi kan se konvertering per side.
2. Hvis stadig 0 leads og 0 trafik: stop med at polstre NIS2-spor og byg til en
   platform med indbygget distribution + betaling i én godkendelse hos Mads.
   Konkret kandidat ift. RESEARCH.md iter 140: Obsidian-plugin ($29–49 licens,
   community-markedets trafik), eller Shopify-app (0% revenue share under $1M).
3. Bitwarden åbnet → Lemon Squeezy live samme dag.
