# EAA Accessibility Statement Template

**Version 1.0 — August 2026**
**Part of ComplianceDocs by Mahope / Hermes Passiv**

---

## About This Document

The European Accessibility Act (EAA) requires that public-facing websites in the EU carry an accessibility statement explaining their status against the Web Content Accessibility Guidelines (WCAG). This template is designed specifically for small web agencies to give their clients a compliant statement.

**Who this is for:** Web agencies, freelancers, and WordPress shops adding EAA compliance statements to client sites.

**What you get:**
- Complete accessibility statement template
- Instructions for assessing your site's compliance level
- Guidance on what to say when your site is not fully compliant (most sites aren't)

---

## Instructions

1. Run your site through a free accessibility checker (see tools below)
2. Fill in the `[BRACKETED]` fields based on your assessment
3. Publish on your website — typically in the footer and an `/accessibility` page
4. Update annually or whenever your site design changes significantly

### Recommended Free Tools

| Tool | URL | What It Checks |
|------|-----|----------------|
| WAVE Web Accessibility Tool | https://wave.webaim.org | Full page audit with visual overlays |
| axe Browser Extension | Deque's axe DevTools | Automated WCAG 2.1 AA checks |
| Lighthouse (Chrome DevTools) | Built into Chrome | Accessibility score + recommendations |
| Colour Contrast Analyzer | https://webaim.org/resources/contrastchecker | Specific colour pair checks |
| HTML Validator | https://validator.w3.org | Structural markup compliance |

---

## Accessibility Statement

**Last updated:** [Date]

**Website:** [Client Website URL]

---

### 1. Commitment

[Client Name] is committed to ensuring digital accessibility for all users, regardless of ability. We are continuously improving the user experience for everyone and applying the relevant accessibility standards.

### 2. Compliance Status

This website is **[fully / partially / not yet]** compliant with the European Accessibility Act (EAA) and Web Content Accessibility Guidelines (WCAG) 2.1 Level AA.

**Choose one:**

> **Fully compliant:** This website meets all WCAG 2.1 AA requirements. We continuously monitor and maintain compliance.

> **Partially compliant:** This website partially meets WCAG 2.1 AA standards. Some content may not fully conform. We are actively working to resolve identified issues.

> **Not yet compliant:** This website has not yet been fully assessed for EAA compliance. We are in the process of auditing and updating our content.

### 3. What We Have Done

We have implemented the following measures to improve accessibility:

- Added alternative text to all images (informative and functional images)
- Ensured sufficient colour contrast between text and background
- Structured content with proper heading hierarchy (h1-h6)
- Made all functionality available from a keyboard
- Added skip-to-content navigation links
- Ensured form inputs have associated labels
- Provided descriptive link text (no "click here" or "read more")

### 4. Known Limitations

Despite our best efforts, some content may not yet be fully accessible. We are working to address these known issues:

| Issue | Status | Target Date |
|-------|--------|-------------|
| [e.g., Older PDF documents] | [In progress / Planned] | [Q4 2026] |
| [e.g., Third-party embedded content] | [Requires vendor action] | [Q2 2027] |
| [e.g., Video content without captions] | [In progress] | [Q4 2026] |

### 5. What to Do If You Encounter a Barrier

If you find any content or feature on this website that is not accessible to you, please contact us:

- **Email:** [accessibility@yourdomain.com]
- **Phone:** [Optional]
- **Response time:** We will acknowledge your report within 5 business days and provide a timeline for resolution.

We take your feedback seriously and will make reasonable accommodations to ensure equal access to our content and services.

### 6. Assessment Method

This statement was prepared using:

- [Automated testing tools used]
- [Manual testing date]
- [Date of most recent review]

### 7. Review Cycle

This accessibility statement is reviewed and updated:

- When the website design changes significantly
- When new content types are added
- At minimum annually

**Next review date:** [Date, 12 months from now]

---

## Appendix: Quick EAA Reference for Web Agencies

### EAA Key Requirements for Websites

| Requirement | WCAG Reference | What to Check |
|-------------|----------------|---------------|
| Perceivable (users must be able to perceive content) | 1.1.1 Non-text Content | Alt text on images |
|  | 1.4.3 Contrast Minimum | 4.5:1 contrast ratio for normal text |
| Operable (users must be able to operate the interface) | 2.1.1 Keyboard | All functions available from keyboard |
|  | 2.4.1 Bypass Blocks | Skip-to-content link |
| Understandable (users must be able to understand content) | 3.2.2 On Input | Forms don't auto-submit unexpected |
|  | 3.3.2 Labels | All form fields have labels |
| Robust (content works across assistive technologies) | 4.1.1 Parsing | Valid HTML, proper ARIA usage |
|  | 4.1.2 Name, Role, Value | Interactive elements have accessible names |

### EAA Enforcement

- **Deadline:** June 28, 2025 (passed — now enforced)
- **Sanctions:** Member state-specific. EU guidance recommends proportionate penalties.
- **First enforcement actions seen:** 2026 (member states beginning active enforcement).
- **Risk for agencies:** Enterprise clients in EAA scope are now requiring their vendors to demonstrate accessibility compliance.

### Monthly Maintenance Checklist

- [ ] Run automated scan (5 min with WAVE or axe)
- [ ] Check new content for alt text and heading structure
- [ ] Test any new third-party embeds (videos, forms, interactive tools)
- [ ] Log issues for next development sprint

---

## Delivery

**Format:** Markdown (fill in blanks, convert to HTML for website)

**Price when published:** $9.99 (Gumroad)

---

*Disclaimer: This document provides a template based on publicly available EAA/WCAG requirements. It does not constitute legal advice. Accessibility requirements may vary by member state implementation of the EAA.*