const fs = require('fs');
const assert = require('assert');
const c = require('./clean_copy_core.js');

// ── compileRules / applyRules ──
let compiled = c.compileRules([{ find: 'foo', replace: 'bar' }]);
assert.strictEqual(c.applyRules('foo foo', compiled), 'bar bar', 'literal rule');

compiled = c.compileRules([{ find: '\\b(\\d{4})-(\\d{2})-(\\d{2})\\b', replace: '$2/$3/$1', regex: true }]);
assert.strictEqual(c.applyRules('on 2026-08-24 ok', compiled), 'on 08/24/2026 ok', 'regex rule');

compiled = c.compileRules([{ find: 'FOO', replace: 'x', caseSensitive: false }, { find: 'bar', replace: 'y' }]);
assert.strictEqual(c.applyRules('foo FOO bar', compiled), 'x x y', 'case sensitivity flag');

assert.throws(() => c.compileRules([{ find: 'a[', replace: '', regex: true }]), /invalid pattern/, 'bad regex throws');

// ── batchConvert ──
let out = c.batchConvert(
  ['<h2>A</h2><p>hello</p>', '<ul><li>x</li></ul>', '<p>plain text here</p>'],
  'markdown'
);
assert.strictEqual(out.length, 3);
assert(out.every(r => r.ok), 'all convert');
assert.match(out[0].content, /^## A/);
assert.match(out[1].content, /^- x$/);
assert.match(out[2].content, /^plain text here$/);

out = c.batchConvert(['<p>foo</p>', null, { html: '<b>b</b>' }], 'plain', [{ find: 'foo', replace: 'bar' }]);
assert.strictEqual(out[0].content, 'bar', 'rules applied in batch plain mode');
assert.ok(out[1].ok && out[2].ok, 'null and object inputs tolerated');

out = c.batchConvert(['a', 'b'], 'markdown', [{ find: 'a[', replace: '', regex: true }]);
assert(out.every(r => !r.ok && /invalid pattern/.test(r.error)), 'bad global rules fail whole batch with message');

out = c.batchConvert([], 'markdown');
assert.deepStrictEqual(out, [], 'empty batch');

console.log('pro core tests: ALL PASS');
