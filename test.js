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

// batch never throws
const batch = Core.batchConvert([null, '<p>ok</p>'], 'markdown', []);
assert.deepStrictEqual(batch.map(b => b.ok), [true, true]);

// ── license clients: the real suite ──────────────────────────────
// The block below used to re-implement the request inside the test and assert
// on its own mock, so it could never fail when a shipped client broke. It now
// loads obsidian-plugin/main.js and extension-clean-copy/options.js — the files
// that actually ship — and covers 200, 403, 409, 503 and the seven-day cache.
console.log('Clean Copy core tests passed.');
require('./tools/test_license_clients.js');
