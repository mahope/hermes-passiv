/**
 * cookie-consent-banner.js
 * Lightweight, GDPR-compliant cookie consent banner.
 * Zero dependencies, no tracking, ~2.5 KB minified.
 *
 * Usage:
 *   <script src="https://hermes-passiv.pages.dev/downloads/cookie-consent-banner.js"
 *           data-site-name="My Website"></script>
 *
 * The banner shows once, sets a consent cookie, and hides for 365 days.
 * No external requests at any time.
 *
 * Customisation — data attributes on the <script> tag:
 *   data-site-name       — Your site name (default: "This website")
 *   data-position        — "bottom" (default) or "top"
 *   data-accept-text     — Button text (default: "Accept All")
 *   data-necessary-text  — Optional: "Necessary Only" button text (default: none — shows accept-only)
 *   data-policy-url      — Link to privacy policy (default: none — no link shown)
 *   data-cookie-name     — Name for the consent cookie (default: "cc_consent")
 *   data-storage-days    — How long consent lasts (default: 365)
 *
 * License: MIT
 */
(function () {
  'use strict';

  var script = document.currentScript;
  if (!script) return;

  var opts = {
    siteName: script.getAttribute('data-site-name') || 'This website',
    position: script.getAttribute('data-position') || 'bottom',
    acceptText: script.getAttribute('data-accept-text') || 'Accept All',
    necessaryText: script.getAttribute('data-necessary-text') || '',
    policyUrl: script.getAttribute('data-policy-url') || '',
    cookieName: script.getAttribute('data-cookie-name') || 'cc_consent',
    storageDays: parseInt(script.getAttribute('data-storage-days'), 10) || 365,
  };

  // Already consented?
  function getCookie(name) {
    var match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : null;
  }

  if (getCookie(opts.cookieName)) return;

  // Build banner
  var banner = document.createElement('div');
  banner.id = 'cc-banner';
  banner.setAttribute('role', 'dialog');
  banner.setAttribute('aria-label', 'Cookie consent');
  banner.style.cssText =
    'position:fixed;left:0;right:0;z-index:999999;padding:14px 20px;' +
    'background:#fff;color:#222;font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;' +
    'box-shadow:0 -2px 12px rgba(0,0,0,.15);display:flex;align-items:center;justify-content:center;' +
    'gap:20px;flex-wrap:wrap;' +
    (opts.position === 'top' ? 'top:0' : 'bottom:0');

  var text = document.createElement('span');
  text.style.cssText = 'max-width:640px;font-size:13px;line-height:1.5;color:#444;';
  text.innerHTML = opts.siteName + ' uses cookies to improve your experience. ' +
    (opts.policyUrl
      ? '<a href="' + opts.policyUrl + '" style="color:#1a73e8;text-decoration:underline;">Privacy policy</a>. '
      : '') +
    'By clicking accept you consent to all cookies.';

  var btnWrap = document.createElement('span');
  btnWrap.style.cssText = 'display:flex;gap:10px;align-items:center;';

  function accept(level) {
    var expires = new Date(Date.now() + opts.storageDays * 864e5).toUTCString();
    document.cookie = opts.cookieName + '=' + encodeURIComponent(level) +
      '; expires=' + expires + '; path=/; SameSite=Lax';
    banner.remove();
  }

  if (opts.necessaryText) {
    var necessaryBtn = document.createElement('button');
    necessaryBtn.textContent = opts.necessaryText;
    necessaryBtn.style.cssText =
      'padding:8px 18px;background:#f0f0f0;color:#333;border:1px solid #ddd;border-radius:6px;' +
      'cursor:pointer;font-size:13px;font-weight:600;';
    necessaryBtn.addEventListener('click', function () { accept('necessary'); });
    btnWrap.appendChild(necessaryBtn);
  }

  var acceptBtn = document.createElement('button');
  acceptBtn.textContent = opts.acceptText;
  acceptBtn.style.cssText =
    'padding:8px 22px;background:#1a73e8;color:#fff;border:none;border-radius:6px;' +
    'cursor:pointer;font-size:13px;font-weight:600;';
  acceptBtn.addEventListener('click', function () { accept('all'); });
  btnWrap.appendChild(acceptBtn);

  banner.appendChild(text);
  banner.appendChild(btnWrap);
  document.body.appendChild(banner);
})();
