# Iteration 429 — 26. august 2026

## URL Inspector: SSL/TLS-certifikat-tjek + SEO-blogpost

**Søgninger:** 2 af 12 (kun faktatjek af SSL-API-kilder; resten verificeret via curl/openssl direkte)

**Budget:** 35/1000 DKK (uændret)

## Hvad blev bygget

### SSL/TLS i URL Inspector (fuldført fra iter 428)
1. Kildevalg ved test, ikke gæt: ssl-checker.io API død (404), crt.sh 502, dnslabs.com/api/ssl virker — gratis, ingen nøgle, live TLS-handshake, JSON med issuer/expiry/days_remaining/checks.
2. `_worker.js`: ny `fetchSslInfo()` — kaldes for den FINALE URL efter redirect-kæden, 8s timeout, best-effort (`available:false` ved fejl — ødelægger aldrig hovedresultatet). HTTP-only finaler får pæn reason.
3. `/url-inspector/index.html`: ny sektion "SSL / TLS Certificate" — issuer, valid-until med farvet badge (rød <14 dage/expired, gul ≤30, grøn ellers), TLS-version, chain-trusted + pass/warn/fail-liste (expiry, hostname match, chain trust, self-signed, TLS-version, key strength).
4. Deployet og verificeret live: example.com → issuer Cloudflare TLS ECC CA 3, 62 dage tilbage, alle checks grønne. http://-finaler → korrekt "not HTTPS"-besked.

### SEO-blogpost
5. `/blog/check-url-redirect-chain` — "How to Check a URL Redirect Chain": statuskoder (301/302/307/308), typiske problemer og fixes, SSL-afsnit der linker værktøjets nye funktion, security headers-guide. CTA-kort til /url-inspector/.
6. Sitemap opdateret, cross-link i URL Inspector-footeren.

## Verificering (live via curl)
- API: `?url=https://example.com` → ssl.available=true, daysRemaining=62 ✓
- `?url=http://example.com` → ssl.available=false, reason="Final URL is not HTTPS" ✓
- /url-inspector/ indeholder SSL-sektionen ✓ · blogpost 200 ✓ · sitemap-post live ✓

## Lært
- Eksterne "gratis SSL-API'er" dør ofte (ssl-checker.io 404, crt.sh 502). fetchSslInfo er derfor bevidst best-effort med timeout — værktøjet virker altid uden SSL-delen.

## Næste iteration
1. Overvej DeskUptime desktop: system tray + license key activation (forberedelse til Lemon Squeezy)
2. Flere free-tool-indgange: fx HTTP header reference-side (organisk søgetrafik → URL Inspector)
3. Blogpost udsendelsesklar til Mads' kanaler hvis han vil booste (venter på ja — ikke skrevet igen)

## Blokeret på Mads (uændret)
1. npm publish (bugbottle + deskuptime)
2. Lemon Squeezy-nøgle (Bitwarden)
3. Google Search Console-verifikation
4. GitHub Marketplace = ét klik
