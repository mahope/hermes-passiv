# NIS2 Contract Clause Pack — Small Web Agencies

**Version 1.0 — August 2026**
**Part of ComplianceDocs by Mahope / Hermes Passiv**

---

## About This Document

A pack of 8 ready-to-use contract clauses covering NIS2 cybersecurity requirements. Each clause includes the legal text, a plain-English explanation, and guidance on where to place it in your contract.

**Who this is for:** Web agencies, managed service providers, freelancers, and WordPress shops serving EU enterprise clients.

**What you get:**
- 8 standalone clauses ready to copy into your contracts
- Explanations so you know what each clause actually does
- Guidance on which clauses to prioritise by client type

---

## Quick Reference — Which Clauses to Use

| Client Type | Must Have | Nice to Have |
|-------------|-----------|--------------|
| Enterprise (250+ emp) | 1, 2, 4, 5, 7 | 3, 6, 8 |
| SME (50–249 emp) | 1, 2, 4, 5 | 3, 7 |
| Small business (<50 emp) | 1, 2 | 4, 5 |
| Public sector | 1, 2, 3, 4, 5, 6, 7 | 8 |

---

## Clause 1: Security Obligations (Core)

**Purpose:** Sets the baseline security standard you commit to maintaining.

**Placement:** Main body of service agreement, under "Obligations of Provider"

```
1.1 The Provider shall maintain appropriate technical and organisational security measures
to protect the Client's data and systems throughout the term of this agreement.

1.2 Without limiting the generality of clause 1.1, the Provider shall implement and maintain:
    (a) Access controls based on the principle of least privilege;
    (b) Encryption of data in transit (TLS 1.2 or higher) and at rest (AES-256);
    (c) Multi-factor authentication on all administrative systems;
    (d) Regular security patching of all systems within 7 days of release;
    (e) Daily automated backups with monthly restoration testing;
    (f) An incident response plan capable of notification within 24 hours.

1.3 The Provider shall review and update these measures at least annually and shall
notify the Client of any material changes.
```

---

## Clause 2: Incident Notification (NIS2 Timeline)

**Purpose:** Aligns your incident reporting with NIS2's strict timeline.

**Placement:** Security section, immediately after Clause 1

```
2.1 The Provider shall notify the Client's designated security contact within 24 hours
of becoming aware of any security incident affecting the Client's data or systems.

2.2 The notification shall include at minimum:
    (a) A description of the incident and its status (ongoing, contained, or resolved);
    (b) The systems and data affected;
    (c) Immediate actions taken;
    (d) A timeline for the next update.

2.3 Within 72 hours of detection, the Provider shall deliver a detailed incident report
including:
    (a) Root cause analysis;
    (b) Full scope of impact;
    (c) Remediation steps taken;
    (d) Preventive measures to avoid recurrence.

2.4 "Security incident" means any event having an actual adverse effect on the security
of the Client's network or information systems, including but not limited to:
unauthorised access, data breach, ransomware, denial of service, or compromise of
administrative credentials.
```

---

## Clause 3: Subcontractor and Supply Chain

**Purpose:** Gives clients visibility into your subcontractors, as NIS2 requires supply chain assessment.

**Placement:** After incident notification clause

```
3.1 The Provider shall maintain a list of all subcontractors and third-party service
providers with access to Client data or systems and shall provide it within 10 business
days of the Client's written request.

3.2 The Provider shall ensure that each subcontractor maintains security measures
equivalent to those described in this agreement, documented in a written agreement
between the Provider and the subcontractor.

3.3 The Provider shall notify the Client at least 30 days before engaging any new
subcontractor that will have access to Client data or systems. If the Client objects
on reasonable security grounds, the Provider may either (a) propose an alternative
subcontractor, or (b) maintain security without the objected subcontractor.

3.4 The Provider remains fully liable for all acts and omissions of its subcontractors
as if they were the Provider's own.
```

---

## Clause 4: Data Processing and Location

**Purpose:** Addresses GDPR data processing requirements alongside NIS2.

**Placement:** Data processing section

```
4.1 The Provider shall process Client data only in accordance with the Client's
documented instructions, and not for any other purpose.

4.2 All Client data shall be stored and processed within the European Economic Area
(EEA) unless:
    (a) The Client gives prior written consent to processing outside the EEA; and
    (b) Adequate safeguards under Article 46 GDPR are in place.

4.3 The Provider shall maintain a Data Processing Agreement (DPA) in accordance with
Article 28 GDPR and shall provide it upon request or within 15 days of the Client's
demand.

4.4 The Provider shall not transfer Client data to a third country without the Client's
express written consent and appropriate transfer mechanisms (Standard Contractual
Clauses or adequacy decision).
```

---

## Clause 5: Audit and Verification

**Purpose:** Lets clients verify your compliance without disrupting your operations.

**Placement:** Compliance or audit section

```
5.1 Upon the Client's reasonable request (not more than once per 12-month period), the
Provider shall complete a security questionnaire provided by the Client and return it
within 15 business days.

5.2 The Provider shall provide documentary evidence of the security measures described
in this agreement, which may include:
    (a) A copy of the Provider's Information Security Policy (redacted for confidentiality);
    (b) Evidence of annual security testing or penetration testing;
    (c) Certification under ISO 27001, SOC 2 Type II, or equivalent standard (if held);
    (d) Records of backup restoration tests.

5.3 The Client may conduct a security assessment of the Provider's relevant systems,
provided that: (a) the assessment is conducted by an independent third party; (b)
reasonable notice (minimum 30 days) is given; (c) the assessment does not unreasonably
disrupt the Provider's operations; and (d) findings are shared with the Provider.
```

---

## Clause 6: Liability and Indemnity for Security Breaches

**Purpose:** Clarifies liability allocation for security incidents.

**Placement:** Liability section

```
6.1 Each party shall notify the other party promptly upon becoming aware of any
circumstance that could give rise to a claim under this clause.

6.2 The Provider shall indemnify the Client against direct damages resulting from a
security incident caused by the Provider's failure to maintain the security measures
required under this agreement.

6.3 The Client shall indemnify the Provider against direct damages resulting from a
security incident caused by the Client's systems, data, or failure to follow the
Provider's reasonable security instructions.

6.4 Neither party shall be liable for indirect, consequential, or incidental damages
arising from a security incident, except where such limitation is prohibited by
applicable law.

6.5 This clause survives termination of the agreement for a period of 12 months.
```

---

## Clause 7: Compliance with Laws (NIS2, GDPR, EAA)

**Purpose:** Broad compliance representation covering multiple EU regulations.

**Placement:** Representations and warranties section

```
7.1 The Provider represents and warrants that it shall comply with all applicable laws
governing the services provided under this agreement, including but not limited to:
    (a) The EU Network and Information Security Directive (NIS2);
    (b) The General Data Protection Regulation (GDPR);
    (c) The European Accessibility Act (EAA), where applicable to services provided.

7.2 The Client represents and warrants that it shall provide accurate and complete
information necessary for the Provider to fulfil its obligations under this clause.

7.3 Both parties shall cooperate in good faith to address any changes in applicable
laws during the term of this agreement.
```

---

## Clause 8: Termination for Security Non-Compliance

**Purpose:** Gives both parties an exit if security standards are not maintained.

**Placement:** Termination section

```
8.1 If either party fails to maintain the security measures required under this
agreement, and such failure materially affects the security of the other party's
data or systems, the non-breaching party may give written notice specifying the
non-compliance.

8.2 The breaching party shall remedy the non-compliance within 30 days of the notice.

8.3 If the non-compliance is not remedied within the cure period, the non-breaching
party may terminate the agreement immediately upon written notice.

8.4 Upon termination under this clause, the Provider shall return or destroy all
Client data (at the Client's direction) within 15 days.
```

---

## Implementation Checklist

- [ ] Copy relevant clauses into your standard contract template
- [ ] Update your Information Security Policy to match what you've committed to
- [ ] Ensure your actual security practices match the clauses (don't promise what you don't do)
- [ ] Train your team on the incident notification timeline (24h / 72h)
- [ ] Review annually — NIS2 enforcement guidance may evolve

## Delivery

**Format:** Markdown (copy clauses directly into your contracts)

**Price when published:** $12.99 (Gumroad)

---

*Disclaimer: This document provides contract clause templates based on publicly available NIS2 requirements. It does not constitute legal advice. Have your legal counsel review all clauses before including them in binding agreements.*