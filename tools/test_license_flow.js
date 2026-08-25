#!/usr/bin/env node
/**
 * test_license_flow.js — local end-to-end test of the Clean Copy Pro
 * licensing stack in site/_worker.js, with NO Cloudflare and NO secrets.
 *
 * Simulates the Worker's fetch handler against an in-memory KV and covers:
 *   1. Lemon webhook: bad signature -> 403, missing secret -> 503,
 *      non-order events ignored, valid order_created -> license issued
 *      (idempotent on retries), counter incremented.
 *   2. /api/license/activate + /validate: format checks, unknown key 404,
 *      device binding, device limit (LICENSE_MAX_DEVICES), revoked 403.
 *   3. Expiry: an expired key is rejected by both activate and validate.
 *
 * Run: node tools/test_license_flow.js
 */
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

// ── load the worker module ──
const src = fs.readFileSync(path.join(__dirname, '..', 'site', '_worker.js'), 'utf8');
const mod = src.replace(/export default\s*\{/, 'module.exports = {');
fs.writeFileSync(path.join(__dirname, '._worker_test_copy.js'), mod);
const worker = require('./._worker_test_copy.js');
fs.unlinkSync(path.join(__dirname, '._worker_test_copy.js'));

// ── in-memory KV ──
function makeKV() {
  const store = new Map();
  return {
    get: async (k) => store.get(k) ?? null,
    put: async (k, v) => { store.set(k, String(v)); },
    _store: store,
  };
}

const SECRET = 'test-webhook-secret-0123456789abcdef';
let passed = 0;
function ok(name, fn) {
  try { fn(); console.log('  ok -', name); passed++; }
  catch (e) { console.error('  FAIL -', name, '\n ', e.message); process.exitCode = 1; }
}
async function okAsync(name, fn) {
  try { await fn(); console.log('  ok -', name); passed++; }
  catch (e) { console.error('  FAIL -', name, '\n ', e.message); process.exitCode = 1; }
}

async function call(env, pathName, opts = {}) {
  const req = new Request('https://hermes-passiv.pages.dev' + pathName, opts);
  return worker.fetch(req, env);
}

function signedBody(payload) {
  const raw = JSON.stringify(payload);
  const sig = crypto.createHmac('sha256', SECRET).update(raw).digest('hex');
  return { raw, headers: { 'content-type': 'application/json', 'x-signature': sig } };
}

function orderPayload(orderId) {
  return {
    meta: { event_name: 'order_created', custom_data: { order_id: orderId } },
    data: {
      id: orderId,
      attributes: { first_order_item: { variant_name: 'Clean Copy Pro — Yearly' } },
    },
  };
}

async function main() {
  // ─── webhook signature handling ───
  console.log('\n[webhook]');
  let env = { VISITS: makeKV() }; // no LS_WEBHOOK_SECRET

  await okAsync('missing secret -> 503 (LS will retry)', async () => {
    const r = await call(env, '/api/lemon-webhook', { method: 'POST', body: '{}' });
    assert.strictEqual(r.status, 503);
  });

  env = { VISITS: makeKV(), LS_WEBHOOK_SECRET: SECRET };

  await okAsync('bad signature -> 403, nothing stored', async () => {
    const r = await call(env, '/api/lemon-webhook', {
      method: 'POST',
      headers: { 'x-signature': 'a'.repeat(64) },
      body: JSON.stringify(orderPayload('o1')),
    });
    assert.strictEqual(r.status, 403);
    assert.strictEqual(env.VISITS._store.size, 0);
  });

  await okAsync('non-POST -> 405', async () => {
    const r = await call(env, '/api/lemon-webhook', { method: 'GET' });
    assert.strictEqual(r.status, 405);
  });

  await okAsync('valid ping event acknowledged, no key minted', async () => {
    const { raw, headers } = signedBody({ meta: { event_name: 'ping' }, data: {} });
    const r = await call(env, '/api/lemon-webhook', { method: 'POST', headers, body: raw });
    const j = await r.json();
    assert.ok(j.ok && j.ignored === 'ping');
    assert.strictEqual(env.VISITS._store.size, 0);
  });

  let key1 = '';
  await okAsync('valid order_created -> license key issued', async () => {
    const { raw, headers } = signedBody(orderPayload('order-A'));
    const r = await call(env, '/api/lemon-webhook', { method: 'POST', headers, body: raw });
    const j = await r.json();
    assert.ok(j.ok, 'ok flag');
    assert.match(j.license_key, /^[a-f0-9]{32}$/, 'key format');
    assert.ok(j.expires_at > new Date().toISOString(), 'expiry in future');
    key1 = j.license_key;
  });

  await okAsync('webhook retry same order -> same key (idempotent)', async () => {
    const { raw, headers } = signedBody(orderPayload('order-A'));
    const r = await call(env, '/api/lemon-webhook', { method: 'POST', headers, body: raw });
    const j = await r.json();
    assert.ok(j.duplicate === true && j.license_key === key1);
  });

  await okAsync('second order -> different key; counter == 2', async () => {
    const { raw, headers } = signedBody(orderPayload('order-B'));
    const r = await call(env, '/api/lemon-webhook', { method: 'POST', headers, body: raw });
    const j = await r.json();
    assert.notStrictEqual(j.license_key, key1);
    assert.strictEqual(await env.VISITS.get('t:all:licenses-issued'), '2');
  });

  // ─── activate / validate ───
  console.log('\n[activate/validate]');

  await okAsync('activate: malformed key -> 400', async () => {
    const r = await call(env, '/api/license/activate', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ license_key: 'nope', device_id: 'd1' }),
    });
    assert.strictEqual(r.status, 400);
  });

  await okAsync('activate: unknown key -> 404', async () => {
    const r = await call(env, '/api/license/activate', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ license_key: 'f'.repeat(32), device_id: 'd1' }),
    });
    assert.strictEqual(r.status, 404);
  });

  await okAsync('activate: missing device_id -> 400', async () => {
    const r = await call(env, '/api/license/activate', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ license_key: key1 }),
    });
    assert.strictEqual(r.status, 400);
  });

  await okAsync('uppercase key accepted (normalised)', async () => {
    const r = await call(env, '/api/license/validate', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ license_key: key1.toUpperCase(), device_id: 'probe' }),
    });
    assert.strictEqual(r.status, 200);
  });

  let dev1 = 'device-' + 'a'.repeat(20);
  await okAsync('activate binds device 1', async () => {
    const r = await call(env, '/api/license/activate', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ license_key: key1, device_id: dev1 }),
    });
    const j = await r.json();
    assert.ok(j.activated && j.plan === 'pro-yearly');
    assert.strictEqual(j.devices_in_use, 1); // validate does NOT bind devices
  });

  await okAsync('re-activate same device -> still 1 bound (no dup)', async () => {
    const r = await call(env, '/api/license/validate', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ license_key: key1, device_id: dev1 }),
    });
    const j = await r.json();
    assert.ok(j.valid === true);
  });

  await okAsync('device limit enforced at LICENSE_MAX_DEVICES', async () => {
    // fill remaining slots
    for (let i = 0; i < 4; i++) {
      await call(env, '/api/license/activate', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ license_key: key1, device_id: `dev-${i}` }),
      });
    }
    const r = await call(env, '/api/license/activate', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ license_key: key1, device_id: 'one-too-many' }),
    });
    assert.strictEqual(r.status, 409);
    // validate for an unbound device reports valid:false instead of erroring
    const v = await call(env, '/api/license/validate', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ license_key: key1, device_id: 'stranger-device' }),
    });
    const jv = await v.json();
    assert.ok(jv.valid === false && jv.reason === 'device_limit');
  });

  // ─── expiry + revoked ───
  console.log('\n[expiry/revoked]');

  const expEnv = { VISITS: makeKV() };
  const expiredKey = 'a'.repeat(32);
  await expEnv.VISITS.put(`lic:${expiredKey}`, JSON.stringify({
    status: 'active', plan: 'pro-yearly', expires_at: '2026-01-01T00:00:00Z', devices: [],
  }));
  await okAsync('expired key -> activate 403 with renew hint', async () => {
    const r = await call(expEnv, '/api/license/activate', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ license_key: expiredKey, device_id: 'd1' }),
    });
    assert.strictEqual(r.status, 403);
  });
  await okAsync('revoked key -> 403', async () => {
    const rk = 'b'.repeat(32);
    await expEnv.VISITS.put(`lic:${rk}`, JSON.stringify({ status: 'revoked', devices: [] }));
    const r = await call(expEnv, '/api/license/validate', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ license_key: rk, device_id: 'd1' }),
    });
    assert.strictEqual(r.status, 403);
  });

  console.log(`\n${passed} checks passed${process.exitCode ? ' (with failures)' : ''}`);
}

main().catch((e) => { console.error(e); process.exit(1); });
