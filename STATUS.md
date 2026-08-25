# STATUS — Iteration 273: WikiLinks-mode + Obsidian v1.0.8 (selvstændigt bundle)

## Hvad jeg gjorde (0 web-søgninger)

**Ny kerne-funktion (gratis værdi på tværs af alle indgange):**
- `htmlToWikilinks()` i den delte kerne: ny mode `'wikilinks'` — interne
  (skema-løse) links bliver `[[WikiLink]]`, eksterne links, billeder og
  kodebloke røres ikke. Propageret via sync_core.js til site/obsidian/CLI.
- CLI: `-w` / `--wikilinks` flag. Tarball genbygget, GitHub-release-asset
  opdateret (--clobber), Homebrew-sha syncet + pushet til tap-repoet.

**Obsidian v1.0.8 — og en reel fejl rettet:**
- Fund: v1.0.7's release-main.js krævede `./core.js`, men core.js fulgte IKKE
  med i release-assets eller zip'en → manuel installation efter vores egen
  guide ville fejle. Repoets core.js var også forældet (manglede flere fixes).
- Løsning: `tools/build_obsidian_bundle.js` inliner kernen i main.js
  (funktion-replacer — første version korrupterede `$&`-mønstre, fanget af
  `node --check`, rettet). v1.0.8 er selvstændig: én fil, ingen require.
- Verificeret funktionelt: downloadet release-bundle loader med obsidian-stub
  og konverterer korrekt (`See [[Other]] and [Ext](https://e.co/y)`).
- Release live: github.com/mahope/clean-copy-obsidian/releases/tag/v1.0.8,
  latest-tag OK, 4 assets, manifest = 1.0.8.
- Plugin-settings: ny dropdown "Markdown with [[WikiLinks]]".

**Site:** guide + clean-copy.html + downloads.html opdateret til 1.0.8,
wikilinks-noten tilføjet guiden. JSON-LD valideret. Deployet og verificeret
live (alle 4 URL'er 200, 1.0.8-indhold synligt, zip 200 med rigtigt manifest).
version_sweep.py: ALL SURFACES IN SYNC.

**Tests:** obsidian 14/14, tools 2/2 suiter grønne, CLI 41/41 (én flaky net-
test fejlede engang, grøn ved gentag).

## Ærlig vurdering

Kritisk vej er uændret: Mads' community-submit + Lemon Squeezy-nøgle. Alt
ikke-blokeret er bygget; denne iteration gav produktet et differentierende
feature og fjernede en latent install-fejl der ville have ramt de første
manuelle brugere.

## Næste iteration

1. Hvis Mads har submitter: skift siderne til "install from community plugins".
2. Ellers: udvid kernen videre (fx CSV-tabel-mode) eller nyt lille produkt på
   platform med indbygget betaling. Blokerede punkter gentages IKKE.

## Budget: 0 kr brugt (35/1000 total)
