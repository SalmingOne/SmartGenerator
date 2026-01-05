from .base import IStrategy
from ..models import AnalyzedMetrics, Decision


class TargetUsers(IStrategy):
    """
    Стратегия проверки конкретного количества пользователей

    TODO: Реализовать логику:
    - Постепенно увеличивать нагрузку до target_users
    - Проверить что система выдерживает эту нагрузку
    - Останавливаться если:
      * Достигли target_users и система стабильна
      * Или началась деградация раньше
    """

    def __init__(
        self,
        target_users: int,
        initial_users: int = 10,
        step_multiplier: float = 1.5,
        stability_checks: int = 3,  # Сколько раз проверить стабильность на target
    ):
        """
        Args:
            target_users: Целевое количество пользователей
            initial_users: Начальное количество пользователей
            step_multiplier: Множитель для увеличения нагрузки
            stability_checks: Сколько раз проверить стабильность на целевой нагрузке
        """
        self.target_users = target_users
        self.initial_users = initial_users
        self.step_multiplier = step_multiplier
        self.stability_checks = stability_checks
        self._checks_done = 0

    def decide(self, metrics: AnalyzedMetrics) -> Decision:
        """
        TODO: Реализовать логику принятия решения

        Если current_users < target_users:
            -> INCREASE
        Если current_users >= target_users:
            Проверить стабильность stability_checks раз:
            - Если стабильно (degradation_index < 0.6) -> HOLD
            - После N проверок -> STOP (цель достигнута)
            - Если нестабильно -> STOP (деградация)
        """
        return Decision.INCREASE

    def get_next_users(self, current_users: int, metrics: AnalyzedMetrics) -> int:
        """
        TODO: Вычислить следующее количество пользователей

        Если current_users < target_users:
            - Увеличивать постепенно, но не превышать target_users
        Если current_users >= target_users:
            - Вернуть target_users (держать на целевой нагрузке)
        """
        if current_users == 0:
            return self.initial_users

        next_users = int(current_users * self.step_multiplier)
        # Не превышаем target
        return min(next_users, self.target_users)

    def reset(self) -> None:
        """TODO: Сбросить внутреннее состояние"""
        self._checks_done = 0