# Български Clinical Readiness Обзор

Статус: Работен обзор за планиране. Не е одобрен за клинична употреба.

Този документ е българският централен вход към clinical-readiness материалите на проекта преди стъпка 8. Той не замества подробните source drafts, а обобщава текущото състояние, границите и оставащите gate-ове.

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

## Основни Артефакти

- [Intended Use](intended-use.md)
- [Regulatory Classification Draft](regulatory-classification.md)
- [Quality System Draft](quality-system.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Lifecycle Draft](software-lifecycle.md)
- [Frontend Prototype Draft](frontend-prototype.md)
- [Software Requirements Specification Draft](software-requirements.md)
- [Traceability Matrix Draft](traceability-matrix.md)

## Какво Е На Български

- Централен root README.
- Frontend validation UI.
- Frontend README.
- Step 6 frontend prototype draft.
- Step 7 software requirements draft.
- Step 7 traceability matrix draft.
- Този readiness overview.

По-старите подробни source drafts остават на английски на този етап, за да се пази историческата им връзка с предишните commits. При нужда могат да бъдат преведени като отделна controlled localization task.

## Минимални Клинични Blockers

Клинична употреба остава блокирана, докато няма:

- финално одобрено intended use и claims;
- регулаторна класификация и правен/институционален route;
- QMS ownership и controlled document process;
- baselined requirements и traceability;
- software architecture и data-flow records;
- verification plan/report;
- validation plan/report с representative cases;
- usability engineering file;
- cybersecurity risk assessment;
- role-based access control, audit trail, retention policy и deployment controls;
- release approval, change control, incident/CAPA и post-market monitoring process.

## Подход За Българска Локализация

Локализацията трябва да пази technical IDs и API contract terms непроменени:

- requirement IDs: `CLM-001`, `DATA-001`, `API-001` и т.н.;
- risk IDs: `RM-001` до `RM-025`;
- API fields: `schema`, `request_id`, `clinical`, `external_id`, `level` и др.;
- endpoint names: `/v1/reports/live`, `/v1/comparisons/levels`, `/v1/audit/live`.

Потребителските labels, README инструкциите, UI предупрежденията и validation wording могат и трябва да бъдат на български за локален клиничен/валидационен екип.

## Следваща Стъпка

Стъпка 8 трябва да създаде software architecture и verification planning artifacts, които да свържат requirements и risk controls с конкретни components, interfaces, tests, validation tasks и release criteria.
