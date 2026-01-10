"""
Demo Locust файл для тестирования стратегий на публичном API
Используется JSONPlaceholder - fake REST API (jsonplaceholder.typicode.com)

Этот API хорошо держит нагрузку и идеален для демонстрации работы стратегий.
Можно увеличить нагрузку до 1000+ пользователей без проблем.
"""
import random
import time
from locust import HttpUser, task, between, constant_pacing


class LightUser(HttpUser):
    """
    Легкий пользователь - только GET запросы
    RPS: ~2-3 на пользователя
    Отлично масштабируется, минимальная деградация
    """
    host = "https://jsonplaceholder.typicode.com"
    wait_time = constant_pacing(0.5)  # 2 RPS per user
    weight = 5  # 50% от общего числа пользователей

    @task(10)
    def get_posts(self):
        """Получить список постов"""
        self.client.get("/posts", name="GET /posts")

    @task(8)
    def get_single_post(self):
        """Получить конкретный пост"""
        post_id = random.randint(1, 100)
        self.client.get(f"/posts/{post_id}", name="GET /posts/[id]")

    @task(5)
    def get_comments(self):
        """Получить комментарии к посту"""
        post_id = random.randint(1, 100)
        self.client.get(f"/posts/{post_id}/comments", name="GET /posts/[id]/comments")

    @task(3)
    def get_users(self):
        """Получить пользователей"""
        self.client.get("/users", name="GET /users")

    @task(2)
    def get_albums(self):
        """Получить альбомы"""
        self.client.get("/albums", name="GET /albums")


class MediumUser(HttpUser):
    """
    Средний пользователь - микс GET и POST запросов
    RPS: ~1-2 на пользователя
    POST создает больше нагрузки чем GET
    """
    host = "https://jsonplaceholder.typicode.com"
    wait_time = constant_pacing(1)  # 1 RPS per user
    weight = 3  # 30% от общего числа

    @task(5)
    def get_posts(self):
        """GET запрос"""
        self.client.get("/posts", name="GET /posts")

    @task(4)
    def create_post(self):
        """POST запрос - создание поста"""
        payload = {
            'title': f'Load Test Post {random.randint(1000, 9999)}',
            'body': 'This is a load test post. ' * random.randint(5, 15),
            'userId': random.randint(1, 10)
        }
        self.client.post("/posts", json=payload, name="POST /posts")

    @task(3)
    def update_post(self):
        """PUT запрос - обновление поста"""
        post_id = random.randint(1, 100)
        payload = {
            'id': post_id,
            'title': f'Updated Post {random.randint(1000, 9999)}',
            'body': 'Updated body. ' * random.randint(10, 20),
            'userId': random.randint(1, 10)
        }
        self.client.put(f"/posts/{post_id}", json=payload, name="PUT /posts/[id]")

    @task(2)
    def create_comment(self):
        """POST запрос - создание комментария"""
        post_id = random.randint(1, 100)
        payload = {
            'postId': post_id,
            'name': f'Commenter {random.randint(1000, 9999)}',
            'email': f'user{random.randint(1000, 9999)}@test.com',
            'body': 'This is a test comment. ' * random.randint(3, 8)
        }
        self.client.post("/comments", json=payload, name="POST /comments")


class HeavyUser(HttpUser):
    """
    Тяжелый пользователь - интенсивные операции с большими payload
    RPS: ~0.5-1 на пользователя
    Создает значительную нагрузку, хорошо показывает деградацию
    """
    host = "https://jsonplaceholder.typicode.com"
    wait_time = constant_pacing(1.5)  # ~0.66 RPS per user
    weight = 2  # 20% от общего числа

    @task(5)
    def heavy_post_creation(self):
        """Создание поста с большим телом"""
        payload = {
            'title': f'Heavy Load Test Post {random.randint(10000, 99999)}',
            'body': 'Lorem ipsum dolor sit amet. ' * 100,  # Большой payload
            'userId': random.randint(1, 10)
        }
        self.client.post("/posts", json=payload, name="POST /posts (heavy)")

    @task(4)
    def multiple_operations(self):
        """Несколько операций подряд"""
        # GET
        post_id = random.randint(1, 100)
        self.client.get(f"/posts/{post_id}", name="GET /posts/[id] (chain)")

        # POST
        payload = {
            'title': f'Chained Post {random.randint(10000, 99999)}',
            'body': 'Chained operation. ' * 50,
            'userId': random.randint(1, 10)
        }
        response = self.client.post("/posts", json=payload, name="POST /posts (chain)")

        # PUT - обновить только что созданный пост
        if response.status_code == 201:
            created_id = response.json().get('id', random.randint(1, 100))
            payload['title'] = f'Updated Chained Post {random.randint(10000, 99999)}'
            self.client.put(f"/posts/{created_id}", json=payload, name="PUT /posts/[id] (chain)")

    @task(3)
    def bulk_comments(self):
        """Создание нескольких комментариев"""
        post_id = random.randint(1, 100)

        for i in range(5):
            payload = {
                'postId': post_id,
                'name': f'Bulk Commenter {i} - {random.randint(10000, 99999)}',
                'email': f'bulkuser{random.randint(10000, 99999)}@test.com',
                'body': 'This is a bulk comment with more text. ' * 20
            }
            self.client.post("/comments", json=payload, name="POST /comments (bulk)")

    @task(2)
    def full_crud_cycle(self):
        """Полный CRUD цикл"""
        # CREATE
        create_payload = {
            'title': f'CRUD Test {random.randint(10000, 99999)}',
            'body': 'CRUD cycle test. ' * 30,
            'userId': random.randint(1, 10)
        }
        response = self.client.post("/posts", json=create_payload, name="POST /posts (CRUD)")

        if response.status_code == 201:
            post_id = response.json().get('id', random.randint(1, 100))

            # READ
            self.client.get(f"/posts/{post_id}", name="GET /posts/[id] (CRUD)")

            # UPDATE
            update_payload = {
                'id': post_id,
                'title': f'Updated CRUD Test {random.randint(10000, 99999)}',
                'body': 'Updated CRUD cycle test. ' * 40,
                'userId': random.randint(1, 10)
            }
            self.client.put(f"/posts/{post_id}", json=update_payload, name="PUT /posts/[id] (CRUD)")

            # DELETE
            self.client.delete(f"/posts/{post_id}", name="DELETE /posts/[id] (CRUD)")


class ExtremeUser(HttpUser):
    """
    Экстремальный пользователь - максимальная нагрузка
    RPS: ~3-5 на пользователя
    Используйте для поиска точки полного отказа системы
    """
    host = "https://jsonplaceholder.typicode.com"
    wait_time = constant_pacing(0.2)  # 5 RPS per user
    weight = 0  # Отключен по умолчанию, установите weight > 0 для включения

    @task(10)
    def rapid_fire_posts(self):
        """Быстрые POST запросы"""
        for i in range(3):
            payload = {
                'title': f'Rapid {i} - {random.randint(100000, 999999)}',
                'body': 'Rapid fire. ' * 50,
                'userId': random.randint(1, 10)
            }
            self.client.post("/posts", json=payload, name="POST /posts (rapid)")

    @task(8)
    def concurrent_reads(self):
        """Множественные GET запросы"""
        endpoints = ["/posts", "/comments", "/albums", "/users", "/todos"]
        for endpoint in random.sample(endpoints, 3):
            self.client.get(endpoint, name=f"GET {endpoint} (concurrent)")

    @task(5)
    def stress_comments(self):
        """Стресс-тест комментариев"""
        post_id = random.randint(1, 100)

        # Создать 10 комментариев подряд
        for i in range(10):
            payload = {
                'postId': post_id,
                'name': f'Stress {i}',
                'email': f'stress{i}@test.com',
                'body': f'Stress comment {i}. ' * 30
            }
            self.client.post("/comments", json=payload, name="POST /comments (stress)")


class MixedRealisticUser(HttpUser):
    """
    Реалистичный микс пользователя - имитирует реальное поведение
    80% читает, 20% пишет
    Полезен для тестирования реалистичных сценариев
    """
    host = "https://jsonplaceholder.typicode.com"
    wait_time = between(0.5, 2)  # Вариативное время между запросами
    weight = 0  # Отключен, включите для реалистичного теста

    @task(40)
    def browse_posts(self):
        """Просмотр постов (самая частая операция)"""
        if random.random() < 0.7:
            # 70% - список постов
            self.client.get("/posts", name="GET /posts")
        else:
            # 30% - конкретный пост
            post_id = random.randint(1, 100)
            self.client.get(f"/posts/{post_id}", name="GET /posts/[id]")

    @task(20)
    def browse_comments(self):
        """Чтение комментариев"""
        post_id = random.randint(1, 100)
        self.client.get(f"/posts/{post_id}/comments", name="GET /posts/[id]/comments")

    @task(5)
    def create_content(self):
        """Создание контента (редкая операция)"""
        payload = {
            'title': f'User Post {random.randint(1000, 9999)}',
            'body': 'User generated content. ' * random.randint(5, 15),
            'userId': random.randint(1, 10)
        }
        self.client.post("/posts", json=payload, name="POST /posts")

    @task(3)
    def interact_comment(self):
        """Добавление комментария (еще реже)"""
        post_id = random.randint(1, 100)
        payload = {
            'postId': post_id,
            'name': f'User {random.randint(1000, 9999)}',
            'email': f'user{random.randint(1000, 9999)}@example.com',
            'body': 'User comment. ' * random.randint(3, 8)
        }
        self.client.post("/comments", json=payload, name="POST /comments")

    @task(2)
    def check_users(self):
        """Просмотр пользователей (редко)"""
        self.client.get("/users", name="GET /users")