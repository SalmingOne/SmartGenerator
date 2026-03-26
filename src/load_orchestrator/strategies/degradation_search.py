from .base import IStrategy
from ..models import RawMetrics, Decision

import statistics


class DegradationSearch(IStrategy):

    def __init__(
        self,
        initial_users: int = 10,
        step_multiplier: float | None = 1.5,  # Экспоненциальный рост (множитель)
        step_size: int | None = None,  # Линейный рост (фиксированный шаг)
        window_size: int = 5,  # Размер скользящего окна
        threshold_count: int = 3,  # Сколько проверок из window_size должны превысить порог
    ):

        self.initial_users = initial_users
        self.step_multiplier = step_multiplier
        self.step_size = step_size
        self.window_size = window_size
        self.threshold_count = threshold_count

        self.metrics_history: list[RawMetrics] = []


    def decide(self, metrics: RawMetrics) -> Decision:
        self.metrics_history.append(metrics)

        # Минимум данных
        if len(self.metrics_history) < 5:
            return Decision.CONTINUE

        # Берём только p95
        p95 = [m.p95 for m in self.metrics_history]
        errors = [m.error_rate for m in self.metrics_history]

        BASELINE_WINDOW = 10
        CHECK_WINDOW = 3
        MULTIPLIER = 1.5

        # baseline — медиана стабильного участка
        baseline_slice_p95 = p95[-(BASELINE_WINDOW + CHECK_WINDOW):-CHECK_WINDOW]
        baseline_slice_error_rate = errors[-(BASELINE_WINDOW + CHECK_WINDOW):-CHECK_WINDOW]
        baseline_p95 = statistics.median(baseline_slice_p95)
        baseline_error_rate = statistics.median(baseline_slice_error_rate)

        # последние значения
        recent_p95 = p95[-CHECK_WINDOW:]
        recent_error_rate = errors[-CHECK_WINDOW:]

        # условие деградации:
        if all(v > baseline_p95 * MULTIPLIER for v in recent_p95) or all(v > baseline_error_rate * MULTIPLIER for v in recent_error_rate) :
            return Decision.STOP

        return Decision.CONTINUE

    def get_next_users(self, current_users: int, metrics: RawMetrics) -> int:
        """
        Вычислить следующее количество пользователей

        Поддерживает два режима:
        1. Линейный рост (step_size): users + step_size
        2. Экспоненциальный рост (step_multiplier): users * step_multiplier
        """
        if self.step_size is not None:
            return int(current_users + self.step_size)
        return int(current_users * self.step_multiplier) + 1

    def get_wait_time(self) -> int:
        return 5

    def reset(self) -> None:
        """Сбросить внутреннее состояние стратегии"""
        self.metrics_history.clear()
