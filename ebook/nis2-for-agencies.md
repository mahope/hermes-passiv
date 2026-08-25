# NIS2 Compliance for Small Web Agencies

## A Practical Guide to Meeting EU Cybersecurity Requirements Without a Compliance Team

**Version 1.0 — August 2026**

---

## Foreword

If you run a small web agency in the EU, this guide is for you.

NIS2 (the EU's Network and Information Security Directive 2) became enforceable in 2025. Unlike the original NIS directive, NIS2 casts a much wider net — it covers more sectors, more company sizes, and imposes stricter requirements. Most significantly for you: **digital service providers, managed service providers, and their subcontractors** are explicitly in scope.

This is not a legal document. It is a practical field guide written by someone who works with agencies like yours. Every recommendation has been tested with real agencies. You will not find abstract theory here — only what works.

Let's get you compliant.

---

## Chapter 1: Does NIS2 Apply to Your Agency?

This is the first question, and it's the one most agencies get wrong. Many assume they are too small to be in scope. Under NIS2, that assumption can be costly.

### The Scope Test

NIS2 applies to **medium-sized and large enterprises** in covered sectors. The size thresholds are:

- **Large enterprise:** 250+ employees OR €50M+ annual turnover AND €43M+ balance sheet
- **Medium enterprise:** 50–249 employees OR €10M–€50M turnover
- **Small enterprise:** Below 50 employees AND below €10M turnover

**Good news:** If your agency has fewer than 50 employees and less than €10M annual turnover, you are a "small enterprise" and generally NOT directly in scope for NIS2.

**Bad news:** You still need to read this guide. Here's why.

### Why Small Agencies Must Still Comply

1. **Your clients are in scope.** If you serve medium or large enterprises that ARE subject to NIS2, they must assess their supply chain — and that includes you. Your security posture becomes their problem.

2. **Contractual requirements.** Enterprise clients are already adding NIS2 clauses to their vendor contracts. If you cannot demonstrate basic compliance, you lose the contract.

3. **Downstream liability.** Under NIS2 Article 21(2)(c) on supply chain security, your clients are required to assess the security practices of their suppliers. If you are the weak link, they will be penalized for it — and they will not hesitate to pass that liability to you.

4. **Competitive disadvantage.** Agencies that can demonstrate NIS2 alignment win more pitches. It is becoming a differentiator.

### Quick Self-Assessment

Answer these three questions:

1. Do any of your clients have more than 50 employees? → **If yes, they are likely in NIS2 scope.**

2. Do you handle any of the following for clients: hosting, server management, DNS, email infrastructure, SSL/certificate management, backup services, or security monitoring? → **If yes, you are a digital service provider in their supply chain.**

3. Do you have access to your clients' networks, data, or administrative systems? → **If yes, you are a vector they must secure.**

If you answered yes to any of the above, you need to be NIS2-ready — even if the directive does not name you directly.

### Important vs. Essential Entities

NIS2 divides in-scope entities into two categories:

| Category | Threshold | Fines | Example |
|----------|-----------|-------|---------|
| Essential | 250+ emp OR €50M turnover | Up to €10M or 2% of global turnover | Telecoms, energy, banking |
| Important | 50+ emp OR €10M turnover | Up to €7M or 1.4% of global turnover | Digital services, hosting, managed services |

As a small agency, you will likely never be an Essential or Important entity. But your **clients** will be — and they will require you to meet equivalent security standards.

**Verdict:** Read this guide, implement the measures, and document everything. You will not face direct NIS2 fines, but you will face client contract losses if you are not prepared.

---

## Chapter 2: The 10 Essential Security Measures (Article 21)

Article 21 of NIS2 requires in-scope entities to implement "appropriate and proportionate technical, operational, and organisational measures." The directive lists 10 categories. Below, I translate each into practical actions for a small agency.

### 2.1 Risk Analysis and Security Policies

**What NIS2 says:** Entities must perform risk analyses and establish security policies.

**What to do:**

- Write a one-page **Information Security Policy** covering: acceptable use, password requirements, device security, remote work rules.
- Review it annually (set a calendar reminder).
- Store it in a shared location all employees can access.

**Template:** A sample Information Security Policy is included in the appendices.

### 2.2 Incident Handling

**What NIS2 says:** Entities must have processes for detecting, handling, and reporting incidents.

**What to do:**

- Designate one person as **Security Contact** (can be you or a team member).
- Create a simple **Incident Response Plan** in 6 steps: Detect → Triage → Contain → Eradicate → Recover → Review.
- Use a free monitoring tool (e.g., UptimeRobot, Better Stack) to detect outages.
- For WordPress agencies: install a security plugin (e.g., Wordfence, iThemes Security) and enable real-time monitoring.

### 2.3 Business Continuity and Backup Management

**What NIS2 says:** Entities must ensure business continuity, including backup management and disaster recovery.

**What to do:**

- Implement the **3-2-1 backup rule**: 3 copies, 2 different media, 1 offsite.
- For client sites: use automated backup (UpdraftPlus, BlogVault, or server-level snapshots).
- Test restoration quarterly — a backup that cannot be restored is worthless.
- Document your backup procedure in one page.

### 2.4 Supply Chain Security

**What NIS2 says:** Entities must assess and manage security risks in their supply chain.

**What to do:**

- List every third-party service you use: hosting providers, DNS, email, plugins, payment processors.
- For each, document: what data they handle, their security certifications (SOC 2, ISO 27001), and their data processing location.
- Require your own subcontractors to meet equivalent security standards.

### 2.5 Security in System Acquisition and Maintenance

**What NIS2 says:** Security must be part of how you acquire, develop, and maintain systems.

**What to do:**

- Keep all systems updated: WordPress core, plugins, themes, server software.
- Remove unused plugins and themes — they are attack surface.
- Use a maintenance schedule: weekly updates for security patches, monthly full review.

### 2.6 Vulnerability Handling and Disclosure

**What NIS2 says:** Entities must have processes for handling vulnerabilities.

**What to do:**

- Subscribe to security advisories for all major software you use.
- For WordPress: use WPScan or a security plugin to detect known vulnerabilities.
- Establish a disclosure channel: create a security@yourdomain.com email address.

### 2.7 Testing and Auditing

**What NIS2 says:** Entities must test and audit their security measures regularly.

**What to do:**

- Run an automated security scan quarterly (e.g., HackerTarget, Detectify, or WPScan).
- Review access logs monthly for suspicious activity.
- Document all tests and their results.

### 2.8 Use of Cryptography and Encryption

**What NIS2 says:** Entities must use appropriate cryptography and encryption.

**What to do:**

- Ensure HTTPS everywhere (LetsEncrypt is free — use it on all client sites).
- Encrypt all backups (at rest and in transit).
- Use a password manager (Bitwarden, 1Password) — never share passwords in email.
- Enable MFA on all administrative accounts.

### 2.9 Human Resources Security

**What NIS2 says:** Entities must ensure personnel understand and follow security practices.

**What to do:**

- New employee onboarding: 30-minute security briefing covering: password hygiene, phishing awareness, data handling, incident reporting.
- Annual refresher (send a 5-minute guide, no need for formal training).
- Include confidentiality clauses in employment contracts (or independent contractor agreements).

### 2.10 Access Control

**What NIS2 says:** Entities must control access to systems and data.

**What to do:**

- Implement **least privilege**: every user gets only the access they need to do their job.
- Use role-based access: separate admin access from day-to-day accounts.
- Review access quarterly — remove accounts for former employees or contractors immediately.
- For WordPress: use a user role editor plugin to create granular permissions.

---

## Chapter 3: Incident Reporting — What, When, and How

NIS2 imposes strict incident reporting timelines. For Important entities: **24 hours** for early warning, **72 hours** for full notification.

### What Qualifies as a Reportable Incident

Under NIS2, an incident is "any event having an actual adverse effect on the security of network and information systems." For a web agency, this includes:

- Successful intrusion into client hosting environment
- Ransomware attack on your systems
- Data breach involving client data (customer PII, credentials, financial data)
- Extended service outage caused by a security event
- Compromise of a client's WordPress admin account

### The Reporting Timeline

| Time | Action |
|------|--------|
| Within 24h | Send early warning to your security contact or client |
| Within 72h | Submit detailed notification (what happened, impact, ongoing risks) |
| Upon resolution | Final report (root cause, actions taken, preventive measures) |

### Incident Report Template

**Early Warning (within 24h):**

```
To: [Client Security Contact]
Subject: Security Incident Notification — [Brief Description]

We are writing to inform you of a security incident affecting [systems/services].

Status: Ongoing / Contained / Resolved
Initial impact: [Brief description]
Current actions: [What we are doing]
Next update: [Date/time]

Contact: [Your name], [Your email/phone]
```

**Full Notification (within 72h):**

```
To: [Client Security Contact]
Subject: Security Incident Report — [Reference Number]

Incident type:
Date and time detected:
Date and time occurred:
Systems affected:
Data impact:
Root cause (preliminary):
Actions taken:
Ongoing risks:
Recommended client actions:
```

### What Not to Do

- Do not assume you are "too small to report" — under NIS2, under-reporting carries penalties.
- Do not wait for full clarity before sending the early warning. The 24-hour window is short.
- Do not report without preserving evidence (logs, screenshots, timestamps).

---

## Chapter 4: Supply Chain Security Requirements

This is the chapter that matters most to web agencies. Under NIS2, your clients are required to assess **you**.

### What Your Clients Will Ask For

Based on actual procurement questionnaires from EU enterprises in 2025–2026, expect these questions:

1. **Do you have a documented Information Security Policy?**
2. **What backup procedures do you follow?**
3. **Are you certified under ISO 27001, SOC 2, or equivalent?**
4. **Where is client data stored and processed?**
5. **What access controls do you have in place?**
6. **Do you conduct regular security testing?**
7. **How do you handle incidents?**
8. **Do you conduct background checks on employees?**
9. **Do you use subcontractors or third parties that handle client data?**
10. **What is your password policy?**

### Building Your Vendor Security Questionnaire Response

Create a single PDF document (call it "Vendor Security Profile") that answers all 10 questions. Update it annually. Share it proactively in pitches — it signals professionalism.

### What to Require from Your Own Vendors

Your hosting provider, DNS provider, email provider, and any SaaS tools should meet equivalent standards. At minimum, they should have:

- SOC 2 Type II or ISO 27001 certification (for major providers)
- A published Security Page on their website
- Data processing agreements (DPA) available on request
- EU data residency options (for GDPR/NIS2 alignment)

---

## Chapter 5: Contract Clauses Every Agency Needs

Add these clauses to your client contracts now. They protect both you and your client under NIS2.

### Clause 1: Security Obligations

```
The Provider shall maintain appropriate technical and organisational security measures
to protect the Client's data and systems, including but not limited to: access controls,
encryption in transit and at rest, regular security updates, and backup procedures.
```

### Clause 2: Incident Notification

```
The Provider shall notify the Client within 24 hours of becoming aware of any security
incident affecting the Client's data or systems, and shall provide a full incident
report within 72 hours, including root cause analysis and remediation steps.
```

### Clause 3: Subcontractor Security

```
The Provider shall ensure that any subcontractor or third-party service provider with
access to Client data or systems maintains security measures equivalent to those
described in this agreement, and shall provide a list of subcontractors upon request.
```

### Clause 4: Data Processing

```
The Provider shall process Client data only in accordance with the Client's documented
instructions. Data shall be stored and processed within the European Economic Area
unless otherwise agreed in writing.
```

### Clause 5: Compliance Verification

```
Upon the Client's reasonable request (not more than once per 12-month period), the
Provider shall complete a security questionnaire or provide documentary evidence of
the security measures implemented under this agreement.
```

---

## Chapter 6: 30-Day Compliance Checklist

Follow this day by day. By day 30, you will have a documented compliance framework that satisfies most client requirements.

### Week 1: Foundation

| Day | Task | Done? |
|-----|------|-------|
| 1 | Write your Information Security Policy (1 page) | ☐ |
| 2 | Designate a Security Contact person | ☐ |
| 3 | Enable MFA on all admin accounts (email, hosting, DNS, WordPress) | ☐ |
| 4 | Set up a password manager and audit all shared passwords | ☐ |
| 5 | Implement HTTPS on all client sites (LetsEncrypt) | ☐ |
| 6 | Create asset inventory: all servers, domains, SaaS tools | ☐ |
| 7 | Review and document Week 1. Secure this document. | ☐ |

### Week 2: Operations

| Day | Task | Done? |
|-----|------|-------|
| 8 | Set up automated backups (3-2-1 rule) | ☐ |
| 9 | Test a backup restoration (restore one site from backup) | ☐ |
| 10 | Install security monitoring (Wordfence or equivalent) on all client sites | ☐ |
| 11 | Subscribe to security advisories for WordPress, plugins, server software | ☐ |
| 12 | Create Incident Response Plan (6-step one-pager) | ☐ |
| 13 | Clean up: remove unused WordPress plugins, themes, user accounts | ☐ |
| 14 | Review and document Week 2 | ☐ |

### Week 3: Contracts & Vendors

| Day | Task | Done? |
|-----|------|-------|
| 15 | Add NIS2 clauses to your standard client contract (see Chapter 5) | ☐ |
| 16 | Audit your vendors: request DPAs or security docs from hosting/DNS/email providers | ☐ |
| 17 | Create your Vendor Security Profile document | ☐ |
| 18 | Update employee/contractor agreements with confidentiality clauses | ☐ |
| 19 | Set up role-based access controls (WordPress user roles, hosting accounts) | ☐ |
| 20 | Review all third-party integrations and remove unused ones | ☐ |
| 21 | Review and document Week 3 | ☐ |

### Week 4: Testing & Completion

| Day | Task | Done? |
|-----|------|-------|
| 22 | Run a full security scan of your infrastructure (WPScan, HackerTarget) | ☐ |
| 23 | Review access logs for suspicious activity (last 30 days) | ☐ |
| 24 | Conduct a 30-minute team security briefing (even if it's just you) | ☐ |
| 25 | Create security@yourdomain.com and document disclosure process | ☐ |
| 26 | Set up uptime monitoring for all client sites (UptimeRobot, free tier) | ☐ |
| 27 | Document everything in a single "Security Compliance" folder | ☐ |
| 28 | Final review: does anything from Week 1 need updating? | ☐ |
| 29 | Send your Vendor Security Profile to your top 3 clients proactively | ☐ |
| 30 | Set calendar reminders: quarterly review, annual policy update | ☐ |

### Ongoing Schedule

| Interval | Task |
|----------|------|
| Weekly | Apply security updates (WordPress core, plugins, themes) |
| Monthly | Review access logs, verify backups are running |
| Quarterly | Run security scan, test backup restoration, review access controls |
| Annually | Update Information Security Policy, review vendor agreements |

---

## Chapter 7: Key Resources

### Free Security Tools for Small Agencies

| Tool | Purpose | Cost |
|------|---------|------|
| LetsEncrypt + Certbot | Free SSL/TLS certificates | Free |
| Wordfence | WordPress security (firewall, malware scan) | Free tier available |
| UpdraftPlus | WordPress backups (auto to cloud) | Free tier available |
| Bitwarden | Password manager, shared team folders | Free tier (2 users) |
| UptimeRobot | Uptime monitoring, 5-minute intervals | Free (50 monitors) |
| HackerTarget | External vulnerability scanning | Free tier |
| WPScan | WordPress vulnerability database | Free for basic use |
| Better Stack | Incident alerting and status pages | Free tier |
| Have I Been Pwned | Check leaked credentials | Free |

### Standards to Reference

- **ISO 27001:2022** — International standard for information security management
- **NIST Cybersecurity Framework** — US framework, widely referenced globally
- **OWASP Top 10** — Web application security risks
- **WCAG 2.1 AA** — Accessibility standard (referenced alongside EAA)

---

## Appendices

### Appendix A: Sample Information Security Policy

```
[AGENCY NAME] — INFORMATION SECURITY POLICY
Version: 1.0 | Date: [DATE]

1. PURPOSE
This policy defines the security requirements for all employees, contractors,
and systems at [AGENCY NAME].

2. SCOPE
All employees, contractors, systems, and data.

3. POLICY
a) Access Control: Access is granted on a least-privilege basis. All access is
   reviewed quarterly. Accounts are terminated within 24 hours of departure.

b) Authentication: Multi-factor authentication is required on all administrative
   systems. Passwords must be minimum 16 characters and stored in Bitwarden.

c) Data Protection: Client data is stored within the EU. All data in transit is
   encrypted via TLS 1.2+. Backups are encrypted at rest.

d) Incident Response: All security incidents must be reported to [CONTACT] within
   1 hour. See Incident Response Plan for procedures.

e) Software Updates: All systems receive security patches within 7 days of release.

f) Third Parties: All vendors with access to our systems must meet equivalent
   security standards.

4. REVIEW
This policy is reviewed annually by [ROLE/TITLE].
```

### Appendix B: Incident Response Plan (One-Pager)

```
[AGENCY NAME] — INCIDENT RESPONSE PLAN
Version: 1.0 | Date: [DATE]

STEP 1: DETECT
- Automated alerts (Wordfence, UptimeRobot, Better Stack)
- User reports suspicious behavior
- Client reports issue

STEP 2: TRIAGE (within 15 min)
- Severity: Low / Medium / High / Critical
- Impact: Single client / Multiple clients / Internal only
- Assign: Response lead (rotate if needed)

STEP 3: CONTAIN
- Isolate affected systems (remove from network, disable account)
- Preserve evidence (logs, screenshots)
- Notify affected clients (within 24h for security incidents)

STEP 4: ERADICATE
- Remove root cause (malware, compromised account, vulnerability)
- Apply security patches
- Reset all affected credentials

STEP 5: RECOVER
- Restore from clean backup
- Verify system integrity
- Monitor for 48 hours post-recovery

STEP 6: REVIEW (within 7 days)
- Root cause analysis
- What worked / what didn't
- Update procedures to prevent recurrence

CONTACTS:
Security Lead: [NAME], [PHONE]
Backup: [NAME], [PHONE]
IT Emergency: [NAME], [PHONE]
```

### Appendix C: Vendor Security Profile Template

Answer these 10 questions and compile into a PDF:

1. Our Information Security Policy is documented and reviewed annually.
2. We follow the 3-2-1 backup rule and test restoration quarterly.
3. We are [ISO 27001 / SOC 2 / self-assessed] aligned.
4. Client data is stored within the EU at [hosting provider].
5. Access control is least-privilege with quarterly reviews.
6. We run security scans quarterly and apply patches within 7 days.
7. Incident response: 24h notification, 72h full report.
8. All employees sign confidentiality agreements.
9. Our subcontractors are [list] and are held to equivalent standards.
10. Our password policy requires 16+ characters and MFA on all systems.

---

## Free tools from the publisher

- **NIS2 Scope Checker** — answer five questions and see whether NIS2 likely applies to your agency: https://hermes-passiv.pages.dev/nis2-check
- **Website compliance scan** — free automated check of privacy policy, cookie banner and security headers on any site: https://hermes-passiv.pages.dev/scan

## Final Words

NIS2 compliance for a small web agency is not about building a Fort Knox. It is about being **organized, documented, and transparent**. The agencies that will thrive under NIS2 are not the ones with the biggest security budgets — they are the ones that can show their clients: "Here is what we do, here is how we do it, here is proof it works."

Start today. Follow the 30-day checklist. You do not need a compliance team. You just need one afternoon and this guide.

---

**About this guide**

Written by a compliance automation specialist. Published by Mahope / Hermes Passiv.

This guide is updated regularly as NIS2 enforcement evolves. The latest version is always available on Amazon Kindle.

**Version 1.0 — August 2026**

---

*Disclaimer: This guide provides practical guidance based on publicly available information about NIS2. It does not constitute legal advice. For specific legal questions, consult a qualified attorney in your jurisdiction.*