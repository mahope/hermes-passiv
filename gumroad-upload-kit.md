# Gumroad Upload Kit — klar til indsættelse

Mads: opret konto på gumroad.com (gratis, ingen månedlig gebyr — Gumroad tager 10% + kortgebyr pr. salg). Kopier felterne ind. 10 minutter.

---

## Produkt: ComplianceDocs Bundle

| Felt | Værdi |
|------|-------|
| Name | ComplianceDocs Bundle |
| Type | Digital product |
| Content | `products/compliance-bundle.html` (+ evt. de 4 .md-filer som kildefiler i en zip) |
| Price | $29 USD |
| Cover | Genereres nedenfor (`products/bundle-cover.png`) |
| Summary | Four ready-to-use EU compliance templates for web agencies: GDPR Data Processing Agreement, European Accessibility Act statement, NIS2 contract clauses, and a vendor security assessment checklist. Editable, plain-HTML/markdown, no license restrictions on client use. |
| Description | (se nedenfor) |

**Description:**

> Stop rewriting compliance documents from scratch for every client.
>
> The ComplianceDocs Bundle gives your agency four professionally structured templates covering the EU regulations that actually hit web work:
>
> **1. GDPR Data Processing Agreement** — Annex A–C pre-filled for typical agency/processor relationships. Fill in names, sign, done.
>
> **2. EAA Accessibility Statement** — the statement your clients need published under the European Accessibility Act, with scope, limitations, and contact sections ready to adapt.
>
> **3. NIS2 Contract Clauses** — eight clauses allocating cybersecurity duties between you and your clients: incident notification windows, supply-chain obligations, and liability boundaries.
>
> **4. Vendor Security Assessment Checklist** — a 10-question scored assessment you can run on any sub-processor or SaaS tool before it touches client data.
>
> Plain markdown + print-ready HTML. Use them for unlimited clients. No attribution required.
>
> Buy once, use forever.

## Rækkefølge

1. Opret Gumroad-konto
2. New product → Digital product → indsæt felterne ovenfor
3. Upload zip (bygges: `zip -j products/compliance-bundle.zip products/compliance-bundle.html products/*.md` — gøres af mig)
4. Publish → send mig linket

## Efter udgivelse (jeg gør det)

- Tilføjer Gumroad-sektion med købsknap på landingssiden og deployer
- Verificér via self-check
