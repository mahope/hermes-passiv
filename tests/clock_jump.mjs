// Kør hele stripe-worker-suiten med et ur der hopper en time hvert 30. ms.
//
// Hvorfor: `rateLimitIp` i site/_worker.js tæller i hele time-bøtter
// (`Math.floor(Date.now() / 3600000)`). En test der kører tælleren til grænsen
// bliver derfor afhængig af, hvornår den kører — og CI ramte præcis det 2/10:
// push kl. 04:59:41, timegrænsen 05:00:00, og «rapporten over grænsen giver 429
// med timegrænsen» fik 200 i stedet. Ét krydsende sekund gjorde et rødt CI-run,
// som så ud som en rigtig fejl i workeren.
//
// Eneste regel for denne fil: den skal kun skaffe uret ud af vejen, så resten af
// suiten er den der beviser noget. Hoptrinnet på 30. ms er vilkårligt — det skal
// bare ramme de sløjfer, der kører tælleren til kanten, mens de kører. Pinner
// testen sig selv (som `stopFastUr` i suiten gør), er denne kørsel grøn, og så
// er den grøn uanset hvornår den kører.
const virkeligNow = Date.now;
const start = virkeligNow();
const timebase = Math.floor(start / 3600000) * 3600000;
Date.now = () => timebase + Math.floor((virkeligNow() - start) / 30) * 3600000;

await import('./stripe-worker.test.mjs');
