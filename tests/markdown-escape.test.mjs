// Escaping i de to AI-renderere: `formatAnswer()` på `/compliance-ai` (EN + DA).
//
// Baggrund (1/10): begge sider skrev modellens svar direkte i `innerHTML` med
// kun markdown-udskiftninger og *ingen* escaping:
//
//     var html = text
//       .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
//
// Svaret er modeloutput bygget af det besøgende skrev i feltet, og spørgsmålet
// er deres at skrive: `<img src=x onerror=…>` kan komme tilbage inde i svaret og
// blive til levende markup på mahope.tools — samme origin som licensnøglerne i
// localStorage. Selve fejlen er *vasken*, ikke endpointet: modellen svarer på det
// den får, og en bruger skal kunne skrive «<» i et spørgsmål uden at det
// betyder script på vores domæne.
//
// Rettelsen er samme rækkefølge som `fmt()` i `site/book-ai.js` allerede bruger
// på det samme endpoint: escape FØRST, og tilføj så vores egne tags. Escape bagefter
// ville æde de `<strong>`/`<li>` vi vil have stående.
//
// Testen dømmer adfærd, ikke tekst: `formatAnswer` hives ud af de bytes der
// faktisk ships og køres i en vm, så den kan ikke reddes ved at omdøbe
// funktionen. Den måles mod de samme fjendtlige strenge på begge sprog.
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = fileURLToPath(new URL('..', import.meta.url));

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => {
  if (cond) pass++;
  else { fail++; console.log('FEJL:', navn, info); }
};

// --------------------------------------------------------------------------
// Udtrækker `formatAnswer` ud af sidens inline-script.
// --------------------------------------------------------------------------
// Klammerne tælles naivt. Det er forsædeligt her, fordi funktionen hverken
// har en klamme i en streng eller i en regex — og hvis en fremtidig udgave får
// det, fejler testen højt i stedet for at dømme noget forkert.
function formatAnswerFrom(source, label) {
  const start = source.indexOf('function formatAnswer(');
  if (start < 0) throw new Error(`formatAnswer ikke fundet i ${label}`);
  let depth = 0, seen = false;
  for (let i = source.indexOf('{', start); i < source.length; i++) {
    if (source[i] === '{') { depth++; seen = true; }
    else if (source[i] === '}' && --depth === 0 && seen) return source.slice(start, i + 1);
  }
  throw new Error(`formatAnswer er ikke afsluttet i ${label}`);
}

function loadFormatAnswer(path) {
  const rel = path;
  const src = formatAnswerFrom(readFileSync(join(root, rel), 'utf8'), rel);
  const ctx = { String, Array, RegExp };
  vm.createContext(ctx);
  vm.runInContext(src + '\n; formatAnswer', ctx, { filename: rel });
  return ctx.formatAnswer;
}

// Det samme sæt strenge på begge sprog: en renderer der kun escaper på dansk
// ville være grøn her, fordi den danske indgang ikke blev prøvet.
const HOSTILE = [
  ['img/onerror', '<img src=x onerror=alert(1)>'],
  ['script-tag', '<script>alert(1)</script>'],
  ['svg/onload', '<svg onload=alert(1)>'],
  ['iframe', '<iframe src=javascript:alert(1)>'],
  ['bold uden omkringt ondskab', '**<img src=x onerror=alert(1)>**'],
  ['listepunkt', '- <img src=x onerror=alert(1)>'],
  ['nummereret punkt', '1. <img src=x onerror=alert(1)>'],
  ['afsluttende tag alene', 'text </p><img src=x onerror=alert(1)>'],
  ['store bogstaver', '<IMG SRC=x ONERROR=alert(1)>'],
];

// En "levende tag" er alt der står tilbage, når de tags *vi* tilføjer er fjernet.
// Det er den præcise dom: substring-søgning på `onerror` ville være rød på helt
// korrekt output, fordi `onerror=alert(1)` godt må stå som tekst — escaped tekst
// er tekst, ikke et attribut.
const VORES_TAGS = /<\/?(?:strong|em|ul|ol|li|p)(?:\s+class="disclaimer")?>/g;
const levendeTags = (html) => html.replace(VORES_TAGS, '').match(/<[^>]*>/g) || [];

const PAGES = [
  ['EN', 'site/compliance-ai.html'],
  ['DA', 'site/da/compliance-ai.html'],
];

for (const [lang, path] of PAGES) {
  const formatAnswer = loadFormatAnswer(path);

  for (const [navn, input] of HOSTILE) {
    const html = formatAnswer(input);
    const levende = levendeTags(html);
    ok(`${lang}: ${navn} kan ikke blive levende markup`, levende.length === 0,
      levende.join(' ') + ` -> ${html}`);
  }

  ok(`${lang}: teksten er escaped, ikke bare fjernet`,
    formatAnswer('<b>x</b>').includes('&lt;b&gt;'), formatAnswer('<b>x</b>'));

  // Escaping må heller ikke ødelægge almindelig tekst. `onmouseover=…` uden
  // `<` er ikke en vektor, så det skal stå i svaret præcis som skrevet.
  ok(`${lang}: almindelig tekst står uændret`,
    formatAnswer('Prisen er 5 kr. onmouseover=1 og 100 %').includes('Prisen er 5 kr. onmouseover=1 og 100 %'),
    formatAnswer('Prisen er 5 kr. onmouseover=1 og 100 %'));

  // Escaping må ikke slå markdown ihjel — ellers kunne "rettelsen" være at
  // stoppe med at formatere, og svaret så ud som én linje rå tekst.
  ok(`${lang}: fed skrift virker stadig`, formatAnswer('**fet**').includes('<strong>fet</strong>'),
    formatAnswer('**fet**'));
  ok(`${lang}: kursive virker stadig`, formatAnswer('*kursiv*').includes('<em>kursiv</em>'),
    formatAnswer('*kursiv*'));
  ok(`${lang}: punktlister virker stadig`,
    formatAnswer('- en\n- to').includes('<ul><li>en</li><li>to</li></ul>'),
    formatAnswer('- en\n- to'));
  ok(`${lang}: nummererede lister virker stadig`,
    formatAnswer('1. en\n2. to').includes('<ol><li>en</li><li>to</li></ol>'),
    formatAnswer('1. en\n2. to'));
  ok(`${lang}: afsnit virker stadig`, formatAnswer('a\n\nb').includes('<p>a</p><p>b</p>'),
    formatAnswer('a\n\nb'));

  // `&` skal escapes FØRST. Escape bagefter ville lave `&lt;` om til
  // `&amp;lt;`, og brugeren ville se den rå markup i stedet for teksten.
  ok(`${lang}: ampersand escapes til netop én enhed`,
    formatAnswer('a & b').includes('a &amp; b') && !formatAnswer('a & b').includes('&amp;amp;'),
    formatAnswer('a & b'));
  ok(`${lang}: en allerede escaped enhed vises sådan som skrevet`,
    formatAnswer('&lt;b&gt;').includes('&amp;lt;b&amp;gt;'), formatAnswer('&lt;b&gt;'));

  // Ansvarsfraskrivelsen er en del af produktet: den skal stadig komme med,
  // og den må ikke sættes på to gange når svaret selv har den.
  const med = formatAnswer('Kort svar.');
  ok(`${lang}: ansvarsfraskrivelsen følger med`, med.includes('class="disclaimer"'), med);
  const medSelv = formatAnswer(lang === 'EN'
    ? 'General guidance, not legal advice.'
    : 'Generel vejledning, ikke juridisk rådgivning.');
  ok(`${lang}: ansvarsfraskrivelsen sættes ikke på to gange`,
    (medSelv.match(/class="disclaimer"/g) || []).length === 0, medSelv);
}

// --------------------------------------------------------------------------
// Mutation: den samme dømning mod koden fra før rettelsen.
// --------------------------------------------------------------------------
// Beviser at dommene ovenfor har tænder. Uden denne ville en test der bare
// læser filen være grøn uden at have dømt noget.
const FØR_RETTELSEN = '22a6d02';
let mutationFund = 0, mutationKontroller = 0;

for (const [lang, path] of PAGES) {
  let gammel;
  try {
    gammel = formatAnswerFrom(
      execFileSync('git', ['show', `${FØR_RETTELSEN}:${path}`], { cwd: root, maxBuffer: 1 << 26 }).toString('utf8'),
      `${FØR_RETTELSEN}:${path}`);
  } catch (e) {
    ok(`mutation: den gamle ${lang}-kode kan hentes fra git`, false, String(e.message).slice(0, 120));
    continue;
  }
  const ctx = { String, Array, RegExp };
  vm.createContext(ctx);
  vm.runInContext(gammel + '\n; formatAnswer', ctx, { filename: `foer-${path}` });
  const foraeldet = ctx.formatAnswer;
  for (const [, input] of HOSTILE) {
    const html = foraeldet(input);
    mutationKontroller++;
    if (levendeTags(html).length > 0) mutationFund++;
  }
}
ok('mutation: den gamle kode kan hentes fra git',
  mutationKontroller === HOSTILE.length * PAGES.length, `${mutationKontroller} kontroller`);
ok('mutation: den gamle kode giver levende markup på hver streng',
  mutationFund === mutationKontroller,
  `${mutationFund}/${mutationKontroller} fangede — resten er falske grønne domme`);

console.log(fail ? `\n${fail} fejl` : `\nmarkdown-escape: alt grønt (${pass})`);
process.exit(fail ? 1 : 0);
