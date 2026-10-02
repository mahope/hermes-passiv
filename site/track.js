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
  // `free-downloads` was measured nowhere on 28/9: the port's `tool_paths` set
  // is built from the whitelists, so a path no page measures is invisible to
  // it — it cannot warn about clicks that every tracker in the family drops.
  // Six pages link to it, two of them the ones that sell templates.
  //
  // 33 more routes were in the same blind spot, measured the same way by
  // `tools/audit_unmeasured_routes.py`: 2366 links in `dist/` to routes that no
  // tracker in the family measured, so every one of them was dropped. The two
  // largest are the ones that sell — `/books`, the e-book shop, 613 inbound
  // links — and `/blog`, the engine that feeds it, 875. You cannot improve a
  // funnel you cannot see, and the funnel's two biggest steps were invisible.
  //
  // `/privacy` and `/terms` are measured on purpose *not*: they sit in the
  // footer of 320 pages, and the pageview beacon already counts every visit to
  // them. A `cta-privacy` on every page load is noise, not a sale.
  //
  // The alternation needs no ordering care here, because it is `$`-anchored:
  // `scan` cannot swallow `/scan-da`, since `-da` cannot match `(\.html)?\/?(#.*)?$`
  // and the engine backtracks. Measured, not assumed — the four earlier
  // iterations that prepended names were fixing a regex that was not anchored
  // the same way.
  // Measured 29/9 i `dist/`: 604 absolutte krydsdomenelinks sendte ingen
  // begivenhed, fordi 21 af ruterne ikke stod her. De var ikke tilfældige —
  // de var to hele klasser, begge med en regel der forklarede dem:
  //
  // 1. **De danske spejlinger med `-da` som *endelse*.** `(?:da\/)?` dækker
  //    `/da/scan`, men ikke `/nis2-check-da` — den danske side hedder sådan, og
  //    `nis2-check` kan ikke sluge `-da`, fordi mønstret er `$`-forankret.
  // 2. **De fem tekstværktøjer fra `/da/blog/7-gratis-dev-tekstvaerktoejer`**
  //    (`word-counter`, `json-formatter`, `case-converter`, `hash-generator`,
  //    `url-encoder-decoder`), som Blog-siden linker til som absolutte URL'er.
  //
  // Plus `support` — donationstrafikken. 60 links pegede på den, og det er den
  // ene rute her der *tjener penge*, så et klik på den var det vigtigste
  // klik at tælle og det eneste der slet ikke blev talt.
  var CTA_PATHS = /^(?:https?:\/\/(?:mahope\.tools|cleancopy\.tools|deskuptime\.com|bugbottle\.dev))?\/(?:da\/)?(scan|scan-da|clean-copy-tool|page-profile|site-icons|text-diff|url-to-markdown|url-til-markdown|free-tools|free-downloads|compliance-report|compliance-ai|compliance-guide|compliance-site-check|paid-templates|deskuptime|books|downloads|blog|wordpress-plugin|activate|license-lookup|mcp|tools|url-inspector|guides|support|accessibility-statement-generator|privacy-notice-generator|privacy-policy-template|privacy-notice-generator-da|privacy-policy-template-da|cookie-check|cookie-check-da|nis2-check|nis2-check-da|nis2-gap-assessment|nis2-gap-assessment-da|nis2-incident-generator|nis2-incident-generator-da|dpa-generator|dpa-generator-da|contrast-checker|contrast-checker-da|color-blindness-simulator|color-blindness-simulator-da|palette-generator|palette-generator-da|ropa-generator|ropa-generator-da|tilgaengelighedserklaering-generator-da|text-on-image-checker|text-on-image-checker-da|markdown-table-generator|uuid-generator|word-counter|json-formatter|case-converter|hash-generator|url-encoder-decoder|bulk-url-checker|security-headers-checker|clean-copy-cli-ref|clean-copy-api|clean-copy-bookmarklet|clean-copy-brew|copy-clean-guide|bugbottle-demo|cookie-consent-banner-demo|pricing)(\.html)?\/?(#.*)?$/;
  // The two sub-pages under `/books/` are two-segment paths, and a group that
  // swallowed the second segment would produce `cta-books/build-your-first-
  // chrome-extension` — which `handleTrack` in `_worker.js` rejects with 400,
  // because an event name is `^[a-z0-9-]+$`. So they get their own pattern and
  // a name that is *prefixed* rather than nested: `cta-books-compliance-
  // bundle`. Measured 29/9 in `dist/` by `tools/audit_dist_cta_routes.py`:
  // 18 absolute cross-domain links to the two book pages, on 18 different
  // pages, sent nothing. They are the pages that sell, so a click on one was
  // the single most valuable click in the family to throw away.
  //
  // Only `/books/<slug>` is added, not a general "any sub-path" rule: that
  // would also make `/blog/*` measurable under the name `blog`, which is a
  // deliberate decision (one bounded name, not one per post) and not this
  // task's to change.
  //
  // The absolute prefix is **optional**, exactly as in `CTA_PATHS`, and that is
  // a fix rather than a style choice. Measured 29/9 in the built `dist/`: the
  // build only rewrites *cross-domain* links, so a book link written on a
  // mahope.tools page stays root-relative — 145 of them, and every one of them
  // was a click on a paid product ($29–$149) that no tracker in the family
  // counted. The absolute-only pattern could not match them, and the inline
  // trackers cannot either: their alternates are `$`-anchored lists of single
  // segments, so a two-segment path falls off the end. Measured with the port's
  // own reader, not by eye: 0 of 182 inline trackers on mahope.tools produce an
  // event for `/books/compliance-bundle`, in either form.
  var CTA_BOOK_PAGES = /^(?:https?:\/\/(?:mahope\.tools|cleancopy\.tools|deskuptime\.com|bugbottle\.dev))?\/(?:da\/)?books\/([a-z0-9-]+)(?:\.html)?\/?(#.*)?$/;
  // The four homepages carry no slug — the host *is* the name. 2184 links go
  // there, more than to every tool put together, and none of them counted.
  // `mahope.tools` -> `cta-mahope`, `deskuptime.com` -> `cta-deskuptime`.
  //
  // Two forms, because the build produces two. `build_sites.py` rewrites a
  // cross-domain link to `https://cleancopy.tools` — no trailing slash — and a
  // page's own home link is root-relative (`/`, `/da/`). The first version
  // required both a scheme *and* a slash after the host, so it matched neither.
  // Measured 28/9 by `tools/check_cta_coverage_dist.py`, which reads the built
  // `dist/` and not `site/`.
  var CTA_HOME = /^(?:https?:\/\/(mahope\.tools|cleancopy\.tools|deskuptime\.com|bugbottle\.dev)(?:\/da)?\/?|\/(?:da\/)?\/?)(?:#.*)?$/;
  // The root-relative form has no host in it, so the listener has to ask where
  // *it* is running. Only the family's own four count: a fork or a
  // `*.pages.dev` preview hostname is not a click we sell anything on.
  //
  // This is the third copy of the same four domains — CTA_PATHS has them as an
  // optional prefix and CTA_HOME in group 1. That duplication is what let the
  // two drift apart, so `check_cta_coverage_dist.py` requires all three to
  // agree, and a fourth host cannot be added to one and forgotten in the rest.
  var CTA_HOSTS = /^(mahope\.tools|cleancopy\.tools|deskuptime\.com|bugbottle\.dev)$/;
  function hasInlineCtaTracker() {
    var scripts = document.getElementsByTagName('script');
    for (var i = 0; i < scripts.length; i++) {
      var s = scripts[i];
      if (s.src) continue;
      if ((s.textContent || s.innerHTML || '').indexOf(CTA_MARKER) !== -1) return true;
    }
    return false;
  }
  // Absolute URL to one of the family's own four domains, with or without a
  // trailing slash. This is the *only* thing `track.js` may take over from a
  // page that has an inline tracker, and the reason is structural, not
  // defensive — see the note on `inlineCta` below.
  var CROSS_DOMAIN = /^https?:\/\/(?:mahope\.tools|cleancopy\.tools|deskuptime\.com|bugbottle\.dev)(?:[/?#]|$)/;
  var inlineCta = null; // decided on first click, not on load
  document.addEventListener('click', function (e) {
    try {
      var el = e.target;
      while (el && el.tagName !== 'A') el = el.parentNode;
      var raw = el && el.getAttribute ? el.getAttribute('href') : null;
      if (!raw) return;
      if (inlineCta === null) inlineCta = hasInlineCtaTracker();
      // Measured 29/9 i `dist/`: 300 absolute cross-domain links
      // sat on 87 pages that carry their own inline tracker, and every one of
      // them was dropped. `track.js` used to bow out of the *whole page* the
      // moment it saw an inline tracker, and the inline tracker reads the raw
      // `getAttribute('href')` through a pattern anchored at `^\/` — so it
      // cannot match a string starting with `https://`. The two sets are
      // disjoint by construction, which is what makes it safe to measure them
      // here: one click, one event, never two.
      //
      // The same argument is why `/books/<slug>` joins the cross-domain links
      // here, and it is measured rather than assumed: an inline tracker's
      // alternates are single segments in a `$`-anchored list, so **0 of 182**
      // of them on mahope.tools produce an event for `/books/compliance-bundle`
      // — there is no overlap to double-count with. The bail-out is therefore
      // widened to "anything the inline tracker cannot match", not "any URL",
      // and the two clauses are named for the two reasons.
      //
      // The bail-out stays for every other root-relative link, which is the
      // inline tracker's whole job. The target is read *before* this test,
      // because deciding it needed the href in the first place.
      if (inlineCta && !CROSS_DOMAIN.test(raw) && !CTA_BOOK_PAGES.test(raw)) return;
      var m = CTA_PATHS.exec(raw);
      var name = m ? m[1] : null;
      if (!name) {
        // `/books/<slug>` first, so a two-segment path never reaches CTA_HOME
        // and never gets the bare `books` name. The prefix is literal here so
        // the event name stays inside `^[a-z0-9-]+$` — see the comment on
        // CTA_BOOK_PAGES.
        var page = CTA_BOOK_PAGES.exec(raw);
        if (page) name = 'books-' + page[1];
      }
      if (!name) {
        var home = CTA_HOME.exec(raw);
        if (!home) return;
        // Group 1 is the host, but only in the absolute form. `/` and `/da/`
        // resolve to the page's own homepage, so they take the hostname we are
        // running on — and send nothing if that is not one of the four.
        var host = home[1] || location.hostname;
        if (!CTA_HOSTS.exec(host)) return;
        name = host.replace(/\.[a-z]+$/, '');
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
