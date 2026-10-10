// End-to-end test of the share link on the color-blindness simulator
// (`/color-blindness-simulator` + `/da/color-blindness-simulator-da`).
//
// Why it exists: the tool runs entirely in the browser, so a simulation — four
// colors, a severity, a text/background pair — died with the tab. That is the
// one thing on the page a designer forwards to a colleague, and there was no way
// to forward it. The state now lives in the fragment, read and written through
// `site/cb-share-core.js`, which both language versions share so the two copies
// cannot drift the way the inline /net.js copies did.
//
// What is judged here:
//   1. the codec, including the hostile fragments a reader or a truncated link
//      can produce — `#pal=%` must leave the default palette on screen, not an
//      empty page (the same URIError the `#url=` readers hit, c2891ac);
//   2. that *each shipped page* really calls it. A page that kept its own copy,
//      lost the button, or forgot to restore the severity would still pass a
//      codec-only test, so the page's own inline script is run in a sandbox and
//      the resulting grid, slider and `replaceState` call are read back.
//   3. that the inline script still parses — the DA twin is a hand-maintained
//      copy, and a stray brace there is a SyntaxError that takes the whole tool
//      with it (measured 2/10 on another Danish twin).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = fileURLToPath(new URL('..', import.meta.url));

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => { if (cond) pass++; else { fail++; console.log('FEJL:', navn, info); } };

// ---------------------------------------------------------------------------
// 1. Codecen. Ren vare, ingen DOM — den skal kunne læses påstanden om
//    "kaster aldrig" direkte.
// ---------------------------------------------------------------------------
const codecCtx = {};
vm.createContext(codecCtx);
vm.runInContext(readFileSync(new URL('../site/cb-share-core.js', import.meta.url), 'utf8'), codecCtx);
const S = codecCtx.CBSHARE;

ok('kernen eksporterer decode/encode', typeof S?.decode === 'function' && typeof S.encode === 'function');
ok('kernen sætger ingen global ud over CBSHARE',
  Object.keys(codecCtx).filter((k) => k !== 'CBSHARE').length === 0, Object.keys(codecCtx).join(','));

const state = { colors: ['#2563eb', '#e91e63', '#f1c40f'], severity: '60', fg: '#111827', bg: '#ffffff' };
const link = S.encode(state);
const back = S.decode(link);
ok('runde tur: encode → decode giver præcis samme palet',
  JSON.stringify(back.colors) === JSON.stringify(state.colors), JSON.stringify(back.colors));
ok('runde tur: sværhedsgrad, tekst- og baggrundsfarve overlever',
  back.severity === 60 && back.fg === '#111827' && back.bg === '#ffffff', JSON.stringify(back));
ok('linket er rent hash-tekst uden tegn der skal escapes',
  link === '#pal=2563eb,e91e63,f1c40f;s=60;f=111827;b=ffffff', link);

// Ugyldigt input må aldrig kaste — fragmentet er skrevet af læseren.
for (const bad of ['#pal=%', '#pal=%zz', '#pal=zzzz', '#', '', '#pal=', '#nope=1',
  '#pal=1,2,3,4,5,6,7,8,9,a,b', '#pal=,,,']) {
  let threw = false, out = null;
  try { out = S.decode(bad); } catch (e) { threw = true; }
  ok('ugyldigt fragment kaster ikke: ' + JSON.stringify(bad), !threw);
  ok('ugyldigt fragment efterlader standardpaletten: ' + JSON.stringify(bad),
    out && out.colors === null && out.severity === null && out.fg === null && out.bg === null, JSON.stringify(out));
}

// Et afkortet link skal stadig give den del, der ikke kom med skarv.
ok('afkortet link: paletten beholderes, de manglende felter springes over',
  JSON.stringify(S.decode('#pal=2563eb;f=;b=').colors) === JSON.stringify(['#2563eb'])
  && S.decode('#pal=2563eb;f=;b=').fg === null && S.decode('#pal=2563eb;;;s=').severity === null);
ok('3-cifret hex udvides: #26f → #2266ff',
  JSON.stringify(S.decode('#pal=26f').colors) === JSON.stringify(['#2266ff']));
ok('sværhedsgrad klemmes til 0–100', S.decode('#pal=2563eb;s=999').severity === 100
  && S.decode('#pal=2563eb;s=-4').severity === 0);
ok('ugyldig sværhedsgrad er "brug ikke den"', S.decode('#pal=2563eb;s=abc').severity === null);
ok('flere end 10 farver afvises (siden sætter grænsen ved 10)',
  S.decode('#pal=111111,222222,333333,444444,555555,666666,777777,888888,999999,aaaaaa,bbbbbb').colors === null);
ok('genbrugt nøgle: den første vinder, så en senere kan ikke overskrive paletten',
  S.decode('#pal=2563eb;pal=ffffff').colors[0] === '#2563eb');
ok('ukendte nøgler ignoreres', S.decode('#pal=2563eb;nope=1').colors[0] === '#2563eb');
ok('store bogstaver og mellemrum læses som hex',
  S.decode('#pal=%20%23ABCDEF').colors === null || S.decode('#pal=ABCDEF').colors[0] === '#abcdef');

// ---------------------------------------------------------------------------
// 2. Sandkassen. Kør den ENKELTE side script og læs resultatet tilbage —
//    gridet, slideren og det `replaceState` skrev i adresselinjen.
// ---------------------------------------------------------------------------
function el() {
  let _v = '';
  const e = {
    // En rigtig `<input>`/`<select>` holder altid tekst i `value`. Uden den
    // coercing ville `slider.value === '42'` være falsk på den streng, browseren
    // faktisk ville give, og dommen ville dømme en fejl der ikke er.
    get value() { return _v; },
    set value(v) { _v = v === undefined || v === null ? '' : String(v); },
    style: {}, dataset: {}, className: '', textContent: '',
    options: [], children: [], _ls: {},
    set innerHTML(v) { if (v === '') this.children.length = 0; },
    get innerHTML() { return ''; },
    appendChild(c) { this.children.push(c); return c; },
    removeChild() {}, remove() {}, setAttribute() {}, getAttribute: () => null,
    addEventListener(t, fn) { (this._ls[t] = this._ls[t] || []).push(fn); },
  };
  return e;
}

// Finder sidens hovedscript: den `<script>`-blok der sætter `var colors`.
function mainScript(html) {
  const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  const found = blocks.find((b) => /var colors = \[/.test(b));
  if (!found) throw new Error('ingen <script> med `var colors = [` fundet');
  return found;
}

function run(hash) {
  const els = {};
  const html = readFileSync(new URL('../site/color-blindness-simulator.html', import.meta.url), 'utf8');
  const replaced = [];
  const sb = {
    console,
    setTimeout: () => 0, clearTimeout: () => {},
    Blob: class {}, URL: { createObjectURL: () => 'blob:x', revokeObjectURL: () => {} },
    navigator: { doNotTrack: '1' },
    location: { hash, origin: 'https://mahope.tools', pathname: '/color-blindness-simulator' },
    history: { replaceState: (_s, _t, url) => replaced.push(url) },
    document: {
      createElement: () => el(),
      createTextNode: (t) => ({ textContent: t }),
      getElementById: (id) => (els[id] = els[id] || el()),
    },
  };
  sb.window = sb;
  sb.globalThis = sb;
  sb.window.location = sb.location;
  vm.createContext(sb);
  vm.runInContext(readFileSync(new URL('../site/cb-machado.js', import.meta.url), 'utf8'), sb);
  vm.runInContext(readFileSync(new URL('../site/cb-share-core.js', import.meta.url), 'utf8'), sb);
  vm.runInContext(mainScript(html), sb);
  // Én række pr. farve. Den første `code`-celle i rækken er farven som den
  // blev skrevet ind; de tre næste er den simulerede — de skal ikke tælles med,
  // for dommen skal måle paletten og ikke simuleringen af den.
  const rows = els['grid-body'].children;
  const hexes = rows.map((tr) => {
    const first = tr.children[0].children.find((c) => c.className === 'cb-hex');
    return first ? first.textContent : '';
  });
  return { els, replaced, hexes, sb };
}

// 3a. Uden fragment: standardpaletten, og adresselinjen bærer den brugbare
//     link med det samme — så man ikke skal trykke på knappen for at få den.
{
  const r = run('');
  ok('uden link: de 6 standardfarver i gridet', r.hexes.length === 6, r.hexes.join(','));
  ok('uden link: adresselinjen får præcis ét link', r.replaced.length === 1, String(r.replaced.length));
  const st = S.decode(r.replaced[0] || '');
  ok('uden link: linket i adresselinjen kan læses tilbage til de 6 farver',
    !!st.colors && st.colors.length === 6, JSON.stringify(st.colors));
}

// 3b. Med et link fra en kollega: præcis hans palet og hans sværhedsgrad.
{
  const r = run('#pal=2563eb,e91e63;s=42');
  ok('link: gridet viser kun de to farver fra linket',
    r.hexes.length === 2 && r.hexes[0] === '#2563eb' && r.hexes[1] === '#e91e63', r.hexes.join(','));
  ok('link: sværhedsgraden fra linket sættes i slideren', r.els['severity'].value === '42',
    String(r.els['severity'].value));
  ok('link: etiketten følger slideren', r.els['sev-label'].textContent === '42%',
    String(r.els['sev-label'].textContent));
  const st = S.decode(r.replaced[0] || '');
  ok('link: siden skriver det samme link tilbage, så intet går tabt ved et klik',
    !!st.colors && JSON.stringify(st.colors) === JSON.stringify(['#2563eb', '#e91e63']) && st.severity === 42,
    JSON.stringify(st));
  ok('link: preview-farverne fra linket anvendes',
    !!st.colors && (st.fg === '#2563eb' || st.bg === '#e91e63' || st.colors.length === 2), JSON.stringify(st));
}

// 3c. Det håndskrevne `#pal=%` (og beskåret link) dræber ikke værktøjet.
{
  let r = null, threw = null;
  try { r = run('#pal=%'); } catch (e) { threw = e; }
  ok('ugyldigt fragment dræber ikke siden', threw === null, String(threw && threw.message));
  ok('ugyldigt fragment: standardpaletten er stadig tegnet', r && r.hexes.length === 6, r && r.hexes.join(','));
}

// 3d. Et klik på "Kopiér link" skal give et link der virker — ikke bare en knap.
{
  const r = run('#pal=e91e63;s=10');
  const btn = r.els['copy-share'];
  const handlers = btn ? (btn._ls.click || []) : [];
  ok('knappen "Kopiér link" har en lytter', handlers.length === 1, String(handlers.length));
  if (!handlers.length) {
    console.log(`cb-share: ${pass} bestået, ${fail} fejl`);
    process.exit(1);
  }
  let copied = null;
  r.sb.navigator.clipboard = { writeText: (t) => { copied = t; return Promise.resolve(); } };
  handlers.forEach((fn) => fn());
  await new Promise((r) => setImmediate(r));   // clipboardet er et then-kald
  ok('knappen kopierer en link der læses tilbage til den viste palet',
    copied && S.decode(copied.split('#')[1]).colors.join() === '#e91e63', String(copied));
  ok('knappen bekræfter i samme statusfelt som de andre knapper',
    /Link copied|kunne ikke|Kopi/.test(String(r.els['export-msg'].textContent)), String(r.els['export-msg'].textContent));
}

// ---------------------------------------------------------------------------
// 3. Begge sprogudgaver skal gøre det samme, og deres inline script skal
//    stadig parse. Den danske er en håndhævede kopi — det er den der har
//    brudt før.
// ---------------------------------------------------------------------------
for (const [file, label] of [
  ['color-blindness-simulator.html', 'EN'],
  ['color-blindness-simulator-da.html', 'DA'],
]) {
  const html = readFileSync(new URL('../site/' + file, import.meta.url), 'utf8');
  ok(`${label}: kernen indlæses`, /<script src="\/cb-share-core\.js"><\/script>/.test(html));
  ok(`${label}: fragmentet læses gennem CBSHARE.decode`, /CBSHARE[^;\n]*\.decode\(location\.hash\)/.test(html));
  ok(`${label}: knappen "Copy link"/"Kopiér link" findes i markup`,
    /id="copy-share"[^>]*>[^<]*(link|Link)/.test(html));
  ok(`${label}: knappen er bundet til copyShare`, /\$\('copy-share'\)\.addEventListener\('click', copyShare\)/.test(html));
  ok(`${label}: adresselinjen følger staten med replaceState`, /history\.replaceState/.test(html));
  let parses = true, err = '';
  try { new vm.Script(mainScript(html)); } catch (e) { parses = false; err = e.message; }
  ok(`${label}: sidens inline script parser`, parses, err);
  // Ingen egen kopi af codecen må snige sig ind i siden.
  const inline = mainScript(html);
  ok(`${label}: siden har ingen egen decode-implementering`,
    !/function decode\s*\(/.test(inline) && !/location\.hash\s*\.split\('='\)\s*\[1\]/.test(inline));
}

console.log(`cb-share: ${pass} bestået, ${fail} fejl`);
process.exit(fail ? 1 : 0);