# Проект На Claims Control Matrix

Статус: Draft за claims-control planning. Не е одобрен labeling, marketing или clinical claims record.

Този документ дефинира начална claims-control matrix за HLA Transplantation Simulation проекта. Той контролира какво може и какво не може да се твърди в README, UI, API, reports, exports, audit bundles, integration docs, release notes и бъдещи user-facing материали.

## Цел

Целта е да се предотврати неволно превръщане на неклиничен deterministic HLA software prototype в clinical decision-support claim.

Текущият allowed claim е ограничен до: неклиничен софтуерен прототип, който създава deterministic comparison/report/export/audit artifacts за development, technical evaluation, validation planning и reproducibility.

## Изходни Документи

- [Document Control Index Draft](document-control-index.md)
- [Approval Matrix Draft](approval-matrix.md)
- [Change Impact Checklist Draft](change-impact-checklist.md)
- [Clinical Readiness Gate Checklist Draft](clinical-readiness-gate-checklist.md)
- [Intended Use](intended-use.md)
- [Regulatory Classification Draft](regulatory-classification.md)
- [Software Requirements Specification Draft](software-requirements.md)
- [Usability Engineering File Draft](usability-engineering.md)
- [Validation Plan Draft](validation-plan.md)
- [Backend API Component](../backend.md)
- [Backend Integration Guide](../backend-integration.md)

Официални външни references, проверени на 2026-08-26:

- FDA, Step 1: Is the Software Function Intended For a Medical Purpose:
  https://www.fda.gov/medical-devices/digital-health-center-excellence/step-1-software-function-intended-medical-purpose
- FDA, Clinical Decision Support Software Guidance, January 2026:
  https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software
- FDA, Device Labeling Guidance #G91-1:
  https://www.fda.gov/regulatory-information/search-fda-guidance-documents/device-labeling-guidance-g91-1-blue-book-memo
- MDCG 2019-11 rev.1, Qualification and classification of software, June 2025:
  https://health.ec.europa.eu/latest-updates/update-mdcg-2019-11-rev1-qualification-and-classification-software-regulation-eu-2017745-and-2025-06-17_en
- MDCG guidance index:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en

## Claims Controls

| ID | Control | Current status |
| --- | --- | --- |
| CLAIM-001 | All user-facing claims shall preserve explicit non-clinical status until approved otherwise. | Present/draft |
| CLAIM-002 | Claims shall not state or imply donor acceptance, donor rejection, organ allocation or transplant suitability. | Present/draft |
| CLAIM-003 | Claims shall not state or imply virtual crossmatch, DSA, MFI, cPRA, eplet, PIRCHE or graft-outcome interpretation. | Present/draft |
| CLAIM-004 | Reports and comparisons shall be described as deterministic software artifacts, not clinical recommendations. | Present/draft |
| CLAIM-005 | Sorting/ranking language shall be described as software ordering only. | Draft |
| CLAIM-006 | API integration docs shall state that downstream systems must not automate clinical action from backend output. | Draft |
| CLAIM-007 | Any new clinical-purpose wording requires clinical, regulatory and quality approval. | Planned |
| CLAIM-008 | Claims shall be linked to intended use, requirements, risks, validation evidence and release records. | Planned |
| CLAIM-009 | Prohibited claims shall be reviewed in README, UI, API schemas, reports, exports and release notes. | Planned |
| CLAIM-010 | Bulgarian localization shall preserve non-clinical boundary and technical meaning. | Draft |
| CLAIM-011 | Claims shall identify user population and workflow context when clinical-intended claims are later proposed. | Planned |
| CLAIM-012 | Claims shall state limitations and required human oversight when clinical workflow support is later proposed. | Planned |
| CLAIM-013 | Benefit/performance claims shall not be made without evidence and approval. | Planned |
| CLAIM-014 | Marketing, screenshots and demos shall not imply clinical approval or donor decision use. | Planned |
| CLAIM-015 | Claims changes shall trigger change-impact assessment. | Draft |
| CLAIM-016 | Unclear claim language shall be treated as release-blocking until reviewed. | Draft |

## Allowed Current Claims

| ID | Allowed claim wording | Scope | Required qualifier |
| --- | --- | --- | --- |
| AC-001 | Non-clinical HLA donor/recipient comparison prototype. | README/docs/demo | Must say non-clinical |
| AC-002 | Generates deterministic software comparison artifacts across CANONICAL/LGX/G/P representations. | CLI/API/reports | No compatibility claim |
| AC-003 | Stores local demo/runtime data in SQLite for development and testing. | README/data docs | No real clinical data |
| AC-004 | Provides FastAPI backend component for larger-application integration planning. | Backend docs | Not clinical decision system |
| AC-005 | Provides reproducible audit bundles for technical investigation and validation planning. | Audit docs | Not clinical sign-off |
| AC-006 | Provides local Bulgarian frontend validation prototype. | Frontend docs | Prototype only |
| AC-007 | Supports verification and validation planning artifacts. | Clinical docs | Planning only |
| AC-008 | Maintains clinical-readiness gaps and blockers. | Clinical docs | Does not authorize clinical use |

## Prohibited Current Claims

| ID | Prohibited claim | Reason |
| --- | --- | --- |
| PC-001 | Determines donor acceptance or donor rejection. | Clinical decision claim not approved |
| PC-002 | Determines transplant suitability. | Clinical decision claim not approved |
| PC-003 | Ranks recipients or donors for organ allocation. | Allocation/prioritization claim not approved |
| PC-004 | Performs virtual crossmatch interpretation. | Crossmatch claim not implemented/validated |
| PC-005 | Interprets DSA, MFI, cPRA, eplet mismatch or PIRCHE. | Outside current functionality and validation |
| PC-006 | Predicts graft outcome, rejection risk or patient survival. | Outcome claim not supported |
| PC-007 | Recommends treatment, desensitization or immunosuppression. | Treatment recommendation claim not supported |
| PC-008 | Confirms compatibility or incompatibility for transplantation. | Compatibility claim not approved |
| PC-009 | Is validated for clinical use. | Validation execution/report not complete |
| PC-010 | Is regulatory approved, certified or cleared. | Regulatory route not complete |
| PC-011 | Is safe for donor-situation clinical workflow. | Clinical readiness gates not complete |
| PC-012 | Can be used with real patient data in this repository. | Data governance not approved |

## Claim Review Matrix

| Surface | Current required wording | Review owner | Release blocker if missing |
| --- | --- | --- | --- |
| Root README | Non-clinical prototype; prohibited clinical uses listed | Product owner | Yes |
| Backend API docs | Backend is analytics/reporting component only | Software lead | Yes |
| Backend JSON envelope | `clinical: false` and non-clinical notice | Software lead | Yes |
| Frontend UI | Bulgarian non-clinical warning and disabled clinical approval | Product/validation lead | Yes |
| Reports and exports | Deterministic artifact wording; no suitability wording | Software/clinical lead | Yes |
| Audit bundles | Reproducibility artifact; not clinical sign-off | Quality/software lead | Yes |
| Integration guide | Downstream app must not automate clinical action | Software/security lead | Yes |
| Release notes | Scope, known limitations and non-clinical/clinical status | Product/quality lead | Yes |
| Marketing/demo materials | No clinical approval, outcome or recommendation implication | Product/regulatory lead | Yes |

## Future Clinical Claim Proposal Template

Any future clinical claim proposal must include:

- claim ID;
- exact proposed wording;
- intended users;
- patient/donor/recipient population;
- clinical workflow context;
- output affected;
- evidence supporting the claim;
- risks and risk controls;
- verification evidence;
- validation and usability evidence;
- cybersecurity and data-governance impact;
- regulatory route impact;
- approval roles and decision.

## Clinical-Use Blockers

Clinical workflow use remains blocked until:

- claims matrix is approved;
- intended use is frozen;
- regulatory route is determined;
- all user-facing text is reviewed;
- validation evidence supports any future clinical claim;
- release notes and integration contracts preserve the approved claim boundary;
- change-impact process blocks unapproved claims changes.

## Step 12 Conclusion

This matrix defines allowed and prohibited current claims. It does not approve any clinical, marketing, regulatory or performance claim beyond non-clinical prototype use.
