/**
 * track.js — cookieless visit counter.
 * No cookies, no localStorage. Sends one beacon per page view,
 * plus one `buy-click` per click on a Stripe checkout link.
 */
(function () {
  var noop = function () {};
  window.trackEvent = window.trackEvent || noop;
  if (window.__hermesTrackLoaded) return;
  window.__hermesTrackLoaded = true;
  try {
    var dnt = navigator.doNotTrack === '1' || navigator.doNotTrack === 'yes' || window.doNotTrack === '1';
    var gpc = navigator.globalPrivacyControl === true;
    if (dnt || gpc) return;
    var p = location.pathname;
    if (p === '/api/track' || p === '/api/stats' || p === '/stats') return;
    var body = JSON.stringify({ path: p });
    var sent = false;
    function send() {
      if (sent) return; sent = true;
      fetch('/api/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body,
        keepalive: true,
      }).catch(function () {});
    }
    if (document.visibilityState === 'visible') send();
    else document.addEventListener('visibilitychange', send, { once: true });

  // Public helper: track a real tool interaction (event name: lowercase letters/digits/dash).
  window.trackEvent = function (event) {
    try {
      fetch('/api/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: location.pathname, event: event }),
        keepalive: true,
      }).catch(function () {});
    } catch (e) { /* analytics must never break the page */ }
  };

  // Every click on a link to one of the family's own tools counts as
  // `cta-<tool>`. Delegated, so a page needs no per-button code.
  //
  // Why here and not in each page: measured 28/9, 77 pages in `site/` link to
  // a family tool and had no tracker at all — the two homepages, /guides, and
  // 61 blog posts among them. Every click from those was invisible. 70 of the
  // 77 already load this file, so one delegated listener here covers them all.
  //
  // Why the guard: 205 other pages carry their own inline tracker with the same
  // whitelist, and they load this file too. Two listeners would send the event
  // twice, so `recordTraffic` would count one click as two. The inline tracker
  // leaves no global to test, so we look for its own marker in the parsed
  // inline scripts. Deferred, so by click time the document is parsed and the
  // test is exact — it is not a heuristic about how the page was built.
  var CTA_MARKER = "event:'cta-'";
  // The family's own four domains, as an *optional* prefix.
  //
  // Measured 28/9 in the built `dist/`, not in `site/`: the build rewrites
  // cross-domain links to absolute URLs, so a post on mahope.tools links to
  // `https://deskuptime.com/`, not `/deskuptime`. A pattern anchored at `^\/`
  // cannot match one of them, and 2020 of the links that pointed at another
  // tool in the family were absolute. A click to any other tool was invisible.
  //
  // The four domains are written out, not matched loosely, so a link to
  // `https://deskuptime.com.evil.tld/scan` still sends nothing.
  var CTA_PATHS = /^(?:https?:\/\/(?:mahope\.tools|cleancopy\.tools|deskuptime\.com|bugbottle\.dev))?\/(?:da\/)?(scan|scan-da|clean-copy-tool|page-profile|site-icons|text-diff|url-to-markdown|free-tools|compliance-report|compliance-ai|compliance-guide|compliance-site-check|paid-templates|deskuptime)(\.html)?\/?(#.*)?$/;
  // The four homepages carry no slug — the host *is* the name. 1706 links go
  // there, more than to every tool put together, and none of them counted.
  // `mahope.tools` -> `cta-mahope`, `deskuptime.com` -> `cta-deskuptime`.
  var CTA_HOME = /^https?:\/\/(mahope\.tools|cleancopy\.tools|deskuptime\.com|bugbottle\.dev)\/(?:da\/)?(?:#.*)?$/;
  function hasInlineCtaTracker() {
    var scripts = document.getElementsByTagName('script');
    for (var i = 0; i < scripts.length; i++) {
      var s = scripts[i];
      if (s.src) continue;
      if ((s.textContent || s.innerHTML || '').indexOf(CTA_MARKER) !== -1) return true;
    }
    return false;
  }
  var inlineCta = null; // decided on first click, not on load
  document.addEventListener('click', function (e) {
    try {
      if (inlineCta === null) inlineCta = hasInlineCtaTracker();
      if (inlineCta) return;
      var el = e.target;
      while (el && el.tagName !== 'A') el = el.parentNode;
      var raw = el && el.getAttribute ? el.getAttribute('href') : null;
      if (!raw) return;
      var m = CTA_PATHS.exec(raw);
      var name = m ? m[1] : null;
      if (!name) {
        var home = CTA_HOME.exec(raw);
        if (!home) return;
        name = home[1].replace(/\.[a-z]+$/, '');
      }
      var payload = JSON.stringify({ path: p, event: 'cta-' + name });
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/api/track', new Blob([payload], { type: 'application/json' }));
      } else {
        window.trackEvent('cta-' + name);
      }
    } catch (err) { /* analytics must never break the page */ }
  }, true);

  // Every Stripe checkout link counts as a `buy-click`. Delegated, so a page
  // needs no per-button code, and sendBeacon because the click leaves for
  // Stripe immediately — this is the last step of the funnel we can see.
  document.addEventListener('click', function (e) {
    try {
      var node = e.target;
      while (node && node.tagName !== 'A') node = node.parentNode;
      var href = node && node.getAttribute ? node.getAttribute('href') : null;
      if (!href || !/^https:\/\/(buy|donate)\.stripe\.com\//.test(href)) return;
      var body = JSON.stringify({ path: location.pathname, event: 'buy-click' });
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/api/track', new Blob([body], { type: 'application/json' }));
      } else {
        window.trackEvent('buy-click');
      }
    } catch (err) { /* analytics must never break the page */ }
  }, true);
  } catch (e) { /* analytics must never break the page */ }
})();
