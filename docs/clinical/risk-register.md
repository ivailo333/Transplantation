# Risk Management And Initial Risk Register

Status: Draft for clinical-readiness planning. This is not a completed ISO
14971 risk management file. Not approved for clinical use.

This document defines the initial risk management approach and seed risk
register for the HLA Transplantation Simulation project. It is intended to start
structured risk thinking before any clinical-intended development, pilot, or
release.

## Purpose

The purpose of this document is to:

- define an initial risk management method;
- identify foreseeable hazards and hazardous situations;
- define preliminary risk controls;
- identify verification and validation evidence needed for controls;
- keep current non-clinical boundaries visible;
- provide input for requirements, traceability, usability, validation, security,
  and release planning.

This document does not establish that risks are acceptable. Risk acceptability
requires qualified clinical, regulatory, quality, and technical review.

## Source Documents Reviewed

Internal project documents:

- [Intended Use](intended-use.md)
- [Regulatory Classification Draft](regulatory-classification.md)
- [Quality System Draft](quality-system.md)
- [Backend API Component](../backend.md)
- [Backend Integration Guide](../backend-integration.md)
- [Data Policy](../data.md)

Official external references checked for this draft:

- ISO 14971:2019, Medical devices - Application of risk management to medical
  devices:
  https://www.iso.org/standard/72704.html
- IEC/TR 80002-1:2009, Medical device software - Guidance on applying ISO 14971
  to medical device software:
  https://www.iso.org/standard/54146.html
- IEC 62304:2006, Medical device software - Software life cycle processes:
  https://www.iso.org/standard/38421.html
- European Commission MDCG guidance index, including software, cybersecurity,
  PMS/vigilance, and standardisation guidance:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en
- European Commission medical-device clinical investigations and performance
  studies overview:
  https://health.ec.europa.eu/medical-devices-clinical-investigations-and-performance-studies_en

## Risk Management Scope

Current scope:

- non-clinical HLA comparison and reporting software;
- CLI and backend API;
- deterministic exports and audit bundles;
- local SQLite persistence;
- synthetic, demo, anonymized, or validation-planning data.

Future scope, if clinical-intended development proceeds:

- clinical workflow UI;
- controlled user roles;
- identifiable or pseudonymized clinical data;
- clinical validation datasets;
- integration with LIS/EHR/FHIR/HL7 systems;
- release, monitoring, incident handling, and post-market processes;
- medical-device software lifecycle if classification confirms that route.

## Risk Management Method

Each risk entry should include:

- risk ID;
- hazard;
- hazardous situation;
- foreseeable harm;
- sequence of events;
- severity;
- probability;
- initial risk level;
- risk controls;
- verification evidence;
- residual risk status;
- owner;
- linked requirements or documents.

This initial draft uses qualitative severity and probability scales. These must
be reviewed and approved before formal use.

## Severity Scale Draft

| Level | Label | Description |
| --- | --- | --- |
| S1 | Negligible | No patient/user harm; inconvenience or rework only |
| S2 | Minor | Temporary workflow delay or minor data correction needed |
| S3 | Serious | Delay, incorrect review, or clinical confusion that could require intervention or escalation |
| S4 | Critical | Serious deterioration, wrong clinical action, wrong donor/candidate review, or surgical decision impact |
| S5 | Catastrophic | Death or irreversible deterioration could result if the output is relied on without detection |

## Probability Scale Draft

| Level | Label | Description |
| --- | --- | --- |
| P1 | Remote | Not expected in normal controlled use |
| P2 | Occasional | Could occur under foreseeable workflow conditions |
| P3 | Probable | Likely without additional controls or training |
| P4 | Frequent | Expected repeatedly in real workflow without redesign/control |

## Initial Risk Level Draft

Initial risk level is assessed qualitatively:

- Low: acceptable for non-clinical use with routine controls.
- Medium: requires documented control before validation use.
- High: requires control, verification, and quality review before any clinical
  workflow evaluation.
- Unacceptable: must block clinical-intended use until reduced or justified by
  benefit-risk analysis.

## Risk Acceptability Draft

For clinical-intended development:

- S5 risks are unacceptable unless strong controls reduce probability and a
  formal benefit-risk assessment is approved.
- S4 risks require independent clinical and quality review.
- Medium or higher residual risks require documented risk-control verification.
- Any risk tied to donor acceptance/rejection, allocation, transplant
  suitability, DSA/crossmatch interpretation, or identifiable patient data must
  be reviewed before clinical workflow use.

## Initial Risk Register

| ID | Hazard | Hazardous situation | Foreseeable harm | Initial risk | Preliminary controls | Evidence needed | Residual status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-001 | Incorrect HLA typing data | User imports or saves wrong allele values for donor or recipient | Incorrect comparison artifact; possible wrong clinical review if misused | High | Data-source traceability; validation on import; display raw and reduced values; require human review | Import validation tests; UI review tests; traceability records | Open |
| RM-002 | Donor/recipient identity mix-up | Donor and recipient identifiers are swapped or associated with wrong typing | Wrong pair comparison; possible donor decision error if used clinically | High | Clear role labels; immutable subject IDs; audit trail; confirmation for pair selection | Role-label UI tests; backend tests; audit log review | Open |
| RM-003 | Missing or partial HLA data | Missing locus/allele copy is displayed without adequate warning | User assumes complete data; incomplete review | High | Completeness checks; missing-data warnings; report flags; block clinical-style conclusions | Completeness tests; report snapshot tests; usability validation | Open |
| RM-004 | Stale IMGT/HLA or py-ard data | Comparison uses outdated reference data without clear version display | Misinterpretation of allele representation or reduced values | Medium | Display IMGT/HLA version; doctor checks; release dependency register | Doctor test; report metadata test; dependency review record | Open |
| RM-005 | Incorrect reduction or representation interpretation | CANONICAL, LGX, G, or P values are misunderstood as clinical compatibility | Misleading confidence; possible wrong decision if misused | High | Definitions in UI/report; non-clinical warning; training; no compatibility claims | Report content tests; claims matrix review; usability validation | Open |
| RM-006 | Software comparison defect | Algorithm defect produces incorrect shared/donor-only/recipient-only values | Incorrect report artifact; possible clinical confusion | High | Unit tests; independent expected-case fixtures; code review; regression tests | Requirements-based tests; algorithm review record | Open |
| RM-007 | Export/report mismatch | JSON, CSV, HTML, or API outputs disagree | Audit inconsistency; wrong artifact used for review | Medium | Deterministic export tests; cross-format consistency checks; audit bundle metadata | Export parity tests; audit bundle validation | Open |
| RM-008 | Audit trail incomplete | Report cannot be reproduced or traced to inputs/version | Failure to investigate discrepancy; quality/audit failure | High | Audit bundle metadata; request IDs; schema/doctor status; immutable release records | Audit bundle tests; release record checklist | Open |
| RM-009 | API misuse as clinical decision engine | Integrating application treats backend output as donor suitability result | Wrong clinical action; donor/candidate harm | Unacceptable | Non-clinical API envelope; claim controls; endpoint docs; no suitability field; integration guide warnings | API contract tests; claims review; integration validation | Open |
| RM-010 | Frontend UI implies recommendation | Future UI labels, colors, ranking, or badges imply accept/reject | User over-relies on software output | Unacceptable | UI claims matrix; neutral language; usability engineering; no red/green suitability labels | UI design review; usability validation; claims approval | Open |
| RM-011 | Wrong sort/ranking interpretation | Sorted report is interpreted as clinical ranking of donor/candidate suitability | Incorrect prioritization or review focus | High | Label rankings as software sorting only; require sort metric disclosure; no allocation language | Report text tests; UI tests; user training evidence | Open |
| RM-012 | Database schema mismatch | Backend runs against stale or migrated database incorrectly | Missing records or incorrect report generation | Medium | `/v1/ready`; schema verification; migrations; CI tests | Migration tests; readiness tests; deployment checklist | Open |
| RM-013 | Unauthorized access | API key, host, or deployment controls expose sensitive data | Privacy breach; unauthorized data use | High | API key; RBAC future work; TLS gateway; secret management; audit logs | Security tests; deployment review; access review records | Open |
| RM-014 | Identifiable clinical data without governance | Real donor/recipient data used in non-approved environment | Privacy/legal breach; loss of trust | High | Data policy; environment separation; no PHI in Git; governance approval before real data | Data-protection assessment; access logs; repo scans | Open |
| RM-015 | Dependency vulnerability | Third-party dependency or Docker base image has known vulnerability | Security compromise; data exposure or service manipulation | Medium | Dependency register; vulnerability monitoring; update policy; release review | Dependency audit records; SBOM future work | Open |
| RM-016 | Service unavailable during donor review | Backend/API unavailable when user expects reports | Workflow delay; possible workaround using uncontrolled process | Medium | Liveness/readiness probes; downtime procedure; no sole-dependency clinical claim | Probe tests; operational runbook; downtime validation | Open |
| RM-017 | Error handling hides root cause | Structured error is too vague or misleading | User repeats wrong workflow or misses data/system issue | Medium | Structured errors with request ID; logs; troubleshooting docs | Error-path tests; log review; support procedure | Open |
| RM-018 | Incorrect clinical expansion of scope | New features add DSA/crossmatch/cPRA/eplet claims without risk review | Uncontrolled medical-device claims; unsafe use | Unacceptable | Change control; claims matrix; regulatory gate; code review checklist | Change-impact records; regulatory review sign-off | Open |
| RM-019 | Validation dataset bias | Retrospective cases do not represent real edge cases or population | False confidence in performance | High | Validation plan; representative case selection; clinical review; edge-case catalog | Validation protocol/report; dataset rationale | Open |
| RM-020 | User training insufficient | Users misunderstand non-clinical boundary or report meaning | Over-reliance or wrong interpretation | High | Training plan; role-based access; visible warnings; competency checks | Training records; usability validation; user feedback | Open |
| RM-021 | Logs or audit bundles leak sensitive data | Debug logs, exports, or bundles include identifiers or clinical data | Privacy breach | High | Data minimization; configurable log level; storage controls; retention policy | Log review; export review; privacy assessment | Open |
| RM-022 | Concurrency or stale view issue | User reviews old report after database or typing update | Decision based on stale artifact | Medium | Timestamps; request IDs; data version metadata; refresh warnings in future UI | Report metadata tests; UI validation | Open |
| RM-023 | Human oversight bypassed | Workflow permits automated downstream action without clinician sign-off | Wrong clinical action | Unacceptable | API contract excludes decision fields; require sign-off in future UI; integration contract | Integration tests; workflow validation; audit review | Open |
| RM-024 | Incorrect environment configuration | Production-like deployment points to wrong database/export path | Wrong data used; audit artifacts misplaced | High | `.env` examples; readiness checks; deployment checklist; environment separation | Config tests; deployment dry run; operational checklist | Open |
| RM-025 | Report language ambiguity | Report wording is interpreted as clinical compatibility or risk | Misinterpretation by user | High | Controlled wording; claims matrix; report review by clinical/regulatory stakeholders | Report content tests; claims approval; usability feedback | Open |

## Preliminary Risk Controls Already Present

The current repository already includes some technical controls:

- repeated non-clinical notices in README, backend docs, and API envelopes;
- structured backend response envelopes with `clinical: false`;
- request ID propagation in backend responses;
- liveness and readiness probes;
- schema status and doctor checks;
- deterministic JSON/CSV/HTML exports;
- reproducible audit bundles;
- unit tests and CI smoke tests;
- `transplant.db`, secrets, exports, and runtime files excluded from Git.

These controls are useful, but they do not establish clinical risk
acceptability.

## Required Next Risk Work

Before clinical-intended development proceeds, complete:

1. Freeze intended use.
2. Assign risk management owner.
3. Approve severity/probability scales.
4. Convert this draft into a controlled risk management file.
5. Link each risk to software requirements.
6. Define verification for every risk control.
7. Define validation evidence for workflow/user-facing controls.
8. Add cybersecurity-specific risk assessment.
9. Add usability/use-error analysis for the frontend.
10. Add production/post-production risk monitoring process.

## Risk Traceability Requirements

Each risk control should trace to:

- one or more software requirements;
- design or architecture elements;
- implementation references;
- verification tests;
- validation evidence, if user workflow or clinical context is affected;
- residual risk evaluation;
- release decision.

## Benefit-Risk Boundary

No benefit-risk claim is made in this draft.

A benefit-risk analysis can only be performed after:

- intended clinical benefit is defined;
- clinical evidence strategy is defined;
- risk controls are implemented and verified;
- residual risks are reviewed;
- clinical stakeholders review the expected benefit in the target workflow.

## Production And Post-Production Monitoring

If a clinical-intended route is pursued, post-production risk monitoring must
collect and review:

- complaints;
- suspected incorrect outputs;
- incident and near-miss reports;
- cybersecurity vulnerabilities;
- dependency changes;
- drift in source data formats or HLA nomenclature;
- usability feedback;
- audit-bundle review findings;
- deployment incidents;
- CAPA effectiveness.

## Decision Gates

Clinical pilot remains blocked until:

1. Risk management owner is assigned.
2. Risk scales are approved.
3. Initial risk register is reviewed by clinical, regulatory, quality, software,
   security, and validation leads.
4. Unacceptable risks have documented controls and verification plans.
5. Requirements traceability matrix includes risk controls.
6. Usability plan covers safety-related UI risks.
7. Validation plan covers high-risk workflows and edge cases.
8. Release checklist includes residual risk review.

## Open Risk Questions

- Which risks are safety-related vs quality-only?
- Which future UI elements could imply clinical ranking or recommendation?
- Which HLA source systems and data formats will be integrated?
- Which fields are authoritative in a donor situation?
- What constitutes a clinically significant incorrect output?
- What retrospective cases will cover high-risk edge cases?
- What downtime procedure is acceptable in a donor review workflow?
- Who approves residual risk acceptability?

## Draft Conclusion

The project now has an initial risk management structure and seed risk register.
All risks remain open. No residual risk has been accepted, and no clinical use is
authorized.

The requirements specification, traceability matrix, architecture draft and
verification plan are now drafted at planning level. The next readiness step
should define usability and validation evidence for user-facing risk controls
before any clinical workflow use is considered.
