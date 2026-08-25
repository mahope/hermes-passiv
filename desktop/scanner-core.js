#!/usr/bin/env node
/**
 * eaa-scanner — Universal EAA/WCAG compliance scanner core.
 *
 * JavaScript port of scanner_core.py. Platform-independent: takes raw HTML
 * (from any CMS) and returns a structured JSON report. No dependencies.
 *
 * Checks: IMG_ALT, FORM_LABEL, LINK_TEXT, BUTTON_TEXT, TARGET_BLANK,
 * DUP_ID, IFRAME_TITLE, TABLE_HEADER, DOC_TITLE, HTML_LANG, VIEWPORT,
 * HEADING_H1, HEADING_SKIP, FIXED_PX_FONTS, ARIA_HIDDEN_FOCUS, CONTRAST,
 * INPUT_TYPE_IMAGE_ALT, VIDEO_TRACKS, AUDIO_TRANSCRIPT, AUTOPLAY_MEDIA,
 * MARQUEE_BLINK, POSITIVE_TABINDEX.
 *
 * Kept in sync with scanner/npm/eaa-scanner/index.js (v1.2.0 rule set).
 * Fetching/crawling lives in scanner.js — this file is pure HTML -> report.
 */
'use strict';

const VOID = new Set(['area','base','br','col','embed','hr','img','input',
  'link','meta','param','source','track','wbr']);

// --- minimal HTML tokenizer -------------------------------------------------
function* tokenize(html) {
  // yields {type:'text'|'start'|'end', tag, attrs, selfClosing}
  const re = /<!--[\s\S]*?-->|<!\[CDATA\[[\s\S]*?\]\]>|<!DOCTYPE[^>]*>|<(\/?)([a-zA-Z][a-zA-Z0-9-]*)((?:"[^"]*"|'[^']*'|[^>"'])*?)(\/?)>|([^<]+)/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    if (m[5] !== undefined) { yield { type: 'text', data: m[5] }; continue; }
    const tag = m[2] && m[2].toLowerCase();
    if (!tag) continue;   // comments / CDATA / doctype
    if (!/^[a-z][a-z0-9-]*$/.test(tag)) continue;
    if (m[1]) { yield { type: 'end', tag }; continue; }
    const attrs = [];
    const are = /([a-zA-Z_:@][-\w:.]*)(?:\s*=\s*("[^"]*"|'[^']*'|[^\s"'>]+))?/g;
    let am;
    const attrStr = m[3] || '';
    while ((am = are.exec(attrStr)) !== null) {
      let v = am[2] === undefined ? '' : am[2];
      if (v.startsWith('"') || v.startsWith("'")) v = v.slice(1, -1);
      attrs.push([am[1].toLowerCase(), v]);
    }
    yield { type: 'start', tag, attrs, selfClosing: !!m[4] || VOID.has(tag) };
  }
}

function decodeEntities(s) {
  if (!s.includes('&')) return s;
  const named = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' };
  return s.replace(/&(#x?[0-9a-fA-F]+|[a-zA-Z]+);/g, (all, body) => {
    if (body[0] === '#') {
      const code = body[1] === 'x' || body[1] === 'X'
        ? parseInt(body.slice(2), 16) : parseInt(body.slice(1), 10);
      return Number.isFinite(code) && code > 0 && code < 0x110000
        ? String.fromCodePoint(code) : all;
    }
    return named[body.toLowerCase()] !== undefined ? named[body.toLowerCase()] : all;
  });
}

// --- WCAG 1.4.3 contrast maths ----------------------------------------------
function parseColor(s) {
  s = String(s).trim().toLowerCase();
  if (['transparent','inherit','currentcolor','initial'].includes(s)) return null;
  let m = s.match(/^#([0-9a-f]{3})$/);
  if (m) return [...m[1]].map(c => parseInt(c + c, 16));
  m = s.match(/^#([0-9a-f]{6})/);
  if (m) return [0, 2, 4].map(i => parseInt(m[1].slice(i, i + 2), 16));
  m = s.match(/^rgba?\(([^)]+)\)/);
  if (m) {
    const parts = m[1].split(',').map(p => p.trim());
    if (parts.length >= 4 && parseFloat(parts[3]) < 0.9) return null;
    try {
      return parts.slice(0, 3).map(p =>
        p.endsWith('%') ? parseFloat(p) * 2.55 : parseFloat(p));
    } catch { return null; }
  }
  const named = { white:[255,255,255], black:[0,0,0], red:[255,0,0],
    green:[0,128,0], blue:[0,0,255], gray:[128,128,128], grey:[128,128,128],
    silver:[192,192,192], yellow:[255,255,0], orange:[255,165,0],
    navy:[0,0,128], teal:[0,128,128], purple:[128,0,128], maroon:[128,0,0],
    olive:[128,128,0], lime:[0,255,0], aqua:[0,255,255], cyan:[0,255,255],
    fuchsia:[255,0,255], magenta:[255,0,255] };
  return named[s] || null;
}

function relLum(rgb) {
  const chan = c => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  const [r, g, b] = rgb.map(chan);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrastRatio(fg, bg) {
  const f = parseColor(fg), b = parseColor(bg);
  if (!f || !b || f.some(isNaN) || b.some(isNaN)) return null;
  const lf = relLum(f), lb = relLum(b);
  return (Math.max(lf, lb) + 0.05) / (Math.min(lf, lb) + 0.05);
}

// --- collector ---------------------------------------------------------------
function scanHtml(html) {
  const findings = [];
  const c = {
    imgsNoAlt: [], imgsAltOk: 0, inputsUnlabeled: [], labelsFor: new Set(),
    headings: [], iframesNoTitle: [], tables: [], targetBlank: 0,
    ariaHiddenFocusable: [], fixedFontPx: 0, titlePresent: false,
    langAttr: null, viewportMeta: false, formCount: 0, inTitle: false,
    buttonOpen: false, buttonText: [], buttonsEmpty: [], linksNoText: 0,
    targetBlankNoWarning: [], idsSeen: new Map(), dupIds: new Set(),
    styleStack: [], linkText: [], blankStack: [], colorPairs: [],
    inHeading: null, headingText: [], openLabel: false,
    inputImagesNoAlt: 0, videoNoTracks: [], audioNoAlt: [],
    autoplayUnpausable: [], marqueeBlinkCount: 0, posTabindex: 0,
  };

  try {
    for (const tok of tokenize(html)) {
      if (tok.type === 'text') {
        const data = decodeEntities(tok.data);
        if (c.inTitle && data.trim()) c.titlePresent = true;
        if (c.inHeading) c.headingText.push(data);
        if (c.buttonOpen) c.buttonText.push(data);
        for (const buf of c.linkText) buf.push(data);
        if (data.trim() && c.styleStack.length) {
          const st = c.styleStack[c.styleStack.length - 1];
          if (st.fg && st.bg) c.colorPairs.push([st.fg, st.bg, !!st.large, data.trim().slice(0, 40)]);
        }
        continue;
      }
      if (tok.type === 'end') {
        const tag = tok.tag;
        if (c.styleStack.length) c.styleStack.pop();
        if (tag === 'title') c.inTitle = false;
        else if (/^h[1-6]$/.test(tag)) {
          c.headings.push([c.inHeading, c.headingText.join('').trim()]);
          c.inHeading = null;
        } else if (tag === 'label') c.openLabel = false;
        else if (tag === 'button' && c.buttonOpen) {
          c.buttonOpen = false;
          if (!c.buttonText.join('').trim()) c.buttonsEmpty.push('button');
        } else if (tag === 'a' && c.linkText.length) {
          const buf = c.linkText.pop();
          const isBlank = c.blankStack.pop();
          const text = buf.join('').trim();
          if (!text) c.linksNoText++;
          else if (isBlank && !/new (window|tab)/i.test(text))
            c.targetBlankNoWarning.push(text.slice(0, 50));
        }
        continue;
      }
      // start tag
      const a = Object.fromEntries(tok.attrs);
      const aid = a.id;
      if (aid) {
        if (c.idsSeen.has(aid)) c.dupIds.add(aid);
        else c.idsSeen.set(aid, tok.tag);
      }
      const tag = tok.tag;
      if (tag === 'title') c.inTitle = true;
      else if (tag === 'html') c.langAttr = a.lang || null;
      else if (tag === 'meta' && (a.name || '').toLowerCase() === 'viewport') c.viewportMeta = true;
      else if (/^h[1-6]$/.test(tag)) { c.inHeading = parseInt(tag[1], 10); c.headingText = []; }
      else if (tag === 'img') {
        if (a.alt === undefined || !a.alt.trim())
          c.imgsNoAlt.push((a.src || '').slice(0, 80));
        else c.imgsAltOk++;
      } else if (tag === 'button' ||
          (tag === 'input' && ['submit','button'].includes((a.type || '').toLowerCase()))) {
        if (tag === 'button') { c.buttonOpen = true; c.buttonText = []; }
      } else if (tag === 'label') {
        c.openLabel = true;
        if (a.for !== undefined && a.for !== '') c.labelsFor.add(a.for);
      } else if (['input','select','textarea'].includes(tag)) {
        const itype = (a.type || 'text').toLowerCase();
        if (['hidden','submit','button','reset'].includes(itype)) continue;
        if (itype === 'image') {
          if (a.alt === undefined || !a.alt.trim()) c.inputImagesNoAlt++;
          continue;
        }
        const labelled = (aid && c.labelsFor.has(aid)) || a['aria-label'] ||
          a['aria-labelledby'] || a.title;
        if (!labelled) {
          const name = a.name || a.placeholder || '';
          c.inputsUnlabeled.push(`${tag}[${itype}] ${name}`.slice(0, 60));
        }
      } else if (tag === 'a') {
        c.blankStack.push(a.target === '_blank');
        c.linkText.push([]);
      } else if (tag === 'iframe') {
        if (!a.title) c.iframesNoTitle.push((a.src || '').slice(0, 60));
      } else if (tag === 'input' && (a.type || '').toLowerCase() === 'image') {
        if (a.alt === undefined || !a.alt.trim()) c.inputImagesNoAlt++;
      } else if (tag === 'video') {
        if (!a['data-captions-present']) c.videoNoTracks.push((a.src || '').slice(0, 60));
        if (a.autoplay !== undefined && a.muted === undefined)
          c.autoplayUnpausable.push('video');
      } else if (tag === 'audio') {
        // an aria-label mentioning a transcript is a weak but real signal of an
        // alternative; without it, flag for manual caption/transcript check
        const label = `${a['aria-label'] || ''} ${a.title || ''}`.toLowerCase();
        if (!/transcript|captions?|subtitle/.test(label)) c.audioNoAlt.push((a.src || '').slice(0, 60));
        if (a.autoplay !== undefined && a.controls === undefined)
          c.autoplayUnpausable.push('audio');
      } else if (tag === 'track') {
        // a captions/subtitles track inside the current <video> satisfies 1.2.2
        if (/captions?|subtitles/.test(a.kind || '') && c.videoNoTracks.length)
          c.videoNoTracks.pop();
      } else if (tag === 'marquee' || tag === 'blink') {
        c.marqueeBlinkCount++;
      } else if (tag === 'table') {
        c.tables.push(false);
      } else if (tag === 'th') {
        if (c.tables.length) c.tables[c.tables.length - 1] = true;
      } else if (tag === 'form') c.formCount++;

      if (a['aria-hidden'] === 'true' && 'tabindex' in a && a.tabindex !== '-1')
        c.ariaHiddenFocusable.push(tag);
      const tb = parseInt(a.tabindex, 10);
      if (Number.isFinite(tb) && tb > 0) c.posTabindex++;
      const style = a.style || '';
      if (/text-decoration\s*:\s*blink/i.test(style)) c.marqueeBlinkCount++;
      if (/font-size\s*:\s*\d+px/.test(style)) c.fixedFontPx++;
      const parent = c.styleStack.length
        ? c.styleStack[c.styleStack.length - 1] : { fg: '', bg: '' };
      let fg = parent.fg, bg = parent.bg;
      const mFg = style.match(/(?:^|;)\s*color\s*:\s*([^;!]+)/);
      if (mFg) fg = mFg[1].trim();
      const mBg = style.match(/background(?:-color)?\s*:\s*([^;!]+)/);
      if (mBg && !/url\(|gradient\(/.test(mBg[1])) bg = mBg[1].trim();
      const large = /font-size\s*:\s*(?:1[89]\d*[.,]?|2\d+|[3-9]\d+)\s*px|font-size\s*:\s*(?:14|1[5-9]|[2-9]\d+(\.\d+)?)pt|font-weight\s*:\s*(?:bold|[6-9]00)/.test(style);
      c.styleStack.push({ fg, bg, large });
    }
  } catch (e) {
    return { ok: false, error: `parse error: ${e.message}`, score: null,
      findings: [], summary: {} };
  }

  const add = (rid, sev, msg, items) => {
    const n = items ? items.length : 0;
    if (n) findings.push({ rule_id: rid, severity: sev, message: msg.replace('{n}', n),
      count: n, examples: items.slice(0, 3).map(i => String(i).slice(0, 80)) });
  };

  add('IMG_ALT', 'error', '{n} image(s) missing alt text', c.imgsNoAlt);
  add('FORM_LABEL', 'error', '{n} form field(s) without an associated label', c.inputsUnlabeled);
  add('LINK_TEXT', 'error', '{n} link(s) with no accessible text',
    Array(c.linksNoText).fill('link'));
  add('BUTTON_TEXT', 'error', '{n} button(s) with no accessible text', c.buttonsEmpty);
  add('TARGET_BLANK', 'warning',
    '{n} link(s) opening in a new window without warning the user',
    c.targetBlankNoWarning);
  add('DUP_ID', 'error',
    '{n} duplicate id attribute value(s) (breaks label/aria references)',
    [...c.dupIds].sort());
  add('IFRAME_TITLE', 'warning', '{n} iframe(s) without a title attribute', c.iframesNoTitle);
  c.tables.forEach((hasHeader, i) => {
    if (!hasHeader) findings.push({ rule_id: 'TABLE_HEADER', severity: 'warning',
      message: `table #${i + 1} has no <th> header cells`, count: 1, examples: [] });
  });
  if (!c.titlePresent) findings.push({ rule_id: 'DOC_TITLE', severity: 'error',
    message: 'page has no non-empty <title>', count: 1, examples: [] });
  if (!c.langAttr) findings.push({ rule_id: 'HTML_LANG', severity: 'error',
    message: '<html> lacks a lang attribute', count: 1, examples: [] });
  if (!c.viewportMeta) findings.push({ rule_id: 'VIEWPORT', severity: 'warning',
    message: 'missing viewport meta (zoom disabled/unresponsive)', count: 1, examples: [] });
  const levels = c.headings.map(h => h[0]);
  const h1Count = c.headings.filter(h => h[0] === 1).length;
  let skips = 0;
  for (let i = 1; i < levels.length; i++) if (levels[i] > levels[i - 1] + 1) skips++;
  if (h1Count === 0) findings.push({ rule_id: 'HEADING_H1', severity: 'warning',
    message: 'no <h1> found on the page', count: 1, examples: [] });
  if (skips) findings.push({ rule_id: 'HEADING_SKIP', severity: 'warning',
    message: `${skips} heading level skip(s) (e.g. h2 followed by h4)`, count: skips, examples: [] });
  if (c.fixedFontPx >= 3) findings.push({ rule_id: 'FIXED_PX_FONTS', severity: 'notice',
    message: `${c.fixedFontPx} inline fixed px font-sizes (may block user zoom/text resize)`,
    count: c.fixedFontPx, examples: [] });
  add('ARIA_HIDDEN_FOCUS', 'error',
    '{n} element(s) with aria-hidden=true that are focusable', c.ariaHiddenFocusable);
  const low = []; const seen = new Set();
  for (const [fgc, bgc, large, txt] of c.colorPairs) {
    const ratio = contrastRatio(fgc, bgc);
    if (ratio === null) continue;
    const threshold = large ? 3.0 : 4.5;
    const key = `${fgc}|${bgc}|${large}`;
    if (ratio < threshold && !seen.has(key)) {
      seen.add(key);
      low.push(`${fgc} on ${bgc}: ${ratio.toFixed(2)}:1 ("${txt}")`);
    }
  }
  if (low.length) findings.push({ rule_id: 'CONTRAST', severity: 'error',
    message: `${low.length} text colour combination(s) below the WCAG AA contrast minimum (4.5:1 normal text, 3:1 large text)`,
    count: low.length, examples: low.slice(0, 3) });
  if (c.inputImagesNoAlt) findings.push({ rule_id: 'INPUT_TYPE_IMAGE_ALT',
    severity: 'error',
    message: `${c.inputImagesNoAlt} image submit button(s) (<input type=image>) without alt text (WCAG 1.1.1)`,
    count: c.inputImagesNoAlt, examples: [] });
  add('VIDEO_TRACKS', 'error',
    '{n} video(s) without a captions/subtitles track (WCAG 1.2.2)', c.videoNoTracks);
  add('AUDIO_TRANSCRIPT', 'warning',
    '{n} audio element(s) with no indicated transcript or captions alternative (WCAG 1.2.1)',
    c.audioNoAlt);
  add('AUTOPLAY_MEDIA', 'error',
    '{n} media element(s) that autoplay without visible pause controls or muting (WCAG 1.4.2)',
    c.autoplayUnpausable);
  if (c.marqueeBlinkCount) findings.push({ rule_id: 'MARQUEE_BLINK',
    severity: 'error',
    message: `${c.marqueeBlinkCount} deprecated blinking/moving element(s) — cannot be paused by the user (WCAG 2.2.2)`,
    count: c.marqueeBlinkCount, examples: [] });
  if (c.posTabindex) findings.push({ rule_id: 'POSITIVE_TABINDEX',
    severity: 'warning',
    message: `${c.posTabindex} element(s) with tabindex greater than 0 — breaks natural focus order (WCAG 2.4.3)`,
    count: c.posTabindex, examples: [] });

  const sevOrder = { error: 0, warning: 1, notice: 2 };
  findings.sort((x, y) => sevOrder[x.severity] - sevOrder[y.severity]);
  const errors = findings.filter(f => f.severity === 'error').length;
  const warnings = findings.filter(f => f.severity === 'warning').length;
  const notices = findings.filter(f => f.severity === 'notice').length;
  const score = Math.max(0, 100 - errors * 12 - warnings * 5 - notices * 2);

  return { ok: true, standard: 'EAA / WCAG 2.1 AA (subset)', score,
    grade: score >= 90 ? 'A' : score >= 75 ? 'B' : score >= 55 ? 'C' : 'D',
    findings, summary: { errors, warnings, notices,
      imagesChecked: c.imgsNoAlt.length + c.imgsAltOk,
      tables: c.tables.length, forms: c.formCount } };
}

module.exports = { scanHtml, contrastRatio, tokenize };
