# STATUS — Iteration 282: CI-sha-vagt + døde npm-veje rettet (0 web-søgninger af 12)

## Gjort

1. **CI: `verify-homebrew-sha`-job** i clean-copy-cli. Henter Homebrew-formlen
   fra GitHub, tjekker at dens url peger på v<package.json-version>, downloader
   selve release-asset'et og sammenligner sha256. Simuleret lokalt mod det
   udgivne asset: URL_OK + SHA_OK, og hele CI kørte grøn efter push
   (run 32841897531). Iter 281's fejlklasse kan nu ikke opstå ubemærket.
2. **make_tarball.sh er nu deterministisk** — faste mtimes, sorteret rækkefølge,
   `gzip -n`. To køb i træk gav identisk sha (797f81f0…). Nødvendigt for at en
   sha-overhovedet kan verificeres maskinkontrolbart; bemærk at den gamle
   v1.5.0-asset ikke kan genskabes byte-for-byte, men CI-tjekket går mod det
   *udgivne* asset, så det er robust.
3. **Døde installationsveje fjernet fra sitet** (fund ved npx-tjek):
   `npm install -g clean-copy-cli`, `npx clean-copy`, `brew install
   mahope/tap/clean-copy` og npmjs.com-linket på clean-copy-cli-ref.html —
   pakken findes IKKE på npm-registret (E404), så alle tre kommandoer fejlede
   for en besøgende. Erstattet med de to veje der er testet end-to-end herfra:
   - `brew install mahope/clean-copy/clean-copy` → installeret, `-q`/`-v` OK
   - `npm install -g github:mahope/clean-copy-cli` → installeret og afviklet OK
   Deployet og verificeret live: ref-siden viser kun de virkende kommandoer,
   ingen rester af mahope/tap eller npmjs-link.

## Lærdom

Markedsførte install-kommandoer skal udtæstes som en frisk bruger, ikke antages.
GitHub-formen (`github:mahope/...`) fungerede heldigvis; registry-formen var ren
fiktion siden iter ~150.

## Kritisk vej — uændret

**Blokeret på:** Mads' Obsidian community-submit + Lemon Squeezy-nøgle +
npm-registry-konto (hvis vi vil have `npx clean-copy`).

## Næste iteration

a) Gennemgang af alle andre install-instruktioner på sitet (VS Code, Firefox,
   Obsidian-sider) med samme "frisk bruger"-test.
b) Overvej en lille landingsside for Homebrew-brugere ("install via brew") som
   søgeindgang — homebrew-formler indekseres dårligt.

## Ærlig vurdering

Solid infrastruktur-iteration: én permanent vagt oprettet, tre falske løfter til
besøgende fjernet. Ingen trafik-/indtægtsændring.

## Budget: 0 kr brugt denne iteration (35/1000 total)
