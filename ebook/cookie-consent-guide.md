# Cookie Consent & Privacy Compliance for Small Websites

## A Practical Guide to Meeting GDPR, ePrivacy, and Cookie Requirements Without a Legal Team

If your website serves visitors in the European Union, you need cookie consent — even if you don't think you use cookies. This guide explains exactly what the law requires, how to audit your site, and how to implement compliant consent without overcomplicating things.

## Chapter 1: What the Law Actually Requires

Three pieces of EU law govern cookies and privacy on websites:

### GDPR (General Data Protection Regulation)

The GDPR — Regulation (EU) 2016/679 — applies whenever you collect or process personal data from EU residents. Personal data includes IP addresses, which means virtually every website tracking visitor behaviour is affected.

**What you need**: A lawful basis for processing personal data. For most cookie-related processing, consent is the appropriate basis.

### ePrivacy Directive (Cookie Law)

The ePrivacy Directive — Directive 2002/58/EC, amended in 2009 — is the specific law that requires cookie consent. Article 5(3) states that storing or accessing information on a user's device requires their consent, unless it's strictly necessary for the service.

**What you need**: Active, informed consent before non-essential cookies are set. A "by continuing to use this site you accept cookies" banner is not compliant.

### The interplay

The GDPR sets the general data protection framework. The ePrivacy Directive sets the specific rules for electronic communications. Both must be satisfied. In practice: you need GDPR-compliant consent (freely given, specific, informed, unambiguous) for ePrivacy-covered tracking.

### National implementations

EU directives are implemented at the member state level, which means minor differences apply:

| Country | Cookie law reference | Key specificity |
|---------|---------------------|-----------------|
| Denmark | Cookie Executive Order | First cookie must be declined on landing, explicit consent before analytics |
| Germany | TTDSG | Strict "only strictly necessary without consent" approach |
| France | RGPD + CNIL guidelines | Heavily enforced; CNIL actively fines non-compliant sites |
| Netherlands | Telecommunicatiewet | Similar to Danish approach; consent before analytics |
| UK (post-Brexit) | PECR (UK) | Similar to ePrivacy, enforced by ICO |

## Chapter 2: Cookies and Tracking Technologies — An Inventory

Before you can implement compliant consent, you need to know what's running on your site.

### Categories of cookies

| Category | Examples | Requires consent? |
|----------|----------|-------------------|
| Strictly necessary | Session cookies, CSRF tokens, shopping cart | No — exemption for "strictly necessary" |
| Functional/preference | Language preference, theme choice | Yes — unless genuinely necessary for the service |
| Analytics | Google Analytics, Plausible, Fathom | Yes — IP addresses are personal data |
| Marketing/tracking | Facebook Pixel, Google Ads, TikTok | Yes — always requires consent |
| Third-party embeds | YouTube videos, Google Maps, Twitter feed | Yes — these set third-party cookies |

### Analysing your site

1. **Browser DevTools > Application > Storage > Cookies**: Lists all cookies your browser stores for the current site. Check after loading a page.

2. **Cookie audit tools**: Free tools like Cookiebot's scanner, CookieYes scanner, or the PrivacyBee extension can scan your site for cookies.

3. **Check your third-party scripts**: Google Analytics, Facebook Pixel, Hotjar, Microsoft Clarity, and most analytics tools set cookies. So do embedded YouTube videos, Google Maps, Typeform embeds, and social media widgets.

### Document your findings

Create a simple table:

```
| Cookie name | Provider | Purpose | Category | Expiry | Requires consent? |
|-------------|----------|---------|----------|--------|-------------------|
| _ga         | Google   | Analytics | Analytics | 2 years | Yes |
| _gid        | Google   | Analytics | Analytics | 24 hours | Yes |
| PHPSESSID   | Self     | Session | Necessary | Session | No |
```

This becomes your cookie policy.

## Chapter 3: Building a Compliant Cookie Banner

The cookie banner is the first thing many visitors see. It's also the most visibly regulated element.

### What a compliant banner needs

1. **Clear information about what cookies are used and why** — not just "we use cookies"

2. **Granular consent options** — separate toggles for analytics, marketing, functional. At minimum: analytics vs. marketing.

3. **Accept all / Reject all** — both must be equally easy. A "reject all" button hidden behind a "settings" link is not compliant.

4. **No pre-checked boxes** — consent must be active, not assumed.

5. **No cookie walls** — EDPB guidelines state that denying consent should not deny access to the website. Blocking all content until the user accepts is not compliant.

### What the banner looks like

```
┌─────────────────────────────────────────────┐
│ We use cookies to improve your experience.  │
│ You can choose which categories to allow.   │
│                                             │
│ □ Analytics  □ Marketing  □ Functional     │
│                                             │
│ [  Reject All  ]  [  Accept Selected  ]     │
│                  [  Accept All  ]           │
│                                             │
│ ↑ Cookie Policy  ↑ Privacy Policy           │
└─────────────────────────────────────────────┘
```

### Implementation options

#### Free options

1. **Cookie Consent by Osano** (open source, free): A simple, lightweight JavaScript library. MIT license, works with any website builder or CMS. Basic compliance.

2. **Manual implementation**: If your site uses very few cookies (e.g., only analytics), you can pause analytics scripts until the user accepts. This requires some JavaScript knowledge.

3. **Cloudflare Zaraz Auto-consent** (if using Cloudflare): Manages cookie consent for Zaraz-deployed scripts. Free tier available.

#### Paid options ($5-30/month)

1. **Cookiebot (by Cybot)**: Comprehensive scanner + banner. The most widely used. Free for small sites (< 100 pages). Paid plans start at €12/month.

2. **CookieYes**: GDPR-compliant banner + scanner. Free for one domain. Paid from $10/month.

3. **CookieFirst**: EU-hosted, GDPR-compliant. Free for one domain with limited features. Paid from €9/month.

#### Platform-specific

- **Shopify**: Several apps (Shopify's built-in cookie banner, CookieYes for Shopify, Cookiebot)
- **WordPress**: Plugins like Complianz, GDPR Cookie Consent, Cookiebot
- **Wix**: Built-in cookie consent (enable in Site Settings)
- **Squarespace**: Built-in cookie banner (enable in Settings → Cookies)

### JavaScript snippet approach

For custom sites, the pattern is:

```javascript
// Only load analytics if user consented
function loadAnalytics() {
    window.dataLayer = window.dataLayer || [];
    // ... Google Analytics loading code
}

// Run when user clicks "Accept"
document.getElementById('accept-btn').addEventListener('click', function() {
    document.cookie = 'cookie_consent=accepted; max-age=31536000';
    loadAnalytics();
    hideBanner();
});

// Check existing consent
if (document.cookie.includes('cookie_consent=accepted')) {
    loadAnalytics();
}
```

## Chapter 4: Consent at Scale — Record-Keeping

The GDPR requires you to demonstrate compliance. This means documenting what consent you received, when, and how.

### What to record

For each consent event, record:

- Unique user identifier (hashed, not raw IP)
- Timestamp of consent
- Which categories were accepted/rejected
- The exact text of the banner shown at the time of consent
- The URL where consent was given
- Proof of user action (clicked "Accept" vs. clicked "Reject")

### Storage methods

| Method | Pros | Cons |
|--------|------|------|
| Cookie-based | Simple, no backend needed | Limited to cookie lifetime, not GDPR-proof for enforcement |
| Local Storage | Simple, no backend | Cleared by user, not permanent |
| Server-side database | Permanent, fully auditable | Requires backend, more complex |
| Third-party service | Hosted, maintained, auditable | Monthly cost, dependency |

For most small sites, **cookie-based consent logging** is sufficient **if** you also keep a log of the consent version shown. The most important record is not the individual consent — it's the fact that your system only loaded tracking scripts after consent was given.

### Consent versioning

When you update your cookie policy or change your tracking tools, all existing consents become invalid. You need a mechanism to re-consent users:

1. Add a version number to your consent cookie
2. When your policy changes, increment the version
3. Show the banner again to users with an older consent version
4. Record the new consent

## Chapter 5: Privacy Policy — What Must Be In It

The GDPR requires specific information in your privacy policy. This is separate from the cookie banner but linked.

### Required information under Article 13

- Identity and contact details of the data controller (you)
- Contact details of your DPO (if applicable)
- Purposes of processing (why you collect data)
- Lawful basis for processing (consent, legitimate interest, contract, etc.)
- Recipients of personal data (Google, Facebook, Stripe, etc.)
- International transfer safeguards (if you use US-based services, this applies)
- Data retention periods
- The data subject's rights (access, rectification, erasure, restriction, portability, objection)
- Right to withdraw consent at any time
- Right to lodge a complaint with a supervisory authority
- Whether providing data is a contractual requirement (e.g., checkout data)
- Automated decision-making and profiling (if applicable)

### Sample structure

```
# Privacy Policy for [Site Name]

## 1. Who we are
[Your business name, address, email, VAT number]

## 2. What data we collect and why
- **Account data**: [description]
- **Purchase data**: [description]
- **Analytics data**: [description]
- **Marketing data**: [description]

## 3. Legal basis
[Consent, legitimate interest, contract — specify which for each category]

## 4. Data sharing
[List third parties, with links to their privacy policies]

## 5. International data transfers
[If you use US services, list the safeguards (SCCs, DPF certification)]

## 6. How long we keep data
[Retention periods per data category]

## 7. Your rights
List all eight rights under GDPR.

## 8. Cookies
[Link to your cookie policy/statement]

## 9. Changes to this policy
[Versioning and update notification]

## 10. Contact
[Email, address]
```

### Free privacy policy generators

- **GDPR.eu Privacy Policy Generator**: Free, basic template
- **SECURi Privacy Policy Generator**: Free, UK/EU compliant
- **Termly**: Tiered, free for basic
- **Iubenda**: Freemium, good for small sites

## Chapter 6: Handling Data Subject Requests

The GDPR gives individuals the right to request access to their data, request deletion, and more. You must respond within one month.

### Types of requests

| Request type | Description | Response time |
|-------------|-------------|---------------|
| Right to access (SAR) | "Give me all data you have about me" | 1 month |
| Right to erasure | "Delete all data about me" | 1 month |
| Right to rectification | "Fix this incorrect data" | 1 month |
| Right to restriction | "Stop processing my data" | Without delay |

### Handling a request

1. **Verify identity**: Ask for identifying information before releasing data. Only send data to the requestor's verified email address.

2. **Acknowledge receipt**: Within 3 business days, confirm you received the request and will respond.

3. **Locate the data**: Check your analytics, email marketing, CRM, database, and any third-party services.

4. **Compile and respond**: For an access request, provide a structured, machine-readable format (commonly CSV or JSON). For erasure, confirm deletion and ask third parties to do the same.

5. **Document**: Keep a record of the request, your response, and the timeline.

### Templates

**Request acknowledgment:**

> Subject: Confirmation of Data Subject Request
>
> Dear [Name],
>
> We confirm receipt of your request to [access/delete/rectify] your personal data on [date]. We will respond within one month. If we need additional information to verify your identity, we will contact you separately.
>
> Regards,
> [Your Name]

**Access response:**

> Subject: Response to Data Subject Access Request
>
> Dear [Name],
>
> In response to your request dated [date], please find attached the personal data we hold about you in CSV format.
>
> The data includes: [list categories].
>
> If you believe any data is incorrect, please contact us to request rectification.
>
> Regards,
> [Your Name]

## Chapter 7: Analytics Without Consent Violations

Most small websites use analytics. Most analytics tools set cookies. Here's how to use analytics compliantly.

### Cookie-less analytics options

These analytics tools work without cookies and therefore don't require consent:

| Tool | Price | Notes |
|------|-------|-------|
| Plausible | €9/month | Privacy-focused, cookie-less, EU-hosted |
| Fathom | €12/month | Cookie-less, privacy-first |
| Matomo (on-premise) | Free | Self-hosted, can be configured cookie-less |
| Pirsch | €7/month | German-made, GDPR-compliant |
| Cloudflare Web Analytics | Free | Basic analytics, no cookies |

### Configuring Google Analytics for consent

If you use Google Analytics and want it to work with consent, you need:

1. **Consent Mode v2**: Google's API that lets GA wait for consent before using cookies. Configure it to respect user choices.

2. **Disable data sharing**: In GA settings, disable "Google signals data" and data sharing with Google products.

3. **IP anonymization**: Set `anonymizeIp: true` in your GA config.

4. **Disable advertising features**: Turn off remarketing, advertising reporting features, and demographics.

Even with these measures, Google Analytics requires consent under the ePrivacy Directive because it stores a client ID in a cookie.

### The simplest compliant setup

1. Install a consent management platform (Cookiebot, CookieYes, or the free Osano script)
2. Configure it to block Google Analytics scripts until consent is given
3. Consider Plausible or Fathom as a no-consent alternative for basic analytics
4. If you must use Google Analytics: enable Consent Mode v2, anonymize IPs, and disable all advertising features

## Chapter 8: Common Compliance Traps

### Using "legitimate interest" for analytics

Some sites claim "legitimate interest" as a basis for analytics cookies instead of consent. This is contested. The ePrivacy Directive clearly requires consent for non-essential cookies. Most data protection authorities (DPAs) in the EU reject legitimate interest for analytics cookies. Using it is a bet against enforcement. The safer — and more honest — approach is consent.

### Implied consent banners

"If you continue browsing, you accept cookies" — this is not compliant. The user must take an active, affirmative action. Banners that imply consent by inaction are a common cause of CNIL (France) and Datatilsynet (Denmark) fines.

### Google Fonts and third-party embeds

Google Fonts can transmit IP addresses to Google servers. YouTube embeds set cookies. Google Maps embeds set cookies. Every third-party embed should be evaluated for data collection.

### Cookie walls

Blocking all content until the user accepts cookies (a "cookie wall") is not compliant per the EDPB's 2020 guidelines. Users must have genuine choice. However, this area is evolving — some paid content sites make a case for legitimate refusal. For most small sites: don't do it.

### No cookie policy

Having a cookie banner without a linked, detailed cookie policy is a compliance gap. The banner offers "more information" links — those should actually lead to information.

### Outdated consent

If you update your tracking setup (adding the Facebook Pixel, adding Hotjar, adding a new analytics tool), your existing consent is no longer valid. You must re-consent all users.

## Appendix A: Quick Implementation Checklist

### Cookie banner
- [ ] Banner appears before any non-essential scripts load
- [ ] Banner explains what cookies are used for
- [ ] Granular on/off toggles for each category (analytics, marketing, functional)
- [ ] Accept All and Reject All buttons are equally prominent
- [ ] No pre-checked boxes
- [ ] No cookie wall (site is accessible without accepting)
- [ ] Banner links to cookie policy and privacy policy
- [ ] Banner respects "Do Not Track" where applicable

### Cookie policy
- [ ] Lists every cookie by name, provider, purpose, category, and expiry
- [ ] Explains how to manage cookie preferences
- [ ] State of banner text displayed
- [ ] Includes date of last update

### Privacy policy
- [ ] Covers all Article 13 required information
- [ ] Identifies data controller (business name, address, contact)
- [ ] Lists all third parties with whom data is shared
- [ ] Specifies lawful basis for each processing activity
- [ ] Describes data subject rights
- [ ] Describes international transfer safeguards (if applicable)
- [ ] Includes date of last update

### Operations
- [ ] Consent records stored (cookie + timestamp + version)
- [ ] Consent versioning system in place
- [ ] Procedure for handling data subject requests documented
- [ ] Privacy policy and cookie policy reviewed at least annually
- [ ] Analytics configured to respect consent
- [ ] Third-party services evaluated for data collection

## Appendix B: Resources

### Free tools
- **Osano Cookie Consent**: opensource.cookieconsent.osano.com — free, open-source banner
- **GDPR.eu Privacy Policy Generator**: gdpr.eu — free template
- **Cookie audit**: Use browser DevTools > Application > Storage > Cookies
- **EAA/WCAG Scanner**: hermes-passiv.pages.dev/scan

### Low-cost solutions
- **Cookiebot**: €12/month, comprehensive
- **CookieYes**: $10/month, good for small sites
- **Plausible Analytics**: €9/month, cookie-less
- **Fathom Analytics**: €12/month, cookie-less

### Official sources
- **GDPR text**: eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679
- **ePrivacy Directive**: eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32002L0058
- **EDPB Guidelines 05/2020**: edpb.europa.eu — on consent under GDPR
- **Cookie consent guidance (UK ICO)**: ico.org.uk

### About the author

This guide is published by Mahope, an EU-focused publishing imprint specialising in practical compliance resources for small web agencies and e-commerce businesses.

## Free tools from the publisher

- **Cookie banner checker** — see every cookie and tracker a site loads, before and after consent: https://hermes-passiv.pages.dev/cookie-check
