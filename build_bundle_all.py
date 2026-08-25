#!/usr/bin/env python3
"""
Build Complete EU Compliance Bundle:
  1. Combined PDF of all 6 e-books (via reportlab)
  2. ZIP archive containing all 6 EPUBs + the combined PDF

Usage: python3 build_bundle_all.py
"""
import os, re, zipfile, json
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    ListFlowable, ListItem, Table, TableStyle
)
from reportlab.lib import colors
from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
EBOOK_DIR = os.path.join(HERE, 'ebook')
SITE_DIR = os.path.join(HERE, 'site')
DOWNLOADS_DIR = os.path.join(SITE_DIR, 'downloads')
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

BUNDLE_VERSION = "1.0"
PDF_FILENAME = 'compliance-bundle.pdf'
ZIP_FILENAME = 'compliance-bundle-v1.0.zip'

PDF_PATH = os.path.join(DOWNLOADS_DIR, PDF_FILENAME)
ZIP_PATH = os.path.join(DOWNLOADS_DIR, ZIP_FILENAME)

# Order/priority of e-books
EBOOKS = [
    ('nis2-for-agencies', 'NIS2 Compliance for Small Web Agencies', 'A complete, plain-English guide for agencies with 1–50 employees: does NIS2 apply to you, the security measures that count, incident reporting templates, and a day-by-day 30-day compliance plan.'),
    ('gdpr-for-agencies', 'GDPR Compliance for Small Web Agencies', 'Controller vs processor roles explained in plain English, the three documents that matter (DPA, RoPA, incident plan), data subject rights handling, and a 14-day action plan with ready-to-paste DPA clause language.'),
    ('eaa-checklist', 'EAA Compliance Checklist for WordPress Sites', 'A 10-point accessibility checklist covering color contrast, alt text, headings, keyboard navigation, screen readers, forms, multimedia and zoom — plus testing tools and a 14-day fix plan.'),
    ('eaa-shopify', 'EAA Compliance for Shopify Stores', 'Shopify-specific EAA guidance: product image alt text systems, theme accessibility (contrast, focus, keyboard), checkout and forms, the required accessibility statement.'),
    ('cookie-consent-guide', 'Cookie Consent & Privacy Compliance for Small Websites', 'What the law actually requires, how to audit your site for cookies and tracking, building a compliant consent banner, consent record-keeping, privacy policy structure under Articles 13–14.'),
    ('build-your-first-chrome-extension', 'Build Your First Chrome Extension', 'A step-by-step, hands-on guide that takes you from "I have never built an extension" to live in the Chrome Web Store. Manifest V3, popups, context menus, storage, options pages and publishing.'),
]

def strip_md(text):
    """Strip Markdown formatting for plain text."""
    # Remove markdown links: [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove bold/italic markers
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    # Remove backtick code markers
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Remove image markers
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Replace entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'")
    # Replace em-dashes etc
    text = text.replace('\u2014', '--').replace('\u2013', '-')
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2022', '-').replace('\u00a0', ' ')
    text = text.replace('\u2705', '[x]').replace('\u2713', '[x]')
    return text

def parse_md_lines(lines, book_name):
    """Parse markdown lines into a list of (style, text) tuples for reportlab."""
    blocks = []
    in_table = False
    table_rows = []
    table_header = None
    in_code_block = False
    code_lines = []

    for i, raw in enumerate(lines):
        line = raw.rstrip('\n')

        # Code block fences
        if line.strip().startswith('```'):
            if in_code_block:
                # End code block
                code_text = '\n'.join(code_lines)
                blocks.append(('code', code_text))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            continue
        if in_code_block:
            code_lines.append(line)
            continue

        # Skip --- separators
        if line.strip().startswith('---') and len(line.strip()) >= 3:
            blocks.append(('spacer', 12))
            continue

        # Horizontal rule
        if re.match(r'^-{3,}$', line.strip()):
            blocks.append(('hr', True))
            continue

        # Tables
        if line.startswith('|'):
            cells = [c.strip() for c in line.strip('|').split('|')]
            in_table = True
            table_rows.append(cells)
            continue
        else:
            if in_table and table_rows:
                # Check if it's a separator row (|---|)
                if not set(''.join(table_rows[-1])).issubset({'-', ':', ' '}):
                    blocks.append(('table', table_rows))
                table_rows = []
                in_table = False

        # Headings
        h_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if h_match:
            level = len(h_match.group(1))
            text = strip_md(h_match.group(2).strip())
            if level <= 2:
                blocks.append((f'h{level}', text))
            else:
                blocks.append(('h3', text))
            continue

        # Bullet list
        if re.match(r'^[-*]\s', line):
            text = strip_md(re.sub(r'^[-*]\s', '', line))
            if text:
                blocks.append(('li', text))
            continue

        # Numbered list (1. 2. etc)
        num_match = re.match(r'^(\d+)\.\s+(.+)$', line)
        if num_match:
            text = strip_md(num_match.group(2))
            if text:
                blocks.append(('li', text))
            continue

        # Blockquote
        if line.startswith('> '):
            text = strip_md(line[2:])
            if text:
                blocks.append(('blockquote', text))
            continue

        # Bold line (like chapter titles with ** around)
        bold_match = re.match(r'^\*\*(.+?)\*\*$', line)
        if bold_match:
            blocks.append(('bold', strip_md(bold_match.group(1))))
            continue

        # Regular paragraph
        text = strip_md(line.strip())
        if text:
            blocks.append(('p', text))

    # Flush pending code block
    if in_code_block and code_lines:
        blocks.append(('code', '\n'.join(code_lines)))

    # Flush pending table
    if in_table and table_rows:
        sep = [set(''.join(r)).issubset({'-', ':', ' '}) for r in table_rows]
        if not any(sep):
            blocks.append(('table', table_rows))

    return blocks


def build_pdf():
    """Build combined PDF of all e-books."""
    print(f"Building combined PDF: {PDF_PATH}")
    print(f"  Filer: {len(EBOOKS)} e-bøger")
    print(f"  Version: {BUNDLE_VERSION}")

    doc = SimpleDocTemplate(
        PDF_PATH, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title='Complete EU Compliance Bundle',
        author='Mahope / Clean Copy Publications',
    )

    styles = getSampleStyleSheet()

    # Define custom styles
    title_style = ParagraphStyle(
        'BundleTitle', parent=styles['Title'],
        fontSize=24, leading=30, spaceAfter=8,
        textColor=colors.HexColor('#1a56db'),
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        'BundleSubtitle', parent=styles['Normal'],
        fontSize=13, leading=17, spaceAfter=20,
        textColor=colors.HexColor('#555'),
        alignment=TA_CENTER,
    )
    h1_style = ParagraphStyle(
        'H1', parent=styles['Heading1'],
        fontSize=18, leading=24, spaceBefore=20, spaceAfter=10,
        textColor=colors.HexColor('#111'),
    )
    h2_style = ParagraphStyle(
        'H2', parent=styles['Heading2'],
        fontSize=14, leading=18, spaceBefore=14, spaceAfter=6,
        textColor=colors.HexColor('#333'),
    )
    h3_style = ParagraphStyle(
        'H3', parent=styles['Heading3'],
        fontSize=12, leading=16, spaceBefore=10, spaceAfter=4,
        textColor=colors.HexColor('#444'),
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=10, leading=14, spaceAfter=6,
        alignment=TA_JUSTIFY,
    )
    li_style = ParagraphStyle(
        'ListItem', parent=styles['Normal'],
        fontSize=10, leading=14, spaceAfter=3,
        leftIndent=20, firstLineIndent=-14,
        bulletIndent=0,
    )
    blockquote_style = ParagraphStyle(
        'Blockquote', parent=styles['Normal'],
        fontSize=10, leading=14, spaceAfter=8,
        leftIndent=20, textColor=colors.HexColor('#555'),
        fontStyle='italic',
    )
    code_style = ParagraphStyle(
        'Code', parent=styles['Code'],
        fontSize=8, leading=10, spaceAfter=8,
        leftIndent=12,
        fontName='Courier',
        backColor=colors.HexColor('#f5f5f5'),
    )
    table_body = ParagraphStyle(
        'TableCell', parent=styles['Normal'],
        fontSize=9, leading=12,
    )
    chapter_style = ParagraphStyle(
        'ChapterHeader', parent=styles['Normal'],
        fontSize=16, leading=20, spaceBefore=24, spaceAfter=12,
        textColor=colors.HexColor('#1a56db'),
    )

    story = []

    # --- Title page ---
    story.append(Spacer(1, 4*cm))
    story.append(Paragraph("Complete EU Compliance", title_style))
    story.append(Paragraph("Bundle", title_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Six Practical Guides for Small Web Agencies", subtitle_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        "Version 1.0 · August 2026<br/>"
        "A Clean Copy Publication · Mahope<br/>"
        "<br/>"
        "<i>Free edition — licensed under Creative Commons BY-NC 4.0</i>",
        subtitle_style
    ))
    story.append(Spacer(1, 1.5*cm))

    # Table of contents
    story.append(Paragraph("Contents", h1_style))
    story.append(Spacer(1, 6))
    for slug, title, desc in EBOOKS:
        story.append(Paragraph(f"<b>{title}</b>", ParagraphStyle(
            'TOCEntry', parent=styles['Normal'], fontSize=11, leading=16, spaceAfter=2
        )))
        story.append(Paragraph(desc, ParagraphStyle(
            'TOCDesc', parent=styles['Normal'], fontSize=9, leading=12, spaceAfter=6,
            textColor=colors.HexColor('#666')
        )))
    story.append(PageBreak())

    # --- Process each e-book ---
    for slug, title, desc in EBOOKS:
        md_path = os.path.join(EBOOK_DIR, f'{slug}.md')
        if not os.path.exists(md_path):
            print(f"  ADVARSEL: '{md_path}' findes ikke — springer over.")
            continue

        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Book title on its own page
        story.append(Spacer(1, 3*cm))
        story.append(Paragraph(title, chapter_style))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(
            f"From: Complete EU Compliance Bundle — Version {BUNDLE_VERSION}",
            ParagraphStyle('BookSubtitle', parent=body_style, fontSize=9, textColor=colors.HexColor('#888'))
        ))
        story.append(PageBreak())

        # Parse content
        blocks = parse_md_lines(lines, slug)
        for btype, bval in blocks:
            if btype == 'h1':
                story.append(Paragraph(bval, h1_style))
            elif btype == 'h2':
                story.append(Paragraph(bval, h2_style))
            elif btype == 'h3':
                story.append(Paragraph(bval, h3_style))
            elif btype == 'p':
                story.append(Paragraph(bval, body_style))
            elif btype == 'li':
                story.append(Paragraph(f"• {bval}", li_style))
            elif btype == 'bold':
                story.append(Paragraph(f"<b>{bval}</b>", body_style))
            elif btype == 'blockquote':
                story.append(Paragraph(bval, blockquote_style))
            elif btype == 'spacer':
                story.append(Spacer(1, bval))
            elif btype == 'code':
                # Use Preformatted for short code; skip huge blocks (HTML pages, etc.)
                if len(bval) < 2000:
                    from reportlab.platypus import Preformatted
                    story.append(Spacer(1, 4))
                    story.append(Preformatted(bval, ParagraphStyle(
                        'CodeBlock', fontName='Courier', fontSize=7.5, leading=9,
                        leftIndent=12, textColor=colors.HexColor('#333'),
                        backColor=colors.HexColor('#f6f8fa'),
                    ), maxLineLength=180))
                    story.append(Spacer(1, 4))
                # else: skip — too large for inline rendering
            elif btype == 'table':
                rows = bval
                if rows:
                    t = Table([[Paragraph(c, table_body) for c in r] for r in rows])
                    t.setStyle(TableStyle([
                        ('FONTSIZE', (0,0), (-1,-1), 9),
                        ('LEADING', (0,0), (-1,-1), 12),
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ccc')),
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f4ff')),
                        ('TOPPADDING', (0,0), (-1,-1), 4),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                        ('LEFTPADDING', (0,0), (-1,-1), 6),
                        ('RIGHTPADDING', (0,0), (-1,-1), 6),
                    ]))
                    story.append(Spacer(1, 6))
                    story.append(t)
                    story.append(Spacer(1, 8))

        # Separator between books
        story.append(PageBreak())

    # --- Colophon ---
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph("About This Bundle", h1_style))
    story.append(Paragraph(
        "The Complete EU Compliance Bundle brings together six practical guides "
        "written for small web agencies that serve EU clients. Each guide was "
        "researched and written to be immediately actionable — no legal background required.",
        body_style
    ))
    story.append(Paragraph(
        f"Published August 2026 by Mahope / Clean Copy Publications.<br/>"
        f"Free edition: Creative Commons BY-NC 4.0.<br/>"
        f"Individual EPUB editions available at <a href=\"https://hermes-passiv.pages.dev/books\">hermes-passiv.pages.dev/books</a>",
        body_style
    ))

    doc.build(story)
    size = os.path.getsize(PDF_PATH)
    print(f"  PDF oprettet: {size:,} bytes")
    return PDF_PATH


def build_zip():
    """Build ZIP with all EPUBs + the combined PDF."""
    files_to_add = []

    # EPUBs
    for slug, title, desc in EBOOKS:
        epub_path = os.path.join(EBOOK_DIR, f'{slug}.epub')
        if os.path.exists(epub_path):
            files_to_add.append((epub_path, f'{slug}.epub'))
            print(f"  EPUB: {slug}.epub")

    # PDF
    if os.path.exists(PDF_PATH):
        files_to_add.append((PDF_PATH, PDF_FILENAME))
        print(f"  PDF: {PDF_FILENAME}")

    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zf:
        for full_path, arc_name in files_to_add:
            zf.write(full_path, arc_name)

    size = os.path.getsize(ZIP_PATH)
    print(f"ZIP oprettet: {size:,} bytes")
    return ZIP_PATH


def main():
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

    pdf = build_pdf()
    print()

    z = build_zip()
    print()
    print(f"Bundle klar:")
    print(f"  PDF: {pdf}")
    print(f"  ZIP: {z}")


if __name__ == '__main__':
    main()