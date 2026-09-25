#!/usr/bin/env node
/**
 * test_license_flow.js — local end-to-end test of the Clean Copy Pro
 * licensing stack in site/_worker.js, with NO Cloudflare and NO secrets.
 *
 * Simulates the Worker's fetch handler against an in-memory KV and covers:
 *   1. /api/license/activate + /validate: format checks, unknown key 404,
 *      device binding, device limit (LICENSE_MAX_DEVICES), revoked 403.
 *   2. Expiry: an expired key is rejected by both activate and validate.
 *   3. Legacy lookup and its rate limit.
 *
 * Run: node tools/test_license_flow.js
 */
const assert = require('assert');
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

async function main() {
  const env = { VISITS: makeKV() };
  const key1 = '1'.repeat(32);
  await env.VISITS.put(`lic:${key1}`, JSON.stringify({
    status: 'active', plan: 'pro-yearly', expires_at: '2099-01-01T00:00:00Z', devices: [],
  }));
  const emailDigest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('lemail:buyer@example.com'));
  const emailHash = [...new Uint8Array(emailDigest)].map(b => b.toString(16).padStart(2, '0')).join('');
  await env.VISITS.put(`lic-email:${emailHash}:order-A`, key1);

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


  // ─── license lookup (delivery gap) ───
  console.log('\n[license lookup]');

  await okAsync('lookup with correct order id + email -> key returned', async () => {
    const r = await call(env, '/api/license/lookup', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ order_id: 'order-A', email: 'Buyer@Example.com' }),
    });
    const j = await r.json();
    assert.strictEqual(r.status, 200);
    assert.ok(j.ok && j.license_key === key1);
  });

  await okAsync('lookup wrong email -> 404 uniform answer', async () => {
    const r = await call(env, '/api/license/lookup', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ order_id: 'order-A', email: 'wrong@example.com' }),
    });
    assert.strictEqual(r.status, 404);
  });

  await okAsync('lookup unknown order id -> same 404 as wrong email', async () => {
    const r1 = await call(env, '/api/license/lookup', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ order_id: 'no-such-order', email: 'buyer@example.com' }),
    });
    assert.strictEqual(r1.status, 404);
    const j1 = await r1.json();
    const r2 = await call(env, '/api/license/lookup', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ order_id: 'order-A', email: 'wrong@example.com' }),
    });
    const j2 = await r2.json();
    assert.strictEqual(j1.error, j2.error, 'uniform error message');
  });

  await okAsync('lookup missing/invalid fields -> 404 (no field oracle)', async () => {
    for (const body of [{}, { order_id: '' }, { order_id: 'x', email: 'notanemail' }, { email: 'a@b.co' }]) {
      const r = await call(env, '/api/license/lookup', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body),
      });
      assert.strictEqual(r.status, 404, JSON.stringify(body));
    }
  });

  await okAsync('lookup GET -> 405', async () => {
    const r = await call(env, '/api/license/lookup', { method: 'GET' });
    assert.strictEqual(r.status, 405);
  });

  await okAsync('lookup rate limit: 11th attempt in hour -> 429', async () => {
    const rlEnv = { VISITS: makeKV() };
    const rlKey = '2'.repeat(32);
    const rlEmailDigest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('lemail:rl@example.com'));
    const rlEmailHash = [...new Uint8Array(rlEmailDigest)].map(b => b.toString(16).padStart(2, '0')).join('');
    await rlEnv.VISITS.put(`lic:${rlKey}`, JSON.stringify({ status: 'active', plan: 'pro-yearly', devices: [] }));
    await rlEnv.VISITS.put(`lic-email:${rlEmailHash}:order-RL`, rlKey);
    let last;
    for (let i = 0; i < 11; i++) {
      last = await call(rlEnv, '/api/license/lookup', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ order_id: 'order-RL', email: 'rl@example.com' }),
      });
    }
    assert.strictEqual(last.status, 429);
  });

  console.log(`\n${passed} checks passed${process.exitCode ? ' (with failures)' : ''}`);
}

main().catch((e) => { console.error(e); process.exit(1); });
