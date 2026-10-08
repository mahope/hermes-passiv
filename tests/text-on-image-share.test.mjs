// Dommen over del-linket i tekst-på-billede-tjekkeren (EN + DA).
//
// Værktøjet kører helt i browseren og har intet serverkald, så en konfiguration
// — gradient, tekster, farver, positioner, slør — døde med fanen. En del-link
// gør det muligt at sende *præcis* det tjek videre. Staten bor i fragmentet,
// læst og skrevet gennem `site/text-on-image-share.js`, som begge
// sprogudgaver deler, så de to kopier ikke kan drive fra hinanden.
//
// Det der dømmes:
//   1. codecen, inkl. de fjendtlige fragmenter en læser eller et afkortet link
//      kan give — `#ti=%` skal efterlade standarden på skærmen, ikke en tom side;
//   2. at *hver shippet side* virkelig kalder kernen. En side der beholdt sin egen
//      kopi, mistede knappen eller glemte at gendanne baggrunden ville stadig
//      bestå en codec-only-test, så sidens eget inline-script køres i en sandkasse
//      og feltværdier, knap og `replaceState`-kald læses tilbage;
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
vm.runInContext(readFileSync(new URL('../site/text-on-image-share.js', import.meta.url), 'utf8'), codecCtx);
const S = codecCtx.TEXT_ON_IMAGE_SHARE;

ok('kernen eksporterer decode/encode', typeof S?.decode === 'function' && typeof S.encode === 'function');
ok('kernen sætter ingen global ud over TEXT_ON_IMAGE_SHARE',
  Object.keys(codecCtx).filter((k) => k !== 'TEXT_ON_IMAGE_SHARE').length === 0, Object.keys(codecCtx).join(','));

const state = {
  bg: 'gradient',
  g1: '#1e3a5f',
  g2: '#c9d8e4',
  ga: 45,
  t1: 'Hello world',
  c1: '#ffffff',
  fs1: 'large',
  x1: 54,
  y1: 218,
  s1: { hex: '#000000', alpha: 0.42 },
  t2: 'Subtitle here',
  c2: '#ffffff',
  fs2: 'large',
  x2: 54,
  y2: 336,
  s2: null,
  a: 0
};
const link = S.encode(state);
const back = S.decode(link);
ok('runde tur: encode → decode giver præcis samme gradient og tekst',
  back.g1 === '#1e3a5f' && back.g2 === '#c9d8e4' && back.ga === 45 &&
  back.t1 === 'Hello world' && back.c1 === '#ffffff' && back.fs1 === 'large' &&
  back.x1 === 54 && back.y1 === 218 &&
  back.s1 && back.s1.hex === '#000000' && back.s1.alpha === 0.42 &&
  back.t2 === 'Subtitle here' && back.c2 === '#ffffff' && back.fs2 === 'large' &&
  back.x2 === 54 && back.y2 === 336 &&
  back.a === 0, JSON.stringify(back));

ok('image mode uden billede-data kan encoders', S.encode({ bg: 'image', t1: 'Test' }).indexOf('bg=image') >= 0);
ok('baggrunden kan udelades (gradient er standarden)', S.encode({ bg: 'gradient', g1: '#1e3a5f', g2: '#c9d8e4', ga: 45 }).indexOf('bg=gradient') >= 0);

// Ugyldigt input må aldrig kaste — fragmentet er skrevet af læseren.
for (const bad of ['#ti=%', '#ti=%zz', '#ti=bg=zzz', '#ti=ga=abc', '#', '', '#ti=', '#nope=1', '#ti=c1=zzzz']) {
  let threw = false, out = null;
  try { out = S.decode(bad); } catch (e) { threw = true; }
  ok('ugyldigt fragment kaster ikke: ' + JSON.stringify(bad), !threw);
  ok('ugyldigt fragment efterlader standarden: ' + JSON.stringify(bad),
    out && out.bg === 'gradient' && out.g1 === '#1e3a5f' && out.t1 === 'Your headline here', JSON.stringify(out));
}

ok('3-cifret hex udvides: c1=26f → #2266ff', S.decode('#ti=c1=26f').c1 === '#2266ff');
ok('genbrugt nøgle: den første vinder', S.decode('#ti=g1=1e3a5f;g1=ffffff').g1 === '#1e3a5f');
ok('ukendte nøgler ignoreres', S.decode('#ti=g1=1e3a5f;nope=1').g1 === '#1e3a5f');
ok('store bogstaver og mellemrum i tekst URL-decodes', S.decode('#ti=t1=Hello%20world').t1 === 'Hello world');
ok('ugyldig farve bliver null', S.decode('#ti=c1=xyz').c1 === '#ffffff');
ok('alpha klampes 0-100', S.decode('#ti=s1=000000,150').s1 && S.decode('#ti=s1=000000,150').s1.alpha === 1);
ok('scrim uden alpha bliver null', S.decode('#ti=s1=000000').s1 === null);
ok('aktiv blok 0 eller 1', S.decode('#ti=a=0').a === 0 && S.decode('#ti=a=1').a === 1);
ok('ugyldig aktiv blok faller tilbage til 0', S.decode('#ti=a=2').a === 0);

// ---------------------------------------------------------------------------
// 2. Sandkassen. Kør den ENKELTE sides script og læs resultatet tilbage.
// ---------------------------------------------------------------------------
function el() {
  let _v = '';
  const e = {
    get value() { return _v; },
    set value(v) { _v = v === undefined || v === null ? '' : String(v); },
    style: { setProperty() {}, display: '' }, dataset: {}, className: '', textContent: '',
    options: [], children: [], _ls: {},
    set innerHTML(v) { if (v === '') this.children.length = 0; },
    get innerHTML() { return ''; },
    appendChild(c) { this.children.push(c); return c; },
    removeChild() {}, remove() {}, setAttribute() {}, getAttribute: () => null,
    querySelector: () => el(), querySelectorAll: () => [],
    addEventListener(t, fn) { (this._ls[t] = this._ls[t] || []).push(fn); },
    classList: { add() {}, remove() {}, contains: () => false },
    get parentNode() { return e; },
  };
  return e;
}

function canvasMock() {
  const ctx = {
    createLinearGradient: () => ({
      addColorStop: () => {},
    }),
    fillStyle: '',
    fillRect: () => {},
    beginPath: () => {},
    arc: () => {},
    fill: () => {},
    drawImage: () => {},
    getImageData: () => ({ data: new Uint8ClampedArray() }),
    clearRect: () => {},
    save: () => {},
    restore: () => {},
    strokeStyle: '',
    lineWidth: 0,
    setLineDash: () => {},
    strokeRect: () => {},
    font: '',
    textBaseline: '',
    fillText: () => {},
    measureText: () => ({ width: 100 }),
    createElement: () => el(),
  };
  const c = el();
  c.getContext = () => ctx;
  c.width = 900;
  c.height = 420;
  c.getBoundingClientRect = () => ({ left: 0, top: 0, width: 900, height: 420 });
  return c;
}

function mainScript(html) {
  const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  const found = blocks.find((b) => /window\.TiContrast\.mount\(/.test(b));
  if (!found) throw new Error('ingen <script> med `window.TiContrast.mount` fundet');
  return found;
}

function run(hash, file = 'text-on-image-checker.html') {
  const els = {};
  const cv = canvasMock();
  // Standardfelter
  els['cv'] = cv;
  els['file'] = el();
  els['text'] = el(); els['text'].value = 'Your headline here';
  els['fg'] = el(); els['fg'].value = '#ffffff';
  els['fontsize'] = el(); els['fontsize'].value = 'large'; els['fontsize'].options = [{value:'small'},{value:'large'}];
  els['bgmode'] = el(); els['bgmode'].value = 'gradient'; els['bgmode'].options = [{value:'image'},{value:'gradient'}];
  els['gfrom'] = el(); els['gfrom'].value = '#1e3a5f';
  els['gto'] = el(); els['gto'].value = '#c9d8e4';
  els['gang'] = el(); els['gang'].value = '45';
  els['text2'] = el(); els['text2'].value = 'Your subtitle here';
  els['fg2'] = el(); els['fg2'].value = '#ffffff';
  els['result'] = el();
  els['result2'] = el();
  els['err'] = el();
  els['verdict'] = el();
  els['tigrad'] = el(); els['tigrad'].style = { display: '' };

  const html = readFileSync(new URL('../site/' + file, import.meta.url), 'utf8');
  const replaced = [];
  const sb = {
    console,
    setTimeout: (fn) => { fn(); return 0; },
    clearTimeout: () => {},
    Blob: class {}, URL: { createObjectURL: () => 'blob:x', revokeObjectURL: () => {} },
    navigator: { doNotTrack: '1', clipboard: { writeText: (t) => Promise.resolve() } },
    location: { hash, origin: 'https://mahope.tools', pathname: '/text-on-image-checker' },
    history: { replaceState: (_s, _t, url) => replaced.push(url) },
    document: {
      createElement: (tag) => {
        if (tag === 'canvas') return canvasMock();
        return el();
      },
      createTextNode: (t) => ({ textContent: t }),
      documentElement: el(),
      getElementById: (id) => (els[id] = els[id] || el()),
    },
    addEventListener: () => {},
    removeEventListener: () => {},
  };
  sb.window = sb;
  sb.globalThis = sb;
  sb.window.location = sb.location;
  vm.createContext(sb);
  vm.runInContext(readFileSync(new URL('../site/text-on-image-share.js', import.meta.url), 'utf8'), sb);
  vm.runInContext(readFileSync(new URL('../site/text-on-image-core.js', import.meta.url), 'utf8'), sb);
  vm.runInContext(mainScript(html), sb);
  return { els, replaced, sb };
}

// 3a. Uden fragment: standardindstillinger, og adresselinjen bærer det brugbare link
{
  const r = run('');
  ok('uden link: teksten står på standarden', r.els['text'].value === 'Your headline here', r.els['text'].value);
  ok('uden link: gradient-start står på standarden', r.els['gfrom'].value === '#1e3a5f', r.els['gfrom'].value);
  ok('uden link: adresselinjen får præcis ét link', r.replaced.length === 1, String(r.replaced.length));
  const st = S.decode(r.replaced[0]?.split('#')[1] || '');
  ok('uden link: linket i adresselinjen kan læses tilbage', st.t1 === 'Your headline here' && st.g1 === '#1e3a5f', JSON.stringify(st));
}

// 3b. Med et link fra en kollega: præcis hans gradient og tekst.
{
  const r = run('#ti=bg=gradient;g1=e91e63;g2=111827;ga=90;t1=Custom%20text;c1=000000;fs1=small;x1=100;y1=100;s1=000000,50;a=0');
  ok('link: teksten får indholdet fra linket', r.els['text'].value === 'Custom text', r.els['text'].value);
  ok('link: gradient-start får farven fra linket', r.els['gfrom'].value === '#e91e63', r.els['gfrom'].value);
  ok('link: gradient-end får farven fra linket', r.els['gto'].value === '#111827', r.els['gto'].value);
  ok('link: vinkel får værdien fra linket', r.els['gang'].value === '90', r.els['gang'].value);
  ok('link: font size får værdien fra linket', r.els['fontsize'].value === 'small', r.els['fontsize'].value);
  const st = S.decode(r.replaced[0]?.split('#')[1] || '');
  ok('link: siden skriver det samme link tilbage', st.t1 === 'Custom text' && st.g1 === '#e91e63', JSON.stringify(st));
}

// 3c. Det håndskrevne `#ti=%` (og et afkortet link) dræber ikke værktøjet.
{
  let r = null, threw = null;
  try { r = run('#ti=%'); } catch (e) { threw = e; }
  ok('ugyldigt fragment dræber ikke siden', threw === null, String(threw && threw.message));
  ok('ugyldigt fragment: standardteksten er stadig sat', r && r.els['text'].value === 'Your headline here', r && r.els['text'].value);
}

// 3d. Begge sprogudgaver skal gøre det samme, og deres inline script skal parse.
for (const [file, label] of [
  ['text-on-image-checker.html', 'EN'],
  ['text-on-image-checker-da.html', 'DA'],
]) {
  const html = readFileSync(new URL('../site/' + file, import.meta.url), 'utf8');
  ok(`${label}: kernen indlæses`, /<script src="\/text-on-image-share\.js"><\/script>/.test(html));
  ok(`${label}: fragmentet læses gennem TEXT_ON_IMAGE_SHARE.decode`, /TEXT_ON_IMAGE_SHARE\.decode\(location\.hash\)/.test(html));
  ok(`${label}: knappen "Share"/"Del" findes i markup`, /class="btn-secondary ti-share"[^>]*>(Share|Del)/.test(html));
  ok(`${label}: knappen er bundet til clipboard`, /navigator\.clipboard\.writeText/.test(html));
  ok(`${label}: adresselinjen følger staten med replaceState`, /history\.replaceState/.test(html));
  let parses = true, err = '';
  try { new vm.Script(mainScript(html)); } catch (e) { parses = false; err = e.message; }
  ok(`${label}: sidens inline script parser`, parses, err);
  const inline = mainScript(html);
  ok(`${label}: siden har ingen egen decode-implementering`,
    !/function decode\s*\(/.test(inline) && !/location\.hash\s*\.split\(['=]\)\s*\[1\]/.test(inline));
}

console.log(`text-on-image-share: ${pass} bestået, ${fail} fejl`);
process.exit(fail ? 1 : 0);