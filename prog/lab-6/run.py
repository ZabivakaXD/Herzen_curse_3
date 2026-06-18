"""Точка входа для локального запуска сервера.

Примеры:
    python run.py                 # реальный API ЦБ, опрос раз в 5 минут
    SIMULATE=1 POLL_INTERVAL=5 python run.py   # демо: колебания раз в 5 сек

Затем откройте http://127.0.0.1:8000 в нескольких вкладках —
каждая получит свой идентификатор клиента.
"""

from __future__ import annotations

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=False)
