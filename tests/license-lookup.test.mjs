// Ende-til-ende: /license-lookup skal kunne finde en licens uden at skrive til Mads.
// Gamle kode: ingen formular, kun "skriv til support" — porten er rød.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const src = process.argv[2] || fileURLToPath(new URL('../site/license-lookup.html', import.meta.url));
const html = readFileSync(src, 'utf8');
let fails = 0;
const ok = (name, cond, info = '') => {
  if (!cond) { fails++; console.log(`FEJL ${name}${info ? ' — ' + info : ''}`); }
  else console.log(`ok ${name}`);
};
ok('siden kalder /api/license/lookup', /(?:fetch|hent)\(\s*'\/api\/license\/lookup'/.test(html));
ok('kaldet er POST', /method:\s*'POST'/.test(html));
ok('den sender de to felter serveren forlanger',
  /order_id:\s*orderId/.test(html) && /email:\s*email/.test(html));
ok('begge felter har et label med for=',
  /<label for="orderId">/.test(html) && /<label for="lookupEmail">/.test(html));
ok('etiketten er helve sætningen, ikke bare et ord', />Order reference</.test(html) && />Email you paid with</.test(html));
ok('knappen siger hvad den gør', />Show my license key</.test(html));
ok('begge felter er påkrævede', (html.match(/\brequired\b/g) || []).length >= 2);
ok('feltet har en beskrivelse for hjælp', /aria-describedby="orderIdHelp"/.test(html));
ok('et 429 er endeligt og viser serverens sætning',
  /status === 429/.test(html) && /x\.data\.error/.test(html) && /x\.status >= 500/.test(html));
ok('429-sætningen siger ikke "try again later" to gange',
  /try again later\/i\.test\(\w+\)/.test(html));
// Ét kald pr. tryk. En 5xx er forbigående, men siden prøver **ikke** igen i
// samme kørsel. Dommen lå først som en tælling af `status >= 500`, fordi der
// kun var én 5xx-gren; da blev den samme håndtering delt ud i to formularer,
// og tællingen målte antallet af formularer i stedet for adfærden. Måler nu
// den egenskab der betyder noget: ingen 5xx-gren må kalde serveren igen.
const femhundredeGrene = [...html.matchAll(/status >= 500/g)].map(m => {
  const linjer = html.slice(m.index).split('\n').slice(0, 3).join('\n');
  return linjer;
});
ok('et 5xx giver ikke et nyt kald i samme kørsel',
  femhundredeGrene.length > 0 && femhundredeGrene.every(g => !/\b(?:hent|fetch)\(/.test(g)),
  `${femhundredeGrene.length} grene`);
ok('nøglen escapes ind i DOM', /esc\(x\.data\.license_key\)/.test(html));
ok('activate_url må ikke være javascript:', html.includes('/^https?:\\/\\//i.test(activate)'));
ok('href bygges af den tjekkede værdi, ikke rå fra svaret', html.includes("esc(activate)"));
ok('livetidsnøgle siges aldrig udløber', /lifetime === true/.test(html) && /never expires/.test(html));
ok('siden peger stadig på den humane vej som sidste udfald',
  /support\@mahope\.tools/.test(html));
ok('siden siger ikke længere at man SKAL skrive til support',
  !/We send the key again, usually the same day/.test(html));

// ── Frigør en plads selv (3/10) ──────────────────────────────────────
// Før dette kunde en «Device limit reached»-fejl kun skrive til Mads, og
// siden lovede både «it is one click in the app» (de to betalte apps ringer
// stadig til Lemon Squeezy) og «we free up the seat».
ok('siden lister maskinerne på nøglen', /(?:fetch|hent)\(\s*'\/api\/license\/devices'/.test(html));
ok('siden frigør via den testede rute', /(?:fetch|hent)\(\s*'\/api\/license\/deactivate'/.test(html));
ok('nøglefeltet til frigørelsen har et label med for=',
  /<label for="seatKey">/.test(html) && /id="seatKey"/.test(html));
ok('knappen siger hvad den gør', />Show the machines on this key</.test(html));
ok('frigørelsesknappen er 44 px eller højere på mobil',
  /\.seat-list button \{ min-height: 44px; \}/.test(html));
ok('maskinens id escapes ind i DOM', /esc\(d\.device_id\)/.test(html));
ok('listen er en rigtig liste, ikke en masse knapper uden semantik',
  /<ul class="seat-list" id="seatList"/.test(html) && /<li>/.test(html));
ok('siden siger aldrig at Mads frigør pladsen',
  !/we\s+(?:will\s+)?free\s+up\s+the\s+seat/i.test(html) && !/one\s+click\s+in\s+the\s+app/i.test(html));
ok('sagen læser serverens `deactivated` før den siger noget lykkes',
  /deactivated\s*!==\s*true/.test(html));
ok('sagen melder ikke succes ved et 5xx eller et 404',
  /x\.status !== 200 \|\| !x\.data \|\| x\.data\.deactivated !== true/.test(html));
ok('datoer vises i kundens tidszone, ikke i UTC-dagen',
  /timeZone:\s*'Europe\/Copenhagen'/.test(html));
ok('listen låses under kallet, så to tryk ikke frigør to pladser',
  /b\.disabled = true/.test(html) && /b\.disabled = false/.test(html));
ok('listen genindlæses efter en frigørelse, så kunden ser den nye tilstand',
  /hent\('\/api\/license\/devices'[\s\S]{0,200}tegnMaskiner/.test(html));
ok('der er en tom-tilstand, der siger hvad kunden kan gøre',
  /not on any\s*'\s*\+\s*'machine yet/.test(html));
console.log(fails ? `\n${fails} fejl` : `\nalt grønt (${'ok'})`);
process.exit(fails ? 1 : 0);

