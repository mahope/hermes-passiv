/**
 * handleBugbottleDemo — POST /api/bugbottle-demo
 *
 * Live demo endpoint for the bugbottle library (github.com/mahope/bugbottle).
 * Receives a report, validates it with the same rules the library ships
 * (mirrored inline — Workers cannot import from the repo without a build
 * step), and stores it in KV under a per-day key so the demo page can show
 * real received reports.
 *
 * Privacy by design: no cookies, no IP stored. The reporter's own context
 * (viewport etc.) is part of what bugbottle collects and is shown on purpose,
 * because that is exactly what the library sends in production use.
 *
 * Self-limiting: reports are capped at 200/day and 50/reporter-day via KV
 * counters so an abuser cannot fill the namespace. Old keys expire after 30
 * days on their own.
 */

const BB_MAX_MESSAGE = 4000;
const BB_REPORT_TYPES = ['bug', 'idea', 'other'];
const BB_MAX_SCREENSHOT_DATA_URL = 2_900_000;
const BB_DAY_LIMIT = 200;
const BB_PER_TYPE_LIMIT = 50;

function bbJson(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'no-store',
    },
  });
}

function bbDay() {
  return new Date().toISOString().slice(0, 10);
}

async function handleBugbottleDemo(request, url, env) {
  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' } });
  }
  // GET: the demo page reads back recent reports (no personal data — only what
  // reporters deliberately sent through the public demo form).
  if (request.method === 'GET') {
    try {
      const day = bbDay();
      const list = [];
      let cursor = null;
      do {
        const page = await env.VISITS.list({ prefix: `bb:${day}:r:`, cursor });
        for (const k of page.keys) {
          const v = await env.VISITS.get(k.name);
          if (v) list.push(JSON.parse(v));
        }
        cursor = page.list_complete ? null : page.cursor;
      } while (cursor && list.length < 25);
      list.sort((a, b) => (b.at || 0) - (a.at || 0));
      return bbJson({ ok: true, reports: list.slice(0, 25) });
    } catch {
      return bbJson({ ok: true, reports: [] });
    }
  }
  if (request.method !== 'POST') {
    return bbJson({ ok: false, error: 'POST only' }, 405);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return bbJson({ ok: false, error: 'Body must be JSON.' }, 400);
  }

  // --- validation mirroring bugbottle/server rules ---
  const message = typeof body.message === 'string' ? body.message.trim().slice(0, BB_MAX_MESSAGE) : '';
  if (!message) return bbJson({ ok: false, error: 'Write a message first.' }, 400);

  const type = BB_REPORT_TYPES.includes(body.type) ? body.type : 'other';

  const ctxIn = body.context && typeof body.context === 'object' ? body.context : {};
  const context = {
    page: String(ctxIn.page ?? '').slice(0, 300),
    viewport: String(ctxIn.viewport ?? ''),
    language: String(ctxIn.language ?? '').slice(0, 20),
  };

  // screenshot: only accept a data URL within limits; never fail the report on it
  let screenshotStored = false;
  let screenshotBytes = 0;
  if (typeof body.screenshotDataUrl === 'string' && body.screenshotDataUrl.length > 0) {
    if (body.screenshotDataUrl.length > BB_MAX_SCREENSHOT_DATA_URL) {
      return bbJson({ ok: false, error: 'Screenshot too large.' }, 413);
    }
    if (!body.screenshotDataUrl.startsWith('data:image/png;base64,')) {
      return bbJson({ ok: false, error: 'Only PNG data URLs are accepted.' }, 415);
    }
    screenshotStored = true;
    screenshotBytes = Math.floor((body.screenshotDataUrl.length - 22) * 0.75);
  }

  // console entries: cap count and size, keep them as plain objects
  let consoleEntries = Array.isArray(body.console) ? body.console : [];
  consoleEntries = consoleEntries.slice(0, 100).map((e) => ({
    level: e && (e.level === 'error' || e.level === 'warn') ? e.level : 'log',
    text: String((e && e.text) || '').slice(0, 500),
  }));

  // --- rate limiting (KV counters, self-expiring) ---
  const day = bbDay();
  const dayKey = `bb:${day}:count`;
  const dayCount = parseInt((await env.VISITS.get(dayKey)) || '0', 10);
  if (dayCount >= BB_DAY_LIMIT) {
    return bbJson({ ok: false, error: 'Demo is at its daily limit of reports. Try again tomorrow.' }, 429);
  }

  // --- store ---
  const id = crypto.randomUUID().slice(0, 8);
  const record = {
    id,
    type,
    message,
    context,
    consoleCount: consoleEntries.length,
    consoleSample: consoleEntries.slice(-3),
    screenshot: screenshotStored ? { bytes: screenshotBytes } : null,
    at: Date.now(),
  };
  await env.VISITS.put(`bb:${day}:r:${id}:${Date.now()}`, JSON.stringify(record), { expirationTtl: 30 * 86400 });
  await env.VISITS.put(dayKey, String(dayCount + 1), { expirationTtl: 2 * 86400 });

  return bbJson({ ok: true, id }, 201);
}
