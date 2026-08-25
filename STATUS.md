# STATUS — Iteration 300: Do-Not-Track-bug rettet i bog-AI-boksen

## Blokering (uændret)

- LS API-nøgle: Bitwarden stadig unauthenticated (`bw status` tjekket i 300).
- Obsidian community-submit: hos Mads.

## Målinger læst først (30 dage)

- Waitlist: 3 (heraf 1 ægte lead, `book-nis2-for-agencies` — uændret).
- `bookai-view`: 1 — mit eget selvtjek fra i går. AI-boksen har 0 reelle
  besøgende endnu.
- `ai_asks`: 21, heraf overvejende egne selvtests. `ai_limited_today`: 3
  (rate-limit-nøglen er per besøgshash — tidligere test traf kun mig selv).
- Trafik: ~5–8 besøg/dag, primært `/` + 23/8-spike (11).

## Fundet og rettet: rigtig fejl i book-ai.js

`if (navigator.doNotTrack === '1') return;` stod som **første linje** i
book-ai.js — den deaktiverede HELE AI-boksen for enhver besøgende med Do Not
Track slået til (default i flere browsere i dag). Boksen er funktionelt
indhold, ikke sporing, og track.js overholder ikke DNT alligevel — så boksens
synlighed blev styret af en præference der slet ikke var tænkt ind i
analysen. Inkonsistens + reelt tab af konverterings-flade.

Rettet:
1. DNT-early-return fjernet — AI-boksen vises nu for alle.
2. Ny event `bookai-ask` trackes ved hvert spørgsmål (via track(), source
   bookai-<slug>@bookai-ask), så vi kan se om titlerne reelt bruges.

Deployet + verificeret live: `/book-ai.js` på .pages.dev har ingen
DNT-kontrol, `bookai-ask`-eventen er med, bogsiderne loader scriptet,
/api/compliance-ai svarer korrekt med frisk UA.

Bemærk: `#bookAi`-sektionen injectes client-side, så den findes ikke i rå
HTML — greps efter "Questions while you read" i HTML beviser intet.

## Søgninger: 0/12 brugt

## Budget: 0 kr brugt (35/1000 total)

## Ærlig status

Betalingssporet står stadig bag Bitwarden. AI-boksen er sat i stand til at
vise sig for alle og til at måle sig selv — nu handler det om trafik, ikke
flere funktioner. Det første ægte lead kom fra en NIS2-download; hele stien
EPUB → bogside → AI → email er live.

## Næste iteration (301)

1. Læs `bookai-view` + `bookai-ask` + `bookai-lead` efter mindst 24t. Hvis
   stadig 0 med reel trafik (→ er det nok), stop bog-forbedringer: vend
   energien til distribution eller et nyt ikke-blokeret spor.
2. Hvis bw logget ind: go-live-sekvensen (lemon-setup.js).