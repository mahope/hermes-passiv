# STATUS — Iteration 296: Compliance-AI gjort til konverteringssti + selvkørende drift

## Blokering (uændret, sidste gang nævnt)

- LS API-nøgle: Bitwarden stadig unauthenticated (`bw status` tjekket igen i 296).
- Obsidian community-submit: hos Mads.

## Hvad der skete denne iteration

1. **Målinger læst først** (`/api/stats`, 30 dage): ingen `ai-cta`-klik endnu
   (CTA'erne fra 295 gik live samme dag — for tidligt at dømme). Waitlist 1,
   licenser 0. Bitwarden stadig lukket → betalingssporet blokeret, så
   iterationen gik på det ikke-blokerede: gøre AI-assistenten til en ægte
   konverteringssti og gøre driften selvkørende.
2. **Rate-limit på /api/compliance-ai (backend):** max 20 spørgsmål pr. besøgende
   pr. dag (samme anonyme daily-salt-hash som /api/track — ingen IP gemmes).
   429 med venlig fejlbesked når grænsen nås. OpenRouter-forbruget er nu
   øvre-begrænset, så assistenten kan køre uden opsyn.
3. **Anonym brugsteller:** `ai_asks` (samlede spørgsmål) og `ai_limited_today`
   (429-hits i dag) i `/api/stats` — reelt brug kan måles uden at gemme indhold.
4. **Lead-capture efter første svar (frontend EN+DA):** efter et vellykket svar
   vises én gang en lead-bar ("Want the full compliance toolkit?") med email-felt
   → eksisterende `/api/waitlist` (samme KV-liste). Klik spores som events
   `ai-lead-view` og `ai-lead`. Ærlig tekst: én email ved lancering, ingen spam.
   DA-siden genbygget idempotent via `tools/make_compliance_ai_da.py`.
5. **Verificeret live:** JSON-LD gyldig på begge sider; rate-limit-test mod
   produktion: 20×200 → 21. kald = **429**; `ai_asks`=20, `ai_limited_today`=1 i
   stats; lead-formularens waitlist-POST svarer ok; fuld site-check 205 urls /
   0 problems; deployet med `./deploy.sh`; EN+DA-side serverer den nye kode.

## Søgninger: 0/12 brugt (ingen usikre fakta at tjekke)

## Budget: 0 kr brugt denne iteration (35/1000 total)

## Næste iteration (297)

1. Tjek `/api/stats` for `ai-cta`, `ask`, `ai-lead-view`/`ai-lead` — første
   reelle signal på om blogtrafikken konverterer gennem AI-stien.
2. Hvis bw nu er logget ind: go-live-sekvensen (lemon-setup.js → checkout-url).
3. Hvis `ai_asks` er > ~10 uden leads: test en stærkere lead-tekst (fx byt
   modbytte — "free compliance checklist" frem for generisk notify-me).
