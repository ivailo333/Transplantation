# HLA Transplantation Simulation

Неклиничен CLI/backend/frontend прототип за сравнение на HLA данни между донор и реципиент.

Проектът валидира и съхранява HLA типизации, изчислява детерминистични софтуерни сравнения през CANONICAL / LGX / G / P представяния, пази история на анализи и batch операции в SQLite и генерира matrix, summary, statistics, report и report-comparison изгледи.

Софтуерът е строго неклиничен. Той не изчислява трансплантационна съвместимост, клиничен риск, приоритет за алокация, virtual crossmatch, DSA, MFI, unacceptable antigens, cPRA, eplet mismatch, PIRCHE, кръвногрупова съвместимост, прогноза за graft outcome или трансплантационна пригодност.

## Изисквания

- Python 3.10 или по-нов
- `py-ard`
- Локални IPD-IMGT/HLA py-ard данни в `pyard-data/`

Инсталиране на runtime зависимости:

```powershell
python -m pip install -r requirements.txt
```

Инсталиране на FastAPI backend зависимости:

```powershell
python -m pip install -e .[api]
# или
python -m pip install -r requirements-api.txt
```

Копирайте `backend.env.example` като `backend.env` за локални backend настройки.

Инсталиране на development инструменти:

```powershell
python -m pip install -e .[dev]
```

## Бърз Старт

Проверка на състоянието на проекта:

```powershell
python .\main.py doctor
python .\main.py doctor --json
```

Проверка на базата и миграциите:

```powershell
python .\main.py db status
```

Списък със записани субекти:

```powershell
python .\main.py subjects list
```

Показване на неклиничен аналитичен отчет:

```powershell
python .\main.py report recipient RECIP-001
```

Сравнение на нива на представяне:

```powershell
python .\main.py compare levels recipient RECIP-001 --level canonical --level lgx
```

Сравнение на записани batch операции:

```powershell
python .\main.py compare batches 1 3
```

Експорт на отчети за браузър или всички поддържани формати:

```powershell
python .\main.py report recipient RECIP-001 --export html
python .\main.py compare levels recipient RECIP-001 --export html
python .\main.py report recipient RECIP-001 --export all
```

Създаване на възпроизводим audit bundle:

```powershell
python .\main.py audit recipient RECIP-001 --zip
python .\main.py audit batches 1 3 --level lgx
```

Показване на command-style help:

```powershell
python .\main.py --help
```

Стартиране на backend API компонента за по-голямо приложение:

```powershell
hla-api
# или
python -m backend_app
```

Стандартният API адрес е `http://127.0.0.1:8000`. Новите интеграции трябва да използват `/v1` endpoints. OpenAPI е достъпен на `/openapi.json`, а interactive docs са на `/docs`.

Проверка на backend компонента:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/v1/live
Invoke-RestMethod http://127.0.0.1:8000/v1/ready
```

Стартиране на неклиничния frontend validation прототип след като backend-ът работи:

```powershell
python .\frontend\serve.py
```

Отворете `http://127.0.0.1:4173/`.

Legacy flags като `--db-status`, `--list-subjects`, `--show-results` и `--export-analysis` остават поддържани за обратна съвместимост.

## Основни Команди

- `doctor`: изпълнява health checks без да променя данни; `--json` връща machine-readable output.
- `db status` / `db migrate`: проверява и прилага SQLite миграции.
- `subjects list`: показва записани DONOR / RECIPIENT субекти.
- `typings history/show/import`: преглежда или импортира HLA типизации.
- `analyses create/run/results/export`: управлява единичен donor-recipient анализ.
- `batch recipient|donor`: изпълнява one-to-many софтуерни сравнения.
- `batches list/search/show/results/export`: преглежда persistent batch история.
- `pairs`: показва one-pair comparison profiles.
- `matrix`: показва STEP 24 comparison matrices.
- `summary`: показва STEP 25 mismatch summaries.
- `stats`: показва STEP 26 descriptive statistics.
- `report`: генерира STEP 27 аналитични отчети.
- `compare`: генерира STEP 28 report comparisons.
- `audit`: създава възпроизводим bundle с doctor output, schema status, STEP 27/28 artifacts и metadata.

Използване на друга SQLite база с глобалната опция `--db PATH`:

```powershell
python .\main.py --db .\other.db report recipient RECIP-001
```

## Тестове

Пускане на целия unittest suite:

```powershell
python -m unittest discover -s tests
```

Ако `pytest` е инсталиран, project metadata също го насочва към `tests/`:

```powershell
python -m pytest
```

## Continuous Integration

GitHub Actions workflow-ът в `.github/workflows/ci.yml` се изпълнява на Windows и проверява:

- whitespace с `git diff --check`
- Python compilation с `compileall`
- целия unittest suite
- CLI smoke tests за `--help` и `doctor --json`
- FastAPI backend app и OpenAPI contract smoke test
- source и wheel builds с `python -m build`
- installed console-script metadata за `hla-match` и `hla-api`
- installed `hla-match` console script

## Packaging

Локално build-ване на release artifacts:

```powershell
python -m build
```

Проектът предоставя console scripts за CLI и API употреба:

```powershell
hla-match --help
hla-api
```

## Структура На Проекта

- `main.py`: минимална executable entry point точка.
- `cli.py`: legacy-compatible CLI entry и command-style routing.
- `command_cli.py`: command-style parser и dispatch.
- `backend_app.py`: FastAPI компонент за reports, comparisons, doctor checks и audit bundles.
- `backend_config.py` и `backend_services.py`: backend settings, `.env` loading, probes и service envelope слой.
- `frontend/`: static неклиничен validation UI прототип и локален API proxy.
- `Dockerfile` и `.dockerignore`: container runtime packaging за backend service.
- `config.py`: shared HLA loci, representation levels и data paths.
- `hla_validation.py`: py-ard initialization и allele validation.
- `hla_reduction.py`: CANONICAL към LGX / G / P reductions.
- `hla_comparison.py`: copy-sensitive multiset comparison.
- `database.py` и `migrations.py`: SQLite schema и migration helpers.
- `subjects.py` и `typings.py`: subject и typing persistence.
- `analyses.py`: analysis run и result persistence.
- `batch_*.py`: one-to-many batch execution, ranking, selection, export, history.
- `hla_matrix.py`, `mismatch_summary.py`, `comparison_statistics.py`: STEP 24-26 изгледи.
- `step27_reporting.py`: analytical report слой.
- `step28_report_comparison.py`: multi-report comparison слой.
- `tests/`: unittest покритие за CLI, persistence, import/export и STEP behavior.

## Документация

- [Backend API компонент](docs/backend.md)
- [Ръководство за backend интеграция](docs/backend-integration.md)
- [Български clinical readiness обзор](docs/clinical/bg-readiness-overview.md)
- [Проект на предназначение за употреба](docs/clinical/intended-use.md)
- [Проект на регулаторна класификация](docs/clinical/regulatory-classification.md)
- [Проект на система за качество](docs/clinical/quality-system.md)
- [Проект на управление на риска](docs/clinical/risk-register.md)
- [Проект на software lifecycle](docs/clinical/software-lifecycle.md)
- [Проект на frontend прототип](docs/clinical/frontend-prototype.md)
- [Проект на софтуерни изисквания](docs/clinical/software-requirements.md)
- [Проект на traceability matrix](docs/clinical/traceability-matrix.md)
- [Проект на software architecture](docs/clinical/software-architecture.md)
- [Проект на verification plan](docs/clinical/verification-plan.md)
- [Проект на usability engineering file](docs/clinical/usability-engineering.md)
- [Проект на validation plan](docs/clinical/validation-plan.md)
- [Проект на cybersecurity plan](docs/clinical/cybersecurity-plan.md)
- [Проект на data governance plan](docs/clinical/data-governance.md)
- [Проект на SOUP/dependency register](docs/clinical/soup-dependency-register.md)
- [Схема на базата данни](docs/schema.md)
- [Политика за данни](docs/data.md)

## Данни И Експорти

Стандартната SQLite база е `transplant.db`. Export командите записват под `exports/`, освен ако не е подадена друга output директория.

JSON, CSV и HTML export-ите са детерминистични софтуерни артефакти. `--export all` записва JSON, CSV и HTML заедно; `both` остава JSON + CSV за обратна съвместимост. Audit bundle-ите събират тези артефакти с doctor output, schema status и metadata за възпроизводимост, не за клинично вземане на решения.
