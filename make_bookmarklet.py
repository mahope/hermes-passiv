#!/usr/bin/env python3
"""
make_bookmarklet.py — builds the Clean Copy bookmarklet.

Reads the shared conversion core (site/clean-copy-core.js — the exact same
code the Chrome/Firefox extensions and /clean-copy-tool run) and wraps it in
an IIFE that grabs the current text selection, converts it, and writes it to
the clipboard. The result is minified, URL-escaped and injected into:

  site/clean-copy-bookmarklet.html   (landing page with draggable link)
  site/clean-copy-bookmarklet.js     (standalone URL for Node tests)

Usage: python3 make_bookmarklet.py [--check]
  --check: exit 0 only if generated page matches what's on disk.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
CORE = SITE / "clean-copy-core.js"
PAGE = SITE / "clean-copy-bookmarklet.html"
STANDALONE = SITE / "clean-copy-bookmarklet.js"
NODE = "node"

BOOKMARKLET_BODY_TEMPLATE = r"""var sel=window.getSelection&&window.getSelection();
if(!sel||sel.isCollapsed||!String(sel).trim()){alert('Clean Copy: select some text on the page first.');return;}
var range=sel.rangeCount>0?sel.getRangeAt(0):null;
var html='';
var text=String(sel);
if(range){var c=document.createElement('div');c.appendChild(range.cloneContents());html=c.innerHTML;}
try{
var out=(html&&/<[a-z][\s\S]*>/i.test(html))?CC.htmlToMarkdown(html):CC.cleanText(text);
if(event&&event.altKey){out=CC.cleanText(String(sel).replace(/<[^>]*>/g,''));}
navigator.clipboard.writeText(out).then(function(){},function(){window.prompt('Clean Copy - copy manually (Ctrl/Cmd+C):',out);});
}catch(e){window.prompt('Clean Copy - copy manually (Ctrl/Cmd+C):',text);}"""


def strip_comments(src: str) -> str:
    """Remove // and /* */ comments while respecting string literals."""
    out = []
    i = 0
    n = len(src)
    in_str = None
    while i < n:
        ch = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if in_str:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(src[i + 1])
                i += 2
                continue
            if ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            in_str = ch
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "*":
            j = src.find("*/", i + 2)
            i = n if j == -1 else j + 2
            out.append(" ")
            continue
        if ch == "/" and nxt == "/":
            j = src.find("\n", i)
            i = n if j == -1 else j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def build_bookmarklet() -> str:
    core_min = strip_comments(CORE.read_text(encoding="utf-8"))
    core_min = re.sub(r"\n\s*\n", "\n", core_min).strip()
    # The UMD wrapper assigns to `self.CleanCopyCore` in browsers; capture it.
    code = (
        "(function(){var event=window.event;"
        + core_min
        + ";var CC=self.CleanCopyCore;"
        + BOOKMARKLET_BODY_TEMPLATE
        + "})();"
    )
    escaped = (
        code.replace("%", "%25")
        .replace('"', "%22")
        .replace("#", "%23")
        .replace("\n", " ")
        .replace(" ", "%20")
    )
    return "javascript:" + escaped


FAQS = [
    ("Does it work on mobile?",
     "Yes, via manual bookmark editing. On iOS Safari use Share → Add Bookmark, then edit "
     "the bookmark's address to the copied bookmarklet link. On Android Chrome, bookmark any "
     "page, then edit it and replace the URL."),
    ("Why a bookmarklet instead of the extension?",
     "No install, no store approval, and it works in browsers where you can't or won't install "
     "extensions — work laptops, locked-down profiles, Safari. The extension adds a keyboard "
     "shortcut and right-click menu; the bookmarklet is the same converter with zero setup."),
    ("Is my selected text uploaded anywhere?",
     "No. Everything happens locally in your browser when you click the bookmark. There is no "
     "server component and no network request carries your text."),
    ("Some sites block clipboard access — what then?",
     "A few sites restrict programmatic clipboard writes. When that happens the bookmarklet "
     "shows the converted text in a dialog so you can copy it manually. Nothing is lost."),
    ("What gets cleaned?",
     "Smart quotes become straight quotes, em/en dashes become plain hyphens, non-breaking and "
     "invisible characters are removed. In Markdown mode, headings, bold/italic, links, images, "
     "code blocks and lists convert properly."),
]

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Clean Copy Bookmarklet — Copy clean Markdown on any browser, no install</title>
  <meta name="description" content="Free bookmarklet: select any text on any web page and copy it as clean Markdown or plain text. Works in Chrome, Safari, Firefox and Edge — no extension, no install, nothing uploaded.">
  <meta property="og:title" content="Clean Copy Bookmarklet — no install, any browser">
  <meta property="og:description" content="Select text anywhere on the web, click the bookmark, paste clean Markdown. Free, no install, nothing leaves your device.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://hermes-passiv.pages.dev/clean-copy-bookmarklet">
  <link rel="canonical" href="https://hermes-passiv.pages.dev/clean-copy-bookmarklet">
  <script type="application/ld+json">
__JSONLD_WEBAPP__
  </script>
  <script type="application/ld+json">
__JSONLD_FAQ__
  </script>
  <style>
    :root { color-scheme: dark; }
    body {
      margin: 0;
      background: var(--color-bg);
      color: var(--color-text);
      font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
      line-height: 1.6;
    }
    main { max-width: 860px; margin: 0 auto; padding: 1rem 1.25rem 3rem; }
    .lead { font-size: 1.15rem; color: var(--color-text-muted); max-width: 640px; }
    h2 { margin-top: 2.5rem; }
    a { color: var(--color-accent); }
    .bm-box {
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: 14px;
      padding: 1.6rem 1.5rem;
      margin: 1.5rem 0;
      text-align: center;
    }
    .bm-link {
      display: inline-block;
      background: var(--color-accent);
      color: #fff;
      padding: 0.7rem 1.5rem;
      border-radius: 999px;
      font-weight: 700;
      font-size: 1.05rem;
      cursor: grab;
      user-select: none;
      -webkit-user-select: none;
      border: 2px dashed rgba(255,255,255,0.35);
      text-decoration: none;
    }
    .bm-note { display: block; margin-top: 0.8rem; color: var(--color-text-muted); font-size: 0.85rem; }
    ol.steps { padding-left: 1.4rem; }
    ol.steps li { margin: 0.5rem 0; }
    code.inline {
      background: var(--color-surface-2);
      border: 1px solid var(--color-border);
      border-radius: 6px;
      padding: 0.1rem 0.4rem;
      font-size: 0.85em;
    }
    .privacy-note {
      display: flex;
      gap: 0.6rem;
      align-items: flex-start;
      background: var(--color-surface-2);
      border: 1px solid var(--color-border);
      border-radius: 10px;
      padding: 0.9rem 1.1rem;
      margin: 1.5rem 0;
      font-size: 0.88rem;
      color: var(--color-text-muted);
    }
    details.faq { border-bottom: 1px solid var(--color-border); padding: 0.8rem 0; }
    details.faq summary { cursor: pointer; font-weight: 600; }
    details.faq p { color: var(--color-text-muted); font-size: 0.9rem; }
    .cta-row { margin-top: 1.2rem; display: flex; gap: 1.2rem; flex-wrap: wrap; font-size: 0.95rem; }
    footer { text-align: center; padding: 2rem 1rem; color: var(--color-text-muted); font-size: 0.85rem; }
  </style>
</head>
<body>
  <main>
    <nav aria-label="Breadcrumb" style="font-size:0.8rem;margin-bottom:1rem;">
      <a href="/">Passiv</a> · <a href="/clean-copy">Clean Copy</a> · <span aria-current="page">Bookmarklet</span>
    </nav>

    <h1>Clean Copy Bookmarklet</h1>
    <p class="lead">Select any text on any web page, click the bookmark, and your clipboard holds
    clean Markdown or plain text. No extension, no install, no account — works in every browser,
    including ones where extensions aren't allowed.</p>

    <div class="privacy-note" role="note">
      <span aria-hidden="true">🔒</span>
      <span><strong>Nothing leaves your device.</strong> The conversion runs in your browser the moment
      you click the bookmark. No upload, no server, no tracking of your text.</span>
    </div>

    <h2>Install it (30 seconds)</h2>
    <div class="bm-box">
      <a class="bm-link" id="cc-bm" href="__BM_URL__" title="Drag me to your bookmarks bar"
         onclick="event.preventDefault();document.getElementById('bm-help').hidden=false;">⬇️ Clean Copy</a>
      <span class="bm-note"><strong>Drag this button to your bookmarks bar.</strong> That's the whole install.</span>
      <span class="bm-note" id="bm-help" hidden>Can't drag? Right-click or long-press the button, choose “Copy link”, then add a new bookmark named “Clean Copy” and paste the link as its address.</span>
    </div>

    <ol class="steps">
      <li>Show your bookmarks bar (<code class="inline">Ctrl+Shift+B</code> on Windows/Linux, <code class="inline">Cmd+Shift+B</code> on Mac).</li>
      <li>Drag the blue button above onto the bar.</li>
      <li>Select some text on any page.</li>
      <li>Click the <strong>Clean Copy</strong> bookmark, then paste — it's clean Markdown.</li>
    </ol>
    <p>Prefer plain text? Hold <code class="inline">Alt</code> (Windows/Linux) or <code class="inline">Option</code> (Mac) while clicking the bookmark to strip all formatting instead.</p>

    <h2>What gets cleaned</h2>
    <ul>
      <li>“Smart quotes” become straight quotes that don't break code or spreadsheets</li>
      <li>Em dashes, en dashes and non-breaking spaces become plain equivalents</li>
      <li>Invisible zero-width characters are removed entirely</li>
      <li>In Markdown mode: headings, bold/italic, links, images, code blocks and lists convert properly</li>
    </ul>
    <p>The converter is the exact same engine used by the
    <a href="/clean-copy-tool">Clean Copy web tool</a> and the
    <a href="/clean-copy">browser extension</a>.</p>

    <div class="cta-row">
      <a href="/clean-copy">Get the browser extension →</a>
      <a href="/clean-copy-tool">Or try the paste-anywhere web tool →</a>
    </div>

    <h2>FAQ</h2>
__FAQ_HTML__

    <footer>
      <p><a href="/clean-copy">Clean Copy extension</a> · <a href="/clean-copy-tool">Web tool</a> · <a href="/free-tools">More free tools</a> · by Passiv</p>
    </footer>
  </main>

  <script src="/track.js"></script>
  <script>
  // Anonymous engagement signal: a click on the placeholder (drag start isn't
  // reliably detectable across browsers).
  document.getElementById('cc-bm').addEventListener('click', function () {
    try { trackEvent('bm-click'); } catch (e) {}
  });
  </script>
</body>
</html>
"""


def build_page(bm_url: str) -> str:
    faq_jsonld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in FAQS
        ],
    }
    webapp_jsonld = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": "Clean Copy Bookmarklet",
        "url": "https://hermes-passiv.pages.dev/clean-copy-bookmarklet",
        "applicationCategory": "UtilitiesApplication",
        "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": ("Free bookmarklet: select text on any web page and copy it as clean "
                        "Markdown or plain text. Works in every browser, no install."),
    }
    faq_html = "\n".join(
        f'    <details class="faq">\n      <summary>{q}</summary>\n      <p>{a}</p>\n    </details>'
        for q, a in FAQS
    )
    html = PAGE_TEMPLATE.replace("__BM_URL__", bm_url)
    html = html.replace("__JSONLD_WEBAPP__", json.dumps(webapp_jsonld, indent=2))
    html = html.replace("__JSONLD_FAQ__", json.dumps(faq_jsonld, indent=2))
    html = html.replace("__FAQ_HTML__", faq_html)
    return html


def node_sanity_check() -> bool:
    """Confirm the core still exposes the API and behaviour the bookmarklet relies on."""
    code = f"""
const m = require({json.dumps(str(CORE))});
for (const fn of ['cleanText','htmlToMarkdown']) {{
  if (typeof m[fn] !== 'function') {{ console.error('MISSING', fn); process.exit(1); }}
}}
const md = m.htmlToMarkdown('<h2>T</h2><p>\\u201CHello\\u201D \\u2014 <b>b</b></p>');
if (!md.includes('## T') || !md.includes('**b**')) {{ console.error('BAD OUTPUT:', md); process.exit(1); }}
console.log('core sanity OK');
"""
    r = subprocess.run([NODE, "-e", code], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return False
    return True


def validate_jsonld(html: str) -> bool:
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                        html, re.DOTALL)
    ok = True
    for b in blocks:
        try:
            d = json.loads(b)
            if d.get("@context") != "https://schema.org":
                print(f"JSON-LD bad @context: {d.get('@context')}")
                ok = False
        except Exception as e:
            print(f"JSON-LD parse error: {e}")
            ok = False
    print(f"JSON-LD: {len(blocks)} blocks validated")
    return ok


def main() -> int:
    check_only = "--check" in sys.argv
    if not node_sanity_check():
        print("Core sanity failed — aborting.", file=sys.stderr)
        return 1
    bm_url = build_bookmarklet()
    html = build_page(bm_url)
    if not validate_jsonld(html):
        return 1
    if check_only:
        cur = PAGE.read_text(encoding="utf-8") if PAGE.exists() else ""
        up_to_date = cur == html and STANDALONE.exists()
        print("up-to-date" if up_to_date else "stale")
        return 0 if up_to_date else 1
    PAGE.write_text(html, encoding="utf-8")
    STANDALONE.write_text(
        "// Generated by make_bookmarklet.py — do not edit.\n"
        f"module.exports = {json.dumps(bm_url)};\n",
        encoding="utf-8",
    )
    print(f"wrote {PAGE} ({len(html)} bytes)")
    print(f"bookmarklet length: {len(bm_url)} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
