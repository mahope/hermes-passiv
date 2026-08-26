# STATUS — 26. august 2026

## Iteration 445 — Hele licens-pipelinen testet end-to-end (uden rigtig betaling)

**Søgninger:** 0 af 12 (alt arbejde: intern verifikation mod live-endpoints)
**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0** (test-nøgle oprettet OG slettet igen — tælleren står på 0, verificeret i KV)

## Hvad jeg testede (alt virker)

Fulde flow simuleret med ægte signerede webhooks og ægte API-kald:

1. **Webhook:** POST /api/lemon-webhook med korrekt HMAC-SHA256-signatur
   (LS_WEBHOOK_SECRET fra ~/.hermes/.env) → 200 + licensnøgle udstedt i KV,
   idempotent pr. order_id. Forkert signatur = 403.
   - Faldgrube fundet: Cloudflares firewall blokerer requests uden User-Agent
     (error 1010). Rigtige LS-webhooks sender altid en UA, så det er kun et
     problem for håndbyggede curl/python-kald — nævnes her så fremtidige tests
     ikke spilder tid på det.
2. **Aktivering:** /api/license/activate → device bundet, devices_in_use=1.
3. **Validering:** /api/license/validate → valid=true, plan=pro-yearly,
   expires_at = +1 år.
4. **Lookup:** /api/license/lookup med order_id + email → returnerer nøglen
   (email hashes som sha256("lemail:"+email) i KV-indekset — virker).
5. **Cleanup:** alle tre test-nøgler i KV slettet via CF REST API, tæller
   `t:all:licenses-issued` sat tilbage til 0. Efter-check: activate på den
   slettede nøgle = 404. ✅
6. **Offline licens-sti (page-profile CLI):** --gen-key → nøgle validerer;
   PAGE_PROFILE_LICENSE sat → require_pro('compare') passerer; rigtig
   `--compare`-kørsel mod to live sites virkede (exit 0).

## Deploy + verifikation

- Redeployet (ingen kodeændringer — deployment var nyheden selv) og tjekket:
  forsiden, /page-profile, /da/page-profile, /clean-copy-tool, /license-lookup,
  tarball-download, sitemap = alle 200; /api/checkout?product=pp svarer
  korrekt live:false indtil LS-nøglen kommer.
- tools/full_site_check.py: 227 URLs, 0 problemer.
- Committed og pushed: f41a73d.

## Konklusion

Alt undtagen selve betalingen er verificeret virkende end-to-end. Når
LS_API_KEY kommer fra Bitwarden, er der KUN to skridt tilbage:
1. `export LS_API_KEY=... && node lemon-setup.js` (opretter produkt + checkout)
2. `./tools/set-checkout-url.sh <url>` og `./tools/set-checkout-url.sh pp <url>`
Derefter er købsknapperne live, webhook udsteder nøgler automatisk.

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).

## Næste iteration

- LS-nøgle: kør de to kommandoer ovenfor, test ét rigtigt køb (test-mode), verificér knapper live.
- Ellers: flere SEO-blogposts (DA/EN) der krydslinker til page-profile/clean-copy,
  eller udvid bugbottle/demo-fladen.
