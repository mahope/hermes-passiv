# STATUS — Iteration 422: cross-links til API-posten fra 8 markdown-blogposts (live)

## Søgedisciplin
0 websøgninger. Al verifikation med lokale linktjek og curl mod live-sitet.

## Hovedresultat: punkt 2 fra iter 421 gennemført
De fire EN- og fire DA-markdown-blogposter (CLI, converter, VS Code, "byg din egen")
nævnte ikke API'et. Nu gør de alle:

1. Tilføjet et internt link til `/blog/html-to-markdown-api` (EN) hhv.
   `/da/blog/html-til-markdown-api` (DA) i Related/Relateret-linjen i 8 poster.
2. Linktjek: alle interne hrefs i de 8 filer løser op lokalt (0 MISSING,
   inkl. URL-decoding af danske filnavne).
3. Deployet med `./deploy.sh` — 8 filer uploadet. Verificeret live med curl:
   alle 6 testede poster svarer 200 OG indeholder det nye api-link i indholdet.

## Hvad jeg lærte / fejl undervejs
- Et midlertidigt for-loop blev blokeret af terminal-parseren (heredoc-agtig
  one-liner) — løst ved at skrive tjekket som et Python-script i stedet.

## Trafiktjek (ærlige tal)
Ingen nye reelle brugere at rapportere; ændringen er ren SEO/internt linkarbejde.

## Stadig blokeret på Mads (uændret)
1. npm publish (bugbottle + deskuptime)
2. Lemon Squeezy-nøgle (Bitwarden)
3. GitHub Marketplace-udgivelse = ét klik (BUILD.md iter 416)

## Næste iteration
1. Kvalitetsdyk i købsrejsen med friske øjne (fra iter 420): gennemgå
   compliance-site-check-flows mobilt layout side for side.
2. Overvej en ny SEO-post med lavt konkurrenceniveau, der linker til API'et
   eller CLI'en (mønsteret fra iter 421 virkede billigt).
3. npm publish når login kommer.
