# Frontend Прототип

Статус: Неклиничен validation прототип. Не е одобрен за клинична употреба.

Тази директория съдържа browser прототип без външни зависимости за преглед на backend API компонента по време на integration planning. Предназначен е само за synthetic, demo, anonymized или validation-planning данни.

Първо стартирайте backend-а:

```powershell
hla-api
```

След това стартирайте frontend proxy-то:

```powershell
python .\frontend\serve.py
```

Отворете `http://127.0.0.1:4173/`.

Frontend server-ът обслужва static файлове от тази директория и proxy-ва `/api/*` заявки към backend `/v1` API. Backend адресът може да се промени с `HLA_FRONTEND_BACKEND_URL`, например:

```powershell
$env:HLA_FRONTEND_BACKEND_URL = "http://127.0.0.1:8000/v1"
python .\frontend\serve.py
```
