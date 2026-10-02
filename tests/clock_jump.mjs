// Kør hele stripe-worker-suiten med et ur der springer én time pr. kald.
//
// Hvorfor: `rateLimitIp` i site/_worker.js tæller i hele timebøtter
// (`Math.floor(Date.now() / 3600000)`), og `sentryRateLimited` har et
// glidende vindue på 12 sekunder. En løkke der kører hen over en tidsgrænse
// får derfor et svar, der afhænger af hvornår den kører: CI-pushen 2/10 kl.
// 04:59:41 ramte timegrænsen 05:00:00 midt i rapport-sløjfen og fik 200 i
// stedet for 429. Ét krydsende sekund gjorde et rødt CI-run, der så ud som en
// fejl i licenserveren.
//
// Hoptrinnet sker pr. `Request`-konstruktion, ikke pr. millisekund. Den
// tidligere version sprang en time hvert 30. ms og var dermed afhængig af
// maskinens hastighed — den gjorde præcis det den skulle (målte Sentry-
// sløjfen ved 12 rapporter i stedet for 1) *og* ramte ved et tilfælde en
// webhook-signatur, fordi uret sprang mellem signering og verifikation, hvor
// `verifyStripeSignature` har 300 sekunders tolerance. Den lavede et rødt
// CI-run kl. 06:03 2/10. Med spring pr. kald står uret stille gennem hele et
// kald, så en signering og dens verifikation altid ser samme tid, og et hop
// kan ikke ramme andet end det, porten skal ramme.
//
// Kald med en Stripe-signatur springer ikke. De er de eneste, hvor springet
// mellem to læsninger af uret betyder noget, og de er ikke tidsbøtte-tællede.
// Resten af suiten hopper én time for hvert kald, så en løkke uden fast ur
// krydser en timegrænse på *hver* iteration — målt i stedet for truffet ved
// et tilfælde. Det er den egenskab `tests/stripe-worker.test.mjs` skal have:
// hvert tællerafsnit får sit eget fast ur.
const virkeligRequest = globalThis.Request;
const timebase = Math.floor(Date.now() / 3600000) * 3600000;
let nu = timebase;
Date.now = () => nu;

globalThis.Request = class extends virkeligRequest {
  constructor(...args) {
    super(...args);
    if (!this.headers.get('stripe-signature')) nu += 3600000;
  }
};

await import('./stripe-worker.test.mjs');
