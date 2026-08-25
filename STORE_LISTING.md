# Chrome Web Store — listetekster (iteration 120)

Klar til copy-paste når upload kan ske (developer dashboard, ~5 min).
Zip: `clean-copy.zip` i repoets rod (v1.1.0, activeTab-only).

## Store listing

**Name:** Clean Copy — Copy as Markdown

**Summary (132 chars max):**
Copy selected text as clean, formatted Markdown. No messy pastes. No tracking, no network requests.

**Category:** Productivity → Tools
**Language:** English

**Description:**

Select text on any page, right-click, and Clean Copy puts properly formatted Markdown on your clipboard.

WHAT IT CONVERTS
• Headings (h1–h6) → # levels
• Bold, italic, strikethrough
• Links (kept, junk URLs stripped)
• Nested lists (ul/ol)
• Code blocks and inline code
• Blockquotes
• Tables
• Images (as ![alt](src))

WHAT IT REMOVES
• Ads, scripts and hidden elements
• Inline styles and CSS classes
• HTML entities (&amp; becomes &)
• Tracking parameters in links

PRIVACY FIRST
No analytics. No telemetry. No network requests — nothing ever leaves your browser. Clean Copy only reads the page when you click the menu item or use the shortcut.

SHORTCUT
Ctrl+Shift+C (Windows/Linux), Cmd+Shift+C (Mac)

Also included: a popup where you can paste dirty HTML or messy text and get clean Markdown back.

Free, open source: https://github.com/mahope/clean-copy

## Review notes for testers (single-purpose justification)

Single purpose: convert a user-selected portion of the current tab's text to Markdown and copy it to the clipboard.

Permission justification:
- activeTab + scripting: inject the converter into the current tab only when the user invokes the context-menu item or keyboard shortcut.
- clipboardWrite: write the converted Markdown to the clipboard.
- contextMenus: provide the "Clean Copy" right-click item.
- offscreen + storage: MV3 service workers have no DOM; an offscreen document provides a reliable clipboard fallback.
- No host permissions. No remote code. No network access of any kind.
