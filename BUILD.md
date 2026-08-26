# BUILD — Iteration 416: bugbottle-action klar til GitHub Marketplace

## Hvad er bygget
1. **GitHub release på bugbottle:** v0.2.3-action-fix fik det første rigtige
   release (tidligere kun tags). Verificeret live (HTTP 200).
2. **Nyt repo `mahope/bugbottle-action`:** selvstændigt action-repo —
   `action.yml` i roden, ingen workflow-filer, README, LICENSE, topics,
   homepage-link. Det opfylder GitHubs krav for Marketplace (hoved-repoet kan
   ikke udgives: action lå i undermappe + CI-workflow i samme repo).
   Tagget v1.0.0 og v1.0.1 med releases.
3. **Rigtig fejl fundet via dogfood:** action'en afviste gyldige rapporter hvor
   et context-felt bare manglede (fx viewport) — strengere end
   `bugbottle/server`'s normaliseContext, som tolererer fravær. Rettet i
   begge kopier, v1.0.1 + v0.2.4 tagget, 24/24 tests stadig grønne.
4. **End-to-end dogfood:** gyldig rapport → exit 0, valid-count 1; malformed →
   ::error::-linjer, exit 1; blanding → korrekt optælling. jsDelivr serverer
   v1.0.1 (200).
5. **Site:** free-tools.html peger nu på bugbottle-action-repoet; deployet og
   verificeret med curl (indhold + 200).

## Udgivelse til Marketplace — én handling for Mads
API'et understøtter det IKKE (verificeret: UI-only, Stack Overflow + docs).
Alt er forberedt så det er ét klik:
1. Åbn https://github.com/mahope/bugbottle-action/releases/tag/v1.0.1 → Edit
   (blyant) → sæt flueben i "Publish this Action to the GitHub Marketplace"
   → vælg kategori (forslag: Software quality / Continuous integration) →
   Update release.
2. Krav: Marketplace Developer Agreement skal være accepteret på mahope-kontoen
   (vises som link i samme dialog hvis mangler).

## Hvad der er verificeret virkende uden Mads
- Install: `uses: mahope/bugbottle-action@v1` VERIFICERET i rigtig CI-run
  (iter 467): flydende v1-tag manglede og er skubbet (peger på v1.0.2 =
  15b0704). Selftest-repo: gyldig rapport → success, ugyldig → failure.
  (jsDelivr 200 kræver alle dist/*.js-filer — ESM-importer; enkeltfil-load
  fejler, men browser-script-tag virker.)
- Biblioteket installeres fortsat npm-frit via github:/jsDelivr.

## Stadig blokeret på Mads
- npm publish (bugbottle registry-listing + deskuptime).
- Lemon Squeezy-nøgle.
- Marketplace-udgivelse = ét klik (se ovenfor).

## Budget: 35/1000 DKK (uændret)

---

# Iteration 442 — Page Profile Pro v1.1.0 (bygget, testet, live)

- page-profile/page_profile.py: +compare, +batch (+urls-from-file), +html-report,
  +history (gratis), offline licens (--activate / --gen-key / PAGE_PROFILE_LICENSE env).
  Låste features: pæn besked + exit 2. Historik: ~/.page-profile-history.json (max 500).
- site/downloads/page-profile/: ny tarball 1.1.0 + opdateret single-file; 1.0.0 fjernet.
- site/page-profile.html + da/: v1.1.0, Pro-kortet matcher virkende features,
  CHECKOUT_URL_PLACEHOLDER klar til LS-checkout.
- Testet lokalt: 9 scenarier (se STATUS.md). Verificeret live med curl: alle 4
  download-/side-URLs 200, indhold viser v1.1.0.
