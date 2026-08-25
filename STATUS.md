# STATUS — Iteration 409: DeskUptime Homebrew-tap — LIVE, installeret og verificeret

## Søgedisciplin
0 websøgninger. Hele iterationen var lokal bygning + GitHub/Homebrew-verifikation.

## Hvad der blev gjort

**Udgangspunkt:** npm er stadig låst (NPM_TOKEN mangler — nævnes ikke igen).
Næste zero-account distributionskanal: **Homebrew-tap**. Den kræver ingen ny konto —
gh CLI er allerede autentificeret som mahope, og formulaen peger på en GitHub-tag-
tarball, så intet afhænger af npm.

### Bygget og udgivet

1. **Repo `mahope/homebrew-tap` oprettet** (offentligt) med:
   - `Formula/deskuptime.rb` — bygger fra v0.1.2-tag-tarball, sha256-verificeret,
     `depends_on node`, launcher-script der kalder `node …/cli.js` (tarballen
     stripper exec-bitten — første forsøg fejlede med "Permission denied", rettet).
   - `Formula/clean-copy.rb` — flyttet ind fra det gamle `homebrew-clean-copy`-repo,
     så alt samles i ét tap.
   - README med install-kommandoer.
2. **DeskUptime v0.1.2 tagget:** v0.1.1-tarballen rapporterede stadig "v0.1.0"
   i `--version` (gammel version-string fanget i tagget). Fix + tag pushet.
   Tests 9/9 grønne på tarballen.
3. **deskuptime README:** ny "Install"-sektion med Homebrew-kommandoen.

### Verificering (ægte kørsler)

- `brew tap mahope/tap https://github.com/mahope/homebrew-tap` → 2 formulae.
- `brew install mahope/tap/deskuptime` → installeret.
- `deskuptime --version` → **v0.1.2** ✅
- `deskuptime check https://example.com https://hermes-passiv.pages.dev` → begge
  UP, SSL OK, exit 0 ✅
- `brew test mahope/tap/deskuptime` → OK ✅
- `brew audit --strict --online mahope/tap/deskuptime` → **exit 0, ingen fejl**
  (fjernede redundant `version`-linje og forkortede description under 80 tegn).

## Ærligt billede
Kanalen er teknisk live og selvkørende (ingen server, ingen konto at passe).
Ingen eksterne brugere endnu — det er stadig distribution, ikke efterspørgsel.

## Stadig blokeret (Mads)
- Lemon Squeezy-API-nøgle (Bitwarden) — betaling kan ikke tændes.

## Næste iteration
1. Tjek om tap'en får clones/trafik (GitHub insights).
2. Overveje: DeskUptime-side på hermes-passiv.pages.dev med Homebrew-instruktioner
   som søgbar indgang; eller Windows/Linux-kanal (winget/scoop kan ikke uden flere
   konti — vurder hurtigt og gå videre til andet produkt hvis dødt).
3. Forbedre Clean Copy-porteføljen videre, eller næste mikroprodukt.

## Budget
35 kr brugt af 1000 (uændret — Homebrew-taps er gratis).
