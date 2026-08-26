# Български Clinical Readiness Обзор

Статус: Работен обзор за планиране. Не е одобрен за клинична употреба.

Този документ е българският централен вход към clinical-readiness материалите на проекта след стъпка 12. Той не замества подробните source drafts, а обобщава текущото състояние, границите и оставащите gate-ове.

## Текуща Граница

Проектът е неклиничен HLA software prototype. Той може да служи за разработка, техническа оценка, демонстрация, валидационно планиране и възпроизводими software artifacts.

Проектът не е готов за клинична употреба при реална донорска ситуация. Не трябва да се използва като основание за donor acceptance, donor rejection, organ allocation, clinical prioritization, virtual crossmatch interpretation, DSA/MFI/cPRA/eplet/PIRCHE interpretation, treatment recommendation или автономно клинично решение.

## Какво Е Изградено До Момента

1. Intended use draft: дефинира неклиничната текуща употреба и бъдещата възможна клинична рамка.
2. Regulatory classification draft: описва защо бъдеща клинична употреба вероятно изисква формална regulatory оценка.
3. Quality system draft: очертава QMS процесите, roles, change control, validation, release и post-market нужди.
4. Risk management draft: съдържа начални рискове RM-001 до RM-025 и preliminary controls.
5. Software lifecycle draft: описва IEC 62304-style lifecycle процеса и deliverables.
6. Frontend prototype draft: добавя локален неклиничен validation UI към backend API компонента.
7. Software requirements и traceability drafts: свързват requirements, risks, controls, current implementation и evidence gaps.
8. Software architecture и verification plan drafts: дефинират components, interfaces, data flows, trust boundaries, failure modes и `VER-*` verification items.
9. Usability engineering и validation plan drafts: дефинират users, environments, safety-related tasks, use errors, datasets, validation scenarios и acceptance criteria.
10. Cybersecurity, data-governance и SOUP/dependency drafts: дефинират security objectives, threat/asset register, health-data rules, retention, SBOM и vulnerability-monitoring planning.
11. Release/deployment, maintenance и problem-resolution/CAPA drafts: дефинират release package, deployment runbook, rollback/downtime controls, change types, post-release monitoring, anomaly triage и CAPA records.
12. Controlled baseline и claims-control drafts: дефинират document-control index, owners/approvers, allowed/prohibited claims, change-impact checklist и clinical-readiness gate checklist.

## Основни Артефакти

- [Intended Use](intended-use.md)
- [Regulatory Classification Draft](regulatory-classification.md)
- [Quality System Draft](quality-system.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Lifecycle Draft](software-lifecycle.md)
- [Frontend Prototype Draft](frontend-prototype.md)
- [Software Requirements Specification Draft](software-requirements.md)
- [Traceability Matrix Draft](traceability-matrix.md)
- [Software Architecture Draft](software-architecture.md)
- [Verification Plan Draft](verification-plan.md)
- [Usability Engineering File Draft](usability-engineering.md)
- [Validation Plan Draft](validation-plan.md)
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

## Какво Е На Български

- Централен root README.
- Frontend validation UI.
- Frontend README.
- Step 6 frontend prototype draft.
- Step 7 software requirements draft.
- Step 7 traceability matrix draft.
- Step 8 software architecture draft.
- Step 8 verification plan draft.
- Step 9 usability engineering draft.
- Step 9 validation plan draft.
- Step 10 cybersecurity plan draft.
- Step 10 data governance plan draft.
- Step 10 SOUP/dependency register draft.
- Step 11 release/deployment plan draft.
- Step 11 maintenance plan draft.
- Step 11 problem-resolution/CAPA plan draft.
- Step 12 document-control index draft.
- Step 12 approval matrix draft.
- Step 12 claims-control matrix draft.
- Step 12 change-impact checklist draft.
- Step 12 clinical-readiness gate checklist draft.
- Този readiness overview.

По-старите подробни source drafts остават на английски на този етап, за да се пази историческата им връзка с предишните commits. При нужда могат да бъдат преведени като отделна controlled localization task.

## Минимални Клинични Blockers

Клинична употреба остава блокирана, докато няма:

- финално одобрено intended use и claims;
- регулаторна класификация и правен/институционален route;
- QMS ownership и approved controlled document process;
- named owners/approvers and approval matrix;
- approved claims matrix and change-impact process;
- baselined requirements и traceability;
- software architecture и data-flow records;
- verification plan/report;
- validation plan/report с representative cases;
- usability engineering file;
- reviewed cybersecurity threat model/risk assessment and security test evidence;
- approved data governance for any real or pseudonymized health data;
- role-based access control, audit trail, retention policy и deployment controls;
- SBOM, vulnerability monitoring and SOUP/supplier review gates;
- release approval, deployment rehearsal, change control, incident/CAPA и post-market monitoring process;
- completed clinical-readiness gate decision by assigned approvers.

## Подход За Българска Локализация

Локализацията трябва да пази technical IDs и API contract terms непроменени:

- requirement IDs: `CLM-001`, `DATA-001`, `API-001` и т.н.;
- risk IDs: `RM-001` до `RM-025`;
- API fields: `schema`, `request_id`, `clinical`, `external_id`, `level` и др.;
- endpoint names: `/v1/reports/live`, `/v1/comparisons/levels`, `/v1/audit/live`.

Потребителските labels, README инструкциите, UI предупрежденията и validation wording могат и трябва да бъдат на български за локален клиничен/валидационен екип.

## Следваща Стъпка

Стъпка 13 трябва да започне technical control implementation срещу този planning package: автоматизиран SBOM/dependency audit scaffold, secret/PHI scan checks, release-evidence command, security headers/gateway guidance и baseline-aware CI checks. RBAC, TLS/gateway, retention и production deployment трябва да останат blocked, докато няма named approvers и approved baseline.
