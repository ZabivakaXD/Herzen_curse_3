# counter-deploy

Учебное приложение «Счётчик»: **Flask** (бэкенд) + **Vue/Vite** (фронтенд) +
**Redis** (хранилище), упаковано в **Docker** и оркестрируется через
`docker compose`.

📄 Полный отчёт о развёртывании (локально / Play with Docker / удалённый сервер
/ CI/CD) — в [**REPORT.md**](./REPORT.md).

## Быстрый старт (локально)

```bash
cp .env.example .env                    # порт и имя проекта (свои у каждого студента)
cp backend/.env.example backend/.env    # настройки приложения
docker compose up -d --build
curl http://localhost:8001/api/counter  # {"value": 0}
```

UI: `http://localhost:8001/` (порт задаётся `APP_PORT` в `.env`).

## API

| Метод | Путь | Ответ |
|-------|------|-------|
| GET  | `/api/counter`           | `200 {"value": N}` |
| POST | `/api/counter/increment` | `200 {"value": N}` |
| POST | `/api/counter/decrement` | `200 {"value": N}` или `400 {"error": "Counter cannot be negative"}` |
| POST | `/api/counter/reset`     | `200 {"value": 0}` |

Бизнес-правило: счётчик не может быть меньше 0 — при попытке уменьшить 0
возвращается `400` и JSON с ошибкой.

## Тесты

```bash
cd backend
pip install -r requirements.txt
pytest -v        # 5 passed (использует fakeredis, реальный Redis не нужен)
```

## CI/CD

`.github/workflows/deploy.yml`: при `push` в `main` запускаются тесты, и
только при их успехе выполняется деплой (`rsync` + `docker compose up`) —
см. REPORT.md, раздел 5.
