# Отчёт о развёртывании приложения «Счётчик»

Приложение: Flask (бэкенд) + Vue/Vite (фронтенд) + Redis (хранилище счётчика),
упаковано в Docker и оркестрируется через `docker compose`.

Содержание:
1. [Архитектура и бизнес-логика](#1-архитектура-и-бизнес-логика)
2. [Локальное развёртывание](#2-локальное-развёртывание)
3. [Развёртывание на Play with Docker](#3-развёртывание-на-play-with-docker)
4. [Удалённое развёртывание на сервере преподавателя](#4-удалённое-развёртывание-на-сервере-преподавателя)
5. [Тестирование и CI/CD](#5-тестирование-и-cicd)
6. [Что было изменено относительно исходного репозитория](#6-что-было-изменено-относительно-исходного-репозитория)

---

## 1. Архитектура и бизнес-логика

Сервис хранит одно значение `counter:value` в Redis и предоставляет REST API:

| Метод | Путь | Описание | Ответ |
|-------|------|----------|-------|
| GET  | `/api/counter`           | текущее значение           | `200 {"value": N}` |
| POST | `/api/counter/increment` | увеличить на 1             | `200 {"value": N}` |
| POST | `/api/counter/decrement` | уменьшить на 1             | `200 {"value": N}` или `400 {"error": ...}` |
| POST | `/api/counter/reset`     | сбросить в 0               | `200 {"value": 0}` |

Реализованные бизнес-правила:

1. **Счётчик не может быть меньше 0.**
2. При попытке уменьшить счётчик, равный 0:
   * сервер возвращает **HTTP 400**;
   * тело ответа — JSON `{"error": "Counter cannot be negative"}`.

Уменьшение реализовано атомарно через оптимистическую блокировку Redis
(`WATCH`/`MULTI`), поэтому при параллельных запросах счётчик не «проваливается»
ниже нуля. Логика вынесена в функцию `_decrement()` в `backend/app.py`, а
само приложение собирается фабрикой `create_app(redis_client=...)`, что
позволяет подменять Redis на `fakeredis` в тестах.

---

## 2. Локальное развёртывание

### Вариант А. Через Docker Compose (рекомендуется — близко к проду)

```bash
git clone <ссылка-на-форк>.git
cd counter-deploy

cp .env.example .env          # настройки compose (порт, имя проекта)
cp backend/.env.example backend/.env   # настройки приложения

docker compose up -d --build
```

Проверка:

```bash
curl http://localhost:8001/api/counter
# {"value": 0}

curl -X POST http://localhost:8001/api/counter/increment
# {"value": 1}

curl -X POST http://localhost:8001/api/counter/decrement
# {"value": 0}

curl -i -X POST http://localhost:8001/api/counter/decrement
# HTTP/1.1 400 BAD REQUEST
# {"error": "Counter cannot be negative"}
```

Веб-интерфейс открывается на `http://localhost:8001/` (порт берётся из
`APP_PORT` в корневом `.env`).

Остановка: `docker compose down` (с удалением данных — `docker compose down -v`).

### Вариант Б. Бэкенд без Docker (для разработки/тестов)

```bash
# Redis локально (в Docker для простоты)
docker run -d --name redis -p 6379:6379 redis:7-alpine

cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# приложение должно ходить в localhost, а не в контейнер `redis`
export REDIS_HOST=localhost
python app.py        # слушает :8000
```

### Результат локального запуска

* Контейнеры `app` и `redis` поднимаются и работают (`docker compose ps` → `Up`).
* Значение счётчика сохраняется между перезапусками контейнера благодаря
  тому `redis_data` (AOF-персистентность Redis).
* Все четыре endpoint'а отвечают согласно таблице выше, правило «не ниже 0»
  соблюдается.

---

## 3. Развёртывание на Play with Docker

[Play with Docker](https://labs.play-with-docker.com/) даёт временную
виртуальную машину с предустановленными Docker и docker compose.

Шаги:

1. Войти на https://labs.play-with-docker.com/ (нужен Docker Hub аккаунт),
   нажать **Start** → **ADD NEW INSTANCE**.
2. В терминале инстанса склонировать репозиторий и подготовить конфиги:

   ```bash
   git clone <ссылка-на-форк>.git
   cd counter-deploy
   cp .env.example .env
   cp backend/.env.example backend/.env
   ```

3. Поднять стек:

   ```bash
   docker compose up -d --build
   ```

4. Открыть приложение. PWD пробрасывает порты автоматически: вверху страницы
   появляется бейдж с номером порта. Если опубликован порт `8001`, нужно
   нажать кнопку **OPEN PORT** и ввести `8001`, либо в `.env` выставить
   `APP_PORT=80`, тогда ссылка с портом 80 появится в шапке сразу.

   > Совет для PWD: проще поставить `APP_PORT=80`, чтобы PWD сразу показал
   > кликабельную ссылку на приложение.

5. Проверить тем же `curl`, что и локально, либо кликнуть по ссылке порта и
   воспользоваться кнопками «+», «−», «Сброс» в UI.

Особенности PWD: сессия живёт ~4 часа и затем удаляется — это площадка для
демонстрации, а не для постоянного хостинга. Образы собираются прямо на
инстансе, внешний реестр не требуется.

---

## 4. Удалённое развёртывание на сервере преподавателя

На одном сервере разворачиваются приложения **многих студентов**, поэтому
параметры, которые могут конфликтовать, вынесены в переменные и у каждого
студента **свои**:

| Что | Где задаётся | Зачем уникально |
|-----|--------------|-----------------|
| Публикуемый порт `APP_PORT` | корневой `.env` / GitHub Variable | два сервиса не могут слушать один порт хоста |
| Имя проекта `COMPOSE_PROJECT_NAME` | корневой `.env` / GitHub Variable | префикс контейнеров, сети и тома — не пересекаются |
| Каталог деплоя `DEPLOY_PATH` | GitHub Secret | у каждого студента своя папка на сервере |
| Redis | внутри сети проекта, порт наружу не публикуется | исключает конфликт по 6379 |

Пример распределения: студент `ivanov` → `APP_PORT=8001`,
`COMPOSE_PROJECT_NAME=ivanov`, `DEPLOY_PATH=/srv/students/ivanov`; студент
`petrov` → `8002`, `petrov`, `/srv/students/petrov` и т.д.

### Ручной деплой (проверка перед настройкой CI)

```bash
ssh ivanov@<server-ip>
mkdir -p /srv/students/ivanov && cd /srv/students/ivanov
git clone <ссылка-на-форк>.git .

cat > .env <<EOF
COMPOSE_PROJECT_NAME=ivanov
APP_PORT=8001
EOF
cp backend/.env.example backend/.env

docker compose up -d --build
```

Приложение доступно на `http://<server-ip>:8001/`. Поскольку
`COMPOSE_PROJECT_NAME=ivanov`, контейнеры называются `ivanov-app-1`,
`ivanov-redis-1`, том — `ivanov_redis_data`, сеть — `ivanov_default`, и
ничего не пересекается со стеками других студентов.

Сетевые настройки: на сервере должен быть открыт выбранный порт (например,
8001) во внешнем firewall / security group; внутри `docker compose` ничего
дополнительно открывать не нужно.

---

## 5. Тестирование и CI/CD

### Тесты (pytest + fakeredis)

Тесты лежат в `backend/tests/test_counter.py`. Redis не запускается
по-настоящему — используется `fakeredis` (in-memory), что делает прогон
быстрым и независимым от окружения. Покрыты обязательные сценарии:

1. **Инициализация** — при первом запросе `GET /api/counter` возвращает 0.
2. **Увеличение** — после `POST /api/counter/increment` значение растёт на 1.
3. **Защита от отрицательных значений** — `POST /api/counter/decrement` при
   нуле возвращает `400` и `{"error": "Counter cannot be negative"}`,
   а значение в Redis остаётся 0.

Дополнительно проверяются корректное уменьшение при положительном значении и
сброс (`/reset`). Локальный запуск:

```bash
cd backend
pip install -r requirements.txt
pytest -v
# 5 passed
```

### CI/CD (GitHub Actions)

Файл `.github/workflows/deploy.yml`. Workflow:

* запускается при каждом `push` в `main`;
* состоит из двух job'ов: `test` и `deploy`, причём `deploy` объявлен с
  `needs: test`. Это и есть «прерывание деплоя, если хотя бы один тест не
  прошёл»: если `pytest` падает — job `test` краснеет, и `deploy` вообще не
  стартует.

Цепочка этапов:

```
checkout → setup python → install deps → run tests → deploy (rsync + docker compose)
```

Реальный деплой — `rsync` каталога на сервер с последующим
`docker compose up -d --build` по SSH.

Необходимые **Secrets** репозитория:
`SSH_PRIVATE_KEY`, `SSH_KNOWN_HOSTS`, `SERVER_USER`, `SERVER_IP`, `DEPLOY_PATH`.

Необходимые **Variables** репозитория (у каждого студента свои):
`APP_PORT`, `COMPOSE_PROJECT_NAME`.

---

## 6. Что было изменено относительно исходного репозитория

* `backend/app.py` — добавлено правило «счётчик ≥ 0» с ответом `400`,
  атомарный `_decrement`, фабрика `create_app()` для тестируемости.
* `backend/redis_client.py` — **новый** модуль подключения к Redis с ретраями.
* `backend/tests/test_counter.py` — **новые** тесты на `pytest` + `fakeredis`.
* `backend/requirements.txt` — добавлены `pytest`, `fakeredis`.
* `backend/pytest.ini` — **новый** конфиг тестов.
* `.github/workflows/deploy.yml` — добавлен job `test`, деплой через
  `needs: test` (блокировка при падении тестов).
* `docker-compose.yml` — публикуемый порт через `${APP_PORT}`, изоляция
  стеков по `COMPOSE_PROJECT_NAME`, Redis больше не публикует порт наружу.
* `.env.example` (корень) — **новый** файл с пер-студенческими переменными
  compose (`APP_PORT`, `COMPOSE_PROJECT_NAME`).
