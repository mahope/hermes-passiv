# STATUS — 26. august 2026

## Iteration 479 — Link-reparation, /privacy + /terms, menu-bar blogpar

**Budget:** 35/1000 DKK (uændret) · **Søgninger brugt: 0**

### Bygget

1. **Fuld intern link-audit** (nyt tjek over alle site/*.html): fandt **360
   doede interne links** — 12 unikke døde targets. Alle rettet:
   - 5 URL-mappings i 26 filer (gammel DA-blog-slugs der var blevet omdøbt).
   - downloads.html pegede på artefakter (1.3.0 / page-profile-1.0.0) som aldrig
     var blevet uploadet → nu til filerne der faktisk ligger i /downloads/.
   - `/privacy/` og `/terms/` blev linket fra footere men eksisterede IKKE.
2. **`/privacy/` + `/terms/` oprettet** — professionelle statiske sider der
   dækker alle produkter, Lemon Squeezy som merchant of record, ingen data-
   indsamling, 14 dages refundering. Også et krav fra extension-stores.
3. **Ny blogpar → deskuptime-funnel:**
   `/blog/macos-menu-bar-website-monitor` +
   `/da/blog/overvaag-hjemmeside-mac-menu-bar`. Article+FAQPage JSON-LD,
   hreflang-par, krydslinks til/fra iter-478-parret, sitemap 268 URL'er.

### Verificering

- Link-audit efter fix: **0 doede interne links** på hele sitet.
- Live: alle 4 nye sider 200 med korrekt titel; JSON-LD og sitemap bekræftet.
- Commit 04ac461 pushet.

### Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker AL betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).
3. GitHub Marketplace-listing for bugbottle-action: ét UI-klik for Mads.

### Næste iteration

- Gentag funnel-mønsteret på flere høj-intent queries, fx "website down checker"
  / "ping website from menu bar windows" → deskuptime.
- Overvej en DA-/EN-"terms"-tekst gennemgang når LS-nøglen kommer (pris skal stå).
