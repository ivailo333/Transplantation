# Intended Use

Status: Draft for clinical-readiness planning. Not approved for clinical use.

This document defines the current and proposed intended use boundaries for the
HLA Transplantation Simulation project. It is the controlling input for later
regulatory classification, risk management, requirements, usability, validation,
and clinical workflow documentation.

## Current Intended Use

The software is currently intended for non-clinical HLA data management,
deterministic donor/recipient software comparison, report generation, report
comparison, and reproducible audit-bundle creation.

The current product is not intended to provide medical advice, transplant
suitability assessment, donor acceptance or rejection, organ allocation,
clinical risk scoring, virtual crossmatch interpretation, DSA interpretation,
MFI interpretation, unacceptable antigen assessment, cPRA calculation, eplet
mismatch assessment, PIRCHE assessment, graft-outcome prediction, treatment
recommendations, or any autonomous clinical decision.

## Proposed Future Clinical Context

The future product may be evaluated as an adjunctive clinical workflow tool for
structured display, comparison, and audit of HLA typing information during
transplantation-related review.

Any future clinical use must remain subject to independent review and final
decision-making by qualified transplant clinicians and/or authorized transplant
laboratory personnel. The software must not become the sole basis for donor
acceptance, donor rejection, candidate selection, or clinical prioritization.

## Intended Users

Current intended users:

- software developers maintaining the project;
- researchers or technical evaluators using synthetic, demo, or anonymized data;
- validation personnel reviewing deterministic report artifacts.

Potential future clinical workflow users, subject to formal validation:

- transplant clinicians;
- transplant coordinators;
- HLA laboratory specialists;
- clinical governance, quality, and audit personnel.

The software is not intended for direct patient or donor self-use.

## Intended Patient Or Case Population

The current software operates on HLA typing records for donor and recipient
subjects represented by local external identifiers. In the current state, these
records must be synthetic, demo, or appropriately anonymized/pseudonymized
records used for development, testing, research, or validation planning.

Any use with identifiable clinical data requires an approved data-governance
process, access controls, retention policy, audit process, and legal basis for
processing.

## Intended Use Environment

Current environments:

- local development;
- local validation;
- non-production backend integration testing.

Potential future environments, subject to approval and validation:

- hospital-controlled staging environment;
- transplant-center validation environment;
- production clinical environment only after regulatory, quality, security,
  usability, and clinical validation activities are completed.

## Inputs

The software may receive:

- donor and recipient subject identifiers;
- HLA typings by locus and allele copy;
- IMGT/HLA version metadata;
- selected representation levels such as CANONICAL, LGX, G, and P;
- report, comparison, export, and audit request parameters;
- local SQLite database records created by project commands or APIs.

The current software does not ingest antibody profiles, DSA results,
crossmatch results, cPRA, eplet libraries, clinical urgency, blood group,
comorbidities, infection risk, graft outcome data, allocation rules, or
therapeutic recommendations.

## Outputs

The software may produce:

- deterministic HLA comparison data;
- STEP 24 matrix views;
- STEP 25 mismatch summaries;
- STEP 26 descriptive statistics;
- STEP 27 analytical reports;
- STEP 28 report comparisons;
- JSON, CSV, and HTML exports;
- backend API response envelopes;
- reproducible audit bundles with metadata and doctor/schema status.

Outputs are software artifacts for review and traceability. Outputs are not
clinical decisions and must not be labelled or interpreted as donor suitability
or transplant suitability determinations.

## Explicit Non-Intended Uses

The software must not be used to:

- accept or reject a donor;
- rank candidates for organ allocation;
- determine transplant suitability;
- replace a transplant clinician, immunologist, or HLA laboratory specialist;
- perform virtual crossmatch interpretation;
- interpret DSA, MFI, unacceptable antigens, cPRA, eplet mismatch, PIRCHE, or
  graft-outcome risk;
- provide emergency medical advice;
- provide autonomous diagnosis, prognosis, treatment, or allocation decisions;
- operate with identifiable clinical data without approved governance and
  security controls.

## Human Oversight

All outputs require review by appropriately qualified personnel. The software
must present its outputs as supporting artifacts only. Any future clinical
workflow must preserve clear user responsibility, clinical sign-off, and audit
traceability.

## Safety And Usability Boundaries

Before any clinical-intended release, the project must define and validate:

- user roles and permissions;
- critical tasks;
- foreseeable use errors;
- required warnings and confirmations;
- display rules for missing, partial, stale, or conflicting data;
- audit logging and report traceability;
- procedures for downtime, data correction, and incident handling.

## Regulatory Classification Trigger

If future claims state or imply that the software provides information used to
make diagnosis, treatment, donor acceptance, donor rejection, organ allocation,
or transplant-suitability decisions, the project must be evaluated as potential
medical device software under applicable regulations before use in that manner.

Regulatory classification is intentionally not finalized in this document. It
must be handled in the regulatory-classification step after this intended use is
reviewed and approved.

## Assumptions

- HLA typing data are entered or imported from trusted sources.
- IMGT/HLA version metadata are available and traceable.
- Users understand that deterministic HLA software comparisons are not complete
  transplant compatibility assessments.
- The backend is deployed only in controlled environments appropriate to its
  validation status.
- Current outputs are non-clinical and validation-oriented.

## Open Decisions

- Will the future product remain a non-clinical audit/reporting component, or
  will it make clinical decision-support claims?
- Which clinical users will be authorized to use the future interface?
- Which transplant workflow step, if any, will the product support?
- Will the system handle identifiable clinical data?
- Which hospital systems, LIS, EHR, or registry integrations are required?
- Which outputs are safety-related and require usability validation?
- Which retrospective cases will be used for validation?
- Which party will act as manufacturer or legal responsible entity if a medical
  device route is pursued?

## Approval Criteria For Freezing Intended Use

This intended use can be frozen for the next readiness phase only after:

- clinical stakeholders review and approve the workflow boundary;
- regulatory counsel or a qualified regulatory lead reviews the claims;
- quality leadership accepts the change-control process;
- the explicit non-intended uses remain visible in user-facing documentation;
- downstream requirements, risk controls, usability tasks, and validation tests
  are traceable to this document.
