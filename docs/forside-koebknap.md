# Spec: mahope.tools' forside skal kunne sælge

Målt 30/9 2026, før denne ændring.

## Fundet

`site/index.html` og `site/da/index.html` — mahope.tools' to forsider — har
**0** `buy.stripe.com` i hele filen (talt med `knap_links()` i
`tools/check_article_paid_path.py`). Katalogen havde intet `offer` på
`mahope.tools` for routen `/`; de to `offer`s der stod på `/` var
`site/clean-copy.html` på cleancopy.tools og `site/deskuptime/index.html` på
deskuptime.com, altså to *andre* domæners forsider.

`/` og `/da/` bærer **461 af de 505** målte besøg i portens trafikkolonne, så
det er den mest læste overflade vi har — og den eneste store overflade uden et
køb. Alt hvad forsiden viser (værktøjer, scanner, e-bøger, licensserver) er
gratis; uden en knap er hele sitet en gratis demo.

## Hvilket produkt, og hvorfor netop det

**EUComply Pro** (`eucomply-pro`), kun den årlige plan.

Målt i sidens egen tekst, ikke valgt efter følelse:

- Det er det eneste betalte produkt der **sælges her**. `page-profile` er også
  under "Sold here", men til $19/år; EUComply Pro er $79/år pr. website og
  ligger på mahope.tools' egen worker.
- Kortet under "Sold here" har **allerede** hele gratis/Pro-fordelingen i
  brødteksten: *"Free without a licence key: the accessibility checks, the
  score and grade, and the whole report on the page. Pro ($79/year) adds the
  PDF download and the GDPR/cookie and NIS2/security checks."* Det er
  ordret katalogens tre `free_features` og to `pro_features`. **Mangler er
  altså kun knappen, ikke forklaringen** — så der er ingen ny påstand at
  finde på, kun en handling at tilføje.
- Clean Copy Pro og DeskUptime Pro sælges på *deres* sites og har allerede
  en synlig købsknap dér. En knap til dem på vores forside ville være en
  henvisning, ikke et salg.

Lifetime-udgaven ($149, første 100 køb) er bevidst **ikke** på forsiden. Den
hører til `/compliance-report`, hvor den står i en tier-tabel med
sammenligning; på en kortliste-kort ville to knapper skjule den ene, og
`check_stripe_ctas.py` vil dømme en lifetime-knap uden
`"lifetime": true` i inventaret som en rød linje.

## Hvor på siden

I kortet under **Larger tools → Sold here → EU Compliance Report**, lige efter
den eksisterende gratis/Pro-tekst, hvor prisen allerede står. Ikke i heroen:
heroen sælger værktøjerne, og en $79-knap oven på "Small, free web tools" er
en påstand om en betaling siden ikke gør. Ikke i footeren: en knap i
footeren ses efter at læseren har scrollet forbi det eneste sted på siden der
beskriver produktet.

Den eksisterende "See the free/Pro table"-link beholder vi — den dybere
vej med tabellen, licensbetingelserne og lifetime-prisen ligger på
`/compliance-report`.

## Hvad der ikke ændres

- Ingen ny rute. `/` og `/da/` står allerede i `tools/route_inventory.json`.
- `site/_worker.js` urørt. Licens-, webhook-, fulfillment- og
  downloadvejen er bit-for-bit uændret.
- Ingen fil i `dist/` (gitignored).
- Ingen ændring i `check_article_paid_path.py`'s `CHROME_ROUTES`.
  Undtagelsen for forsiderne står, fordi de tælles i `check_stripe_ctas.py`
  i stedet — det er her den tælles nu.

## Måling

- Baseline: **0** købsknapper på begge forsider, **461** målte besøg på
  `/` + `/da/` (Plausible via `reports/weekly/2026-38.json`; `/api/stats`
  svarer 401 uden `STATS_TOKEN`, **❓ Til Mads**).
- Efter: **1** `buy.stripe.com` på hver forside, og begge registreret i
  `tools/stripe_catalog.json` med `product: "eucomply-pro"`.
- Porten der dømmer det er `check_stripe_ctas.py` (`check_offers`: præcis én
  synlig CTA pr. side pr. produkt). Beviset er mutationen: med linket
  erstattet af `https://example.com/x` skal porten blive rød på netop den
  linje.
- Plausible kan ikke se klik. Kun `/api/stats` kan det, og det kræver
  `STATS_TOKEN`.
