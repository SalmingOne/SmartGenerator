from .base import IStrategy
from ..models import RawMetrics, Decision


class StepLoad(IStrategy):
    """
    Стратегия ступенчатой нагрузки (Step Load Test)

    TODO: Реализовать логику:
    - Увеличивать нагрузку ступенями (steps)
    - На каждой ступени держать нагрузку step_duration секунд
    - Проверять стабильность на каждой ступени
    - Останавливаться если:
      * Система деградировала на текущей ступени
      * Достигли max_users
    """

    def __init__(
        self,
        step_size: int = 50,  # На сколько users увеличивать каждый шаг
        step_duration: int = 60,  # Сколько секунд держать каждую ступень
        max_users: int = 1000,
        initial_users: int = 10,
    ):
        """
        Args:
            step_size: Размер ступени (на сколько увеличивать users)
            step_duration: Длительность каждой ступени (секунд)
            max_users: Максимальное количество пользователей
            initial_users: Начальное количество пользователей
        """
        self.step_size = step_size
        self.step_duration = step_duration
        self.max_users = max_users
        self.initial_users = initial_users

        self._current_step = 0
        self._step_checks = 0

    def decide(self, metrics: RawMetrics) -> Decision:
        """
        TODO: Реализовать логику принятия решения

        Логика:
        1. На каждой ступени проверять стабильность N раз
        2. Если стабильно -> HOLD (еще держим ступень)
        3. После N проверок -> INCREASE (переход на следующую ступень)
        4. Если нестабильно -> STOP (деградация)
        5. Если достигли max_users -> STOP
        """
        return Decision.CONTINUE

    def get_next_users(self, current_users: int, metrics: RawMetrics) -> int:
        """
        TODO: Вычислить следующее количество пользователей

        Логика:
        - Если переходим на новую ступень: current_users + step_size
        - Если держим ступень: current_users
        - Не превышать max_users
        """
        if current_users == 0:
            return self.initial_users

        next_users = current_users + self.step_size
        return min(next_users, self.max_users)

    def get_wait_time(self) -> int:
        """
        StepLoad держит каждую ступень step_duration секунд

        Returns:
            step_duration из конфигурации
        """
        return self.step_duration

    def reset(self) -> None:
        """TODO: Сбросить внутреннее состояние"""
        self._current_step = 0
        self._step_checks = 0