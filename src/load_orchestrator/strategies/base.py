from abc import ABC, abstractmethod
from ..models import AnalyzedMetrics, Decision


class IStrategy(ABC):
    """Интерфейс стратегии тестирования"""

    @abstractmethod
    def decide(self, metrics: AnalyzedMetrics) -> Decision:
        """
        Принять решение на основе метрик

        Args:
            metrics: Проанализированные метрики

        Returns:
            Decision: INCREASE, HOLD или STOP
        """
        pass

    @abstractmethod
    def get_next_users(self, current_users: int, metrics: AnalyzedMetrics) -> int:
        """
        Вычислить следующее количество юзеров

        Args:
            current_users: Текущее количество пользователей
            metrics: Проанализированные метрики

        Returns:
            Новое количество пользователей
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Сбросить состояние для нового теста"""
        pass