from .base import IStrategy
from ..models import AnalyzedMetrics, Decision


class BreakPoint(IStrategy):
    """
    Стратегия поиска точки отказа системы

    TODO: Реализовать логику:
    - Агрессивно увеличивать нагрузку до полного отказа
    - Останавливаться когда:
      * error_rate > 10% (система начала массово отказывать)
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

    def decide(self, metrics: AnalyzedMetrics) -> Decision:
        """
        TODO: Реализовать логику принятия решения

        Останавливаться если:
        1. error_rate >= error_threshold -> STOP (система отказывает)
        2. rps == 0 -> STOP (система не отвечает)
        3. p99 > 10000 (10 сек) -> STOP (система зависла)
        4. Иначе -> INCREASE (продолжаем давить)
        """
        return Decision.INCREASE

    def get_next_users(self, current_users: int, metrics: AnalyzedMetrics) -> int:
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