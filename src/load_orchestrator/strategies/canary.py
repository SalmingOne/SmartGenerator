import time

from .base import IStrategy
from ..models import RawMetrics, Decision


class Canary(IStrategy):
    """
    Стратегия быстрой проверки (Canary/Smoke Test)

    TODO: Реализовать логику:
    - Быстро проверить что система вообще работает
    - Минимальная нагрузка (canary_users)
    - Короткий тест (canary_duration секунд)
    - Останавливаться если:
      * Есть критические ошибки (error_rate > threshold)
      * Прошло canary_duration времени и всё OK
    """

    def __init__(
        self,
        canary_users: int = 5,
        canary_duration: int = 30,  # секунд
        error_threshold: float = 1.0,  # 1% ошибок уже плохо для canary
    ):
        """
        Args:
            canary_users: Количество пользователей для проверки
            canary_duration: Длительность проверки (секунд)
            error_threshold: Порог ошибок для остановки (%)
        """
        self.canary_users = canary_users
        self.canary_duration = canary_duration
        self.error_threshold = error_threshold

        self._checks_done = 0
        self._started_at = None

    def decide(self, metrics: RawMetrics) -> Decision:
        """

        Логика:
        1. Если error_rate > error_threshold -> STOP (система не работает)
        2. Если p99 очень большой (> 5000ms) -> STOP (система тормозит)
        3. Если прошло достаточно времени и всё OK -> STOP (успешная проверка)
        4. Иначе -> HOLD (продолжаем проверку)
        """
        # На первом шаге всегда держим
        if self._checks_done == 0:
            self._started_at = time.time()
            self._checks_done += 1
            return Decision.HOLD


        if metrics.error_rate > self.error_threshold:
            return Decision.STOP
        if metrics.p99 > self.error_threshold:
            return Decision.STOP

        if time.time() - self._started_at > self.canary_duration:
            return Decision.STOP

        return Decision.HOLD

    def get_next_users(self, current_users: int, metrics: RawMetrics) -> int:
        """
        TODO: Вычислить следующее количество пользователей

        Всегда возвращать canary_users (фиксированная минимальная нагрузка)
        """
        return self.canary_users

    def get_wait_time(self) -> int:
        """
        Canary быстро проверяет систему

        Returns:
            5 секунд (быстрая проверка)
        """
        return self.canary_duration

    def reset(self) -> None:
        """TODO: Сбросить внутреннее состояние"""
        self._checks_done = 0
        self._started_at = None