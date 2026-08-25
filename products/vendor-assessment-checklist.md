# Vendor Security Assessment Checklist — Small Web Agencies

**Version 1.0 — August 2026**
**Part of ComplianceDocs by Mahope / Hermes Passiv**

---

## About This Document

Under NIS2, enterprise clients must assess their supply chain security — and you, as their web agency, are part of that supply chain. This checklist helps you:

1. **Answer** the security questionnaires clients send you (as a vendor)
2. **Assess** your own subcontractors and service providers
3. **Build** your Vendor Security Profile — a proactive document you share in pitches

**Who this is for:** Web agency owners, freelancers, and managed service providers who need to demonstrate security compliance to enterprise clients.

**What you get:**
- The 10 most common client security questions (with model answers)
- A vendor assessment scorecard for your own suppliers
- A template for your Vendor Security Profile
- Integration tracking spreadsheet format

---

## Part 1: The 10 Most Common Client Security Questions

Based on actual NIS2 procurement questionnaires from EU enterprises (2025–2026). These appear in nearly every vendor assessment.

**How to use:** Prepare written answers to all 10. Store them in a document called "Vendor Security Profile" (see Part 3). Update annually.

---

### Q1: Do you have a documented Information Security Policy?

**What they're looking for:** Evidence that you have formalised your security approach.

**Model answer:**
```
Yes. Our Information Security Policy is a one-page document covering:
- Access control (least privilege, quarterly review)
- Authentication (MFA, 16+ character passwords)
- Data protection (encryption at rest and in transit, EU-only storage)
- Incident response (24h notification)
- Software updates (patches within 7 days)
- Third-party security requirements

Last reviewed: [Date]. Review cycle: Annual.
```

**Do if you don't have this:** See Appendix A of "NIS2 Compliance for Small Web Agencies" — a sample policy template ready to copy.

---

### Q2: What backup procedures do you follow?

**What they're looking for:** Proof you can recover from data loss.

**Model answer:**
```
We follow the 3-2-1 backup rule:
- 3 copies of client data (production + 2 backups)
- 2 different media types (cloud + on-site)
- 1 offsite copy

Backup schedule:
- Client sites: daily automated backups
- Databases: hourly incremental
- Retention: 30-day rolling with monthly snapshots

We test restoration quarterly and document each test. Last test: [Date].
```

---

### Q3: Are you certified under ISO 27001, SOC 2, or equivalent?

**What they're looking for:** Third-party validation of your security practices.

**Model answer (choose one):**
```
a) Yes, we are ISO 27001:2022 certified. Certificate available upon request.
b) We follow ISO 27001 principles but are not formally certified (self-assessed alignment).
   For a small agency, self-assessment aligned to ISO 27001 controls is a practical and
   accepted approach for non-critical vendors.
c) We are SOC 2 Type II audited. Report available under NDA.
```

**Honesty matters:** If you're not certified, say so. A self-assessment with documented practices is accepted for small vendors. Lying about certification will end the relationship when discovered.

---

### Q4: Where is client data stored and processed?

**What they're looking for:** GDPR compliance — data must stay in the EEA unless otherwise agreed.

**Model answer:**
```
All client data is stored and processed within the European Economic Area (EEA).
- Primary hosting: [Provider], [Location — e.g., Frankfurt, Germany]
- Backup storage: [Provider], [Location]
- Data transit: Encrypted via TLS 1.2+ at all times

We do not transfer client data outside the EEA unless expressly authorised in writing.
```

---

### Q5: What access controls do you have in place?

**What they're looking for:** Protection against insider threats and credential misuse.

**Model answer:**
```
- Least-privilege access: every employee gets only the access needed for their role
- Role-based access control across all systems (hosting, DNS, email, WordPress admin)
- MFA required on all administrative accounts
- Quarterly access review and removal of unused accounts
- Employee accounts terminated within 24 hours of departure
- All access logged and logs retained for 90 days
```

---

### Q6: Do you conduct regular security testing?

**What they're looking for:** Proactive vulnerability detection.

**Model answer:**
```
Yes. Our testing schedule:
- Automated vulnerability scanning: quarterly (HackerTarget / WPScan / equivalent)
- Manual access log review: monthly
- Backup restoration test: quarterly
- Penetration testing: annually (or when significant infrastructure changes occur)

All test results are documented and reviewed with remediation within 15 days.
```

---

### Q7: How do you handle incidents?

**What they're looking for:** A defined incident response process, not ad hoc.

**Model answer:**
```
We follow a 6-step Incident Response Plan:
1. Detect (automated monitoring, user reports, client notification)
2. Triage (severity assessment within 15 minutes)
3. Contain (isolate affected systems, preserve evidence)
4. Eradicate (remove root cause, apply patches)
5. Recover (restore from clean backup, verify integrity)
6. Review (root cause analysis within 7 days, update procedures)

Client notification timeline: 24 hours for early warning, 72 hours for full report.
Documented plan available upon request.
```

---

### Q8: Do you conduct background checks on employees?

**What they're looking for:** Personnel security.

**Model answer:**
```
Where legally permitted, we conduct:
- Reference checks for all new hires
- Confidentiality agreements signed by all employees and contractors
- Security awareness briefing within 30 days of start date

Full background checks (criminal records, credit checks) are conducted for roles involving
access to sensitive financial or health data, where permitted under local law.
```

---

### Q9: Do you use subcontractors or third parties that handle client data?

**What they're looking for:** Supply chain awareness — they're assessing your supply chain, so they need to know yours.

**Model answer:**
```
We use the following third parties that may process client data:

| Provider | Service | Security Certification | DPA Available |
|----------|---------|----------------------|---------------|
| [Host] | Server hosting | SOC 2 Type II | Yes |
| [DNS] | DNS management | ISO 27001 | Yes |
| [Email] | Email delivery | SOC 2 Type II | Yes |
| [CDN] | Content delivery | ISO 27001 | Yes |

Full list available upon request. All subcontractors are contractually required to
maintain security measures equivalent to our own.
```

---

### Q10: What is your password policy?

**What they're looking for:** Credential hygiene.

**Model answer:**
```
- Minimum password length: 16 characters
- Complexity: mixed case, numbers, special characters required
- MFA: enabled on all administrative accounts
- Password manager: Bitwarden (enterprise) — no passwords stored in email or spreadsheets
- No shared accounts: every user has unique credentials
- Account lockout: after 5 failed attempts, 15-minute lockout
- Review: all credentials reviewed quarterly
```

---

## Part 2: Vendor Assessment Scorecard (For Your Own Suppliers)

Use this table to assess each third-party service you rely on. Score each criterion 0-2:
- **0** = No evidence available / not compliant
- **1** = Self-attested / partially documented
- **2** = Certified / contractually guaranteed

| Criterion | Weight | Provider A | Provider B | Provider C |
|-----------|--------|-----------|-----------|-----------|
| Security certification (SOC 2 / ISO 27001) | 3 | | | |
| Published security page | 1 | | | |
| DPA available | 2 | | | |
| EU data residency | 2 | | | |
| Incident notification SLA | 2 | | | |
| Encryption (at rest + in transit) | 2 | | | |
| Access controls (MFA, least privilege) | 1 | | | |
| Uptime SLA | 1 | | | |
| **Total Weighted Score** | | /14 | /14 | /14 |

**Score interpretation:**
- **12–14:** Strong vendor — well-documented, certified
- **8–11:** Acceptable — documented but not certified
- **0–7:** Replace or require improvement plan

---

## Part 3: Vendor Security Profile Template

Compile answers from Part 1 into a single document. Add your letterhead, convert to PDF, and keep it ready.

**Structure:**

```
1. ABOUT [AGENCY NAME]
   - Company overview, years in business
   - Services provided
   - Client industries served

2. SECURITY AT A GLANCE
   - Certification status (ISO 27001 / SOC 2 / self-assessed)
   - Security contact: [name/email]
   - Last security review: [date]

3. INFORMATION SECURITY POLICY SUMMARY
   - 1-page summary of your policy

4. ANSWERS TO SECURITY QUESTIONNAIRE
   - Q1–Q10 as prepared above

5. SUBCONTRACTOR LIST
   - Table of third parties

6. INCIDENT HISTORY
   - Number of reportable incidents in last 12 months
   - Lessons learned (if any)

7. CONTACT
   - Security: security@yourdomain.com
   - Emergency: [phone number, if applicable]
```

---

## Delivery

**Format:** Markdown (compile into PDF for client delivery)

**Price when published:** $14.99 (Gumroad)

---

*Disclaimer: This checklist is based on publicly available NIS2 procurement practices and industry standards. Requirements vary by client. Customise answers to reflect your actual practices — never claim measures you have not implemented.*