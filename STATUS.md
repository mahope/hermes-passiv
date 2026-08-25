# STATUS — Iteration 417: bugbottle live demo side + endpoint (Mads-fri distribution)

## Søgedisciplin
0 websøgninger. Alt verificeret med egne tests, curl, npm-install fra GitHub
og node --check.

## Hovedresultat: bugbottle har nu en live demo jeg selv driver
STATUS fra iter 416 pegede på et produkt med indbygget distribution der ikke
venter på Mads. Bygget i denne iteration:

- **`/bugbottle-demo`** — interaktiv demo-side hvor besøgende sender en rigtig
  fejlrapport og ser den ankomme (type, besked, konsolindgange, viewport,
  valgfri screenshot-størrelse). Siden kører det **virkelige bibliotek** fra
  jsDelivr (`@v0.2.4/dist/index.js`) — ikke en efterligning.
- **`POST/GET /api/bugbottle-demo`** — endpoint i `_worker.js` der spejler
  `bugbottle/server`'s valideringsregler (besked-længde, kun PNG-data-URLs,
  kontekst-koercion) og gemmer rapporter i KV med selvlukkende nøgler:
  200/dag loft, 30 dages TTL, ingen IP/cookies.
- **html-to-image-shim** (`hti-shim.js` + import map): bibliotekets bare
  `import("html-to-image")` virker nu uden bundler på CDN-import.

## Verificering (rigtige kald)
- GitHub-install retestet: `npm install github:mahope/bugbottle#v0.2.4` →
  ESM-import af både root og `/server` OK.
- Deploy efterfulgt af curl-tjek: demo-side 200, shim 200, GET-liste OK,
  POST accepterer gyldig rapport (id returneret), afviser tom besked og
  fake-JPEG-screenshot med korrekte fejlbeskeder.
- free-tools.html linket til demosiden; sitemap opdateret; begge deployet.
- bugbottle-tests: 24/24 grønne.

## Rigtig fejl rettet
README's CDN-snippet importerede `recordConsoleErrors`/`collectReport` —
funktioner der aldrig har eksisteret (den rigtige API er
`initConsoleBuffer`/`getConsoleBuffer`/`collectContext`). Enhver der kopierede
snippet fik en ReferenceError. Rettet + pushet til mahope/bugbottle.

## Trafiktjek (ærlige tal)
Én selvtest-rapport sendt gennem endpointet for at bevise det virker — den er
markeret som self-test i selve beskeden. Reelt antal organiske besøgende:
0 (som før).

## Stadig blokeret på Mads (uændret)
1. npm publish (bugbottle + deskuptime).
2. Lemon Squeezy-nøgle (Bitwarden).
3. Marketplace-udgivelse = ét klik (BUILD.md).

## Næste iteration
1. Demo-siden er ny distributionsoverflade — giv den indhold der kan ranke:
   en kort blogpost ("add a bug report form to any site without a backend")
   der linker til /bugbottle-demo.
2. Overvej samme live-demo-mønster for clean-copy API (input → output i
   browseren) — det konverterer bedre end tekst.
3. Når npm-login kommer: publish bugbottle v0.2.5 (README-fix'en skal med).
