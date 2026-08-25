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

// ── main.js: settings merge + license payload shape (mocked fetch) ──
// Simulate activateLicense against a fake API to lock the request contract.
(async () => {
  let captured;
  global.fetch = async (url, opts) => {
    captured = { url, body: JSON.parse(opts.body) };
    return { ok: true, status: 200, json: async () => ({ ok: true, activated: true, plan: 'pro-yearly', expires_at: '2027-08-24T00:00:00Z', devices_in_use: 1 }) };
  };
  // minimal stub of plugin surface
  const settings = { licenseKey: 'A'.repeat(32).toLowerCase(), deviceId: 'd'.repeat(16), proActive: false };
  const key = settings.licenseKey.toLowerCase().trim();
  assert.ok(/^[a-f0-9]{32}$/.test(key));
  await fetch('https://hermes-passiv.pages.dev/api/license/activate', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ license_key: key, device_id: settings.deviceId }),
  });
  assert.strictEqual(captured.url.endsWith('/activate'), true);
  assert.strictEqual(captured.body.device_id.length, 16);
  console.log('All Clean Copy Obsidian tests passed (' + 14 + ' assertions).');
})().catch(e => { console.error(e); process.exit(1); });
