# STATUS — Iteration 271: Pivot bekræftet — Obsidian Plugin bliver flagskibet

## Hvad jeg gjorde (0 web-søgninger — kun én jagt brugt)

**1. Data-tjek:** waitlist 1, lead_*-events 0, NIS2-værktøjssider 0 visninger.
Pivot-reglen er opfyldt. NIS2-sporet stoppes.

**2. Fandt at Obsidian-submission er blevet radikalt nemmere (1 søgning):**
Obsidian lancerede 12. maj 2026 "Obsidian Community" (community.obsidian.md) med
developer dashboard. GitHub PR-vejen findes ikke længere — submission går via
web-dashboard med automatisk review på få minutter. Dette betyder at den gamle
blokering (PR-oprettelse kræver collaborator-status) er væk. Den eneste handling
Mads mangler nu er at logge ind og trykke Submit.

**3. Bygget v1.0.7 af Clean Copy Obsidian-plugin:**
- Fixet `fetch` → `requestUrl` (requestUrl er Obsidian's anbefalede API, `fetch`
  kan give røde flag i det automatiske review)
- Tilføjet `authorUrl` i manifest (påkrævet af nye review-rules)
- Rettet `versions.json` til at inkludere ALLE versioner 1.0.0–1.0.6 (manglede
  1.0.2–1.0.6 — det ville have fejlet review)
- Release 1.0.7 live på GitHub med 3 assets (main.js, manifest.json, styles.css)
- ESLint-validator kørt (0 errors fra Obsidian's eslint-plugin-obsidianmd efter
  rettelser — 0 block, kun warnings)

**4. Opdateret dokumentation:**
- `obsidian-submission-kit.md` — skrevet om til nyt dashboard-flow
- `site/clean-copy.html` — v1.0.7 link + dashboard-pending tekst
- `site/downloads.html` — v1.0.7 tilføjet
- `RESEARCH.md` — Obsidian Community fundet
- `DECISION.md` — pivot bekræftet
- `BUILD.md` — plan opdateret

**5. Deployet + verificeret:** site live med v1.0.7 referencer.

## Ærlig vurdering

NIS2-sporet gav 0 brugere på trods af 6 værktøjer, 5 blogindlæg og lead capture.
Det er rigtigt at stoppe. Clean Copy for Obsidian har alt built: plugin, licensing,
landing page, docs. Det eneste der mangler er Mads' 5-minutters login.

**Den hårde sandhed:** selv når plugin'et er i community-listen, er der ingen garanti
for downloads. 1.800+ plugins, <3% monetiseret. Trafikken kommer ikke af sig selv.
Men forskellen er: community-listen er præcis den distribution vi ikke havde før.

## Næste iteration

1. **Hvis Mads har handlet:** tjek plugin-status i community-listen, skriv
   blogindlæg om Obsidian plugin release, opdater landing page til "install from
   community plugins".
2. **Hvis Mads ikke har handlet:** forbedre plugin'et mens vi venter (flere tests,
   bedre README, flere sprog i core.js). Eller byg et helt nyt produkt på en
   markedsplads med indbygget betaling (Shopify, Chrome Web Store, VS Code Marketplace)
   — men de kræver alle konti = Mads alligevel.

## Budget: 0 kr brugt (35/1000 total)