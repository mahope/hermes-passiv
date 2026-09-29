/* net.js — the one POST helper our own worker is called through.
 *
 * It used to be copied inline into every client that talks to a worker route
 * (/api/compliance-ai, /api/waitlist, /api/header-check …). Four near-identical
 * copies meant one fix had to be made four times, and a DA copy that nobody
 * remembered had already drifted by a single string. The behaviour is what a
 * visitor sees when we have a bad day, so it lives here once and is judged by
 * the sandbox in tests/scan-clients.test.mjs for every caller.
 *
 * The rule it encodes: a 5xx, an unreadable body and a broken connection are
 * all *ours* to retry, and only a real 4xx is final. Cloudflare answers a
 * crashed worker with an HTML page, so a bare `res.json()` throws and the catch
 * blames the visitor's Wi-Fi for our own outage.
 *
 * A 429 used to sit on the retry side. It is final: the server already said how
 * long it lasts ("try again later", "resets at midnight UTC") and the counter it
 * counts is the visitor's own hourly/daily allowance. Retrying spends the
 * visitor's remaining budget on answers the server has already refused to give,
 * so the error carries the server's own sentence and the page shows it. Retrying
 * it was also what made the AI quota look full: three client retries on one
 * question burned three of the twenty daily slots before any answer came back.
 */
(function (global) {
  'use strict';

  function postJSON(path, payload) {
    return fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).catch(function (e) {
      // The call never left. Not our server's fault, but a broken connection is
      // still worth one more try.
      var err = new Error((e && e.message) || 'connection failed');
      err.transport = true;
      err.transient = true;
      throw err;
    }).then(function (res) {
      return res.json().catch(function () { return null; }).then(function (data) {
        if (res.ok && data) return data;
        var err = new Error((data && data.error) || ('Server replied with ' + res.status));
        err.status = res.status;
        err.limited = res.status === 429;
        // No body means the answer was not ours to read, so it is transient by
        // definition whatever status the edge reported — including a 429 whose
        // body the edge stripped, which is the one case we may not treat as
        // final, because then we would have no sentence to show.
        err.transient = !data || res.status >= 500;
        throw err;
      });
    });
  }

  // One backoff for every caller: 1200 ms, then 2400 ms. `maxTries` counts the
  // first attempt too, so 3 means "try, then try twice more".
  function ask(path, payload, maxTries) {
    var tries = 0;
    function attempt() {
      return postJSON(path, payload).catch(function (err) {
        if (err.transient && ++tries < maxTries) {
          return new Promise(function (res) { setTimeout(res, 1200 * tries); }).then(attempt);
        }
        throw err;
      });
    }
    return attempt();
  }

  global.NET = global.NET || {};
  global.NET.postJSON = postJSON;
  global.NET.ask = ask;
})(typeof window !== 'undefined' ? window : globalThis);
