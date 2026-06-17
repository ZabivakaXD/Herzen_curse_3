"""Генерация статической документации из OpenAPI-спецификации (инструмент ReDoc).

Запуск:
    python generate_docs.py
или внутри контейнера:
    docker compose run --rm glossary python generate_docs.py
"""
import json
import os

from app.main import app

HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <style>body {{ margin: 0; }}</style>
</head>
<body>
  <div id="redoc"></div>
  <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
  <script>Redoc.init({spec}, {{}}, document.getElementById("redoc"));</script>
</body>
</html>
"""


def main():
    os.makedirs("docs", exist_ok=True)
    spec = app.openapi()
    with open("docs/openapi.json", "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(HTML.format(title=spec["info"]["title"], spec=json.dumps(spec, ensure_ascii=False)))
    print("Готово: docs/index.html и docs/openapi.json")


if __name__ == "__main__":
    main()
