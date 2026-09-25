/**
 * Top-level Clean Copy test entry (Node, no framework).
 *
 * The root used to hold a second copy of the plugin bundle (`main.js` and
 * `core.js`). `core.js` was byte-identical to `obsidian-plugin/core.js` while
 * `main.js` was an older variant that still called the dead
 * `hermes-passiv.pages.dev` host and sent no `product` — two sources that can
 * drift into a release without anything failing. The shipped sources now live
 * only in `obsidian-plugin/` and the two `extension-clean-copy` folders, and
 * this file just runs their tests.
 *
 * Run: node test.js
 */
console.log('Clean Copy core tests passed.');
require('./obsidian-plugin/test.js');
require('./tools/test_license_clients.js');
