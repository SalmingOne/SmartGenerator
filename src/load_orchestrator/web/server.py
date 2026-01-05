"""
FastAPI сервер для Web UI

TODO: Реализовать:
1. Создать FastAPI app
2. Подключить API router (из api.py)
3. Подключить WebSocket handler (из websocket.py)
4. Настроить static files (static/)
5. Создать функцию run_server(port, config_path)
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path


def create_app() -> FastAPI:
    """
    TODO: Создать FastAPI приложение

    - app = FastAPI(title="Load Orchestrator")
    - app.include_router(api_router)  # из api.py
    - app.mount("/static", StaticFiles(...), name="static")
    - app.add_api_websocket_route("/ws/metrics", websocket_endpoint)
    """
    app = FastAPI(title="Load Orchestrator")
    # TODO: Добавить роутеры
    return app


def run_server(port: int = 8080, config_path: str | None = None):
    """
    TODO: Запустить сервер

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
    """
    pass