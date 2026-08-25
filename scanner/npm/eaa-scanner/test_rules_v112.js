#!/usr/bin/env node
'use strict';
/**
 * New checks added to the core (iteration 75):
 *  - INPUT_TYPE_IMAGE_ALT   (WCAG 1.1.1) <input type=image> without alt
 *  - AUDIO_CAPTIONS         (WCAG 1.2.2) <audio> without a captions/transcript track
 *  - VIDEO_TRACKS           (WCAG 1.2.2) <video> without any <track kind=captions|subtitles>
 *  - AUTOPLAY_MEDIA         (WCAG 1.4.2) audio/video that autoplays and cannot be paused
 *  - MARQUEE_BLINK          (WCAG 2.2.2) deprecated blinking/moving content elements
 *  - POSITIVE_TABINDEX      (WCAG 2.4.3) tabindex greater than 0
 * All are pure-HTML checks: no JS execution, no external requests.
 */
const { scanHtml } = require('./index.js');
const assert = require('assert');

let pass = 0, fail = 0;
function check(name, html, ruleId, expectedCount, severity) {
  const rep = scanHtml(html);
  const f = rep.findings.find(x => x.rule_id === ruleId);
  try {
    if (expectedCount === 0) {
      assert.ok(!f || f.count === undefined, `${name}: expected no ${ruleId}, got ${JSON.stringify(f)}`);
    } else {
      assert.ok(f, `${name}: ${ruleId} finding missing`);
      assert.strictEqual(f.count, expectedCount, `${name}: count`);
      if (severity) assert.strictEqual(f.severity, severity, `${name}: severity`);
    }
    console.log(`PASS ${name} (${ruleId})`);
    pass++;
  } catch (e) { console.log(`FAIL ${name}: ${e.message}`); fail++; }
}

// --- INPUT_TYPE_IMAGE_ALT ---
check('input-image-no-alt',
  '<html lang="en"><head><title>T</title></head><body><input type="image" src="go.png"></body></html>',
  'INPUT_TYPE_IMAGE_ALT', 1, 'error');
check('input-image-with-alt',
  '<html lang="en"><head><title>T</title></head><body><input type="image" src="go.png" alt="Go"></body></html>',
  'INPUT_TYPE_IMAGE_ALT', 0);

// --- VIDEO_TRACKS ---
check('video-no-track',
  '<html lang="en"><head><title>T</title></head><body><video src="v.mp4"></video></body></html>',
  'VIDEO_TRACKS', 1, 'error');
check('video-with-captions',
  '<html lang="en"><head><title>T</title></head><body><video src="v.mp4"><track kind="captions" src="c.vtt"></video></body></html>',
  'VIDEO_TRACKS', 0);

// --- AUDIO_TRANSCRIPT ---
check('audio-no-alternative',
  '<html lang="en"><head><title>T</title></head><body><audio src="a.mp3" controls></audio></body></html>',
  'AUDIO_TRANSCRIPT', 1, 'warning');
check('audio-ok', // aria-label describing transcript link counts as alternative signal
  '<html lang="en"><head><title>T</title></head><body><audio src="a.mp3" controls aria-label="Podcast episode 1, transcript available below"></audio></body></html>',
  'AUDIO_TRANSCRIPT', 0);

// --- AUTOPLAY_MEDIA ---
check('autoplay-audio-no-controls',
  '<html lang="en"><head><title>T</title></head><body><audio src="a.mp3" autoplay></audio></body></html>',
  'AUTOPLAY_MEDIA', 1, 'error');
check('autoplay-with-controls',
  '<html lang="en"><head><title>T</title></head><body><audio src="a.mp3" autoplay controls></audio></body></html>',
  'AUTOPLAY_MEDIA', 0);
check('muted-autoplay-video-ok',
  '<html lang="en"><head><title>T</title></head><body><video src="v.mp4" autoplay muted></video></body></html>',
  'AUTOPLAY_MEDIA', 0);

// --- MARQUEE_BLINK ---
check('marquee-and-blink',
  '<html lang="en"><head><title>T</title></head><body><marquee>news</marquee><p style="text-decoration:blink">old</p></body></html>',
  'MARQUEE_BLINK', 2, 'error');
check('clean-page-no-marquee',
  '<html lang="en"><head><title>T</title></head><body><p>fine</p></body></html>',
  'MARQUEE_BLINK', 0);

// --- POSITIVE_TABINDEX ---
check('positive-tabindex',
  '<html lang="en"><head><title>T</title></head><body><a href="/x" tabindex="3">x</a></body></html>',
  'POSITIVE_TABINDEX', 1, 'warning');
check('tabindex-zero-fine',
  '<html lang="en"><head><title>T</title></head><body><a href="/x" tabindex="0">x</a></body></html>',
  'POSITIVE_TABINDEX', 0);

// --- regression: existing rules still fire on the old smoke fixture ---
const reg = scanHtml(`<html lang="en"><head><title>T</title></head><body>
<h1>Hi</h1><img src="x.png"><input type="text" name="q"><a href="/a"></a>
<button></button><div id="d"></div><div id="d"></div>
<iframe src="//x.com/e"></iframe><table><tr><td>a</td></tr></table></body></html>`);
const ids = new Set(reg.findings.map(f => f.rule_id));
for (const want of ['IMG_ALT','FORM_LABEL','LINK_TEXT','BUTTON_TEXT','DUP_ID','IFRAME_TITLE','TABLE_HEADER']) {
  try { assert.ok(ids.has(want), `regression: ${want} missing`); console.log(`PASS regression ${want}`); pass++; }
  catch (e) { console.log(`FAIL ${e.message}`); fail++; }
}
// clean page should score 100 / grade A with zero findings
const clean = scanHtml('<!DOCTYPE html><html lang="en"><head><title>Ok</title><meta name="viewport" content="width=device-width"></head><body><h1>Hello</h1><p>World</p></body></html>');
try {
  assert.strictEqual(clean.findings.length, 0);
  assert.strictEqual(clean.score, 100);
  assert.strictEqual(clean.grade, 'A');
  console.log('PASS clean page = 100/A'); pass++;
} catch (e) { console.log(`FAIL clean page: ${JSON.stringify(clean.findings)} score=${clean.score}`); fail++; }

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
