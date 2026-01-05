from .base import IStrategy
from ..models import AnalyzedMetrics, Decision


class DegradationSearch(IStrategy):
    """
    Стратегия поиска точки деградации системы

    TODO: Реализовать логику:
    - Постепенно увеличивать нагрузку
    - Отслеживать падение эффективности масштабирования
    - Отслеживать ухудшение стабильности (рост P99/P50)
    - Останавливаться когда degradation_index > порога
    """

    def __init__(self, initial_users: int = 10, step_multiplier: float = 1.5):
        # TODO: Добавить параметры стратегии
        self.initial_users = initial_users
        self.step_multiplier = step_multiplier

    def decide(self, metrics: AnalyzedMetrics) -> Decision:
        """
        TODO: Реализовать логику принятия решения

        Проверить:
        1. degradation_index >= 0.6 -> STOP
        2. stability > 3.0 -> STOP
        3. scaling_efficiency < 0.3 -> STOP
        4. error_rate > 5% -> STOP
        5. Иначе -> INCREASE
        """
        return Decision.INCREASE

    def get_next_users(self, current_users: int, metrics: AnalyzedMetrics) -> int:
        """
        TODO: Вычислить следующее количество пользователей

        Логика:
        - Если current_users == 0, вернуть initial_users
        - Иначе увеличить на step_multiplier (например, * 1.5)
        """
        if current_users == 0:
            return self.initial_users
        return int(current_users * self.step_multiplier)

    def reset(self) -> None:
        """TODO: Сбросить внутреннее состояние"""
        pass