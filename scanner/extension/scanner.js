// scanner.js — runs the same rule set as scanner_core.py, in the live DOM.
// This is the browser-side port of the universal core (platform-independent).

function scanPage() {
  const findings = [];
  const add = (id, sev, msg, n) => {
    if (n > 0) findings.push({ id, sev, msg: msg.replace("{n}", n), count: n });
  };

  const imgsNoAlt = [...document.images].filter(
    im => !im.hasAttribute("alt") || im.alt.trim() === "");
  add("IMG_ALT", "error", "{n} image(s) missing alt text", imgsNoAlt.length);

  const fields = [...document.querySelectorAll("input,select,textarea")].filter(el => {
    const t = (el.type || "").toLowerCase();
    if (["hidden","submit","button","reset","image"].includes(t)) return false;
    if (el.labels && el.labels.length) return false;
    return !(el.getAttribute("aria-label") || el.getAttribute("aria-labelledby") ||
             el.getAttribute("title"));
  });
  add("FORM_LABEL", "error", "{n} form field(s) without a label", fields.length);

  const emptyLinks = [...document.querySelectorAll("a[href]")].filter(
    a => !(a.textContent.trim() ||
           a.getAttribute("aria-label") || a.querySelector("img[alt]:not([alt=''])")));
  add("LINK_TEXT", "error", "{n} link(s) with no accessible text",
      emptyLinks.length);

  const emptyButtons = [...document.querySelectorAll("button")].filter(
    b => !(b.textContent.trim() || b.getAttribute("aria-label") ||
           b.querySelector("img[alt]:not([alt=''])")));
  add("BUTTON_TEXT", "error", "{n} button(s) with no accessible text",
      emptyButtons.length);

  const idSeen = new Set(), dupIds = new Set();
  for (const el of document.querySelectorAll("[id]")) {
    if (idSeen.has(el.id)) dupIds.add(el.id); else idSeen.add(el.id);
  }
  add("DUP_ID", "error",
      "{n} duplicate id value(s) (breaks label/aria references)",
      dupIds.size);

  const blankNoWarn = [...document.querySelectorAll('a[target="_blank"]')]
    .filter(a => {
      const t = (a.textContent || "").toLowerCase();
      return t && !t.includes("new window") && !t.includes("new tab");
    });
  add("TARGET_BLANK", "warning",
      "{n} link(s) opening in a new window without warning",
      blankNoWarn.length);

  if (!document.title || !document.title.trim())
    findings.push({ id:"DOC_TITLE", sev:"error", msg:"page has no <title>", count:1 });
  if (!document.documentElement.lang)
    findings.push({ id:"HTML_LANG", sev:"error",
      msg:"<html> lacks a lang attribute", count:1 });

  if (!document.querySelector('meta[name="viewport"]'))
    findings.push({ id:"VIEWPORT", sev:"warning",
      msg:"missing viewport meta tag", count:1 });

  if (!document.querySelector("h1"))
    findings.push({ id:"HEADING_H1", sev:"warning", msg:"no <h1> found", count:1 });

  let skips = 0, prev = 0;
  for (const h of document.querySelectorAll("h1,h2,h3,h4,h5,h6")) {
    const lvl = +h.tagName[1];
    if (prev && lvl > prev + 1) skips++;
    prev = lvl;
  }
  add("HEADING_SKIP", "warning", "{n} heading level skip(s)", skips);

  const frames = [...document.querySelectorAll("iframe:not([title])")];
  add("IFRAME_TITLE", "warning", "{n} iframe(s) without a title", frames.length);

  const badTables = [...document.querySelectorAll("table")].filter(
    t => !t.querySelector("th"));
  add("TABLE_HEADER", "warning", "{n} table(s) without header cells",
      badTables.length);

  const hiddenFocusable = [...document.querySelectorAll('[aria-hidden="true"]')]
    .filter(el => el.matches('a[href],button,input,select,textarea,[tabindex]:not([tabindex="-1"])'));
  add("ARIA_HIDDEN_FOCUS", "error",
      "{n} aria-hidden element(s) that are still focusable",
      hiddenFocusable.length);

  // --- v1.2.0 rules (same set as npm core / Python core) ---

  const inputImgsNoAlt = [...document.querySelectorAll('input[type="image"]')]
    .filter(el => !el.hasAttribute("alt") || el.alt.trim() === "");
  add("INPUT_TYPE_IMAGE_ALT", "error",
      "{n} image submit button(s) (<input type=image>) without alt text (WCAG 1.1.1)",
      inputImgsNoAlt.length);

  const videosNoTracks = [...document.querySelectorAll("video")].filter(v =>
    ![...v.querySelectorAll("track")].some(t =>
      /captions?|subtitles/.test((t.kind || "").toLowerCase())));
  add("VIDEO_TRACKS", "error",
      "{n} video(s) without a captions/subtitles track (WCAG 1.2.2)",
      videosNoTracks.length);

  const audioNoAlt = [...document.querySelectorAll("audio")].filter(a => {
    const label = ((a.getAttribute("aria-label") || "") + " " +
                   (a.title || "")).toLowerCase();
    return !/transcript|captions?|subtitle/.test(label);
  });
  add("AUDIO_TRANSCRIPT", "warning",
      "{n} audio element(s) with no indicated transcript or captions alternative (WCAG 1.2.1)",
      audioNoAlt.length);

  const autoplayBad = [
    ...document.querySelectorAll("video[autoplay]:not([muted])"),
    ...document.querySelectorAll("audio[autoplay]:not([controls])"),
  ];
  add("AUTOPLAY_MEDIA", "error",
      "{n} media element(s) that autoplay without visible pause controls or muting (WCAG 1.4.2)",
      autoplayBad.length);

  const marqueeBlinkCount =
    document.querySelectorAll("marquee,blink").length +
    [...document.querySelectorAll('[style*="blink"]')].filter(
      el => /text-decoration\s*:\s*blink/i.test(el.getAttribute("style"))).length;
  add("MARQUEE_BLINK", "error",
      "{n} deprecated blinking/moving element(s) — cannot be paused by the user (WCAG 2.2.2)",
      marqueeBlinkCount);

  const posTabindex = [...document.querySelectorAll("[tabindex]")].filter(
    el => { const t = parseInt(el.getAttribute("tabindex"), 10);
            return Number.isFinite(t) && t > 0; }).length;
  add("POSITIVE_TABINDEX", "warning",
      "{n} element(s) with tabindex greater than 0 — breaks natural focus order (WCAG 2.4.3)",
      posTabindex);

  // WCAG 1.4.3 contrast on inline-styled text
  function parseCol(s) {
    s = (s || "").trim().toLowerCase();
    if (!s || ["transparent","inherit","currentcolor","initial"].includes(s)) return null;
    let m = s.match(/^#([0-9a-f]{3})$/);
    if (m) return m[1].split("").map(c => parseInt(c + c, 16));
    m = s.match(/^#([0-9a-f]{6})/);
    if (m) return [0,2,4].map(i => parseInt(m[1].slice(i, i+2), 16));
    m = s.match(/^rgba?\(([^)]+)\)/);
    if (m) {
      const p = m[1].split(",").map(x => x.trim());
      if (p.length >= 4 && parseFloat(p[3]) < 0.9) return null;
      try { return p.slice(0,3).map(x => x.endsWith("%") ? parseFloat(x)*2.55 : parseFloat(x)); }
      catch (e) { return null; }
    }
    const named = { white:[255,255,255], black:[0,0,0], red:[255,0,0],
      green:[0,128,0], blue:[0,0,255], gray:[128,128,128], grey:[128,128,128],
      silver:[192,192,192], yellow:[255,255,0], orange:[255,165,0] };
    return named[s] || null;
  }
  const chan = c => { c /= 255; return c <= 0.04045 ? c/12.92 : Math.pow((c+0.055)/1.055, 2.4); };
  const lum = rgb => 0.2126*chan(rgb[0]) + 0.7152*chan(rgb[1]) + 0.0722*chan(rgb[2]);
  const seenPairs = new Set();
  let lowContrast = 0;
  const walker = document.createTreeWalker(document.body || document.documentElement,
                                           NodeFilter.SHOW_TEXT);
  let tn;
  while ((tn = walker.nextNode())) {
    if (!tn.textContent.trim()) continue;
    let el = tn.parentElement, fg = null, bg = null, large = false, node = el;
    while (node && node.nodeType === 1) {
      const st = (node.getAttribute && node.getAttribute("style")) || "";
      if (st) {
        if (fg === null) { const m = st.match(/(?:^|;)\s*color\s*:\s*([^;!]+)/); if (m) fg = m[1].trim(); }
        if (bg === null) {
          const m = st.match(/background(?:-color)?\s*:\s*([^;!]+)/);
          if (m && !/url\(|gradient\(/.test(m[1])) bg = m[1].trim();
        }
        if (/font-size\s*:\s*(?:1[89]\d*|2\d+|[3-9]\d+)\s*px|font-size\s*:\s*(?:14|1[5-9]|[2-9]\d+(\.\d+)?)\s*pt|font-weight\s*:\s*(?:bold|[6-9]00)/.test(st)) large = true;
      }
      node = node.parentElement;
    }
    if (fg === null || bg === null) continue;
    const f = parseCol(fg), b = parseCol(bg);
    if (!f || !b) continue;
    const lf = lum(f), lb = lum(b), hi = Math.max(lf, lb), lo = Math.min(lf, lb);
    const ratio = (hi + 0.05) / (lo + 0.05), thr = large ? 3.0 : 4.5;
    const key = fg + "|" + bg + "|" + large;
    if (ratio < thr && !seenPairs.has(key)) { seenPairs.add(key); lowContrast++; }
  }
  add("CONTRAST", "error",
      "{n} text colour combination(s) below WCAG AA contrast (4.5:1 normal, 3:1 large)",
      lowContrast);

  const errors = findings.filter(f => f.sev === "error").length;
  const warnings = findings.filter(f => f.sev === "warning").length;
  const notices = findings.filter(f => f.sev === "notice").length;
  const score = Math.max(0, 100 - errors * 12 - warnings * 5 - notices * 2);
  return { ok:true, score,
           grade: score >= 90 ? "A" : score >= 75 ? "B" : score >= 55 ? "C" : "D",
           findings };
}

document.getElementById("scan").addEventListener("click", async () => {
  const out = document.getElementById("result");
  out.textContent = "Scanning…";
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const [res] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: scanPage,
    });
    const r = res.result;
    let html = `<div class="score grade-${r.grade}">${r.score}/100 — Grade ${r.grade}</div>`;
    if (!r.findings.length) html += "<p>No issues found by automated checks. 🎉</p>";
    else {
      html += "<ul>" + r.findings.map(f =>
        `<li><span class="sev-${f.sev}">${f.msg}</span></li>`).join("") + "</ul>";
    }
    out.innerHTML = html;
  } catch (e) {
    out.textContent = "Could not scan this page (" + e.message +
                      "). Browser-internal pages can't be scanned.";
  }
});
