# EAA Compliance Scanner — WordPress plugin

Universal accessibility scanner (EAA / WCAG 2.1 AA subset, 15 rules) that runs
entirely on your own server. Works with **any theme** and scans any URL — the
engine is platform-independent (the same rule set as the web scanner at
hermes-passiv.pages.dev/scan).

## Install

1. In WordPress admin: **Plugins → Add New → Upload Plugin**
2. Choose `eaa-compliance-scanner.zip` → Install → Activate
3. Go to **Tools → EAA Scanner** and click "Scan now" (scans your front page by default)

## What it checks

Images missing alt text · form fields without labels · links/buttons with no
accessible text · duplicate id values · links opening in new windows without
warning · missing title / lang / viewport · heading structure (no h1, skipped
levels) · untitled iframes · tables without headers · aria-hidden elements that
are still focusable · low text contrast (WCAG 1.4.3) · fixed px font sizes.

## Privacy

Nothing is sent to third parties. The scan is performed by your own WordPress
server fetching the page itself.

## Honest limitation

Automated checks catch roughly 30–40% of accessibility issues. The rest needs
human judgement — see the guides and e-books at hermes-passiv.pages.dev.

## Testing

`php test_engine.php` (from this directory) exercises the engine against a
deliberately broken document (all 15 rules must fire), a clean document
(must score 100/A), and a live URL.
