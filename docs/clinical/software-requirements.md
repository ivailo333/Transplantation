# Проект На Спецификация На Софтуерните Изисквания

Статус: Draft за планиране на клинична готовност. Не е одобрен за клинична употреба.

Този документ дефинира начални testable software requirements за HLA Transplantation Simulation проекта, докато той се движи от неклиничен CLI/backend prototype към възможно по-голямо приложение. Тези requirements не са baselined, не са одобрени и не са достатъчни за clinical release.

## Цел

Целта на този draft е да превърне intended use, risk register, backend API, frontend prototype и quality/lifecycle planning в requirements, които по-късно могат да бъдат reviewed, baselined, implemented, verified, validated и поставени под change control.

## Изходни Документи

Вътрешни source документи:

- [Intended Use](intended-use.md)
- [Regulatory Classification Draft](regulatory-classification.md)
- [Quality System Draft](quality-system.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Lifecycle Draft](software-lifecycle.md)
- [Frontend Prototype Draft](frontend-prototype.md)
- [Backend API Component](../backend.md)
- [Backend Integration Guide](../backend-integration.md)
- [Data Policy](../data.md)

Официални външни references, проверени на 2026-08-26:

- IEC 62304:2006, Medical device software - software life cycle processes:
  https://committee.iso.org/standard/38421.html
- ISO 14971:2019, Medical devices - application of risk management:
  https://www.iso.org/standard/72704.html
- IEC 62366-1:2015, Medical devices - usability engineering:
  https://webstore.iec.ch/en/publication/21863
- European Commission MDCG guidance index for MDR/IVDR:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en

## Requirement Status Values

| Статус | Значение |
| --- | --- |
| Present | В текущото repository има начална implementation или control. |
| Prototype | Частично implemented за неклинична validation, но не е production-ready. |
| Planned | Requirement е идентифициран, но не е implemented. |
| Blocker | Requirement е нужен преди всякаква clinical workflow употреба. |

## Verification Method Values

| Метод | Значение |
| --- | --- |
| Unit | Automated unit test или focused module test. |
| Integration | Backend/frontend/database/API integration test. |
| System | End-to-end workflow test в controlled environment. |
| Review | Documented design, code, claims, security или clinical review. |
| Validation | Representative user/workflow validation с предварително дефинирани acceptance criteria. |

## Изисквания

| ID | Изискване | Статус | Връзки към рискове | Верификация |
| --- | --- | --- | --- | --- |
| CLM-001 | Софтуерът shall display and return explicit non-clinical status за текущите CLI, API, reports, audit bundles и frontend prototype outputs. | Present | RM-005, RM-009, RM-010, RM-018, RM-020, RM-025 | Unit, Integration, Review |
| CLM-002 | Софтуерът shall not expose donor acceptance, donor rejection, transplant suitability, allocation, prioritization, treatment или autonomous clinical decision fields. | Present | RM-009, RM-010, RM-018, RM-023 | Integration, Review |
| CLM-003 | User-facing labels, API fields, reports и documentation shall avoid compatibility, recommendation, risk-score или clinical ranking claims, освен ако не са formally approved. | Prototype | RM-005, RM-010, RM-011, RM-018, RM-025 | Review, Validation |
| CLM-004 | Clinical approval или sign-off workflow shall remain disabled or absent, докато intended use, regulatory, risk, usability, validation и release gates не бъдат approved. | Prototype | RM-010, RM-018, RM-023 | Integration, Review |
| DATA-001 | Текущата употреба shall be limited to synthetic, demo, anonymized или validation-planning records. | Present | RM-014, RM-021 | Review |
| DATA-002 | Софтуерът shall preserve donor/recipient direction и subject role labels през input, persistence, API, reports, frontend display и audit artifacts. | Prototype | RM-002, RM-011, RM-022 | Unit, Integration, Validation |
| DATA-003 | HLA typing values shall be validated against the configured HLA validation path преди persistence или deterministic comparison. | Present | RM-001, RM-003, RM-006 | Unit, Integration |
| DATA-004 | Missing, partial или ambiguous HLA typing data shall be represented explicitly и shall not be converted into clinical conclusions. | Planned | RM-003, RM-025 | Unit, System, Validation |
| DATA-005 | Reports и comparisons shall include source identifiers, representation level, request ID, generation metadata и relevant HLA reference version metadata. | Present | RM-004, RM-008, RM-022 | Unit, Integration |
| DATA-006 | Identifiable clinical data, secrets, runtime databases, exports, audit bundles и logs shall not be committed to source control. | Present | RM-014, RM-021 | Review, System |
| API-001 | Backend APIs intended for new integrations shall use versioned `/v1` endpoints и structured JSON request/response contracts. | Present | RM-009, RM-012, RM-017 | Integration |
| API-002 | Backend API responses shall include `schema`, `request_id`, `clinical: false` и non-clinical notice where applicable. | Present | RM-008, RM-009, RM-017, RM-020 | Integration |
| API-003 | Protected backend endpoints shall support API-key authentication в неклинични deployments и shall be replaced or supplemented by role-based access control before clinical use. | Prototype | RM-013, RM-014, RM-023 | Integration, Review |
| API-004 | Liveness и readiness probes shall provide operational status без clinical claims или unnecessary sensitive data exposure. | Present | RM-012, RM-013, RM-016, RM-024 | Integration, Review |
| API-005 | Error responses shall distinguish validation, encoding, IO, schema, not-found, conflict, authorization и service-unavailable conditions with request IDs. | Present | RM-012, RM-017, RM-024 | Unit, Integration |
| API-006 | Backend request handling shall propagate request IDs into response headers and logs за reproducibility и support review. | Present | RM-008, RM-017, RM-021 | Integration, Review |
| FUNC-001 | Софтуерът shall generate deterministic STEP 27 live and batch analytical reports from persisted donor/recipient HLA typing data. | Present | RM-001, RM-006, RM-007, RM-008 | Unit, Integration |
| FUNC-002 | Софтуерът shall compare representation levels for the same case and report deterministic pair/locus deltas без да ги interpreted as clinical suitability. | Present | RM-005, RM-006, RM-009, RM-025 | Unit, Integration, Review |
| FUNC-003 | Софтуерът shall create reproducible audit bundles containing report, comparison, doctor, schema и metadata artifacts. | Present | RM-007, RM-008, RM-021 | Unit, Integration |
| FUNC-004 | JSON, CSV, HTML, text, API и audit outputs for the same operation shall remain consistent for controlled fields. | Prototype | RM-007, RM-008 | Unit, Integration |
| FUNC-005 | Sorting и ranking fields shall be disclosed as software ordering only и shall not imply clinical prioritization. | Prototype | RM-011, RM-025 | Review, Validation |
| UI-001 | Frontend-ът shall show donor/recipient direction, external ID, selected level, request ID и backend status clearly during case review. | Prototype | RM-002, RM-011, RM-016, RM-022 | System, Validation |
| UI-002 | Frontend-ът shall expose liveness/readiness checks before report review и shall surface backend/proxy errors without hiding request details. | Prototype | RM-016, RM-017, RM-024 | System |
| UI-003 | Frontend-ът shall display report tables, locus summaries, comparison rows и raw JSON response data for validation traceability. | Prototype | RM-001, RM-005, RM-008, RM-022 | System, Validation |
| UI-004 | Clinical workflow UI shall provide explicit warnings за missing, partial, stale или inconsistent case data before any reviewed output is used. | Planned | RM-003, RM-004, RM-022 | System, Validation |
| UI-005 | Frontend-ът shall use neutral language and visual states that do not imply accept/reject или suitability recommendations. | Prototype | RM-010, RM-011, RM-025 | Review, Validation |
| UI-006 | Frontend-ът shall not store clinical approval. Prototype reviewer notes may be local-only and clearly labelled as validation notes. | Prototype | RM-010, RM-014, RM-021, RM-023 | System, Review |
| AUD-001 | Audit bundles shall include enough metadata to reproduce or investigate the generated software artifact. | Present | RM-008, RM-017, RM-021 | Unit, Integration |
| AUD-002 | Clinical-intended releases shall include immutable release identifiers, dependency versions, migration status и approved configuration records. | Planned | RM-004, RM-008, RM-012, RM-015, RM-024 | Review, System |
| SEC-001 | Runtime configuration shall be supplied through environment/configuration files, with examples that do not contain secrets. | Present | RM-013, RM-014, RM-024 | Review |
| SEC-002 | Before clinical workflow use, larger application shall implement role-based authentication, authorization, session management and access review. | Blocker | RM-013, RM-014, RM-021, RM-023 | System, Review |
| SEC-003 | Before clinical workflow use, deployment shall use TLS, network segmentation, secret management, backup/restore controls and monitored logs. | Blocker | RM-013, RM-014, RM-016, RM-021, RM-024 | System, Review |
| SEC-004 | Проектът shall maintain a dependency/SOUP register, vulnerability monitoring and update policy before controlled release. | Planned | RM-004, RM-015 | Review |
| OPS-001 | Clinical workflow shall define downtime, degraded-mode, support and escalation procedures before donor-situation use. | Blocker | RM-016, RM-017, RM-024 | Review, Validation |
| OPS-002 | Production-like deployment shall require readiness checks, migration checks, environment checks, smoke tests and rollback criteria. | Planned | RM-012, RM-016, RM-024 | System, Review |
| INT-001 | Integration contracts shall state that downstream systems must not treat API outputs as autonomous clinical actions or automated sign-off. | Planned | RM-009, RM-018, RM-023 | Review, System |
| INT-002 | Future LIS/EHR/FHIR/HL7 integrations shall preserve source-system identity, data timestamps, authoritativeness and transformation provenance. | Planned | RM-001, RM-002, RM-004, RM-022 | Integration, Review |
| VAL-001 | Verification shall include requirements-based tests for deterministic comparison, reporting, export parity, API contracts, migrations, errors and audit bundles. | Planned | RM-006, RM-007, RM-008, RM-012, RM-017 | Unit, Integration |
| VAL-002 | Validation shall use representative cases, edge cases and documented inclusion/exclusion rationale before clinical workflow use. | Blocker | RM-019 | Validation |
| VAL-003 | Usability engineering shall cover safety-related UI tasks, foreseeable use errors, warnings, neutral wording and user comprehension. | Blocker | RM-010, RM-011, RM-020, RM-025 | Validation |
| VAL-004 | Clinical workflow validation shall verify that qualified human review remains mandatory and that no automated clinical action can bypass oversight. | Blocker | RM-009, RM-018, RM-023 | System, Validation |

## Baseline Правила

Преди тези requirements да станат controlled:

1. Назначете requirement owner и approvers.
2. Потвърдете intended use и regulatory classification.
3. Прегледайте всеки requirement с clinical, HLA laboratory, regulatory, quality, software, security и validation stakeholders.
4. Свържете всеки requirement към design, implementation, verification, validation и risk controls в traceability matrix.
5. Добавете version, approval и change-control metadata.
6. Freeze-нете baseline преди изпълнение на clinical-intended validation protocol.

## Заключение За Стъпка 7

Проектът вече има начален requirements draft, architecture draft, verification plan draft, usability engineering draft и validation plan draft. Следващата readiness работа трябва да създаде cybersecurity, data-governance и SOUP/dependency records, след което frontend и security моделът да се разширяват само под change control.
