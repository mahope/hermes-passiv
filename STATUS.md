# STATUS — Iteration 424: Homebrew-tap verificeret end-to-end + curl-installer

## Søgedisciplin
1 søgning (gh api repo-liste — ikke en websøgning). 0 websøgninger brugt.

## Hovedresultat: distributionskanal bevist virkende uden nogen konto
Tidligere iterationer byggede kanaler der aldrig var blevet testet af et rigtigt
install. Denne iteration testede og fik dem alle grønne:

1. **`brew install mahope/tap/clean-copy`** — installeret, `brew test` grøn,
   pipe-test giver korrekt Markdown-output.
2. **`brew install mahope/tap/deskuptime`** — allerede installeret, `--version` OK.
3. **`brew audit --strict --online`**: clean-copy fejlede ("redundant version line")
   — rettet i tap-repoet, nu **0 problemer på begge formler**.
4. **Duplikat-tap opryddet:** maskinen havde clean-copy fra to taps
   (mahope/clean-copy + mahope/tap); den gamle `mahope/clean-copy`-tap er untappet
   så der kun er én officiel vej (`mahope/tap`). README i clean-copy-cli pegede også
   på den gamle tap — rettet til `mahope/tap`.
5. **Ny curl-installer** `tools/install.sh` i clean-copy-cli: én linje, ingen
   Homebrew, installerer til ~/.local/bin. Første version fejlede (package.json
   manglede ved siden af scriptet) — fanget af min egen lokale test, rettet.
   **Verificeret end-to-end via rå GitHub-URL på ren maskine-mappe:** download →
   install → korrekt output. Tests: 41/41 grønne.

## Hvorfor det betyder noget
Homebrew + curl-install kræver hverken npm-login, Lemon Squeezy eller domæne.
Det er de første distributionskanaler i porteføljen der er **bevist virkende
slut-til-slut**, ikke blot "forberedt".

## Trafik/brug (uændret, ærlige tal)
Ingen nye rigtige brugere denne iteration. 0 tilmeldinger.

## Stadig blokeret på Mads (uændret)
1. npm publish (bugbottle + deskuptime)
2. Lemon Squeezy-nøgle (Bitwarden)
3. Google Search Console-verifikation (DNS-post)
4. GitHub Marketplace-udgivelse = ét klik (beskrevet i BUILD.md)

## Næste iteration
1. Samme end-to-end-bevis for deskuptime-curl-install (der findes ingen
   installer-script dér endnu).
2. Verificér at GitHub Action-repoerne (compliance-site-check, bugbottle-action)
   kan tages i brug af en fremmed: frisk mappe, `uses:` fra tag, gyldig rapport.
3. Overvej en "verified install"-badge/sektion på sitets free-tools-side med de
   nu beviste kommandoer.
