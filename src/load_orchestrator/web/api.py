"""
REST API endpoints

TODO: Реализовать endpoints:

GET  /api/status         - Текущий статус (init/running/finished)
GET  /api/config         - Текущая конфигурация
POST /api/config         - Обновить конфигурацию
POST /api/start          - Запустить тест
POST /api/stop           - Остановить тест
GET  /api/metrics        - Текущие метрики
GET  /api/history        - История всех замеров
GET  /api/result         - Результат теста
GET  /api/strategies     - Список доступных стратегий
GET  /api/adapters       - Список доступных адаптеров
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/status")
async def get_status():
    """
    TODO: Вернуть текущий статус оркестратора

    return {
        "state": "running",  # init, running, finished
        "current_step": 8,
        "current_users": 150,
        "elapsed_time": 245.5
    }
    """
    return {"state": "init"}


@router.get("/config")
async def get_config():
    """TODO: Вернуть текущую конфигурацию"""
    return {}


@router.post("/config")
async def update_config(config: dict):
    """TODO: Обновить конфигурацию"""
    return {"status": "ok"}


@router.post("/start")
async def start_test():
    """TODO: Запустить тест в background"""
    return {"status": "started"}


@router.post("/stop")
async def stop_test():
    """TODO: Остановить тест"""
    return {"status": "stopped"}


@router.get("/metrics")
async def get_metrics():
    """
    TODO: Вернуть текущие метрики

    return {
        "timestamp": ...,
        "raw": {...},
        "analyzed": {...},
        "decision": "INCREASE"
    }
    """
    return {}


@router.get("/history")
async def get_history():
    """TODO: Вернуть историю всех замеров"""
    return []


@router.get("/result")
async def get_result():
    """TODO: Вернуть результат теста"""
    return {}


@router.get("/strategies")
async def list_strategies():
    """
    TODO: Вернуть список доступных стратегий

    return [
        {
            "type": "degradation_search",
            "name": "Degradation Search",
            "description": "Найти точку деградации"
        },
        ...
    ]
    """
    return []


@router.get("/adapters")
async def list_adapters():
    """TODO: Вернуть список доступных адаптеров"""
    return [
        {"type": "locust", "name": "Locust"}
    ]