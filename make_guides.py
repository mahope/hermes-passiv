#!/usr/bin/env python3
"""Generate platform accessibility guides from the Joomla template.
Usage: python3 make_guides.py  (writes prestashop + weebly guides)"""
import re, json

TPL = 'site/guides/joomla-accessibility-check.html'

def faq(q, a):
    return {"@type": "Question", "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a}}

def make_guide(slug, name, title_tag, meta_desc, hero_sub, why_html,
               fixes_rows, tools_cards, maintain_items, faqs, deeper_text,
               scan_cta_name=None):
    s = open(TPL, encoding='utf-8').read()
    cta = scan_cta_name or f'Your {name} Site'

    s = s.replace('<title>Joomla Accessibility Check — Free WCAG/EAA Site Scan</title>',
                  f'<title>{title_tag}</title>')
    s = s.replace('content="Free Joomla WCAG 2.1 AA scan — 16 automated rules, instant grade, '
                  'no signup. Check alt text, contrast, headings, forms, and links on your Joomla site."',
                  f'content="{meta_desc}"')
    s = s.replace('/guides/joomla-accessibility-check', f'/guides/{slug}')
    s = s.replace('Joomla Accessibility Check — Free WCAG/EAA Scan',
                  f'{name} Accessibility Check — Free WCAG/EAA Scan')
    s = s.replace('Scan your Joomla site against 16 WCAG 2.1 AA rules. Free, instant, EAA-ready.',
                  f'Scan your {name} site against 16 WCAG 2.1 AA rules. Free, instant, EAA-ready.')

    faq_json = json.dumps({"@context": "https://schema.org", "@type": "FAQPage",
                           "mainEntity": faqs}, ensure_ascii=False)
    m = re.search(r'<script type="application/ld\+json">\s*\{.*?\}\s*</script>', s, re.S)
    s = s[:m.start()] + '<script type="application/ld+json">\n' + faq_json + '\n</script>' + s[m.end():]

    s = s.replace('<h1>Joomla Accessibility Check</h1>', f'<h1>{name} Accessibility Check</h1>')
    s = s.replace('Scan any Joomla site against 16 WCAG 2.1 AA rules in seconds — no extension '
                  'install, no signup. Built for EU compliance.', hero_sub)
    s = s.replace('/scan#url=https%3A%2F%2Fwww.joomla.org', '/scan')
    s = s.replace('Run a Free Scan on joomla.org', f'Run a Free Scan on {cta}')

    # --- Why section ---
    wm = re.search(r'<h2>Why Joomla accessibility matters in the EU</h2>\s*<p>.*?</p>\s*<p>.*?</p>',
                   s, re.S)
    s = s[:wm.start()] + (f'<h2>Why {name} accessibility matters in the EU</h2>\n    '
                          + why_html) + s[wm.end():]

    # --- How-to section ---
    s = s.replace('<h2>How to check your Joomla site</h2>', f'<h2>How to check your {name} site</h2>')
    s = s.replace('<strong>Paste your Joomla URL</strong>', f'<strong>Paste your {name} URL</strong>')
    s = s.replace('an article, or a category listing', 'a product page, or a category listing')
    s = s.replace('Scan Your Joomla Site Now — Free', f'Scan Your {name} Site Now — Free')
    # --- How-to list: genericise the last step wording ---
    s = s.replace('In Joomla, most image-alt, heading, and form-label issues are fixed right in '
                  f'the article editor or Media Manager.',
                  f'Most image-alt, heading, and form-label issues are fixed right inside {name}\'s editor or theme settings.')

    # --- Fixes table ---
    rows = ''.join(
        f'\n      <tr><td style="padding:10px;border-bottom:1px solid var(--color-border);">{i}</td>'
        f'<td style="padding:10px;border-bottom:1px solid var(--color-border);">{w}</td></tr>'
        for i, w in fixes_rows)
    fm = re.search(r'<h2>Common fixes in Joomla</h2>\s*<p>When your scan flags a failing rule.*?</table>', s, re.S)
    newtab = (f'<h2>Common fixes in {name}</h2>\n    <p>When your scan flags a failing rule, '
              f'here is where to fix it:</p>\n    <table style="width:100%;border-collapse:collapse;margin-top:16px;">\n'
              f'      <tr style="background:var(--color-surface-2);">'
              f'<th style="padding:10px;text-align:left;border-bottom:1px solid var(--color-border);">Issue</th>'
              f'<th style="padding:10px;text-align:left;border-bottom:1px solid var(--color-border);">Where to fix in {name}</th></tr>'
              f'{rows}\n    </table>')
    s = s[:fm.start()] + newtab + s[fm.end():]

    # --- Tools section ---
    cards = ''.join(f'\n      <div class="card"><h3>{t}</h3><p>{d}</p></div>' for t, d in tools_cards)
    tm = re.search(r'<h2>Joomla-specific tools &amp; extensions</h2>[\s\S]*?\n  </div>\n</section>',
                   s)
    newtools = (f'<h2>{name}-specific tools &amp; resources</h2>\n    <p>{name} ships with useful '
                f'foundations — these approaches take you further:</p>\n    '
                f'<div style="display:grid;gap:16px;margin-top:24px;">{cards}\n    </div>\n  </div>\n</section>')
    s = s[:tm.start()] + newtools + s[tm.end():]

    # --- Maintain section ---
    items = ''.join(
        f'\n      <li style="padding:16px 20px;background:var(--color-surface-2);border:1px solid var(--color-border);'
        f'border-radius:var(--radius);font-size:0.95rem;">{i}</li>' for i in maintain_items)
    mm = re.search(r'<h2>Maintaining EAA compliance on Joomla</h2>\s*<p>.*?</p>\s*'
                   r'<ul style="list-style:none;display:grid;gap:12px;margin-top:24px;">.*?</ul>', s, re.S)
    newmaint = (f'<h2>Maintaining EAA compliance on {name}</h2>\n    <p>Accessibility is not a '
                f'one-time fix — sites change through content edits, theme updates and new pages. '
                f'Keep compliance sustainable:</p>\n    '
                f'<ul style="list-style:none;display:grid;gap:12px;margin-top:24px;">{items}\n    </ul>')
    s = s[:mm.start()] + newmaint + s[mm.end():]

    # --- Deeper section text ---
    dm = re.search(r'<h2>Go deeper</h2>\s*<p>.*?</p>', s, re.S)
    s = s[:dm.start()] + f'<h2>Go deeper</h2>\n    <p>{deeper_text}</p>' + s[dm.end():]
    return s


# ---------------------------------------------------------------- PrestaShop
prestashop_fixes = [
    ("Missing alt text on images",
     "Product images: Catalog → Products → edit product → Photos tab — set the Legend field per language. "
     "Theme/logo images: Design → Image Settings or the theme configuration panel."),
    ("Low contrast text",
     "Design → Theme & Logo → edit the theme's CSS (Advanced → Custom CSS / theme editor). "
     "Adjust body text colour to at least #767676 on white, and check button states."),
    ("Missing heading structure",
     "Product descriptions use the Rich Text Editor — apply Heading 2/3 styles instead of bold paragraphs. "
     "Theme templates (.tpl files) control page-level headings; keep one H1 per page."),
    ("Missing form labels",
     "Most core forms render labels by default. For custom forms built with the Contact Form module or "
     "third-party form builders, verify each field has an explicit label in its configuration."),
    ("Generic link text (\"read more\", \"click here\")",
     "Edit category and CMS page content in International → Translations or directly in the CMS pages "
     "(Design → Pages) — rewrite links so they describe their destination."),
    ("Missing page language",
     "International → Localization → configure default language per shop context. Multi-store setups "
     "should ensure each store URL serves the correct html lang attribute."),
    ("Missing alt on logo",
     "Design → Theme & Logo → configure — the logo alt text usually defaults to the shop name; verify it is not empty."),
]
presta_tools = [
    ("🛠️ Built-in foundations",
     "PrestaShop 8 renders semantic templates with the default Classic theme, including proper form markup "
     "and responsive viewport handling. Custom themes based on the starter theme inherit this structure."),
    ("✅ Audit your theme's .tpl files",
     "PrestaShop themes are template-based — overrides in themes/YOURTHEME/templates/ can silently drop "
     "labels, alt attributes or heading levels that the parent template provided. Diff your overrides against the original."),
    ("🔤 Multilingual alt text",
     "PrestaShop stores image legends per language. If you sell across EU markets, fill the Legend field for "
     "every language — a French customer's screen reader should get French alt text."),
    ("🎨 Faceted search & modules",
     "Filter modules (faceted search) often render interactive controls as plain divs. Verify keyboard operability "
     "and ARIA state attributes on any filter UI before going live."),
    ("🏗️ Checkout accessibility",
     "The checkout is where EU revenue lives — test every step with the keyboard only, confirm error messages are "
     "announced, and check contrast on price and shipping labels."),
]
presta_maintain = [
    ("<strong>🔁 Module updates.</strong> PrestaShop modules update frequently and can change rendered markup. "
     "Re-scan key pages after every significant update."),
    ("<strong>🌐 Language reviews.</strong> New languages bring new translations — including alt-text fields. "
     "Audit untranslated or empty Legends when you add a market."),
    ("<strong>📝 Content author guidelines.</strong> Train staff adding products to write descriptive names, "
     "fill the Legend field, and structure descriptions with real headings."),
    ("<strong>📊 Scan quarterly.</strong> Run the scanner on your homepage, a category page, a product page and "
     "the checkout every quarter. Keep result links as documentation for compliance reviews."),
]
presta_faqs = [
    faq("Does the EAA apply to my PrestaShop store?",
        "Yes. If your PrestaShop store sells to consumers in the EU, the European Accessibility Act requires "
        "e-commerce services to be accessible under WCAG 2.1 AA. Merchants above the micro-enterprise threshold "
        "must comply, and payment providers and marketplaces increasingly ask for documented conformance."),
    faq("What does the free scanner check on PrestaShop sites?",
        "16 automated rules covering alt text on images, form labels, link text, buttons, heading hierarchy, "
        "page language, viewport meta, iframe titles, table headers, contrast ratios, ARIA misuse, and more. "
        "Each finding includes the exact element location and a concrete fix tip relevant to PrestaShop's back office."),
    faq("Where do I fix common issues in PrestaShop?",
        "Product image alt text lives in Catalog → Products → Photos (Legend field), colours and typography in "
        "Design → Theme & Logo, CMS page content in Design → Pages, and shop-wide language settings in "
        "International → Localization. The scanner tells you exactly which element to fix and where it sits."),
    faq("Does my PrestaShop theme affect accessibility?",
        "Strongly. The theme controls nearly all rendered HTML — heading hierarchy, button markup, focus styles and "
        "contrast. Themes bought from marketplaces vary widely; always scan a full page of your live theme rather "
        "than trusting the demo."),
    faq("Is PrestaShop accessible out of the box?",
        "The default Classic theme provides reasonable semantics and responsive markup, but most shops customise "
        "themes, add modules and translate content — each step can introduce regressions like missing labels, "
        "generic link text or low-contrast promotional banners."),
]
presta_why = (
    "<p>PrestaShop powers hundreds of thousands of online stores, with a strong footprint among European "
    "small and mid-sized merchants. Under the European Accessibility Act (EAA), e-commerce is explicitly "
    "in scope: if you sell to EU customers, your storefront must meet WCAG 2.1 AA — product pages, "
    "checkout flows and customer accounts alike.</p>\n    <p>The typical PrestaShop store stacks a purchased theme, "
    "a dozen modules and multiple languages on top of the core. Each layer can quietly introduce the exact issues "
    "our scanner finds everywhere: missing image legends from bulk imports, filter widgets without keyboard support, "
    "and promotional banners that fail contrast requirements.</p>")

# ------------------------------------------------------------------ Weebly
weebly_fixes = [
    ("Missing alt text on images",
     "Edit the page → click the image element → Advanced → Alt Text field. For gallery images, open the gallery "
     "editor and set alt text per photo."),
    ("Low contrast text",
     "Theme → Change Theme / Edit Theme → adjust font and background colours. Weebly's colour pickers show hex "
     "values — aim for at least 4.5:1 between body text and background."),
    ("Missing heading structure",
     "Weebly's Title element defaults to H2. Use one H1 (page title via theme settings) then Titles for sections. "
     "Avoid using bold paragraph text instead of real headings — screen readers cannot navigate it."),
    ("Missing form labels",
     "Weebly's Form element generates labels automatically for standard fields. For placeholder-only custom fields, "
     "edit the form element and give each field a visible label."),
    ("Generic link text (\"read more\", \"click here\")",
     "Edit text elements and rewrite link anchors descriptively — blog post excerpts commonly repeat \"Read More\"; "
     "change the excerpt link text where the theme allows, or lead with descriptive sentence text."),
    ("Missing page language",
     "Settings → General → Site Language sets the site language, which feeds the html lang attribute. Verify after "
     "changing it by viewing your page source."),
    ("Buttons without discernible text",
     "Icon-only buttons in headers or footers need accessible names — check social icons render with aria-labels "
     "or add visible text next to them."),
]
weebly_tools = [
    ("🛠️ What Weebly handles for you",
     "Weebly themes ship responsive layouts, skip-navigation behaviour and labelled standard forms. The platform "
     "handles much of the technical layer automatically — which means most remaining issues come from content and "
     "theme colour choices."),
    ("✅ Theme switching check",
     "Changing themes re-renders every page. After any theme change, run a fresh scan — heading structures and "
     "colour palettes differ between themes and can silently break compliance."),
    ("🎨 Colour contrast discipline",
     "Weebly gives free rein over fonts and colours with no contrast warnings. Pick text/background pairs that pass "
     "4.5:1 and stick to them site-wide; the scanner flags violations page by page."),
    ("📐 Custom HTML elements",
     "Embed code bypasses all platform safeguards. If you paste third-party widgets (calendars, chats, maps), scan "
     "the published page — embedded iframes need titles and their inner content may be inaccessible."),
    ("🏗️ Square ecosystem note",
     "Weebly is now part of Square. Accounts are migrating to Square Online, whose editor differs — if you migrate, "
     "re-verify accessibility from scratch rather than assuming parity."),
]
weebly_maintain = [
    ("<strong>🔁 Post-edit rescans.</strong> Every page edit can shift structure. Re-scan after significant "
     "changes, especially new landing pages."),
    ("<strong>🎨 Theme consistency.</strong> Resist one-off colour tweaks per section — inconsistent pairs are "
     "where contrast failures breed."),
    ("<strong>📝 Editor habits.</strong> Use real Title elements for headings, fill alt text at upload time, and "
     "never leave \"Click here\" as link text."),
    ("<strong>📊 Scan quarterly.</strong> Homepage plus top landing pages, every quarter, with saved results as "
     "your documentation trail."),
]
weebly_faqs = [
    faq("Does the EAA apply to my Weebly site?",
        "Yes. Weebly sites selling products or services to EU consumers fall under the European Accessibility Act's "
        "e-commerce provisions. WCAG 2.1 AA applies to the whole shopping experience — browsing, cart and checkout."),
    faq("What does the free scanner check on Weebly sites?",
        "16 automated rules covering alt text, form labels, link text, buttons, heading hierarchy, page language, "
        "viewport meta, iframe titles, table headers, contrast ratios, ARIA misuse and more. Findings include the "
        "exact element and a concrete fix tip for Weebly's editor."),
    faq("Where do I fix common issues in Weebly?",
        "Image alt text is set per image element under Advanced settings, colours under the theme editor, headings "
        "via Title elements, and site language under Settings → General. The scanner points you at the exact "
        "element so fixes stay concrete."),
    faq("Can I even break accessibility in a drag-and-drop builder?",
        "Easily. Builders make layout effortless but say nothing about contrast, alt text or heading order. Most "
        "Weebly failures come from content choices — uploaded images without alt, decorative colour combinations "
        "and pasted embed codes."),
    faq("I heard Weebly is moving to Square Online — what does that mean for compliance?",
        "Square is migrating Weebly accounts to Square Online. Editors and themes differ, so accessibility work does "
        "not transfer automatically. After any migration, run a full scan of the new site before treating yourself "
        "as compliant."),
]
weebly_why = (
    "<p>Weebly (now part of Square) hosts millions of small-business sites and stores. EU accessibility law does "
    "not care how easy the builder was: a Weebly storefront selling to European consumers must meet WCAG 2.1 AA "
    "under the European Accessibility Act, same as any bespoke site.</p>\n    <p>Drag-and-drop builders create a "
    "false sense of safety — the layout looks clean, but alt text fields go unfilled, decorative colour pairings "
    "fail contrast, and pasted embed widgets ship without titles. Our scanner reads the published page exactly the "
    "way a user with a screen reader would encounter it.</p>")


def main():
    jobs = [
        dict(slug='prestashop-accessibility-check',
             name='PrestaShop',
             title_tag='Free PrestaShop Accessibility Check (WCAG/EAA) — Scan Your Store',
             meta_desc='Free PrestaShop WCAG 2.1 AA scan — 16 automated rules, instant grade, no signup. '
                       'Check alt text, contrast, headings, forms and links on your PrestaShop store.',
             hero_sub='Scan any PrestaShop store against 16 WCAG 2.1 AA rules in seconds — no module install, '
                      'no signup. Built for EU e-commerce compliance.',
             why_html=presta_why, fixes_rows=prestashop_fixes, tools_cards=presta_tools,
             maintain_items=presta_maintain, faqs=presta_faqs,
             deeper_text='Automated scanning catches roughly a third of accessibility issues — but it catches '
                         'the ones that are cheapest to fix first. For the complete picture, our e-book covers '
                         'the full checklist plus a 14-day fix plan.'),
        dict(slug='weebly-accessibility-check',
             name='Weebly',
             title_tag='Free Weebly Accessibility Check (WCAG/EAA) — Scan Your Site',
             meta_desc='Free Weebly WCAG 2.1 AA scan — 16 automated rules, instant grade, no signup. Check alt '
                       'text, contrast, headings, forms and links on your Weebly site.',
             hero_sub='Scan any Weebly site against 16 WCAG 2.1 AA rules in seconds — nothing to install, no '
                      'signup. Built for EU compliance.',
             why_html=weebly_why, fixes_rows=weebly_fixes, tools_cards=weebly_tools,
             maintain_items=weebly_maintain, faqs=weebly_faqs,
             deeper_text='Automated scanning catches roughly a third of accessibility issues — but it catches '
                         'the ones that are cheapest to fix first. For the full picture, our e-book covers the '
                         'complete checklist plus a 14-day fix plan.',
             scan_cta_name='Your Weebly Site'),
    ]
    for j in jobs:
        out = f"site/guides/{j['slug']}.html"
        html = make_guide(**j)
        open(out, 'w', encoding='utf-8').write(html)
        print('wrote', out, len(html))

if __name__ == '__main__':
    main()
