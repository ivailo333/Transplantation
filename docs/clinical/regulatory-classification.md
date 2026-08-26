# Regulatory Classification Draft

Status: Draft for clinical-readiness planning. Not a legal opinion. Not approved
for clinical use.

This document records the initial regulatory-classification analysis for the
HLA Transplantation Simulation project. It depends on the Intended Use document
and must be reviewed by qualified regulatory counsel, quality leadership, and
clinical stakeholders before any clinical claims, clinical deployment, or
regulatory submission.

## Source Documents Reviewed

Internal project documents:

- [Intended Use](intended-use.md)
- [Backend API Component](../backend.md)
- [Backend Integration Guide](../backend-integration.md)
- [Data Policy](../data.md)
- [Cybersecurity Plan Draft](cybersecurity-plan.md)
- [Data Governance Plan Draft](data-governance.md)
- [SOUP And Dependency Register Draft](soup-dependency-register.md)
- [Release And Deployment Plan Draft](release-deployment-plan.md)
- [Maintenance Plan Draft](maintenance-plan.md)
- [Problem Resolution And CAPA Plan Draft](problem-resolution-capa.md)
- [Document Control Index Draft](document-control-index.md)
- [Approval Matrix Draft](approval-matrix.md)
- [Claims Control Matrix Draft](claims-control-matrix.md)
- [Change Impact Checklist Draft](change-impact-checklist.md)
- [Clinical Readiness Gate Checklist Draft](clinical-readiness-gate-checklist.md)

Official external references checked for this draft:

- Regulation (EU) 2017/745 on medical devices (MDR):
  https://eur-lex.europa.eu/eli/reg/2017/745/oj/eng
- Regulation (EU) 2017/746 on in vitro diagnostic medical devices (IVDR), via
  European Commission medical-device guidance pages:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en
- MDCG 2019-11 rev.1, Qualification and classification of software under MDR
  and IVDR, June 2025:
  https://health.ec.europa.eu/latest-updates/update-mdcg-2019-11-rev1-qualification-and-classification-software-regulation-eu-2017745-and-2025-06-17_en
- European Commission MDCG guidance index, including software, classification,
  clinical evaluation/performance evaluation, cybersecurity, PMS, and PRRC
  guidance:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en
- EUDAMED UDI/device registration information, including mandatory use of the
  first four modules from 28 May 2026:
  https://health.ec.europa.eu/medical-devices-eudamed/udidevice-registration_en

## Classification Scope

This draft covers the European Union route first, because Bulgaria is an EU
Member State and clinical market access would be governed by MDR and/or IVDR,
plus national implementation and institutional requirements.

United States FDA SaMD/CDS classification may be considered later if US use or
US market access becomes a product goal. It is not in scope for this draft.

## Current Regulatory Position

Based on the current Intended Use, the project is a non-clinical software
prototype for deterministic HLA data comparison, report generation, report
comparison, export, backend API access, and audit-bundle creation.

Current regulatory working position:

- The current software must not be marketed, labelled, advertised, deployed, or
  used as clinical decision-support software.
- The current software has no approved medical purpose claim.
- The current software should remain outside clinical medical-device use as
  long as all documentation, UI, API responses, reports, exports, and user
  communications preserve the non-clinical boundary.
- This position depends on strict claim control. Any claim that outputs are used
  for diagnosis, treatment, donor acceptance, donor rejection, allocation, or
  transplant suitability triggers reclassification work.

Current conclusion: no clinical-use classification is finalized. The product is
not ready for clinical use.

## Medical Device Software Trigger

A regulatory classification trigger occurs if the manufacturer states or implies
that the software is intended to provide information used for medical decisions,
including diagnosis, treatment, donor acceptance, donor rejection, allocation,
transplant suitability, crossmatch interpretation, immunological risk, or
clinical prioritization.

If that trigger occurs, the software must be evaluated as potential medical
device software before that use is allowed.

## MDR / IVDR Borderline Question

The project works with HLA typing data. HLA typing data originate from in vitro
laboratory processes, but the current software does not examine specimens and
does not itself perform laboratory measurement.

Regulatory route must therefore be assessed explicitly:

- MDR route may apply if the software provides information used for diagnosis or
  therapeutic decision-making, such as transplantation-related decisions.
- IVDR route may need assessment if the software is claimed to process,
  interpret, or provide information derived from in vitro examination of human
  specimens for an IVD medical purpose.
- A combined workflow may include both IVD source systems and MDR clinical
  decision-support functions.

Working assumption for planning: do not assume MDR-only or IVDR-only until the
intended purpose, data flow, claims, and manufacturer role are reviewed by a
qualified regulatory lead.

## Scenario-Based Working Classification

### Scenario A: Non-Clinical Reporting And Audit Tool

Description:

- synthetic, demo, anonymized, or validation-planning data only;
- no clinical decision-support claim;
- no donor acceptance/rejection output;
- no allocation or transplant-suitability output;
- no patient-care deployment.

Working classification:

- outside clinical medical-device use, provided claim control is maintained.

Controls required:

- persistent non-clinical labels in UI, API, reports, exports, and README;
- no clinical claims in marketing or documentation;
- no production clinical deployment;
- no identifiable clinical data without governance approval.

### Scenario B: Clinical Display And Workflow Support Only

Description:

- used in a controlled clinical workflow;
- displays HLA typing data, deterministic comparisons, reports, and audit
  artifacts;
- does not recommend donor acceptance/rejection;
- does not rank recipients for allocation;
- does not compute DSA, cPRA, eplets, PIRCHE, crossmatch, graft outcome, or
  clinical risk;
- requires independent clinician/laboratory review.

Working classification:

- potential medical device software depending on actual claims and use;
- if outputs are used to make diagnosis or therapeutic decisions, MDR Rule 11
  assessment is likely required;
- classification could be at least Class IIa under MDR Rule 11 if information is
  used for diagnosis or therapeutic decisions;
- higher classification may apply depending on the possible impact of decisions.

Controls required before this scenario is allowed:

- regulatory classification opinion;
- clinical workflow definition;
- risk management file;
- usability engineering plan;
- validation protocol;
- controlled claims and labelling;
- clinical sign-off and audit controls.

### Scenario C: Donor Suitability Or Donor Acceptance Decision Support

Description:

- software outputs influence donor acceptance, donor rejection, candidate
  selection, organ allocation, transplant suitability, immunological risk, or
  similar decisions.

Working classification:

- likely medical device software;
- MDR Rule 11 is highly relevant if the software provides information used for
  diagnosis or therapeutic decisions;
- transplant decisions may involve serious deterioration, surgical intervention,
  death, or irreversible deterioration if incorrect information is used;
- conservative planning assumption: treat as high-risk software until a formal
  regulatory classification concludes otherwise;
- potential MDR Class IIb or Class III risk must be evaluated;
- IVDR applicability must also be checked if claims are tied to interpretation
  of in vitro HLA results.

Controls required before this scenario is allowed:

- formal regulatory strategy;
- Notified Body engagement if required;
- QMS under medical-device quality processes;
- full software lifecycle file;
- clinical evaluation or performance evaluation strategy as applicable;
- risk management and benefit-risk analysis;
- usability validation;
- cybersecurity and data protection controls;
- post-market surveillance and vigilance planning.

## Preliminary Classification Table

| Topic | Current position | Future clinical trigger |
| --- | --- | --- |
| Intended medical purpose | None approved | Any claim supporting diagnosis, treatment, donor acceptance/rejection, allocation, or transplant suitability |
| Medical-device status | Not finalized; maintained as non-clinical | Potential medical device software |
| EU route | No clinical route selected | MDR and IVDR borderline assessment required |
| Rule 11 relevance | Not applicable to current non-clinical use | Likely relevant if information is used for diagnosis or therapeutic decisions |
| Working risk class | None for current non-clinical use | At least IIa if Rule 11 applies; IIb/III must be evaluated for transplant decision impact |
| Notified Body | Not applicable for current non-clinical use | Likely required if higher than Class I or if IVDR classification requires it |
| EUDAMED / UDI | Not applicable for current non-clinical use | Required if placed on EU market as a device, subject to final route and timelines |

## Claim Controls

Until classification is finalized, the project must not use claims such as:

- compatible donor;
- incompatible donor;
- donor accepted;
- donor rejected;
- patient is suitable for transplant;
- patient is unsuitable for transplant;
- immunological risk score;
- virtual crossmatch result;
- DSA interpretation;
- allocation recommendation;
- treatment recommendation.

Allowed current wording should remain limited to:

- deterministic software comparison;
- non-clinical report;
- validation artifact;
- audit bundle;
- data export;
- technical/backend integration.

## Regulatory Deliverables Needed Next

Before clinical-intended development proceeds, create or assign ownership for:

- manufacturer/legal responsible entity decision;
- Person Responsible for Regulatory Compliance (PRRC) assessment if applicable;
- regulatory strategy memo;
- MDR/IVDR borderline assessment;
- formal classification rationale;
- claims matrix for README, UI, API, reports, exports, and any future website;
- applicable standards list;
- conformity assessment route assessment;
- Notified Body engagement plan if required;
- EUDAMED/UDI impact assessment if placed on the EU market;
- clinical evaluation or performance evaluation plan, depending on final route.

## Required Evidence Inputs For Final Classification

Final classification requires:

- frozen intended purpose;
- finalized user groups;
- finalized workflow and clinical context;
- data-flow diagram from HLA source systems to outputs;
- output catalogue and clinical significance analysis;
- foreseeable misuse analysis;
- severity assessment for incorrect, missing, stale, or misread outputs;
- human oversight model;
- deployment model, including hospital-only, SaaS, or distributed software;
- manufacturer and economic-operator roles.

## Decision Gates

The project must not move to clinical pilot until these gates are complete:

1. Intended Use frozen and approved.
2. MDR/IVDR borderline assessment completed.
3. Preliminary classification reviewed by qualified regulatory lead.
4. Claims matrix approved.
5. Risk management file initiated.
6. Requirements traceability started.
7. Usability engineering plan drafted for any clinical UI.
8. Clinical validation plan drafted.
9. Security, data-protection, data-governance and SOUP/dependency controls reviewed and approved.
10. Release/deployment, maintenance, problem-resolution and CAPA controls reviewed and approved.
11. Document-control index, approval matrix, claims matrix, change-impact checklist and clinical-readiness gate checklist reviewed and approved.
12. Manufacturer/legal responsible entity identified.

## Open Regulatory Questions

- Is the target route MDR, IVDR, or a combined/borderline route?
- Which exact clinical decision, if any, will the software support?
- Will outputs be used before surgery, during donor offer review, or only for
  retrospective audit?
- Will the software receive data directly from LIS/EHR systems?
- Will the software be placed on the EU market, used only in-house, or deployed
  as a hosted service?
- Who is the manufacturer or legal responsible entity?
- Is a Notified Body required for the final route and class?
- Which claims are acceptable for the frontend, reports, API documentation, and
  public repository?

## Draft Conclusion

The current project remains non-clinical and is not ready for clinical use.

If the project is developed for donor-situation clinical workflow use, it must
be treated as potential medical device software. Because transplantation-related
errors can have severe consequences, the project should use a conservative
classification strategy and assume significant MDR/IVDR regulatory work until a
qualified regulatory decision says otherwise.

No clinical claims should be added to the software, UI, API, documentation,
reports, or repository until the regulatory route and classification are
reviewed and approved.
