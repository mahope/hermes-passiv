# Clean Copy MD — for Firefox

Copy any selected text as **clean, formatted Markdown** — right from your browser's right-click menu. No more messy pastes with broken styling, inline CSS junk, or lost formatting.

![Version](https://img.shields.io/badge/version-1.5.4-blue) ![Firefox](https://img.shields.io/badge/Firefox-MV3-orange) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

![Extension demo](demo-extension.gif)

## What it does
 
Select text on any webpage → right-click → **Clean Copy**:

- Converts headings, bold, italic, links, lists (nested too), code blocks, blockquotes, definition lists and tables to proper Markdown
- **Table column alignment preserved** (v1.4.1): `text-align` styles become `:---` / `:---:` / `---:` separators
- Strips ads, scripts, hidden elements and inline styling
- Unescapes HTML entities so `&amp;` becomes `&`
- Copies straight to your clipboard as clean Markdown

Keyboard shortcut: <kbd>Ctrl+Shift+C</kbd> (Windows/Linux) / <kbd>Cmd+Shift+C</kbd> (Mac)

The popup also lets you paste-and-clean: drop in dirty HTML or messy text and get clean Markdown out.

This is the Firefox port of [Clean Copy](https://github.com/mahope/clean-copy) (Chrome). Same converter core, same features. Also available as a [CLI](https://github.com/mahope/clean-copy-cli) (`brew install clean-copy`) and an [Obsidian plugin](https://github.com/mahope/clean-copy-obsidian).

## Install from source (~30 seconds)

No build step. No dependencies. Plain JavaScript.

1. Download or clone this repository:
   ```bash
   git clone https://github.com/mahope/clean-copy-firefox.git
   ```
2. Open Firefox and go to `about:debugging#/runtime/this-firefox`
3. Click **Load Temporary Add-on…**
4. Select `manifest.json` in the cloned folder
5. Done — select some text, right-click, choose **Clean Copy**

Note: temporary add-ons are removed when Firefox restarts. A signed listing on addons.mozilla.org is planned.

## Clean Copy Pro — $19/year

The free version does the whole job on any page: it never asks for an account and never phones home. Pro is for the case where the *same* cleanup has to happen every single time:

- **Custom cleanup rules** applied on every copy — your own find/replace patterns, with regex support
- **Batch conversion** of many snippets at once in the [web tool](https://cleancopy.tools/clean-copy-tool)

[Buy Clean Copy Pro — $19/year](https://buy.stripe.com/6oU4gy76PgvgdBIdAXbMQ00)

The license key arrives by email and on the thank-you page. Paste it into the extension's options page (**Add-on manager → Clean Copy MD → Preferences**, or right-click the toolbar icon → Options) and the rules unlock. One license covers 5 devices, and the free version stays free forever.

## Privacy

Clean Copy does exactly one thing on the page you're looking at, when you ask it to. There is:

- **No analytics, no tracking, no telemetry**
- **No network requests while you copy** — nothing leaves your browser
- One exception, and only if you choose it: activating or checking a **Pro license key** sends that key and a random device id to `mahope.tools` so the key can be validated. The pages you visit are never sent, and the free version never makes that call.
- Declared data collection for the free version: **none** (`data_collection_permissions` in the manifest)

## Tests

```bash
node tools/test_clean_copy.js
```

## Support

Clean Copy is free and MIT-licensed, and it stays that way. If it saved you a bit of time, a [small donation](https://donate.stripe.com/7sYeVcbn50wieFM8gDbMQ0c) keeps the free tools maintained.

## License

MIT
