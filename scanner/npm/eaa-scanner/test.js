'use strict';
// Basic self-test: known-bad HTML must produce expected findings.
const { scanHtml } = require('./index.js');

const bad = `<!DOCTYPE html><html><head><meta name="viewport" content="width=320">
<style></style></head><body>
<img src="a.png"><img src="b.png" alt="">
<a href="/x"></a><button></button>
<input type="text" name="q"><input type="email" id="em">
<label for="other">Name</label>
<iframe src="https://x.example"></iframe>
<table><tr><td>1</td></tr></table>
<p style="color:#999;background-color:#fff">low contrast</p>
<h2>skip</h2><h4>levels</h4>
<div id="dup"></div><span id="dup"></span>
</body></html>`;
// note: no <title>, no lang → DOC_TITLE + HTML_LANG errors

const r = scanHtml(bad);
const ids = new Set(r.findings.map(f => f.rule_id));
const expect = ['IMG_ALT','FORM_LABEL','LINK_TEXT','BUTTON_TEXT','DUP_ID',
  'IFRAME_TITLE','TABLE_HEADER','DOC_TITLE','HTML_LANG','CONTRAST',
  'HEADING_SKIP'];
let fail = 0;
for (const e of expect) {
  const ok = ids.has(e);
  console.log(`${ok ? 'PASS' : 'FAIL'} ${e}`);
  if (!ok) fail++;
}
console.log(`score=${r.score} grade=${r.grade} errors=${r.summary.errors}`);
if (!r.ok || fail || r.score >= 40) { console.log('SELF-TEST FAILED'); process.exit(1); }
console.log('SELF-TEST OK');

// SARIF-output: --sarif skal give et gyldigt SARIF 2.1.0-dokument.
const { execFileSync } = require('child_process');
const os = require('os');
const path = require('path');
const tmp = path.join(os.tmpdir(), 'eaa-sarif-test.html');
require('fs').writeFileSync(tmp, bad);
const sarifOut = execFileSync('node', [__dirname + '/cli.js', tmp, '--sarif'], {
  encoding: 'utf8',
  cwd: __dirname,
});
require('fs').unlinkSync(tmp);
const sarif = JSON.parse(sarifOut);
const sarifOk = sarif.version === '2.1.0'
  && sarif.runs?.[0]?.tool?.driver?.name === 'eaa-scanner'
  && Array.isArray(sarif.runs[0].results)
  && sarif.runs[0].results.length > 0
  && sarif.runs[0].results.every(res =>
    res.ruleId && res.level && res.message?.text
    && res.locations?.[0]?.physicalLocation?.artifactLocation?.uri);
console.log(sarifOk ? 'PASS SARIF' : 'FAIL SARIF');
if (!sarifOk) { console.log('SARIF-TEST FAILED'); process.exit(1); }
console.log('SARIF-TEST OK');
