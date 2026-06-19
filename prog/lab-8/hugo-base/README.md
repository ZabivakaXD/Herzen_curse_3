# Базовый сайт на Hugo для SourceCraft

Минимальный сайт на Hugo **без внешней темы** — собирается «из коробки»,
без git-сабмодулей. Готов к публикации через CI/CD SourceCraft.

## Структура

- `content/` — Markdown-контент (страницы и записи блога)
- `layouts/` — HTML-шаблоны (своя мини-тема)
- `static/css/` — стили
- `hugo.toml` — конфигурация Hugo
- `.sourcecraft/ci.yaml` — пайплайн: проверки Markdown, сборка, публикация
- `.sourcecraft/sites.yaml` — откуда SourceCraft Sites отдаёт сайт (ветка `release`)
- `.markdownlint-cli2.yaml` — правила проверки Markdown

## Что поправить под себя

1. В `hugo.toml` замените `EXAMPLE` на слаг организации, а `my-site` — на имя репозитория.
2. В `.sourcecraft/ci.yaml` укажите свои `ORG` и `REPO`.
3. Добавьте секрет `SC_TOKEN` (ваш PAT) в настройках репозитория.

## Локальный запуск

```bash
hugo server          # http://localhost:1313
hugo --gc --minify   # сборка в каталог public/
```

## Локальная проверка Markdown

```bash
npm install -g markdownlint-cli2 remark-cli remark-preset-lint-recommended
markdownlint-cli2 "content/**/*.md" "*.md"
remark --frail --use remark-preset-lint-recommended content/
```
