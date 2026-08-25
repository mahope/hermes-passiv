# EAA Compliance Checklist for WordPress Sites

## A Practical Guide to Meeting EU Accessibility Requirements Under the European Accessibility Act

**Version 1.0 — August 2026**

---

## Foreword

If you manage WordPress sites for EU clients, the European Accessibility Act (EAA) affects you directly.

The EAA requires that digital services — including websites, mobile apps, and e-commerce platforms — meet specific accessibility standards. The deadline (June 28, 2025) has now passed. Enforcement is ramping up across EU member states.

This is not about "nice to have" accessibility. This is about legal compliance.

This guide gives you a practical, step-by-step checklist for making WordPress sites EAA-compliant. No theory, no abstract standards — just actionable tasks you can work through site by site.

---

## Chapter 1: Is Your Site in Scope?

The EAA applies to **digital services** offered in the EU. If your agency builds, hosts, or maintains any of the following, you are in scope:

| Service type | Examples | In scope? |
|-------------|----------|-----------|
| E-commerce | WooCommerce stores, membership sites, booking systems | ✅ Yes |
| Public sector | Municipality sites, government services | ✅ Yes (also covered by EN 301 549) |
| Banking/Insurance | Financial service sites | ✅ Yes |
| Transport | Booking portals, schedule sites | ✅ Yes |
| Telecom | ISP portals, mobile operator sites | ✅ Yes |
| Private blogs | Personal sites, portfolio sites | ❌ No (unless commercial) |
| Brochure sites | Small business info sites | ⚠️ Likely yes if selling |

### The Key Question

Ask this for every site you manage:

> *Does this site offer a service or product to the EU public?*

If yes, it needs to be EAA-compliant. Content management systems (WordPress), e-commerce platforms (WooCommerce), and booking systems are explicitly included.

---

## Chapter 2: The 10-Point EAA Compliance Checklist

This is the core of the guide. Each item is a concrete check that you can run on any WordPress site. Pass all 10, and the site is demonstrably EAA-compliant.

### 1. Color Contrast (WCAG 2.1 AA)

**Requirement:** Text must have a contrast ratio of at least 4.5:1 (normal text) or 3:1 (large text 18pt+ / 14pt bold+).

**How to check:**
- Use the **WebAIM Contrast Checker** (webaim.org/resources/contrastchecker/)
  - Enter the text color hex and background color hex
  - Pass/fail result instantly
- Testing tool: **Accessibility Insights** browser extension (free, Microsoft)
- Testing tool: **WAVE** browser extension (free, WebAIM)
- Quick check: Toggle "High Contrast" mode in browser dev tools

**Common WordPress violations:**
- Light gray text on white backgrounds (most common)
- Blue link text on blue-ish backgrounds
- Footer text on dark backgrounds
- Button text against button colors

**Fix:** Adjust colors in the theme customizer, or add custom CSS. If the theme is locked, create a child theme.

### 2. Alt Text on All Images

**Requirement:** Every meaningful image must have alt text. Decorative images must have `alt=""` (empty alt).

**How to check:**
- Run the **WAVE extension** — it lists all missing alt attributes
- Browser DevTools > Accessibility tab > inspect images
- For WooCommerce: check product images, category images

**Common violations:**
- Gallery images uploaded without alt text
- Logo in header/ footer without alt
- Social media icons without alt
- Decorative spacer images without `alt=""`

**Fix in WordPress:**
- Edit Media > Alternative Text field
- For existing sites with hundreds of images: use a plugin like **Accessibility Checker** to bulk-fill missing alt text
- Add `alt=""` for decorative images via filter functions

### 3. Heading Structure (h1-h6 Hierarchy)

**Requirement:** Headings must form a logical hierarchy. No skipped levels. No heading used purely for styling.

**How to check:**
- Install the **HeadingsMap** browser extension
- It shows the full heading outline — look for:
  - No h1 → fail
  - h1 → h3 (skipping h2) → fail
  - Multiple h1s → fail
  - Text styled as heading but not marked as heading → fail

**Common violations:**
- Theme logo is a div, not an h1
- Widget headings jump from h2 to h4
- Page builders create headings at arbitrary levels
- Content editors use bold text instead of heading tags

**Fix:** Map the site's heading outline. Rename heading levels in the theme files or use a plugin that enforces accessibility-ready heading blocks.

### 4. Keyboard Navigation

**Requirement:** Every interactive element must be reachable and operable via keyboard alone. No "keyboard trap" where focus gets stuck.

**How to check:**
- Navigate the entire site using only **Tab**, **Shift+Tab**, **Enter**, and **Escape**
- Can you reach every link, button, and form field?
- Is there a visible **focus indicator** on every element? (blue outline or similar)
- Can you open all menus, dropdowns, and modals?
- Can you close them with Escape?

**Common violations:**
- Mega menus that don't work with keyboard
- Modal popups that trap focus
- Custom select/dropdown elements that aren't keyboard accessible
- "Skip to content" link missing or broken

**Fix:**
- Add a "Skip to content" link as the first focusable element
- Ensure all custom JavaScript components handle keyboard events
- Use native HTML elements (button, a) instead of divs with click handlers

### 5. Screen Reader Compatibility

**Requirement:** Content must be readable by screen readers. This means proper ARIA labels, semantic HTML, and logical reading order.

**How to check:**
- Turn on **VoiceOver** (macOS: Cmd+F5) or **NVDA** (Windows, free)
- Navigate the page — does it make sense when read linearly?
- Do images have alt text that describes the content?
- Do form fields have proper labels?
- Are dynamic content updates announced?

**Common violations:**
- "Read more" links without context (should say "Read more about [page title]")
- Form fields without `<label>` elements
- Buttons with icon-only content and no aria-label
- Auto-playing video/audio without pause controls

**Fix:**
- Add descriptive link text or use `aria-label`
- Ensure every `<input>` has a matching `<label>`
- Add `aria-live` regions for dynamic content

### 6. Forms and Input Validation

**Requirement:** Forms must be accessible. Error messages must be clear and programmatically associated with the field.

**How to check:**
- Submit a form with invalid data — are errors communicated clearly?
- Are error messages linked to the input field via `aria-describedby`?
- Does the focus move to the first error?
- Are required fields marked with `aria-required` or text?

**Common violations:**
- Inline validation messages that disappear too fast
- Color-only error indicators (red border without text)
- CAPTCHAs that are not accessible (reCAPTCHA v2 has audio fallback, but test it)
- Confirmation messages that are not detected by screen readers

**Fix:**
- Use inline error messages with clear text
- Add `aria-describedby` connecting error to field
- Use accessible CAPTCHA alternatives (honeypot + time-based check)
- Use `aria-live="polite"` for confirmation messages

### 7. Links and Navigation

**Requirement:** Links must be distinguishable and meaningful. No "click here", no "read more" without context.

**How to check:**
- Scan all links on the page — does each link text describe its destination?
- Are links visually distinguishable from surrounding text (underlined or high contrast color)?
- Do navigation menus have consistent structure across pages?

**Common violations:**
- "Click here" / "Learn more" / "Read more" as link text
- Color-only distinction for links (no underline)
- Same link text pointing to different URLs
- Broken anchor links

**Fix:**
- Rewrite link text to describe the target page
- Add `text-decoration: underline` to links (user preference style)
- Run a link checker (W3C Link Checker or browser extension)

### 8. Multimedia: Video and Audio

**Requirement:** All pre-recorded video must have captions. Audio must have transcripts. Live video must have captions where feasible.

**How to check:**
- Does every embedded video (YouTube, Vimeo) have captions turned on?
- Do audio players have visible play/pause/volume controls?
- Are auto-playing videos controllable?
- Is there a transcript for podcast/audio content?

**Common violations:**
- YouTube videos without auto-captions (auto-generated are insufficient for compliance)
- Background video with no pause button
- Audio content with no text alternative
- Animated GIFs with no description

**Fix:**
- Upload corrected captions to YouTube/Vimeo
- Add a "Pause" button for all moving content
- Provide text transcripts below audio embeds
- Add `aria-label` to describe GIF content

### 9. Resize and Zoom

**Requirement:** Content must be readable when zoomed to 200%. No horizontal scrolling. No text clipping.

**How to check:**
- Open the site
- Zoom to 200% (Cmd++ on macOS, Ctrl++ on Windows)
- Does the layout reflow or require horizontal scrolling?
- Is all text readable?
- Do buttons and links still have enough padding to be clickable?

**Common violations:**
- Fixed-width containers that don't scale
- Text in images that pixelate at 200%
- Off-canvas menus that overflow at zoom
- Tables with many columns that break layout

**Fix:**
- Use relative units (rem, %) instead of fixed px widths
- Test the theme's responsive breakpoints
- For complex tables: use responsive table techniques (horizontal scroll on mobile, or stacked rows)

### 10. Accessibility Statement

**Requirement:** EAA requires a published accessibility statement on the site. This includes current compliance status, contact information, and a process for reporting issues.

**How to check:**
- Is there an accessibility statement page?
- Does it include:
  - Compliance status (e.g., "Partially compliant with WCAG 2.1 AA")
  - Contact method for accessibility issues
  - Description of known limitations
  - Expected response time (typically 5 business days)

**Common violations:**
- No accessibility statement at all
- Statement is generic boilerplate with no actual commitment
- No contact form or email for reporting issues
- Statement claims "fully compliant" without evidence

**Fix:**
- Create a `/accessibility-statement/` page
- Use the EAA-compliant statement generator (w3.org/WAI/accessibility-statement/)
- Include a contact form or dedicated email
- Update when compliance status changes

---

## Chapter 3: Testing Tools (All Free)

| Tool | What it checks | Cost |
|------|---------------|------|
| WAVE Browser Extension | All 10 points, visual overlay | Free |
| Axe Browser Extension | Automated WCAG 2.1 AA checks | Free |
| Lighthouse (Chrome DevTools) | Integrated audit with scores | Free (built into Chrome) |
| WebAIM Contrast Checker | Color contrast ratios | Free |
| NVDA Screen Reader | Full screen reader test | Free (Windows) |
| VoiceOver | Full screen reader test | Free (macOS) |
| Accessibility Insights | Guided manual testing | Free (Microsoft) |
| HeadingsMap | Heading structure outline | Free |

**Recommended workflow:**
1. Run **Lighthouse** accessibility audit → fix automated findings
2. Run **WAVE** → fix reported errors and contrast issues
3. Run **HeadingsMap** → fix heading hierarchy
4. Manual **keyboard navigation** test
5. Test with **NVDA or VoiceOver** on 3 key pages

---

## Chapter 4: 14-Day Fix Plan

| Day | Task | Time |
|-----|------|------|
| 1 | Run Lighthouse + WAVE audit. Document all issues | 1h |
| 2 | Fix all color contrast issues (check 1) | 1h |
| 3 | Add alt text to all images (check 2) | 1-3h |
| 4 | Fix heading hierarchy (check 3) | 1h |
| 5 | Test and fix keyboard navigation (check 4) | 2h |
| 6 | Test screen reader flow (check 5) | 1h |
| 7 | Fix form accessibility (check 6) | 1h |
| 8 | Fix links and navigation (check 7) | 1h |
| 9 | Fix multimedia issues (check 8) | 1h |
| 10 | Test resize and zoom (check 9) | 30min |
| 11 | Create accessibility statement (check 10) | 1h |
| 12 | Final full audit | 1h |
| 13 | Client handover: document what was done | 1h |
| 14 | Set up monitoring: quarterly re-scans | 30min |

---

## Chapter 5: Making EAA Compliance a Revenue Stream

For agencies, EAA compliance is not just a legal obligation — it is a service you can sell.

### Service Pricing Guide

| Service | Description | Price range |
|---------|-------------|------------|
| EAA Audit | Full automated + manual audit with report | €500-1,500 |
| EAA Remediation | Fix all 10 checklist items | €1,000-5,000 |
| EAA Maintenance | Quarterly re-scans + fixes | €200-500/mo |
| Accessibility Statement setup | Create + publish | €150-300 |

### Selling Compliance as a Service

Use the checklist in this guide as your service scope. When a client asks "what does EAA compliance cost?", hand them the 10-point checklist and say: *"Each of these needs to be checked and fixed. We can do it all."*

The 14-day fix plan becomes your project timeline. The accessibility statement becomes your deliverable.

---

## Appendix A: Quick Reference Card

Print this and keep it at your desk.

```
EAA QUICK CHECK (WordPress)
─────────────────────────────
☐ Color contrast ≥ 4.5:1 → WebAIM tool
☐ All images have alt text → WAVE tool
☐ Heading hierarchy logical → HeadingsMap
☐ Full keyboard navigation → Tab test
☐ Screen reader compatible → VoiceOver/NVDA
☐ Forms have error messages → Submit test
☐ Links are descriptive → Visual scan
☐ Videos have captions → Player check
☐ 200% zoom no horizontal scroll → Zoom test
☐ Accessibility statement published → Site check
```

---

## Appendix B: Sample Accessibility Statement (Template)

```
ACCESSIBILITY STATEMENT
Last updated: [DATE]

[AGENCY/SITE NAME] is committed to ensuring digital accessibility for
people with disabilities. We are continually improving the user experience
for everyone and applying the relevant accessibility standards.

Compliance Status
We strive to conform to WCAG 2.1 Level AA, which is the standard required
under the European Accessibility Act.

Current Status: [Full compliance / Partial compliance]
Known limitations: [List any known issues]

Feedback
We welcome your feedback on the accessibility of this site.
Please contact us:
Email: accessibility@[domain]
Phone: [optional]
Response time: Within 5 business days

Technical specifications
- Accessibility relies on the following technologies: HTML, WAI-ARIA,
  CSS, JavaScript
- These technologies are relied upon for conformance with accessibility
  standards

Assessment approach
We assess accessibility using automated tools (Lighthouse, WAVE) and
manual testing (keyboard navigation, screen reader testing).

This statement was last reviewed on [DATE] and will be updated annually.
```

---

## Final Words

EAA compliance for WordPress sites is achievable without a massive budget. The 10-point checklist covers the vast majority of issues found on the average WordPress site. Most fixes take an hour or less.

The agencies that treat accessibility as a feature — and learn to sell it — will win more clients, charge higher rates, and avoid the fines that are now being enforced across Europe.

Start with one site. Run the checklist. Fix what's broken. Document what you did. That is compliance.

---

**Version 1.0 — August 2026**
Published by Mahope / Hermes Passiv

*This guide provides practical guidance based on publicly available information about the European Accessibility Act. It does not constitute legal advice. For specific legal questions, consult a qualified attorney in your jurisdiction.*