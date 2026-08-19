from .base import IStrategy
from ..models import RawMetrics, Decision

import statistics


class DegradationSearch(IStrategy):
    def __init__(
        self,
        initial_users: int = 10,
        step_multiplier: float | None = 1.5,
        step_size: int | None = None,
        window_size: int = 10,      # Размер окна baseline
        threshold_count: int = 3,   # Размер окна проверки (должен быть < window_size)
        relative_multiplier: float = 2.0,   # Множитель для p95
        error_multiplier: float = 3.0,      # Множитель для error_rate
        required_ratio: float = 0.6,        # Доля точек для срабатывания (0.0-1.0)
        absolute_latency_limit: float = 3000,   # Абсолютный лимит p95 (ms)
        trend_window: int = 10,             # Окно для проверки тренда
        trend_slope_threshold: float = 100.0,  # Порог наклона тренда (мс/шаг)
    ):
        # Валидация
        if threshold_count >= window_size:
            raise ValueError(f"threshold_count ({threshold_count}) must be < window_size ({window_size})")
        if not 0 <= required_ratio <= 1:
            raise ValueError(f"required_ratio ({required_ratio}) must be in [0, 1]")

        self.initial_users = initial_users
        self.step_multiplier = step_multiplier
        self.step_size = step_size
        self.window_size = window_size
        self.threshold_count = threshold_count
        self.relative_multiplier = relative_multiplier
        self.error_multiplier = error_multiplier
        self.required_ratio = required_ratio
        self.absolute_latency_limit = absolute_latency_limit
        self.trend_window = trend_window
        self.trend_slope_threshold = trend_slope_threshold

        self.metrics_history: list[RawMetrics] = []

    def decide(self, metrics: RawMetrics) -> Decision:
        self.metrics_history.append(metrics)

        # Минимум данных: baseline + проверка
        min_required = self.window_size + self.threshold_count
        if len(self.metrics_history) < min_required:
            return Decision.CONTINUE

        # --- Разделение на окна ---
        # Baseline: более ранние точки (стабильная нагрузка)
        # Recent: последние точки (возможная деградация)
        baseline_p95 = [m.p95 for m in self.metrics_history[-min_required:-self.threshold_count]]
        baseline_errors = [m.error_rate for m in self.metrics_history[-min_required:-self.threshold_count]]
        recent = self.metrics_history[-self.threshold_count:]

        baseline_p95_median = statistics.median(baseline_p95)
        baseline_error_median = max(1.0, statistics.median(baseline_errors))

        # --- Проверка 1: Абсолютный лимит p95 ---
        recent_p95_median = statistics.median(m.p95 for m in recent)
        if recent_p95_median > self.absolute_latency_limit:
            return Decision.STOP

        # --- Проверка 2: Абсолютный лимит p50 ---
        recent_p50_median = statistics.median(m.p50 for m in recent)
        if recent_p50_median > self.absolute_latency_limit * 0.5:  # p50 строже
            return Decision.STOP

        # --- Проверка 3: Относительная деградация p95 ---
        p95_threshold = baseline_p95_median * self.relative_multiplier
        p95_exceeding = sum(1 for m in recent if m.p95 > p95_threshold)
        if p95_exceeding / len(recent) >= self.required_ratio:
            return Decision.STOP

        # --- Проверка 4: Относительная деградация ошибок ---
        error_threshold = baseline_error_median * self.error_multiplier
        error_exceeding = sum(1 for m in recent if m.error_rate > error_threshold)
        if error_exceeding / len(recent) >= self.required_ratio:
            return Decision.STOP

        # --- Проверка 5: Устойчивый тренд роста ---
        if len(self.metrics_history) >= self.trend_window:
            trend_p95 = [m.p95 for m in self.metrics_history[-self.trend_window:]]
            if self._is_trending_up(trend_p95, threshold=p95_threshold):
                return Decision.STOP

        return Decision.CONTINUE

    def _is_trending_up(self, values: list[float], threshold: float) -> bool:
        """Линейная регрессия: проверяет устойчивый рост."""
        if len(values) < 5:
            return False

        n = len(values)
        x = list(range(n))

        mean_x = sum(x) / n
        mean_y = sum(values) / n

        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator = sum((xi - mean_x) ** 2 for xi in x)

        if denominator == 0:
            return False

        slope = numerator / denominator
        # Растёт быстро И уже выше относительного порога
        return slope > self.trend_slope_threshold and values[-1] > threshold


    def get_next_users(self, current_users: int, metrics: RawMetrics) -> int:
        """
        Вычислить следующее количество пользователей

        Поддерживает два режима:
        1. Линейный рост (step_size): users + step_size
        2. Экспоненциальный рост (step_multiplier): users * step_multiplier
        """
        if current_users == 0:
            return self.initial_users
        if self.step_size is not None:
            return int(current_users + self.step_size)
        return int(current_users * self.step_multiplier) + 1

    def get_wait_time(self) -> int:
        return 5

    def reset(self) -> None:
        """Сбросить внутреннее состояние стратегии"""
        self.metrics_history.clear()
