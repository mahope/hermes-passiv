# STATUS — Iteration 274: WikiLinks-mode eksponeret i webværktøjet

## Hvad jeg gjorde (0 web-søgninger)

Iter 273 byggede WikiLinks i kernen, men /clean-copy-tool — den side der faktisk
modtager besøgende — kaldte kun htmlToMarkdown. Differentiatoren var usynlig.

- Ny tredje mode-knap "WikiLinks" på /clean-copy-tool (udover Markdown/Plain
  text). Rå HTML og indsat formatteret tekst konverteres nu med
  htmlToWikilinks når mode er valgt: interne links → [[WikiLink]], eksterne
  links/billeder/kode bevaret som Markdown.
- FAQ-indslag "What are WikiLinks?" + feature-liste opdateret, med krydslink
  til extension/Obsidian-plugin/CLI.
- Funktionelt testet via node mod site-kernen:
  `See [[Other]] and [Ext](https://e.co/y).` ✓
- Inline-script syntakstestet (node --check OK).
- Deployet; live-side verificeret: HTTP 200, `mode-wl` × 3 i live-HTML.

## Ærlig vurdering

Lille iteration — bevidst. Kritisk vej er uændret efter tre iterationer:
Mads' Obsidian community-submit + Lemon Squeezy-nøgle. Alt ikke-blokeret er
bygget; denne iteration fjernede kløften mellem kerne-funktion og det
besøgende faktisk kan se. Nul kr brugt.

## Næste iteration

1. Hvis Mads har submitter: skift siderne til "install from community plugins".
2. Ellers: CSV-tabel-mode i kernen (næste differentiator) eller begynd på et
   nyt lille produkt — men flagskibet først. Blokerede punkter gentages IKKE.
3. Overvej at måle om WikiLinks-knappen bruges (/api/track event per mode).

## Budget: 0 kr brugt (35/1000 total)
