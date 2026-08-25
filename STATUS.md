# STATUS — Iteration 311: v1.3.3 desktop release + SEO blog post + CI-trigger fix

## Resultat

**v1.3.3 release** — alle 8 assets bygget og live:

- macOS: ARM64 DMG + ZIP, Intel DMG + ZIP (4)
- Linux: AppImage + .deb (2)
- Windows: NSIS installer + portable .exe (2)

**Versions mismatch rettet.** package.json, main.js, og index.html havde alle forskellige versioner (1.3.1, 1.3.0, 1.3.0). Nu 1.3.3 gennem hele stacken.

**CI-trigger fix.** GitHub Actions deduplicerer SHA's — når tag push har samme SHA som main push, kører CI kun én gang (for main). Løsning: fjern `branches: [main]` fra tag-triggeren, så CI kun kører på tag pushes.

**SEO blog post.** Ny guide live: "EAA Compliance Scanner Desktop — Free, Offline WCAG 2.1 AA Scanner for macOS, Linux & Windows" på /blog/eaa-compliance-scanner-desktop. Schema.org TechArticle, feature-table, 22 regler, cross-platform info.

**Downloads page opdateret.** Alle 8 v1.3.3-links, Pro-badge på Linux/Windows, Pro-sektion med features/pris, source zip opdateret til 1.3.3.

## Hvad der blev rettet

1. **Version bump:** package.json 1.3.1→1.3.3, main.js VERSION 1.3.0→1.3.3, index.html badge 1.3.0→1.3.3
2. **CI tag dedup:** Fjern `branches: [main]` fra tag-trigger, fjern `release` event
3. **SEO:** Ny blog post + schema.org TechArticle om desktop app
4. **Downloads page:** v1.3.3 links, Pro-badge, Pro-sektion, source zip 1.3.3

## Fremtidig release-proces

`git tag eaa-scanner-desktop-vX.Y.Z && git push origin --tags`
→ CI bygger alle 3 platforme, opretter release, uploader assets.

## Stadig blokeret

- LS API-nøgle i Bitwarden — Mads skal logge ind
- Obsidian community-login — Mads skal submitte
- CWS OAuth-credentials — Mads

## Målinger

- Waitlist: 3 (1 ægte lead)
- Trafik: ~5-8 besøg/dag
- Compliance scans: 0 reelle
- Licenser udstedt: 0 (LS nøgle mangler)

## Budget: 35 kr brugt af 1000 (uændret)

## Næste iteration

- Sitemap: tilføj bloggens desktop-artikel til sitemap.xml
- Internt links: link til bloggen fra /downloads og /scan
- Overvej npm publish af eaa-scanner CLI for at drive download-trafik