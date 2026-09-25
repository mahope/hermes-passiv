/**
 * tests for the Obsidian plugin core + license flow (Node, no framework).
 * Run: node obsidian-plugin/test.js
 */
const assert = require('assert');
const Core = require('./core.js');

// ── core: identical behaviour to extension core ──
assert.strictEqual(Core.cleanText('a\u00A0b  c\n\n\n\nd'), 'a b c\n\nd');
assert.strictEqual(Core.htmlToMarkdown('<h2>Hi</h2><p>Some <b>bold</b> text</p>'),
  '## Hi\n\nSome **bold** text');
assert.ok(Core.htmlToMarkdown('<ul><li>a</li><li>b</li></ul>').includes('- a\n- b'));
assert.ok(Core.htmlToMarkdown('<ol><li>one</li><li>two</li></ol>').includes('1. one\n2. two'));
assert.ok(Core.htmlToMarkdown('<pre><code>x &lt; y</code></pre>').includes('```\nx < y\n```'));
assert.ok(Core.htmlToMarkdown('<a href="https://x.dk">link</a>').includes('[link](https://x.dk)'));

// Pro rules
const rules = [{ find: 'TODO', replace: 'DONE' }];
assert.ok(Core.batchConvert(['<p>TODO now</p>'], 'markdown', rules)[0].content.includes('DONE now'));
// literal rules are escaped, so metacharacters don't throw; invalid REGEX does
assert.strictEqual(Core.batchConvert(['<p>(x)</p>'], 'markdown', [{ find: '(', replace: '-' }])[0].content, '-x)');
assert.throws(() => Core.compileRules([{ find: '[', replace: 'x', regex: true }]), /invalid pattern/);
// regex rule
const rr = [{ find: '\\d+', replace: '#', regex: true }];
assert.strictEqual(Core.batchConvert(['<p>abc 123</p>'], 'markdown', rr)[0].content, 'abc #');

// wikilinks mode: internal links -> [[WikiLink]], external stay Markdown,
// images and fenced code are untouched
const wl = Core.batchConvert(
  ['<p>See <a href="/other">Other</a> and <a href="https://x.example/y">Ext</a> <img src="a.png" alt="im"></p><pre><code>[z](w)</code></pre>'],
  'wikilinks', [])[0].content;
assert.ok(wl.includes('[[Other]]'), wl);
assert.ok(wl.includes('[Ext](https://x.example/y)'), wl);
assert.ok(wl.includes('![im](a.png)'), wl);
assert.ok(wl.includes('[z](w)'), wl);
// scheme-less relative + root-relative both convert
const wl2 = Core.batchConvert(['<a href="sub/page">Sub</a>'], 'wikilinks', [])[0].content;
assert.strictEqual(wl2, '[[Sub]]');

// csv mode: tables -> RFC 4180 rows, prose dropped, fallback to plain text
const csv = Core.batchConvert(
  ['<p>intro</p><table><tr><th>Name</th><th>Note</th></tr><tr><td>A</td><td>has, comma and "q"</td></tr></table>'],
  'csv', [])[0].content;
assert.ok(csv.startsWith('Name,Note'), csv);
assert.ok(csv.includes('"has, comma and ""q"""'), csv);
assert.strictEqual(Core.batchConvert(['<p>no table</p>'], 'csv', [])[0].content.trim(), 'no table');

// batch never throws
const batch = Core.batchConvert([null, '<p>ok</p>'], 'markdown', []);
assert.deepStrictEqual(batch.map(b => b.ok), [true, true]);

// ── main.js: the real request contract lives in tools/test_license_clients.js ──
// This file used to end with a block that re-implemented the activation request
// against the old `hermes-passiv.pages.dev` host and asserted on its own mock,
// so it could never fail when the shipped plugin broke. `tools/test_license_clients.js`
// loads this plugin's main.js for real and covers 200/403/404/400/409/500/503,
// the seven-day outage cache, and the product payload.
require('../tools/test_license_clients.js');
console.log('All Clean Copy Obsidian tests passed.');
