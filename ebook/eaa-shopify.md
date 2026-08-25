# EAA Compliance for Shopify Stores

## A Practical Guide to Meeting EU Accessibility Requirements Under the European Accessibility Act

If your Shopify store sells to customers in the European Union, the European Accessibility Act (EAA) applies to you — regardless of where your business is registered. This guide walks through exactly what you need to check, fix, and document.

## Chapter 1: What the EAA Means for Your Shopify Store

The European Accessibility Act (Directive 2019/882) took full effect on June 28, 2025. It requires that products and services sold in the EU meet common accessibility standards. For e-commerce stores — including those built on Shopify — this means your website must be usable by people with disabilities.

### Who must comply

Any business selling to EU consumers, regardless of where the business is headquartered. A Shopify store based in New York, Sydney, or Singapore that ships to customers in Germany, France, or Spain must comply.

### Covered products and services under the EAA

For an e-commerce store, the EAA covers:

- The entire browsing experience (product catalog, search, navigation)
- Product selection and purchasing (filters, size/color selectors, add-to-cart)
- Checkout and payment flows
- Customer accounts and order tracking
- Contact forms and support interfaces

### What happens if you don't comply

Each EU member state sets its own penalties. Current enforcement examples:

- Germany (BFSG): fines up to €100,000 per violation
- France: fines up to €75,000, with daily penalties for ongoing non-compliance
- Netherlands: administrative fines, plus orders to remediate within deadlines
- Spain: fines up to €600,000 for serious infractions
- Sweden: fines up to €900,000

Beyond fines: enterprise partners increasingly ask for proof of EAA compliance before signing contracts. A non-compliant store can lose B2B revenue even without a direct fine.

### The standard you need to meet

The EAA references EN 301 549, which in turn references WCAG 2.1 Level AA as the baseline technical standard. From 2026, WCAG 2.2 Level AA is increasingly the expected level. Practically, WCAG 2.1 AA covers everything you need for compliance — WCAG 2.2 adds a few new criteria that most Shopify themes already meet.

## Chapter 2: EAA Compliance Requirements for E-commerce

The EAA's accessibility requirements map to four principles, known as POUR:

### Perceivable

Information and user interface components must be presentable to users in ways they can perceive.

For a Shopify store this means:
- Text must have sufficient contrast against backgrounds (WCAG 1.4.3: 4.5:1 ratio for normal text, 3:1 for large text)
- Images must have text alternatives (alt text) — especially product images
- Content must adapt to different screen sizes and zoom levels
- Colour must not be the only way to convey information (e.g., price changes indicated by colour alone)

### Operable

User interface components and navigation must be operable.

For a Shopify store this means:
- All functionality must be available from a keyboard (no mouse-only interactions)
- Users must have enough time to read and use content
- Content must not cause seizures (no flashing animations)
- Navigation must be consistent and predictable
- Focus indicators must be visible when tabbing through the page

### Understandable

Information and the operation of the user interface must be understandable.

For a Shopify store this means:
- Text must be readable (plain language where possible)
- Pages must appear and operate in predictable ways
- Input assistance must help users avoid and correct mistakes
- Form labels must be clear and associated with their fields

### Robust

Content must be robust enough to be interpreted by a wide variety of user agents, including assistive technologies.

For a Shopify store this means:
- HTML must be valid and semantically correct
- ARIA landmarks and roles must be used correctly where needed
- Custom interactive elements (sliders, accordions, modals) must work with screen readers

## Chapter 3: 10 Most Common Accessibility Failures on Shopify

Through automated scanning of hundreds of Shopify stores, these are the most frequent failures:

### 1. Missing alt text on product images

Product images are the heart of a Shopify store. Alt text is often left empty or filled with generic text like "product image" or the filename.

The fix: In the Shopify admin, edit each product and fill the "Alt text" field (a.k.a. image alt tag in the media manager). Describe the product clearly: "Red cashmere scarf draped over a wooden chair, soft lighting" rather than "scarf.jpg".

### 2. Low contrast text

Shopify themes frequently use light grey text on white backgrounds — especially for prices, sale badges, and secondary information. This fails WCAG 1.4.3.

The fix: In Theme Editor (customize), go to Theme Settings → Typography or Colour. Increase contrast of body text. If the theme doesn't allow per-element control, add CSS via Custom CSS: `body { color: #1a1a1a; }` or override specific text colours.

### 3. Empty buttons and unlabelled links

"Add to cart" buttons that use only an icon without accessible text. Social media icons without aria-labels. "Read more" links that don't describe where they lead.

The fix: Use `aria-label` on icon-only buttons. For social links: `<a href="..." aria-label="Follow us on Instagram">...</a>`. Replace generic links with descriptive text.

### 4. Missing form labels

Newsletter signup forms, search bars, and contact forms often have placeholder text but no proper `<label>` element.

The fix: Wrap form fields in `<label>` tags or use `aria-label`. In Shopify, edit your newsletter section and ensure labels are visible. Placeholder text alone is not sufficient for legal compliance.

### 5. Keyboard traps

Product modals (quick-view, size guide, cart drawer) that trap keyboard focus — users can tab into them but not out. This is a WCAG 2.1.2 failure and a common issue in many Shopify themes.

The fix: Ensure the Escape key closes the modal and returns focus to the trigger element. Test by tabbing through your site without using a mouse.

### 6. Missing page title and language

Shopify auto-generates page titles, but custom pages often have empty or duplicate titles. Missing `<html lang="...">` attribute is also common.

The fix: In Theme Settings → Search engine listing, set a unique title for each page. Verify the `<html>` tag includes `lang="en"` (or your store's language).

### 7. Non-descriptive link text

"Click here", "Shop now", "Learn more" — these appear everywhere on Shopify stores. Screen reader users tab through links and hear each one in isolation.

The fix: Make link text unique and descriptive. "Shop men's winter jackets" instead of "Shop now". "Read our shipping policy" instead of "Click here".

### 8. Inaccessible colour swatches

Size, color, and material selectors that rely solely on colour to show the selected state. A colour-blind user or screen reader user cannot tell which option is selected.

The fix: Show both colour and text label on each swatch. Add a visible border or checkmark to the selected swatch. Ensure selected state is announced by screen readers.

### 9. Insufficient focus indicators

When tabbing through a Shopify store, the default blue outline is often removed by theme CSS (`outline: none`) without providing a visible replacement.

The fix: In Custom CSS, add: `*:focus-visible { outline: 3px solid #0066cc; outline-offset: 2px; }`. Never remove focus outlines without providing a visible alternative.

### 10. Missing accessibility statement

The EAA requires an accessibility statement on your store. Most Shopify stores don't have one.

The fix: Create a dedicated page at `/pages/accessibility-statement` listing your conformance level, any known issues, how to give feedback, and the supervisory authority for complaints. We provide a template in Chapter 7.

## Chapter 4: Fixing Product Images — The Right Way

Product images are your biggest accessibility surface area. Most Shopify stores have dozens to thousands of images, each needing proper alt text.

### Shopify's alt text system

In Shopify admin, each product image can have alt text. Here's where to find it:

1. Go to Products → All products
2. Click a product
3. Scroll to the Media section
4. Click an image
5. Find the "Alt text" field
6. Enter a descriptive text

### What good alt text looks like

Bad: "Blue sweater"
Good: "Navy blue merino wool sweater with crew neck, photographed on a grey mannequin against white background — front view"

Bad: "Product image"
Good: "Handcrafted ceramic coffee mug in matte sage green, 350ml capacity — shown with saucer from a 45-degree angle"

Bad: "Red shoes 2"
Good: "Women's size 37 red leather ballet flats with gold buckle detail, top-down view on marble floor"

### Batch editing alt text

For stores with hundreds of products, consider:

- Exporting products via Shopify's CSV export/import
- Filling alt text in a spreadsheet
- Importing back into Shopify
- Or hiring a virtual assistant for one-off batch work
- AI alt-text generators (several Shopify apps exist — review output manually, they can miss context)

### When alt text isn't needed

Decorative images (background textures, purely decorative icons, spacers) should have empty alt text: `alt=""`. This tells screen readers to skip them. Do not omit the alt attribute entirely — that causes some screen readers to read the image filename.

## Chapter 5: Theme Accessibility

Your Shopify theme controls most of the accessibility surface. Some themes are better than others.

### Choosing an accessible theme

Shopify's "Dawn" theme (the default) is a good starting point for accessibility. Other themes from the Shopify Theme Store vary widely. Look for themes that:

- Use semantic HTML (proper heading hierarchy: h1, h2, h3 in order)
- Include visible focus indicators
- Have configurable contrast settings
- Support proper keyboard navigation
- Include ARIA landmarks

### Contrast: the most common theme failure

Many premium Shopify themes use designer-approved colour palettes that fail contrast checks. The most common pattern: light grey (#999 or #aaa) body text on white background.

Test every text colour in your theme using a contrast checker. WCAG 2.1 AA requires:

- Normal text (< 18px or < 14px bold): 4.5:1 contrast ratio
- Large text (≥ 18px or ≥ 14px bold): 3:1 contrast ratio
- UI components and icons: 3:1 contrast ratio

### Custom CSS for accessibility

Add these rules to your theme's Custom CSS (in Theme Editor → Custom CSS):

```css
/* Ensure all text meets contrast */
body, p, li, .text-body {
  color: #1a1a1a;
}

/* Visible focus for keyboard users */
*:focus-visible {
  outline: 3px solid #0066cc !important;
  outline-offset: 2px !important;
}

/* Remove focus outline only when using mouse */
*:focus:not(:focus-visible) {
  outline: none;
}

/* Ensure links are distinguishable */
a { text-decoration: underline; }
a:hover { text-decoration-thickness: 2px; }
```

### Testing keyboard navigation

Go through your entire Shopify store using only the Tab, Shift+Tab, Enter, and Escape keys:

1. Can you reach every link and button?
2. Can you see which element is focused at all times?
3. Can you close all modals and drawers?
4. Can you complete a purchase without the mouse?

If any step fails, you have a keyboard accessibility issue.

## Chapter 6: Checkout and Forms Accessibility

The checkout is your revenue conversion point. An inaccessible checkout loses sales.

### Common Shopify checkout issues

1. **Auto-focus issues**: Some themes move focus unexpectedly during checkout, disorienting screen reader users. Test the complete checkout flow.

2. **Error messages**: Inline validation errors that aren't announced. Ensure error messages use `aria-describedby` on the invalid field. Shopify Checkout (Shopify's hosted checkout) is generally good — custom checkouts are where problems arise.

3. **CAPTCHA**: If you use CAPTCHA on any form, provide an audio alternative. Google reCAPTCHA v3 (invisible) avoids this issue entirely.

4. **Address auto-complete**: Fields that change content dynamically need to announce changes to screen readers.

### Shopify's hosted checkout vs. custom checkout

- **Shopify Checkout** (default): Shopify manages the accessibility of the checkout flow. It's reasonably good and continuously improving. Stick with it if possible.
- **Custom checkout** (Shopify Plus or third-party): You are fully responsible. Every form field, dropdown, and validation message must meet WCAG.

### Form accessibility checklist

Every form on your store should:

- Have visible `<label>` elements for each field
- Group related fields with `<fieldset>` and `<legend>`
- Show clear error messages linked to the field via `aria-describedby`
- Not auto-submit on field change without warning
- Support autocomplete attributes (`autocomplete="given-name"`, `autocomplete="email"`, etc.)

## Chapter 7: The EAA Accessibility Statement

The EAA requires an accessibility statement. This is the most commonly missed requirement.

### What must be in the statement

| Field | Required | Details |
|-------|----------|---------|
| Name and contact of the merchant | Yes | Business name, address, email |
| Products/services covered | Yes | "This statement applies to our website at [URL]" |
| Conformance level | Yes | "WCAG 2.1 Level AA" |
| Known non-conformances | Yes | List any known accessibility issues, with reasons and remediation timeline |
| Date of preparation | Yes | When this statement was created |
| Last review date | Yes | When it was last reviewed/updated |
| Feedback mechanism | Yes | Email or form for accessibility feedback |
| Supervisory authority contact | Yes | Contact details for the EU member state's relevant authority |

### Sample accessibility statement

> **Accessibility Statement for [Store Name]**
>
> Last updated: [date]
>
> [Store Name] is committed to ensuring digital accessibility for all users, regardless of technology or ability. We are actively working to make our website at [URL] accessible in accordance with the European Accessibility Act (Directive 2019/882) and EN 301 549, which references WCAG 2.1 Level AA.
>
> **Conformance status**
>
> As of [date], [URL] is partially compliant with WCAG 2.1 Level AA. We have identified and are working to remediate the following known non-conformances:
>
> - [Known issue 1, e.g., "Product images published before [date] may lack descriptive alt text"]
> - [Known issue 2, e.g., "Legacy product pages from [version] have heading hierarchy issues"]
>
> **Feedback**
>
> If you encounter an accessibility barrier on our website, please contact us at [accessibility@store.com]. We aim to respond within 5 business days and resolve issues within 30 days where feasible.
>
> **Supervisory authority**
>
> If you are not satisfied with our response, you may contact:
> [Name of national authority]
> [Address]
> [Email/Website]
>
> **Preparation date:** [date]
> **Last reviewed:** [date]
> **Next review:** [date + 3 months]

### Where to publish the statement

Create a page on your Shopify store at `/pages/accessibility-statement`. Link to it from your footer or legal section alongside your Privacy Policy and Terms of Service.

### How often to update

Review the statement every three months. Update it any time there is a material change in your compliance posture — for example after a theme change, major feature release, or remediation work.

## Chapter 8: Testing Your Shopify Store

You don't need expensive tools to check EAA compliance. Here's a tiered approach:

### Free — every store should do this

1. **Our EAA/WCAG Scanner** ([hermes-passiv.pages.dev/scan](https://hermes-passiv.pages.dev/scan)): Paste your store URL, get an instant letter grade with every issue listed by severity. 16 automated checks covering alt text, contrast, form labels, headings, language, and more.

2. **WAVE Browser Extension**: Install the WAVE toolbar (free Chrome/Firefox extension). Scan any page for contrast errors, missing alt text, and structural issues.

3. **Manual keyboard test**: Tab through your entire site. Note any focus loss, keyboard traps, or invisible elements.

4. **Contrast checker**: Use WebAIM's free contrast checker to test all text colours in your theme against their background.

5. **Screen reader test**: Use VoiceOver (macOS, built-in) or NVDA (Windows, free) to navigate your store. Listen for issues: does the screen reader announce product names, prices, and add-to-cart buttons correctly?

### Low-cost — for stores ready to invest

- **axe DevTools (free tier)**: Browser extension that runs automated WCAG checks
- **Lighthouse (built into Chrome DevTools)**: Generates an accessibility score with specific fixes
- **SiteImprove (free tier)**: Scans for accessibility issues across your entire store

### Professional — for enterprise contracts

- **Manual accessibility audit by a qualified agency** ($500-5,000)
- **Automated monitoring tools** ($10-200/month)
- **VPAT (Voluntary Product Accessibility Template)** — often requested by enterprise buyers

### Testing frequency

| Phase | Frequency |
|-------|-----------|
| Automated scan | Every theme update or major change |
| Manual keyboard test | Monthly |
| Full audit | Quarterly |
| Accessibility statement review | Every 3 months, or after any material change |

## Chapter 9: Maintaining Compliance Over Time

EAA compliance is not a one-time project. Your store changes — new products, new theme versions, new apps — and each change can introduce new issues.

### Build compliance into your workflow

1. **New product check**: Before publishing a new product, verify alt text on all images, check that descriptions don't use colour alone to convey information, and test the product page with Tab navigation.

2. **Theme updates**: Before applying a theme update, test critical pages (homepage, a product page, checkout) with your scanner and keyboard.

3. **App reviews**: Before installing a Shopify app, check whether it uses custom UI elements (modals, sliders, dropdowns) that could introduce accessibility issues. Test each new app.

4. **Regular scans**: Run an automated scan monthly. Set a calendar reminder.

5. **Statement reviews**: Update your accessibility statement every quarter and any time there's a material change.

### What happens when enforcement comes

EAA enforcement varies by member state, but the pattern is consistent:

1. A customer or competitor files a complaint with the national supervisory authority
2. The authority contacts you and requests evidence of compliance attempts
3. If your statement is current and shows ongoing remediation, you get a notice period
4. If you have no statement and no evidence of effort, the fine is larger

The presence of an up-to-date accessibility statement showing active remediation substantially reduces penalty risk. Most authorities give remediation time if you can show good faith.

### Record keeping

Keep records of:
- Accessibility scan results (date, score, issues found)
- Remediation actions taken
- Accessibility statement versions (date and content)
- Any accessibility-related correspondence

These records serve as evidence of good faith if you are ever investigated.

## Appendix A: EAA Compliance Quick Checklist

### Theme and layout
- [ ] All text meets WCAG 2.1 AA contrast (4.5:1 normal, 3:1 large)
- [ ] Colour alone is not used to convey information (price changes, sale indicators)
- [ ] Page has proper heading hierarchy (one h1, followed by h2, h3)
- [ ] Skip-to-content link is present at the top of the page
- [ ] Focus indicators visible on all interactive elements
- [ ] Page language is set in `<html lang="...">`

### Images and media
- [ ] All product images have descriptive alt text
- [ ] Decorative images have empty alt text (`alt=""`)
- [ ] No images of text used where real text could be used
- [ ] Videos have captions or transcripts

### Navigation and interactions
- [ ] All functionality works with keyboard alone
- [ ] No keyboard traps in modals, drawers, or quick-view
- [ ] Focus order matches visual order (left to right, top to bottom)
- [ ] Link text is unique and descriptive (no "click here" or "read more")
- [ ] Dropdown menus work with keyboard (Enter opens, Escape closes)
- [ ] Colour swatches show selected state with text/border, not colour alone

### Forms and checkout
- [ ] Every form field has a visible `<label>` element
- [ ] Error messages are linked to the field via `aria-describedby`
- [ ] Required fields are clearly marked (visual + text for screen readers)
- [ ] Autocomplete attributes are set on checkout fields
- [ ] CAPTCHA has audio alternative or uses invisible version

### Documentation
- [ ] Accessibility statement is published at `/pages/accessibility-statement`
- [ ] Statement includes all required fields (see Chapter 7)
- [ ] Statement is linked from footer
- [ ] Statement is reviewed quarterly
- [ ] PDF receipts and invoices are accessible (text-based, not scanned images)

## Appendix B: Resources

### Free testing tools
- **EAA/WCAG Scanner**: hermes-passiv.pages.dev/scan — 16 automated checks
- **Ask the AI compliance assistant**: https://hermes-passiv.pages.dev/books/eaa-shopify#bookAi — free answers to EAA questions, no signup
- **WAVE Browser Extension**: wave.webaim.org — visual overlay of issues
- **WebAIM Contrast Checker**: webaim.org/resources/contrastchecker/
- **aXe DevTools**: deque.com/axe/devtools/ — browser extension
- **Lighthouse**: Built into Chrome DevTools → Lighthouse → Accessibility
- **NVDA Screen Reader**: nvaccess.org (Windows, free)
- **VoiceOver**: Built into macOS (System Settings → Accessibility → VoiceOver)

### Official resources
- **EAA Directive Text**: eur-lex.europa.eu (Directive 2019/882)
- **EN 301 549**: etsi.org — the European accessibility standard
- **WCAG 2.1 Quick Reference**: w3.org/WAI/WCAG21/quickref/
- **Shopify's accessibility documentation**: community.shopify.com

### About the author

This guide is published by Mahope, an EU-focused publishing imprint specialising in practical compliance resources for small web agencies and e-commerce businesses. Our tools and e-books are designed for teams without dedicated legal or compliance departments.