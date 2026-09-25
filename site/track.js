/**
 * track.js — cookieless visit counter.
 * No cookies, no localStorage. Sends one beacon per page view.
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
  } catch (e) { /* analytics must never break the page */ }
})();
