"""
WebSocket handler для live метрик

TODO: Реализовать:
1. Подключение клиентов к WebSocket
2. Broadcast метрик всем подключенным клиентам
3. Типы сообщений:
   - "metrics" - новые метрики
   - "status" - изменение статуса (started, stopped)
   - "decision" - решение стратегии
   - "result" - тест завершен

Пример использования в server.py:
@app.websocket("/ws/metrics")
async def websocket_endpoint(websocket: WebSocket):
    await handle_websocket(websocket)
"""

from fastapi import WebSocket
import json


class ConnectionManager:
    """
    TODO: Менеджер WebSocket подключений

    - Хранить список активных подключений
    - Метод connect(websocket) - добавить подключение
    - Метод disconnect(websocket) - удалить подключение
    - Метод broadcast(data) - отправить всем
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """TODO: Принять подключение"""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """TODO: Удалить подключение"""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """
        TODO: Отправить сообщение всем клиентам

        for connection in self.active_connections:
            await connection.send_json(message)
        """
        pass


manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket):
    """
    TODO: Обработать WebSocket подключение

    await manager.connect(websocket)
    try:
        while True:
            # Можно получать сообщения от клиента
            data = await websocket.receive_text()
            # Или просто держать соединение открытым
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    """
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        manager.disconnect(websocket)


async def send_metrics_update(metrics: dict):
    """
    TODO: Отправить обновление метрик всем клиентам

    await manager.broadcast({
        "type": "metrics",
        "payload": metrics
    })
    """
    pass


async def send_status_update(status: dict):
    """TODO: Отправить обновление статуса"""
    pass


async def send_result(result: dict):
    """TODO: Отправить результат теста"""
    pass