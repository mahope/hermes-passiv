# Gumroad Product: EAA Compliance Audit — Full Report

**Felt** | **Værdi**
---|---
Name | EAA Compliance Audit — Full Report
Type | Digital download (PDF)
Content | `products/pro-audit-<url>.pdf` (genereret pr. forespørgsel — se nedenfor)
Price | $29 USD
Cover | `products/audit-report-cover.png` (genereret)
Summary | Professional EAA/WCAG compliance audit report for any website. Automated scan covering 11 WCAG 2.1 AA criteria — images, headings, forms, ARIA, document structure, and more. Delivered as a printable PDF with executive summary, detailed findings, and prioritized recommendations.

**Description:**

> Stop guessing whether your client's site meets EU accessibility requirements.
>
> The EAA Compliance Audit — Full Report gives you a professional, printable PDF compliance assessment of any public website. Built for web agencies, freelancers, and compliance officers who need documented proof of accessibility status.
>
> **How it works:**
>
> 1. Purchase the report
> 2. Email the URL you want scanned to mads@mahope.dk (or use the web form)
> 3. Receive your 3-5 page PDF report within minutes
>
> **What you get:**
>
> - Executive summary with score (0–100) and grade (A–D)
> - 11 automated WCAG 2.1 AA checks: alt text, form labels, headings, document title, language attribute, viewport meta, iFrames, data tables, ARIA usage, fixed font sizes, and button/link accessible names
> - Detailed findings with severity labels (ERROR, WARNING, NOTICE)
> - Prioritized remediation recommendations
> - Full methodology and scope documentation
>
> **Who needs this:**
>
> - Web agencies documenting EAA compliance for client handovers
> - Freelancers doing pre-launch accessibility checks
> - Compliance officers maintaining vendor accessibility records
> - Anyone preparing for an EAA/WCAG audit
>
> **Limitations:**
>
> - Automated scan covers a subset of WCAG 2.1 AA criteria — manual review with assistive technologies is recommended for full conformance
> - Dynamic JavaScript-rendered content is analyzed in its initial HTML state
> - Color contrast ratios require pixel-level analysis (future feature)
>
> One purchase, one report. Need multiple URLs? Contact us for volume pricing.

## Technical setup (når Mads har Gumroad-konto)

1. Opret produkt på Gumroad med metadata ovenfor
2. Upload en sample PDF (fx `products/pro-audit-clean.pdf`) som produktfil
3. Noter i produktbeskrivelsen at kunden sender URL efter køb
4. Tilføj købsknap på landingssiden
5. Opdater `site/scan.html` med link til Pro-versionen efter den gratis scan

## Automatisk rapportgenerering (når Gumroad er aktiv)

En webhook kan senere bygges (Cloudflare Worker + Gumroad API) der:
1. Modtager webhook ved køb
2. Genererer PDF med `scan_pro.py`
3. Sender PDF til kunden via email