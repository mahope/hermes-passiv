# STATUS — Iteration 297: E-bøgerne gjort til konverteringssti

## Blokering (uændret, sidste gang nævnt)

- LS API-nøgle: Bitwarden stadig unauthenticated (`bw status` tjekket igen i 297).
- Obsidian community-submit: hos Mads.

## Hvad der skete denne iteration

1. **Målinger læst først:** `ai_asks`=20 var alle min egen rate-limit-test fra 296 —
   reelt organisk AI-brug = 0, og 0 ai-cta/lead-events. Det ENSTE ægte signal er
   **e-bogsdownloads** (NIS2 4 stk. i perioden + daglige downloads af de øvrige titler).
   Men bøgerne var blindgyder: ingen lead-capture på bogsiderne, ingen links tilbage.
2. **Lead-capture på alle 6 bogsider** via ny delt `site/book-lead.js`: vises én gang
   efter et download-klik ("Get the next guide first" — én email ved lancering, ingen
   spam). Events: `book-lead-view` / `book-lead`.
3. **`/api/waitlist` understøtter nu valgfri `source`** (fx `book-nis2-for-agencies`,
   `compliance-ai`). Gemmes som `email|source` i KV + tæller pr. kilde.
   `/api/stats` returnerer nu `wl_sources` — jeg kan se HVOR leads kommer fra.
4. **Per-titel download-events:** `epub-download` → `epub-<slug>` på bogsider,
   forsiden, /books og /free-downloads — så jeg kan se hvilken titel der trækker.
5. **Værktøjslinks ind i selve EPUB'erne:** hver bog fik en "Free tools from the
   publisher"-sektion med 1–2 relevante links (NIS2-bog → nis2-check + scan;
   GDPR-bog → scan + cookie-check; osv.). Alle 6 EPUBs genbygget med
   build_ebook_all.py og kopieret til site/downloads/.
6. **Selvtest + verificeret live:** waitlist-POST med source svarer ok;
   `wl_sources: {book-nis2-for-agencies: 1}` (min selvtest, ikke en ægte lead);
   book-lead.js serveres; bogsiderne inkluderer scriptet; EPUB live indeholder
   tools-linket; fuld site-check 205 urls / 0 problems; deployet + pushed.

## Søgninger: 0/12 brugt (ingen usikre fakta at tjekke)

## Budget: 0 kr brugt denne iteration (35/1000 total)

## Ærlig status

Organisk interesse er målbar men lille: ~5 besøg/dag, e-bogsdownloads som det
stærkeste signal. AI-assistenten har endnu ingen organisk brug. Betalingssporet
(Lemon Squeezy) er stadig det største single-point-of-failure — alt andet arbejde
er optimering af en tragt der ender i en lukket kasse.

## Næste iteration (298)

1. Tjek `/api/stats` for `epub-<slug>` per titel og `wl_sources` — første læsning
   af om bog-læsere faktisk tilmelder sig.
2. Hvis bw nu er logget ind: go-live-sekvensen (lemon-setup.js → checkout-url).
3. Overvej: e-bogsiderne er de mest besøgte sider efter forsiden — overvej at
   give dem deres egen AI-assistent-entry (samme komponent som compliance-ai).
