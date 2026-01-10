from .base import IStrategy
from ..models import RawMetrics, Decision


class SLAValidation(IStrategy):
    """
    Стратегия проверки соответствия SLA

    TODO: Реализовать логику:
    - Постепенно увеличивать нагрузку
    - Проверять что система соответствует SLA:
      * P99 < max_p99
      * error_rate < max_error_rate
    - Останавливаться если:
      * Нарушили SLA
      * Или достигли max_users без нарушений
    """

    def __init__(
        self,
        max_p99: float,  # в миллисекундах
        max_error_rate: float,  # в процентах
        initial_users: int = 10,
        step_multiplier: float = 1.5,
    ):
        """
        Args:
            max_p99: Максимально допустимый P99 (мс)
            max_error_rate: Максимально допустимый уровень ошибок (%)
            max_users: Максимальное количество пользователей для проверки
            initial_users: Начальное количество пользователей
            step_multiplier: Множитель для увеличения нагрузки
        """
        self.max_p99 = max_p99
        self.max_error_rate = max_error_rate
        self.initial_users = initial_users
        self.step_multiplier = step_multiplier

    def decide(self, metrics: RawMetrics) -> Decision:
        """
        Принять решение о следующем шаге

        Проверяет соответствие SLA:
        - P99 превышает лимит
        - Error rate превышает лимит
        - Достигнут max_users (успешная валидация)
        """
        # Проверка нарушения P99
        if metrics.p99 > self.max_p99:
            print(f"⚠️  SLA violation: P99={metrics.p99:.0f}ms > {self.max_p99}ms")
            return Decision.STOP

        # Проверка нарушения error rate
        if metrics.error_rate > self.max_error_rate:
            print(f"⚠️  SLA violation: error_rate={metrics.error_rate:.2f}% > {self.max_error_rate}%")
            return Decision.STOP

        return Decision.CONTINUE

    def get_next_users(self, current_users: int, metrics: RawMetrics) -> int:
        """
        TODO: Вычислить следующее количество пользователей

        Не превышать max_users
        """
        if current_users == 0:
            return self.initial_users

        next_users = int(current_users * self.step_multiplier)
        return next_users

    def reset(self) -> None:
        """TODO: Сбросить внутреннее состояние"""
        pass