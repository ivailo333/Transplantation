# Frontend Прототип

Статус: Draft за планиране на клинична готовност. Не е одобрен за клинична употреба.

Този документ описва началния неклиничен frontend прототип, добавен в стъпка 6. Прототипът е browser-based validation console за backend API компонента и не е production клиничен потребителски интерфейс.

## Изходни Документи

Вътрешни документи, използвани за този draft:

- [Intended Use](intended-use.md)
- [Regulatory Classification Draft](regulatory-classification.md)
- [Quality System Draft](quality-system.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Lifecycle Draft](software-lifecycle.md)
- [Backend API Component](../backend.md)
- [Backend Integration Guide](../backend-integration.md)
- [Data Policy](../data.md)

## Местоположение На Прототипа

Source файловете са в `frontend/`.

Ключови файлове:

- `frontend/index.html`: markup на validation console.
- `frontend/styles.css`: responsive operational UI styling.
- `frontend/app.js`: browser логика за backend API заявки и локални validation notes.
- `frontend/serve.py`: static development server и `/api/*` proxy към backend `/v1` endpoints.
- `frontend/README.md`: локални инструкции за стартиране.

## Обхват

Прототипът поддържа следния неклиничен workflow:

- backend liveness и readiness probes;
- въвеждане на donor-side или recipient-side case параметри;
- създаване на STEP 27 live report чрез `/v1/reports/live`;
- STEP 28 comparison между representation levels чрез `/v1/comparisons/levels`;
- създаване на reproducible live audit bundle чрез `/v1/audit/live`;
- преглед на raw JSON response;
- локални validation notes.

Прототипът е предназначен да помага на developers, technical evaluators и validation personnel да инспектират backend behavior по време на integration planning.

## Непредназначени Употреби

Прототипът не трябва да се използва за:

- клинично приемане или отхвърляне на донор;
- organ allocation, prioritization или waitlist decision-making;
- virtual crossmatch interpretation;
- DSA, MFI, unacceptable antigen, cPRA, eplet или PIRCHE interpretation;
- graft outcome prediction;
- treatment recommendation;
- autonomous или semi-autonomous clinical decision support;
- съхранение на clinical approval или final clinical sign-off.

Видимият UI съдържа неклинична status граница и умишлено държи clinical approval контрола disabled.

## Backend Зависимост

Прототипът зависи от наличен backend API компонент. Стандартният proxy target е:

```text
http://127.0.0.1:8000/v1
```

Target адресът може да се промени чрез `HLA_FRONTEND_BACKEND_URL`.

Локално стартиране:

```powershell
hla-api
python .\frontend\serve.py
```

Отваряне:

```text
http://127.0.0.1:4173/
```

## Safety И Claims Контроли

Прототипът включва начални контроли:

- explicit non-clinical labeling на първия екран;
- без persistence на clinical approval;
- disabled clinical-use approval button;
- local-only reviewer note storage;
- raw backend response panel за traceability по време на validation;
- same-origin frontend proxy, така че browser calls да не изискват отделна CORS конфигурация при локална оценка;
- без scoring, recommendation или acceptance/rejection language.

Тези контроли не са достатъчни за clinical release. Те са само planning и prototype controls.

## Usability Validation Notes

Бъдещата usability работа трябва да дефинира и тества user tasks преди да се разглежда клинична употреба. Начални candidate tasks:

- проверка на backend readiness преди преглед на случай;
- въвеждане на donor или recipient identifier и създаване на report;
- сравнение на representation levels и идентифициране къде deterministic software outputs се различават;
- създаване на audit bundle и потвърждение на file manifest;
- записване на validation observations без внушение за clinical approval.

Usability validation трябва да включва representative intended users, реалистични workflow constraints и документирани pass/fail criteria.

## Data Governance Notes

Прототипът е ограничен до synthetic, demo, anonymized или validation-planning записи. Всяка употреба с identifiable donor, recipient или patient data изисква approved governance process, access controls, retention rules, audit review и legal basis for processing преди въвеждане на данни в системата.

## Open Items Преди Клинична Употреба

Преди това да стане част от клиничен workflow, проектът все още има нужда поне от:

- formally approved intended use and claims;
- потвърдена regulatory classification;
- reviewed and baselined software requirements linked to risk controls;
- role-based authentication and authorization;
- validated audit trail and retention behavior;
- clinical workflow hazard analysis;
- cybersecurity risk assessment;
- usability engineering file и formative/summative validation;
- verification and validation protocol с objective acceptance criteria;
- production deployment architecture and operational procedures;
- approved release, change-control, incident и post-market processes.
