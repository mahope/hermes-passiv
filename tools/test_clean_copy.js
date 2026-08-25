const fs = require('fs');
const vm = require('vm');

let src = fs.readFileSync('tools/clean_copy_core.js', 'utf8');
// The UMD factory assigns to module.exports in Node — provide a shim so the
// sandbox exposes CleanCopyCore's API directly.
src += '\n;this.CleanCopyCore = (typeof module === "object" && module.exports) ? module.exports : CleanCopyCore;\n';

const sandbox = {};
sandbox.module = { exports: {} };
vm.createContext(sandbox);
vm.runInContext(src, sandbox);
Object.assign(sandbox, sandbox.module.exports);

const assert = require('assert');
const t1 = sandbox.cleanText('  \u201Csmart\u201D  \u00A0  text\u200B  ');
assert.strictEqual(t1, '"smart" text', 'cleanText');
console.log('cleanText OK:', JSON.stringify(t1));

assert.strictEqual(sandbox.cleanText('Guard\u2060ian artic\u2062le'), 'Guardian article', 'invisible word joiners stripped');
console.log('invisible chars OK');

const md = sandbox.htmlToMarkdown(
  '<h2>Title</h2><p>Hello <strong>world</strong> and <a href="https://x.com">link</a>.</p>' +
  '<ul><li>one</li><li>two</li></ul><pre><code>if (a &lt; b) {}</code></pre>'
);
console.log('--- markdown output ---');
console.log(md);
assert(md.startsWith('## Title'), 'h2');
assert(/\*\*world\*\*/.test(md), 'bold');
assert(/\[link\]\(https:\/\/x\.com\)/.test(md), 'link');
assert(/- one/.test(md) && /- two/.test(md), 'list');
assert(/```/.test(md) && /if \(a < b\) \{\}/.test(md), 'code block + entity unescape');
console.log('htmlToMarkdown OK');

// Table conversion (iteration 135)
const tbl = sandbox.htmlToMarkdown(
  '<table><thead><tr><th>Name</th><th>Price</th></tr></thead>' +
  '<tbody><tr><td>A &amp; B</td><td>$9</td></tr><tr><td>C</td><td>p|q</td></tr></tbody></table>'
);
assert(tbl.startsWith('| Name | Price |'), 'table header row');
assert(/\|\s*---\s*\|\s*---\s*\|/.test(tbl), 'table separator');
assert(tbl.includes('| A & B | $9 |'), 'table body row + entity unescape');
assert(tbl.includes('p\\|q'), 'pipe escaped in cell');

const tbl2 = sandbox.htmlToMarkdown(
  '<table><tr><th>H1</th><th>H2</th></tr><tr><td colspan="2">wide</td></tr></table>'
);
assert(tbl2.includes('| wide |  |') || tbl2.includes('| wide | |'), 'colspan padding: ' + JSON.stringify(tbl2));

const tbl3 = sandbox.htmlToMarkdown(
  '<table><tr><th>H</th></tr><tr><td><strong>b</strong> <a href="x">l</a></td></tr></table>'
);
assert(tbl3.includes('| **b** [l](x) |'), 'inline markup inside cell: ' + JSON.stringify(tbl3));
console.log('table conversion OK');

// Iteration 174: CDATA content must survive (was silently dropped)
const cdata = sandbox.htmlToMarkdown('<p>a</p><![CDATA[raw cdata text]]><p>b</p>');
assert(cdata.includes('raw cdata text'), 'CDATA kept: ' + JSON.stringify(cdata));

// Iteration 174: definition lists get structure instead of smelting together
const dl = sandbox.htmlToMarkdown('<dl><dt>API</dt><dd>Interface for apps</dd><dt>SDK</dt><dd>Toolkit</dd></dl>');
assert(dl.includes('**API**'), 'dt bolded: ' + JSON.stringify(dl));
assert(/:\s*Interface for apps/.test(dl), 'dd indented: ' + JSON.stringify(dl));
assert(!/APISDK|TermDef/.test(dl.replace(/[\s*:]|\*\*/g, '')), 'no fused terms');
console.log('iteration-174 fixes OK');

// Iteration 175: figcaption separated from the image line
const fig = sandbox.htmlToMarkdown('<figure><img src="a.png" alt="x"><figcaption>Caption text</figcaption></figure>');
assert(fig.includes('\n\nCaption text') || /\)\s*\n+\s*Caption text/.test(fig), 'figcaption separated: ' + JSON.stringify(fig));

// Iteration 175: blockquotes become "> " prefixed Markdown
const bq1 = sandbox.htmlToMarkdown('<blockquote><p>quoted line</p></blockquote>');
assert(bq1.startsWith('> quoted line'), 'simple blockquote: ' + JSON.stringify(bq1));

// Nested: inner quote gets double prefix
const bq2 = sandbox.htmlToMarkdown('<blockquote><p>a</p><blockquote><p>b</p></blockquote><p>c</p></blockquote>');
assert(bq2.includes('> > b'), 'nested blockquote prefix: ' + JSON.stringify(bq2));
assert(bq2.includes('> a'), 'outer content quoted');
assert(/>\s*c/.test(bq2), 'trailing outer content still quoted');

// Quote containing a list keeps list markers under the prefix
const bq3 = sandbox.htmlToMarkdown('<blockquote><ul><li>i1</li><li>i2</li></ul></blockquote>');
assert(bq3.includes('> - i1') && bq3.includes('> - i2'), 'list in quote: ' + JSON.stringify(bq3));
console.log('iteration-175 fixes OK');

// Iteration 177: <ol start="N"> continues numbering
const olStart = sandbox.htmlToMarkdown('<ol start="3"><li>three</li><li>four</li></ol>');
assert(/3\. three/.test(olStart) && /4\. four/.test(olStart), 'ol start attr: ' + JSON.stringify(olStart));

// Iteration 177: details/summary -> bold summary + content
const det = sandbox.htmlToMarkdown('<details><summary>More info</summary><p>Hidden text</p></details>');
assert(/\*\*More info\*\*/.test(det) && /Hidden text/.test(det), 'details/summary: ' + JSON.stringify(det));

// Iteration 177: SVG subtrees stripped, MathML alt kept
const svg = sandbox.htmlToMarkdown('<p>A</p><svg width="10"><circle r="5"/></svg><p>B</p>');
assert(/^A\s*\n+\s*B$/.test(svg), 'svg stripped: ' + JSON.stringify(svg));
const math = sandbox.htmlToMarkdown('<p>Formula:</p><math alt="E=mc2"><mi>E</mi></math>');
assert(/E=mc2/.test(math) && !/<mi>/.test(math), 'math alt kept: ' + JSON.stringify(math));
console.log('iteration-177 fixes OK');

// Iteration 178: iframe fallback becomes its own block, doesn't glue
const ifr = sandbox.htmlToMarkdown('<iframe src="x">fallback</iframe><p>b</p>');
assert(/^fallback\s*\n+\s*b$/.test(ifr), 'iframe fallback separated: ' + JSON.stringify(ifr));

// Iteration 178: select options on separate lines, optgroup label kept
const sel = sandbox.htmlToMarkdown('<select><option>Red</option><option>Blue</option></select><p>x</p>');
assert(/Red/.test(sel) && /Red\s*\n+\s*Blue/.test(sel), 'select options: ' + JSON.stringify(sel));
const og = sandbox.htmlToMarkdown('<select><optgroup label="Group A"><option>1</option></optgroup></select>');
assert(/Group A/.test(og) && /\n1/.test(og), 'optgroup label: ' + JSON.stringify(og));

// Iteration 178: input value kept as text
const inp = sandbox.htmlToMarkdown('<p>a <input type="text" value="Navn"> b</p>');
assert(/Navn/.test(inp), 'input value: ' + JSON.stringify(inp));

console.log('iteration-178 fixes OK');

// Iteration 180: nested tables — inner table converts first, content survives
const nt = sandbox.htmlToMarkdown('<table><tr><th>Outer</th></tr><tr><td><table><tr><td>inner</td></tr></table></td></tr></table>');
assert(/inner/.test(nt), 'nested table cell survives: ' + JSON.stringify(nt));
assert(nt.startsWith('| Outer |'), 'outer table intact');
// flat table regression
assert(sandbox.htmlToMarkdown('<table><tr><th>A</th></tr><tr><td>1</td></tr></table>').startsWith('| A |'), 'flat table');

// Iteration 180: abbr title as parenthetical at first occurrence only
const ab = sandbox.htmlToMarkdown('<p>The <abbr title="World Health Organization">WHO</abbr> and <abbr title="World Health Organization">WHO</abbr> again.</p>');
assert(ab.includes('WHO (World Health Organization)'), 'abbr expanded: ' + JSON.stringify(ab));
assert(ab.indexOf('WHO (World Health') === ab.lastIndexOf('WHO (World Health'), 'abbr expanded only once');

console.log('iteration-180 fixes OK');

// Iteration 179: parity check — extension background.js conversion must equal the shared core
(function(){
  const bg = fs.readFileSync('extension-clean-copy/background.js', 'utf8');
  const extract = (src, name) => {
    let i = src.indexOf('function ' + name);
    if (i < 0) throw new Error(name + ' not found');
    let depth = 0, j = src.indexOf('{', i), k = j;
    while (true) { const c = src[k];
      if (c === '{') depth++;
      else if (c === '}') { depth--; if (!depth) break; }
      k++; }
    return src.slice(i, k + 1);
  };
  assert.strictEqual(extract(bg,'htmlToMarkdown'), extract(src,'htmlToMarkdown'),
    'extension background.js htmlToMarkdown diverged from tools/clean_copy_core.js');
  console.log('core/extension parity OK');
})();
