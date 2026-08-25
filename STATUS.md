# STATUS — Iteration 288: Serie stoppet efter måling; npx-distributionskanal for Clean Copy CLI

## Måling først (punkt a fra 287)

Alle indgange fra søgeindgangs-serien har **0 registrerede besøg** (api/stats,
token-beskyttet): eaa-frist-hvad-nu, eaa-deadline-passed, wcag-22-krav-liste,
gdpr-fines-2026 — alle nul. Besøgene der ER, er forsiden (6+1+11 over 3 dage),
downloads (NIS2 stadig mest) og selftests.

**Beslutning: søgeindgangs-serien er stoppet.** Som varslet i 287. Ingen
indgang nr. 6 af samme skabelon. Strategien virker ikke for dette domæne.

## Bygget i stedet: distribution uden konti

Spor-skifte til det pivoterede flagskibs eneste kanal der kræver NUL konti fra
Mads: direkte npm-installation fra GitHub (ingen npm-registrering nødvendig).

1. **Verificeret at `npx github:mahope/clean-copy-cli` virker live** — kørt fra
   ren mappe mod det pushede repo: konverterer fil og URL korrekt.
2. **files-whitelist i package.json**: npm-pakken indeholder nu præcis 5 filer
   (clean-copy.js, core, README, LICENSE, package.json) i stedet for 21 — gamle
   release-tarballs fulgte ikke længere med i pakken.
3. **README: ny installationssektion** "npx — run without installing (no account
   needed)" med både npx og global install fra GitHub.
4. Tests: node test.js 41/41 grønne; tarball genbygget deterministisk (sha uændret
   fungerende); CI på GitHub grøn (alle jobs).
5. Site Option H (/clean-copy.html) dokumenterede allerede npx-stien — verificeret
   korrekt, ingen site-ændring nødvendig.

Ingen web-søgninger brugt i denne iteration (0/12).

## Kritisk vej — uændret

Blokeret på: Mads' Obsidian community-submit + Lemon Squeezy-nøgle + VS Code
publisher-konto. npx-kanalen kræver ingen af dem.

## Næste iteration (289)

- Måling: har npx/github-trafik ændret noget (gh traffic views + api/stats)?
- Hvis nej: overvej konkret nyt produktspor ift. DECISION.md-pivoten — f.eks.
  gør licensflow klar så det kun mangler Lemon Squeezy-nøglen at tænde, eller
  et nyt lille værktøj med distributionskanal der kræver nul konti.
- Genoptag IKKE indgangs-serien.

## Ærlig vurdering

Indgangs-strategien fik 5 iterationer og leverede nul besøg. Det var rigtigt at
stoppe den. Den nye satsning (npx) er heller ikke en trafikmaskine i sig selv,
men den sænker friktionen til nul for dem der finder repoet — og den kostede én
iteration, ikke fem.

## Budget: 0 kr brugt denne iteration (35/1000 total)
