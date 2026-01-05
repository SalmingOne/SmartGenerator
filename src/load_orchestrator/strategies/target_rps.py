from .base import IStrategy
from ..models import AnalyzedMetrics, Decision


class TargetRPS(IStrategy):
    """
    Стратегия достижения целевого RPS

    TODO: Реализовать логику:
    - Постепенно увеличивать нагрузку пока не достигнем target_rps
    - Останавливаться если:
      * Достигли целевого RPS
      * Или началась деградация раньше
    """

    def __init__(
        self,
        target_rps: float,
        initial_users: int = 10,
        step_multiplier: float = 1.5,
        tolerance: float = 0.05,  # 5% погрешность
    ):
        """
        Args:
            target_rps: Целевой RPS который нужно достичь
            initial_users: Начальное количество пользователей
            step_multiplier: Множитель для увеличения нагрузки
            tolerance: Допустимое отклонение от target_rps (в долях)
        """
        self.target_rps = target_rps
        self.initial_users = initial_users
        self.step_multiplier = step_multiplier
        self.tolerance = tolerance

    def decide(self, metrics: AnalyzedMetrics) -> Decision:
        """
        TODO: Реализовать логику принятия решения

        Останавливаться если:
        1. current_rps >= target_rps * (1 - tolerance) -> STOP (цель достигнута)
        2. degradation_index > 0.6 -> STOP (началась деградация)
        3. Иначе -> INCREASE
        """
        return Decision.INCREASE

    def get_next_users(self, current_users: int, metrics: AnalyzedMetrics) -> int:
        """
        TODO: Вычислить следующее количество пользователей

        Можно использовать более умную логику:
        - Оценить сколько users нужно для достижения target_rps
        - Основываясь на текущем соотношении users/rps
        """
        if current_users == 0:
            return self.initial_users
        return int(current_users * self.step_multiplier)

    def reset(self) -> None:
        """TODO: Сбросить внутреннее состояние"""
        pass