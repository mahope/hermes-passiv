# Redirects på de fire sites

En note, fordi emnet er faldet en iteration på gulvet: en tidligere iteration
ville have tilføjet en `_redirects`-fil til `dist/`, og den ville have været
uploadet og **ignoreret** i drift. Porten ville have været grøn, fordi en fil der
ligner rigtig, er grøn.

## Kort svar

**Brug ikke `_redirects` på de fire sites.** Skriv redirecten i
`site/_worker.js` i stedet, som en blok der matcher på path.

## Hvorfor

Kilde: <https://developers.cloudflare.com/pages/configuration/redirects/>
(afsnittet "Caution", side opdateret 25. august 2026, hentet 27. september 2026).
Citatet er ordret, så det kan efterprøves.

> Redirects defined in the `_redirects` file are not applied to requests served
> by Pages Functions, even if the Function route matches the URL pattern.

Vores `site/_worker.js` er en Pages Function, der matcher **alle** stier og
ender i `env.ASSETS.fetch()`. Den er altså ikke enkelte ruter — den er hele
serveringen. Derfor rammer `_redirects` aldrig noget.

Det er målt, ikke antaget. Efter merge `2f6a544` svarer de to ruter
`https://cleancopy.tools/clean-copy` og `/da/clean-copy` **301** med det
rigtige `location`, kun fordi reglen ligger i workeren.

## Det der virker

Tre blokke i `site/_worker.js`, alle med `Response.redirect(..., 301)`, alle
inde i routing-kæden **før** `env.ASSETS.fetch()`:

| Blok | Gør |
|---|---|
| `EN_BLOG_BACK_REDIRECTS` | gamle `/da/blog/<slug>` → `/blog/<slug>` |
| `DA_SLUG_REDIRECTS` | omdøbte DA-slugs → nye slugs |
| `CANONICAL_HOME_REDIRECTS` | cleancopy.tools' dubletter → forsiden |

## To regler der skal overholdes

1. **Host-scop på tværs af domæner.** `/clean-copy` er 404 på de tre andre
   domæner. En redirect til *deres* forside derfra ville være en løgneste, så
   `CANONICAL_HOME_REDIRECTS` er pakket i
   `trackingDomain(url) === 'cleancopy.tools'`. Samme regel for enhver ny blok.

2. **Reglen må ikke spise filerne i mappen.** `https://cleancopy.tools/clean-copy/og-preview.png`
   skal stadig svare **200**. Blokken matcher derfor på den *normaliserede*
   path (`path.replace(/\/+$/, '')`), så `/clean-copy/og-preview.png` ikke
   matcher nøglen `/clean-copy`.

## Test

`tests/stripe-worker.test.mjs` dømmer alle tre blokke. `site/_worker.js` er
produktionskritisk, så en ny redirect-blok skal have en arm der beviser både
at den **gør** redirecten, og at den **ikke** spiser en fil under den gamle
sti. Se fx de otte arme tilføjet til `CANONICAL_HOME_REDIRECTS`: 301 fra begge
ruter, at dubletten ikke serveres selv om CDN'en har den, at mappen uden side
sender 301, at `og-preview.png` stadig serveres, at reglen ikke gælder
mahope.tools, og at forsiden selv ikke er omfattet.

## Hvornår det alligevel er relevant

Cloudflares egennote peger på to veje ud afFunctions: **migrér reglerne ind i
Function-koden** (det er den vi bruger), eller **ekskludér routen fra Functions**
med en `_routes.json`-fil. Den sidste er den eneste måde en `_redirects`-fil
kan virke på et Pages-projekt med Functions.

Forudsætningen er altså, at `site/_worker.js` på et tidspunkt **kun** matcher
bestemte stier — i dag `/api/*` og en håndfuld assets — og at resten går til
statisk servering uden om sig. Målt i dag: workeren matcher alle stier og
ender i `env.ASSETS.fetch()` (`site/_worker.js:257`), så `_routes.json` ville
kræve, at vi bevidst lod redirect-ruterne falde uden for workeren.

Vi har ingen `_routes.json`, og vi bør ikke få en uden at måle det først:
`/clean-copy/og-preview.png` skal stadig serveres, og en `_routes.json` der
udelukker for meget, får statikken til at svare selv for de ruter, der skal
redirecte.
