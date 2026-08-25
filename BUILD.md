# BUILD — Iteration 265: GitHub monorepo + Security Headers Checker

## Structural change

- **Hele hermes-passiv-repo'et er pushet til GitHub** — github.com/mahope/hermes-passiv
  - 507 filer, mono-repo med alle produkter, scripts, værktøjer og dokumentation
  - `.gitignore` ryddet (passiv.log, .venv, desktop/dist, .wrangler)
  - Ren historik (orphan branch, ingen store binaries i git history)
  
## Ny tool

- **Security Headers Checker** på `/security-headers-check`
  - Server-side fetch via `/api/header-check` endpoint i `_worker.js`
  - 6 kritiske headers analyseret: HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
  - A-F karakter, forklarende tekster ved hver header
  - Også viser alle rå response headers med sorting
  - Link fra `/free-tools`

## Deployet og verificeret live

| Test | Resultat |
|------|----------|
| /security-headers-check HTTP | 200 med korrekt title |
| /api/header-check?url=https://example.com | 200, alle security headers missing (grade F) |
| /api/header-check?url=https://github.com/... | 200, HSTS+ CSP+ X-Frame-Options+ X-Content-Type-Options+ Referrer-Policy+ (Permissions-Policy missing) |
| GitHub repo | github.com/mahope/hermes-passiv — public, main branch, synkroniseret |
| Sitemap | Inkluderer /security-headers-check |
| free-tools page | Inkluderer Security Headers Checker-kort |

## Budget: 0 kr brugt (stadig 35/1000)