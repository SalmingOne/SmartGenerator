"""
FastAPI сервер для Web UI

TODO: Реализовать:
1. ✓ Создать FastAPI app
2. TODO: Подключить API router (из api.py)
3. TODO: Подключить WebSocket handler (из websocket.py)
4. ✓ Настроить static files (static/)
5. ✓ Создать функцию run_server(port, config_path)
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path


# Путь к директории web
WEB_DIR = Path(__file__).parent
STATIC_DIR = WEB_DIR / "static"


def create_app() -> FastAPI:
    """
    Создать FastAPI приложение

    - app = FastAPI(title="Load Orchestrator")
    - app.include_router(api_router)  # TODO: из api.py
    - app.mount("/static", StaticFiles(...), name="static")
    - app.add_api_websocket_route("/ws/metrics", websocket_endpoint)  # TODO
    """
    app = FastAPI(title="Load Orchestrator")

    # Роут для главной страницы (ВАЖНО: до mount!)
    @app.get("/")
    async def read_index():
        """Отдать index.html на главной странице"""
        return FileResponse(STATIC_DIR / "index.html")

    # TODO: Добавить API роутеры
    # app.include_router(api_router, prefix="/api")

    # TODO: Добавить WebSocket
    # app.add_api_websocket_route("/ws/metrics", websocket_endpoint)

    # Смонтировать static файлы (CSS, JS, images)
    # ВАЖНО: mount должен быть ПОСЛЕДНИМ, иначе перехватывает все запросы
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return app


def run_server(port: int = 8080, config_path: str | None = None):
    """
    Запустить сервер

    Args:
        port: Порт для запуска (по умолчанию 8080)
        config_path: Путь к конфигу (опционально, для будущего использования)
    """
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=port)