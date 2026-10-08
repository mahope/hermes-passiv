// Dommen over eaa-scannerens GitHub Action og det workflow vi sender ud.
//
// Baggrund (8/10): udviklere scanner allerede med CLI'en (@mahope/eucomply-
// scanner har 91 npm-downloads/uge — den stærkeste adoption vi har), men der
// fandtes ingen action: kunden kopierede et workflow fra /downloads. Samtidig
// viste målingen to reelle fejl i CLI'en, som handlen afslørede:
//
//   1. `--sarif` skrev rapporten til stdout EFTER fail-on-dommen. En CI-kørsel
//      med fund forlod jobbet med exit 1 uden at skrive SARIF — altså præcis de
//      kørsler hvor Security-taben har mest brug for at se fundene.
//   2. `--fail-on never` stod i shippede workflows kommentar
//      (`FAIL_ON warning | error | never`), men CLI'en afviste det med exit 2.
//      En indstilling der ser gyldig ud og fejler med det samme.
//
// Derudover var en side der ikke kunne hentes usynlig i SARIF: rapporterne
// tæller kun fund, så en død URL stod i Security-taben som "ingen resultater".
//
// Testen dømmer fire lag:
//   A. `action.yml` er en komplet composite-action (install → scan → upload →
//      dom), og skriver rapporten før den dømmer.
//   B. Det workflow vi sender ud til kunderne har SARIF + upload-sarif og
//      skrive-rettighed til Security-taben.
//   C. Siden der sælger det (site/downloads.html) forklarer alle tre dele.
//   D. CLI'ens adfærd køres for rigtigt: rapport skrevet ved exit 1, `never`
//      accepteret, en uhentet side er et SARIF-fund, en forkert værdi afvist.
//
// Mutationerne til sidst er beviset for at lag A–D kan gå rød: hver mutation
// skrives til en kopi af den shippede CLI, og den pågældende dom skal være RØD
// på kopien. En mutation ingen dom kan se, er en test der ikke dømmer.
//
// Kør:  node tests/eaa-action.test.mjs               (alt)
//       node tests/eaa-action.test.mjs --self-test   (kun mutationerne)
import { readFileSync, writeFileSync, unlinkSync, mkdtempSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));
const CLI = join(root, 'scanner/npm/eaa-scanner/cli.js');
const ACTION = join(root, 'action.yml');
const WORKFLOW = join(root, 'site/downloads/eaa-scan-github-action.yml');
const DOCS = join(root, 'site/downloads.html');

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => {
  if (cond) pass++;
  else { fail++; console.log('FEJL:', navn, info); }
};

const read = (p) => readFileSync(p, 'utf8');

// En side med ét fejl-fund (IMG_ALT) og én advarsel (VIEWPORT) — nok til at
// trykke både error- og warning-grænsen.
const SCRATCH = mkdtempSync(join(tmpdir(), 'eaa-action-'));
const PAGE = join(SCRATCH, 'page.html');
writeFileSync(PAGE, '<!doctype html><html lang="en"><head><title>t</title></head>'
  + '<body><h1>H</h1><img src="a.png"></body></html>\n');
const MISSING = join(SCRATCH, 'findes-ikke.html');

// --------------------------------------------------------------------------
// Lag A–C: strukturel dom over de tre filer.
// --------------------------------------------------------------------------
function auditAction(yml) {
  const p = [];
  if (!/runs:\s*\r?\n\s*using:\s*["']?composite/.test(yml)) p.push('runs.using er ikke composite');
  for (const input of ['pages', 'paths', 'fail-on', 'tarball', 'sarif-file']) {
    if (!new RegExp(`^ {2}${input}:`, 'm').test(yml)) p.push(`mangler inputtet '${input}'`);
  }
  if (!/npm install --global "\$\{\{ inputs\.tarball \}\}"/.test(yml)) p.push('installerer ikke fra inputs.tarball');
  if (!/npx eaa-scan/.test(yml)) p.push('scanner ikke med eaa-scan');
  if (!/--fail-on "\$\{\{ inputs\.fail-on \}\}"/.test(yml)) p.push('sender ikke inputs.fail-on til --fail-on');
  if (!/--sarif "\$\{args\[@\]\}" > "\$\{\{ inputs\.sarif-file \}\}"/.test(yml)) {
    p.push('skriver ikke SARIF-rapporten til inputs.sarif-file');
  }
  if (!/continue-on-error: true/.test(yml)) p.push('dømmer før rapporten er skrevet (continue-on-error mangler)');
  if (!/there is nothing to scan/.test(yml)) p.push('tier ikke véd tom input');
  if (!/exit 1/.test(yml)) p.push('har ingen exit 1');
  if (!/github\/codeql-action\/upload-sarif@v3/.test(yml)) p.push('uploader ikke SARIF til code scanning');
  if (!/sarif_file: \$\{\{ inputs\.sarif-file \}\}/.test(yml)) p.push('upload-sarif får ikke sarif_file');
  if (!/steps\.scan\.outcome == 'failure'/.test(yml)) p.push('fejler ikke på scanningens outcome');
  if (!/error, warning or never/.test(yml)) p.push('fail-on-inputtet tilbyder ikke never');
  return p;
}

function auditWorkflow(yml) {
  const p = [];
  if (!/permissions:\s*\r?\n\s+security-events: write/.test(yml)) p.push('mangler security-events: write');
  if (!/--sarif "\$@" > eaa-scan\.sarif/.test(yml)) p.push('skriver ikke SARIF-rapporten');
  if (!/--fail-on never/.test(yml)) p.push('SARIF-kørslen skal dømmes med never');
  if (!/github\/codeql-action\/upload-sarif@v3/.test(yml)) p.push('uploader ikke SARIF');
  if (!/sarif_file: eaa-scan\.sarif/.test(yml)) p.push('upload-sarif peger ikke på rapporten');
  if (!/FAIL_ON warning \| error \| never/.test(yml)) p.push('dokumenterer ikke de gyldige FAIL_ON-værdier');
  return p;
}

function auditDocs(html) {
  const p = [];
  if (!/uses: mahope\/hermes-passiv/.test(html)) p.push('viser ikke action-eksemplet');
  if (!/fail-on: warning/.test(html)) p.push('eksemplet viser ikke fail-on');
  if (!/security-events: write/.test(html)) p.push('nævner ikke rettigheden upload-sarif kræver');
  if (!/SARIF/.test(html)) p.push('forklarer ikke SARIF');
  if (!/Security tab/.test(html)) p.push('siger ikke hvor fundene ender');
  if (!/href="\/downloads\/eaa-scan-github-action\.yml"/.test(html)) p.push('har mistet linket til workflow-skabelonen');
  return p;
}

const selfTest = process.argv.includes('--self-test');

if (!selfTest) {
  for (const [navn, fil, audit] of [
    ['action.yml', ACTION, auditAction],
    ['workflow-skabelonen', WORKFLOW, auditWorkflow],
    ['downloads-siden', DOCS, auditDocs],
  ]) {
    const problems = audit(read(fil));
    ok(`${navn}: ingen fund`, problems.length === 0, problems.join('; '));
  }
}

// --------------------------------------------------------------------------
// Lag D: CLI'ens adfærd, kørt for rigtigt.
// --------------------------------------------------------------------------
function runCli(args, cli = CLI) {
  const r = spawnSync(process.execPath, [cli, ...args], { encoding: 'utf8' });
  return { status: r.status, stdout: r.stdout || '', stderr: r.stderr || '' };
}

// Kravet bag hver af lag D domme, som en funktion der kan køres både mod den
// rigtige CLI og mod en mutation — det er derfor mutationerne er ærlige.
const D1 = (r) => {
  if (r.status !== 1) return false;
  try {
    const doc = JSON.parse(r.stdout);
    const results = doc?.runs?.[0]?.results || [];
    return doc?.version === '2.1.0' && results.length > 0
      && Array.isArray(doc?.runs?.[0]?.tool?.driver?.rules);
  } catch { return false; }
};
const D2 = (r) => r.status === 0;
const D3 = (r) => {
  if (r.status !== 2) return false;
  try {
    const doc = JSON.parse(r.stdout);
    return (doc?.runs?.[0]?.results || []).some(x => x.ruleId === 'SCAN_ERROR' && x.level === 'error');
  } catch { return false; }
};
const D4 = (r) => r.status === 2;

if (!selfTest) {
  const d1 = runCli([PAGE, '--sarif', '--fail-on', 'warning']);
  ok('D1: exit 1 skriver alligevel SARIF med fund', D1(d1), `status=${d1.status} stdout=${d1.stdout.slice(0, 80)}`);

  const d2 = runCli([PAGE, '--fail-on', 'never']);
  ok('D2: --fail-on never accepteres og går grøn', D2(d2), `status=${d2.status} ${d2.stderr.slice(0, 80)}`);

  const d3 = runCli([MISSING, '--sarif']);
  ok('D3: en uhentet side giver et SCAN_ERROR-fund i SARIF', D3(d3), `status=${d3.status} stdout=${d3.stdout.slice(0, 80)}`);

  const d4 = runCli([PAGE, '--fail-on', 'maybe']);
  ok('D4: --fail-on maybe afvises', D4(d4), `status=${d4.status}`);
}

// --------------------------------------------------------------------------
// Mutationer: bevis for at lag D kan gå rød.
// --------------------------------------------------------------------------
// Hver mutation ligner en rettelse og er det ikke. Skrives den til en kopi af
// den shippede CLI, skal den pågældende dom blive RØD på kopien.
const MUTANT = join(root, 'scanner/npm/eaa-scanner/.cli-mutant.mjs');

function mutateAndRun(pairs, args) {
  const source = read(CLI);
  let out = source;
  for (const [fra, til] of pairs) {
    if (!out.includes(fra)) throw new Error(`mutationen ramte ikke: ${fra.slice(0, 50)}`);
    out = out.replace(fra, til);
  }
  writeFileSync(MUTANT, out);
  try {
    return runCli(args, MUTANT);
  } finally {
    unlinkSync(MUTANT);
  }
}

function assertRed(navn, pairs, args, dom) {
  const m = mutateAndRun(pairs, args);
  ok(navn, !dom(m), `dommen var grøn på mutationen: status=${m.status} stdout=${m.stdout.slice(0, 60)}`);
}

// M1: `never` fjernet fra de gyldige værdier → D2 skal være rød.
assertRed('M1: D2 er ikke grøn uden never i --fail-on',
  [["['error', 'warning', 'never']", "['error', 'warning']"]],
  [PAGE, '--fail-on', 'never'], D2);

// M2: dømmen sat til før rapporten skrives → D1 skal være rød (tom stdout).
assertRed('M2: D1 er ikke grøn når dømmen kommer før rapporten',
  [['if (failOn && failOn !== \'never\') {', 'if (failOn && failOn !== \'never\') { process.exit(1);']],
  [PAGE, '--sarif', '--fail-on', 'warning'], D1);

// M3: SCAN_ERROR-fundet omdøbt → D3 skal være rød.
assertRed('M3: D3 er ikke grøn uden SCAN_ERROR-funet',
  [["ruleId: 'SCAN_ERROR'", "ruleId: 'SCAN_ERRORX'"]],
  [MISSING, '--sarif'], D3);

console.log(`eaa-action: ${pass} bestået, ${fail} fejl`);
process.exit(fail ? 1 : 0);
