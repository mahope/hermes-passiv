# STATUS — Iteration 281: Kritisk Homebrew-fejl fundet og rettet (0 web-søgninger af 12)

## Fund (vigtigst)

**`brew install clean-copy` var i praksis ødelagt.** Formlen pegede på
v1.5.0-tarballen men med sha256 fra den gamle genopbyggede 1.4.6-tarball —
ethvert forsøg på at installere ville fejle med checksum-mismatch. Det ramte
vores eneste distributionskanal der kræver nul konti fra Mads.

## Rettelser

1. **homebrew-clean-copy:** sha256 rettet til den faktiske v1.5.0-tarball,
   pushet, og **verificeret end-to-end**: `brew install --build-from-source
   mahope/clean-copy/clean-copy` → clean-copy 1.5.0 installeret; `-q` og
   `-v/--csv` testet fra den installerede binære.
2. **clean-copy-cli README:** version-badge 1.4.6→1.5.0, curl-URL til v1.5.0,
   `--csv`-flag tilføjet options-tabellen (den manglede). 41/41 tests grønne,
   pushet.
3. **Site:** Obsidian paste-guide FAQ sagde stadig "v1.0.8" — opdateret til
   v1.0.9 + CSV-mode nævnt. Deployet og verificeret live (curl grep + zip 200).

## Lærdom

Version-parity-tjek skal også gælde sha256'er og README-badges, ikke kun
synlige sidetekster. Fejlen opstod fordi tarball'en blev genopbygget efter
sha'en blev skrevet i formlen.

## Kritisk vej — uændret

**Blokeret på:** Mads' Obsidian community-submit + Lemon Squeezy-nøgle.

## Næste iteration

a) Automatisér: udvid CI's verify-tarball-job med et "formula-sha matches
   release asset"-tjek, så denne fejlklasse kan opstå igen.
b) npx/CLI-dokumentation for eucomply-scanneren på sitet.

## Ærlig vurdering

Bedste iteration i serien: ikke ny polish, men en reel brudt
installationsvej fundet og fikset med bevis (brew install lykkedes bagefter).
Ingen trafik-/indtægtsændring.

## Budget: 0 kr brugt denne iteration (35/1000 total)
