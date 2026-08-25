# Firefox (AMO) listing kit — Clean Copy MD v1.1.1

Alt der skal indsættes på addons.mozilla.org Developer Hub, klar til copy-paste.
Upload kræver en Firefox-konto + API-nøgle fra https://addons.mozilla.org/developers/addon/api/key/
(eller én manuel upload via Developer Hub). Zip klar: `clean-copy-firefox-v1.1.1.zip` i repo-roden
(også på https://hermes-passiv.pages.dev/downloads/clean-copy/clean-copy-firefox-v1.1.1.zip).

**VIGTIGT — navnet:** "Clean Copy" er optaget på AMO af et urelateret URL-rensnings-tilbehør
(slug `clean-copy`, author Wavesonics, 2020) og endnu et "Clean Copy" (slug `clean-copy21`, 2025).
Firefox-versionen hedder derfor **Clean Copy MD** med gecko-ID `clean-copy-md@mahope.dk`.
Chrome-versionen beholder navnet Clean Copy — der er slug'en ledig.

---

## Listing

**Name:** Clean Copy MD

**Summary (max 250 chars):**
Copy any selected text as clean, formatted Markdown or plain text. Right-click or press Ctrl+Shift+C. No tracking, no network requests.

**Description:**

Clean Copy MD fixes the oldest annoyance on the web: you copy text from a page and it comes out wrong — smart quotes that break code, invisible characters that corrupt data, formatting soup that ruins your document.

HOW IT WORKS
1. Select any text on any web page
2. Right-click → "Copy as Clean Text" or "Copy as Markdown" — or press Ctrl+Shift+C (Cmd+Shift+C on Mac)
3. Paste. It's clean.

WHAT GETS CLEANED
• “Smart quotes” → straight quotes (" ')
• Em dashes and en dashes → regular hyphens
• Non-breaking spaces → regular spaces
• Zero-width characters (U+200B–D, U+FEFF) → removed
• Runs of spaces and blank lines collapsed

MARKDOWN MODE
Converts the selection's HTML to proper Markdown: headings (#), bold/italic, links, images, inline code and fenced code blocks, ordered and nested lists, paragraphs, horizontal rules.

PRIVACY
Everything happens locally in your browser. Clean Copy MD collects no data — the manifest declares `data_collection_permissions: none`. No servers, no analytics, no accounts, no network requests. Source code is MIT-licensed: https://github.com/mahope/clean-copy

Works on any page you can select text on. No host permissions — Clean Copy MD only touches the tab you invoke it on.

**Categories:** Productivity; Developer Tools

**Tags:** markdown, clipboard, copy-paste, clean-text, developer-tools

**Support e-mail / homepage:** https://hermes-passiv.pages.dev/clean-copy · https://github.com/mahope/clean-copy/issues

## Reviewer notes

- No minification/bundling — source is uploaded as-is. No source zip needed.
- Permissions justification:
  - `activeTab` + `scripting`: injects the selection extractor and toast into the current tab only when the user invokes Clean Copy MD (context menu or keyboard shortcut).
  - `clipboardWrite`: writes cleaned text to the clipboard from the background page.
  - `contextMenus`: registers "Copy as Clean Text"/"Copy as Markdown".
  - `storage`: remembers plain-vs-Markdown mode preference locally.
- No host permissions. No remote code. No data collection (`browser_specific_settings.gecko.data_collection_permissions.required = ["none"]`).
- Name note for reviewer: this is not related to the existing "Clean Copy" add-ons; the name distinguishes the Markdown focus.
- Test steps: select text on any page → right-click → "Copy as Markdown" → paste in a text editor.

## AMO submission facts (verified 2026-08-24)

- MV3 in Firefox uses `"background": {"scripts": [...]}` event pages, not service workers.
- New add-ons since Nov 3 2025 MUST declare `gecko.data_collection_permissions` or the submission is rejected.
- MV3 signing requires an explicit add-on ID (`clean-copy-md@mahope.dk`).
- First submission can be unlisted/self-distributed with no GUID; listed submissions need the first upload done manually in Developer Hub, then V5 API automates updates.
- All submissions get automated validation; signing typically < 24 h, manual review possible at any time.
- AMO search API: https://services.addons.mozilla.org/api/v4/addons/search/?q=clean%20copy&app=firefox (brugt til at verificere navnekonflikt).
