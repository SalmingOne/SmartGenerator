from .base import IStrategy
from ..models import RawMetrics, Decision


class BreakPoint(IStrategy):
    """
    Стратегия поиска точки отказа системы

    TODO: Реализовать логику:
    - Агрессивно увеличивать нагрузку до полного отказа
    - Останавливаться когда:
      * error_rate > 10% (система начала масмсово отказывать)
      * RPS падает до 0 (система перестала отвечать)
      * P99 становится экстремально большим (> 10 секунд)
    """

    def __init__(
        self,
        initial_users: int = 10,
        step_multiplier: float = 2.0,  # Более агрессивный рост
        error_threshold: float = 10.0,  # 10% ошибок
    ):
        """
        Args:
            initial_users: Начальное количество пользователей
            step_multiplier: Множитель для увеличения нагрузки (агрессивнее чем degradation)
            error_threshold: Порог ошибок для остановки (в процентах)
        """
        self.initial_users = initial_users
        self.step_multiplier = step_multiplier
        self.error_threshold = error_threshold
        self.previous_metrics: RawMetrics = RawMetrics(
            timestamp=0,
            users=0,
            rps=0,
            rt_avg=0,
            p50=0,
            p95=0,
            p99=0,
            failed_requests=0,
            error_rate=0,
            total_requests=0,
        )

    def decide(self, metrics: RawMetrics) -> Decision:
        """
        Принять решение о следующем шаге

        Проверяет критические условия для поиска точки отказа:
        - error_rate >= error_threshold
        - RPS == 0 (система не отвечает)
        - P99 > 10 секунд (экстремальная латентность)
        - Падение RPS на 50% (требует previous_metrics)
        """
        # Проверка критического уровня ошибок
        if metrics.error_rate >= self.error_threshold:
            print(f"⚠️  Critical error rate: {metrics.error_rate:.2f}%")
            return Decision.STOP

        # Система перестала отвечать
        if metrics.rps == 0 and metrics.users > 0:
            print("⚠️  System stopped responding")
            return Decision.STOP

        # Экстремальная латентность
        if metrics.p99 > 10000:  # 10 секунд
            print(f"⚠️  Extreme latency: {metrics.p99:.0f}ms")
            return Decision.STOP

        # Проверка падения RPS (требует previous_metrics)
        if self.previous_metrics.rps > 0 and metrics.rps < self.previous_metrics.rps * 0.5:
            print(f"⚠️  RPS dropped by 50%: {self.previous_metrics.rps:.1f} → {metrics.rps:.1f}")
            self.previous_metrics = metrics
            return Decision.STOP

        self.previous_metrics = metrics
        return Decision.CONTINUE

    def get_next_users(self, current_users: int, metrics: RawMetrics) -> int:
        """
        TODO: Вычислить следующее количество пользователей

        Логика: агрессивное увеличение (например, x2 каждый раз)
        """
        if current_users == 0:
            return self.initial_users
        return int(current_users * self.step_multiplier)

    def reset(self) -> None:
        """TODO: Сбросить внутреннее состояние"""
        pass