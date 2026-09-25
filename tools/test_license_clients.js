#!/usr/bin/env node
/**
 * Real tests for the shipped Clean Copy license clients.
 *
 * The old suite in `test.js` never loaded a client: it re-implemented the
 * request in the test body and then asserted on its own mock. This suite
 * loads the files that actually ship and drives them:
 *
 *   - `obsidian-plugin/main.js`   (the bundle inside the Obsidian zip)
 *   - `extension-clean-copy/options.js` (the Chrome zip, mirrored to Firefox)
 *
 * and covers the four cases a paying customer can hit: success (200),
 * 403 revoked/expired, 409 device limit, and 503 server outage — including
 * the rule that an outage keeps Pro for at most seven days.
 *
 * Run: node tools/test_license_clients.js
 */
'use strict';

const assert = require('assert');
const Module = require('module');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const License = require(path.join(ROOT, 'tools/clean_copy_license.js'));

const KEY = 'a'.repeat(32);
const DAY = 24 * 60 * 60 * 1000;
let checks = 0;
function ok(cond, what) {
  checks++;
  assert.ok(cond, what);
}

/* ── 1. The canonical rules ───────────────────────────────────────────── */

ok(License.PRODUCT === 'clean-copy-pro', 'product is clean-copy-pro');
ok(License.API_BASE === 'https://mahope.tools/api/license', 'API base is mahope.tools');
ok(License.CACHE_MAX_MS === 7 * DAY, 'cache window is seven days');
ok(License.isKeyFormat('  ' + KEY.toUpperCase() + ' '), 'key format trims and lowercases');
ok(!License.isKeyFormat('zz' + KEY), 'non-hex key rejected');

const body = License.payload(' ' + KEY.toUpperCase() + ' ', 'dev-123');
ok(body.license_key === KEY, 'payload normalizes the key');
ok(body.device_id === 'dev-123', 'payload carries the device id');
ok(body.product === 'clean-copy-pro', 'payload carries the product');

const now = 1_700_000_000_000;
ok(License.decide({ status: 200, data: { ok: true, valid: true }, now }).active === true, '200 valid is Pro');
ok(License.decide({ status: 200, data: { ok: true, activated: true }, now }).active === true, '200 activated is Pro');
ok(License.decide({ status: 403, data: { error: 'Expired.' }, now }).active === false, '403 is not Pro');
ok(/expired/i.test(License.decide({ status: 403, data: {}, now }).message), '403 explains itself');
ok(/another product/i.test(License.decide({ status: 403, data: {}, now }).message), '403 covers wrong product');
ok(/device limit/i.test(License.decide({ status: 409, data: {}, now }).message), '409 says device limit');
ok(License.decide({ status: 404, data: {}, now }).active === false, '404 is not Pro');
ok(License.decide({ status: 400, data: {}, now }).active === false, '400 is not Pro');
ok(License.decide({ status: 200, data: { ok: true, valid: false, reason: 'device_limit' }, now }).message
  .includes('Device limit'), 'valid:false device_limit is explicit');

/* The outage rule: cached for at most seven days, never longer. */
const fresh = License.decide({ status: 503, data: {}, checkedAt: now - DAY, now });
ok(fresh.active === true && fresh.cached === true, '503 within a day keeps Pro');
ok(License.decide({ status: 503, data: {}, checkedAt: now - 7 * DAY, now }).active === true,
  '503 at exactly seven days keeps Pro');
ok(License.decide({ status: 503, data: {}, checkedAt: now - 7 * DAY - 1, now }).active === false,
  '503 after seven days does not keep Pro');
ok(License.decide({ status: 0, data: {}, checkedAt: now - 2 * DAY, now }).active === true,
  'offline (status 0) keeps Pro from cache');
ok(License.decide({ status: 0, data: {}, checkedAt: 0, now }).active === false,
  'offline with no cache is not Pro');
ok(License.decide({ status: 500, data: {}, checkedAt: now - 2 * DAY, now }).active === true,
  '500 keeps Pro from cache');
/* A hard answer always wins over the cache. */
ok(License.decide({ status: 403, data: {}, checkedAt: now, now }).active === false,
  '403 beats a fresh cache');
ok(License.decide({ status: 409, data: {}, checkedAt: now, now }).active === false,
  '409 beats a fresh cache');
ok(License.decide({ status: 200, data: { ok: true, valid: false }, checkedAt: now, now }).active === false,
  'valid:false beats a fresh cache');

/* ── 2. The Obsidian plugin that ships in the zip ────────────────────── */

const notices = [];
const requests = [];
let nextResponse = { status: 200, json: { ok: true, activated: true, plan: 'pro-yearly', expires_at: '2027-08-24T00:00:00Z' } };

const obsidianStub = {
  requestUrl: async (opts) => {
    requests.push({ url: opts.url, body: JSON.parse(opts.body) });
    if (nextResponse instanceof Error) throw nextResponse;
    return nextResponse;
  },
  // Obsidian's base classes are old-style constructors (the plugin calls them
  // with .call(this, …)), so the stubs must be too.
  Notice: function (msg) { notices.push(msg); },
  Plugin: function () {},
  PluginSettingTab: function () {},
  Setting: function () {},
  request: () => {},
};

const loadWithStub = (absPath, stub) => {
  const original = Module._load;
  Module._load = function (request, parent, isMain) {
    if (request === 'obsidian') return stub;
    return original.apply(this, arguments);
  };
  try {
    delete require.cache[require.resolve(absPath)];
    return require(absPath);
  } finally {
    Module._load = original;
  }
};

const ObsidianPlugin = loadWithStub(path.join(ROOT, 'obsidian-plugin/main.js'), obsidianStub);

function makePlugin(settings) {
  const p = new ObsidianPlugin();
  p.app = {};
  p.settings = Object.assign({ licenseKey: KEY, deviceId: 'dev-obsidian', proActive: false, licenseCheckedAt: 0 }, settings);
  p.loadData = async () => p.settings;
  p.saveData = async () => {};
  p.saveSettings = async function () { p._saved = (p._saved || 0) + 1; };
  p.addCommand = () => {};
  p.addSettingTab = () => {};
  p.registerEvent = () => {};
  return p;
}

(async () => {
  /* activate → Pro, and the request carries product + the canonical base */
  let p = makePlugin();
  nextResponse = { status: 200, json: { ok: true, activated: true, plan: 'pro-yearly', expires_at: '2027-08-24T00:00:00Z' } };
  const activated = await p.activateLicense();
  ok(activated === true, 'obsidian: 200 activate → Pro');
  ok(p.settings.proActive === true, 'obsidian: proActive saved');
  ok(p.settings.licenseCheckedAt > 0, 'obsidian: positive check is timestamped');
  ok(requests[requests.length - 1].url === 'https://mahope.tools/api/license/activate',
    'obsidian: activate hits the contract base');
  ok(requests[requests.length - 1].body.product === 'clean-copy-pro', 'obsidian: activate sends product');
  ok(requests[requests.length - 1].body.license_key === KEY, 'obsidian: activate sends the key');

  /* 403 on re-validate → Pro off, with a visible reason */
  p = makePlugin({ proActive: true, licenseCheckedAt: now });
  notices.length = 0;
  nextResponse = { status: 403, json: { ok: false, error: 'This license has expired.' } };
  await p.validateLicensePeriodic();
  ok(p.settings.proActive === false, 'obsidian: 403 revokes Pro');
  ok(p.settings.licenseCheckedAt === 0, 'obsidian: 403 clears the cache stamp');
  ok(notices.some((m) => /expired/i.test(m)), 'obsidian: 403 tells the user why');

  /* 409 → Pro off, device limit named */
  p = makePlugin({ proActive: true, licenseCheckedAt: now });
  nextResponse = { status: 409, json: { ok: false, error: 'Device limit reached.' } };
  await p.validateLicensePeriodic();
  ok(p.settings.proActive === false, 'obsidian: 409 revokes Pro');
  ok(notices.some((m) => /device limit/i.test(m)), 'obsidian: 409 names the device limit');

  /* 503 with a recent positive check → Pro stays on */
  p = makePlugin({ proActive: true, licenseCheckedAt: Date.now() - 2 * DAY });
  nextResponse = { status: 503, json: { ok: false, error: 'Service unavailable.' } };
  await p.validateLicensePeriodic();
  ok(p.settings.proActive === true, 'obsidian: 503 within the cache window keeps Pro');

  /* 503 with a stale check → Pro off */
  p = makePlugin({ proActive: true, licenseCheckedAt: Date.now() - 8 * DAY });
  await p.validateLicensePeriodic();
  ok(p.settings.proActive === false, 'obsidian: 503 after seven days drops Pro');

  /* a thrown request is an outage, not a lost license */
  p = makePlugin({ proActive: true, licenseCheckedAt: Date.now() - DAY });
  nextResponse = new Error('network down');
  await p.validateLicensePeriodic();
  ok(p.settings.proActive === true, 'obsidian: a thrown request keeps Pro from cache');
  nextResponse = { status: 200, json: { ok: true, valid: true, expires_at: '2027-08-24T00:00:00Z' } };

  /* bad key format never reaches the network */
  p = makePlugin({ licenseKey: 'nope' });
  const before = requests.length;
  ok((await p.activateLicense()) === false, 'obsidian: malformed key rejected locally');
  ok(requests.length === before, 'obsidian: malformed key sends no request');

  /* ── 3. The Chrome options page (the Firefox copy is byte-identical) ── */
  const store = { deviceId: 'dev-chrome', proLicense: KEY, proExpires: '', proCheckedAt: 0 };
  global.chrome = {
    storage: {
      local: {
        get(keys, cb) { cb(Object.fromEntries(keys.map((k) => [k, store[k]]))); },
        set(obj, cb) { Object.assign(store, obj); if (cb) cb(); },
        remove(keys, cb) { (Array.isArray(keys) ? keys : [keys]).forEach((k) => delete store[k]); if (cb) cb(); },
      },
    },
  };
  const nodes = {};
  function node(id) {
    return nodes[id] || (nodes[id] = { id, textContent: '', innerHTML: '', hidden: false, disabled: false, style: {}, className: '', value: '', addEventListener() {} });
  }
  global.document = { getElementById: node, addEventListener() {}, createElement: () => node('tmp') };

  global.CleanCopyLicense = License;
  const optionsPath = path.join(ROOT, 'extension-clean-copy/options.js');
  const options = require(optionsPath);
  global.fetch = async () => ({ status: 200, json: async () => ({ ok: true, valid: true, expires_at: '2027-08-24T00:00:00Z' }) });
  let bodies = [];
  global.fetch = async (url, opts) => { bodies.push({ url, body: JSON.parse(opts.body) }); return { status: 200, json: async () => ({ ok: true, valid: true, expires_at: '2027-08-24T00:00:00Z' }) }; };

  await options.checkSavedLicense(KEY);
  ok(node('license-status').textContent.includes('Pro active'), 'chrome: 200 valid shows Pro');
  ok(bodies[0].body.product === 'clean-copy-pro', 'chrome: validate sends product');
  ok(bodies[0].url === 'https://mahope.tools/api/license/validate', 'chrome: validate hits the contract base');
  ok(store.proCheckedAt > 0, 'chrome: positive check is timestamped');

  store.proCheckedAt = Date.now();
  global.fetch = async () => ({ status: 503, json: async () => ({}) });
  await options.checkSavedLicense(KEY);
  ok(node('lic-state').textContent.includes('active'), 'chrome: 503 keeps Pro');
  ok(store.proLicense === KEY, 'chrome: 503 keeps the stored key');

  global.fetch = async () => ({ status: 503, json: async () => ({}) });
  store.proCheckedAt = Date.now() - 8 * DAY;
  await options.checkSavedLicense(KEY);
  ok(store.proLicense === undefined, 'chrome: 503 after seven days drops the key');
  ok(/unreachable/i.test(node('license-status').textContent), 'chrome: outage is explained');

  store.proLicense = KEY;
  store.proCheckedAt = Date.now();
  global.fetch = async () => ({ status: 403, json: async () => ({ ok: false, error: 'License revoked.' }) });
  await options.checkSavedLicense(KEY);
  ok(store.proLicense === undefined, 'chrome: 403 drops the key');
  ok(/revoked/i.test(node('license-status').textContent), 'chrome: 403 shows the server reason');

  global.fetch = async () => { throw new Error('offline'); };
  store.proLicense = KEY;
  store.proCheckedAt = Date.now() - 3 * DAY;
  await options.checkSavedLicense(KEY);
  ok(store.proLicense === KEY, 'chrome: offline keeps Pro from cache');
  ok(node('license-status').textContent.includes('unreachable'), 'chrome: offline is announced, not silent');

  /* the Firefox copy must be the same file, or the two browsers drift */
  const fs = require('fs');
  ok(fs.readFileSync(path.join(ROOT, 'extension-clean-copy-firefox/options.js'), 'utf8')
    === fs.readFileSync(optionsPath, 'utf8'), 'firefox options.js is byte-identical to chrome');
  ok(fs.readFileSync(path.join(ROOT, 'extension-clean-copy-firefox/license.js'), 'utf8')
    === fs.readFileSync(path.join(ROOT, 'extension-clean-copy/license.js'), 'utf8'),
    'firefox license.js is byte-identical to chrome');
  ok(fs.readFileSync(path.join(ROOT, 'extension-clean-copy/license.js'), 'utf8')
    === fs.readFileSync(path.join(ROOT, 'tools/clean_copy_license.js'), 'utf8'),
    'extension license.js is byte-identical to the canonical rules');

  console.log('Clean Copy license clients OK (' + checks + ' checks).');
})().catch((e) => { console.error(e); process.exit(1); });
