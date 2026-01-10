"""
Locust файл для тестирования на httpbin.org
Это самый стабильный публичный сервис для нагрузочного тестирования
Держит ОЧЕНЬ большую нагрузку без проблем
"""
import random
import time
from locust import HttpUser, task, constant_pacing, between


class FastUser(HttpUser):
    """
    Быстрый пользователь - простые GET запросы
    Можно масштабировать до 5000+ пользователей
    """
    host = "https://httpbin.org"
    wait_time = constant_pacing(0.5)  # 2 RPS per user
    weight = 5

    @task(10)
    def get_request(self):
        """Простой GET"""
        self.client.get("/get", name="GET /get")

    @task(5)
    def get_with_params(self):
        """GET с параметрами"""
        params = {
            'param1': random.randint(1, 1000),
            'param2': f'test_{random.randint(1, 100)}'
        }
        self.client.get("/get", params=params, name="GET /get?params")

    @task(3)
    def get_status(self):
        """GET со случайным статусом"""
        status = random.choice([200, 201, 400, 404, 500])
        self.client.get(f"/status/{status}", name="GET /status/[code]")


class MediumUser(HttpUser):
    """
    Средний пользователь - POST/PUT запросы
    """
    host = "https://httpbin.org"
    wait_time = constant_pacing(1)  # 1 RPS per user
    weight = 3

    @task(5)
    def post_json(self):
        """POST с JSON"""
        payload = {
            'test': f'data_{random.randint(1000, 9999)}',
            'value': random.randint(1, 100),
            'data': 'x' * 100  # 100 символов
        }
        self.client.post("/post", json=payload, name="POST /post")

    @task(3)
    def put_request(self):
        """PUT запрос"""
        payload = {
            'id': random.randint(1, 1000),
            'updated': True,
            'data': 'y' * 200
        }
        self.client.put("/put", json=payload, name="PUT /put")

    @task(2)
    def delete_request(self):
        """DELETE запрос"""
        self.client.delete("/delete", name="DELETE /delete")


class HeavyUser(HttpUser):
    """
    Тяжелый пользователь - большие payload и задержки
    """
    host = "https://httpbin.org"
    wait_time = constant_pacing(2)  # 0.5 RPS per user
    weight = 2

    @task(5)
    def delay_request(self):
        """Запрос с задержкой на сервере"""
        delay = random.uniform(0.5, 2)
        with self.client.get(f"/delay/{delay:.1f}", name="GET /delay/[seconds]", catch_response=True) as response:
            if response.elapsed.total_seconds() < 10:
                response.success()

    @task(3)
    def large_post(self):
        """POST с большим payload"""
        payload = {
            'data': 'x' * 10000,  # 10KB
            'id': random.randint(10000, 99999),
            'items': [f'item_{i}' for i in range(100)]
        }
        self.client.post("/post", json=payload, name="POST /post (large)")

    @task(2)
    def multiple_operations(self):
        """Несколько операций подряд"""
        # GET
        self.client.get("/get", name="GET /get (chain)")

        # POST
        payload = {'data': 'chain_test', 'value': random.randint(1, 100)}
        self.client.post("/post", json=payload, name="POST /post (chain)")

        # PUT
        self.client.put("/put", json=payload, name="PUT /put (chain)")

        # DELETE
        self.client.delete("/delete", name="DELETE /delete (chain)")


class StressUser(HttpUser):
    """
    Стресс-пользователь - максимальная нагрузка
    Включите для экстремального теста
    """
    host = "https://httpbin.org"
    wait_time = constant_pacing(0.2)  # 5 RPS per user
    weight = 0  # Отключен, установите > 0 для включения

    @task(10)
    def rapid_gets(self):
        """Быстрые GET запросы"""
        for i in range(5):
            self.client.get("/get", name="GET /get (rapid)")

    @task(5)
    def rapid_posts(self):
        """Быстрые POST запросы"""
        for i in range(3):
            payload = {
                'rapid': i,
                'data': f'rapid_{random.randint(100000, 999999)}'
            }
            self.client.post("/post", json=payload, name="POST /post (rapid)")

    @task(3)
    def stream_test(self):
        """Тест streaming"""
        n = random.randint(10, 50)
        self.client.get(f"/stream/{n}", name="GET /stream/[n]")