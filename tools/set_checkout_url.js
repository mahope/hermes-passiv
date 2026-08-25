#!/usr/bin/env node
/**
 * set_checkout_url.js — inject the Lemon Squeezy checkout URL into
 * site/clean-copy-tool.html (the Pro buy button). Run BEFORE deploy once
 * a real checkout exists. Run with no argument to remove the link again.
 *
 * Usage:  node tools/set_checkout_url.js "https://xxx.lemonsqueezy.com/buy/yyy"
 *         node tools/set_checkout_url.js          # clear
 */

const fs = require('fs');
const path = require('path');

const FILE = path.join(__dirname, '..', 'site', 'clean-copy-tool.html');
const MARKER = /var PRO_CHECKOUT_URL = '[^']*';/;

const url = process.argv[2] || '';
if (url && !/^https:\/\/[a-z0-9.-]+lemonsqueezy\.com\//i.test(url)) {
  console.error('Refusing: URL does not look like a Lemon Squeezy checkout link.');
  process.exit(1);
}

let html = fs.readFileSync(FILE, 'utf8');
if (!MARKER.test(html)) {
  console.error('PRO_CHECKOUT_URL placeholder not found in clean-copy-tool.html');
  process.exit(1);
}
html = html.replace(MARKER, `var PRO_CHECKOUT_URL = '${url}';`);
fs.writeFileSync(FILE, html);
console.log(url ? `Checkout URL set: ${url}` : 'Checkout URL cleared (buy button hidden).');
