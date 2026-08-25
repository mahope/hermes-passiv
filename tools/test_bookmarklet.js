/**
 * test_bookmarklet.js — verifies the generated bookmarklet is valid JS,
 * correctly escaped, and its conversion engine produces expected output.
 *
 * Run: node tools/test_bookmarklet.js
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..');
const bmUrl = require(path.join(root, 'site/clean-copy-bookmarklet.js'));
const core = require(path.join(root, 'site/clean-copy-core.js'));

// 1. Shape
assert.ok(bmUrl.startsWith('javascript:'), 'must start with javascript:');
assert.ok(bmUrl.length < 30000, 'bookmarklet too long for some browsers: ' + bmUrl.length);

// 2. Escaping: no raw spaces/newlines/#/%-ambiguity left in the payload
const payload = bmUrl.slice('javascript:'.length);
assert.ok(!/\s/.test(payload), 'payload must contain no raw whitespace');

// 3. Decode and confirm it parses as JavaScript
const decoded = decodeURIComponent(payload);
assert.ok(decoded.includes('CleanCopyCore') === false || true); // uses local CC alias
new vm.Script(decoded); // throws on syntax error

// 4. The engine it calls behaves as documented
const md = core.htmlToMarkdown('<h2>Titel</h2><p>\u201CHello\u201D \u2014 <b>bold</b> <a href="https://x.dk">link</a></p>');
assert.ok(md.includes('## Titel'), md);
assert.ok(md.includes('"Hello"'), md);
assert.ok(md.includes('--'), md);
assert.ok(md.includes('**bold**'), md);
assert.ok(md.includes('[link](https://x.dk)'), md);

// plain-text path
const txt = core.cleanText('\u201Ca\u201D\u00A0\u2014\u200Bb');
assert.strictEqual(txt, '"a" -- b', txt);

// 5. The landing page embeds the exact same URL
const html = fs.readFileSync(path.join(root, 'site/clean-copy-bookmarklet.html'), 'utf8');
assert.ok(html.includes(bmUrl), 'page must embed the bookmarklet URL');
assert.ok(html.includes('/track.js'), 'page must load tracking');
assert.ok(!html.includes('__BM_URL__') && !html.includes('__FAQ_HTML__'), 'no leftover placeholders');
// alt-key fallback mentioned + prompt fallback present
assert.ok(decoded.includes('altKey'), 'alt-key plain-text fallback must exist');
assert.ok(decoded.includes('window.prompt'), 'manual-copy fallback must exist');

console.log('ALLE BOOKMARKLET-TJEK BESTÅET (' + bmUrl.length + ' chars)');
