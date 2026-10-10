// Ende-til-ende: /license-lookup (EN) og /da/license-lookup (DA) skal kunne
// finde en licens, frigøre en plads og forudfylde nøglen — uden at skrive til
// Mads. Gamle kode: ingen formular, kun "skriv til support" — porten er rød.
//
// Sidens egne funktioner trækkes ud af HTML'en og køres med stubber: en dom der
// kun tæller tegn i kilden ved om en sætning *kunne* stå dér, ikke om siden
// gør hvad den lover foran kunden.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

function her(rel) {
  return fileURLToPath(new URL(rel, import.meta.url));
}

const PAGES = [
  {
    src: process.argv[2] || her('../site/license-lookup.html'),
    navn: 'EN',
    copy: {
      orderLabel: '>Order reference<',
      emailLabel: '>Email you paid with<',
      lookupBtn: '>Show my license key<',
      seatBtn: '>Show the machines on this key<',
      lifetime: 'never expires',
      emptySeats: /not on any\s*'\s*\+\s*'machine yet/,
      // Det ord som står for «frie pladser», så sætningen dømmes på sproget.
      friePladser: 'places',
    },
  },
  {
    src: her('../site/da/license-lookup.html'),
    navn: 'DA',
    copy: {
      orderLabel: '>Ordrehenvisning<',
      emailLabel: '>E-mail du betalte med<',
      lookupBtn: '>Vis min licensnøgle<',
      seatBtn: '>Vis maskinerne på denne nøgle<',
      lifetime: 'udløber aldrig',
      emptySeats: /ikke på nogen\s*'\s*\+\s*'maskine endnu/,
      friePladser: 'pladser',
    },
  },
];

let fails = 0;
const ok = (name, cond, info = '') => {
  if (!cond) { fails++; console.log(`FEJL ${name}${info ? ' — ' + info : ''}`); }
  else console.log(`ok ${name}`);
};

/** Kilde for én funktion i sidens indlejrede script, eller null. */
function extractFn(html, name) {
  const start = html.match(new RegExp(`function ${name}\\s*\\(`));
  if (!start) return null;
  let depth = 0;
  for (let i = start.index; i < html.length; i++) {
    if (html[i] === '{') depth++;
    else if (html[i] === '}') {
      depth--;
      if (depth === 0) return html.slice(start.index, i + 1);
    }
  }
  return null;
}

/**
 * Sidens `udfyldSeatKey` med stubber omkring sig: et nøglefelt, en
 * normalisering og et element der holder den fundne nøgle. Returnerer null
 * hvis funktionen ikke findes i kilden.
 */
function makeUdFyld(html) {
  const src = extractFn(html, 'udfyldSeatKey');
  if (!src) return null;
  const factory = new Function('seatKey', 'normalisér', 'document',
    `return ${src};`);
  let felt = '';
  const seatKey = {
    get value() { return felt; },
    set value(v) { felt = String(v); },
  };
  const normalisér = (k) => String(k || '').trim().toLowerCase();
  const document = {
    getElementById: (id) => (id === 'foundKey'
      ? { textContent: '  AABBccDD1234  ' }
      : null),
  };
  const fn = factory(seatKey, normalisér, document);
  return { fn, felt: () => felt };
}

/** Sidens `tegnMaskiner` med stubber omkring sig. */
function makeTegnMaskiner(html) {
  const src = extractFn(html, 'tegnMaskiner');
  if (!src) return null;
  const factory = new Function('rydSeat', 'seatList', 'seatSay', 'dato', 'esc', 'frigør',
    `return ${src};`);
  const state = { sagt: null, list: '' };
  const seatList = {
    get innerHTML() { return state.list; },
    set innerHTML(v) { state.list = String(v); },
    hidden: true,
    querySelectorAll: () => [],
  };
  const tegnMaskiner = factory(
    () => {},
    seatList,
    (s) => { state.sagt = s; },
    (v) => (v ? String(v).slice(0, 10) : null),
    (s) => String(s),
    () => {},
  );
  return { tegnMaskiner, sagt: () => state.sagt, list: () => state.list };
}

for (const page of PAGES) {
  const html = readFileSync(page.src, 'utf8');
  const c = page.copy;
  console.log(`\n--- ${page.navn}: ${page.src.split('/').pop()} ---`);

  // ── Find nøglen ───────────────────────────────────────────────────
  ok('siden kalder /api/license/lookup', /(?:fetch|hent)\(\s*'\/api\/license\/lookup'/.test(html));
  ok('kaldet er POST', /method:\s*'POST'/.test(html));
  ok('den sender de to felter serveren forlanger',
    /(?:order_id|ordrenummer):\s*orderId/.test(html) && /email:\s*email/.test(html));
  ok('begge felter har et label med for=',
    /<label for="orderId">/.test(html) && /<label for="lookupEmail">/.test(html));
  ok('etiketten er helve sætningen, ikke bare et ord',
    new RegExp(c.orderLabel).test(html) && new RegExp(c.emailLabel).test(html));
  ok('knappen siger hvad den gør', new RegExp(c.lookupBtn).test(html));
  ok('begge felter er påkrævede', (html.match(/\brequired\b/g) || []).length >= 2);
  ok('feltet har en beskrivelse for hjælp', /aria-describedby="orderIdHelp"/.test(html));
  ok('et 429 er endeligt og viser serverens sætning',
    /status === 429/.test(html) && /x\.data\.error/.test(html) && /x\.status >= 500/.test(html));
  if (page.navn === 'EN') {
    ok('429-sætningen siger ikke "try again later" to gange',
      /try again later\/i\.test\(\w+\)/.test(html));
  }
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
  ok('href bygges af den tjekkede værdi, ikke rå fra svaret', html.includes('esc(activate)'));
  ok('livetidsnøgle siges aldrig udløber',
    /lifetime === true/.test(html) && html.includes(c.lifetime));
  ok('siden peger stadig på den humane vej som sidste udfald',
    /support\@mahope\.tools/.test(html));

  // ── Frigør en plads selv (3/10) ──────────────────────────────────────
  // Før dette kunde en «Device limit reached»-fejl kun skrive til Mads, og
  // siden lovede både «it is one click in the app» (de to betalte apps ringer
  // stadig til Lemon Squeezy) og «we free up the seat».
  ok('siden lister maskinerne på nøglen', /(?:fetch|hent)\(\s*'\/api\/license\/devices'/.test(html));
  ok('siden frigør via den testede rute', /(?:fetch|hent)\(\s*'\/api\/license\/deactivate'/.test(html));
  ok('nøglefeltet til frigørelsen har et label med for=',
    /<label for="seatKey">/.test(html) && /id="seatKey"/.test(html));
  ok('knappen siger hvad den gør', new RegExp(c.seatBtn).test(html));
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
    /(?:hent|fetch)\('\/api\/license\/devices'[\s\S]{0,200}tegnMaskiner/.test(html));
  ok('der er en tom-tilstand, der siger hvad kunden kan gøre',
    c.emptySeats.test(html));

  // ── Nøglen forudfyldt i frigørelsesformularen (10/10) ────────────────
  // Kunden har lige fået nøglen vist på den samme side; hun skal ikke skrive
  // de samme 32 tegn om for at frigøre en plads. Gammel kode: et
  // `setTimeout(…, 0)` på formularens submit — timeren løb ud inden svaret
  // var kommet tilbage, så `#foundKey` ikke fandtes, og feltet forblev tomt.
  const udfyld = makeUdFyld(html);
  ok('der er en funktion der slår nøglen ind i feltet', udfyld !== null);
  if (udfyld) {
    udfyld.fn();
    ok('funktionen skriver nøglen ned og uden mellemrum',
      udfyld.felt() === 'aabbccdd1234', `feltet stod «${udfyld.felt()}»`);
  }
  // Kaldet skal stå som en ren sætning lige efter at svaret er gjort synligt.
  // Kun at finde `udfyldSeatKey();` et sted efter `out.hidden = false;` er
  // ikke nok: pakker man den i en timer, `.then()` eller en andenfunktion,
  // løber den stadig efter svaret er tegnet, og kunden skriver nøglen om.
  const mellem = html.match(/out\.hidden = false;([\s\S]{0,400}?)udfyldSeatKey\(\);/);
  ok('forudfyldningen kaldes når svaret vises, ikke på et tidspunkt senere',
    mellem !== null);
  ok('kaldet står ikke bag en timer, et løfte eller en anden funktion',
    mellem !== null
      && !/setTimeout|requestAnimationFrame|\.then\s*\(|function\s*\(|=>/.test(mellem[1]),
    mellem ? mellem[1].trim().slice(0, 120) : 'kaldet blev ikke fundet');
  // Og ingen timer må skrive i nøglefeltet overhovedet, heller ikke gennem
  // `udfyldSeatKey()` — det var den gamle fejl.
  ok('ingen timer skriver i nøglefeltet',
    !/setTimeout\([^)]*(?:seatKey\.value|udfyldSeatKey)/.test(html));

  // ── Tal i sætningen må ikke blive «undefined» (10/10) ────────────────
  // `max_devices` og `devices_in_use` er alt med i svaret i dag, men en
  // licens skrevet før felterne fandtes har dem ikke, og så stod kunden med
  // «3 af undefined maskiner i brug. NaN pladser er frie».
  const tegn = makeTegnMaskiner(html);
  ok('der er en funktion der tegner maskinlisten', tegn !== null);
  if (tegn) {
    tegn.tegnMaskiner({
      ok: true,
      max_devices: 3,
      devices_in_use: 1,
      devices: [
        { device_id: 'abc123', first_seen: '2026-01-01T00:00:00Z', last_seen: '2026-02-01T00:00:00Z' },
      ],
    }, null);
    const sagt = tegn.sagt() || '';
    ok('sætningen nævner både brug og loft',
      /1/.test(sagt) && /3/.test(sagt), sagt);
    ok('sætningen siger hvor mange pladser der er frie',
      new RegExp(`\\d+ ${c.friePladser}`).test(sagt), sagt);
    ok('intet i listen eller sætningen er `undefined` eller `NaN`',
      !/undefined|NaN/.test(sagt) && !/undefined|NaN/.test(tegn.list()), sagt);
    ok('knappen i listen siger hvilken maskine den frigør',
      /Free machine 1|Frigør maskine 1/.test(tegn.list()), tegn.list().slice(0, 120));

    tegn.tegnMaskiner({
      ok: true,
      devices: [
        { device_id: 'abc123', first_seen: '2026-01-01T00:00:00Z', last_seen: '2026-02-01T00:00:00Z' },
      ],
    }, null);
    const gammel = tegn.sagt() || '';
    ok('en nøgle uden loft- og brug-felt giver stadig en brugbar sætning',
      /1/.test(gammel) && !/undefined|NaN/.test(gammel), gammel);

    // Kun det ene felt mangler: svaret har loftet men ikke forbruget. Uden
    // faldet skrev sætningen «1 of 3 machines in use. NaN places are free».
    tegn.tegnMaskiner({
      ok: true,
      max_devices: 3,
      devices: [
        { device_id: 'abc123', first_seen: '2026-01-01T00:00:00Z', last_seen: '2026-02-01T00:00:00Z' },
      ],
    }, null);
    const halv = tegn.sagt() || '';
    ok('en nøgle med loft men uden forbrugstal giver stadig en brugbar sætning',
      !/undefined|NaN/.test(halv), halv);
    // Og den må ikke lyve om pladserne: `NaN > 0` er falsk, så en naiv
    // beregning sagde «All places are in use» om en nøgle med to pladser frie.
    ok('sætningen lyver ikke om frie pladser når forbrugstallet mangler',
      !/All places are in use|Alle pladser er i brug/.test(halv)
      && new RegExp(`\\d+ ${c.friePladser}`).test(halv), halv);
  }
}

console.log(fails ? `\n${fails} fejl` : `\nalt grønt (${'ok'})`);
process.exit(fails ? 1 : 0);
