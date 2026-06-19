# Лабораторная работа №7. Деплой приложения на Flask с БД Redis

## Задание

1. Регистрация в sourcecraft.dev: используйте учетную запись Yandex. 

2. Создание организации (организация должна быть публичной). 

3. Создание репозитория (должен быть публичным). 

4. Создать токены/ключи для работы посредством https и/или ssh:

https://sourcecraft.dev/portal/docs/en/sourcecraft/security/pat
https://sourcecraft.dev/portal/docs/en/sourcecraft/security/ssh
 5. Клонировать репозиторий и запушить в сурскрафт основу для построения статического сайта (пример репозитория). 

Инструкция от самого Yandex https://sourcecraft.dev/portal/docs/ru/sourcecraft/tutorials/sites



Реализовать CI/CD-процесс публикации сайта на Hugo с использованием DevOps-платформы Sourcecraft:

1. Переписать существующий пайплайн на основе среды SourceCraft

2. Дополнить сценарии проверками синтаксиса Markdown (в виде отдельных шагов).

## Решение:

Базовый сайт на Hugo для SourceCraft
Ссылка на SourceCraft: https://sourcecraft.dev/zabivakaxd/lab-1-sem-6?rev=main

Минимальный сайт на Hugo **без внешней темы** — собирается «из коробки», без git-сабмодулей. Готов к публикации через CI/CD SourceCraft.

## Структура

- `content/` — Markdown-контент (страницы и записи блога)
- `layouts/` — HTML-шаблоны (своя мини-тема)
- `static/css/` — стили
- `hugo.toml` — конфигурация Hugo
- `.sourcecraft/ci.yaml` — пайплайн: проверки Markdown, сборка, публикация
- `.sourcecraft/sites.yaml` — откуда SourceCraft Sites отдаёт сайт (ветка `release`)
- `.markdownlint-cli2.yaml` — правила проверки Markdown

Проверка:

![1.png](https://github.com/ZabivakaXD/Herzen_curse_3/blob/main/prog/lab-8/img/1.png)

![2.png](https://github.com/ZabivakaXD/Herzen_curse_3/blob/main/prog/lab-8/img/2.png)