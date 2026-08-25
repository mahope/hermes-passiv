# Build Your First Chrome Extension — A Complete Practical Guide

**By the Clean Copy team** · Version 1.0

---

## Preface: Why This Book Exists

Every developer I know has had the same thought at some point: "I wish my browser could just do X." Maybe it's copying text without formatting, checking a page for accessibility issues, or automating a repetitive task. Chrome extensions are how you build that.

I wrote this book because when I built my first extension (Clean Copy — an HTML-to-Markdown converter that runs in your browser), I had to piece together information from a dozen sources. The official Chrome docs are thorough but scattered. Stack Overflow answers assume you already know the architecture. Blog posts go out of date when Google updates the platform.

This book is what I wish I'd had: a single, practical, step-by-step guide that takes you from "I've never built an extension" to "my extension is live in the Chrome Web Store."

## Who This Book Is For

- Web developers who know HTML, CSS, and basic JavaScript
- Anyone who has thought "I could build a browser extension for that"
- Developers who want to publish their first Chrome Web Store listing

You don't need experience with service workers, the Chrome API, or browser extension architecture. You'll learn all of that here.

## What You Will Build

By the end of this book, you'll have built and published a working Chrome extension. Along the way, you'll create:

- A popup that interacts with the current page
- A context menu that copies formatted text
- A background service worker that handles events
- An options page that persists user settings
- A keyboard shortcut for power users

The final extension is Clean Copy Lite — a simplified version of the real Clean Copy extension. It converts selected HTML into clean Markdown, ready to paste into any document.

## What You Need

- A computer running Chrome or Edge (Chromium-based)
- A text editor (VS Code recommended)
- Basic familiarity with JavaScript, HTML, and CSS
- About 2-3 hours to build the complete extension

---

## Chapter 1: Understanding Chrome Extension Architecture

### 1.1 What Makes an Extension Different from a Website

A Chrome extension is a collection of files — HTML, CSS, JavaScript, images — packaged together and loaded by the browser. Unlike a website which runs on a remote server, an extension runs **locally in the user's browser**.

This fundamental difference shapes everything: there's no backend server, no database (unless you use one), and the extension can only interact with the web through the Chrome API. But it also means your extension works offline, has near-zero latency, and costs nothing to host.

### 1.2 The Three Core Components

Every Chrome extension has at least these three files:

**manifest.json** — The heart of your extension. This JSON file tells Chrome what your extension is called, what permissions it needs, which files to load, and what version it is. It's the first file Chrome reads when installing your extension.

**background.js** — A service worker that runs in the background, listening for events. Think of it as the brain of your extension: it handles context menu clicks, keyboard shortcuts, messages from the popup, and any long-running logic. It does NOT have access to the DOM of web pages.

**popup.html + popup.js** — The UI that appears when the user clicks your extension's toolbar icon. This is a regular HTML page (with JavaScript) that can interact with the currently active tab through the Chrome API. The popup only exists while it's open — once the user clicks elsewhere, it's destroyed.

There are other components too (options pages, content scripts, offscreen documents), but these three are where you start.

### 1.3 Manifest V3 (MV3)

As of 2023, Chrome requires all new extensions to use Manifest V3 (MV3). The key changes from the older MV2:

- Background pages are replaced by **service workers** (which can be killed and restarted by Chrome)
- Remote code execution is banned (all code must be in the extension package)
- Network request modification uses `declarativeNetRequest` instead of the old webRequest API
- Service workers don't have DOM access (no `document`, no `window`)

MV3 is more restrictive but also more secure. This book covers only MV3.

### 1.4 The Extension Lifecycle

1. User installs your extension from the Chrome Web Store
2. Chrome reads `manifest.json` and registers all components
3. The background service worker starts when needed (on install, on a triggered event)
4. The popup loads when the user clicks the toolbar icon
5. The extension runs until Chrome decides to unload it (or the user uninstalls it)

Extensions do NOT run continuously. The service worker starts on demand and stops after ~30 seconds of inactivity. This is critical to understand: you cannot rely on persistent state in memory.

### 1.5 Permissions: Only What You Need

Every extension must declare its permissions in `manifest.json`. Chrome shows these to the user before installation. Common permissions:

```json
{
  "permissions": ["activeTab", "contextMenus", "storage", "clipboardWrite"],
  "host_permissions": ["https://*/*"]
}
```

**The golden rule:** ask for the minimum permissions you actually need. Users are wary of extensions that request access to "all websites" or "all your data." The `activeTab` permission is your best friend — it gives temporary access to the current tab only when the user interacts with your extension.

---

## Chapter 2: Your First Extension — Hello World

Let's build something real. Open your text editor and create a new folder called `clean-copy-lite`.

### 2.1 Create manifest.json

Inside `clean-copy-lite/`, create `manifest.json`:

```json
{
  "manifest_version": 3,
  "name": "Clean Copy Lite",
  "version": "1.0.0",
  "description": "Copy selected text as clean Markdown — right-click and paste anywhere.",
  "permissions": ["activeTab", "contextMenus", "clipboardWrite"],
  "background": {
    "service_worker": "background.js"
  },
  "action": {
    "default_popup": "popup.html",
    "default_title": "Clean Copy Lite"
  },
  "icons": {
    "16": "icon-16.png",
    "48": "icon-48.png",
    "128": "icon-128.png"
  }
}
```

Note: We declare `clipboardWrite` so our extension can copy to the clipboard. `activeTab` gives access to the current page when the user invokes the extension. `contextMenus` lets us add a right-click option.

### 2.2 Create the Background Service Worker

Create `background.js`:

```javascript
// Clean Copy Lite — Background Service Worker
// Runs in the background, handles context menu clicks and events.

// Create the context menu when the extension is installed
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "copy-as-markdown",
    title: "Copy as Markdown",
    contexts: ["selection"]
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "copy-as-markdown") {
    // Execute a script in the current tab to get the selected HTML
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: getSelectedHtml
    }, (results) => {
      if (chrome.runtime.lastError) {
        console.error(chrome.runtime.lastError.message);
        return;
      }
      const html = results[0].result;
      if (!html) return;
      
      const markdown = htmlToMarkdown(html);
      copyToClipboard(markdown, tab.id);
    });
  }
});

// This function runs IN the page context (injected by executeScript)
function getSelectedHtml() {
  const selection = window.getSelection();
  if (!selection.rangeCount) return '';
  
  const range = selection.getRangeAt(0);
  const container = document.createElement('div');
  container.appendChild(range.cloneContents());
  return container.innerHTML;
}

// Copy text using an offscreen document (MV3 does not allow
// navigator.clipboard from service workers)
async function copyToClipboard(text, tabId) {
  // Store the text temporarily in chrome.storage
  await chrome.storage.local.set({ _clipboard: text });
  
  // Create or reuse an offscreen document that has clipboard access
  try {
    await chrome.offscreen.createDocument({
      url: 'offscreen.html',
      reasons: ['CLIPBOARD'],
      justification: 'Copy formatted Markdown text to clipboard'
    });
  } catch (e) {
    // Document may already exist — ignore
  }
  
  // Tell the offscreen document to copy
  chrome.runtime.sendMessage({ type: 'copy-from-storage' });
}
```

Wait — we're getting ahead of ourselves. We need the offscreen document too. Let's create it.

Create `offscreen.html`:

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
<script>
// Wait for the background to tell us what to copy
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'copy-from-storage') {
    chrome.storage.local.get('_clipboard', (data) => {
      if (data._clipboard) {
        navigator.clipboard.writeText(data._clipboard).catch(console.error);
        chrome.storage.local.remove('_clipboard');
      }
    });
  }
});
</script>
</body>
</html>
```

The offscreen document is an MV3 workaround: service workers can't call `navigator.clipboard.writeText()`, so we create a hidden HTML page that has DOM access and do the clipboard operation there.

### 2.3 Load Your Extension in Chrome

1. Open Chrome and go to `chrome://extensions`
2. Enable "Developer mode" (toggle in the top-right corner)
3. Click "Load unpacked" and select your `clean-copy-lite` folder
4. The extension appears in your toolbar

Right-click on any text selection on a web page. You should see "Copy as Markdown" in the context menu. Click it — nothing visible happens yet because we haven't built the HTML-to-Markdown conversion! Let's fix that.

### 2.4 The Conversion Function

Add this to `background.js` (before the event listeners):

```javascript
// Simple HTML-to-Markdown converter
function htmlToMarkdown(html) {
  let md = html;
  
  // Strip script/style content first
  md = md.replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi, '');
  
  // Headings
  md = md.replace(/<h1[^>]*>(.*?)<\/h1>/gi, '# $1\n\n');
  md = md.replace(/<h2[^>]*>(.*?)<\/h2>/gi, '## $1\n\n');
  md = md.replace(/<h3[^>]*>(.*?)<\/h3>/gi, '### $1\n\n');
  
  // Bold and italic
  md = md.replace(/<(?:b|strong)[^>]*>(.*?)<\/(?:b|strong)>/gi, '**$1**');
  md = md.replace(/<(?:i|em)[^>]*>(.*?)<\/(?:i|em)>/gi, '*$1*');
  
  // Links
  md = md.replace(/<a[^>]*href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/gi, (m, href, inner) => {
    // Drop image-only links and fragment-only anchors
    const text = inner.replace(/<img[^>]*>/gi, '').replace(/<[^>]*>/g, '').trim();
    if (!text || /^#/.test(href)) return inner;
    return '[' + text + '](' + href + ')';
  });
  
  // Images
  md = md.replace(/<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*>/gi, '![$2]($1)');
  md = md.replace(/<img[^>]*src="([^"]*)"[^>]*>/gi, '![]($1)');
  
  // Paragraphs and line breaks
  md = md.replace(/<p[^>]*>(.*?)<\/p>/gi, '$1\n\n');
  md = md.replace(/<br\s*\/?>/gi, '\n');
  
  // Strip remaining HTML tags (tolerate > inside attributes)
  md = stripTagsSafe(md);
  
  // Decode HTML entities
  md = md.replace(/&amp;/g, '&');
  md = md.replace(/&lt;/g, '<');
  md = md.replace(/&gt;/g, '>');
  md = md.replace(/&quot;/g, '"');
  md = md.replace(/&#39;/g, "'");
  md = md.replace(/&nbsp;/g, ' ');
  
  // Clean up excessive whitespace
  md = md.replace(/\n{4,}/g, '\n\n');
  md = md.trim();
  
  return md;
}

function stripTagsSafe(html) {
  let out = '';
  let i = 0;
  const n = html.length;
  while (i < n) {
    const lt = html.indexOf('<', i);
    if (lt === -1) { out += html.slice(i); break; }
    out += html.slice(i, lt);
    // Find tag end, respecting quotes
    let j = lt + 1, quote = null;
    while (j < n) {
      const ch = html[j];
      if (quote) {
        if (ch === quote) quote = null;
      } else if (ch === '"' || ch === "'") {
        quote = ch;
      } else if (ch === '>') {
        break;
      }
      j++;
    }
    i = (j >= n) ? n : (j + 1);
  }
  return out;
}
```

### 2.5 Test Your Extension

1. Go to any page with formatted text (try Wikipedia)
2. Select a paragraph with bold text and links
3. Right-click → "Copy as Markdown"
4. Paste into a text editor or document

You should see clean Markdown: `**bold**`, `[link text](url)`, headings with `#`, etc.

**Troubleshooting:**
- If nothing happens after clicking the menu, check `chrome://extensions` → your extension → "Service Worker" → "Inspect" for error messages
- Common issue: the extension doesn't have `scripting` permission. Add it to manifest.json.
- Another common issue: the offscreen document needs `offscreen` permission.

Update your `manifest.json` permissions to:
```json
"permissions": ["activeTab", "contextMenus", "clipboardWrite", "scripting", "offscreen"]
```

---

## Chapter 3: The Popup — Your Extension's UI

The context menu is useful, but sometimes you want to paste messy text into the extension and get clean output. The popup is how you do that.

### 3.1 Create popup.html

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {
      width: 400px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      padding: 12px;
      margin: 0;
    }
    h2 {
      font-size: 16px;
      margin: 0 0 8px;
      color: #1a1a1a;
    }
    textarea {
      width: 100%;
      height: 120px;
      font-family: 'Menlo', 'Consolas', monospace;
      font-size: 13px;
      padding: 8px;
      border: 1px solid #ccc;
      border-radius: 4px;
      box-sizing: border-box;
      resize: vertical;
    }
    textarea:focus {
      outline: none;
      border-color: #666;
    }
    .output {
      margin-top: 8px;
      min-height: 60px;
      padding: 8px;
      background: #f5f5f5;
      border-radius: 4px;
      font-size: 13px;
      white-space: pre-wrap;
      word-break: break-all;
    }
    button {
      margin-top: 8px;
      padding: 6px 16px;
      background: #1a73e8;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 13px;
    }
    button:hover {
      background: #1557b0;
    }
    button.copy-btn {
      background: #34a853;
    }
    .status {
      font-size: 12px;
      color: #666;
      margin-top: 6px;
    }
  </style>
</head>
<body>
  <h2>Clean Copy Lite</h2>
  <textarea id="input" placeholder="Paste HTML or messy text here..."></textarea>
  <button id="convert">Convert to Markdown</button>
  <div class="output" id="output"></div>
  <button class="copy-btn" id="copy" style="display:none">Copy to Clipboard</button>
  <div class="status" id="status"></div>

  <script src="popup.js"></script>
</body>
</html>
```

### 3.2 Create popup.js

```javascript
// Clean Copy Lite — Popup Logic
document.getElementById('convert').addEventListener('click', async () => {
  const input = document.getElementById('input').value;
  if (!input.trim()) {
    document.getElementById('status').textContent = 'Paste some text first.';
    return;
  }
  
  // Send to background for conversion
  chrome.runtime.sendMessage(
    { type: 'convert-to-markdown', html: input },
    (response) => {
      if (chrome.runtime.lastError) {
        document.getElementById('status').textContent = 'Error: ' + chrome.runtime.lastError.message;
        return;
      }
      document.getElementById('output').textContent = response.markdown;
      document.getElementById('copy').style.display = 'inline-block';
      document.getElementById('status').textContent = 'Converted!';
    }
  );
});

document.getElementById('copy').addEventListener('click', async () => {
  const text = document.getElementById('output').textContent;
  
  // Store and trigger offscreen copy
  await chrome.storage.local.set({ _clipboard: text });
  try {
    await chrome.offscreen.createDocument({
      url: 'offscreen.html',
      reasons: ['CLIPBOARD'],
      justification: 'Copy Markdown text to clipboard'
    });
  } catch (e) {}
  chrome.runtime.sendMessage({ type: 'copy-from-storage' });
  document.getElementById('status').textContent = 'Copied!';
});
```

### 3.3 Add the Message Handler to background.js

Add this to your `background.js` (inside the `chrome.runtime.onInstalled.addListener` or as a separate listener):

```javascript
// Handle messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'convert-to-markdown') {
    const markdown = htmlToMarkdown(request.html);
    sendResponse({ markdown });
    return true;  // Keep the channel open for async response
  }
  if (request.type === 'copy-from-storage') {
    // Already handled by offscreen.html — but send a response to avoid warnings
    sendResponse({ ok: true });
  }
});
```

Now reload your extension (`chrome://extensions` → reload icon). Click the extension toolbar icon, paste some HTML, and click "Convert to Markdown."

---

## Chapter 4: Keyboard Shortcuts

Power users love keyboard shortcuts. Chrome extensions can declare shortcuts in `manifest.json` and handle them in the background.

### 4.1 Add Commands to manifest.json

Add to `manifest.json`:

```json
"commands": {
  "copy-selection": {
    "suggested_key": {
      "default": "Alt+C",
      "mac": "MacCtrl+C"
    },
    "description": "Copy selected text as Markdown"
  }
}
```

Note: On Mac, Chrome extensions cannot use Cmd+C (it's reserved). Use `MacCtrl+C` instead.

### 4.2 Handle the Command in background.js

```javascript
chrome.commands.onCommand.addListener(async (command) => {
  if (command === 'copy-selection') {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;
    
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: getSelectedHtml
    }, async (results) => {
      if (chrome.runtime.lastError || !results[0].result) return;
      const markdown = htmlToMarkdown(results[0].result);
      
      // Store and copy via offscreen document
      await chrome.storage.local.set({ _clipboard: markdown });
      try {
        await chrome.offscreen.createDocument({
          url: 'offscreen.html',
          reasons: ['CLIPBOARD'],
          justification: 'Copy Markdown to clipboard via keyboard shortcut'
        });
      } catch (e) {}
      chrome.runtime.sendMessage({ type: 'copy-from-storage' });
    });
  }
});
```

Reload the extension. Select some text on any page, press Ctrl+Alt+C (Windows/Linux) or Ctrl+MacCtrl+C (Mac), then paste. The text should be converted to Markdown automatically.

---

## Chapter 5: Persisting User Settings

Users want to customize their experience. Chrome's `storage` API makes this easy.

### 5.1 Add Storage Permission

Update `manifest.json` permissions:

```json
"permissions": [
  "activeTab", "contextMenus", "clipboardWrite",
  "scripting", "offscreen", "storage"
]
```

### 5.2 Custom Cleanup Rules

Let's let users define custom find-and-replace rules. Update `background.js` to read rules from storage:

```javascript
// Load custom rules on startup and whenever storage changes
let customRules = [];

async function loadCustomRules() {
  const data = await chrome.storage.local.get('customRules');
  customRules = (data.customRules || []).filter(r => r.pattern && r.replacement);
}

// Apply custom rules to text
function applyCustomRules(text) {
  for (const rule of customRules) {
    try {
      const regex = new RegExp(rule.pattern, 'g');
      text = text.replace(regex, rule.replacement);
    } catch (e) {
      // Skip invalid regex — never break copying
      console.warn('Invalid rule skipped:', rule.pattern);
    }
  }
  return text;
}

// Load rules initially
loadCustomRules();

// Reload rules when they change
chrome.storage.onChanged.addListener((changes) => {
  if (changes.customRules) {
    customRules = (changes.customRules.newValue || []).filter(r => r.pattern && r.replacement);
  }
});
```

Now update the copy chain to apply custom rules before writing to clipboard. Wherever you call `copyToClipboard`, pass the text through `applyCustomRules` first:

```javascript
// Instead of: copyToClipboard(markdown, tab.id);
// Do: copyToClipboard(applyCustomRules(markdown), tab.id);
```

### 5.3 Saving the User's Mode Preference

Some users always want plain text instead of Markdown. Let's persist that choice:

```javascript
// In the popup:
chrome.storage.local.get('plainMode', (data) => {
  if (data.plainMode) {
    document.getElementById('plain-mode').checked = true;
  }
});

document.getElementById('plain-mode').addEventListener('change', (e) => {
  chrome.storage.local.set({ plainMode: e.target.checked });
});
```

Add a checkbox to `popup.html`:
```html
<label>
  <input type="checkbox" id="plain-mode">
  Plain text only (strip all Markdown formatting)
</label>
```

---

## Chapter 6: The Options Page

An options page gives users a place to configure your extension outside the popup.

### 6.1 Create options.html

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      max-width: 600px;
      margin: 40px auto;
      padding: 0 20px;
    }
    h1 { font-size: 24px; }
    .rule {
      display: flex;
      gap: 8px;
      margin-bottom: 8px;
      align-items: center;
    }
    .rule input {
      flex: 1;
      padding: 6px;
      border: 1px solid #ccc;
      border-radius: 4px;
      font-family: monospace;
    }
    .rule button {
      padding: 6px 10px;
      background: #e74c3c;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }
    .add-btn {
      padding: 6px 16px;
      background: #1a73e8;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      margin-top: 8px;
    }
    .save-btn {
      padding: 8px 24px;
      background: #34a853;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      margin-top: 16px;
      font-size: 14px;
    }
    .status { margin-top: 8px; color: #666; }
  </style>
</head>
<body>
  <h1>Clean Copy Lite Settings</h1>
  <p>Custom find-and-replace rules are applied after every copy:</p>
  <div id="rules"></div>
  <button class="add-btn" id="add-rule">Add Rule</button>
  <br><br>
  <button class="save-btn" id="save">Save Rules</button>
  <div class="status" id="status"></div>

  <script src="options.js"></script>
</body>
</html>
```

### 6.2 Create options.js

```javascript
let rules = [];

async function loadRules() {
  const data = await chrome.storage.local.get('customRules');
  rules = data.customRules || [];
  renderRules();
}

function renderRules() {
  const container = document.getElementById('rules');
  container.innerHTML = '';
  rules.forEach((rule, i) => {
    const div = document.createElement('div');
    div.className = 'rule';
    div.innerHTML = `
      <input class="pattern" value="${escHtml(rule.pattern || '')}" placeholder="Find (regex)">
      <input class="replacement" value="${escHtml(rule.replacement || '')}" placeholder="Replace">
      <button data-index="${i}" class="remove">×</button>
    `;
    container.appendChild(div);
  });
  
  document.querySelectorAll('.remove').forEach(btn => {
    btn.addEventListener('click', () => {
      const i = parseInt(btn.dataset.index);
      rules.splice(i, 1);
      renderRules();
    });
  });
}

function escHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

document.getElementById('add-rule').addEventListener('click', () => {
  rules.push({ pattern: '', replacement: '' });
  renderRules();
});

document.getElementById('save').addEventListener('click', async () => {
  const inputs = document.querySelectorAll('.rule');
  const newRules = [];
  inputs.forEach(div => {
    const pattern = div.querySelector('.pattern').value.trim();
    const replacement = div.querySelector('.replacement').value;
    if (pattern) newRules.push({ pattern, replacement });
  });
  await chrome.storage.local.set({ customRules: newRules });
  document.getElementById('status').textContent = 'Saved! Rules will apply on next copy.';
  setTimeout(() => { document.getElementById('status').textContent = ''; }, 2000);
});

loadRules();
```

### 6.3 Register the Options Page in manifest.json

```json
"options_page": "options.html"
```

Now users can right-click your extension icon → "Options" to open the settings page.

---

## Chapter 7: Icons and Branding

Your extension needs icons. At minimum: 16×16, 48×48, and 128×128 pixels. Chrome uses 16px for the toolbar, 48px for the extensions page, and 128px for the Web Store listing.

### 7.1 Creating Simple Icons

You can create simple icons with an HTML canvas. Create `generate-icons.html` and open it in a browser:

```html
<!DOCTYPE html>
<html>
<body>
<script>
const sizes = [16, 48, 128];
sizes.forEach(size => {
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  
  // Background circle
  ctx.fillStyle = '#1a73e8';
  ctx.beginPath();
  ctx.arc(size/2, size/2, size/2 - 1, 0, Math.PI * 2);
  ctx.fill();
  
  // Letter C (simplified)
  ctx.fillStyle = 'white';
  ctx.font = `bold ${size * 0.6}px sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('C', size/2, size/2 + 1);
  
  // Download
  canvas.toBlob(blob => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `icon-${size}.png`;
    a.click();
  });
});
</script>
</body>
</html>
```

For production, use a proper icon (SVG converted to PNG, or a designer's asset). The key requirement: icons should be recognizable at 16px in the toolbar.

### 7.2 Extension Name and Description

Your extension name and description in `manifest.json` are shown in the Chrome Web Store and in `chrome://extensions`. Make them clear and descriptive:

- **Name:** "Clean Copy Lite — HTML to Markdown" (descriptive)
- **Description:** "Copy selected text as clean, formatted Markdown. Right-click, copy, paste anywhere." (tells the user exactly what it does and how to use it)

Avoid keyword stuffing, but do include relevant terms users search for: "Markdown," "copy," "format," "clipboard."

---

## Chapter 8: Publishing to the Chrome Web Store

### 8.1 Prepare Your Package

Chrome Web Store accepts a .zip file containing your extension. The zip should include:

1. `manifest.json`
2. `background.js`
3. `popup.html` + `popup.js`
4. `offscreen.html`
5. `options.html` + `options.js` (optional)
6. `icon-16.png`, `icon-48.png`, `icon-128.png`

**Important:** Remove any development-only files (test files, build scripts, `.git` folder). The zip must be under 500 MB.

Create the zip:
```bash
zip -r clean-copy-lite.zip * -x "*.git*" -x "*.md" -x "generate-icons.html"
```

### 8.2 Create a Developer Account

1. Go to [chrome.google.com/webstore/devconsole](https://chrome.google.com/webstore/devconsole)
2. Sign in with your Google account
3. Pay the one-time $5 registration fee
4. Accept the developer agreement

### 8.3 Upload Your Extension

1. In the Developer Console, click "New item"
2. Upload your .zip file
3. Fill in the store listing:
   - **Description:** Write 2-3 paragraphs explaining what your extension does, why it's useful, and how to use it. Include the key features as bullet points.
   - **Screenshots:** At least one 1280×800 screenshot showing the popup in action. You can take this by opening the popup and using Chrome's screenshot tool.
   - **Promotional images:** Optional but recommended (a small tile for the Chrome Web Store homepage).
   - **Category:** "Productivity" or "Developer Tools"
   - **Language:** English
4. Review the permission justification — Chrome will ask you to explain each permission you request
5. Submit for review

### 8.4 The Review Process

Chrome Web Store reviews typically take 1-3 business days. Common reasons for rejection:

- **Insufficient permissions justification:** If you request `activeTab`, explain "Only activated when user right-clicks or opens the popup." For `clipboardWrite`, say "Required to write formatted text to the clipboard."
- **Minimal functionality:** The extension must provide real value. A simple "Hello World" will be rejected.
- **Broken functionality:** Make sure everything works before submitting
- **Privacy concerns:** Any data collection must be disclosed. If you don't collect data, say so explicitly.

For Clean Copy Lite, the permission justification could be:

> "activeTab — Only accesses the current tab's selected text when the user right-clicks and chooses 'Copy as Markdown' or opens the popup. No background data collection. clipboardWrite — Required to write converted Markdown text to the system clipboard. scripting — Required to inject a selection-reader script into the active tab at the user's request. storage — Stores user's custom cleanup rules locally; no data is sent externally."

### 8.5 Handling Updates

When you update your extension:

1. Increment the `version` field in `manifest.json`
2. Build a new .zip
3. Upload to the Developer Console
4. Submit for review again

Minor updates (bug fixes) are usually reviewed within 24 hours. Major UI changes may take 1-3 days.

### 8.6 Post-Publish Checklist

After your extension is live:

- [ ] Verify the listing looks correct (visit the Chrome Web Store URL)
- [ ] Install from the store and test all features
- [ ] Check that screenshots are correct
- [ ] Respond to any user reviews within 48 hours
- [ ] Monitor the Developer Console for policy violation warnings

---

## Chapter 9: Testing and Debugging

### 9.1 Inspecting the Service Worker

1. Go to `chrome://extensions`
2. Find your extension
3. Click "Service Worker" (under "Inspect views")
4. A DevTools window opens showing the background service worker's console

This is where you'll see `console.log` output from `background.js`.

### 9.2 Debugging the Popup

1. Right-click your extension's toolbar icon
2. Select "Inspect popup"
3. DevTools opens for the popup HTML page

Note: The popup closes when it loses focus. To keep it open, click inside the DevTools window immediately after it opens.

### 9.3 Common Pitfalls

| Problem | Cause | Solution |
|---------|-------|----------|
| Context menu doesn't appear | `contextMenus` permission missing | Add to manifest |
| Clipboard doesn't work | MV3 service worker can't use `navigator.clipboard` | Use offscreen document |
| Extension stops working after idle | Service worker was terminated | Use `chrome.storage` for persistent state |
| Popup shows nothing | Missing permissions or JS error | Check DevTools console |
| `executeScript` returns error | Missing `scripting` permission | Add to manifest |
| Keyboard shortcut doesn't work | Shortcut conflicts with browser | Check `chrome://extensions/shortcuts` |

### 9.4 Simple Unit Tests

You can test your core logic (HTML-to-Markdown conversion) without Chrome. Create `test.js`:

```javascript
// Copy htmlToMarkdown and stripTagsSafe here (or import them)
const assert = require('assert');

// Test cases
assert.strictEqual(
  htmlToMarkdown('<h1>Title</h1>').trim(),
  '# Title'
);

assert.strictEqual(
  htmlToMarkdown('<p>Hello <strong>world</strong></p>').trim(),
  'Hello **world**'
);

assert.strictEqual(
  htmlToMarkdown('<a href="https://x.com">link</a>').trim(),
  '[link](https://x.com)'
);

console.log('All tests passed!');
```

Run with Node.js: `node test.js`

These tests run in Node, not Chrome, so they're fast for development iteration. Keep a file of 5-10 core tests and run them after every change.

---

## Chapter 10: From Lite to Production — What's Next

You've built a working Chrome extension. Here's how to take it further:

### 10.1 Firefox Port

Chrome extensions are almost compatible with Firefox (which uses the WebExtensions API). Key differences:

- **Manifest:** Firefox needs `browser_specific_settings.gecko.id`
- **Clipboard:** Firefox lets background pages use `navigator.clipboard.writeText()` directly (no offscreen document needed)
- **API prefix:** Chrome uses `chrome.*`, Firefox also supports `browser.*` (promise-based)
- **MV3:** Firefox MV3 uses event pages, not service workers

Tools like [web-ext](https://extensionworkshop.com/documentation/develop/getting-started-with-web-ext/) help with cross-browser development.

### 10.2 Premium Features

If you want to monetize your extension:

1. **Free + Pro model:** Basic features are free, advanced features (batch conversion, custom rules, cloud sync) require a license
2. **License keys:** Generate license keys via a service like Lemon Squeezy, validate against a remote API
3. **In-app purchase:** Chrome Web Store supports one-time purchases and subscriptions

Example Pro features for Clean Copy:
- Custom cleanup rule sets (save and load)
- Batch convert multiple pages
- Cloud sync of settings across devices
- PDF export

### 10.3 Analytics (Privacy-First)

Know your users without compromising privacy:

- **chrome.storage** counters: Increment a counter on each copy
- **Optional opt-in analytics:** Ask users if they want to share anonymous usage data
- **No tracking scripts:** Never inject Google Analytics or similar into web pages

A simple counter:
```javascript
chrome.storage.local.get('copyCount', (data) => {
  const count = (data.copyCount || 0) + 1;
  chrome.storage.local.set({ copyCount: count });
});
```

### 10.4 Your Extension's GitHub Repository

Publish your code on GitHub. A public repo:
- Builds trust (users can inspect the code)
- Enables community contributions
- Serves as a portfolio piece

Include:
- README with install instructions and screenshots
- MIT license
- `.github/workflows/` for CI testing

---

## Appendix A: Complete manifest.json Reference

```json
{
  // Required
  "manifest_version": 3,
  "name": "Your Extension Name",
  "version": "1.0.0",
  
  // Recommended
  "description": "What your extension does in one sentence.",
  "icons": {
    "16": "icon-16.png",
    "48": "icon-48.png",
    "128": "icon-128.png"
  },
  
  // Optional but common
  "action": {
    "default_popup": "popup.html",
    "default_title": "Tooltip text"
  },
  "background": {
    "service_worker": "background.js"
  },
  "options_page": "options.html",
  "permissions": ["activeTab", "storage", "contextMenus", "clipboardWrite", "scripting", "offscreen"],
  "commands": {
    "my-command": {
      "suggested_key": { "default": "Alt+Shift+1" },
      "description": "Run my command"
    }
  },
  
  // Rarely needed
  "host_permissions": ["https://*/*"],
  "content_scripts": [{
    "matches": ["https://*/*"],
    "js": ["content.js"]
  }]
}
```

## Appendix B: Permissions Quick Reference

| Permission | What It Allows | User Perception |
|-----------|---------------|-----------------|
| `activeTab` | Access the current tab on user action | Low concern — "only when I click" |
| `storage` | Read/write chrome.storage.local | Low — local only, no data sent |
| `contextMenus` | Add right-click menu items | Low — expected behavior |
| `clipboardWrite` | Write to system clipboard | Low — required for copy features |
| `clipboardRead` | Read from system clipboard | Medium — only if truly needed |
| `scripting` | Inject scripts into pages | Medium — explain clearly |
| `offscreen` | Create hidden documents | Low — MV3 technical requirement |
| `tabs` | Full tab info (URLs, etc.) | High — avoid when possible |
| `<all_urls>` | Access all websites | Very high — avoid unless essential |

## Appendix C: Final Checklist

Before publishing, verify:

- [ ] Extension works without errors in `chrome://extensions`
- [ ] Context menu appears on text selection
- [ ] Popup opens and converts text
- [ ] Keyboard shortcut triggers the copy
- [ ] Options page saves and loads settings
- [ ] Icons are crisp at all 3 sizes
- [ ] All permissions are justified in the store listing
- [ ] Version number is updated
- [ ] Zip contains only necessary files
- [ ] Privacy policy is mentioned (even if "no data collected")

---

## About the Author

This book was written by the team behind Clean Copy, an open-source browser extension that converts HTML to clean Markdown. Clean Copy is available for Chrome and Firefox, and has been downloaded and tested by developers worldwide.

The techniques in this book are battle-tested in a production extension with thousands of lines of code, multiple release versions, and real user feedback.

---

*© 2026. This book is provided for educational purposes. Chrome is a trademark of Google LLC. All code examples are MIT-licensed and may be used freely.*