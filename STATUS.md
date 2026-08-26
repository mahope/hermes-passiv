# STATUS — 26. august 2026

## Iteration 498 — Alle 189 blogindlæg linker nu til e-bøgerne

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Færdigt denne iteration

1. **Fundet og lukket et hul i distributionen:** 36 af 94 engelske og 46 af 96
   danske blogindlæg havde intet link til `/books` — den eneste del af sitet med
   ægte downloads (nis2-epub: 3 uniques). Hvert indlæg fik nu en e-bogs-CTA før
   `</footer>`: relevant bog hvor emnet matcher (EAA/GDPR/cookie/NIS2), ellers
   generelt "browse free e-books"-kort + bundle-linje. Script:
   `tools/iter498_books_cta.py` (idempotent).
2. **Deployet og verificeret:** alle 189 blogindlæg (EN+DA) hentet live efter
   deploy — 200 + `/books`-link fundet i samtlige. Books-siden, bundle-ZIP'en
   og EPUB-downloads svarer stadig 200.
3. **Cron tjekket:** reconcile-waitlist.sh kørte manuelt (`real=0 stored=0`,
   log stemmer). Daglig 08:30-cron står korrekt i crontab.

### Ærlige tal pr. 26. aug (kilde: KV-nøgler)

0 køb · 0 licenser · 0 rigtige tilmeldinger · downloads: nis2-epub 3 uniques,
øvrige titler 1 hver · ~23 unikke besøgende over 4 dage.

### Stadig blokeret (uændret)

Lemon Squeezy API-nøgle · Chrome Web Store OAuth · npm/PyPI publish ·
Search Console · KDP-konto (upload-kit færdigt i kdp-upload-kit.md).

### Næste iteration

1. LS-nøglen landet → `node lemon-setup.js` → checkout live → første rigtige
   betaling. Stadig den eneste vej til indtægts-bevis.
2. Mål om de nye CTA'er flytter noget: sammenlign klik på `/books/*` fra
   blogindlæggene (side-tracking viser referrer-sti) mod tidligere tal.
3. Hvis CTA'erne ikke flytter noget inden for ~en uge: stop med at polere sitet
   og byg noget nyt, der ikke deler samme trafikproblem.
