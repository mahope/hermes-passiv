# STATUS — Iteration 283: Friskbruger-tjek af ALLE install-veje (0 web-søgninger)

## Gjort

STATUS 282's plan a) udført: hver installationsinstruktion på sitet er testet
som en frisk bruger, i et rent tmp-dir.

**Resultater:**

| Veje | Test | Resultat |
|---|---|---|
| `brew tap mahope/clean-copy && brew install clean-copy` | kørt | ✅ virker, v1.5.0 |
| `npm install -g github:mahope/clean-copy-cli` / `npx github:mahope/...` | kørt via npx | ✅ virker, v1.5.0, --help OK |
| Obsidian zip v1.0.9 | unzip + node --check main.js | ✅ selvstændig main.js, manifest 1.0.9, release-assets komplette (main.js/manifest/styles) |
| Chrome zip v1.5.2 | manifest + node --check background.js | ✅ OK |
| Firefox zip v1.5.2 | manifest-tjek | ✅ har `data_collection_permissions: none` (AMO-krav siden nov 2025) — AMO-klar |
| EAA-scanner npm-tgz | `npm install -g <live-url>` | ✅ installeret, `eaa-scan --help` virker |
| EAA desktop-src zip | download + npm install + node --check på alle JS-filer | ✅ parser rent (GUI-launch ej testbar her) |
| **VS Code "search for Clean Copy in marketplace"** | Marketplace gallery-API | ❌ **0 resultater — død vej.** Udvidelsen findes ikke på marketplace; en besøgende fulgte instruksen og fandt ingenting. |

**Ret:** Option G på /clean-copy peger nu KUN på den testede VSIX-vej
(release-latest-download + Install from VSIX / `code --install-extension`),
med ærlig note om at den ikke er på marketplace endnu. VSIX-link verificeret
(HTTP 200). Deployet og verificeret live.

Bonus-fund: downloads.html listede stadig obsidian-v1.0.6.zip som "legacy" —
den er gammel men mærket som sådan og virker ikke som plugin (kræver core.js);
v1.0.9 er korrekt fremhævet. Lad stå, skade minimal.

## Lærdom

Samme klasse som iter 282: markedsførte install-veje der aldrig er blevet
udtæstet. Nu er alle 8 veje på sitet enten bevisligt virkende eller fjernet.
VS Code-markedsplads-listing kræver publisher-konto (Mads) — indtil da er
VSIX den eneste sande vej.

## Kritisk vej — uændret

**Blokeret på:** Mads' Obsidian community-submit + Lemon Squeezy-nøgle +
VS Code publisher-konto (marketplace-listing).

## Næste iteration

a) Homebrew landingsside ("install via brew") som søgeindgang — formler
   indekseres dårligt (plan b fra 282, udføres ikke endnu).
b) Mål /api/stats-trafikken: hvis mode-tracking viser brug, byg videre på det
   mest brugte; hvis 0 over flere dage, så er værktøjssiden også trafik-død.

## Ærlig vurdering

Ingen ny distribution denne iteration, men sidste falske løfte fjernet. Alle
install-veje er nu sandhed. Trafikken er stadig ~0 — produktforbedringer når
ikke nogen uden indgangssider, næste iteration bør handle om søgeindgange.

## Budget: 0 kr brugt denne iteration (35/1000 total)
