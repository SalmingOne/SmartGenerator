from .base import IStrategy
from ..models import AnalyzedMetrics, Decision


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
        max_users: int,
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
        self.max_users = max_users
        self.initial_users = initial_users
        self.step_multiplier = step_multiplier

    def decide(self, metrics: AnalyzedMetrics) -> Decision:
        """
        TODO: Реализовать логику принятия решения

        Проверять SLA:
        1. Если p99 > max_p99 -> STOP (нарушили SLA по latency)
        2. Если error_rate > max_error_rate -> STOP (нарушили SLA по ошибкам)
        3. Если users >= max_users -> STOP (достигли лимита, SLA OK)
        4. Иначе -> INCREASE (продолжаем проверку)
        """
        return Decision.INCREASE

    def get_next_users(self, current_users: int, metrics: AnalyzedMetrics) -> int:
        """
        TODO: Вычислить следующее количество пользователей

        Не превышать max_users
        """
        if current_users == 0:
            return self.initial_users

        next_users = int(current_users * self.step_multiplier)
        return min(next_users, self.max_users)

    def reset(self) -> None:
        """TODO: Сбросить внутреннее состояние"""
        pass