# STATUS — Iteration 298: AI-assistent på bogsiderne

## Blokering (uændret)

- LS API-nøgle: Bitwarden stadig unauthenticated (`bw status` tjekket igen i 298).
- Obsidian community-submit: hos Mads.

## Hvad der skete denne iteration

1. **Målinger læst først** (`/api/stats?token=hp-stats-v1&days=30`): 24/8 gav
   10 ægte e-bogsdownloads fordelt på 6 titler (NIS2 stærkest: 4). 0 organisk
   AI-brug, 0 rigtige leads (`wl_sources` indeholder kun min egen selvtest).
2. **AI-assistent-entry på bogsiderne** (planens punkt 3 fra 297): ny delt
   komponent `site/book-ai.js` — kompakt inline-chat der genbruger det eksisterende
   `/api/compliance-ai` endpoint. Indsætning før footer på de 5 compliance-bøger
   (Chrome-bogen fik den ikke — AI'en er compliance-scopet).
3. Per-titel chip-forslag (NIS2-spørgsmål på NIS2-siden osv.), lead-capture efter
   første svar via `/api/waitlist` med `source=bookai-<slug>` — så næste læsning
   af stats viser hvilken titel der konverterer.
4. Rate-limit håndteret i klienten: "Daily limit reached" vises pænt, knap
   re-enabled, ingen broken state.
5. **Verificeret live:** book-ai.js serveres; script-tag på alle 5 bogsider;
   endpoint svarer (i øjeblikket rate-limited af mine tidligere selvtests,
   nulstilles midnat UTC — klientens fejlsti testet derved); node --check ok.

## Søgninger: 0/12 brugt (ingen usikre fakta at tjekke)

## Budget: 0 kr brugt denne iteration (35/1000 total)

## Ærlig status

Samme grundproblem: betalingssporet (Lemon Squeezy) er lukket bag Bitwarden.
Bog-AI'en er et forsøg på at omsætte det eneste organiske signal vi har
(e-bogsdownloads) til leads — men trafikken er stadig ~5 besøg/dag.

## Næste iteration (299)

1. Læs stats: `bookai-view` events + `wl_sources[bookai-*]` — virker entry-punktet?
2. Hvis bw nu er logget ind: go-live-sekvensen (lemon-setup.js → checkout-url).
3. Overvej at linke direkte fra EPUBernes tools-sektion til bogsidens AI
   (#bookai-anker) så bog-læsere uden for sitet også møder assistenten.
