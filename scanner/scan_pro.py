#!/usr/bin/env python3
"""
scan_pro.py — Pro EAA Compliance Audit Report generator.

Takes a URL, runs the full scanner_core scan, and generates a professional
PDF compliance report suitable for client handover or internal documentation.
Output: PDF in products/ or specified path.

Gumroad product: "EAA Compliance Audit — Full Report" ($29.00, one-time)
"""

import io, json, os, sys, textwrap
from datetime import datetime

# Ensure we can import scanner_core from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scanner_core import scan_url

try:
    from fpdf import FPDF
except ImportError:
    sys.exit("fpdf2 required: pip install fpdf2")


def _clean_text(t: str) -> str:
    """Strip unsupported Unicode characters for built-in fonts."""
    replacements = {
        '\u2014': '--',   # em dash
        '\u2013': '-',    # en dash
        '\u2018': "'",    # left single quote
        '\u2019': "'",    # right single quote
        '\u201c': '"',    # left double quote
        '\u201d': '"',    # right double quote
        '\u2022': '-',    # bullet
        '\u00a0': ' ',    # non-breaking space
        '\u2026': '...',  # ellipsis
    }
    for k, v in replacements.items():
        t = t.replace(k, v)
    return t


class AuditReport(FPDF):
    """Professional compliance audit report PDF."""

    def __init__(self, scan_data: dict, url: str):
        super().__init__()
        self.scan = scan_data
        self.site_url = url
        self.scan_date = datetime.now().strftime("%B %d, %Y")
        self.set_auto_page_break(True, margin=24)
        self.set_margins(22, 22, 22)

    def color_block(self, r, g, b):
        """Set fill color for shaded regions."""
        self.set_fill_color(r, g, b)

    def section_title(self, text: str):
        """Draw a section heading with underline."""
        self.ln(4)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(26, 52, 96)
        self.cell(0, 10, _clean_text(text), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(26, 52, 96)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def sub_title(self, text: str):
        self.ln(2)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(52, 73, 94)
        self.cell(0, 8, _clean_text(text), new_x="LMARGIN", new_y="NEXT")

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(44, 44, 44)
        self.multi_cell(0, 5.5, _clean_text(text))
        self.ln(1)

    def severity_label(self, sev: str) -> tuple:
        """Return (label, (r,g,b)) for severity badge."""
        return {
            "error":   ("ERROR",   (200, 50, 50)),
            "warning": ("WARNING", (210, 150, 30)),
            "notice":  ("NOTICE",  (60, 120, 180)),
        }.get(sev, ("INFO", (100, 100, 100)))

    def _cover_page(self):
        self.add_page()
        self.ln(30)

        # Title block
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(26, 52, 96)
        self.cell(0, 14, "EAA Compliance Audit", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        self.set_font("Helvetica", "", 16)
        self.set_text_color(52, 73, 94)
        self.cell(0, 10, _clean_text("European Accessibility Act -- WCAG 2.1 AA"), align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(8)

        # URL plaque
        self.color_block(240, 245, 250)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(26, 52, 96)
        self.cell(0, 12, f"Scanned URL:  {self.site_url}",
                  align="C", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)

        # Date & report info
        self.set_font("Helvetica", "", 11)
        self.set_text_color(100, 100, 100)
        self.cell(0, 7, f"Report generated: {self.scan_date}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 7, _clean_text("Reference: EAA / WCAG 2.1 AA (subset -- 10 rule checks)"),
                  align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)

        # Score plaque — large
        score = self.scan.get("score", 0)
        grade = self.scan.get("grade", "?")
        if score >= 90:
            score_color = (30, 140, 70)
        elif score >= 75:
            score_color = (180, 150, 30)
        elif score >= 55:
            score_color = (200, 100, 30)
        else:
            score_color = (200, 50, 50)

        self.ln(10)
        self.set_font("Helvetica", "B", 48)
        self.set_text_color(*score_color)
        self.cell(0, 20, f"{score} / 100", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "B", 32)
        self.ln(2)
        self.cell(0, 16, f"Grade {grade}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)

        # Summary row
        s = self.scan.get("summary", {})
        summary_line = (
            f"Errors: {s.get('errors', 0)}  |  "
            f"Warnings: {s.get('warnings', 0)}  |  "
            f"Notices: {s.get('notices', 0)}  |  "
            f"Images checked: {s.get('images_checked', 0)}  |  "
            f"Tables: {s.get('tables', 0)}  |  "
            f"Forms: {s.get('forms', 0)}"
        )
        self.set_font("Helvetica", "", 10)
        self.set_text_color(80, 80, 80)
        self.cell(0, 7, summary_line, align="C", new_x="LMARGIN", new_y="NEXT")

        self.ln(20)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(160, 160, 160)
        self.cell(0, 6, _clean_text("Confidential -- for internal compliance documentation purposes"),
                  align="C", new_x="LMARGIN", new_y="NEXT")

    def _executive_summary(self):
        self.section_title("Executive Summary")
        score = self.scan.get("score", 0)
        grade = self.scan.get("grade", "?")
        s = self.scan.get("summary", {})

        if score >= 90:
            verdict = "The scanned page meets most EAA/WCAG accessibility requirements. Minor issues remain."
        elif score >= 75:
            verdict = "The scanned page is partially compliant. Several issues need attention to meet EAA requirements."
        elif score >= 55:
            verdict = "The scanned page has significant accessibility gaps. Prompt remediation is recommended."
        else:
            verdict = "The scanned page has critical accessibility compliance issues. Immediate action is required."

        self.body_text(
            f"This compliance audit evaluates the page at {self.site_url} against a subset of "
            f"WCAG 2.1 AA success criteria relevant to the European Accessibility Act (EAA). "
            f"The assessment covers document structure, image accessibility, form labeling, "
            f"keyboard navigation indicators, and ARIA usage.\n\n"
            f"Overall score: {score}/100 (Grade {grade}). {verdict}\n\n"
            f"Breakdown:\n"
            f"  - {s.get('errors', 0)} error(s) — must fix (affect barrier-free access)\n"
            f"  - {s.get('warnings', 0)} warning(s) — should fix (reduce usability barriers)\n"
            f"  - {s.get('notices', 0)} notice(s) — consider fixing (best practices)\n"
            f"  - {s.get('images_checked', 0)} images checked\n"
            f"  - {s.get('tables', 0)} tables, {s.get('forms', 0)} form(s) evaluated"
        )

    def _detailed_findings(self):
        self.section_title("Detailed Findings")
        findings = self.scan.get("findings", [])

        if not findings:
            self.body_text("No accessibility issues detected on this page.")
            return

        for f_data in findings:
            sev = f_data.get("severity", "info")
            label, (r, g, b) = self.severity_label(sev)
            self.ln(3)
            self.set_x(self.l_margin)

            # Severity badge + Rule ID on one line
            self.color_block(r, g, b)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(255, 255, 255)
            badge_w = self.get_string_width(f"  {label}  ") + 4
            self.cell(badge_w, 7, f" {label} ", fill=True)
            self.set_x(self.l_margin + badge_w + 3)

            rid = f_data.get("rule_id", "")
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(44, 44, 44)
            self.cell(0, 7, rid)
            self.ln(8)

            # Message
            self.set_x(self.l_margin)
            self.set_font("Helvetica", "", 9.5)
            self.set_text_color(60, 60, 60)
            self.multi_cell(0, 5, f_data.get("message", ""))

            # Examples if any
            examples = f_data.get("examples", [])
            if examples:
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(120, 120, 120)
                for ex in examples[:3]:
                    ex_str = str(ex)
                    if len(ex_str) > 60:
                        ex_str = ex_str[:57] + "..."
                    self.set_x(self.l_margin + 4)
                    self.cell(0, 4, _clean_text(f"  Example: {ex_str}"),
                              new_x="LMARGIN", new_y="NEXT")
            self.ln(2)

        # Severity legend
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        for sev in ("error", "warning", "notice"):
            label, (r, g, b) = self.severity_label(sev)
            self.color_block(r, g, b)
            self.set_font("Helvetica", "B", 7)
            self.set_text_color(255, 255, 255)
            self.cell(self.get_string_width(f" {label} ") + 3, 5, f" {label} ", fill=True)

            self.set_font("Helvetica", "", 8)
            self.set_text_color(150, 150, 150)
            descs = {"error": _clean_text("Must fix -- fails legal requirement"),
                     "warning": _clean_text("Should fix -- reduces usability barrier"),
                     "notice": _clean_text("Consider fixing -- best practice improvement")}
            self.cell(0, 5, f"  {descs[sev]}", new_x="LMARGIN", new_y="NEXT")
            self.ln(0.5)

    def _recommendations(self):
        self.section_title("Recommendations")
        errors = [f for f in self.scan.get("findings", [])
                  if f.get("severity") == "error"]
        warnings = [f for f in self.scan.get("findings", [])
                    if f.get("severity") == "warning"]
        notices = [f for f in self.scan.get("findings", [])
                   if f.get("severity") == "notice"]

        self.set_font("Helvetica", "B", 11)
        self.set_text_color(52, 73, 94)
        self.cell(0, 8, _clean_text("Priority 1 -- Must Fix (EAA compliance risk)"), new_x="LMARGIN", new_y="NEXT")

        if errors:
            self.body_text("The following issues represent clear compliance gaps "
                           "under the European Accessibility Act. Address these first:")
            for e in errors:
                self.set_font("Helvetica", "", 10)
                self.set_text_color(44, 44, 44)
                self.multi_cell(0, 5.5,
                    _clean_text(f"  - {e.get('rule_id', '')}: {e.get('message', '')}"))
        else:
            self.body_text("No critical issues found at this level.")

        self.ln(3)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(52, 73, 94)
        self.cell(0, 8, _clean_text("Priority 2 -- Should Fix (usability & best practice)"),
                  new_x="LMARGIN", new_y="NEXT")

        if warnings:
            for w in warnings:
                self.set_font("Helvetica", "", 10)
                self.set_text_color(44, 44, 44)
                self.multi_cell(0, 5.5,
                    _clean_text(f"  - {w.get('rule_id', '')}: {w.get('message', '')}"))
        else:
            self.body_text("No warnings found.")

        if notices:
            self.ln(3)
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(52, 73, 94)
            self.cell(0, 8, _clean_text("Priority 3 -- Consider Fixing (progressive enhancement)"),
                      new_x="LMARGIN", new_y="NEXT")
            for n in notices:
                            self.set_font("Helvetica", "", 10)
                            self.set_text_color(44, 44, 44)
                            self.multi_cell(0, 5.5,
                                _clean_text(f"  - {n.get('rule_id', '')}: {n.get('message', '')}"))

        self.ln(4)
        self.body_text(
            "Note: This audit covers a subset of WCAG 2.1 AA criteria relevant to EAA compliance. "
            "A full conformance audit may require manual testing with assistive technologies "
            "(screen readers, keyboard-only navigation, magnification tools)."
        )

    def _methodology(self):
        self.section_title("Methodology & Scope")
        self.body_text(
            f"Audit performed: {self.scan_date}\n"
            f"Standard checked: {self.scan.get('standard', 'EAA / WCAG 2.1 AA (subset)')}\n"
            f"Tool: EAA Compliance Scanner v1.0\n"
            f"Method: Automated static HTML analysis of the page content retrieved via HTTP(S) GET request.\n\n"
            "Criteria checked:\n"
            "  1. Images — alt text presence (WCAG 1.1.1 Non-text Content)\n"
            "  2. Form inputs — associated labels (WCAG 1.3.1 Info and Relationships)\n"
            "  3. Buttons/links — accessible name present (WCAG 4.1.2 Name, Role, Value)\n"
            "  4. Document title — non-empty <title> (WCAG 2.4.2 Page Titled)\n"
            "  5. Language — <html lang> attribute (WCAG 3.1.1 Language of Page)\n"
            "  6. Viewport — meta viewport for responsive zoom (WCAG 1.4.4 Resize text)\n"
            "  7. Heading structure — h1 presence, no level skips (WCAG 1.3.1, 2.4.6)\n"
            "  8. iFrames — title attributes (WCAG 2.4.1 Bypass Blocks)\n"
            "  9. Tables — header cells (<th>) for data tables (WCAG 1.3.1)\n"
            " 10. ARIA — aria-hidden on focusable elements (WCAG 4.1.2)\n"
            " 11. Fixed px font sizes (WCAG 1.4.4 Resize text — advisory)\n\n"
            "Limitations:\n"
            "  - Automated checks cannot detect all accessibility issues. Manual review required.\n"
            "  - Color contrast ratios require pixel-level analysis not performed here.\n"
            "  - Screen reader behavior, keyboard navigation flow, and focus order are not evaluated.\n"
            "  - Dynamic/JavaScript-rendered content is analyzed in its initial HTML state only."
        )

    def footer(self):
        self.set_font("Helvetica", "", 7)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, _clean_text("  EAA Compliance Audit -- hermes-passiv.pages.dev  |  Confidential"),
                  align="C")
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="R")

    def generate(self) -> bytes:
        """Generate the full PDF report and return as bytes."""
        self._cover_page()
        self._executive_summary()
        self._detailed_findings()
        self._recommendations()
        self._methodology()
        self.alias_nb_pages()
        raw = self.output()
        if isinstance(raw, str):
            return raw.encode("latin-1")
        return bytes(raw)


def generate_report(url: str, output_path: str = None) -> str:
    """Scan URL and generate a pro PDF report. Returns path to PDF."""
    print(f"Scanning {url} ...")
    data = scan_url(url)

    if not data.get("ok"):
        print(f"Scan failed: {data.get('error', 'unknown error')}")
        sys.exit(1)

    if output_path is None:
        base = url.replace("https://", "").replace("http://", "").replace("/", "_")[:60]
        output_path = f"products/pro-audit-{base}.pdf"

    print(f"Score: {data['score']}/100 (Grade {data['grade']})")
    print(f"Findings: {data['summary']['errors']} errors, "
          f"{data['summary']['warnings']} warnings, "
          f"{data['summary']['notices']} notices")

    report = AuditReport(data, url)
    pdf_bytes = report.generate()

    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    size_kb = len(pdf_bytes) / 1024
    print(f"\nReport saved: {output_path}")
    print(f"Size: {size_kb:.1f} KB, {report.page_no()} pages")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: scan_pro.py <url> [output.pdf]")
        sys.exit(2)
    url = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    generate_report(url, out)