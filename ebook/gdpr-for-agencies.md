# GDPR Compliance for Small Web Agencies

## A Practical Guide to Client Data Protection Without a Legal Department

*By Mahope*

---

Every agency that builds or maintains websites for European clients is already processing personal data — and already responsible for GDPR compliance, whether anyone has said so out loud or not. This guide turns that vague obligation into a concrete checklist you can complete in two weeks.

It is written for agencies of one to fifty people: no legal department, no DPO on payroll, no budget for outside counsel. Everything here can be done by a technically competent founder with a spreadsheet and an afternoon.

**What this guide gives you:**

- A plain-language map of which GDPR rules actually apply to an agency
- The three documents every client relationship needs (DPA, processor list, incident plan)
- A 14-day action plan that takes you from "nothing written down" to "defensible"
- Contract clauses you can paste into your next agreement
- Templates and checklists referenced throughout

This guide is practical, not exhaustive. Where the law leaves room for judgement, we tell you what most agencies do and what regulators expect. It is general information about compliance practice — not legal advice for your specific situation.

## Chapter 1 — Why This Applies to You (Yes, You)

### The myth that gets agencies in trouble

The most common misconception among small agencies is some version of: "We just build websites. Our clients own the data."

Under GDPR, that's only half true. When your client asks you to build a contact form, set up analytics, or configure email marketing, **you are processing personal data on their behalf**. That makes you a *data processor* under Article 28, with direct legal obligations of your own — obligations that exist regardless of what your contract says.

Regulators have been explicit about this. Processing without a written contract that meets Article 28 requirements is itself a violation — for both parties. If your client gets audited and cannot produce a compliant contract with you, that is their violation. If you process data without the right terms in place, it is yours.

### What "processing" means in practice

Almost everything an agency does touches personal data:

| Activity | Personal data involved |
|----------|------------------------|
| Building a contact form | Name, email, message content |
| Setting up Google Analytics | IP addresses, device identifiers |
| Configuring email/newsletter tools | Subscriber lists |
| Managing hosting | Access logs, error logs with IPs |
| Website maintenance | Database contents, user accounts |
| Handling staging/backup environments | Full copies of production data |

If you do any of these for EU-based clients (or their EU visitors), you're in scope. There is no size threshold for GDPR — unlike NIS2, a one-person shop is fully covered.

### What actually happens when something goes wrong

The dramatic fines make headlines, but they are not the realistic risk for a small agency. The realistic risks, in order:

1. **A client procurement review fails you.** Larger clients increasingly audit vendors before signing. No DPA template? You lose the deal or sign their one-sided paper.
2. **A data breach you can't document.** You must notify the affected client (and often the authorities) within 72 hours of becoming aware. If you don't know where data lives or who to call, you miss the deadline.
3. **A subject access request lands.** A website visitor demands their data. Your client calls you in a panic because the request involves systems you built.
4. **Insurance won't cover you.** Professional indemnity insurers now routinely ask for documented GDPR processes.

None of these require a regulator to be involved. All of them cost real money and reputation. Compliance is cheaper than any of them.

### The good news

For a small agency, GDPR is mostly documentation discipline, not technology. You almost certainly already do most of the right things technically — encrypted connections, access control, backups. What you lack is the paperwork that proves it. This guide fixes exactly that.

## Chapter 2 — Your Two Roles: Controller vs Processor

GDPR assigns every organisation one of two roles in each processing activity, and the roles carry different duties. Getting this straight is the foundation for everything else.

### When you're a controller

You are a *controller* when you decide why and how personal data is processed — i.e., it's your own business purpose. For an agency this typically means:

- Your own CRM and client records
- Your own marketing and newsletter
- Your own website's analytics and contact form
- Job applications you receive
- Freelancer and supplier records

As a controller you owe individuals the full set of duties: lawful basis, privacy notice, data subject rights handling, breach notification to authorities, records of processing.

### When you're a processor

You are a *processor* when you handle personal data on someone else's instructions — your clients' data. Building and maintaining their sites, hosting their databases, administering their email accounts.

As a processor you owe narrower but still direct duties:

- Process only per documented instructions (the contract)
- Keep records of what you process for whom
- Secure the data appropriately
- Notify each client of a breach *without undue delay* (your contracts should say within 24–48 hours)
- Get authorisation before using sub-processors (e.g., your hosting provider)
- Delete or return data when the engagement ends

### Why the distinction matters commercially

Two consequences worth internalising:

1. **Your clients owe you DPAs.** Every client for whom you touch personal data should have signed a data processing agreement with you. Most small agencies have none — meaning they've been non-compliant since day one, along with their clients.
2. **You owe your sub-processors the same.** Your hosting provider is your sub-processor when working on client sites; you need their DPA on file (all major providers publish theirs) and your clients need to be told roughly who they are.

### One role per activity

Note that you can be both at once for the same client: controller for your invoicing data about them, processor for their website users' data. Document them separately. Chapter 4's register handles this cleanly.

## Chapter 3 — The Three Documents That Matter

Small-agency compliance boils down to having three documents current and in use. Skip the forty-page compliance manual; these are what get requested, checked, and relied upon.

### Document 1: The Data Processing Agreement (DPA)

The single most important piece of paper in your stack. It's required by Article 28 whenever a controller engages a processor — which means between your clients and you, and between you and your hosts/tools.

A compliant DPA covers:

1. Subject matter, duration, nature and purpose of processing
2. Types of data and categories of data subjects
3. Your obligation to process only on documented instructions
4. Confidentiality commitments for staff
5. Security measures (reference an annex)
6. Rules on sub-processors (with a list + notice period for changes)
7. Assistance with data subject rights requests
8. Breach notification commitment (we recommend 24 hours)
9. Deletion or return of data at termination
10. Audit/cooperation rights

**How to get there fast:** Use the standard EU Commission SCCs annexed as a DPA module, or start from your national DPA guidance body's template. Don't draft from scratch. Send your template to new clients as part of the standard contract pack — negotiating DPAs one by one is where small agencies lose weeks. Appendix B includes clause language you can adapt.

### Document 2: The Record of Processing Activities (RoPA)

Article 30 requires controllers to keep a written record of all processing activities. Processors must keep one too. For a small agency, this is a spreadsheet with one row per activity, not software.

Columns we recommend:

| Column | Example entry |
|--------|---------------|
| Activity | Hosting & maintenance of Client X website |
| Role | Processor |
| Controller | Client X ApS |
| Categories of data | Contact-form submissions: name, email, message |
| Data subjects | Website visitors |
| Where stored | [Host] EU region, backups in same region |
| Retention | Per client instructions; deleted 30 days after termination |
| Transfers | None outside EEA |
| Security measures | TLS, 2FA admin access, encrypted backups |

One afternoon fills it in for a typical agency. Update it whenever you take on a new client or tool — make it part of project kickoff.

### Document 3: The Incident Response Plan

When a breach happens you have hours, not days. Write the plan now, while calm. Minimum content:

1. **Definition of a breach:** any accidental or unlawful destruction, loss, alteration, unauthorised disclosure of, or access to personal data — including ransomware, misdirected emails, exposed backups, and compromised admin accounts.
2. **Who does what:** one person leads, one contacts affected clients, one preserves evidence. In a tiny agency, one name per task is fine.
3. **First-hour actions:** contain (revoke credentials, isolate), assess scope (which data, whose, how many), preserve logs.
4. **Notification clock:** clients within 24h of confirming a breach involving their data. Controllers then have 72h to notify supervisory authorities; help them meet it.
5. **Template messages:** pre-draft the client notification email and the facts you'll need (what happened, when detected, data involved, mitigation, next update time).
6. **Post-incident review:** what failed, what changes.

Test it once a year with a tabletop exercise — an hour, one fake ransomware scenario. Write down what went wrong in your response and fix the plan.

## Chapter 4 — Your Privacy Infrastructure

Beyond the big three documents, four pieces of infrastructure keep you out of trouble day-to-day.

### Privacy notices

Controllers need a privacy notice wherever personal data is collected. Two you likely owe today:

1. **Your own site's privacy policy** — covering your contact form, analytics, newsletter. Most agencies either lack one or copied one that describes activities they don't actually have. Rewrite it against reality.
2. **Client-facing statements** — your clients owe notices on their sites; offering a review of their privacy policy as part of projects is both good service and a differentiator (and pairs naturally with the accessibility statement work from our companion guide).

### Lawful bases — keep it boring

For your own operations: *legitimate interest* for B2B records and security logging (document the balancing test briefly), *contract* for serving clients, *consent* for your newsletter.

Do not overthink consent banners for your own brochureware site beyond what your analytics actually requires. Do not rely on consent for anything essential — consent can be withdrawn and then you must stop.

### Data minimisation and retention

The cheapest way to reduce breach impact is holding less data. Practical rules:

- Collect nothing on forms you don't act on ("company size" fields nobody reads)
- Purge old prospect and applicant data annually — calendar it
- Set log retention explicitly (e.g., 30–90 days), don't let defaults accumulate forever
- Staging environments: use anonymised data, never full production copies left lying around

### Sub-processors and transfers

Keep a simple sub-processor list: hosting, backup, email delivery, analytics, support tooling. For each, note the DPA location (most major providers self-host their SCCs-backed DPA online — link it) and whether data stays in the EEA.

Transfers outside the EEA need a transfer mechanism — in practice, Standard Contractual Clauses plus a Transfer Impact Assessment note. Nearly every mainstream SaaS provider has this handled; your job is to record it, not renegotiate it.

## Chapter 5 — Security Measures That Actually Count

Article 32 requires security "appropriate to the risk." Regulators don't expect enterprise SOC2 from a five-person agency; they do expect the fundamentals done consistently.

### The baseline twelve

1. TLS everywhere, HSTS on
2. Unique admin accounts — no shared logins, ever
3. Two-factor authentication on all admin panels, hosters, code repos
4. Password manager for the team
5. Least privilege: developers don't have standing production database write access
6. Encrypted backups, tested restore at least twice a year
7. Automatic updates for CMS cores and critical plugins; a documented patching routine
8. Offboarding checklist: revoke access same-day when someone leaves
9. Encryption of laptops (FileVault/BitLocker) — default-on, verify once
10. Logging on production systems, retained long enough to investigate an incident
11. Vendor review: before adopting a new tool that touches client data, confirm its DPA and security page exist
12. Client handover: documented credential transfer, keys rotated after handover

That list costs almost nothing and satisfies the overwhelming majority of what an auditor or client questionnaire will ask. Everything above it is proportional response to specific risk.

### The staging environment trap

The single most common small-agency failure: production data cloned to staging servers with weaker access controls, forgotten for years. Fix with policy: staging uses synthetic or anonymised data; if production data is truly necessary, the staging environment inherits production-grade access controls and is destroyed after use.

## Chapter 6 — Handling Data Subject Rights

Individuals can exercise eight rights; in agency life you will realistically encounter three.

### Access requests (DSARs)

Someone asks what data you hold about them. As controller for your own data, you must respond within one month. As processor, you assist your client within contractual timescales.

Practical procedure:

1. Log the request (date, identity verification method, scope)
2. Search the places you know: CRM, email, website databases, backups (note: you generally inform the requester about backups rather than restoring them if restoration would be disproportionate)
3. Compile and respond in plain language
4. Deliver securely

### Erasure requests

Delete where no overriding obligation requires retention. Watch for: legal retention duties (invoices — typically 5 years in Denmark), ongoing contracts, and legitimate-interest overrides. Document your decision either way.

### Portability and rectification

Portability applies to data given by consent or contract, delivered machine-readably — usually a CSV export from the relevant system. Rectification is simply correcting the record everywhere it appears.

**Agency angle:** your clients will fumble these requests. Offering a defined service — "we handle DSAR fulfilment for sites we maintain, 48h SLA" — is a genuine productised upsell that deepens retention.

## Chapter 7 — The 14-Day Action Plan

Everything in this guide compressed into two working weeks. Assume 1–2 hours per day.

### Week 1 — Map and document

- **Day 1:** List every system you use that holds personal data (yours and clients'). Spreadsheet.
- **Day 2:** Classify each row: are you controller or processor?
- **Day 3:** Draft your RoPA using the Chapter 4 columns.
- **Day 4:** Find and file DPAs from your hosting, backup, and email providers. Note gaps.
- **Day 5:** Adopt or adapt a DPA template (Appendix B) for your client contracts.
- **Day 6:** Write your incident response plan skeleton (Chapter 3).
- **Day 7:** Buffer / catch-up.

### Week 2 — Close gaps and prove it

- **Day 8:** Run the baseline-twelve security checklist; note failures.
- **Day 9:** Fix authentication gaps first (unique accounts + 2FA).
- **Day 10:** Fix staging-environment issues; purge stale data copies.
- **Day 11:** Write/rewrite your own privacy policy.
- **Day 12:** Set retention rules and calendar annual purges.
- **Day 13:** Draft client-notification templates for breaches.
- **Day 14:** Review everything with fresh eyes; schedule quarterly review.

After two weeks you will have more documented compliance than the large majority of similarly sized agencies. Maintain with one hour per month.

## Chapter 8 — Selling Compliance as a Service

Once your own house is in order, the knowledge becomes revenue.

### Products agencies successfully sell

- **Compliance starter package:** RoPA setup + DPA signing + privacy policy review for new retainers
- **Annual compliance review:** fixed-price audit against the Chapter 7 checklist
- **DSAR handling retainer:** rights-request fulfilment for maintained sites
- **Breach readiness:** incident plan drafting + tabletop exercise for clients

Each is scoped, repeatable, and uses documents you already built for yourself. Clients buying NIS2 or accessibility work (see our companion guides) will frequently add GDPR scope — the sales conversation is warm, not cold.

### Positioning

Lead with risk removal, not law: *"Your vendor reviews ask for DPAs and records of processing. We set those up and keep them current."* Procurement friction is the pain buyers feel; cite it directly.

## Appendix A — Quick Reference Checklist

**Documents**

- [ ] DPA template adopted and included in contract pack
- [ ] Signed DPA with every active client
- [ ] Provider DPAs filed (hosting, backup, email, analytics)
- [ ] RoPA current, updated at each new engagement
- [ ] Incident response plan written, tested annually
- [ ] Own-site privacy policy accurate

**Security**

- [ ] Unique accounts + 2FA everywhere
- [ ] Password manager in use
- [ ] Backups encrypted, restores tested twice yearly
- [ ] Patching routine documented and running
- [ ] Staging free of raw production data
- [ ] Offboarding checklist executed for every departure

**Ongoing**

- [ ] Quarterly: RoPA + sub-processor list review
- [ ] Annually: purge stale data, tabletop exercise, policy refresh
- [ ] Per project: DPA attached, data flows added to RoPA

## Appendix B — Core DPA Clause Language

Adapt with counsel as needed; these reflect common market standards.

**Instructions.** *Processor shall process personal data solely on documented instructions from Controller, including with regard to transfers, unless required otherwise by Union or Member State law.*

**Sub-processors.** *Processor may engage sub-processors listed in Annex III. Processor shall give Controller thirty (30) days' written notice of any intended change and an opportunity to object on reasonable grounds.*

**Assistance.** *Processor shall promptly notify Controller if it receives a request from a data subject to exercise any right, and shall assist Controller in responding, taking into account the nature of the processing.*

**Breach notification.** *Processor shall notify Controller without undue delay, and in any case within twenty-four (24) hours, after becoming aware of a personal data breach affecting Controller's personal data.*

**Return and deletion.** *Upon termination, Processor shall, at Controller's choice, delete or return all personal data and delete existing copies, except where Union or Member State law requires storage.*

**Audit.** *Processor shall make available to Controller all information necessary to demonstrate compliance with Article 28 obligations and allow for and contribute to audits, including inspections.*

## Appendix C — Glossary

**Controller** — decides purposes and means of processing. **Processor** — processes on behalf of a controller. **DPA (Data Processing Agreement)** — mandatory Article 28 contract between controller and processor. **RoPA** — Record of Processing Activities (Art. 30). **DSAR** — Data Subject Access Request. **Personal data breach** — any security failure exposing personal data, including loss of availability. **SCCs** — Standard Contractual Clauses for transfers outside the EEA. **Supervisory authority** — national regulator (in Denmark: Datatilsynet). **Pseudonymisation** — replacing identifying fields so data can't be attributed without additional information held separately.

## Free tools from the publisher

- **Website compliance scan** — free automated check of privacy policy, cookies and security headers: https://hermes-passiv.pages.dev/scan
- **Cookie banner checker** — see what cookies a site sets before consent: https://hermes-passiv.pages.dev/cookie-check
