/* Clean Copy — canonical license client rules.
 *
 * This file is the single source of truth for how a Clean Copy client talks
 * to the license API. It is inlined verbatim into every shipped client
 * (Chrome extension, Firefox add-on, Obsidian plugin, web tool);
 * `tools/check_license_clients.py` fails if a copy drifts from these bytes.
 *
 * Contract (24/9-2026): keys are 32 lowercase hex characters, product is
 * `clean-copy-pro`, and a paying customer must never be locked out by a
 * license-server outage — hence the seven-day positive cache.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.CleanCopyLicense = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var PRODUCT = 'clean-copy-pro';
  var API_BASE = 'https://mahope.tools/api/license';
  var CACHE_MAX_MS = 7 * 24 * 60 * 60 * 1000;

  function normalizeKey(key) {
    return String(key === null || key === undefined ? '' : key).trim().toLowerCase();
  }

  function isKeyFormat(key) {
    return /^[a-f0-9]{32}$/.test(normalizeKey(key));
  }

  // status 0 = the request never got an answer (offline, DNS, timeout).
  function isServerError(status) {
    return status === 0 || status >= 500;
  }

  /* Decide what a client shows, from one HTTP exchange.
   * opts: { status, data, checkedAt, expiresAt, now }
   * Returns { active, message, cached, checkedAt, expiresAt }. */
  function decide(opts) {
    var status = opts.status;
    var data = opts.data || {};
    var now = typeof opts.now === 'number' ? opts.now : Date.now();
    var checkedAt = typeof opts.checkedAt === 'number' ? opts.checkedAt : 0;

    if (status === 200 && data.ok && (data.activated === true || data.valid === true)) {
      return {
        active: true, message: '', cached: false,
        checkedAt: now, expiresAt: data.expires_at || opts.expiresAt || ''
      };
    }

    if (isServerError(status)) {
      if (checkedAt > 0 && now - checkedAt <= CACHE_MAX_MS) {
        return {
          active: true, cached: true, checkedAt: checkedAt,
          expiresAt: opts.expiresAt || '',
          message: 'License server unreachable — Pro stays active until ' +
            new Date(checkedAt + CACHE_MAX_MS).toISOString().slice(0, 10) + '.'
        };
      }
      return {
        active: false, cached: false, checkedAt: 0, expiresAt: '',
        message: 'License server unreachable. Try again later — Pro comes back on its own.'
      };
    }

    if (status === 409) {
      return { active: false, message: data.error || 'Device limit reached for this license.', checkedAt: 0, expiresAt: '' };
    }
    if (status === 403) {
      return { active: false, message: data.error || 'This license is expired, revoked, or for another product.', checkedAt: 0, expiresAt: '' };
    }
    if (status === 404) {
      return { active: false, message: data.error || 'License key not found.', checkedAt: 0, expiresAt: '' };
    }
    if (status === 400) {
      return { active: false, message: data.error || 'Invalid license key.', checkedAt: 0, expiresAt: '' };
    }
    if (status === 200) {
      return {
        active: false, message: data.reason === 'device_limit'
          ? 'Device limit reached for this license.'
          : (data.error || 'This license is not valid anymore.'),
        checkedAt: 0, expiresAt: ''
      };
    }
    return { active: false, message: data.error || 'License check failed. Try again.', checkedAt: 0, expiresAt: '' };
  }

  function payload(key, deviceId) {
    return { license_key: normalizeKey(key), device_id: String(deviceId || ''), product: PRODUCT };
  }

  return {
    PRODUCT: PRODUCT, API_BASE: API_BASE, CACHE_MAX_MS: CACHE_MAX_MS,
    normalizeKey: normalizeKey, isKeyFormat: isKeyFormat,
    isServerError: isServerError, decide: decide, payload: payload
  };
});
