// Dommen over del-linket i paletgeneratoren (EN + DA).
//
// Generatoren kører helt i browseren og har intet serverkald, så en palet — én
// basisfarve og én sidebaggrund — døde med fanen. Det er den ene ting på siden
// en designer sender videre til en kollega, og der var ingen måde at sende den.
// Staten bor nu i fragmentet, læst og skrevet gennem `site/palette-share-core.js`,
// som begge sprogudgaver deler, så de to kopier ikke kan drive fra hinanden.
//
// Det der dømmes:
//   1. codecen, inkl. de fjendtlige fragmenter en læser eller et afkortet link
//      kan give — `#c=%` skal efterlade standardpaletten på skærmen, ikke en tom
//      side (samme URIError som `#url=`-læserne ramte, c2891ac);
//   2. at *hver shippet side* virkelig kalder den. En side der beholdt sin egen
//      kopi, mistede knappen eller glemte at gendanne baggrunden ville stadig
//      bestå en codec-only-test, så sidens eget inline-script køres i en sandkasse
//      og basisfeltet, baggrundsvælgeren og `replaceState`-kaldet læses tilbage;
//   3. at inline-scriptet stadig parser — den danske tvilling er en
//      håndvedligeholdt kopi, og en løs klamme der er en SyntaxError tager hele
//      værktøjet med sig.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => { if (cond) pass++; else { fail++; console.log('FEJL:', navn, info); } };

// ---------------------------------------------------------------------------
// 1. Codecen. Ren vare, ingen DOM.
// ---------------------------------------------------------------------------
const codecCtx = {};
vm.createContext(codecCtx);
vm.runInContext(readFileSync(new URL('../site/palette-share-core.js', import.meta.url), 'utf8'), codecCtx);
const S = codecCtx.PALETTE_SHARE;

ok('kernen eksporterer decode/encode', typeof S?.decode === 'function' && typeof S.encode === 'function');
ok('kernen sætter ingen global ud over PALETTE_SHARE',
  Object.keys(codecCtx).filter((k) => k !== 'PALETTE_SHARE').length === 0, Object.keys(codecCtx).join(','));

const state = { base: '#2563eb', bg: '#111827' };
const link = S.encode(state);
const back = S.decode(link);
ok('runde tur: encode → decode giver præcis samme basisfarve og baggrund',
  back.base === '#2563eb' && back.bg === '#111827', JSON.stringify(back));
ok('linket er ren hash-tekst uden tegn der skal escapes', link === '#c=2563eb;b=111827', link);
ok('baggrunden kan udelades (hvid er standarden)', S.encode({ base: '#2563eb' }) === '#c=2563eb',
  S.encode({ base: '#2563eb' }));

// Ugyldigt input må aldrig kaste — fragmentet er skrevet af læseren.
for (const bad of ['#c=%', '#c=%zz', '#c=zzzz', '#', '', '#c=', '#nope=1', '#c=;b=']) {
  let threw = false, out = null;
  try { out = S.decode(bad); } catch (e) { threw = true; }
  ok('ugyldigt fragment kaster ikke: ' + JSON.stringify(bad), !threw);
  ok('ugyldigt fragment efterlader standarden: ' + JSON.stringify(bad),
    out && out.base === null && out.bg === null, JSON.stringify(out));
}

ok('afkortet link: basen beholdes, den manglende baggrund springes over',
  S.decode('#c=2563eb;b=').base === '#2563eb' && S.decode('#c=2563eb;b=').bg === null);
ok('3-cifret hex udvides: #26f → #2266ff', S.decode('#c=26f').base === '#2266ff');
ok('genbrugt nøgle: den første vinder, så en senere ikke kan overskrive baggrunden',
  S.decode('#c=2563eb;b=111827;b=ffffff').bg === '#111827');
ok('ukendte nøgler ignoreres', S.decode('#c=2563eb;nope=1').base === '#2563eb');
ok('store bogstaver og mellemrum læses som hex', S.decode('#c=%20ABCDEF').base === '#abcdef');
ok('ugyldig baggrund bliver null, ikke en gætning', S.decode('#c=2563eb;b=xyz').bg === null);

// ---------------------------------------------------------------------------
// 2. Sandkassen. Kør den ENKELTE sides script og læs resultatet tilbage.
// ---------------------------------------------------------------------------
function el() {
  let _v = '';
  const e = {
    get value() { return _v; },
    set value(v) { _v = v === undefined || v === null ? '' : String(v); },
    style: { setProperty() {} }, dataset: {}, className: '', textContent: '',
    options: [], children: [], _ls: {},
    set innerHTML(v) { if (v === '') this.children.length = 0; },
    get innerHTML() { return ''; },
    appendChild(c) { this.children.push(c); return c; },
    removeChild() {}, remove() {}, setAttribute() {}, getAttribute: () => null,
    querySelector: () => el(), querySelectorAll: () => [],
    addEventListener(t, fn) { (this._ls[t] = this._ls[t] || []).push(fn); },
  };
  return e;
}

// Finder sidens hovedscript: den `<script>`-blok der definerer `buildPalette`.
function mainScript(html) {
  const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  const found = blocks.find((b) => /function buildPalette\s*\(/.test(b));
  if (!found) throw new Error('ingen <script> med `function buildPalette` fundet');
  return found;
}

function run(hash, file = 'palette-generator.html') {
  const els = {};
  // Vælgeren har fem faste baggrunde i markup; sandkassen kender dem ikke, så
  // de lægges ind på forhånd, som browseren ville have gjort.
  els['bg-select'] = el();
  els['bg-select'].options = [
    { value: '#ffffff' }, { value: '#f8fafc' }, { value: '#f5f0e8' },
    { value: '#111827' }, { value: '#000000' },
  ];
  els['bg-select'].value = '#ffffff';
  // Felterne har deres standardværdi i markup'en; sandkassen læser ikke HTML,
  // så den sættes her, præcis som browseren ville have gjort.
  els['base-text'] = el(); els['base-text'].value = '#2563eb';
  els['base-color'] = el(); els['base-color'].value = '#2563eb';
  const html = readFileSync(new URL('../site/' + file, import.meta.url), 'utf8');
  const replaced = [];
  const sb = {
    console,
    setTimeout: () => 0, clearTimeout: () => {},
    Blob: class {}, URL: { createObjectURL: () => 'blob:x', revokeObjectURL: () => {} },
    navigator: { doNotTrack: '1' },
    location: { hash, origin: 'https://mahope.tools', pathname: '/palette-generator' },
    history: { replaceState: (_s, _t, url) => replaced.push(url) },
    document: {
      createElement: () => el(),
      createTextNode: (t) => ({ textContent: t }),
      documentElement: el(),
      getElementById: (id) => (els[id] = els[id] || el()),
    },
  };
  sb.window = sb;
  sb.globalThis = sb;
  sb.window.location = sb.location;
  vm.createContext(sb);
  vm.runInContext(readFileSync(new URL('../site/palette-share-core.js', import.meta.url), 'utf8'), sb);
  vm.runInContext(mainScript(html), sb);
  return { els, replaced, sb };
}

// 3a. Uden fragment: standardpaletten, og adresselinjen bærer det brugbare link
//     med det samme — man skal ikke trykke på knappen for at få det.
{
  const r = run('');
  ok('uden link: basisfeltet står på standarden', r.els['base-text'].value === '#2563eb', r.els['base-text'].value);
  ok('uden link: adresselinjen får præcis ét link', r.replaced.length === 1, String(r.replaced.length));
  const st = S.decode(r.replaced[0] || '');
  ok('uden link: linket i adresselinjen kan læses tilbage til basen og baggrunden',
    st.base === '#2563eb' && st.bg === '#ffffff', JSON.stringify(st));
}

// 3b. Med et link fra en kollega: præcis hans basisfarve og baggrund.
{
  const r = run('#c=e91e63;b=111827');
  ok('link: basisfeltet får farven fra linket', r.els['base-text'].value === '#e91e63', r.els['base-text'].value);
  ok('link: baggrundsvælgeren vælger baggrunden fra linket', r.els['bg-select'].value === '#111827',
    r.els['bg-select'].value);
  const st = S.decode(r.replaced[0] || '');
  ok('link: siden skriver det samme link tilbage, så intet går tabt ved et klik',
    st.base === '#e91e63' && st.bg === '#111827', JSON.stringify(st));
}

// 3c. En baggrund uden for de fem faste skal stadig gendannes.
{
  const r = run('#c=2563eb;b=1a1a1a');
  ok('ukendt baggrund tilføjes som tilpasset valgmulighed og vælges',
    r.els['bg-select'].value === '#1a1a1a', r.els['bg-select'].value);
  ok('den tilpassede valgmulighed er lagt til listen',
    r.els['bg-select'].options.length === 6 || r.els['bg-select'].children.length === 1,
    String(r.els['bg-select'].options.length) + '/' + String(r.els['bg-select'].children.length));
}

// 3d. Det håndskrevne `#c=%` (og et afkortet link) dræber ikke værktøjet.
{
  let r = null, threw = null;
  try { r = run('#c=%'); } catch (e) { threw = e; }
  ok('ugyldigt fragment dræber ikke siden', threw === null, String(threw && threw.message));
  ok('ugyldigt fragment: standardbasen er stadig sat', r && r.els['base-text'].value === '#2563eb',
    r && r.els['base-text'].value);
}

// 3e. Et klik på "Copy link" skal give et link der virker — ikke bare en knap.
{
  const r = run('#c=e91e63;b=111827');
  const btn = r.els['copy-share'];
  const handlers = btn ? (btn._ls.click || []) : [];
  ok('knappen "Copy link"/"Kopiér link" har en lytter', handlers.length === 1, String(handlers.length));
  if (!handlers.length) {
    console.log(`palette-share: ${pass} bestået, ${fail} fejl`);
    process.exit(1);
  }
  let copied = null;
  r.sb.navigator.clipboard = { writeText: (t) => { copied = t; return Promise.resolve(); } };
  handlers.forEach((fn) => fn());
  await new Promise((res) => setImmediate(res));   // clipboardet er et then-kald
  const st = S.decode((copied || '').split('#')[1]);
  ok('knappen kopierer et link der læses tilbage til den viste palet',
    copied && st.base === '#e91e63' && st.bg === '#111827', String(copied));
  ok('knappen bekræfter i samme statusfelt som de andre knapper',
    /Link copied|Linket er kopieret|kunne ikke|fejlede/.test(String(r.els['export-msg'].textContent)),
    String(r.els['export-msg'].textContent));
}

// ---------------------------------------------------------------------------
// 3. Begge sprogudgaver skal gøre det samme, og deres inline script skal parse.
// ---------------------------------------------------------------------------
for (const [file, label] of [
  ['palette-generator.html', 'EN'],
  ['palette-generator-da.html', 'DA'],
]) {
  const html = readFileSync(new URL('../site/' + file, import.meta.url), 'utf8');
  ok(`${label}: kernen indlæses`, /<script src="\/palette-share-core\.js"><\/script>/.test(html));
  ok(`${label}: fragmentet læses gennem PALETTE_SHARE.decode`, /PALETTE_SHARE\.decode\(location\.hash\)/.test(html));
  ok(`${label}: knappen "Copy link"/"Kopiér link" findes i markup`,
    /id="copy-share"[^>]*>[^<]*(link|Link)/.test(html));
  ok(`${label}: knappen er bundet til copyShare`, /\$\('copy-share'\)\.addEventListener\('click', copyShare\)/.test(html));
  ok(`${label}: adresselinjen følger staten med replaceState`, /history\.replaceState/.test(html));
  let parses = true, err = '';
  try { new vm.Script(mainScript(html)); } catch (e) { parses = false; err = e.message; }
  ok(`${label}: sidens inline script parser`, parses, err);
  const inline = mainScript(html);
  ok(`${label}: siden har ingen egen decode-implementering`,
    !/function decode\s*\(/.test(inline) && !/location\.hash\s*\.split\('='\)\s*\[1\]/.test(inline));
}

console.log(`palette-share: ${pass} bestået, ${fail} fejl`);
process.exit(fail ? 1 : 0);
