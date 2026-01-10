from abc import ABC, abstractmethod
from ..models import RawMetrics, Decision


class IStrategy(ABC):
    """Интерфейс стратегии тестирования"""

    @abstractmethod
    def decide(self, metrics: RawMetrics) -> Decision:
        """
        Принять решение на основе метрик

        Args:
            metrics: Сырые метрики от генератора нагрузки

        Returns:
            Decision: CONTINUE, HOLD или STOP
        """
        pass

    @abstractmethod
    def get_next_users(self, current_users: int, metrics: RawMetrics) -> int:
        """
        Вычислить следующее количество юзеров

        Args:
            current_users: Текущее количество пользователей
            metrics: Сырые метрики от генератора нагрузки

        Returns:
            Новое количество пользователей
        """
        pass

    def get_wait_time(self) -> int:
        """
        Вернуть время ожидания между изменениями нагрузки (в секундах)

        Контролирует как часто увеличивать нагрузку при Decision.CONTINUE.
        Метод decide() вызывается при каждом мониторинге, но нагрузка
        изменяется только раз в get_wait_time() секунд.

        Примеры:
        - DegradationSearch: 30 сек (время стабилизации после увеличения нагрузки)
        - Spike: 1 сек (быстрая смена фаз)
        - StepLoad: step_duration (держать ступень)
        - Canary: 5 сек (быстрая проверка)

        Returns:
            Время ожидания в секундах (по умолчанию 30)
        """
        return 30

    @abstractmethod
    def reset(self) -> None:
        """Сбросить состояние для нового теста"""
        pass