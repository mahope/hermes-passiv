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
 *
 * The six GET clients — `/compliance-site-check` (EN+DA), `/page-profile`
 * (EN+DA), `/security-headers-check` and `/url-inspector` — had each written
 * their own copy of the rule below, in two variants of the same call, which is
 * what let a DA copy drift by a single string before anyone noticed. They read
 * the rule from here now, through `getJSON`/`askGet`. `tools/check_net_copies.py`
 * judges that, and `tests/scan-clients.test.mjs` proves it by breaking this file
 * and watching all six go red.
 */
(function (global) {
  'use strict';

  // The one place a response becomes either data or a typed error. Every caller
  // reads status before body, so Cloudflare's HTML page for a crashed worker is
  // our outage and not the visitor's Wi-Fi.
  function readResponse(res) {
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
  }

  // A connection that never arrived is not our server's fault, but a broken
  // connection is still worth one more try.
  function fromTransport(e) {
    var err = new Error((e && e.message) || 'connection failed');
    err.transport = true;
    err.transient = true;
    throw err;
  }

  function postJSON(path, payload) {
    return fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).catch(fromTransport).then(readResponse);
  }

  // The same rule for the tools that scan a URL and therefore have to GET. They
  // used to inline their own status-first chain; six copies of one judgement is
  // six chances to disagree about what a visitor is shown when we are down.
  function getJSON(path) {
    return fetch(path).catch(fromTransport).then(readResponse);
  }

  // One backoff for every caller: 1200 ms, then 2400 ms. `maxTries` counts the
  // first attempt too, so 3 means "try, then try twice more". `onRetry(tries,
  // waitMs)` runs while we are waiting, so a page can say so instead of leaving
  // the visitor looking at a spinner that looks stuck.
  function withBackoff(run, maxTries, onRetry) {
    var tries = 0;
    function attempt() {
      return run().catch(function (err) {
        if (err.transient && ++tries < maxTries) {
          var wait = 1200 * tries;
          if (onRetry) { try { onRetry(tries, wait); } catch (e) { /* kosmetik */ } }
          return new Promise(function (res) { setTimeout(res, wait); }).then(attempt);
        }
        throw err;
      });
    }
    return attempt();
  }

  function ask(path, payload, maxTries) {
    return withBackoff(function () { return postJSON(path, payload); }, maxTries);
  }

  function askGet(path, maxTries, onRetry) {
    return withBackoff(function () { return getJSON(path); }, maxTries, onRetry);
  }

  global.NET = global.NET || {};
  global.NET.postJSON = postJSON;
  global.NET.getJSON = getJSON;
  global.NET.ask = ask;
  global.NET.askGet = askGet;
})(typeof window !== 'undefined' ? window : globalThis);
