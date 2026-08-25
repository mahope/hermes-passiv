#!/usr/bin/env python3
"""Generate four additional platform accessibility guides (Ghost, TYPO3,
Craft CMS, Umbraco) using make_guides.make_guide. Run after make_guides.py."""
import json, re, sys
sys.path.insert(0, '.')
from make_guides import make_guide

# ------------------------------------------------------------------ Ghost
ghost_why = ('Ghost is a lean publishing platform used by newsletters, blogs and '
             'independent media across Europe. Because themes are Handlebars templates, '
             'accessibility depends heavily on which theme you pick — and many popular '
             'themes ship with contrast problems, missing alt-text prompts and generic '
             'link text. The European Accessibility Act applies to paid memberships and '
             'subscriptions sold into the EU, so a Ghost publication monetising EU readers '
             'is covered.')
ghost_fixes = [
    ("Missing alt text on images",
     "Ghost prompts for alt text when you insert an image in the editor — fill it in there. "
     "Theme and logo images are set in Settings → Design, where the logo alt defaults to the "
     "publication name; verify it is not empty."),
    ("Low contrast text",
     "Contrast lives in your theme. If it is an official Ghost theme, override colours in "
     "Settings → Design → Brand, or add custom CSS via Code Injection (Settings → Code injection → Site header)."),
    ("Missing heading structure",
     "Use the editor's heading cards (H2/H3) rather than bold paragraphs. Post titles become "
     "the page H1 automatically — avoid extra H1s inside content."),
    ("Missing form labels",
     "The built-in membership/signup forms ship labelled. Custom forms added via Code Injection "
     "or embedded services must include explicit <label> elements."),
    ("Generic link text (\"read more\", \"click here\")",
     "Rewrite links in the post editor so they describe their destination. Theme-level "
     "\"Read more\" excerpts can be changed in the theme template or via translations."),
    ("Missing page language",
     "Set Publication language in Settings → Publication info (e.g. \"en\", \"de\"). This drives "
     "the html lang attribute on every page."),
    ("Keyboard traps in embeds",
     "Third-party embeds (video players, podcast widgets) are the usual culprit. Test each embed "
     "with Tab/Shift+Tab and prefer providers with accessible players."),
]
ghost_tools = [
    ("Lighthouse (built into Chrome)",
     "Run an audit on any Ghost page — covers contrast, alt text and ARIA basics. Free."),
    ("WAVE browser extension",
     "Visual overlay of errors directly on your rendered Ghost theme. Free."),
    ("Code Injection",
     "Ghost ships a site-wide CSS/JS injection point — the cleanest way to patch small "
     "theme accessibility gaps without forking the theme."),
]
ghost_maintain = [
    "Re-scan after every theme change or theme update — updates can silently reintroduce issues.",
    "Make alt text part of your editorial checklist for every image in every post.",
    "Check membership/paywall flows quarterly: buttons, error messages and emails must stay accessible too.",
]
ghost_faqs = [
    {"@type": "Question", "name": "Is my Ghost blog covered by the European Accessibility Act?",
     "acceptedAnswer": {"@type": "Answer", "text": "Purely personal blogs usually are not. Publications that sell services to EU consumers — paid memberships, sponsorships presented as a service, or commerce — generally fall under the EAA from 28 June 2025."}},
    {"@type": "Question", "name": "Does Ghost itself have accessibility problems?",
     "acceptedAnswer": {"@type": "Answer", "text": "The core Ghost frontend renders semantic HTML, but most accessibility issues come from third-party themes and embedded content. Scan your live site to see your own score."}},
    {"@type": "Question", "name": "How do I fix contrast issues without editing theme files?",
     "acceptedAnswer": {"@type": "Answer", "text": "Use Settings → Design to adjust brand colours where the theme supports it, or add an overriding CSS rule in Settings → Code injection."}},
    {"@type": "Question", "name": "Can I scan a Ghost site without installing anything?",
     "acceptedAnswer": {"@type": "Answer", "text": "Yes. Our scanner only needs your public URL — nothing is installed on your Ghost site, and no account is required."}},
    {"@type": "Question", "name": "How often should I check my publication?",
     "acceptedAnswer": {"@type": "Answer", "text": "After every theme change and at least once a quarter. New posts mostly affect alt text and link quality, which automated checks catch well."}},
]

# ------------------------------------------------------------------ TYPO3
typo3_why = ('TYPO3 powers a large share of German-speaking public-sector and enterprise '
             'websites, and BITV 2.0 / EN 301 549 obligations already bind many of its operators. '
             'TYPO3 has solid accessibility foundations (accessible backend, fluid-based '
             'templates), but real-world output depends on the integrator: content elements, '
             'custom Fluid templates and extensions frequently introduce missing labels, weak '
             'contrast and broken heading hierarchies. With the EAA extending duties to more '
             'private operators from June 2025, verification matters.')
typo3_fixes = [
    ("Missing alt text on images",
     "Every FAL image reference has an alt-text field in the media adjustment — fill it per language. "
     "For content images set it in the image properties of the content element."),
    ("Low contrast text",
     "Fix in your site package's TypoScript constants / SCSS variables, then clear cache. "
     "Do not patch contrast inline per element — fix the variable once."),
    ("Missing heading structure",
     "Header type is chosen per content element (Type dropdown). Audit pages where editors picked "
     "\"Layout\" headings instead of real H2/H3, and constrain choices in your pageTSconfig."),
    ("Missing form labels",
     "EXT:form labels are configured in the form YAML definition — every field needs a label "
     "element, not just a placeholder."),
    ("Generic link text (\"read more\", \"click here\")",
     'Replace hardcoded "more" links in Fluid templates with aria-label or visually hidden text '
     "carrying the page/item title."),
    ("Missing page language",
     "Language is derived from the site configuration (sites.yaml). Verify each language tree sets "
     "the correct hreflang/lang value."),
    ("Skip link / keyboard navigation",
     "Ensure your base Fluid layout includes a skip-to-content link and that extension output "
     "(news lists, menus) is reachable by keyboard in DOM order."),
]
typo3_tools = [
    ("T3C / agency audits",
     "Most TYPO3 agencies offer BITV tests based on EN 301 549 — useful for public-sector BIK compliance."),
    ("Lighthouse + WAVE",
     "Free first-pass checks that cover roughly a third of WCAG issues on rendered TYPO3 pages."),
    ("Editor training",
     "Most recurring TYPO3 issues come from editor choices (headings, alt text). A short style guide reduces them permanently."),
]
typo3_maintain = [
    "Re-test after major core or extension upgrades — output markup can change between LTS versions.",
    "Add accessibility rules to your review process for new content elements and extensions.",
    "Keep an up-to-date accessibility statement if you are under BITV/EN 301 549 — it is legally required.",
]
typo3_faqs = [
    {"@type": "Question", "name": "Does TYPO3 meet EN 301 549 out of the box?",
     "acceptedAnswer": {"@type": "Answer", "text": "The core aims to, but your site package, templates and extensions determine the final result. Only a test of the rendered pages tells you where you stand."}},
    {"@type": "Question", "name": "We run a public-sector TYPO3 site. What applies to us?",
     "acceptedAnswer": {"@type": "Answer", "text": "In the EU, Directive (EU) 2016/2102 requires WCAG 2.1 AA conformity, a published accessibility statement and a feedback mechanism. In Germany this is implemented via BITV 2.0."}},
    {"@type": "Question", "name": "How do I restrict editors to accessible heading levels?",
     "acceptedAnswer": {"@type": "Answer", "text": "Use page TSconfig to limit the header types available in content elements so editors can only pick H2–H4 below the automatic H1."}},
    {"@type": "Question", "name": "Can I scan without installing anything on our server?",
     "acceptedAnswer": {"@type": "Answer", "text": "Yes. The scanner fetches your public pages like any visitor — no extension, no server access, no data stored beyond the scan result."}},
    {"@type": "Question", "name": "What does the EAA change for private TYPO3 operators?",
     "acceptedAnswer": {"@type": "Answer", "text": "From 28 June 2025 e-commerce and consumer-facing digital services in the EU must be perceivable, operable, understandable and robust — in practice WCAG-aligned. Scanning is the fastest first check."}},
]

# ------------------------------------------------------------------ Craft CMS
craft_why = ('Craft CMS gives developers full control over markup, which means accessibility '
             'is entirely a function of how your templates were written. There is no theme layer '
             'to blame: Twig templates, entry fields and plugin output decide everything. Craft '
             'is popular with studios across Europe building marketing and e-commerce sites that '
             'fall under the EAA from June 2025.')
craft_fixes = [
    ("Missing alt text on assets",
     "Craft assets have an Alt Text field only if you define one — add an \"altText\" field to the "
     "asset volume and require it, then output {{ asset.altText }} in templates."),
    ("Low contrast text",
     "Fix in your CSS/Tailwind config. If you use utility classes, audit the colour tokens against "
     "WCAG ratios once instead of case by case."),
    ("Missing heading structure",
     "Headings come straight from your Twig templates. Enforce one H1 per template and use semantic "
     "H2/H3 in shared includes (cards, sections)."),
    ("Missing form labels",
     "Whatever form plugin or hand-written form you use, every input needs a visible <label>. "
     "Placeholders are not labels — most contact-form plugins let you enable labels explicitly."),
    ("Generic link text (\"read more\", \"click here\")",
     "In card/list templates, extend the link with visually hidden context ({{ entry.title }}) or "
     "an aria-label so screen-reader users hear what the link opens."),
    ("Missing page language",
     "Set lang on the <html> tag from the site locale — for multi-site setups output the current "
     "site's language dynamically."),
    ("Focus styles removed by CSS resets",
     "CSS resets commonly strip outline. Restore :focus-visible styles globally in your stylesheet."),
]
craft_tools = [
    ("Lighthouse + axe DevTools",
     "Both free; run against rendered templates to catch contrast, labels and ARIA mistakes."),
    ("Template linting in code review",
     "Because markup is fully developer-controlled, catching issues at PR time is cheaper than scanning later."),
    ("Asset field requirements",
     "Make the alt-text field required in the asset volume settings so editors cannot publish images without it."),
]
craft_maintain = [
    "Re-check templates whenever a plugin changes its front-end output.",
    "Keep alt text mandatory in the CMS so new content stays compliant.",
    "Re-run the scan after each release — template refactors are the top cause of regressions.",
]
craft_faqs = [
    {"@type": "Question", "name": "Is Craft CMS accessible by default?",
     "acceptedAnswer": {"@type": "Answer", "text": "Craft's control panel follows good practices, but your site's accessibility is defined entirely by your Twig templates and CSS. There is no theme safety net — verify your rendered pages."}},
    {"@type": "Question", "name": "How do I enforce alt text for images in Craft?",
     "acceptedAnswer": {"@type": "Answer", "text": "Create an alt-text field on the asset volume and mark it required, then render it in templates. Without this, Craft will happily serve images with empty alt attributes."}},
    {"@type": "Question", "name": "Our site sells into the EU. Does the EAA apply?",
     "acceptedAnswer": {"@type": "Answer", "text": "If you sell e-commerce services or consumer-facing digital services to EU customers, the EAA applies from 28 June 2025. WCAG 2.1 AA is the practical benchmark."}},
    {"@type": "Question", "name": "Do I need to install anything to scan my Craft site?",
     "acceptedAnswer": {"@type": "Answer", "text": "No. The scanner works on the public URL alone — nothing is installed on your server and no signup is needed."}},
    {"@type": "Question", "name": "How long does fixing typical Craft issues take?",
     "acceptedAnswer": {"@type": "Answer", "text": "Most template-level fixes (labels, headings, alt text wiring, focus styles) take hours, not weeks, because markup is centralised in your templates."}},
]

# ------------------------------------------------------------------ Umbraco
umbraco_why = ('Umbraco is widely used by European organisations, municipalities and NGOs — '
               'exactly the groups already bound by EN 301 549 or moving under EAA duties. Umbraco '
               'ships accessible starter behaviour, but Razor views, property editors and packages '
               'determine the final markup. Grid/Rich Text content edited by non-technical staff is '
               'where most issues creep in.')
umbraco_fixes = [
    ("Missing alt text on images",
     "Umbraco's Media Picker surfaces the Media item's \"Umbraco alt text\" property if your views "
     "render it — check your partials actually output the value, and require it on media types."),
    ("Low contrast text",
     "Fix in your CSS/SCSS source, not in backoffice-styled content. For brand colours set via "
     "settings nodes, validate the palette once against WCAG ratios."),
    ("Missing heading structure",
     "Rich Text Editor heading styles depend on your rte.css configuration. Restrict formats so "
     "editors choose real H2/H3, and ensure view templates emit one H1 per page."),
    ("Missing form labels",
     "Umbraco Forms: configure a label per field in the form definition and check your theme renders "
     "it visibly. Placeholders alone fail WCAG 1.3.1."),
    ("Generic link text (\"read more\", \"click here\")",
     "In list/grid views append the item name to the link via aria-label or visually hidden span."),
    ("Missing page language",
     "Set the culture on each language/domain in Settings, and confirm your master template outputs "
     "the culture on <html lang>."),
    ("Grid/Block List layouts breaking keyboard order",
     "Custom grid renderers sometimes produce DOM order that differs from visual order. Keep the "
     "rendered order aligned with the editor's logical content order."),
]
umbraco_tools = [
    ("Lighthouse + WAVE",
     "Free scans of rendered pages; catches contrast, labels and structure issues quickly."),
    ("Umbraco Forms validation settings",
     "Enable built-in required-field and error-message rendering so forms announce errors to screen readers."),
    ("Backoffice editor guidelines",
     "A short editorial checklist (alt text, heading levels, meaningful links) prevents most content-side regressions."),
]
umbraco_maintain = [
    "Re-scan after upgrading Umbraco or packages — rendering helpers change between versions.",
    "Audit new document types and block previews for heading semantics before editors start using them.",
    "Public-sector operators: keep the accessibility statement and feedback channel current (Directive 2016/2102).",
]
umbraco_faqs = [
    {"@type": "Question", "name": "Is Umbraco compliant with WCAG out of the box?",
     "acceptedAnswer": {"@type": "Answer", "text": "Umbraco's own products target accessibility, but your Razor views, packages and editor content determine the delivered pages. Test the rendered site, not the CMS."}},
    {"@type": "Question", "name": "We are a municipality. Which rules apply?",
     "acceptedAnswer": {"@type": "Answer", "text": "Public-sector bodies in the EU must meet EN 301 549 / WCAG 2.1 AA under Directive (EU) 2016/2102, publish an accessibility statement, and offer a feedback route. National implementations vary in detail."}},
    {"@type": "Question", "name": "How do I make editors produce accessible Rich Text content?",
     "acceptedAnswer": {"@type": "Answer", "text": "Restrict the RTE format list to semantic headings and lists, require alt text on media, and provide a short editorial checklist. Technical fixes plus editor guidance together give the best result."}},
    {"@type": "Question", "name": "Can the scanner check our site without server access?",
     "acceptedAnswer": {"@type": "Answer", "text": "Yes — it only needs your public URL. Nothing is installed, no credentials are needed, and results appear immediately."}},
    {"@type": "Question", "name": "Does the EAA apply to us as a private organisation using Umbraco?",
     "acceptedAnswer": {"@type": "Answer", "text": "If you provide e-commerce or consumer-facing digital services in the EU, yes, from 28 June 2025. Internal tools and purely B2B systems are treated differently — check the national transposition."}},
]

JOBS = [
    dict(slug='ghost-accessibility-check', name='Ghost',
         title_tag='Free Ghost Accessibility Check (WCAG/EAA) — Scan Your Blog',
         meta_desc='Free Ghost WCAG 2.1 AA scan — 16 automated rules, instant grade, no signup. '
                   'Check alt text, contrast, headings, forms and links on your Ghost publication.',
         hero_sub='Scan any Ghost publication against 16 WCAG 2.1 AA rules in seconds — nothing to '
                  'install, no signup. Built for EU compliance.',
         why_html=ghost_why, fixes_rows=ghost_fixes, tools_cards=ghost_tools,
         maintain_items=ghost_maintain, faqs=ghost_faqs,
         deeper_text='Automated scanning catches roughly a third of accessibility issues — but it '
                     'catches the ones that are cheapest to fix first. For the complete picture, our '
                     'e-book covers the full checklist plus a 14-day fix plan.',
         scan_cta_name='Your Ghost Site'),
    dict(slug='typo3-accessibility-check', name='TYPO3',
         title_tag='Free TYPO3 Accessibility Check (WCAG/EAA/BITV) — Scan Your Site',
         meta_desc='Free TYPO3 WCAG 2.1 AA scan — 16 automated rules, instant grade, no signup. '
                   'Check alt text, contrast, headings, forms and links on your TYPO3 site.',
         hero_sub='Scan any TYPO3 site against 16 WCAG 2.1 AA rules in seconds — nothing to install, '
                  'no signup. Built for EU compliance.',
         why_html=typo3_why, fixes_rows=typo3_fixes, tools_cards=typo3_tools,
         maintain_items=typo3_maintain, faqs=typo3_faqs,
         deeper_text='Automated scanning catches roughly a third of accessibility issues — but it '
                     'catches the ones that are cheapest to fix first. For the complete picture, our '
                     'e-book covers the full checklist plus a 14-day fix plan.',
         scan_cta_name='Your TYPO3 Site'),
    dict(slug='craftcms-accessibility-check', name='Craft CMS',
         title_tag='Free Craft CMS Accessibility Check (WCAG/EAA) — Scan Your Site',
         meta_desc='Free Craft CMS WCAG 2.1 AA scan — 16 automated rules, instant grade, no signup. '
                   'Check alt text, contrast, headings, forms and links on your Craft site.',
         hero_sub='Scan any Craft CMS site against 16 WCAG 2.1 AA rules in seconds — nothing to '
                  'install, no signup. Built for EU compliance.',
         why_html=craft_why, fixes_rows=craft_fixes, tools_cards=craft_tools,
         maintain_items=craft_maintain, faqs=craft_faqs,
         deeper_text='Automated scanning catches roughly a third of accessibility issues — but it '
                     'catches the ones that are cheapest to fix first. For the complete picture, our '
                     'e-book covers the full checklist plus a 14-day fix plan.',
         scan_cta_name='Your Craft CMS Site'),
    dict(slug='umbraco-accessibility-check', name='Umbraco',
         title_tag='Free Umbraco Accessibility Check (WCAG/EAA) — Scan Your Site',
         meta_desc='Free Umbraco WCAG 2.1 AA scan — 16 automated rules, instant grade, no signup. '
                   'Check alt text, contrast, headings, forms and links on your Umbraco site.',
         hero_sub='Scan any Umbraco site against 16 WCAG 2.1 AA rules in seconds — nothing to install, '
                  'no signup. Built for EU compliance.',
         why_html=umbraco_why, fixes_rows=umbraco_fixes, tools_cards=umbraco_tools,
         maintain_items=umbraco_maintain, faqs=umbraco_faqs,
         deeper_text='Automated scanning catches roughly a third of accessibility issues — but it '
                     'catches the ones that are cheapest to fix first. For the complete picture, our '
                     'e-book covers the full checklist plus a 14-day fix plan.',
         scan_cta_name='Your Umbraco Site'),
]

def main():
    for j in JOBS:
        out = f"site/guides/{j['slug']}.html"
        html = make_guide(**j)
        open(out, 'w', encoding='utf-8').write(html)
        print('wrote', out, len(html))

if __name__ == '__main__':
    main()
