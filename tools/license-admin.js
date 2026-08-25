#!/usr/bin/env node
/**
 * license-admin.js — issue/revoke/list Clean Copy Pro license keys.
 *
 * Keys live in the same Cloudflare KV namespace (VISITS) the Worker uses,
 * under lic:<key>. This script talks to the KV REST API directly with the
 * same credentials deploy.sh uses (~/.hermes/.env). (The `wrangler kv` CLI
 * path proved unreliable from this machine — writes silently landed in a
 * different view than production — so we use the REST API.)
 *
 * Usage:
 *   node tools/license-admin.js issue [N]     # create N keys, print them
 *   node tools/license-admin.js revoke <key>  # mark a key revoked
 *   node tools/license-admin.js list          # list keys + device counts
 *
 * Requires: CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID in env
 * (and CF_KV_NAMESPACE_ID, which defaults to the VISITS namespace).
 */

const crypto = require('crypto');

const NAMESPACE = process.env.CF_KV_NAMESPACE_ID || '215f8a921ac34dbcad9eb204e06baf2f';
const ACCOUNT = process.env.CLOUDFLARE_ACCOUNT_ID;
const TOKEN = process.env.CLOUDFLARE_API_TOKEN;
if (!ACCOUNT || !TOKEN) {
  console.error('CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN missing — source ~/.hermes/.env first.');
  process.exit(1);
}

const BASE = `https://api.cloudflare.com/client/v4/accounts/${ACCOUNT}/storage/kv/namespaces/${NAMESPACE}`;

async function kvPut(key, value) {
  const res = await fetch(`${BASE}/values/${encodeURIComponent(key)}`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${TOKEN}`, 'Content-Type': 'application/json' },
    body: value,
  });
  const j = await res.json();
  if (!j.success) throw new Error(`KV put failed for ${key}: ${JSON.stringify(j.errors)}`);
}

async function kvGet(key) {
  const res = await fetch(`${BASE}/values/${encodeURIComponent(key)}`, {
    headers: { Authorization: `Bearer ${TOKEN}` },
  });
  if (!res.ok) return null;
  return await res.text();
}

async function kvList(prefix) {
  const out = [];
  let cursor = '';
  do {
    const url = `${BASE}/keys?limit=1000&prefix=${encodeURIComponent(prefix)}${cursor ? `&cursor=${cursor}` : ''}`;
    const res = await fetch(url, { headers: { Authorization: `Bearer ${TOKEN}` } });
    const j = await res.json();
    if (!j.success) throw new Error(`KV list failed: ${JSON.stringify(j.errors)}`);
    out.push(...j.result.map((k) => k.name));
    cursor = j.result_info.cursor || '';
  } while (cursor);
  return out;
}

function newKey() {
  return crypto.randomBytes(16).toString('hex'); // 32 hex chars
}

function putKey(key, record) {
  return kvPut(`lic:${key}`, JSON.stringify(record));
}

async function main() {
  const [cmd, arg] = process.argv.slice(2);

  if (cmd === 'issue') {
    const n = Math.max(1, parseInt(arg || '1', 10));
    for (let i = 0; i < n; i++) {
      const key = newKey();
      const record = {
        plan: 'pro-yearly',
        created_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 365 * 86400 * 1000).toISOString(),
        status: 'active',
        devices: [],
      };
      await putKey(key, record);
      console.log(key);
    }
    return;
  }

  if (cmd === 'revoke') {
    if (!/^[a-f0-9]{32}$/.test(arg || '')) {
      console.error('Usage: license-admin.js revoke <32-hex-key>');
      process.exit(1);
    }
    let rec = { devices: [] };
    try {
      const raw = await kvGet(`lic:${arg}`);
      if (raw) rec = JSON.parse(raw);
    } catch {}
    rec.status = 'revoked';
    await putKey(arg, rec);
    console.log(`Revoked ${arg}`);
    return;
  }

  if (cmd === 'list') {
    const names = await kvList('lic:');
    for (const name of names) {
      const key = name.slice(4);
      let rec;
      try { rec = JSON.parse(await kvGet(name)); } catch { rec = {}; }
      console.log(`${key}  status=${rec.status || '?'}  expires=${rec.expires_at || '?'}  devices=${(rec.devices || []).length}`);
    }
    if (!names.length) console.log('(no lic: keys)');
    return;
  }

  console.error('Unknown command. Use: issue [N] | revoke <key> | list');
  process.exit(1);
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
