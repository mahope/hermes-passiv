#!/usr/bin/env node
/**
 * build_obsidian_bundle.js — produce a self-contained main.js for the
 * Obsidian plugin by inlining core.js at the require site.
 *
 * Why: GitHub release assets are copied individually into .obsidian/plugins/
 * clean-copy-obsidian/. A main.js that does require('./core.js') breaks when
 * the user grabs only the listed assets (main.js/manifest.json/styles.css).
 * Inlining removes the second file entirely.
 *
 * Usage: node tools/build_obsidian_bundle.js [outdir]
 * Writes: <outdir>/main.js   (bundled)
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const PLUGIN = path.join(ROOT, 'obsidian-plugin');
const outdir = process.argv[2] || PLUGIN;

const mainSrc = fs.readFileSync(path.join(PLUGIN, 'main.js'), 'utf8');
const coreSrc = fs.readFileSync(path.join(PLUGIN, 'core.js'), 'utf8');

if (!mainSrc.includes("require('./core.js')")) {
  console.error('bundle: require("./core.js") not found — main.js changed?');
  process.exit(1);
}

// Sandbox the UMD core: give it a fake module so its module.exports branch
// fires regardless of the host environment (Obsidian eval context).
const inlined =
  'var CleanCopyCore = (function () {\n' +
  '  var module = { exports: {} };\n' +
  coreSrc +
  '\n  return module.exports;\n})();';

const bundled = mainSrc.replace("var CleanCopyCore = require('./core.js');",
  () => inlined);  // function replacer: core source is inserted literally

fs.mkdirSync(outdir, { recursive: true });
fs.writeFileSync(path.join(outdir, 'main.js'), bundled);
console.log('bundled main.js ->', path.join(outdir, 'main.js'),
  '(' + bundled.length + ' bytes)');
