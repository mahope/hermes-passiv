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
ok('siden kalder /api/license/lookup', /fetch\(\s*'\/api\/license\/lookup'/.test(html));
ok('kaldet er POST', /method:\s*'POST'/.test(html));
ok('den sender de to felter serveren forlanger',
  /order_id:\s*orderId/.test(html) && /email:\s*email/.test(html));
ok('begge felter har et label med for=',
  /<label for="orderId">/.test(html) && /<label for="lookupEmail">/.test(html));
ok('etiketten er hele sætningen, ikke bare et ord', />Order reference</.test(html) && />Email you paid with</.test(html));
ok('knappen siger hvad den gør', />Show my license key</.test(html));
ok('begge felter er påkrævede', (html.match(/\brequired\b/g) || []).length >= 2);
ok('feltet har en beskrivelse for hjælp', /aria-describedby="orderIdHelp"/.test(html));
ok('et 429 er endeligt og viser serverens sætning',
  /status === 429/.test(html) && /x\.data\.error/.test(html) && /x\.status >= 500/.test(html));
ok('429-sætningen siger ikke "try again later" to gange',
  /try again later\/i\.test\(limited\)/.test(html));
ok('et 5xx giver ikke et nyt kald i samme kørsel', (html.match(/status >= 500/g) || []).length === 1);
ok('nøglen escapes ind i DOM', /esc\(x\.data\.license_key\)/.test(html));
ok('activate_url må ikke være javascript:', html.includes('/^https?:\\/\\//i.test(activate)'));
ok('href bygges af den tjekkede værdi, ikke rå fra svaret', html.includes("esc(activate)"));
ok('livetidsnøgle siges aldrig udløber', /lifetime === true/.test(html) && /never expires/.test(html));
ok('siden peger stadig på den humane vej som sidste udfald',
  /support\@mahope\.tools/.test(html));
ok('siden siger ikke længere at man SKAL skrive til support',
  !/We send the key again, usually the same day/.test(html));
console.log(fails ? `\n${fails} fejl` : `\nalt grønt (${'ok'})`);
process.exit(fails ? 1 : 0);
