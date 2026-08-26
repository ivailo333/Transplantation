# Проект На Usability Engineering File

Статус: Draft за планиране на клинична готовност. Не е одобрен за клинична употреба.

Този документ започва usability engineering file за HLA Transplantation
Simulation проекта. Той е planning artifact за бъдеща оценка на user interface,
workflow и use-related risks. Документът не е summative usability validation и
не разрешава clinical use.

## Цел

Целта е да се дефинират intended users, use environments, user interface
елементи, safety-related user tasks, foreseeable use errors, preliminary
controls и evidence gaps преди бъдеща clinical workflow употреба.

Usability engineering трябва да намали риска потребителят да разбере
deterministic software artifact като clinical recommendation, donor acceptance,
donor rejection, allocation priority или transplant suitability.

## Изходни Документи

- [Български Clinical Readiness Обзор](bg-readiness-overview.md)
- [Intended Use](intended-use.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Requirements Specification Draft](software-requirements.md)
- [Traceability Matrix Draft](traceability-matrix.md)
- [Software Architecture Draft](software-architecture.md)
- [Verification Plan Draft](verification-plan.md)
- [Frontend Prototype Draft](frontend-prototype.md)
- [Backend API Component](../backend.md)

Официални външни references, проверени на 2026-08-26:

- IEC 62366-1:2015, Medical devices - application of usability engineering:
  https://www.iso.org/standard/63179.html
- FDA, Applying Human Factors and Usability Engineering to Medical Devices,
  final guidance, August 2026:
  https://www.fda.gov/regulatory-information/search-fda-guidance-documents/applying-human-factors-and-usability-engineering-medical-devices
- FDA, Human Factors and Medical Devices:
  https://www.fda.gov/medical-devices/device-advice-comprehensive-regulatory-assistance/human-factors-and-medical-devices
- ISO 14971:2019, Medical devices - application of risk management:
  https://www.iso.org/standard/72704.html

## Usability Scope

Current scope:

- неклиничен frontend validation prototype;
- CLI/backend/reporting/audit outputs, когато потребителят ги интерпретира;
- Bulgarian UI wording и non-clinical boundary labels;
- human review behavior, без clinical approval persistence.

Future clinical-intended scope, if approved:

- clinical workflow UI в larger application;
- role-specific displays for transplant clinician, coordinator, HLA lab user,
  quality/audit reviewer и admin/support user;
- user training and labeling;
- formative and summative usability validation;
- integration with final clinical sign-off workflow.

Out of current scope:

- approval for clinical use;
- validation of real donor-situation performance;
- direct patient/donor self-use;
- automated clinical action.

## Intended User Groups

| ID | User group | Current status | Key needs | Main risks |
| --- | --- | --- | --- | --- |
| USE-001 | Developer / maintainer | Current | Run CLI/API/frontend checks and inspect deterministic outputs | Mislabeling prototype as clinical-ready |
| USE-002 | Technical validator | Current | Reproduce reports, compare outputs and inspect audit bundles | Missing traceability or wrong artifact selected |
| USE-003 | HLA laboratory specialist | Future | Review typing source, representation level and missing-data status | Misread reduction or stale HLA reference |
| USE-004 | Transplant clinician | Future | Review structured HLA artifacts as adjunct information | Over-reliance or implied recommendation |
| USE-005 | Transplant coordinator | Future | Track case workflow and request audit evidence | Donor/recipient identity mix-up or stale view |
| USE-006 | Quality/audit reviewer | Future | Inspect traceability, release evidence and audit bundles | Incomplete audit trail |
| USE-007 | Admin/support user | Future | Monitor service readiness and configuration | Wrong environment or unauthorized access |

The software is not intended for direct patient, donor or general public use.

## Use Environments

| ID | Environment | Current status | Notes |
| --- | --- | --- | --- |
| UENV-001 | Local development | Current | Synthetic/demo/anonymized data only |
| UENV-002 | Local validation | Current | Prototype review and non-clinical test evidence |
| UENV-003 | Hospital-controlled staging | Future | Requires governance, RBAC, audit and controlled datasets |
| UENV-004 | Production clinical environment | Blocked | Requires regulatory/QMS/security/usability/validation release gates |
| UENV-005 | Emergency donor-situation workflow | Blocked | Requires downtime SOP, human oversight and clinical validation |

## User Interface Elements

| ID | Interface element | Current implementation | Safety relevance |
| --- | --- | --- | --- |
| UIE-001 | Root README and CLI help | `README.md`, CLI help tests | Must preserve non-clinical boundary |
| UIE-002 | Backend JSON envelopes | `backend_app.py`, `backend_services.py` | Must return `clinical: false` and request ID |
| UIE-003 | STEP 27/28 report text and exports | `step27_reporting.py`, `step28_report_comparison.py` | Must avoid suitability language |
| UIE-004 | Frontend case form | `frontend/index.html` | Must preserve donor/recipient direction and IDs |
| UIE-005 | Frontend tables and locus summaries | `frontend/app.js`, `frontend/styles.css` | Must avoid accept/reject visual cues |
| UIE-006 | Frontend raw JSON panel | `frontend/app.js` | Supports validation traceability |
| UIE-007 | Frontend clinical gate panel | `frontend/index.html` | Approval control intentionally disabled |
| UIE-008 | Future clinical app sign-off UI | Not implemented | Must enforce qualified human review if clinical route is approved |

## Safety-Related User Tasks

| ID | Task | User groups | Linked risks | Preliminary acceptance criterion |
| --- | --- | --- | --- | --- |
| UTASK-001 | Confirm that the system is non-clinical before using any output. | USE-001, USE-002, future users | RM-009, RM-018, RM-020, RM-025 | User can identify the non-clinical boundary without external instruction |
| UTASK-002 | Verify backend readiness before reviewing a report. | USE-001, USE-002, USE-007 | RM-012, RM-016, RM-024 | User can distinguish liveness/readiness from clinical availability |
| UTASK-003 | Enter donor/recipient direction and external ID correctly. | USE-002, USE-003, USE-005 | RM-001, RM-002, RM-022 | User can detect if donor/recipient direction is wrong before running report |
| UTASK-004 | Interpret missing or partial HLA data as incomplete information, not a conclusion. | USE-003, USE-004 | RM-003, RM-025 | User can identify missing-data warning and stop escalation if needed |
| UTASK-005 | Compare representation levels without treating deltas as compatibility or suitability. | USE-002, USE-003, USE-004 | RM-005, RM-010, RM-025 | User explains deltas as representation differences only |
| UTASK-006 | Read sorted/ranked rows as software ordering, not allocation priority. | USE-003, USE-004, USE-005 | RM-011, RM-025 | User can state the sorting metric and its non-clinical meaning |
| UTASK-007 | Create and locate an audit bundle for reproducibility review. | USE-002, USE-006 | RM-007, RM-008, RM-021 | User can confirm bundle manifest and request ID |
| UTASK-008 | Record validation observations without implying clinical approval. | USE-002, USE-006 | RM-010, RM-020, RM-023 | User understands local validation note is not clinical sign-off |
| UTASK-009 | Escalate backend/proxy error with request ID. | USE-001, USE-002, USE-007 | RM-017, RM-024 | User can provide request ID and error category to support |
| UTASK-010 | Future: complete clinical sign-off outside the backend component. | USE-003, USE-004, USE-005 | RM-018, RM-023 | Clinical sign-off cannot be bypassed or automated by backend output |

## Foreseeable Use Errors

| ID | Foreseeable use error | Linked tasks | Linked risks | Preliminary controls |
| --- | --- | --- | --- | --- |
| UERR-001 | User treats report output as donor suitability. | UTASK-001, UTASK-005 | RM-009, RM-018, RM-025 | Non-clinical labeling, claims review, no suitability fields |
| UERR-002 | User swaps donor and recipient direction. | UTASK-003 | RM-002 | Clear role labels, future confirmation step, audit metadata |
| UERR-003 | User overlooks missing locus/allele data. | UTASK-004 | RM-003 | Missing-data warnings, report flags, blocked conclusions |
| UERR-004 | User assumes LGX/G/P reduction is clinical compatibility. | UTASK-005 | RM-005 | Definitions, training, neutral labels |
| UERR-005 | User interprets sorted rows as allocation priority. | UTASK-006 | RM-011 | Sorting disclosure, no red/green suitability states |
| UERR-006 | User reviews stale output after data changes. | UTASK-003, UTASK-009 | RM-022 | Request IDs, timestamps, future refresh warning |
| UERR-007 | User ignores backend readiness failure. | UTASK-002, UTASK-009 | RM-016, RM-024 | Readiness display, downtime SOP, no sole-dependency claim |
| UERR-008 | User records validation note as clinical approval. | UTASK-008 | RM-010, RM-023 | Local-only label, disabled approval control |
| UERR-009 | User shares audit bundle or logs with sensitive identifiers. | UTASK-007 | RM-014, RM-021 | Data policy, storage controls, future retention/access rules |
| UERR-010 | Future integration uses API output to trigger automated action. | UTASK-010 | RM-009, RM-018, RM-023 | Integration contract, API excludes decision fields, workflow validation |

## Formative Evaluation Plan

Formative usability evaluation should be performed before any clinical-intended
release candidate. Suggested rounds:

| Round | Goal | Participants | Evidence |
| --- | --- | --- | --- |
| UF-001 | Review language and visual cues for unintended clinical claims | Clinical, HLA lab, regulatory, quality, software | Annotated UI/report wording review |
| UF-002 | Walk through donor/recipient case entry and report review | HLA lab specialist, coordinator, validator | Task observations and use-error log |
| UF-003 | Review representation-level comparison understanding | HLA lab specialist, transplant clinician | Comprehension notes and mitigation actions |
| UF-004 | Test audit bundle and error escalation workflow | Validator, quality/audit reviewer, support | Audit traceability and support handoff evidence |

## Summative Validation Planning

Summative usability validation remains blocked until:

- intended use and user groups are approved;
- clinical workflow and use environments are finalized;
- representative UI is implemented;
- training and labeling are drafted;
- risk controls for use-related hazards are implemented;
- formative findings are resolved or justified;
- validation protocol and acceptance criteria are approved.

## Usability Acceptance Criteria Draft

Initial criteria for future validation planning:

- users identify the software as adjunct/non-clinical unless clinical claims are
  later approved;
- users correctly identify donor/recipient direction before report execution;
- users recognize missing/stale/incomplete data warnings;
- users explain representation-level comparisons without stating compatibility;
- users do not interpret sorting as donor/candidate prioritization;
- users can locate request ID and audit bundle evidence;
- users understand that final clinical review is external and mandatory;
- critical use errors are absent or controlled to acceptable residual risk.

## Training And Labeling Needs

Future training/labeling must explain:

- intended use and non-intended uses;
- donor/recipient role handling;
- meaning of CANONICAL, LGX, G and P representation levels;
- missing-data and stale-data warnings;
- sorting and ranking as software ordering only;
- audit bundle purpose and limitations;
- downtime and support escalation;
- data governance and PHI handling;
- clinical sign-off responsibility if a clinical route is approved.

## Current Gap Status

| Area | Status |
| --- | --- |
| User groups | Drafted, not approved |
| Use environments | Drafted, not approved |
| Safety-related tasks | Drafted, not validated |
| Use-error analysis | Drafted, not reviewed |
| Formative evaluation | Planned |
| Summative usability validation | Not started |
| Training/labeling | Not started |
| Clinical UI sign-off workflow | Not implemented |

## Step 9 Conclusion

The project now has a planning-level usability engineering draft. It defines
representative users, use environments, safety-related tasks, foreseeable use
errors and preliminary usability evidence needs. It does not establish clinical
usability validation or clinical release readiness.
