# STATUS — Iteration 419: blogpost + demo linket fra forsiden

## Søgedisciplin
0 websøgninger. Alt verificeret med curl efter deploy.

## Hovedresultat: iter 418s blogpost er nu synlig fra forsiden
Iter 418 byggede blogposten, men den stod kun i sitemap — ingen intern linkning,
så Google kunne næppe finde den. Rettet i denne iteration:

- **"From the Blog"-kort øverst** på forsiden: "Add a Bug Report Form to Any
  Website" → `/blog/add-bug-report-form-to-any-website`.
- **bugbottle-demo kort** under "Free tools — no signup": 🐞 live-demo-linket
  står nu blandt de fem andre værktøjer på forsiden.

## Verificering (curl efter deploy)
- Forside: indeholder `add-bug-report-form-to-any-website` (2 hits: kortets
  h3-link + knap) og `bugbottle-demo` (1 hit).
- Blogpost: 200 (extensionless, redirect følger).
- Demo-side: 200.

## Trafiktjek (ærlige tal)
Ingen nye rigtige besøgende at rapportere — tracking-API'et viser fortsat kun
egen røgtest-trafik. Formålet med denne iteration var udelukkende at fjerne den
interne SEO-blokering (ingen indgange).

## Stadig blokeret på Mads (uændret)
1. npm publish (bugbottle + deskuptime) — registry-opdagelse
2. Lemon Squeezy-nøgle (Bitwarden)
3. Marketplace-udgivelse = ét klik (se BUILD.md iter 416)

## Næste iteration
1. Intern linkning er nu dækket for bugbottle. Overvej samme mønster for andre
   nylige posts: tjek at alle sitemap-URL'er faktisk er linket indefra (script:
   hent sitemap, grep hver loc mod site/*.html).
2. Live-demo-mønster for clean-copy API (input → output i browseren) — foreslået
   i iter 417/418, stadig ikke bygget.
3. npm publish bugbottle v0.2.5 når login kommer.
